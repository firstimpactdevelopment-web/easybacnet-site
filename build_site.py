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

BASE_URL = "https://easybacnet.com"

HERE = os.path.dirname(os.path.abspath(__file__))

CSS = """
  :root { color-scheme: light dark; --fg:#1a1a1a; --bg:#fff; --muted:#5a5a5a;
          --accent:#1565C0; --box:#eef4fb; --line:#cfe0f2; --code:#f0f0f0; }
  @media (prefers-color-scheme: dark) {
    :root { --fg:#e6e6e6; --bg:#121212; --muted:#a5a5a5; --accent:#7fb2f0;
            --box:#16222f; --line:#284straight; --code:#262626; }
  }
  * { box-sizing: border-box; }
  body { max-width: 48rem; margin: 0 auto; padding: 2rem 1.25rem 5rem;
         font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
         Helvetica, Arial, sans-serif; color: var(--fg); background: var(--bg); }
  header.site { display:flex; align-items:center; gap:.6rem; padding-bottom:1.5rem;
                border-bottom:1px solid var(--line); margin-bottom:2rem; }
  header.site a { color: var(--accent); text-decoration: none; font-weight: 600; }
  h1 { font-size: 1.85rem; line-height: 1.25; margin: 0 0 .75rem; }
  h2 { font-size: 1.25rem; margin-top: 2.4rem; }
  h3 { font-size: 1.05rem; margin-top: 1.8rem; }
  a { color: var(--accent); }
  .answer { background: var(--box); border: 1px solid var(--line);
            border-radius: 10px; padding: 1rem 1.15rem; margin: 1.25rem 0 2rem; }
  .answer strong { display:block; margin-bottom:.35rem; text-transform:uppercase;
                   font-size:.75rem; letter-spacing:.08em; color: var(--muted); }
  code { background: var(--code); padding: .1rem .35rem; border-radius: 4px; font-size: .9em; }
  pre { background: var(--code); padding: 1rem; border-radius: 8px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  table { border-collapse: collapse; width: 100%; margin: 1.25rem 0; display:block; overflow-x:auto; }
  th, td { text-align: left; padding: .5rem .7rem; border-bottom: 1px solid var(--line); }
  th { font-size: .85rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  ul, ol { padding-left: 1.3rem; }
  li { margin: .4rem 0; }
  .muted { color: var(--muted); font-size: .92rem; }
  nav.more { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--line); }
  nav.more ul { list-style: none; padding: 0; }
  nav.more li { margin: .5rem 0; }
  footer { margin-top: 3.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line);
           color: var(--muted); font-size: .9rem; }
""".replace("#284straight", "#2c4a6b")


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
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": %s,
    "acceptedAnswer": { "@type": "Answer", "text": %s }
  }]
}""" % (
        jstr(question),
        jstr(strip_tags(answer_html)),
    )

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(description)s">
<link rel="canonical" href="%(base)s/%(slug)s.html">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#1565C0">
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
  <a href="%(prefix)sindex.html">Easy BACnet</a>
  <span class="muted">&middot; BACnet field reference</span>
</header>

<article>
  <h1>%(question)s</h1>

  <div class="answer">
    <strong>Short answer</strong>
    %(answer)s
  </div>

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
        "body": body_html,
        "rel": rel,
        "prefix": prefix,
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
    description="A BACnet points list is an inventory of every object a BACnet device exposes: object type, instance number, name, present value and units. Here is what one contains and what it is used for.",
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
    description="Four ways to get a BACnet points list: ask your controls contractor, export from the BMS front end, scan the network with a discovery tool, or read Object_List from the controller directly.",
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
    title="A vendor asked for my BACnet information - what do I send? | Easy BACnet",
    question="A vendor asked for my BACnet information &mdash; what do I send them?",
    description="What to send when an integrator, analytics vendor or contractor asks for your BACnet information: device IDs, IP addresses, a points list, network topology, and what to hold back.",
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
    description="A BACnet scan returning nothing is usually a network problem: wrong subnet with no BBMD, Wi-Fi blocking broadcasts, client isolation, a non-standard port, or devices behind an MS/TP router.",
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
        ("guides/how-to-find-your-bacnet-points-list", "How do I find my BACnet points list?"),
        ("guides/bacnet-device-id-explained", "What is a BACnet Device ID?"),
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
    description="A BACnet Device ID (device instance number) uniquely identifies a controller across the entire BACnet internetwork. Duplicates break integrations; 4194303 means a device was never commissioned.",
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
    controls, open Easy BACnet, tap <strong>Scan for Devices</strong>, wait for
    the scan to finish, then tap <strong>Export Results</strong>. The app reads
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

  <h2>Step 1 &mdash; Scan</h2>
  <p>Tap <strong>Scan for Devices</strong>. The app broadcasts a BACnet
  <em>Who-Is</em> and listens for replies. It keeps re-broadcasting for up to
  about forty-five seconds, because Wi-Fi access points drop broadcast packets
  routinely and one shot is not reliable. A counter shows how many devices have
  answered so far; let it run to the end.</p>
  <p>When it finishes you get a one-line summary, for example
  <em>Scan complete &mdash; found 6 device(s)</em>, and two buttons: <strong>View
  Results</strong> and <strong>Export Results</strong>.</p>
  <div class="callout">
  <p>If the summary warns about <strong>unconfigured devices</strong> or
  <strong>duplicate Device IDs</strong>, that is worth telling whoever looks
  after the system. Both are commissioning mistakes that will cause trouble for
  any integrator later. See
  <a href="bacnet-device-id-explained.html">BACnet Device IDs explained</a>.</p>
  </div>

  <h2>Step 2 &mdash; Look at what it found (optional)</h2>
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

  <h2>Step 3 &mdash; Export</h2>
  <p>Tap <strong>Export Results</strong> (from the home screen after a scan).
  The app now reads every point on every device: names, present values, units
  and status. A progress box shows which device it is on. Do not walk out of
  Wi-Fi range while it runs.</p>
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
    title="How to write to a BACnet point with Easy BACnet, and release it | Easy BACnet",
    question="How do I write to a BACnet point with Easy BACnet, and release it afterwards?",
    description="Turning on write mode, choosing a priority, confirming the write, and - the part people forget - releasing the point back to automatic control before you leave.",
    answer_html="""<p>Turn on <strong>Write mode</strong> from the menu on the home
    screen and accept the warning. Open the point, tap <strong>Write Value</strong>,
    enter the new value, leave the priority at <strong>8 &mdash; Manual Operator</strong>
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
  <strong>8 &mdash; Manual Operator</strong>, is the conventional slot for a
  person with a tool standing in front of the equipment, and it is the right
  choice unless a site standard says otherwise.</p>
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
    description="Build a drag-and-drop control screen for one air handler or controller: setpoint arrows, on/off switches, readouts and a release button. What each control does, what the 48-hour rule is, and what the one-time unlock buys.",
    answer_html="""<p>Open a device from your scan results, tap the menu and choose
    <strong>Custom Remote</strong>, then tap <strong>Edit</strong> and
    <strong>Add Control</strong>. Pick a point from the device's list (or type
    one in by hand), choose what kind of control it should be &mdash; a readout,
    a setpoint with minus and plus, an on/off toggle, a button, a multi-state
    picker, or a release button &mdash; and it appears on a grid. Drag controls
    to arrange them, tap one to rename or recolour it, then tap
    <strong>Done</strong>. Saved remotes live under <strong>My Remotes</strong>
    on the home screen. A remote built for free works fully for 48 hours and is
    then deleted; a one-time unlock keeps every remote permanently.</p>""",
    body_html="""
  <h2>What a custom remote is for</h2>
  <p>The point list shows everything a controller has &mdash; eighty rows on a
  typical rooftop unit. A custom remote is the six of those you actually touch,
  laid out as big buttons on one screen: the zone setpoint, the fan, the mode,
  the supply temperature. You build it once per device and it is there every
  visit.</p>

  <h2>Step 1 &mdash; Open the device's remote</h2>
  <p>Scan, tap <strong>View Results</strong>, tap the device. In the menu (three
  dots) tap <strong>Custom Remote</strong>. The first time you add a control the
  app tells you about the 48-hour rule, once, so there are no surprises.</p>

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

  <h2>The 48-hour rule and the unlock</h2>
  <p>Everything else in Easy BACnet is free with nothing held back. Custom
  remotes are the one paid feature, and they are offered as a working trial
  rather than a locked door: a remote you build for free is fully functional for
  <strong>48 hours</strong> from the moment it gets its first control, and is
  then deleted. You can build it again, free, as many times as you like.</p>
  <p>A single <strong>one-time purchase</strong> makes every remote permanent
  &mdash; the ones you have already built as well as the ones you build later,
  on as many devices as you look after. There is no subscription. The app tells
  you when remotes have been deleted, on the way in, rather than leaving you to
  find an empty screen.</p>
""",
    related=[
        ("guides/how-to-write-to-a-bacnet-point", "How do I write to a BACnet point with Easy BACnet, and release it?"),
        ("guides/how-to-use-easy-bacnet", "How do I use Easy BACnet to get a points list?"),
        ("guides/bacnet-priority-and-stuck-overrides", "BACnet priority and stuck overrides"),
    ],
))

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Easy BACnet &mdash; BACnet points lists, explained</title>
<meta name="description" content="Free Android app that scans a building network for BACnet/IP devices, reads their points and exports a CSV. Plus plain-English guides to BACnet points lists, device IDs, priority arrays and discovery troubleshooting.">
<link rel="canonical" href="%(base)s/index.html">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#1565C0">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Easy BACnet">
<meta property="og:title" content="Easy BACnet &mdash; BACnet points lists, explained">
<meta property="og:description" content="Free Android app that scans a building network for BACnet/IP devices, reads their points and exports a CSV. Plus plain-English guides to BACnet points lists, device IDs, priority arrays and discovery troubleshooting.">
<meta property="og:url" content="%(base)s/index.html">
<meta property="og:image" content="%(base)s/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Easy BACnet &mdash; BACnet points lists, explained">
<meta name="twitter:description" content="Free Android app that scans a building network for BACnet/IP devices, reads their points and exports a CSV. Plus plain-English guides to BACnet points lists, device IDs, priority arrays and discovery troubleshooting.">
<meta name="twitter:image" content="%(base)s/img/og-image.png">
<style>%(css)s</style>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Easy BACnet",
  "applicationCategory": "UtilitiesApplication",
  "operatingSystem": "Android 8.0 or later",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Scans a local network for BACnet/IP devices, reads their points, and exports the results as a CSV for handing to a vendor or integrator."
}
</script>
</head>
<body>

<header class="site">
  <a href="index.html">Easy BACnet</a>
  <span class="muted">&middot; BACnet field reference</span>
</header>

<h1>Get a BACnet points list off a building network, in minutes</h1>

<div class="answer">
  <strong>What this is</strong>
  <p>Easy BACnet is a free Android app for building-automation technicians. It
  broadcasts a BACnet <em>Who-Is</em>, lists every BACnet/IP device that answers,
  reads every point on each one, and exports the lot as a CSV attached to an email.
  No account, no analytics, no server &mdash; everything happens on your phone and
  your local network.</p>
</div>

<h2>What it does</h2>
<ul>
  <li><strong>Scan for devices</strong> &mdash; finds BACnet/IP devices on the local
  subnet, including devices reached through a BACnet router on an MS/TP trunk.</li>
  <li><strong>Browse points</strong> &mdash; every object on a device, with its type,
  instance number and name.</li>
  <li><strong>Read live values</strong> &mdash; present value, units, status flags and
  description, with a refresh.</li>
  <li><strong>See who is commanding a point</strong> &mdash; the priority array and
  relinquish default, so you can tell whether a point is being overridden.</li>
  <li><strong>Write and release</strong> &mdash; command a point at a chosen BACnet
  priority, or release it back to automatic. Write mode is off by default and turns
  itself off every time the app starts.</li>
  <li><strong>Export a CSV</strong> &mdash; device ID, device name, device IP, object
  type, object number, point name, present value, units and status.</li>
</ul>

<h2>Using the app</h2>
<ul>
  <li><a href="guides/how-to-use-easy-bacnet.html">How do I use Easy BACnet to get a points list off a building?</a></li>
  <li><a href="guides/how-to-write-to-a-bacnet-point.html">How do I write to a BACnet point, and release it afterwards?</a></li>
  <li><a href="guides/how-to-build-a-custom-remote.html">How do I build a custom remote for a device?</a></li>
</ul>

<h2>Guides</h2>
<nav class="more" style="margin-top:0;border-top:none;padding-top:0">
<ul>
%(guides)s
</ul>
</nav>

<h2>Notes for anyone scanning a building network</h2>
<ul>
  <li>Connect to the <strong>same subnet</strong> as the controllers. BACnet
  discovery is a broadcast and broadcasts do not cross routers without a BBMD.</li>
  <li>Discovery uses <strong>UDP port 47808</strong>. Some sites use 47809 and up.</li>
  <li>Reading is harmless. <strong>Writing is not</strong> &mdash; a commanded point
  stays commanded until it is released. Read
  <a href="guides/bacnet-priority-and-stuck-overrides.html">the priority guide</a>
  before you write to anything on a live building.</li>
</ul>

<footer>
  <p><a href="privacy.html">Privacy policy</a></p>
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

    links = "\n".join(
        '  <li><a href="%s.html">%s</a><br><span class="muted">%s</span></li>'
        % (g["slug"], g["question"], g["description"].split(".")[0] + ".")
        for g in GUIDES
    )
    write("index.html", INDEX % {"base": BASE_URL, "css": CSS, "guides": links})

    # sitemap + robots so crawlers and agents can enumerate the whole set
    urls = ["index.html", "privacy.html"] + [g["slug"] + ".html" for g in GUIDES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("  <url><loc>%s/%s</loc></url>" % (BASE_URL, u))
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
<title>Page not found &mdash; Easy BACnet</title>
<meta name="robots" content="noindex">
<style>
  :root { color-scheme: light dark; }
  body { max-width: 40rem; margin: 0 auto; padding: 6rem 1.25rem; text-align: center;
         font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
         Helvetica, Arial, sans-serif; }
  h1 { font-size: 1.85rem; margin: 0 0 .75rem; }
  a { color: #1565C0; font-weight: 600; }
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
            "A free Android app that scans a building network for BACnet/IP devices, reads their points, and exports a CSV; plus plain-English BACnet field guides.",
            "",
            "## Guides"]
    for g in GUIDES:
        llms.append("- %s: %s/%s.html" % (g["question"], BASE_URL, g["slug"]))
    llms.append("- Easy BACnet home: %s/index.html" % BASE_URL)
    llms.append("- Privacy policy: %s/privacy.html" % BASE_URL)
    write("llms.txt", "\n".join(llms) + "\n")


if __name__ == "__main__":
    main()
