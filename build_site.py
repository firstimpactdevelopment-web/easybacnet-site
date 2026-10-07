#!/usr/bin/env python3
"""
Generates the Easy BACnet public site (GitHub Pages).

The pages are written for two audiences at once. A technician who lands here
from a search gets a direct answer at the top. An AI assistant answering
someone's BACnet question gets clean semantic HTML, a one-paragraph answer
immediately after each heading, and FAQPage/Article JSON-LD it can parse.

Run:  python build_site.py
Then commit and push the generated .html files.

BASE_URL below is the only thing that needs changing once the GitHub Pages
URL is known. Everything else is relative.
"""

import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import html as html_module

BASE_URL = "https://easybacnet.com"

# IndexNow (Bing, Yandex, Seznam, Naver, …) instant-recrawl key. The key file
# below is served at BASE_URL/<key>.txt and IS the ownership proof — its
# contents must equal the key. Google does not consume IndexNow, so this is a
# free supplement to the sitemap, not a Google-ranking lever. Ping AFTER a
# deploy is live:  python build_site.py --ping
INDEXNOW_KEY = "e9a7c4f20b8d46139f5c1a7e63d02b8f"

# Freshness signal. Bump when guide content is meaningfully revised.
UPDATED = "2026-10-03"            # ISO, for JSON-LD and sitemap <lastmod>
UPDATED_HUMAN = "3 October 2026"  # for the visible "Updated" line

HERE = os.path.dirname(os.path.abspath(__file__))

# Google Analytics 4 measurement ID for easybacnet.com (GA4 property under
# tim.bruhn89 "Default Account for Firebase", created 2026-09-20).
GA_MEASUREMENT_ID = "G-BH9W9B8YRJ"

# GA4 with Consent Mode v2. Analytics storage defaults to DENIED and only
# loads gtag/config after the visitor accepts the cookie banner (GDPR/ePrivacy).
# Self-contained (own <style>, own banner DOM) so it can be dropped into any
# page after the <meta charset> line. IP anonymisation is on; no ad signals.
ANALYTICS = ("""
<!-- Google Analytics 4 (Consent Mode v2) — analytics cookies gated by the banner -->
<script>
(function(){
  var ID="%(ga)s", KEY="ga-consent", P="%(privacy)s";
  window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}window.gtag=gtag;
  gtag('js',new Date());
  gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500});
  var v=null;try{v=localStorage.getItem(KEY);}catch(e){}
  function load(){if(window.__ga)return;window.__ga=1;var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+ID;document.head.appendChild(s);gtag('config',ID,{anonymize_ip:true});}
  function grant(){gtag('consent','update',{analytics_storage:'granted'});load();}
  if(v==='granted'){grant();}
  function banner(){
    if(v==='granted'||v==='denied')return;
    var d=document.createElement('div');d.className='cookie-consent';
    d.innerHTML='<p>We use Google Analytics to understand which guides help. No ads, no cross-site tracking. <a href="'+P+'">Privacy policy</a>.</p><div class="cc-row"><button type="button" id="cc-no">Decline</button><button type="button" id="cc-yes">Accept</button></div>';
    document.body.appendChild(d);
    d.querySelector('#cc-yes').onclick=function(){try{localStorage.setItem(KEY,'granted');}catch(e){}grant();d.remove();};
    d.querySelector('#cc-no').onclick=function(){try{localStorage.setItem(KEY,'denied');}catch(e){}d.remove();};
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',banner);}else{banner();}
})();
</script>
<style>
.cookie-consent{position:fixed;left:1rem;right:1rem;bottom:1rem;max-width:660px;margin:0 auto;z-index:9999;background:#1d2227;color:#f3f5f6;border:1px solid #2f363d;border-radius:12px;padding:1rem 1.15rem;box-shadow:0 14px 44px rgba(0,0,0,.55);font-family:"Manrope",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;font-size:.92rem;line-height:1.5}
.cookie-consent p{margin:0 0 .8rem}
.cookie-consent a{color:#ff9a1f}
.cookie-consent .cc-row{display:flex;gap:.6rem;justify-content:flex-end}
.cookie-consent button{font:inherit;font-weight:700;padding:.5rem 1.15rem;border-radius:8px;border:1px solid #3a424c;background:transparent;color:#f3f5f6;cursor:pointer}
.cookie-consent #cc-yes{background:#ff9a1f;border-color:#ff9a1f;color:#0d0f11}
</style>
""" % {"ga": GA_MEASUREMENT_ID, "privacy": BASE_URL + "/privacy"})

CSS = """
  :root { color-scheme: dark; --fg:#f3f5f6; --bg:#14171a; --muted:#9aa4ad;
          --accent:#ff9a1f; --box:#1d2227; --line:#2f363d; --code:#101418; --ink:#0d0f11; }
  * { box-sizing: border-box; }
  body { max-width: 48rem; margin: 0 auto; padding: 2rem 1.25rem 5rem;
         font-family:"Manrope",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         font-size:17px; line-height:1.7; color:var(--fg); background:var(--bg);
         -webkit-font-smoothing:antialiased; }
  header.site { display:flex; align-items:center; gap:.6rem; flex-wrap:wrap;
                padding-bottom:1.25rem; border-bottom:1px solid var(--line); margin-bottom:2.25rem; }
  header.site a { color:var(--fg); text-decoration:none; }
  header.site .brand { font-family:"Archivo",sans-serif; font-weight:900;
                       text-transform:uppercase; letter-spacing:.02em; font-size:1.05rem; }
  header.site .muted { margin-left:auto; font-family:"IBM Plex Mono",ui-monospace,monospace;
                       font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; }
  h1, h2, h3 { font-family:"Archivo",sans-serif; letter-spacing:-.01em; line-height:1.12; }
  h1 { font-weight:900; text-transform:uppercase; font-size:clamp(1.7rem,4.5vw,2.5rem);
       margin:0 0 .6rem; }
  .updated { color:var(--muted); font-size:.8rem; margin:0 0 1.5rem;
             font-family:"IBM Plex Mono",ui-monospace,monospace; letter-spacing:.06em; }
  h2 { font-weight:800; font-size:1.35rem; margin:2.6rem 0 .6rem; }
  h3 { font-weight:800; font-size:1.06rem; margin:1.8rem 0 .4rem; }
  a { color:var(--accent); }
  strong { color:#fff; }
  .answer { background:var(--box); border:1px solid var(--line); border-left:3px solid var(--accent);
            border-radius:12px; padding:1.1rem 1.3rem; margin:1.5rem 0 2rem; }
  .answer > strong { display:block; margin-bottom:.5rem; text-transform:uppercase;
                   font-family:"IBM Plex Mono",ui-monospace,monospace; font-weight:600;
                   font-size:.72rem; letter-spacing:.18em; color:var(--accent); }
  .answer p { margin:.6rem 0; }
  .answer p strong { color:#fff; font-weight:700; }
  code { background:var(--code); padding:.1rem .4rem; border-radius:4px; font-size:.9em;
         font-family:"IBM Plex Mono",ui-monospace,monospace; }
  pre { background:var(--code); padding:1rem; border-radius:10px; overflow-x:auto;
        border:1px solid var(--line); }
  pre code { background:none; padding:0; }
  table { border-collapse:collapse; width:100%; margin:1.25rem 0; display:block; overflow-x:auto; }
  th, td { text-align:left; padding:.55rem .75rem; border-bottom:1px solid var(--line); }
  th { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.72rem;
       text-transform:uppercase; letter-spacing:.1em; color:var(--accent); font-weight:600; }
  ul, ol { padding-left:1.3rem; }
  li { margin:.45rem 0; }
  .muted { color:var(--muted); font-size:.92rem; }
  nav.more { margin-top:3rem; padding-top:1.5rem; border-top:1px solid var(--line); }
  nav.more h2 { margin-top:0; }
  nav.more ul { list-style:none; padding:0; }
  nav.more li { margin:0; border-bottom:1px solid var(--line); padding:.85rem 0; }
  nav.more li:last-child { border-bottom:none; }
  nav.more a { font-family:"Archivo",sans-serif; font-weight:600; }
  footer { margin-top:3.5rem; padding-top:1.5rem; border-top:1px solid var(--line);
           color:var(--muted); font-size:.9rem; }
  footer a { color:var(--accent); }
  .shotrow { display:flex; flex-wrap:wrap; gap:1rem; margin:1.75rem 0; }
  .shotrow figure { margin:0; flex:0 1 200px; }
  .shotrow img { width:100%; height:auto; border:1px solid var(--line);
                 border-radius:16px; display:block; background:var(--ink); }
  .shotrow figcaption { color:var(--muted); font-size:.82rem; margin-top:.5rem;
                        text-align:center; line-height:1.35; }
  .callout { background:var(--box); border:1px solid var(--line);
             border-left:3px solid var(--accent); border-radius:12px;
             padding:1rem 1.25rem; margin:1.75rem 0; }
  .callout p:last-child { margin-bottom:0; }
"""


SCREENSHOTS = {
    "guides/how-to-use-easy-bacnet": [("picker.png","Choose a mode on the home screen"),
        ("scan.png","A finished scan"),
        ("devices.png","Every device found"),("points.png","One device\u2019s points")],
    "guides/how-to-write-to-a-bacnet-point": [("point.png","Point detail, showing who is commanding it"),
        ("write.png","Choosing a value and priority"),("release.png","Releasing back to auto")],
    "guides/how-to-build-a-control-panel": [("remote-edit.png","Edit mode \u2014 drag to arrange"),
        ("control-types.png","Pick a control type"),("remote-use.png","A finished panel, live")],
    "guides/how-to-build-a-custom-remote": [("remote-edit.png","Edit mode \u2014 drag to arrange"),
        ("add-control.png","Add a control"),("control-types.png","Pick a control type"),
        ("remote-use.png","The finished panel, live")],
    "guides/cant-find-what-im-looking-for": [("no-devices.png","When a scan finds nothing")],
    "guides/why-cant-i-find-my-bacnet-devices": [("no-devices.png","When a scan finds nothing")],
    "guides/subnets": [("no-devices.png","Wrong subnet: the scan finds nothing")],
    "guides/what-is-a-bacnet-points-list": [("points.png","A device\u2019s point list in Easy BACnet")],
    "guides/how-to-find-your-bacnet-points-list": [("devices.png","Devices found"),
        ("points.png","Points on one device")],
    "guides/vendor-asking-for-bacnet-information": [("points.png","The point list you can export")],
    "guides/bacnet-priority-and-stuck-overrides": [("point.png","\u201cCommanded At\u201d shows the active priority"),
        ("write.png","Writing at a priority you choose")],
    "guides/bacnet-object-types-explained": [("points.png","Object types shown for every point")],
    "guides/bacnet-device-id-explained": [("devices.png","Each device with its Device ID")],
    "guides/who-is-i-am-explained": [("scan.png","A Who-Is scan and the devices that answered"),
        ("devices.png","Each I-Am becomes a row")],
    "guides/what-is-a-bbmd": [("no-devices.png","No BBMD, wrong subnet: nothing answers")],
    "guides/bacnet-mstp-vs-bacnet-ip": [("devices.png","MS/TP devices reached through an IP router")],
    "guides/what-port-does-bacnet-use": [("scan.png","Discovery broadcasts on UDP 47808")],
    "guides/bacnet-vs-modbus": [("points.png","A BACnet point: named, typed, with units")],
    "guides/what-is-bacnet": [("scan.png","A Who-Is scan finds every BACnet IP device"),
        ("devices.png","Each device that answered"),("points.png","One device’s points, named and typed")],
    "guides/bacnet-engineering-units-explained": [("points.png","Units shown next to every value")],
    "guides/bacnet-status-flags-explained": [("point.png","Status flags on a point’s detail")],
    "guides/how-to-release-a-bacnet-override": [("point.png","“Commanded At” shows the active priority"),
        ("release.png","Releasing a point back to auto")],
    "guides/bacnet-add-device-by-ip": [("no-devices.png","When a broadcast scan finds nothing")],
    "guides/bacnet-add-object-by-number": [("points.png","A device’s point list")],
    "guides/duplicate-bacnet-device-id": [("devices.png","Each device with its Device ID")],
    "guides/is-it-safe-to-write-to-bacnet": [("write.png","Choosing a value and priority"),
        ("release.png","Releasing back to auto")],
    "guides/bacnet-multistate-values-explained": [("point.png","A multi-state point and its options")],
    "guides/export-bacnet-points-to-csv": [("scan.png","A finished scan, ready to export"),
        ("devices.png","Every device found goes into the spreadsheet")],
    "guides/bacnet-scanner-app-android": [("scan.png","A finished scan"),("devices.png","Every device found")],
}


def screenshot_block(slug, prefix):
    imgs = SCREENSHOTS.get(slug)
    if not imgs:
        return ""
    figs = "".join(
        '<figure><img src="%simg/%s" alt="%s" width="480" height="1068" loading="lazy"><figcaption>%s</figcaption></figure>'
        % (prefix, f, cap, cap) for f, cap in imgs
    )
    return '<div class="shotrow">%s</div>' % figs


def page(slug, title, question, answer_html, body_html, related, description):
    """One guide page: semantic HTML plus FAQPage JSON-LD."""
    prefix = "../" if slug.startswith("guides/") else ""
    rel = ""
    if related:
        items = "\n".join(
            '      <li><a href="%s%s.html">%s</a></li>' % (prefix, r[0], r[1])
            for r in related
        )
        rel = (
            '\n  <nav class="more">\n    <h2>Related</h2>\n    <ul>\n%s\n    </ul>\n  </nav>'
            % items
        )

    jsonld = """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "FAQPage",
      "datePublished": "%(pub)s",
      "dateModified": "%(pub)s",
      "mainEntity": [{
        "@type": "Question",
        "name": %(q)s,
        "acceptedAnswer": { "@type": "Answer", "text": %(a)s }
      }]
    },
    {
      "@type": "Article",
      "headline": %(q)s,
      "datePublished": "%(pub)s",
      "dateModified": "%(pub)s",
      "mainEntityOfPage": "%(base)s/%(slug)s.html",
      "image": "%(base)s/img/og-image.png",
      "author": { "@id": "%(base)s/#org" },
      "publisher": {
        "@type": "Organization",
        "@id": "%(base)s/#org",
        "name": "Easy BACnet",
        "url": "%(base)s/",
        "logo": { "@type": "ImageObject", "url": "%(base)s/logo-512.png" }
      }
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "%(base)s/index.html" },
        { "@type": "ListItem", "position": 2, "name": %(q)s, "item": "%(base)s/%(slug)s.html" }
      ]
    }
  ]
}""" % {
        "q": jstr(html_module.unescape(question)),
        "a": jstr(html_module.unescape(strip_tags(answer_html))),
        "pub": UPDATED,
        "base": BASE_URL,
        "slug": slug,
    }

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>%(title)s</title>
<meta name="description" content="%(description)s">
<link rel="canonical" href="%(base)s/%(slug)s.html">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#14171a">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800;900&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Easy BACnet">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(description)s">
<meta property="og:url" content="%(base)s/%(slug)s.html">
<meta property="og:image" content="%(base)s/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(description)s">
<meta name="twitter:image" content="%(base)s/img/og-image.png">
<style>%(css)s</style>
<script type="application/ld+json">
%(jsonld)s
</script>
</head>
<body>

<header class="site">
  <a href="%(prefix)sindex.html" style="display:inline-flex;align-items:center;gap:.5rem;text-decoration:none"><img src="icon.svg" alt="" width="28" height="28" style="border-radius:7px"><b class="brand">Easy BACnet</b></a>
  <span class="muted">&middot; BACnet IP Controls made Easy</span>
</header>

<article>
  <h1>%(question)s</h1>
  <p class="updated">Updated %(updated_h)s</p>

  <div class="answer">
    <strong>Short answer</strong>
    %(answer)s
  </div>
%(shots)s
%(body)s
</article>%(rel)s

<footer>
  <p>Published alongside <a href="%(prefix)sindex.html">Easy BACnet</a>, a free
  Android app that scans a building network for BACnet IP devices, reads and
  commands their points, and exports the results as an Excel (.xlsx) spreadsheet.</p>
  <p><a href="%(prefix)sindex.html#guides">All guides</a> &middot;
  <a href="%(prefix)sterms.html">Terms of use</a> &middot;
  <a href="%(prefix)sprivacy.html">Privacy policy</a></p>
</footer>

</body>
</html>
""" % {
        "title": title,
        "description": description,
        "base": BASE_URL,
        "slug": slug,
        "css": CSS,
        "jsonld": jsonld,
        "question": question,
        "answer": answer_html,
        "shots": screenshot_block(slug, prefix),
        "body": body_html,
        "rel": rel,
        "prefix": prefix,
        "updated_h": UPDATED_HUMAN,
    }


def strip_tags(html):
    out, depth = [], 0
    for ch in html:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return " ".join("".join(out).split())


def jstr(s):
    return ('"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("<", "\\u003c")
            + '"')


def _to_clean_url(u):
    # Cloudflare Pages serves extensionless clean URLs and 301-redirects any
    # ".html" to them. So every internal URL we emit — links, canonical, og:url,
    # breadcrumb items, sitemap <loc> — must be the extensionless form, or it
    # points at a redirect (Google Search Central: link consistently to the
    # canonical URL and keep sitemaps/canonicals in agreement). Same-site and
    # relative URLs only; external hosts (e.g. easymodbus.com) are left alone.
    if u.startswith(("http://", "https://")) and "easybacnet.com" not in u:
        return u
    if u.startswith(("mailto:", "tel:", "#", "javascript:", "data:")):
        return u
    u = re.sub(r'index\.html(?=$|[#?])', "", u)   # ".../index.html" -> ".../"
    u = re.sub(r'\.html(?=$|[#?])', "", u)          # ".../page.html"  -> ".../page"
    return u or "/"                                  # bare "index.html" -> "/"


def _clean_internal_urls(text):
    text = re.sub(r'href="([^"]*)"',
                  lambda m: 'href="%s"' % _to_clean_url(m.group(1)), text)
    text = re.sub(r'(<meta property="og:url" content=")([^"]*)(")',
                  lambda m: m.group(1) + _to_clean_url(m.group(2)) + m.group(3), text)
    text = re.sub(r'("item":\s*")([^"]*)(")',
                  lambda m: m.group(1) + _to_clean_url(m.group(2)) + m.group(3), text)
    text = re.sub(r'(<loc>)([^<]*)(</loc>)',
                  lambda m: m.group(1) + _to_clean_url(m.group(2)) + m.group(3), text)
    return text


def write(relpath, content):
    # Inject the analytics + consent banner into every HTML page, right after
    # the charset meta so it never pushes charset past the first 1 KB.
    if "<head>" in content and "googletagmanager" not in content:
        marker = '<meta charset="utf-8">'
        if marker in content:
            content = content.replace(marker, marker + ANALYTICS, 1)
        else:
            content = content.replace("<head>", "<head>" + ANALYTICS, 1)
    content = _clean_internal_urls(content)
    full = os.path.join(HERE, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    io.open(full, "w", encoding="utf-8", newline="\n").write(content)
    print("wrote", relpath)


# ---------------------------------------------------------------------------
# Guides
# ---------------------------------------------------------------------------

GUIDES = []

GUIDES.append(dict(
    slug="guides/what-is-a-bacnet-points-list",
    title="What is a BACnet IP points list? | Easy BACnet",
    question="What is a BACnet IP points list?",
    description="A BACnet IP points list inventories every object a device exposes: type, instance, name, present value and units. What it contains and why.",
    answer_html="""<p>A BACnet IP points list is an inventory of every data object a BACnet
    device exposes to the network. Each row is one point &mdash; a sensor reading, a
    setpoint, a command, or a status flag &mdash; identified by its <em>object type</em>
    (Analog Input, Binary Output, and so on) and its <em>instance number</em>, usually
    alongside the point name, its present value, and its engineering units. It is
    the document an integrator, vendor, or analytics platform needs before they can
    read or control anything in your building.</p>""",
    body_html="""
  <h2>What a point actually is</h2>
  <p>BACnet models a controller as a collection of <strong>objects</strong>. Every
  object has properties, and the one nearly everybody cares about is
  <code>Present_Value</code> &mdash; the number or state the point is reporting right
  now. A rooftop unit controller might expose eighty objects: supply air
  temperature, fan status, damper position, occupancy mode, a dozen setpoints, and
  a long tail of internal values that only the manufacturer cares about.</p>

  <p>Each object is addressed by a pair: its type and its instance number. Analog
  Input 3 and Binary Input 3 are different points on the same controller. The pair
  is what makes a point unambiguous, which is why a points list that gives only
  names is not much use to an integrator.</p>

  <h2>What a points list contains</h2>
  <p>A usable points list has at least these columns:</p>
  <table>
    <tr><th>Column</th><th>Why it matters</th></tr>
    <tr><td>Device ID (instance)</td><td>Identifies which controller the point lives on. Must be unique across the whole BACnet internetwork.</td></tr>
    <tr><td>Device name / IP address</td><td>How a person and a machine respectively find the controller.</td></tr>
    <tr><td>Object type</td><td>Analog Input, Binary Value, Multi-State Output, etc. Determines the datatype and whether the point can be commanded.</td></tr>
    <tr><td>Object instance</td><td>The number within that type. Type plus instance is the point's address.</td></tr>
    <tr><td>Point name</td><td>The <code>Object_Name</code> property. Human-readable, and often the only clue to what the point does.</td></tr>
    <tr><td>Present value</td><td>What it reads right now. Proves the point is live and gives the reader a sanity check on units.</td></tr>
    <tr><td>Units</td><td>Degrees F, percent, CFM, and so on. Without this a number is meaningless.</td></tr>
    <tr><td>Status flags</td><td>In alarm, fault, overridden, out of service. Tells you whether the value can be trusted.</td></tr>
  </table>

  <h2>The object types you will actually see</h2>
  <p>Three families cover the overwhelming majority of points in a building:</p>
  <ul>
    <li><strong>Analog</strong> (Input, Output, Value) &mdash; anything with a
    continuous number: temperatures, pressures, percentages, setpoints.</li>
    <li><strong>Binary</strong> (Input, Output, Value) &mdash; two-state points:
    a fan running or stopped, a call for cooling, an alarm contact.</li>
    <li><strong>Multi-state</strong> (Input, Output, Value) &mdash; a small set of
    named states: Off / Low / High, or Occupied / Unoccupied / Standby.</li>
  </ul>
  <p>Within each family, <em>Input</em> generally means a physical sensor,
  <em>Output</em> a physical actuator, and <em>Value</em> a software point that
  exists only inside the controller's logic. That distinction matters when someone
  wants to write to a point: see
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck overrides</a>.</p>

  <h2>Why anyone asks for one</h2>
  <ul>
    <li><strong>Integration.</strong> An analytics platform, a tenant billing
    system, or a new head-end needs to know what exists before it can map anything.</li>
    <li><strong>Commissioning and troubleshooting.</strong> Comparing the points
    list against the sequence of operations is how you find the sensor that was
    never wired.</li>
    <li><strong>Handover.</strong> When a building changes hands or contractors,
    the points list is the map of the control system.</li>
  </ul>

  <p>If someone has asked you for one, see
  <a href="vendor-asking-for-bacnet-information.html">what to send when a vendor
  asks for your BACnet information</a>. If you need to produce one from a live
  system, see
  <a href="how-to-find-your-bacnet-points-list.html">how to find your BACnet IP points list</a>.</p>
""",
    related=[
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet IP points list?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-find-your-bacnet-points-list",
    title="How do I find my BACnet IP points list? | Easy BACnet",
    question="How do I find my BACnet IP points list?",
    description="Four ways to get a BACnet IP points list: contractor submittals, a BMS export, a network scan from your phone, or reading Object_List directly.",
    answer_html="""<p>There are four routes, easiest first: ask your controls contractor
    for the submittal documents, export a points list from your building management
    system's front end, scan the network with a BACnet IP discovery tool, or read the
    <code>Object_List</code> property from each controller directly. Scanning is the
    only one that is guaranteed to reflect what is actually on the network today
    rather than what was installed on paper.</p>""",
    body_html="""
  <h2>1. Ask the controls contractor</h2>
  <p>The company that installed or maintains the building automation system
  normally holds a points list as part of the project submittals, often as a
  spreadsheet. This is the fastest route when it works. Two caveats: the document
  describes the design, not necessarily the installed system, and it goes stale the
  first time anyone adds a VAV box.</p>

  <h2>2. Export from the BMS front end</h2>
  <p>Most head-end software &mdash; Niagara, Metasys, Desigo, EBI, and the rest &mdash;
  can export a point list or a database report. Look for a report, export, or
  database view rather than the graphics pages. This gives you what the head-end
  knows about, which is usually a curated subset: points nobody mapped into the
  front end will be missing.</p>

  <h2>3. Scan the network</h2>
  <p>A discovery tool broadcasts a BACnet <em>Who-Is</em> message and lists every
  device that answers, then reads each device's object list. This is the only method
  that reflects reality, including the controllers nobody documented.</p>

  <p>You need three things:</p>
  <ul>
    <li>A device on <strong>the same IP subnet</strong> as the controllers, or a
    BBMD configured to forward broadcasts to you.</li>
    <li>UDP port <strong>47808</strong> (0xBAC0) reachable and not blocked. Some
    sites move devices to 47809&ndash;47817 to separate networks on one wire.</li>
    <li>Permission. Scanning a building network is a read-only operation, but it is
    still someone's production control system.</li>
  </ul>

  <p><a href="../index.html">Easy BACnet</a> does this from an Android phone: connect
  to the building's network, tap <em>Scan for Devices</em>, and it discovers the
  devices, reads every point on each one, and exports the whole thing as an Excel
  spreadsheet you can email straight from the phone. That is usually faster than getting a laptop onto a
  controls VLAN.</p>

  <h2>4. Read Object_List directly</h2>
  <p>If you are writing your own tooling: every BACnet IP device object exposes the
  <code>Object_List</code> property (property identifier 76), which enumerates every
  object on that device. Read index 0 first to get the count, then read each index
  in turn, then read <code>Object_Name</code> (77) and <code>Present_Value</code>
  (85) for each object you care about.</p>

  <p>Two practical warnings. Some inexpensive gateways cannot serve
  <code>Object_List</code> one index at a time and need the whole array requested in
  a single read. And a controller with hundreds of objects will return a list too
  large for one packet, which requires segmentation support in your client.</p>

  <h2>If the scan finds nothing</h2>
  <p>That is common and usually a network problem rather than a BACnet problem. See
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP devices</a>.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/vendor-asking-for-bacnet-information",
    title="What BACnet info to send a vendor | Easy BACnet",
    question="A vendor asked for my BACnet information &mdash; what do I send them?",
    description="What to hand a vendor or integrator who asks for your BACnet details: device IDs, IPs, a full points list, and how to export it as a spreadsheet.",
    answer_html="""<p>In almost every case they want four things: a
    <strong>points list</strong> (object type, instance number and name for each
    point), the <strong>device instance IDs and IP addresses</strong> of the
    controllers, the <strong>network layout</strong> (which devices sit behind a
    BACnet router or on MS/TP trunks), and a statement of whether they will need
    <strong>read-only or read-write</strong> access. A spreadsheet export from a network
    scan covers the first two in one step.</p>""",
    body_html="""
  <h2>The checklist</h2>
  <ol>
    <li><strong>Points list.</strong> Object type, object instance, point name,
    current value, units, and the device each point belongs to. This is the bulk of
    what they need. See
    <a href="what-is-a-bacnet-points-list.html">what a points list is</a> and
    <a href="how-to-find-your-bacnet-points-list.html">how to produce one</a>.</li>

    <li><strong>Device instance IDs.</strong> Every BACnet IP device has a unique
    instance number. Integrators address devices by this number, not by name, so a
    list of names alone will send them back to you.</li>

    <li><strong>IP addresses and port.</strong> Which subnet the controllers are on
    and whether they use the standard UDP port 47808 or something else.</li>

    <li><strong>Network topology.</strong> Are all devices on one IP subnet, or are
    some behind a BACnet router on an MS/TP trunk? Is there a BBMD, and where? If
    the vendor will connect from a different subnet or over a VPN, this determines
    whether discovery will work at all.</li>

    <li><strong>Access expectations.</strong> State plainly whether they are getting
    read-only access or whether they will be commanding points. If they will write,
    agree in advance on which BACnet priority level they may use &mdash; this is the
    single most common cause of a building being left in a bad state after an
    integration. See
    <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck overrides</a>.</li>

    <li><strong>A point of contact.</strong> Whoever maintains the control system,
    so the vendor is not guessing about what a cryptic point name means.</li>
  </ol>

  <h2>The fastest way to produce it</h2>
  <p>If you already have current documentation, send that. If you do not, a network
  scan produces items 1 and 2 in a few minutes.
  <a href="../index.html">Easy BACnet</a> was built for this handoff: connect
  a phone to the building network, scan, and email the resulting Excel spreadsheet
  (<code>.xlsx</code>) straight to the vendor. The export contains device ID, device name, device IP, object type, object
  number, point name, present value, units, and status for every point it found.</p>

  <h2>What to think twice about</h2>
  <ul>
    <li><strong>Do not put the control network on the public internet</strong> to
    make a vendor's life easier. If they need remote access, use a VPN with an
    account you can revoke.</li>
    <li><strong>A points list is a map of your building's controls.</strong> It is
    not usually sensitive on its own, but combined with remote access it is a
    complete attack surface description. Send it to a named person, not a shared
    inbox.</li>
    <li><strong>Watch out for write access granted casually.</strong> Read-only
    integration is safe. Write access to a live plant is a commissioning activity
    and deserves a scheduled window and someone on site.</li>
    <li><strong>Check for duplicate device IDs before you send.</strong> Two devices
    claiming the same instance number will break the vendor's integration and waste
    a site visit. A scan will flag them.</li>
  </ul>

  <h2>A reasonable reply template</h2>
  <pre><code>Attached is a points list (Excel) exported from a live scan on [date].
It covers [N] BACnet/IP devices on subnet [x.x.x.0/24], port 47808.

Columns: Device ID, Device Name, Device IP, Object Type,
Object Number, Point Name, Present Value, Units, Status.

Topology: [all devices on one IP subnet] / [devices 1001-1012 sit
behind a BACnet router at 10.x.x.x on an MS/TP trunk].

Access: read-only for now. Let us know if you need write access and
we will schedule a window and agree a priority level.

Technical contact: [name, email].</code></pre>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet IP points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
    ],
))

GUIDES.append(dict(
    slug="guides/why-cant-i-find-my-bacnet-devices",
    title="Why can't I find my BACnet IP devices? | Easy BACnet",
    question="Why can't I find my BACnet IP devices when I scan?",
    description="The usual reasons a BACnet IP scan finds nothing: wrong subnet, blocked broadcasts, no BBMD, mobile data on, or the wrong UDP port. How to fix each.",
    answer_html="""<p>Because the <em>Who-Is</em> broadcast is not reaching the
    devices. A scan only reaches equipment on the same IP subnet as your phone, so the
    first thing to rule out is that you are on the office or guest network instead of
    the controls network. After that, in order: the Wi-Fi is dropping or blocking
    broadcasts, the devices use a non-standard UDP port, or a firewall is blocking
    47808. A scan that finds nothing at all is a network problem. The devices
    themselves are rarely the cause.</p>""",
    body_html="""
  <h2>Check these in order</h2>

  <h3>1. Is the phone on the controls network?</h3>
  <p>Broadcasts do not cross routers, so your phone has to be on the same subnet as
  the controllers. When a scan finds nothing, Easy BACnet shows the phone's own IP
  address and subnet mask. Compare it with a controller's address (on its label, in
  its front-panel menu, or in the hand-over documents). With a 255.255.255.0 mask the
  first three numbers must match: a phone on 192.168.1.20 can find a controller on
  192.168.1.50 but not one on 10.20.30.50.</p>
  <p>If they do not match, you are on the wrong network. Guest Wi-Fi and the office
  network are the usual culprits; controls normally sit on their own network or VLAN.
  An address starting <code>169.254</code> means no DHCP server answered and the phone
  made one up, which is common when you plug straight into a controls switch. See
  <a href="subnets.html">what is a subnet, and why doesn't the switch give me the
  right one?</a> for how to get onto the right one.</p>
  <p>If Wi-Fi shows <em>Connected, no internet</em>, turn mobile data off and scan
  again. Android can route traffic over mobile data when the Wi-Fi has no internet
  access.</p>

  <h3>2. Is the network blocking the broadcast?</h3>
  <p>Wi-Fi access points drop broadcast frames under load, and guest or corporate
  Wi-Fi often has client isolation on, which stops wireless clients reaching other
  devices at all. Easy BACnet re-sends Who-Is throughout the scan, and if nothing
  answers it contacts each address on the subnet directly. If devices turn up that
  way, the scan summary says they <em>only answered when contacted directly</em>:
  the network is blocking broadcast replies, and other BACnet tools on that Wi-Fi
  will see nothing. The fix is a wired connection (a USB-Ethernet adapter into the
  controls switch) or a network that allows the traffic.</p>

  <h3>3. Are the devices on a non-standard port?</h3>
  <p>The standard is UDP 47808 (0xBAC0). Sites that run more than one BACnet network
  over the same wire put the others on 47809, 47810 and up. Easy BACnet checks the
  common alternates during a scan, but a device on an unusual port can be added
  with <strong>Add device by IP&hellip;</strong> and the right port typed in.</p>

  <h3>4. Is a firewall or access list in the way?</h3>
  <p>A switch or router access list can block UDP 47808 between VLANs even when
  addressing is correct. Phones have no host firewall to worry about, so if the
  first three checks pass this is a question for whoever runs the network.</p>

  <h2>If you find some devices but not others</h2>
  <ul>
    <li><strong>They are on another segment.</strong> The ones you found are on your
    subnet; the missing ones are behind a router. Add a known one by IP, or scan
    through the site's BBMD (below).</li>
    <li><strong>They are MS/TP devices behind a router that is not forwarding.</strong>
    MS/TP devices normally answer a Who-Is through their router, with a network
    number and MAC address instead of a plain IP. If a whole trunk is missing, the
    router or the trunk is the problem, which is a controls question.</li>
    <li><strong>The missing device is off</strong> or unplugged. Check power and the
    link light before anything else.</li>
    <li><strong>Two devices share a Device ID.</strong> One of them can appear to
    vanish, or the two swap places between scans. The scan summary warns about
    duplicates. See <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</li>
  </ul>

  <h2>If devices appear with no name or no points</h2>
  <p>The device answered discovery but is failing property reads. Give a large
  controller a minute, then back out and open it again. If it still shows nothing,
  it may be busy, it may only serve its object list in a form the client cannot
  read, or it may be an unconfigured unit still on the factory-default Device ID
  (the scan flags these as <em>needs commissioning</em>).</p>

  <h2>Reaching devices on another subnet</h2>
  <p>Two options in the menu (three dots, top right):</p>
  <ul>
    <li><strong>Add device by IP&hellip;</strong> contacts one controller directly at
    an address you know. It works across routers because it is not a broadcast. See
    <a href="bacnet-add-device-by-ip.html">add a device by IP</a>.</li>
    <li><strong>BBMD for remote networks&hellip;</strong> registers the phone with the
    site's BBMD so scans reach the subnets it serves. You need the BBMD's address from
    whoever manages the controls network. See <a href="what-is-a-bbmd.html">what is a
    BBMD?</a></li>
  </ul>
""",
    related=[
        ("guides/subnets", "What is a subnet, and why doesn&rsquo;t the switch give me the right one?"),
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet IP points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
    ],
))

GUIDES.append(dict(
    slug="guides/subnets",
    title="What is a subnet? BACnet/IP discovery | Easy BACnet",
    question="Why am I on the wrong network even though I'm plugged into the switch?",
    description="A switch port doesn't mean you're on the controls network. What a subnet is, why a port hands you the wrong one (VLANs, DHCP), and how to fix it.",
    answer_html="""<p>Plugging a cable into a switch only gives you a physical
    connection. Which <strong>network</strong> you actually land on &mdash; the
    <em>subnet</em> &mdash; is decided by how that switch port is configured, by
    the address a DHCP server hands you, or by the static address set on your own
    device. A single switch commonly carries several separate networks at once, so
    it can easily place you on the office or guest network instead of the controls
    network. BACnet IP discovery only reaches your own subnet, so when you are on the
    wrong one the scan finds nothing even though the cable is plugged in and the
    link light is on.</p>""",
    body_html="""
  <h2>What a subnet is, in plain terms</h2>
  <p>Think of the building's wiring as a set of separate mail systems that happen to
  share the same hallways. Each system &mdash; the office computers, the guest
  Wi-Fi, the heating/cooling/ventilation controls &mdash; is its own
  <strong>subnet</strong>: a group of devices that can talk to each other directly.
  A message sent within one subnet does not automatically reach another; getting
  between them requires a router (or, for BACnet broadcasts specifically, a BBMD).</p>
  <p>You can tell subnets apart by their address range. An address like
  <code>10.20.30.42</code> with a mask of <code>255.255.255.0</code> means "I am on
  the 10.20.30 network." A device at <code>192.168.1.55</code> is on a different
  network and, without a router between them, the two cannot hear each other.</p>

  <h2>Why "plugged into the switch" isn't enough</h2>
  <p>On anything bigger than a home network, switches are <strong>managed</strong>:
  one physical switch is divided into several logical networks (VLANs), and each
  port is assigned to one of them. The controls, the offices, the cameras and the
  guest Wi-Fi can all run through the same switch on different VLANs. So the port
  you happened to plug into decides which network you are on &mdash; and it is often
  not the controls network. A link light confirms the cable works. It says nothing
  about which subnet you were placed on.</p>

  <h2>The four common reasons the switch gives you the wrong subnet</h2>
  <h3>1. The port is on a different VLAN</h3>
  <p>The most common one. The jack you used is assigned to the office or guest VLAN,
  not the controls VLAN. Everything looks connected, but you are walled off from the
  controllers. The fix is a port (or a switch configuration change) on the controls
  VLAN &mdash; a network task, not something an app can do.</p>
  <h3>2. DHCP handed you an address from the wrong pool</h3>
  <p>If that VLAN has its own DHCP server, it gives you an address on <em>its</em>
  subnet &mdash; a perfectly valid address on the wrong network.</p>
  <h3>3. No DHCP answered, so your device made up an address</h3>
  <p>Controls networks often have no DHCP server at all &mdash; every controller is
  set by hand. Plug a laptop or phone expecting DHCP into that network and, after a
  timeout, it self-assigns an address starting with <code>169.254</code> (called
  APIPA). That address is on nothing useful and reaches nothing. Seeing
  <code>169.254.x.x</code> is a strong sign you need a static address on the controls
  subnet.</p>
  <h3>4. Your device has a static IP for another subnet</h3>
  <p>If your laptop was previously set to a fixed address for a different site or
  network, it will keep trying to use it here and land on the wrong subnet.</p>

  <h2>How to tell which subnet you are on</h2>
  <p>When a scan finds nothing, Easy BACnet shows this device's own address and
  subnet mask (for example <code>192.168.1.42 (mask 255.255.255.0)</code>). Compare
  the first three groups of numbers with the controllers' known range. If the
  controllers are on <code>10.20.30.x</code> and you are on <code>192.168.1.x</code>
  &mdash; or on <code>169.254.x.x</code> &mdash; that mismatch is why nothing was
  found. It is the first thing to check, and the first thing to tell whoever runs
  the network. (Some sites bridge subnets with a
  <a href="what-is-a-bbmd.html">BBMD</a>, which forwards BACnet broadcasts between
  them; ask whether one exists.)</p>

  <h2>How to get onto the right subnet</h2>
  <ul>
    <li><strong>Ask for a controls-network connection.</strong> Your network or HVAC
    provider can point you to a switch port on the controls VLAN, or put your port
    on it.</li>
    <li><strong>Get the right address.</strong> If that network uses DHCP, you'll be
    given a correct address automatically. If it doesn't (common for controls), ask
    for a free static IP, subnet mask and gateway on the controls subnet and set them
    on your device.</li>
    <li><strong>Ask whether there's a BBMD.</strong> If one exists, it can forward
    discovery from another subnet &mdash; you'll need its address.</li>
    <li><strong>Use a known device address.</strong> If you already know a
    controller's IP and it is reachable through a router, Easy BACnet's Browser Mode
    can add it directly by IP without a broadcast.</li>
  </ul>

  <h2>What to give your network and HVAC provider</h2>
  <p>Share three things and the conversation is usually short: the address and mask
  Easy BACnet shows for your device; the subnet the controllers are supposed to be
  on (if you know it); and which switch and port, or which jack, you are plugged
  into. That tells them immediately whether you are on the wrong VLAN and what to
  change. None of this is a fault with the equipment or the app &mdash; it is about
  which network your connection lands on.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
        ("guides/cant-find-what-im-looking-for", "The app can&rsquo;t find what I&rsquo;m looking for"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-priority-and-stuck-overrides",
    title="BACnet priority array and stuck overrides | Easy BACnet",
    question="Why is my BACnet point stuck, and how do I release an override?",
    description="How the BACnet priority array works, why a commanded point stays commanded, and how to release an override by writing NULL at the same priority level.",
    answer_html="""<p>Because a value written to a commandable BACnet point is
    <em>held</em> at the priority it was written at until something explicitly
    releases it. It does not time out, and it survives the tool that wrote it being
    closed or disconnected. To release it you write <code>NULL</code> to
    <code>Present_Value</code> at the <em>same priority level</em> that is holding the
    point. Then control falls to the next-highest occupied priority, or to
    <code>Relinquish_Default</code> if the array is empty.</p>""",
    body_html="""
  <h2>How the priority array works</h2>
  <p>Commandable BACnet objects &mdash; typically Analog Outputs and Values, Binary
  Outputs and Values, and Multi-state Outputs and Values &mdash; do not have a single
  present value. They have a <strong>priority array</strong> of 16 slots. Slot 1 is
  the highest priority, slot 16 the lowest. The object's actual
  <code>Present_Value</code> is whatever sits in the lowest-numbered occupied slot.</p>

  <p>When every slot is empty, the point falls back to its
  <code>Relinquish_Default</code> property. That is the value the object reverts to
  when nobody is commanding it at all.</p>

  <table>
    <tr><th>Priority</th><th>Conventional use</th></tr>
    <tr><td>1</td><td>Manual Life Safety</td></tr>
    <tr><td>2</td><td>Automatic Life Safety</td></tr>
    <tr><td>5</td><td>Critical Equipment Control</td></tr>
    <tr><td>6</td><td>Minimum On/Off</td></tr>
    <tr><td>8</td><td>Manual Operator &mdash; a person with a tool</td></tr>
    <tr><td>16</td><td>Lowest; often where the normal control program writes</td></tr>
  </table>

  <p>Only 1, 2, 5, 6 and 8 have meanings assigned by the standard. The rest are
  available and every vendor uses them a little differently, so agree a priority
  level with an integrator before they command anything. A write that carries no
  priority at all lands at 16.</p>

  <h2>Why the point is stuck</h2>
  <p>Someone wrote a value at a priority and never released it. In rough order of
  how often it happens:</p>
  <ul>
    <li>A technician overrode a point at priority 8 to test something and left.</li>
    <li>A graphics page has an override control that writes but no obvious release.</li>
    <li>An integration or analytics platform that commands points on a schedule
    stopped running, leaving its last command in place.</li>
  </ul>
  <p>The active priority tells you who is holding it. Priority 8 is a person with a
  tool. Priority 16 is usually the control program. Priority 1, 2, 5 or 6 is a safety
  or equipment-protection function and should be left alone.</p>
  <p>A related case that looks the same from the outside: the control program is
  still writing at 16 and something at a higher priority is outranking it. The
  program is not broken; it is losing. Releasing the higher slot fixes it.</p>

  <h2>How to release it</h2>
  <p>Write <code>NULL</code> to <code>Present_Value</code> at the priority that is
  holding the point. Writing a normal value at a lower priority does nothing, because
  the higher slot still wins. Writing NULL at a priority that is already empty also
  does nothing. After releasing, re-read the point: control should drop to the next
  occupied slot or to <code>Relinquish_Default</code>.</p>

  <h2>Release before you leave</h2>
  <p>A commanded point does not expire. A damper driven to 100% to test an actuator
  stays at 100% until somebody clears it, and the control program cannot tell anyone
  it is being overruled. Release every point you take command of before you leave
  site.</p>
  <p>In <a href="../index.html">Easy BACnet</a>, the point screen shows
  <strong>Commanded At</strong> (the active priority and its value) and
  <strong>Falls Back To</strong> (the relinquish default), and <strong>Release to
  Auto</strong> writes NULL at the priority you choose. Menu &rarr; <strong>Session
  write log</strong> lists every write and release since the app started, so you can
  check nothing was left behind.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-object-types-explained",
    title="BACnet Object Types: Full List with Type Numbers | Easy BACnet",
    question="What do the BACnet object types mean?",
    description="Reference table of BACnet object types: Analog and Binary Input/Output/Value, Multi-state, Device, Schedule, Trend Log and the rest, with what each is for.",
    answer_html="""<p>BACnet describes everything in a controller as an
    <em>object</em>, and the object's type tells you what kind of data it holds and
    how it behaves. The three families you will meet constantly are <strong>Analog</strong>
    (continuous numbers), <strong>Binary</strong> (two states) and
    <strong>Multi-state</strong> (a short list of named states). Each comes in
    Input, Output and Value flavours: Input means a physical sensor, Output a
    physical actuator, and Value a software point inside the controller's logic.</p>""",
    body_html="""
  <h2>The common types</h2>
  <table>
    <tr><th>#</th><th>Type</th><th>What it is</th></tr>
    <tr><td>0</td><td>Analog Input</td><td>A physical sensor reading a continuous value: a temperature, a pressure, a flow.</td></tr>
    <tr><td>1</td><td>Analog Output</td><td>A physical analog output driving something: a valve or damper position, a fan speed reference.</td></tr>
    <tr><td>2</td><td>Analog Value</td><td>A number inside the controller's logic: a setpoint, a calculated value, a tuning parameter.</td></tr>
    <tr><td>3</td><td>Binary Input</td><td>A physical two-state input: a status contact, a flow switch, an alarm contact.</td></tr>
    <tr><td>4</td><td>Binary Output</td><td>A physical two-state output: a relay starting a fan or opening a two-position valve.</td></tr>
    <tr><td>5</td><td>Binary Value</td><td>A two-state software point: an enable flag, a mode, a software alarm.</td></tr>
    <tr><td>8</td><td>Device</td><td>The controller itself. Holds the device name, model, vendor, and the <code>Object_List</code> that enumerates everything else.</td></tr>
    <tr><td>10</td><td>File</td><td>A file on the device, used for firmware and configuration transfer.</td></tr>
    <tr><td>13</td><td>Multi-State Input</td><td>A physical input with a small set of named states.</td></tr>
    <tr><td>14</td><td>Multi-State Output</td><td>A physical output with named states: Off / Low / High.</td></tr>
    <tr><td>15</td><td>Notification Class</td><td>Where alarms get routed and who gets told.</td></tr>
    <tr><td>16</td><td>Program</td><td>A control program running on the device.</td></tr>
    <tr><td>17</td><td>Schedule</td><td>A time-of-day schedule object that writes to other points.</td></tr>
    <tr><td>19</td><td>Multi-State Value</td><td>A software point with named states: Occupied / Unoccupied / Standby.</td></tr>
    <tr><td>20</td><td>Trend Log</td><td>Historical samples of another point, logged inside the controller.</td></tr>
    <tr><td>23</td><td>Accumulator</td><td>A running total, typically a utility meter.</td></tr>
  </table>
  <p>The numbers are the type codes BACnet uses on the wire; a type-plus-instance
  pair packed into one number is an Object Identifier, which our
  <a href="../bacnet-object-id-decoder.html">decoder tool</a> splits apart.</p>

  <h2>Input, Output, Value &mdash; the distinction that matters</h2>
  <p>The suffix tells you where the value comes from, and that determines whether
  you can write to it:</p>
  <ul>
    <li><strong>Input</strong> objects reflect a physical sensor. Writing to
    <code>Present_Value</code> is ignored unless you first set
    <code>Out_Of_Service</code> to true, which disconnects the object from the sensor
    so you can simulate a reading. That is a commissioning technique, and it is easy
    to leave behind by accident.</li>
    <li><strong>Output</strong> objects drive hardware and are commandable through
    the priority array.</li>
    <li><strong>Value</strong> objects live in software. Most are commandable; some
    are plain read/write properties with no priority array at all.</li>
  </ul>
  <p>See <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a> for what commandable actually means in practice.</p>

  <h2>Reading an object address</h2>
  <p>A point is identified by type plus instance number, so "Analog Input 4" and
  "Binary Input 4" are two different points on the same controller. Tools write this
  various ways &mdash; <code>AI:4</code>, <code>AI-4</code>, <code>analog-input,4</code>
  &mdash; but they all mean the same pair.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-priority-and-stuck-overrides", "Why is my BACnet point stuck?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-device-id-explained",
    title="What is a BACnet Device ID? | Easy BACnet",
    question="What is a BACnet Device ID, and why do duplicates matter?",
    description="A BACnet Device ID (device instance) uniquely identifies a controller across the whole network. What it is, and why duplicates break discovery.",
    answer_html="""<p>The Device ID &mdash; properly the <em>device instance
    number</em> &mdash; is a number from 0 to 4194302 that uniquely identifies one
    controller across the entire BACnet internetwork, not just its local subnet.
    Integrators address devices by this number rather than by name or IP, so it has
    to be unique. Two devices sharing one ID will break discovery and integration in
    ways that are hard to diagnose. A device reporting <strong>4194303</strong> is
    sitting on the factory default and was never commissioned.</p>""",
    body_html="""
  <h2>Why it exists</h2>
  <p>IP addresses change, names get edited, and MS/TP devices have no IP address at
  all. The device instance number is the one stable identifier that works across the
  whole internetwork, including devices sitting behind routers on twisted-pair
  trunks. When a vendor asks for your BACnet information, this is the number they
  actually need.</p>

  <p>It is carried in the device object's identifier: object type 8, instance
  <em>N</em>. Discovery works by broadcasting <em>Who-Is</em> and collecting the
  <em>I-Am</em> replies, each of which announces the responding device's instance
  number.</p>

  <h2>Why duplicates break things</h2>
  <p>The standard requires the number to be unique. When two controllers claim the
  same one:</p>
  <ul>
    <li>Discovery becomes non-deterministic &mdash; whichever device answers first
    wins, and it may not be the same one twice.</li>
    <li>An integration mapped to that ID will silently read from, or write to, the
    wrong controller.</li>
    <li>One of the devices may appear to vanish from the network entirely.</li>
  </ul>
  <p>Duplicates typically come from a contractor imaging several controllers from one
  template, or from a replacement unit installed without being renumbered. They are
  worth checking for before handing a points list to anyone &mdash; a scan that reports
  the same instance number at two different IP addresses has found one.</p>

  <h2>4194303 means "never commissioned"</h2>
  <p>The value 4194303 (0x3FFFFF) is the uninitialized default many manufacturers
  ship. A device reporting it has never been given a real ID. If several such devices
  are on one network they all share it, and there is no reliable way to address any
  of them individually until they are commissioned.</p>

  <h2>Choosing numbers</h2>
  <p>Most sites use a scheme that encodes something useful &mdash; building number,
  floor, or panel &mdash; for example 21001 through 21099 for building 2, floor 1.
  Any scheme is fine as long as it is written down and genuinely unique. What causes
  pain later is a site where every panel starts at 1.</p>
""",
    related=[
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
    ],
))


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# How-to guides for the app itself (added 2026-09-15)
# ---------------------------------------------------------------------------

GUIDES.append(dict(
    slug="guides/how-to-use-easy-bacnet",
    title="How to Get a BACnet IP Points List | Easy BACnet",
    question="How do I get a BACnet IP points list off a building?",
    description="Step by step: join the building network, scan for BACnet IP devices, check their points, and share the whole lot as an Excel report. No laptop needed.",
    answer_html="""<p>Connect your phone to the same network as the building
    controls, open the app and tap the <strong>Easy BACnet Mode</strong> card, tap
    <strong>Scan for Devices</strong>, wait for the scan to finish, then tap
    <strong>Export Results</strong>. The app reads every point on every device it
    found, builds an Excel spreadsheet (<code>.xlsx</code>) and opens your phone's
    share sheet so you can email it or save it wherever you like. Tap
    <strong>View Results</strong> instead if you want to look at the devices and
    points on the phone first.</p>""",
    body_html="""
  <h2>Before you start</h2>
  <ul>
    <li><strong>Be on the same network as the controls.</strong> Join the
    building's Wi-Fi, or plug the phone into the controls network with a
    USB-Ethernet adapter. A phone on guest Wi-Fi or on mobile data will find
    nothing. See
    <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet
    devices?</a> if the scan comes back empty.</li>
    <li><strong>You do not need anyone's password.</strong> BACnet has no login.
    If you are on the network, the devices will answer.</li>
    <li><strong>Easy BACnet speaks BACnet IP.</strong> MS/TP (RS-485) devices show
    up only when a BACnet router publishes them onto IP &mdash; see
    <a href="does-easy-bacnet-support-mstp-rs485.html">does Easy BACnet support
    MS/TP?</a></li>
  </ul>

  <h2>Step 1 &mdash; Open Easy BACnet Mode</h2>
  <p>The first time you open the app it asks you to <strong>Choose your
  language</strong> (English, Espa&ntilde;ol, Deutsch, Fran&ccedil;ais, Portugu&ecirc;s
  or Thai) and to accept a short safety notice (<strong>I Agree</strong>). After that
  it opens on <em>Choose how you want to work today</em> and four cards:</p>
  <ul>
    <li><strong>Easy BACnet Mode</strong> &mdash; the simple scan, read and export flow
    this guide covers.</li>
    <li><strong>Browser Mode</strong> &mdash; a diagnostic console with routing and
    vendor detail, and a tool to read any property of any object by number.</li>
    <li><strong>Custom Remotes</strong> &mdash; your own control screen for one device
    (<a href="how-to-build-a-custom-remote.html">guide</a>).</li>
    <li><strong>Control Panel Builder</strong> (beta) &mdash; one control screen for up
    to 32 devices, in the beta version of the mobile app only
    (<a href="how-to-build-a-control-panel.html">guide</a>).</li>
  </ul>
  <p>Tap <strong>Easy BACnet Mode</strong>.</p>

  <h2>Step 2 &mdash; Scan</h2>
  <p>Tap <strong>Scan for Devices</strong>. The app broadcasts a BACnet
  <em>Who-Is</em> and listens for replies, re-sending it through the scan because
  Wi-Fi access points drop broadcast packets routinely and one shot is not reliable.
  It also checks the common alternate ports, and if broadcasts seem to be blocked it
  contacts each address on your subnet directly. A counter shows the seconds elapsed
  and how many devices have answered; then it reads each device's name. The whole
  scan can take up to a minute &mdash; let it run to the end.</p>
  <p>When it finishes you get a green banner &mdash; <em>Success! Found 6
  device(s)</em> &mdash; or a red one, <em>No devices found</em>. On success two
  buttons appear: <strong>View Results</strong> and <strong>Export Results</strong>.
  If it comes back red, the screen shows your phone's own IP address and mask and a
  checklist; see also
  <a href="cant-find-what-im-looking-for.html">the app can't find what I'm
  looking for</a>.</p>
  <div class="callout">
  <p>If the summary warns about <strong>unconfigured devices</strong> (still on the
  factory-default ID) or <strong>duplicate Device IDs</strong>, tell whoever looks
  after the system. Both are commissioning mistakes that will cause trouble for any
  integrator later. See
  <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a> and
  <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</p>
  </div>

  <h3>Devices on another subnet</h3>
  <p>A broadcast scan only reaches your own subnet. For anything further away, open
  the menu (three dots, top right):</p>
  <ul>
    <li><strong>Add device by IP&hellip;</strong> &mdash; type the controller's
    <em>IP address or host name</em> and <em>UDP port</em> (47808 is standard) and tap
    <strong>Add</strong>. See <a href="bacnet-add-device-by-ip.html">add a device by
    IP</a>.</li>
    <li><strong>BBMD for remote networks&hellip;</strong> &mdash; enter the site's BBMD
    address once and every scan registers the phone as a foreign device and reaches
    the networks it serves. See <a href="what-is-a-bbmd.html">what is a BBMD?</a></li>
  </ul>

  <h2>Step 3 &mdash; Look at what it found (optional)</h2>
  <p>Tap <strong>View Results</strong>. Each device shows its name, Device ID
  and IP address. Tap a device (its screen also shows the model, when the device
  reports one) and the app reads its full object list. On a big controller this
  can take a minute: the app reads one object at a time rather than in bulk,
  because bulk reads fail on a lot of older and cheaper controllers. It loads up
  to 2,000 objects automatically; past that, use the menu's <strong>Add object by
  number</strong> (<a href="bacnet-add-object-by-number.html">how</a>).</p>
  <p>Tap a point to see its <strong>Present Value</strong>, <strong>Units</strong>,
  <strong>Status</strong> and <strong>Description</strong>, with a
  <strong>Refresh</strong> button for a fresh read. On points that can be
  commanded you also see <strong>Commanded At</strong> and <strong>Falls Back
  To</strong>: whether something is currently overriding the point, at what
  priority, and what it will do when released. If you are chasing a damper that
  will not close or a fan that will not stop, this is the screen that explains it.</p>

  <h2>Step 4 &mdash; Export</h2>
  <p>Back on the main screen, tap <strong>Export Results</strong>. On the free
  version the app first asks <em>Watch a short ad?</em> &mdash; choose
  <strong>Watch ad</strong> to continue, <strong>Remove ads</strong> to see Easy
  BACnet Pro, or <strong>Cancel</strong>. No ad ever plays unless you choose it,
  and if no ad can load (no signal in the plant room) the export simply goes ahead.</p>
  <p>The app then reads every point on every device &mdash; names, present values,
  units and status. A progress box (<em>Exporting BACnet IP Results</em>) shows which
  device and which point it is on; <strong>Cancel</strong> stops it. Do not walk out
  of Wi-Fi range while it runs.</p>
  <p>When it finishes, Android's share sheet opens titled <em>Send export by
  email</em>, with a file named like <code>EasyBACnet_20260930_1415.xlsx</code>
  attached, the subject <em>BACnet IP Export</em> plus the date, and a line saying
  how many devices and points it holds. Pick your email app and address it, or pick
  any other app (Drive, Files, a messenger) to save or send it. The app never sends
  anything itself and has no idea who your integrator is.</p>

  <h2>What is in the spreadsheet</h2>
  <p>One sheet, two tables:</p>
  <ul>
    <li><strong>Device summary</strong> at the top: <em>Devices Found</em>, then one row
    per device with Device ID, Device Name, Device IP and the number of Points.</li>
    <li><strong>Point detail</strong> below it, one row per point: Device ID, Device
    Name, Device IP, Object Type, Object Number, Point Name, Present Value, Units,
    Status. Each device also gets its own bold row, so every device and its IP is
    listed even if it has no points.</li>
  </ul>
  <p>Any point whose Status is not <em>Normal</em> (in alarm, fault, overridden or out
  of service) is shaded red so it cannot be scrolled past. IDs and object numbers are
  stored as real numbers, so you can sort and filter straight away. That is exactly
  what someone asking for a points list needs &mdash; see
  <a href="vendor-asking-for-bacnet-information.html">a vendor asked for my BACnet
  information</a> and <a href="export-bacnet-points-to-csv.html">exporting to Excel
  or CSV</a>.</p>

  <h2>Good to know</h2>
  <ul>
    <li><strong>Nothing is uploaded anywhere.</strong> The app has no account and
    no server. The spreadsheet exists on your phone and wherever you send it.</li>
    <li><strong>Scanning and reading cannot change anything</strong> on the
    equipment. Writing is a separate, deliberately awkward mode &mdash; see
    <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet
    point</a>.</li>
    <li><strong>Dark screen by default.</strong> The app opens dark whatever your
    phone is set to, because plant rooms are dark. Change it under
    <strong>Appearance</strong> in the menu (Dark, Light or Follow system) if you are
    working in sunlight. <strong>Language</strong> is in the same menu.</li>
    <li><strong>Scan results are not saved.</strong> They live in memory while the
    app is open; export them if you want a record.</li>
  </ul>
""",
    related=[
        ("guides/export-bacnet-points-to-csv", "How do I export a BACnet IP points list to Excel or CSV?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/how-to-build-a-custom-remote", "How do I build a custom remote in Easy BACnet?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-write-to-a-bacnet-point",
    title="How to write to a BACnet point | Easy BACnet",
    question="How do I write to a BACnet point with Easy BACnet, and release it afterwards?",
    description="Turn on write mode, choose a priority, confirm the write, then the part people forget: release the point back to automatic control before you leave.",
    answer_html="""<p>Turn on <strong>Write mode</strong> from the menu on the home
    screen and accept the warning. Open the point, tap <strong>Write Value</strong>,
    enter the new value, leave the priority at <strong>8</strong>
    unless you know better, tap <strong>Review&hellip;</strong>, check the summary, then
    <strong>Write it</strong>. When you are done, tap <strong>Release to Auto</strong>
    on the same point. A BACnet command does not expire on its own; if you do not
    release it, the point stays where you left it after you drive away.</p>""",
    body_html="""
  <h2>Why write mode is off, and turns itself off</h2>
  <p>Easy BACnet opens with writing disabled every single time. This is not a
  setting it remembers. Someone who picked the app up to read a temperature
  should never be two taps away from commanding a damper, and a phone left
  unlocked on a bench should not be able to change a building. Turn it on when
  you need it; the app turns it off for you when it next starts.</p>

  <h2>Step 1 &mdash; Turn on write mode</h2>
  <p>On the home screen, open the menu (the three dots, top right) and tap
  <strong>Write mode</strong>. Read the warning. It says, in short: a value you
  write is held at the priority you choose until it is released, it does not
  time out, and closing the app does not undo it. Tap <strong>I understand
  &mdash; turn it on</strong>.</p>
  <p>Already on a point? If write mode is off, a commandable point shows <em>Write mode is
  off, so this point can be read but not changed</em> with an <strong>Enable Write
  Mode</strong> button that opens the same warning.</p>

  <h2>Step 2 &mdash; Look before you write</h2>
  <p>Open the point. Two rows matter here:</p>
  <ul>
    <li><strong>Commanded At</strong> &mdash; whether something is already
    overriding this point, and at what priority. <em>Not commanded &mdash;
    following its own program</em> means the controller's own logic is in
    charge. <em>Priority 8 (68)</em> means somebody has already written 68 at
    priority 8 and it is holding.</li>
    <li><strong>Falls Back To</strong> &mdash; what the point will do once every
    override is released. This is the relinquish default.</li>
  </ul>
  <p>If the point is already commanded at a <em>higher</em> priority than you
  are about to use (a lower number), your write will be accepted and ignored.
  That is BACnet behaving correctly &mdash; see
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>

  <h2>Step 3 &mdash; Write</h2>
  <p>Tap <strong>Write Value</strong>. Enter the new value &mdash; for a binary
  point you pick <em>Active (On)</em> or <em>Inactive (Off)</em> from a list
  instead of typing. Choose a <strong>Priority</strong>. The default,
  <strong>8</strong>, is the conventional level for a person with a tool
  standing in front of the equipment (priority 8 is the &ldquo;manual operator&rdquo;
  level in BACnet), and it is the right choice unless a site standard says
  otherwise.</p>
  <p>Tap <strong>Review&hellip;</strong>. You get a summary (<em>Confirm write</em>): the point, the device, the
  old value, the new value and the priority, and a reminder that this takes
  command of the point until you release it. Tap <strong>Write it</strong>.</p>
  <p>The app sends the write, waits for the controller to acknowledge, then
  re-reads the point so what you see is what the device actually did, not what
  you asked for. If the controller refused, you get its reason in plain words.</p>

  <h2>Step 4 &mdash; Release it before you leave</h2>
  <p>This is the step that matters. Tap <strong>Release to Auto</strong> on the
  point, check what it will fall back to, tap <strong>Release it</strong>, and the app
  writes a release (a NULL) at the priority you used. A <strong>Release</strong> control on a
  <a href="how-to-build-a-custom-remote.html">custom remote</a> does the same in one tap. The
  point drops back to the next override, or to its <em>Falls Back To</em>
  value if there is none. <strong>Commanded At</strong> should now read
  <em>Not commanded</em>.</p>
  <div class="callout">
  <p>A fan commanded on at priority 8 and never released keeps running until
  someone finds the override, which can be months. Releasing is the second half
  of writing, not an extra.</p>
  </div>

  <h2>Checking what you did</h2>
  <p>Menu &rarr; <strong>Session write log</strong> lists every write and release
  this session, with the time, the point, old and new values, the priority, and
  whether the controller accepted it. Read it before you walk out. If anything
  is still commanded that should not be, the log tells you where.</p>

  <h2>Points that will not accept a write</h2>
  <ul>
    <li><strong>Input points</strong> (Analog Input, Binary Input, Multi-State
    Input) ignore a write unless the point is <em>Out Of Service</em>, because
    their value belongs to the physical sensor. The app warns you about this
    before you try.</li>
    <li><strong>Points with no priority array</strong> may still accept a write
    but cannot be released &mdash; there is nothing to release. The app only
    offers <em>Release to Auto</em> when the point is actually commandable.</li>
  </ul>
""",
    related=[
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/how-to-use-easy-bacnet", "How do I get a BACnet IP points list?"),
        ("guides/how-to-build-a-custom-remote", "How do I build a custom remote in Easy BACnet?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-build-a-custom-remote",
    title="How to build a custom remote in Easy BACnet",
    question="How do I build a custom remote for a BACnet IP device in Easy BACnet?",
    description="Step by step: build a drag-and-drop control screen for one BACnet IP device. All seven control types, edit mode, the grid, .ebremote sharing, free limit.",
    answer_html="""<p>Scan, open a device, tap the menu (three dots) and choose
    <strong>Custom Remote</strong>. Tap <strong>Edit</strong>, then <strong>Add Control</strong>:
    pick a point from the device's list (or <strong>Enter a point by hand</strong>), then
    choose a control type &mdash; <strong>Readout</strong>, <strong>Indicator</strong>,
    <strong>Setpoint</strong>, <strong>Toggle</strong>, <strong>Button</strong>,
    <strong>Multi-state</strong> or <strong>Release</strong>. Drag controls around the
    four-column grid, tap one to rename, resize, recolour or set its write priority, then tap
    <strong>Done</strong>. Saved remotes live under <strong>My Remotes</strong>; long-press one
    to export it as an <code>.ebremote</code> file. The free version keeps one remote (opening
    it asks to show a short ad); Easy BACnet Pro, a $9.99-a-year subscription, removes the ads
    and the limit.</p>""",
    body_html="""
  <div class="callout">
  <p>Need one screen for <strong>several</strong> devices &mdash; a whole boiler room? That is
  the <a href="how-to-build-a-control-panel.html">Control Panel Builder</a>, which uses the same
  designer for up to 32 devices at once. It is in beta and only in the beta version of the
  mobile app.</p>
  </div>

  <h2>What a custom remote is for</h2>
  <p>The point list shows everything a controller has &mdash; eighty rows on a typical rooftop
  unit. A custom remote is the six of those you actually touch, laid out as big controls on one
  screen: the zone setpoint, the fan, the mode, the supply temperature. You build it once per
  device and it is there every visit. Each device has one remote, and the remote follows the
  device by its <strong>Device ID</strong>, so it survives an IP change.</p>

  <h2>Step 1 &mdash; Open (or create) the device's remote</h2>
  <p>Any of these gets you there:</p>
  <ul>
    <li><strong>From a scan:</strong> in <strong>Easy BACnet Mode</strong> tap <strong>Scan for
    Devices</strong>, then <strong>View Results</strong>, tap the device, open the menu (three
    dots) and tap <strong>Custom Remote</strong>.</li>
    <li><strong>From the opening screen:</strong> tap the <strong>Custom Remotes</strong> card.
    The <strong>My Remotes</strong> screen lists your saved remotes. With none yet it offers
    <strong>Scan for Devices</strong> (no scan this session) or <strong>Choose a Device</strong>
    (pick from <em>Build a remote for which device?</em>).</li>
    <li><strong>From the main screen:</strong> the <strong>My Remotes (n)</strong> button, or
    <strong>My Remotes</strong> in the menu.</li>
  </ul>
  <p>A new remote opens empty: <em>No controls yet. Tap Edit, then Add Control.</em></p>

  <h2>Step 2 &mdash; Turn on Edit mode and add a control</h2>
  <p>Tap <strong>Edit</strong> in the top bar. The hint reads <em>Drag controls to rearrange
  them. Tap one to change it.</em> Nothing is sent to the device while you edit. Tap
  <strong>Add Control</strong>; under <em>Add a control</em> choose how to pick the point:</p>
  <ul>
    <li><strong>Pick from this device&rsquo;s points</strong> &mdash; the list the app already
    read, under <em>Choose a point</em>. If you see <em>This device&rsquo;s point list has not
    loaded yet</em>, go back and open the device's point list once, or enter the point by
    hand.</li>
    <li><strong>Enter a point by hand</strong> &mdash; an <strong>Object type</strong> and
    <strong>Object instance</strong>. Use it for a point beyond the 2,000-object load limit or
    one you know from a points list.</li>
  </ul>
  <p>Then <strong>Choose a control type</strong> (each row shows a small picture of the
  control):</p>
  <table>
    <tr><th>Control</th><th>What it does</th><th>Use it for</th></tr>
    <tr><td>Readout</td><td>Live value, never writes.</td><td>Supply temperature, pressure, anything you just want to see.</td></tr>
    <tr><td>Indicator</td><td>Status light, read-only. Lit when the value is at or above a threshold.</td><td>Fan status, alarm, filter switch &mdash; binary or analog inputs.</td></tr>
    <tr><td>Setpoint</td><td>Minus / value / plus. Tap the value to type an exact number.</td><td>Zone setpoint, damper minimum, any analog you adjust.</td></tr>
    <tr><td>Toggle</td><td>Switches between on and off.</td><td>Fan enable, occupancy override, pump command.</td></tr>
    <tr><td>Button</td><td>Sends one fixed value when tapped (after a confirmation).</td><td>A reset, a &ldquo;go to 100%&rdquo;.</td></tr>
    <tr><td>Multi-state</td><td>Pick a named state.</td><td>Fan speed Off/Low/High, operating mode.</td></tr>
    <tr><td>Release</td><td>Hands the point back to automatic at this control's priority.</td><td>Put one next to every control that writes.</td></tr>
  </table>
  <p>The control lands in the first free spot on the grid, labelled with the point name.</p>

  <h2>Step 3 &mdash; Arrange it on the grid</h2>
  <p>A remote is a <strong>four-column grid</strong>. In Edit mode, <strong>press and
  drag</strong> a control to move it: it snaps to the grid and will not land on top of another
  control. To make a control wider, tap it and choose <strong>Width</strong>; if there is no
  room at that width you will see <em>No room at that width. Move the control first.</em></p>

  <h2>Step 4 &mdash; Configure each control</h2>
  <p>In Edit mode, <strong>tap</strong> a control for its options. Every control has:</p>
  <ul>
    <li><strong>Rename control</strong> &mdash; label it by what it does
    (&ldquo;Boiler 2 enable&rdquo; beats &ldquo;BO-3&rdquo;).</li>
    <li><strong>Width</strong> &mdash; 1 to 4 columns (setpoints and multi-state pickers need
    at least 2).</li>
    <li><strong>Write priority</strong> &mdash; the BACnet priority (1&ndash;16) its writes and
    releases use. 8 (manual operator) is the default; see
    <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority</a>.</li>
    <li><strong>Colour</strong> &mdash; Theme default, Blue, Green (running / normal), Amber
    (caution) or Red (stops equipment).</li>
    <li><strong>Card style</strong> &mdash; Filled (default), Outlined (quieter, good for
    readouts) or Bold (tinted, for controls that act).</li>
    <li><strong>Toggle large value text</strong> &mdash; oversized digits for the one value you
    read from across the room.</li>
    <li><strong>Delete control</strong>.</li>
  </ul>
  <p>Plus, by type:</p>
  <ul>
    <li><strong>Setpoint:</strong> <strong>Step size</strong> &mdash; how far one press of minus
    or plus moves it.</li>
    <li><strong>Button:</strong> <strong>Value to send</strong>.</li>
    <li><strong>Multi-state:</strong> <strong>State names</strong> &mdash; one per line, the
    first line is state 1.</li>
    <li><strong>Indicator:</strong> <strong>Indicator style</strong> (Lamp, LED, Pill, Bar or
    Ring), <strong>On colour</strong> and <strong>Off colour</strong> (green, red, amber or blue;
    default green on, red off), and <strong>On at / above</strong> &mdash; the threshold that
    lights it (0.5 by default, so a binary 1 is on).</li>
  </ul>
  <div class="callout">
  <p>Use colour to mark what acts. Make the control that stops a fan
  <strong>red</strong> and leave readouts plain, so the one that matters stands out
  when you are up a ladder with gloves on.</p>
  </div>
  <p>Everything saves as you go. In Edit mode the menu also has <strong>Rename remote</strong>
  and <strong>Delete remote</strong> (which removes the controls from this phone only; nothing
  on the device changes). Tap <strong>Done</strong> when it looks right.</p>

  <h2>Step 5 &mdash; Use it</h2>
  <p>Out of Edit mode the remote is live. The status line at the top tells you the truth about
  the connection: <strong>Online</strong> with the time of the last reply, <strong>Some points
  not answering</strong>, or <strong>No response from device</strong> &mdash; and when the
  device stops answering, values grey out rather than sitting there looking current. Tap
  <strong>Refresh</strong> for a fresh read of everything.</p>
  <p>Controls that write need <strong>Write mode</strong> turned on from the menu on the main
  screen, exactly like the point screen &mdash; see
  <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet point</a>. Until then
  the remote says <em>Read-only</em>. With write mode on, know what acts at once and what asks
  first: the setpoint's <strong>minus/plus</strong>, a <strong>toggle</strong> and picking a
  <strong>multi-state</strong> state write immediately; a <strong>typed setpoint
  value</strong>, a <strong>button</strong> and a <strong>release</strong> ask you to confirm.
  A toggle or step will not act until the point has been read (<em>No value read yet &mdash;
  tap Refresh first</em>), so it never guesses. Every write and release appears in the
  <strong>Session write log</strong> on the main screen's menu.</p>

  <h2>Coming back to it</h2>
  <p>Saved remotes appear under <strong>My Remotes</strong>, one per device, showing the device
  name, how many controls it has and its last known IP address. Open one and it talks to the
  controller directly at that address &mdash; no scan needed. If the controller has moved, the
  remote reports it unreachable and a fresh scan puts it right.</p>

  <h2>Sharing a remote: export and import</h2>
  <ul>
    <li><strong>Export:</strong> on <strong>My Remotes</strong>, <strong>long-press</strong> a
    remote. Android's save dialog opens with a file named after the device
    (<code>Device&nbsp;name.ebremote</code>); save it to Downloads, Drive or wherever you like,
    then send it as you would any file.</li>
    <li><strong>Import:</strong> on <strong>My Remotes</strong>, menu &rarr; <strong>Import
    remote</strong>, then pick the <code>.ebremote</code> file. If you already have a remote for
    that device, the app asks <em>Replace the existing remote?</em> first. A control-panel file
    (<code>.ebpanel</code>) is refused here &mdash; import it in Control Panel Builder (beta
    version of the app only).</li>
  </ul>
  <p>The file is plain JSON holding the layout, the device's ID and its last known address. It
  holds no values from the building.</p>

  <h2>Free vs Easy BACnet Pro</h2>
  <p>Scanning, reading, writing and exporting are free. Custom remotes are limited on the
  free version, but gently: on the free version you can keep <strong>one</strong> remote (for
  one device). Opening that saved remote asks <em>Watch a short ad?</em> &mdash; choose
  <strong>Watch ad</strong>, <strong>Remove ads</strong> or <strong>Cancel</strong>; no ad
  plays unless you choose it. If no ad can load &mdash; common in a plant room with no signal
  &mdash; the remote just opens, so you are never locked out of your own controls. Building or
  importing a second remote shows <em>One remote on the free version</em> with an
  <strong>Unlock</strong> button.</p>
  <p><strong>Easy BACnet Pro</strong> is a Google Play subscription: $9.99 a year (Play shows
  the price in your currency), with a 14-day free trial if you have never had it before. It
  removes the ads and lifts the limit: as many remotes as you like, on as many devices as you
  look after. Cancel any time in Google Play &rsaquo; Subscriptions; Pro stays on until the end
  of the year you paid for. If it ends, your remotes are kept &mdash; nothing is deleted &mdash;
  but the free limit and the ads come back.</p>
""",
    related=[
        ("guides/how-to-build-a-control-panel", "How do I build a control panel for several devices?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/how-to-use-easy-bacnet", "How do I get a BACnet IP points list?"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-build-a-control-panel",
    title="Build a multi-device BACnet control panel | Easy BACnet",
    question="How do I build a custom BACnet control panel for several devices in Easy BACnet?",
    description="Step by step: one live control screen for up to 32 BACnet IP devices with the Control Panel Builder, in beta on the mobile app. Devices, grid width, controls, sharing.",
    answer_html="""<p>The Control Panel Builder is in beta on the mobile app: it is only in the
    beta version of Easy BACnet, not the standard Play Store release. In the beta app, on the
    opening screen tap <strong>Control Panel Builder</strong>, then
    <strong>New panel</strong> (the <strong>+</strong> in the top bar, or <strong>Create a
    Panel</strong>). Pick the first device from your scan and name the panel; it opens in Edit
    mode. Tap <strong>Add Control</strong> to place a readout, setpoint, toggle, button,
    multi-state picker or release button, each bound to one point on one device. Add more
    devices from the menu's <strong>Devices&hellip;</strong> &mdash; up to 32 per panel &mdash;
    set the <strong>Grid width</strong>, drag controls into place, then tap
    <strong>Done</strong> to use it live. The builder is in beta; the free version keeps one
    panel driving one device, and Easy BACnet Pro ($9.99 a year) allows unlimited panels with
    up to 32 devices each.</p>""",
    body_html="""
  <h2>Remote or control panel?</h2>
  <p>A <a href="how-to-build-a-custom-remote.html">custom remote</a> is one screen for
  <strong>one</strong> device. A <strong>control panel</strong> uses the same drag-and-drop
  designer, but every control can point at a <strong>different</strong> device &mdash; up to 32
  on one panel. Build a remote for the rooftop unit you visit every week; build a control panel
  for the boiler room, where four boilers, two pumps and the outdoor-air sensor are all separate
  BACnet IP devices and you want them on one screen.</p>
  <div class="callout">
  <p><strong>Beta on the mobile app.</strong> The Control Panel Builder is only in the beta
  version of the Easy BACnet mobile app; the standard Play Store release does not include it
  yet. It works end to end, but check each control against the equipment the first time you
  use it. Panels are saved on your phone and can be shared as <code>.ebpanel</code> files.</p>
  </div>

  <h2>Before you start</h2>
  <ul>
    <li><strong>Scan first.</strong> The builder picks devices from your last scan. If you have
    not scanned this session it says <em>Scan for devices first, then build a panel from what you
    find</em> and takes you to Easy BACnet Mode. Devices on another subnet can be added with
    <strong>Add device by IP&hellip;</strong> or a <strong>BBMD</strong> before you start (see
    <a href="bacnet-add-device-by-ip.html">add a device by IP</a>), or typed in by hand later.</li>
    <li><strong>Load the point lists</strong> of the devices you want to control (open each one
    from <strong>View Results</strong>) if you want to pick points by name. Otherwise you can
    enter any point by object type and instance number.</li>
    <li><strong>Know which points are commandable.</strong> Readouts work on anything; setpoints,
    toggles, buttons and multi-state pickers need a point that accepts writes &mdash; see
    <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet point</a>.</li>
  </ul>

  <h2>Step 1 &mdash; Create the panel</h2>
  <p>On the opening screen tap the <strong>Control Panel Builder</strong> card. The
  <strong>Control Panels</strong> screen lists your saved panels. Tap the <strong>+</strong>
  (<strong>New panel</strong>) in the top bar, or <strong>Create a Panel</strong> if you have
  none yet. Choose the first device in <strong>Start the panel with which device?</strong>
  &mdash; this becomes the panel's <em>primary</em> device, the one controls use unless you
  point them elsewhere. Give it a name in <strong>Name this panel</strong> (the device name is
  pre-filled) and tap OK. The panel opens straight into Edit mode with a four-column grid.</p>

  <h2>Step 2 &mdash; Add the other devices</h2>
  <p>In Edit mode open the menu (three dots) and tap <strong>Devices&hellip;</strong>. The
  dialog title shows how many devices the panel drives (<em>Devices &mdash; 1 of 32</em>); the
  list shows <em>Primary: &hellip;</em> first, then any extra devices with their IP addresses,
  and <strong>Add a device</strong> at the bottom. Add a device by either:</p>
  <ul>
    <li><strong>Picking it from your scan</strong> &mdash; devices already on the panel are left
    out of the list; or</li>
    <li><strong>Enter a device by hand</strong> &mdash; <em>Name (optional)</em>, <em>Device
    ID</em>, and <em>IP address (optional)</em>. Use this for a controller the scan cannot see.
    A device with no address cannot be reached until a scan finds it (the control shows
    <em>This control's device isn't reachable</em>).</li>
  </ul>
  <p>A panel can drive up to <strong>32 devices</strong>, including the primary; past that you
  see <em>A control panel can drive up to 32 devices</em>. Adding the same Device ID twice is
  refused. To remove an extra device, tap it in the list: <em>Remove this device?</em> warns how
  many of its controls will fall back to the primary device &mdash; check those controls
  afterwards. The primary device cannot be removed.</p>

  <h2>Step 3 &mdash; Add controls</h2>
  <p>Tap <strong>Add Control</strong>. When the panel has more than one device you first choose
  <strong>Add a control for which device?</strong>. Then pick the point:</p>
  <ul>
    <li><strong>Pick from this device&rsquo;s points</strong> &mdash; the list from your scan
    (open the device's point list once first if it says the list has not loaded).</li>
    <li><strong>Enter a point by hand</strong> &mdash; <strong>Object type</strong> plus
    <strong>Object instance</strong>, for a point you know but did not enumerate.</li>
  </ul>
  <p>Next, <strong>Choose a control type</strong>:</p>
  <table>
    <tr><th>Control</th><th>What it does</th><th>Typical point</th></tr>
    <tr><td>Readout</td><td>Shows the live value. Never writes.</td><td>Supply temperature, status, pressure.</td></tr>
    <tr><td>Setpoint</td><td>Minus / value / plus; tap the value to type one.</td><td>Zone setpoint, damper minimum, any analog you adjust.</td></tr>
    <tr><td>Toggle</td><td>Flips between an on and an off value.</td><td>Fan enable, occupancy override, pump command.</td></tr>
    <tr><td>Button</td><td>Sends one fixed value when pressed (with a confirmation).</td><td>A reset, a &ldquo;go to 100%&rdquo;.</td></tr>
    <tr><td>Multi-state</td><td>Pick one of several named states.</td><td>Fan speed Off/Low/High, operating mode.</td></tr>
    <tr><td>Release</td><td>Hands the point back to automatic at your priority.</td><td>Put one next to every control that writes.</td></tr>
  </table>
  <p>The new control lands in the first free slot, labelled with the point name. (The
  status-light <em>Indicator</em> is available on single-device custom remotes; on a panel, use
  a Readout for an input.)</p>

  <h2>Step 4 &mdash; Set the grid width and arrange</h2>
  <p>Menu &rarr; <strong>Grid width</strong> sets the panel from <strong>2 to 6 columns</strong>
  (new panels start at 4). Wider fits more small readouts per row; narrower gives bigger
  controls. Controls are refitted to the new width automatically. In Edit mode <strong>press and
  drag</strong> a control to move it; it snaps to the grid and will not land on another
  control. The hint at the top reminds you: <em>Nothing is sent to any device while
  editing.</em></p>

  <h2>Step 5 &mdash; Configure each control</h2>
  <p><strong>Tap</strong> a control to open its options: <strong>Rename control</strong>,
  <strong>Width</strong>, <strong>Write priority</strong> (1&ndash;16, default 8),
  <strong>Step size</strong> for a setpoint, <strong>Value to send</strong> for a button,
  <strong>State names</strong> for a multi-state (one per line, first line = state 1),
  <strong>Change device</strong> when the panel has several devices, <strong>Colour</strong>,
  <strong>Card style</strong>, <strong>Toggle large value text</strong>, or <strong>Delete
  control</strong>. Everything saves as you go; there is no Save button. The same Edit-mode
  menu has <strong>Rename panel</strong> and <strong>Delete panel</strong> (which cannot be
  undone).</p>

  <h2>Step 6 &mdash; Use it</h2>
  <p>Tap <strong>Done</strong>. The panel reads every control once and shows
  <strong>Online</strong>, <strong>Some points not answering</strong> or <strong>No response
  from device</strong> at the top; <strong>Refresh</strong> reads them again. Controls that
  write need <strong>Write mode</strong> turned on from the menu on the main screen, exactly as
  the point screen does; until then the panel is read-only. A toggle will not act until it has
  read the point's current state, so it can never guess. Opening a saved panel later talks to
  each device at its last known address, so no scan is needed unless a device has moved.</p>

  <h2>Sharing panels: export and import</h2>
  <ul>
    <li><strong>Export:</strong> on the <strong>Control Panels</strong> list,
    <strong>long-press</strong> a panel. Android's save dialog opens with
    <code>Panel&nbsp;name.ebpanel</code>; save it and send it like any file.</li>
    <li><strong>Import:</strong> menu &rarr; <strong>Import panel</strong>, then choose the
    file. An imported panel is always added as a new panel; it never overwrites one you have.
    A single-device remote file (<code>.ebremote</code>) belongs in Custom Remotes instead.</li>
  </ul>

  <h2>Free vs Easy BACnet Pro</h2>
  <p>The free version keeps <strong>one</strong> control panel, driving its primary device only;
  trying to add a second device shows <em>Multiple devices is a Pro feature</em>, and a second
  panel shows <em>One panel on the free version</em>. Importing a multi-device panel on the free
  version keeps the layout but points every control at the primary device. Opening a panel never
  needs an ad. Easy BACnet Pro &mdash; the same $9.99-a-year subscription that removes ads and
  lifts the remotes limit &mdash; allows unlimited panels with up to 32 devices each. If the
  subscription ends, your panels are kept as they are, but the free limits apply again.</p>

  <h2>Tips from the field</h2>
  <ul>
    <li><strong>Colour what acts.</strong> Make the control that stops a pump red and
    leave readouts plain, so the controls that change something are obvious at a glance.</li>
    <li><strong>One Release per writer.</strong> Anything you can command you should be able to
    hand back. A release button next to each setpoint or toggle keeps a temporary override from
    becoming a permanent one &mdash; see
    <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck overrides</a>.</li>
    <li><strong>Label by location, not by tag.</strong> &ldquo;Boiler 2 enable&rdquo; beats
    &ldquo;BO-3&rdquo; when the panel spans six devices with overlapping point names.</li>
    <li><strong>Duplicate Device IDs break panels.</strong> A panel follows each device by its
    ID (and remembers its IP). If two controllers share an ID, fix that first &mdash; see
    <a href="duplicate-bacnet-device-id.html">duplicate BACnet device IDs</a>.</li>
  </ul>
""",
    related=[
        ("guides/how-to-build-a-custom-remote", "How do I build a custom remote in Easy BACnet?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/bacnet-add-device-by-ip", "Add a BACnet device by IP address"),
        ("guides/duplicate-bacnet-device-id", "Two devices have the same BACnet Device ID"),
    ],
))

GUIDES.append(dict(
    slug="guides/cant-find-what-im-looking-for",
    title="The app can't find what I'm looking for | Easy BACnet",
    question="The app can't find what I'm looking for \u2014 what do I do?",
    description="A plain-English checklist for when a scan finds nothing, finds the wrong things, shows a device with no points, or a point with no value.",
    answer_html="""<p>Usually the phone is not on the same network as the equipment.
    When a scan finds nothing, the app shows the phone's IP address and subnet mask:
    if the first three numbers do not match the controllers' addresses, join the
    building's controls Wi-Fi or plug in with a USB-Ethernet adapter and scan again.
    If the addresses do match, or the problem is a missing device, an empty point
    list or a blank value, find the matching section below.</p>""",
    body_html="""
  <h2>The scan finds nothing at all</h2>
  <p>You tapped <strong>Scan for Devices</strong> and got the red <em>No devices
  found</em> banner. Work down this list; each step is cheaper than the next.</p>
  <ol>
    <li><strong>Compare addresses.</strong> Under the banner the app lists the
    phone's IP address and mask. Find a controller's address on its label, in its
    front-panel menu, or in the hand-over documents. With a 255.255.255.0 mask the
    first three numbers must match (phone 192.168.1.20, controller 192.168.1.50).
    If they do not, nothing else matters until you are on the right network.</li>
    <li><strong>Get on the right network.</strong> Building controls are almost
    always on their own network or VLAN, not the office or guest Wi-Fi. Ask whoever
    runs the site which network the controllers are on and how to join it. If there
    is no Wi-Fi in the plant room, plug a USB-Ethernet adapter into the phone and
    run a cable to the same switch the controllers use.</li>
    <li><strong>Turn mobile data off</strong> if the status bar says <em>Connected,
    no internet</em>, then scan again.</li>
    <li><strong>Scan once more.</strong> Wi-Fi drops the broadcast a scan relies
    on. The app repeats it through the scan and then tries each address on the
    subnet directly, but a second run sometimes catches what the first missed. A
    wired connection removes this problem entirely.</li>
    <li><strong>Add the device by IP.</strong> If you know a controller's address,
    menu &rarr; <strong>Add device by IP&hellip;</strong> contacts it directly without
    a broadcast. If that works when a scan does not, the device is fine and the
    network is blocking broadcasts: you are on another segment, or the Wi-Fi has
    client isolation on. Ask the network team for a port on the controls VLAN, or
    for the site's BBMD address (menu &rarr; <strong>BBMD for remote
    networks&hellip;</strong>).</li>
    <li><strong>Ping it.</strong> If even a directed add fails, ping the address from
    a laptop on the same network. No reply means the network path is the problem; a
    reply with no BACnet answer means the device is up but BACnet is blocked or
    misconfigured. <a href="is-my-bacnet-device-online-ping-test.html">Is my BACnet
    device online?</a> walks through what each result means.</li>
  </ol>
  <p>For the longer technical version, see
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet
  devices?</a></p>

  <h2>It finds some devices, but not the one I want</h2>
  <ul>
    <li><strong>Look at the Device ID, not just the name.</strong> Every device shows
    its ID and IP address under the name. The unit you want may have a blank or
    unhelpful name and the right ID.</li>
    <li><strong>Check it is powered and plugged in.</strong> A controller with a dead
    link light cannot answer.</li>
    <li><strong>It may be on another segment.</strong> Devices near you answered;
    this one is behind a router. Add it by IP, plug into its switch, or use a BBMD.</li>
    <li><strong>It may be an MS/TP device whose router is not forwarding.</strong>
    Those devices appear only through a BACnet router. If the whole trunk is
    missing, that is a controls question. See
    <a href="does-easy-bacnet-support-mstp-rs485.html">does Easy BACnet support MS/TP?</a></li>
    <li><strong>Two devices may share an ID.</strong> The scan summary warns about
    duplicates; one of the pair can appear to vanish. See
    <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</li>
  </ul>

  <h2>I opened a device but it shows no points</h2>
  <ul>
    <li><strong>Give it a minute.</strong> The app reads one object at a time, so a
    large controller takes a while. Watch the <em>Loading points</em> counter.</li>
    <li><strong>Back out and open it again.</strong> One dropped reply can stall the
    list; reopening starts fresh.</li>
    <li><strong>Small devices have few points.</strong> A sensor may expose one or
    two. That is the device, not a fault.</li>
    <li><strong>A huge controller shows only part of its list.</strong> The app
    loads the first 2,000 objects and says so. Reach the rest with menu &rarr;
    <strong>Add object by number</strong>
    (<a href="bacnet-add-object-by-number.html">how</a>).</li>
  </ul>

  <h2>I see a point but no value</h2>
  <ul>
    <li><strong>Tap Refresh.</strong> Values are read live; one missed reply shows a
    dash until the next read.</li>
    <li><strong>If every point on the device shows dashes</strong>, it has stopped
    answering. Scan again to confirm it is still there.</li>
    <li><strong>Some points have no present value.</strong> Schedules, notification
    classes and similar objects are settings, not readings.</li>
  </ul>

  <h2>Who to call</h2>
  <p>In short: if you cannot reach the equipment on the network, call
  <strong>IT / network</strong> and have the phone's IP and mask ready. If you can
  reach it but the points, IDs or values are wrong, call the <strong>controls /
  BMS</strong> contractor and send them the exported spreadsheet. If the point
  reads correctly but the machine is not doing what it says, call the
  <strong>HVAC / mechanical</strong> contractor. The full breakdown, with what to
  have ready for each, is in <a href="who-to-call-it-hvac-or-controls.html">who do I
  call &mdash; IT, HVAC, or controls/BMS?</a></p>
""",
    related=[
        ("guides/is-my-bacnet-device-online-ping-test", "Is my BACnet device actually online? Ping it first"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/bacnet-device-id-explained", "BACnet Device IDs explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/is-my-bacnet-device-online-ping-test",
    title="Is my BACnet device online? Ping test | Easy BACnet",
    question="How do I tell if a BACnet device is really online before blaming the app?",
    description="A hands-on test that separates a network problem from a BACnet problem: find the device IP, ping it, then try a directed read, and what each result means.",
    answer_html="""<p>Two tests settle it. First, in Easy BACnet, use <strong>Add device
    by IP&hellip;</strong> with the controller's address: that contacts it directly, with
    no broadcast involved, and if it answers the device is online and your scan is being
    blocked by the network. If it does not answer, <strong>ping</strong> the address
    from a laptop on the same network. A failed ping means the network path is broken
    (wrong subnet, firewall, cable, wrong IP). A successful ping with no BACnet answer
    means the device is up but BACnet is blocked or misconfigured: the wrong port, a
    firewall that allows ping but not UDP 47808, or a device problem.</p>""",
    body_html="""
  <h2>Why test this way</h2>
  <p>A scan can fail for many reasons, and most of them have nothing to do with the
  device. These two tests separate the possibilities. A directed BACnet read proves
  the device is alive and speaking BACnet. A ping proves only that packets can reach
  the address. Running them in that order tells you whether you are dealing with a
  broadcast problem, a network problem, or a BACnet configuration problem, and
  therefore who to call.</p>

  <h2>Step 1 &mdash; find the device's IP address</h2>
  <p>If the device has ever appeared in a scan, its IP is shown under its name. If
  not, look on the controller's label, its front-panel display, or the commissioning
  sheet; ask the controls contractor; or ask the network team to read it from the
  switch's DHCP or ARP table.</p>

  <h2>Step 2 &mdash; add it by IP in the app</h2>
  <p>In Easy BACnet Mode, menu (three dots) &rarr; <strong>Add device by IP&hellip;</strong>,
  type the address and port (47808 unless the site uses another) and tap
  <strong>Add</strong>. The app sends a directed Who-Is and a direct read.</p>
  <ul>
    <li><strong>It answers.</strong> The device is online and speaking BACnet. Your
    scan failed because the broadcast is not reaching it: you are on another subnet,
    the Wi-Fi has client isolation on, or a switch filters broadcasts. For the whole
    remote network you need the site's <a href="what-is-a-bbmd.html">BBMD</a>; for this
    one device, you are done.</li>
    <li><strong>It does not answer</strong> (<em>No BACnet IP device answered
    at&hellip;</em>). Go to step 3.</li>
  </ul>

  <h2>Step 3 &mdash; ping it</h2>
  <p>Ping from a device on the same network as the controller; a laptop plugged into
  the controls switch is ideal. Open a command prompt and type <code>ping</code> and
  the address, for example <code>ping 10.20.30.41</code>. A ping app on the phone does
  the same job. You want replies, not &ldquo;request timed out&rdquo; or
  &ldquo;destination unreachable&rdquo;.</p>

  <h3>The ping fails</h3>
  <p>The device cannot be reached on the network, so no BACnet tool will see it until
  that is fixed. Causes, most likely first:</p>
  <ul>
    <li>You are on a <a href="subnets.html">different subnet</a> with no route to it.
    Get onto the controls network and try again.</li>
    <li>The IP is wrong, or the device moved to a new DHCP address.</li>
    <li>A cable is unplugged, a switch port is dead, or the unit is powered down.</li>
    <li>A firewall or VLAN access list blocks the path. Some block ping on purpose while
    allowing everything else, so a failed ping on a managed network is not final proof.</li>
  </ul>
  <p>This is an <strong>IT / network</strong> conversation, unless you can see the device
  itself is unpowered.</p>

  <h3>The ping succeeds, but step 2 failed</h3>
  <p>The device is on the network but not answering BACnet at that address and port.
  Possible reasons:</p>
  <ul>
    <li><strong>Wrong UDP port.</strong> Sites running several BACnet networks on one
    wire use 47809 and up. Ping ignores ports; BACnet does not. Try the add again with
    the right port. See <a href="what-port-does-bacnet-use.html">what port does BACnet
    use?</a></li>
    <li><strong>A firewall allows ping but blocks UDP 47808.</strong> They are separate
    rules and it is common to have one without the other. Network team.</li>
    <li><strong>The address belongs to a router, not the device.</strong> An MS/TP
    controller has no IP of its own; the IP you have may be its router, which answers
    ping but only forwards BACnet for trunks that are configured. See
    <a href="does-easy-bacnet-support-mstp-rs485.html">does Easy BACnet support MS/TP?</a></li>
    <li><strong>BACnet is disabled or misconfigured on the device</strong>, or it shares
    a <a href="duplicate-bacnet-device-id.html">Device ID</a> with another unit.
    Controls contractor.</li>
  </ul>

  <h3>Both work, but the device shows no points or no values</h3>
  <p>Communication is fine. The device is slow to enumerate, refusing some property
  reads, or has very little to show. See
  <a href="cant-find-what-im-looking-for.html">the app can't find what I'm looking
  for</a>.</p>

  <h2>What to tell whoever you call</h2>
  <p>One sentence with both results saves a lot of back-and-forth:
  <em>&ldquo;10.20.30.41 pings from a laptop on the controls switch, but a directed
  BACnet read on port 47808 gets no answer.&rdquo;</em> That rules out the cable, the
  power and the network path, and points at the port, a firewall rule, or the
  device's BACnet settings.</p>
""",
    related=[
        ("guides/cant-find-what-im-looking-for", "The app can&rsquo;t find what I&rsquo;m looking for"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/bacnet-device-shows-offline", "Why does my BACnet IP device show offline?"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-vs-modbus",
    title="BACnet vs Modbus: the difference | Easy BACnet",
    question="BACnet vs Modbus — what is the difference?",
    description="BACnet is self-describing with built-in discovery; Modbus is a bare register protocol with neither. When you meet each, and why it matters.",
    answer_html="""<p>Both move data to and from building and industrial equipment, but
    they work at different levels. <strong>BACnet</strong> is object-oriented and
    self-describing: every device announces itself, and every point carries a type, a
    name and units. <strong>Modbus</strong> is a thin, fast register protocol: it hands
    you numbered slots and nothing else &mdash; no discovery, no names, no units. As a
    rule of thumb, BACnet runs the HVAC and building-management side; Modbus runs meters,
    variable-speed drives, PLCs and simple sensors.</p>""",
    body_html="""
  <h2>Discovery: ask the network vs sweep it</h2>
  <p>BACnet has discovery built in. A device broadcasts a
  <a href="who-is-i-am-explained.html">Who-Is</a> and every controller answers with an
  I-Am, so a tool can build a device list in seconds without being told what is out
  there. Modbus has nothing of the kind: you must already know a device's IP address
  and unit ID, or sweep the subnet address by address to find it.</p>

  <h2>Meaning: named points vs bare registers</h2>
  <p>A BACnet point is an object such as <code>Analog Input 3</code> that carries an
  <code>Object_Name</code>, a <code>Present_Value</code>, engineering units and status
  flags &mdash; the device tells you what the number means. A Modbus register is just
  address 40007 holding the number 685; whether that is 68.5&nbsp;&deg;F, 685&nbsp;kPa
  or two packed bytes is something you work out yourself from the vendor's map.</p>

  <h2>Addressing</h2>
  <table>
    <tr><th></th><th>BACnet</th><th>Modbus</th></tr>
    <tr><td>Identity</td><td>Device Instance (unique network-wide)</td><td>IP + Unit/Slave ID</td></tr>
    <tr><td>A point</td><td>Object type + instance (e.g. AI 3)</td><td>Register number + type</td></tr>
    <tr><td>Self-describing</td><td>Yes &mdash; name, units, status</td><td>No &mdash; just a number</td></tr>
    <tr><td>Discovery</td><td>Who-Is / I-Am</td><td>None</td></tr>
  </table>

  <h2>Where you meet each</h2>
  <p>BACnet dominates air handlers, VAV boxes, chillers, and the building-management
  head-end. Modbus dominates power and BTU meters, VFDs, generators, and OEM skids. Many
  buildings run both, bridged by a gateway that presents Modbus registers as BACnet
  objects (or the reverse).</p>

  <h2>Which app do I use?</h2>
  <p>Use <a href="../index.html">Easy BACnet</a> for BACnet/IP equipment. For Modbus gear
  there is a sister app, <a href="https://easymodbus.com">Easy Modbus</a>, built the same
  way &mdash; and its own write-up of
  <a href="https://easymodbus.com/guides/modbus-vs-bacnet.html">Modbus vs BACnet</a> covers
  the same ground from the Modbus side.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/who-is-i-am-explained",
    title="BACnet Who-Is and I-Am explained | Easy BACnet",
    question="What are BACnet Who-Is and I-Am?",
    description="Who-Is is a broadcast asking which devices exist; each replies I-Am with its instance, vendor and capabilities. How BACnet IP discovery works.",
    answer_html="""<p><strong>Who-Is</strong> and <strong>I-Am</strong> are the two
    messages behind BACnet IP discovery. A tool broadcasts a <em>Who-Is</em> meaning
    &ldquo;who is out there?&rdquo;, and every device that hears it answers with an
    <em>I-Am</em> carrying its Device Instance number, the vendor, and what it can do.
    Collect the replies and you have a device list. That is what Easy BACnet does
    when you tap Scan.</p>""",
    body_html="""
  <h2>The exchange</h2>
  <p>A Who-Is is normally sent to the local broadcast address, so it reaches every device
  on the subnet at once. Each device replies with an I-Am. A Who-Is can be
  <em>unconstrained</em> (everybody answer) or <em>constrained</em> to a range of Device
  Instances, which is how a tool asks only for device 200001 without hearing from the
  whole building.</p>

  <h2>What an I-Am carries</h2>
  <ul>
    <li><strong>Device Instance</strong> &mdash; the device's unique number on the whole
    BACnet internetwork. If two devices share one, discovery gets unreliable: see
    <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a>.</li>
    <li><strong>Max APDU length</strong> and <strong>segmentation support</strong> &mdash;
    how big a message the device can handle, which decides how points are read.</li>
    <li><strong>Vendor ID</strong> &mdash; who made it.</li>
  </ul>

  <h2>Why a scan sometimes finds nothing</h2>
  <p>Because Who-Is is a broadcast, and routers do not forward broadcasts, a device on a
  different IP subnet never hears it &mdash; unless a
  <a href="what-is-a-bbmd.html">BBMD</a> bridges the two. That is the usual reason a
  scan comes back empty: see
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP devices?</a>.
  Devices on a serial <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> trunk answer too,
  as long as a router carries the traffic onto IP.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
        ("guides/bacnet-device-id-explained", "BACnet Device IDs explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/what-is-a-bbmd",
    title="What is a BBMD in BACnet? | Easy BACnet",
    question="What is a BBMD, and when do I need one?",
    description="A BBMD forwards BACnet/IP broadcasts across subnets, because routers do not. Without one, equipment on another subnet cannot be discovered.",
    answer_html="""<p>A <strong>BBMD</strong> &mdash; BACnet Broadcast Management Device
    &mdash; forwards BACnet/IP broadcasts from one IP subnet to another. BACnet IP discovery
    leans on broadcasts, and IP routers deliberately do not pass broadcasts, so equipment
    on a different subnet is invisible until a BBMD carries the broadcast across. You need
    one whenever BACnet/IP has to span more than a single subnet.</p>""",
    body_html="""
  <h2>Why broadcasts are the problem</h2>
  <p>A <a href="who-is-i-am-explained.html">Who-Is</a> is a broadcast: it reaches every
  device on the local subnet in one shot. That is efficient, but a router's whole job is
  to <em>not</em> forward broadcasts, or they would flood the network. So the moment your
  equipment sits on a different subnet from the tool looking for it, discovery stops at
  the router.</p>

  <h2>What a BBMD does</h2>
  <p>One BBMD sits on each subnet that has BACnet/IP devices. The BBMDs know about each
  other through a <strong>Broadcast Distribution Table</strong>. When a broadcast arrives
  on one subnet, its BBMD wraps it up and unicasts it to the other BBMDs, which re-broadcast
  it locally. The result is that a Who-Is sent on subnet A is heard by devices on subnet
  B, without opening the routers to general broadcast traffic.</p>

  <h2>Foreign Device Registration</h2>
  <p>A tool that is not on any BACnet subnet &mdash; a laptop or phone on office Wi-Fi,
  say &mdash; can ask a BBMD to include it as a <strong>foreign device</strong>. The BBMD
  then forwards broadcasts to it directly for a time. It is the standard way a piece of
  software reaches equipment it is not physically alongside.</p>

  <h2>What this means for a phone scan</h2>
  <p>Easy BACnet scans the subnet the phone is on. If the equipment is elsewhere and there
  is no BBMD reaching your phone, the scan finds nothing &mdash; not because the app failed,
  but because the broadcast never crossed the router. The reliable fix on site is to get
  the phone onto the <strong>same subnet</strong> as the controllers; see
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP devices?</a>.</p>

  <h2>Scanning through a BBMD with Easy BACnet</h2>
  <p>If the site has a BBMD and your phone can reach it, Easy BACnet can register with it as a
  foreign device:</p>
  <ol>
    <li>In <strong>Easy BACnet Mode</strong>, open the menu (three dots) &rarr; <strong>BBMD for
    remote networks&hellip;</strong>.</li>
    <li>Enter the <strong>BBMD IP address</strong> and its UDP port (47808 is standard), then tap
    <strong>Save</strong>. The app confirms <em>Scans will now also go through the BBMD at
    &hellip;</em> and remembers the address.</li>
    <li>Tap <strong>Scan for Devices</strong>. Each scan registers the phone with the BBMD and
    sends its Who-Is through it, as well as on the local subnet.</li>
  </ol>
  <p>If the BBMD rejects the registration you will see a warning with its result code &mdash;
  ask whoever manages it to allow foreign-device registration. If it does not answer, the scan
  covered the local network only. Tap <strong>Clear</strong> in the same dialog to stop using
  it. For a single known controller, <a href="bacnet-add-device-by-ip.html">add it by IP</a>
  instead.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/what-port-does-bacnet-use", "What port does BACnet IP use?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-mstp-vs-bacnet-ip",
    title="BACnet MS/TP vs BACnet/IP | Easy BACnet",
    question="BACnet MS/TP vs BACnet/IP — what is the difference?",
    description="BACnet/IP runs over Ethernet and Wi-Fi on UDP 47808; MS/TP runs over an RS-485 serial pair. How they differ and how a router joins them.",
    answer_html="""<p><strong>BACnet/IP</strong> carries BACnet over ordinary Ethernet and
    Wi-Fi networks using <a href="what-port-does-bacnet-use.html">UDP&nbsp;47808</a>.
    <strong>BACnet MS/TP</strong> (Master-Slave/Token-Passing) carries it over a cheap
    RS-485 serial twisted pair. IP is fast and everywhere; MS/TP is slow and inexpensive,
    which is why most individual field controllers are MS/TP and reach the wider network
    through a BACnet router.</p>""",
    body_html="""
  <h2>Different wires, same BACnet</h2>
  <p>The objects, the points and the services are identical; only the bottom layer differs.
  BACnet/IP rides on the building's data network. MS/TP rides on a two- or three-wire
  RS-485 bus daisy-chained from controller to controller, typically at 9600 to 115200 baud
  &mdash; a fraction of Ethernet speed, but enough for a VAV box reporting a temperature.</p>

  <h2>Token passing</h2>
  <p>MS/TP devices share one wire, so they take turns: a token is passed from master to
  master, and only the holder may speak. It is robust and cheap, but it puts a ceiling on
  how fast a trunk can be polled &mdash; part of why reading a large MS/TP unit is not
  instant.</p>

  <h2>Addressing and how they meet</h2>
  <p>On MS/TP a device has a small <strong>MAC address</strong> (0&ndash;127) on its
  trunk, plus a <strong>network number</strong> for that trunk. A <strong>BACnet
  router</strong> joins the MS/TP trunk to BACnet/IP, so from the IP side each MS/TP
  device appears as a normal BACnet IP device with its Device Instance. That routing is why
  Easy BACnet, which speaks BACnet/IP over Wi-Fi, can still list and read MS/TP
  controllers &mdash; provided a router is carrying them onto the subnet your phone is on.</p>

  <h2>Which am I looking at?</h2>
  <p>If a device shows a network number greater than the local one and a low MAC address,
  it is almost certainly an MS/TP device reached through a router. Pure BACnet/IP devices
  sit on the IP network directly with their own IP address.</p>
""",
    related=[
        ("guides/does-easy-bacnet-support-mstp-rs485", "Does Easy BACnet support MS/TP or RS-485?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/what-port-does-bacnet-use", "What port does BACnet IP use?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/what-port-does-bacnet-use",
    title="BACnet Port: UDP 47808 (0xBAC0), the Default BACnet IP Port",
    question="What port does BACnet IP use?",
    description="The default BACnet port is UDP 47808 (0xBAC0). Why it is UDP, not TCP, when sites use 47809 and up, what to open in a firewall, and how to check a device answers.",
    answer_html="""<p>BACnet/IP uses <strong>UDP port 47808</strong> by default &mdash; that
    is <code>0xBAC0</code> in hex, which is where the number comes from. It is UDP, not TCP,
    and discovery relies on broadcasts to that port. Where a single IP subnet carries more
    than one BACnet IP network, the extra networks use <strong>47809</strong> and up.</p>""",
    body_html="""
  <h2>47808, and why</h2>
  <p>The default port is 47808 decimal, chosen because in hexadecimal it reads
  <code>0xBAC0</code> &mdash; &ldquo;BAC0&rdquo;, for BACnet. It is a UDP port: BACnet/IP
  sends connectionless datagrams, and a <a href="who-is-i-am-explained.html">Who-Is</a>
  goes out as a broadcast to that port so every device on the subnet hears it.</p>

  <h2>When it is not 47808</h2>
  <p>One IP subnet can host several separate BACnet networks by giving each its own port,
  starting at 47808 and counting up: 47809, 47810, and so on (up to 47823 is common). If a
  building was set up that way, a tool must check each port, because devices on 47809 never
  answer a broadcast sent to 47808. Easy BACnet checks the common range for you.</p>

  <h2>Firewalls and MS/TP</h2>
  <p>If a software firewall or a locked-down switch is dropping UDP 47808, discovery fails
  even on the right subnet; ask whoever runs the network to check. Note
  that <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> devices have no IP port at all;
  they live on a serial trunk and reach IP only through a BACnet router. And because the
  port carries broadcasts, it will not cross a router to another subnet without a
  <a href="what-is-a-bbmd.html">BBMD</a>.</p>
""",
    related=[
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
        ("guides/bacnet-mstp-vs-bacnet-ip", "BACnet MS/TP vs BACnet/IP"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-scanner-app-android",
    title="BACnet IP scanner app for Android | Easy BACnet",
    question="Is there a BACnet IP scanner app for Android?",
    description="Yes. How to discover, read and command BACnet/IP devices from an Android phone, what a phone can and cannot reach, and the subnet and MS/TP catches.",
    answer_html="""<p>Yes &mdash; <a href="../index.html">Easy BACnet</a> is an
    Android app that broadcasts a BACnet <em>Who-Is</em>, lists every BACnet/IP
    device that answers, reads each one's points, and &mdash; with safety rails
    &mdash; writes to them at a chosen priority. Unlike Modbus, BACnet has real
    discovery built in, so a phone on the same network as the controllers will find
    them in seconds. The one thing to get right first is the network: a phone can
    only find what its Wi-Fi connection can actually reach.</p>""",
    body_html="""
  <h2>Why a phone is the right tool here</h2>
  <p>BACnet controllers live in plant rooms, ceilings and rooftop units. When all
  you need is to confirm a device is alive, read a sensor, or release a stuck
  override, getting a laptop onto the control network is most of the work. A phone
  already on the building network does the same job and fits in a pocket &mdash;
  which is the difference between checking a point on the spot and booking a return
  visit.</p>

  <h2>How discovery works &mdash; and why it sometimes finds nothing</h2>
  <p>Easy BACnet sends a <em>Who-Is</em> broadcast and collects the <em>I-Am</em>
  replies. That broadcast only travels across the local subnet, so the usual reason
  a scan comes back empty is that the phone is on the wrong network: guest Wi-Fi, a
  separate controls VLAN, or a switch port that hands out an address in the wrong
  range. See <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find
  my BACnet IP devices?</a> and <a href="subnets.html">what is a subnet, and why doesn't
  the switch give me the right one?</a></p>

  <h2>What a phone can and cannot reach</h2>
  <table>
    <tr><th>Situation</th><th>Works from the phone?</th></tr>
    <tr><td>BACnet/IP devices on the same subnet as the phone</td><td>Yes &mdash; the normal case, found by <em>Who-Is</em></td></tr>
    <tr><td>A specific device you can reach by IP but not by broadcast</td><td>Yes &mdash; add it directly by IP address</td></tr>
    <tr><td>MS/TP devices on a serial trunk behind a BACnet router</td><td>Yes, if the router advertises them onto IP &mdash; you reach them through it, not directly. See <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP vs BACnet/IP</a></td></tr>
    <tr><td>Devices on another subnet, through the site's BBMD</td><td>Yes &mdash; enter the <a href="what-is-a-bbmd.html">BBMD</a> address and the app registers as a foreign device</td></tr>
    <tr><td>Devices on another subnet, with no BBMD</td><td>Only one at a time, by IP &mdash; broadcasts don't cross a router</td></tr>
  </table>
  <p>The limits: Easy BACnet speaks <strong>BACnet IP</strong> only. It reaches MS/TP
  devices through a router that publishes them, not by plugging into a serial trunk.
  A device on a different subnet needs either a direct
  <a href="bacnet-add-device-by-ip.html">add by IP</a> or the site's BBMD, which the app
  can register with (menu &rarr; <em>BBMD for remote networks</em>).</p>

  <h2>Reading is safe; writing has rails</h2>
  <p>Discovering and reading changes nothing &mdash; a phone is a perfectly safe way
  to look around a live system. Writing is where BACnet is genuinely careful, and so
  is the app: write mode is off every time you launch, each command goes out at a
  priority you choose, the priority array is read back so you can see what won, and
  a one-tap <em>release to auto</em> hands control back. If you have ever left an
  override in a controller by accident, that matters &mdash; see
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a> and <a href="how-to-write-to-a-bacnet-point.html">how to write to a
  BACnet point</a>.</p>

  <h2>What you walk away with</h2>
  <p>Every device, point, present value, unit and status the scan finds can be
  exported as an Excel spreadsheet &mdash; so a phone standing in a plant room turns a system nobody
  had documented into a list somebody can use. Walk through a full scan in
  <a href="how-to-use-easy-bacnet.html">how to use Easy BACnet</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/subnets", "What is a subnet, and why doesn't the switch give me the right one?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
        ("guides/best-free-bacnet-explorer", "What is the best free BACnet explorer tool?"),
        ("guides/what-is-bacnet", "What is BACnet?"),
    ],
))

GUIDES.append(dict(
    slug="guides/read-bacnet-values-from-phone",
    title="How to read BACnet values from a phone | Easy BACnet",
    question="How do I read BACnet values from a phone?",
    description="Step by step: join the controls network, discover BACnet IP devices, then open a point and read its live value, units and status on an Android phone.",
    answer_html="""<p>Join your phone to the same network as the controls, open
    <a href="../index.html">Easy BACnet</a>, tap <strong>Scan for Devices</strong>,
    open the device you want and then the point you want, and its live
    <strong>Present Value</strong>, <strong>Units</strong> and <strong>Status</strong>
    are right there, with a <strong>Refresh</strong> button for a fresh read.
    Reading changes nothing on the equipment, so this is completely safe to do on a
    live system. The whole thing takes under a minute once the phone is on the right
    network &mdash; which is the one part worth getting right first.</p>""",
    body_html="""
  <h2>What you need</h2>
  <ul>
    <li><strong>Your phone on the controls network.</strong> Join the building's
    controls Wi-Fi, or plug into the network with a USB-Ethernet adapter. A phone on
    guest Wi-Fi or mobile data reaches nothing &mdash; and that is the network, not
    the app. See <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my
    BACnet IP devices?</a> and <a href="subnets.html">the subnet guide</a> if the scan
    is empty.</li>
    <li><strong>No password.</strong> BACnet has no login. If you are on the network,
    the devices answer.</li>
  </ul>

  <h2>Step 1 &mdash; Scan for devices</h2>
  <p>Open the app, tap the <strong>Easy BACnet Mode</strong> card, then <strong>Scan for
  Devices</strong>. The app broadcasts a BACnet <em>Who-Is</em> and collects the
  replies, then reads each device's name &mdash; up to a minute in all. Access points drop
  broadcasts, so it keeps asking rather than trusting one shot. A counter shows devices as
  they answer.</p>
  <figure class="shot">
    <img src="../img/scan.png" alt="Easy BACnet scanning a network and listing the BACnet IP devices that answered" loading="lazy">
    <figcaption>A scan in progress &mdash; devices appear as they answer the Who-Is.</figcaption>
  </figure>

  <h2>Step 2 &mdash; Open the device</h2>
  <p>Tap <strong>View Results</strong>. Each device shows its name, Device ID and IP
  address. Tap the one you want and the app reads its object list. On a large
  controller this takes a moment; it reads one object at a time so that it works
  with older and cheaper controllers too.</p>
  <figure class="shot">
    <img src="../img/devices.png" alt="A list of discovered BACnet IP devices with names, Device IDs and IP addresses" loading="lazy">
    <figcaption>Discovered devices, each with its name, Device ID and IP.</figcaption>
  </figure>

  <h2>Step 3 &mdash; Find the point</h2>
  <p>The device opens to its list of points &mdash; analog inputs, binary values,
  setpoints and the rest. Names come from the controller's own
  <em>Object_Name</em>, so a well-commissioned device reads like plain English and a
  poorly-commissioned one reads like <code>AI-3</code>. If you already know the object you
  want on a big controller, menu &rarr; <strong>Add object by number</strong> reads it
  directly. Not sure what the object types mean? See
  <a href="bacnet-object-types-explained.html">BACnet object types explained</a>.</p>
  <figure class="shot">
    <img src="../img/points.png" alt="The point list for a BACnet IP device showing analog and binary objects with live values" loading="lazy">
    <figcaption>A device's points, each showing its live value.</figcaption>
  </figure>

  <h2>Step 4 &mdash; Read the value</h2>
  <p>Tap the point. You get its live <strong>Present Value</strong>, the
  <strong>Units</strong> the controller reports, the <strong>Status</strong> flags
  (in alarm, in fault, overridden, out of service) and the
  <strong>Description</strong> if the device carries one. <strong>Refresh</strong>
  reads it again on demand.</p>
  <figure class="shot">
    <img src="../img/point.png" alt="A single BACnet point showing present value, units, status flags and description" loading="lazy">
    <figcaption>One point: present value, units, status, and whether anything is overriding it.</figcaption>
  </figure>
  <div class="callout">
  <p>On a commandable point you also see <strong>Commanded At</strong> and
  <strong>Falls Back To</strong>: whether something is currently overriding
  the point, at what priority, and what it will do when released. See
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>
  </div>

  <h2>Reading is safe; writing is separate</h2>
  <p>Everything above only reads &mdash; it cannot change a thing on the equipment,
  so a phone is a perfectly safe way to look around a live building. Changing a value
  is a deliberate, separate mode that is off every time you launch the app. When you
  do need it, see <a href="how-to-write-to-a-bacnet-point.html">how to write to a
  BACnet point</a>.</p>

  <h2>Turning a quick read into a record</h2>
  <p>If you need more than one value, skip tapping through points one by one:
  <strong>Export Results</strong> reads every point on every device and hands you an
  Excel spreadsheet to email or save &mdash; names, present values, units and status. A five-minute scan in
  a plant room turns an undocumented building into a points list somebody can use.
  The full walkthrough is in <a href="how-to-use-easy-bacnet.html">how to use Easy
  BACnet</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/bacnet-scanner-app-android", "Is there a BACnet IP scanner app for Android?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-device-shows-offline",
    title="BACnet IP device shows offline? Causes & fixes | Easy BACnet",
    question="Why does my BACnet IP device show offline?",
    description="A BACnet IP device showing offline is usually a network problem, not dead hardware: wrong subnet, dropped broadcasts, a firewall, or a duplicate ID.",
    answer_html="""<p>&ldquo;Offline&rdquo; in BACnet means <em>I stopped hearing from
    it</em>, which is usually a network problem rather than dead hardware. In order
    of likelihood: your phone is on a different subnet so the broadcast never reaches
    the device, the Wi-Fi is dropping broadcasts, a firewall or access list is blocking
    UDP 47808, two devices share a Device ID, or the device really has lost power or
    its network link. Before any of that, make sure you are looking at a device that
    does not answer, and not at a point with a <em>fault</em> flag, which is a
    different problem.</p>""",
    body_html="""
  <h2>Offline or fault?</h2>
  <p>People use &ldquo;offline&rdquo; for two different things. A device that does
  not answer discovery or reads is a <strong>communication</strong> problem, and
  the rest of this guide is about that. A device that answers but has a point
  showing <em>Fault</em> or an impossible value has a <strong>sensor or wiring</strong>
  problem on the equipment. If you can open the device and read its points, it is
  not offline. See <a href="bacnet-status-flags-explained.html">status flags
  explained</a> for the fault case.</p>

  <h2>Work through these in order</h2>

  <h3>1. Is your phone on the same subnet?</h3>
  <p>Controls equipment normally sits on its own subnet or VLAN. A phone on guest
  Wi-Fi or the office network never receives the device's reply, so everything
  looks offline. When a scan finds nothing, the app shows the phone's IP and mask;
  compare them with the device's address. If they differ, see
  <a href="subnets.html">what is a subnet, and why doesn't the switch give me the
  right one?</a> A device on another subnet needs a
  <a href="what-is-a-bbmd.html">BBMD</a> or a direct add by IP (step 3) to be seen
  at all.</p>

  <h3>2. Scan again</h3>
  <p>Discovery is a broadcast, and Wi-Fi access points drop broadcasts under load.
  A device that shows up in one scan and is gone in the next is usually this. The
  app repeats the Who-Is through each scan and then tries each address directly,
  but a second scan, or a wired connection, settles it.</p>

  <h3>3. Add it directly by IP</h3>
  <p>Menu &rarr; <strong>Add device by IP&hellip;</strong> sends a directed message
  instead of a broadcast. If the device answers that, it is online and the problem
  is purely that broadcasts are not getting through: another subnet, client
  isolation, or a switch that filters them. If it does not answer, carry on.</p>

  <h3>4. Is UDP 47808 blocked, or is the device on another port?</h3>
  <p>BACnet/IP uses UDP <strong>47808</strong>. An access list between VLANs, or a
  device set to 47809 or higher, keeps it unreachable even from the right subnet.
  The port can be typed in when adding by IP; the access list is a question for
  the network team. See <a href="what-port-does-bacnet-use.html">what port does
  BACnet use?</a></p>

  <h3>5. Does another device share its Device ID?</h3>
  <p>Two devices with the same ID, or two MS/TP devices with the same MAC behind one
  router, answer for each other. The symptom is a device that flickers between
  online and offline, or whose name and IP change between scans. The scan summary
  warns about both. See <a href="duplicate-bacnet-device-id.html">duplicate Device
  IDs</a>.</p>

  <h3>6. It really is down</h3>
  <p>Lost power, a pulled cable, a dead switch port, or an MS/TP trunk that has
  stopped behind its router. Once the steps above are ruled out, this is what is
  left, and it is time to look at the equipment. A ping from a laptop on the same
  network confirms it: see <a href="is-my-bacnet-device-online-ping-test.html">is my
  BACnet device online?</a></p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/subnets", "What is a subnet, and why doesn't the switch give me the right one?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-write-access-denied",
    title="BACnet Write Access Denied — what it means | Easy BACnet",
    question="What does BACnet 'Write Access Denied' mean, and how do I fix it?",
    description="Write Access Denied means the BACnet property cannot be written that way: usually a read-only property, a non-commandable point, or the wrong priority.",
    answer_html="""<p>&ldquo;Write Access Denied&rdquo; is the device refusing your
    write on its own rules. Communication worked; the controller received the request
    and declined it. The usual reasons, most common first: you wrote to an input point,
    whose Present_Value belongs to the physical sensor; the object or property is
    read-only on that device; the controller requires the point to be Out Of Service
    before it accepts an external write; or the point is locked by the controller's own
    program. The fix is to write to a different point, or to change how the device is
    configured, not to retry the same write.</p>""",
    body_html="""
  <h2>What the error is</h2>
  <p>It is a BACnet error with class <em>property</em> and code
  <em>write-access-denied</em>, sent back by the device in reply to your WriteProperty.
  That tells you two useful things. The network and the device are fine. And the
  problem is <em>what</em> you tried to write, so retrying or changing the value will
  not help.</p>
  <p>Other error codes mean other things. <em>invalid-data-type</em> means the value
  was the wrong kind (text where a number was expected); <em>value-out-of-range</em>
  means the number was outside what the point accepts; <em>unknown-property</em> or
  <em>unknown-object</em> means you addressed something that does not exist. Only
  <em>write-access-denied</em> is a permissions answer.</p>

  <h2>Why a device refuses, in order of likelihood</h2>

  <h3>1. It is an input point</h3>
  <p>The Present_Value of an Analog Input, Binary Input or Multi-state Input is the
  sensor reading, and the device will not let the network overwrite it. Easy BACnet
  warns you before you try. If you need to force a reading for testing, the BACnet
  way is to set <em>Out_Of_Service</em> true first, which disconnects the object from
  the sensor; many devices do not allow that over the network either. Check the
  object type: the points you can command are Outputs and Values. See
  <a href="bacnet-object-types-explained.html">BACnet object types explained</a>.</p>

  <h3>2. The object or property is read-only on this device</h3>
  <p>Not every Value object is commandable; the vendor decides. Configuration
  properties such as Object_Name, Units or Description are commonly read-only too.
  If the vendor's documentation marks it read-only, there is no way round it over
  BACnet.</p>

  <h3>3. The device wants Out_Of_Service first</h3>
  <p>Some controllers accept external writes to a point only while it is marked Out
  Of Service, so the controller's own logic stops driving it. This is a device policy
  and it is in the manual. Be careful: a point left Out Of Service shows the forced
  value rather than reality until someone clears it.</p>

  <h3>4. The controller's program owns the point</h3>
  <p>Some vendors lock points that their internal logic controls, or restrict which
  priorities an outside tool may use. Forcing past that on live equipment is not a
  good idea without knowing what the program expects. Ask the
  <a href="who-to-call-it-hvac-or-controls.html">controls contractor</a> which
  points are meant to be commanded from outside.</p>

  <h2>What does not cause it</h2>
  <p>Leaving the priority out does not. A WriteProperty with no priority lands at
  priority 16, the lowest; the write is accepted, it just may be outranked. That is
  the &ldquo;I wrote it and nothing changed&rdquo; case, which is covered in
  <a href="bacnet-value-does-not-change-when-written.html">why doesn't my BACnet
  value change when I write to it?</a> Easy BACnet always sends a priority (8 by
  default), so this does not arise from the app.</p>
""",
    related=[
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/bacnet-value-does-not-change-when-written", "Why doesn't my BACnet value change when I write to it?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-value-does-not-change-when-written",
    title="BACnet value won't change when written? | Easy BACnet",
    question="Why doesn't my BACnet value change when I write to it?",
    description="You wrote a BACnet point and nothing changed. Usually a higher priority already commands it, the write missed the priority array, or it is read-only.",
    answer_html="""<p>You wrote the point, the device accepted it, and nothing moved.
    Re-read the point and look at what changed. If the <strong>Present Value did not
    change</strong>, something at a higher priority is holding the point: your write
    landed in its slot and is being outranked. If the <strong>value changed but the
    equipment did not</strong>, the point is overridden at the hardware, Out Of Service,
    or the machine itself has a problem. If the value <strong>changed and then snapped
    back</strong>, the controller's own program is rewriting it. The point screen in
    Easy BACnet shows which priority is in command, which tells you which of the three
    you have.</p>""",
    body_html="""
  <h2>First, re-read the point</h2>
  <p>Easy BACnet re-reads the point after every write, so the value on screen is what
  the device reports, not what you sent. Compare it with what you wrote, and look at
  <strong>Commanded At</strong>. Then pick the case below.</p>

  <h2>Case 1 &mdash; the value did not change</h2>
  <p>A commandable point has sixteen priority slots and follows the highest-priority
  slot that holds a value (1 is highest). If slot 5 holds 72 and you write 68 at slot
  8, the point stays at 72. Your write was accepted and stored; it is simply outranked.
  <strong>Commanded At</strong> shows the winning priority and its value.</p>
  <p>Two things to check:</p>
  <ul>
    <li><strong>Which slot is winning, and whose is it?</strong> Priority 1 and 2 are
    life safety, 5 is critical equipment, 6 is minimum on/off. If one of those holds
    the point, the control system has a reason and you should leave it. Priority 8 is
    another operator or a tool like this one; a stuck 8 is usually an override someone
    forgot to release.</li>
    <li><strong>Did your write carry a priority?</strong> A WriteProperty with no
    priority lands at 16, the lowest, so anything else wins. Easy BACnet always sends
    one (8 by default); some other tools do not.</li>
  </ul>
  <p>The right fix is usually to <strong>release</strong> the slot that should not be
  held (write NULL at that priority) so the point falls back to the program, rather
  than to write at a higher priority and pile one override on another. See
  <a href="how-to-release-a-bacnet-override.html">how to release a BACnet override</a>
  and <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>

  <h2>Case 2 &mdash; the value changed, the equipment did not</h2>
  <p>The controller accepted the command and shows your value, but the fan did not
  start or the valve did not move. The controller is no longer the problem:</p>
  <ul>
    <li><strong>The point is Overridden.</strong> The <em>Overridden</em> status flag
    means something local to the device, typically a hand/off/auto switch at the
    equipment, is forcing the output. Nothing written over the network will move it.</li>
    <li><strong>The point is Out Of Service.</strong> The object is disconnected from
    its hardware for testing, so Present_Value changes freely and drives nothing.</li>
    <li><strong>The machine has a fault.</strong> A tripped overload, a locked-out
    compressor, a failed actuator. The command is correct; the mechanical side is not.</li>
  </ul>
  <p>Check the point's status flags (see
  <a href="bacnet-status-flags-explained.html">status flags explained</a>). Overridden
  and Out Of Service are a controls visit; a healthy point with a dead machine is an
  HVAC visit.</p>

  <h2>Case 3 &mdash; the value changed, then snapped back</h2>
  <p>The controller's own logic writes that point every program cycle at the same or a
  higher priority, so your value lasts a second. You cannot win that from outside, and
  on a live system you should not try. If you need to hold the point, the program has
  to be changed or the point released from its control, which is a job for the
  <a href="who-to-call-it-hvac-or-controls.html">controls contractor</a>.</p>

  <h2>If the write was refused instead</h2>
  <p>If the device answered with an error rather than accepting the write, that is a
  different problem: see
  <a href="bacnet-write-access-denied.html">what does BACnet Write Access Denied
  mean?</a> Input points and read-only Value objects fall in that category.</p>
""",
    related=[
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
        ("guides/bacnet-write-access-denied", "What does BACnet Write Access Denied mean?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/export-bacnet-points-to-csv",
    title="Export BACnet IP points to Excel or CSV | Easy BACnet",
    question="How do I export a BACnet IP points list to Excel or CSV, and what is an EDE file?",
    description="Scan a building from your phone and export every BACnet IP device and point as an Excel spreadsheet to share or save as CSV. Plus how EDE files differ.",
    answer_html="""<p>Scan the network, then export: <a href="../index.html">Easy BACnet</a>
    reads every point on every device it found and builds an Excel spreadsheet
    (<code>.xlsx</code>) &mdash; a device summary on top, then one row per point with Device ID,
    Device Name, Device IP, Object Type, Object Number, Point Name, Present Value, Units and
    Status. Your phone's share sheet opens so you can email it or save it to Drive or Files. It
    opens in Excel, Google Sheets or LibreOffice, and <em>File &rarr; Save As &rarr; CSV</em>
    turns it into a CSV if that is what was asked for. An <strong>EDE file</strong> (Engineering
    Data Exchange) is a more formal, fixed-column spreadsheet that integrators use to import
    points into a building management system &mdash; the same information, in a set layout.</p>""",
    body_html="""
  <h2>What people mean by &ldquo;a points list&rdquo;</h2>
  <p>When a vendor, integrator or analytics provider asks for your points list, they want a
  table of what exists on the equipment: for each object, its name, what kind of object it is,
  its number, and usually a live value and units. Unlike Modbus, BACnet devices can be
  <em>asked</em> what they contain &mdash; so this list can be built by reading the device, not
  by hunting for a document. See
  <a href="what-is-a-bacnet-points-list.html">what is a BACnet IP points list?</a></p>

  <h2>Step by step: collect and export from a phone</h2>
  <ol>
    <li><strong>Get on the controls network.</strong> Join the building's controls Wi-Fi, or
    plug in with a USB-Ethernet adapter. Turn mobile data off if Wi-Fi says <em>Connected, no
    internet</em>.</li>
    <li><strong>Scan.</strong> Open Easy BACnet, tap <strong>Easy BACnet Mode</strong>, then
    <strong>Scan for Devices</strong>. Wait for <em>Success! Found N device(s)</em> (up to a
    minute). For controllers on other subnets, add them first with menu &rarr; <strong>Add device
    by IP&hellip;</strong> or set <strong>BBMD for remote networks&hellip;</strong> and scan
    again &mdash; everything in the device list is exported.</li>
    <li><strong>Check it (optional).</strong> <strong>View Results</strong> lists every device;
    tap one to see its points. Very large controllers load the first 2,000 objects; add any
    specific object beyond that with <strong>Add object by number</strong>.</li>
    <li><strong>Export.</strong> Tap <strong>Export Results</strong>. On the free version you
    are asked <em>Watch a short ad?</em> first (<strong>Watch ad</strong> / <strong>Remove
    ads</strong> / <strong>Cancel</strong>); if no ad can load, the export just runs. The app
    re-reads every point list and every present value &mdash; the progress box shows
    <em>Point list: x of y</em> then <em>Values: x of y</em> for each device. Stay in Wi-Fi range
    until it finishes, or tap <strong>Cancel</strong> to stop.</li>
    <li><strong>Share or save.</strong> The share sheet opens (<em>Send export by email</em>)
    with <code>EasyBACnet_YYYYMMDD_HHMM.xlsx</code> attached, the subject <em>BACnet IP
    Export</em> and today's date, and a line giving the device and point counts. Pick your email
    app and add the recipient, or pick Drive, Files or a messenger to keep it. Nothing is sent
    until you send it.</li>
  </ol>

  <h2>What the spreadsheet contains</h2>
  <p>One sheet with two tables, so it reads well on a phone screen and in Excel:</p>
  <table>
    <tr><th>Section</th><th>Columns</th></tr>
    <tr><td>Device summary (top)</td><td><em>Devices Found</em> count, then per device: Device ID, Device Name, Device IP, Points (how many)</td></tr>
    <tr><td>Point detail (below)</td><td>Device ID, Device Name, Device IP, Object Type, Object Number, Point Name, Present Value, Units, Status</td></tr>
  </table>
  <ul>
    <li>Each device gets a bold row of its own in the detail table (Object Type
    <em>Device</em>), so every controller and its IP is listed even if it returned no
    points.</li>
    <li>Any point whose <strong>Status</strong> is not <em>Normal</em> &mdash; in alarm, fault,
    overridden or out of service &mdash; is shaded red. See
    <a href="bacnet-status-flags-explained.html">status flags explained</a>.</li>
    <li>Device IDs, object numbers and counts are stored as numbers, so sorting and filtering
    work straight away. Present values keep the app's formatting (e.g. <em>Active (On)</em> for a
    binary point) and units use short symbols such as °F, % RH or kW.</li>
    <li>Descriptions and priority arrays are not exported; open a point in the app to see
    those.</li>
  </ul>

  <h2>Need a CSV?</h2>
  <p>Open the <code>.xlsx</code> in Excel and use <em>File &rarr; Save As &rarr; CSV UTF-8</em>
  (Google Sheets: <em>File &rarr; Download &rarr; CSV</em>). If you only want the point detail
  in the CSV, delete the summary rows above the detail header first, so the file has a single
  header row &mdash; that is what most import tools expect.</p>

  <h2>Excel/CSV versus EDE &mdash; which do they want?</h2>
  <table>
    <tr><th></th><th>Easy BACnet export</th><th>EDE file</th></tr>
    <tr><td>What it is</td><td>A plain table of the network's devices, objects and live values</td><td>A standardised BACnet spreadsheet with fixed columns for import</td></tr>
    <tr><td>Opens in Excel</td><td>Yes (.xlsx; save as CSV if needed)</td><td>Yes (it is a spreadsheet/CSV)</td></tr>
    <tr><td>Best for</td><td>&ldquo;Show me what's on this site&rdquo;, records, a vendor request, troubleshooting</td><td>Bulk-importing points into a BMS or analytics platform to a fixed schema</td></tr>
    <tr><td>Contains</td><td>Names, values, units, status, object IDs, device IPs</td><td>Object name, type, instance, and standard EDE columns (present-value fields, units, COV increment, etc.)</td></tr>
  </table>
  <p>EDE (Engineering Data Exchange) is a convention from the BACnet world for moving a point
  list between tools in a predictable column order. If someone specifically asks for &ldquo;an
  EDE&rdquo;, they mean that layout. If they just say &ldquo;send me the points&rdquo;, a
  spreadsheet with clear names and values is what they are after &mdash; and it is easy to
  reshape into an EDE template if they later need one.</p>

  <div class="callout">
  <p>The value of exporting from the live devices is that it is <em>true</em>: it is what the
  equipment actually reports today, not what a years-old design document claims. An export
  built from a real scan is often the most accurate points list a building has. See
  <a href="vendor-asking-for-bacnet-information.html">a vendor asked for my BACnet
  information</a>.</p>
  </div>

  <h2>Privacy</h2>
  <p>The export is built on your phone and kept in the app's private cache; the app has no
  server and sends nothing itself. Once you share it, it goes wherever you send it. A points
  list is a map of a building's controls &mdash; send it to a named person, not a shared inbox.
  Details are in the <a href="../privacy.html">privacy policy</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I get a BACnet IP points list off a building?"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information"),
        ("guides/read-bacnet-values-from-phone", "How do I read BACnet values from a phone?"),
    ],
))

GUIDES.append(dict(
    slug="guides/test-bacnet-device-without-bms",
    title="Test a BACnet IP device without a BMS | Easy BACnet",
    question="How do I test a BACnet IP device without a BMS?",
    description="You don't need the BMS to prove a BACnet IP device works. How to discover it, read its points and check that it responds to commands, with a phone.",
    answer_html="""<p>You do not need the building management system, a laptop, or the
    integrator to prove a BACnet IP device is alive and working. Any BACnet client on the
    same network can do it &mdash; including <a href="../index.html">Easy BACnet</a> on
    a phone. Join the network, run a Who-Is, and if the device answers with its name and
    Device ID it is online and speaking BACnet. Read its points to confirm the sensors
    report sane values, and &mdash; carefully &mdash; command a commandable point to
    confirm it responds. That is a full functional check with nothing but a phone.</p>""",
    body_html="""
  <h2>Why you can do this without the BMS</h2>
  <p>BACnet has no login and no single master. Any device on the network can ask any
  other device questions, and that is all a BMS does: it is a BACnet client with a
  front end. A handheld client can perform the same discovery, reads and writes,
  which makes a phone a good tool for commissioning checks, start-up and
  &ldquo;is this new controller talking yet?&rdquo; before the BMS is connected.</p>

  <h2>The test, step by step</h2>

  <h3>1. Prove it is on the network (discovery)</h3>
  <p>Run a scan. If the device answers a Who-Is with its name, Device ID and IP, it is
  powered, on the network, and speaking BACnet/IP &mdash; three things confirmed at
  once. If it does not answer, that is a network or address problem, not necessarily a
  dead device: see <a href="bacnet-device-shows-offline.html">why does my BACnet IP device
  show offline?</a></p>

  <h3>2. Prove the sensors read (inputs)</h3>
  <p>Open the device and read its input points. Do the values make physical sense &mdash;
  a room temperature near room temperature, a damper position between 0 and 100%? A
  point flagged fault or unreliable, or reading an impossible number, points at a sensor
  or wiring problem on the equipment. This alone catches a lot of commissioning faults.</p>

  <h3>3. Prove it responds to control (outputs)</h3>
  <p>On a commandable output, write a value at a manual priority and watch what happens
  &mdash; a valve drives, a fan starts, the feedback point moves. Then <strong>release
  it</strong> so you do not leave an override behind. This confirms the whole chain: the
  controller received the command and the actuator obeyed. Do this only where it is safe
  to move the equipment, and always release afterwards &mdash; see
  <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet point</a> and
  <a href="bacnet-priority-and-stuck-overrides.html">priority and stuck overrides</a>.</p>

  <h2>What a phone test can and cannot tell you</h2>
  <ul>
    <li><strong>Can</strong>: confirm the device is online, that points read sane
    values, that outputs respond to commands, and capture the whole lot as a
    <a href="export-bacnet-points-to-csv.html">spreadsheet</a> for a record.</li>
    <li><strong>Cannot</strong>: discover a whole other subnet without a
    <a href="what-is-a-bbmd.html">BBMD</a> (one known device can be
    <a href="bacnet-add-device-by-ip.html">added by IP</a>), or plug straight into an MS/TP trunk &mdash;
    those go through a router. And it does not replace the BMS's scheduling and trending;
    it proves the device works, not that the whole sequence is programmed.</li>
  </ul>
""",
    related=[
        ("guides/read-bacnet-values-from-phone", "How do I read BACnet values from a phone?"),
        ("guides/bacnet-device-shows-offline", "Why does my BACnet IP device show offline?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
        ("guides/export-bacnet-points-to-csv", "How do I export a BACnet IP points list to Excel or CSV?"),
    ],
))

GUIDES.append(dict(
    slug="guides/best-free-bacnet-explorer",
    title="Best free BACnet explorer tools | Easy BACnet",
    question="What is the best free BACnet explorer tool?",
    description="The free BACnet explorers compared: YABE, CAS BACnet Explorer, the Contemporary Controls BDT and Wacnet, plus where a free phone tool fits fieldwork.",
    answer_html="""<p>On a laptop, the free choices are <strong>YABE</strong> (Yet Another
    BACnet Explorer, open source, Windows), the <strong>Contemporary Controls BACnet
    Discovery Tool</strong> (free Windows download) and <strong>Wacnet</strong> (open
    source, runs anywhere Java does, browser interface). Chipkin's <strong>CAS BACnet
    Explorer</strong> is the polished commercial option, with a free trial. All of them
    need a laptop on the controls network. For a quick check from the plant room,
    <a href="../index.html">Easy BACnet</a> does discovery, reading, writing and export
    from an Android phone, free.</p>""",
    body_html="""
  <h2>The tools</h2>
  <table>
    <tr><th>Tool</th><th>Platform</th><th>Reads</th><th>Writes</th><th>Cost</th><th>Notes</th></tr>
    <tr><td>YABE</td><td>Windows</td><td>Yes</td><td>Yes</td><td>Free, open source</td><td>Very capable, dense technical interface. The usual first answer to &ldquo;free BACnet explorer&rdquo;.</td></tr>
    <tr><td>Contemporary Controls BDT</td><td>Windows</td><td>Yes</td><td>Yes (value, priority, object name)</td><td>Free (download behind a contact form)</td><td>Light discovery tool; good for checking MS/TP devices behind the maker's routers. Can graph points.</td></tr>
    <tr><td>Wacnet</td><td>Windows, macOS, Linux (Java)</td><td>Yes</td><td>Yes</td><td>Free, open source</td><td>Single JAR, browser-based interface, REST API for scripting.</td></tr>
    <tr><td>CAS BACnet Explorer</td><td>Windows</td><td>Yes</td><td>Yes</td><td>Paid, free trial</td><td>Polished commissioning tool from Chipkin; a licence is bundled with their gateways.</td></tr>
    <tr><td>Easy BACnet</td><td>Android</td><td>Yes</td><td>Yes</td><td>Free (optional Pro subscription)</td><td>Discovery, read, write at a chosen priority with release, Excel export. Phone or tablet.</td></tr>
  </table>

  <h2>Which one</h2>
  <ul>
    <li><strong>Deep work at a Windows laptop:</strong> YABE. If you want something more
    polished and the budget allows, CAS BACnet Explorer.</li>
    <li><strong>A quick device check on a laptop, or a Mac:</strong> Wacnet. On Windows
    the Contemporary Controls tool is also quick to set up.</li>
    <li><strong>Checking equipment where it is, without a laptop:</strong> Easy BACnet.
    Discovery, live values, a careful write and release, and an
    <a href="export-bacnet-points-to-csv.html">Excel report</a> from the network you are
    already standing on. See <a href="bacnet-scanner-app-android.html">is there a BACnet
    IP scanner app for Android?</a></li>
  </ul>
  <p>Most people end up with one of each: a desktop explorer for desk work and a phone
  tool for the walk-around.</p>

  <h2>What &ldquo;free&rdquo; covers</h2>
  <p>Check before you rely on a tool: some gate the download behind a form, some are
  trial versions, some are free for personal use only. Easy BACnet is free to scan,
  read, write and export. The optional Easy BACnet Pro subscription ($9.99 a year)
  removes the ads and lifts the limit on saved custom remotes and control panels; it
  adds no reading or writing features.</p>
""",
    related=[
        ("guides/bacnet-scanner-app-android", "Is there a BACnet IP scanner app for Android?"),
        ("guides/read-bacnet-values-from-phone", "How do I read BACnet values from a phone?"),
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/test-bacnet-device-without-bms", "How do I test a BACnet IP device without a BMS?"),
    ],
))

GUIDES.append(dict(
    slug="guides/does-easy-bacnet-support-mstp-rs485",
    title="Does Easy BACnet support MS/TP or RS-485? | Easy BACnet",
    question="Does Easy BACnet support MS/TP or RS-485?",
    description="No. Easy BACnet is a BACnet IP tool and does not connect to an MS/TP (RS-485) trunk directly, but it reads MS/TP devices routed onto IP by a BACnet router.",
    answer_html="""<p><strong>No &mdash; not directly, and not at this time.</strong> Easy
    BACnet talks <strong>BACnet IP</strong> over your phone's Wi-Fi or a
    USB-Ethernet adapter. A phone has no RS-485 serial port, so the app cannot plug
    into or read an <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> (RS-485)
    trunk on its own. It <em>can</em> see MS/TP devices when they are routed onto
    the IP network by a BACnet router &mdash; you reach them through the router, not
    by wiring into the serial bus.</p>""",
    body_html="""
  <h2>The short version</h2>
  <p>Easy BACnet is a BACnet IP browser and control tool. It does two things with
  MS/TP:</p>
  <ul>
    <li><strong>Direct MS/TP / RS-485 connection: not supported.</strong> The app
    does not speak to a serial trunk, and there is no plan for a phone to do so &mdash;
    phones have no RS-485 hardware.</li>
    <li><strong>Routed MS/TP over IP: supported.</strong> If a BACnet router (or a
    controller with a built-in router) advertises its MS/TP devices onto BACnet IP,
    those devices appear in a scan and you can read and command them through the
    router. Easy BACnet shows their routed network number and MAC so you can tell
    them apart from native IP devices.</li>
  </ul>

  <div class="callout">
  <p>If the only path to your controllers is a bare RS-485 MS/TP trunk with no
  router onto IP, Easy BACnet cannot reach them, and neither can any other phone
  app. You need a device that bridges MS/TP onto the IP network first.</p>
  </div>

  <h2>Why a phone can't touch MS/TP directly</h2>
  <p><a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> runs over an RS-485 serial
  pair &mdash; two or three wires, a token passed from device to device. BACnet IP
  runs over the ordinary data network on UDP 47808. They are the same language on
  completely different wiring. Reading MS/TP directly needs an RS-485 serial
  interface, which phones do not have and which a laptop only gets with a dedicated
  USB-to-RS-485 adapter and MS/TP software. Easy BACnet stays on the IP side on
  purpose: it is the side a phone can actually reach.</p>

  <h2>How to reach MS/TP devices anyway</h2>
  <ul>
    <li><strong>Through the router they already sit behind.</strong> Most buildings
    put a BACnet router (often part of a supervisory controller or gateway) between
    the MS/TP trunks and the IP backbone. If yours does, those MS/TP devices are
    already on IP as far as your phone is concerned &mdash; scan and they show up.</li>
    <li><strong>Confirm a router exists.</strong> If a whole set of controllers is
    missing from a scan and they are known to be MS/TP, ask whoever owns the controls
    whether those trunks are routed onto IP, and where the router is. That is a
    <a href="who-to-call-it-hvac-or-controls.html">controls / BMS question</a>, not a
    network or app one.</li>
  </ul>

  <h2>Might direct MS/TP come later?</h2>
  <p>Not for the phone app; phones have no RS-485 hardware. Easy BACnet is a BACnet
  IP tool and will stay one. If you need to sit on a serial trunk directly, that is a
  job for a laptop with an RS-485 adapter and MS/TP software.</p>
""",
    related=[
        ("guides/bacnet-mstp-vs-bacnet-ip", "BACnet MS/TP vs BACnet/IP"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
    ],
))

GUIDES.append(dict(
    slug="guides/who-to-call-it-hvac-or-controls",
    title="Who to call: IT, HVAC, or controls/BMS? | Easy BACnet",
    question="Who do I call when something's wrong &mdash; IT, HVAC, or the controls contractor?",
    description="Most BACnet IP problems belong to IT/network, the HVAC contractor, or the controls/BMS integrator. Who owns what, and who to call for each symptom.",
    answer_html="""<p>Match the problem to the provider. If you <strong>can't reach the
    equipment on the network</strong> (nothing scans, wrong subnet, a firewall),
    that's your <strong>IT / network</strong> provider. If the equipment is reachable
    but <strong>the physical machine is misbehaving</strong> (a fan that won't run, no
    heating, a tripped unit), that's the <strong>HVAC / mechanical</strong>
    contractor. If the equipment runs but <strong>the control logic, points, schedules
    or overrides are wrong</strong>, that's the <strong>controls / BMS integrator</strong>
    &mdash; the company that programmed the system. Easy BACnet helps you tell which of
    the three you're looking at; it doesn't replace any of them.</p>""",
    body_html="""
  <h2>Three providers, three kinds of problem</h2>
  <p>On almost every building, three different companies own three different layers.
  Knowing which one to call &mdash; and not wasting a day with the wrong one &mdash; is
  half the job.</p>

  <h3>IT / network provider</h3>
  <p>Owns the wires, switches, Wi-Fi, VLANs, IP addresses and firewalls &mdash; the
  network the controllers ride on. Call them when the problem is
  <strong>reachability</strong>: you can't get onto the controls network, you're on
  the wrong <a href="subnets.html">subnet</a>, a scan finds nothing, or a firewall is
  blocking BACnet IP (UDP 47808). They cannot help with what a controller is doing,
  only whether you can talk to it.</p>

  <h3>HVAC / mechanical contractor</h3>
  <p>Owns the physical equipment &mdash; the air handlers, chillers, boilers, pumps,
  fans, dampers and valves, and the wiring to them. Call them when the
  <strong>machine itself</strong> is the problem: a fan motor that won't start, a
  compressor that's locked out, no airflow, a water leak, a unit that's mechanically
  tripped. The app may read a point correctly and the equipment still be broken &mdash;
  that's their domain.</p>

  <h3>Controls / BMS integrator</h3>
  <p>Also called the temperature controls contractor, ATC, or building-automation
  integrator &mdash; the company that <strong>programmed and commissioned</strong> the
  control system. Owns the controllers, the BACnet points, the sequences of
  operation, schedules, setpoints, alarms and graphics. Call them when the equipment
  is healthy and reachable but the <strong>logic is wrong</strong>: a point is
  <a href="bacnet-priority-and-stuck-overrides.html">stuck in override</a>, a schedule
  isn't running, a setpoint won't hold, a device is
  <a href="bacnet-device-id-explained.html">unconfigured or has a duplicate ID</a>, or
  a value reads right but nothing acts on it.</p>

  <h2>Which one do I call? (symptom &rarr; owner)</h2>
  <table>
    <tr><th>What you're seeing</th><th>Who owns it</th></tr>
    <tr><td>Scan finds nothing; you may be on the wrong subnet or on guest Wi-Fi</td><td>IT / network</td></tr>
    <tr><td>You can reach some devices but a firewall or VLAN blocks others</td><td>IT / network</td></tr>
    <tr><td>You need a static IP, a switch port on the controls VLAN, or a BBMD address</td><td>IT / network</td></tr>
    <tr><td>A device answers, but the fan/pump/compressor physically won't run</td><td>HVAC / mechanical</td></tr>
    <tr><td>No heating or cooling, a leak, a mechanically tripped or locked-out unit</td><td>HVAC / mechanical</td></tr>
    <tr><td>A point is stuck in override and won't release</td><td>Controls / BMS</td></tr>
    <tr><td>A schedule, setpoint or sequence isn't behaving; a value reads right but nothing happens</td><td>Controls / BMS</td></tr>
    <tr><td>Unconfigured devices, duplicate Device IDs, or missing points after commissioning</td><td>Controls / BMS</td></tr>
    <tr><td>MS/TP controllers aren't visible and you're not sure they're routed onto IP</td><td>Controls / BMS</td></tr>
  </table>

  <h2>What to have ready before you call</h2>
  <p>The same handful of facts turns a long call into a short one. Easy BACnet gives
  you most of them:</p>
  <ul>
    <li><strong>Your phone's address and subnet mask</strong> (the app shows these when
    a scan finds nothing) &mdash; the first thing IT will ask.</li>
    <li><strong>The Device ID, name and IP</strong> of the unit in question, from the
    scan.</li>
    <li><strong>The point name and what it's doing</strong> &mdash; its present value,
    units, status, and which priority is commanding it &mdash; for a controls call.</li>
    <li><strong>What you expected versus what you saw.</strong> "AHU-2 supply fan
    command reads On at priority 8 but the fan isn't turning" tells all three providers
    exactly whose problem it is.</li>
    <li><strong>Which switch or jack you're plugged into</strong>, if it's a network
    question.</li>
  </ul>
  <p>Exporting the scan as a spreadsheet and attaching it is often the fastest way to give an
  integrator what they need &mdash; see
  <a href="vendor-asking-for-bacnet-information.html">what to send when a vendor asks
  for your BACnet information</a>.</p>

  <h2>The grey areas &mdash; who to call first</h2>
  <ul>
    <li><strong>"I can't find any devices."</strong> Usually IT / network first
    (you're likely on the wrong subnet). If IT confirms you're on the controls network
    and devices are known to be MS/TP, it becomes a controls question &mdash; are those
    trunks <a href="does-easy-bacnet-support-mstp-rs485.html">routed onto IP</a>?</li>
    <li><strong>"The value looks wrong."</strong> Decide whether the <em>number</em> is
    wrong (a sensor reading nonsense &rarr; controls or mechanical) or the number is
    right but nothing acts on it (a stuck override or bad sequence &rarr; controls).</li>
    <li><strong>"It worked yesterday."</strong> Ask what changed &mdash; a network
    change (IT), a part that failed (mechanical), or a programming change (controls).</li>
  </ul>

  <h2>Where Easy BACnet fits</h2>
  <p>The app tells you what is on the network, what each point reads, and who is
  commanding it. That is enough to call the right provider with evidence instead of
  a guess. It does not fix a network, a motor or a control program, and it is
  <a href="does-easy-bacnet-support-mstp-rs485.html">BACnet IP only</a>, so it will
  not reach a bare MS/TP serial trunk.</p>
""",
    related=[
        ("guides/subnets", "Why am I on the wrong network even though I'm plugged into the switch?"),
        ("guides/cant-find-what-im-looking-for", "The app can&rsquo;t find what I&rsquo;m looking for"),
        ("guides/does-easy-bacnet-support-mstp-rs485", "Does Easy BACnet support MS/TP or RS-485?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/what-is-bacnet",
    title="What is BACnet? A plain-English guide | Easy BACnet",
    question="What is BACnet?",
    description="BACnet is the standard language building equipment uses to talk over a network: HVAC, lighting, metering. What it is, how BACnet IP works, how to see it.",
    answer_html="""<p><strong>BACnet is the common language that building equipment uses to
    talk to a control system and to each other.</strong> It is an open standard
    (ASHRAE 135 / ISO 16484-5) that lets a thermostat, air handler, chiller, meter or
    lighting panel from one manufacturer exchange data with a building management system
    from another. On a modern building it usually rides on the ordinary data network as
    <strong>BACnet IP</strong> (UDP port 47808). Each piece of equipment is a
    <em>device</em>; every readable or controllable thing inside it &mdash; a temperature,
    a fan command, a setpoint &mdash; is an <em>object</em>, or <em>point</em>. Easy BACnet
    lets you see all of that from a phone on the same network.</p>""",
    body_html="""
  <h2>The one-paragraph version</h2>
  <p>Before BACnet, every controls manufacturer spoke its own private protocol, and
  nothing from one brand could talk to anything from another. BACnet fixed that: it is a
  vendor-neutral standard, first published in 1995 and maintained by ASHRAE, that defines
  <em>how</em> building devices describe themselves and exchange values. A Trane air
  handler, a Johnson Controls thermostat and a Schneider meter can all sit on the same
  network and be read by the same tool &mdash; because they all speak BACnet.</p>

  <h2>Devices, objects and points</h2>
  <p>BACnet organises everything into a simple hierarchy:</p>
  <ul>
    <li><strong>Device</strong> &mdash; one piece of equipment or one controller. It has a
    unique <a href="bacnet-device-id-explained.html">Device ID</a> and, on BACnet IP, an IP
    address.</li>
    <li><strong>Object</strong> &mdash; one thing inside that device: an analog input for a
    temperature sensor, a binary output for a fan, an analog value for a setpoint. Each has
    an <a href="bacnet-object-types-explained.html">object type</a> and an instance number.</li>
    <li><strong>Property</strong> &mdash; a fact about an object. The one you care about most
    is <code>Present_Value</code> (the current reading or command), but there are also
    <code>Units</code>, <code>Status_Flags</code>, <code>Description</code> and more.</li>
  </ul>
  <p>The list of every object on a device is its
  <a href="what-is-a-bacnet-points-list.html">points list</a> &mdash; the map of everything
  you can read or command.</p>

  <h2>How devices find each other: Who-Is / I-Am</h2>
  <p>You do not need to know a device's address in advance. A tool broadcasts a
  <a href="who-is-i-am-explained.html">Who-Is</a> message; every device on the network
  answers with <em>I-Am</em>, giving its Device ID and address. That is what happens
  when you tap Scan in Easy BACnet.</p>

  <h2>BACnet IP vs MS/TP</h2>
  <p>BACnet runs over more than one kind of wiring. The two you will meet are:</p>
  <ul>
    <li><strong>BACnet IP</strong> &mdash; runs on the normal Ethernet/Wi-Fi network on
    <a href="what-port-does-bacnet-use.html">UDP 47808</a>. This is what a phone or laptop
    can reach.</li>
    <li><strong><a href="bacnet-mstp-vs-bacnet-ip.html">BACnet MS/TP</a></strong> &mdash; runs
    on an RS-485 serial pair, common for the smaller controllers out at the equipment. A
    phone cannot touch MS/TP directly, but a BACnet router can bring those devices
    onto IP where you <em>can</em> see them.</li>
  </ul>

  <div class="callout">
  <p><strong>Where Easy BACnet fits.</strong> It is a BACnet IP browser: put your phone on
  the same network as the controllers, scan, and it shows every device, every point, live
  values, and who is commanding each one &mdash; and it can command and release points too.
  It is BACnet IP only; it does not wire into a bare MS/TP serial trunk.</p>
  </div>

  <h2>What people use BACnet for</h2>
  <p>Mostly HVAC &mdash; air handlers, rooftop units, chillers, boilers, VAV boxes,
  thermostats &mdash; but also lighting control, metering (power, water, gas), and parts of
  access and life-safety systems. If a building has a &ldquo;BMS&rdquo; or &ldquo;BAS&rdquo;
  (building management/automation system), BACnet is very often the language underneath it.</p>

  <h2>See it for yourself</h2>
  <p>The fastest way to understand BACnet is to look at a live one. On a phone on the
  building network, <a href="how-to-use-easy-bacnet.html">run a scan</a>, open a device, and
  browse its points. For the terms you will run into, keep the
  <a href="bacnet-glossary.html">BACnet glossary</a> handy.</p>
""",
    related=[
        ("guides/bacnet-glossary", "BACnet glossary: the terms explained"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/bacnet-vs-modbus", "BACnet vs Modbus: the difference"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-glossary",
    title="BACnet glossary: the terms explained | Easy BACnet",
    question="BACnet glossary: what do all the terms mean?",
    description="Plain-English definitions of BACnet terms you meet in the field: device, object, point, Present_Value, priority array, Who-Is, BBMD, MS/TP and more.",
    answer_html="""<p><strong>A short, plain-English dictionary of the BACnet words you will
    actually run into.</strong> A <em>device</em> is one piece of equipment; an
    <em>object</em> (or <em>point</em>) is one readable/controllable thing inside it; its
    <em>Present_Value</em> is the current reading or command. The rest &mdash; Device ID,
    object types, priority array, Who-Is/I-Am, BBMD, MS/TP &mdash; are defined below, each
    with a link to a fuller guide.</p>""",
    body_html="""
  <h2>The core building blocks</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong>BACnet</strong></td><td>The open standard (ASHRAE 135 / ISO 16484-5) building equipment uses to talk to each other. See <a href="what-is-bacnet.html">What is BACnet?</a></td></tr>
    <tr><td><strong>Device</strong></td><td>One controller or piece of equipment on the network. Has a unique Device ID and, on IP, an IP address.</td></tr>
    <tr><td><strong>Object</strong></td><td>One thing inside a device &mdash; a sensor, an output, a setpoint. Has a type and an instance number.</td></tr>
    <tr><td><strong>Point</strong></td><td>Everyday word for an object you read or command. A device's full list is its <a href="what-is-a-bacnet-points-list.html">points list</a>.</td></tr>
    <tr><td><strong>Property</strong></td><td>A field on an object, e.g. <code>Present_Value</code>, <code>Units</code>, <code>Status_Flags</code>, <code>Description</code>.</td></tr>
    <tr><td><strong>Present_Value</strong></td><td>The current reading (for an input) or the current command (for an output/value). The number you usually want.</td></tr>
  </table>

  <h2>Identifying and finding things</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong><a href="bacnet-device-id-explained.html">Device ID</a></strong></td><td>A number that uniquely identifies a device across the whole BACnet network (0&ndash;4194302). Not the same as its IP address.</td></tr>
    <tr><td><strong><a href="bacnet-object-types-explained.html">Object type</a></strong></td><td>What kind of object it is: Analog Input, Binary Output, Multi-state Value, etc.</td></tr>
    <tr><td><strong>Instance number</strong></td><td>Which one of that type &mdash; Analog Input 1, Analog Input 2, and so on.</td></tr>
    <tr><td><strong>Object Identifier</strong></td><td>Type + instance packed into one 32-bit number. Our <a href="../bacnet-object-id-decoder.html">decoder tool</a> splits it apart.</td></tr>
    <tr><td><strong><a href="who-is-i-am-explained.html">Who-Is / I-Am</a></strong></td><td>The broadcast question and answer that let a tool discover devices without knowing their addresses.</td></tr>
  </table>

  <h2>Commanding and overrides</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong><a href="bacnet-priority-and-stuck-overrides.html">Priority array</a></strong></td><td>A 16-slot list on a commandable object. Whoever writes at the highest priority (1 = highest) wins.</td></tr>
    <tr><td><strong>Command priority</strong></td><td>The slot (1&ndash;16) you write at. Manual operators typically use 8.</td></tr>
    <tr><td><strong>Relinquish default</strong></td><td>The value the object falls back to when every priority slot is empty.</td></tr>
    <tr><td><strong>Release (relinquish)</strong></td><td>Writing NULL to a slot to give control back. See <a href="how-to-release-a-bacnet-override.html">how to release an override</a>.</td></tr>
    <tr><td><strong>Commandable</strong></td><td>An object you can write to (typically outputs and values), as opposed to a read-only input.</td></tr>
    <tr><td><strong>Out of Service</strong></td><td>An object flag that decouples <code>Present_Value</code> from the real hardware so it can be forced for testing.</td></tr>
    <tr><td><strong><a href="bacnet-status-flags-explained.html">Status_Flags</a></strong></td><td>Four flags on an object: In Alarm, Fault, Overridden, Out Of Service.</td></tr>
  </table>

  <h2>Networking and wiring</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong>BACnet IP</strong></td><td>BACnet over the normal data network, on <a href="what-port-does-bacnet-use.html">UDP 47808</a>. What a phone can reach.</td></tr>
    <tr><td><strong><a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a></strong></td><td>BACnet over an RS-485 serial pair. Common for small field controllers. A phone cannot reach it directly.</td></tr>
    <tr><td><strong>BACnet router</strong></td><td>A device that bridges MS/TP (or other) networks onto BACnet IP, so those devices appear on IP.</td></tr>
    <tr><td><strong><a href="what-is-a-bbmd.html">BBMD</a></strong></td><td>BACnet Broadcast Management Device &mdash; forwards broadcast discovery across subnets that a router otherwise blocks.</td></tr>
    <tr><td><strong>Network number</strong></td><td>An ID for a BACnet network segment. Routed (e.g. MS/TP) devices show a network number and a MAC.</td></tr>
    <tr><td><strong><a href="subnets.html">Subnet</a></strong></td><td>The IP neighbourhood your phone is on. Broadcast discovery only reaches devices on the same subnet (absent a BBMD).</td></tr>
  </table>

  <div class="callout">
  <p>New to all of this? Start with <a href="what-is-bacnet.html">What is BACnet?</a> for the
  big picture, then come back here whenever a word trips you up.</p>
  </div>
""",
    related=[
        ("guides/what-is-bacnet", "What is BACnet?"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-engineering-units-explained",
    title="BACnet engineering units explained | Easy BACnet",
    question="What do the units on a BACnet point mean?",
    description="BACnet sends an engineering-units code with each analog value: degrees F, kPa, %RH, cfm and hundreds more. What the Units property is and how to read it.",
    answer_html="""<p><strong>Every analog BACnet point can carry a <code>Units</code> property
    &mdash; a standard code that says what the number means.</strong> A supply-air value of
    <code>55.0</code> means little on its own; with <code>Units = degrees-Fahrenheit</code>
    it is 55&nbsp;&deg;F. BACnet defines a fixed list of engineering units (temperature,
    pressure, flow, humidity, power, and many more), and Easy BACnet shows the human name
    next to each value so you do not have to memorise the code numbers.</p>""",
    body_html="""
  <h2>What the Units property actually is</h2>
  <p>On an analog object &mdash; Analog Input, Analog Output, Analog Value &mdash; the
  <code>Present_Value</code> is just a number. A second property, <code>Units</code>, holds a
  standard code (an enumeration) that tells you what that number is measuring. The BACnet
  standard fixes the list, so <code>degrees-Fahrenheit</code> means the same thing on every
  brand of controller. Binary and multi-state points usually have no units &mdash; their
  meaning comes from their states, not a scale.</p>

  <p>Easy BACnet reads <code>Units</code> for you and prints the readable name (e.g.
  &ldquo;&deg;F&rdquo;, &ldquo;%&rdquo;, &ldquo;cfm&rdquo;) beside the value, so a point reads
  as <em>72.4&nbsp;&deg;F</em> rather than a bare number and a code.</p>

  <h2>Common units you'll meet in the field</h2>
  <table>
    <tr><th>Category</th><th>Typical units</th><th>Seen on</th></tr>
    <tr><td>Temperature</td><td>&deg;F, &deg;C, K</td><td>Space, supply, return, outdoor air; setpoints</td></tr>
    <tr><td>Humidity</td><td>% relative humidity (%RH)</td><td>Space and duct humidity sensors</td></tr>
    <tr><td>Pressure</td><td>in. w.c. (inches of water), Pa, kPa, psi</td><td>Duct static, filter, building pressure</td></tr>
    <tr><td>Air flow</td><td>cfm, L/s, m&sup3;/h</td><td>VAV boxes, air handlers</td></tr>
    <tr><td>Percentage</td><td>% (percent)</td><td>Damper and valve position, VFD speed, output level</td></tr>
    <tr><td>Power / energy</td><td>kW, W, kWh, A, V</td><td>Meters, VFDs</td></tr>
    <tr><td>Time</td><td>hours, minutes, seconds</td><td>Runtime, timers</td></tr>
    <tr><td>Count / none</td><td>no-units</td><td>Counters, ratios, dimensionless values</td></tr>
  </table>

  <div class="callout">
  <p><strong>&ldquo;no-units&rdquo; is normal.</strong> Plenty of legitimate points (counts,
  ratios, indexes) carry <code>no-units</code>. It does not mean the point is broken &mdash;
  just that the number is dimensionless.</p>
  </div>

  <h2>When the units look wrong</h2>
  <ul>
    <li><strong>A temperature that reads ~22 where you expected ~72.</strong> The sensor is
    almost certainly in &deg;C, not &deg;F. The value is right; only the scale differs.</li>
    <li><strong>Units say one thing, the number says another.</strong> Some integrators leave
    <code>Units</code> at a default and never set it, so a point can carry the wrong unit
    code while the value is fine. Trust the number and the point name over a suspicious unit,
    and flag it to whoever <a href="who-to-call-it-hvac-or-controls.html">programmed the
    system</a>.</li>
    <li><strong>Blank or &ldquo;no-units&rdquo; on an analog point.</strong> Common and
    usually harmless &mdash; see above.</li>
  </ul>

  <h2>Why it matters for a report</h2>
  <p>When you <a href="export-bacnet-points-to-csv.html">export a points list to Excel</a>, the
  units travel with each value, which is exactly what an integrator or vendor needs to make
  sense of the numbers. A column of readings without units is far less useful than one that
  says &ldquo;55.0&nbsp;&deg;F&rdquo;.</p>
""",
    related=[
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-multistate-values-explained", "BACnet binary and multi-state values explained"),
        ("guides/export-bacnet-points-to-csv", "Export BACnet points to Excel or CSV"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-status-flags-explained",
    title="BACnet Status_Flags explained | Easy BACnet",
    question="What do BACnet status flags (fault, alarm, overridden, out of service) mean?",
    description="Every BACnet object carries four status flags: In Alarm, Fault, Overridden and Out Of Service. What each means and when a value can't be trusted.",
    answer_html="""<p><strong>BACnet objects carry a <code>Status_Flags</code> property with
    four true/false flags: In Alarm, Fault, Overridden, and Out Of Service.</strong> They
    tell you whether a value can be trusted and why it might be behaving oddly. <em>Fault</em>
    means the reading is unreliable (a failed or shorted sensor). <em>Overridden</em> means
    something is forcing the point. <em>Out Of Service</em> means the point is decoupled from
    the real hardware. <em>In Alarm</em> means it has crossed an alarm limit. Easy BACnet
    surfaces these so a strange value comes with a reason.</p>""",
    body_html="""
  <h2>The four flags, one at a time</h2>

  <h3>Fault</h3>
  <p>The object cannot trust its own value &mdash; typically a sensor that is open-circuit,
  shorted, or out of its valid range. When Fault is set, treat <code>Present_Value</code> as
  meaningless: a temperature reading of &minus;40 or 300&nbsp;&deg;F with Fault set is the
  device telling you the sensor is dead, not that the room is on fire. This is the flag to
  check first when a number looks impossible.</p>

  <h3>Overridden</h3>
  <p>Something has forced the point away from its normal logic &mdash; often a hand/off/auto
  switch thrown to Hand at the equipment, or a physical override on the controller. When you
  see Overridden, the control system is not fully in charge of that point, which explains a
  value that <a href="bacnet-value-does-not-change-when-written.html">will not respond to a
  write</a>. Note this is a hardware/logic override and is distinct from a
  <a href="bacnet-priority-and-stuck-overrides.html">priority-array override</a>, though both
  leave a point stuck.</p>

  <h3>Out Of Service</h3>
  <p>The object has been deliberately disconnected from the real world. Its
  <code>Present_Value</code> no longer reflects the hardware and can be written freely for
  testing or commissioning. Very useful on purpose &mdash; and a nasty surprise if someone
  left it set, because the point will show whatever was forced into it, not reality.</p>

  <h3>In Alarm</h3>
  <p>The object has crossed an alarm limit defined in the control program (too hot, too cold,
  a pressure out of band). The reading itself may be perfectly valid &mdash; In Alarm is about
  the value being <em>out of range</em>, not about the sensor being broken.</p>

  <h2>Reading them in Easy BACnet</h2>
  <p>Open any point's detail and the status is shown alongside the value. A point that reads
  cleanly with no flags set is behaving normally. A flag that is set is a clue, not
  necessarily a failure &mdash; it tells you <em>why</em> the point looks the way it does.</p>

  <div class="callout">
  <p><strong>Rule of thumb.</strong> Before you believe a suspicious number, check the flags.
  <em>Fault</em> = don't trust the value. <em>Out Of Service</em> = the value is forced, not
  real. <em>Overridden</em> = the control system isn't driving it. <em>In Alarm</em> = the
  value is real but out of bounds.</p>
  </div>

  <h2>Status flags in an export</h2>
  <p>When you <a href="export-bacnet-points-to-csv.html">export a points list</a>, the
  Status column carries these flags for every point, and any row that is not
  <em>Normal</em> is shaded red. Sorting the spreadsheet by that column is a quick
  way to find every faulty sensor and every forced point on a site.</p>
""",
    related=[
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/bacnet-value-does-not-change-when-written", "I wrote a value but nothing changed"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/how-to-build-a-custom-remote", "How to build a custom remote"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-release-a-bacnet-override",
    title="How to release a BACnet override (relinquish) | Easy BACnet",
    question="How do I release a BACnet override and give control back to automatic?",
    description="Releasing a BACnet override means writing NULL to the priority slot you commanded so the control system takes back over. Step by step, and which slot.",
    answer_html="""<p><strong>To release a BACnet override you write NULL to the priority slot
    that is holding the point &mdash; you don't write a &ldquo;normal&rdquo; value back.</strong>
    Commanding a point parks a value in one of its 16 priority slots, and it stays there until
    that slot is cleared. In Easy BACnet, open the point and tap <em>Release</em> at the
    priority you used; the app writes NULL (relinquish) to that slot, and control falls to the
    next-highest slot &mdash; or to the relinquish default if none remain, which usually hands
    the point back to the automatic logic.</p>""",
    body_html="""
  <h2>Why writing a value back doesn't work</h2>
  <p>A commandable BACnet point has a 16-slot
  <a href="bacnet-priority-and-stuck-overrides.html">priority array</a>. When you command it,
  your value sits in a slot (slot 8 by default for manual operators). If you later write a
  different value at the same slot, you have only changed the override &mdash; the point is
  still overridden. To truly let go, you clear the slot by writing <strong>NULL</strong>. That
  is called relinquishing, or releasing. Only then does the point fall through to whatever is
  below: another operator's command at a lower priority, or the
  <strong>relinquish default</strong> &mdash; the value the object rests at when every slot is
  empty.</p>

  <h2>Release a point, step by step</h2>
  <ol>
    <li><strong>Open the point.</strong> <strong>Commanded At</strong> shows the priority
    currently in command and the value held there; <strong>Falls Back To</strong> shows
    the relinquish default.</li>
    <li><strong>Identify the slot you own.</strong> If you commanded it earlier, that is
    your slot, usually 8. If Commanded At shows a lower number than yours, someone else's
    override is on top; releasing yours will not change the value (see below).</li>
    <li><strong>Tap Release to Auto</strong>, check the priority it will clear and what the
    point will fall back to, then tap <strong>Release it</strong>. The app writes NULL to
    that slot.</li>
    <li><strong>Read it back.</strong> Commanded At should now show the next occupied
    priority, or <em>Not commanded</em> if the point is back on its program.</li>
  </ol>

  <div class="callout">
  <p><strong>Release the slot you commanded, not someone else's.</strong> If a point is held
  at priority 1 or 2 by the control system (life-safety, minimum on/off), clearing your
  priority-8 slot will not change the value, because a higher slot still wins. That is correct
  behaviour, not a bug.</p>
  </div>

  <h2>&ldquo;I released it but it didn't change&rdquo;</h2>
  <ul>
    <li><strong>A higher slot still holds it.</strong> Something at a lower priority number is
    commanding. Check the whole array &mdash; you can only release what you put there.</li>
    <li><strong>The point is <a href="bacnet-status-flags-explained.html">Overridden or Out Of
    Service</a> at the hardware.</strong> A physical hand/off/auto switch or an Out Of Service
    flag beats anything you write over the network. That's a
    <a href="who-to-call-it-hvac-or-controls.html">controls or mechanical</a> visit.</li>
    <li><strong>The relinquish default <em>is</em> the value you're seeing.</strong> If the
    automatic value and your override value happen to match, releasing looks like nothing
    happened &mdash; but control has still returned to auto.</li>
  </ul>

  <h2>Good practice</h2>
  <p>If you commanded something to test it, release it before you leave &mdash; a slot left set
  is exactly how points get <a href="bacnet-priority-and-stuck-overrides.html">stuck in
  override</a> for the next person. Easy BACnet also resets write mode to off on every launch,
  so you never leave the app armed by accident, but that does not clear a command you already
  sent to a device: only a release does that.</p>
""",
    related=[
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/how-to-write-to-a-bacnet-point", "How to write to a BACnet point"),
        ("guides/is-it-safe-to-write-to-bacnet", "Is it safe to write to a BACnet point?"),
        ("guides/bacnet-status-flags-explained", "BACnet status flags explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-add-device-by-ip",
    title="Add a BACnet device by IP address | Easy BACnet",
    question="A device won't show up in a scan &mdash; can I add it by IP address?",
    description="When a BACnet scan can't reach a device (another subnet, blocked broadcasts, no BBMD) you can add it directly by IP address. How, and what to check.",
    answer_html="""<p><strong>Yes &mdash; if a device won't answer a broadcast scan but you know
    its IP address, you can reach it with a directed message instead of a broadcast.</strong>
    Discovery normally works by broadcasting <a href="who-is-i-am-explained.html">Who-Is</a>,
    and broadcasts don't cross routers without a <a href="what-is-a-bbmd.html">BBMD</a>. A
    directed read sent straight to the device's IP sidesteps that, so a controller on another
    subnet &mdash; or one behind a switch that swallows broadcast &mdash; can still be read once
    you know where it lives.</p>""",
    body_html="""
  <h2>When you'd add a device by IP</h2>
  <p>Broadcast discovery is the easy path, but it has limits. Add a device directly when:</p>
  <ul>
    <li>The device is on a <strong>different <a href="subnets.html">subnet</a></strong> and
    there's no <a href="what-is-a-bbmd.html">BBMD</a> forwarding broadcasts.</li>
    <li>The network <strong>blocks or drops broadcast</strong> traffic (some managed switches
    and Wi-Fi setups do), even though unicast to the device works fine.</li>
    <li>You <strong>only need one known controller</strong> and don't want to scan a large
    or sensitive network.</li>
    <li>A scan finds everything <em>except</em> one device whose IP you already have.</li>
  </ul>

  <h2>What you need first</h2>
  <ul>
    <li><strong>The device's IP address.</strong> From the integrator, a label on the panel,
    the DHCP/router table, or a prior scan. This is the one thing a directed read can't guess.</li>
    <li><strong>A route to it.</strong> Your phone must be able to reach that IP &mdash; same
    network, or a network that routes to it. Directed BACnet still travels over
    <a href="what-port-does-bacnet-use.html">UDP 47808</a>, so that port must be open along
    the path.</li>
    <li><strong>Its port, if non-standard.</strong> Most devices use 47808; some sites use
    47809 or higher.</li>
  </ul>

  <h2>How to do it in Easy BACnet</h2>
  <ol>
    <li>Open <strong>Easy BACnet Mode</strong> and tap the menu (three dots, top right) &rarr;
    <strong>Add device by IP&hellip;</strong> (in <strong>Browser Mode</strong> it is a button
    under <em>Scan the network</em>). Wait for any running scan to finish first.</li>
    <li>In <em>Add a device by IP address</em>, type the <strong>IP address or host name</strong>
    (e.g. 192.168.1.50) and the <strong>UDP port</strong> &mdash; leave 47808 unless the site uses
    another.</li>
    <li>Tap <strong>Add</strong>. The app sends a directed Who-Is and a direct read to that
    address (<em>Contacting&hellip;</em>). A router at that address can answer for several
    MS/TP devices behind it, so you may see <em>Added 3 device(s)</em>.</li>
    <li>The device joins your results like any scanned device: open its points, write, export
    it, or build a <a href="how-to-build-a-custom-remote.html">custom remote</a> or
    <a href="how-to-build-a-control-panel.html">control panel</a> for it.</li>
  </ol>
  <p>If nothing answers you get <em>No BACnet IP device answered at &hellip;</em> &mdash; check the
  address and port, and that the phone can reach that network at all (the steps below).</p>

  <h2>Seeing a whole remote subnet: use a BBMD</h2>
  <p>If the site has a <a href="what-is-a-bbmd.html">BBMD</a>, menu &rarr; <strong>BBMD for remote
  networks&hellip;</strong> lets you enter its <strong>BBMD IP address</strong> (and port) and tap
  <strong>Save</strong>. Every scan then registers the phone as a foreign device with the BBMD
  and broadcasts through it, so devices on the subnets it serves are discovered too.
  <strong>Clear</strong> goes back to scanning the local network only. If the BBMD refuses the
  registration or does not answer, the scan result says so.</p>

  <div class="callout">
  <p><strong>A directed add is not a BBMD.</strong> Reaching one device by IP does not make the
  rest of a remote subnet discoverable. If you need to see a whole remote network, that's a
  <a href="what-is-a-bbmd.html">BBMD</a> conversation with whoever runs the controls network.</p>
  </div>

  <h2>If a directed read still fails</h2>
  <ol>
    <li><strong>Check the address and port.</strong> A typo, or a device on 47809 that
    you asked for on 47808, gets no answer.</li>
    <li><strong>Confirm the IP is current.</strong> A DHCP lease can move; the address you
    were given may now belong to something else, or to nothing.</li>
    <li><strong>Ping it</strong> from a laptop on the same network. No reply means the
    network path is the problem, not BACnet. See
    <a href="is-my-bacnet-device-online-ping-test.html">is my BACnet device online?</a></li>
    <li><strong>Ask about firewalls and access lists.</strong> If it pings but will not
    answer BACnet, something between you and the device is blocking UDP 47808. That is
    an <a href="who-to-call-it-hvac-or-controls.html">IT / network</a> question.</li>
  </ol>

  <p>For the broader &ldquo;nothing shows up&rdquo; case, start with
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP devices</a>.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
        ("guides/is-my-bacnet-device-online-ping-test", "Is my BACnet device online? Ping test"),
        ("guides/subnets", "What is a subnet?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-add-object-by-number",
    title="Add a BACnet object by number | Easy BACnet",
    question="A point is missing from the list &mdash; can I add an object by number?",
    description="Easy BACnet loads the first 2,000 objects on a huge controller. Reach any object beyond that directly by its object type and instance number. Here's how.",
    answer_html="""<p><strong>Yes &mdash; if a point isn't in the enumerated list, you can add it
    directly by its object type and instance number.</strong> Reading a device's full
    <a href="what-is-a-bacnet-points-list.html">Object_List</a> costs roughly two reads per
    object, so on a very large controller Easy BACnet caps automatic enumeration (and marks the
    device truncated) to keep the app fast and gentle on cheap gateways. Anything beyond that
    cap is still reachable: tell the app exactly which object you want &mdash; say Analog Value
    3001 &mdash; and it reads that one directly.</p>""",
    body_html="""
  <h2>Why a device might be truncated</h2>
  <p>Some controllers expose thousands of objects. Enumerating all of them means reading the
  Object_List and then querying each object's value, units and status &mdash; a lot of small
  requests, and slow going over a busy network or a low-cost router. To stay responsive, Easy
  BACnet stops automatic enumeration after a large number of objects and flags the device as
  truncated, rather than grinding for minutes &mdash; the cap is the first 2,000 objects, and
  the list says <em>Showing the first 2000 of N objects</em>. The points it did read work
  normally; you just
  haven't loaded <em>every</em> object.</p>

  <h2>Add the object you want</h2>
  <ol>
    <li><strong>Know the object's type and instance.</strong> For example Analog Value 3001,
    Binary Output 12, Multi-state Value 40. The integrator's points list, a graphic, or a
    prior export will have these.</li>
    <li><strong>Open the device</strong> from <strong>View Results</strong>, tap the menu (three
    dots) and choose <strong>Add object by number</strong>. Pick the object type from the list
    (Analog Input, Analog Output, Analog Value, Binary Input/Output/Value, Multi-state
    Input/Output/Value), type the <strong>Instance number</strong>, and tap
    <strong>Add</strong>. If the device has no such object you are told so.</li>
    <li><strong>The app reads that object directly</strong> &mdash; no full enumeration needed
    &mdash; and adds it to the list with its live value, units and status, just like any other
    point. You can then read it, command it, or put it on a
    <a href="how-to-build-a-custom-remote.html">custom remote</a>.</li>
  </ol>

  <div class="callout">
  <p><strong>You don't have to load everything.</strong> On a big plant controller you usually
  care about a handful of points. Adding those few by number is faster and cleaner than waiting
  for thousands to enumerate.</p>
  </div>

  <h2>Not sure of the exact number?</h2>
  <ul>
    <li><strong>Ask for the points list.</strong> Whoever <a href="who-to-call-it-hvac-or-controls.html">programmed
    the controller</a> can give you the object type and instance for the point you need &mdash;
    this is the fastest route.</li>
    <li><strong>Check an existing export.</strong> If you've already
    <a href="export-bacnet-points-to-csv.html">exported this device's points</a> before it was
    truncated, the object types and numbers are in the spreadsheet.</li>
    <li><strong>Decode an Object Identifier.</strong> If all you have is a single 32-bit
    Object Identifier number, our <a href="../bacnet-object-id-decoder.html">Object Identifier
    decoder</a> splits it into type and instance.</li>
  </ul>

  <p>If instead the whole device is missing rather than one point, that's a discovery problem
  &mdash; see <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP
  devices</a> or <a href="bacnet-add-device-by-ip.html">add a device by IP</a>.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/cant-find-what-im-looking-for", "The app can't find what I'm looking for"),
        ("guides/bacnet-add-device-by-ip", "Add a BACnet device by IP"),
    ],
))

GUIDES.append(dict(
    slug="guides/duplicate-bacnet-device-id",
    title="Duplicate BACnet Device ID: how to fix it | Easy BACnet",
    question="Two devices have the same BACnet Device ID &mdash; what do I do?",
    description="A BACnet Device ID must be unique network-wide. When two devices share one they flicker in scans and return wrong data. How to spot and fix a duplicate.",
    answer_html="""<p><strong>A BACnet Device ID must be unique across the entire BACnet
    network, and when two devices share one, both misbehave.</strong> You'll see a device that
    flickers in and out of scans, readings that seem to come from the &ldquo;wrong&rdquo; unit,
    or intermittent comms errors &mdash; because a <a href="who-is-i-am-explained.html">Who-Is</a>
    for that ID gets two answers. The fix is to change one of the two devices to an unused
    Device ID, which is a job for whoever <a href="who-to-call-it-hvac-or-controls.html">programmed
    the controllers</a>. Easy BACnet helps you catch it.</p>""",
    body_html="""
  <h2>Why duplicates break things</h2>
  <p>The <a href="bacnet-device-id-explained.html">Device ID</a> (also called the device
  instance) is how BACnet names a device uniquely &mdash; not its IP address, its Device ID.
  Discovery and every addressed message rely on that number being one-of-a-kind. When two
  devices claim the same ID:</p>
  <ul>
    <li>A <strong>Who-Is</strong> for that ID gets <strong>two I-Am replies</strong>, and tools
    can't agree which device is which.</li>
    <li>A device may <strong>appear and disappear</strong> between scans, or its IP/name seems
    to change, because you're really seeing two different units under one identity.</li>
    <li>Reads can return <strong>data from the wrong equipment</strong>, and writes can land on
    the wrong controller &mdash; which is exactly why you don't want to command anything until
    it's resolved.</li>
  </ul>

  <h2>How to spot one with Easy BACnet</h2>
  <ul>
    <li><strong>Scan more than once.</strong> A device whose <strong>name or IP changes</strong>
    between otherwise identical scans, while the Device ID stays the same, is a classic
    duplicate signature.</li>
    <li><strong>Watch for a device that won't hold still</strong> &mdash; present in one scan,
    gone the next, back again &mdash; especially on a network you know is stable.</li>
    <li><strong>Compare the names.</strong> If a single Device ID sometimes reads as
    &ldquo;AHU-1&rdquo; and sometimes &ldquo;AHU-2&rdquo;, that's two devices, one ID.</li>
  </ul>

  <div class="callout">
  <p><strong>Don't command a point while a duplicate ID is live.</strong> A write addressed to
  the shared ID can reach whichever device answers first &mdash; possibly not the one you're
  looking at. Sort the ID out before you override anything.</p>
  </div>

  <h2>How it gets fixed</h2>
  <p>The cure is to give one of the two devices a new, unused Device ID. That is a
  <strong>controls / BMS</strong> task &mdash; done in the controller's own configuration by the
  integrator, not something a browsing tool changes for you. Duplicates most often appear when a
  device is swapped or added and left at a <strong>factory-default ID</strong> (many ship with
  the same default), or when two panels are copied from one template without renumbering.</p>

  <h2>What to hand the integrator</h2>
  <p>Give them the shared Device ID, both IP addresses you saw it flip between, and both names.
  The fastest way is to <a href="export-bacnet-points-to-csv.html">export the scan</a> across a
  couple of runs so they can see the ID resolving to two different addresses. See
  <a href="vendor-asking-for-bacnet-information.html">what to send when a vendor asks for your
  BACnet information</a>.</p>
""",
    related=[
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/is-it-safe-to-write-to-bacnet",
    title="Is it safe to write to a BACnet point? | Easy BACnet",
    question="Is it safe to write to a BACnet point?",
    description="Reading BACnet is completely safe. Writing is real control of live equipment: safe when you understand priority and release, risky if you command blindly.",
    answer_html="""<p><strong>Reading is completely safe; writing is real control of live
    equipment, so treat it with respect.</strong> A BACnet write commands actual hardware &mdash;
    a fan, a valve, a setpoint &mdash; and the value <em>holds</em> until it is
    <a href="how-to-release-a-bacnet-override.html">released</a>. Done knowingly &mdash; the
    right point, a sensible <a href="bacnet-priority-and-stuck-overrides.html">priority</a>, and
    a release afterwards &mdash; it is a normal, safe part of the job. Done blindly on a system
    you don't understand, it can disrupt comfort, waste energy, or trip equipment. Easy BACnet
    keeps write mode off by default so you never command anything by accident.</p>""",
    body_html="""
  <h2>Reading is safe. Always.</h2>
  <p>Scanning, browsing points, reading values, checking status and
  <a href="export-bacnet-points-to-csv.html">exporting a spreadsheet</a> only <em>ask</em> devices
  for information. Nothing you read changes anything. You can explore a live building's BACnet
  network all day without touching its operation. If all you need is to see what's there and
  what it's doing, there is zero risk.</p>

  <h2>What a write actually does</h2>
  <p>A write commands a real point. If you set a fan command On, the fan runs. If you set a
  damper to 100%, it opens. Crucially, the command <strong>persists</strong>: it sits in the
  point's <a href="bacnet-priority-and-stuck-overrides.html">priority array</a> and stays there
  until someone clears it. That's the whole point of BACnet commanding &mdash; but it's also why
  a forgotten override is the most common way people cause trouble. The equipment does exactly
  what you told it, indefinitely, until it's released.</p>

  <div class="callout">
  <p><strong>The golden rule:</strong> if you command something, <a href="how-to-release-a-bacnet-override.html">release
  it</a> when you're done. A point left overridden is how the next person inherits a &ldquo;stuck&rdquo;
  unit.</p>
  </div>

  <h2>How to write responsibly</h2>
  <ul>
    <li><strong>Know the point.</strong> Confirm the name, type and current value before you
    command. Writing to the wrong Analog Value because two look alike is an avoidable mistake.</li>
    <li><strong>Use a sensible priority.</strong> Manual operators typically command at
    <strong>priority 8</strong> &mdash; high enough to take manual control, low enough that
    safeties and critical logic at priorities 1&ndash;2 still win. Don't reach for priority 1
    unless you know exactly why.</li>
    <li><strong>Change one thing at a time</strong> and watch the result, rather than commanding
    several points at once.</li>
    <li><strong>Release when finished</strong>, and read the point back to confirm control
    returned to automatic.</li>
    <li><strong>Get permission on someone else's system.</strong> On an occupied or critical
    building, commanding a point is an operational change &mdash; clear it with whoever
    <a href="who-to-call-it-hvac-or-controls.html">runs the controls</a> first.</li>
  </ul>

  <h2>Where it can go wrong</h2>
  <ul>
    <li><strong>Comfort and process.</strong> Overriding a setpoint or a fan in an occupied
    space, a lab, a grow room or a data hall has immediate real-world effects.</li>
    <li><strong>Energy and equipment.</strong> Forcing a valve or damper against the sequence
    can waste energy or, in the worst case, contribute to freezing a coil or short-cycling a
    compressor.</li>
    <li><strong>The forgotten override.</strong> The value itself was fine &mdash; it was leaving
    it commanded that caused weeks of a unit &ldquo;not working right.&rdquo;</li>
  </ul>

  <h2>The safety rails Easy BACnet gives you</h2>
  <p>Write mode is <strong>off by default and resets to off every time you launch the app</strong>,
  so you can't command anything without deliberately turning writing on. You choose the priority
  explicitly, the app reads the priority array back so you can see the effect, and
  <a href="how-to-release-a-bacnet-override.html">Release</a> is one tap away. The guard rails
  are there; the judgement is still yours.</p>
""",
    related=[
        ("guides/how-to-write-to-a-bacnet-point", "How to write to a BACnet point"),
        ("guides/how-to-release-a-bacnet-override", "How to release a BACnet override"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-multistate-values-explained",
    title="BACnet binary and multi-state values explained | Easy BACnet",
    question="What do BACnet binary and multi-state values mean?",
    description="Not every BACnet point is a number. Binary points are Off/On; multi-state points pick from a list (1=Off, 2=Low, 3=High). How to read and write them.",
    answer_html="""<p><strong>Binary and multi-state points don't carry a measured number &mdash;
    they carry a <em>state</em>.</strong> A binary point is one of two states (typically Off/On
    or Inactive/Active). A multi-state point picks one option from a numbered list &mdash; for a
    fan that might be 1&nbsp;=&nbsp;Off, 2&nbsp;=&nbsp;Low, 3&nbsp;=&nbsp;High. The value you read
    is the state number; the meaning comes from the list of states, not from
    <a href="bacnet-engineering-units-explained.html">engineering units</a>. Easy BACnet shows
    and lets you command these by their state.</p>""",
    body_html="""
  <h2>Three families of point</h2>
  <p>It helps to see where binary and multi-state sit alongside the analog points you've
  probably met already:</p>
  <table>
    <tr><th>Family</th><th>Value looks like</th><th>Example</th></tr>
    <tr><td>Analog</td><td>A number with <a href="bacnet-engineering-units-explained.html">units</a></td><td>72.4 &deg;F, 45% RH, 1200 cfm</td></tr>
    <tr><td>Binary</td><td>One of two states</td><td>Fan command: Off / On</td></tr>
    <tr><td>Multi-state</td><td>One of a numbered list</td><td>Fan speed: 1 Off, 2 Low, 3 Med, 4 High</td></tr>
  </table>

  <h2>Binary points</h2>
  <p>A binary object (Binary Input, Binary Output, Binary Value) is on or off &mdash; internally
  0 or 1, shown as Inactive/Active or Off/On. Inputs report a state (a status switch, a proof
  contact); outputs and values can be commanded. Because it's just two states, commanding one is
  simply choosing which. Bear in mind the state names are set by the integrator, so
  &ldquo;Active&rdquo; might mean &ldquo;running,&rdquo; &ldquo;occupied,&rdquo; or
  &ldquo;alarm&rdquo; depending on the point &mdash; read the point name, not just the state.</p>

  <h2>Multi-state points</h2>
  <p>A multi-state object (Multi-state Input, Output, or Value) holds one value from a numbered
  list. The catch that trips people up: <strong>BACnet multi-state values start at 1, not 0</strong>.
  State 1 is the first option, state 2 the second, and so on. So a fan speed of &ldquo;3&rdquo;
  means the third option in that point's list &mdash; which you have to look at to know is
  &ldquo;High.&rdquo; Where the device provides them, Easy BACnet shows the state text so you're
  choosing &ldquo;High,&rdquo; not memorising that High is number 3.</p>

  <div class="callout">
  <p><strong>Read the number as an index, not a measurement.</strong> A multi-state value of 2
  is &ldquo;the second option,&rdquo; not &ldquo;2 of something.&rdquo; The meaning lives in the
  point's list of states.</p>
  </div>

  <h2>Commanding them</h2>
  <p>Commandable binary and multi-state points obey the same
  <a href="bacnet-priority-and-stuck-overrides.html">priority array</a> as analog points: you
  command a state at a chosen priority, it holds, and you
  <a href="how-to-release-a-bacnet-override.html">release</a> it to hand control back. The only
  difference is that you're picking a state (On, or &ldquo;High&rdquo;) rather than typing a
  number with units. Everything in <a href="is-it-safe-to-write-to-bacnet.html">writing
  responsibly</a> still applies.</p>

  <h2>On a custom remote</h2>
  <p>Binary points map naturally to a toggle or button, and multi-state points to a small set of
  buttons or a picker &mdash; which is exactly what the
  <a href="how-to-build-a-custom-remote.html">custom remote builder</a> gives you: a real
  On/Off switch or a Low/Med/High selector for the equipment you touch most.</p>
""",
    related=[
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/bacnet-engineering-units-explained", "BACnet engineering units explained"),
        ("guides/how-to-write-to-a-bacnet-point", "How to write to a BACnet point"),
        ("guides/how-to-build-a-custom-remote", "How to build a custom remote"),
    ],
))

# Homepage grouping. Slugs are relative to guides/. Order within a group is the
# order a reader would want them; a guide missing from every group lands in "More".
GUIDE_GROUPS = [
    ("Start here", [
        "what-is-bacnet",
        "bacnet-glossary",
        "what-is-a-bacnet-points-list",
        "bacnet-scanner-app-android",
        "best-free-bacnet-explorer",
        "bacnet-vs-modbus",
    ]),
    ("Reading and exporting", [
        "how-to-use-easy-bacnet",
        "read-bacnet-values-from-phone",
        "how-to-find-your-bacnet-points-list",
        "export-bacnet-points-to-csv",
        "vendor-asking-for-bacnet-information",
        "bacnet-add-object-by-number",
        "test-bacnet-device-without-bms",
    ]),
    ("When a scan finds nothing", [
        "cant-find-what-im-looking-for",
        "why-cant-i-find-my-bacnet-devices",
        "subnets",
        "is-my-bacnet-device-online-ping-test",
        "bacnet-device-shows-offline",
        "bacnet-add-device-by-ip",
        "what-is-a-bbmd",
        "duplicate-bacnet-device-id",
        "does-easy-bacnet-support-mstp-rs485",
        "who-to-call-it-hvac-or-controls",
    ]),
    ("Writing and overrides", [
        "is-it-safe-to-write-to-bacnet",
        "how-to-write-to-a-bacnet-point",
        "how-to-release-a-bacnet-override",
        "bacnet-priority-and-stuck-overrides",
        "bacnet-value-does-not-change-when-written",
        "bacnet-write-access-denied",
    ]),
    ("Custom remotes and control panels", [
        "how-to-build-a-custom-remote",
        "how-to-build-a-control-panel",
    ]),
    ("BACnet reference", [
        "bacnet-object-types-explained",
        "bacnet-device-id-explained",
        "bacnet-engineering-units-explained",
        "bacnet-status-flags-explained",
        "bacnet-multistate-values-explained",
        "who-is-i-am-explained",
        "what-port-does-bacnet-use",
        "bacnet-mstp-vs-bacnet-ip",
    ]),
]

# ---------------------------------------------------------------------------
# Free interactive tools (link magnets; generated, schema-marked)
# ---------------------------------------------------------------------------

TOOLS = []

TOOL_CSS_EXTRA = """
  .tool { background:var(--box); border:1px solid var(--line); border-radius:14px;
          padding:1.3rem 1.4rem; margin:1.75rem 0; }
  .tool label { display:block; font-family:"IBM Plex Mono",ui-monospace,monospace;
                font-size:.72rem; text-transform:uppercase; letter-spacing:.12em;
                color:var(--accent); margin:.9rem 0 .3rem; }
  .tool input, .tool select { width:100%; padding:.6rem .7rem; font-size:1rem;
                font-family:"IBM Plex Mono",ui-monospace,monospace; color:var(--fg);
                background:var(--code); border:1px solid var(--line); border-radius:8px; }
  .tool .row { display:flex; gap:1rem; flex-wrap:wrap; }
  .tool .row > div { flex:1 1 160px; }
  .tool button { margin-top:1.1rem; padding:.6rem 1.2rem; font-family:"Archivo",sans-serif;
                font-weight:700; text-transform:uppercase; letter-spacing:.03em; font-size:.85rem;
                color:var(--ink); background:var(--accent); border:none; border-radius:8px;
                cursor:pointer; }
  .tool table { margin:1.3rem 0 0; }
  .tool .out-note { color:var(--muted); font-size:.85rem; margin-top:.8rem; }
  .tool hr { border:none; border-top:1px solid var(--line); margin:1.8rem 0; }
"""


def tool_page(slug, title, question, description, intro_html, tool_html, related):
    """A standalone interactive tool page, rendered with .replace() so JavaScript in
    tool_html is safe. Carries SoftwareApplication + BreadcrumbList JSON-LD."""
    rel = ""
    if related:
        items = "\n".join(
            '      <li><a href="%s.html">%s</a></li>' % (r[0], r[1]) for r in related
        )
        rel = ('\n  <nav class="more">\n    <h2>Related</h2>\n    <ul>\n' + items +
               '\n    </ul>\n  </nav>')
    jsonld = ('{"@context":"https://schema.org","@graph":['
              '{"@type":"SoftwareApplication","name":' + jstr(question) +
              ',"applicationCategory":"UtilitiesApplication","operatingSystem":"Any (web browser)"'
              ',"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}'
              ',"description":' + jstr(description) + '},'
              '{"@type":"BreadcrumbList","itemListElement":['
              '{"@type":"ListItem","position":1,"name":"Home","item":"' + BASE_URL + '/index.html"},'
              '{"@type":"ListItem","position":2,"name":' + jstr(question) +
              ',"item":"' + BASE_URL + '/' + slug + '.html"}]}]}')
    return (TOOL_TEMPLATE
            .replace("{{TITLE}}", title)
            .replace("{{DESC}}", description)
            .replace("{{BASE}}", BASE_URL)
            .replace("{{SLUG}}", slug)
            .replace("{{CSS}}", CSS + TOOL_CSS_EXTRA)
            .replace("{{JSONLD}}", jsonld)
            .replace("{{H1}}", question)
            .replace("{{UPDATED}}", UPDATED_HUMAN)
            .replace("{{INTRO}}", intro_html)
            .replace("{{TOOL}}", tool_html)
            .replace("{{REL}}", rel))


TOOL_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<link rel="canonical" href="{{BASE}}/{{SLUG}}.html">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#14171a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Easy BACnet">
<meta property="og:title" content="{{TITLE}}">
<meta property="og:description" content="{{DESC}}">
<meta property="og:url" content="{{BASE}}/{{SLUG}}.html">
<meta property="og:image" content="{{BASE}}/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{TITLE}}">
<meta name="twitter:description" content="{{DESC}}">
<meta name="twitter:image" content="{{BASE}}/img/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800;900&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>{{CSS}}</style>
<script type="application/ld+json">
{{JSONLD}}
</script>
</head>
<body>

<header class="site">
  <a href="index.html" style="display:inline-flex;align-items:center;gap:.5rem;text-decoration:none"><img src="icon.svg" alt="" width="26" height="26" style="border-radius:6px"><span>Easy BACnet</span></a>
  <span class="muted">&middot; free BACnet tools</span>
</header>

<article>
  <h1>{{H1}}</h1>
  <p class="updated">Free browser tool &middot; nothing is uploaded &middot; updated {{UPDATED}}</p>
  {{INTRO}}
  {{TOOL}}
</article>{{REL}}

<footer>
  <p>Published alongside <a href="index.html">Easy BACnet</a>, a free Android app that
  scans a building network for BACnet IP devices, reads and commands their points, and
  exports an Excel (.xlsx) report. This tool runs entirely in your browser.</p>
  <p><a href="terms.html">Terms of use</a> &middot; <a href="privacy.html">Privacy policy</a></p>
</footer>

</body>
</html>
"""

TOOLS.append(dict(
    slug="bacnet-object-id-decoder",
    title="BACnet Object Identifier decoder | Easy BACnet",
    question="BACnet Object Identifier decoder",
    description="Encode or decode a BACnet Object Identifier: object type and instance to the 32-bit number and back. Free browser tool.",
    intro_html="""<p>A BACnet Object Identifier packs an <strong>object type</strong> and
    an <strong>instance number</strong> into a single 32-bit value &mdash; the top 10
    bits are the type, the bottom 22 bits are the instance. This tool goes both ways:
    pick a type and instance to get the encoded number, or paste a raw Object Identifier
    to see what it means. Background: <a href="guides/what-is-a-bacnet-points-list.html">what
    is a BACnet IP points list?</a> and <a href="guides/bacnet-object-types-explained.html">BACnet
    object types explained</a>.</p>""",
    tool_html="""
  <div class="tool">
    <strong style="font-family:'Archivo',sans-serif">Encode &mdash; type + instance to number</strong>
    <div class="row">
      <div><label for="otype">Object type</label><select id="otype"></select></div>
      <div><label for="oinst">Instance (0&ndash;4194303)</label><input id="oinst" value="7" inputmode="numeric"></div>
    </div>
    <button onclick="encId()">Encode</button>
    <table id="eout" style="display:none"><tbody id="ebody"></tbody></table>
    <p class="out-note" id="enote"></p>
    <hr>
    <strong style="font-family:'Archivo',sans-serif">Decode &mdash; number to type + instance</strong>
    <label for="oraw">Object Identifier (decimal or 0x hex)</label>
    <input id="oraw" value="8388615" inputmode="text">
    <button onclick="decId()">Decode</button>
    <table id="dout" style="display:none"><tbody id="dbody"></tbody></table>
    <p class="out-note" id="dnote"></p>
  </div>
<script>
var OT={0:'Analog Input',1:'Analog Output',2:'Analog Value',3:'Binary Input',
4:'Binary Output',5:'Binary Value',6:'Calendar',7:'Command',8:'Device',
9:'Event Enrollment',10:'File',11:'Group',12:'Loop',13:'Multi-state Input',
14:'Multi-state Output',15:'Notification Class',16:'Program',17:'Schedule',
18:'Averaging',19:'Multi-state Value',20:'Trend Log',21:'Life Safety Point',
22:'Life Safety Zone',23:'Accumulator',24:'Pulse Converter',25:'Event Log',
27:'Trend Log Multiple',28:'Load Control',29:'Structured View',30:'Access Door',
36:'Access User',39:'BitString Value',40:'CharacterString Value',
45:'Integer Value',46:'Large Analog Value',49:'Positive Integer Value',
56:'Network Port'};
var MAXI=4194303;
function tname(t){return OT[t]?OT[t]:'Type '+t+' (proprietary or less common)';}
function row(k,v){return '<tr><th>'+k+'</th><td>'+v+'</td></tr>';}
(function(){var s=document.getElementById('otype');var keys=Object.keys(OT).map(Number).sort(function(a,b){return a-b;});
for(var i=0;i<keys.length;i++){var o=document.createElement('option');o.value=keys[i];o.textContent=keys[i]+' — '+OT[keys[i]];if(keys[i]===0){o.selected=true;}s.appendChild(o);}})();
function encId(){
  var t=parseInt(document.getElementById('otype').value,10);
  var inst=parseInt((document.getElementById('oinst').value||'').trim(),10);
  var note=document.getElementById('enote');var out=document.getElementById('eout');
  if(isNaN(inst)||inst<0||inst>MAXI){note.textContent='Instance must be between 0 and 4194303.';out.style.display='none';return;}
  var id=t*4194304+inst;
  document.getElementById('ebody').innerHTML=
    row('Object',tname(t)+', instance '+inst)
    +row('Object Identifier (decimal)',id)
    +row('Object Identifier (hex)','0x'+id.toString(16).toUpperCase())
    +row('How it splits','type '+t+' &laquo; 22  |  instance '+inst);
  out.style.display='';note.textContent='';
}
function decId(){
  var s=(document.getElementById('oraw').value||'').trim().toLowerCase();
  var note=document.getElementById('dnote');var out=document.getElementById('dout');
  var n;
  if(s.indexOf('0x')===0){n=parseInt(s.slice(2),16);}else{n=parseInt(s,10);}
  if(isNaN(n)||n<0||n>4294967295){note.textContent='Enter a number between 0 and 4294967295 (0xFFFFFFFF).';out.style.display='none';return;}
  var t=Math.floor(n/4194304);var inst=n-t*4194304;
  var extra=(t===1023&&inst===MAXI)?' &mdash; this is the &ldquo;uninitialized&rdquo; value':'';
  document.getElementById('dbody').innerHTML=
    row('Object type',t+' &mdash; '+tname(t))
    +row('Instance number',inst+extra)
    +row('Reads as',tname(t)+', instance '+inst);
  out.style.display='';note.textContent='';
}
window.addEventListener('DOMContentLoaded',function(){encId();decId();});
</script>
""",
    related=[
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
        ("guides/bacnet-scanner-app-android", "Is there a BACnet IP scanner app for Android?"),
    ],
))

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>Easy BACnet &mdash; scan, read &amp; control BACnet/IP devices</title>
<meta name="description" content="Free Android app to scan a network for BACnet IP devices, read and command points by priority, build custom remotes, and export an Excel report.">
<link rel="canonical" href="{{BASE}}/index.html">
<meta name="robots" content="index, follow">
<meta name="google-site-verification" content="5mp_Qm6jQXeHC7IbyiRUwPt3te2kFjKv67pCaqqLAhQ">
<meta name="google-site-verification" content="rbS8niGRuwenITXwh4zN0Ak8BX8jyhI73wGn0c0yW-k">
<meta name="theme-color" content="#14171a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Easy BACnet">
<meta property="og:title" content="Easy BACnet &mdash; scan, read &amp; control BACnet/IP devices">
<meta property="og:description" content="Free Android app to scan a network for BACnet IP devices, read and command points by priority, build custom remotes, and export an Excel report.">
<meta property="og:url" content="{{BASE}}/index.html">
<meta property="og:image" content="{{BASE}}/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Easy BACnet &mdash; scan, read &amp; control BACnet/IP devices">
<meta name="twitter:description" content="Free Android app to scan a network for BACnet IP devices, read and command points by priority, build custom remotes, and export an Excel report.">
<meta name="twitter:image" content="{{BASE}}/img/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800;900&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#14171a; --panel:#1d2227; --panel2:#191e22; --line:#2f363d;
  --fg:#f3f5f6; --mut:#9aa4ad; --accent:#ff9a1f; --ink:#0d0f11;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--fg);
  font-family:"Manrope",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  font-size:17px; line-height:1.65; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1080px; margin:0 auto; padding:0 16px}
a{color:var(--accent); text-decoration:none}
a:hover{text-decoration:underline}
.eyebrow{
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-weight:600;
  font-size:.74rem; letter-spacing:.22em; text-transform:uppercase;
  color:var(--accent); margin:0 0 1rem;
}
h1,h2,h3{font-family:"Archivo",sans-serif; letter-spacing:-.01em; line-height:1.05}
h1{font-weight:900; text-transform:uppercase; font-size:clamp(2.1rem,6vw,4rem); margin:0 0 1.25rem}
h1 span{color:var(--accent)}
h2{font-weight:800; text-transform:uppercase; font-size:clamp(1.4rem,3.2vw,2rem); margin:0 0 1.25rem}
h3{font-weight:800; font-size:1.05rem; margin:0 0 .4rem}
p{margin:0 0 1rem}
strong{color:#fff}

/* top bar */
.top{border-bottom:1px solid var(--line); background:rgba(20,23,26,.85); backdrop-filter:blur(8px); position:sticky; top:0; z-index:10}
.top .wrap{display:flex; align-items:center; gap:.65rem; height:60px}
.brand{display:inline-flex; align-items:center; gap:.6rem; color:var(--fg)!important}
.brand img{width:30px; height:30px; border-radius:8px; display:block}
.brand b{font-family:"Archivo",sans-serif; font-weight:900; text-transform:uppercase; letter-spacing:.02em; font-size:1.05rem}
.top .tag{margin-left:auto; color:var(--mut); font-family:"IBM Plex Mono",monospace; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase}

/* hero */
.hero{padding:clamp(2.5rem,6vw,5rem) 0 clamp(2rem,4vw,3.5rem)}
.hero .wrap{display:grid; grid-template-columns:1.15fr .85fr; gap:clamp(2rem,5vw,4rem); align-items:center}
.hero .lede{font-size:1.12rem; color:#e7ebee; max-width:44ch}
.hero .sub{color:var(--mut); font-size:1rem}
.hero .sub b{color:var(--accent)}
.phone{
  border:2px solid var(--accent); border-radius:34px; padding:10px;
  background:var(--ink); box-shadow:0 30px 70px rgba(0,0,0,.5); max-width:290px; margin:0 auto;
}
.phone img{width:100%; height:auto; display:block; border-radius:24px}

/* feature grid */
.features{padding:clamp(2rem,4vw,3.5rem) 0; border-top:1px solid var(--line)}
.grid{display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--line); border:1px solid var(--line)}
.cell{background:var(--panel); padding:1.6rem 1.4rem; border-top:3px solid var(--accent)}
.cell .n{font-family:"IBM Plex Mono",monospace; font-weight:600; color:var(--accent); font-size:.78rem; letter-spacing:.12em; margin-bottom:.8rem}
.cell p{color:var(--mut); font-size:.95rem; margin:0}

/* screenshot strip */
.shots{padding:clamp(2rem,4vw,3.5rem) 0; border-top:1px solid var(--line)}
.shotrow{display:grid; grid-template-columns:repeat(3,1fr); gap:1.25rem}
.shotrow figure{margin:0}
.shotrow img{width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:18px; background:var(--ink)}
.shotrow figcaption{color:var(--mut); font-size:.85rem; margin-top:.6rem; text-align:center}

/* link + notes sections */
.band{padding:clamp(2rem,4vw,3.5rem) 0; border-top:1px solid var(--line)}
.linklist{list-style:none; margin:0; padding:0}
.linklist li{border-bottom:1px solid var(--line); padding:.9rem 0}
.linklist li:last-child{border-bottom:none}
.linklist a{font-family:"Archivo",sans-serif; font-weight:600; font-size:1.05rem}
.linklist .muted{display:block; color:var(--mut); font-size:.9rem; margin-top:.15rem}
.band h3.grp{font-family:"IBM Plex Mono",ui-monospace,monospace; font-weight:600; font-size:.78rem;
  letter-spacing:.14em; text-transform:uppercase; color:var(--accent); margin:1.75rem 0 .25rem}
.band h3.grp:first-of-type{margin-top:0}
.notes{list-style:none; margin:0; padding:0; display:grid; gap:1rem}
.notes li{background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:10px; padding:1.1rem 1.2rem; color:var(--mut); font-size:.98rem}
.notes strong{color:#fff}

footer{border-top:1px solid var(--line); padding:2rem 0 3rem; color:var(--mut); font-size:.9rem}
footer a{color:var(--mut); text-decoration:underline}

@media (max-width:760px){
  body{font-size:16px}
  .hero .wrap{grid-template-columns:1fr}
  .hero .art{order:-1}
  .grid{grid-template-columns:1fr}
  .shotrow{grid-template-columns:1fr}
  .top .tag{display:none}
}
</style>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "{{BASE}}/#org",
      "name": "Easy BACnet",
      "url": "{{BASE}}/",
      "logo": "{{BASE}}/logo-512.png"
    },
    {
      "@type": "WebSite",
      "@id": "{{BASE}}/#site",
      "name": "Easy BACnet",
      "url": "{{BASE}}/",
      "publisher": { "@id": "{{BASE}}/#org" }
    },
    {
      "@type": "SoftwareApplication",
      "name": "Easy BACnet",
      "applicationCategory": "UtilitiesApplication",
      "operatingSystem": "Android 8.0 or later",
      "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
      "publisher": { "@id": "{{BASE}}/#org" },
      "description": "Scans a local network for BACnet IP devices, reads their points, commands and releases them by priority, builds custom remotes and multi-device control panels, and exports the results as an Excel (.xlsx) spreadsheet."
    }
  ]
}
</script>
</head>
<body>

<div class="top">
  <div class="wrap">
    <a class="brand" href="index.html"><img src="icon.svg" alt=""><b>Easy BACnet</b></a>
    <span class="tag">BACnet IP Controls made Easy</span>
  </div>
</div>

<section class="hero">
  <div class="wrap">
    <div class="copy">
      <p class="eyebrow">BACnet/IP &middot; Android</p>
      <h1>Browse and <span>control</span> BACnet/IP devices, straight from your phone</h1>
      <p class="lede">Easy BACnet is a BACnet/IP <strong>browser and control tool</strong> for anyone
      who works with BACnet/IP devices &mdash; discover what is on the network, browse each
      device and its points, read live values, command a point at the priority you choose
      (and release it), export a full report, and build your own on-screen controls for the
      equipment you touch most.</p>
      <p class="sub">No account, no sign-up, no cloud. <b>Easy.</b> Your scan data stays on
      your phone and your local network.</p>
    </div>
    <div class="art">
      <div class="phone"><img src="img/scan.png" alt="A finished scan in Easy BACnet" width="480" height="1068" fetchpriority="high"></div>
    </div>
  </div>
</section>

<section class="features">
  <div class="wrap">
    <h2>What it does</h2>
    <div class="grid">
      <div class="cell"><div class="n">01 / DISCOVER</div>
        <h3>Discover the network</h3>
        <p>Finds every BACnet/IP device on the subnet, including MS/TP devices reached
        through a BACnet router. <strong>BACnet IP only</strong> &mdash; it does not connect
        to an MS/TP (RS-485) serial trunk directly.</p></div>
      <div class="cell"><div class="n">02 / BROWSE</div>
        <h3>Browse devices &amp; points</h3>
        <p>Every object on every device &mdash; type, instance, name, live value, units,
        status flags and description. A full browser in your pocket.</p></div>
      <div class="cell"><div class="n">03 / INSPECT</div>
        <h3>See who&rsquo;s commanding</h3>
        <p>The priority array and relinquish default, so you can tell at a glance whether a
        point is being overridden, and at what level.</p></div>
      <div class="cell"><div class="n">04 / COMMAND</div>
        <h3>Command &amp; release</h3>
        <p>Write a value at the BACnet priority you choose, then release it back to
        automatic. Write mode is off by default and resets on every launch.</p></div>
      <div class="cell"><div class="n">05 / BUILD</div>
        <h3>Build custom BACnet/IP controls</h3>
        <p>Create your own on-screen control menu for a unit &mdash; run an air handler,
        chiller or any BMS point from setpoints, toggles and readouts you arrange yourself.</p></div>
      <div class="cell"><div class="n">06 / EXPORT</div>
        <h3>Export a device &amp; points list</h3>
        <p>Scan and export the whole network as an Excel (.xlsx) spreadsheet &mdash; a
        device summary plus every point &mdash; ready to hand to an integrator, keep on
        file, or feed an AI.</p></div>
    </div>
  </div>
</section>

<section class="shots">
  <div class="wrap">
    <div class="shotrow">
      <figure><img src="img/points.png" alt="A device's points" width="480" height="1068" loading="lazy"><figcaption>Browse each device and its points</figcaption></figure>
      <figure><img src="img/write.png" alt="Writing a value at a chosen priority" width="480" height="1068" loading="lazy"><figcaption>Command a point at the priority you choose</figcaption></figure>
      <figure><img src="img/remote-use.png" alt="A custom control panel" width="480" height="1068" loading="lazy"><figcaption>Build your own control panel</figcaption></figure>
    </div>
  </div>
</section>

<section class="band">
  <div class="wrap">
    <h2>Using the app</h2>
    <ul class="linklist">
      <li><a href="guides/how-to-use-easy-bacnet.html">How do I get a BACnet IP points list off a building?</a></li>
      <li><a href="guides/how-to-write-to-a-bacnet-point.html">How do I write to a BACnet point, and release it afterwards?</a></li>
      <li><a href="guides/how-to-build-a-custom-remote.html">How do I build a custom remote for a device?</a></li>
      <li><a href="guides/how-to-build-a-control-panel.html">How do I build a control panel for several devices?</a></li>
      <li><a href="guides/export-bacnet-points-to-csv.html">How do I export a BACnet IP points list to Excel?</a></li>
      <li><a href="guides/bacnet-add-device-by-ip.html">How do I add a device by IP address, or scan through a BBMD?</a></li>
      <li><a href="guides/cant-find-what-im-looking-for.html">The app can&rsquo;t find what I&rsquo;m looking for &mdash; what do I do?</a></li>
    </ul>
  </div>
</section>

<section class="band">
  <div class="wrap">
    <h2>Free tools</h2>
    <p>Quick browser calculators &mdash; nothing is uploaded.</p>
    <ul class="linklist">
{{TOOLS}}
    </ul>
  </div>
</section>

<section class="band" id="guides">
  <div class="wrap">
    <h2>Guides</h2>
{{GUIDES}}
  </div>
</section>

<section class="band">
  <div class="wrap">
    <h2>Before you connect</h2>
    <ul class="notes">
      <li><strong>Put the phone on the same subnet as the controllers.</strong> BACnet
      discovery relies on broadcast, and broadcast traffic does not cross a router
      without a BBMD &mdash; so a phone on guest Wi&#8209;Fi or a separate VLAN will not
      see the equipment.</li>
      <li><strong>Discovery runs on UDP&nbsp;47808</strong>, the standard BACnet/IP port.
      Some sites assign 47809 and above; the app checks the common range automatically.</li>
      <li><strong>Reading is safe. Writing carries real weight.</strong> A commanded point
      holds the value you write until it is released. If you intend to command anything on
      a live system, read
      <a href="guides/bacnet-priority-and-stuck-overrides.html">how BACnet priority works</a>
      first.</li>
    </ul>
  </div>
</section>

<footer>
  <div class="wrap">
    <p><a href="terms.html">Terms of use</a> &middot; <a href="privacy.html">Privacy policy</a> &middot;
    Contact: <a href="mailto:Firstimpactdevelopment@gmail.com">Firstimpactdevelopment@gmail.com</a></p>
  </div>
</footer>

</body>
</html>
"""


def ping_indexnow(urls):
    """Tell IndexNow-consuming engines (Bing/Yandex/Seznam/Naver) to recrawl.
    Safe to call repeatedly; run it after a deploy is live."""
    payload = json.dumps({
        "host": "easybacnet.com",
        "key": INDEXNOW_KEY,
        "keyLocation": "%s/%s.txt" % (BASE_URL, INDEXNOW_KEY),
        "urlList": urls,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("IndexNow: submitted %d URLs -> HTTP %d (200/202 = accepted)" % (len(urls), resp.status))
    except urllib.error.HTTPError as e:
        print("IndexNow: HTTP %d %s (422 = key/URL mismatch; ensure %s.txt is deployed)" % (e.code, e.reason, INDEXNOW_KEY))
    except Exception as e:  # network-dead plant rooms etc. — never fail the build
        print("IndexNow: ping skipped/failed — %s" % e)


def check_lengths():
    """Warn (don't fail) when a title or meta description drifts out of range."""
    rows = [(g["slug"], g["title"], g["description"]) for g in GUIDES]
    rows += [(t["slug"], t["title"], t["description"]) for t in TOOLS]
    for slug, title, desc in rows:
        tl, dl = len(html_module.unescape(title)), len(html_module.unescape(desc))
        if tl > 60:
            print("WARNING: %s title is %d chars (keep <= 60)" % (slug, tl))
        if not 110 <= dl <= 160:
            print("WARNING: %s description is %d chars (aim for 120-155)" % (slug, dl))


def main(ping=False):
    check_lengths()
    for g in GUIDES:
        write(
            g["slug"] + ".html",
            page(
                g["slug"], g["title"], g["question"], g["answer_html"],
                g["body_html"], g["related"], g["description"],
            ),
        )

    for t in TOOLS:
        write(
            t["slug"] + ".html",
            tool_page(
                t["slug"], t["title"], t["question"], t["description"],
                t["intro_html"], t["tool_html"], t["related"],
            ),
        )

    # The homepage lists guides by topic, not in the order they were written.
    by_slug = {g["slug"]: g for g in GUIDES}
    placed = set()
    groups = []
    for heading, slugs in GUIDE_GROUPS:
        items = []
        for s in slugs:
            g = by_slug.get("guides/" + s)
            if g is None:
                print("WARNING: GUIDE_GROUPS names unknown guide", s)
                continue
            placed.add(g["slug"])
            items.append(g)
        groups.append((heading, items))
    leftover = [g for g in GUIDES if g["slug"] not in placed]
    if leftover:
        groups.append(("More", leftover))
    links = "\n".join(
        '    <h3 class="grp">%s</h3>\n    <ul class="linklist">\n%s\n    </ul>' % (
            heading,
            "\n".join(
                '  <li><a href="%s.html">%s</a><br><span class="muted">%s</span></li>'
                % (g["slug"], g["question"], g["description"].split(".")[0] + ".")
                for g in items),
        )
        for heading, items in groups
    )
    tool_links = "\n".join(
        '  <li><a href="%s.html">%s</a><br><span class="muted">%s</span></li>'
        % (t["slug"], t["question"], t["description"].split(".")[0] + ".")
        for t in TOOLS
    )
    write("index.html", INDEX.replace("{{BASE}}", BASE_URL)
          .replace("{{TOOLS}}", tool_links).replace("{{GUIDES}}", links))

    # sitemap + robots so crawlers and agents can enumerate the whole set
    # <loc> values are normalised to extensionless clean URLs in write().
    # privacy-desktop.html is live (the PC app links to it) but kept out of the
    # sitemap and noindexed until the PC version is announced on the site.
    urls = (["index.html", "privacy.html", "terms.html"]
            + [t["slug"] + ".html" for t in TOOLS]
            + [g["slug"] + ".html" for g in GUIDES])
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod></url>" % (BASE_URL, u, UPDATED))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")

    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE_URL)

    # AdMob app-ads.txt (app publisher pub-6721099502169382). Must sit at the
    # root of the developer-website domain entered on the Play store listing.
    write("app-ads.txt", "google.com, pub-6721099502169382, DIRECT, f08c47fec0942fa0\n")

    # IndexNow key file (its contents ARE the ownership proof) + optional ping.
    write(INDEXNOW_KEY + ".txt", INDEXNOW_KEY + "\n")
    if ping:
        clean = [BASE_URL + "/" if _to_clean_url(u) == "/" else BASE_URL + "/" + _to_clean_url(u)
                 for u in urls]
        ping_indexnow(clean)

    # Custom domain + host hints
    write("CNAME", "easybacnet.com")
    write(".nojekyll", "")

    # Standalone 404 page (not built via page())
    write("404.html", """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>Page not found &mdash; Easy BACnet</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#14171a">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@800;900&family=Manrope:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root { color-scheme: dark; }
  body { max-width: 40rem; margin: 0 auto; padding: 6rem 1.25rem; text-align: center;
         font-family:"Manrope",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
         font-size:17px; line-height:1.7; color:#f3f5f6; background:#14171a; }
  h1 { font-family:"Archivo",sans-serif; font-weight:900; text-transform:uppercase;
       font-size:2rem; margin:0 0 .75rem; }
  a { color:#ff9a1f; font-weight:600; }
</style>
</head>
<body>
  <h1>Page not found</h1>
  <p>The page you were looking for does not exist or has moved.</p>
  <p><a href="/">Go to Easy BACnet</a></p>
</body>
</html>
""")

    # llms.txt for AI agents: site name, purpose, and key URLs
    llms = ["# Easy BACnet",
            "Free Android app to scan a network for BACnet IP devices, read and command points by priority, build custom remotes, and export an Excel report. Plus plain-English BACnet guides.",
            "",
            "## Free tools"]
    for t in TOOLS:
        llms.append("- %s: %s/%s" % (html_module.unescape(t["question"]), BASE_URL, t["slug"]))
    llms.append("")
    llms.append("## Guides")
    for g in GUIDES:
        llms.append("- %s: %s/%s" % (html_module.unescape(g["question"]), BASE_URL, g["slug"]))
    llms.append("- Easy BACnet home: %s/" % BASE_URL)
    llms.append("- Privacy policy: %s/privacy" % BASE_URL)
    write("llms.txt", "\n".join(llms) + "\n")


if __name__ == "__main__":
    main(ping="--ping" in sys.argv)
