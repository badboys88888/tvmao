def parse(data):
    """
    data = JSON
    """

    items = []

    if not data:
        return []

    for p in data.get("data", {}).get("programs", []):
        items.append({
            "date": p.get("date"),
            "time": p.get("time"),
            "title": p.get("title")
        })

    return items
