from fetch import fetch_week
from parse import parse_week
from build import build_epg
import json

URL = "https://www.tvmao.com/program/LUZHOUTV-KUZHOUTV1-w1.html"

def run():
    html = fetch_week(URL)

    parsed = parse_week(html)

    epg = build_epg(parsed)

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(epg, f, ensure_ascii=False, indent=2)

    print("done")

run()
