import os

print("--- Testing google-genai ---")
try:
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        client = genai.Client(api_key=api_key)
        print("Available models in google.genai:")
        for m in client.models.list():
            print(" -", m.name)
    else:
        print("No GEMINI_API_KEY set.")
except Exception as e:
    print("Error listing with google-genai:", e)

print("\n--- Testing google.generativeai ---")
try:
    import google.generativeai as legacy_genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        legacy_genai.configure(api_key=api_key)
        print("Available models in google.generativeai:")
        for m in legacy_genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(" -", m.name)
except Exception as e:
    print("Error listing with google.generativeai:", e)
