import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch(url):   # 👈 必须叫这个名字
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = "utf-8"
    return r.text
