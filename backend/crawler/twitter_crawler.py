from datetime import datetime
from typing import List, Dict, Any, Optional
from crawler.base import BaseCrawler, CrawlResult


class TwitterCrawler(BaseCrawler):
    """
    Twitter/X 爬虫 - 使用 twikit 库
    项目地址: https://github.com/d60/twikit
    特点: 无需 API Key，直接逆向 Twitter Web API
    """

    platform = "twitter"

    # AI 相关搜索关键词
    SEARCH_KEYWORDS = [
        "artificial intelligence", "machine learning", "LLM", "ChatGPT",
        "GPT-4", "Claude", "AI", "generative AI", "NLP", "transformer"
    ]

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.username = config.get("username", "") if config else ""
        self.password = config.get("password", "") if config else ""
        self.email = config.get("email", "") if config else ""
        self._client = None

    async def _get_client(self):
        """Lazy init twikit client"""
        if self._client is None:
            try:
                from twikit import Client
                self._client = Client(language='en')

                # 如果有账号信息，尝试登录
                if self.username and self.password:
                    await self._client.login(
                        auth_info_1=self.username,
                        auth_info_2=self.email if self.email else None,
                        password=self.password
                    )
                    print(f"Twitter login successful: {self.username}")
            except ImportError:
                print("twikit not installed")
                return None
            except Exception as e:
                print(f"Twitter client init error: {e}")
                return None
        return self._client

    async def login(self, credentials: Dict[str, str]) -> bool:
        """登录 Twitter"""
        if not self.username or not self.password:
            print("Twitter credentials not provided")
            return False

        try:
            client = await self._get_client()
            return client is not None
        except Exception as e:
            print(f"Twitter login failed: {e}")
            return False

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        """抓取 Twitter AI 相关内容"""
        results = []

        client = await self._get_client()
        if client is None:
            print("Twitter client not available")
            return []

        try:
            # 1. 搜索推文
            for keyword in self.SEARCH_KEYWORDS[:3]:
                try:
                    search_results = await self._search_tweets(client, keyword)
                    results.extend(search_results)
                    await self.random_delay(3, 5)
                except Exception as e:
                    print(f"Error searching Twitter for '{keyword}': {e}")
                    continue

            # 2. 获取热门 AI 账号推文
            try:
                ai_accounts = [
                    "OpenAI", "AnthropicAI", "DeepMind",
                    "huggingface", "ylecun", "karpathy"
                ]
                for account in ai_accounts[:3]:
                    user_results = await self._fetch_user_tweets(client, account)
                    results.extend(user_results)
                    await self.random_delay(2, 4)
            except Exception as e:
                print(f"Error fetching Twitter user tweets: {e}")

        except Exception as e:
            print(f"Twitter crawler error: {e}")

        # 去重
        seen_ids = set()
        unique_results = []
        for r in results:
            if r.external_id not in seen_ids:
                seen_ids.add(r.external_id)
                unique_results.append(r)

        return self.filter_ai_content(unique_results)

    async def _search_tweets(self, client, keyword: str) -> List[CrawlResult]:
        """搜索推文"""
        results = []

        # 搜索最新推文
        tweets = await client.search_tweet(keyword, 'Latest')

        for tweet in tweets[:15]:  # 限制数量
            try:
                result = self._parse_tweet(tweet)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error parsing tweet: {e}")
                continue

        return results

    async def _fetch_user_tweets(self, client, username: str) -> List[CrawlResult]:
        """获取用户推文"""
        results = []

        try:
            # 获取用户信息
            user = await client.get_user_by_screen_name(username)

            # 获取用户推文
            tweets = await user.get_tweets('Tweets')

            for tweet in tweets[:5]:  # 限制数量
                try:
                    result = self._parse_tweet(tweet)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error parsing user tweet: {e}")
                    continue

        except Exception as e:
            print(f"Error fetching user {username}: {e}")

        return results

    def _parse_tweet(self, tweet) -> Optional[CrawlResult]:
        """解析推文"""
        try:
            tweet_id = str(tweet.id)
            text = tweet.text if hasattr(tweet, 'text') else str(tweet)

            # 获取作者信息
            if hasattr(tweet, 'user'):
                author = tweet.user.name
                author_screen = tweet.user.screen_name
            else:
                author = "Unknown"
                author_screen = "unknown"

            return CrawlResult(
                platform=self.platform,
                external_id=tweet_id,
                title=text[:100] + "..." if len(text) > 100 else text,
                content=text,
                author=author,
                author_url=f"https://twitter.com/{author_screen}",
                url=f"https://twitter.com/{author_screen}/status/{tweet_id}",
                raw_data={
                    "tweet_id": tweet_id,
                    "created_at": tweet.created_at if hasattr(tweet, 'created_at') else None,
                    "favorite_count": tweet.favorite_count if hasattr(tweet, 'favorite_count') else 0,
                    "retweet_count": tweet.retweet_count if hasattr(tweet, 'retweet_count') else 0
                },
                fetched_at=datetime.now()
            )
        except Exception as e:
            print(f"Error in _parse_tweet: {e}")
            return None
