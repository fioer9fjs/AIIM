"""
Generates rich seed dataset of realistic AI incidents and Knowledge Graph edges
conforming to the academic/regulatory taxonomy. Output is saved to JSON for the web UI.
"""

import json
import os
from datetime import datetime, timedelta

INCIDENTS_SEED = [
    {
        "incident_id": "INC-2026-001",
        "title": "Autonomous Fleet Software Update Causes Emergency Braking Glitch on Highways",
        "summary": "An over-the-air model update for autonomous robo-taxis caused phantom emergency braking triggers at high speeds across major transit corridors.",
        "date": "2026-08-02",
        "verification_status": "confirmed",
        "lifecycle_phase": "deployment_and_integration",
        "system_classification": "autonomous_agent",
        "root_cause_category": "model",
        "root_cause_subtype": "robustness_failure",
        "failure_mode": "Edge-case optical reflection under direct sunlight tricked perception model into identifying non-existent obstacles.",
        "harm_domain": "persons_physical",
        "temporality": "actual",
        "severity": "critical",
        "confidence_scores": {
            "verification_status": 1.0,
            "lifecycle_phase": 0.95,
            "system_classification": 0.98,
            "root_cause_category": 0.90,
            "harm_domain": 0.99,
            "severity": 0.95
        },
        "geographic_scope": ["United States", "Germany"],
        "affected_parties": ["WayNav Autonomous Systems", "Highway Transportation Board"],
        "source_urls": ["https://news.example.com/autotaxi-braking-glitch-2026"],
        "related_incidents": []
    },
    {
        "incident_id": "INC-2026-002",
        "title": "Regulatory Fine Issued After Fleet Braking Investigation Confirms Sensor Fusion Flaw",
        "summary": "National Highway Traffic Safety Regulators fined WayNav $15M following investigation into phantom braking software defect, ordering recall of software v4.2.",
        "date": "2026-08-10",
        "verification_status": "confirmed",
        "lifecycle_phase": "operation_and_monitoring",
        "system_classification": "autonomous_agent",
        "root_cause_category": "governance",
        "root_cause_subtype": "inadequate_monitoring",
        "failure_mode": "Safety monitoring failed to catch regression during pre-deployment simulation cycles.",
        "harm_domain": "systemic_integrity",
        "temporality": "actual",
        "severity": "high",
        "confidence_scores": {
            "verification_status": 1.0,
            "lifecycle_phase": 0.92,
            "system_classification": 0.95,
            "root_cause_category": 0.88,
            "harm_domain": 0.90,
            "severity": 0.92
        },
        "geographic_scope": ["United States"],
        "affected_parties": ["WayNav Autonomous Systems", "NHTSA"],
        "source_urls": ["https://news.example.com/waynav-nhtsa-fine-investigation"],
        "related_incidents": ["INC-2026-001"]
    },
    {
        "incident_id": "INC-2026-003",
        "title": "LLM Customer Service Bot Tricked Into Executing Unauthorized Refunds via Indirect Prompt Injection",
        "summary": "Attackers embedded white-text instructions in uploaded PDF invoices that caused an enterprise AI agent to bypass transaction limits and issue unauthorized refund credits.",
        "date": "2026-07-28",
        "verification_status": "confirmed",
        "lifecycle_phase": "operation_and_monitoring",
        "system_classification": "general_purpose_model",
        "root_cause_category": "external",
        "root_cause_subtype": "adversarial_attack",
        "failure_mode": "Lack of input sanitization between untrusted document payload and agent execution framework.",
        "harm_domain": "property",
        "temporality": "actual",
        "severity": "high",
        "confidence_scores": {
            "verification_status": 0.98,
            "lifecycle_phase": 0.90,
            "system_classification": 0.95,
            "root_cause_category": 0.96,
            "harm_domain": 0.95,
            "severity": 0.89
        },
        "geographic_scope": ["United Kingdom", "EU"],
        "affected_parties": ["OmniPay Solutions", "Retail Global Inc"],
        "source_urls": ["https://cybersecurity.example.org/prompt-injection-refund-bypass"],
        "related_incidents": []
    },
    {
        "incident_id": "INC-2026-004",
        "title": "Automated Hiring Screening System Penalized Older Applicants Due to Training Data Shift",
        "summary": "An automated candidate ranking tool used by major tech recruiters consistently down-scored resumes with graduation dates prior to 2012.",
        "date": "2026-06-14",
        "verification_status": "confirmed",
        "lifecycle_phase": "deployment_and_integration",
        "system_classification": "high_risk_regulated",
        "root_cause_category": "data",
        "root_cause_subtype": "bias",
        "failure_mode": "Historical hiring dataset reflected ageist bias in previous tenure records, which was amplified during model optimization.",
        "harm_domain": "persons_rights",
        "temporality": "actual",
        "severity": "high",
        "confidence_scores": {
            "verification_status": 0.99,
            "lifecycle_phase": 0.91,
            "system_classification": 0.98,
            "root_cause_category": 0.95,
            "harm_domain": 0.97,
            "severity": 0.91
        },
        "geographic_scope": ["United States"],
        "affected_parties": ["TalentAI Corp", "EEOC"],
        "source_urls": ["https://lawandtech.example.org/talentai-age-discrimination-finding"],
        "related_incidents": []
    },
    {
        "incident_id": "INC-2026-005",
        "title": "Generative Audio Deepfake Used in High-Profile Financial Fraud Scheme",
        "summary": "Criminals cloned the voice of a corporate CFO in real-time during a confidential web call, tricking financial operations into transferring $4.2M to fraudulent accounts.",
        "date": "2026-08-05",
        "verification_status": "confirmed",
        "lifecycle_phase": "operation_and_monitoring",
        "system_classification": "dual_use_security",
        "root_cause_category": "human",
        "root_cause_subtype": "intentional_misuse",
        "failure_mode": "Malicious actors leveraged zero-shot voice synthesis to impersonate executive authority.",
        "harm_domain": "property",
        "temporality": "actual",
        "severity": "critical",
        "confidence_scores": {
            "verification_status": 0.99,
            "lifecycle_phase": 0.90,
            "system_classification": 0.92,
            "root_cause_category": 0.97,
            "harm_domain": 0.98,
            "severity": 0.96
        },
        "geographic_scope": ["Singapore", "Hong Kong"],
        "affected_parties": ["Global Capital Partners", "Interpol AI Taskforce"],
        "source_urls": ["https://fin-security.example.com/audio-deepfake-ceo-scam-2026"],
        "related_incidents": []
    },
    {
        "incident_id": "INC-2026-006",
        "title": "Medical Imaging Assistant Hallucinated Non-Existent Lesions on Synthetic Ultrasound Scans",
        "summary": "An AI diagnostic assistant evaluated synthetic ultrasound artifacts as malignant tumors, resulting in unnecessary invasive biopsies prior to audit discovery.",
        "date": "2026-07-11",
        "verification_status": "confirmed",
        "lifecycle_phase": "operation_and_monitoring",
        "system_classification": "high_risk_regulated",
        "root_cause_category": "model",
        "root_cause_subtype": "hallucination",
        "failure_mode": "Distribution shift between training dataset noise patterns and real scanner calibration values led to high-confidence false positive detections.",
        "harm_domain": "persons_physical",
        "temporality": "actual",
        "severity": "critical",
        "confidence_scores": {
            "verification_status": 0.97,
            "lifecycle_phase": 0.94,
            "system_classification": 0.99,
            "root_cause_category": 0.93,
            "harm_domain": 0.98,
            "severity": 0.97
        },
        "geographic_scope": ["France", "Germany"],
        "affected_parties": ["MediScan Diagnostic AI", "European Medical Devices Agency"],
        "source_urls": ["https://healthtech.example.org/mediscan-hallucination-audit"],
        "related_incidents": []
    },
    {
        "incident_id": "INC-2026-007",
        "title": "MediScan Deploys Corrective Patch & Enhanced Safety Thresholds Following Biopsy Audit",
        "summary": "MediScan Diagnostic released v3.1 update featuring human-in-the-loop validation mandatory gating for all anomaly scores below 0.98.",
        "date": "2026-08-01",
        "verification_status": "confirmed",
        "lifecycle_phase": "operation_and_monitoring",
        "system_classification": "high_risk_regulated",
        "root_cause_category": "governance",
        "root_cause_subtype": "inadequate_monitoring",
        "failure_mode": "Remediation patch released to mandate physician dual-signoff on AI recommendations.",
        "harm_domain": "systemic_integrity",
        "temporality": "potential",
        "severity": "low",
        "confidence_scores": {
            "verification_status": 1.0,
            "lifecycle_phase": 0.95,
            "system_classification": 0.99,
            "root_cause_category": 0.89,
            "harm_domain": 0.92,
            "severity": 0.90
        },
        "geographic_scope": ["EU"],
        "affected_parties": ["MediScan Diagnostic AI"],
        "source_urls": ["https://healthtech.example.org/mediscan-v31-patch-release"],
        "related_incidents": ["INC-2026-006"]
    }
]

GRAPH_EDGES_SEED = [
    {
        "edge_id": "EDGE-001",
        "source_id": "INC-2026-002",
        "target_id": "INC-2026-001",
        "relation_type": "lawsuit",
        "description": "NHTSA regulatory investigation & fine resulting from the autonomous braking glitch.",
        "confidence": 0.98
    },
    {
        "edge_id": "EDGE-002",
        "source_id": "INC-2026-007",
        "target_id": "INC-2026-006",
        "relation_type": "mitigation_patch",
        "description": "MediScan deployed corrective software patch v3.1 following the medical hallucination audit.",
        "confidence": 0.99
    }
]

def generate_dataset():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    incidents_path = os.path.join(output_dir, "incidents.json")
    edges_path = os.path.join(output_dir, "edges.json")
    
    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(INCIDENTS_SEED, f, indent=2)
        
    with open(edges_path, "w", encoding="utf-8") as f:
        json.dump(GRAPH_EDGES_SEED, f, indent=2)
        
    print(f"Successfully generated seed data at {output_dir}")

if __name__ == "__main__":
    generate_dataset()
