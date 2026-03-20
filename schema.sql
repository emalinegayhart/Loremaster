-- Wowpedia pages table
-- Run this once against your Neon database to create the schema

CREATE TABLE IF NOT EXISTS pages (
    id            SERIAL PRIMARY KEY,
    page_id       TEXT UNIQUE NOT NULL,
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    summary       TEXT,
    content       TEXT,
    last_modified TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups by page_id and title
CREATE INDEX IF NOT EXISTS idx_pages_page_id ON pages(page_id);
CREATE INDEX IF NOT EXISTS idx_pages_title   ON pages(title);
