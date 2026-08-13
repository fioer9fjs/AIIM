# Global AI Incident Monitor & Knowledge Graph

A fully automated, zero-maintenance web platform designed to continuously track, analyze, and visualize global AI safety, security, governance, and operational incidents over time.

## Architectural Overview

- **Data Ingestion**: Daily automated fetch from GDELT, Google News RSS, and AI safety databases.
- **LLM Pipeline**: Powered by **Gemini 2.5 Flash** for taxonomy extraction, confidence scoring, entity recognition, and semantic deduplication/linking into a Knowledge Graph.
- **Taxonomy**: Custom academic and regulatory classification aligning with the EU AI Act, OECD AI Incident taxonomy, and MIT Causal Taxonomy.
- **Frontend**: Multi-view dashboard featuring an **Interactive Knowledge Graph (Network View)**, **Filterable Incident Explorer (Table View)**, and **Analytics & Metrics Dashboard**.
- **Hosting**: 100% Free-Tier deployment target (Vercel / GitHub Actions / Supabase / Google AI Studio).

## Taxonomy Summary

### 1. Event
- `verification_status`: `alleged` | `confirmed` | `disputed`
- `lifecycle_phase`: `design_and_training` | `testing_and_validation` | `deployment_and_integration` | `operation_and_monitoring` | `decommissioning`
- `system_classification`: `high_risk_regulated` | `general_purpose_model` | `autonomous_agent` | `biometric_identification` | `critical_infrastructure_component` | `dual_use_security` | `unclassified`

### 2. Mechanism
- `root_cause_category`: `data` | `model` | `human` | `governance` | `external` | `undetermined`
- `root_cause_subtype`: Specific failure mechanism (e.g. `hallucination`, `poisoning`, `adversarial_attack`)
- `failure_mode`: Narrative connecting cause to consequence

### 3. Consequence
- `harm_domain`: `persons_physical` | `persons_mental` | `persons_rights` | `property` | `environment` | `systemic_integrity` | `societal`
- `temporality`: `actual` | `potential` | `latent`
- `severity`: `critical` | `high` | `medium` | `low`

## Directory Structure

```
.
├── .github/workflows/daily_ingest.yml # Automated daily ingestion workflow
├── scripts/
│   ├── taxonomy.py                    # Python taxonomy definitions & validators
│   ├── ingest.py                      # Automated news scraper & Gemini Flash pipeline
│   └── mock_data_generator.py         # Seed dataset generator
├── src/
│   ├── components/                    # React components (Graph, Explorer, Analytics)
│   ├── data/                          # Incident dataset & Knowledge Graph edges
│   ├── types/                         # TypeScript interfaces & taxonomy schemas
│   └── App.tsx                        # Main application container
└── README.md
```
