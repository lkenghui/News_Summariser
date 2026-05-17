import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class KeylessNewsAppTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("OPENAI_API_KEY", None)
        self.tmp = tempfile.TemporaryDirectory()

        for name in ("app", "database", "summarizer"):
            sys.modules.pop(name, None)

        database = importlib.import_module("database")
        database.DB_PATH = str(Path(self.tmp.name) / "digest.db")
        database.init_db()
        database.save_digest(json.dumps([{
            "source": "Test Source",
            "title": "Cached article",
            "url": "https://example.com/article",
            "summary": "Cached summary",
            "topic": "Other",
            "topic_icon": "N",
        }]))

        self.app_module = importlib.import_module("app")
        self.app_module.app.config.update(TESTING=True)
        self.client = self.app_module.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_homepage_uses_saved_digest_without_key(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cached article", response.data)

    def test_status_endpoint_is_available_without_key(self):
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("running", response.get_json())

    def test_summarizer_reports_missing_key(self):
        summarizer = importlib.import_module("summarizer")
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            summarizer.summarize_articles([{
                "title": "Example",
                "source": "Test",
                "description": "Example description",
            }])


if __name__ == "__main__":
    unittest.main()
