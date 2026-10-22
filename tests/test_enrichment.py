"""
Unit Tests for Incident Taxonomy Enrichment & Classification Guardrails
(scripts/clean_and_enrich_incidents.py)
Following the strict Arrange - Act - Assert (AAA) pattern.
100% self-contained: 0 external network requests, 0 API tokens required.
"""

import unittest
from typing import Dict, Any

from scripts.clean_and_enrich_incidents import (
    assign_compliance_frameworks,
    assign_impact_scope,
    MACRO_KEYWORDS,
)


class TestComplianceFrameworkAssignment(unittest.TestCase):
    """
    Unit Tests for NIST AI RMF 1.0 and ISO/IEC 42001 Category mapping.
    """

    def test_assign_compliance_nist_govern_for_legal_and_fcc(self):
        # --- ARRANGE ---
        # Incident with regulatory/legal enforcement keywords
        incident: Dict[str, Any] = {
            "title": "FCC Issues Enforcement Action and Penalties Against Unauthorized Voice Cloning",
            "summary": "Court settlement concludes policy and legal dispute regarding AI robocalls.",
            "root_cause_category": "governance_policy",
            "harm_type": "regulatory_non_compliance",
        }

        # --- ACT ---
        assign_compliance_frameworks(incident)

        # --- ASSERT ---
        self.assertEqual(incident.get("nist_ai_rmf_function"), "GOVERN")
        self.assertEqual(incident.get("iso_42001_category"), "Internal_Governance")

    def test_assign_compliance_nist_manage_for_cyber_and_autonomous(self):
        # --- ARRANGE ---
        # Incident involving an autonomous agent sandbox escape / breach
        incident: Dict[str, Any] = {
            "title": "Autonomous AI Agent Escalates Privileges and Breaches Corporate Database",
            "summary": "Cyber intrusion exploit allowed agent to bypass sandbox security controls.",
            "system_classification": "autonomous_agent_system",
            "harm_type": "security_breach",
        }

        # --- ACT ---
        assign_compliance_frameworks(incident)

        # --- ASSERT ---
        self.assertEqual(incident.get("nist_ai_rmf_function"), "MANAGE")
        self.assertEqual(incident.get("iso_42001_category"), "Operational_Security")

    def test_assign_compliance_iso_operational_security_and_data(self):
        # --- ARRANGE ---
        # Incident involving copyright and training data infringement
        incident: Dict[str, Any] = {
            "title": "Publishers File Suit Over Proprietary Trade Secret and Copyright Data Scrape",
            "summary": "Allegations of unconsented training on confidential author manuscripts.",
            "root_cause_category": "data_training",
            "harm_type": "intellectual_property_violation",
        }

        # --- ACT ---
        assign_compliance_frameworks(incident)

        # --- ASSERT ---
        self.assertEqual(incident.get("nist_ai_rmf_function"), "MEASURE")
        self.assertEqual(incident.get("iso_42001_category"), "Data_&_Resources")

    def test_assign_compliance_handles_none_and_malformed_gracefully(self):
        # --- ARRANGE ---
        # None and empty records
        empty_record: Dict[str, Any] = {}
        none_record = None

        # --- ACT & ASSERT --- (Must not raise exceptions)
        assign_compliance_frameworks(empty_record)
        assign_compliance_frameworks(none_record)  # type: ignore

        self.assertEqual(empty_record.get("nist_ai_rmf_function"), "MAP")
        self.assertEqual(empty_record.get("iso_42001_category"), "System_Impact")


class TestImpactScopeAssignment(unittest.TestCase):
    """
    Unit Tests for Discrete Incident vs Macro Trend classification (Architectural Invariant #3).
    Ensures that industry-wide annual aggregates do not distort single incident damage figures.
    """

    def test_assign_impact_scope_detects_macro_trend(self):
        # --- ARRANGE ---
        macro_report: Dict[str, Any] = {
            "title": "Chainalysis Annual Report: Global Crypto Theft Reaches $1.2 Billion in 2026",
            "summary": "Industry report details total losses across industry from multiple incidents.",
            "financial_damage_usd": 1_200_000_000,
        }

        # --- ACT ---
        assign_impact_scope(macro_report)

        # --- ASSERT ---
        self.assertEqual(
            macro_report.get("impact_scope"),
            "cumulative_macro_trend",
            "Annual reports and industry-wide totals must be classified as cumulative_macro_trend."
        )

    def test_assign_impact_scope_defaults_to_discrete_incident(self):
        # --- ARRANGE ---
        discrete_case: Dict[str, Any] = {
            "title": "Autonomous Drone Navigation Malfunction Causes Warehouse Collision",
            "summary": "Single delivery quadcopter crashed into logistics rack in Berlin facility.",
            "financial_damage_usd": 450_000,
        }

        # --- ACT ---
        assign_impact_scope(discrete_case)

        # --- ASSERT ---
        self.assertEqual(
            discrete_case.get("impact_scope"),
            "discrete_incident",
            "Single discrete events must be classified as discrete_incident."
        )


if __name__ == "__main__":
    unittest.main()
