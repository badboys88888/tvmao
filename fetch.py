import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.tvmao.com/"
}

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        return r.text
    except Exception as e:
        print("fetch error:", e)
        return ""
