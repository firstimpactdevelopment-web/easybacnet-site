"""Data-quality audit for points_data/*.json. Run: python tools_audit_points.py"""
import glob, io, json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
HEADER_WORDS = {"object name", "name", "object type", "type", "instance", "units", "description", "access", "point name"}
issues = collections.defaultdict(list)
totals = collections.Counter()

for path in sorted(glob.glob(os.path.join(HERE, "points_data", "*", "*.json"))):
    rel = os.path.relpath(path, HERE)
    d = json.load(io.open(path, encoding="utf-8"))
    pts = d.get("points") or []
    totals["models"] += 1
    totals["points"] += len(pts)
    seen = collections.Counter((p.get("type"), p.get("instance")) for p in pts)
    dups = [k for k, c in seen.items() if c > 1]
    if dups:
        issues[rel].append("%d duplicate type/instance pairs e.g. %s" % (len(dups), dups[:3]))
    for p in pts:
        n = (p.get("name") or "").strip()
        if n.lower() in HEADER_WORDS:
            issues[rel].append("header leaked: %r" % n)
        if len(n) > 80:
            issues[rel].append("very long name: %r" % n[:60])
        if re.search(r"\|\s|\s{3,}|\\n", n):
            issues[rel].append("garbled name: %r" % n[:60])
        if len((p.get("description") or "").split()) > 16:
            issues[rel].append("long description (%d words) on %s %s" % (len(p["description"].split()), p.get("type"), p.get("instance")))
    if not pts:
        issues[rel].append("no points")
    it = d.get("integration")
    if not isinstance(it, dict):
        issues[rel].append("NO integration object")
    else:
        refs = {(p.get("type", "").upper(), p.get("instance")) for p in pts}
        for mp in it.get("minimum_points") or []:
            m = re.fullmatch(r"\s*([A-Za-z]+)[\s:_-]*(\d+)\s*", mp.get("ref") or "")
            if not m or (m.group(1).upper(), int(m.group(2))) not in refs:
                issues[rel].append("bad minimum_points ref %r" % mp.get("ref"))
        if not (it.get("minimum_points")):
            issues[rel].append("integration has no minimum_points")
    for k in ("summary", "equipment_type", "applies_to"):
        if not d.get(k):
            issues[rel].append("missing " + k)
    if len(d.get("summary") or "") > 700:
        issues[rel].append("summary very long (%d chars)" % len(d["summary"]))

print("models=%d points=%d" % (totals["models"], totals["points"]))
for rel, lst in issues.items():
    uniq = list(dict.fromkeys(lst))
    print("\n" + rel)
    for x in uniq[:8]:
        print("  - " + x)
    if len(uniq) > 8:
        print("  ... %d more" % (len(uniq) - 8))
