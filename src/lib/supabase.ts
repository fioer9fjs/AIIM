import { createClient } from '@supabase/supabase-js';
import { AIIncident, GraphEdge } from '../types/incident';

// Read Vercel / Vite environment variables (Modern Publishable Key with Legacy fallback)
const metaEnv = (import.meta as unknown as { env?: Record<string, string> }).env || {};
const supabaseUrl = metaEnv.VITE_SUPABASE_URL || metaEnv.SUPABASE_URL || '';
const supabaseKey = metaEnv.VITE_SUPABASE_PUBLISHABLE_KEY || metaEnv.VITE_SUPABASE_ANON_KEY || metaEnv.SUPABASE_PUBLISHABLE_KEY || metaEnv.SUPABASE_ANON_KEY || '';

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseKey)
  : null;

/**
 * Fetches all incidents live from Supabase PostgreSQL database.
 * SECURITY & PERFORMANCE FIX: Explicitly selects lightweight UI columns,
 * leaving raw article full_text protected inside PostgreSQL.
 */
export async function fetchIncidentsFromSupabase(): Promise<AIIncident[]> {
  if (!supabase) return [];

  const { data, error } = await supabase
    .from('incidents')
    .select('incident_id, title, summary, date, verification_status, severity, source_type, financial_damage_usd, taxonomy, confidence_scores, geographic_scope, affected_parties, source_urls, related_incidents')
    .order('date', { ascending: false });

  if (error || !data) {
    console.error('Error fetching incidents from Supabase:', error);
    return [];
  }

  return data.map((row) => ({
    incident_id: row.incident_id,
    title: row.title,
    summary: row.summary,
    date: row.date,
    verification_status: row.verification_status || 'confirmed',
    severity: row.severity || 'medium',
    source_type: row.source_type || row.taxonomy?.source_type || 'google_news_rss',
    financial_damage_usd: row.financial_damage_usd ?? row.taxonomy?.financial_damage_usd ?? 0,
    lifecycle_phase: row.taxonomy?.lifecycle_phase || 'operation_and_monitoring',
    system_classification: row.taxonomy?.system_classification || 'general_purpose_model',
    root_cause_category: row.taxonomy?.root_cause_category || 'governance',
    root_cause_subtype: row.taxonomy?.root_cause_subtype || '',
    failure_mode: row.taxonomy?.failure_mode || '',
    harm_domain: row.taxonomy?.harm_domain || 'persons_rights',
    temporality: row.taxonomy?.temporality || 'actual',
    
    // MIT & AIID Extended fields from JSONB
    impact_scope: row.taxonomy?.impact_scope || (row as Record<string, any>).impact_scope || 'discrete_incident',
    valuation_methodology: row.taxonomy?.valuation_methodology || (row as Record<string, any>).valuation_methodology,
    intent: row.taxonomy?.intent,
    primary_purpose: row.taxonomy?.primary_purpose,
    harm_type: row.taxonomy?.harm_type,
    eu_ai_act_tier: row.taxonomy?.eu_ai_act_tier,
    natsec_impact: row.taxonomy?.natsec_impact,

    confidence_scores: row.confidence_scores || {
      verification_status: 0.95,
      lifecycle_phase: 0.90,
      system_classification: 0.95,
      root_cause_category: 0.90,
      harm_domain: 0.95,
      severity: 0.90
    },
    geographic_scope: row.geographic_scope || [],
    affected_parties: row.affected_parties || [],
    source_urls: row.source_urls || [],
    related_incidents: row.related_incidents || []
  }));
}

/**
 * Fetches Knowledge Graph edges live from Supabase.
 */
export async function fetchEdgesFromSupabase(): Promise<GraphEdge[]> {
  if (!supabase) return [];

  const { data, error } = await supabase
    .from('edges')
    .select('edge_id, source_id, target_id, relation_type, description, confidence');

  if (error || !data) {
    console.error('Error fetching Knowledge Graph edges from Supabase:', error);
    return [];
  }

  return data.map((row) => ({
    edge_id: row.edge_id,
    source_id: row.source_id,
    target_id: row.target_id,
    relation_type: row.relation_type || 'related_cause',
    description: row.description || '',
    confidence: Number(row.confidence) || 0.90
  }));
}
