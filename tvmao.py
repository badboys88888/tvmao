#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import time
import requests
import json
import gzip
import re
from dateutil import tz

# =========================
# 读取配置（兼容旧/新格式）
# =========================
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

channels = config["channels"]

# =========================
# 请求头
# =========================
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
}

# =========================
# JSON安全解析
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
# 自动识别 region（核心）
# =========================
def auto_region(name, info):
    if isinstance(info, dict):
        if "region" in info:
            return info["region"]

    if "香港" in name or "HK" in name:
        return "HK"
    if "台湾" in name or "TW" in name:
        return "TW"

    return "CN"

# =========================
# 统一读取 channel 字段（兼容旧结构）
# =========================
def get_channel_meta(name, info):

    # 新结构（dict）
    if isinstance(info, dict):
        return {
            "id": info.get("id"),
            "path": info.get("path"),
            "region": auto_region(name, info),
            "source": info.get("source", "tvmao"),
            "icon": info.get("icon", "")
        }

    # 旧结构（list）
    return {
        "path": info[0],
        "id": info[1],
        "region": "CN",
        "source": "tvmao",
        "icon": ""
    }

# =========================
# 获取EPG
# =========================
def get_epg(channel_name, channel_id, dt):

    weekday = dt.weekday() + 1

    url = (
        f"https://lighttv.tvmao.com/qa/qachannelschedule"
        f"?epgCode={channel_id}&op=getProgramByChnid"
        f"&epgName=&isNew=on&day={weekday}"
    )

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = safe_json(res)

        programs = extract_programs(data)

        if not programs:
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
                "starttime": start,
                "endtime": end,
                "title": title,
                "desc": ""
            })

        return epgs

    except:
        return []

# =========================
# 写 XML
# =========================
def save_xml(all_epgs):

    tz_sh = tz.gettz("Asia/Shanghai")

    with open("tvmao.xml", "w", encoding="utf-8") as f:

        f.write('<?xml version="1.0" encoding="UTF-8"?><tv>\n')

        # ===== channels =====
        for name, info in channels.items():

            meta = get_channel_meta(name, info)

            f.write(
                f'<channel id="{meta["id"]}" '
                f'region="{meta["region"]}" '
                f'source="{meta["source"]}">'
                f'<display-name>{name}</display-name>'
            )

            if meta["icon"]:
                f.write(f'<icon src="{meta["icon"]}"/>')

            f.write('</channel>\n')

        # ===== programmes =====
        for e in all_epgs:

            meta = None
            for name, info in channels.items():
                m = get_channel_meta(name, info)
                if m["id"] == e["channel_id"]:
                    meta = m
                    break

            region = meta["region"] if meta else ""

            start = e["starttime"].astimezone(tz_sh).strftime("%Y%m%d%H%M%S") + " +0800"
            end = e["endtime"].astimezone(tz_sh).strftime("%Y%m%d%H%M%S") + " +0800"

            title = e["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            f.write(
                f'<programme channel="{e["channel_id"]}" start="{start}" stop="{end}">'
                f'<title lang="zh">{title}</title>'
                f'<category system="region">{region}</category>'
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
        print(f"\n===== {dt} =====")

        for name, info in channels.items():

            meta = get_channel_meta(name, info)

            epgs = get_epg(name, meta["id"], dt)

            all_epgs.extend(epgs)

            print(f"[OK] {name}")

            time.sleep(0.2)

    save_xml(all_epgs)


if __name__ == "__main__":
    main()
