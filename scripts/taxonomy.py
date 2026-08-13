"""
Taxonomy Definitions and Schema Validation for Global AI Incident Monitor.
Matches the EU AI Act, OECD AI Incident taxonomy, and MIT Causal Taxonomy.
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime

# Verification Status
VerificationStatus = Literal["alleged", "confirmed", "disputed"]

# Lifecycle Phase
LifecyclePhase = Literal[
    "design_and_training",
    "testing_and_validation",
    "deployment_and_integration",
    "operation_and_monitoring",
    "decommissioning"
]

# System Classification
SystemClassification = Literal[
    "high_risk_regulated",
    "general_purpose_model",
    "autonomous_agent",
    "biometric_identification",
    "critical_infrastructure_component",
    "dual_use_security",
    "unclassified"
]

# Root Cause Category (MIT Causal Taxonomy)
RootCauseCategory = Literal[
    "data",
    "model",
    "human",
    "governance",
    "external",
    "undetermined"
]

# Harm Domain (OECD Taxonomy)
HarmDomain = Literal[
    "persons_physical",
    "persons_mental",
    "persons_rights",
    "property",
    "environment",
    "systemic_integrity",
    "societal"
]

# Temporality
Temporality = Literal["actual", "potential", "latent"]

# Severity
Severity = Literal["critical", "high", "medium", "low"]

# Edge / Connection Relation Types
RelationType = Literal[
    "follow_up",
    "lawsuit",
    "mitigation_patch",
    "official_rebuttal",
    "related_cause"
]

@dataclass
class ConfidenceScores:
    verification_status: float = 1.0
    lifecycle_phase: float = 1.0
    system_classification: float = 1.0
    root_cause_category: float = 1.0
    harm_domain: float = 1.0
    severity: float = 1.0

@dataclass
class AIIncident:
    incident_id: str
    title: str
    summary: str
    date: str  # ISO format string YYYY-MM-DD
    verification_status: VerificationStatus
    lifecycle_phase: LifecyclePhase
    system_classification: SystemClassification
    root_cause_category: RootCauseCategory
    root_cause_subtype: Optional[str] = None
    failure_mode: Optional[str] = None
    harm_domain: HarmDomain = "societal"
    temporality: Temporality = "actual"
    severity: Severity = "medium"
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    geographic_scope: List[str] = field(default_factory=list)
    affected_parties: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    related_incidents: List[str] = field(default_factory=list) # Linked parent/child IDs

@dataclass
class KnowledgeGraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    description: str
    confidence: float = 1.0
