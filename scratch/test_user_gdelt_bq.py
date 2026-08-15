import os
import json

def test_user_gdelt_query():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

    try:
        from google.cloud import bigquery
    except ImportError:
        print("google.cloud.bigquery not installed!")
        return

    project_id = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GCP_PROJECT")
    client = bigquery.Client(project=project_id) if project_id else bigquery.Client()

    sql = """
    WITH filtered_articles AS (
        SELECT 
            DATE,
            DocumentIdentifier AS url,
            SourceCommonName AS source,
            CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) AS tone,
            REGEXP_EXTRACT(LOWER(DocumentIdentifier), r'/([^/]+)[/]?$') AS url_slug
        FROM 
            `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE 
            _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)
            
            -- AI term filter
            AND REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'\\b(ai|artificial-intelligence|genai|generative-ai|machine-learning|chatgpt|openai|gpt|llm|deepmind|anthropic|claude|copilot|gemini|mistral|huggingface|hugging-face|xai|midjourney|stable-diffusion|sora|perplexity|grok)\\b')
            
            -- Incident term filter
            AND REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'\\b(incident|failure|outage|glitch|breach|hack|flaw|vulnerability|hallucination|deepfake|bias|jailbreak|lawsuit|fraud|fine|ban|probe|investigation|violation|copyright|penalty|leak|exploit|scam|malware|error|crash|bug|malfunction|misinformation|disinformation|plagiarism|propaganda)\\b')
            
            -- Aviation exclusion
            AND NOT REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'\\b(flight|plane|aircraft|aviation|airline|airlines|pilot|jet)\\b')
            
            -- Tone threshold
            AND CAST(SPLIT(V2Tone, ',')[OFFSET(0)] AS FLOAT64) < -3.0
    )
    SELECT 
        MIN(DATE) AS first_published,
        ANY_VALUE(url) AS example_url,
        COUNT(1) AS number_of_reports,
        ARRAY_AGG(DISTINCT source LIMIT 5) AS reported_by_samples,
        ROUND(AVG(tone), 2) AS avg_tone
    FROM 
        filtered_articles
    WHERE 
        url_slug IS NOT NULL
    GROUP BY 
        url_slug
    ORDER BY 
        number_of_reports DESC, 
        first_published DESC
    LIMIT 50;
    """

    print("Running dry-run check on user GDELT query...")
    dry_job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    bytes_scanned = dry_job.total_bytes_processed
    print(f"Dry-run estimated bytes scanned: {bytes_scanned / (1024**3):.3f} GB")

    if bytes_scanned > 50 * 1024 * 1024 * 1024:
        print("Query exceeds 50 GB limit!")
        return

    print("\nExecuting GDELT query...")
    query_job = client.query(sql)
    results = list(query_job.result())
    print(f"Fetched {len(results)} clustered incident candidates!")
    
    for i, row in enumerate(results[:15], 1):
        print(f"{i:02d}. [Reports: {row.number_of_reports}] Tone: {row.avg_tone} | URL: {row.example_url}")
        print(f"    Sources: {', '.join(row.reported_by_samples)}")

if __name__ == "__main__":
    test_user_gdelt_query()
