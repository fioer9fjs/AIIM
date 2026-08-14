import urllib.request
import re

url = "https://news.google.com/rss/articles/CBMif0FVX3lxTFBPV1U1RXg1QmVlUW5jaXczUVVqXzgwSkg4ajNKajV3dE1fTGVpZktJWlNjbm1FQkVJRVE0S25xYjB0ZTZacTdhWWpVbWNQbVNXNFFrVHhnZnIyNzlsRl8zcHdOS3BCOGlXTTlWRm5DQ0lNNXhpSVpnX0tTVWlLSXM?oc=5"

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
        print("Length:", len(content))
        print("Final URL:", resp.geturl())
        urls = re.findall(r'https?://[a-zA-Z0-9\.\-_/\?%&=]+', content)
        pub_urls = [u for u in urls if 'google' not in u and 'gstatic' not in u and 'w3.org' not in u]
        print("Publisher URLs found:", set(pub_urls[:10]))
except Exception as e:
    print("Error:", e)
