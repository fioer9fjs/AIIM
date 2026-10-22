-- ==============================================================================
-- MIGRATION: 20261022_harden_rls_and_columns.sql
-- PURPOSE: Protect full_text column from public PostgREST API exfiltration,
--          restrict daily_source_stats telemetry to service_role,
--          and ensure WITH CHECK clauses on service_role write policies.
-- ==============================================================================

-- 1. Restrict Incidents column-level SELECT: Revoke whole-table SELECT from public
REVOKE SELECT ON TABLE incidents FROM anon, authenticated;

-- 2. Grant SELECT only on public UI columns (excluding full_text)
GRANT SELECT (
    incident_id,
    title,
    summary,
    date,
    verification_status,
    severity,
    source_type,
    financial_damage_usd,
    taxonomy,
    confidence_scores,
    geographic_scope,
    affected_parties,
    source_urls,
    related_incidents,
    created_at
) ON TABLE incidents TO anon, authenticated;

-- 3. Restrict daily_source_stats telemetry table: Remove public read
DROP POLICY IF EXISTS "Allow public read access to daily_source_stats" ON daily_source_stats;
REVOKE SELECT ON TABLE daily_source_stats FROM anon, authenticated;

-- 4. Harden service_role policies with explicit WITH CHECK (true)
DROP POLICY IF EXISTS "Allow service role full access to incidents" ON incidents;
CREATE POLICY "Allow service role full access to incidents" ON incidents FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to edges" ON edges;
CREATE POLICY "Allow service role full access to edges" ON edges FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service role full access to daily_source_stats" ON daily_source_stats;
CREATE POLICY "Allow service role full access to daily_source_stats" ON daily_source_stats FOR ALL TO service_role USING (true) WITH CHECK (true);
