import unittest

from spacex_twitter_bot.tweet_text import format_tweet


class TweetFormatTests(unittest.TestCase):
    def test_tweet_stays_within_x_limit(self):
        launch = {
            "name": "Starlink Group 99-99 With A Very Long Mission Name",
            "date_utc": "2026-05-30T12:00:00.000Z",
            "cores": [{"landing_attempt": True}],
        }
        predictions = {"launch_success": 0.973, "landing_success": 0.918}

        tweet = format_tweet(launch, predictions)

        self.assertIn("Launch success: 97.3%", tweet)
        self.assertLessEqual(len(tweet), 280)


if __name__ == "__main__":
    unittest.main()
