import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio

from notifier.email_sender import send_daily_digest, build_email_html


@pytest.fixture
def mock_settings():
    """Create mock settings with email config"""
    settings = Mock()
    settings.smtp_host = "smtp.qq.com"
    settings.smtp_port = 587
    settings.smtp_user = "test@qq.com"
    settings.smtp_password = "testpassword"
    settings.email_to = "recipient@example.com"
    return settings


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    db = MagicMock()
    return db


class TestEmailSender:
    """Test email sender functionality"""

    @patch('notifier.email_sender.get_settings')
    @patch('notifier.email_sender.SessionLocal')
    @patch('notifier.email_sender.FastMail')
    def test_send_daily_digest_success(self, mock_fastmail_class, mock_session_local, mock_get_settings, mock_settings, mock_db_session):
        """Test successful daily digest email sending"""
        mock_get_settings.return_value = mock_settings
        mock_session_local.return_value = mock_db_session

        # Mock database query result
        mock_summary = Mock(
            summary_text="This is a test summary",
            key_points=["point1", "point2"],
            tags=["AI", "ML"],
            created_at=datetime.now()
        )
        mock_raw = Mock(
            platform="github",
            title="Test Repository",
            url="https://github.com/test/repo"
        )

        mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (mock_summary, mock_raw)
        ]

        mock_fastmail = AsyncMock()
        mock_fastmail_class.return_value = mock_fastmail

        asyncio.run(send_daily_digest())

        mock_fastmail.send_message.assert_called_once()
        mock_db_session.close.assert_called_once()

    @patch('notifier.email_sender.get_settings')
    def test_send_daily_digest_not_configured(self, mock_get_settings):
        """Test email sending when not configured"""
        settings = Mock()
        settings.smtp_user = ""
        settings.smtp_password = ""
        mock_get_settings.return_value = settings

        # Should complete without error
        asyncio.run(send_daily_digest())

    @patch('notifier.email_sender.get_settings')
    @patch('notifier.email_sender.SessionLocal')
    def test_send_daily_digest_no_summaries(self, mock_session_local, mock_get_settings, mock_settings, mock_db_session):
        """Test email sending when no new summaries"""
        mock_get_settings.return_value = mock_settings
        mock_session_local.return_value = mock_db_session

        # Empty summaries
        mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        # Should complete without sending email
        asyncio.run(send_daily_digest())

        mock_db_session.close.assert_called_once()

    @patch('notifier.email_sender.get_settings')
    @patch('notifier.email_sender.SessionLocal')
    @patch('notifier.email_sender.FastMail')
    def test_send_daily_digest_default_recipient(self, mock_fastmail_class, mock_session_local, mock_get_settings):
        """Test email sending with default recipient (smtp_user)"""
        settings = Mock()
        settings.smtp_host = "smtp.qq.com"
        settings.smtp_port = 587
        settings.smtp_user = "sender@qq.com"
        settings.smtp_password = "password"
        settings.email_to = ""  # No specific recipient
        mock_get_settings.return_value = settings

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock database query result
        mock_summary = Mock(
            summary_text="Test summary",
            key_points=["point1"],
            tags=["AI"],
            created_at=datetime.now()
        )
        mock_raw = Mock(
            platform="github",
            title="Test Repo",
            url="https://github.com/test/repo"
        )

        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (mock_summary, mock_raw)
        ]

        mock_fastmail = AsyncMock()
        mock_fastmail_class.return_value = mock_fastmail

        asyncio.run(send_daily_digest())

        # Verify email was sent to smtp_user as default recipient
        call_args = mock_fastmail.send_message.call_args
        message = call_args[0][0]
        # fastapi-mail converts string to NameEmail object
        assert len(message.recipients) == 1
        assert "sender@qq.com" in str(message.recipients[0])
        mock_db.close.assert_called_once()


class TestBuildEmailHtml:
    """Test email HTML building"""

    def test_build_email_html_structure(self):
        """Test HTML email structure"""
        mock_summary = Mock(
            summary_text="Test summary content that is long enough to be truncated",
            key_points=["point1", "point2"],
            tags=["AI", "ML"]
        )
        mock_raw = Mock(
            platform="github",
            title="Test Repository",
            url="https://github.com/test/repo"
        )

        summaries = [(mock_summary, mock_raw)]
        html = build_email_html(summaries)

        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "今日 AI 知识摘要" in html
        assert "Test Repository" in html
        assert "github" in html.lower()
        assert "查看原文" in html

    def test_build_email_html_multiple_platforms(self):
        """Test HTML with multiple platforms"""
        summaries = [
            (Mock(summary_text="GitHub summary", key_points=[], tags=[]),
             Mock(platform="github", title="GitHub Repo", url="https://github.com/test")),
            (Mock(summary_text="Zhihu summary", key_points=[], tags=[]),
             Mock(platform="zhihu", title="Zhihu Article", url="https://zhihu.com/test")),
            (Mock(summary_text="Bilibili summary", key_points=[], tags=[]),
             Mock(platform="bilibili", title="Bilibili Video", url="https://bilibili.com/test")),
        ]

        html = build_email_html(summaries)

        assert "GITHUB" in html
        assert "ZHIHU" in html
        assert "BILIBILI" in html

    def test_build_email_html_platform_colors(self):
        """Test platform-specific colors in HTML"""
        summaries = [
            (Mock(summary_text="Summary", key_points=[], tags=[]),
             Mock(platform="github", title="Title", url="https://example.com")),
        ]

        html = build_email_html(summaries)

        # Check for GitHub color
        assert "#24292e" in html

    def test_build_email_html_unknown_platform(self):
        """Test HTML with unknown platform uses default color"""
        summaries = [
            (Mock(summary_text="Summary", key_points=[], tags=[]),
             Mock(platform="unknown_platform", title="Title", url="https://example.com")),
        ]

        html = build_email_html(summaries)

        # Should use default color #666
        assert "#666" in html

    def test_build_email_html_empty_title(self):
        """Test HTML with empty title"""
        summaries = [
            (Mock(summary_text="Summary", key_points=[], tags=[]),
             Mock(platform="github", title=None, url="https://example.com")),
        ]

        html = build_email_html(summaries)

        assert "无标题" in html

    def test_build_email_html_summary_truncation(self):
        """Test that long summaries are truncated"""
        long_summary = "A" * 300
        summaries = [
            (Mock(summary_text=long_summary, key_points=[], tags=[]),
             Mock(platform="github", title="Title", url="https://example.com")),
        ]

        html = build_email_html(summaries)

        # Should contain "..." indicating truncation
        assert "..." in html


class TestNotifierErrorHandling:
    """Test error handling in notifier"""

    @patch('notifier.email_sender.get_settings')
    @patch('notifier.email_sender.SessionLocal')
    def test_send_daily_digest_db_error(self, mock_session_local, mock_get_settings, mock_settings):
        """Test handling of database errors"""
        mock_get_settings.return_value = mock_settings
        mock_session_local.side_effect = Exception("Database connection failed")

        # Should raise the exception
        with pytest.raises(Exception, match="Database connection failed"):
            asyncio.run(send_daily_digest())
