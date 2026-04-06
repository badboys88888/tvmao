import re

def parse_week(text):
    lines = text.splitlines()

    data = []
    current_date = None

    for line in lines:
        line = line.strip()

        # 日期行
        if re.match(r"\d{2}-\d{2}", line):
            current_date = line.split()[0]
            continue

        # 节目行
        m = re.match(r"(\d{2}:\d{2})\s+(.+)", line)
        if m and current_date:
            data.append({
                "date": current_date,
                "time": m.group(1),
                "title": m.group(2).strip()
            })

    return data
