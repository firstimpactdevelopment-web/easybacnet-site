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
import os
import html as html_module

BASE_URL = "https://easybacnet.com"

# Freshness signal. Bump when guide content is meaningfully revised.
UPDATED = "2026-09-18"            # ISO, for JSON-LD and sitemap <lastmod>
UPDATED_HUMAN = "18 September 2026"  # for the visible "Updated" line

HERE = os.path.dirname(os.path.abspath(__file__))

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
"""


SCREENSHOTS = {
    "guides/how-to-use-easy-bacnet": [("picker.png","Choose a mode on the home screen"),
        ("scan.png","A finished scan"),
        ("devices.png","Every device found"),("points.png","One device\u2019s points")],
    "guides/how-to-write-to-a-bacnet-point": [("point.png","Point detail, showing who is commanding it"),
        ("write.png","Choosing a value and priority"),("release.png","Releasing back to auto")],
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
}


def screenshot_block(slug, prefix):
    imgs = SCREENSHOTS.get(slug)
    if not imgs:
        return ""
    figs = "".join(
        '<figure><img src="%simg/%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>'
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
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "%(base)s/index.html" },
        { "@type": "ListItem", "position": 2, "name": %(q)s, "item": "%(base)s/%(slug)s.html" }
      ]
    }
  ]
}""" % {
        "q": jstr(question),
        "a": jstr(strip_tags(answer_html)),
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
  Android app that scans a building network for BACnet/IP devices, reads their
  points, and exports the results as a CSV.</p>
  <p><a href="%(prefix)sprivacy.html">Privacy policy</a></p>
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
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write(relpath, content):
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
    title="What is a BACnet points list? | Easy BACnet",
    question="What is a BACnet points list?",
    description="A BACnet points list inventories every object a device exposes: type, instance, name, present value and units. What it contains and why.",
    answer_html="""<p>A BACnet points list is an inventory of every data object a BACnet
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
  <a href="how-to-find-your-bacnet-points-list.html">how to find your BACnet points list</a>.</p>
""",
    related=[
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet points list?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-find-your-bacnet-points-list",
    title="How do I find my BACnet points list? | Easy BACnet",
    question="How do I find my BACnet points list?",
    description="Scan a building network with an Android phone, read every point on each BACnet device, and export the whole list as a CSV in minutes.",
    answer_html="""<p>There are four routes, easiest first: ask your controls contractor
    for the submittal documents, export a points list from your building management
    system's front end, scan the network with a BACnet discovery tool, or read the
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
  devices, reads every point on each one, and exports the whole thing as a CSV
  attached to an email. That is usually faster than getting a laptop onto a
  controls VLAN.</p>

  <h2>4. Read Object_List directly</h2>
  <p>If you are writing your own tooling: every BACnet device object exposes the
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
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet devices</a>.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/vendor-asking-for-bacnet-information",
    title="What BACnet info to send a vendor | Easy BACnet",
    question="A vendor asked for my BACnet information &mdash; what do I send them?",
    description="What to hand a vendor or integrator who asks for your BACnet details: device IDs, IPs, a full points list, and how to export it as a CSV.",
    answer_html="""<p>In almost every case they want four things: a
    <strong>points list</strong> (object type, instance number and name for each
    point), the <strong>device instance IDs and IP addresses</strong> of the
    controllers, the <strong>network layout</strong> (which devices sit behind a
    BACnet router or on MS/TP trunks), and a statement of whether they will need
    <strong>read-only or read-write</strong> access. A CSV export from a network scan
    covers the first two in one step.</p>""",
    body_html="""
  <h2>The checklist</h2>
  <ol>
    <li><strong>Points list.</strong> Object type, object instance, point name,
    current value, units, and the device each point belongs to. This is the bulk of
    what they need. See
    <a href="what-is-a-bacnet-points-list.html">what a points list is</a> and
    <a href="how-to-find-your-bacnet-points-list.html">how to produce one</a>.</li>

    <li><strong>Device instance IDs.</strong> Every BACnet device has a unique
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
  <a href="../index.html">Easy BACnet</a> was built for exactly this handoff: connect
  a phone to the building network, scan, and email the resulting CSV straight to the
  vendor. The export contains device ID, device name, device IP, object type, object
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
  <pre><code>Attached is a CSV points list exported from a live scan on [date].
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
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
    ],
))

GUIDES.append(dict(
    slug="guides/why-cant-i-find-my-bacnet-devices",
    title="Why can't I find my BACnet devices? | Easy BACnet",
    question="Why can't I find my BACnet devices when I scan?",
    description="The usual reasons a BACnet scan finds nothing: wrong subnet, blocked broadcasts, no BBMD, mobile data on, or the wrong UDP port. How to fix each.",
    answer_html="""<p>Almost always because the <em>Who-Is</em> broadcast is not
    reaching the devices. The usual causes, in order of how often they turn out to be
    the problem: you are on a different IP subnet and there is no BBMD forwarding
    broadcasts; the Wi-Fi access point is dropping or filtering broadcast traffic;
    client isolation is on; the devices use a non-standard UDP port; or the devices
    sit on an MS/TP trunk behind a BACnet router. Finding nothing at all points at
    the network, not at the devices.</p>""",
    body_html="""
  <h2>Work through these in order</h2>

  <h3>1. Are you on the same IP subnet?</h3>
  <p>BACnet/IP discovery is a broadcast, and broadcasts do not cross routers. If the
  controllers are on 10.20.30.0/24 and your phone got a DHCP address on the guest
  network at 192.168.1.0/24, you will find nothing and the system is working
  correctly. This is the single most common cause.</p>
  <p>The fix is either to get onto the controls subnet, or to have a
  <strong>BBMD</strong> (BACnet Broadcast Management Device) configured to forward
  broadcasts between subnets. Many sites have one; you need its address and, for a
  client on a foreign subnet, foreign device registration support in your tool.</p>

  <h3>2. Is Wi-Fi eating the broadcast?</h3>
  <p>Access points routinely rate-limit or drop broadcast frames, and a single
  Who-Is can vanish without trace. A tool that sends Who-Is once and gives up will
  intermittently find nothing on Wi-Fi even when everything is correct. Re-broadcasting
  throughout the discovery window fixes this &mdash;
  <a href="../index.html">Easy BACnet</a> re-sends every 1.3 seconds for this reason.</p>
  <p>If you can, test on a wired connection to rule this out.</p>

  <h3>3. Is client isolation enabled?</h3>
  <p>Guest and corporate wireless networks frequently enable client isolation (also
  called AP isolation), which blocks traffic between wireless clients and often
  between wireless clients and parts of the wired network. Nothing you do in a
  BACnet tool will work around it.</p>

  <h3>4. Are the devices on a non-standard port?</h3>
  <p>The standard is UDP 47808 (0xBAC0). Sites that run multiple logical BACnet
  networks over one physical wire often move some onto 47809, 47810, and upward.
  A scanner that only checks 47808 will miss them entirely.</p>

  <h3>5. Are the devices behind a BACnet router?</h3>
  <p>MS/TP devices &mdash; most VAV boxes, many unitary controllers &mdash; are not on
  the IP network at all. They sit on a twisted-pair trunk behind a router that
  forwards for them. They should still answer a Who-Is, but replies come back with a
  network number and MAC address rather than a plain IP, and token-passing on the
  trunk makes them slow: allow several seconds per request rather than one.</p>

  <h3>6. Is a firewall in the way?</h3>
  <p>Host firewalls and VLAN access lists both block UDP 47808 readily. On a phone
  this is rarely the issue; on a laptop it often is.</p>

  <h2>If you find some devices but not others</h2>
  <p>That rules out most of the above and points at either a non-standard port for
  the missing ones, an MS/TP trunk whose router is not forwarding, or devices that
  are genuinely offline. It is also worth checking for
  <a href="bacnet-device-id-explained.html">duplicate device IDs</a> &mdash; two
  controllers claiming the same instance number can make one appear to vanish.</p>

  <h2>If devices appear with no name or no points</h2>
  <p>The device answered discovery but is refusing or failing property reads. Common
  causes: the device is busy, it only supports segmented responses for its object
  list and your client does not, or it is an unconfigured unit still sitting on the
  factory-default device ID.</p>
""",
    related=[
        ("guides/subnets", "What is a subnet, and why doesn&rsquo;t the switch give me the right one?"),
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
    ],
))

GUIDES.append(dict(
    slug="guides/subnets",
    title="What is a subnet, and why doesn't the switch give me the right one? | Easy BACnet",
    question="Why am I on the wrong network even though I'm plugged into the switch?",
    description="Being plugged into a switch doesn't mean you're on the building's controls network. What a subnet is, why a switch port can hand you the wrong one (VLANs, DHCP, static IPs), and how to get on the right one to find your BACnet devices.",
    answer_html="""<p>Plugging a cable into a switch only gives you a physical
    connection. Which <strong>network</strong> you actually land on &mdash; the
    <em>subnet</em> &mdash; is decided by how that switch port is configured, by
    the address a DHCP server hands you, or by the static address set on your own
    device. A single switch commonly carries several separate networks at once, so
    it can easily place you on the office or guest network instead of the controls
    network. BACnet discovery only reaches your own subnet, so when you are on the
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
  found. This is the single most useful thing to check, and to share.</p>

  <h2>Why this stops a BACnet scan specifically</h2>
  <p>BACnet/IP discovery works by broadcasting a <em>Who-Is</em> and listening for
  replies. A broadcast stays inside your own subnet; it does not cross routers or
  VLAN boundaries. So being on the wrong subnet doesn't just make things slow
  &mdash; it makes the controllers completely invisible, and the system is behaving
  correctly when that happens. (Some sites bridge this gap with a
  <a href="what-is-a-bbmd.html">BBMD</a>, which forwards these broadcasts between
  subnets.)</p>

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
    controller's IP and it is reachable through a router, Easy BACnet's Advanced Mode
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
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
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

  <p>Only 1, 2, 5, 6 and 8 are assigned meanings by the standard. The rest are
  available, and every vendor uses them slightly differently &mdash; which is exactly
  why you should agree a priority level in writing before letting an integrator
  command anything.</p>

  <h2>Why the point is stuck</h2>
  <p>Someone wrote a value at a priority and never released it. The usual suspects:</p>
  <ul>
    <li>A technician overrode a point at priority 8 to test something and went home.</li>
    <li>An integration or analytics platform commands a point on a schedule and
    stopped running, leaving its last command in place.</li>
    <li>A graphics page has an override control that writes but has no obvious
    release button.</li>
    <li>Someone wrote at a <em>higher</em> priority than the control program, so the
    program keeps writing to slot 16 and nothing happens. The program looks broken;
    it is being outranked.</li>
  </ul>

  <p>Reading the priority array tells you immediately which slot is occupied, and
  therefore who to blame. A point being held at priority 8 is a person; at 16, it is
  probably the control program doing its job.</p>

  <h2>How to release it</h2>
  <p>Write <code>NULL</code> to <code>Present_Value</code> at the priority that is
  holding the point. Writing a normal value at a lower priority will not help &mdash;
  the higher slot still wins. Writing NULL at the wrong priority clears an empty slot
  and changes nothing.</p>

  <p>After releasing, re-read the point. Control should drop to the next occupied
  slot or to <code>Relinquish_Default</code>.</p>

  <h2>The rule that keeps you out of trouble</h2>
  <p>Release every point you take command of before you leave site. A commanded
  point does not expire. A damper you drove to 100% to prove an actuator works will
  still be at 100% next February unless somebody clears it, and the control program
  will have no way to tell you it is being overruled.</p>

  <p>If you are writing from <a href="../index.html">Easy BACnet</a>: the point detail
  screen shows which priority currently commands the point and what it falls back to,
  and the <em>Release to Auto</em> button writes NULL at the priority you select.
  Every write and release in a session is recorded in the session write log so you
  can check nothing was left behind.</p>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information &mdash; what do I send?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-object-types-explained",
    title="BACnet object types explained | Easy BACnet",
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
    <tr><td>13</td><td>Multi-State Input</td><td>A physical input with a small set of named states.</td></tr>
    <tr><td>14</td><td>Multi-State Output</td><td>A physical output with named states: Off / Low / High.</td></tr>
    <tr><td>19</td><td>Multi-State Value</td><td>A software point with named states: Occupied / Unoccupied / Standby.</td></tr>
    <tr><td>17</td><td>Schedule</td><td>A time-of-day schedule object that writes to other points.</td></tr>
    <tr><td>20</td><td>Trend Log</td><td>Historical samples of another point, logged inside the controller.</td></tr>
    <tr><td>15</td><td>Notification Class</td><td>Where alarms get routed and who gets told.</td></tr>
    <tr><td>10</td><td>File</td><td>A file on the device, used for firmware and configuration transfer.</td></tr>
    <tr><td>16</td><td>Program</td><td>A control program running on the device.</td></tr>
    <tr><td>23</td><td>Accumulator</td><td>A running total, typically a utility meter.</td></tr>
  </table>

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
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
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
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
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
    title="How to use Easy BACnet to get a points list | Easy BACnet",
    question="How do I use Easy BACnet to get a points list off a building?",
    description="Step by step: connect to the building network, scan for BACnet devices, look at their points, and email the whole lot as a CSV. Five minutes, no laptop.",
    answer_html="""<p>Connect your phone to the same network as the building
    controls, open the app and tap the <strong>Easy BACnet</strong> card, tap
    <strong>Scan for Devices</strong>, wait for the scan to finish, then tap
    <strong>Export Results</strong>. The app reads
    every point on every device it found and hands you an email with a CSV
    attached. Tap <strong>View Results</strong> instead if you want to look at
    the devices and points on the phone first.</p>""",
    body_html="""
  <h2>Before you start</h2>
  <ul>
    <li><strong>Be on the same network as the controls.</strong> Join the
    building's Wi-Fi, or plug the phone into the controls network with a
    USB-Ethernet adapter. A phone on guest Wi-Fi or on mobile data will find
    nothing, and that is the network's doing, not the app's. See
    <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet
    devices?</a> if the scan comes back empty.</li>
    <li><strong>You do not need anyone's password.</strong> BACnet has no login.
    If you are on the network, the devices will answer.</li>
  </ul>

  <h2>Step 1 &mdash; Open Easy BACnet</h2>
  <p>The app opens on a choice of three cards: <strong>Easy BACnet</strong> (the
  simple flow this guide covers), <strong>Advanced Mode</strong> (a diagnostic
  console), and <strong>Custom Remotes</strong>. Tap <strong>Easy BACnet</strong>.</p>

  <h2>Step 2 &mdash; Scan</h2>
  <p>Tap <strong>Scan for Devices</strong>. The app broadcasts a BACnet
  <em>Who-Is</em> and listens for replies. It keeps re-broadcasting for up to
  about forty-five seconds, because Wi-Fi access points drop broadcast packets
  routinely and one shot is not reliable. A counter shows how many devices have
  answered so far; let it run to the end.</p>
  <p>When it finishes you get a green banner &mdash; <em>Success! Found 6
  device(s)</em> &mdash; or a red one, <em>No devices found</em>. On success two
  buttons appear: <strong>View Results</strong> and <strong>Export Results</strong>.
  If it comes back red, see
  <a href="cant-find-what-im-looking-for.html">the app can't find what I'm
  looking for</a>.</p>
  <div class="callout">
  <p>If the summary warns about <strong>unconfigured devices</strong> or
  <strong>duplicate Device IDs</strong>, that is worth telling whoever looks
  after the system. Both are commissioning mistakes that will cause trouble for
  any integrator later. See
  <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a>.</p>
  </div>

  <h2>Step 3 &mdash; Look at what it found (optional)</h2>
  <p>Tap <strong>View Results</strong>. Each device shows its name, Device ID
  and IP address. Tap a device and the app reads its full object list &mdash; on
  a big controller this can take a minute, because it asks for the points one at
  a time on purpose, which is the only way that works with every controller ever
  made.</p>
  <p>Tap a point to see its <strong>Present Value</strong>, <strong>Units</strong>,
  <strong>Status</strong> and <strong>Description</strong>, with a
  <strong>Refresh</strong> button for a fresh read. On points that can be
  commanded you also see <strong>Commanded At</strong> and <strong>Falls Back
  To</strong> &mdash; whether something is currently overriding the point, and
  at what priority. That one screen answers "why is this damper stuck open"
  more often than anything else in the app.</p>

  <h2>Step 4 &mdash; Export</h2>
  <p>Tap <strong>Export Results</strong> (from the home screen after a scan).
  On the free version this plays one short video ad first &mdash; and if no ad
  can load, the export just goes ahead anyway, so you are never stuck. (The
  one-time unlock removes the ad.) The app then reads every point on every
  device: names, present values, units and status. A progress box shows which
  device it is on. Do not walk out of Wi-Fi range while it runs.</p>
  <p>When it finishes, your email app opens with a message and a
  <strong>CSV attached</strong>. You choose who it goes to. The app never sends
  anything itself and has no idea who your integrator is.</p>
  <p>The CSV columns are: Device ID, Device Name, Device IP, Object Type, Object
  Number, Point Name, Present Value, Units, Status. That is exactly what someone
  asking for a points list needs &mdash; see
  <a href="vendor-asking-for-bacnet-information.html">a vendor asked for my
  BACnet information</a>.</p>

  <h2>Things worth knowing</h2>
  <ul>
    <li><strong>Nothing is uploaded anywhere.</strong> The app has no account and
    no server. The CSV exists on your phone and in the email you send.</li>
    <li><strong>Scanning and reading cannot change anything</strong> on the
    equipment. Writing is a separate, deliberately awkward mode &mdash; see
    <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet
    point</a>.</li>
    <li><strong>Dark screen by default.</strong> The app opens dark whatever your
    phone is set to, because plant rooms are dark. Change it under
    <em>Appearance</em> in the menu if you are working in sunlight.</li>
    <li><strong>Devices on another subnet</strong> will not appear unless there is
    a BACnet router or BBMD forwarding to your segment. That is how BACnet works
    everywhere, not a limitation of this app in particular.</li>
  </ul>
""",
    related=[
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/how-to-build-a-custom-remote", "How do I build a custom remote in Easy BACnet?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-write-to-a-bacnet-point",
    title="How to write to a BACnet point | Easy BACnet",
    question="How do I write to a BACnet point with Easy BACnet, and release it afterwards?",
    description="Turning on write mode, choosing a priority, confirming the write, and - the part people forget - releasing the point back to automatic control before you leave.",
    answer_html="""<p>Turn on <strong>Write mode</strong> from the menu on the home
    screen and accept the warning. Open the point, tap <strong>Write Value</strong>,
    enter the new value, leave the priority at <strong>8</strong>
    unless you know better, tap <strong>Review</strong>, check the summary, then
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
  <p>Tap <strong>Review</strong>. You get a summary: the point, the device, the
  old value, the new value and the priority, and a reminder that this takes
  command of the point until you release it. Tap <strong>Write it</strong>.</p>
  <p>The app sends the write, waits for the controller to acknowledge, then
  re-reads the point so what you see is what the device actually did, not what
  you asked for. If the controller refused, you get its reason in plain words.</p>

  <h2>Step 4 &mdash; Release it before you leave</h2>
  <p>This is the step that matters. Tap <strong>Release to Auto</strong> on the
  point, confirm, and the app writes a release at the priority you used. The
  point drops back to the next override, or to its <em>Falls Back To</em>
  value if there is none. <strong>Commanded At</strong> should now read
  <em>Not commanded</em>.</p>
  <div class="callout">
  <p>A fan commanded on at priority 8 and never released will run until someone
  notices the energy bill. Releasing is not optional; it is the second half of
  writing.</p>
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
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to get a points list?"),
        ("guides/how-to-build-a-custom-remote", "How do I build a custom remote in Easy BACnet?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/how-to-build-a-custom-remote",
    title="How to build a custom remote in Easy BACnet | Easy BACnet",
    question="How do I build a custom remote for a BACnet device in Easy BACnet?",
    description="Build a drag-and-drop control screen for one device: setpoints, toggles, readouts and a release button. The free one-remote limit explained.",
    answer_html="""<p>Open a device from your scan results, tap the menu and choose
    <strong>Custom Remote</strong>, then tap <strong>Edit</strong> and
    <strong>Add Control</strong>. Pick a point from the device's list (or type
    one in by hand), choose what kind of control it should be &mdash; a readout,
    a setpoint with minus and plus, an on/off toggle, a button, a multi-state
    picker, or a release button &mdash; and it appears on a grid. Drag controls
    to arrange them, tap one to rename or recolour it, then tap
    <strong>Done</strong>. Saved remotes live under <strong>My Remotes</strong>
    on the home screen. On the free version you can keep one remote, and
    opening it plays one short video ad; the one-time unlock removes the ad and
    lets you build as many as you like.</p>""",
    body_html="""
  <h2>What a custom remote is for</h2>
  <p>The point list shows everything a controller has &mdash; eighty rows on a
  typical rooftop unit. A custom remote is the six of those you actually touch,
  laid out as big buttons on one screen: the zone setpoint, the fan, the mode,
  the supply temperature. You build it once per device and it is there every
  visit.</p>

  <h2>Step 1 &mdash; Open the device's remote</h2>
  <p>Scan, tap <strong>View Results</strong>, tap the device. In the menu (three
  dots) tap <strong>Custom Remote</strong>. You can also reach your saved
  remotes from the <strong>Custom Remotes</strong> card on the opening screen,
  or the <strong>My Remotes</strong> button once you have built one.</p>

  <h2>Step 2 &mdash; Add controls</h2>
  <p>Tap <strong>Edit</strong> in the top bar, then <strong>Add Control</strong>.
  You get two ways to choose the point:</p>
  <ul>
    <li><strong>Pick from this device's points</strong> &mdash; the list the app
    already read. Easiest.</li>
    <li><strong>Enter a point by hand</strong> &mdash; type an object type and
    instance number. For a point you know exists but that did not show up, or
    for a device with a huge object list you did not wait for.</li>
  </ul>
  <p>Then choose what kind of control it should be:</p>
  <table>
    <tr><th>Control</th><th>What it does</th><th>Use it for</th></tr>
    <tr><td>Readout</td><td>Shows the live value. Never writes.</td><td>Supply temperature, status, anything you just want to see.</td></tr>
    <tr><td>Setpoint</td><td>Minus, value, plus. Tap the value to type one.</td><td>Zone setpoint, damper minimum, anything analog you adjust.</td></tr>
    <tr><td>Toggle</td><td>Tap to flip on/off.</td><td>Fan enable, occupancy override.</td></tr>
    <tr><td>Button</td><td>Sends one fixed value when tapped.</td><td>A reset, a "go to 100%".</td></tr>
    <tr><td>Multi-state</td><td>Tap to pick from named states.</td><td>Fan speed Off/Low/High, operating mode.</td></tr>
    <tr><td>Release</td><td>Hands the point back to automatic.</td><td>Put one next to every control that writes.</td></tr>
  </table>

  <h2>Step 3 &mdash; Arrange it</h2>
  <p>Controls sit on a four-column grid. In Edit mode, <strong>drag</strong> a
  control to move it; it snaps to the grid and refuses to land on top of
  another. <strong>Tap</strong> a control to change it: rename it, make it
  wider, set the <strong>write priority</strong> it uses, change the step size
  on a setpoint, name the states on a multi-state, pick a <strong>colour</strong>
  and <strong>card style</strong>, or delete it.</p>
  <div class="callout">
  <p>Colour is a safety feature, not decoration. Make the control that stops a
  fan <strong>red</strong> and the ones that only display temperatures plain.
  On a ladder, with gloves on, that is the difference you will actually see.</p>
  </div>
  <p>Tap <strong>Done</strong> when it looks right. Nothing talks to the device
  while you are in Edit mode; arranging a layout cannot command anything.</p>

  <h2>Using it</h2>
  <p>Out of Edit mode the remote is live. The line at the top tells you the
  truth about the connection: a green <strong>Online</strong> with the time of
  the last reply, or a red <strong>No response from device</strong> &mdash; and
  when the device stops answering, the numbers on the controls grey out rather
  than sitting there looking current. Tap <strong>Refresh</strong> for a fresh
  read of everything.</p>
  <p>Controls that write need <strong>Write mode</strong> on, exactly as the
  point screen does &mdash; see
  <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet
  point</a>. Until it is on, the remote is read-only and says so.</p>

  <h2>Coming back to it</h2>
  <p>Saved remotes appear under <strong>My Remotes</strong> on the home screen,
  one per device, with the device name, how many controls it has, and how long
  it has left. Open one and it talks to the controller directly at its last
  known address &mdash; no scan needed. If the controller has moved to a new IP,
  the remote says it is unreachable and a scan puts it right.</p>

  <h2>Free vs unlocked</h2>
  <p>Everything else in Easy BACnet is free with nothing held back. Custom
  remotes are the one paid feature, handled gently: on the free version you can
  keep <strong>one</strong> saved remote, and <strong>opening it plays one short
  video ad</strong>. If no ad can load &mdash; common in a plant room with no
  signal &mdash; the remote just opens anyway, so you are never locked out of
  your own controls.</p>
  <p>A single <strong>one-time purchase</strong> removes the ads and lifts the
  limit: build as many remotes as you like, on as many devices as you look
  after, and open them with no ad. Remotes never expire either way. There is no
  subscription.</p>
""",
    related=[
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to get a points list?"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
    ],
))

GUIDES.append(dict(
    slug="guides/cant-find-what-im-looking-for",
    title="The app can't find what I'm looking for | Easy BACnet",
    question="The app can't find what I'm looking for \u2014 what do I do?",
    description="A plain-English checklist for when a scan finds nothing, finds the wrong things, shows a device with no points, or a point with no value.",
    answer_html="""<p>Nine times out of ten it is one thing: your phone is not on
    the same network as the equipment. Turn off mobile data, join the building's
    Wi-Fi (or plug the phone into the controls network with a USB-to-Ethernet
    adapter), and scan again. If that is not it, work down the checklist below for
    whichever problem you have.</p>""",
    body_html="""
  <p>Pick the line that matches what you are seeing.</p>

  <h2>The scan finds nothing at all</h2>
  <p>You tapped <strong>Scan for Devices</strong> and got the red
  <em>No devices found</em> banner. In order, easiest first:</p>
  <ul>
    <li><strong>Turn off mobile data.</strong> If the phone can reach the
    internet over cellular, it may not bother using the Wi-Fi you need. Swipe
    down and switch mobile data off, leave Wi-Fi on, scan again.</li>
    <li><strong>Check which Wi-Fi you are on.</strong> It has to be the same
    network as the equipment. A "guest" Wi-Fi almost never is &mdash; guest
    networks deliberately hide everything else on them. Ask whoever runs the
    site which network the controls are on.</li>
    <li><strong>If there is no Wi-Fi near the equipment</strong>, that is normal
    in a plant room. You need a USB-to-Ethernet adapter: plug it into the phone,
    run a network cable from the adapter to the same switch the controllers are
    on, and scan again.</li>
    <li><strong>Try again a couple of times.</strong> Wi-Fi quietly drops the
    kind of "shout to everyone" message a scan uses. The app already repeats it
    for about 45 seconds, but a second scan sometimes catches what the first
    missed.</li>
    <li><strong>Move closer / onto the wired side.</strong> A weak Wi-Fi signal
    loses these messages first.</li>
  </ul>
  <div class="callout">
  <p>If none of that works, the devices are very likely on a <em>different</em>
  part of the network that does not forward these messages to where you are
  plugged in. That is a real thing in bigger buildings and it is not a fault in
  the app &mdash; whoever manages the network can tell you which segment the
  controls live on, or point you at the right switch. See
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet
  devices</a> for the technical version.</p>
  </div>

  <h2>It finds some devices, but not the one I want</h2>
  <ul>
    <li><strong>Look by number, not just name.</strong> Every device shows a
    <strong>Device ID</strong> and an IP address under its name. The unit you
    want might have a blank or unhelpful name but the right ID. See
    <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a>.</li>
    <li><strong>The one you want may be on another segment.</strong> Same cause
    as finding nothing &mdash; some devices answer because they are near you,
    while the missing one sits behind a router that is not forwarding to your
    spot. Being plugged into the same switch as that specific unit fixes it.</li>
    <li><strong>It may simply be powered down</strong> or unplugged from the
    network. Worth checking before assuming it is the app.</li>
  </ul>

  <h2>I opened a device but it shows no points</h2>
  <ul>
    <li><strong>Give it a moment.</strong> The app reads points one at a time so
    it works with every controller, so a big unit can take up to a minute. Watch
    for the "Loading points" progress.</li>
    <li><strong>Back out and open it again.</strong> A single dropped reply can
    stall the list; reopening starts it fresh.</li>
    <li><strong>Some small devices genuinely expose very little</strong> &mdash;
    a sensor might have only one or two points. That is the device, not a
    failure.</li>
  </ul>

  <h2>I see a point but no value (it shows a dash, or "none")</h2>
  <ul>
    <li><strong>Tap Refresh.</strong> The value is read live; one miss shows a
    dash until the next read.</li>
    <li><strong>Not every point has a live value.</strong> Some are settings or
    status the device does not report as a number, and a dash is the honest
    answer.</li>
    <li><strong>If a whole device suddenly shows dashes</strong>, it has stopped
    answering &mdash; it may have lost power or dropped off the network. Scan
    again to confirm it is still there.</li>
  </ul>

  <h2>Still stuck?</h2>
  <p>Note the Device ID or point you were after and tell whoever looks after the
  building system. Almost every "can't find it" comes down to which network the
  phone is on, and they will know the answer for their site in seconds.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to get a points list?"),
        ("guides/bacnet-device-id-explained", "BACnet Device IDs explained"),
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
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
    ],
))

GUIDES.append(dict(
    slug="guides/who-is-i-am-explained",
    title="BACnet Who-Is and I-Am explained | Easy BACnet",
    question="What are BACnet Who-Is and I-Am?",
    description="Who-Is is a broadcast asking which devices exist; each replies I-Am with its instance, vendor and capabilities. How BACnet discovery works.",
    answer_html="""<p><strong>Who-Is</strong> and <strong>I-Am</strong> are the two
    messages behind BACnet discovery. A tool broadcasts a <em>Who-Is</em> meaning
    &ldquo;who is out there?&rdquo;, and every device that hears it answers with an
    <em>I-Am</em> carrying its Device Instance number, the vendor, and what it can do.
    Collect the replies and you have a device list &mdash; which is exactly what Easy
    BACnet does when you tap Scan.</p>""",
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
  <a href="what-is-a-bbmd.html">BBMD</a> bridges the two. That is the single most common
  reason a scan comes back empty: see
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet devices?</a>.
  Devices on a serial <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> trunk answer too,
  as long as a router carries the traffic onto IP.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
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
    &mdash; forwards BACnet/IP broadcasts from one IP subnet to another. BACnet discovery
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
  <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find my BACnet devices?</a>.</p>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/what-port-does-bacnet-use", "What port does BACnet use?"),
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
  device appears as a normal BACnet device with its Device Instance. That routing is why
  Easy BACnet, which speaks BACnet/IP over Wi-Fi, can still list and read MS/TP
  controllers &mdash; provided a router is carrying them onto the subnet your phone is on.</p>

  <h2>Which am I looking at?</h2>
  <p>If a device shows a network number greater than the local one and a low MAC address,
  it is almost certainly an MS/TP device reached through a router. Pure BACnet/IP devices
  sit on the IP network directly with their own IP address.</p>
""",
    related=[
        ("guides/who-is-i-am-explained", "BACnet Who-Is and I-Am explained"),
        ("guides/what-port-does-bacnet-use", "What port does BACnet use?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/what-port-does-bacnet-use",
    title="What port does BACnet use? | Easy BACnet",
    question="What port does BACnet use?",
    description="BACnet/IP uses UDP port 47808 (0xBAC0) by default; extra networks use 47809 and up. Easy BACnet checks the common range automatically.",
    answer_html="""<p>BACnet/IP uses <strong>UDP port 47808</strong> by default &mdash; that
    is <code>0xBAC0</code> in hex, which is where the number comes from. It is UDP, not TCP,
    and discovery relies on broadcasts to that port. Where a single IP subnet carries more
    than one BACnet network, the extra networks use <strong>47809</strong> and up.</p>""",
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
  even on the right subnet &mdash; worth ruling out with whoever runs the network. Note
  that <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP</a> devices have no IP port at all;
  they live on a serial trunk and reach IP only through a BACnet router. And because the
  port carries broadcasts, it will not cross a router to another subnet without a
  <a href="what-is-a-bbmd.html">BBMD</a>.</p>
""",
    related=[
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
        ("guides/bacnet-mstp-vs-bacnet-ip", "BACnet MS/TP vs BACnet/IP"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-scanner-app-android",
    title="BACnet scanner app for Android | Easy BACnet",
    question="Is there a BACnet scanner app for Android?",
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
  a scan comes back empty is not the app &mdash; it is that the phone landed on the
  wrong network. Guest Wi-Fi, a separate controls VLAN, or a switch handing out an
  address in the wrong range will all leave you shouting into a room the controllers
  cannot hear. See <a href="why-cant-i-find-my-bacnet-devices.html">why can't I find
  my BACnet devices?</a> and <a href="subnets.html">what is a subnet, and why doesn't
  the switch give me the right one?</a></p>

  <h2>What a phone can and cannot reach</h2>
  <table>
    <tr><th>Situation</th><th>Works from the phone?</th></tr>
    <tr><td>BACnet/IP devices on the same subnet as the phone</td><td>Yes &mdash; the normal case, found by <em>Who-Is</em></td></tr>
    <tr><td>A specific device you can reach by IP but not by broadcast</td><td>Yes &mdash; add it directly by IP address</td></tr>
    <tr><td>MS/TP devices on a serial trunk behind a BACnet router</td><td>Yes, if the router advertises them onto IP &mdash; you reach them through it, not directly. See <a href="bacnet-mstp-vs-bacnet-ip.html">MS/TP vs BACnet/IP</a></td></tr>
    <tr><td>Devices on another subnet, with no BBMD</td><td>No &mdash; broadcasts don't cross a router without a <a href="what-is-a-bbmd.html">BBMD</a></td></tr>
  </table>
  <p>The honest limits worth knowing up front: Easy BACnet speaks <strong>BACnet/IP</strong>.
  It reaches MS/TP devices through a router that publishes them, not by plugging into
  a serial trunk directly, and it does not register as a foreign device with a BBMD,
  so a device on a different subnet needs either a BBMD or a direct add-by-IP.</p>

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
  exported as a CSV &mdash; so a phone standing in a plant room turns a system nobody
  had documented into a list somebody can use. Walk through a full scan in
  <a href="how-to-use-easy-bacnet.html">how to use Easy BACnet</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/subnets", "What is a subnet, and why doesn't the switch give me the right one?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
    ],
))

GUIDES.append(dict(
    slug="guides/read-bacnet-values-from-phone",
    title="How to read BACnet values from a phone | Easy BACnet",
    question="How do I read BACnet values from a phone?",
    description="Step by step: join the controls network, discover BACnet devices, open a point and read its live present value, units and status — from an Android phone, no laptop.",
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
    BACnet devices?</a> and <a href="subnets.html">the subnet guide</a> if the scan
    is empty.</li>
    <li><strong>No password.</strong> BACnet has no login. If you are on the network,
    the devices answer.</li>
  </ul>

  <h2>Step 1 &mdash; Scan for devices</h2>
  <p>Open the app, tap the <strong>Easy BACnet</strong> card, then <strong>Scan for
  Devices</strong>. The app broadcasts a BACnet <em>Who-Is</em> and collects the
  replies for up to about forty-five seconds &mdash; access points drop broadcasts,
  so it keeps asking rather than trusting one shot. A counter shows devices as they
  answer.</p>
  <figure class="shot">
    <img src="../img/scan.png" alt="Easy BACnet scanning a network and listing the BACnet devices that answered" loading="lazy">
    <figcaption>A scan in progress &mdash; devices appear as they answer the Who-Is.</figcaption>
  </figure>

  <h2>Step 2 &mdash; Open the device</h2>
  <p>Tap <strong>View Results</strong>. Each device shows its name, Device ID and IP
  address. Tap the one you want and the app reads its object list &mdash; on a large
  controller this takes a moment, because it reads the points one at a time on
  purpose, which is the only approach that works with every controller ever made.</p>
  <figure class="shot">
    <img src="../img/devices.png" alt="A list of discovered BACnet devices with names, Device IDs and IP addresses" loading="lazy">
    <figcaption>Discovered devices, each with its name, Device ID and IP.</figcaption>
  </figure>

  <h2>Step 3 &mdash; Find the point</h2>
  <p>The device opens to its list of points &mdash; analog inputs, binary values,
  setpoints and the rest. Names come from the controller's own
  <em>Object_Name</em>, so a well-commissioned device reads like plain English and a
  poorly-commissioned one reads like <code>AI-3</code>. If a big controller has
  hundreds of points, use the search box. Not sure what the object types mean? See
  <a href="bacnet-object-types-explained.html">BACnet object types explained</a>.</p>
  <figure class="shot">
    <img src="../img/points.png" alt="The point list for a BACnet device showing analog and binary objects with live values" loading="lazy">
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
  <strong>Falls Back To</strong> &mdash; whether something is currently overriding
  the point and at what priority. That single screen answers &ldquo;why is this
  damper stuck open?&rdquo; more often than anything else in the app. See
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
  <strong>Export Results</strong> reads every point on every device and hands you a
  CSV by email &mdash; names, present values, units and status. A five-minute scan in
  a plant room turns an undocumented building into a points list somebody can use.
  The full walkthrough is in <a href="how-to-use-easy-bacnet.html">how to use Easy
  BACnet</a>.</p>
""",
    related=[
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/bacnet-scanner-app-android", "Is there a BACnet scanner app for Android?"),
        ("guides/bacnet-object-types-explained", "BACnet object types explained"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-device-shows-offline",
    title="BACnet device shows offline? Causes & fixes | Easy BACnet",
    question="Why does my BACnet device show offline?",
    description="A BACnet device that shows offline is usually a network or discovery problem, not dead hardware — wrong subnet, dropped broadcasts, a firewall on UDP 47808, or a duplicate ID.",
    answer_html="""<p>&ldquo;Offline&rdquo; in BACnet almost always means <em>I stopped
    hearing from it</em>, not <em>it is broken</em>. The usual causes, most common
    first: your phone or client is on the wrong subnet so the broadcast never reaches
    it, a Wi-Fi access point is dropping the broadcast packets, a firewall is blocking
    UDP 47808, the device shares a Device ID or network number with another device, or
    it genuinely lost power or its network link. A device showing a <em>fault</em> flag
    is a different thing from one showing offline &mdash; worth separating first.</p>""",
    body_html="""
  <h2>Offline versus fault &mdash; not the same</h2>
  <p>First separate two things people both call &ldquo;offline&rdquo;. A device that
  does not answer discovery or reads at all is a <strong>communication</strong>
  problem &mdash; the causes below. A device that answers fine but whose
  <em>points</em> show a fault or unreliable flag is a <strong>health</strong> problem
  on the equipment &mdash; a failed sensor, not a network fault. If you can read the
  device but a point looks wrong, that is fault, not offline.</p>

  <h2>The causes of a truly unreachable device</h2>

  <h3>1. Wrong subnet (by far the most common)</h3>
  <p>Controls equipment usually sits on its own subnet or VLAN. If your phone is on
  guest Wi-Fi, the office network, or a different scope, the broadcast that finds
  BACnet devices never reaches them and everything looks offline. See
  <a href="subnets.html">what is a subnet, and why doesn't the switch give me the right
  one?</a></p>

  <h3>2. Dropped broadcast packets</h3>
  <p>BACnet discovery is a broadcast, and Wi-Fi access points drop broadcast packets
  freely under load. A device that appears one scan and vanishes the next, or shows
  offline intermittently, is often this. Scanning repeatedly &mdash; which a good tool
  does automatically &mdash; works around it.</p>

  <h3>3. A firewall on UDP 47808</h3>
  <p>BACnet/IP lives on UDP <strong>47808</strong> (0xBAC0). A software firewall,
  antivirus, or a locked-down switch dropping that port makes devices unreachable even
  on the right subnet. See <a href="what-port-does-bacnet-use.html">what port does
  BACnet use?</a></p>

  <h3>4. A duplicate Device ID or network number</h3>
  <p>Two devices sharing a Device ID, or a duplicated network number, makes devices
  appear and disappear or answer for each other &mdash; a classic &ldquo;it is online,
  no it is not&rdquo; symptom. If it started when equipment was added, suspect this.
  See <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a>.</p>

  <h3>5. It is on another subnet with no BBMD</h3>
  <p>Broadcasts do not cross a router by themselves. A device on a different segment
  needs a <a href="what-is-a-bbmd.html">BBMD</a> or a directed add-by-IP, or it will
  always look absent from your side.</p>

  <h3>6. It really is down</h3>
  <p>Lost power, a pulled network cable, a dead MS/TP trunk behind its router. Once the
  five above are ruled out, this is what is left &mdash; and now you know to look at the
  equipment, not the network.</p>

  <h2>A quick order to check in</h2>
  <ol>
    <li>Confirm your phone's IP is on the <strong>same subnet</strong> as the controls.</li>
    <li><strong>Scan again</strong> a couple of times &mdash; dropped broadcasts hide
    devices.</li>
    <li>Try adding the device <strong>directly by IP</strong>; if that works, it is a
    broadcast/subnet problem, not a dead device.</li>
    <li>Check for <strong>duplicate IDs</strong> in what you did find.</li>
    <li>Ask whoever runs the network about <strong>UDP 47808</strong> and VLANs.</li>
  </ol>
  <div class="callout">
  <p><a href="../index.html">Easy BACnet</a> re-broadcasts discovery for up to about
  forty-five seconds to beat dropped packets, shows your phone's own subnet when a scan
  is empty, and flags duplicate Device IDs when it sees them &mdash; the three things
  behind most &ldquo;offline&rdquo; reports.</p>
  </div>
""",
    related=[
        ("guides/why-cant-i-find-my-bacnet-devices", "Why can't I find my BACnet devices?"),
        ("guides/subnets", "What is a subnet, and why doesn't the switch give me the right one?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
        ("guides/what-is-a-bbmd", "What is a BBMD?"),
    ],
))

GUIDES.append(dict(
    slug="guides/bacnet-write-access-denied",
    title="BACnet Write Access Denied — what it means | Easy BACnet",
    question="What does BACnet 'Write Access Denied' mean, and how do I fix it?",
    description="Write Access Denied means the BACnet property you tried to write cannot be written that way — usually a read-only property, a non-commandable point, or the wrong priority.",
    answer_html="""<p>&ldquo;Write Access Denied&rdquo; is BACnet telling you the
    property you aimed at cannot be written the way you tried &mdash; it is a
    permission answer from the device, not a network error. The usual reasons: the
    property is read-only (you cannot write an input's Present_Value directly), the
    object is not commandable so it has no priority array to write into, the point is
    locked by <em>Out_Of_Service</em> or the controller's own program, or you wrote
    the right thing to the wrong property. The device is healthy; it is declining this
    particular write.</p>""",
    body_html="""
  <h2>What the error actually is</h2>
  <p>It is a BACnet error class <em>property</em>, error code <em>write-access-denied</em>,
  returned by the device in response to your WriteProperty. That means communication
  worked end to end &mdash; the device received the request, understood it, and refused
  it on rules. So this is never a wiring or subnet problem; it is about <em>what</em>
  you tried to write.</p>

  <h2>The common reasons, and the fix</h2>

  <h3>1. The property is read-only</h3>
  <p>You cannot write the Present_Value of an Analog Input or Binary Input &mdash; those
  reflect a physical sensor and are read-only by definition. If you need to force a
  value for testing, that is what <em>Out_Of_Service</em> plus the manual override is
  for, not a direct write. Writing to an <em>output</em> or <em>value</em> object is
  the writable case.</p>

  <h3>2. The object is not commandable</h3>
  <p>Only commandable objects (typically outputs, and value objects the vendor made
  commandable) have the 16-slot priority array you write into. Write to a
  non-commandable object and you get access denied. Check the object type &mdash; see
  <a href="bacnet-object-types-explained.html">BACnet object types explained</a>.</p>

  <h3>3. You wrote the value instead of a priority</h3>
  <p>On a commandable point you write Present_Value <em>at a priority</em> (1&ndash;16).
  Some controllers reject a write that does not specify a priority, or reject writes at
  priorities they reserve. Choose a priority &mdash; 8 is the usual manual-operator
  slot &mdash; and write there. See
  <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority and stuck
  overrides</a>.</p>

  <h3>4. The controller's program owns it</h3>
  <p>Some devices lock points that their internal logic controls, or require the point
  to be out of service before an external write is allowed. This is a device policy;
  the vendor's manual will say so, and forcing past it is not something to do on live
  equipment without understanding what the program expects.</p>

  <h3>5. Genuinely protected</h3>
  <p>Configuration properties, and some vendors' whole objects, are simply not
  writable over BACnet by design. If the manual says read-only, it is read-only.</p>

  <h2>How to work out which</h2>
  <ol>
    <li><strong>Look at the object type.</strong> Input? It is read-only &mdash; you want
    an output or value object.</li>
    <li><strong>Check whether it is commandable</strong> (does it have a priority
    array?). If not, there is nothing to write.</li>
    <li><strong>Write Present_Value at priority 8</strong> rather than as a plain
    value.</li>
    <li><strong>Read the vendor manual</strong> for points the program locks or that
    need Out_Of_Service first.</li>
  </ol>
  <div class="callout">
  <p><a href="../index.html">Easy BACnet</a> only offers a write where the object is
  commandable, defaults to a sensible priority, and reads the priority array back so
  you can see whether the write took &mdash; which turns &ldquo;access denied&rdquo;
  from a mystery into an obvious &ldquo;that point is not writable.&rdquo; See
  <a href="how-to-write-to-a-bacnet-point.html">how to write to a BACnet point</a>.</p>
  </div>
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
    description="You wrote a BACnet point and nothing changed. Usually a higher priority is already commanding it, you wrote a value instead of at a priority, or the point is read-only.",
    answer_html="""<p>You wrote the point, got no error, and nothing moved. In BACnet
    that almost always means <strong>something at a higher priority is already in
    command</strong>. A commandable point obeys the highest active slot in its 16-level
    priority array, so a write at priority 8 does nothing while priority 5 is held. The
    other possibilities: you wrote at a priority the equipment's logic immediately
    overrides on its next cycle, you wrote a read-only property, or the write went to
    the wrong object. Reading the priority array tells you which in one look.</p>""",
    body_html="""
  <h2>The priority array is the whole story</h2>
  <p>A commandable BACnet point does not simply hold the last value written. It has
  sixteen priority slots, and its Present_Value follows the <em>highest-priority slot
  that currently has a value</em>. If slot 5 holds 72 and you write 68 at slot 8, the
  point stays at 72 &mdash; your write landed, it is just being outranked. This is
  working exactly as designed, and it is the number-one reason a write &ldquo;does
  nothing.&rdquo; See <a href="bacnet-priority-and-stuck-overrides.html">BACnet priority
  and stuck overrides</a>.</p>

  <h2>Work through it in order</h2>

  <h3>1. Read the priority array</h3>
  <p>Look at all sixteen slots. If any slot <em>above</em> the one you wrote holds a
  value, that is what is winning. Common culprits: a manual override left in slot 8 by
  a previous technician, or the building program holding a low-numbered slot.</p>

  <h3>2. Decide the right way to win</h3>
  <p>You can write at a higher priority than the one holding it &mdash; but understand
  what you are overriding before you do, because you may be fighting the safety logic.
  Often the correct fix is not to write higher but to <strong>release</strong> the slot
  that should not be held (write NULL to relinquish it), letting the point fall back to
  the program.</p>

  <h3>3. Check you wrote at a priority at all</h3>
  <p>Writing Present_Value as a bare value, with no priority, behaves inconsistently
  across controllers &mdash; some take it, some ignore it. Write explicitly at a
  priority (8 is the usual manual slot).</p>

  <h3>4. Rule out read-only and wrong-object</h3>
  <p>If the point is an input or a non-commandable object, a &ldquo;successful&rdquo;
  write may have gone nowhere useful &mdash; or returned
  <a href="bacnet-write-access-denied.html">Write Access Denied</a>. Confirm you are on
  a commandable output or value object.</p>

  <h3>5. The program rewrites it every cycle</h3>
  <p>If the value flicks to yours for a second and then snaps back, the controller's
  own logic is writing that point on its scan at a higher priority. You cannot win that
  from outside without addressing the program &mdash; and you usually should not.</p>

  <div class="callout">
  <p><a href="../index.html">Easy BACnet</a> reads the full priority array after every
  write and shows which slot is in command, so &ldquo;nothing happened&rdquo; becomes
  &ldquo;priority 5 is holding it&rdquo; &mdash; the difference between guessing and
  knowing. It also offers a one-tap release to hand a stuck slot back to Auto.</p>
  </div>
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
    title="Export a BACnet points list to CSV (and EDE) | Easy BACnet",
    question="How do I export a BACnet points list to CSV, and what is an EDE file?",
    description="How to get a BACnet device's points out as a CSV you can open in Excel or hand to an integrator — from a phone — and how that relates to the EDE format vendors ask for.",
    answer_html="""<p>Scan the device, read its points, and export &mdash; a CSV with
    each object's name, type, instance, present value, units and status is what
    &ldquo;a points list&rdquo; usually means, and it opens straight in Excel.
    <a href="../index.html">Easy BACnet</a> does this from a phone and emails you the
    CSV. An <strong>EDE file</strong> (Engineering Data Exchange) is a more formal,
    column-standardised spreadsheet that integrators use to import points into a
    building management system &mdash; the same information, in a fixed layout. For most
    &ldquo;send me your points&rdquo; requests a clean CSV is exactly what is wanted.</p>""",
    body_html="""
  <h2>What people mean by &ldquo;a points list&rdquo;</h2>
  <p>When a vendor, integrator or analytics provider asks for your points list, they
  want a table of what exists on the equipment: for each object, its name, what kind of
  object it is, its number, and usually a live value and units. Unlike Modbus, BACnet
  devices can be <em>asked</em> what they contain &mdash; so this list can be built by
  reading the device, not by hunting for a document. See
  <a href="what-is-a-bacnet-points-list.html">what is a BACnet points list?</a></p>

  <h2>Getting it out as a CSV from a phone</h2>
  <ol>
    <li>Join the controls network and <strong>scan</strong> for devices.</li>
    <li>Choose <strong>Export</strong> &mdash; the app reads every point on every device
    it found: name, present value, units, status, object type and instance.</li>
    <li>Your email app opens with a <strong>CSV attached</strong>. You choose who it
    goes to; nothing is uploaded anywhere.</li>
  </ol>
  <p>The columns are the ones an integrator actually needs: Device ID, Device Name,
  Device IP, Object Type, Object Number, Point Name, Present Value, Units, Status. The
  full walkthrough is in <a href="how-to-use-easy-bacnet.html">how to use Easy
  BACnet</a>.</p>

  <h2>CSV versus EDE &mdash; which do they want?</h2>
  <table>
    <tr><th></th><th>CSV (from Easy BACnet)</th><th>EDE file</th></tr>
    <tr><td>What it is</td><td>A plain table of the device's objects and values</td><td>A standardised BACnet spreadsheet with fixed columns for import</td></tr>
    <tr><td>Opens in Excel</td><td>Yes</td><td>Yes (it is a spreadsheet)</td></tr>
    <tr><td>Best for</td><td>&ldquo;Show me what's on this device&rdquo;, records, a vendor request, troubleshooting</td><td>Bulk-importing points into a BMS or analytics platform to a fixed schema</td></tr>
    <tr><td>Contains</td><td>Names, values, units, status, object IDs</td><td>Object name, type, instance, and standard EDE columns (present-value fields, units, COV increment, etc.)</td></tr>
  </table>
  <p>EDE (Engineering Data Exchange) is a convention from the BACnet world for moving a
  point list between tools in a predictable column order. If someone specifically asks
  for &ldquo;an EDE&rdquo;, they mean that layout. If they just say &ldquo;send me the
  points&rdquo;, a CSV with clear names and values is what they are after &mdash; and it
  is trivial to reshape a CSV into an EDE template if they later need one.</p>

  <div class="callout">
  <p>The value of exporting from the live device is that it is <em>true</em>: it is what
  the equipment actually reports today, not what a years-old design document claims. A
  CSV built from a real scan is often the most accurate points list a building has. See
  <a href="vendor-asking-for-bacnet-information.html">a vendor asked for my BACnet
  information</a>.</p>
  </div>
""",
    related=[
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/vendor-asking-for-bacnet-information", "A vendor asked for my BACnet information"),
        ("guides/read-bacnet-values-from-phone", "How do I read BACnet values from a phone?"),
    ],
))

GUIDES.append(dict(
    slug="guides/test-bacnet-device-without-bms",
    title="Test a BACnet device without a BMS | Easy BACnet",
    question="How do I test a BACnet device without a BMS?",
    description="You don't need the building management system to prove a BACnet device works. How to discover it, read its points and check control response with just a phone on the network.",
    answer_html="""<p>You do not need the building management system, a laptop, or the
    integrator to prove a BACnet device is alive and working. Any BACnet client on the
    same network can do it &mdash; including <a href="../index.html">Easy BACnet</a> on
    a phone. Join the network, run a Who-Is, and if the device answers with its name and
    Device ID it is online and speaking BACnet. Read its points to confirm the sensors
    report sane values, and &mdash; carefully &mdash; command a commandable point to
    confirm it responds. That is a full functional check with nothing but a phone.</p>""",
    body_html="""
  <h2>Why you can do this without the BMS</h2>
  <p>BACnet has no login and no single master. Any device on the network can ask any
  other device questions, which is exactly what a BMS does &mdash; it is just a BACnet
  client with a nice front end. So a handheld client can perform the same discovery,
  reads and writes the BMS would, which makes a phone ideal for commissioning checks,
  startup verification, and &ldquo;is this new controller actually talking?&rdquo;
  before the BMS is even connected.</p>

  <h2>The test, step by step</h2>

  <h3>1. Prove it is on the network (discovery)</h3>
  <p>Run a scan. If the device answers a Who-Is with its name, Device ID and IP, it is
  powered, on the network, and speaking BACnet/IP &mdash; three things confirmed at
  once. If it does not answer, that is a network or address problem, not necessarily a
  dead device: see <a href="bacnet-device-shows-offline.html">why does my BACnet device
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
    <a href="export-bacnet-points-to-csv.html">CSV</a> for a record.</li>
    <li><strong>Cannot</strong>: reach devices on another subnet without a
    <a href="what-is-a-bbmd.html">BBMD</a>, or plug straight into an MS/TP trunk &mdash;
    those go through a router. And it does not replace the BMS's scheduling and trending;
    it proves the device works, not that the whole sequence is programmed.</li>
  </ul>
  <div class="callout">
  <p>This is the field-tech use Easy BACnet is built for: walk up to a new or suspect
  controller with a phone, prove in two minutes whether it is the device, the network or
  the program at fault, and leave a CSV behind &mdash; no BMS access required.</p>
  </div>
""",
    related=[
        ("guides/read-bacnet-values-from-phone", "How do I read BACnet values from a phone?"),
        ("guides/bacnet-device-shows-offline", "Why does my BACnet device show offline?"),
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point?"),
        ("guides/export-bacnet-points-to-csv", "How do I export a BACnet points list to CSV?"),
    ],
))

GUIDES.append(dict(
    slug="guides/best-free-bacnet-explorer",
    title="Best free BACnet explorer tools | Easy BACnet",
    question="What is the best free BACnet explorer tool?",
    description="The free BACnet explorers compared — YABE, CAS BACnet Explorer, the Contemporary Controls BDT and Wacnet — plus where a free phone-based option fits for fieldwork.",
    answer_html="""<p>For a Windows desk, the established free choices are
    <strong>YABE</strong> (Yet Another BACnet Explorer, open source), the
    <strong>Contemporary Controls BACnet Discovery Tool (BDT)</strong>, Chipkin's
    <strong>CAS BACnet Explorer</strong>, and <strong>Wacnet</strong>. They are capable
    and worth having. What none of them is, is a tool you can carry &mdash; they are all
    Windows programs. For discovering and reading BACnet from the plant room on the
    device in your pocket, <a href="../index.html">Easy BACnet</a> fills the gap the
    desktop explorers leave open, and it writes as well as reads.</p>""",
    body_html="""
  <h2>The free desktop explorers</h2>
  <table>
    <tr><th>Tool</th><th>Platform</th><th>Reads</th><th>Writes</th><th>Notes</th></tr>
    <tr><td>YABE</td><td>Windows</td><td>Yes</td><td>Yes</td><td>Open source, very capable, technical interface. The default &ldquo;free explorer&rdquo; answer.</td></tr>
    <tr><td>CAS BACnet Explorer</td><td>Windows</td><td>Yes</td><td>Yes</td><td>Polished, free tier, from Chipkin. Good for commissioning.</td></tr>
    <tr><td>Contemporary Controls BDT</td><td>Windows</td><td>Yes</td><td>No</td><td>Free discovery/read tool; read-only. Download is behind a form.</td></tr>
    <tr><td>Wacnet</td><td>Windows/Java</td><td>Yes</td><td>Yes</td><td>Open source, single-JAR, quick to stand up.</td></tr>
    <tr><td>Easy BACnet</td><td>Android (phone/tablet)</td><td>Yes</td><td>Yes</td><td>Free; discovery, read, write with priority safety, CSV export &mdash; in the field.</td></tr>
  </table>

  <h2>How to choose</h2>
  <ul>
    <li><strong>You are at a Windows desk and want the deepest free tool:</strong> YABE
    or CAS BACnet Explorer. YABE if you like open source and don't mind a dense UI; CAS
    if you want something more polished.</li>
    <li><strong>You just want to discover devices on a Windows laptop:</strong> the
    Contemporary Controls BDT is purpose-built for that &mdash; but it is read-only, so
    it will not command a point.</li>
    <li><strong>You want to check equipment where it lives, without a laptop:</strong>
    that is the phone case, and it is the one the desktop tools cannot serve. Easy BACnet
    discovers, reads live values, writes with a priority array and release, and exports a
    <a href="export-bacnet-points-to-csv.html">CSV</a> &mdash; from the network you are
    already standing on.</li>
  </ul>

  <div class="callout">
  <p>These are not either/or. Many people keep YABE or CAS on the laptop for deep desk
  work and use a phone tool for the walk-around &mdash; discovery, a quick read, a
  careful override and release, a CSV for the file. The desktop explorers are strong;
  the open niche is <em>portable</em>, and that is where a phone wins. See
  <a href="bacnet-scanner-app-android.html">is there a BACnet scanner app for
  Android?</a></p>
  </div>

  <h2>A note on &ldquo;free&rdquo;</h2>
  <p>Watch what &ldquo;free&rdquo; includes. Some free tools read but do not write; some
  gate the download behind a lead form; some are free for personal use only. Easy BACnet
  is free to scan, read, write and export; a one-time purchase only lifts the limit on
  saved custom control panels. Reading and commissioning a device costs nothing.</p>
""",
    related=[
        ("guides/bacnet-scanner-app-android", "Is there a BACnet scanner app for Android?"),
        ("guides/read-bacnet-values-from-phone", "How do I read BACnet values from a phone?"),
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to scan and read?"),
        ("guides/test-bacnet-device-without-bms", "How do I test a BACnet device without a BMS?"),
    ],
))

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
  scans a building network for BACnet/IP devices, reads and commands their points, and
  exports a CSV. This tool runs entirely in your browser.</p>
  <p><a href="terms.html">Terms of use</a> &middot; <a href="privacy.html">Privacy policy</a></p>
</footer>

</body>
</html>
"""

TOOLS.append(dict(
    slug="bacnet-object-id-decoder",
    title="BACnet Object Identifier decoder | Easy BACnet",
    question="BACnet Object Identifier decoder",
    description="Encode or decode a BACnet Object Identifier: turn an object type and instance into the 32-bit number, or decode a raw number back into its type and instance. Free browser tool.",
    intro_html="""<p>A BACnet Object Identifier packs an <strong>object type</strong> and
    an <strong>instance number</strong> into a single 32-bit value &mdash; the top 10
    bits are the type, the bottom 22 bits are the instance. This tool goes both ways:
    pick a type and instance to get the encoded number, or paste a raw Object Identifier
    to see what it means. Background: <a href="guides/what-is-a-bacnet-points-list.html">what
    is a BACnet points list?</a> and <a href="guides/bacnet-object-types-explained.html">BACnet
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
        ("guides/what-is-a-bacnet-points-list", "What is a BACnet points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
        ("guides/bacnet-scanner-app-android", "Is there a BACnet scanner app for Android?"),
    ],
))

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<title>Easy BACnet &mdash; scan, read &amp; control BACnet/IP devices</title>
<meta name="description" content="Free Android app to scan a network for BACnet/IP devices, read and command their points by priority, build control panels, and export a CSV.">
<link rel="canonical" href="{{BASE}}/index.html">
<meta name="robots" content="index, follow">
<meta name="google-site-verification" content="5mp_Qm6jQXeHC7IbyiRUwPt3te2kFjKv67pCaqqLAhQ">
<meta name="theme-color" content="#14171a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Easy BACnet">
<meta property="og:title" content="Easy BACnet &mdash; scan, read &amp; control BACnet/IP devices">
<meta property="og:description" content="Free Android app to scan a network for BACnet/IP devices, read and command their points by priority, build control panels, and export a CSV.">
<meta property="og:url" content="{{BASE}}/index.html">
<meta property="og:image" content="{{BASE}}/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Easy BACnet &mdash; scan, read &amp; control BACnet/IP devices">
<meta name="twitter:description" content="Free Android app to scan a network for BACnet/IP devices, read and command their points by priority, build control panels, and export a CSV.">
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
      "logo": "{{BASE}}/icon.svg"
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
      "description": "Scans a local network for BACnet/IP devices, reads their points, commands and releases them by priority, builds custom control panels, and exports the results as a CSV."
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
      <p class="sub">No account, no analytics, no server. <b>Easy.</b> Everything happens on
      your phone and your local network.</p>
    </div>
    <div class="art">
      <div class="phone"><img src="img/scan.png" alt="A finished scan in Easy BACnet"></div>
    </div>
  </div>
</section>

<section class="features">
  <div class="wrap">
    <h2>What it does</h2>
    <div class="grid">
      <div class="cell"><div class="n">01 / DISCOVER</div>
        <h3>Discover the network</h3>
        <p>Finds every BACnet/IP device on the subnet, including devices reached through a
        BACnet router on an MS/TP trunk.</p></div>
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
        <p>Scan and export the whole network as a CSV &mdash; ready to hand to an
        integrator, keep on file, or feed an AI.</p></div>
    </div>
  </div>
</section>

<section class="shots">
  <div class="wrap">
    <div class="shotrow">
      <figure><img src="img/points.png" alt="A device's points" loading="lazy"><figcaption>Browse each device and its points</figcaption></figure>
      <figure><img src="img/write.png" alt="Writing a value at a chosen priority" loading="lazy"><figcaption>Command a point at the priority you choose</figcaption></figure>
      <figure><img src="img/remote-use.png" alt="A custom control panel" loading="lazy"><figcaption>Build your own control panel</figcaption></figure>
    </div>
  </div>
</section>

<section class="band">
  <div class="wrap">
    <h2>Using the app</h2>
    <ul class="linklist">
      <li><a href="guides/how-to-use-easy-bacnet.html">How do I use Easy BACnet to get a points list off a building?</a></li>
      <li><a href="guides/how-to-write-to-a-bacnet-point.html">How do I write to a BACnet point, and release it afterwards?</a></li>
      <li><a href="guides/how-to-build-a-custom-remote.html">How do I build a custom remote for a device?</a></li>
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

<section class="band">
  <div class="wrap">
    <h2>Guides</h2>
    <ul class="linklist">
{{GUIDES}}
    </ul>
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
    <p><a href="privacy.html">Privacy policy</a></p>
  </div>
</footer>

</body>
</html>
"""


def main():
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

    links = "\n".join(
        '  <li><a href="%s.html">%s</a><br><span class="muted">%s</span></li>'
        % (g["slug"], g["question"], g["description"].split(".")[0] + ".")
        for g in GUIDES
    )
    tool_links = "\n".join(
        '  <li><a href="%s.html">%s</a><br><span class="muted">%s</span></li>'
        % (t["slug"], t["question"], t["description"].split(".")[0] + ".")
        for t in TOOLS
    )
    write("index.html", INDEX.replace("{{BASE}}", BASE_URL)
          .replace("{{TOOLS}}", tool_links).replace("{{GUIDES}}", links))

    # sitemap + robots so crawlers and agents can enumerate the whole set
    urls = (["index.html", "privacy.html"]
            + [t["slug"] + ".html" for t in TOOLS]
            + [g["slug"] + ".html" for g in GUIDES])
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod></url>" % (BASE_URL, u, UPDATED))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")

    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE_URL)

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
            "Free Android app to scan a network for BACnet/IP devices, read and command their points by priority, build control panels, and export a CSV. Plus plain-English BACnet guides.",
            "",
            "## Free tools"]
    for t in TOOLS:
        llms.append("- %s: %s/%s.html" % (html_module.unescape(t["question"]), BASE_URL, t["slug"]))
    llms.append("")
    llms.append("## Guides")
    for g in GUIDES:
        llms.append("- %s: %s/%s.html" % (html_module.unescape(g["question"]), BASE_URL, g["slug"]))
    llms.append("- Easy BACnet home: %s/index.html" % BASE_URL)
    llms.append("- Privacy policy: %s/privacy.html" % BASE_URL)
    write("llms.txt", "\n".join(llms) + "\n")


if __name__ == "__main__":
    main()
