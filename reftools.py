"""BACnet reference lookups (/bacnet-reference/) and the scan-vs-points-list compare tool.

Reference data: bacnet_enums.json, built from bacnet-stack 1.6.1 bacenum.h and cross-checked
value by value against bacpypes and @bacnet-js/client (x = 1 when a second stack agrees).
The compare tool runs entirely in the browser: it reads an Easy BACnet Excel export, an EDE
file or any CSV, and compares it with a points list from the library (index.json + model JSON).
Built from build_site.main(); returns (sitemap_paths, llms_lines).
"""
import json
import os
import shutil

import calculators
import points_library as PL

ROOT = "bacnet-reference"
COMPARE = "bacnet-points-list-compare.html"
PUBLISHED = "2026-11-07"
esc = PL.esc

DATA = json.load(open(os.path.join(PL.HERE, "bacnet_enums.json"), encoding="utf-8"))
T = DATA["tables"]


ACRONYMS = {"apdu", "npdu", "cov", "id", "ip", "ipv6", "udp", "bbmd", "bdt", "fdt", "mac", "utc", "vt", "uuid",
            "uri", "uris", "dhcp", "dns", "sc", "bvlc", "pdu", "mstp", "hvac", "rh"}


def title_case(i):
    return "_".join(w.upper() if w in ACRONYMS else w.capitalize() for w in i.split("-"))


# Unique anchor prefix per table (several tables share a page).
ANCHOR = {"units": "u", "property": "p", "object_type": "t", "error_class": "ec", "error_code": "e",
          "reject_reason": "rj", "abort_reason": "ab", "reliability": "r", "event_state": "es",
          "event_type": "et", "device_status": "ds", "confirmed_service": "cs", "unconfirmed_service": "us"}


def words(i):
    return i.replace("-", " ")


# Plain-English notes for the values a tech actually runs into. Each is checked
# against the table at build time (number and identifier must both match).
HINTS = {
    "property": {
        (4, "active-text"): "Text for the active (1) state of a binary object.",
        (22, "cov-increment"): "How much an analog value must change before a COV notification is sent.",
        (28, "description"): "Free-text description of the object.",
        (46, "inactive-text"): "Text for the inactive (0) state of a binary object.",
        (74, "number-of-states"): "How many states a multi-state object has (states are numbered from 1).",
        (75, "object-identifier"): "Object type plus instance number, packed into one 32-bit value.",
        (76, "object-list"): "Every object in the device. Reading it is how a scan finds the points.",
        (77, "object-name"): "The point name. Unique within a device.",
        (79, "object-type"): "Which kind of object this is (AI, BO, MV...).",
        (81, "out-of-service"): "True disconnects the object from its real input/output; Present_Value can then be written freely.",
        (85, "present-value"): "The live value. Commands are written here at a priority (1-16).",
        (87, "priority-array"): "16 command slots. The lowest-numbered slot that is not empty wins.",
        (103, "reliability"): "Why a value may be wrong (no sensor, open loop, communication failure...).",
        (104, "relinquish-default"): "The value used when all 16 priority slots are empty.",
        (110, "state-text"): "The names of a multi-state object's states, starting at state 1.",
        (111, "status-flags"): "Four bits: in-alarm, fault, overridden, out-of-service.",
        (117, "units"): "Engineering units of an analog value, as a number (see the units table).",
        (120, "vendor-identifier"): "The manufacturer's ASHRAE vendor ID.",
        (121, "vendor-name"): "The manufacturer's name as text.",
    },
    "error_code": {
        (0, "other"): "A catch-all: the device refused but gave no specific reason.",
        (3, "device-busy"): "The device is busy; try again shortly.",
        (9, "invalid-data-type"): "Wrong data type, e.g. a Real written to a binary point, or Unsigned where Enumerated is expected.",
        (26, "password-failure"): "The device wants a password for this service (often DeviceCommunicationControl or ReinitializeDevice).",
        (27, "read-access-denied"): "The device will not let you read this property.",
        (29, "service-request-denied"): "The device refused the request as a whole, often because of a lock or its current state.",
        (30, "timeout"): "The device timed out handling the request (often while talking to a sub-network).",
        (31, "unknown-object"): "That object type and instance do not exist on this device. Check the instance number and the device.",
        (32, "unknown-property"): "The object exists but does not have that property.",
        (37, "value-out-of-range"): "The value is outside the object's limits, e.g. a setpoint min/max or a state that does not exist.",
        (40, "write-access-denied"): "The property is read-only, or the device blocks writes (local mode, hand/off/auto switch, lock).",
        (42, "invalid-array-index"): "The array index does not exist, e.g. priority 17 or a state number past Number_Of_States.",
        (50, "property-is-not-an-array"): "An array index was given for a property that is not an array.",
    },
    "error_class": {(0, "device"): "", (1, "object"): "", (2, "property"): "Most failed reads and writes are in this class.",
                    (3, "resources"): "", (4, "security"): "", (5, "services"): "", (6, "vt"): "", (7, "communication"): ""},
    "reject_reason": {
        (9, "unrecognized-service"): "The device does not support that service, e.g. ReadPropertyMultiple. Read one property at a time.",
        (3, "invalid-parameter-data-type"): "A parameter in the request had the wrong data type.",
        (6, "parameter-out-of-range"): "A parameter in the request was out of range.",
    },
    "abort_reason": {
        (4, "segmentation-not-supported"): "The reply was too big for one packet and the device cannot split it. Ask for fewer properties at once.",
        (1, "buffer-overflow"): "The request or reply did not fit the device's buffer.",
    },
    "reliability": {
        (0, "no-fault-detected"): "The value can be trusted.",
        (1, "no-sensor"): "No sensor is connected.",
        (2, "over-range"): "The input reads above its range (often an open or failed sensor).",
        (3, "under-range"): "The input reads below its range (often a shorted or failed sensor).",
        (4, "open-loop"): "Open circuit on the input or output.",
        (5, "shorted-loop"): "Short circuit on the input or output.",
        (7, "unreliable-other"): "The device knows the value is wrong but gives no specific reason.",
        (12, "communication-failure"): "The device lost contact with whatever supplies the value (a sub-network, wireless sensor or gateway).",
    },
}

for tbl, hints in HINTS.items():
    by = {r["n"]: r["id"] for r in T[tbl]}
    for (n, ident) in hints:
        assert by.get(n) == ident, ("hint mismatch", tbl, n, ident, by.get(n))


def hint(tbl, r):
    return HINTS.get(tbl, {}).get((r["n"], r["id"]), "")


# Reference pages: (slug, title, h1 rest, description, lede, sections [(table key, heading, column label)])
PAGES = [
    ("engineering-units", "BACnet Engineering Units List (Number to Unit) | Easy BACnet",
     "engineering units list",
     "Every BACnet engineering units number and what it means: 62 = degrees-celsius, 64 = degrees-fahrenheit, "
     "98 = percent. Searchable, free.",
     "A BACnet analog object reports its units as a number. Scans, EDE files and some front ends show that "
     "number instead of the unit. Find any of them here.",
     [("units", "Engineering units", "Unit")]),
    ("property-identifiers", "BACnet Property Identifiers List | Easy BACnet",
     "property identifiers",
     "Every BACnet property number and name: 85 = Present_Value, 87 = Priority_Array, 111 = Status_Flags. "
     "With plain-English notes on the common ones.",
     "Every BACnet property has a number. Packet captures, error messages and tools such as Wireshark often "
     "show the number. Look any of them up here.",
     [("property", "Property identifiers", "Property")]),
    ("object-types", "BACnet Object Types List (Type Numbers 0-64) | Easy BACnet",
     "object types",
     "Every BACnet object type number: 0 = analog-input, 3 = binary-input, 8 = device, 19 = multi-state-value. "
     "Free searchable list.",
     "The object type is the top 10 bits of every BACnet Object Identifier. Here is every standard type number "
     "and its name.",
     [("object_type", "Object types", "Object type")]),
    ("error-codes", "BACnet Error, Reject and Abort Codes Explained | Easy BACnet",
     "error, reject and abort codes",
     "What BACnet error codes mean: error class 2 / code 31 = unknown-object, 40 = write-access-denied, plus "
     "every reject and abort reason.",
     "When a read or write fails, the device answers with an Error (class + code), a Reject or an Abort. Each "
     "is a number. Here is what every one means, with notes on the ones you will actually see.",
     [("error_class", "Error classes", "Error class"), ("error_code", "Error codes", "Error code"),
      ("reject_reason", "Reject reasons", "Reject reason"), ("abort_reason", "Abort reasons", "Abort reason")]),
    ("reliability-and-event-states", "BACnet Reliability, Event State and Device Status | Easy BACnet",
     "reliability, event state and device status",
     "BACnet Reliability values (1 = no-sensor, 12 = communication-failure), Event_State, Event_Type and "
     "System_Status numbers explained.",
     "Reliability says why a value may be wrong; Event_State says whether an object is in alarm; System_Status "
     "says what the device itself is doing. All are numbers on the wire.",
     [("reliability", "Reliability", "Reliability"), ("event_state", "Event state", "Event state"),
      ("event_type", "Event type", "Event type"), ("device_status", "Device status (System_Status)", "Status")]),
    ("services", "BACnet Service Choice Numbers List | Easy BACnet",
     "service choice numbers",
     "BACnet confirmed and unconfirmed service numbers: 12 = readProperty, 15 = writeProperty, 0 = i-am, "
     "8 = who-is. Useful when reading packet captures.",
     "Every BACnet request carries a service choice number. Packet captures and error logs show it; this is "
     "what each one is.",
     [("confirmed_service", "Confirmed services", "Service"), ("unconfirmed_service", "Unconfirmed services", "Service")]),
]

TABLE_LABEL = {"units": "Engineering units", "property": "Property", "object_type": "Object type",
               "error_class": "Error class", "error_code": "Error code", "reject_reason": "Reject reason",
               "abort_reason": "Abort reason", "reliability": "Reliability", "event_state": "Event state",
               "event_type": "Event type", "device_status": "Device status",
               "confirmed_service": "Confirmed service", "unconfirmed_service": "Unconfirmed service"}
PAGE_OF = {k: p[0] for p in PAGES for k, _, _ in p[5]}

CSS = calculators.CALC_CSS + """<style>
.reftab td.num{font-family:"IBM Plex Mono",monospace;white-space:nowrap;text-align:right;color:var(--accent);font-weight:600}
.reftab td.id{font-family:"IBM Plex Mono",monospace;white-space:nowrap}
.reftab td.note{color:#d6dde3;font-size:.9rem}
.reftab tr:target td{background:rgba(255,154,31,.14)}
.reftab .one{color:var(--mut);font-size:.75rem}
.qbox{display:flex;gap:.6rem;flex-wrap:wrap;margin:.6rem 0}
.qbox input{flex:1 1 260px;font:inherit;font-family:"IBM Plex Mono",monospace;color:var(--fg);background:var(--code);border:1px solid var(--line);border-radius:9px;padding:.7rem .85rem}
.hits{list-style:none;padding:0;margin:.6rem 0}
.hits li{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:.55rem .8rem;margin:.35rem 0}
.hits b.n{font-family:"IBM Plex Mono",monospace;color:var(--accent);margin-right:.4rem}
.hits .k{font-family:"IBM Plex Mono",monospace;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin-right:.5rem}
.hits .t{color:var(--mut);font-size:.88rem}
</style>"""

FILTER = r"""<script>
(function(){var q=document.getElementById('rq');if(!q)return;var rows=[].slice.call(document.querySelectorAll('.reftab tbody tr'));
rows.forEach(function(r){r._t=r.textContent.toLowerCase();});var out=document.getElementById('rq-n');
function run(){var s=q.value.trim().toLowerCase(),n=0,num=/^\d+$/.test(s);rows.forEach(function(r){
 var ok=!s||(num?r.getAttribute('data-n')===s:r._t.indexOf(s)>=0||r._t.indexOf(s.replace(/[ _]/g,'-'))>=0);r.hidden=!ok;if(ok)n++;});
 out.textContent=s?n+' match'+(n===1?'':'es'):'';}
q.addEventListener('input',run);try{var P=new URLSearchParams(location.search);if(P.get('q')){q.value=P.get('q');run();}}catch(e){}})();
</script>"""


def ref_path(slug):
    return ROOT + "/" + slug + ".html"


def hub_path():
    return ROOT + "/index.html"


def table_html(key, heading, col):
    rows = []
    for r in T[key]:
        extra = ' <span class="one" title="Only in bacnet-stack; newer than the other two stacks checked">(newer)</span>' if not r["x"] else ""
        label = esc(r["id"])
        alt = ""
        if key == "property":
            alt = '<br><span class="one">%s</span>' % esc(title_case(r["id"]))
        if key == "units" and r.get("s"):
            alt = ' <span class="one">(%s)</span>' % esc(r["s"])
        rows.append('<tr id="%s%d" data-n="%d"><td class="num">%d</td><td class="id">%s%s%s</td><td class="note">%s</td></tr>'
                    % (ANCHOR[key], r["n"], r["n"], r["n"], label, alt, extra, esc(hint(key, r))))
    return ('<h2 id="%s">%s <span class="count">(%d)</span></h2><div class="tablewrap"><table class="fx reftab">'
            '<thead><tr><th>Number</th><th>%s</th><th>Notes</th></tr></thead><tbody>%s</tbody></table></div>'
            % (key, esc(heading), len(T[key]), esc(col), "".join(rows)))


SOURCE_NOTE = ("Values come from the open-source bacnet-stack 1.6.1 (bacenum.h), which follows ANSI/ASHRAE "
               "Standard 135, and were cross-checked one by one against two other independent BACnet stacks "
               "(bacpypes and @bacnet-js/client). Entries marked <em>(newer)</em> are in bacnet-stack only, "
               "because the other two stacks predate them. Numbers 0-255 (and the higher ASHRAE ranges) are "
               "standard; vendors may use proprietary numbers above them.")


def nav_ref(html_out):
    return html_out.replace('class="on">Points lists', '>Points lists', 1)


def ref_page(p):
    slug, title, h1rest, desc, lede, sections = p
    relpath = ref_path(slug)
    url = PL.clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet reference", "/" + hub_path()), (h1rest.capitalize(), None)]
    first = T[sections[0][0]]
    ex = [r for r in first if hint(sections[0][0], r)][:3] or first[:3]
    answer = "%s Examples: %s." % (lede, ", ".join("<strong>%d</strong> = %s" % (r["n"], esc(r["id"])) for r in ex))
    others = "".join('<li><a href="/%s">BACnet %s</a></li>' % (ref_path(q[0]), esc(q[2])) for q in PAGES if q is not p)
    body = """
<div class="answer"><b>Short answer</b><p>%(answer)s</p></div>
<div class="qbox"><input id="rq" type="search" placeholder="Type a number or a name, e.g. %(ph)s" aria-label="Filter this list" autocomplete="off"><span class="count" id="rq-n" aria-live="polite"></span></div>
<p class="count">Looking for a number but not sure which list it belongs to? Use the
<a href="/%(hub)s">BACnet number lookup</a>, which searches every table at once.</p>
%(tables)s
<p class="count">%(src)s</p>
<h2>More BACnet reference</h2><ul class="notes">%(others)s
<li><a href="/bacnet-object-id-decoder.html">BACnet Object Identifier decoder</a></li>
<li><a href="/bacnet-vendor-id-lookup.html">BACnet Vendor ID lookup</a></li>
<li><a href="/%(cmp)s">Compare a scan with a points list</a></li></ul>
<div class="callout"><p><a href="/index.html">Easy BACnet</a> reads these values straight off the device from an
Android phone and shows them as words, not numbers.</p></div>
""" % {"answer": answer, "ph": esc(str(ex[0]["n"])), "hub": hub_path(), "tables": "".join(table_html(*s) for s in sections),
       "src": SOURCE_NOTE, "others": others, "cmp": COMPARE}
    h1 = ('<p class="eyebrow">BACnet reference</p><h1>BACnet <span class="mfr">%s</span></h1>'
          '<p class="updated">Updated %s</p>' % (esc(h1rest), PL.human_date(PUBLISHED)))
    page_ld = {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc,
               "isPartOf": {"@id": PL.BASE_URL + "/#site"}, "dateModified": PUBLISHED, "publisher": {"@id": PL.ORG["@id"]}}
    ds = {"@type": "Dataset", "@id": url + "#data", "name": "BACnet " + h1rest, "description": desc, "url": url,
          "isAccessibleForFree": True, "creator": {"@id": PL.ORG["@id"]},
          "isBasedOn": "ANSI/ASHRAE Standard 135 (BACnet), via bacnet-stack 1.6.1"}
    jsonld = PL.graph(PL.ORG, page_ld, ds, PL.breadcrumb_ld(crumbs, url))
    return nav_ref(PL.shell(relpath, title, desc, h1, CSS + body + FILTER, jsonld, crumbs))


HUB_TITLE = "BACnet Units, Property and Error Code Lookup"
HUB_DESC = ("Type any BACnet number and see what it means in every table at once: engineering units, property "
            "IDs, object types, error codes, reliability, services.")

HUB_JS = r"""<script>
(function(){var D=window.REFD,q=document.getElementById('lq'),out=document.getElementById('lq-out');
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function run(){var s=q.value.trim().toLowerCase();if(!s){out.innerHTML='';return;}
 var num=/^\d+$/.test(s),hs=s.replace(/[ _]/g,'-'),h=[],n=0;
 D.t.forEach(function(t){t.r.forEach(function(r){
  var hit=num?String(r[0])===s:(r[1].indexOf(hs)>=0||r[1].replace(/-/g,'').indexOf(s.replace(/[ _-]/g,''))>=0||(r[2]&&r[2].toLowerCase().indexOf(s)>=0));
  if(!hit)return;n++;if(n>60)return;
  h.push('<li><span class="k">'+esc(t.label)+'</span><b class="n">'+r[0]+'</b> <a href="'+t.href+'#'+t.key+r[0]+'">'+esc(r[1])+'</a>'+(r[2]?' <span class="t">('+esc(r[2])+')</span>':'')+(r[3]?'<br><span class="t">'+esc(r[3])+'</span>':'')+'</li>');});});
 out.innerHTML=n?h.join('')+(n>60?'<li class="t">'+(n-60)+' more: type more of the name to narrow it down.</li>':''):'<li>No standard BACnet value matches. Numbers above the standard ranges are usually vendor-proprietary.</li>';
 try{history.replaceState(null,'',location.pathname+'?q='+encodeURIComponent(q.value.trim()));}catch(e){}}
q.addEventListener('input',run);try{var P=new URLSearchParams(location.search);if(P.get('q'))q.value=P.get('q');}catch(e){}run();})();
</script>"""


def hub_page():
    relpath = hub_path()
    url = PL.clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet reference", None)]
    data = {"t": [{"key": ANCHOR[k], "label": TABLE_LABEL[k], "href": "/" + ref_path(PAGE_OF[k])[:-5],
                   "r": [[r["n"], r["id"], r.get("s", "") if k == "units" else (title_case(r["id"]) if k == "property" else ""),
                          hint(k, r)] for r in T[k]]}
                  for p in PAGES for k, _, _ in p[5]]}
    cards = "".join('<li><a href="/%s"><b>BACnet %s</b><span>%s</span><code>%s</code></a></li>'
                    % (ref_path(p[0]), esc(p[2]), esc(p[4].split(". ")[0] + "."),
                       esc(", ".join("%d %s" % (len(T[k]), TABLE_LABEL[k].lower()) for k, _, _ in p[5])))
                    for p in PAGES)
    body = """
<p class="lede">BACnet sends almost everything as a number: the units of a reading, the property you asked for,
the reason a write failed. Type the number (or part of a name) and see what it means in every table at once.</p>
<section class="calc"><h2>BACnet number lookup</h2>
<div class="qbox"><input id="lq" type="search" placeholder="e.g. 62, 31, present value, unknown-object" aria-label="Number or name" autocomplete="off" autofocus></div>
<ul class="hits" id="lq-out" aria-live="polite"></ul>
<p class="count">The same number means different things in different tables (62 is degrees-celsius as a unit and
Max_APDU_Length_Accepted as a property), so every match is labelled with its table.</p></section>
<div class="answer"><b>Short answer</b><p>Common ones: units <strong>62</strong> = degrees-celsius,
<strong>64</strong> = degrees-fahrenheit, <strong>98</strong> = percent; property <strong>85</strong> = Present_Value,
<strong>87</strong> = Priority_Array; error code <strong>31</strong> = unknown-object, <strong>32</strong> =
unknown-property, <strong>40</strong> = write-access-denied; reliability <strong>12</strong> =
communication-failure.</p></div>
<h2>Full tables</h2><ul class="calclist">%(cards)s</ul>
<p class="count">%(src)s</p>
<div class="callout"><p>Other free tools: <a href="/bacnet-object-id-decoder.html">Object Identifier decoder</a>,
<a href="/bacnet-vendor-id-lookup.html">Vendor ID lookup</a>, <a href="/bacnet-instance-calculators/index.html">instance
calculators</a> and <a href="/%(cmp)s">scan vs. points list compare</a>.</p></div>
<script>window.REFD=%(data)s;</script>
""" % {"cards": cards, "src": SOURCE_NOTE, "cmp": COMPARE,
       "data": json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}
    h1 = ('<p class="eyebrow">Free tool &middot; nothing is uploaded</p><h1>BACnet <span class="mfr">number lookup</span></h1>'
          '<p class="updated">Updated %s</p>' % PL.human_date(PUBLISHED))
    app = {"@type": "WebApplication", "@id": url + "#app", "name": "BACnet number lookup", "url": url,
           "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any (web browser)",
           "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
           "description": HUB_DESC, "publisher": {"@id": PL.ORG["@id"]}}
    page_ld = {"@type": "WebPage", "@id": url, "url": url, "name": HUB_TITLE, "description": HUB_DESC,
               "isPartOf": {"@id": PL.BASE_URL + "/#site"}, "mainEntity": {"@id": url + "#app"},
               "dateModified": PUBLISHED, "publisher": {"@id": PL.ORG["@id"]}}
    jsonld = PL.graph(PL.ORG, page_ld, app, PL.breadcrumb_ld(crumbs, url))
    return nav_ref(PL.shell(relpath, HUB_TITLE, HUB_DESC, h1, CSS + body + HUB_JS, jsonld, crumbs))


# ---------------------------------------------------------------------------
# Scan vs points list compare
# ---------------------------------------------------------------------------
CMP_TITLE = "Compare a BACnet Scan With a Points List | Easy BACnet"
CMP_DESC = ("Free tool: drop in an Easy BACnet Excel export, EDE file or CSV and see which points match the "
            "maker's points list, which are missing and which are extra.")

CMP_JS = r"""<script>
(function(){
var TYPES=window.CMP_TYPES,CALC=window.CMP_CALC;
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function norm(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');}
var TYPE_BY=(function(){var m={};TYPES.forEach(function(t){m[norm(t[1])]=t[0];m[norm(t[1].replace(/multistate/,'multi-state'))]=t[0];if(t[2])m[norm(t[2])]=t[0];m[String(t[0])]=t[0];});
 m[norm('Multi-state Input')]=13;m[norm('Multi-state Output')]=14;m[norm('Multi-state Value')]=19;m['msi']=13;m['mso']=14;m['msv']=19;return m;})();
function typeNum(s){s=String(s==null?'':s).trim();if(s==='')return null;var k=norm(s);if(k in TYPE_BY)return TYPE_BY[k];var m=/^(?:type|object)?(\d+)$/.exec(k);return m?+m[1]:null;}
function tname(n){for(var i=0;i<TYPES.length;i++)if(TYPES[i][0]===n)return TYPES[i][2]||TYPES[i][1];return 'Type '+n;}
var LIB=null,MODEL=null,SCAN=null;
// ---- library picker
function loadIndex(){if(LIB)return Promise.resolve(LIB);return fetch('/bacnet-points-lists/index.json').then(function(r){return r.json();}).then(function(d){LIB=d.models;return LIB;});}
function search(){var s=$('cm-q').value.trim().toLowerCase(),box=$('cm-list');if(s.length<2){box.innerHTML='';return;}
 loadIndex().then(function(L){var words=s.split(/\s+/),hits=L.filter(function(m){var t=(m.manufacturer+' '+m.model+' '+(m.aliases||[]).join(' ')+' '+(m.equipment_type||'')).toLowerCase();return words.every(function(w){return t.indexOf(w)>=0;});}).slice(0,12);
  box.innerHTML=hits.length?hits.map(function(m,i){return '<li><button type="button" data-i="'+L.indexOf(m)+'">'+esc(m.manufacturer)+' '+esc(m.model)+' <span class="t">('+m.objects+' objects)</span></button></li>';}).join(''):'<li class="t">No list matches. Try the manufacturer name or a part number.</li>';});}
function pick(i){var m=LIB[i];var path=new URL(m.json,location.href).pathname;$('cm-picked').innerHTML='Loading '+esc(m.manufacturer+' '+m.model)+'&hellip;';
 fetch(path).then(function(r){return r.json();}).then(function(d){var seen={},pts=[];d.points.forEach(function(p){if(p.type==='DEV'||p.type==='Other')return;var t=typeNum(p.type);if(t===null)return;var k=t+':'+p.instance;
  if(seen[k]){seen[k].names.push(p.name);seen[k].name=seen[k].names.join(' / ');return;}var o={t:t,i:p.instance,name:p.name,names:[p.name],d:p.description||''};seen[k]=o;pts.push(o);});
  MODEL={meta:m,path:path,points:pts};
  var page=new URL(m.page,location.href).pathname,rel=page.replace(/^\/bacnet-points-lists\//,''),c=CALC[rel];
  $('cm-picked').innerHTML='List: <a href="'+esc(page)+'">'+esc(m.manufacturer+' '+m.model)+'</a> ('+MODEL.points.length+' objects)'+(c?'<br><strong>This list prints one unit.</strong> Other units have different instance numbers; work them out with the <a href="'+esc(c[0])+'">'+esc(c[1])+' instance calculator</a> before comparing.':'');
  $('cm-list').innerHTML='';run();}).catch(function(){$('cm-picked').textContent='Could not load that list.';});}
// ---- file reading
function u16(b,o){return b[o]|b[o+1]<<8;}function u32(b,o){return(b[o]|b[o+1]<<8|b[o+2]<<16|b[o+3]<<24)>>>0;}
function unzip(buf){var b=new Uint8Array(buf),e=-1;for(var o=b.length-22;o>=Math.max(0,b.length-65557);o--){if(u32(b,o)===0x06054b50){e=o;break;}}
 if(e<0)return Promise.reject(new Error('Not an .xlsx file'));var n=u16(b,e+10),p=u32(b,e+16),files={},jobs=[];
 for(var k=0;k<n;k++){var meth=u16(b,p+10),csize=u32(b,p+20),nl=u16(b,p+28),xl=u16(b,p+30),cl=u16(b,p+32),lo=u32(b,p+42);
  var name=new TextDecoder().decode(b.subarray(p+46,p+46+nl));p+=46+nl+xl+cl;
  if(!/^xl\/(sharedStrings\.xml|worksheets\/sheet1\.xml|workbook\.xml)$/.test(name)&&!/^xl\/worksheets\/sheet\d+\.xml$/.test(name))continue;
  var start=lo+30+u16(b,lo+26)+u16(b,lo+28),data=b.subarray(start,start+csize);
  jobs.push((function(name,meth,data){if(meth===0)return Promise.resolve([name,new TextDecoder().decode(data)]);
   if(meth!==8||typeof DecompressionStream==='undefined')return Promise.reject(new Error('This browser cannot open .xlsx files; save as CSV instead.'));
   return new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text().then(function(t){return[name,t];});})(name,meth,data));}
 return Promise.all(jobs).then(function(r){r.forEach(function(x){files[x[0]]=x[1];});return files;});}
function xlsxRows(files){var P=new DOMParser(),ss=[];if(files['xl/sharedStrings.xml']){var sd=P.parseFromString(files['xl/sharedStrings.xml'],'application/xml');
 [].forEach.call(sd.getElementsByTagName('si'),function(si){ss.push([].map.call(si.getElementsByTagName('t'),function(t){return t.textContent;}).join(''));});}
 var sheet=files['xl/worksheets/sheet1.xml']||files[Object.keys(files).filter(function(k){return /sheet\d+\.xml$/.test(k);}).sort()[0]];if(!sheet)throw new Error('No worksheet found');
 var d=P.parseFromString(sheet,'application/xml'),rows=[];
 [].forEach.call(d.getElementsByTagName('row'),function(r){var row=[];[].forEach.call(r.getElementsByTagName('c'),function(c){var ref=c.getAttribute('r')||'',col=0,m=/^([A-Z]+)/.exec(ref);
  if(m){for(var i=0;i<m[1].length;i++)col=col*26+m[1].charCodeAt(i)-64;col--;}else col=row.length;var t=c.getAttribute('t'),v='';
  if(t==='s'){var vv=c.getElementsByTagName('v')[0];v=vv?ss[+vv.textContent]||'':'';}else if(t==='inlineStr'){v=[].map.call(c.getElementsByTagName('t'),function(x){return x.textContent;}).join('');}
  else{var v2=c.getElementsByTagName('v')[0];v=v2?v2.textContent:'';}row[col]=v;});rows.push(row);});return rows;}
function textRows(t){t=t.replace(/^﻿/,'');var lines=t.split(/\r?\n/).filter(function(l){return l.trim()!=='';});if(!lines.length)return[];
 var cand=[';','\t',','],sep=',';var best=-1;cand.forEach(function(c){var n=lines.slice(0,40).reduce(function(a,l){return a+(l.split(c).length-1);},0);if(n>best){best=n;sep=c;}});
 return lines.map(function(l){var out=[],cur='',q=false;for(var i=0;i<l.length;i++){var ch=l[i];if(q){if(ch==='"'){if(l[i+1]==='"'){cur+='"';i++;}else q=false;}else cur+=ch;}
  else if(ch==='"')q=true;else if(ch===sep){out.push(cur);cur='';}else cur+=ch;}out.push(cur);return out;});}
function findCols(rows){// returns {h,type,inst,name,dev,devname}
 for(var r=0;r<Math.min(rows.length,60);r++){var row=(rows[r]||[]).map(function(x){return norm(String(x||'').replace(/^#\s*/,''));});
  var c={h:r,type:-1,inst:-1,name:-1,dev:-1,devname:-1};
  row.forEach(function(h,i){if(c.type<0&&(h==='objecttype'||h==='type'||h==='objtype'))c.type=i;
   else if(c.inst<0&&(h==='objectnumber'||h==='objectinstance'||h==='instance'||h==='objinstance'||h==='instancenumber'||h==='number'))c.inst=i;
   else if(c.name<0&&(h==='pointname'||h==='objectname'||h==='name'))c.name=i;
   else if(c.dev<0&&(h==='deviceid'||h==='deviceobjinstance'||h==='deviceinstance'||h==='device'))c.dev=i;
   else if(c.devname<0&&h==='devicename')c.devname=i;});
  if(c.type>=0&&c.inst>=0)return c;}return null;}
function parse(rows){var c=findCols(rows);if(!c)throw new Error('Could not find object type and instance columns. The file needs a header row with e.g. "Object Type" and "Object Number" (Easy BACnet), or an EDE layout.');
 var devs={},order=[];for(var r=c.h+1;r<rows.length;r++){var row=rows[r]||[];var t=typeNum(row[c.type]),i=parseInt(String(row[c.inst]||'').trim(),10);if(t===null||isNaN(i))continue;
  var dk=c.dev>=0?String(row[c.dev]||'').trim():'file';if(!(dk in devs)){devs[dk]={id:dk,name:c.devname>=0?row[c.devname]:'',pts:[]};order.push(dk);}
  if(t===8)continue;devs[dk].pts.push({t:t,i:i,name:c.name>=0?String(row[c.name]||''):''});}
 if(!order.length)throw new Error('No BACnet objects found in the file.');return order.map(function(k){return devs[k];}).filter(function(d){return d.pts.length;});}
function readFile(f){$('cm-fmsg').textContent='Reading '+f.name+'...';
 var p=/\.xlsx$/i.test(f.name)?f.arrayBuffer().then(unzip).then(xlsxRows):f.text().then(textRows);
 p.then(function(rows){SCAN=parse(rows);showDevs();$('cm-fmsg').textContent=f.name+': '+SCAN.length+' device'+(SCAN.length===1?'':'s')+', '+SCAN.reduce(function(a,d){return a+d.pts.length;},0)+' objects.';run();})
  .catch(function(e){SCAN=null;showDevs();$('cm-fmsg').textContent=e.message;run();});}
function showDevs(){var s=$('cm-dev');s.innerHTML='';if(!SCAN){s.parentNode.hidden=true;return;}s.parentNode.hidden=SCAN.length<2;
 SCAN.forEach(function(d,i){var o=document.createElement('option');o.value=i;o.textContent=(d.id==='file'?'All rows':'Device '+d.id)+(d.name?' - '+d.name:'')+' ('+d.pts.length+' objects)';s.appendChild(o);});}
// ---- compare
var REPORT=[];
function run(){var out=$('cm-out');if(!MODEL||!SCAN){out.innerHTML='<p class="count">'+(MODEL?'Now add a scan file.':SCAN?'Now pick the points list to compare against.':'Pick a points list and add a scan file.')+'</p>';$('cm-csv').hidden=true;return;}
 // auto-pick the device that overlaps most, once per file
 var sel=$('cm-dev');if(SCAN.length>1&&!sel._auto){var bestI=0,bestN=-1,keys={};MODEL.points.forEach(function(p){keys[p.t+':'+p.i]=1;});
  SCAN.forEach(function(d,i){var n=d.pts.filter(function(p){return keys[p.t+':'+p.i];}).length;if(n>bestN){bestN=n;bestI=i;}});sel.value=bestI;sel._auto=true;}
 var dev=SCAN[+sel.value||0],lib={},scan={},same=[],diff=[],miss=[],extra=[];
 MODEL.points.forEach(function(p){lib[p.t+':'+p.i]=p;});dev.pts.forEach(function(p){scan[p.t+':'+p.i]=p;});
 MODEL.points.forEach(function(p){var s=scan[p.t+':'+p.i];if(!s)miss.push(p);else if(!s.name||p.names.some(function(n){return norm(n)===norm(s.name);}))same.push([p,s]);else diff.push([p,s]);});
 dev.pts.forEach(function(p){if(!lib[p.t+':'+p.i])extra.push(p);});
 function ab(t){return tname(t);}
 function tbl(rows,head){return '<div class="tablewrap"><table class="pts"><thead><tr>'+head.map(function(h){return '<th>'+h+'</th>';}).join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';}
 var h='<dl class="facts"><div><dt>Match</dt><dd>'+same.length+'</dd></div><div><dt>Same object, different name</dt><dd>'+diff.length+'</dd></div><div><dt>In the list, not on the device</dt><dd>'+miss.length+'</dd></div><div><dt>On the device, not in the list</dt><dd>'+extra.length+'</dd></div></dl>';
 var pct=MODEL.points.length?Math.round(100*(same.length+diff.length)/MODEL.points.length):0;
 h+='<p>'+pct+'% of the list\'s objects were found on '+(dev.id==='file'?'the device':'device '+esc(dev.id))+'.'+(pct<20?' <strong>Very little matches</strong> &mdash; check that you picked the right list, the right device, and (for gateways) the right unit.':'')+'</p>';
 if(diff.length)h+='<h3>Same object, different name ('+diff.length+')</h3>'+tbl(diff.map(function(x){return '<tr><td class="t">'+esc(ab(x[0].t))+'</td><td class="i">'+x[0].i+'</td><td class="n">'+esc(x[0].name)+'</td><td>'+esc(x[1].name)+'</td></tr>';}),['Type','Instance','Name in list','Name on device']);
 if(miss.length)h+='<h3>In the list, not on the device ('+miss.length+')</h3><p class="count">Usually options the unit does not have, a different firmware, or a list for a different model.</p>'+tbl(miss.map(function(p){return '<tr><td class="t">'+esc(ab(p.t))+'</td><td class="i">'+p.i+'</td><td class="n">'+esc(p.name)+'</td><td>'+esc(p.d)+'</td></tr>';}),['Type','Instance','Name in list','What it is']);
 if(extra.length)h+='<h3>On the device, not in the list ('+extra.length+')</h3><p class="count">Often vendor-specific or configuration objects the published list leaves out.</p>'+tbl(extra.map(function(p){return '<tr><td class="t">'+esc(ab(p.t))+'</td><td class="i">'+p.i+'</td><td class="n">'+esc(p.name)+'</td></tr>';}),['Type','Instance','Name on device']);
 if(same.length)h+='<details><summary>Matching objects ('+same.length+')</summary>'+tbl(same.map(function(x){return '<tr><td class="t">'+esc(ab(x[0].t))+'</td><td class="i">'+x[0].i+'</td><td class="n">'+esc(x[0].name)+'</td></tr>';}),['Type','Instance','Name'])+'</details>';
 out.innerHTML=h;REPORT=[['Result','Object type','Instance','Name in list','Name on device']];
 same.forEach(function(x){REPORT.push(['Match',ab(x[0].t),x[0].i,x[0].name,x[1].name]);});diff.forEach(function(x){REPORT.push(['Name differs',ab(x[0].t),x[0].i,x[0].name,x[1].name]);});
 miss.forEach(function(p){REPORT.push(['Not on device',ab(p.t),p.i,p.name,'']);});extra.forEach(function(p){REPORT.push(['Not in list',ab(p.t),p.i,'',p.name]);});$('cm-csv').hidden=false;}
function csvq(s){s=String(s==null?'':s);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;}
$('cm-csv').addEventListener('click',function(){var b=new Blob([REPORT.map(function(r){return r.map(csvq).join(',');}).join('\r\n')+'\r\n'],{type:'text/csv'});
 var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='scan-vs-points-list.csv';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);});
$('cm-q').addEventListener('input',search);$('cm-list').addEventListener('click',function(e){var b=e.target.closest('button[data-i]');if(b)pick(+b.getAttribute('data-i'));});
$('cm-file').addEventListener('change',function(){if(this.files[0]){$('cm-dev')._auto=false;readFile(this.files[0]);}});
$('cm-paste-go').addEventListener('click',function(){try{SCAN=parse(textRows($('cm-paste').value));$('cm-dev')._auto=false;showDevs();$('cm-fmsg').textContent='Pasted: '+SCAN.reduce(function(a,d){return a+d.pts.length;},0)+' objects.';}catch(e){SCAN=null;showDevs();$('cm-fmsg').textContent=e.message;}run();});
$('cm-dev').addEventListener('change',run);
var drop=$('cm-drop');['dragover','dragenter'].forEach(function(ev){drop.addEventListener(ev,function(e){e.preventDefault();drop.classList.add('over');});});
['dragleave','drop'].forEach(function(ev){drop.addEventListener(ev,function(e){e.preventDefault();drop.classList.remove('over');});});
drop.addEventListener('drop',function(e){var f=e.dataTransfer.files[0];if(f){$('cm-dev')._auto=false;readFile(f);}});
try{var P=new URLSearchParams(location.search),want=P.get('list');if(want){loadIndex().then(function(L){for(var i=0;i<L.length;i++){if(new URL(L[i].page,location.href).pathname.replace(/^\/bacnet-points-lists\//,'')===want){pick(i);break;}}});}}catch(e){}
run();
})();
</script>"""

CMP_CSS = """<style>
.drop{border:2px dashed var(--line);border-radius:12px;padding:1.2rem;text-align:center;margin:.6rem 0}
.drop.over{border-color:var(--accent);background:rgba(255,154,31,.08)}
.drop input{margin-top:.5rem;font:inherit;color:var(--fg);max-width:100%;box-sizing:border-box}
#cm-list{list-style:none;padding:0;margin:.4rem 0}
#cm-list button{width:100%;text-align:left;font:inherit;color:var(--fg);background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:.55rem .75rem;margin:.25rem 0;cursor:pointer}
#cm-list button:hover{border-color:var(--accent)}
#cm-list .t,.t{color:var(--mut);font-size:.86rem}
#cm-paste{width:100%;min-height:6rem;font:inherit;font-family:"IBM Plex Mono",monospace;font-size:.85rem;color:var(--fg);background:var(--code);border:1px solid var(--line);border-radius:9px;padding:.6rem}
.step{font-family:"IBM Plex Mono",monospace;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:1.2rem 0 .3rem}
</style>"""


def compare_page():
    relpath = COMPARE
    url = PL.clean(relpath)
    crumbs = [("Home", "/index.html"), ("Scan vs. points list compare", None)]
    types = [[r["n"], r["id"], ""] for r in T["object_type"]]
    abbr = {v[1]: k for k, v in PL.OBJECT_TYPES.items() if v[1] is not None}
    for t in types:
        t[2] = abbr.get(t[0], "")
    # Only lists whose object instances move with the unit address (not device-ID schemes).
    obj_calc = {c["slug"] for c in calculators.CALCS if c["kind"] == "object"}
    calc = {rel: [u, lab] for rel, lst in calculators.links().items() for u, lab in lst
            if u.rsplit("/", 1)[-1].replace(".html", "") in obj_calc}
    body = """
<p class="lede">Does the device in front of you match its manufacturer's points list? Pick the list, drop in your
scan, and see what matches, what is missing and what is extra. Everything happens in your browser; the file is
never uploaded.</p>
<section class="calc" aria-label="Compare">
<p class="step">1 &middot; Points list</p>
<div class="qbox"><input id="cm-q" type="search" placeholder="Manufacturer, model or part number, e.g. Trane Symbio" aria-label="Find a points list" autocomplete="off"></div>
<ul id="cm-list" aria-live="polite"></ul>
<p id="cm-picked" class="count" aria-live="polite"></p>
<p class="step">2 &middot; Your scan</p>
<div class="drop" id="cm-drop"><strong>Drop a file here</strong> or choose one:<br>
<input type="file" id="cm-file" accept=".xlsx,.csv,.txt,.ede"><br>
<span class="t">Easy BACnet Excel export (.xlsx), an EDE file (.csv) or any CSV with object type and instance columns.</span></div>
<details><summary>Or paste rows</summary><textarea id="cm-paste" placeholder="Object Type,Object Number,Point Name&#10;Analog Input,1,Zone Temp&#10;Binary Output,3,Fan Start"></textarea>
<button type="button" class="sec" id="cm-paste-go" style="margin-top:.5rem;font:inherit;font-weight:700;padding:.5rem .9rem;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--fg);cursor:pointer">Use pasted rows</button></details>
<p id="cm-fmsg" class="count" aria-live="polite"></p>
<div class="cin" hidden><div><label for="cm-dev">Device in the file</label><select id="cm-dev"></select></div></div>
<p class="step">3 &middot; Result</p>
<div id="cm-out" aria-live="polite"><p class="count">The compare tool needs JavaScript.</p></div>
<div class="cbar"><button type="button" id="cm-csv" hidden>Download the comparison (CSV)</button></div>
</section>
<h2>How it compares</h2>
<p>Objects are matched by <strong>object type and instance number</strong>, the way a BMS finds them. A match with a
different name usually means the integrator or the manufacturer renamed the point; the object is the same. Objects
in the list but not on the device are normally options the unit does not have or a different firmware.</p>
<p>Gateways that number objects by unit address (VRF gateways, boiler cascades) print only one unit in their list.
For those, the tool says so and links the matching <a href="/bacnet-instance-calculators/index.html">instance
calculator</a>.</p>
<h2>Getting a scan file</h2>
<p><a href="/index.html">Easy BACnet</a> scans the network from an Android phone, reads every object on each device
and exports the result to Excel; that file drops straight in here. Exports from other tools work too if they have
an object type column and an instance column (EDE files from most BACnet tools do).</p>
<div class="callout"><p>Not sure which list fits your unit? Browse the <a href="/bacnet-points-lists/index.html">points-list
library</a> (%(n)s lists) or read <a href="/guides/find-bacnet-points-list-for-your-equipment.html">how to find the points
list for your equipment</a>.</p></div>
<script>window.CMP_TYPES=%(types)s;window.CMP_CALC=%(calc)s;</script>
""" % {"types": json.dumps(types), "calc": json.dumps(calc), "n": "{:,}".format(len(PL.LASTMOD) and PL_COUNT())}
    h1 = ('<p class="eyebrow">Free tool &middot; nothing is uploaded</p><h1>Compare a scan with a '
          '<span class="mfr">points list</span></h1><p class="updated">Updated %s</p>' % PL.human_date(PUBLISHED))
    app = {"@type": "WebApplication", "@id": url + "#app", "name": "BACnet scan vs. points list compare", "url": url,
           "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any (web browser)",
           "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
           "description": CMP_DESC, "publisher": {"@id": PL.ORG["@id"]}}
    page_ld = {"@type": "WebPage", "@id": url, "url": url, "name": CMP_TITLE, "description": CMP_DESC,
               "isPartOf": {"@id": PL.BASE_URL + "/#site"}, "mainEntity": {"@id": url + "#app"},
               "dateModified": PUBLISHED, "publisher": {"@id": PL.ORG["@id"]}}
    jsonld = PL.graph(PL.ORG, page_ld, app, PL.breadcrumb_ld(crumbs, url))
    return nav_ref(PL.shell(relpath, CMP_TITLE, CMP_DESC, h1, calculators.CALC_CSS + CSS + CMP_CSS + body + CMP_JS,
                            jsonld, crumbs))


def PL_COUNT():
    return sum(1 for p in PL.LASTMOD if p.startswith(PL.ROOT + "/") and p.count("/") == 2
               and not p.endswith("index.html"))


def build(write):
    out_dir = os.path.join(PL.HERE, ROOT)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    paths = [hub_path()]
    write(hub_path(), hub_page())
    for p in PAGES:
        write(ref_path(p[0]), ref_page(p))
        paths.append(ref_path(p[0]))
    write(COMPARE, compare_page())
    paths.append(COMPARE)
    for p in paths:
        PL.LASTMOD[p] = PUBLISHED
    llms = ["", "## BACnet reference and tools",
            "- BACnet number lookup (search every table): %s" % PL.clean(hub_path())]
    for p in PAGES:
        llms.append("- BACnet %s: %s" % (p[2], PL.clean(ref_path(p[0]))))
    llms.append("- Compare a BACnet scan with a points list: %s" % PL.clean(COMPARE))
    return paths, llms
