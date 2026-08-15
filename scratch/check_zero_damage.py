import os
import json
import urllib.request

def check_incidents():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if url and key:
        req = urllib.request.Request(
            f"{url}/rest/v1/incidents?select=*",
            headers={"apikey": key, "Authorization": f"Bearer {key}"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"Total Supabase records: {len(data)}")
                print("\n--- INCIDENTS WITH $0 FINANCIAL DAMAGE ---")
                zero_count = 0
                for d in data:
                    usd = d.get("financial_damage_usd", 0) or 0
                    if usd == 0 or "060" in d.get("incident_id", ""):
                        zero_count += 1
                        print(f"ID: {d.get('incident_id')} | Date: {d.get('date')} | Damage: ${usd} | Title: {d.get('title')}")
                if zero_count == 0:
                    print("None! All incidents have financial damage USD populated.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_incidents()
