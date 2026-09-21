-- Supabase SQL Schema for Intelligent Shipping Document Management
-- Run this in your Supabase project: SQL Editor -> New Query -> Run

-- 1. Pipeline Events Table (replaces local DuckDB pipeline_events)
CREATE TABLE IF NOT EXISTS public.pipeline_events (
    event_id VARCHAR PRIMARY KEY,
    shipment_id VARCHAR,
    email_id VARCHAR,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    category VARCHAR,
    classification_confidence FLOAT,
    extraction_tier VARCHAR,
    anchor_triage_outcome VARCHAR,
    anchor_triage_reason VARCHAR,
    comparison_status VARCHAR,
    review_reason TEXT,
    defect_fields TEXT,
    cache_hit_si BOOLEAN DEFAULT FALSE,
    cache_hit_bl BOOLEAN DEFAULT FALSE,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying by email or shipment
CREATE INDEX IF NOT EXISTS idx_pipeline_events_email ON public.pipeline_events(email_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_shipment ON public.pipeline_events(shipment_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_timestamp ON public.pipeline_events(timestamp DESC);

-- 2. Human Overrides Table (persists manual reviewer corrections across restarts)
CREATE TABLE IF NOT EXISTS public.human_overrides (
    email_id VARCHAR PRIMARY KEY,
    reviewer_name VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    si_overrides JSONB DEFAULT '{}'::jsonb,
    bl_overrides JSONB DEFAULT '{}'::jsonb,
    corrections JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. DCSA Shipment Corrections Table (replaces local corrections.csv)
CREATE TABLE IF NOT EXISTS public.shipment_corrections (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    email_id VARCHAR NOT NULL,
    field VARCHAR NOT NULL,
    dcsa_field VARCHAR,
    original_value TEXT,
    corrected_value TEXT,
    resolution VARCHAR,
    reviewer VARCHAR,
    evidence_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_corrections_email ON public.shipment_corrections(email_id);
CREATE INDEX IF NOT EXISTS idx_corrections_dcsa_field ON public.shipment_corrections(dcsa_field);

-- Enable Row Level Security (RLS)
ALTER TABLE public.pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.human_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shipment_corrections ENABLE ROW LEVEL SECURITY;

-- Allow read & write access
DROP POLICY IF EXISTS "Allow anon read pipeline_events" ON public.pipeline_events;
CREATE POLICY "Allow anon read pipeline_events" ON public.pipeline_events FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow anon insert pipeline_events" ON public.pipeline_events;
CREATE POLICY "Allow anon insert pipeline_events" ON public.pipeline_events FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon all human_overrides" ON public.human_overrides;
CREATE POLICY "Allow anon all human_overrides" ON public.human_overrides FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon all shipment_corrections" ON public.shipment_corrections;
CREATE POLICY "Allow anon all shipment_corrections" ON public.shipment_corrections FOR ALL USING (true) WITH CHECK (true);
