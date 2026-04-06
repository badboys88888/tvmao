import json
import time
from config import CHANNELS, YEAR, OUTPUT_FILE
from fetch import fetch
from parser import parse
from builder import build

def main():

    all_epg = {}

    for name, url in CHANNELS.items():
        print("fetch:", name)

        html = fetch(url)

        items = parse(html)

        epg = build(items, YEAR)

        all_epg[name] = epg

        time.sleep(2)  # 防封

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_epg, f, ensure_ascii=False, indent=2)

    print("done ->", OUTPUT_FILE)


if __name__ == "__main__":
    main()
