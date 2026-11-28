"""Shared-scan pages: /view (enter a code, see the scans), /share-admin (only
useful while the share server runs in "open" mode) and the how-to guide.

The scans are decrypted in the visitor's browser by js/share-crypto.js. The
code is read from the box or from the link's #fragment, which browsers never
send to a server. No analytics or ads run on these pages.
"""

BASE_URL = "https://easybacnet.com"
API_PROD = "https://api.easybacnet.com"
VIEW = "view"
ADMIN = "share-admin"
GUIDE = "guides/share-bacnet-scan-results-with-a-code"
UPDATED = "2026-11-27"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<!--no-analytics-->
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="no-referrer">
<meta name="theme-color" content="#14171a">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800;900&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>%(css)s</style>
</head>
<body>

<header class="site">
  <a href="index.html" style="display:inline-flex;align-items:center;gap:.5rem;text-decoration:none"><img src="icon.svg" alt="" width="26" height="26" style="border-radius:6px"><span>Easy BACnet</span></a>
  <span class="muted">&middot; shared scans</span>
  <a class="getapp" href="%(play)s" rel="noopener">Get the app</a>
</header>
"""

VIEW_CSS = """
  body { max-width: 64rem; }
  .codebox { display:flex; gap:.6rem; flex-wrap:wrap; align-items:stretch; }
  .codebox input { flex:1 1 14rem; max-width:20rem; font-size:1.5rem; letter-spacing:.18em;
                   text-transform:uppercase; text-align:center; }
  .codebox button { margin-top:0; }
  .msg { margin-top:1rem; color:var(--muted); }
  .msg.err { color:#ff8a7a; }
  .folder { color:var(--muted); font-family:"IBM Plex Mono",monospace; font-size:.85rem;
            margin:1.5rem 0 .6rem; letter-spacing:.04em; }
  .scans { display:grid; grid-template-columns:repeat(auto-fill,minmax(15rem,1fr)); gap:.8rem; }
  .scan { text-align:left; background:var(--code); border:1px solid var(--line); border-radius:12px;
          padding:.85rem 1rem; color:var(--fg); cursor:pointer; font:inherit; margin:0; }
  .scan:hover, .scan.on { border-color:var(--accent); }
  .scan b { display:block; font-family:"Archivo",sans-serif; font-size:1rem; }
  .scan span { display:block; color:var(--muted); font-size:.85rem; line-height:1.5; }
  .bar { display:flex; gap:.6rem; flex-wrap:wrap; align-items:center; margin:1.4rem 0 .4rem; }
  .bar input { flex:1 1 14rem; max-width:22rem; padding:.55rem .7rem; font-size:.95rem; color:var(--fg);
               font-family:"IBM Plex Mono",ui-monospace,monospace; background:var(--code);
               border:1px solid var(--line); border-radius:8px; }
  .bar button { padding:.6rem 1.1rem; font-family:"Archivo",sans-serif; font-weight:700;
                text-transform:uppercase; letter-spacing:.03em; font-size:.8rem; color:var(--ink);
                background:var(--accent); border:1px solid var(--accent); border-radius:8px; cursor:pointer; }
  .bar .ghost { background:transparent; color:var(--fg); border:1px solid var(--line); }
  .bar .ghost:hover { border-color:var(--accent); }
  .dev { margin:1.6rem 0 .4rem; }
  .dev h3 { margin:0; font-family:"Archivo",sans-serif; }
  .dev p { margin:.1rem 0 .5rem; color:var(--muted); font-size:.85rem; font-family:"IBM Plex Mono",monospace; }
  .tablewrap { overflow-x:auto; }
  table.pts { width:100%; border-collapse:collapse; font-size:.88rem; }
  table.pts th, table.pts td { text-align:left; padding:.35rem .55rem; border-bottom:1px solid var(--line);
                               vertical-align:top; }
  table.pts th { font-family:"IBM Plex Mono",monospace; font-size:.7rem; letter-spacing:.1em;
                 text-transform:uppercase; color:var(--accent); }
  table.pts td.v { font-family:"IBM Plex Mono",monospace; white-space:nowrap; }
  .net { background:var(--code); border:1px solid var(--line); border-radius:10px; padding:.6rem .9rem;
         font-family:"IBM Plex Mono",monospace; font-size:.85rem; margin:.8rem 0; }
  .lock { color:var(--muted); font-size:.85rem; margin-top:.9rem; }
  .hidden { display:none; }
  table.adm { width:100%; border-collapse:collapse; } table.adm td, table.adm th { padding:.35rem .5rem; border-bottom:1px solid var(--line); text-align:left; }
"""

VIEW_BODY = """
<article>
  <h1>View a shared scan</h1>
  <p>Someone ran a scan in the Easy BACnet app and gave you a code. Type it here to see
  their results: every device and point, with the values read at the time of the scan.</p>

  <div class="tool">
    <label for="code">8-character code</label>
    <form class="codebox" id="f" autocomplete="off">
      <input id="code" name="code" maxlength="24" placeholder="K7QM-4XPR" spellcheck="false" autocapitalize="characters" aria-label="Share code">
      <button type="submit" id="go">View</button>
    </form>
    <p class="msg" id="msg" role="status"></p>
    <p class="lock">Scans are encrypted on the phone or PC with this code. Our server only
    stores scrambled data and can't read it. Your browser unlocks it here. Shared scans
    delete themselves 7 days after the last one was added.</p>
  </div>

  <div id="out" class="hidden">
    <p class="folder" id="folder"></p>
    <div class="scans" id="scans"></div>
    <div id="detail" class="hidden">
      <div class="bar">
        <input id="filter" placeholder="Filter points (name, type, value)" aria-label="Filter points">
        <button type="button" id="csv">Download CSV</button>
        <button type="button" id="csvall" class="ghost">Download all scans</button>
      </div>
      <div class="net" id="net"></div>
      <div id="devs"></div>
    </div>
  </div>
</article>

<footer>
  <p>Shared from <a href="index.html">Easy BACnet</a>, a free BACnet IP scanner and explorer.
  <a href="%(guide)s">How sharing works</a> &middot; <a href="privacy.html">Privacy policy</a> &middot;
  <a href="terms.html">Terms of use</a></p>
</footer>

<script type="module">
import { normalizeCode, formatCode, deriveKeys, openBlob } from "./js/share-crypto.js?v=2";

const LOCAL = ["localhost", "127.0.0.1"].includes(location.hostname);
// ?api= is for local testing only; on easybacnet.com the server address is fixed.
const API = LOCAL ? (new URLSearchParams(location.search).get("api") || "http://127.0.0.1:8787") : "%(api)s";
const $ = (id) => document.getElementById(id);
let keys = null, folder = null, current = null;
const DEMO_CODES = ["GQLMQX9Z", "K7QM4XPR"];
const cache = new Map();

function say(text, err) { $("msg").textContent = text; $("msg").className = "msg" + (err ? " err" : ""); }
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const when = (iso) => { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); };
function left(ms) {
  const h = Math.max(0, Math.round((ms - Date.now()) / 3600000));
  return h >= 48 ? Math.round(h / 24) + " days" : h + " hours";
}

async function api(path, tries = 3) {
  const r = await fetch(API + path, { cache: "no-store", referrerPolicy: "no-referrer" });
  const j = await r.json().catch(() => ({}));
  // Busy (many scans in one code): wait and try again rather than failing halfway.
  if (r.status === 429 && tries > 0) { await new Promise((ok) => setTimeout(ok, 15000)); return api(path, tries - 1); }
  if (!r.ok) throw new Error(j.error || "Could not reach the server. Try again.");
  return j;
}

async function open(raw) {
  const code = normalizeCode(raw);
  if (!code) { say("A code is 8 letters and numbers, like K7QM-4XPR. It never uses 0, O, 1 or I.", true); return; }
  // Codes printed in our own store screenshots and examples never hold real scans.
  if (DEMO_CODES.includes(code)) {
    $("code").value = formatCode(code);
    $("out").classList.add("hidden");
    $("msg").className = "msg";
    $("msg").innerHTML = "Nice try! That code is from our screenshots, so there's nothing behind it. " +
      'Run a scan in the <a href="%(play)s" rel="noopener">Easy BACnet app</a> and share your own.';
    return;
  }
  $("code").value = formatCode(code);
  $("go").disabled = true;
  say("Unlocking…");
  try {
    keys = await deriveKeys(code);
    folder = await api("/api/share/folders/" + keys.id);
    cache.clear();
    history.replaceState(null, "", location.pathname + location.search + "#" + formatCode(code));
    const metas = await Promise.all(folder.scans.map(async (s) => {
      try { return { ...s, meta: await openBlob(s.summary, keys, s.enc) }; }
      catch { return { ...s, meta: null }; }
    }));
    folder.scans = metas;
    renderFolder();
    say("");
    if (metas.length) show(metas[metas.length - 1].seq);
    else say("This code has no scans yet. Ask the sender to add one.");
  } catch (e) {
    $("out").classList.add("hidden");
    say(e.message || "Something went wrong.", true);
  } finally { $("go").disabled = false; }
}

function renderFolder() {
  $("out").classList.remove("hidden");
  const n = folder.scans.length;
  $("folder").textContent = n + (n === 1 ? " scan" : " scans") + " · deletes itself in " + left(folder.expires) +
    (folder.mode === "open" ? " · stored unencrypted" : " · encrypted");
  $("scans").innerHTML = folder.scans.map((s) => {
    const m = s.meta;
    const n = Number(s.seq) || 0;
    if (!m) return `<button class="scan" disabled><b>Scan ${n}</b><span>Could not unlock this scan.</span></button>`;
    return `<button class="scan" data-seq="${n}"><b>${esc(when(m.scannedAt))}</b>
      <span>${esc(m.kind === "advanced" ? "Advanced scan" : "Easy scan")} · ${esc(m.devices)} ${m.devices === 1 ? "device" : "devices"} · ${esc(m.points)} ${m.points === 1 ? "point" : "points"}</span>
      <span>Scanned from ${esc(m.ip || "unknown IP")}${m.app ? " · " + esc(m.app) : ""}</span></button>`;
  }).reverse().join("");
  for (const b of $("scans").querySelectorAll("button[data-seq]")) b.onclick = () => show(Number(b.dataset.seq));
}

async function scan(seq) {
  if (cache.has(seq)) return cache.get(seq);
  const s = await api("/api/share/folders/" + keys.id + "/scans/" + seq);
  const data = await openBlob(s.blob, keys, s.enc);
  cache.set(seq, data);
  return data;
}

async function show(seq) {
  for (const b of $("scans").querySelectorAll(".scan")) b.classList.toggle("on", Number(b.dataset.seq) === seq);
  say("Loading scan…");
  try {
    current = await scan(seq);
    say("");
    $("detail").classList.remove("hidden");
    drawScan();
  } catch (e) { say(e.message || "Could not open that scan.", true); }
}

function drawScan() {
  const d = current, q = $("filter").value.trim().toLowerCase();
  const n = d.network || {};
  $("net").innerHTML = "Scanned " + esc(when(d.scannedAt)) + " from <b>" + esc(n.ip || "unknown") + "</b>" +
    (n.mask ? " mask " + esc(n.mask) : n.prefix ? "/" + esc(n.prefix) : "") +
    (n.gateway ? " · gateway " + esc(n.gateway) : "") + (n.iface ? " · " + esc(n.iface) : "") +
    (d.app ? "<br>" + esc(d.app) : "");
  let shown = 0;
  $("devs").innerHTML = (d.devices || []).map((dev) => {
    const pts = (dev.points || []).filter((p) => !q ||
      [p.name, p.typeName, p.instance, p.value, p.units, p.status, p.description].join(" ").toLowerCase().includes(q));
    const devHit = !q || [dev.name, dev.instance, dev.ip, dev.model].join(" ").toLowerCase().includes(q);
    if (!pts.length && !devHit) return "";
    shown++;
    const rows = pts.map((p) => `<tr><td>${esc(p.typeName)}</td><td>${esc(p.instance)}</td><td>${esc(p.name)}</td>
      <td class="v">${esc(p.value)}</td><td>${esc(p.units)}</td><td>${esc(p.status)}</td></tr>`).join("");
    return `<section class="dev"><h3>${esc(dev.name || "Device " + dev.instance)}</h3>
      <p>Device ${esc(dev.instance)} · ${esc(dev.ip)}${dev.port && dev.port !== 47808 ? ":" + esc(dev.port) : ""}${dev.network ? " · network " + esc(dev.network) : ""}${dev.model ? " · " + esc(dev.model) : ""} · ${(dev.points || []).length} points</p>
      ${rows ? `<div class="tablewrap"><table class="pts"><thead><tr><th>Type</th><th>Number</th><th>Name</th><th>Value at scan time</th><th>Units</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}</section>`;
  }).join("") || "<p class='msg'>Nothing matches that filter.</p>";
}

// Same columns as the app's CSV, so the compare tool takes it.
const SAFE_NUM = /^[+-](\\d+\\.?\\d*|\\.\\d+)([eE][+-]?\\d+)?$/;
function cell(v) {
  let s = String(v ?? "");
  const c0 = s[0];
  if (c0 && ("=@\\t\\r".includes(c0) || ((c0 === "-" || c0 === "+") && !SAFE_NUM.test(s)))) s = "'" + s;
  return /[",\\r\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
function csvRows(d) {
  const out = [];
  for (const dev of d.devices || []) {
    out.push([dev.instance, dev.name, dev.ip, "Device", dev.instance, dev.name, "", "", ""]);
    for (const p of dev.points || []) out.push([dev.instance, dev.name, dev.ip, p.typeName, p.instance, p.name, p.value, p.units, p.status]);
  }
  return out;
}
function download(name, rows, header) {
  const text = "\\ufeff" + [header, ...rows].map((r) => r.map(cell).join(",")).join("\\r\\n") + "\\r\\n";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
const HEADER = ["Device ID", "Device Name", "Device IP", "Object Type", "Object Number", "Point Name", "Present Value", "Units", "Status"];
const stamp = (iso) => (iso || "").slice(0, 16).replace(/[-:T]/g, "").replace(/^(\\d{8})(\\d{4})$/, "$1-$2");

$("csv").onclick = () => current && download("easybacnet-shared-" + stamp(current.scannedAt) + ".csv", csvRows(current), HEADER);
$("csvall").onclick = async () => {
  say("Collecting every scan…");
  try {
    const rows = [];
    for (const s of folder.scans) {
      if (!s.meta) continue;
      const d = await scan(s.seq);
      for (const r of csvRows(d)) rows.push([when(d.scannedAt), (d.network || {}).ip || "", ...r]);
    }
    download("easybacnet-shared-all.csv", rows, ["Scan time", "Scanned from", ...HEADER]);
    say("");
  } catch (e) { say(e.message, true); }
};
let filterTimer = 0;
$("filter").oninput = () => { clearTimeout(filterTimer); filterTimer = setTimeout(() => current && drawScan(), 200); };
$("f").onsubmit = (e) => { e.preventDefault(); open($("code").value); };
let fromLink = location.hash.slice(1);
try { fromLink = decodeURIComponent(fromLink); } catch {}
if (fromLink) open(fromLink); else $("code").focus();
</script>
</body>
</html>
"""

ADMIN_BODY = """
<article>
  <h1>Shared codes (admin)</h1>
  <p>This list only shows codes made while the share server is in <b>open</b> mode.
  In private mode (the default) nobody, including us, can read shared scans, so they never appear here.</p>
  <div class="tool">
    <label for="tok">Admin token</label>
    <form class="codebox" id="f"><input id="tok" type="password" autocomplete="off" style="letter-spacing:0;text-transform:none;font-size:1rem"><button type="submit">Show</button></form>
    <p class="msg" id="msg"></p>
  </div>
  <div id="out"></div>
</article>
<script type="module">
const LOCAL = ["localhost", "127.0.0.1"].includes(location.hostname);
// ?api= is for local testing only; on easybacnet.com the server address is fixed.
const API = LOCAL ? (new URLSearchParams(location.search).get("api") || "http://127.0.0.1:8787") : "%(api)s";
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
$("f").onsubmit = async (e) => {
  e.preventDefault();
  const r = await fetch(API + "/api/share/admin/folders", { headers: { Authorization: "Bearer " + $("tok").value }, cache: "no-store" });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { $("msg").textContent = j.error || "Not allowed."; return; }
  $("msg").textContent = "Server mode: " + j.mode + " · " + j.privateCount + " private codes (unreadable) · " + j.open.length + " open codes";
  $("out").innerHTML = '<table class="adm"><tr><th>Code</th><th>Scans</th><th>Last added</th><th>Deletes</th></tr>' +
    j.open.map((f) => `<tr><td><a href="view.html#${esc(f.code)}">${esc(f.code.slice(0,4) + "-" + f.code.slice(4))}</a></td><td>${esc(f.scan_count)}</td><td>${esc(new Date(f.updated).toLocaleString())}</td><td>${esc(new Date(f.expires).toLocaleString())}</td></tr>`).join("") + "</table>";
};
</script>
</body>
</html>
"""

GUIDE_META = dict(
    title="Share BACnet Scan Results With a Code | Easy BACnet",
    question="How do I share BACnet scan results with a code?",
    description="Share an Easy BACnet scan with an 8-character code instead of emailing a file. Encrypted, readable only with the code, deleted after 7 days.",
)

GUIDE_ANSWER = """<p>After a scan in Easy BACnet (phone or PC), choose <strong>Share with code</strong>.
The app gives you an 8-character code like <code>K7QM-4XPR</code>. Send that code to whoever
needs the results. They type it at <a href="../view.html">easybacnet.com/view</a> and see every device and point,
with the values read at the time of the scan. The scan is encrypted with the code, so we can't read it,
and it deletes itself 7 days after the last scan was added.</p>"""

GUIDE_BODY = """
  <h2>Making a code</h2>
  <ol>
    <li>Run a scan in Easy Mode, or open Advanced Mode (Browser Mode on the PC).</li>
    <li>Choose <strong>Share with code</strong>. The app reads the current value of every point, the same as an export.</li>
    <li>Pick <strong>Make a new code</strong>, or add the scan to a code you already made on this phone or PC.</li>
    <li>Read the code out, copy it, or send the link. The link opens the results directly.</li>
  </ol>

  <h2>Adding more scans to the same code</h2>
  <p>A code works like a folder. Keep adding scans to it from the same device, for example one per
  floor or one per visit. Every scan shows its own date, time and the phone or PC's IP address.
  Each time you add a scan, the 7-day clock starts again. A code holds 50 scans on the free version
  and has no limit with Pro. Only the phone or PC that made a code can add scans to it or delete it.</p>

  <h2>Viewing a shared scan</h2>
  <p>Open <a href="../view.html">easybacnet.com/view</a> and type the code. Dashes, spaces and lower case
  are fine. You can filter the points, and download one scan or all of them as a CSV in the same
  layout as the app's export, which the <a href="../bacnet-points-list-compare.html">compare tool</a> also takes.</p>

  <h2>Who can see it</h2>
  <ul>
    <li>The scan is encrypted on the phone or PC before it is uploaded. The key is the code itself.</li>
    <li>Our server never receives the code, so it only holds scrambled data. We can't read it.</li>
    <li>Anyone you give the code to can view the scans until they expire, so treat it like a password.</li>
    <li>A share includes device and point names, values at scan time, and the phone or PC's address on the
    building network (for example 192.168.1.47). It does not include your public internet address or location.</li>
    <li>Scans are deleted automatically 7 days after the last one was added, or straight away with
    <strong>Stop sharing</strong> in the app.</li>
  </ul>

  <h2>Is it free?</h2>
  <p>Yes, for the sender and the viewer. On the phone, the free version shows a small ad on the
  share screen and makes one new code per week. An extra code that week takes a short optional ad.
  Adding scans to a code you already have is always free. Pro has no ads or limits.</p>
"""


def _play(medium):
    return ("https://play.google.com/store/apps/details?id=com.easybacnet.app"
            "&amp;utm_source=easybacnet.com&amp;utm_medium=%s&amp;utm_campaign=view" % medium)


def build(write, page, css, tool_css):
    """Writes the pages; returns (sitemap paths, llms.txt lines)."""
    full_css = css + tool_css + VIEW_CSS
    write(VIEW + ".html", HEAD % dict(title="View a shared scan | Easy BACnet",
                                      desc="Type an Easy BACnet share code to see a scan someone shared with you.",
                                      css=full_css, play=_play("nav"))
          + VIEW_BODY.replace("%(guide)s", GUIDE + ".html").replace("%(api)s", API_PROD).replace("%(play)s", _play("demo")))
    write(ADMIN + ".html", HEAD % dict(title="Shared codes | Easy BACnet", desc="Admin list.",
                                       css=full_css, play=_play("nav"))
          + ADMIN_BODY.replace("%(api)s", API_PROD))
    write(GUIDE + ".html", page(GUIDE, GUIDE_META["title"], GUIDE_META["question"], GUIDE_ANSWER, GUIDE_BODY,
                                [("view", "View a shared scan"),
                                 ("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?")],
                                GUIDE_META["description"], UPDATED, UPDATED))
    return [GUIDE + ".html"], [
        "", "## Shared scans",
        "- View a shared scan (enter an 8-character code): %s/%s" % (BASE_URL, VIEW),
        "- How sharing with a code works: %s/%s" % (BASE_URL, GUIDE),
    ]
