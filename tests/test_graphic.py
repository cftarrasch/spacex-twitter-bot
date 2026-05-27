import os
import tempfile
import unittest

from spacex_twitter_bot.graphic import generate_prediction_chart

class TestGraphic(unittest.TestCase):
    def test_generate_prediction_chart(self):
        launch = {
            "name": "Test Mission",
            "cores": [{"landing_attempt": True}],
        }
        predictions = {
            "launch_success": 0.95,
            "landing_success": 0.85,
        }
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            output_path = generate_prediction_chart(launch, predictions, tmp_path)
            self.assertEqual(output_path, tmp_path)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
