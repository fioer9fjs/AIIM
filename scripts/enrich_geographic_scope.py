"""
Geographic Scope Enrichment & Country Normalization Engine.

1. Analyzes titles, summaries, full-text, and source URLs for explicit national jurisdictions and country adjectives.
2. Corrects inaccurate 'Global' default tags to precise country names (e.g. 'Australia', 'South Korea', 'Spain', 'Russia', 'United Kingdom', 'United States').
3. Synchronizes updated dataset to src/data/incidents.json and Supabase PostgreSQL.
"""

import os
import json
import re
from typing import List, Dict, Any

COUNTRY_KEYWORD_RULES = [
    (r'\b(australia|australian|sydney|melbourne|canberra)\b', 'Australia'),
    (r'\b(south korea|korean|seoul|busan)\b', 'South Korea'),
    (r'\b(spain|spanish|madrid|barcelona)\b', 'Spain'),
    (r'\b(russia|russian|moscow)\b', 'Russia'),
    (r'\b(united kingdom|uk|britain|british|london)\b', 'United Kingdom'),
    (r'\b(united states|usa|us|american|washington|new york|california)\b', 'United States'),
    (r'\b(france|french|paris)\b', 'France'),
    (r'\b(germany|german|berlin)\b', 'Germany'),
    (r'\b(china|chinese|beijing)\b', 'China'),
    (r'\b(japan|japanese|tokyo)\b', 'Japan'),
    (r'\b(india|indian|delhi|mumbai)\b', 'India'),
    (r'\b(canada|canadian|ottawa|toronto)\b', 'Canada'),
    (r'\b(brazil|brazilian)\b', 'Brazil'),
    (r'\b(south africa|south african)\b', 'South Africa'),
    (r'\b(taiwan|taiwanese|taipei)\b', 'Taiwan'),
    (r'\b(israel|israeli|tel aviv)\b', 'Israel'),
    (r'\b(eu|european union|brussels)\b', 'European Union'),
]

def extract_countries_from_incident(inc: Dict[str, Any]) -> List[str]:
    text_corpus = f"{inc.get('title', '')} {inc.get('summary', '')} {inc.get('full_text', '')} {' '.join(inc.get('source_urls', []))}".lower()
    
    detected = []
    for pattern, country in COUNTRY_KEYWORD_RULES:
        if re.search(pattern, text_corpus):
            if country not in detected:
                detected.append(country)
                
    # Specific override for Australia gym incident if triggered
    if "gym" in text_corpus and ("australia" in text_corpus or "australian" in text_corpus or "allaboutcookies" in text_corpus):
        return ["Australia"]
        
    # Specific override for South Korea deepfake student incident
    if "deepfake" in text_corpus and ("korea" in text_corpus or "korean" in text_corpus or "heraldcorp" in text_corpus):
        return ["South Korea"]

    # Specific override for Spain deepfake fraud arrest
    if "spanish police" in text_corpus or "spain" in text_corpus or "helpnetsecurity" in text_corpus:
        return ["Spain"]

    # Specific override for Russia antiwar party / commercial secret incident
    if "russia" in text_corpus or "russian" in text_corpus or "revera.legal" in text_corpus or "meduza" in text_corpus:
        return ["Russia"]

    if detected:
        # If specific countries detected, exclude 'Global' unless genuinely multi-region
        if len(detected) == 1:
            return detected
        return [c for c in detected if c != "Global"]
        
    return inc.get("geographic_scope", ["Global"]) or ["Global"]

def get_supabase_credentials():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    return url, key

def main():
    print("=" * 85)
    print("ENRICHING & NORMALIZING INCIDENT GEOGRAPHIC SCOPE METADATA")
    print("=" * 85)

    data_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    incidents_path = os.path.join(data_dir, "incidents.json")

    if not os.path.exists(incidents_path):
        print("incidents.json not found.")
        return

    with open(incidents_path, "r", encoding="utf-8") as f:
        incidents: List[Dict[str, Any]] = json.load(f)

    updated_count = 0

    for inc in incidents:
        old_scope = inc.get("geographic_scope", ["Global"])
        new_scope = extract_countries_from_incident(inc)
        
        if old_scope != new_scope:
            updated_count += 1
            inc["geographic_scope"] = new_scope
            if isinstance(inc.get("taxonomy"), dict):
                inc["taxonomy"]["geographic_scope"] = new_scope
            print(f"  [GEOLOCATION UPDATED] '{inc.get('title')[:45]}...'\n    Old: {old_scope} -> New: {new_scope}")

    with open(incidents_path, "w", encoding="utf-8") as f:
        json.dump(incidents, f, indent=2)

    print(f"\nGeographic scope enriched for {updated_count} incidents.")
    print(f"Saved updated incidents.json.")

    # Synchronize clean dataset to Supabase Cloud PostgreSQL
    url, key = get_supabase_credentials()
    if url and key:
        print("\n---> SYNCHRONIZING GEOLOCATION FIXES TO SUPABASE POSTGRESQL...")
        from migrate_json_to_supabase import run_migration
        run_migration()

    print("\n" + "=" * 85)
    print("GEOGRAPHIC ENRICHMENT PIPELINE COMPLETE!")
    print("=" * 85)

if __name__ == "__main__":
    main()
