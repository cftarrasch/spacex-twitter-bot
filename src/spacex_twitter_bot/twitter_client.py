from __future__ import annotations

from dataclasses import dataclass

from .config import Settings


@dataclass(frozen=True)
class TweetResult:
    posted: bool
    tweet_id: str | None
    text: str
    media_path: str | None = None


class TwitterPoster:
    def __init__(self, settings: Settings) -> None:
        settings.validate_twitter_credentials()
        import tweepy

        self.client = tweepy.Client(
            consumer_key=settings.twitter_api_key,
            consumer_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_secret,
        )
        
        auth = tweepy.OAuth1UserHandler(
            settings.twitter_api_key,
            settings.twitter_api_secret,
            settings.twitter_access_token,
            settings.twitter_access_secret,
        )
        self.api = tweepy.API(auth)

    def post(self, text: str, media_path: str | None = None) -> TweetResult:
        media_ids = None
        if media_path:
            media = self.api.media_upload(media_path)
            media_ids = [media.media_id]

        response = self.client.create_tweet(text=text, media_ids=media_ids)
        tweet_id = None
        if response and getattr(response, "data", None):
            tweet_id = str(response.data.get("id"))
        return TweetResult(posted=True, tweet_id=tweet_id, text=text, media_path=media_path)

