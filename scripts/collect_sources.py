#!/usr/bin/env python3
"""Collect candidate Begonia records from authoritative sources.

Modes:
1) Live mode (default): query Crossref REST API.
2) Offline sample mode: emit a normalized dataset template when network is restricted.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from urllib.error import URLError
from datetime import datetime, timezone
from typing import Any

CROSSREF_API = "https://api.crossref.org/works"


def fetch_json(url: str, timeout: int = 30, direct: bool = False) -> dict[str, Any]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if direct else urllib.request.build_opener()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "begonia-db-bot/0.2 (mailto:ops@example.org)",
            "Accept": "application/json",
        },
    )
    with opener.open(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return json.loads(resp.read().decode(charset))


def normalize_crossref_item(item: dict[str, Any]) -> dict[str, Any]:
    title = (item.get("title") or [""])[0]
    doi = item.get("DOI")
    issued_parts = (item.get("issued") or {}).get("date-parts") or []
    published_on = None
    if issued_parts and issued_parts[0]:
        parts = issued_parts[0]
        year = parts[0]
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        published_on = f"{year:04d}-{month:02d}-{day:02d}"

    links = item.get("link") or []
    pdf_url = next((link.get("URL") for link in links if str(link.get("content-type", "")).lower() == "application/pdf"), None)

    return {
        "source": "crossref",
        "title": title,
        "doi": doi,
        "url": item.get("URL"),
        "pdf_url": pdf_url,
        "journal_title": (item.get("container-title") or [None])[0],
        "published_on": published_on,
        "type": item.get("type"),
        "score": item.get("score"),
        "abstract": item.get("abstract"),
    }


def collect_crossref(query: str, from_date: str, rows: int, direct: bool = False) -> list[dict[str, Any]]:
    params = {
        "query.title": query,
        "filter": f"from-pub-date:{from_date},type:journal-article",
        "rows": str(rows),
        "sort": "published",
        "order": "desc",
    }
    url = f"{CROSSREF_API}?{urllib.parse.urlencode(params)}"
    payload = fetch_json(url, direct=direct)
    items = payload.get("message", {}).get("items", [])
    return [normalize_crossref_item(item) for item in items]


def build_offline_sample(query: str, from_date: str) -> list[dict[str, Any]]:
    return [
        {
            "source": "crossref",
            "title": f"[OFFLINE SAMPLE] {query} candidate article",
            "doi": None,
            "url": "https://api.crossref.org/works",
            "pdf_url": None,
            "journal_title": None,
            "published_on": from_date,
            "type": "journal-article",
            "score": None,
            "abstract": None,
            "note": "Generated because runtime network cannot reach Crossref from this container.",
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Begonia candidates from official sources")
    parser.add_argument("--query", default="Begonia", help="Title query keyword")
    parser.add_argument("--from-date", default="2025-01-01", help="Publication lower bound (YYYY-MM-DD)")
    parser.add_argument("--rows", type=int, default=30, help="Max rows from Crossref")
    parser.add_argument("--direct", action="store_true", help="Bypass HTTP(S)_PROXY and connect directly")
    parser.add_argument(
        "--retry-direct-on-403",
        action="store_true",
        default=True,
        help="When proxy tunnel returns 403, retry once via direct egress",
    )
    parser.add_argument("--offline-sample", action="store_true", help="Generate offline sample data")
    parser.add_argument("--output", default="data/crossref_begonia_candidates.json", help="Output JSON path")
    args = parser.parse_args()

    if args.offline_sample:
        items = build_offline_sample(args.query, args.from_date)
        mode = "offline-sample"
    else:
        try:
            items = collect_crossref(args.query, args.from_date, args.rows, direct=args.direct)
            mode = "live-direct" if args.direct else "live-proxy"
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] live collection failed: {exc}", file=sys.stderr)
            tunnel_403 = "Tunnel connection failed: 403" in str(exc)
            if tunnel_403 and args.retry_direct_on_403 and not args.direct:
                print("[INFO] retrying once with --direct due to proxy tunnel 403 ...", file=sys.stderr)
                try:
                    items = collect_crossref(args.query, args.from_date, args.rows, direct=True)
                    mode = "live-direct-fallback"
                except URLError as direct_exc:
                    print(f"[ERROR] direct fallback failed: {direct_exc}", file=sys.stderr)
                    print("[HINT] re-run with --offline-sample in restricted environments.", file=sys.stderr)
                    return 1
            elif tunnel_403:
                print(
                    "[HINT] proxy blocked CONNECT tunnel. Try --direct in a direct-egress environment, "
                    "or unset HTTP(S)_PROXY.",
                    file=sys.stderr,
                )
                print("[HINT] re-run with --offline-sample in restricted environments.", file=sys.stderr)
                return 1
            else:
                print("[HINT] re-run with --offline-sample in restricted environments.", file=sys.stderr)
                return 1

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "query": args.query,
        "from_date": args.from_date,
        "count": len(items),
        "items": items,
        "env_proxy": {
            "HTTP_PROXY": bool(os.getenv("HTTP_PROXY") or os.getenv("http_proxy")),
            "HTTPS_PROXY": bool(os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")),
        },
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote {len(items)} records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
