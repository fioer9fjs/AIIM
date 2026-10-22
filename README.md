# Global AI Incident Monitor & Knowledge Graph

A fully automated, zero-maintenance web platform designed to continuously harvest, analyze, classify, and visualize global AI safety, security, governance, and operational incidents in real time.

[![Live Web Application](https://img.shields.io/badge/Vercel-Live%20App-brightgreen?style=flat&logo=vercel)](https://aiim-eight.vercel.app/)
[![Database](https://img.shields.io/badge/Supabase-PostgreSQL-blue?style=flat&logo=supabase)](https://supabase.com)
[![AI Engine](https://img.shields.io/badge/Google%20GenAI-Gemma%204%20%2F%20Gemini%203.6-orange?style=flat&logo=google)](https://ai.google.dev)

---

## 🏛️ System Architecture & Data Flow

```text
[ Data Ingestion ] ──────> [ AI Pipeline (Gemma 4 / Gemini 3.6) ] ──────> [ Supabase PostgreSQL ] ──────> [ Multi-View React App ]
• GDELT 2.0 (GCP BigQuery)   • Operational Incident Gatekeeper              • Incidents Table (Hybrid JSONB)   • Knowledge Graph (vis-network)
• Google News RSS             • EU AI Act & NIST Classification              • Directed Causal Edges Table      • GIS World Map (Leaflet)
• ArXiv AI Papers             • Causal Knowledge Graph Linker                • Row Level Security (RLS)         • Compliance Analytics Dashboard
• AI Incident Database (AIID) • Adaptive Trend Keyword Evolution             • Column-Level full_text Security  • 1-Page Daily Briefing
```

---

## ⚙️ Core Components

### 1. Automated Harvester & AI Pipeline (`scripts/ingest.py`)
- **Multi-Source Ingestion**: Automated daily harvesting from GDELT 2.0 BigQuery, Google News RSS, ArXiv, and the AI Incident Database (AIID), with automatic URL unrolling (`googlenewsdecoder`).
- **Binary Gatekeeper**: Powered by **Gemma 4 (`gemma-4-31b-it`)** for zero-sycophancy verification of real-world operational AI incidents vs. corporate litigation or speculative noise.
- **Deep Taxonomy & Damage Extraction**: Multi-model extraction (**Gemma 4 31B** & **Gemini 3.6 Flash**) mapping incidents to international regulatory standards with financial damage guardrails.
- **Causal Graph Deduplication**: Hybrid TF-IDF and LLM semantic deduplication (`scripts/dedup_engine.py`) linking related incidents into directed graph relationships (`edges`).
- **Adaptive Keyword Learning**: Self-improving trend keyword evolution (`scripts/dynamic_keywords.py`) enriching search lanes based on detected emerging threats.

### 2. Primary Database (Supabase Cloud PostgreSQL)
- **`incidents` Table**: Stores verified AI incidents, structured taxonomy metadata, confidence scores, and unrolled source URLs with column-level security.
- **`edges` Table**: Stores directed causal relationships (`EVOLVED_FROM`, `RELATED_CAUSE`) forming the Knowledge Graph topology.
- **`daily_source_stats` Table**: Internal ingestion telemetry tracking candidate yield across harvest lanes.

### 3. Interactive Web Dashboard (`src/`)
- 🕸️ **Interactive Knowledge Graph**: Built with `vis-network` canvas engine featuring dynamic drag-and-drop physics, node inspection drawers, and dynamic clustering (EU AI Act, Harm Domain, System Type, Severity).
- 🗺️ **GIS World Map**: Interactive Leaflet map with Esri World Dark Gray Canvas tiles for geographic risk visualization.
- 📋 **Incident Explorer**: Multi-column tabular/grid layout with 2-tier sidebar filters, search, and CSV/JSON data export.
- 📊 **Analytics & Compliance Dashboard**: Recharts-powered analytics for EU AI Act, NIST AI RMF, and ISO 42001 compliance tracking.
- 📰 **Daily Briefing**: 1-page executive dashboard summarizing top AI safety events.

---

## 📊 Taxonomy & Regulatory Standards

- **EU AI Act Tiers**: `Prohibited Risk` | `High Risk` | `Limited Risk` | `Minimal Risk` | `Unclassified (N/A)`
- **System Classification**: `High-Risk Regulated` | `General Purpose Model` | `Autonomous Agent` | `Biometric Identification` | `Critical Infrastructure` | `Dual-Use Security` | `Unclassified`
- **Harm Domains (CSET/OECD)**: `Physical Safety` | `Mental Harm` | `Fundamental Rights` | `Property & Financial` | `Environment` | `Systemic Integrity` | `Societal`
- **Enterprise Standards**: **NIST AI RMF** (GOVERN, MAP, MEASURE, MANAGE) & **ISO 42001**

---

## 📁 Repository Structure

```text
AI_Incident_Monitor/
├── .github/workflows/
│   └── daily_ingest.yml            # Automated daily ingestion & Supabase upload (@ 02:00 UTC)
├── config/
│   ├── harvest_keywords.json       # Curated multi-lane static harvest subjects & incident terms
│   └── dynamic_keywords.json       # Adaptive self-evolving trend keywords
├── scripts/
│   ├── ingest.py                   # 4-stage automated pipeline (Scout, Gatekeeper, Taxonomy, Dedup)
│   ├── dedup_engine.py             # Hybrid TF-IDF & LLM semantic deduplication engine
│   ├── dynamic_keywords.py         # Self-improving trend keyword evolution system
│   └── migrate_json_to_supabase.py # Supabase PostgreSQL database synchronizer
├── src/
│   ├── components/                 # Web Dashboard Views (GraphView, GeoMapView, ExplorerView, etc.)
│   ├── data/                       # Bundled static fallback datasets (incidents.json, edges.json)
│   ├── lib/supabase.ts             # Supabase Client connection & database queries
│   ├── types/incident.ts           # Authoritative TypeScript data interfaces & taxonomy schemas
│   └── App.tsx                     # Main router & global filter state
├── supabase/
│   └── migrations/                 # Versioned SQL migrations & rollback scripts
├── tests/                          # Deterministic AAA automated unit test suite
├── supabase_schema.sql             # Supabase PostgreSQL DDL schema & Row Level Security policies
└── vercel.json                     # Edge deployment configuration & hardened security headers
```
