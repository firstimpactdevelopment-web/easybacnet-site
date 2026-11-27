"""Printable PDF guides (hub page + a download box on the matching guides).

The PDFs are built from docs/customer_guide in the app repo and copied to downloads/.
Only the Android guides are public: the Windows PC app has not been announced on the
site (privacy-desktop.html is noindexed for the same reason), so PC PDFs stay off the
site until it is. Set PC_PUBLIC = True and copy the PC PDFs into downloads/ to publish them.
"""
import html as _h
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PC_PUBLIC = True
HUB = "printable-guides"
UPDATED = "2026-11-26"

GUIDES = [
    ("points", "Export a BACnet points list",
     "Scan the building network and email the points list as an Excel file, then read and (optionally) write points.",
     "Easy-BACnet-Mobile-Points-List-Guide.pdf", "Easy-BACnet-PC-Points-List-Guide.pdf"),
    ("remotes", "Build a custom remote",
     "One control screen for one device: readouts, setpoints, switches and release buttons.",
     "Easy-BACnet-Mobile-Custom-Remotes-Guide.pdf", "Easy-BACnet-PC-Custom-Remotes-Guide.pdf"),
    ("panels", "Build a control panel",
     "One control screen that drives up to 32 devices.",
     "Easy-BACnet-Mobile-Control-Panels-Guide.pdf", "Easy-BACnet-PC-Control-Panels-Guide.pdf"),
    ("emulator", "Check what a BMS is writing with the Device Emulator",
     "Make the phone answer as a BACnet device and see every command that arrives.",
     "Easy-BACnet-Mobile-Device-Emulator-Guide.pdf", "Easy-BACnet-PC-Device-Emulator-Guide.pdf"),
    ("networks", "Find devices on another network",
     "Add a device by IP address, use a BBMD, or add an object by number when a normal scan misses it.",
     "Easy-BACnet-Mobile-Other-Networks-Guide.pdf", "Easy-BACnet-PC-Other-Networks-Guide.pdf"),
]
BY_KEY = {g[0]: g for g in GUIDES}

# guide slug -> PDF keys shown in the download box on that page
SLUG_MAP = {
    "guides/how-to-use-easy-bacnet": ["points"],
    "guides/export-bacnet-points-to-csv": ["points"],
    "guides/how-to-find-your-bacnet-points-list": ["points"],
    "guides/bacnet-scanner-app-android": ["points"],
    "guides/read-bacnet-values-from-phone": ["points"],
    "guides/how-to-write-to-a-bacnet-point": ["points"],
    "guides/is-it-safe-to-write-to-bacnet": ["points"],
    "guides/how-to-build-a-custom-remote": ["remotes"],
    "guides/how-to-build-a-control-panel": ["panels"],
    "guides/bacnet-device-emulator-check-writes": ["emulator"],
    "guides/test-bacnet-device-without-bms": ["emulator"],
    "guides/troubleshoot-bacnet-with-remotes-and-emulator": ["remotes", "emulator"],
    "guides/why-cant-i-find-my-bacnet-devices": ["networks"],
    "guides/cant-find-what-im-looking-for": ["networks"],
    "guides/subnets": ["networks"],
}


def _exists(name):
    return os.path.exists(os.path.join(HERE, "downloads", name))


def _links(key):
    g = BY_KEY[key]
    out = []
    if _exists(g[3]):
        out.append('<a href="/downloads/%s">Android guide (PDF)</a>' % g[3])
    if PC_PUBLIC and _exists(g[4]):
        out.append('<a href="/downloads/%s">Windows guide (PDF)</a>' % g[4])
    return out


def box(slug):
    """Download note placed before the app call-to-action on a matching guide."""
    keys = [k for k in SLUG_MAP.get(slug, []) if _links(k)]
    if not keys:
        return ""
    rows = "".join('<li><strong>%s</strong> &mdash; %s</li>' % (_h.escape(BY_KEY[k][1]), " &middot; ".join(_links(k)))
                   for k in keys)
    return ('\n  <aside class="more" style="margin:1.4rem 0"><h2>Printable PDF guide</h2>'
            '<p>A short, illustrated version of this guide you can print or send to a colleague.</p>'
            '<ul>%s</ul><p><a href="/%s">All printable guides</a></p></aside>\n' % (rows, HUB))


def hub_meta():
    return dict(
        slug=HUB,
        title="Printable Easy BACnet guides (PDF)",
        question="Printable Easy BACnet guides (PDF)",
        description="Illustrated PDF guides for Easy BACnet: export a BACnet points list, build remotes and control panels, use the device emulator and find devices on another network.",
        answer_html=("Illustrated, short PDF guides for people who do not normally work with HVAC controls. "
                     "Each one opens with a three-step quick version, then a basic walkthrough. Free to download, print or forward."),
    )


def hub_body():
    items = []
    for k, title, desc, *_ in GUIDES:
        links = _links(k)
        if not links:
            continue
        items.append('<li><strong>%s</strong><br><span class="muted">%s</span><br>%s</li>'
                     % (_h.escape(title), _h.escape(desc), " &middot; ".join(links)))
    return ('<h2>The guides</h2>\n<ul class="linklist">\n%s\n</ul>\n'
            '<h2>Looking for the points list for your unit?</h2>\n'
            '<p>Browse <a href="/bacnet-points-lists/index.html">BACnet points lists by manufacturer and model</a> '
            'to see what each point means before you connect.</p>\n' % "\n".join(items))


def build(write, page):
    m = hub_meta()
    write(HUB + ".html", page(m["slug"], m["title"], m["question"], m["answer_html"], hub_body(),
                              [("guides/how-to-use-easy-bacnet", "How do I scan for my BACnet points list?"),
                               ("guides/bacnet-glossary", "BACnet glossary")],
                              m["description"], UPDATED, UPDATED))
    return [HUB + ".html"], ["", "## Printable guides", "- Printable PDF guides: %s/%s" % ("https://easybacnet.com", HUB)]
