"""Device Remotes: ready-made remote templates for the Easy BACnet apps.

Each high-confidence points list gets a `.ebremote` template the phone and PC
apps import into their Device Remotes section ("Download a Remote for This
Device" on the points-list page). The contract is docs/DEVICE_REMOTES_SPEC.md
in the parent repo; the widget JSON is exactly the apps' RemoteWidget.toJson().

High confidence only: the manufacturer's document states read/write access
(`access_inferred` is present and false) and the list has at least one writable
analog, binary or multi-state value/output. Anything else gets no template and
no button, because a remote built on guessed access could write to a point
that doesn't take writes.
"""
import json
import re
import uuid

import os

# OFF until app releases with Device Remotes are live (Tim: ships only after a
# Pixel test and a clean bug hunt). While off, no template files and no button
# are built, so a routine site push can't publish them early. Build with
# EASYBACNET_DEVICE_REMOTES=1 to preview locally.
ENABLED = os.environ.get("EASYBACNET_DEVICE_REMOTES") == "1"

ROOT = "device-remotes"
BASE_URL = "https://easybacnet.com"
FORMAT = "easybacnet-device-remote"
VERSION = 1
MAX_CONTROLS = 48
COLUMNS = 4

# BACnet object type numbers.
TYPE_NUM = {"AI": 0, "AO": 1, "AV": 2, "BI": 3, "BO": 4, "BV": 5, "MI": 13, "MO": 14, "MV": 19}
WRITABLE_TYPES = ("AO", "AV", "BO", "BV", "MO", "MV")
MAX_INSTANCE = 4194303


def _ref(ref):
    m = re.fullmatch(r"\s*([A-Za-z]+)[\s:_-]*(\d+)\s*", ref or "")
    return (m.group(1).upper(), int(m.group(2))) if m else None


def _writable(p):
    return p.get("access") in ("W", "C")


def _usable(p):
    t = (p.get("type") or "").upper()
    inst = p.get("instance")
    return t in TYPE_NUM and isinstance(inst, int) and not isinstance(inst, bool) and 0 <= inst < MAX_INSTANCE


def eligible(m):
    """True when this list is solid enough to build a remote from."""
    if m.get("access_inferred") is not False:
        return False
    return any(_usable(p) and _writable(p) and p["type"].upper() in WRITABLE_TYPES for p in m["points"])


def _label(p):
    """Readable label: the description without its "(default ...)" tail when it is
    short enough, else the object name. Object names are often cryptic
    (tempering_stpt); descriptions read better on a tile."""
    name = (p.get("name") or "").strip()
    desc = re.sub(r"\s*\((?:default|def\.?)[^)]*\)\s*$", "", (p.get("description") or "").strip(), flags=re.I).strip()
    text = desc if desc and len(desc) <= 40 else name or desc
    text = re.sub(r"\s+", " ", text)
    return text[:40] or "%s %d" % (p["type"].upper(), p["instance"])


def _states(text):
    """"1=Off, 2=Heat, 3=Cool" -> ["Off", "Heat", "Cool"] (index = state - 1).
    None unless the states are numbered 1..n with no gaps: a picker that put a
    label against the wrong number would write the wrong state."""
    found = {}
    for part in re.split(r"[,;\n]", text or ""):
        m = re.fullmatch(r"\s*(\d+)\s*[=:\-]\s*(.+?)\s*", part)
        if m:
            found[int(m.group(1))] = m.group(2)[:40]
    if not found or sorted(found) != list(range(1, len(found) + 1)):
        return None
    return [found[i] for i in range(1, len(found) + 1)]


def _widget(p, writable):
    t = p["type"].upper()
    units = (p.get("units") or "").strip().lower()
    w = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "%s:%d" % (t, p["instance"]))),
        "kind": "READOUT", "label": _label(p), "objectType": TYPE_NUM[t], "objectInstance": p["instance"],
        "priority": 8, "step": 1.0, "onValue": 1, "offValue": 0, "buttonValue": 1.0, "states": [],
        "accent": "DEFAULT", "style": "FILLED", "bigValue": False, "deviceInstance": -1,
    }
    if writable and t in ("AO", "AV"):
        w["kind"] = "SETPOINT"
        w["style"] = "BOLD"
        if units == "%":
            w.update(step=5.0, minValue=0.0, maxValue=100.0)
        elif units in ("v", "volts"):
            w["step"] = 0.1
    elif writable and t in ("BO", "BV"):
        w["kind"] = "TOGGLE"
        w["style"] = "BOLD"
    elif writable and t in ("MO", "MV"):
        states = _states(p.get("states"))
        if states:
            w["kind"] = "MULTISTATE"
            w["style"] = "BOLD"
            w["states"] = states
    elif t in ("BI", "BV", "BO", "MI", "MV", "MO"):
        states = _states(p.get("states"))
        if states:
            w["states"] = states   # lets the readout show "Heat", not "2"
    if w["kind"] == "READOUT":
        w["style"] = "OUTLINED"
    return w


def template(m, page_url):
    """The template dict for list m, or None when it doesn't qualify."""
    if not eligible(m):
        return None
    index = {}
    for p in m["points"]:
        if _usable(p):
            index.setdefault((p["type"].upper(), p["instance"]), p)
    chosen, seen = [], set()

    def add(p, include_read):
        key = (p["type"].upper(), p["instance"])
        if key in seen or len(chosen) >= MAX_CONTROLS:
            return
        writable = _writable(p) and key[0] in WRITABLE_TYPES
        if not writable and not include_read:
            return
        seen.add(key)
        chosen.append(_widget(p, writable))

    # 1. The integrator's minimum points, in their order (reads included: the
    #    status they name is what you check after commanding the unit).
    for mp in ((m.get("integration") or {}).get("minimum_points") or []):
        key = _ref(mp.get("ref"))
        if key and key in index:
            add(index[key], include_read=True)
    # 2. Every other writable point, in document order.
    for p in m["points"]:
        if _usable(p):
            add(p, include_read=False)
    if not any(w["kind"] != "READOUT" for w in chosen):
        return None
    for i, w in enumerate(chosen):
        w.update(gx=(i % 2) * 2, gy=i // 2, gw=2, gh=1)
    name = "%s %s" % (m["manufacturer"], m.get("short_model") or m["model"])
    if len(name) > 60:
        # Too long for a title: drop the bracketed detail whole first
        # ("(ProtoNode FPC-N54 profile)"), then cut at a word, and never leave
        # half a bracket behind.
        name = re.sub(r"\s*\([^)]*\)", "", name).strip()
        if len(name) > 60:
            name = re.sub(r"[\s,\-/]+\S*$", "", name[:61]).rstrip(" ,-/")
        if name.count("(") > name.count(")"):
            name = name[:name.rindex("(")].rstrip(" ,-/")
    return {
        "format": FORMAT, "version": VERSION,
        "manufacturer": m["manufacturer"], "model": m["model"], "name": name,
        "source": page_url, "columns": COLUMNS, "widgets": chosen,
    }


def path_of(m):
    return "%s/%s/%s.ebremote" % (ROOT, m["manufacturer_slug"], m["model_slug"])


def text_of(t):
    return json.dumps(t, ensure_ascii=False, indent=1) + "\n"


PLAY = ("https://play.google.com/store/apps/details?id=com.easybacnet.app"
        "&utm_source=easybacnet.com&utm_medium=device_remote&utm_campaign=points")


def button_html(m, t):
    """The "Download a Remote for This Device" button and its small helper script.
    Android opens the app straight into the import (Play Store if it isn't
    installed); Windows hands the link to the PC app; anything else downloads
    the file to import by hand."""
    href = "/" + path_of(m)
    full = BASE_URL + href
    from urllib.parse import quote
    u = quote(full, safe="")
    android = ("intent://import?u=%s#Intent;scheme=easybacnet;package=com.easybacnet.app;"
               "S.browser_fallback_url=%s;end" % (u, quote(PLAY, safe="")))
    windows = "easybacnet://import?u=%s" % u
    n = len(t["widgets"])
    return """
<div class="devremote">
  <a class="btn primary devremote-btn" href="%(href)s" download data-android="%(android)s" data-windows="%(windows)s">Download a Remote for This Device <small>%(n)d controls &middot; Easy BACnet app</small></a>
  <p class="count">Opens in the Easy BACnet app (Android or Windows) under <strong>Device Remotes</strong>. Enter your
  unit&rsquo;s Device ID and it&rsquo;s ready to use. Pro users can add more units and command them all at once.
  No app? <a href="%(href)s" download>Download the .ebremote file</a> and import it later.
  Check every control against the live unit before you write &mdash; <a href="/terms.html#content">terms</a>.</p>
</div>
<script>
(function(){
  var b=document.querySelector('.devremote-btn');if(!b)return;
  b.addEventListener('click',function(e){
    var ua=navigator.userAgent,p=/Android/i.test(ua)?'android':(/Windows/i.test(ua)?'windows':'other');
    if(window.gtag)gtag('event','device_remote_click',{platform:p,page_path:location.pathname,transport_type:'beacon'});
    if(p==='android'){e.preventDefault();location.href=b.getAttribute('data-android');}
    else if(p==='windows'){
      // Hand the link to the PC app. If nothing takes it (app not installed),
      // the page keeps focus: fall back to downloading the file.
      e.preventDefault();var left=false,f=function(){left=true;};
      window.addEventListener('blur',f,{once:true});
      location.href=b.getAttribute('data-windows');
      setTimeout(function(){window.removeEventListener('blur',f);if(!left&&!document.hidden)location.href=b.getAttribute('href');},2000);
    }
  });
})();
</script>""" % {"href": href, "android": html_attr(android), "windows": html_attr(windows), "n": n}


def html_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")
