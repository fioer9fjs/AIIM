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

export type RelationType = 
  | 'follow_up'
  | 'lawsuit'
  | 'mitigation_patch'
  | 'official_rebuttal'
  | 'related_cause';

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
  date: string;
  verification_status: VerificationStatus;
  lifecycle_phase: LifecyclePhase;
  system_classification: SystemClassification;
  root_cause_category: RootCauseCategory;
  root_cause_subtype?: string;
  failure_mode?: string;
  harm_domain: HarmDomain;
  temporality: Temporality;
  severity: Severity;
  confidence_scores: ConfidenceScores;
  geographic_scope: string[];
  affected_parties: string[];
  source_urls: string[];
  related_incidents: string[];
}

export interface GraphEdge {
  edge_id: string;
  source_id: string;
  target_id: string;
  relation_type: RelationType;
  description: string;
  confidence: number;
}
