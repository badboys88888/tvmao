import json
import time
from config import CHANNELS, YEAR, OUTPUT_FILE
from fetch import fetch
from parse import parse
from builder import build

def main():
    all_epg = {}

    for name, url in CHANNELS.items():
        print("\n========================")
        print("fetch:", name)
        print(url)

        html = fetch(url)

        # 🔥 DEBUG：确认是否抓到真实页面
        print("----- HTML PREVIEW -----")
        print(html[:500])
        print("------------------------")

        items = parse(html)

        print("parsed items:", len(items))
        print(items[:3])

        epg = build(items, YEAR)

        print("epg items:", len(epg))

        all_epg[name] = epg

        time.sleep(2)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_epg, f, ensure_ascii=False, indent=2)

    print("\ndone ->", OUTPUT_FILE)


if __name__ == "__main__":
    main()
