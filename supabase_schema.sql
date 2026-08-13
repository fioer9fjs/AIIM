-- ==============================================================================
-- GLOBAL AI INCIDENT MONITOR - SUPABASE POSTGRESQL SCHEMA
-- Supports 100% free hosting with hybrid JSONB columns for 0-friction schema expansion
-- ==============================================================================

-- 1. Create Core Incidents Table
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    full_text TEXT,
    date DATE NOT NULL,
    verification_status TEXT,
    severity TEXT,
    
    -- Data Provider Origin Telemetry (RSS, GDELT, ArXiv, AIID)
    source_type TEXT DEFAULT 'google_news_rss',
    
    -- Hybrid JSONB Column for flexible taxonomy metadata (MIT, AIID, CSET, EU AI Act, NatSec)
    taxonomy JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    confidence_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    geographic_scope TEXT[] DEFAULT '{}',
    affected_parties TEXT[] DEFAULT '{}',
    source_urls TEXT[] DEFAULT '{}',
    related_incidents TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure source_type column exists if table was created previously
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'google_news_rss';

-- 2. Create Knowledge Graph Edges Table
CREATE TABLE IF NOT EXISTS edges (
    edge_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    description TEXT,
    confidence NUMERIC DEFAULT 0.90,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create Daily Source Telemetry & Ingestion Statistics Table
CREATE TABLE IF NOT EXISTS daily_source_stats (
    stat_date DATE PRIMARY KEY,
    rss_count INTEGER DEFAULT 0,
    gdelt_count INTEGER DEFAULT 0,
    arxiv_count INTEGER DEFAULT 0,
    aiid_count INTEGER DEFAULT 0,
    total_fetched INTEGER DEFAULT 0,
    passed_filter INTEGER DEFAULT 0,
    extracted_incidents INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_source_stats ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS Policies for Public Read & Service Role Write
CREATE POLICY "Allow public read access to incidents" ON incidents
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to edges" ON edges
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to daily_source_stats" ON daily_source_stats
    FOR SELECT USING (true);

CREATE POLICY "Allow service role full access to incidents" ON incidents
    FOR ALL USING (true);

CREATE POLICY "Allow service role full access to edges" ON edges
    FOR ALL USING (true);

CREATE POLICY "Allow service role full access to daily_source_stats" ON daily_source_stats
    FOR ALL USING (true);

-- 6. Create Performance Indexes for Fast Searching & Sorting
CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(date DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_source_type ON incidents(source_type);
CREATE INDEX IF NOT EXISTS idx_incidents_taxonomy_gin ON incidents USING GIN (taxonomy);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
