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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.tvmao.com/"
}

# =========================
# 统一解析 channel（关键修复）
# =========================
def parse_channel(info):
    """
    兼容：
    1. list: [path, id]
    2. list: [path, id, xxx...]
    3. dict: {"path":..., "id":..., "icon":..., "region":...}
    """

    if isinstance(info, dict):
        return {
            "path": info.get("path", ""),
            "id": info.get("id", ""),
            "icon": info.get("icon", ""),
            "region": info.get("region", "CN"),
            "source": info.get("source", "tvmao")
        }

    return {
        "path": info[0] if len(info) > 0 else "",
        "id": info[1] if len(info) > 1 else "",
        "icon": "",
        "region": "CN",
        "source": "tvmao"
    }

# =========================
# JSON解析
# =========================
def safe_json(res):
    try:
        return res.json()
    except:
        return None

# =========================
# 提取节目
# =========================
def extract_programs(data):
    if not data:
        return []

    if isinstance(data, dict):
        if "pro" in data:
            return data["pro"]
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
        if "result" in data and isinstance(data["result"], list):
            return data["result"]

    if isinstance(data, list):
        return data

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
def get_epg(channel_name, channel_id, dt):

    need_weekday = dt.weekday() + 1

    url = (
        f"https://lighttv.tvmao.com/qa/qachannelschedule"
        f"?epgCode={channel_id}&op=getProgramByChnid"
        f"&epgName=&isNew=on&day={need_weekday}"
    )

    print(f"\n[FETCH] {channel_name} | {channel_id} | {dt}")

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

            title = p.get("name") or p.get("title") or "未知节目"
            t = p.get("time")

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
# 写XML（完整增强版）
# =========================
def save_xml(all_epgs):

    tz_sh = tz.gettz("Asia/Shanghai")

    with open("tvmao.xml", "w", encoding="utf-8") as f:

        f.write('<?xml version="1.0" encoding="UTF-8"?><tv>\n')

        # =========================
        # CHANNELS
        # =========================
        for name, info in channels.items():

            meta = parse_channel(info)

            region = meta["region"]
            source = meta["source"]
            icon = meta["icon"]

            f.write(
                f'<channel id="{meta["id"]}" region="{region}" source="{source}">'
                f'<display-name>{name}</display-name>'
            )

            if icon:
                f.write(f'<icon src="{icon}" />')

            f.write('</channel>\n')

        # =========================
        # PROGRAMMES
        # =========================
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
                f'<category system="type">IPTV</category>'
                f'</programme>\n'
            )

        f.write("</tv>")

    print("\nXML生成完成: tvmao.xml")

    with open("tvmao.xml", "rb") as f_in:
        with gzip.open("tvmao.xml.gz", "wb") as f_out:
            f_out.writelines(f_in)

    print("GZ生成完成: tvmao.xml.gz")

# =========================
# 主函数
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
