from datetime import datetime, timedelta

def build(items, year):
    epg = []

    for i in range(len(items)):
        cur = items[i]

        start = datetime.strptime(
            f"{year}-{cur['date']} {cur['time']}",
            "%Y-%m-%d %H:%M"
        )

        if i + 1 < len(items):
            nxt = items[i+1]

            end = datetime.strptime(
                f"{year}-{nxt['date']} {nxt['time']}",
                "%Y-%m-%d %H:%M"
            )

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
