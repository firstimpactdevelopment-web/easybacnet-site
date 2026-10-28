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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagrams
import points_library

BASE_URL = "https://easybacnet.com"

# IndexNow (Bing, Yandex, Seznam, Naver, …) instant-recrawl key. The key file
# below is served at BASE_URL/<key>.txt and IS the ownership proof — its
# contents must equal the key. Google does not consume IndexNow, so this is a
# free supplement to the sitemap, not a Google-ranking lever. Ping AFTER a
# deploy is live:  python build_site.py --ping
INDEXNOW_KEY = "e9a7c4f20b8d46139f5c1a7e63d02b8f"

# Freshness signal. Bump when guide content is meaningfully revised.
UPDATED = "2026-10-11"            # ISO, for JSON-LD and sitemap <lastmod>
UPDATED_HUMAN = "11 October 2026"  # for the visible "Updated" line


def play_url(medium, campaign="site"):
    # Google Play listing with UTM tags, so Play Console (Store analysis ->
    # traffic sources) credits installs to the site and to the placement.
    # GA4 enhanced measurement logs the outbound "click" event on its own.
    # Returned HTML-escaped (&amp;) for use straight inside href="...".
    return ("https://play.google.com/store/apps/details?id=com.easybacnet.app"
            "&amp;utm_source=easybacnet.com&amp;utm_medium=%s&amp;utm_campaign=%s"
            % (medium, campaign))


HERE = os.path.dirname(os.path.abspath(__file__))

# Google Analytics 4 measurement ID for easybacnet.com (GA4 property under
# tim.bruhn89 "Default Account for Firebase", created 2026-09-20).
GA_MEASUREMENT_ID = "G-BH9W9B8YRJ"

# Google AdSense (web ads) publisher -- firstimpactdevelopment@gmail.com, same
# account as xivprofitability.com. Auto ads: placement is chosen in the AdSense
# console, so pages only need the loader. EEA/UK/CH ad consent is handled by
# Google's own certified CMP (AdSense > Privacy & messaging > GDPR message).
ADSENSE_CLIENT = "ca-pub-8667608030467156"

# GA4 with Consent Mode v2 + the AdSense loader. Analytics storage defaults to
# DENIED and only loads gtag/config after the visitor accepts the cookie banner
# (GDPR/ePrivacy). Ad consent is left to Google's CMP, so no ad_* default here
# (a global "denied" would also throttle AdSense). Self-contained (own <style>,
# own banner DOM) so it can be dropped into any page after the <meta charset>
# line. IP anonymisation is on; GA gets no Google-signals/ad-personalisation.
ANALYTICS = ("""
<meta name="google-adsense-account" content="%(ads)s">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=%(ads)s" crossorigin="anonymous"></script>
<!-- Google Analytics 4 (Consent Mode v2) — analytics cookies gated by the banner -->
<script>
(function(){
  var ID="%(ga)s", KEY="ga-consent", P="%(privacy)s";
  window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}window.gtag=gtag;
  gtag('js',new Date());
  gtag('consent','default',{analytics_storage:'denied',wait_for_update:500});
  var v=null;try{v=localStorage.getItem(KEY);}catch(e){}
  function load(){if(window.__ga)return;window.__ga=1;var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+ID;document.head.appendChild(s);gtag('config',ID,{anonymize_ip:true,allow_google_signals:false,allow_ad_personalization_signals:false});}
  function grant(){gtag('consent','update',{analytics_storage:'granted'});load();}
  if(v==='granted'){grant();}
  function banner(){
    if(v==='granted'||v==='denied')return;
    var d=document.createElement('div');d.className='cookie-consent';
    d.innerHTML='<p>We use Google Analytics to see which guides help. Ads from Google AdSense keep the guides free. <a href="'+P+'">Privacy policy</a>.</p><div class="cc-row"><button type="button" id="cc-no">Decline</button><button type="button" id="cc-yes">Accept</button></div>';
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
""" % {"ga": GA_MEASUREMENT_ID, "privacy": BASE_URL + "/privacy", "ads": ADSENSE_CLIENT})

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
  header.site .getapp { margin-left:.9rem; padding:.3rem .7rem; border-radius:8px;
                        background:var(--accent); color:var(--ink); font-weight:700;
                        font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem;
                        letter-spacing:.1em; text-transform:uppercase; }
  .appcta { background:var(--box); border:1px solid var(--line);
            border-left:3px solid var(--accent); border-radius:12px;
            padding:1.1rem 1.3rem; margin:2.5rem 0 0; display:flex; gap:1rem;
            align-items:center; flex-wrap:wrap; }
  .appcta p { margin:0; flex:1 1 18rem; }
  .appcta a.btn { background:var(--accent); color:var(--ink); text-decoration:none;
                  font-weight:700; padding:.6rem 1rem; border-radius:10px; white-space:nowrap; }
  /* Phones: the tagline wrapped onto its own line and the nav onto a third;
     the footer already links the points library. */
  @media (max-width:520px) {
    header.site .muted, header.site .navl { display:none; }
    header.site .getapp { margin-left:auto; }
    code { overflow-wrap:anywhere; }
  }
""" + diagrams.CSS


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
    "guides/what-is-bacnet": [("scan.png","A scan finds every BACnet IP device"),
        ("devices.png","Each device that answered"),("points.png","One device’s points, named and typed")],
    "guides/bacnet-engineering-units-explained": [("points.png","Units shown next to every value")],
    "guides/duplicate-bacnet-device-id": [("devices.png","Each device with its Device ID")],
    "guides/is-it-safe-to-write-to-bacnet": [("write.png","Choosing a value and priority"),
        ("release.png","Releasing back to auto")],
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
  <a class="navl" href="%(prefix)sbacnet-points-lists/index.html" style="margin-left:1rem;font-family:'IBM Plex Mono',monospace;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#ff9a1f">Points lists</a>
  <a class="getapp" href="%(play_nav)s" rel="noopener">Get the app</a>
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
  <div class="appcta">
    <p><strong>Check it on your own network.</strong> Easy BACnet is a free Android app
    that finds BACnet IP devices and reads their points in a couple of taps.</p>
    <a class="btn" href="%(play_cta)s" rel="noopener">Get it on Google Play</a>
  </div>
</article>%(rel)s

<footer>
  <p>Published alongside <a href="%(prefix)sindex.html">Easy BACnet</a>, a
  <a href="%(play_footer)s" rel="noopener">free Android app</a> that scans a building network for BACnet IP devices, reads and
  commands their points, and exports the results as an Excel (.xlsx) spreadsheet.</p>
  <p><a href="%(prefix)sindex.html#guides">All guides</a> &middot;
  <a href="%(prefix)sbacnet-points-lists/index.html">BACnet points lists by manufacturer</a> &middot;
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
        "body": re.sub(r"\{\{fig:(\w+)\}\}", lambda m: diagrams.figure(m.group(1)), body_html),
        "rel": rel,
        "prefix": prefix,
        "updated_h": UPDATED_HUMAN,
        "play_nav": play_url("nav", slug.split("/")[-1]),
        "play_cta": play_url("guide_cta", slug.split("/")[-1]),
        "play_footer": play_url("footer", slug.split("/")[-1]),
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
    answer_html="""<p>A BACnet IP points list is a spreadsheet of the data objects your
    controllers expose on the network. Each row is one point (a sensor reading, a
    setpoint, a command or a status) identified by the device it lives on, its
    <em>object type</em> (Analog Input, Binary Output and so on) and its <em>instance
    number</em>, usually with the point name, present value and units. Integrators,
    analytics vendors and new head-end contractors ask for it before they map
    anything.</p>""",
    body_html="""
  <h2>What a point is</h2>
  <p>BACnet models a controller as a set of <strong>objects</strong>, and each object
  has properties. The one most people care about is <code>Present_Value</code>: what
  the point reads or is commanded to right now. A packaged RTU controller might
  expose sixty to a hundred objects: supply air temp, fan status, economizer damper
  position, occupancy, a handful of setpoints, and a pile of internal values only the
  manufacturer's tech will ever look at.</p>
{{fig:objects}}
  <p>A point is addressed by its type plus instance. Analog Input 3 and Binary Input
  3 are different points on the same controller. That pair, together with the device
  instance, is what an integrator maps, so a list that only gives names isn't much
  use to them.</p>

  <h2>What a points list contains</h2>
  <p>A usable points list has at least these columns:</p>
  <table>
    <tr><th>Column</th><th>Why it matters</th></tr>
    <tr><td>Device ID (instance)</td><td>Which controller the point lives on. Must be unique across the whole BACnet internetwork.</td></tr>
    <tr><td>Device name / IP address</td><td>How a person and a machine find the controller. MS/TP devices behind a router show the router's IP plus a network number and MAC.</td></tr>
    <tr><td>Object type</td><td>Analog Input, Binary Value, Multi-State Output, etc. Tells you the data type and whether the point can be commanded.</td></tr>
    <tr><td>Object instance</td><td>The number within that type. Type plus instance is the point's address on the device.</td></tr>
    <tr><td>Point name</td><td>The <code>Object_Name</code> property, e.g. <code>RTU-3 SA-T</code> or <code>VAV-2-14 ZN-T</code>. Often the only clue to what the point does.</td></tr>
    <tr><td>Present value</td><td>What it reads right now. Shows the point is live and lets the reader sanity-check the units.</td></tr>
    <tr><td>Units</td><td>&deg;F, %, CFM, in. W.C. A number without units is a guess.</td></tr>
    <tr><td>Status flags</td><td>In alarm, fault, overridden, out of service. Tells you whether to trust the value.</td></tr>
  </table>

  <h2>The object types you'll see most</h2>
  <ul>
    <li><strong>Analog</strong> (Input, Output, Value): temperatures, pressures,
    valve and damper positions, setpoints.</li>
    <li><strong>Binary</strong> (Input, Output, Value): fan status, start/stop
    commands, enable flags, alarm contacts.</li>
    <li><strong>Multi-state</strong> (Input, Output, Value): a short list of named
    states, such as Off / Low / High or Occupied / Unoccupied / Standby.</li>
  </ul>
  <p>As a rule of thumb, <em>Input</em> is a wired sensor, <em>Output</em> a wired
  actuator and <em>Value</em> a software point, though gateways and equipment
  controllers bend that rule often. Outputs and many Values can be commanded; see
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck overrides</a>
  before anyone writes to one.</p>

  <h2>Why people ask for one</h2>
  <ul>
    <li><strong>Integration.</strong> An analytics or FDD platform, a metering or
    tenant billing system, or a new head-end needs to know what exists before it can
    map anything.</li>
    <li><strong>Commissioning and troubleshooting.</strong> Checking the list against
    the sequence of operations turns up the sensor that was never wired or the point
    that's been out of service since startup.</li>
    <li><strong>Turnover.</strong> When a building changes owners or controls
    contractors, the points list is the closest thing to a map of the system.</li>
  </ul>

  <p>If someone has asked you for one, see
  <a href="vendor-asking-for-bacnet-information.html">what to send when a vendor
  asks for your BACnet information</a>. To pull one from a live system, see
  <a href="how-to-find-your-bacnet-points-list.html">how to find your BACnet IP points list</a>.</p>
""",
    related=[
        ("bacnet-points-lists/index", "Free BACnet points lists by manufacturer"),
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
    answer_html="""<p>Four routes, roughly easiest first: ask your controls contractor
    for the submittals or as-builts, export a point report from the BMS head-end,
    scan the network with a BACnet IP discovery tool, or read the
    <code>Object_List</code> property from each controller yourself. A scan is the one
    that shows what's actually on the network today rather than what was drawn up at
    the start of the job.</p>""",
    body_html="""
  <h2>1. Ask the controls contractor</h2>
  <p>Whoever installed or services the BAS usually has a points list in the
  submittals or as-built package, often as a spreadsheet. When it exists it's the
  quickest answer. Two catches: it describes the design, which isn't always what got
  installed, and it goes stale the first time someone adds a VAV or swaps a
  controller.</p>

  <h2>2. Export from the BMS head-end</h2>
  <p>Niagara (a JACE or Supervisor), Metasys, Desigo CC, EcoStruxure Building
  Operation, WebCTRL and the rest can all produce a point report or database export.
  Look under reports or the database/point manager views, not the graphics. You get
  what the head-end has mapped, which is usually a subset: anything nobody brought
  into the front end won't be there.</p>

  <h2>3. Scan the network</h2>
  <p>A scanning tool finds every BACnet IP device on the network you're connected to,
  then reads each one's list of points. It finds the undocumented controllers too.</p>
  <p>You need:</p>
  <ul>
    <li>A connection on <strong>the same IP subnet</strong> as the controllers
    (typically a port on the controls switch or BAS VLAN), or a BBMD that will accept
    you as a foreign device.</li>
    <li>UDP port <strong>47808</strong> (0xBAC0) open between you and the devices.
    Some sites run a second BACnet network on 47809 or nearby.</li>
    <li>Permission. A scan only reads, but it's still someone's production control
    system.</li>
  </ul>

  <p><a href="../index.html">Easy BACnet</a> does this from an Android phone. Plug a
  USB-C Ethernet adapter into the controls switch (or join the controls Wi-Fi if the
  site has one), tap <strong>Scan for Devices</strong>, then <strong>Export
  Results</strong>. It reads every point on each device it found and builds an Excel
  spreadsheet (<code>.xlsx</code>) you can email from the phone.</p>

  <h2>4. Read Object_List directly</h2>
  <p>If you're writing your own tooling: every device object has an
  <code>Object_List</code> property (property ID 76) listing every object on that
  device. Read array index 0 to get the count, then each index in turn, then
  <code>Object_Name</code> (77) and <code>Present_Value</code> (85) for each object you
  care about.</p>

  <p>Reading index by index matters. Plenty of controllers and gateways don't support
  segmentation, so asking for the whole <code>Object_List</code> in one read fails
  once the list is too big for a single packet. A few devices reject the indexed
  read, so it's worth falling back to the whole-array read when that happens. Easy
  BACnet does both, and stops auto-loading at 2,000 objects on very large devices.</p>

  <h2>If the scan finds nothing</h2>
  <p>That's common, and it's almost always the network rather than the controllers.
  See <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP devices</a>.</p>
""",
    related=[
        ("bacnet-points-lists/index", "Free BACnet points lists by manufacturer"),
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
    answer_html="""<p>Usually four things: a <strong>points list</strong> (device,
    object type, instance and name for each point), the <strong>device instances and
    IP addresses</strong> of the controllers, the <strong>network layout</strong>
    (subnets, BACnet routers, MS/TP trunks, any BBMD), and whether they're getting
    <strong>read-only or read-write</strong> access. An export from a network scan
    covers the first two.</p>""",
    body_html="""
  <h2>The checklist</h2>
  <ol>
    <li><strong>Points list.</strong> Device, object type, object instance, point
    name, current value and units. This is most of what they need. See
    <a href="what-is-a-bacnet-points-list.html">what a points list is</a> and
    <a href="how-to-find-your-bacnet-points-list.html">how to produce one</a>.</li>

    <li><strong>Device instances.</strong> Every BACnet device has a Device ID that
    should be unique on the site. Integrators map by that number, so a list of names
    alone will come straight back to you.</li>

    <li><strong>IP addresses and port.</strong> Which subnet the controllers are on
    (say 10.20.30.0/24) and whether they use the standard UDP 47808.</li>

    <li><strong>Topology.</strong> Is everything on one IP subnet, or are some
    devices on MS/TP trunks behind BACnet routers? Is there a BBMD, and at what
    address? If the vendor's gateway or VPN lands on a different subnet, this decides
    whether their discovery works.</li>

    <li><strong>Access.</strong> Say plainly whether they get read-only or will be
    commanding points. If they'll write, agree on the priority they use up front.
    Integrations writing at the wrong priority, and never releasing, are a common
    source of stuck equipment. See
    <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck overrides</a>.</li>

    <li><strong>A contact.</strong> Whoever maintains the controls, so the vendor
    can ask what <code>AHU1_MAD_O</code> means instead of guessing.</li>
  </ol>

  <h2>The fastest way to produce it</h2>
  <p>If your documentation is current, send it. If not, a scan gets you items 1 and 2
  in a few minutes. With <a href="../index.html">Easy BACnet</a>, connect the phone to
  the controls network, scan, export, and email the Excel file (<code>.xlsx</code>) to
  the vendor. The export has a device summary on top, then one row per point with
  Device ID, Device Name, Device IP, Object Type, Object Number, Point Name, Present
  Value, Units and Status.</p>

  <h2>Things to watch</h2>
  <ul>
    <li><strong>Don't put the controls network on the internet</strong> to make a
    vendor's life easier. If they need remote access, give them a VPN account you can
    shut off.</li>
    <li><strong>Send it to a person.</strong> A points list isn't secret on its own,
    but together with remote access it's a full description of what can be
    commanded. Email a named contact, not a shared inbox.</li>
    <li><strong>Treat write access as a scheduled job.</strong> Read-only
    integration is low risk. Commanding a live plant deserves a window and someone on
    site.</li>
    <li><strong>Check for duplicate Device IDs first.</strong> Two devices with the
    same instance will break the vendor's mapping and cost a site visit. Easy BACnet
    warns about duplicates after a scan.</li>
  </ul>

  <h2>A reply template</h2>
  <pre><code>Attached is a points list (Excel) from a live scan on [date].
It covers [N] BACnet IP devices on subnet [10.20.30.0/24], UDP 47808.

Columns: Device ID, Device Name, Device IP, Object Type,
Object Number, Point Name, Present Value, Units, Status.

Topology: [all devices on one IP subnet] / [VAV controllers
20101-20124 are on MS/TP network 201 behind the router at 10.20.30.5].

Access: read-only for now. If you need write access, we'll schedule
a window and agree on a priority.

Technical contact: [name, email].</code></pre>
""",
    related=[
        ("bacnet-points-lists/index", "Free BACnet points lists by manufacturer"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet IP points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
    ],
))

GUIDES.append(dict(
    slug="guides/why-cant-i-find-my-bacnet-devices",
    title="Why can't I find my BACnet IP devices? | Easy BACnet",
    question="Why can't I find my BACnet IP devices?",
    description="Why a BACnet IP scan finds nothing, in plain terms: usually the wrong network, or BACnet IP is turned off in the device. How to tell which and fix it.",
    answer_html="""<p>Usually because your phone isn't on the same network as the
    equipment. A scan can only see devices on the network you're connected to, and
    building controls often have their own separate network, not the office or guest
    Wi-Fi. So first make sure you're on the right one. If you are, check that BACnet
    IP is actually turned on in the device, because some ship with it off. A quick ping
    tells the two apart: if the device answers a ping but not a scan, BACnet IP is
    probably off. If it doesn't answer at all, you're probably on the wrong
    network.</p>""",
    body_html="""
  <h2>Check these in order</h2>
{{fig:scanflow}}
  <h3>1. Are you on the right network?</h3>
  <p>Your phone has to be on the same network as the equipment. Building controls
  usually have their own network, separate from the office and guest Wi-Fi, so being
  on the building's Wi-Fi isn't enough. Ask whoever runs the site which network the
  controls are on. If there's no controls Wi-Fi, plug in: a USB-C Ethernet adapter
  into a spare port on the controls switch (often inside the JACE or supervisory
  panel) gets you there.</p>
  <p>A quick check: Easy BACnet shows your phone's IP address on the scan screen.
  Compare it with a controller's IP from its label, its display or the site drawings.
  On most sites the first three numbers should match: a phone on 10.20.30.250 can find
  a controller on 10.20.30.41, but not one on 192.168.1.41. An address starting
  <code>169.254</code> means the network didn't hand you an address at all, which is
  common on controls networks; you'll need a static address from the controls
  contractor. See <a href="subnets.html">what is a subnet, and why doesn't the switch
  give me the right one?</a></p>

  <h3>2. Is BACnet IP turned on in the device?</h3>
  <p>Plenty of controllers ship with BACnet IP switched off, or set up for MS/TP
  wiring only. In the device's setup (its web page, display or the manufacturer's
  tool), check that BACnet IP is enabled, that it uses the standard port 47808, and
  that it has a Device ID. If you don't have access to that, it's a job for the
  controls contractor.</p>

  <h3>3. Does the device answer a ping?</h3>
  <p>Easy BACnet has a ping tool right on the "No devices found" screen: type the
  controller's IP address and tap <strong>Ping</strong>.</p>
  <ul>
    <li><strong>It answers:</strong> the network is fine. The problem is the device
    itself, so check step 2.</li>
    <li><strong>No answer:</strong> you're probably on the wrong network (step 1), or
    the device is switched off or unplugged. Some devices ignore ping, so also check
    its power and the link light on its network port.</li>
  </ul>
  <p>More on this in <a href="is-my-bacnet-device-online-ping-test.html">is my BACnet
  device online?</a></p>

  <h3>4. Is it on a different subnet?</h3>
  <p>If the ping worked but the device's address doesn't match your phone's (step 1),
  a normal scan can't reach it. Use <strong>Add device by IP&hellip;</strong> to go
  straight to it, or enter the site's BBMD if it has one (see below).</p>

  <h3>Still nothing?</h3>
  <p>Some Wi-Fi networks block the kind of traffic a scan uses, or have a firewall
  between networks. If Easy BACnet says devices <em>only answered when contacted
  directly</em>, that's what is happening, and a wired connection on the controls
  switch fixes it. Otherwise, it's time to call IT or the controls contractor with
  your phone's IP address.</p>

  <h2>If you find some devices but not others</h2>
  <ul>
    <li><strong>They're on another subnet.</strong> The ones you found share your
    subnet; the missing ones are behind a router. Add one by IP, or register with the
    site's BBMD (below).</li>
    <li><strong>A whole MS/TP trunk is missing.</strong> MS/TP devices answer through
    their BACnet router, showing a network number and MAC instead of their own IP. If
    every device on a trunk is missing, look at the router or the trunk itself
    (wiring, baud rate, a duplicate MAC). That's a controls job.</li>
    <li><strong>The device is down.</strong> Check power and the link light first.</li>
    <li><strong>Two devices share a Device ID.</strong> One can seem to vanish, or the
    two trade places between scans. Easy BACnet warns about duplicates after a scan.
    See <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</li>
  </ul>

  <h2>If a device shows no name or no points</h2>
  <p>It answered the scan, but reading its details is failing or slow. Give a large
  controller a minute, then back out and open it again. A device behind a busy
  MS/TP router can take a while. If the scan marks it <em>needs commissioning</em>,
  it's reporting Device ID 4194303, which isn't a valid ID, and it needs setting up
  before anything can address it reliably.</p>

  <h2>Reaching devices on another subnet</h2>
  <p>Two options in the menu (three dots, top right):</p>
  <ul>
    <li><strong>Add device by IP&hellip;</strong> contacts one controller directly. It
    goes straight to that address, so it works across routers as long as the phone can
    reach it (a ping is a quick way to check).</li>
    <li><strong>BBMD for remote networks&hellip;</strong> registers the phone with the
    site's BBMD as a foreign device so scans reach the subnets it serves. Get the
    BBMD's address from whoever manages the controls network.</li>
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
    answer_html="""<p>A cable in a switch only gets you a link. Which
    <strong>subnet</strong> you land on depends on the VLAN that port is assigned to and
    the IP address you end up with, from DHCP or set by hand. One managed switch often
    carries the office, cameras, guest Wi-Fi and controls on separate VLANs. BACnet IP
    discovery only reaches your own subnet, so on the wrong one a scan finds nothing
    even with the link light on.</p>""",
    body_html="""
  <h2>What a subnet is</h2>
  <p>A subnet is a group of addresses that can reach each other directly, without a
  router. On most sites you can tell by the IP address: <code>10.20.30.42</code> is on
  the 10.20.30.x network, and a device at <code>192.168.1.55</code> is on a different
  one. The two only talk through a router. A BACnet scan only covers your own subnet
  (unless the site has a BBMD to pass it on), so being on the wrong one means it finds
  nothing.</p>
{{fig:subnets}}

  <h2>Why being plugged in isn't enough</h2>
  <p>In commercial buildings the switches are managed. Each port is assigned to a
  VLAN, and each VLAN is usually its own subnet. The controls, offices, cameras and
  guest Wi-Fi can all share one switch. The port you picked decides where you land,
  and a link light only tells you the cable is good.</p>

  <h2>Common reasons you land on the wrong subnet</h2>
  <h3>1. The port is on a different VLAN</h3>
  <p>The most common one. The wall jack or switch port is on the office or guest
  VLAN. Use a port in the controls panel or JACE enclosure, or have IT move your port
  to the controls VLAN.</p>
  <h3>2. DHCP gave you an address from another network</h3>
  <p>If the VLAN you're on has DHCP, you get a perfectly good address on the wrong
  subnet.</p>
  <h3>3. No DHCP answered</h3>
  <p>Many controls networks have no DHCP server; every controller is set by hand.
  A phone or laptop expecting DHCP gives up after a while and picks a
  <code>169.254.x.x</code> address, which reaches nothing useful. That's your cue to
  set a static address on the controls subnet.</p>
  <h3>4. A leftover static IP</h3>
  <p>A laptop still set for the last job's controls network will sit on that
  address here and see nothing.</p>

  <h2>How to tell which subnet you're on</h2>
  <p>Easy BACnet shows the phone's IP address on the scan screen, for example
  <code>192.168.1.42</code>. Compare that with the controllers' addresses. If they're on <code>10.20.30.x</code> and you're on
  <code>192.168.1.x</code> or <code>169.254.x.x</code>, that's why nothing was
  found.</p>

  <h2>How to get onto the right subnet</h2>
  <ul>
    <li><strong>Use a controls switch port.</strong> Most controls panels and JACE
    enclosures have a small switch with a spare port. A USB-C Ethernet adapter on the
    phone gets you onto it.</li>
    <li><strong>Get an address.</strong> If the controls VLAN has DHCP you'll get one
    automatically. If not, ask the controls contractor for a free static IP address in
    that range (an address like 10.20.30.250 that nothing else uses). Not
    every Android phone lets you set a static IP on a USB Ethernet adapter, so check
    yours before you're on site; a laptop or small travel router set to the static
    address is a common workaround.</li>
    <li><strong>Ask about a BBMD.</strong> If the site has one, Easy BACnet can
    register with it from another subnet and discover through it.</li>
    <li><strong>Add a known device by IP.</strong> If a controller's address is
    reachable through a router, <strong>Add device by IP&hellip;</strong> in the menu
    goes straight to it.</li>
  </ul>

  <h2>What to tell IT or the controls contractor</h2>
  <p>Three things usually settle it quickly: the IP address Easy BACnet shows for the
  phone, the subnet the controllers should be on (if you know it), and which
  switch and port you're plugged into. That tells them straight away whether you're
  on the wrong VLAN.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
        ("guides/cant-find-what-im-looking-for", "What do I do if I can&rsquo;t find my BACnet devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-priority-and-stuck-overrides",
    title="BACnet priority array and stuck overrides | Easy BACnet",
    question="Why is my BACnet point stuck, and how do I release an override?",
    description="How the BACnet priority array works, why a commanded point stays commanded, and how to release an override by writing NULL at the same priority level.",
    answer_html="""<p>A value written to a commandable BACnet point is held at the
    priority it was written at until something releases it. It doesn't time out, and
    closing or disconnecting the tool that wrote it changes nothing. To release it,
    write <code>NULL</code> to <code>Present_Value</code> at the <em>same priority</em>
    that's holding the point. Control then drops to the next occupied priority, or to
    <code>Relinquish_Default</code> if nothing else is commanding it.</p>""",
    body_html="""
  <h2>How the priority array works</h2>
  <p>Commandable objects have a <code>Priority_Array</code> of 16 slots. Analog,
  Binary and Multi-state Outputs are always commandable; the matching Value objects
  often are, but not always. Slot 1 is highest, 16 lowest. <code>Present_Value</code>
  is whatever sits in the lowest-numbered slot that isn't NULL. When every slot is
  empty the object uses <code>Relinquish_Default</code>.</p>
{{fig:priority}}
  <table>
    <tr><th>Priority</th><th>Standard meaning</th></tr>
    <tr><td>1</td><td>Manual Life Safety</td></tr>
    <tr><td>2</td><td>Automatic Life Safety</td></tr>
    <tr><td>5</td><td>Critical Equipment Control</td></tr>
    <tr><td>6</td><td>Minimum On/Off</td></tr>
    <tr><td>8</td><td>Manual Operator</td></tr>
    <tr><td>3, 4, 7, 9&ndash;16</td><td>Available; each vendor and integrator uses them their own way</td></tr>
  </table>

  <p>Head-ends and programs use different slots. Operator overrides from a front end
  usually land at 8, and control logic and schedules commonly write somewhere in the
  9&ndash;16 range. A WriteProperty that carries no priority goes to 16. Agree a
  priority with any integrator before they command anything.</p>

  <h2>Why the point is stuck</h2>
  <p>Someone wrote at a priority and never released it. The usual suspects:</p>
  <ul>
    <li>A tech overrode a point at 8 during a service call and left it.</li>
    <li>A graphic has an override button but no obvious release.</li>
    <li>An integration that commands points stopped running and left its last value
    in place.</li>
  </ul>
  <p>Read the priority array to see which slot is active. Priority 8 is almost
  always someone with a tool or a front-end override. 1, 2, 5 or 6 belongs to a
  safety or equipment-protection function: leave it alone and find out why.</p>
  <p>A related case: the program is still writing at its usual slot, but a higher
  slot is outranking it. The logic looks broken when it isn't. Clearing the higher
  slot puts it back in control.</p>

  <h2>How to release it</h2>
  <p>Write <code>NULL</code> to <code>Present_Value</code> at the priority holding the
  point. Writing a normal value at a lower priority doesn't help, because the higher
  slot still wins, and writing NULL to an empty slot does nothing. Then re-read the
  point and check it dropped to the next slot or to <code>Relinquish_Default</code>.</p>
{{fig:release}}

  <h2>Release before you leave</h2>
  <p>A damper commanded to 100% to stroke-test the actuator stays at 100% until
  someone clears it, and nothing tells the operator it's overridden unless they look
  at the status flags or priority array. Release everything you commanded before you
  leave site.</p>
  <p>In <a href="../index.html">Easy BACnet</a> the point screen shows
  <strong>Commanded At</strong> (the active priority and its value) and
  <strong>Falls Back To</strong> (the relinquish default). With Write mode on,
  <strong>Release to Auto</strong> writes NULL to a priority slot that is actually held:
  it starts on the one you last wrote (or the one in control) and lets you pick if several
  are held. The Easy BACnet Mode menu &rarr; <strong>Session write log</strong> lists
  every write and release since the app started, so you can check nothing was left
  behind.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-object-types-explained",
    title="BACnet Object Types and Type Numbers | Easy BACnet",
    question="What do the BACnet object types mean?",
    description="Reference table of BACnet object types: Analog and Binary Input/Output/Value, Multi-state, Device, Schedule, Trend Log and the rest, with what each is for.",
    answer_html="""<p>BACnet describes everything in a controller as an
    <em>object</em>, and the type tells you what kind of data it holds and how it
    behaves. The ones you'll see on every job are <strong>Analog</strong> (numbers),
    <strong>Binary</strong> (two states) and <strong>Multi-state</strong> (a short list
    of named states), each in Input, Output and Value form. Roughly, Input is a sensor,
    Output drives something, and Value is a software point inside the controller.</p>""",
    body_html="""
  <h2>The common types</h2>
  <table>
    <tr><th>#</th><th>Type</th><th>What it is</th></tr>
    <tr><td>0</td><td>Analog Input</td><td>A measured value: a temperature, pressure, flow, or a reading passed through from a drive or meter.</td></tr>
    <tr><td>1</td><td>Analog Output</td><td>An analog command: valve or damper position, fan speed reference.</td></tr>
    <tr><td>2</td><td>Analog Value</td><td>A number in the controller's logic: a setpoint, a calculated value, a tuning parameter.</td></tr>
    <tr><td>3</td><td>Binary Input</td><td>A two-state input: fan status, flow switch, filter or freezestat contact.</td></tr>
    <tr><td>4</td><td>Binary Output</td><td>A two-state command: a relay starting a fan or pump, a two-position valve.</td></tr>
    <tr><td>5</td><td>Binary Value</td><td>A two-state software point: an enable, an occupancy flag, a software alarm.</td></tr>
    <tr><td>6</td><td>Calendar</td><td>A list of dates (holidays) that schedules refer to.</td></tr>
    <tr><td>8</td><td>Device</td><td>The controller itself: name, vendor, model, firmware, and the <code>Object_List</code> of everything else.</td></tr>
    <tr><td>10</td><td>File</td><td>A file on the device, used by some vendors for programs, configuration or logs.</td></tr>
    <tr><td>12</td><td>Loop</td><td>A PID loop: setpoint, controlled variable, output and tuning.</td></tr>
    <tr><td>13</td><td>Multi-State Input</td><td>An input with named states, such as a drive's Run / Stop / Fault status.</td></tr>
    <tr><td>14</td><td>Multi-State Output</td><td>A command with named states: Off / Low / High.</td></tr>
    <tr><td>15</td><td>Notification Class</td><td>Where alarms are routed and who gets them.</td></tr>
    <tr><td>16</td><td>Program</td><td>A control program running on the device.</td></tr>
    <tr><td>17</td><td>Schedule</td><td>A weekly schedule with exceptions that writes to other points.</td></tr>
    <tr><td>19</td><td>Multi-State Value</td><td>A software point with named states: Occupied / Unoccupied / Standby.</td></tr>
    <tr><td>20</td><td>Trend Log</td><td>Samples of another point, logged inside the controller.</td></tr>
    <tr><td>23</td><td>Accumulator</td><td>A running total, typically pulses from a utility meter.</td></tr>
  </table>
  <p>The numbers are the type codes sent on the wire. Type and instance are packed
  together into a 32-bit Object Identifier: 10 bits of type, 22 bits of instance. Our
  <a href="../bacnet-object-id-decoder.html">decoder tool</a> splits one apart.</p>
{{fig:objectid}}

  <h2>Input, Output, Value: what it means for writing</h2>
  <ul>
    <li><strong>Input</strong> objects follow their source. A write to
    <code>Present_Value</code> is normally refused (write access denied) unless
    <code>Out_Of_Service</code> is set true first, which disconnects the object from
    the sensor so you can simulate a reading. Handy during commissioning, and easy to
    forget to undo.</li>
    <li><strong>Output</strong> objects are always commandable through the priority
    array.</li>
    <li><strong>Value</strong> objects live in software. Many are commandable; others
    are plain writable values with no priority array, and some are read-only.</li>
  </ul>
  <p>The Input/Output/Value split is a convention, not a guarantee. A BACnet card on a
  VFD or a packaged unit controller may expose plenty of AIs and BIs that aren't wired
  sensors at all. See <a href="bacnet-priority-and-stuck-overrides.html">BACnet
  priority and stuck overrides</a> for what commandable means in practice.</p>

  <h2>How tools write an object address</h2>
  <p>A point is type plus instance, so Analog Input 4 and Binary Input 4 are two
  different points on the same controller. Tools write it as <code>AI:4</code>,
  <code>AI-4</code>, <code>AI 4</code> or <code>analog-input,4</code>; all the same
  thing.</p>
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
    answer_html="""<p>The Device ID, properly the <em>device instance number</em>, is a
    number from 0 to 4194302 that identifies one controller across the whole BACnet
    internetwork, not just its own subnet or MS/TP trunk. Integrators and head-ends
    map devices by this number rather than by name or IP, so it has to be unique.
    Two devices with the same ID cause confusing, intermittent problems. The value
    4194303 is reserved as a wildcard and isn't a valid Device ID.</p>""",
    body_html="""
  <h2>Why it exists</h2>
  <p>IP addresses change, names get edited, and MS/TP devices have no IP address of
  their own. The device instance is the identifier that stays put across the whole
  internetwork, including controllers behind routers on RS-485 trunks. When a vendor
  asks for your BACnet information, this is the number they're after.</p>

  <p>Every device reports its Device ID when it answers a scan, which is why a scan
  list shows it next to each device's name and IP address.</p>

  <h2>Why duplicates break things</h2>
  <p>The standard requires every Device ID on the internetwork to be unique. When two
  controllers share one:</p>
  <ul>
    <li>Discovery gets unpredictable. The head-end binds the ID to whichever device
    answered, and it may not be the same one next time.</li>
    <li>An integration mapped to that ID can read from, or write to, the wrong
    controller without any error.</li>
    <li>One device can seem to drop off the network, or the two trade places.</li>
  </ul>
  <p>Duplicates usually come from controllers loaded from the same template or
  backup, or a replacement controller that went in with the old unit's settings on
  another trunk. Check before you hand a points list to anyone. Easy BACnet flags any
  instance it sees at two different addresses as a <em>duplicate ID</em>.</p>

  <h2>4194303 and factory defaults</h2>
  <p>4194303 (0x3FFFFF, the largest 22-bit number) is reserved: a client uses it as a
  wildcard meaning &ldquo;whichever device I'm talking to&rdquo;, and a real device may
  not use it as its own ID. Factory defaults vary by vendor. Some ship as 0 or 1,
  some derive the ID from the MAC address or a serial number, and some MS/TP devices
  default to a number tied to their MAC. That's why a new controller can collide with
  another out of the box. If a device does report 4194303, it hasn't been set up
  properly; Easy BACnet marks it <em>needs commissioning</em>.</p>

  <h2>Choosing numbers</h2>
  <p>Most integrators use a scheme that encodes something useful. A common one for
  MS/TP is network number plus MAC: device 14 on network 201 becomes 20114. Others
  use building and floor, such as 21001&ndash;21099 for building 2, floor 1. Any scheme
  works if it's written down and actually unique. The sites that hurt are the ones
  where every contractor started at 1.</p>
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
    title="How to Scan for Your BACnet Points List | Easy BACnet",
    question="How do I scan for my BACnet points list?",
    description="Step by step: get on the controls network, scan for BACnet IP devices, check their points, and share the whole lot as an Excel report from your phone.",
    answer_html="""<p>Get the phone onto the same network as the building controls
    (usually a USB-C Ethernet adapter into the controls switch), open the app and tap
    the <strong>Easy BACnet Mode</strong> card, tap <strong>Scan for Devices</strong>,
    let the scan finish, then tap <strong>Export Results</strong>. The app reads every
    point on every device it found, builds an Excel spreadsheet (<code>.xlsx</code>) and
    opens your phone's share sheet so you can email it or save it. Tap
    <strong>View Results</strong> instead if you want to look through the devices and
    points on the phone first.</p>""",
    body_html="""
  <h2>Before you start</h2>
  <ul>
    <li><strong>Get on the controls network.</strong> On most sites the BAS lives on
    its own VLAN or a flat network behind the supervisory controller, not on the
    office Wi-Fi. The usual way in is a USB-C Ethernet adapter plugged into a spare
    port on the controls switch (often in the JACE or supervisory panel), with a static
    IP in the controls range or DHCP if that VLAN has it. If the site has a Wi-Fi access
    point on the controls network, that works too. Guest Wi-Fi or mobile data will find
    nothing. See <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my
    BACnet devices?</a> if the scan comes back empty.</li>
    <li><strong>Get permission.</strong> BACnet IP itself has no login, so reading
    points needs no password, but you still need the owner's or IT's OK to plug into
    their network.</li>
    <li><strong>Easy BACnet speaks BACnet IP only.</strong> MS/TP (RS-485) devices show
    up when a BACnet router puts them on IP &mdash; see
    <a href="does-easy-bacnet-support-mstp-rs485.html">does Easy BACnet support
    MS/TP?</a></li>
  </ul>
{{fig:network}}

  <h2>Step 1 &mdash; Open Easy BACnet Mode</h2>
  <p>The first time you open the app it asks you to <strong>Choose your
  language</strong> (English, Espa&ntilde;ol, Deutsch, Fran&ccedil;ais, Portugu&ecirc;s
  or Thai) and to accept a short safety notice (<strong>I Agree</strong>). After that
  it opens on <em>Choose how you want to work today</em> with three cards:</p>
  <ul>
    <li><strong>Easy BACnet Mode</strong> &mdash; the scan, read and export flow
    this guide covers.</li>
    <li><strong>Browser Mode</strong> &mdash; a diagnostic view with routing and
    vendor detail, and a tool to read any property of any object by number.</li>
    <li><strong>Custom Remotes</strong> &mdash; your own control screen for one device
    (<a href="how-to-build-a-custom-remote.html">guide</a>).</li>
  </ul>
  <p>Testers on the beta version also see a fourth card, <strong>Control Panel
  Builder</strong> (<a href="how-to-build-a-control-panel.html">guide</a>). Tap
  <strong>Easy BACnet Mode</strong>.</p>

  <h2>Step 2 &mdash; Scan</h2>
  <p>The scan screen shows the network your phone is on and its IP address, so you
  can check you're on the right one before you start. If the phone isn't on Wi-Fi or
  Ethernet at all, it tells you to connect first instead of scanning.</p>
  <p>Tap <strong>Scan for Devices</strong>. The app calls out to every BACnet IP
  device on your network and keeps asking, because a single call is easily missed,
  especially over Wi-Fi. It finishes a few seconds after the last device answers, or
  after about 30 seconds if nothing does. A counter shows the seconds elapsed
  and how many devices have answered; then it reads each device's name and model.
  Allow up to a minute on a big site.</p>
  <p>When it finishes you get a green banner &mdash; <em>Success! Found 6
  device(s)</em> &mdash; or a red one, <em>No devices found</em>. On success two
  buttons appear: <strong>View Results</strong> and <strong>Export Results</strong>.
  If it comes back red, the screen shows the network that was scanned, a short
  checklist and a ping tool to test a controller's IP address; see also
  <a href="cant-find-what-im-looking-for.html">what do I do if I can't find my
  BACnet devices?</a>.</p>
  <div class="callout">
  <p>The summary may warn about <strong>unconfigured devices</strong> or
  <strong>duplicate Device IDs</strong>. Unconfigured means the device answered with
  instance 4194303, the reserved wildcard number no commissioned device should use, so
  it was probably never given an ID. Duplicates mean two controllers share an ID. Both
  are commissioning problems to pass to whoever looks after the system. See
  <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a> and
  <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</p>
  </div>

  <h3>Devices on another subnet</h3>
  <p>A scan only reaches your own subnet. For anything further away, open
  the menu (three dots, top right):</p>
  <ul>
    <li><strong>Add device by IP&hellip;</strong> &mdash; type the controller's
    <em>IP address or host name</em> and <em>UDP port</em> (47808 is standard) and tap
    <strong>Add</strong>.</li>
    <li><strong>BBMD for remote networks&hellip;</strong> &mdash; enter the site's BBMD
    address once and every scan goes through it, so it reaches the other subnets the
    BBMD serves.</li>
  </ul>

  <h2>Step 3 &mdash; Look at what it found (optional)</h2>
  <p>Tap <strong>View Results</strong>. Each device shows its name, Device ID
  and IP address, plus the model when the device reports one. Tap a device and the
  app reads its list of points. On a big controller this takes a while: the app reads
  one item at a time, because plenty of small controllers and gateways struggle with
  bigger requests. It loads
  up to 2,000 objects automatically; past that, use <strong>Add object by
  number</strong> in the device screen's menu (three dots).</p>
  <p>Tap a point to see its <strong>Present Value</strong>, <strong>Units</strong>,
  <strong>Status</strong> and <strong>Description</strong>, with a
  <strong>Refresh</strong> button for a fresh read. On commandable points you also
  see <strong>Commanded At</strong> and <strong>Falls Back To</strong>: whether
  something is holding the point at a priority, and what it will go to when released.
  When a damper won't close or a fan won't stop, check this first.</p>

  <h2>Step 4 &mdash; Export</h2>
  <p>Back on the Easy BACnet Mode screen, tap <strong>Export Results</strong>. On the
  free version the app first asks <em>Watch a short ad?</em> &mdash; choose
  <strong>Watch ad</strong> to continue, <strong>Remove ads</strong> to see Easy
  BACnet Pro, or <strong>Cancel</strong>. No ad plays unless you choose it, and if
  no ad can load (no signal in the mechanical room) the export goes ahead anyway.</p>
  <p>The app then reads every point on every device: names, present values,
  units and status. A progress box (<em>Exporting BACnet IP Results</em>) shows which
  device and point it is on; <strong>Cancel</strong> stops it. Keep the phone
  connected until it finishes.</p>
  <p>When it finishes, Android's share sheet opens titled <em>Send export by
  email</em>, with a file named like <code>EasyBACnet_20260930_1415.xlsx</code>
  attached, the subject <em>BACnet IP Export</em> plus the date, and a line saying
  how many devices and points it holds. Pick your email app, or any other app
  (Drive, Files, a messenger) to save or send it. The app never sends anything by
  itself.</p>

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
  of service) is shaded red. IDs and object numbers are stored as numbers, so you can
  sort and filter straight away. That covers what an integrator or analytics vendor
  usually means by a points list &mdash; see
  <a href="vendor-asking-for-bacnet-information.html">a vendor asked for my BACnet
  information</a> and <a href="export-bacnet-points-to-csv.html">exporting to Excel
  or CSV</a>.</p>

  <h2>Good to know</h2>
  <ul>
    <li><strong>Nothing is uploaded anywhere.</strong> The app has no account and
    no server. The spreadsheet exists on your phone and wherever you send it.</li>
    <li><strong>Scanning and reading don't change anything</strong> on the
    equipment. Writing has to be switched on separately &mdash; see
    <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet
    point</a>.</li>
    <li><strong>Dark screen by default.</strong> Change it under
    <strong>Appearance</strong> in the menu (Dark, Light or Follow system) if you are
    working outside. <strong>Language</strong> is in the same menu.</li>
    <li><strong>Scan results are not saved.</strong> They stay in memory while the
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
    answer_html="""<p>In <strong>Easy BACnet Mode</strong>, open the menu (three dots),
    tap <strong>Write mode</strong> and accept the warning. Open the point, tap
    <strong>Write Value</strong>, enter the new value, leave the priority at
    <strong>8</strong> unless the site uses something else, tap
    <strong>Review&hellip;</strong>, check the summary, then <strong>Write it</strong>.
    When you are done, tap <strong>Release to Auto</strong> on the same point. A BACnet
    command does not expire; if you don't release it, the point stays where you left it
    after you leave site.</p>""",
    body_html="""
  <h2>Write mode is off every time the app starts</h2>
  <p>Easy BACnet opens with writing disabled, every time. It is not a setting it
  remembers. Someone who opened the app to check a temperature shouldn't be two taps
  from commanding a damper. Turn it on when you need it; it is off again the next
  time the app starts.</p>

  <h2>Step 1 &mdash; Turn on write mode</h2>
  <p>On the Easy BACnet Mode screen, open the menu (three dots, top right) and tap
  <strong>Write mode</strong>. The warning says, in short: a value you write is held
  at the priority you choose until it is released, it does not time out, and closing
  the app does not undo it. Tap <strong>I understand &mdash; turn it on</strong>.</p>
  <p>Already on a point? With write mode off, a writable point shows <em>Write mode is
  off, so this point can be read but not changed</em> and an <strong>Enable Write
  Mode</strong> button that opens the same warning.</p>

  <h2>Step 2 &mdash; Look before you write</h2>
  <p>Open the point. Two rows matter here:</p>
  <ul>
    <li><strong>Commanded At</strong> &mdash; the highest priority currently holding
    the point. <em>Not commanded &mdash; following its own program</em> means every
    slot in the priority array is empty and the point is sitting at its relinquish
    default. <em>Priority 8 (68)</em> means a value of 68 is in slot 8 and is in
    control.</li>
    <li><strong>Falls Back To</strong> &mdash; the relinquish default: what the point
    goes to once every slot is released.</li>
  </ul>
  <p>If the point is already held at a <em>higher</em> priority than yours (a lower
  number, say 5 or 6), the controller will accept your write and store it in your
  slot, but Present_Value won't change until that higher priority releases. That is
  normal BACnet behaviour &mdash; see
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>
{{fig:priority}}

  <h2>Step 3 &mdash; Write</h2>
  <p>Tap <strong>Write Value</strong>. Enter the new value; for a binary point you
  pick <em>Active (On)</em> or <em>Inactive (Off)</em> from a list instead of typing.
  Choose a <strong>Priority</strong>. The default, <strong>8</strong>, is
  <em>Manual Operator</em> in the BACnet standard and is what most front ends use for
  operator overrides. Leave it there unless the site's standard says otherwise, and
  stay away from 1 and 2, which are reserved for life safety.</p>
  <p>Priority slots don't belong to anyone. If Commanded At already shows priority 8,
  that may be an override someone left from the head-end; writing at 8 replaces their
  value, and releasing 8 clears it. Note what was there before you touch it.</p>
  <p>Tap <strong>Review&hellip;</strong>. The <em>Confirm write</em> summary shows the
  point, the device, the old value, the new value and the priority. Tap <strong>Write
  it</strong>. The app sends the write, waits for the acknowledgement, then re-reads
  the point so you see what the device actually did. If the controller refuses, you
  get its error in plain words.</p>
{{fig:writeflow}}

  <h2>Step 4 &mdash; Release it before you leave</h2>
  <p>Tap <strong>Release to Auto</strong> on the point. The confirmation shows which
  priority it will clear and what the point should fall back to; tap <strong>Release
  it</strong> and the app writes NULL to that slot. It only offers slots that are
  actually held, starting on the one you wrote (or the one in control); if several are
  held, pick the one to clear and check the number before you tap. A
  <strong>Release</strong> control on a
  <a href="how-to-build-a-custom-remote.html">custom remote</a> does the same at that
  control's priority. The point then follows the next priority down, or its
  <em>Falls Back To</em> value if the array is empty, and <strong>Commanded
  At</strong> should read <em>Not commanded</em> again.</p>
  <div class="callout">
  <p>A supply fan commanded on at priority 8 and never released keeps running until
  someone finds the override, which can be months. Releasing is part of the job, not
  an extra.</p>
  </div>

  <h2>Checking what you did</h2>
  <p>The Easy BACnet Mode menu &rarr; <strong>Session write log</strong> lists every
  write and release this session, with the time, the point, old and new values, the priority, and
  whether the controller accepted it. Go through it before you leave. Anything you
  wrote that has no matching release is still commanded.</p>

  <h2>Points that will not accept a write</h2>
  <ul>
    <li><strong>Input points</strong> (Analog Input, Binary Input, Multi-State
    Input) normally reject a Present_Value write, often with Write Access Denied,
    unless the point is <em>Out Of Service</em>, because their value comes from the
    physical sensor. The app warns you about this in the write dialog.</li>
    <li><strong>Points with no priority array</strong> (many plain Analog and Binary
    Values) take a write straight into Present_Value. There is nothing to release, so
    the app only shows <em>Release to Auto</em> on points it has confirmed are
    commandable. Put the old value back by hand if you change one.</li>
  </ul>
""",
    related=[
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?"),
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
  <h2>What a custom remote is for</h2>
  <p>The point list shows everything a controller has, which can be eighty-odd objects on a
  rooftop unit controller. A custom remote is the handful you actually touch, laid out as big
  controls on one screen: zone temperature, occupied setpoint, fan command, mode, supply air
  temperature. You build it once per device and it is there on every visit. Each device has
  one remote, saved against its <strong>Device ID</strong> along with its last known address.</p>

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
    one you know from a points list (for example AV 12).</li>
  </ul>
  <p>Then <strong>Choose a control type</strong> (each row shows a small picture of the
  control):</p>
  <table>
    <tr><th>Control</th><th>What it does</th><th>Use it for</th></tr>
    <tr><td>Readout</td><td>Live value, never writes.</td><td>Supply air temp, duct static, anything you just want to see.</td></tr>
    <tr><td>Indicator</td><td>Status light, read-only. Lit when the value is at or above a threshold.</td><td>Fan status, filter alarm, freezestat &mdash; usually binary inputs.</td></tr>
    <tr><td>Setpoint</td><td>Minus / value / plus. Tap the value to type an exact number.</td><td>Occupied setpoint, minimum OA damper position.</td></tr>
    <tr><td>Toggle</td><td>Switches between on and off.</td><td>Fan command, occupancy override, pump enable.</td></tr>
    <tr><td>Button</td><td>Sends one fixed value when tapped (after a confirmation).</td><td>An alarm reset, a valve to 100%.</td></tr>
    <tr><td>Multi-state</td><td>Pick a named state.</td><td>Fan speed Off/Low/High, Occupied/Unoccupied/Standby.</td></tr>
    <tr><td>Release</td><td>Hands the point back to automatic at this control's priority.</td><td>Put one next to every control that writes.</td></tr>
  </table>
  <p>The control lands in the first free spot on the grid, labelled with the point name. A new
  multi-state control reads the point's own state names (State_Text) when the device has
  them.</p>

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
    releases use. 8 (Manual Operator) is the default; see
    <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority</a>.</li>
    <li><strong>Colour</strong> &mdash; Theme default, Blue, Green (running / normal), Amber
    (caution) or Red (stops equipment).</li>
    <li><strong>Card style</strong> &mdash; Filled (default), Outlined (quieter, good for
    readouts) or Bold (tinted, for controls that act).</li>
    <li><strong>Toggle large value text</strong> &mdash; bigger digits for the value you want
    to read at a glance.</li>
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
  <p>Use colour to mark what acts. Make the control that stops a fan <strong>red</strong> and
  leave readouts plain, so it is obvious which tiles change something.</p>
  </div>
  <p>Everything saves as you go. In Edit mode the menu also has <strong>Rename remote</strong>
  and <strong>Delete remote</strong> (which removes the controls from this phone only; nothing
  on the device changes). Tap <strong>Done</strong> when it looks right.</p>

  <h2>Step 5 &mdash; Use it</h2>
  <p>Out of Edit mode the remote is live. The status line at the top shows the connection:
  <strong>Online</strong> with the time of the last reply, <strong>Some points not
  answering</strong>, or <strong>No response from device</strong>. When the device stops
  answering, values grey out instead of showing stale numbers. Tap <strong>Refresh</strong>
  for a fresh read of everything.</p>
  <p>Controls that write need <strong>Write mode</strong> turned on from the menu on the Easy
  BACnet Mode screen, the same as for the point screen &mdash; see
  <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet point</a>. Until then
  the remote says <em>Read-only</em>. With write mode on, know what acts at once and what asks
  first: the setpoint's <strong>minus/plus</strong>, a <strong>toggle</strong> and picking a
  <strong>multi-state</strong> state write immediately; a <strong>typed setpoint
  value</strong>, a <strong>button</strong> and a <strong>release</strong> ask you to confirm.
  A toggle or step won't act until the point has been read (<em>No value read yet &mdash;
  tap Refresh first</em>), so it never writes based on a guess. Every write and release appears
  in the <strong>Session write log</strong> in the Easy BACnet Mode menu.</p>
  <p>After every write the remote reads the point back, and every control on that point
  updates. If the device accepted the write but the value didn't move, the remote says so:
  <em>Sent 1.5 at priority 10, but it still reads 2.50</em>. Something at a higher priority
  (another operator, a schedule, the BMS) or the controller's own logic is holding the point.
  See <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a> for how to find out what.</p>

  <h2>Coming back to it</h2>
  <p>Saved remotes appear under <strong>My Remotes</strong>, one per device, showing the device
  name, how many controls it has and its last known IP address. Open one and it talks to the
  controller directly at that address, no scan needed. If the controller's IP has changed, the
  remote shows it as not responding; scan again so the app finds the device at its new
  address.</p>

  <h2>Sharing a remote: export and import</h2>
  <ul>
    <li><strong>Export:</strong> on <strong>My Remotes</strong>, <strong>long-press</strong> a
    remote. Android's save dialog opens with a file named after the device
    (<code>Device&nbsp;name.ebremote</code>); save it to Downloads, Drive or wherever you like,
    then send it as you would any file.</li>
    <li><strong>Import:</strong> on <strong>My Remotes</strong>, menu &rarr; <strong>Import
    remote</strong>, then pick the <code>.ebremote</code> file. If you already have a remote for
    that device, the app asks <em>Replace the existing remote?</em> first. Control-panel files
    (<code>.ebpanel</code>, from the beta Control Panel Builder) can't be opened here.</li>
  </ul>
  <p>The file is plain JSON holding the layout, the device's ID and its last known address. It
  holds no values from the building.</p>

  <h2>Free vs Easy BACnet Pro</h2>
  <p>Scanning, reading, writing and exporting are free (on the free version each export
  asks to show a short ad first). On the free version you can keep
  <strong>one</strong> custom remote. Opening that saved remote asks <em>Watch a short
  ad?</em> &mdash; choose <strong>Watch ad</strong>, <strong>Remove ads</strong> or
  <strong>Cancel</strong>; no ad plays unless you choose it. If no ad can load (common in a
  mechanical room with no signal) the remote just opens, so you are never locked out of your
  own controls. Building or importing a second remote shows <em>One remote on the free
  version</em> with an <strong>Unlock</strong> button.</p>
  <p><strong>Easy BACnet Pro</strong> is a Google Play subscription: $9.99 a year (Play shows
  the price in your currency). It
  removes the ads and the limit: as many remotes as you like, on as many devices as you look
  after. Cancel any time in Google Play &rsaquo; Subscriptions; Pro stays on until the end of
  the year you paid for. If it ends, your remotes are kept, but the free limit and the ads
  come back.</p>
""",
    related=[
        ("guides/how-to-build-a-control-panel", "How do I build a control panel for several devices?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-build-a-control-panel",
    title="Build a multi-device BACnet control panel | Easy BACnet",
    question="How do I build a custom BACnet control panel for several devices in Easy BACnet?",
    description="Beta: build one live control screen for up to 32 BACnet IP devices with the Control Panel Builder. Devices, grid width, controls and sharing.",
    answer_html="""<p>The Control Panel Builder is a <strong>beta</strong> feature: it is
    only in the beta version of Easy BACnet, not the standard Play Store release. In the beta
    app, tap <strong>Control Panel Builder</strong> on the opening screen, then <strong>New
    panel</strong> (the <strong>+</strong> in the top bar, or <strong>Create a Panel</strong>).
    Pick the first device from your scan and name the panel; it opens in Edit mode. Tap
    <strong>Add Control</strong> to place a readout, setpoint, toggle, button, multi-state picker
    or release button, each bound to one point on one device. Add more devices from the menu's
    <strong>Devices&hellip;</strong> (up to 32 per panel), set the <strong>Grid width</strong>,
    drag controls into place, then tap <strong>Done</strong> to use it live. The free version
    keeps one panel driving one device; Easy BACnet Pro ($9.99 a year) allows unlimited panels
    with up to 32 devices each.</p>""",
    body_html="""
  <div class="callout">
  <p><strong>Beta feature.</strong> The Control Panel Builder is only in the beta version of
  Easy BACnet; the standard Play Store release does not include it. It works end to end, but
  check each control against the equipment the first time you use it. Panels are saved on your
  phone and can be shared as <code>.ebpanel</code> files.</p>
  </div>

  <h2>Remote or control panel?</h2>
  <p>A <a href="how-to-build-a-custom-remote.html">custom remote</a> is one screen for
  <strong>one</strong> device. A <strong>control panel</strong> uses the same drag-and-drop
  designer, but each control can point at a <strong>different</strong> device, up to 32 on one
  panel. Build a remote for the rooftop unit you check every week; build a control panel for a
  heating plant where the plant controller, each boiler's controller and the pump controllers
  are separate BACnet devices and you want the enables, supply water temperature and setpoint
  on one screen. Devices behind a BACnet router (MS/TP) work too, as long as the scan found
  them.</p>

  <h2>Before you start</h2>
  <ul>
    <li><strong>Scan first.</strong> The builder picks devices from your last scan. If you have
    not scanned this session it says <em>Scan for devices first, then build a panel from what you
    find</em> and takes you to Easy BACnet Mode. Devices on another subnet can be added with
    <strong>Add device by IP&hellip;</strong> or a <strong>BBMD</strong> before you start, or typed in by hand later.</li>
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
  (<strong>New panel</strong>) in the top bar; with no panels yet, the screen offers
  <strong>Create a Panel</strong> (or <strong>Scan for Devices</strong> if you haven't scanned).
  Choose the first device in <strong>Start the panel with which device?</strong> &mdash; this
  becomes the panel's <em>primary</em> device, the one controls use unless you point them
  elsewhere. Give it a name in <strong>Name this panel</strong> (the device name is pre-filled)
  and tap OK. The panel opens in Edit mode with a four-column grid.</p>

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
  many of its controls will be disconnected; they command nothing until you use
  <strong>Change device</strong> to point them at another device. The primary device cannot be removed.</p>

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
    <tr><td>Readout</td><td>Shows the live value. Never writes.</td><td>Supply water temp, boiler status, differential pressure.</td></tr>
    <tr><td>Setpoint</td><td>Minus / value / plus; tap the value to type one.</td><td>Hot water supply setpoint, pump speed.</td></tr>
    <tr><td>Toggle</td><td>Flips between an on and an off value.</td><td>Boiler enable, pump command.</td></tr>
    <tr><td>Button</td><td>Sends one fixed value when pressed (with a confirmation).</td><td>An alarm reset.</td></tr>
    <tr><td>Multi-state</td><td>Pick one of several named states.</td><td>Lead/lag selection, Occupied/Unoccupied.</td></tr>
    <tr><td>Release</td><td>Hands the point back to automatic at the control's priority.</td><td>Put one next to every control that writes.</td></tr>
  </table>
  <p>The new control lands in the first free slot, labelled with the point name. (The
  status-light <em>Indicator</em> is only on single-device custom remotes; on a panel, use a
  Readout for an input.)</p>

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
  write need <strong>Write mode</strong> turned on from the menu on the Easy BACnet Mode
  screen; until then the panel is read-only. A toggle won't act until it has read the point's
  current state, so it never writes based on a guess. Opening a saved panel later talks to
  each device at its last known address, so no scan is needed unless a device's IP has
  changed.</p>

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
  version keeps the layout and the primary device's controls; controls for the other devices
  are disconnected. Opening a saved panel on the free version asks to show one short ad, as a
  remote does; if no ad loads, the panel just opens. Easy BACnet Pro, the same $9.99-a-year subscription that removes ads and
  lifts the remotes limit, allows unlimited panels with up to 32 devices each. If the
  subscription ends, your panels are kept, but the free limits apply again.</p>

  <h2>Tips from the field</h2>
  <ul>
    <li><strong>Colour what acts.</strong> Make the control that stops a pump red and
    leave readouts plain, so the controls that change something are obvious at a glance.</li>
    <li><strong>One Release per writer.</strong> Anything you can command you should be able to
    hand back. A release button next to each setpoint or toggle keeps a temporary override from
    becoming a permanent one &mdash; see
    <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck overrides</a>.</li>
    <li><strong>Label by equipment, not by object.</strong> &ldquo;B-2 Enable&rdquo; beats
    &ldquo;BO-3&rdquo; when the panel spans six controllers that all have a BO-3.</li>
    <li><strong>Duplicate Device IDs break panels.</strong> A panel follows each device by its
    ID (and remembers its IP). If two controllers share an ID, fix that first &mdash; see
    <a href="duplicate-bacnet-device-id.html">duplicate BACnet device IDs</a>.</li>
  </ul>
""",
    related=[
        ("guides/how-to-build-a-custom-remote", "How do I build a custom remote in Easy BACnet?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/duplicate-bacnet-device-id", "Two devices have the same BACnet Device ID"),
    ],
))

GUIDES.append(dict(
    slug="guides/cant-find-what-im-looking-for",
    title="Can't find your BACnet devices? What to do | Easy BACnet",
    question="What do I do if I can't find my BACnet devices?",
    description="A plain-English checklist for when a scan finds nothing, misses a device, shows a device with no points, or a point with no value.",
    answer_html="""<p>Work through the same four checks the app shows: are you on the right
    network, is BACnet IP turned on in the device, can you ping it, and is it on another
    subnet? The most common cause is that the phone is not on the same network as the
    controllers. Compare the phone's IP address (shown in the app) with a controller's;
    on most sites the first three numbers should match. If they don't, get onto the
    controls network, usually with a USB-C Ethernet adapter into the controls switch, and
    scan again. For a missing device, an empty point list or a blank value, see the
    matching section below.</p>""",
    body_html="""
  <h2>The scan finds nothing at all</h2>
  <p>You tapped <strong>Scan for Devices</strong> and got the red <em>No devices
  found</em> banner. The app shows the same four checks on that screen.</p>
  <ol>
    <li><strong>Are you on the right network?</strong> This phone has to be on the same
    network as the controllers. Building controls usually have their own network, not
    the office or guest Wi-Fi. Ask IT which one, or plug into the controls switch with a
    USB-C Ethernet adapter. The app shows your phone's IP address; on most sites the
    first three numbers should match a controller's (phone 192.168.10.20, controller
    192.168.10.50).</li>
    <li><strong>Is BACnet IP turned on in the device?</strong> Many controllers ship with
    BACnet IP off, or set up for MS/TP only. In the device's setup (web page, display or
    the manufacturer's tool), check that BACnet IP is enabled on port 47808 and that it
    has a Device ID.</li>
    <li><strong>Can you ping it?</strong> Type the device's IP address into the ping box
    on the <em>No devices found</em> screen and tap <strong>Ping</strong>. If it answers,
    the network path is fine, so BACnet IP is probably off in the device or set to a
    different UDP port (step 2). If it
    doesn't, this phone probably isn't on the same network as the device (step 1), or the
    device is off. If it answers but is on a different subnet, the app says so; go to
    step 4. <a href="is-my-bacnet-device-online-ping-test.html">Is my BACnet device
    online?</a> explains each result.</li>
    <li><strong>Another subnet or a BBMD.</strong> For a controller on another subnet,
    use <strong>Add device by IP&hellip;</strong> on that screen (or in the menu). If the
    site has a BBMD, enter it once with <strong>BBMD for remote networks&hellip;</strong>
    and every scan will use it.</li>
  </ol>
  <p>If the phone isn't on Wi-Fi or Ethernet at all, the app doesn't scan; it tells you
  to connect to Wi-Fi first and has a button straight to Wi-Fi settings.</p>
{{fig:scanflow}}
  <p>For more background, see
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP
  devices?</a></p>

  <h2>It finds some devices, but not the one I want</h2>
  <ul>
    <li><strong>Look at the Device ID, not just the name.</strong> Every device shows
    its ID and IP address under the name. The unit you want may have a default name
    like the controller model, with the right ID.</li>
    <li><strong>Check it is powered and connected.</strong> A controller with no link
    light on its Ethernet port can't answer.</li>
    <li><strong>It may be on another subnet.</strong> Devices near you answered; this
    one is behind an IP router. Add it by IP, plug into its switch, or use the site's
    BBMD.</li>
    <li><strong>It may be an MS/TP device whose router isn't passing it through.</strong>
    MS/TP devices only appear via a BACnet router. If a whole trunk is missing, that
    is a controls question (router config, a trunk wiring fault, or a bad device
    dragging the trunk down). See
    <a href="does-easy-bacnet-support-mstp-rs485.html">does Easy BACnet support MS/TP?</a></li>
    <li><strong>Two devices may share an ID.</strong> Easy BACnet lists both and flags
    them <em>duplicate ID</em>, but the head-end and other tools often show only one
    and talk to whichever answers first. See
    <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</li>
  </ul>

  <h2>I opened a device but it shows no points</h2>
  <ul>
    <li><strong>Give it a minute.</strong> The app reads one property at a time, so a
    large controller takes a while. Watch the <em>Loading points</em> counter.</li>
    <li><strong>Back out and open it again.</strong> A run of dropped replies can stop
    the load; reopening starts it fresh.</li>
    <li><strong>Small devices have few objects.</strong> A thermostat or a meter
    gateway may expose only a handful. That is the device, not a fault.</li>
    <li><strong>A big controller shows only part of its list.</strong> The app
    loads the first 2,000 objects and says so. Reach the rest with the device
    screen's menu &rarr; <strong>Add object by number</strong>.</li>
  </ul>

  <h2>I see a point but no value</h2>
  <ul>
    <li><strong>Tap Refresh.</strong> Values are read live; one missed reply shows a
    dash until the next read.</li>
    <li><strong>If every point on the device shows dashes</strong>, it has stopped
    answering. Scan again to confirm it is still there.</li>
    <li><strong>Some objects have no Present_Value.</strong> Trend logs, notification
    classes, programs and files hold configuration or history, not a live reading.</li>
  </ul>

  <h2>Who to call</h2>
  <p>In short: if you can't reach the equipment on the network, call
  <strong>IT / network</strong> and have the phone's IP address ready. If you can
  reach it but the points, IDs or values are wrong, call the <strong>controls /
  BAS</strong> contractor and send them the exported spreadsheet. If the point
  reads correctly but the equipment isn't doing what it says, call the
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
    question="How do I tell if a BACnet device is online?",
    description="A hands-on test that separates a network problem from a BACnet problem: find the device IP, ping it, then add it by IP, and what each result means.",
    answer_html="""<p><strong>Ping it.</strong> Easy BACnet has a ping tool on the
    <em>No devices found</em> screen: type the controller's IP address and tap Ping. No
    reply means the phone can't reach it at all: you're on the wrong network, the
    address is wrong, or the device is off or unplugged. A reply means the network is
    fine and the device is on, so if a scan still can't see it, BACnet IP is probably
    turned off in the device, set to a different port, or the device is on another
    subnet (try <strong>Add device by IP&hellip;</strong>).</p>""",
    body_html="""
  <h2>Why test this way</h2>
  <p>A scan can fail for plenty of reasons that have nothing to do with the device. A
  ping proves the phone can reach the address at all. Adding the device by IP proves it
  is speaking BACnet. Together they tell you whether you have a network problem or a
  device-setup problem, and so who to call.</p>

  <h2>Step 1 &mdash; find the device's IP address</h2>
  <p>If the device has ever appeared in a scan, its IP is shown under its name. If
  not, check the head-end's device or network list, the as-built drawings or the
  controller's label, ask the controls contractor, or ask the network team to look it up
  in the switch's ARP or DHCP tables.</p>

  <h2>Step 2 &mdash; ping it</h2>
  <p>After a scan that finds nothing, Easy BACnet's <em>No devices found</em> screen has a
  <strong>Can you ping it?</strong> box. Type the address and tap <strong>Ping</strong>.
  The app pings over the same Wi-Fi or Ethernet connection it scans on, and tells you
  whether the device answered and whether it's on your subnet. A laptop on the same
  network works too: open a command prompt and type <code>ping 10.20.30.41</code>. You
  want replies, not &ldquo;request timed out&rdquo;.</p>
{{fig:subnets}}

  <h2>Step 3 &mdash; add it by IP</h2>
  <p>If the ping worked, in Easy BACnet Mode open the menu (three dots) &rarr;
  <strong>Add device by IP&hellip;</strong>, type the address and port (47808 unless the
  site uses another) and tap <strong>Add</strong>. The app contacts that address
  directly.</p>
  <ul>
    <li><strong>It answers.</strong> The device is online and speaking BACnet. Your scan
    missed it because it's on another subnet or the network is filtering scan traffic. To
    scan a whole remote subnet you need the site's BBMD; for this one device, you are
    done.</li>
    <li><strong>It does not answer</strong> (<em>No BACnet IP device answered
    at&hellip;</em>). See <em>The ping works, but Add by IP doesn't</em> below.</li>
  </ul>

  <h3>The ping fails</h3>
  <p>The device can't be reached over IP, so no BACnet tool will see it until that is
  fixed. Common causes:</p>
  <ul>
    <li>You are on a <a href="subnets.html">different subnet</a> with no route to it.
    Get onto the controls network and try again.</li>
    <li>The controller has no default gateway set, or the wrong one, so it can't reply
    to anything outside its own subnet. Common on controls networks that were set up
    flat and later routed.</li>
    <li>The IP is wrong, or the device picked up a new DHCP address.</li>
    <li>A cable is unplugged, a switch port is dead or disabled, or the unit is powered
    down.</li>
    <li>A firewall or VLAN access list blocks the path. Some networks block ping on
    purpose and allow BACnet, so on a managed network a failed ping is not final
    proof.</li>
  </ul>
  <p>This is usually an <strong>IT / network</strong> conversation, unless you can see
  the device itself is dead.</p>

  <h3>The ping works, but Add by IP doesn't</h3>
  <p>The device is on the network but not answering BACnet at that address and port.
  Possible reasons:</p>
  <ul>
    <li><strong>Wrong UDP port.</strong> Some sites run BACnet/IP on another port in the
    47808&ndash;47823 range, most often 47809. Ping doesn't use ports; BACnet does. Try the
    add again with the right port. See <a href="what-port-does-bacnet-use.html">what port
    does BACnet use?</a></li>
    <li><strong>A firewall allows ping but blocks UDP 47808.</strong> They are separate
    rules and it is common to have one without the other. Network team.</li>
    <li><strong>The address belongs to a router or gateway, not the device.</strong> An
    MS/TP controller has no IP of its own; the IP you have may be its BACnet router, which
    answers ping but only reaches MS/TP devices on trunks that are configured and healthy.
    See <a href="does-easy-bacnet-support-mstp-rs485.html">does Easy BACnet support
    MS/TP?</a></li>
    <li><strong>BACnet/IP isn't set up on that interface.</strong> It may be disabled,
    bound to the controller's other Ethernet port, or not yet configured on a new
    gateway. Controls contractor.</li>
  </ul>

  <h3>Both work, but the device shows no points or no values</h3>
  <p>Communication is fine. The device is slow to enumerate, refusing some property
  reads, or has very little to show. See
  <a href="cant-find-what-im-looking-for.html">the app can't find what I'm looking
  for</a>.</p>

  <h2>What to tell whoever you call</h2>
  <p>One sentence with both results saves a lot of back-and-forth:
  <em>&ldquo;10.20.30.41 answers a ping from the controls network, but doesn't answer
  BACnet on port 47808.&rdquo;</em> That rules out the cable, the
  power and the network path, and points at the port, a firewall rule, or the
  device's BACnet settings.</p>
""",
    related=[
        ("guides/cant-find-what-im-looking-for", "What do I do if I can&rsquo;t find my BACnet devices?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/bacnet-device-shows-offline", "Why does my BACnet IP device show offline?"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-vs-modbus",
    title="BACnet vs Modbus: the difference | Easy BACnet",
    question="BACnet vs Modbus — what is the difference?",
    description="BACnet is self-describing with built-in discovery; Modbus is a bare register protocol with neither. Where you meet each, and why it matters.",
    answer_html="""<p>Both move data to and from building and industrial equipment, but
    they work at different levels. <strong>BACnet</strong> is object-oriented and
    self-describing: devices can be discovered on the network, and every point carries a
    type, a name and units. <strong>Modbus</strong> is a simple register protocol: it
    gives you numbered registers and nothing else &mdash; no discovery, no names, no
    units. As a rule of thumb, BACnet runs the HVAC controls and the building management
    system; Modbus is common on meters, VFDs, generators, PLCs and packaged equipment.</p>""",
    body_html="""
  <h2>Discovery: ask the network vs sweep it</h2>
  <p>BACnet has discovery built in. A tool broadcasts a
  <a href="who-is-i-am-explained.html">Who-Is</a> and each device that receives it
  answers with an I-Am, so you can build a device list in seconds without knowing what
  is out there. Modbus has nothing like it: you must already know a device's IP address
  and unit ID (or its slave address on an RS-485 bus), or poll address by address until
  something answers.</p>

  <h2>Meaning: named points vs bare registers</h2>
  <p>A BACnet point is an object such as <code>Analog Input 3</code> with an
  <code>Object_Name</code> (say <code>AHU-1 SA-T</code>), a <code>Present_Value</code>,
  engineering units and status flags, so the device tells you what the number means. A
  Modbus holding register is just address 40007 containing 685; whether that is
  68.5&nbsp;&deg;F, 685&nbsp;kPa or half of a 32-bit value split across two registers is
  something you work out from the vendor's register map.</p>
{{fig:bacnetvsmodbus}}

  <h2>Addressing</h2>
  <table>
    <tr><th></th><th>BACnet</th><th>Modbus</th></tr>
    <tr><td>Identity</td><td>Device instance (must be unique across the whole BACnet internetwork)</td><td>IP + unit ID (TCP), or slave address 1&ndash;247 (RTU)</td></tr>
    <tr><td>A point</td><td>Object type + instance (e.g. AI 3)</td><td>Register type + number (e.g. holding register 40007)</td></tr>
    <tr><td>Self-describing</td><td>Yes &mdash; name, units, status</td><td>No &mdash; just a number</td></tr>
    <tr><td>Discovery</td><td>Who-Is / I-Am</td><td>None</td></tr>
    <tr><td>Wiring</td><td>BACnet/IP on Ethernet, MS/TP on RS-485</td><td>Modbus TCP on Ethernet, Modbus RTU on RS-485</td></tr>
  </table>

  <h2>Where you meet each</h2>
  <p>BACnet dominates air handlers, VAV boxes, rooftop units, chillers and the BAS
  head-end (Niagara, Metasys, Desigo CC, WebCTRL and the rest). Modbus is everywhere on
  power and BTU meters, generators, PV inverters and OEM skids; many VFDs and boilers
  offer both. Plenty of buildings run both, with the head-end or a protocol gateway
  mapping Modbus registers onto BACnet objects.</p>

  <h2>Which app do I use?</h2>
  <p>Use <a href="../index.html">Easy BACnet</a> for BACnet IP equipment. For Modbus gear
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
    messages behind BACnet discovery. A tool broadcasts a <em>Who-Is</em>, and each device
    that hears it (and falls inside the instance range asked for, if there is one) answers
    with an <em>I-Am</em> carrying its Device Instance, its vendor ID, its maximum message
    size and whether it supports segmentation. Collect the replies and you have a device
    list. That is what Easy BACnet does when you tap <strong>Scan for Devices</strong>.</p>""",
    body_html="""
  <h2>The exchange</h2>
  <p>On BACnet IP a Who-Is goes to the subnet's broadcast address on UDP 47808, so every
  device on that subnet gets it at once. A Who-Is can be <em>unconstrained</em> (everyone
  answer) or carry a low and high instance limit, which is how a head-end asks for device
  20114 alone without hearing from the whole building. Many devices broadcast their I-Am
  back rather than replying only to the sender, which is why a busy site's I-Ams are seen
  by every tool on the subnet.</p>
{{fig:whois}}

  <h2>What an I-Am carries</h2>
  <ul>
    <li><strong>Device Instance</strong> &mdash; the device's number, which has to be unique
    across the whole BACnet internetwork, not just the subnet. Two devices sharing one makes
    discovery and reads unreliable: see
    <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a>.</li>
    <li><strong>Max APDU length accepted</strong> and <strong>segmentation supported</strong>
    &mdash; the largest message the device takes (50 to 1476 bytes; small MS/TP controllers
    are often 480 or less) and whether it can split a long reply into segments. A tool uses
    these to decide how to read; Easy BACnet reads one property at a time, so it works with
    devices that support neither.</li>
    <li><strong>Vendor ID</strong> &mdash; the ASHRAE-assigned number for the manufacturer.</li>
  </ul>
  <p>The source address of the I-Am matters too. A device behind a BACnet router answers
  through the router, so its reply comes from the router's IP with a network number and
  MAC address inside the BACnet header.</p>

  <h2>Why a scan sometimes finds nothing</h2>
  <p>Who-Is is a broadcast, and IP routers do not forward broadcasts, so a device on a
  different subnet never hears it unless a BBMD carries
  it across. That is the usual reason a scan comes back empty: see
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet IP devices?</a>.
  Devices on an <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> trunk answer too, because
  the BACnet router passes the Who-Is down the trunk and the I-Ams back up. Some devices also
  answer badly or late, so Easy BACnet repeats the Who-Is through the scan and, if nothing
  answers, probes the subnet's addresses directly.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/bacnet-device-id-explained", "BACnet Device IDs explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-mstp-vs-bacnet-ip",
    title="BACnet MS/TP vs BACnet/IP | Easy BACnet",
    question="BACnet MS/TP vs BACnet/IP — what is the difference?",
    description="BACnet/IP runs over Ethernet on UDP 47808; MS/TP runs over an RS-485 twisted pair. How they differ, how a router joins them, and which one you have.",
    answer_html="""<p><strong>BACnet/IP</strong> carries BACnet over Ethernet using
    <a href="what-port-does-bacnet-use.html">UDP&nbsp;47808</a>.
    <strong>BACnet MS/TP</strong> (Master-Slave/Token-Passing; recent editions of the
    standard say Manager-Subordinate) carries it over an RS-485
    twisted pair daisy-chained between controllers. IP is fast and needs a switch port per
    device; MS/TP is slow but cheap to wire. That is why on many sites the supervisory
    controllers and plant controllers are on IP, while VAV boxes, fan coils and unit
    controllers sit on MS/TP trunks behind a BACnet router.</p>""",
    body_html="""
  <h2>Different wires, same BACnet</h2>
  <p>The objects, properties and services are the same on both; only the lower layers
  differ. BACnet/IP rides on an Ethernet network, usually a dedicated controls network or
  VLAN. MS/TP rides on a shielded RS-485 pair (plus a reference conductor) run from
  controller to controller, with end-of-line termination at each end. Common baud rates are
  38400 and 76800; older trunks run 9600 or 19200.</p>
{{fig:network}}

  <h2>Token passing</h2>
  <p>MS/TP devices share one pair, so masters take turns: a token passes from one master MAC
  address to the next, and only the holder may transmit. It works well when the trunk is
  healthy, but it limits throughput. A heavily loaded trunk (40 to 60 devices), a bad
  termination or a duplicate MAC address slows every device on it. That is part of why
  reading a large MS/TP controller from the IP side takes a while.</p>

  <h2>Addressing and how they meet</h2>
  <p>On MS/TP a device has a one-byte <strong>MAC address</strong> on its trunk (0&ndash;127
  for masters), and the trunk has its own BACnet <strong>network number</strong>. A
  <strong>BACnet router</strong> (often built into the JACE or supervisory controller) joins
  the trunk to BACnet/IP. From the IP side each MS/TP device still has its own Device
  Instance and answers scans through the router. That is how Easy BACnet, which speaks BACnet
  IP only, lists and reads MS/TP controllers: through a router on the subnet your phone is
  on. It cannot connect to an RS-485 trunk directly.</p>

  <h2>Which am I looking at?</h2>
  <p>In Easy BACnet's device list, MS/TP devices behind a router show the
  <strong>router's IP address</strong>, so a dozen devices sharing one IP are almost
  certainly on a trunk behind that router. A device with its own IP address is BACnet/IP.
  If the scan warns that two controllers share one MS/TP address behind a router, that trunk
  has a duplicate MAC to fix.</p>
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
    description="The default BACnet port is UDP 47808 (0xBAC0). Why it is UDP, when sites use 47809 and up, what to open in a firewall, and how to check a device answers.",
    answer_html="""<p>BACnet/IP uses <strong>UDP port 47808</strong> by default. That is
    <code>0xBAC0</code> in hex, which is where the number comes from. It is UDP, not TCP,
    and discovery relies on broadcasts to that port. When more than one BACnet/IP network
    shares an IP subnet, the others use other ports, normally from the
    <strong>47808&ndash;47823</strong> range (0xBAC0&ndash;0xBACF).</p>""",
    body_html="""
  <h2>47808, and why</h2>
  <p>The default port is 47808 decimal, which reads <code>0xBAC0</code> in hexadecimal.
  BACnet/IP sends connectionless UDP datagrams; a
  <a href="who-is-i-am-explained.html">Who-Is</a> goes out as a broadcast to that port so
  every device on the subnet hears it, and reads and writes go to each device's IP on the
  same port.</p>
{{fig:packet}}

  <h2>When it is not 47808</h2>
  <p>Each UDP port on a subnet is a separate BACnet/IP network, and a router is needed to
  pass traffic between them. Some sites use this to split, for example, lighting onto 47809
  or a third-party gateway onto 47810. A device on 47809 never answers a scan on 47808, so
  you have to know the port. Easy BACnet always scans 47808 and also tries 47809,
  47810 and 47817; for any other port, use <strong>Add device by IP&hellip;</strong> and type
  the port in.</p>

  <h2>Firewalls, BBMDs and MS/TP</h2>
  <p>If an access list between VLANs or a host firewall drops UDP 47808, discovery and reads
  fail even though the devices are fine; the network team needs to allow it in both
  directions. Broadcasts on 47808 do not cross a router at all; that takes a
  BBMD on each subnet, and the BBMDs need unicast 47808
  open between them. <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> devices have no IP
  port; they sit on an RS-485 trunk and reach IP through a BACnet router. BACnet Secure
  Connect (BACnet/SC) is different again: it runs over TLS on TCP, typically port 443, and
  is not something Easy BACnet speaks.</p>
""",
    related=[
        ("guides/bacnet-mstp-vs-bacnet-ip", "BACnet MS/TP vs BACnet/IP"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-scanner-app-android",
    title="BACnet IP scanner app for Android | Easy BACnet",
    question="Is there a BACnet IP scanner app for Android?",
    description="Yes. How to discover, read and command BACnet/IP devices from an Android phone, what a phone can and cannot reach, and the subnet and MS/TP catches.",
    answer_html="""<p>Yes. <a href="../index.html">Easy BACnet</a> is an Android app that
    scans the network for BACnet IP devices, lists every one that answers, reads their
    points, and can write to them at a priority you choose and release them afterwards.
    BACnet has discovery built in, so once the phone is on the same subnet as the controllers
    a scan usually finds them within a minute. Getting the phone onto that subnet is the part
    that takes thought.</p>""",
    body_html="""
  <h2>Where a phone fits</h2>
  <p>A lot of service calls only need a few answers: is the controller talking, what is
  the discharge air temperature, is someone holding the damper at 100%. Opening a laptop
  and a full engineering tool for that is slow. With a USB-C Ethernet adapter, a phone
  plugged into the controls switch in the panel answers those questions in a couple of
  minutes.</p>

  <h2>Getting on the network</h2>
  <p>Controls networks are rarely on the building Wi-Fi. The usual way in is a spare port on
  the controls switch, or the BAS VLAN at an IT closet, with the adapter set to a static IP
  in the controls range (or DHCP, if that VLAN has it). A scan only covers the network
  the phone is on, so a phone on guest Wi-Fi or the office network finds nothing. See <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find
  my BACnet IP devices?</a> and <a href="subnets.html">what is a subnet, and why doesn't
  the switch give me the right one?</a></p>

  <h2>What a phone can and cannot reach</h2>
  <table>
    <tr><th>Situation</th><th>Works from the phone?</th></tr>
    <tr><td>BACnet/IP devices on the same subnet as the phone</td><td>Yes &mdash; the normal case, found by a scan</td></tr>
    <tr><td>A specific device you can reach by IP but a scan misses</td><td>Yes &mdash; add it directly by IP address</td></tr>
    <tr><td>MS/TP devices on an RS-485 trunk behind a BACnet router</td><td>Yes, through the router. See <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP vs BACnet/IP</a></td></tr>
    <tr><td>Devices on another subnet, through the site's BBMD</td><td>Yes &mdash; enter the BBMD address and the app registers as a foreign device</td></tr>
    <tr><td>Devices on another subnet, with no BBMD</td><td>Only one at a time, by IP &mdash; a scan doesn't cross a router</td></tr>
    <tr><td>An RS-485 trunk wired straight to the phone</td><td>No &mdash; the app speaks BACnet IP only</td></tr>
  </table>
  <p>Menu &rarr; Add device by IP&hellip; and
  menu &rarr; <strong>BBMD for remote networks&hellip;</strong> cover the other-subnet cases.</p>

  <h2>Reading is safe; writing has rails</h2>
  <p>Discovering and reading change nothing on the equipment. Writing is off every time the
  app starts and has to be turned on from the menu. Each write goes out at a priority you
  pick (8, Manual Operator, by default), the point is read back afterwards so you can see
  which priority is in command, and <strong>Release to Auto</strong> writes NULL to the
  priority slot holding the point (you pick it if several are held) to hand it back. See
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a> and <a href="how-to-write-to-a-bacnet-point.html">how to write to a
  BACnet point</a>.</p>

  <h2>What you walk away with</h2>
  <p>The devices and points the scan finds, with present values, units and status, can be
  exported as an Excel spreadsheet, which is a quick way to put a points list together on a
  site with no documentation. Walk through a full scan in
  <a href="how-to-use-easy-bacnet.html">how to use Easy BACnet</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/subnets", "What is a subnet, and why doesn't the switch give me the right one?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
        ("guides/what-is-bacnet", "What is BACnet?"),
    ],
))

GUIDES.append(dict(
    slug="guides/read-bacnet-values-from-phone",
    title="How to read BACnet values from a phone | Easy BACnet",
    question="How do I read BACnet values from a phone?",
    description="Step by step: join the controls network, discover BACnet IP devices, then open a point and read its live value, units and status on an Android phone.",
    answer_html="""<p>Get your phone onto the controls network, open
    <a href="../index.html">Easy BACnet</a>, tap <strong>Scan for Devices</strong>, then
    open the device and the point you want. Its live <strong>Present Value</strong>,
    <strong>Units</strong> and <strong>Status</strong> are shown, with a
    <strong>Refresh</strong> button for a fresh read. Reading changes nothing on the
    equipment, so it is safe on a live system. Once the phone is on the right subnet the
    whole thing takes a minute or two.</p>""",
    body_html="""
  <h2>What you need</h2>
  <ul>
    <li><strong>Your phone on the controls network.</strong> Usually that means a USB-C
    Ethernet adapter plugged into the controls switch (in a JACE or supervisory panel, or the
    BAS VLAN), with a static IP in the controls range or DHCP if that VLAN has it. A few sites
    have a controls Wi-Fi network. Guest Wi-Fi or mobile data reaches nothing. See
    <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my
    BACnet IP devices?</a> and <a href="subnets.html">the subnet guide</a> if the scan
    is empty.</li>
    <li><strong>No login.</strong> BACnet IP reads do not need a password. If the phone is on
    the right subnet and nothing is filtering UDP 47808, the controllers will answer.</li>
  </ul>

  <h2>Step 1 &mdash; Scan for devices</h2>
  <p>Open the app, tap the <strong>Easy BACnet Mode</strong> card, then <strong>Scan for
  Devices</strong>. The app finds every BACnet IP device on your network, then reads each
  one's name. It can take up to a minute; it keeps asking through the scan in case a reply
  gets lost, and a counter shows devices as they answer.</p>
  <figure class="shot">
    <img src="../img/scan.png" alt="Easy BACnet scanning a network and listing the BACnet IP devices that answered" loading="lazy">
    <figcaption>A scan in progress &mdash; devices appear as they answer.</figcaption>
  </figure>

  <h2>Step 2 &mdash; Open the device</h2>
  <p>Tap <strong>View Results</strong>. Each device shows its name, Device ID and IP
  address (devices behind a BACnet router show the router's IP). Tap one and the app reads
  its object list. It reads one entry at a time, which works on small controllers that
  cannot send the whole list in one reply, but a large controller takes a little while.</p>
  <figure class="shot">
    <img src="../img/devices.png" alt="A list of discovered BACnet IP devices with names, Device IDs and IP addresses" loading="lazy">
    <figcaption>Discovered devices, each with its name, Device ID and IP.</figcaption>
  </figure>

  <h2>Step 3 &mdash; Find the point</h2>
  <p>The device opens to its list of points: analog inputs, binary outputs, setpoints and
  so on. Names come from each object's <em>Object_Name</em>, so a well-commissioned
  controller shows names like <code>RTU-3 SA-T</code> and a factory-fresh one shows
  <code>AI-3</code>. On a very large controller only the first 2,000 objects load; if you
  know the object you want, menu &rarr; <strong>Add object by number</strong> reads it
  directly. For what the object types mean, see
  <a href="bacnet-object-types-explained.html">BACnet object types explained</a>.</p>
  <figure class="shot">
    <img src="../img/points.png" alt="The point list for a BACnet IP device showing analog and binary objects with live values" loading="lazy">
    <figcaption>A device's points, each showing its live value.</figcaption>
  </figure>

  <h2>Step 4 &mdash; Read the value</h2>
  <p>Tap the point. You get its <strong>Present Value</strong>, the <strong>Units</strong>
  the controller reports, the <strong>Status</strong> flags (in alarm, fault, overridden,
  out of service) and the <strong>Description</strong> if the device has one.
  <strong>Refresh</strong> reads it again.</p>
  <figure class="shot">
    <img src="../img/point.png" alt="A single BACnet point showing present value, units, status flags and description" loading="lazy">
    <figcaption>One point: present value, units, status, and whether anything is overriding it.</figcaption>
  </figure>
  <div class="callout">
  <p>On a commandable point you also see <strong>Commanded At</strong> and
  <strong>Falls Back To</strong>: which priority is currently in control and with what
  value, and the Relinquish_Default it goes to when every priority is released. See
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>
  </div>

  <h2>Reading is safe; writing is separate</h2>
  <p>Nothing above changes the equipment. Writing is a separate mode that is off every time
  the app starts. When you need it, see <a href="how-to-write-to-a-bacnet-point.html">how
  to write to a BACnet point</a>.</p>

  <h2>Getting every value at once</h2>
  <p>If you need more than a few points, <strong>Export Results</strong> reads every point
  on every device found and builds an Excel spreadsheet you can email or save, with names,
  present values, units and status. The full walkthrough is in
  <a href="how-to-use-easy-bacnet.html">how to use Easy BACnet</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?"),
        ("guides/bacnet-scanner-app-android", "Is there a BACnet IP scanner app for Android?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-device-shows-offline",
    title="BACnet IP device shows offline? Causes & fixes | Easy BACnet",
    question="Why does my BACnet IP device show offline?",
    description="A BACnet IP device showing offline is usually a network problem, not dead hardware: wrong subnet, dropped scan traffic, a firewall, or a duplicate ID.",
    answer_html="""<p>&ldquo;Offline&rdquo; means the head-end or your tool stopped getting
    answers from the device. More often than not that is a network or addressing problem
    rather than dead hardware. The usual causes: you are on a different subnet, the network
    is dropping scan traffic, an access list or firewall is blocking UDP 47808, two devices share a
    Device ID or MS/TP MAC, or the device has really lost power or its network link. First
    make sure the device itself is not answering; a point with a <em>Fault</em> flag on a
    device that does answer is a different problem.</p>""",
    body_html="""
  <h2>Offline or fault?</h2>
  <p>People use &ldquo;offline&rdquo; for two different things. A device that does not
  answer discovery or reads is a <strong>communication</strong> problem, and the rest of
  this guide covers that. A device that answers but has a point showing <em>Fault</em> or
  an impossible value (a zone temperature of -40, say) has a <strong>sensor or wiring</strong>
  problem. If you can open the device and read its points, it is not offline.</p>

  <h2>Work through these in order</h2>

  <h3>1. Are you on the same subnet?</h3>
  <p>Controls equipment normally sits on its own subnet or VLAN. A phone on guest Wi-Fi or
  the office network never hears the device, so everything looks offline. When a scan
  finds nothing, Easy BACnet shows the phone's IP address; compare it with the
  controller's. If they differ, see
  <a href="subnets.html">what is a subnet, and why doesn't the switch give me the
  right one?</a> A device on another subnet needs a
  BBMD or a direct add by IP (step 3).</p>

  <h3>2. Scan again</h3>
  <p>Scan traffic gets dropped, especially over Wi-Fi. A device that appears in one scan
  and not the next is usually this. The app keeps asking through the scan, but a second
  scan or a wired connection settles it.</p>

  <h3>3. Add it directly by IP</h3>
  <p>Menu &rarr; <strong>Add device by IP&hellip;</strong> goes straight to the device's
  address. If it answers, it is online and the scan just isn't reaching it: it's on another
  subnet, or the Wi-Fi is blocking scan traffic. If it does not answer, ping it from the
  <em>No devices found</em> screen: no reply means a network problem, a reply means the
  device's BACnet settings. Then carry on.</p>

  <h3>4. Is UDP 47808 blocked, or is the device on another port?</h3>
  <p>An access list between VLANs, or a device set to 47809 or another non-standard port,
  keeps it unreachable even from the right subnet. You can type the port in when adding by
  IP; the access list is a question for the network team. See
  <a href="what-port-does-bacnet-use.html">what port does BACnet use?</a></p>

  <h3>5. Does another device share its Device ID or MAC?</h3>
  <p>Two devices with the same Device Instance, or two MS/TP controllers with the same MAC
  on one trunk, answer for each other. The symptom is a device that drops in and out, or
  whose name and IP change between scans; a duplicate MAC also slows or breaks the whole
  trunk. The scan summary warns about both. See
  <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</p>

  <h3>6. It really is down</h3>
  <p>Lost power, a pulled patch cable, a dead switch port, or an MS/TP trunk that has gone
  quiet behind its router (open wire, missing termination, a shorted device). Check the
  controller's power and link lights. A ping from a laptop on the same network shows
  whether the IP side is alive: see
  <a href="is-my-bacnet-device-online-ping-test.html">is my BACnet device online?</a></p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet IP devices?"),
        ("guides/subnets", "What is a subnet, and why doesn't the switch give me the right one?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-write-access-denied",
    title="BACnet Write Access Denied — what it means | Easy BACnet",
    question="What does BACnet 'Write Access Denied' mean, and how do I fix it?",
    description="Write Access Denied means the BACnet property cannot be written that way: usually an input point, a read-only object, or a vendor lock on the point.",
    answer_html="""<p>&ldquo;Write Access Denied&rdquo; means the device received your write
    and refused it. Communication is fine. The common reasons: you wrote the Present_Value of
    an input point that is not Out Of Service; the object or property is read-only on that
    device (or on the gateway or JACE exposing it); or the vendor has locked the point.
    Retrying the same write will not help. Write to a different point, or change the
    device's configuration.</p>""",
    body_html="""
  <h2>What the error is</h2>
  <p>It is a BACnet Error reply to your WriteProperty with error class <em>property</em> and
  error code <em>write-access-denied</em>. Easy BACnet shows it as <em>Write failed: Write
  access denied</em>. It tells you the network and the device are working, and that the
  problem is the target of the write, not the value.</p>
  <p>Other codes point elsewhere. <em>invalid-data-type</em> means the value was the wrong
  kind (a REAL sent to a binary point, for example); <em>value-out-of-range</em> means the
  number is outside what the point accepts, such as state 5 on a three-state Multi-state
  Value; <em>unknown-object</em> or <em>unknown-property</em> means you addressed something
  that is not there.</p>

  <h2>Why a device refuses</h2>

  <h3>1. It is an input point</h3>
  <p>The Present_Value of an Analog Input, Binary Input or Multi-state Input comes from the
  physical input. The standard makes it writable only while <em>Out_Of_Service</em> is true,
  which disconnects the object from the sensor; otherwise the device refuses the write.
  Easy BACnet warns you before you try. Some devices also refuse Out_Of_Service writes from
  the network. If you meant to change a setpoint or command an output, look for the matching
  Analog Value, Binary Output or Analog Output instead. See
  <a href="bacnet-object-types-explained.html">BACnet object types explained</a>.</p>

  <h3>2. The object or property is read-only</h3>
  <p>Not every Value object is writable; the vendor or the programmer decides. Points
  exported from a JACE or a protocol gateway are often exposed read-only unless someone set
  them writable. Configuration properties such as Object_Name, Units and Description are
  commonly read-only too. If the device or gateway marks it read-only, there is no way
  round it over BACnet; it has to be changed in the device's configuration.</p>

  <h3>3. The vendor or the program has locked it</h3>
  <p>Some controllers lock points that their own logic drives, or only accept writes at
  certain priorities. Pushing past that on live equipment without knowing what the program
  expects is a bad idea. Ask the
  <a href="who-to-call-it-hvac-or-controls.html">controls contractor</a> which points are
  meant to be commanded from outside.</p>

  <h2>What does not cause it</h2>
  <p>Leaving the priority out does not. A WriteProperty to a commandable Present_Value with
  no priority is stored at priority 16, the lowest; it is accepted but may be outranked. That
  is the &ldquo;I wrote it and nothing changed&rdquo; case, covered in
  <a href="bacnet-value-does-not-change-when-written.html">why doesn't my BACnet
  value change when I write to it?</a> Easy BACnet always sends a priority (8 by
  default).</p>
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
    description="You wrote a BACnet point and nothing changed. Usually a higher priority already commands it, the program overwrites it, or the output is overridden locally.",
    answer_html="""<p>You wrote the point, the device accepted it, and nothing happened.
    Re-read the point. If the <strong>Present Value did not change</strong>, a higher
    priority is in command and your write is sitting in its slot underneath it. If the
    <strong>value changed but the equipment did not</strong>, the output is overridden at
    the equipment, the point is Out Of Service, or the equipment has a fault. If the value
    <strong>changed and then went back</strong>, the controller's program is writing it.
    In Easy BACnet, <strong>Commanded At</strong> on the point screen shows which priority is
    in control, which usually tells you which case you have.</p>""",
    body_html="""
  <h2>First, re-read the point</h2>
  <p>Easy BACnet re-reads the point after every write, so the value on screen is what the
  device reports, not what you sent. Compare it with what you wrote and look at
  <strong>Commanded At</strong>. Then pick the case below.</p>

  <h2>Case 1 &mdash; the value did not change</h2>
  <p>A commandable point has a 16-slot priority array and follows the highest-priority slot
  that is not NULL (1 is highest). If something holds slot 5 and you write at slot 8, your
  value is stored but the point keeps following slot 5. <strong>Commanded At</strong> shows
  the winning priority and its value.</p>
{{fig:priority}}
  <p>Two things to check:</p>
  <ul>
    <li><strong>Which slot is winning?</strong> By the standard, 1 and 2 are manual and
    automatic life safety, 5 is critical equipment control, and 6 is minimum on/off (a
    fan's minimum run time holding a Binary Output, for example). If one of those holds the
    point there is usually a reason; leave it until you know what it is. Anything else above
    8 may be a head-end, a sequence, or an override another tech left behind.</li>
    <li><strong>Did your write carry a priority?</strong> A WriteProperty with no priority
    lands at 16, the lowest, so almost anything outranks it. Easy BACnet always sends one
    (8 by default); some other tools and scripts do not.</li>
  </ul>
  <p>Usually the right fix is to <strong>release</strong> the slot that should not be held
  (write NULL at that priority) so the point goes back to its program, rather than writing
  at a higher priority and stacking another override on top. See
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>

  <h2>Case 2 &mdash; the value changed, the equipment did not</h2>
  <p>The controller shows your value but the fan did not start or the valve did not move.
  The command got through; look past the BACnet side:</p>
  <ul>
    <li><strong>The point is Overridden.</strong> The <em>Overridden</em> status flag means
    something local is forcing the output, typically a hand/off/auto switch on the controller
    or the starter. Nothing written over the network moves it.</li>
    <li><strong>The point is Out Of Service.</strong> The object is disconnected from its
    hardware, so Present_Value changes but drives nothing.</li>
    <li><strong>The equipment has a fault.</strong> A tripped overload, a compressor on
    lockout, a failed actuator, a VFD in fault. The command is right; the mechanical or
    electrical side is not.</li>
  </ul>
  <p>Check the point's status flags. Overridden and
  Out Of Service are for the controls side; a healthy point driving dead equipment is for
  the mechanical or electrical side.</p>

  <h2>Case 3 &mdash; the value changed, then went back</h2>
  <p>The controller's program is writing the same point. Often it is a non-commandable
  Analog Value that the program sets every scan, so the last write wins and the program
  writes last. Or the sequence commands it at a priority at or above yours. Either way you
  cannot hold it from outside, and on a live system you should not try. The program needs
  changing, or the sequence needs a proper override point, which is a job for the
  <a href="who-to-call-it-hvac-or-controls.html">controls contractor</a>.</p>

  <h2>If the write was refused instead</h2>
  <p>If the device answered with an error rather than accepting the write, see
  <a href="bacnet-write-access-denied.html">what does BACnet Write Access Denied
  mean?</a> Input points and read-only objects fall there.</p>
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
    answer_html="""<p>Scan the network, then export. <a href="../index.html">Easy BACnet</a>
    reads every point on every device it found and builds an Excel spreadsheet
    (<code>.xlsx</code>): a device summary at the top, then one row per point with Device ID,
    Device Name, Device IP, Object Type, Object Number, Point Name, Present Value, Units and
    Status. Your phone's share sheet opens so you can email it or save it to Drive or Files.
    The app does not write CSV directly; open the file in Excel or Google Sheets and save it
    as CSV if that is what was asked for. An <strong>EDE file</strong> (Engineering Data
    Exchange) is a fixed-column CSV layout used to import points into another BACnet tool or
    head-end.</p>""",
    body_html="""
  <h2>What people mean by &ldquo;a points list&rdquo;</h2>
  <p>When an integrator, an analytics vendor or a new service contractor asks for a points
  list, they want a table of what is on each controller: object name, object type and
  instance, and usually the live value and units. BACnet devices can be asked what objects
  they contain, so the list can be read off the devices instead of dug out of old
  submittals. See
  <a href="what-is-a-bacnet-points-list.html">what is a BACnet IP points list?</a></p>

  <h2>Step by step: collect and export from a phone</h2>
  <ol>
    <li><strong>Get on the controls network.</strong> Usually a USB-C Ethernet adapter into
    the controls switch or BAS VLAN, with an IP in the controls range.</li>
    <li><strong>Scan.</strong> Open Easy BACnet, tap <strong>Easy BACnet Mode</strong>, then
    <strong>Scan for Devices</strong>. Wait for <em>Success! Found N device(s)</em> (up to a
    minute). For controllers on other subnets, add them with menu &rarr; <strong>Add device
    by IP&hellip;</strong> or set <strong>BBMD for remote networks&hellip;</strong> and scan
    again. Everything in the device list is exported.</li>
    <li><strong>Check it (optional).</strong> <strong>View Results</strong> lists every device;
    tap one to see its points. Very large controllers load the first 2,000 objects; reach a
    specific object beyond that with <strong>Add object by number</strong>.</li>
    <li><strong>Export.</strong> Tap <strong>Export Results</strong>. On the free version you
    are asked <em>Watch a short ad?</em> first (<strong>Watch ad</strong> / <strong>Remove
    ads</strong> / <strong>Cancel</strong>); if no ad can load, the export just runs. The app
    re-reads each device's object list and every present value, one property at a time; the
    progress box shows <em>Point list: x of y</em> then <em>Values: x of y</em> for each
    device. A site with big MS/TP controllers takes a while. Stay connected until it
    finishes, or tap <strong>Cancel</strong>.</li>
    <li><strong>Share or save.</strong> The share sheet opens (<em>Send export by email</em>)
    with <code>EasyBACnet_YYYYMMDD_HHMM.xlsx</code> attached, the subject <em>BACnet IP
    Export</em> plus the date, and a line giving the device and point counts. Pick an email
    app and add the recipient, or pick Drive, Files or a messenger. Nothing is sent until you
    send it.</li>
  </ol>

  <h2>What the spreadsheet contains</h2>
  <p>One sheet with two tables:</p>
  <table>
    <tr><th>Section</th><th>Columns</th></tr>
    <tr><td>Device summary (top)</td><td><em>Devices Found</em> count, then per device: Device ID, Device Name, Device IP, Points (how many)</td></tr>
    <tr><td>Point detail (below)</td><td>Device ID, Device Name, Device IP, Object Type, Object Number, Point Name, Present Value, Units, Status</td></tr>
  </table>
  <ul>
    <li>Each device gets a bold row of its own in the detail table (Object Type
    <em>Device</em>), so every controller and its IP is listed even if it returned no
    points.</li>
    <li>Any point whose <strong>Status</strong> is not <em>Normal</em> (in alarm, fault,
    overridden or out of service) is shaded red.</li>
    <li>Device IDs, object numbers and counts are stored as numbers, so sorting and filtering
    work straight away. Present values keep the app's formatting (e.g. <em>Active (On)</em> for a
    binary point) and units use short symbols such as °F, % RH or kW.</li>
    <li>Descriptions and priority arrays are not exported; open a point in the app to see
    those.</li>
  </ul>

  <h2>Need a CSV?</h2>
  <p>Open the <code>.xlsx</code> in Excel and use <em>File &rarr; Save As &rarr; CSV UTF-8</em>
  (Google Sheets: <em>File &rarr; Download &rarr; CSV</em>). If you only want the point detail,
  delete the summary rows above the detail header first so the file has a single header row,
  which is what most import tools expect.</p>

  <h2>Excel/CSV versus EDE</h2>
  <table>
    <tr><th></th><th>Easy BACnet export</th><th>EDE file</th></tr>
    <tr><td>What it is</td><td>A plain table of the network's devices, objects and live values</td><td>A CSV in a fixed column layout meant for importing</td></tr>
    <tr><td>Opens in Excel</td><td>Yes (.xlsx; save as CSV if needed)</td><td>Yes</td></tr>
    <tr><td>Best for</td><td>A site survey, a vendor request, records, troubleshooting</td><td>Bulk-importing points into another BACnet tool, head-end or analytics platform</td></tr>
    <tr><td>Contains</td><td>Names, live values, units, status, object IDs, device IPs</td><td>Device and object names, object type and instance, description, settable, COV support, unit code, state-text references and similar engineering fields</td></tr>
  </table>
  <p>EDE came out of the European BACnet Interest Group as a common way to hand a point
  list between tools. If someone specifically asks for &ldquo;an EDE&rdquo;, they mean that
  layout. If they just say &ldquo;send me the points&rdquo;, a spreadsheet with clear names
  and values is usually what they want, and it can be reshaped into an EDE template later
  if needed.</p>

  <div class="callout">
  <p>An export read from the live devices shows what the controllers actually contain
  today, which is often not what the original submittal says. See
  <a href="vendor-asking-for-bacnet-information.html">a vendor asked for my BACnet
  information</a>.</p>
  </div>

  <h2>Privacy</h2>
  <p>The export is built on your phone and kept in the app's private cache; the app has no
  server and sends nothing itself. Once you share it, it goes wherever you send it. A points
  list is a map of a building's controls, so send it to a named person, not a shared inbox.
  Details are in the <a href="../privacy.html">privacy policy</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?"),
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
    answer_html="""<p>You do not need the head-end to prove a BACnet IP controller is up and
    working. Any BACnet client on the same subnet can do it, including
    <a href="../index.html">Easy BACnet</a> on a phone. Plug into the network, run a scan,
    and if the controller shows up with its Device ID it is powered, addressed and speaking
    BACnet. Read its inputs to check the sensors make sense, then, where it is safe,
    command an output, watch the equipment respond, and release it. That is a useful
    point-to-point check before the BMS is connected.</p>""",
    body_html="""
  <h2>Why you can do this without the BMS</h2>
  <p>BACnet IP has no login and no single master. A head-end is a BACnet client with
  graphics, trends and schedules on top; a handheld client can do the same discovery, reads
  and writes. That makes a phone handy at start-up, for checking a replacement controller,
  or for &ldquo;is this new RTU controller talking yet?&rdquo; before the integrator has it
  in the Supervisor.</p>

  <h2>Before you start</h2>
  <p>A new controller is often still on its factory IP address and Device ID. Find out what
  they are (label, manual, or the commissioning tool) and give your phone's Ethernet adapter
  a static IP on that subnet. If two new controllers share the same default Device ID, sort
  that out before anything else; see
  <a href="duplicate-bacnet-device-id.html">duplicate Device IDs</a>.</p>

  <h2>The test, step by step</h2>

  <h3>1. Prove it is on the network (discovery)</h3>
  <p>Run a scan. If the controller shows up with its Device ID and IP, it is
  powered, on the network and speaking BACnet/IP. If it does not answer, that is a network
  or addressing problem first, not necessarily a dead controller: see
  <a href="bacnet-device-shows-offline.html">why does my BACnet IP device show offline?</a></p>

  <h3>2. Check the inputs</h3>
  <p>Open the device and read its input points. Do the values make sense? A zone
  temperature around 70&nbsp;°F, an outdoor air temperature that matches the weather, a
  damper feedback between 0 and 100%. A point flagged <em>Fault</em>, or reading -40 or
  250, usually means an open or shorted sensor, a wiring error, or the wrong sensor type
  configured.</p>

  <h3>3. Check the outputs respond</h3>
  <p>On a commandable output, write a value at priority 8 and watch the equipment: the
  valve strokes, the fan starts, the feedback point follows. Then <strong>release
  it</strong> so you do not leave an override behind, and re-read to confirm it went back
  to auto. Only do this where moving the equipment is safe and the people on site know. See
  <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet point</a> and
  <a href="bacnet-priority-and-stuck-overrides.html">priority and stuck overrides</a>.</p>
{{fig:writeflow}}

  <h2>What a phone test can and cannot tell you</h2>
  <ul>
    <li><strong>Can</strong>: confirm the controller is online, that inputs read sensible
    values, that outputs respond to commands, and capture the lot as a
    <a href="export-bacnet-points-to-csv.html">spreadsheet</a> for the record.</li>
    <li><strong>Cannot</strong>: discover a whole other subnet without a
    BBMD (one known device can be
    added by IP), or connect straight to an MS/TP
    trunk; MS/TP controllers need a BACnet router. And it does not check schedules, trends,
    alarms or the full sequence of operation. It proves the controller and its I/O work, not
    that the programming is right.</li>
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
    slug="guides/does-easy-bacnet-support-mstp-rs485",
    title="Does Easy BACnet support MS/TP or RS-485? | Easy BACnet",
    question="Does Easy BACnet support MS/TP or RS-485?",
    description="No. Easy BACnet is a BACnet IP tool and does not connect to an MS/TP (RS-485) trunk directly, but it reads MS/TP devices routed onto IP by a BACnet router.",
    answer_html="""<p><strong>Not directly.</strong> Easy BACnet speaks <strong>BACnet
    IP</strong>, over Wi-Fi or a USB-C Ethernet adapter. A phone has no RS-485 port, so the
    app can't land on an <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> trunk by itself.
    What it <em>can</em> do is read and command MS/TP controllers that sit behind a BACnet
    router: the router puts them on the IP side, and the app talks to them through it.</p>""",
    body_html="""
  <h2>What works and what doesn't</h2>
  <ul>
    <li><strong>Wiring into an MS/TP trunk: no.</strong> The app does not talk RS-485, and
    a phone has no hardware for it.</li>
    <li><strong>MS/TP behind a BACnet router: yes.</strong> If a router (standalone, or a
    supervisory controller with routing turned on) connects the trunk to BACnet IP, those
    controllers answer a scan through the router. You can browse their points, read, write
    and release just like an IP device. <strong>Browser Mode</strong> shows each routed
    device's network number and MAC address so you can tell which trunk it lives on.</li>
  </ul>
{{fig:network}}

  <div class="callout">
  <p>If the only way to your controllers is a bare RS-485 trunk with no router onto IP, no
  phone app will reach them. Something has to route that trunk onto the IP network first.</p>
  </div>

  <h2>Why a phone can't touch MS/TP</h2>
  <p><a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> is BACnet on a twisted pair
  (plus a reference/shield) running RS-485, usually at 38,400 or 76,800 baud, with a token
  passed from MAC address to MAC address. BACnet IP is the same protocol carried in UDP on
  port 47808 over Ethernet. Getting on the wire directly takes a USB-to-RS-485 adapter and
  MS/TP software on a laptop. A phone only has the IP side, so that is where the app stays.</p>

  <h2>Reaching MS/TP controllers in practice</h2>
  <ul>
    <li><strong>Find the router.</strong> On most jobs the MS/TP trunks land on a supervisory
    controller (a JACE, an NAE/SNE, a Desigo PXC, an AS-P and so on) or on a standalone
    BACnet router in the same panel. Plug into the controls switch in that panel and scan.</li>
    <li><strong>Polled is not the same as routed.</strong> A supervisory controller can poll
    its MS/TP trunk for the head-end without routing it onto IP. In that case the field
    controllers show up in the BAS front end but not in a scan. Whether routing is enabled is
    a <a href="who-to-call-it-hvac-or-controls.html">question for the controls contractor</a>,
    not IT.</li>
    <li><strong>Missing a whole trunk?</strong> If the IP controllers show up but the VAVs on
    one trunk don't, suspect the router or that trunk (wiring, termination, a dead
    controller pulling the bus down) before the app.</li>
  </ul>

  <h2>Will the app ever do MS/TP directly?</h2>
  <p>Not on a phone. For work on the trunk itself, use a laptop with an RS-485 adapter and
  MS/TP software. Easy BACnet stays a BACnet IP tool.</p>
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
    answer_html="""<p>It depends which layer is broken. If you <strong>can't reach the
    controllers on the network</strong> (nothing scans, wrong VLAN, a firewall), start with
    whoever owns the <strong>network</strong>. If the controllers answer but <strong>the
    equipment itself won't run</strong> (a fan that won't start, a tripped compressor, a
    leak), call the <strong>HVAC / mechanical</strong> contractor. If the equipment runs but
    <strong>the points, schedules, setpoints or overrides are wrong</strong>, call the
    <strong>controls / BMS contractor</strong> who programmed it. Easy BACnet helps you work
    out which one you're looking at before you pick up the phone.</p>""",
    body_html="""
  <h2>Who owns what</h2>
  <p>On most buildings the network, the equipment and the control programming belong to
  different people. Calling the right one first saves a wasted site visit.</p>
{{fig:whotocall}}

  <h3>IT / network</h3>
  <p>Owns switches, VLANs, IP ranges, Wi-Fi and firewalls. Call them about
  <strong>reachability</strong>: you can't get a port on the controls VLAN, you're on the
  wrong <a href="subnets.html">subnet</a>, or something is blocking UDP 47808 between you
  and the controllers. One catch: on a lot of older sites the controls contractor installed
  and still owns the BAS switches, and IT has never touched them. Ask before you assume.</p>

  <h3>HVAC / mechanical contractor</h3>
  <p>Owns the physical equipment: RTUs, AHUs, chillers, boilers, pumps, fans, VFDs,
  dampers, valves. Call them when the <strong>machine</strong> is the problem. A typical
  example: the BO for <code>AHU-1 SF-C</code> reads On, the VFD shows no fault on the network,
  but there's no airflow because a belt is gone.</p>

  <h3>Controls / BMS contractor</h3>
  <p>Also called the ATC or temperature controls contractor. They programmed and
  commissioned the controllers and the head-end (Niagara, Metasys, Desigo CC, EBO, WebCTRL
  and so on). Call them when the equipment is healthy and reachable but the
  <strong>logic</strong> is wrong: a point
  <a href="bacnet-priority-and-stuck-overrides.html">stuck in override</a>, a schedule not
  running, a setpoint that won't hold, a
  <a href="duplicate-bacnet-device-id.html">duplicate Device ID</a>, or MS/TP controllers
  that aren't routed onto IP. On some jobs the controls contractor works under the
  mechanical contractor, so your first call may still go to mechanical.</p>

  <h2>Symptom &rarr; who to call first</h2>
  <table>
    <tr><th>What you're seeing</th><th>Call first</th></tr>
    <tr><td>Scan finds nothing; you're on office or guest Wi-Fi, or the wrong VLAN</td><td>Network owner</td></tr>
    <tr><td>Some controllers answer but a firewall or VLAN blocks others</td><td>Network owner</td></tr>
    <tr><td>You need a static IP, a port on the controls VLAN, or a route to another subnet</td><td>Network owner</td></tr>
    <tr><td>The controller answers and commands the output, but the fan/pump/compressor won't run</td><td>HVAC / mechanical</td></tr>
    <tr><td>No heat or cooling with no control fault, a leak, a unit locked out on a safety</td><td>HVAC / mechanical</td></tr>
    <tr><td>A point is commanded and nobody knows who left it there</td><td>Controls / BMS</td></tr>
    <tr><td>Schedule, setpoint or sequence not behaving</td><td>Controls / BMS</td></tr>
    <tr><td>Duplicate Device IDs, unconfigured controllers, missing points</td><td>Controls / BMS</td></tr>
    <tr><td>MS/TP controllers visible in the head-end but not in a scan</td><td>Controls / BMS</td></tr>
    <tr><td>Remote subnets need a BBMD or foreign-device registration</td><td>Controls / BMS, with the network owner</td></tr>
  </table>

  <h2>What to have ready</h2>
  <ul>
    <li><strong>Your phone's IP address.</strong> The app shows it on the scan screen, with a
    Copy button. That's the first thing a network person will ask for.</li>
    <li><strong>The Device ID, name and IP</strong> of the controller in question.</li>
    <li><strong>The point and what it's doing:</strong> Present Value, units, status, and the
    <em>Commanded At</em> priority from the point screen.</li>
    <li><strong>What you expected versus what you saw.</strong> &ldquo;RTU-3 SF-C reads On,
    commanded at priority 8, fan not turning&rdquo; tells everyone whose problem it is.</li>
    <li><strong>Where you're plugged in:</strong> which panel, switch and port.</li>
  </ul>
  <p>For a controls call, an exported spreadsheet of the device's points is often the
  quickest thing to send. See
  <a href="vendor-asking-for-bacnet-information.html">what to send when a vendor asks for
  your BACnet information</a>.</p>

  <h2>The grey areas</h2>
  <ul>
    <li><strong>&ldquo;I can't find any devices.&rdquo;</strong> Usually a network or
    which-port-am-I-in problem first. If you're definitely on the controls VLAN and the
    missing controllers are MS/TP, it becomes a controls question: are those trunks
    <a href="does-easy-bacnet-support-mstp-rs485.html">routed onto IP</a>?</li>
    <li><strong>&ldquo;The value looks wrong.&rdquo;</strong> Check the
    status flags. A FAULT on a sensor is
    usually wiring or a failed sensor (controls, sometimes mechanical). A sane value that
    nothing acts on is usually an override or sequence problem (controls).</li>
    <li><strong>&ldquo;It worked yesterday.&rdquo;</strong> Ask what changed: a network change,
    a failed part, or someone editing the program.</li>
  </ul>

  <h2>Where Easy BACnet fits</h2>
  <p>The app shows what's on the BACnet IP network, what each point reads, and which
  priority is commanding it. That's enough to call the right people with evidence. It won't
  fix a VLAN, a motor or a sequence, and it is
  <a href="does-easy-bacnet-support-mstp-rs485.html">BACnet IP only</a>.</p>
""",
    related=[
        ("guides/subnets", "Why am I on the wrong network even though I'm plugged into the switch?"),
        ("guides/cant-find-what-im-looking-for", "What do I do if I can&rsquo;t find my BACnet devices?"),
        ("guides/does-easy-bacnet-support-mstp-rs485", "Does Easy BACnet support MS/TP or RS-485?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/what-is-bacnet",
    title="What is BACnet? A plain-English guide | Easy BACnet",
    question="What is BACnet?",
    description="BACnet is the standard protocol building controls use to talk over a network: HVAC, lighting, metering. What it is, how BACnet IP works, how to see it.",
    answer_html="""<p><strong>BACnet is the open protocol most building controls use to
    talk to each other and to the BAS front end.</strong> It's defined by ASHRAE Standard 135
    (also ISO 16484-5), so a VAV controller from one manufacturer can be read by a head-end
    from another. On most sites it runs as <strong>BACnet IP</strong> (UDP port 47808) on a
    controls network or VLAN kept apart from the office network, with smaller field
    controllers on <strong>MS/TP</strong> serial trunks behind routers. Each controller is a
    <em>device</em>; each value inside it, such as a temperature, a fan command or a setpoint,
    is an <em>object</em>, usually called a <em>point</em>. Easy BACnet shows all of that on a
    phone connected to the BACnet IP network.</p>""",
    body_html="""
  <h2>Why it exists</h2>
  <p>Before BACnet, each controls manufacturer had its own proprietary protocol, and mixing
  brands meant gateways or a rip-and-replace. ASHRAE published BACnet in 1995 as a
  vendor-neutral standard for how controllers describe themselves and exchange values. Today a
  Trane RTU controller, a JCI VAV controller and a Schneider power meter can sit on the same
  network and be read by the same tool.</p>

  <h2>Devices, objects and properties</h2>
{{fig:objects}}
  <ul>
    <li><strong>Device</strong>: one controller, gateway or smart piece of equipment. It has a
    <a href="bacnet-device-id-explained.html">Device ID</a> (instance number) that must be
    unique on the whole BACnet network, and on BACnet IP an IP address.</li>
    <li><strong>Object</strong>: one thing inside the device, such as an Analog Input for a
    space temp, a Binary Output for a fan start/stop, or an Analog Value for a setpoint. Each
    has an <a href="bacnet-object-types-explained.html">object type</a> and an instance
    number.</li>
    <li><strong>Property</strong>: a field on an object. <code>Present_Value</code> is the one
    you usually want; others include <code>Object_Name</code>, <code>Units</code>,
    <code>Status_Flags</code> and <code>Description</code>.</li>
  </ul>
  <p>Every device keeps an <code>Object_List</code> property naming all its objects. Read out
  with names and values, that's its <a href="what-is-a-bacnet-points-list.html">points
  list</a>.</p>

  <h2>Finding devices</h2>
  <p>A tool doesn't need to know addresses up front. It asks the whole network &ldquo;who's
  out there?&rdquo; and every BACnet device answers with its Device ID. That's what happens
  when you tap <strong>Scan for Devices</strong> in Easy BACnet. The question only reaches
  your own subnet (unless the site has a BBMD to pass it on), so a device on another subnet
  won't show up in a plain scan. The technical names for the question and answer are
  <a href="who-is-i-am-explained.html">Who-Is and I-Am</a>.</p>

  <h2>BACnet IP and MS/TP</h2>
  <ul>
    <li><strong>BACnet IP</strong> runs over Ethernet on
    <a href="what-port-does-bacnet-use.html">UDP 47808</a>. Supervisory controllers, plant
    controllers and many newer field controllers use it. This is what a phone or laptop
    reaches, usually by plugging into a controls switch or joining the BAS VLAN.</li>
    <li><strong><a href="bacnet-mstp-vs-bacnet-ip.html">BACnet MS/TP</a></strong> runs on an
    RS-485 twisted pair and is common for VAVs, fan coils and unit controllers. A phone can't
    reach MS/TP directly, but devices behind a BACnet router are reachable over IP.</li>
  </ul>

  <div class="callout">
  <p><strong>Where Easy BACnet fits.</strong> It's a BACnet IP browser. Get the phone onto the
  controls network, scan, and it lists the devices, their points, live values, and which
  priority is commanding each point. With write mode on it can also command and release
  points. It doesn't connect to an MS/TP trunk directly.</p>
  </div>

  <h2>What it's used for</h2>
  <p>Mostly HVAC: AHUs, RTUs, VAVs, chillers, boilers, pumps, fan coils. Also lighting
  panels, power and utility meters, and some integrations with access control and fire
  systems. If a building has a BAS or BMS, BACnet is very often what's underneath it.</p>

  <h2>See it for yourself</h2>
  <p>The quickest way to understand it is to look at a live system:
  <a href="how-to-use-easy-bacnet.html">run a scan</a>, open a device and browse its points.
  Keep the <a href="bacnet-glossary.html">BACnet glossary</a> handy for the terms.</p>
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
    answer_html="""<p><strong>Plain-English definitions of the BACnet terms you'll run into on
    the job.</strong> A <em>device</em> is one controller; an <em>object</em> (usually called a
    <em>point</em>) is one value inside it; <em>Present_Value</em> is its current reading or
    command. Device ID, object types, the priority array, Who-Is/I-Am, BBMDs and MS/TP are
    below, each linked to a longer guide.</p>""",
    body_html="""
  <h2>The basics</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong>BACnet</strong></td><td>The open building-automation protocol defined by ASHRAE 135 / ISO 16484-5. See <a href="what-is-bacnet.html">What is BACnet?</a></td></tr>
    <tr><td><strong>Device</strong></td><td>One controller, gateway or piece of equipment on the network. Has a Device ID and, on BACnet IP, an IP address.</td></tr>
    <tr><td><strong>Object</strong></td><td>One thing inside a device: an input, an output, a setpoint, a schedule. Has a type and an instance number.</td></tr>
    <tr><td><strong>Point</strong></td><td>The everyday word for an object you read or command. A device's full set is its <a href="what-is-a-bacnet-points-list.html">points list</a>.</td></tr>
    <tr><td><strong>Property</strong></td><td>A field on an object, e.g. <code>Object_Name</code>, <code>Present_Value</code>, <code>Units</code>, <code>Status_Flags</code>.</td></tr>
    <tr><td><strong>Present_Value</strong></td><td>The current reading (inputs) or current command/value (outputs and values).</td></tr>
    <tr><td><strong>Object_List</strong></td><td>A property of the Device object listing every object in it. Reading it is how a tool builds the points list.</td></tr>
  </table>

  <h2>Identifying and finding things</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong><a href="bacnet-device-id-explained.html">Device ID</a></strong></td><td>The device's instance number, 0&ndash;4194302, unique across the whole BACnet network (including routed MS/TP). Not the IP address. 4194303 is reserved as a wildcard.</td></tr>
    <tr><td><strong><a href="bacnet-object-types-explained.html">Object type</a></strong></td><td>What kind of object it is: Analog Input (AI), Binary Output (BO), Multi-state Value (MSV) and so on.</td></tr>
    <tr><td><strong>Instance number</strong></td><td>Which one of that type in the device: AI 1, AI 2, AV 3001.</td></tr>
    <tr><td><strong>Object Identifier</strong></td><td>Type and instance packed into one 32-bit number (10 bits type, 22 bits instance). Our <a href="../bacnet-object-id-decoder.html">decoder tool</a> splits it apart.</td></tr>
    <tr><td><strong><a href="who-is-i-am-explained.html">Who-Is / I-Am</a></strong></td><td>The broadcast request and the replies that let a tool discover devices without knowing their addresses.</td></tr>
    <tr><td><strong>Segmentation</strong></td><td>Splitting a large reply across several packets. Small controllers often don't support it, which is why tools read a big Object_List one entry at a time.</td></tr>
  </table>

  <h2>Commanding and overrides</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong><a href="bacnet-priority-and-stuck-overrides.html">Priority array</a></strong></td><td>16 slots on a commandable object. The lowest-numbered slot holding a value wins (1 is highest).</td></tr>
    <tr><td><strong>Command priority</strong></td><td>The slot (1&ndash;16) you write at. 8 is conventionally Manual Operator; 1&ndash;2 are life safety, 5 critical equipment, 6 minimum on/off; programs often use 10&ndash;16.</td></tr>
    <tr><td><strong>Relinquish_Default</strong></td><td>The value the object uses when every priority slot is empty.</td></tr>
    <tr><td><strong>Release (relinquish)</strong></td><td>Writing NULL to a slot to clear it. See <a href="bacnet-priority-and-stuck-overrides.html">how to release an override</a>.</td></tr>
    <tr><td><strong>Commandable</strong></td><td>Has a priority array. Analog/Binary/Multi-state Outputs always do; Values (AV, BV, MSV) only if the vendor built them that way. Inputs never do.</td></tr>
    <tr><td><strong>Out_Of_Service</strong></td><td>A property that disconnects <code>Present_Value</code> from the physical I/O so it can be written for testing.</td></tr>
    <tr><td><strong>Status_Flags</strong></td><td>Four flags on a point: IN_ALARM, FAULT, OVERRIDDEN, OUT_OF_SERVICE.</td></tr>
  </table>

  <h2>Networking and wiring</h2>
  <table>
    <tr><th>Term</th><th>What it means</th></tr>
    <tr><td><strong>BACnet IP</strong></td><td>BACnet in UDP over Ethernet, normally on <a href="what-port-does-bacnet-use.html">port 47808</a> (0xBAC0). What a phone can reach.</td></tr>
    <tr><td><strong><a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a></strong></td><td>BACnet over an RS-485 twisted pair, common for VAVs and unit controllers. Devices are addressed by a MAC (0&ndash;127 for masters). A phone can't reach it directly.</td></tr>
    <tr><td><strong>BACnet router</strong></td><td>Connects BACnet networks, typically MS/TP trunks to BACnet IP, so routed devices can be reached from IP.</td></tr>
    <tr><td><strong>Network number</strong></td><td>The BACnet number of a network segment (e.g. each MS/TP trunk). Routed devices are addressed by network number plus MAC.</td></tr>
    <tr><td><strong>BBMD</strong></td><td>BACnet/IP Broadcast Management Device. Forwards BACnet broadcasts such as Who-Is between IP subnets, and accepts foreign-device registrations.</td></tr>
    <tr><td><strong>Foreign device</strong></td><td>A tool on another subnet that registers with a BBMD so it can send and receive broadcasts through it.</td></tr>
    <tr><td><strong><a href="subnets.html">Subnet</a></strong></td><td>The IP range your phone is on. A broadcast scan only reaches devices on the same subnet unless a BBMD is used.</td></tr>
    <tr><td><strong>BACnet/SC</strong></td><td>Secure Connect, a newer TLS-based BACnet transport. Easy BACnet doesn't speak it; it's BACnet IP only.</td></tr>
  </table>

  <div class="callout">
  <p>New to this? Start with <a href="what-is-bacnet.html">What is BACnet?</a>, then come back
  here when a term trips you up.</p>
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
    description="BACnet analog points carry an engineering-units code: degrees F, inches of water, %RH, CFM and many more. What the Units property is and how to read it.",
    answer_html="""<p><strong>Analog BACnet points carry a <code>Units</code> property, a
    standard code that says what the number means.</strong> A Present_Value of
    <code>55.0</code> on <code>AHU-1 SA-T</code> is just a number; with
    <code>Units = degrees-Fahrenheit</code> it's 55&nbsp;&deg;F supply air. The standard fixes
    the list of codes, so the same code means the same thing on every brand. Easy BACnet reads
    the code and shows a short name next to the value (&deg;F, % RH, CFM).</p>""",
    body_html="""
  <h2>What the Units property is</h2>
  <p>Analog Inputs, Outputs and Values all have a <code>Units</code> property alongside
  <code>Present_Value</code>. It holds an enumerated code from the BACnet standard, for
  example 64 for degrees-Fahrenheit, 62 for degrees-Celsius, 58 for inches-of-water, 84 for
  cubic-feet-per-minute and 98 for percent. Binary and multi-state objects have no
  <code>Units</code> property at all; their meaning comes from their states.</p>
  <p>Easy BACnet reads the code and shows a readable label in the Units row of the point
  screen, so <code>RM-214 ZN-T</code> reads as 72.4 with units &deg;F. If a
  device returns a code the app doesn't have a name for, you'll see it as &ldquo;units&nbsp;N&rdquo;
  with the raw number, which you can look up in the standard.</p>

  <h2>Units you'll see most</h2>
  <table>
    <tr><th>Category</th><th>Typical units</th><th>Seen on</th></tr>
    <tr><td>Temperature</td><td>&deg;F, &deg;C</td><td>Zone, supply, return, mixed, outdoor air; water temps; setpoints</td></tr>
    <tr><td>Humidity</td><td>% RH</td><td>Zone and duct humidity, outdoor air</td></tr>
    <tr><td>Air pressure</td><td>in of water, Pa</td><td>Duct static, filter DP, building static</td></tr>
    <tr><td>Water pressure</td><td>psi, kPa</td><td>Loop DP, pump discharge</td></tr>
    <tr><td>Air flow</td><td>CFM, L/s</td><td>VAV boxes, outdoor air stations</td></tr>
    <tr><td>Water flow</td><td>GPM, L/s</td><td>Chilled and hot water loops</td></tr>
    <tr><td>Percent</td><td>%</td><td>Damper and valve commands, VFD speed</td></tr>
    <tr><td>Power and energy</td><td>kW, kWh, A, V</td><td>Meters, VFDs</td></tr>
    <tr><td>Air quality</td><td>ppm</td><td>CO2 sensors</td></tr>
    <tr><td>Time</td><td>hours, minutes, seconds</td><td>Runtimes, delays, timers</td></tr>
  </table>

  <div class="callout">
  <p><strong>No units is normal for some points.</strong> Counters, ratios, mode indexes and
  some setpoint AVs carry <code>no-units</code>. The app shows those with a blank unit. It
  doesn't mean anything is broken.</p>
  </div>

  <h2>When the units look wrong</h2>
  <ul>
    <li><strong>A zone temp around 22 where you expected 72.</strong> The controller is
    working in &deg;C. Check the Units label; the value is probably fine.</li>
    <li><strong>The head-end shows &deg;F but the controller says &deg;C.</strong> Many
    front ends convert units on display, so the graphic and the raw BACnet value can differ.
    The app shows what the controller actually holds.</li>
    <li><strong>The label doesn't match the point.</strong> AVs created during programming
    are sometimes left at a default unit, so a static pressure setpoint might say
    <code>no-units</code> or even &deg;F. Go by the point name and the value, and tell
    whoever <a href="who-to-call-it-hvac-or-controls.html">programmed the system</a>.</li>
  </ul>

  <h2>Units in an export</h2>
  <p>When you <a href="export-bacnet-points-to-csv.html">export a points list</a>, the
  spreadsheet has a Units column next to Present Value, so whoever receives it can read
  &ldquo;55.0&nbsp;&deg;F&rdquo; instead of guessing what 55 means.</p>
""",
    related=[
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet IP points list?"),
        ("guides/export-bacnet-points-to-csv", "Export BACnet points to Excel"),
    ],
))

GUIDES.append(dict(
    slug="guides/duplicate-bacnet-device-id",
    title="Duplicate BACnet Device ID: how to fix it | Easy BACnet",
    question="Two devices have the same BACnet Device ID &mdash; what do I do?",
    description="A BACnet Device ID must be unique network-wide. When two devices share one, the head-end loses track of them. How to spot a duplicate and get it fixed.",
    answer_html="""<p><strong>A Device ID has to be unique across the whole BACnet network,
    including every routed MS/TP trunk.</strong> When two controllers share one, the head-end
    binds that ID to whichever device answered last, so points drop offline, flip between two
    units, or read values from the wrong equipment. Easy BACnet flags it after a scan
    (&ldquo;device ID(s) are duplicated on the network&rdquo;) and marks both devices
    <em>duplicate ID</em>. The fix is to renumber one of them, which is a job for
    <a href="who-to-call-it-hvac-or-controls.html">the controls contractor</a>.</p>""",
    body_html="""
  <h2>Why duplicates cause trouble</h2>
  <p>BACnet clients find a device by its <a href="bacnet-device-id-explained.html">Device
  ID</a> and then remember its address. A head-end looking for device 20114 asks the network
  &ldquo;who is 20114?&rdquo;, takes whichever answer comes back, and uses that address from
  then on. With two controllers on 20114:</p>
  <ul>
    <li>Both answer, and the head-end's binding can <strong>flip between them</strong> after
    a restart or rediscovery.</li>
    <li>Points can <strong>go offline and come back</strong>, or show values that clearly
    belong to a different unit.</li>
    <li><strong>Commands can land on the wrong controller</strong>, because the head-end is
    sending to whatever address it last bound.</li>
  </ul>

  <h2>How Easy BACnet shows it</h2>
  <p>The app keeps every reply it gets, keyed by Device ID <em>and</em> address, so two
  controllers on one ID both appear in the list. After the scan you'll see a warning such as
  <em>&#9888; 1 device ID(s) are duplicated on the network</em>, and in the Easy BACnet Mode
  results each affected device is marked <em>&#9888; duplicate ID</em> next to its own IP.
  Browser Mode lists both too, with network number and MAC for routed devices. Because the app reads each device at the address it answered from,
  you can open both and compare names and points to see which is which.</p>
  <p>The scan also warns separately when two MS/TP controllers share one MAC address behind
  a router. That's a different fault on the trunk, but it causes similar
  flaky comms.</p>

  <div class="callout">
  <p><strong>Hold off on writes until it's sorted.</strong> Even if the app reaches the right
  box, the head-end may not, and changes you make can get confused with the other unit.</p>
  </div>

  <h2>Where duplicates come from</h2>
  <ul>
    <li><strong>A replacement controller</strong> loaded from another unit's backup, or a
    panel copied from a template, without renumbering.</li>
    <li><strong>MS/TP controllers whose Device ID is derived from their MAC</strong> (some
    vendors default to a base number plus the MAC). Two trunks each with a MAC 5 controller
    end up with the same ID unless each trunk gets its own base.</li>
    <li><strong>Two buildings or two contractors' networks joined</strong> later, each with
    its own numbering scheme.</li>
    <li><strong>New controllers left at the vendor default ID</strong> and installed side by
    side.</li>
  </ul>

  <h2>How it gets fixed</h2>
  <p>One of the two controllers gets a new, unused Device ID in its own configuration tool,
  then the head-end rediscovers it and remaps its points. That's controls contractor work,
  not something to do from a browsing tool. Most sites have a numbering scheme (for example
  building + floor + trunk + MAC, giving IDs like 20114) and the new number should follow it.</p>

  <h2>What to send them</h2>
  <p>The shared Device ID, both IP addresses (or network numbers and MACs), and both device
  names. An <a href="export-bacnet-points-to-csv.html">export of the scan</a> covers all of
  that. See <a href="vendor-asking-for-bacnet-information.html">what to send when a vendor
  asks for your BACnet information</a>.</p>
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
    description="Reading BACnet doesn't change anything. Writing commands live equipment: fine when you understand priority and release, risky if you command blindly.",
    answer_html="""<p><strong>Reading doesn't change anything. Writing commands live
    equipment.</strong> A write to a commandable point sits in its
    <a href="bacnet-priority-and-stuck-overrides.html">priority array</a> and holds until
    someone <a href="bacnet-priority-and-stuck-overrides.html">releases</a> it. If you know the
    point, write at a sensible priority (normally 8) and release when you're done, it's routine
    work. Commanding points you don't understand on an occupied building can upset comfort,
    waste energy or trip equipment. Easy BACnet keeps write mode off until you turn it on, and
    turns it off again every time the app starts.</p>""",
    body_html="""
  <h2>Reading</h2>
  <p>Scanning, browsing points, reading values and
  <a href="export-bacnet-points-to-csv.html">exporting</a> only request information; nothing
  in the controllers changes. Two cautions still apply. Reading every point on a big site adds
  traffic, and an MS/TP trunk behind a router is slow, so don't keep re-reading thousands of
  points through a busy router. And on someone else's network, get permission before you plug
  in and scan.</p>

  <h2>What a write does</h2>
  <p>If you command <code>AHU-1 SF-C</code> On, the fan starts. If you command an OA damper
  to 100%, it opens. On a commandable point the value stays in its priority slot until
  someone clears it, through schedule changes, power cycles of the head-end, and you leaving
  site. That's how BACnet commanding is meant to work, and it's also why forgotten overrides
  are the most common mess techs leave behind.</p>
  <p>Not every point is commandable. Many AVs used as setpoints have no priority array: a
  write just replaces the value, the priority is ignored, and there's nothing to release. The
  only way back is to write the old value again, so note it before you change it.</p>
{{fig:writeflow}}

  <h2>How to write responsibly</h2>
  <ul>
    <li><strong>Read and note first.</strong> Confirm the device, the point name and the
    current value, and whether it's commandable (the point screen shows <em>Commanded At</em>
    for commandable points).</li>
    <li><strong>Use priority 8 unless you have a reason not to.</strong> It's the
    conventional manual operator level: above the program, which usually writes at 10&ndash;16,
    and below life safety (1&ndash;2), critical equipment (5) and minimum on/off (6). Don't
    use 1 or 2.</li>
    <li><strong>Change one thing at a time</strong> and watch the equipment respond.</li>
    <li><strong>Release when finished</strong> and check Commanded At shows the program back
    in control. The <strong>Session write log</strong> in the main menu lists everything you
    wrote.</li>
    <li><strong>Clear it with whoever runs the building.</strong> On an occupied or critical
    site, commanding a point is an operational change. Check with the
    <a href="who-to-call-it-hvac-or-controls.html">controls contractor or facility staff</a>
    first.</li>
  </ul>

  <h2>Where it goes wrong</h2>
  <ul>
    <li><strong>Occupants and process.</strong> Overriding a setpoint or fan in an occupied
    space, a lab, a grow room or a data hall has immediate effects.</li>
    <li><strong>Equipment.</strong> Forcing a valve or damper against the sequence can waste
    energy, freeze a coil on a cold day, or short-cycle a compressor.</li>
    <li><strong>Inputs.</strong> A write to an AI or BI is ignored unless Out_Of_Service is
    true. Putting an input out of service to force it means the sequence runs on your fake
    value until someone sets it back.</li>
    <li><strong>The forgotten override.</strong> The command was fine; leaving it in place is
    what caused weeks of a unit &ldquo;not working right.&rdquo;</li>
  </ul>

  <h2>What Easy BACnet does to help</h2>
  <p>Write mode is <strong>off by default and turns off every time the app starts</strong>.
  On the point screen every write shows a confirmation with the old value, the new value and
  the priority before anything is sent (on a custom remote, minus/plus, a toggle and a
  multi-state pick act at once; a button and a release ask first), and the app re-reads the point afterwards so you see what actually
  happened. On an input it warns you that the write will be ignored unless the point is out of
  service. <a href="bacnet-priority-and-stuck-overrides.html">Release to Auto</a> is on the same
  screen. The judgement is still yours.</p>
""",
    related=[
        ("guides/how-to-write-to-a-bacnet-point", "How to write to a BACnet point"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
        ("guides/who-to-call-it-hvac-or-controls", "Who do I call &mdash; IT, HVAC, or controls/BMS?"),
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
        "bacnet-vs-modbus",
    ]),
    ("Reading and exporting", [
        "how-to-use-easy-bacnet",
        "export-bacnet-points-to-csv",
        "read-bacnet-values-from-phone",
        "how-to-find-your-bacnet-points-list",
        "vendor-asking-for-bacnet-information",
        "test-bacnet-device-without-bms",
    ]),
    ("When a scan finds nothing", [
        "cant-find-what-im-looking-for",
        "why-cant-i-find-my-bacnet-devices",
        "subnets",
        "is-my-bacnet-device-online-ping-test",
        "bacnet-device-shows-offline",
        "duplicate-bacnet-device-id",
        "does-easy-bacnet-support-mstp-rs485",
        "who-to-call-it-hvac-or-controls",
    ]),
    ("Writing and overrides", [
        "is-it-safe-to-write-to-bacnet",
        "how-to-write-to-a-bacnet-point",
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
            .replace("{{PLAY_NAV}}", play_url("nav", slug))
            .replace("{{PLAY_FOOTER}}", play_url("footer", slug))
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
  <a class="getapp" href="{{PLAY_NAV}}" rel="noopener">Get the app</a>
</header>

<article>
  <h1>{{H1}}</h1>
  <p class="updated">Free browser tool &middot; nothing is uploaded &middot; updated {{UPDATED}}</p>
  {{INTRO}}
  {{TOOL}}
</article>{{REL}}

<footer>
  <p>Published alongside <a href="index.html">Easy BACnet</a>, a
  <a href="{{PLAY_FOOTER}}" rel="noopener">free Android app</a> that
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
.top .getapp{margin-left:.9rem; padding:.35rem .75rem; border-radius:8px; background:var(--accent); color:#0d0f11; font-weight:700; font-family:"IBM Plex Mono",monospace; font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; text-decoration:none; white-space:nowrap}
.hero .cta{display:flex; align-items:center; gap:1rem; flex-wrap:wrap; margin-top:1.5rem}
.hero .cta .btn{background:var(--accent); color:#0d0f11; font-weight:800; padding:.8rem 1.3rem; border-radius:12px; text-decoration:none; font-size:1.05rem}
.hero .cta span{color:var(--mut); font-family:"IBM Plex Mono",monospace; font-size:.75rem; letter-spacing:.12em; text-transform:uppercase}

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
  .phone{max-width:230px}
  .grid{grid-template-columns:1fr}
  .shotrow{grid-template-columns:1fr}
  .top .tag{display:none}
}
@media (max-width:520px){
  .top .navl{display:none}
  .top .getapp{margin-left:auto}
}
.brand b{white-space:nowrap}
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
      "description": "Scans a local network for BACnet IP devices, reads their points, commands and releases them by priority, builds custom remotes for its devices, and exports the results as an Excel (.xlsx) spreadsheet."
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
    <a class="navl" href="bacnet-points-lists/index.html" style="margin-left:1.2rem;font-family:'IBM Plex Mono',monospace;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase">Points lists</a>
    <a class="getapp" href="{{PLAY_NAV}}" rel="noopener">Get the app</a>
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
      <p class="cta"><a class="btn" href="{{PLAY_HERO}}" rel="noopener">Get it on Google Play</a>
      <span>Free &middot; Android</span></p>
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
      <figure><img src="img/remote-use.png" alt="A custom remote for one unit" width="480" height="1068" loading="lazy"><figcaption>Build your own custom remote</figcaption></figure>
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
      <li><a href="guides/cant-find-what-im-looking-for.html">The app can&rsquo;t find what I&rsquo;m looking for &mdash; what do I do?</a></li>
    </ul>
  </div>
</section>

<section class="band">
  <div class="wrap">
    <h2>BACnet points lists by manufacturer</h2>
    <p>A free library of manufacturer BACnet points lists &mdash; object types, instance numbers, names, units and
    read/write access for chillers, rooftops, VRF gateways, drives, valves and more, with CSV and EDE downloads.</p>
    <ul class="linklist">
      <li><a href="bacnet-points-lists/index.html">Browse BACnet points lists by manufacturer</a><span class="muted">Pick a manufacturer, then a model, and get its full BACnet object table.</span></li>
    </ul>
    <h3 class="grp">Popular lists</h3>
    <ul class="linklist">
      <li><a href="bacnet-points-lists/trane/symbio-700-precedent-axiom.html">Trane Symbio 700 (Precedent / Axiom) BACnet points list</a></li>
      <li><a href="bacnet-points-lists/daikin-applied/microtech-iii-rooftop-self-contained.html">Daikin Applied MicroTech III rooftop BACnet points list</a></li>
      <li><a href="bacnet-points-lists/carrier/rtu-open-v5.html">Carrier RTU Open v5 BACnet points list</a></li>
      <li><a href="bacnet-points-lists/belimo/energy-valve-v4.html">Belimo Energy Valve V4 BACnet points list</a></li>
      <li><a href="bacnet-points-lists/danfoss/vlt-hvac-drive-fc-102-mca-125.html">Danfoss VLT HVAC Drive FC 102 BACnet points list</a></li>
      <li><a href="bacnet-points-lists/abb/ach580.html">ABB ACH580 BACnet points list</a></li>
      <li><a href="bacnet-points-lists/mitsubishi-electric/bac-hd150.html">Mitsubishi Electric BAC-HD150 BACnet points list</a></li>
      <li><a href="bacnet-points-lists/lochinvar/crest.html">Lochinvar Crest boiler BACnet points list</a></li>
    </ul>
    <h3 class="grp">By equipment type</h3>
    <p><a href="bacnet-points-lists/equipment/chillers/index.html">Chillers</a> &middot;
    <a href="bacnet-points-lists/equipment/rooftop-ahu-doas/index.html">Rooftop units, AHUs &amp; DOAS</a> &middot;
    <a href="bacnet-points-lists/equipment/vrf-split-ac/index.html">VRF &amp; split AC</a> &middot;
    <a href="bacnet-points-lists/equipment/heat-pumps/index.html">Heat pumps</a> &middot;
    <a href="bacnet-points-lists/equipment/boilers/index.html">Boilers</a> &middot;
    <a href="bacnet-points-lists/equipment/humidifiers/index.html">Humidifiers</a> &middot;
    <a href="bacnet-points-lists/equipment/dehumidifiers/index.html">Dehumidifiers</a> &middot;
    <a href="bacnet-points-lists/equipment/cooling-towers/index.html">Cooling towers</a> &middot;
    <a href="bacnet-points-lists/equipment/drives-pumps/index.html">VFDs &amp; pumps</a> &middot;
    <a href="bacnet-points-lists/equipment/valves-actuators/index.html">Valves &amp; actuators</a> &middot;
    <a href="bacnet-points-lists/equipment/terminal-units/index.html">VAV &amp; fan coils</a></p>
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

<footer>
  <div class="wrap">
    <p><a href="{{PLAY_FOOTER}}" rel="noopener">Easy BACnet on Google Play</a> &middot;
    <a href="terms.html">Terms of use</a> &middot; <a href="privacy.html">Privacy policy</a> &middot;
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

    # BACnet points-list library (points_library.py, data in points_data/).
    lib_paths, lib_llms = points_library.build(write)

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
          .replace("{{TOOLS}}", tool_links).replace("{{GUIDES}}", links)
          .replace("{{PLAY_NAV}}", play_url("nav", "home"))
          .replace("{{PLAY_HERO}}", play_url("hero", "home"))
          .replace("{{PLAY_FOOTER}}", play_url("footer", "home")))

    # sitemap + robots so crawlers and agents can enumerate the whole set
    # <loc> values are normalised to extensionless clean URLs in write().
    # privacy-desktop.html is live (the PC app links to it) but kept out of the
    # sitemap and noindexed until the PC version is announced on the site.
    urls = (["index.html", "privacy.html", "terms.html"]
            + [t["slug"] + ".html" for t in TOOLS]
            + [g["slug"] + ".html" for g in GUIDES]
            + lib_paths)
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

    # AdSense ads.txt (web publisher pub-8667608030467156).
    write("ads.txt", "google.com, %s, DIRECT, f08c47fec0942fa0\n" % ADSENSE_CLIENT.replace("ca-", ""))

    # IndexNow key file (its contents ARE the ownership proof) + optional ping.
    write(INDEXNOW_KEY + ".txt", INDEXNOW_KEY + "\n")
    if ping:
        clean = [BASE_URL + "/" if _to_clean_url(u) == "/" else BASE_URL + "/" + _to_clean_url(u)
                 for u in urls]
        ping_indexnow(clean)

    # Custom domain + host hints
    write("CNAME", "easybacnet.com")
    write(".nojekyll", "")

    # Guides removed 2026-10-12: send their old URLs to the closest live guide.
    write("_redirects", "/guides /#guides 301\n/guides/ /#guides 301\n/guides/best-free-bacnet-explorer /guides/bacnet-scanner-app-android 301\n/guides/bacnet-add-object-by-number /guides/read-bacnet-values-from-phone 301\n/guides/bacnet-add-device-by-ip /guides/why-cant-i-find-my-bacnet-devices 301\n/guides/what-is-a-bbmd /guides/subnets 301\n/guides/how-to-release-a-bacnet-override /guides/bacnet-priority-and-stuck-overrides 301\n/guides/bacnet-status-flags-explained /guides/bacnet-glossary 301\n/guides/bacnet-multistate-values-explained /guides/bacnet-object-types-explained 301\n/guides/best-free-bacnet-explorer.html /guides/bacnet-scanner-app-android 301\n/guides/bacnet-add-object-by-number.html /guides/read-bacnet-values-from-phone 301\n/guides/bacnet-add-device-by-ip.html /guides/why-cant-i-find-my-bacnet-devices 301\n/guides/what-is-a-bbmd.html /guides/subnets 301\n/guides/how-to-release-a-bacnet-override.html /guides/bacnet-priority-and-stuck-overrides 301\n/guides/bacnet-status-flags-explained.html /guides/bacnet-glossary 301\n/guides/bacnet-multistate-values-explained.html /guides/bacnet-object-types-explained 301\n")

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
    llms.extend(lib_llms)
    llms.append("")
    llms.append("- Easy BACnet home: %s/" % BASE_URL)
    llms.append("- Privacy policy: %s/privacy" % BASE_URL)
    write("llms.txt", "\n".join(llms) + "\n")


if __name__ == "__main__":
    main(ping="--ping" in sys.argv)
