import unittest

from spacex_twitter_bot.features import (
    extract_feature_row,
    landing_success_label,
    launch_success_label,
)


def sample_launch():
    return {
        "flight_number": 100,
        "name": "DemoSat",
        "date_utc": "2026-05-30T12:00:00.000Z",
        "date_precision": "hour",
        "net": False,
        "tbd": False,
        "static_fire_date_utc": "2026-05-28T12:00:00.000Z",
        "success": True,
        "rocket": {
            "id": "rocket-1",
            "name": "Falcon 9",
            "success_rate_pct": 98,
        },
        "launchpad": {
            "id": "pad-1",
            "region": "Florida",
            "launch_attempts": 10,
            "launch_successes": 9,
        },
        "payloads": [
            {
                "id": "payload-1",
                "name": "Payload 1",
                "mass_kg": 500,
                "orbit": "LEO",
                "inclination_deg": 53.0,
            },
            {
                "id": "payload-2",
                "name": "Payload 2",
                "mass_kg": None,
                "orbit": "LEO",
                "inclination_deg": None,
            },
        ],
        "cores": [
            {
                "flight": 7,
                "gridfins": True,
                "legs": True,
                "reused": True,
                "landing_attempt": True,
                "landing_success": True,
                "landing_type": "ASDS",
            }
        ],
    }


class FeatureTests(unittest.TestCase):
    def test_extract_feature_row_uses_populated_api_fields(self):
        row = extract_feature_row(sample_launch())

        self.assertEqual(row["rocket_name"], "Falcon 9")
        self.assertEqual(row["payload_count"], 2)
        self.assertEqual(row["payload_mass_kg"], 500)
        self.assertEqual(row["payload_unknown_mass_count"], 1)
        self.assertEqual(row["primary_orbit"], "LEO")
        self.assertEqual(row["launchpad_success_rate"], 0.9)
        self.assertEqual(row["declared_landing_attempt"], 1)

    def test_labels(self):
        launch = sample_launch()

        self.assertIs(launch_success_label(launch), True)
        self.assertIs(landing_success_label(launch), True)


if __name__ == "__main__":
    unittest.main()
