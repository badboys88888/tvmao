from config import CHANNELS, YEAR, OUTPUT_FILE
from fetch import fetch_api
from parse import parse
from builder import build
import json
import time

def main():

    all_epg = {}

    for name, channel_id in CHANNELS.items():

        print("\nfetch:", name, channel_id)

        data = fetch_api(channel_id)

        items = parse(data)

        print("items:", len(items))

        epg = build(items, YEAR)

        all_epg[name] = epg

        time.sleep(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_epg, f, ensure_ascii=False, indent=2)

    print("done ->", OUTPUT_FILE)


if __name__ == "__main__":
    main()
