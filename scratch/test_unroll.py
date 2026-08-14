import urllib.request
import re
import base64

def unwrap_google_news_url(url: str) -> str:
    if "news.google.com" not in url:
        return url
    
    # Try decoding base64 payload inside RSS articles URL
    try:
        if "/rss/articles/" in url or "/articles/" in url:
            parts = url.split("/")
            encoded = parts[-1].split("?")[0]
            # Try decoding base64
            padded = encoded + "=" * (-len(encoded) % 4)
            try:
                decoded_bytes = base64.b64decode(padded)
                # Find http/https strings in raw decoded bytes
                found = re.findall(rb'https?://[^\s\x00-\x1f\"\'<>]+', decoded_bytes)
                for f in found:
                    s = f.decode('latin1', errors='ignore')
                    if "news.google.com" not in s and "google.com" not in s and len(s) > 10:
                        return s
            except Exception:
                pass

        # Fallback to HTTP request following redirects
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=6) as response:
            final_url = response.geturl()
            if "news.google.com" not in final_url:
                return final_url
            html = response.read().decode('utf-8', errors='ignore')
            m = re.search(r'data-n-au="([^"]+)"', html)
            if m and "google.com" not in m.group(1):
                return m.group(1)
            m2 = re.search(r'<a[^>]+href="(https?://[^"]+)"[^>]*>Opening', html)
            if m2 and "google.com" not in m2.group(1):
                return m2.group(1)
    except Exception as e:
        print(f"Error unwrapping {url[:40]}: {e}")
    return url

test_urls = [
    "https://news.google.com/rss/articles/CBMif0FVX3lxTFBPV1U1RXg1QmVlUW5jaXczUVVqXzgwSkg4ajNKajV3dE1fTGVpZktJWlNjbm1FQkVJRVE0S25xYjB0ZTZacTdhWWpVbWNQbVNXNFFrVHhnZnIyNzlsRl8zcHdOS3BCOGlXTTlWRm5DQ0lNNXhpSVpnX0tTVWlLSXM?oc=5",
    "https://news.google.com/articles/CBMi"
]

for tu in test_urls:
    res = unwrap_google_news_url(tu)
    print("Original:", tu[:60] + "...")
    print("Unwrapped:", res)
    print("-" * 50)
