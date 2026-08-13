export type VerificationStatus = 'alleged' | 'confirmed' | 'disputed';

export type LifecyclePhase =
  | 'design_and_training'
  | 'testing_and_validation'
  | 'deployment_and_integration'
  | 'operation_and_monitoring'
  | 'decommissioning';

export type SystemClassification =
  | 'high_risk_regulated'
  | 'general_purpose_model'
  | 'autonomous_agent'
  | 'biometric_identification'
  | 'critical_infrastructure_component'
  | 'dual_use_security'
  | 'unclassified';

export type RootCauseCategory =
  | 'data'
  | 'model'
  | 'human'
  | 'governance'
  | 'external'
  | 'undetermined';

export type HarmDomain =
  | 'persons_physical'
  | 'persons_mental'
  | 'persons_rights'
  | 'property'
  | 'environment'
  | 'systemic_integrity'
  | 'societal';

export type Temporality = 'actual' | 'potential' | 'latent';

export type Severity = 'critical' | 'high' | 'medium' | 'low';

// MIT & AIID Taxonomy Additions
export type IncidentIntent = 'intentional_misuse' | 'unintentional_failure';

export type PrimaryPurpose =
  | 'generative_content'
  | 'autonomous_mobility'
  | 'biometric_surveillance'
  | 'financial_fintech'
  | 'healthcare_medical'
  | 'recruitment_hr'
  | 'defense_national_security'
  | 'content_recommendation'
  | 'other';

export type HarmType =
  | 'discrimination_bias'
  | 'privacy_breach'
  | 'physical_safety'
  | 'misinformation'
  | 'economic_labor'
  | 'copyright_ip'
  | 'psychological_harm'
  | 'national_security';

export type EUAIActTier = 'prohibited' | 'high_risk' | 'limited_risk' | 'minimal_risk';

export interface ConfidenceScores {
  verification_status: number;
  lifecycle_phase: number;
  system_classification: number;
  root_cause_category: number;
  harm_domain: number;
  severity: number;
}

export interface AIIncident {
  incident_id: string;
  title: string;
  summary: string;
  full_text?: string;
  date: string;
  verification_status: VerificationStatus;
  lifecycle_phase: LifecyclePhase;
  system_classification: SystemClassification;
  root_cause_category: RootCauseCategory;
  root_cause_subtype: string;
  failure_mode: string;
  harm_domain: HarmDomain;
  temporality: Temporality;
  severity: Severity;
  
  // MIT & AIID Extensions
  intent?: IncidentIntent;
  primary_purpose?: PrimaryPurpose;
  harm_type?: HarmType;
  eu_ai_act_tier?: EUAIActTier;
  natsec_impact?: boolean;

  confidence_scores: ConfidenceScores;
  geographic_scope: string[];
  affected_parties: string[];
  source_urls: string[];
  related_incidents: string[];
}

export interface GraphNode {
  id: string;
  title: string;
  severity: Severity;
  harm_domain: HarmDomain;
}

export interface GraphEdge {
  edge_id: string;
  source_id: string;
  target_id: string;
  relation_type: 'lawsuit' | 'regulatory_action' | 'patch' | 'fork' | 'related_cause';
  description: string;
  confidence: number;
}
