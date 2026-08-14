import urllib.request
import re

def resolve_google_news_url(url: str) -> str:
    if "news.google.com" not in url:
        return url
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            final_url = response.geturl()
            if "news.google.com" not in final_url:
                return final_url
            html = response.read().decode('utf-8', errors='ignore')
            # Extract data-n-au or target href inside google news wrapper
            match = re.search(r'data-n-au="([^"]+)"', html)
            if match:
                return match.group(1)
            match_c = re.search(r'c-wiz[^>]+href="([^"]+)"', html)
            if match_c and not match_c.group(1).startswith("./"):
                return match_c.group(1)
    except Exception as e:
        print(f"Error unrolling {url[:40]}: {e}")
    return url

# Test sample
test_url = "https://news.google.com/rss/articles/CBMi"
print("Resolved:", resolve_google_news_url(test_url))
