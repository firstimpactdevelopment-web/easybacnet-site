"""Refresh vendor_ids.json from the official BACnet International list.

    python update_vendor_ids.py [saved-page.html]

With no argument it downloads https://bacnet.org/assigned-vendor-ids/.
Only the Vendor ID, organization name and country are kept; contact names and
street addresses are left out on purpose. build_site.py reads vendor_ids.json.
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

SRC = "https://bacnet.org/assigned-vendor-ids/"
OUT = Path(__file__).with_name("vendor_ids.json")


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def clean(cell):
    cell = re.sub(r"<br\s*/?>", "\n", cell, flags=re.I)
    cell = re.sub(r"<[^>]+>", "", cell)
    return [html.unescape(x).replace("\xa0", " ").strip() for x in cell.split("\n") if x.strip()]


def parse(page):
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", page, flags=re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S | re.I)
        if len(tds) < 2:
            continue
        idtxt = " ".join(clean(tds[0]))
        if not idtxt.isdigit():
            continue
        name = " ".join(clean(tds[1]))
        name = re.sub(r"\s+", " ", name)
        addr = clean(tds[3]) if len(tds) > 3 else []
        country = addr[-1] if addr else ""
        # The last address line is the country on nearly every row; drop it if it
        # looks like a street/postcode line rather than a country name.
        if re.search(r"\d", country) or len(country) > 40:
            country = ""
        rows.append({"id": int(idtxt), "name": name, "country": country})
    rows.sort(key=lambda r: r["id"])
    return rows


def main():
    page = Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else fetch()
    rows = parse(page)
    if len(rows) < 1000:
        sys.exit("Only parsed %d rows - page layout may have changed; not overwriting." % len(rows))
    OUT.write_text(json.dumps({"source": SRC, "retrieved": date.today().isoformat(), "vendors": rows},
                              ensure_ascii=False, indent=0), encoding="utf-8")
    print("Wrote %d vendors to %s (highest ID %d)" % (len(rows), OUT.name, rows[-1]["id"]))


if __name__ == "__main__":
    main()
