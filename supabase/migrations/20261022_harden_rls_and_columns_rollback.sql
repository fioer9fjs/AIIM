-- ==============================================================================
-- ROLLBACK: 20261022_harden_rls_and_columns_rollback.sql
-- PURPOSE: Restores whole-table SELECT on incidents and public read on daily_source_stats
-- ==============================================================================

-- 1. Restore whole-table SELECT on incidents
GRANT SELECT ON TABLE incidents TO anon, authenticated;

-- 2. Restore public SELECT on daily_source_stats
GRANT SELECT ON TABLE daily_source_stats TO anon, authenticated;
DROP POLICY IF EXISTS "Allow public read access to daily_source_stats" ON daily_source_stats;
CREATE POLICY "Allow public read access to daily_source_stats" ON daily_source_stats FOR SELECT USING (true);
