from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings
from .features import parse_launch_datetime
from .spacex_api import SpaceXClient
from .state import BotState
from .tweet_text import format_launch_date, format_tweet
from .twitter_client import TweetResult, TwitterPoster


@dataclass(frozen=True)
class BotDecision:
    should_post: bool
    reason: str
    launch: dict[str, Any] | None = None
    text: str | None = None
    media_path: str | None = None


def evaluate_posting_rules(
    launch: dict[str, Any],
    state: BotState,
    settings: Settings,
    *,
    force: bool,
    allow_stale: bool,
) -> BotDecision:
    launch_id = str(launch.get("id") or "")
    if not launch_id:
        return BotDecision(False, "launch has no id", launch)
    if state.was_tweeted(launch_id) and not force:
        return BotDecision(False, f"already tweeted launch {launch_id}", launch)

    launch_time = parse_launch_datetime(launch)
    if launch_time is None:
        return BotDecision(False, "launch has no parseable date_utc", launch)

    now = datetime.now(timezone.utc)
    hours_until_launch = (launch_time - now).total_seconds() / 3600
    if hours_until_launch < -settings.max_stale_hours and not allow_stale:
        return BotDecision(
            False,
            (
                "SpaceX API next launch is stale: "
                f"{format_launch_date(launch)} is in the past"
            ),
            launch,
        )
    if hours_until_launch > settings.post_window_hours and not force:
        return BotDecision(
            False,
            (
                f"launch is {hours_until_launch:.1f} hours away; "
                f"window is {settings.post_window_hours:.1f} hours"
            ),
            launch,
        )
    return BotDecision(True, "posting rules passed", launch)


def build_decision(
    settings: Settings,
    *,
    force: bool,
    allow_stale: bool,
) -> BotDecision:
    client = SpaceXClient(base_url=settings.spacex_api_base_url)
    launch = client.next_launch()
    if launch is None:
        return BotDecision(False, "no upcoming launch returned by SpaceX API")

    state = BotState(settings.state_path)
    decision = evaluate_posting_rules(
        launch, state, settings, force=force, allow_stale=allow_stale
    )
    if not decision.should_post:
        return decision

    from .model import load_model_bundle, predict_probabilities
    from .graphic import generate_prediction_chart

    bundle = load_model_bundle(settings.model_path)
    predictions = predict_probabilities(bundle, launch)
    
    media_path = "/tmp/spacex_prediction.png"
    generate_prediction_chart(launch, predictions, media_path)
    
    return BotDecision(
        True, "ready to post", launch, format_tweet(launch, predictions), media_path
    )


def run_bot(
    settings: Settings,
    *,
    dry_run: bool | None = None,
    force: bool = False,
    allow_stale: bool = False,
) -> TweetResult | BotDecision:
    effective_dry_run = settings.dry_run if dry_run is None else dry_run
    decision = build_decision(settings, force=force, allow_stale=allow_stale)
    if not decision.should_post:
        return decision
    assert decision.launch is not None
    assert decision.text is not None

    if effective_dry_run:
        return TweetResult(posted=False, tweet_id=None, text=decision.text, media_path=decision.media_path)

    poster = TwitterPoster(settings)
    result = poster.post(decision.text, media_path=decision.media_path)
    BotState(settings.state_path).mark_tweeted(
        str(decision.launch.get("id")), result.tweet_id
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the SpaceX predictor X bot.")
    parser.add_argument("--dry-run", action="store_true", help="Print tweet only.")
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post to X/Twitter, overriding DRY_RUN=true.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass duplicate and post-window checks.",
    )
    parser.add_argument(
        "--allow-stale",
        action="store_true",
        help="Allow local testing when the API returns a past launch.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Override MODEL_PATH.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    if args.model_path is not None:
        settings = replace(settings, model_path=args.model_path)
    dry_run = True if args.dry_run else False if args.post else None
    result = run_bot(
        settings,
        dry_run=dry_run,
        force=args.force,
        allow_stale=args.allow_stale,
    )
    if isinstance(result, TweetResult):
        status = "DRY RUN" if not result.posted else f"POSTED {result.tweet_id}"
        print(f"{status}\n{result.text}")
        if getattr(result, "media_path", None):
            print(f"Graphic saved to: {result.media_path}")
    else:
        print(f"NO POST: {result.reason}")


if __name__ == "__main__":
    main()
