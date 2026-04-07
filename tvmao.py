def save_xml(all_epgs):

    tz_sh = tz.gettz("Asia/Shanghai")

    with open("tvmao.xml", "w", encoding="utf-8") as f:

        f.write('<?xml version="1.0" encoding="UTF-8"?><tv>\n')

        # =========================
        # channels（增强版）
        # =========================
        for name, info in channels.items():

            url_part, channel_id = info

            # 默认值（你可以以后放 config）
            region = "CN"
            source = "tvmao"
            icon = ""

            f.write(
                f'<channel id="{channel_id}" '
                f'region="{region}" '
                f'source="{source}">'
                f'<display-name>{name}</display-name>'
            )

            if icon:
                f.write(f'<icon src="{icon}" />')

            f.write('</channel>\n')

        # =========================
        # programmes（增强标签）
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
                f'<category system="tag">IPTV</category>'
                f'<category system="region">CN</category>'
                f'</programme>\n'
            )

        f.write("</tv>")

    print("\nXML生成完成: tvmao.xml")

    with open("tvmao.xml", "rb") as f_in:
        with gzip.open("tvmao.xml.gz", "wb") as f_out:
            f_out.writelines(f_in)

    print("GZ生成完成: tvmao.xml.gz")
