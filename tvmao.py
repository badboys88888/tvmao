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
}

# =========================
# JSON安全解析
# =========================
def safe_json(res):
    try:
        return res.json()
    except Exception:
        return None

# =========================
# 提取节目数据（核心修复）
# =========================
def extract_programs(data):
    if not data:
        return []

    # dict结构
    if isinstance(data, dict):
        if "pro" in data:
            return data["pro"]
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
        if "result" in data and isinstance(data["result"], list):
            return data["result"]

    # list结构
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if "pro" in item:
                    return item["pro"]
                if "data" in item:
                    return item["data"]

    return []

# =========================
# 时间解析（容错）
# =========================
def parse_time(dt, t):
    """
    支持：
    1830
    18:30
    2026-04-06 18:30
    """
    try:
        t = str(t).strip()

        # 1830
        if re.fullmatch(r"\d{4}", t):
            return datetime.datetime.combine(
                dt,
                datetime.time(int(t[:2]), int(t[2:]))
            )

        # 18:30
        if ":" in t and len(t) <= 5:
            h, m = t.split(":")
            return datetime.datetime.combine(
                dt,
                datetime.time(int(h), int(m))
            )

        # fallback datetime
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
            return {
                "success": 0,
                "epgs": [],
                "msg": "no data",
                "source": "tvmao"
            }

        epgs = []

        # 排序（防乱序）
        programs.sort(key=lambda x: x.get("time", ""))

        for i, p in enumerate(programs):

            title = p.get("name") or p.get("title") or "未知节目"
            t = p.get("time")

            start = parse_time(dt, t)
            if not start:
                continue

            # 估算结束时间
            if i < len(programs) - 1:
                next_t = programs[i + 1].get("time")
                end = parse_time(dt, next_t)
                if not end:
                    end = start + datetime.timedelta(minutes=30)
            else:
                end = start + datetime.timedelta(minutes=30)

            epgs.append({
                "channel_id": channel_id,
                "starttime": start,
                "endtime": end,
                "title": title,
                "desc": "",
            })

        return {
            "success": 1,
            "epgs": epgs,
            "msg": "",
            "source": "tvmao"
        }

    except Exception as e:
        return {
            "success": 0,
            "epgs": [],
            "msg": str(e),
            "source": "tvmao"
        }

# =========================
# 写XML
# =========================
def save_xml(all_epgs):

    tz_sh = tz.gettz("Asia/Shanghai")

    with open("tvmao.xml", "w", encoding="utf-8") as f:

        f.write('<?xml version="1.0" encoding="UTF-8"?><tv>\n')

        # channels
        for name, info in channels.items():
            channel_id = info[1]
            f.write(f'<channel id="{channel_id}"><display-name>{name}</display-name></channel>\n')

        # programmes
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
                f'<title lang="zh">{title}</title></programme>\n'
            )

        f.write("</tv>")

    print("\nXML生成完成: tvmao.xml")

    # gzip
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
    days = [today, today + datetime.timedelta(days=1), today + datetime.timedelta(days=2)]

    for dt in days:
        print(f"\n===== 日期 {dt} =====")

        for name, info in channels.items():
            url_part, channel_id = info

            ret = get_epg(name, channel_id, dt)

            if ret["success"]:
                all_epgs.extend(ret["epgs"])
            else:
                print(f"[FAIL] {name}: {ret['msg']}")

            time.sleep(0.2)

    save_xml(all_epgs)


if __name__ == "__main__":
    main()
