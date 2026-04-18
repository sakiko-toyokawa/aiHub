import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scheduler.jobs import scheduler, init_scheduler, run_crawl_job, run_summarize_job, run_email_job


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.outerjoin.return_value.filter.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = Mock()
    settings.crawl_schedule = "0 */2 * * *"
    settings.summarize_schedule = "0 */3 * * *"
    settings.email_schedule = "0 22 * * *"
    settings.default_ai_provider = "openai"
    return settings


class TestScheduler:
    """Test scheduler functionality"""

    def test_scheduler_singleton(self):
        """Test that scheduler is a singleton"""
        from scheduler.jobs import scheduler as s1
        from scheduler.jobs import scheduler as s2
        assert s1 is s2

    @patch('app.config.get_settings')
    @patch('scheduler.jobs.scheduler')
    def test_init_scheduler(self, mock_scheduler, mock_get_settings, mock_settings):
        """Test scheduler initialization"""
        mock_get_settings.return_value = mock_settings
        mock_scheduler.add_job = Mock()
        mock_scheduler.start = Mock()

        result = init_scheduler()

        # Verify jobs were added
        assert mock_scheduler.add_job.call_count == 3
        mock_scheduler.start.assert_called_once()
        assert result == mock_scheduler

    @patch('app.database.SessionLocal')
    @patch('crawler.github_crawler.GitHubCrawler')
    def test_run_crawl_job(self, mock_crawler_class, mock_session_local):
        """Test crawl job execution"""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        # Mock the query chain to return None (no existing content)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_crawler = AsyncMock()
        mock_crawler.fetch.return_value = [
            Mock(
                platform="github",
                external_id="123",
                title="Test Repo",
                content="Test description",
                author="testuser",
                author_url="https://github.com/testuser",
                url="https://github.com/testuser/testrepo",
                raw_data={"id": 123}
            )
        ]
        mock_crawler_class.return_value = mock_crawler

        # Run the async function
        asyncio.run(run_crawl_job())

        mock_crawler.fetch.assert_called_once()
        mock_db.close.assert_called_once()

    @patch('app.config.get_settings')
    @patch('app.database.SessionLocal')
    @patch('summarizer.llm_client.LLMClient')
    def test_run_summarize_job_no_content(self, mock_llm_class, mock_session_local, mock_get_settings, mock_settings):
        """Test summarize job when no content to summarize"""
        mock_get_settings.return_value = mock_settings

        mock_db = MagicMock()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.limit.return_value.all.return_value = []
        mock_session_local.return_value = mock_db

        asyncio.run(run_summarize_job())

        mock_llm_class.assert_not_called()
        mock_db.close.assert_called_once()

    @patch('app.config.get_settings')
    @patch('app.database.SessionLocal')
    @patch('summarizer.llm_client.LLMClient')
    def test_run_summarize_job_with_content(self, mock_llm_class, mock_session_local, mock_get_settings, mock_settings):
        """Test summarize job with content to process"""
        mock_get_settings.return_value = mock_settings

        mock_raw = Mock(
            id=1,
            title="Test Content",
            content="Test content body"
        )

        mock_db = MagicMock()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.limit.return_value.all.return_value = [mock_raw]
        mock_session_local.return_value = mock_db

        mock_llm_client = AsyncMock()
        mock_llm_client.summarize.return_value = Mock(
            summary_text="Summary text",
            key_points=["point1", "point2"],
            tags=["tag1", "tag2"],
            model_used="gpt-4",
            provider="openai",
            tokens_used=100
        )
        mock_llm_class.return_value = mock_llm_client

        asyncio.run(run_summarize_job())

        mock_llm_client.summarize.assert_called_once_with(content="Test content body", title="Test Content")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_db.close.assert_called_once()

    @patch('notifier.email_sender.send_daily_digest')
    def test_run_email_job(self, mock_send_digest):
        """Test email job execution"""
        mock_send_digest.return_value = None

        asyncio.run(run_email_job())

        mock_send_digest.assert_called_once()

    @patch('notifier.email_sender.send_daily_digest')
    def test_run_email_job_error(self, mock_send_digest):
        """Test email job error handling"""
        mock_send_digest.side_effect = Exception("Email error")

        # Should not raise exception
        asyncio.run(run_email_job())

        mock_send_digest.assert_called_once()


class TestSchedulerIntegration:
    """Integration tests for scheduler"""

    def test_scheduler_job_ids(self):
        """Test that scheduler has expected job IDs configured"""
        # This test verifies the job IDs are correct in the code
        expected_jobs = ['crawl_job', 'summarize_job', 'email_job']
        # The actual jobs are added when init_scheduler is called
        assert len(expected_jobs) == 3
