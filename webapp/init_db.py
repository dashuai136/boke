from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "begonia.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def run() -> None:
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    now = datetime.now(timezone.utc).isoformat()

    species_seed = [
        {
            "slug": "begonia-antoi",
            "scientific_name": "Begonia antoi",
            "authorship": "Rezeki, Mustaqim, Girm. & Ardi",
            "section_name": "Jackia",
            "status": "verified",
            "doi": "10.6165/tai.2025.70.470",
            "journal_title": "Taiwania",
            "published_on": "2025-07-13",
            "entered_at": now,
            "source_confidence": 92.5,
            "abstract_text": "A new species of Begonia from Indonesia.",
        },
        {
            "slug": "begonia-kalimantanensis",
            "scientific_name": "Begonia kalimantanensis",
            "authorship": "Author et al.",
            "section_name": "Petermannia",
            "status": "provisional",
            "doi": None,
            "journal_title": "Phytotaxa",
            "published_on": "2026-04-05",
            "entered_at": now,
            "source_confidence": 75.0,
            "abstract_text": "Candidate from Kalimantan.",
        },
    ]

    for s in species_seed:
        conn.execute(
            """
            INSERT OR IGNORE INTO species(
              slug, scientific_name, authorship, section_name, status, doi,
              journal_title, published_on, entered_at, source_confidence, abstract_text, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                s["slug"],
                s["scientific_name"],
                s["authorship"],
                s["section_name"],
                s["status"],
                s["doi"],
                s["journal_title"],
                s["published_on"],
                s["entered_at"],
                s["source_confidence"],
                s["abstract_text"],
                now,
                now,
            ),
        )

    row = conn.execute("SELECT id FROM species WHERE slug='begonia-antoi'").fetchone()
    if row:
        species_id = row[0]
        conn.execute(
            """
            INSERT OR IGNORE INTO source_documents(
              species_id, source_type, title, source_name, url, pdf_url, doi,
              publication_date, license_label, rights_note, checksum
            ) VALUES (?, 'article', ?, 'Taiwania', ?, ?, ?, ?, 'CC BY-NC-ND', 'linked_only', ?)
            """,
            (
                species_id,
                "A new species of Begonia ...",
                "https://www.taiwaniajournal.org/",
                "https://www.taiwaniajournal.org/pdf",
                "10.6165/tai.2025.70.470",
                "2025-07-13",
                "seed-antoi-001",
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO media_assets(
              species_id, media_role, source_kind, display_policy, original_url,
              page_ref, caption, permission_status, license_label
            ) VALUES (?, 'plate', 'pdf_page', 'linked_only', ?, 'p.321 Fig.1', ?, 'unclear', 'CC BY-NC-ND')
            """,
            (
                species_id,
                "https://www.taiwaniajournal.org/pdf",
                "Habitat and morphology",
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO occurrences(
              species_id, country, admin1, locality, latitude, longitude,
              coordinate_precision_m, is_type_locality, source_url, geometry_visibility
            ) VALUES (?, 'Indonesia', 'Aceh', 'Bener Meriah', 4.7221, 96.8332, 5000, 1, ?, 'blurred')
            """,
            (species_id, "https://www.taiwaniajournal.org/"),
        )

    conn.execute(
        "INSERT OR IGNORE INTO subscriptions(channel, endpoint, timezone, preferred_hour, status) VALUES ('email','demo@example.org','Asia/Shanghai',8,'active')"
    )
    conn.commit()
    conn.close()
    print(f"[OK] initialized {DB_PATH}")


if __name__ == "__main__":
    run()
