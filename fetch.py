import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.tvmao.com/"
}

def fetch_api(channel_id):
    """
    直接抓TVmao JSON接口（核心）
    """

    url = f"https://m.tvmao.com/program/{channel_id}/json"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.json()
    except Exception as e:
        print("API fetch error:", e)
        return {}
