# -*- coding: utf-8 -*-

import requests
import re
import json
from datetime import datetime, timedelta
import time
import random

# ===================== 配置 ===================== #

URL = "https://www.tvmao.com/program/LUZHOUTV-KUZHOUTV1-w1.html"
YEAR = 2026
OUTPUT_FILE = "epg.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ===================== 抓取 ===================== #

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        return r.text
    except Exception as e:
        print("fetch error:", e)
        return ""

# ===================== 清洗 ===================== #

def clean_line(line):
    line = line.strip()

    # 丢弃无用行
    bad_keywords = [
        "午间节目",
        "晚间节目",
        "下周",
        "周一", "周二", "周三", "周四", "周五", "周六", "周日"
    ]

    for b in bad_keywords:
        if b in line and ":" not in line:
            return None

    return line

# ===================== 解析 ===================== #

def parse(text):
    lines = text.splitlines()

    result = []
    current_date = None

    for line in lines:
        line = clean_line(line)
        if not line:
            continue

        # 日期行
        m_date = re.match(r"(\d{2}-\d{2})", line)
        if m_date:
            current_date = m_date.group(1)
            continue

        # 节目行
        m = re.match(r"(\d{2}:\d{2})\s+(.+)", line)
        if m and current_date:
            result.append({
                "date": current_date,
                "time": m.group(1),
                "title": m.group(2).strip()
            })

    return result

# ===================== 时间计算 ===================== #

def build_epg(items):
    epg = []

    for i in range(len(items)):
        cur = items[i]

        start = datetime.strptime(
            f"{YEAR}-{cur['date']} {cur['time']}",
            "%Y-%m-%d %H:%M"
        )

        # 默认 end
        if i + 1 < len(items):
            nxt = items[i + 1]

            end = datetime.strptime(
                f"{YEAR}-{nxt['date']} {nxt['time']}",
                "%Y-%m-%d %H:%M"
            )

            # 跨天修正
            if end <= start:
                end += timedelta(days=1)
        else:
            end = start + timedelta(minutes=30)

        epg.append({
            "start": start.strftime("%Y%m%d%H%M%S"),
            "end": end.strftime("%Y%m%d%H%M%S"),
            "title": cur["title"]
        })

    return epg

# ===================== 主程序 ===================== #

def main():
    print("fetching...")

    html = fetch(URL)

    if not html:
        print("empty html")
        return

    print("parsing...")

    data = parse(html)

    print("items:", len(data))

    print("building epg...")

    epg = build_epg(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(epg, f, ensure_ascii=False, indent=2)

    print("done ->", OUTPUT_FILE)


# ===================== 运行 ===================== #

if __name__ == "__main__":
    main()
