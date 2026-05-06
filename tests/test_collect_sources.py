import unittest
from unittest.mock import patch
from urllib.error import URLError
from tempfile import TemporaryDirectory
from pathlib import Path

import scripts.collect_sources as cs


class CollectSourcesTests(unittest.TestCase):
    def test_normalize_crossref_item_minimal(self):
        item = {
            "title": ["A new species of Begonia"],
            "DOI": "10.1234/example",
            "issued": {"date-parts": [[2026, 4, 1]]},
            "container-title": ["Phytotaxa"],
            "link": [{"content-type": "application/pdf", "URL": "https://example/pdf"}],
            "URL": "https://doi.org/10.1234/example",
            "type": "journal-article",
            "score": 12.3,
        }
        out = cs.normalize_crossref_item(item)
        self.assertEqual(out["title"], "A new species of Begonia")
        self.assertEqual(out["doi"], "10.1234/example")
        self.assertEqual(out["published_on"], "2026-04-01")
        self.assertEqual(out["pdf_url"], "https://example/pdf")

    @patch("scripts.collect_sources.fetch_json")
    def test_collect_crossref_passes_direct_flag(self, mock_fetch):
        mock_fetch.return_value = {"message": {"items": []}}
        cs.collect_crossref("Begonia", "2025-01-01", 3, direct=True)
        _, kwargs = mock_fetch.call_args
        self.assertTrue(kwargs["direct"])

    @patch("scripts.collect_sources.collect_crossref")
    def test_main_retries_direct_on_tunnel_403(self, mock_collect):
        # First call (proxy) fails with tunnel 403, second call (direct) succeeds.
        mock_collect.side_effect = [
            URLError("Tunnel connection failed: 403 Forbidden"),
            [{"source": "crossref", "title": "ok"}],
        ]
        with TemporaryDirectory() as tmp_dir:
            output = str(Path(tmp_dir) / "out.json")
            argv = ["collect_sources.py", "--output", output]
            with patch("sys.argv", argv):
                code = cs.main()

        self.assertEqual(code, 0)
        self.assertEqual(mock_collect.call_count, 2)
        _, first_kwargs = mock_collect.call_args_list[0]
        _, second_kwargs = mock_collect.call_args_list[1]
        self.assertFalse(first_kwargs["direct"])
        self.assertTrue(second_kwargs["direct"])


if __name__ == "__main__":
    unittest.main()
