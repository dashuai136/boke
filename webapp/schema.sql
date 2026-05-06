CREATE TABLE IF NOT EXISTS species (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  scientific_name TEXT NOT NULL,
  authorship TEXT,
  rank TEXT DEFAULT 'species',
  section_name TEXT,
  common_name_zh TEXT,
  taxon_scope TEXT DEFAULT 'new_species',
  status TEXT NOT NULL CHECK(status IN ('candidate','provisional','verified','archived')),
  doi TEXT UNIQUE,
  journal_title TEXT,
  published_on TEXT,
  first_seen_at TEXT,
  entered_at TEXT,
  verified_at TEXT,
  source_confidence REAL,
  abstract_text TEXT,
  diagnosis_text TEXT,
  habitat_text TEXT,
  conservation_status TEXT,
  notes_md TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS external_refs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER NOT NULL,
  provider TEXT NOT NULL,
  provider_id TEXT,
  ref_type TEXT NOT NULL,
  url TEXT NOT NULL,
  is_primary INTEGER DEFAULT 0,
  fetched_at TEXT,
  payload_json TEXT,
  FOREIGN KEY(species_id) REFERENCES species(id)
);

CREATE TABLE IF NOT EXISTS source_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER NOT NULL,
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  source_name TEXT NOT NULL,
  url TEXT,
  pdf_url TEXT,
  doi TEXT,
  publication_date TEXT,
  license_label TEXT,
  rights_note TEXT,
  checksum TEXT,
  FOREIGN KEY(species_id) REFERENCES species(id)
);

CREATE TABLE IF NOT EXISTS media_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER NOT NULL,
  media_role TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  display_policy TEXT NOT NULL CHECK(display_policy IN ('hosted','proxied','linked_only','card_only')),
  original_url TEXT,
  thumb_url TEXT,
  page_ref TEXT,
  caption TEXT,
  alt_text TEXT,
  copyright_owner TEXT,
  license_label TEXT,
  permission_status TEXT NOT NULL CHECK(permission_status IN ('licensed','compatible','unclear','denied')),
  derivative_allowed INTEGER,
  hotlink_allowed INTEGER,
  width INTEGER,
  height INTEGER,
  verified_at TEXT,
  FOREIGN KEY(species_id) REFERENCES species(id)
);

CREATE TABLE IF NOT EXISTS occurrences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER NOT NULL,
  country TEXT,
  admin1 TEXT,
  locality TEXT,
  latitude REAL,
  longitude REAL,
  coordinate_precision_m INTEGER,
  is_type_locality INTEGER,
  source_url TEXT,
  geometry_visibility TEXT NOT NULL CHECK(geometry_visibility IN ('exact','blurred','region_only')),
  FOREIGN KEY(species_id) REFERENCES species(id)
);

CREATE TABLE IF NOT EXISTS submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submitter_name TEXT,
  submitter_email TEXT,
  submitted_name TEXT NOT NULL,
  evidence_urls TEXT,
  message TEXT,
  status TEXT NOT NULL CHECK(status IN ('pending','reviewed','accepted','rejected')),
  assigned_to TEXT,
  review_notes TEXT,
  created_at TEXT,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel TEXT NOT NULL CHECK(channel IN ('email','telegram','wecom','webpush')),
  endpoint TEXT NOT NULL,
  timezone TEXT NOT NULL,
  preferred_hour INTEGER NOT NULL CHECK(preferred_hour BETWEEN 0 AND 23),
  status TEXT NOT NULL CHECK(status IN ('active','paused','unverified')),
  last_sent_at TEXT
);

CREATE TABLE IF NOT EXISTS digests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  business_date TEXT NOT NULL UNIQUE,
  generated_at TEXT,
  item_count INTEGER,
  payload_json TEXT
);

CREATE TABLE IF NOT EXISTS delivery_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  digest_id INTEGER,
  subscription_id INTEGER,
  channel TEXT,
  endpoint TEXT,
  status TEXT,
  error_message TEXT,
  attempt_count INTEGER DEFAULT 0,
  sent_at TEXT,
  created_at TEXT,
  FOREIGN KEY(digest_id) REFERENCES digests(id),
  FOREIGN KEY(subscription_id) REFERENCES subscriptions(id)
);
