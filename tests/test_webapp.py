import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"

        conn = sqlite3.connect(self.db_path)
        schema = Path("webapp/schema.sql").read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.execute(
            "INSERT INTO species(slug, scientific_name, status, created_at, updated_at, entered_at) VALUES ('begonia-test','Begonia test','verified','2026-01-01','2026-01-01','2026-01-01')"
        )
        conn.commit()
        conn.close()

        env = os.environ.copy()
        env["BEGONIA_DB"] = str(self.db_path)
        env["PORT"] = "8099"
        self.proc = subprocess.Popen(["python3", "webapp/app.py"], env=env)
        time.sleep(1.0)

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait(timeout=5)
        self.tmp.cleanup()

    def test_home_ok(self):
        with urlopen("http://127.0.0.1:8099/") as r:
            body = r.read().decode("utf-8")
        self.assertIn("秋海棠新种数据库", body)

    def test_api_species_has_items(self):
        with urlopen("http://127.0.0.1:8099/api/species") as r:
            payload = r.read().decode("utf-8")
        self.assertIn("items", payload)

    def test_api_submission_create(self):
        req = Request(
            "http://127.0.0.1:8099/api/submissions",
            method="POST",
            data=b'{"submitted_name":"Begonia sp."}',
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req) as r:
            payload = r.read().decode("utf-8")
        self.assertIn('"ok": true', payload)


if __name__ == "__main__":
    unittest.main()
