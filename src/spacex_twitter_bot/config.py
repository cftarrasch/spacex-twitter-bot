from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - dependency exists in normal env
    load_dotenv = None


def _load_dotenv() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    spacex_api_base_url: str
    model_path: Path
    state_path: Path
    post_window_hours: float
    max_stale_hours: float
    dry_run: bool
    twitter_api_key: str | None
    twitter_api_secret: str | None
    twitter_access_token: str | None
    twitter_access_secret: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        return cls(
            spacex_api_base_url=os.getenv(
                "SPACEX_API_BASE_URL", "https://api.spacexdata.com/v4"
            ).rstrip("/"),
            model_path=Path(os.getenv("MODEL_PATH", "models/spacex_success.joblib")),
            state_path=Path(os.getenv("STATE_PATH", "data/bot_state.json")),
            post_window_hours=float(os.getenv("POST_WINDOW_HOURS", "48")),
            max_stale_hours=float(os.getenv("MAX_STALE_HOURS", "6")),
            dry_run=_bool_env("DRY_RUN", True),
            twitter_api_key=os.getenv("TWITTER_API_KEY") or None,
            twitter_api_secret=os.getenv("TWITTER_API_SECRET") or None,
            twitter_access_token=os.getenv("TWITTER_ACCESS_TOKEN") or None,
            twitter_access_secret=os.getenv("TWITTER_ACCESS_SECRET") or None,
        )

    def validate_twitter_credentials(self) -> None:
        missing = [
            name
            for name, value in {
                "TWITTER_API_KEY": self.twitter_api_key,
                "TWITTER_API_SECRET": self.twitter_api_secret,
                "TWITTER_ACCESS_TOKEN": self.twitter_access_token,
                "TWITTER_ACCESS_SECRET": self.twitter_access_secret,
            }.items()
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing Twitter credentials: {joined}")

