import re

def clean(line):
    bad = [
        "午间节目", "晚间节目", "下周",
        "周一", "周二", "周三", "周四", "周五", "周六", "周日"
    ]

    line = line.strip()

    for b in bad:
        if b in line and ":" not in line:
            return None

    return line


def parse(text):
    if not text:
        return []

    lines = text.splitlines()
    res = []
    date = None

    for line in lines:
        line = clean(line)
        if not line:
            continue

        # 日期
        if re.match(r"\d{2}-\d{2}", line):
            date = line[:5]
            continue

        # 时间节目
        m = re.match(r"(\d{2}:\d{2})\s+(.+)", line)
        if m and date:
            res.append({
                "date": date,
                "time": m.group(1),
                "title": m.group(2)
            })

    return res
