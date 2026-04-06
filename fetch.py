import requests
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_week(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = "utf-8"
    return r.text
