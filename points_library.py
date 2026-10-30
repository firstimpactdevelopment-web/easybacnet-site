"""
BACnet points-list library for easybacnet.com.

Source data lives in points_data/<manufacturer_slug>/<model_slug>.json, one file
per model, re-keyed by hand (well, by careful extraction) from each
manufacturer's free public points-list PDF. We publish the FACTS (object type,
instance, name, units, access, state text) in our own tables and link to the
manufacturer's document; we never re-host their PDF or copy their prose.

Pages generated (clean URLs; write() in build_site strips .html/index.html):
  /bacnet-points-lists/                          hub: pick a manufacturer, search all models
  /bacnet-points-lists/<mfr>/                    every model we have for that manufacturer
  /bacnet-points-lists/<mfr>/<model>             the points table + downloads + source
  /bacnet-points-lists/<mfr>/<model>.csv         plain CSV
  /bacnet-points-lists/<mfr>/<model>-ede.csv     EDE (B.I.G.-EU engineering data exchange)
  /bacnet-points-lists/<mfr>/<model>.json        machine-readable, for tools and AI agents
  /bacnet-points-lists/index.json                catalogue of everything above

build_site.main() calls build(write) and folds the returned URLs into the
sitemap, llms.txt and IndexNow ping.
"""

import csv
import glob
import html
import io
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "points_data")
BASE_URL = "https://easybacnet.com"
ROOT = "bacnet-points-lists"

# Bump when the library's data or pages change meaningfully.
UPDATED = "2026-10-28"
UPDATED_HUMAN = "28 October 2026"

# Google Play listing with UTM tags (same scheme as build_site.play_url), so
# Play Console credits installs that start from a points-list page.
PLAY_URL = ("https://play.google.com/store/apps/details?id=com.easybacnet.app"
            "&amp;utm_source=easybacnet.com&amp;utm_medium=%s&amp;utm_campaign=points")

# abbreviation -> (full object type name, BACnet object type number)
OBJECT_TYPES = {
    "AI": ("Analog Input", 0), "AO": ("Analog Output", 1), "AV": ("Analog Value", 2),
    "BI": ("Binary Input", 3), "BO": ("Binary Output", 4), "BV": ("Binary Value", 5),
    "CAL": ("Calendar", 6), "DEV": ("Device", 8), "FILE": ("File", 10),
    "LO": ("Loop", 12), "MI": ("Multi-state Input", 13), "MO": ("Multi-state Output", 14),
    "NC": ("Notification Class", 15), "SCH": ("Schedule", 17), "MV": ("Multi-state Value", 19),
    "TL": ("Trend Log", 20), "ACC": ("Accumulator", 23), "CSV": ("CharacterString Value", 40),
    "DTV": ("DateTime Value", 44), "IV": ("Integer Value", 45),
    "LAV": ("Large Analog Value", 46), "OSV": ("OctetString Value", 47),
    "PIV": ("Positive Integer Value", 48), "Other": ("Other", None),
}
TYPE_ORDER = list(OBJECT_TYPES)

# Common unit spellings -> BACnet engineering-units enumeration (matches the
# app's Names.kt table). Used for the EDE unit-code column; unknown -> blank.
_UNIT_CODES = {
    "°f": 64, "deg f": 64, "degf": 64, "f": 64, "degrees fahrenheit": 64, "degrees-fahrenheit": 64,
    "°c": 62, "deg c": 62, "degc": 62, "c": 62, "degrees celsius": 62, "degrees-celsius": 62,
    "k": 63, "%": 98, "percent": 98, "% rh": 29, "%rh": 29, "percent-relative-humidity": 29,
    "psi": 56, "psig": 56, "pa": 53, "kpa": 54, "bar": 55, "in wc": 58, "inwc": 58,
    "in. w.c.": 58, "in h2o": 58, "inh2o": 58, "in of water": 58, "inches-of-water": 58,
    "cfm": 84, "gpm": 89, "l/s": 87, "l/min": 88, "m3/s": 85, "kw": 48, "w": 47,
    "kwh": 19, "wh": 18, "btu/h": 50, "btu/hr": 50, "btuh": 50, "mbh": None, "tons": 52,
    "v": 5, "volts": 5, "a": 3, "amps": 3, "amperes": 3, "ma": 2, "hz": 27, "rpm": 104,
    "hp": 51, "hours": 71, "hrs": 71, "hr": 71, "h": 71, "minutes": 72, "min": 72,
    "seconds": 73, "sec": 73, "s": 73, "days": 70, "ppm": 96, "ppb": 97,
    "fpm": 77, "ft/min": 77, "m/s": 74, "ohms": 4, "kva": 9, "va": 8, "kvar": 12,
    "pf": 15, "power factor": 15, "lbs": 40, "lb/hr": 46, "kg": 39,
}


def unit_code(units):
    if not units:
        return ""
    c = _UNIT_CODES.get(units.strip().lower())
    return "" if c is None else str(c)


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def jstr(s):
    return json.dumps("" if s is None else str(s), ensure_ascii=False).replace("<", "\\u003c")


def slug_ok(s):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s or ""))


# ---------------------------------------------------------------------------
# Data loading + validation
# ---------------------------------------------------------------------------

def load_all():
    models = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*", "*.json"))):
        with io.open(path, encoding="utf-8") as f:
            d = json.load(f)
        problems = validate(d, path)
        if problems:
            print("SKIP %s:\n  - %s" % (os.path.relpath(path, HERE), "\n  - ".join(problems)))
            continue
        d["_path"] = path
        assign_row_ids(d["points"])
        models.append(d)
    return models


def validate(d, path):
    p = []
    for k in ("manufacturer", "manufacturer_slug", "model", "model_slug", "source", "points"):
        if not d.get(k):
            p.append("missing " + k)
    if p:
        return p
    folder = os.path.basename(os.path.dirname(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    if d["manufacturer_slug"] != folder or not slug_ok(folder):
        p.append("manufacturer_slug %r doesn't match folder %r" % (d["manufacturer_slug"], folder))
    if d["model_slug"] != stem or not slug_ok(stem):
        p.append("model_slug %r doesn't match file %r" % (d["model_slug"], stem))
    if not str(d["source"].get("url", "")).startswith("http"):
        p.append("source.url missing")
    for i, pt in enumerate(d["points"]):
        if pt.get("type") not in OBJECT_TYPES:
            pt["type"] = "Other"
        if not pt.get("name"):
            p.append("point %d has no name" % i)
            break
        inst = pt.get("instance")
        if inst is not None and not isinstance(inst, int):
            try:
                pt["instance"] = int(str(inst).strip())
            except ValueError:
                p.append("point %d instance %r not an integer" % (i, inst))
                break
        if pt.get("access") not in ("R", "W", "C"):
            pt["access"] = "R"
        for k in ("description", "units", "states"):
            pt[k] = (pt.get(k) or "").strip()
    return p


def by_manufacturer(models):
    groups = {}
    for m in models:
        groups.setdefault(m["manufacturer_slug"], []).append(m)
    for v in groups.values():
        v.sort(key=lambda m: m["model"].lower())
    return dict(sorted(groups.items(), key=lambda kv: kv[1][0]["manufacturer"].lower()))


def type_counts(points):
    c = {}
    for pt in points:
        c[pt["type"]] = c.get(pt["type"], 0) + 1
    return [(t, c[t]) for t in TYPE_ORDER if t in c]


def writable_count(points):
    return sum(1 for pt in points if pt["access"] in ("W", "C"))


# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

def hub_path():
    return ROOT + "/index.html"


def mfr_path(mslug):
    return "%s/%s/index.html" % (ROOT, mslug)


def model_path(m, ext=".html"):
    return "%s/%s/%s%s" % (ROOT, m["manufacturer_slug"], m["model_slug"], ext)


def clean(relpath):
    """Absolute clean URL for a site-relative .html path."""
    u = re.sub(r"index\.html$", "", relpath)
    u = re.sub(r"\.html$", "", u)
    return BASE_URL + "/" + u


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------

CSS = """
:root{color-scheme:dark;--bg:#14171a;--panel:#1d2227;--panel2:#191e22;--line:#2f363d;
  --fg:#f3f5f6;--mut:#9aa4ad;--accent:#ff9a1f;--ink:#0d0f11;--code:#101418;--ok:#5fd38d}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Manrope",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  font-size:16.5px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3{font-family:"Archivo",sans-serif;letter-spacing:-.01em;line-height:1.1}
h1{font-weight:900;text-transform:uppercase;font-size:clamp(1.7rem,4.6vw,2.9rem);margin:.4rem 0 .8rem}
h1 .mfr{color:var(--accent)}
h2{font-weight:800;font-size:clamp(1.2rem,2.6vw,1.55rem);margin:2.6rem 0 .9rem}
h3{font-weight:800;font-size:1.05rem;margin:0 0 .35rem}
p{margin:0 0 1rem}
strong{color:#fff}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
.top{border-bottom:1px solid var(--line);background:rgba(20,23,26,.9);backdrop-filter:blur(8px);position:sticky;top:0;z-index:20}
.top .wrap{display:flex;align-items:center;gap:.65rem;height:58px}
.brand{display:inline-flex;align-items:center;gap:.55rem;color:var(--fg)!important;text-decoration:none!important}
.brand img{width:28px;height:28px;border-radius:7px;display:block}
.brand b{font-family:"Archivo",sans-serif;font-weight:900;text-transform:uppercase;letter-spacing:.02em}
.top nav{margin-left:auto;display:flex;gap:1.1rem;font-family:"IBM Plex Mono",monospace;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase}
.top nav a{color:var(--mut)}
.top nav a.on{color:var(--accent)}
.top nav a.getapp{background:var(--accent);color:#0d0f11;font-weight:700;padding:.3rem .65rem;border-radius:8px;text-decoration:none;white-space:nowrap}
.crumbs{font-family:"IBM Plex Mono",monospace;font-size:.74rem;letter-spacing:.06em;color:var(--mut);margin:1.6rem 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:.35rem}
.crumbs li:not(:last-child)::after{content:"/";margin-left:.35rem;color:var(--line)}
.crumbs a{color:var(--mut)}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin:1.4rem 0 0}
.lede{font-size:1.08rem;color:#e7ebee;max-width:70ch}
.updated{color:var(--mut);font-family:"IBM Plex Mono",monospace;font-size:.74rem;letter-spacing:.06em}
.answer{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:1.1rem 1.3rem;margin:1.4rem 0;max-width:78ch}
.answer > b{display:block;font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin-bottom:.4rem}
.answer p:last-child{margin:0}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:1.4rem 0}
.facts div{background:var(--panel);padding:.85rem 1rem}
.facts dt{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.facts dd{margin:.2rem 0 0;font-weight:700;word-break:break-word}
.chips{display:flex;flex-wrap:wrap;gap:.45rem;margin:.6rem 0 0;padding:0;list-style:none}
.chip{font-family:"IBM Plex Mono",monospace;font-size:.76rem;border:1px solid var(--line);background:var(--panel2);border-radius:999px;padding:.25rem .7rem;color:var(--fg);cursor:pointer}
.chip b{color:var(--accent);margin-left:.3rem}
.chip[aria-pressed="true"]{border-color:var(--accent);background:rgba(255,154,31,.12)}
.dl{display:flex;flex-wrap:wrap;gap:.6rem;margin:1.2rem 0}
.btn{display:inline-flex;align-items:center;gap:.45rem;font-weight:700;font-size:.92rem;padding:.6rem 1rem;border-radius:9px;border:1px solid var(--line);background:var(--panel);color:var(--fg)!important;text-decoration:none!important}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--ink)!important}
.btn.app{border-color:var(--accent);color:var(--accent)!important}
.btn small{font-family:"IBM Plex Mono",monospace;font-weight:500;font-size:.68rem;opacity:.75}
.tools{display:flex;flex-wrap:wrap;gap:.7rem;align-items:center;margin:1rem 0 .4rem}
.search{flex:1 1 260px;font:inherit;color:var(--fg);background:var(--code);border:1px solid var(--line);border-radius:9px;padding:.65rem .85rem}
.search:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}
select.pick{font:inherit;font-weight:700;color:var(--fg);background:var(--code);border:1px solid var(--line);border-radius:9px;padding:.7rem .85rem;min-width:min(100%,320px)}
.count{color:var(--mut);font-family:"IBM Plex Mono",monospace;font-size:.76rem}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:.6rem 0 1rem;background:var(--panel2)}
table.pts{border-collapse:collapse;width:100%;font-size:.9rem;min-width:760px}
table.pts th,table.pts td{text-align:left;padding:.5rem .7rem;border-bottom:1px solid var(--line);vertical-align:top}
table.pts thead th{position:sticky;top:0;background:#20262c;font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:600;white-space:nowrap}
table.pts td.t{font-family:"IBM Plex Mono",monospace;white-space:nowrap;color:#cfe1f2}
table.pts td.i{font-family:"IBM Plex Mono",monospace;text-align:right}
table.pts td.n{font-weight:600}
table.pts td.d,table.pts td.s{color:var(--mut)}
table.pts tr:hover td{background:rgba(255,255,255,.025)}
.acc{font-family:"IBM Plex Mono",monospace;font-size:.72rem;border-radius:5px;padding:.08rem .4rem;border:1px solid var(--line);white-space:nowrap}
.acc.C{color:var(--accent);border-color:rgba(255,154,31,.5)}
.acc.W{color:var(--ok);border-color:rgba(95,211,141,.45)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem;margin:1rem 0;padding:0;list-style:none}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:12px;padding:1.05rem 1.1rem;color:var(--fg)!important;text-decoration:none!important;height:100%}
.card:hover{border-color:var(--accent)}
.card .k{font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.card h3{margin:.35rem 0 .3rem;font-size:1.08rem}
.card p{color:var(--mut);font-size:.9rem;margin:0}
.card .meta{margin-top:.6rem;font-family:"IBM Plex Mono",monospace;font-size:.72rem;color:var(--mut)}
.notes{margin:0;padding-left:1.2rem}
.notes li{margin:.35rem 0}
.callout{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:1rem 1.2rem;margin:1.5rem 0;max-width:78ch}
.callout p:last-child{margin:0}
.faq details{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.8rem 1rem;margin:.6rem 0;max-width:78ch}
.faq summary{cursor:pointer;font-weight:700}
.faq details p{margin:.6rem 0 0;color:#dfe4e8}
.ibgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem;margin:1.2rem 0}
.ib{background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:12px;padding:1rem 1.1rem}
.ib p{margin:0;color:#dfe4e8;font-size:.95rem}
.integ h3{margin-top:1.4rem}
table.pts.min{min-width:560px}
.facets{display:flex;flex-wrap:wrap;gap:.5rem 1.2rem;align-items:center;margin:.2rem 0 .8rem}
.facets .lbl{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.facets .chips{margin:0}
select.mini{font:inherit;font-size:.85rem;color:var(--fg);background:var(--code);border:1px solid var(--line);border-radius:9px;padding:.45rem .6rem}
select.sortm{display:none}
table.cmp{border-collapse:collapse;width:100%;font-size:.92rem}
table.cmp th,table.cmp td{text-align:left;padding:.55rem .8rem;border-bottom:1px solid var(--line);vertical-align:middle}
table.cmp thead th{background:#20262c;font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);font-weight:600;white-space:nowrap}
table.cmp thead th button{all:unset;cursor:pointer;color:inherit}
table.cmp thead th button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
table.cmp thead th button::after{content:" \\2195";opacity:.35}
table.cmp thead th[aria-sort="ascending"] button,table.cmp thead th[aria-sort="descending"] button{color:var(--accent)}
table.cmp thead th[aria-sort="ascending"] button::after{content:" \\2191";opacity:1}
table.cmp thead th[aria-sort="descending"] button::after{content:" \\2193";opacity:1}
table.cmp tbody tr:nth-child(even) td{background:rgba(255,255,255,.015)}
table.cmp tbody tr:hover td{background:rgba(255,154,31,.05)}
table.cmp td.mf{font-weight:700;white-space:nowrap}
table.cmp td.md a{font-weight:700;color:var(--fg)}
table.cmp td.md a:hover{color:var(--accent)}
table.cmp td.md small{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:var(--mut);font-size:.8rem;line-height:1.35;margin-top:.15rem}
table.cmp td.md .doc{font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:#7d8790}
.tag{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:.68rem;border:1px solid var(--line);border-radius:5px;padding:.05rem .4rem;margin:.1rem .25rem .1rem 0;color:#cfe1f2;white-space:nowrap}
table.cmp td.num{font-family:"IBM Plex Mono",monospace;text-align:right;white-space:nowrap}
table.cmp th.num{text-align:right}
.bar{display:block;height:4px;border-radius:2px;background:var(--line);margin-top:.3rem;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent)}
.bar.w i{background:var(--ok)}
table.cmp td.dls{white-space:nowrap}
table.cmp td.dls a{font-family:"IBM Plex Mono",monospace;font-size:.72rem;border:1px solid var(--line);border-radius:6px;padding:.15rem .45rem;margin-right:.3rem;color:var(--fg)}
table.cmp td.dls a:hover{border-color:var(--accent);text-decoration:none}
@media (max-width:760px){
  table.cmp thead{display:none}
  table.cmp,table.cmp tbody,table.cmp td{display:block;width:100%}
  table.cmp tr{display:grid;grid-template-columns:1fr 1fr;gap:.2rem .8rem;padding:.75rem .9rem;border-bottom:1px solid var(--line)}
  table.cmp td{border:0;padding:0;background:none!important}
  table.cmp td.mf{grid-column:1/-1;font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}
  table.cmp td.md,table.cmp td.ty,table.cmp td.dls{grid-column:1/-1}
  table.cmp td.ty:empty{display:none}
  table.cmp td.num{text-align:left}
  table.cmp td.num::before{content:attr(data-l) " ";color:var(--mut)}
  table.cmp td.num .bar{display:none}
  select.sortm{display:inline-block}
}
.hn{font-family:"IBM Plex Mono",monospace;font-size:.8rem;font-weight:500;color:var(--mut);margin-left:.4rem;vertical-align:middle}
table.lst{border-collapse:collapse;width:100%;font-size:.92rem}
table.lst th,table.lst td{text-align:left;padding:.55rem .8rem;border-bottom:1px solid var(--line);vertical-align:middle}
table.lst thead th{background:#20262c;font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);font-weight:600;white-space:nowrap}
table.lst tbody tr:nth-child(even)>*{background:rgba(255,255,255,.015)}
table.lst tbody tr:hover>*{background:rgba(255,154,31,.05)}
table.lst tbody tr:last-child>*{border-bottom:0}
table.lst tbody th{font-weight:700;white-space:nowrap}
table.lst tbody th a{color:var(--fg)}
table.lst tbody th a:hover{color:var(--accent)}
table.lst .num{font-family:"IBM Plex Mono",monospace;text-align:right;white-space:nowrap;width:1%}
table.lst td.mk{color:var(--mut);font-size:.86rem}
table.lst td.mk span,table.lst .via{font-family:"IBM Plex Mono",monospace;font-size:.72rem;color:#7d8790}
@media (max-width:760px){
  table.lst thead{display:none}
  table.lst,table.lst tbody,table.lst tr,table.lst th,table.lst td{display:block;width:100%}
  table.lst tr{display:flex;flex-wrap:wrap;align-items:baseline;gap:.15rem .9rem;padding:.65rem .9rem;border-bottom:1px solid var(--line)}
  table.lst tbody tr:last-child{border-bottom:0}
  table.lst th,table.lst td{border:0;padding:0;background:none!important}
  table.lst tbody th{flex:1 1 auto;width:auto;white-space:normal}
  table.lst .num{width:auto;text-align:left;color:var(--mut);font-size:.78rem}
  table.lst .num::before{content:attr(data-l) " "}
  table.lst td.mk,table.lst td.ty{order:5;flex-basis:100%}
}
.hidden{display:none!important}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.fbar{padding:.2rem 0 .5rem;margin:.6rem 0 0}
.frow{display:flex;gap:.55rem;align-items:center;flex-wrap:wrap}
.sbox{position:relative;flex:1 1 260px;display:flex}
.sbox .search{flex:1;padding:.55rem 2.2rem .55rem .8rem}
.sclear{position:absolute;right:.35rem;top:50%;transform:translateY(-50%);width:1.7rem;height:1.7rem;border:0;border-radius:6px;background:transparent;color:var(--mut);font-size:1.15rem;cursor:pointer}
.sclear:hover{color:var(--fg);background:var(--panel)}
.fbtn,.freset,.tog,.tgl,.seg button,.linkbtn{font:inherit;cursor:pointer}
.fbtn{display:none;align-items:center;gap:.4rem;font-family:"IBM Plex Mono",monospace;font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--fg);background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:.55rem .8rem}
.fbtn b,.tog b,.seg b{font-weight:600;color:var(--accent);margin-left:.35rem}
.fbtn b{margin:0;background:var(--accent);color:var(--ink);border-radius:999px;padding:0 .4rem;font-size:.68rem}
.freset{font-family:"IBM Plex Mono",monospace;font-size:.72rem;color:var(--accent);background:none;border:1px solid rgba(255,154,31,.45);border-radius:8px;padding:.3rem .65rem}
.freset:hover{background:rgba(255,154,31,.1)}
.fpanel{display:flex;flex-wrap:wrap;gap:.45rem 1.4rem;align-items:center;margin-top:.55rem}
.fg{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}
.fl{font-family:"IBM Plex Mono",monospace;font-size:.64rem;letter-spacing:.16em;text-transform:uppercase;color:var(--mut)}
.fc{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}
.tg{display:inline-flex;align-items:center;gap:.25rem;padding:.12rem .3rem .12rem .15rem;border:1px dashed var(--line);border-radius:999px}
.tgl{font-family:"IBM Plex Mono",monospace;font-size:.66rem;color:var(--mut);background:none;border:0;padding:.15rem .35rem;border-radius:999px}
button.tgl:hover{color:var(--fg)}
.fbar .chip{padding:.18rem .55rem;font-size:.72rem}
.chip:hover,.tog:hover,.seg button:hover{border-color:#4a535c}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;background:var(--panel2)}
.seg button{font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--mut);background:none;border:0;border-left:1px solid var(--line);padding:.32rem .6rem}
.seg button:first-child{border-left:0}
.seg button[aria-checked="true"]{background:rgba(255,154,31,.14);color:var(--fg)}
.tog{font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--mut);background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:.3rem .6rem}
.tog::before{content:"";display:inline-block;width:.55rem;height:.55rem;border:1px solid var(--mut);border-radius:2px;margin-right:.4rem;vertical-align:-1px}
.tog[aria-pressed="true"]{color:var(--fg);border-color:var(--accent)}
.tog[aria-pressed="true"]::before{background:var(--accent);border-color:var(--accent)}
.fbar select.mini{font-size:.78rem;padding:.3rem .5rem;max-width:12rem}
.chip:focus-visible,.tog:focus-visible,.seg button:focus-visible,.tgl:focus-visible,.fbtn:focus-visible,.freset:focus-visible,table.pts th button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
table.pts th button{all:unset;cursor:pointer;color:inherit}
table.pts th button::after{content:" \\2195";opacity:.3}
table.pts th[aria-sort="ascending"] button,table.pts th[aria-sort="descending"] button{color:#fff}
table.pts th[aria-sort="ascending"] button::after{content:" \\2191";opacity:1}
table.pts th[aria-sort="descending"] button::after{content:" \\2193";opacity:1}
table.pts th.r{text-align:right}
.minmark{display:inline-block;margin-left:.35rem;font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink);background:var(--accent);border-radius:4px;padding:0 .25rem;vertical-align:1px}
table.pts.compact td{padding:.28rem .6rem;font-size:.84rem}
table.pts.compact td.d,table.pts.compact td.s{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:20rem}
table.pts.compact td.n{white-space:nowrap}
table.pts.compact tr:hover td.d,table.pts.compact tr:hover td.s{white-space:normal}
/* Phones: a 7-column table squeezed to 375px gave one-word-wide cells and
   rows hundreds of pixels tall. Each point becomes a card instead; the
   sortable headings stay as a row of sort buttons above the cards. */
@media (max-width:760px){
  table.pts,table.pts.min{min-width:0}
  table.pts,table.pts tbody,table.pts thead{display:block}
  table.pts thead tr{display:flex;flex-wrap:wrap;gap:.35rem 1.1rem;padding:.65rem .9rem;border-bottom:1px solid var(--line);background:#20262c}
  table.pts thead th{border:0;padding:0;position:static;background:none}
  table.pts thead th:not(:has(button)){display:none}
  table.pts.min thead{display:none}
  table.pts tbody tr{display:grid;grid-template-columns:auto 1fr auto;align-items:baseline;gap:.2rem .7rem;padding:.7rem .9rem;border-bottom:1px solid var(--line)}
  table.pts tbody tr:last-child{border-bottom:0}
  table.pts td{display:block;border:0;padding:0;background:none!important}
  table.pts td:empty{display:none}
  table.pts td.i{text-align:left;color:#cfe1f2}
  table.pts td.n,table.pts td.d,table.pts td.u,table.pts td.s{grid-column:1/-1}
  table.pts:not(.min) td:nth-child(6){grid-column:3;grid-row:1}
  table.pts td.u::before{content:"Units: ";color:var(--mut)}
  table.pts td.s::before{content:"States: ";color:var(--mut)}
  table.pts td.s{font-size:.84rem}
  table.pts.compact td.d,table.pts.compact td.s{max-width:none}
  table.pts.min td.t{grid-column:1/3;grid-row:1}
  table.pts.min td:nth-child(4){grid-column:3;grid-row:1}
  table.pts.min td.n,table.pts.min td:nth-child(3){grid-column:1/-1}
  table.pts.min td:nth-child(3){color:var(--mut);font-size:.9rem}
}
.fnone{color:var(--mut);margin:.4rem 0 1rem}
.linkbtn{background:none;border:0;padding:0;color:var(--accent);text-decoration:underline}
@media (max-width:640px){
  .fbtn{display:inline-flex}
  .fpanel{display:none;flex-direction:column;align-items:stretch;gap:.7rem;padding:.7rem;border:1px solid var(--line);border-radius:10px;background:var(--panel2)}
  .fbar.open .fpanel{display:flex}
  .fg{align-items:flex-start;flex-direction:column;gap:.35rem}
  .count{order:3;flex-basis:100%}
  .seg{display:flex;flex-wrap:wrap;max-width:100%}
  .seg button{flex:1 1 auto;white-space:nowrap;border-top:1px solid var(--line);margin-top:-1px}
  .fbar select.mini{max-width:100%}
}
.share{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:1.1rem 1.3rem;margin:3rem 0 0;max-width:78ch}
.share p{margin:0}
.share b{color:#fff}
footer{border-top:1px solid var(--line);margin-top:3.5rem;padding:2rem 0 3rem;color:var(--mut);font-size:.9rem}
footer a{color:var(--mut);text-decoration:underline}
@media (max-width:640px){.top nav a:not(.getapp){display:none}body{font-size:16px}}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800;900&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">')


def shell(relpath, title, description, h1_html, body, jsonld, crumbs, og_type="website"):
    url = clean(relpath)
    crumb_html = "".join(
        '<li><a href="%s">%s</a></li>' % (esc(href), esc(name)) if href else
        '<li aria-current="page">%s</li>' % esc(name)
        for name, href in crumbs)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(url)s">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta name="theme-color" content="#14171a">
<link rel="icon" type="image/svg+xml" href="/icon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="%(ogtype)s">
<meta property="og:site_name" content="Easy BACnet">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(base)s/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(base)s/img/og-image.png">
%(fonts)s
<style>%(css)s</style>
<script type="application/ld+json">
%(jsonld)s
</script>
</head>
<body>
<div class="top"><div class="wrap">
  <a class="brand" href="/index.html"><img src="/icon.svg" alt="" width="28" height="28"><b>Easy BACnet</b></a>
  <nav aria-label="Site"><a href="/bacnet-points-lists/index.html" class="on">Points lists</a><a href="/index.html#guides">Guides</a><a href="/index.html">The app</a><a class="getapp" href="%(play_nav)s" rel="noopener">Get the app</a></nav>
</div></div>
<main class="wrap">
<ol class="crumbs" aria-label="Breadcrumb">%(crumbs)s</ol>
%(h1)s
%(body)s
<aside class="share">
  <p><b>Have a list to share?</b> Got a BACnet points list, PICS or integration notes for
  equipment that isn&rsquo;t here, or a newer version of one that is? Send it to us at
  <a href="mailto:Firstimpactdevelopment@gmail.com?subject=Points%%20list%%20to%%20share">Firstimpactdevelopment@gmail.com</a>
  and we&rsquo;ll add it to the library.</p>
</aside>
</main>
<footer><div class="wrap">
  <p>Points lists are re-typed from each manufacturer&rsquo;s free public documentation and linked to the original.
  Point availability varies by firmware, options and configuration &mdash; always confirm against the live device.
  Brand names identify the equipment only; Easy BACnet is not affiliated with any manufacturer listed.
  Spotted an error, or want a list removed? Email <a href="mailto:Firstimpactdevelopment@gmail.com">Firstimpactdevelopment@gmail.com</a>.</p>
  <p><a href="/index.html">Easy BACnet</a> &middot; <a href="%(play_footer)s" rel="noopener">Get it on Google Play</a> &middot;
  <a href="/bacnet-points-lists/index.html">Points lists</a> &middot;
  <a href="/index.html#guides">Guides</a> &middot; <a href="/terms.html">Terms of use</a> &middot; <a href="/privacy.html">Privacy policy</a></p>
</div></footer>
%(script)s
</body>
</html>
""" % {
        "title": esc(title), "desc": esc(description), "url": url, "base": BASE_URL,
        "ogtype": og_type, "fonts": FONTS, "css": CSS, "jsonld": jsonld,
        "crumbs": crumb_html, "h1": h1_html, "body": body, "script": FILTER_JS,
        "play_nav": PLAY_URL % "nav", "play_footer": PLAY_URL % "footer",
    }


# One small script for every page: free-text filter + object-type chips on a
# points table, free-text filter on card grids, and the manufacturer picker.
# Pages are fully rendered without it (crawlers and no-JS readers see all rows).
FILTER_JS = """<script>
(function(){
  var pick=document.getElementById('mfr-pick');
  if(pick){pick.addEventListener('change',function(){if(pick.value)location.href=pick.value;});}
  document.querySelectorAll('[data-filter]').forEach(function(box){
    var scope=document.getElementById(box.getAttribute('data-filter'));if(!scope)return;
    var rows=[].slice.call(scope.querySelectorAll('[data-row]'));
    var chips=[].slice.call(document.querySelectorAll('[data-chip-for="'+scope.id+'"]'));
    var out=document.querySelector('[data-count-for="'+scope.id+'"]');
    var type='';
    function run(){
      var q=box.value.trim().toLowerCase(),n=0;
      rows.forEach(function(r){
        var ok=(!q||r.textContent.toLowerCase().indexOf(q)>=0)&&(!type||r.getAttribute('data-type')===type);
        r.classList.toggle('hidden',!ok);if(ok)n++;
      });
      if(out)out.textContent=n+' of '+rows.length+' shown';
    }
    chips.forEach(function(c){c.addEventListener('click',function(){
      var t=c.getAttribute('data-type');type=(type===t)?'':t;
      chips.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-type')===type?'true':'false');});run();});});
    box.addEventListener('input',run);
  });
  (function(){
    var T=document.getElementById('pts'),bar=document.getElementById('pts-fbar');if(!T||!bar)return;
    var tb=T.tBodies[0],rows=[].slice.call(tb.rows),ths=[].slice.call(T.tHead.rows[0].cells);
    var q=document.getElementById('pts-q'),clr=document.getElementById('pts-clear'),us=document.getElementById('pts-u');
    var out=document.getElementById('pts-count'),rst=document.getElementById('pts-reset'),none=document.getElementById('pts-none');
    var fb=document.getElementById('pts-fbtn'),nact=document.getElementById('pts-nact');
    var chips=[].slice.call(bar.querySelectorAll('[data-t]')),grps=[].slice.call(bar.querySelectorAll('[data-g]'));
    var segs=[].slice.call(bar.querySelectorAll('[data-a]')),togs=[].slice.call(bar.querySelectorAll('[data-x]'));
    var S={types:{},acc:'',unit:'*',min:false,st:false,cmp:false,sort:''};
    rows.forEach(function(r){r._t=r.textContent.toLowerCase();});
    function apply(){
      var s=q.value.trim().toLowerCase(),ty=Object.keys(S.types),n=0;
      rows.forEach(function(r){
        var a=r.getAttribute('data-acc');
        var ok=(!s||r._t.indexOf(s)>=0)&&(!ty.length||S.types[r.getAttribute('data-type')])&&
          (!S.acc||S.acc.indexOf(a)>=0)&&(S.unit==='*'||r.getAttribute('data-u')===S.unit)&&
          (!S.min||r.hasAttribute('data-min'))&&(!S.st||r.hasAttribute('data-st'));
        r.classList.toggle('hidden',!ok);if(ok)n++;
      });
      T.classList.toggle('compact',S.cmp);
      out.textContent=n+' of '+rows.length+' shown';
      var act=ty.length+(S.acc?1:0)+(S.unit!=='*'?1:0)+(S.min?1:0)+(S.st?1:0);
      nact.hidden=!act;nact.textContent=act;
      rst.hidden=!(act||s||S.cmp||S.sort);clr.hidden=!s;none.hidden=n>0;
      chips.forEach(function(c){c.setAttribute('aria-pressed',S.types[c.getAttribute('data-t')]?'true':'false');});
      segs.forEach(function(b){b.setAttribute('aria-checked',b.getAttribute('data-a')===S.acc?'true':'false');});
      togs.forEach(function(b){b.setAttribute('aria-pressed',S[b.getAttribute('data-x')]?'true':'false');});
      if(us)us.value=S.unit;
      save(s);
    }
    function key(r,k){
      if(k==='t')return [+r.getAttribute('data-to'),+(r.getAttribute('data-i')||0)];
      if(k==='i')return [+(r.getAttribute('data-i')||-1),0];
      if(k==='a')return ['RWC'.indexOf(r.getAttribute('data-acc')),+r.getAttribute('data-o')];
      if(k==='u')return [r.getAttribute('data-u').toLowerCase(),+r.getAttribute('data-o')];
      return [r.cells[2].textContent.toLowerCase(),0];
    }
    function sort(){
      var p=S.sort.split(':'),k=p[0],d=p[1]==='d'?-1:1;
      ths.forEach(function(h){var b=h.querySelector('button');if(b)h.setAttribute('aria-sort',b.getAttribute('data-k')===k?(d>0?'ascending':'descending'):'none');});
      rows.slice().sort(function(x,y){
        if(!k)return x.getAttribute('data-o')-y.getAttribute('data-o');
        var a=key(x,k),b=key(y,k);
        for(var i=0;i<2;i++){if(a[i]<b[i])return -d;if(a[i]>b[i])return d;}return 0;
      }).forEach(function(r){tb.appendChild(r);});
    }
    function save(s){
      try{var u=new URL(location.href),P=u.searchParams;
        ['q','type','access','units','min','states','compact','sort'].forEach(function(x){P.delete(x);});
        if(s)P.set('q',s);var ty=Object.keys(S.types);if(ty.length)P.set('type',ty.join(','));
        if(S.acc)P.set('access',S.acc);if(S.unit!=='*')P.set('units',S.unit);
        if(S.min)P.set('min','1');if(S.st)P.set('states','1');if(S.cmp)P.set('compact','1');if(S.sort)P.set('sort',S.sort);
        history.replaceState(null,'',u.pathname+(P.toString()?'?'+P.toString():'')+u.hash);}catch(e){}
    }
    try{var P=new URLSearchParams(location.search);
      if(P.get('q'))q.value=P.get('q');
      (P.get('type')||'').split(',').forEach(function(t){if(t&&bar.querySelector('[data-t="'+t+'"]'))S.types[t]=1;});
      if(P.get('access')&&bar.querySelector('[data-a="'+P.get('access')+'"]'))S.acc=P.get('access');
      if(P.has('units')&&us){var v=P.get('units');if([].some.call(us.options,function(o){return o.value===v;}))S.unit=v;}
      S.min=P.get('min')==='1'&&!!bar.querySelector('[data-x="min"]');S.st=P.get('states')==='1'&&!!bar.querySelector('[data-x="st"]');
      S.cmp=P.get('compact')==='1';S.sort=P.get('sort')||'';
      if(S.sort)sort();}catch(e){}
    chips.forEach(function(c){c.addEventListener('click',function(){var t=c.getAttribute('data-t');
      if(S.types[t])delete S.types[t];else S.types[t]=1;apply();});});
    grps.forEach(function(g){g.addEventListener('click',function(){var ts=g.getAttribute('data-g').split(' ');
      var all=ts.every(function(t){return S.types[t];});ts.forEach(function(t){if(all)delete S.types[t];else S.types[t]=1;});apply();});});
    segs.forEach(function(b){b.addEventListener('click',function(){S.acc=b.getAttribute('data-a');apply();});});
    togs.forEach(function(b){b.addEventListener('click',function(){var x=b.getAttribute('data-x');S[x]=!S[x];apply();});});
    if(us)us.addEventListener('change',function(){S.unit=us.value;apply();});
    ths.forEach(function(h){var b=h.querySelector('button');if(!b)return;b.addEventListener('click',function(){
      var k=b.getAttribute('data-k'),p=S.sort.split(':');
      S.sort=p[0]!==k?k+':a':(p[1]==='a'?k+':d':'');sort();apply();});});
    q.addEventListener('input',apply);
    q.addEventListener('keydown',function(e){if(e.key==='Escape'){q.value='';apply();}});
    clr.addEventListener('click',function(){q.value='';apply();q.focus();});
    function reset(){q.value='';S={types:{},acc:'',unit:'*',min:false,st:false,cmp:false,sort:''};sort();apply();}
    rst.addEventListener('click',reset);
    [].forEach.call(document.querySelectorAll('[data-reset]'),function(b){b.addEventListener('click',reset);});
    fb.addEventListener('click',function(){var o=bar.classList.toggle('open');fb.setAttribute('aria-expanded',o?'true':'false');});
    document.addEventListener('keydown',function(e){
      if(e.key==='/'&&!/input|select|textarea/i.test((document.activeElement||{}).tagName||'')){e.preventDefault();q.focus();}});
    apply();
  })();
  var t=document.getElementById('cmp');if(!t)return;
  var tb=t.tBodies[0],rows=[].slice.call(tb.rows),ths=[].slice.call(t.tHead.rows[0].cells);
  var q=document.getElementById('cmp-q'),mf=document.getElementById('cmp-mf'),sm=document.getElementById('cmp-sort');
  var out=document.getElementById('cmp-count'),kchips=[].slice.call(document.querySelectorAll('[data-kind]')),kind='';
  function filt(){
    var s=q.value.trim().toLowerCase(),n=0;
    rows.forEach(function(r){
      var ok=(!s||r.textContent.toLowerCase().indexOf(s)>=0)&&(!mf.value||r.getAttribute('data-mf')===mf.value)&&
        (!kind||(' '+r.getAttribute('data-kinds')+' ').indexOf(' '+kind+' ')>=0);
      r.classList.toggle('hidden',!ok);if(ok)n++;
    });
    out.textContent=n+' of '+rows.length+' shown';
  }
  function sortBy(k,dir){
    var num=k==='o'||k==='w';
    ths.forEach(function(h){if(h.getAttribute('data-k'))h.setAttribute('aria-sort',h.getAttribute('data-k')===k?dir:'none');});
    rows.sort(function(a,b){
      var x=a.getAttribute('data-'+k),y=b.getAttribute('data-'+k),c=num?(+x)-(+y):x.localeCompare(y);
      return dir==='ascending'?c:-c;
    });
    rows.forEach(function(r){tb.appendChild(r);});
    if(sm)sm.value=k+':'+dir;
  }
  ths.forEach(function(h){var b=h.querySelector('button'),k=h.getAttribute('data-k');if(!b)return;
    b.addEventListener('click',function(){var cur=h.getAttribute('aria-sort'),num=k==='o'||k==='w';
      sortBy(k,cur==='none'?(num?'descending':'ascending'):(cur==='ascending'?'descending':'ascending'));});});
  kchips.forEach(function(c){c.addEventListener('click',function(){
    var k=c.getAttribute('data-kind');kind=(kind===k)?'':k;
    kchips.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-kind')===kind?'true':'false');});filt();});});
  q.addEventListener('input',filt);mf.addEventListener('change',filt);
  if(sm)sm.addEventListener('change',function(){var p=sm.value.split(':');sortBy(p[0],p[1]);});
})();
</script>"""


def graph(*nodes):
    return json.dumps({"@context": "https://schema.org", "@graph": list(nodes)},
                      ensure_ascii=False, indent=1).replace("</", "<\\/")


def breadcrumb_ld(crumbs, last_url):
    items = []
    for i, (name, href) in enumerate(crumbs, 1):
        u = clean(href.lstrip("/")) if href else last_url
        items.append({"@type": "ListItem", "position": i, "name": name, "item": u})
    return {"@type": "BreadcrumbList", "itemListElement": items}


ORG = {"@type": "Organization", "@id": BASE_URL + "/#org", "name": "Easy BACnet",
       "url": BASE_URL + "/", "logo": BASE_URL + "/logo-512.png"}


# ---------------------------------------------------------------------------
# Equipment categories (cross-manufacturer landing pages)
# ---------------------------------------------------------------------------

# (slug, plural heading, singular noun, keywords matched against equipment_type) - first match wins.
CATEGORIES = [
    ("dehumidifiers", "Dehumidifiers", "dehumidifier", ["dehumidif"]),
    ("humidifiers", "Humidifiers", "humidifier", ["humidif", "evaporative cooler", "reverse osmosis"]),
    ("cooling-towers", "Cooling towers & fluid coolers", "cooling tower", ["cooling tower", "fluid cooler"]),
    ("chillers", "Chillers", "chiller", ["chiller"]),
    ("heat-pumps", "Heat pumps", "heat pump", ["heat pump"]),
    ("vrf-split-ac", "VRF & split air conditioners", "VRF / split AC", ["vrf", "vrv", "split"]),
    ("rooftop-ahu-doas", "Rooftop units, AHUs & DOAS", "rooftop / AHU", ["rooftop", "air handl", "self-contained", "make-up air", "energy recovery", "doas"]),
    ("boilers", "Boilers & water heaters", "boiler", ["boiler", "water heater"]),
    ("drives-pumps", "VFDs & pumps", "drive / pump", ["frequency drive", "pump", "vfd"]),
    ("valves-actuators", "Valves & actuators", "valve / actuator", ["valve", "actuator"]),
    ("terminal-units", "VAV boxes & fan coils", "terminal unit", ["vav", "fan coil", "diffuser", "terminal"]),
    ("sensors-thermostats", "Thermostats, sensors & meters", "sensor / thermostat", ["thermostat", "sensor", "room", "airflow", "meter"]),
]
OTHER_CAT = ("other-equipment", "Other equipment", "equipment", [])


def category_of(m):
    et = (m.get("equipment_type") or "").lower()
    for c in CATEGORIES:
        if any(k in et for k in c[3]):
            return c
    return OTHER_CAT


def cat_path(cslug):
    return "%s/equipment/%s/index.html" % (ROOT, cslug)


def short_model(m):
    """Model name trimmed for <title>: explicit short_model, else drop parentheticals,
    ' - ' tails and a trailing 'BACnet' so titles stay near 60 characters."""
    if m.get("short_model"):
        return m["short_model"]
    if m.get("_full_title"):
        return re.sub(r"^%s\s+" % re.escape(m["manufacturer"]), "", m["model"], flags=re.I)
    s = re.sub(r"\s*\([^)]*\)", "", m["model"])
    s = re.sub(r"^%s\s+" % re.escape(m["manufacturer"]), "", s, flags=re.I)
    s = re.split(r"\s+[-\u2013]\s+", s)[0]
    s = re.sub(r"(?i)\s+bacnet(\s+(ip|module|option|gateway|controller))?$", "", s).strip()
    return s or m["model"]


def page_title(m, n):
    mm = "%s %s" % (m["manufacturer"], short_model(m))
    for t in ("%s BACnet Points List (%d Objects) | Easy BACnet" % (mm, n),
              "%s BACnet Points List | Easy BACnet" % mm,
              "%s BACnet Points List" % mm):
        if len(t) <= 62:
            return t
    if m.get("_full_title"):
        return "%s BACnet Points List" % mm
    out = ""
    for w in mm.split():
        if len(out) + len(w) + 1 > 40:
            break
        out = (out + " " + w).strip()
    return "%s BACnet Points List" % out


# Unit-type filter chips on each category page: (key, label, keywords matched against
# equipment_type). A model can carry several tags; the chip row is hidden under two tags.
CAT_TAGS = {
    "rooftop-ahu-doas": [("rtu", "Rooftop unit", ["rooftop"]), ("ahu", "Air handler", ["air handl", "ahu"]),
                         ("doas", "DOAS", ["doas"]), ("mua", "Make-up air", ["make-up air"]),
                         ("erv", "Energy recovery", ["energy recovery"]), ("sc", "Self-contained", ["self-contained"])],
    "drives-pumps": [("vfd", "Drive", ["frequency drive"]), ("pump", "Pump", ["pump"]),
                     ("card", "Option card / module", ["option card", "module"])],
    "boilers": [("boiler", "Boiler", ["boiler"]), ("wh", "Water heater", ["water heater"]),
                ("cond", "Condensing", ["condensing"])],
    "sensors-thermostats": [("room", "Room / thermostat", ["thermostat", "room"]), ("duct", "Duct / outdoor", ["duct"]),
                            ("meter", "Energy meter", ["meter"]), ("air", "Airflow", ["airflow"]),
                            ("flow", "Liquid flow", ["flow sensor"])],
    "valves-actuators": [("picv", "Control valve", ["control valve"]), ("em", "Energy meter", ["energy meter"]),
                         ("vav", "VAV actuator", ["vav"])],
    "terminal-units": [("vav", "VAV", ["vav"]), ("dd", "Dual duct", ["dual duct"]), ("fcu", "Fan coil", ["fan coil"]),
                       ("diff", "Diffuser", ["diffuser"])],
    "heat-pumps": [("wshp", "Water-source", ["water-source", "water source"]),
                   ("ww", "Water-to-water", ["water-to-water"])],
    "chillers": [("ac", "Air-cooled", ["air-cooled"]), ("wc", "Water-cooled", ["water-cooled"]),
                 ("screw", "Screw", ["screw"]), ("scroll", "Scroll", ["scroll"]),
                 ("cent", "Centrifugal", ["centrifugal"]), ("hp", "Heat pump", ["heat pump"])],
    "dehumidifiers": [("pool", "Indoor pool", ["pool"]), ("grow", "Grow room", ["grow room"]),
                      ("ind", "Industrial", ["industrial"]), ("oa", "Outdoor air / DOAS", ["outdoor air", "doas"])],
    "humidifiers": [("steam", "Steam", ["steam"]), ("evap", "Evaporative", ["evaporative"]),
                    ("hp", "High-pressure", ["high-pressure", "atomizing"]), ("hyb", "Hybrid", ["hybrid"]),
                    ("gw", "BACnet gateway", ["gateway"]), ("ro", "Water treatment", ["reverse osmosis"])],
    "vrf-split-ac": [("vrf", "VRF / VRV", ["vrf", "vrv"]), ("split", "Split AC", ["split"]),
                     ("gw", "Gateway / interface", ["gateway", "interface"]),
                     ("cc", "Central controller", ["central controller"])],
    "cooling-towers": [("ct", "Cooling tower", ["cooling tower"]), ("fc", "Fluid cooler", ["fluid cooler"])],
}


def tags_of(m, tags):
    et = (m.get("equipment_type") or "").lower()
    return [t for t in tags if any(k in et for k in t[2])]


def cat_row(m, tags, maxo, show_type=False):
    pts = m["points"]
    n, w = len(pts), writable_count(pts)
    mt = tags_of(m, tags)
    doc = m["source"].get("doc_number")
    return ('<tr data-mf="%(mf)s" data-md="%(md)s" data-o="%(n)d" data-w="%(w)d" data-kinds="%(kinds)s">'
            '<td class="mf">%(mf)s</td>'
            '<td class="md"><a href="/%(href)s">%(mfa)s%(md)s</a><small>%(ap)s%(doc)s</small>%(al)s</td>'
            '%(ty)s'
            '<td class="num" data-l="Objects">%(n)d<span class="bar" aria-hidden="true"><i style="width:%(po).0f%%"></i></span></td>'
            '<td class="num" data-l="Writable">%(w)d<span class="bar w" aria-hidden="true"><i style="width:%(pw).0f%%"></i></span></td>'
            '<td class="dls"><a href="/%(csv)s" aria-label="%(mf)s %(md)s CSV">CSV</a>'
            '<a href="/%(ede)s" aria-label="%(mf)s %(md)s EDE">EDE</a></td></tr>') % {
        "mf": esc(m["manufacturer"]), "md": esc(m["model"]), "n": n, "w": w,
        "mfa": "" if m["model"].lower().startswith(m["manufacturer"].lower()) else
               '<span class="sr-only">%s </span>' % esc(m["manufacturer"]),
        "kinds": category_of(m)[0] if show_type else " ".join(t[0] for t in mt), "href": model_path(m), "ap": esc(m.get("applies_to") or ""),
        "doc": (' <span class="doc">&middot; %s</span>' % esc(doc)) if doc else "",
        "al": ('<span class="sr-only"> Also known as: %s</span>' % esc(", ".join(m["aliases"])))
              if m.get("aliases") else "",
        "ty": ('<td class="ty">%s</td>' % "".join('<span class="tag">%s</span>' % esc(t[1]) for t in mt)) if tags else
              ('<td class="ty"><span class="tag">%s</span></td>' % esc(category_of(m)[1])) if show_type else "",
        "po": 100.0 * n / maxo, "pw": 100.0 * w / maxo,
        "csv": model_path(m, ".csv"), "ede": model_path(m, "-ede.csv")}


def cat_page(cat, models, all_cats):
    cslug, heading, noun, _ = cat
    models = sorted(models, key=lambda m: (m["manufacturer"].lower(), m["model"].lower()))
    tags = CAT_TAGS.get(cslug, [])
    relpath = cat_path(cslug)
    url = clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet points lists", "/" + hub_path()), (heading, None)]
    mfrs = sorted({m["manufacturer"] for m in models})
    maxo = max(len(m["points"]) for m in models) or 1
    chip_counts = [(t, sum(1 for m in models if t in tags_of(m, tags))) for t in tags]
    chip_counts = [tc for tc in chip_counts if tc[1]]
    if not chip_counts:
        tags = []
    title = "%s BACnet Points Lists | Easy BACnet" % heading.replace(" & ", " and ")
    if len(title) > 62:
        title = "%s BACnet Points Lists" % heading
    desc = ("Free BACnet points lists for %d %s models from %s: object types, instances, units, "
            "minimum BMS points and CSV/EDE downloads." % (
                len(models), noun, ", ".join(mfrs[:4]) + (" and more" if len(mfrs) > 4 else "")))
    if len(desc) > 160:
        desc = ("Free BACnet points lists for %d %s models: object types, instances, units, minimum BMS "
                "points and CSV/EDE downloads." % (len(models), noun))
    h1 = ('<p class="eyebrow">Equipment type</p><h1><span class="mfr">%s</span> BACnet points lists</h1>'
          '<p class="updated">Updated %s</p>' % (esc(heading), UPDATED_HUMAN))
    body = """
<p class="lede">%(n)d %(heading_l)s BACnet points lists from %(nm)d manufacturer%(nms)s &mdash; %(mfrs)s. Each one has the
full object table, the minimum points an integrator needs, enable and heartbeat notes, and CSV/EDE downloads.
Click a column heading to sort.</p>
<div class="tools"><input class="search" id="cmp-q" type="search" placeholder="Search model, part number or alias&hellip;"
 aria-label="Filter models">
<select class="mini" id="cmp-mf" aria-label="Manufacturer"><option value="">All manufacturers (%(nm)d)</option>%(opts)s</select>
<select class="mini sortm" id="cmp-sort" aria-label="Sort by"><option value="mf:ascending">Sort: manufacturer</option>
<option value="md:ascending">Sort: model</option><option value="o:descending">Sort: most objects</option>
<option value="w:descending">Sort: most writable</option></select>
<span class="count" id="cmp-count" aria-live="polite">%(n)d of %(n)d shown</span></div>
%(chips)s<div class="tablewrap"><table class="cmp" id="cmp"><thead><tr>
<th scope="col" data-k="mf" aria-sort="ascending"><button type="button">Manufacturer</button></th>
<th scope="col" data-k="md" aria-sort="none"><button type="button">Model</button></th>
%(tyh)s
<th scope="col" class="num" data-k="o" aria-sort="none"><button type="button">Objects</button></th>
<th scope="col" class="num" data-k="w" aria-sort="none"><button type="button">Writable</button></th>
<th scope="col">Download</th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
""" % {"n": len(models), "heading_l": esc(heading[0].lower() + heading[1:]), "nm": len(mfrs),
       "nms": "" if len(mfrs) == 1 else "s", "mfrs": esc(", ".join(mfrs)),
       "opts": "".join('<option>%s</option>' % esc(x) for x in mfrs),
       "chips": ('<div class="facets"><span class="lbl">Unit type</span><ul class="chips">%s</ul></div>\n'
                 % "".join('<li><button class="chip" type="button" data-kind="%s" aria-pressed="false">%s<b>%d</b>'
                           '</button></li>' % (t[0], esc(t[1]), c) for t, c in chip_counts)) if len(chip_counts) > 1 else "",
       "tyh": '<th scope="col">Type</th>' if tags else "",
       "rows": "".join(cat_row(m, tags, maxo) for m in models)}
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": clean(model_path(m)), "name": model_title(m)}
        for i, m in enumerate(models, 1)]}
    page_ld = {"@type": "CollectionPage", "@id": url, "url": url, "name": title, "description": desc,
               "dateModified": UPDATED, "isPartOf": {"@id": BASE_URL + "/#site"}, "mainEntity": item_list,
               "publisher": {"@id": ORG["@id"]}}
    return shell(relpath, title, desc, h1, body, graph(ORG, page_ld, breadcrumb_ld(crumbs, url)), crumbs)


def cat_item(cat, models):
    mf = sorted({m["manufacturer"] for m in models}, key=str.lower)
    return ('<tr><th scope="row"><a href="/%s">%s</a></th><td class="mk">%s</td><td class="num" data-l="Models">%d</td></tr>'
            % (cat_path(cat[0]), esc(cat[1]),
               esc(", ".join(mf[:6])) + (" <span>+%d more</span>" % (len(mf) - 6) if len(mf) > 6 else ""),
               len(models)))


def group_by_category(models):
    order = list(CATEGORIES) + [OTHER_CAT]
    buckets = {c[0]: [] for c in order}
    for m in models:
        buckets[category_of(m)[0]].append(m)
    return [(c, sorted(buckets[c[0]], key=lambda m: (m["manufacturer"].lower(), m["model"].lower())))
            for c in order if buckets[c[0]]]


# ---------------------------------------------------------------------------
# Model page
# ---------------------------------------------------------------------------

def access_label(a):
    return {"R": "Read", "W": "Write", "C": "Command"}[a]


def model_title(m):
    return "%s %s BACnet Points List" % (m["manufacturer"], m["model"])


def model_desc(m):
    n = len(m["points"])
    w = writable_count(m["points"])
    eq = m.get("equipment_type") or "equipment"
    mm = "%s %s" % (m["manufacturer"], short_model(m))
    integ = bool(m.get("integration"))
    for s in (
        "%s BACnet points list: %d objects (%d writable), minimum BMS points, enable and heartbeat notes, "
        "plus free CSV and EDE downloads." % (mm, n, w) if integ else None,
        "%s BACnet points list: %d objects (%d writable) with minimum BMS points and free CSV/EDE "
        "downloads." % (mm, n, w) if integ else None,
        "%s BACnet points list: %d objects (%d writable) for the %s. Object type, instance, name, units "
        "and access, plus free CSV and EDE downloads." % (mm, n, w, eq.lower()),
    ):
        if s and len(s) <= 160:
            return s
    return s[:157].rsplit(" ", 1)[0] + "..."


def source_line(m):
    s = m["source"]
    bits = [esc(s.get("title") or "Manufacturer documentation")]
    if s.get("doc_number"):
        bits.append(esc(s["doc_number"]))
    if s.get("revision_date"):
        bits.append("rev. " + esc(s["revision_date"]))
    return " &middot; ".join(bits)


def row_id(pt):
    return pt.get("_rid") or "obj-%s-%s" % (pt["type"].lower(), "" if pt.get("instance") is None else pt["instance"])


def assign_row_ids(points):
    used = set()
    for pt in points:
        base = "obj-%s-%s" % (pt["type"].lower(), "" if pt.get("instance") is None else pt["instance"])
        rid, n = base, 2
        while rid in used:
            rid, n = "%s-%d" % (base, n), n + 1
        used.add(rid)
        pt["_rid"] = rid


def parse_ref(ref):
    m = re.fullmatch(r"\s*([A-Za-z]+)[\s:_-]*(\d+)\s*", ref or "")
    return (m.group(1).upper(), int(m.group(2))) if m else None


def integration_of(m):
    """The validated integration block, or None. Drops minimum_points whose ref isn't in the list."""
    it = m.get("integration")
    if not isinstance(it, dict):
        return None
    index = {}
    for pt in m["points"]:
        index.setdefault((pt["type"].upper(), pt.get("instance")), pt)
    mins = []
    for mp in it.get("minimum_points") or []:
        key = parse_ref(mp.get("ref"))
        pt = index.get(key) if key else None
        if pt is None:
            print("  WARN %s %s: minimum point %r not in list" % (m["manufacturer"], m["model"], mp.get("ref")))
            continue
        mins.append((pt, (mp.get("why") or "").strip()))
    clean_it = {
        "summary": (it.get("summary") or "").strip(),
        "minimum_points": mins,
        "enable": (it.get("enable") or "").strip() or None,
        "heartbeat": (it.get("heartbeat") or "").strip() or None,
        "remote_sensors": (it.get("remote_sensors") or "").strip() or None,
        "setup": [x.strip() for x in it.get("setup") or [] if x and x.strip()],
        "gotchas": [x.strip() for x in it.get("gotchas") or [] if x and x.strip()],
    }
    if not (clean_it["summary"] or mins or clean_it["enable"] or clean_it["heartbeat"]):
        return None
    return clean_it


def integration_html(m):
    it = integration_of(m)
    if not it:
        return ""
    mfr, model = esc(m["manufacturer"]), esc(m["model"])
    out = ['<section class="integ" id="bms-integration"><h2>BMS integration notes: %s %s</h2>' % (mfr, model)]
    if it["summary"]:
        out.append('<div class="answer"><b>Integration in brief</b><p>%s</p></div>' % esc(it["summary"]))
    if it["minimum_points"]:
        rows = "".join(
            '<tr><td class="t"><a href="#%s">%s %s</a></td><td class="n">%s</td><td>%s</td>'
            '<td><span class="acc %s">%s</span></td></tr>' % (
                row_id(pt), esc(pt["type"]), "" if pt.get("instance") is None else pt["instance"],
                esc(pt["name"]), esc(why), pt["access"], access_label(pt["access"]))
            for pt, why in it["minimum_points"])
        out.append('<h3>Minimum points to map</h3><p class="count">The short list most integrators start with &mdash; '
                   'enough to run the unit from a BMS. Map more as the job needs.</p>'
                   '<div class="tablewrap"><table class="pts min"><thead><tr><th scope="col">Object</th>'
                   '<th scope="col">Name</th><th scope="col">Why</th><th scope="col">Access</th></tr></thead>'
                   '<tbody>%s</tbody></table></div>' % rows)
    blocks = [("Enable &amp; remote start", it["enable"]),
              ("Heartbeat &amp; communication loss", it["heartbeat"]),
              ("Sensors &amp; values from the BMS", it["remote_sensors"])]
    cards = "".join('<div class="ib"><h3>%s</h3><p>%s</p></div>' % (h, esc(t)) for h, t in blocks if t)
    if cards:
        out.append('<div class="ibgrid">%s</div>' % cards)
    if it["setup"]:
        out.append('<h3>Network setup</h3><ul class="notes">%s</ul>' % "".join("<li>%s</li>" % esc(x) for x in it["setup"]))
    if it["gotchas"]:
        out.append('<h3>Watch out for</h3><ul class="notes">%s</ul>' % "".join("<li>%s</li>" % esc(x) for x in it["gotchas"]))
    out.append("</section>")
    return "\n".join(out)


def min_point_ids(m):
    """ids of the point dicts named in the minimum list (by identity, so duplicate instances stay distinct)."""
    it = integration_of(m)
    return {id(pt) for pt, _ in it["minimum_points"]} if it else set()


def points_table(m, tid="pts"):
    rows = []
    mins = min_point_ids(m)
    for k, pt in enumerate(m["points"]):
        full = OBJECT_TYPES[pt["type"]][0]
        inst = "" if pt.get("instance") is None else str(pt["instance"])
        rows.append(
            '<tr data-row data-type="%s" data-to="%d" data-o="%d" data-i="%s" data-acc="%s" data-u="%s"%s%s id="%s">'
            '<td class="t"><abbr title="%s">%s</abbr>%s</td><td class="i">%s</td>'
            '<td class="n">%s</td><td class="d">%s</td><td class="u">%s</td>'
            '<td><span class="acc %s">%s</span></td><td class="s">%s</td></tr>'
            % (esc(pt["type"]), TYPE_ORDER.index(pt["type"]), k, inst, pt["access"], esc(pt["units"]),
               ' data-min="1"' if id(pt) in mins else "", ' data-st="1"' if pt["states"] else "",
               row_id(pt), esc(full), esc(pt["type"]),
               '<span class="minmark" title="In the minimum points list">min</span>' if id(pt) in mins else "",
               inst, esc(pt["name"]), esc(pt["description"]), esc(pt["units"]), pt["access"],
               access_label(pt["access"]), esc(pt["states"])))
    head = "".join(
        '<th scope="col"%s><button type="button" data-k="%s">%s</button></th>' % (cls, k, label)
        if k else '<th scope="col">%s</th>' % label
        for k, label, cls in (("t", "Type", ""), ("i", "Instance", ' class="r"'), ("n", "Object name", ""),
                              ("", "Description", ""), ("u", "Units", ""), ("a", "Access", ""), ("", "States", "")))
    return ('<div class="tablewrap"><table class="pts" id="%s">'
            '<caption class="sr-only">%s</caption>'
            '<thead><tr>%s</tr></thead><tbody>\n%s\n</tbody></table></div>'
            % (tid, esc(model_title(m)), head, "\n".join(rows)))


TYPE_GROUPS = (("Analog", ("AI", "AO", "AV")), ("Binary", ("BI", "BO", "BV")), ("Multi-state", ("MI", "MO", "MV")))


def filter_bar(m):
    """Compact filter toolbar for the full points table (wired up by FILTER_JS)."""
    pts = m["points"]
    n = len(pts)
    tc = dict(type_counts(pts))
    groups, used = [], set()
    for label, ts in TYPE_GROUPS:
        present = [t for t in ts if t in tc]
        if present:
            groups.append((label, present))
            used.update(present)
    other = [t for t, _ in type_counts(pts) if t not in used]
    if other:
        groups.append(("Other", other))

    def chip(t):
        return ('<button type="button" class="chip" data-t="%s" aria-pressed="false" title="%s">%s<b>%d</b></button>'
                % (t, esc(OBJECT_TYPES[t][0]), t, tc[t]))

    type_html = "".join(
        '<span class="tg">%s%s</span>' % (
            ('<button type="button" class="tgl" data-g="%s" title="Toggle all %s types">%s</button>'
             % (" ".join(ts), label.lower(), label)) if len(ts) > 1 else '<span class="tgl">%s</span>' % label,
            "".join(chip(t) for t in ts))
        for label, ts in groups)
    out = ['<div class="fg"><span class="fl">Type</span><div class="fc">%s</div></div>' % type_html]

    acc = {a: sum(1 for p in pts if p["access"] == a) for a in ("R", "W", "C")}
    if sum(1 for v in acc.values() if v) > 1:
        segs = [("", "All", n), ("R", "Read-only", acc["R"])]
        if acc["W"] and acc["C"]:
            segs.append(("WC", "Writable", acc["W"] + acc["C"]))
        if acc["W"]:
            segs.append(("W", "Write", acc["W"]))
        if acc["C"]:
            segs.append(("C", "Command", acc["C"]))
        out.append('<div class="fg"><span class="fl">Access</span><div class="seg" role="radiogroup" aria-label="Access">%s'
                   '</div></div>' % "".join(
                       '<button type="button" role="radio" data-a="%s" aria-checked="%s">%s<b>%d</b></button>'
                       % (k, "true" if not k else "false", label, c) for k, label, c in segs))

    units = {}
    for p in pts:
        units[p["units"]] = units.get(p["units"], 0) + 1
    if len([u for u in units if u]) > 1:
        opts = ['<option value="*">Any units</option>']
        if units.get(""):
            opts.append('<option value="">No units (%d)</option>' % units[""])
        opts += ['<option value="%s">%s (%d)</option>' % (esc(u), esc(u), c)
                 for u, c in sorted(units.items(), key=lambda x: (-x[1], x[0].lower())) if u]
        out.append('<div class="fg"><label class="fl" for="pts-u">Units</label>'
                   '<select class="mini" id="pts-u">%s</select></div>' % "".join(opts))

    toggles = []
    nmin = len(min_point_ids(m))
    if nmin:
        toggles.append(('min', "Minimum points", nmin))
    nst = sum(1 for p in pts if p["states"])
    if 0 < nst < n:
        toggles.append(('st', "Has states", nst))
    toggles.append(('cmp', "Compact rows", None))
    out.append('<div class="fg"><span class="fl">Show</span><div class="fc">%s</div></div>' % "".join(
        '<button type="button" class="tog" data-x="%s" aria-pressed="false">%s%s</button>'
        % (k, label, "" if c is None else "<b>%d</b>" % c) for k, label, c in toggles))

    return ('<div class="fbar" id="pts-fbar">'
            '<div class="frow"><div class="sbox"><input class="search" id="pts-q" type="search" autocomplete="off"'
            ' placeholder="Search name, description, units, states&hellip;  ( / )" aria-label="Search points">'
            '<button type="button" class="sclear" id="pts-clear" aria-label="Clear search" hidden>&times;</button></div>'
            '<button type="button" class="fbtn" id="pts-fbtn" aria-expanded="false" aria-controls="pts-panel">'
            'Filters<b id="pts-nact" hidden></b></button>'
            '<span class="count" id="pts-count" aria-live="polite">%d of %d shown</span>'
            '<button type="button" class="freset" id="pts-reset" hidden>Reset</button></div>'
            '<div class="fpanel" id="pts-panel">%s</div></div>' % (n, n, "".join(out)))


def model_faq(m):
    n = len(m["points"])
    w = writable_count(m["points"])
    tc = ", ".join("%d %s" % (c, OBJECT_TYPES[t][0].lower() + ("s" if c != 1 else ""))
                   for t, c in type_counts(m["points"]))
    s = m["source"]
    qa = [
        ("How many BACnet points does the %s %s have?" % (m["manufacturer"], m["model"]),
         "This list has %d BACnet objects: %s. The exact set on a given unit depends on its "
         "firmware, installed options and configuration." % (n, tc)),
        ("Which %s %s BACnet points are writable?" % (m["manufacturer"], m["model"]),
         (("%d of the %d objects accept a write. Points marked Command have a priority array: a write "
           "holds until it is released, so release it back to automatic when you are done." % (w, n))
          if w else "None of the listed objects are marked writable in the source documentation.")
         + (" The source has no read/write column, so this is inferred from object type."
            if m.get("access_inferred") else "")),
        ("Where is the official %s %s BACnet documentation?" % (m["manufacturer"], m["model"]),
         "The source is %s%s%s, published free by %s at %s." % (
             s.get("title") or "the manufacturer's BACnet documentation",
             (" (" + s["doc_number"] + ")") if s.get("doc_number") else "",
             (", revision " + s["revision_date"]) if s.get("revision_date") else "",
             m["manufacturer"], s["url"])),
    ] + integration_faq(m) + [
        ("How do I check these points on the real %s?" % m["model"],
         "Scan the network with a BACnet IP browser such as Easy BACnet, open the device and compare "
         "its object list with this table. Anything missing is usually an option that isn't installed "
         "or a point that is disabled in the controller's configuration."),
    ]
    return qa


def integration_faq(m):
    it = integration_of(m)
    if not it:
        return []
    mm = "%s %s" % (m["manufacturer"], m["model"])
    qa = []
    if it["minimum_points"]:
        qa.append(("What are the minimum BACnet points to integrate the %s?" % mm,
                   "Start with " + "; ".join(
                       "%s %s %s (%s)" % (pt["type"], "" if pt.get("instance") is None else pt["instance"],
                                         pt["name"], why.rstrip(".")) if why else
                       "%s %s %s" % (pt["type"], pt.get("instance"), pt["name"])
                       for pt, why in it["minimum_points"]) + "."))
    if it["enable"]:
        qa.append(("How do I enable BMS control of the %s?" % mm, it["enable"]))
    if it["heartbeat"]:
        qa.append(("Does the %s need a BACnet heartbeat or have a communication timeout?" % mm, it["heartbeat"]))
    if it["remote_sensors"]:
        qa.append(("Can the BMS supply sensor values to the %s?" % mm, it["remote_sensors"]))
    return qa


def model_page(m, siblings):
    relpath = model_path(m)
    url = clean(relpath)
    pts = m["points"]
    n, w = len(pts), writable_count(pts)
    mfr_href = "/" + mfr_path(m["manufacturer_slug"])
    crumbs = [("Home", "/index.html"), ("BACnet points lists", "/" + hub_path()),
              (m["manufacturer"], mfr_href), (m["model"], None)]
    title = page_title(m, n)
    desc = model_desc(m)
    s = m["source"]
    faq = model_faq(m)

    aliases = [a for a in (m.get("aliases") or []) if a and a != m["model"]]
    facts = [
        ("Manufacturer", '<a href="%s">%s</a>' % (mfr_href, esc(m["manufacturer"]))),
        ("Model", esc(m["model"])),
        ("Equipment", esc(m.get("equipment_type") or "")),
        ("BACnet objects", "%d (%d writable)" % (n, w)),
        ("Transport", esc(", ".join(m.get("bacnet_transport") or [])) or "&mdash;"),
        ("Firmware", esc(m.get("firmware") or "Not stated")),
    ]
    if m.get("default_device_instance") not in (None, ""):
        facts.append(("Default device instance", esc(m["default_device_instance"])))
    if aliases:
        facts.append(("Also known as", esc(", ".join(aliases))))
    cat = category_of(m)
    facts.insert(3, ("Equipment type", '<a href="/%s">%s</a>' % (cat_path(cat[0]), esc(cat[1]))))
    facts.append(("Source document", '<a href="%s" rel="nofollow noopener" target="_blank">%s</a>'
                  % (esc(s["url"]), source_line(m))))
    facts_html = '<dl class="facts">%s</dl>' % "".join(
        "<div><dt>%s</dt><dd>%s</dd></div>" % (k, v) for k, v in facts)

    notes = m.get("notes") or []
    notes_html = ""
    if notes:
        notes_html = "<h2>Integration notes</h2><ul class=\"notes\">%s</ul>" % "".join(
            "<li>%s</li>" % esc(x) for x in notes)

    sib = [x for x in siblings if x is not m]
    sib_html = ""
    if sib:
        sib_html = ('<h2>More %s BACnet points lists</h2><ul class="grid">%s</ul>'
                    % (esc(m["manufacturer"]), "".join(card(x) for x in sib)))

    faq_html = '<h2>Questions about the %s %s</h2><div class="faq">%s</div>' % (
        esc(m["manufacturer"]), esc(m["model"]),
        "".join("<details%s><summary>%s</summary><p>%s</p></details>"
                % (" open" if i == 0 else "", esc(q), esc(a)) for i, (q, a) in enumerate(faq)))

    h1 = ('<p class="eyebrow">%s &middot; BACnet points list</p>'
          '<h1><span class="mfr">%s</span> %s BACnet points list</h1>'
          '<p class="updated">Updated %s</p>' % (
              esc(m.get("equipment_type") or "Equipment"), esc(m["manufacturer"]), esc(m["model"]),
              UPDATED_HUMAN))

    base = "/" + model_path(m, "")
    body = """
<div class="answer"><b>Short answer</b><p>%(summary)s</p>
<p>This page lists <strong>%(n)d BACnet objects</strong> for the %(mfr)s %(model)s &mdash; %(w)d of them
writable &mdash; with each object&rsquo;s type, instance number, name, engineering units and access.
It is re-typed from %(mfr)s&rsquo;s own free documentation, linked below.</p></div>
%(facts)s
<div class="dl">
  <a class="btn primary" href="%(base)s.csv" download>Download CSV <small>%(n)d rows</small></a>
  <a class="btn" href="%(base)s-ede.csv" download>Download EDE <small>B.I.G.-EU</small></a>
  <a class="btn" href="%(base)s.json">JSON</a>
  <a class="btn" href="%(src)s" rel="nofollow noopener" target="_blank">Manufacturer PDF &#8599;</a>
  <a class="btn app" href="%(play_pdf)s" rel="noopener" target="_blank">Download Easy BACnet Mobile App <small>Google Play</small></a>
</div>
%(integ)s
<h2 id="points">%(mfr)s %(model)s BACnet objects</h2>
<p class="count">Type: <abbr title="Analog Input">AI</abbr>, AO, AV, BI, BO, BV, MI/MO/MV (multi-state) &middot;
Access: <span class="acc">Read</span> read-only, <span class="acc W">Write</span> writable,
<span class="acc C">Command</span> writable with a priority array.</p>
%(inferred)s%(fbar)s
%(table)s
<p class="fnone" id="pts-none" hidden>No points match these filters. <button type="button" class="linkbtn" data-reset>Clear filters</button></p>
%(notes)s
<div class="callout"><p><strong>Check it against the live device.</strong> A points list tells you what the
controller <em>can</em> expose; the unit in front of you may differ by firmware or installed options.
<a href="/index.html">Easy BACnet</a> scans a network for BACnet IP devices from an Android phone, reads every
object on the %(model)s and exports what it actually has to Excel &mdash; free. New to BACnet?
Start with <a href="/guides/what-is-a-bacnet-points-list.html">what a BACnet points list is</a> and
<a href="/guides/bacnet-object-types-explained.html">what the object types mean</a>.</p></div>
%(faq)s
%(sib)s
<p class="updated">Source: <a href="%(src)s" rel="nofollow noopener" target="_blank">%(srcline)s</a>.
Object names, instances and units are reproduced as published; descriptions are our own.</p>
""" % {
        "summary": esc(m.get("summary") or ""), "n": n, "w": w,
        "mfr": esc(m["manufacturer"]), "model": esc(m["model"]), "facts": facts_html,
        "base": base, "src": esc(s["url"]), "play_pdf": PLAY_URL % "pdf", "fbar": filter_bar(m), "table": points_table(m),
        "notes": notes_html, "faq": faq_html, "integ": integration_html(m),
        "inferred": ('<p class="count"><strong>Note:</strong> the source document has no read/write column, so access '
                     'here is inferred from the object type (inputs read-only, values writable). Confirm on the live '
                     'controller before writing.</p>') if m.get("access_inferred") else "", "sib": sib_html, "srcline": source_line(m),
    }

    keywords = [model_title(m), "%s %s BACnet objects" % (m["manufacturer"], m["model"]),
                "%s BACnet" % m["manufacturer"]] + ["%s BACnet points list" % a for a in aliases]
    dataset = {
        "@type": "Dataset", "@id": url + "#dataset", "name": model_title(m),
        "description": (m.get("summary") or "") + " " + desc,
        "url": url, "keywords": keywords, "isAccessibleForFree": True,
        "creator": {"@id": ORG["@id"]}, "publisher": {"@id": ORG["@id"]},
        "dateModified": UPDATED,
        "isBasedOn": {"@type": "CreativeWork", "name": s.get("title") or "", "url": s["url"],
                      "author": {"@type": "Organization", "name": m["manufacturer"]}},
        "about": {"@type": "Product", "name": "%s %s" % (m["manufacturer"], m["model"]),
                  "brand": {"@type": "Brand", "name": m["manufacturer"]},
                  "category": m.get("equipment_type") or ""},
        "variableMeasured": ["Object type", "Object instance", "Object name", "Engineering units",
                             "Access (read / write / command)", "State text"],
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE_URL + base + ".csv"},
            {"@type": "DataDownload", "encodingFormat": "text/csv", "name": "EDE (B.I.G.-EU)",
             "contentUrl": BASE_URL + base + "-ede.csv"},
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASE_URL + base + ".json"},
        ],
        "includedInDataCatalog": {"@id": clean(hub_path()) + "#catalog"},
    }
    faq_ld = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    page_ld = {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc,
               "dateModified": UPDATED, "isPartOf": {"@id": BASE_URL + "/#site"},
               "mainEntity": {"@id": url + "#dataset"}, "publisher": {"@id": ORG["@id"]}}
    jsonld = graph(ORG, page_ld, dataset, faq_ld, breadcrumb_ld(crumbs, url))
    return shell(relpath, title, desc, h1, body, jsonld, crumbs, og_type="article")


def card(m):
    pts = m["points"]
    return ('<li><a class="card" href="/%s" data-row><span class="k">%s</span>'
            '<h3>%s %s</h3><p>%s</p><div class="meta">%d objects &middot; %d writable%s</div>%s</a></li>'
            % (model_path(m), esc(m.get("equipment_type") or ""), esc(m["manufacturer"]), esc(m["model"]),
               esc(m.get("applies_to") or ""), len(pts), writable_count(pts),
               (" &middot; " + esc(m["source"]["doc_number"])) if m["source"].get("doc_number") else "",
               ('<span class="sr-only"> Also known as: %s</span>' % esc(", ".join(m["aliases"])))
               if m.get("aliases") else ""))


# ---------------------------------------------------------------------------
# Manufacturer page
# ---------------------------------------------------------------------------

def mfr_page(mslug, models, all_groups, gws=()):
    name = models[0]["manufacturer"]
    relpath = mfr_path(mslug)
    url = clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet points lists", "/" + hub_path()), (name, None)]
    total = sum(len(m["points"]) for m in models)
    kinds = sorted({m.get("equipment_type") or "" for m in models} - {""})
    title = "%s BACnet Points Lists (%d Model%s) | Easy BACnet" % (name, len(models), "" if len(models) == 1 else "s")
    if len(title) > 62:
        title = "%s BACnet Points Lists | Easy BACnet" % name
    desc = ("Free %s BACnet points lists for %d models%s: object types, instances, names, units and "
            "access, with CSV and EDE downloads." % (
                name, len(models), (" including " + ", ".join(m["model"] for m in models[:3])) if models else ""))
    if len(desc) > 160:
        desc = "Free %s BACnet points lists for %d models: object types, instances, names, units and access, with CSV and EDE downloads." % (name, len(models))
    h1 = ('<p class="eyebrow">Manufacturer</p><h1><span class="mfr">%s</span> BACnet points lists</h1>'
          '<p class="updated">Updated %s</p>' % (esc(name), UPDATED_HUMAN))
    body = """
<p class="lede">Every %(name)s BACnet points list we have: %(nm)d models, %(total)s BACnet objects in all.
Pick a model to see its full object table with types, instance numbers, units and read/write access,
and download it as CSV or EDE.</p>
<div class="answer"><b>What&rsquo;s here</b><p>%(kinds)s. Each list is re-typed from %(name)s&rsquo;s own free
documentation and links back to the original PDF.</p></div>
<div class="tools"><input class="search" type="search" placeholder="Filter %(name)s models&hellip;"
 aria-label="Filter models" data-filter="models"><span class="count" data-count-for="models">%(nm)d of %(nm)d shown</span></div>
<ul class="grid" id="models">%(cards)s</ul>
%(gws)s
""" % {"name": esc(name), "nm": len(models), "total": "{:,}".format(total),
       "gws": gateway_section(name, [g for g in gws if g["manufacturer_slug"] != mslug]),
       "kinds": esc("Covers " + ", ".join(k.lower() for k in kinds)) if kinds else "BACnet equipment",
       "cards": "".join(card(m) for m in models)}
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": clean(model_path(m)), "name": model_title(m)}
        for i, m in enumerate(models, 1)]}
    page_ld = {"@type": "CollectionPage", "@id": url, "url": url, "name": title, "description": desc,
               "dateModified": UPDATED, "isPartOf": {"@id": BASE_URL + "/#site"},
               "about": {"@type": "Brand", "name": name}, "mainEntity": item_list,
               "publisher": {"@id": ORG["@id"]}}
    return shell(relpath, title, desc, h1, body, graph(ORG, page_ld, breadcrumb_ld(crumbs, url)), crumbs)


def mfr_rows(groups, gw_only):
    """Manufacturer table: name, equipment types covered, model count, total objects. Gateway-only
    brands (no list of their own, only third-party gateway lists) sort in with a 'via gateway' note."""
    rows = []
    for sl, g in groups.items():
        cats = sorted({category_of(m)[1] for m in g})
        rows.append((g[0]["manufacturer"], sl, "".join('<span class="tag">%s</span>' % esc(c) for c in cats),
                     str(len(g)), "{:,}".format(sum(len(m["points"]) for m in g))))
    for sl, (b, gws) in gw_only.items():
        rows.append((b, sl, '<span class="via">via %s</span>' % esc(" / ".join(sorted({m["manufacturer"] for m in gws}))),
                     "&ndash;", "&ndash;"))
    return "".join('<tr><th scope="row"><a href="/%s">%s</a></th><td class="ty">%s</td>'
                   '<td class="num" data-l="Models">%s</td><td class="num" data-l="Objects">%s</td></tr>'
                   % (mfr_path(sl), esc(n), ty, nm, ob) for n, sl, ty, nm, ob in sorted(rows, key=lambda r: r[0].lower()))


# ---------------------------------------------------------------------------
# Brands covered by third-party gateways (Intesis, CoolAutomation...)
# ---------------------------------------------------------------------------

def brand_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def brand_map(models):
    """{brand_slug: (brand name, [gateway models])} from each model's covers_brands."""
    out = {}
    for m in models:
        for b in m.get("covers_brands") or []:
            out.setdefault(brand_slug(b), (b, []))[1].append(m)
    for _, ms in out.values():
        ms.sort(key=lambda m: (m["manufacturer"].lower(), m["model"].lower()))
    return dict(sorted(out.items(), key=lambda kv: kv[1][0].lower()))


def gateway_section(brand, gws):
    if not gws:
        return ""
    return ('<h2>Third-party BACnet gateways for %s</h2>'
            '<p>%s equipment can also be brought onto BACnet through a protocol gateway. These lists show the '
            'objects each gateway exposes for %s units.</p><ul class="grid">%s</ul>'
            % (esc(brand), esc(brand), esc(brand), "".join(card(m) for m in gws)))


def brand_page(bslug, brand, gws, groups, brands):
    relpath = mfr_path(bslug)
    url = clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet points lists", "/" + hub_path()), (brand, None)]
    makers = sorted({m["manufacturer"] for m in gws})
    title = "%s BACnet Points Lists (via Gateways) | Easy BACnet" % brand
    if len(title) > 62:
        title = "%s BACnet Points Lists | Easy BACnet" % brand
    desc = ("%s BACnet points lists: the BACnet objects exposed for %s air conditioners by %s gateways, with "
            "minimum BMS points and CSV/EDE downloads." % (brand, brand, " and ".join(makers)))
    if len(desc) > 160:
        desc = ("%s BACnet points lists through gateways: objects, minimum BMS points and CSV/EDE downloads."
                % brand)
    h1 = ('<p class="eyebrow">Brand &middot; via BACnet gateways</p><h1><span class="mfr">%s</span> BACnet '
          'points lists</h1><p class="updated">Updated %s</p>' % (esc(brand), UPDATED_HUMAN))
    body = """
<p class="lede">We haven&rsquo;t found a public BACnet points list published by %(brand)s itself. %(brand)s
units are usually put on BACnet through a protocol gateway, and the gateway makers do publish their object
tables. These are the gateways we have for %(brand)s, each with its full object list, the minimum points to map,
and CSV/EDE downloads.</p>
<div class="answer"><b>Short answer</b><p>To read or control %(brand)s equipment from a BACnet BMS, fit a
BACnet gateway on the unit&rsquo;s own bus. Each indoor unit then appears as a set of BACnet objects (on/off,
mode, setpoint, room temperature, fan speed, alarm) whose instance numbers follow the gateway&rsquo;s numbering
rule &mdash; see the integration notes on each list.</p></div>
<ul class="grid">%(cards)s</ul>
""" % {"brand": esc(brand), "cards": "".join(card(m) for m in gws)}
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": clean(model_path(m)), "name": model_title(m)}
        for i, m in enumerate(gws, 1)]}
    page_ld = {"@type": "CollectionPage", "@id": url, "url": url, "name": title, "description": desc,
               "dateModified": UPDATED, "isPartOf": {"@id": BASE_URL + "/#site"},
               "about": {"@type": "Brand", "name": brand}, "mainEntity": item_list,
               "publisher": {"@id": ORG["@id"]}}
    return shell(relpath, title, desc, h1, body, graph(ORG, page_ld, breadcrumb_ld(crumbs, url)), crumbs)


# ---------------------------------------------------------------------------
# Hub
# ---------------------------------------------------------------------------

def hub_page(groups, brands=None):
    brands = brands or {}
    gw_only = {b: v for b, v in brands.items() if b not in groups}
    relpath = hub_path()
    url = clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet points lists", None)]
    models = [m for g in groups.values() for m in g]
    total = sum(len(m["points"]) for m in models)
    models_sorted = sorted(models, key=lambda m: (m["manufacturer"].lower(), m["model"].lower()))
    maxo = max(len(m["points"]) for m in models) or 1
    cats = group_by_category(models)
    title = "BACnet Points Lists by Manufacturer | Easy BACnet"
    desc = ("Free BACnet points lists for %d models from %d manufacturers, including %s. Object types, "
            "instances, units and access, with CSV and EDE downloads." % (
                len(models), len(groups), ", ".join(g[0]["manufacturer"] for g in list(groups.values())[:3])))
    if len(desc) > 160:
        desc = ("Free BACnet points lists for %d models from %d manufacturers: object types, instances, "
                "units and access, with CSV and EDE downloads." % (len(models), len(groups)))
    opts = [(g[0]["manufacturer"], '<option value="/%s">%s (%d)</option>' % (
        mfr_path(s), esc(g[0]["manufacturer"]), len(g))) for s, g in groups.items()]
    opts += [(b, '<option value="/%s">%s (via gateways)</option>' % (mfr_path(s), esc(b)))
             for s, (b, gws) in gw_only.items()]
    options = "".join(o for _, o in sorted(opts, key=lambda x: x[0].lower()))
    h1 = ('<p class="eyebrow">Free library</p><h1>BACnet points lists <span class="mfr">by manufacturer</span></h1>'
          '<p class="updated">Updated %s</p>' % UPDATED_HUMAN)
    body = """
<p class="lede">Need a BACnet points list before you get to site? This library has <strong>%(nm)d models from
%(ng)d manufacturers</strong> &mdash; %(total)s BACnet objects &mdash; each with object type, instance number,
name, engineering units and read/write access, ready to download as CSV or EDE.</p>
<form class="tools" action="#" onsubmit="return false" aria-label="Choose a manufacturer">
  <label class="mono count" for="mfr-pick">Select manufacturer</label>
  <select class="pick" id="mfr-pick"><option value="">Choose a manufacturer&hellip;</option>%(options)s</select>
</form>
<h2>Equipment types</h2>
<div class="tablewrap"><table class="lst types"><thead><tr><th scope="col">Equipment type</th>
<th scope="col">Manufacturers</th><th scope="col" class="num">Models</th></tr></thead>
<tbody>%(types)s</tbody></table></div>
<h2>Manufacturers</h2>
<div class="tablewrap"><table class="lst mfrs"><thead><tr><th scope="col">Manufacturer</th>
<th scope="col">Equipment</th><th scope="col" class="num">Models</th><th scope="col" class="num">Objects</th></tr></thead>
<tbody>%(mrows)s</tbody></table></div>
<h2 id="models">Every model <span class="hn">%(nm)d</span></h2>
<div class="tools"><input class="search" id="cmp-q" type="search" placeholder="Model, part number or equipment &mdash; e.g. Symbio, VRV, chiller, drive&hellip;"
 aria-label="Search all models">
<select class="mini" id="cmp-mf" aria-label="Manufacturer"><option value="">All manufacturers (%(ng)d)</option>%(mopts)s</select>
<select class="mini sortm" id="cmp-sort" aria-label="Sort by"><option value="mf:ascending">Sort: manufacturer</option>
<option value="md:ascending">Sort: model</option><option value="o:descending">Sort: most objects</option>
<option value="w:descending">Sort: most writable</option></select>
<span class="count" id="cmp-count" aria-live="polite">%(nm)d of %(nm)d shown</span></div>
<div class="facets"><span class="lbl">Type</span><ul class="chips">%(chips)s</ul></div>
<div class="tablewrap"><table class="cmp" id="cmp"><thead><tr>
<th scope="col" data-k="mf" aria-sort="ascending"><button type="button">Manufacturer</button></th>
<th scope="col" data-k="md" aria-sort="none"><button type="button">Model</button></th>
<th scope="col">Type</th>
<th scope="col" class="num" data-k="o" aria-sort="none"><button type="button">Objects</button></th>
<th scope="col" class="num" data-k="w" aria-sort="none"><button type="button">Writable</button></th>
<th scope="col">Download</th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
""" % {"nm": len(models), "ng": len(groups),
       "total": "{:,}".format(total), "options": options,
       "mrows": mfr_rows(groups, gw_only),
       "types": "".join(cat_item(c, ms) for c, ms in cats),
       "mopts": "".join('<option>%s</option>' % esc(x)
                        for x in sorted({m["manufacturer"] for m in models}, key=str.lower)),
       "chips": "".join('<li><button class="chip" type="button" data-kind="%s" aria-pressed="false">%s<b>%d</b>'
                        '</button></li>' % (c[0], esc(c[1]), len(ms)) for c, ms in cats),
       "rows": "".join(cat_row(m, [], maxo, show_type=True) for m in models_sorted)}
    catalog = {"@type": "DataCatalog", "@id": url + "#catalog", "name": "Easy BACnet points-list library",
               "url": url, "description": desc, "publisher": {"@id": ORG["@id"]},
               "dataset": [{"@id": clean(model_path(m)) + "#dataset"} for m in models]}
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "url": clean(mfr_path(s)),
         "name": "%s BACnet points lists" % g[0]["manufacturer"]}
        for i, (s, g) in enumerate(groups.items(), 1)]}
    page_ld = {"@type": "CollectionPage", "@id": url, "url": url, "name": title, "description": desc,
               "dateModified": UPDATED, "isPartOf": {"@id": BASE_URL + "/#site"}, "mainEntity": item_list,
               "publisher": {"@id": ORG["@id"]}}
    return shell(relpath, title, desc, h1, body,
                 graph(ORG, page_ld, catalog, breadcrumb_ld(crumbs, url)), crumbs)


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------

def csv_text(m):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(["# %s %s BACnet points list - easybacnet.com - source: %s" %
                (m["manufacturer"], m["model"], m["source"]["url"])])
    w.writerow(["Object type", "Type code", "Instance", "Object name", "Description", "Units", "Access", "States"])
    for pt in m["points"]:
        w.writerow([OBJECT_TYPES[pt["type"]][0], pt["type"],
                    "" if pt.get("instance") is None else pt["instance"],
                    pt["name"], pt["description"], pt["units"], access_label(pt["access"]), pt["states"]])
    return "\ufeff" + buf.getvalue()   # BOM so Excel reads UTF-8 (°F etc.)


def ede_text(m):
    dev = m.get("default_device_instance")
    dev = "" if dev in (None, "") else str(dev)
    lines = [
        "#Engineering-Data-Exchange - B.I.G.-EU",
        "PROJECT_NAME;%s %s" % (m["manufacturer"], m["model"]),
        "VERSION_OF_REFERENCEFILE;1",
        "TIMESTAMP_OF_LAST_CHANGE;%s" % UPDATED,
        "AUTHOR_OF_LAST_CHANGE;easybacnet.com",
        "VERSION_OF_LAYOUT;2.3",
        "#mandatory;mandatory;mandatory;mandatory;mandatory;optional;optional;optional;optional;optional;optional;optional;optional;optional;optional;optional",
        "# keyname;device obj.-instance;object-name;object-type;object-instance;description;present-value-default;min-present-value;max-present-value;settable;supports COV;hi-limit;low-limit;state-text-reference;unit-code;vendor-specific-address",
    ]

    def cell(s):
        return (s or "").replace(";", ",").replace("\n", " ")
    for pt in m["points"]:
        code = OBJECT_TYPES[pt["type"]][1]
        if code is None:
            continue
        inst = "" if pt.get("instance") is None else str(pt["instance"])
        key = "%s_%s" % (pt["type"], inst)
        lines.append(";".join([
            cell(key), dev, cell(pt["name"]), str(code), inst, cell(pt["description"]),
            "", "", "", "Y" if pt["access"] in ("W", "C") else "N", "", "", "", "",
            unit_code(pt["units"]), ""]))
    return "\r\n".join(lines) + "\r\n"


def json_text(m):
    out = {k: v for k, v in m.items() if not k.startswith("_")}
    out["points"] = [{k: v for k, v in pt.items() if not k.startswith("_")} for pt in m["points"]]
    out["page"] = clean(model_path(m))
    out["note"] = ("Re-typed from the manufacturer's public documentation (see source). Point availability varies "
                   "by firmware and options; verify against the live device.")
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build(write):
    """Generate every library page and download via build_site.write().
    Returns (sitemap_paths, llms_lines)."""
    models = load_all()
    if not models:
        print("points library: no data yet, skipped")
        return [], []
    # Everything under ROOT is generated: clear it so renamed/removed models leave no stale pages.
    out_dir = os.path.join(HERE, ROOT)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    groups = by_manufacturer(models)
    seen = {}
    for m in models:
        seen.setdefault(page_title(m, len(m["points"])), []).append(m)
    for ms in seen.values():
        if len(ms) > 1:
            for m in ms:
                m["_full_title"] = True
    paths = [hub_path()]
    brands = brand_map(models)
    write(hub_path(), hub_page(groups, brands))
    for mslug, ms in groups.items():
        write(mfr_path(mslug), mfr_page(mslug, ms, groups, brands.get(mslug, ("", []))[1]))
        paths.append(mfr_path(mslug))
        for m in ms:
            write(model_path(m), model_page(m, ms))
            write(model_path(m, ".csv"), csv_text(m))
            write(model_path(m, "-ede.csv"), ede_text(m))
            write(model_path(m, ".json"), json_text(m))
            paths.append(model_path(m))
    for bslug, (bname, gws) in brands.items():
        if bslug not in groups:
            write(mfr_path(bslug), brand_page(bslug, bname, gws, groups, brands))
            paths.append(mfr_path(bslug))
    cats = group_by_category(models)
    for c, ms in cats:
        write(cat_path(c[0]), cat_page(c, ms, cats))
        paths.append(cat_path(c[0]))
    catalogue = {
        "name": "Easy BACnet points-list library", "url": clean(hub_path()), "updated": UPDATED,
        "models": [{
            "manufacturer": m["manufacturer"], "model": m["model"], "aliases": m.get("aliases") or [],
            "equipment_type": m.get("equipment_type"), "objects": len(m["points"]),
            "writable": writable_count(m["points"]), "page": clean(model_path(m)),
            "csv": BASE_URL + "/" + model_path(m, ".csv"), "json": BASE_URL + "/" + model_path(m, ".json"),
            "source": m["source"]["url"]} for g in groups.values() for m in g]}
    write(ROOT + "/index.json", json.dumps(catalogue, ensure_ascii=False, indent=1) + "\n")

    llms = ["", "## BACnet points lists (free library, by manufacturer)",
            "- Library home: %s" % clean(hub_path()),
            "- Machine-readable catalogue: %s/%s/index.json" % (BASE_URL, ROOT)]
    for c, ms in cats:
        llms.append("- %s BACnet points lists (%d models): %s" % (c[1], len(ms), clean(cat_path(c[0]))))
    for bslug, (bname, gws) in brands.items():
        if bslug not in groups:
            llms.append("- %s BACnet points lists (via gateways): %s" % (bname, clean(mfr_path(bslug))))
    for mslug, ms in groups.items():
        llms.append("- %s BACnet points lists: %s" % (ms[0]["manufacturer"], clean(mfr_path(mslug))))
        for m in ms:
            llms.append("  - %s (%d objects): %s" % (model_title(m), len(m["points"]), clean(model_path(m))))
    print("points library: %d manufacturers, %d models, %d objects" % (
        len(groups), len(models), sum(len(m["points"]) for m in models)))
    return paths, llms
