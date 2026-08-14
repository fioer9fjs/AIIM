import base64
import re

url = "https://news.google.com/rss/articles/CBMif0FVX3lxTFBPV1U1RXg1QmVlUW5jaXczUVVqXzgwSkg4ajNKajV3dE1fTGVpZktJWlNjbm1FQkVJRVE0S25xYjB0ZTZacTdhWWpVbWNQbVNXNFFrVHhnZnIyNzlsRl8zcHdOS3BCOGlXTTlWRm5DQ0lNNXhpSVpnX0tTVWlLSXM?oc=5"

code = url.split("/articles/")[1].split("?")[0]
print("Code:", code)

# Try decoding base64
for b64 in [code, code + "==", code + "="]:
    try:
        raw = base64.urlsafe_b64decode(b64)
        print("Raw decoded:", raw[:150])
        # Find URLs inside bytes
        urls = re.findall(rb'https?://[^\s\x00-\x1f\"\'<>]+', raw)
        print("Found in raw:", urls)
        
        # Search for string parts
        matches = re.findall(rb'[\x20-\x7e]{8,}', raw)
        for m in matches:
            s = m.decode('ascii', errors='ignore')
            if 'http' in s or 'news' in s or '.' in s:
                print("String match:", s)
    except Exception as e:
        pass
