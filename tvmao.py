#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import time
import requests
import json
import gzip
from dateutil import tz
import re

# =========================
# 读取配置
# =========================
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

channels = config["channels"]

# =========================
# 请求头
# =========================
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.tvmao.com/"
}

# =========================
# channel解析（兼容4字段）
# =========================
def parse_channel(info):

    if isinstance(info, dict):
        return {
            "path": info.get("path", ""),
            "id": info.get("id", ""),
            "region": info.get("region", "CN"),
            "source": info.get("source", "tvmao"),
            "icon": info.get("icon", "")
        }

    return {
        "path": info[0] if len(info) > 0 else "",
        "id": info[1] if len(info) > 1 else "",
        "region": info[2] if len(info) > 2 else "CN",
        "source": info[3] if len(info) > 3 else "tvmao",
        "icon": ""
    }

# =========================
# 安全JSON
# =========================
def safe_json(res):
    try:
        return res.json()
    except:
        return None

# =========================
# 提取节目（🔥防炸核心）
# =========================
def extract_programs(data):

    if not data:
        return []

    if isinstance(data, dict):
        pro = data.get("pro") or data.get("data") or data.get("result")

        if isinstance(pro, list):
            return [p for p in pro if isinstance(p, dict)]

    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]

    return []

# =========================
# 时间解析
# =========================
def parse_time(dt, t):

    try:
        t = str(t).strip()

        if re.fullmatch(r"\d{4}", t):
            return datetime.datetime.combine(
                dt,
                datetime.time(int(t[:2]), int(t[2:]))
            )

        if ":" in t and len(t) <= 5:
            h, m = t.split(":")
            return datetime.datetime.combine(
                dt,
                datetime.time(int(h), int(m))
            )

        return datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")

    except:
        return None

# =========================
# 获取EPG
# =========================
def get_epg(name, channel_id, dt):

    weekday = dt.weekday() + 1

    url = (
        f"https://lighttv.tvmao.com/qa/qachannelschedule"
        f"?epgCode={channel_id}&op=getProgramByChnid"
        f"&isNew=on&day={weekday}"
    )

    print(f"\n[FETCH] {name} | {channel_id} | {dt}")

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = safe_json(res)

        programs = extract_programs(data)

        if not programs:
            print("[EMPTY] no data")
            return []

        programs.sort(key=lambda x: x.get("time", ""))

        epgs = []

        for i, p in enumerate(programs):

            # 🔥 核心防炸
            if not isinstance(p, dict):
                print("[SKIP]", p)
                continue

            title = p.get("name") or p.get("title") or "未知节目"
            t = p.get("time")

            if not t:
                continue

            start = parse_time(dt, t)
            if not start:
                continue

            if i < len(programs) - 1:
                end = parse_time(dt, programs[i + 1].get("time"))
                if not end:
                    end = start + datetime.timedelta(minutes=30)
            else:
                end = start + datetime.timedelta(minutes=30)

            epgs.append({
                "channel_id": channel_id,
                "title": title,
                "starttime": start,
                "endtime": end
            })

        return epgs

    except Exception as e:
        print("[ERROR]", e)
        return []

# =========================
# 写XML
# =========================
def save_xml(all_epgs):

    tz_sh = tz.gettz("Asia/Shanghai")

    with open("tvmao.xml", "w", encoding="utf-8") as f:

        f.write('<?xml version="1.0" encoding="UTF-8"?><tv>\n')

        # CHANNEL
        for name, info in channels.items():

            meta = parse_channel(info)

            f.write(
                f'<channel id="{meta["id"]}" region="{meta["region"]}" source="{meta["source"]}">'
                f'<display-name>{name}</display-name>'
            )

            if meta["icon"]:
                f.write(f'<icon src="{meta["icon"]}" />')

            f.write('</channel>\n')

        # PROGRAM
        for e in all_epgs:

            start = e["starttime"].astimezone(tz_sh).strftime("%Y%m%d%H%M%S") + " +0800"
            end = e["endtime"].astimezone(tz_sh).strftime("%Y%m%d%H%M%S") + " +0800"

            title = (
                e["title"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            f.write(
                f'<programme channel="{e["channel_id"]}" start="{start}" stop="{end}">'
                f'<title lang="zh">{title}</title>'
                f'<category system="region">CN</category>'
                f'</programme>\n'
            )

        f.write("</tv>")

    print("\nXML生成完成: tvmao.xml")

    with open("tvmao.xml", "rb") as f_in:
        with gzip.open("tvmao.xml.gz", "wb") as f_out:
            f_out.writelines(f_in)

    print("GZ生成完成: tvmao.xml.gz")

# =========================
# 主流程
# =========================
def main():

    all_epgs = []

    today = datetime.datetime.now().date()

    days = [
        today,
        today + datetime.timedelta(days=1),
        today + datetime.timedelta(days=2)
    ]

    for dt in days:

        print(f"\n===== 日期 {dt} =====")

        for name, info in channels.items():

            meta = parse_channel(info)

            epgs = get_epg(name, meta["id"], dt)

            if epgs:
                all_epgs.extend(epgs)
                print(f"[OK] {name} ({len(epgs)})")
            else:
                print(f"[FAIL] {name}")

            time.sleep(0.3)

    save_xml(all_epgs)


if __name__ == "__main__":
    main()
