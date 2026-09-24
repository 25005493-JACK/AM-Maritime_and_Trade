-- Supabase SQL Schema for Intelligent Shipping Document Management
-- Run this in your Supabase project: SQL Editor -> New Query -> Run

-- 1. Pipeline Events Table (audit log of pipeline processing runs)
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

-- 4. Durable Processing Jobs Table (persists asynchronous verification state)
CREATE TABLE IF NOT EXISTS public.processing_jobs (
    job_id VARCHAR PRIMARY KEY,
    task_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    progress INTEGER DEFAULT 0,
    email_id VARCHAR,
    shipment_id VARCHAR,
    reviewer_id VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    result_summary JSONB DEFAULT '{}'::jsonb,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_email ON public.processing_jobs(email_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON public.processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_created ON public.processing_jobs(created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES - ZERO ANONYMOUS ACCESS
-- Anonymous users ('anon' role) CANNOT read or write any reviewer records,
-- pipeline events, human overrides, shipment corrections, or processing jobs.
-- Only authenticated reviewers ('authenticated' role) or the backend service role
-- are granted access.
-- ============================================================================

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE public.pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.human_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shipment_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;

-- Clean up any legacy anonymous policies
DROP POLICY IF EXISTS "Allow anon read pipeline_events" ON public.pipeline_events;
DROP POLICY IF EXISTS "Allow anon insert pipeline_events" ON public.pipeline_events;
DROP POLICY IF EXISTS "Allow anon all human_overrides" ON public.human_overrides;
DROP POLICY IF EXISTS "Allow anon all shipment_corrections" ON public.shipment_corrections;
DROP POLICY IF EXISTS "Allow anon all processing_jobs" ON public.processing_jobs;

-- 1. Pipeline Events: Authenticated reviewers can view and record audit events
CREATE POLICY "Authenticated reviewers can read pipeline_events"
    ON public.pipeline_events
    FOR SELECT
    TO authenticated
    USING (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Authenticated reviewers can insert pipeline_events"
    ON public.pipeline_events
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Service role full access pipeline_events"
    ON public.pipeline_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 2. Human Overrides: Authenticated reviewers can view, create, and update overrides
CREATE POLICY "Authenticated reviewers can read human_overrides"
    ON public.human_overrides
    FOR SELECT
    TO authenticated
    USING (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Authenticated reviewers can insert human_overrides"
    ON public.human_overrides
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Authenticated reviewers can update human_overrides"
    ON public.human_overrides
    FOR UPDATE
    TO authenticated
    USING (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated')
    WITH CHECK (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Service role full access human_overrides"
    ON public.human_overrides
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 3. Shipment Corrections: Authenticated reviewers can view and record resolutions
CREATE POLICY "Authenticated reviewers can read shipment_corrections"
    ON public.shipment_corrections
    FOR SELECT
    TO authenticated
    USING (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Authenticated reviewers can insert shipment_corrections"
    ON public.shipment_corrections
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Service role full access shipment_corrections"
    ON public.shipment_corrections
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 4. Processing Jobs: Authenticated reviewers can view and manage processing jobs
CREATE POLICY "Authenticated reviewers can read processing_jobs"
    ON public.processing_jobs
    FOR SELECT
    TO authenticated
    USING (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Authenticated reviewers can insert processing_jobs"
    ON public.processing_jobs
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Authenticated reviewers can update processing_jobs"
    ON public.processing_jobs
    FOR UPDATE
    TO authenticated
    USING (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated')
    WITH CHECK (auth.jwt() ->> 'role' = 'reviewer' OR auth.role() = 'authenticated');

CREATE POLICY "Service role full access processing_jobs"
    ON public.processing_jobs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
