import requests


def fetch_full_article(article_url):
    try:
        jina_url = f"https://r.jina.ai/http://{article_url.replace('https://', '').replace('http://', '')}"
        response = requests.get(jina_url, timeout=20)

        if response.status_code != 200:
            print(f"Jina fetch failed: {response.status_code}")
            return ""

        return response.text[:25000]
    except Exception as e:
        print(f"Full article fetch error: {e}")
        return ""
