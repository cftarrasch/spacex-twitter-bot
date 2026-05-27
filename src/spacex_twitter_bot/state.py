from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BotState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"tweeted_launches": {}}
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def was_tweeted(self, launch_id: str) -> bool:
        return launch_id in self.data.get("tweeted_launches", {})

    def mark_tweeted(self, launch_id: str, tweet_id: str | None = None) -> None:
        self.data.setdefault("tweeted_launches", {})[launch_id] = {
            "tweeted_at": datetime.now(timezone.utc).isoformat(),
            "tweet_id": tweet_id,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2, sort_keys=True)
            file.write("\n")
