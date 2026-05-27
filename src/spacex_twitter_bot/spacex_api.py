from __future__ import annotations

from typing import Any

import requests


class SpaceXAPIError(RuntimeError):
    """Raised when the SpaceX API cannot be read."""


LAUNCH_POPULATE = [
    {
        "path": "payloads",
        "select": {
            "name": 1,
            "type": 1,
            "mass_kg": 1,
            "orbit": 1,
            "inclination_deg": 1,
            "period_min": 1,
        },
    },
    {
        "path": "rocket",
        "select": {"name": 1, "type": 1, "success_rate_pct": 1},
    },
    {
        "path": "launchpad",
        "select": {
            "name": 1,
            "region": 1,
            "locality": 1,
            "launch_attempts": 1,
            "launch_successes": 1,
        },
    },
]


class SpaceXClient:
    def __init__(
        self,
        base_url: str = "https://api.spacexdata.com/v4",
        timeout_seconds: float = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method, url, json=json, timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SpaceXAPIError(f"SpaceX API request failed: {method} {url}") from exc
        return response.json()

    def query_launches(
        self,
        query: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        body = {"query": query or {}, "options": options or {}}
        data = self._request("POST", "/launches/query", json=body)
        if isinstance(data, dict) and "docs" in data:
            return data["docs"]
        if isinstance(data, list):
            return data
        raise SpaceXAPIError("Unexpected SpaceX query response shape")

    def past_launches(self) -> list[dict[str, Any]]:
        return self.query_launches(
            {"upcoming": False},
            {
                "pagination": False,
                "sort": {"flight_number": "asc"},
                "populate": LAUNCH_POPULATE,
            },
        )

    def upcoming_launches(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.query_launches(
            {"upcoming": True},
            {
                "limit": limit,
                "sort": {"date_unix": "asc"},
                "populate": LAUNCH_POPULATE,
            },
        )

    def next_launch(self) -> dict[str, Any] | None:
        launches = self.upcoming_launches(limit=1)
        return launches[0] if launches else None

