import tempfile
import unittest
from pathlib import Path

from twcmanager.config import Settings, load_settings, save_settings


class TestConfig(unittest.TestCase):
    def test_save_and_load_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            save_settings(Settings(degraded_mode_max_amps=8), path)

            loaded = load_settings(path)

        self.assertEqual(loaded.degraded_mode_max_amps, 8)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                load_settings(path)

    def test_rejects_unknown_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text('{"unknown": true}', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unknown top-level"):
                load_settings(path)


if __name__ == "__main__":
    unittest.main()
