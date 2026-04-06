from datetime import datetime, timedelta

YEAR = 2026

def build_epg(items):
    result = []

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

            # 跨天处理
            if end <= start:
                end += timedelta(days=1)
        else:
            end = start + timedelta(minutes=30)

        result.append({
            "start": start.strftime("%Y%m%d%H%M%S"),
            "end": end.strftime("%Y%m%d%H%M%S"),
            "title": cur["title"]
        })

    return result
