from __future__ import annotations

from typing import Any

from .features import landing_attempt_declared, parse_launch_datetime


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def format_launch_date(launch: dict[str, Any]) -> str:
    parsed = parse_launch_datetime(launch)
    if parsed is None:
        return str(launch.get("date_utc") or "unknown date")
    return parsed.strftime("%Y-%m-%d %H:%M UTC")


def format_tweet(launch: dict[str, Any], predictions: dict[str, float]) -> str:
    launch_prob = percent(predictions["launch_success"])
    if landing_attempt_declared(launch):
        landing_line = f"Booster landing success: {percent(predictions['landing_success'])}"
    else:
        landing_line = "Booster landing: no landing attempt declared"

    text = (
        f"SpaceX prediction for {launch.get('name', 'next mission')}\n"
        f"Target: {format_launch_date(launch)}\n"
        f"Launch success: {launch_prob}\n"
        f"{landing_line}\n"
        "Model trained on public r/SpaceX API data."
    )
    if len(text) <= 280:
        return text
    return text[:276].rstrip() + "..."

