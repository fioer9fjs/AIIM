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
    estimate_financial_damage,
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


class TestFinancialDamageValuation(unittest.TestCase):
    """
    Unit Tests for Strict Evidence-Only Financial Valuation.
    Ensures zero hallucinated fallbacks, immunity against company valuations & contract sizes,
    and verified extraction of genuine loss/theft/fine amounts.
    """

    def test_unquantified_incident_returns_zero(self):
        # --- ARRANGE ---
        # Incident with no monetary figure mentioned in text
        incident: Dict[str, Any] = {
            "title": "Chatbot Generates Inaccurate Legal Citations in Court Brief",
            "summary": "Attorneys faced disciplinary hearing after citing fictitious cases generated by AI.",
            "severity": "medium",
            "harm_domain": "persons_rights"
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(incident)

        # --- ASSERT ---
        self.assertEqual(usd, 0)
        self.assertEqual(methodology, "unquantified")

    def test_valuation_and_contract_bid_immunity(self):
        # --- ARRANGE ---
        # Incidents mentioning corporate valuations or government contract sizes
        ipo_incident: Dict[str, Any] = {
            "title": "AI Developer Discloses Model Misbehavior in IPO Prospectus",
            "summary": "According to a leaked IPO prospectus, the firm warned of risks. Valued at $42 billion.",
            "financial_damage_usd": 42_000_000_000
        }
        contract_incident: Dict[str, Any] = {
            "title": "Lawsuit over Army AI Hallucination in $450 Million Contract Bid Evaluation",
            "summary": "Contractor claims AI tool malfunctioned during evaluation of a $450 million contract bid.",
            "financial_damage_usd": 450_000_000
        }

        # --- ACT ---
        usd_ipo, meth_ipo = estimate_financial_damage(ipo_incident)
        usd_contract, meth_contract = estimate_financial_damage(contract_incident)

        # --- ASSERT ---
        self.assertEqual(usd_ipo, 0, "Company IPO valuation must not be counted as incident damage.")
        self.assertEqual(meth_ipo, "unquantified")
        self.assertEqual(usd_contract, 0, "Procurement contract bid value must not be counted as incident damage.")
        self.assertEqual(meth_contract, "unquantified")

    def test_fatal_error_keyword_immunity(self):
        # --- ARRANGE ---
        # Technical text containing 'fatal' without loss of life
        code_incident: Dict[str, Any] = {
            "title": "Autonomous Driving Codebase Throws Fatal Exception in Simulation",
            "summary": "Software suffered a fatal error crash during testing; no injuries or real vehicles involved.",
            "severity": "high"
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(code_incident)

        # --- ASSERT ---
        self.assertEqual(usd, 0, "Technical 'fatal error' in code must not trigger VSL fatality benchmark.")
        self.assertEqual(methodology, "unquantified")

    def test_prompt_anchored_2_5m_cleared_when_not_in_text(self):
        # --- ARRANGE ---
        # Incident where LLM hallucinated the 2,500,000 prompt placeholder
        hallucinated_inc: Dict[str, Any] = {
            "title": "Deepfake Impersonation Call Targets Small Business Accounting Desk",
            "summary": "Caller attempted to trick employee into wiring money, but employee verified via phone.",
            "financial_damage_usd": 2_500_000
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(hallucinated_inc)

        # --- ASSERT ---
        self.assertEqual(usd, 0, "Unbacked 2.5M prompt placeholder must be cleared.")
        self.assertEqual(methodology, "unquantified")

    def test_explicit_confirmed_loss_extracted(self):
        # --- ARRANGE ---
        # Real-world incident with explicit theft amount
        theft_incident: Dict[str, Any] = {
            "title": "Deepfake Video Call CFO Impersonation Nets Scammers Millions",
            "summary": "A multinational firm lost $25 million after scammers used deepfake video technology.",
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(theft_incident)

        # --- ASSERT ---
        self.assertEqual(usd, 25_000_000)
        self.assertEqual(methodology, "explicit_confirmed")

    def test_explicit_regulatory_fine_extracted(self):
        # --- ARRANGE ---
        fine_incident: Dict[str, Any] = {
            "title": "Data Protection Authority Penalizes Retailer Over Facial Recognition",
            "summary": "Regulators imposed a fine of $15 million for unconsented biometric monitoring.",
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(fine_incident)

        # --- ASSERT ---
        self.assertEqual(usd, 15_000_000)
        self.assertEqual(methodology, "explicit_confirmed")

    def test_arxiv_preprint_returns_theoretical_academic(self):
        # --- ARRANGE ---
        arxiv_paper: Dict[str, Any] = {
            "title": "Adversarial Jailbreaks in Frontier Language Models",
            "summary": "Researchers demonstrate jailbreak techniques causing theoretical security breaches.",
            "source_type": "arxiv",
            "financial_damage_usd": 5_000_000
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(arxiv_paper)

        # --- ASSERT ---
        self.assertEqual(usd, 0)
        self.assertEqual(methodology, "theoretical_academic")

    def test_macro_statistic_methodology(self):
        # --- ARRANGE ---
        macro_incident: Dict[str, Any] = {
            "title": "Chainalysis Annual Report: Crypto Theft Losses Reach $1.2 Billion",
            "summary": "Industry report details global losses of $1.2 billion across multiple incidents.",
            "impact_scope": "cumulative_macro_trend"
        }

        # --- ACT ---
        usd, methodology = estimate_financial_damage(macro_incident)

        # --- ASSERT ---
        self.assertEqual(usd, 1_200_000_000)
        self.assertEqual(methodology, "macro_statistic")


if __name__ == "__main__":
    unittest.main()
