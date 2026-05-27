from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

NUMERIC_FEATURES = [
    "flight_number",
    "payload_count",
    "payload_mass_kg",
    "payload_unknown_mass_count",
    "payload_mean_inclination_deg",
    "core_count",
    "core_flights_total",
    "max_core_flight",
    "any_reused_core",
    "all_reused_cores",
    "any_gridfins",
    "any_legs",
    "declared_landing_attempt",
    "has_static_fire",
    "is_net",
    "is_tbd",
    "rocket_success_rate_pct",
    "launchpad_success_rate",
]

CATEGORICAL_FEATURES = [
    "rocket_id",
    "rocket_name",
    "launchpad_id",
    "launchpad_region",
    "date_precision",
    "primary_orbit",
    "landing_type",
]


def bool_int(value: Any) -> int:
    return 1 if value is True else 0


def id_of(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("id") or "unknown")
    if value:
        return str(value)
    return "unknown"


def name_of(value: Any, fallback: str = "unknown") -> str:
    if isinstance(value, dict):
        return str(value.get("name") or fallback)
    if value:
        return str(value)
    return fallback


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def average(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def payload_stats(payloads: list[Any]) -> dict[str, Any]:
    populated = [payload for payload in payloads if isinstance(payload, dict)]
    masses = [safe_float(payload.get("mass_kg")) for payload in populated]
    masses = [mass for mass in masses if mass is not None]
    inclinations = [
        safe_float(payload.get("inclination_deg")) for payload in populated
    ]
    inclinations = [value for value in inclinations if value is not None]
    orbit = next(
        (payload.get("orbit") for payload in populated if payload.get("orbit")), None
    )
    unknown_mass_count = max(len(payloads) - len(masses), 0)
    return {
        "payload_count": len(payloads),
        "payload_mass_kg": sum(masses) if masses else None,
        "payload_unknown_mass_count": unknown_mass_count,
        "payload_mean_inclination_deg": average(inclinations),
        "primary_orbit": str(orbit or "unknown"),
    }


def core_stats(cores: list[dict[str, Any]]) -> dict[str, Any]:
    flights = [safe_float(core.get("flight")) or 0.0 for core in cores]
    reused_flags = [core.get("reused") is True for core in cores]
    landing_type = next(
        (core.get("landing_type") for core in cores if core.get("landing_type")), None
    )
    declared_attempt = any(core.get("landing_attempt") is True for core in cores)
    return {
        "core_count": len(cores),
        "core_flights_total": sum(flights),
        "max_core_flight": max(flights, default=0.0),
        "any_reused_core": 1 if any(reused_flags) else 0,
        "all_reused_cores": 1 if cores and all(reused_flags) else 0,
        "any_gridfins": 1 if any(core.get("gridfins") is True for core in cores) else 0,
        "any_legs": 1 if any(core.get("legs") is True for core in cores) else 0,
        "declared_landing_attempt": 1 if declared_attempt else 0,
        "landing_type": str(landing_type or "unknown"),
    }


def launchpad_success_rate(launchpad: Any) -> float | None:
    if not isinstance(launchpad, dict):
        return None
    attempts = safe_float(launchpad.get("launch_attempts"))
    successes = safe_float(launchpad.get("launch_successes"))
    if attempts is None or attempts <= 0 or successes is None:
        return None
    return successes / attempts


def extract_feature_row(launch: dict[str, Any]) -> dict[str, Any]:
    payloads = launch.get("payloads") or []
    cores = launch.get("cores") or []
    rocket = launch.get("rocket")
    launchpad = launch.get("launchpad")

    row: dict[str, Any] = {
        "flight_number": launch.get("flight_number"),
        "rocket_id": id_of(rocket),
        "rocket_name": name_of(rocket),
        "launchpad_id": id_of(launchpad),
        "launchpad_region": (
            str(launchpad.get("region") or "unknown")
            if isinstance(launchpad, dict)
            else "unknown"
        ),
        "date_precision": str(launch.get("date_precision") or "unknown"),
        "has_static_fire": bool_int(bool(launch.get("static_fire_date_utc"))),
        "is_net": bool_int(launch.get("net")),
        "is_tbd": bool_int(launch.get("tbd") or launch.get("tdb")),
        "rocket_success_rate_pct": (
            safe_float(rocket.get("success_rate_pct"))
            if isinstance(rocket, dict)
            else None
        ),
        "launchpad_success_rate": launchpad_success_rate(launchpad),
    }
    row.update(payload_stats(payloads))
    row.update(core_stats(cores))
    return row


def launch_success_label(launch: dict[str, Any]) -> bool | None:
    value = launch.get("success")
    return value if isinstance(value, bool) else None


def landing_success_label(launch: dict[str, Any]) -> bool | None:
    attempted = [
        core
        for core in launch.get("cores") or []
        if core.get("landing_attempt") is True
    ]
    if not attempted:
        return None
    outcomes = [core.get("landing_success") for core in attempted]
    if any(not isinstance(outcome, bool) for outcome in outcomes):
        return None
    return all(outcomes)


def landing_attempt_declared(launch: dict[str, Any]) -> bool:
    return any(
        core.get("landing_attempt") is True for core in launch.get("cores") or []
    )


def parse_launch_datetime(launch: dict[str, Any]) -> datetime | None:
    date_utc = launch.get("date_utc")
    if not isinstance(date_utc, str):
        return None
    value = date_utc.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
