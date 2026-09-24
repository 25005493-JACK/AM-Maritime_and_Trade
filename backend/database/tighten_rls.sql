-- =============================================================================
-- DocuMatch Migration: Tighten Supabase Row Level Security (RLS)
-- Phase 6: Security and Claims Hardening
-- =============================================================================

-- 1. Enable Row Level Security on all sensitive operational tables
ALTER TABLE IF EXISTS pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS human_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS shipment_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_reflections ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS routing_policy ENABLE ROW LEVEL SECURITY;

-- 2. Revoke all default permissions from anonymous role
REVOKE ALL ON TABLE pipeline_events FROM anon;
REVOKE ALL ON TABLE human_overrides FROM anon;
REVOKE ALL ON TABLE shipment_corrections FROM anon;
REVOKE ALL ON TABLE agent_reflections FROM anon;
REVOKE ALL ON TABLE routing_policy FROM anon;

-- 3. Human Overrides: Only authenticated reviewers can read or insert/update overrides
DROP POLICY IF EXISTS "Authenticated reviewers can read overrides" ON human_overrides;
CREATE POLICY "Authenticated reviewers can read overrides"
    ON human_overrides
    FOR SELECT
    TO authenticated
    USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Authenticated reviewers can upsert overrides" ON human_overrides;
CREATE POLICY "Authenticated reviewers can upsert overrides"
    ON human_overrides
    FOR ALL
    TO authenticated
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

-- 4. Pipeline Events: Authenticated audit read and append-only logging
DROP POLICY IF EXISTS "Authenticated operators can view timeline events" ON pipeline_events;
CREATE POLICY "Authenticated operators can view timeline events"
    ON pipeline_events
    FOR SELECT
    TO authenticated
    USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Authenticated services can append timeline events" ON pipeline_events;
CREATE POLICY "Authenticated services can append timeline events"
    ON pipeline_events
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.role() = 'authenticated');

-- 5. Shipment Corrections: Restricted to authorized human review sessions
DROP POLICY IF EXISTS "Authenticated reviewers can read corrections" ON shipment_corrections;
CREATE POLICY "Authenticated reviewers can read corrections"
    ON shipment_corrections
    FOR SELECT
    TO authenticated
    USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Authenticated reviewers can record corrections" ON shipment_corrections;
CREATE POLICY "Authenticated reviewers can record corrections"
    ON shipment_corrections
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.role() = 'authenticated');
