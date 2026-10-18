"""
Inline SVG diagrams for the guides.

A guide drops `{{fig:NAME}}` on its own line in body_html and build_site.py
swaps in figure(NAME). They are inline (not <img>) so they pick up the page
fonts, stay sharp at any size, and their labels are real text that search
engines and screen readers can read.

Drawn on a 560-wide canvas and laid out tall rather than wide so labels stay
legible on a phone. Colours match the site's Field palette.
"""

from html import escape

FG = "#f3f5f6"
MUTED = "#9aa4ad"
BOX = "#1d2227"
BOX2 = "#232a31"
LINE = "#3a434c"
ACC = "#ff9a1f"
OK = "#5cc98a"
BAD = "#ff6b6b"
BLUE = "#6fb3ff"

W = 560

CSS = """
  figure.diagram { margin:2rem 0; background:#171b1f; border:1px solid var(--line);
                   border-radius:14px; padding:1rem 1rem .85rem; }
  figure.diagram svg { display:block; width:100%; height:auto; max-width:560px; margin:0 auto; }
  figure.diagram svg text { font-family:"Manrope",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }
  figure.diagram svg .mono { font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace; }
  figure.diagram figcaption { color:var(--muted); font-size:.86rem; line-height:1.45;
                              margin-top:.75rem; text-align:center; }
  /* Phones: go edge to edge and keep labels readable; wide diagrams swipe. */
  @media (max-width: 520px) {
    figure.diagram { margin:1.75rem -1.25rem; border-radius:0; border-left:0; border-right:0;
                     padding:.85rem 0 .75rem; }
    figure.diagram .dg-scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; padding:0 .75rem; }
    figure.diagram svg { min-width:480px; }
    figure.diagram figcaption { padding:0 1.25rem; }
    figure.diagram figcaption::after { content:" (swipe to see it all)"; opacity:.7; }
  }
"""


# --- tiny drawing kit -------------------------------------------------------

def _a(**kw):
    return "".join(' %s="%s"' % (k.rstrip("_").replace("_", "-"), v) for k, v in kw.items())


def box(x, y, w, h, fill=BOX, stroke=LINE, r=10, dash=None, sw=1.5):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s"%s/>' % (
        x, y, w, h, r, fill, stroke, sw, d)


def text(x, y, s, size=15, fill=FG, anchor="start", weight=500, mono=False, italic=False):
    cls = ' class="mono"' if mono else ""
    st = ' font-style="italic"' if italic else ""
    return '<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" font-weight="%s"%s%s>%s</text>' % (
        x, y, size, fill, anchor, weight, cls, st, escape(s))


def line(x1, y1, x2, y2, stroke=LINE, sw=2, dash=None, arrow=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#ah-%s)"' % arrow if arrow else ""
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s%s/>' % (
        x1, y1, x2, y2, stroke, sw, d, m)


def path(d, stroke=LINE, sw=2, fill="none", dash=None, arrow=None):
    da = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#ah-%s)"' % arrow if arrow else ""
    return '<path d="%s" stroke="%s" stroke-width="%s" fill="%s"%s%s/>' % (d, stroke, sw, fill, da, m)


def node(x, y, w, h, title, sub=None, sub2=None, stroke=LINE, fill=BOX, tsize=15, accent=None):
    """A labelled box: bold title, optional mono subtitle lines."""
    out = [box(x, y, w, h, fill=fill, stroke=stroke)]
    cx = x + w / 2
    lines = [l for l in (sub, sub2) if l]
    ty = y + h / 2 + 5 - len(lines) * 9
    out.append(text(cx, ty, title, size=tsize, anchor="middle", weight=700, fill=accent or FG))
    for i, l in enumerate(lines):
        out.append(text(cx, ty + 19 + i * 17, l, size=12.5, anchor="middle", fill=MUTED, mono=True))
    return "".join(out)


def cross(x, y, s=9, color=BAD):
    return line(x - s, y - s, x + s, y + s, stroke=color, sw=3) + line(x - s, y + s, x + s, y - s, stroke=color, sw=3)


def svg(h, body, label):
    markers = "".join(
        '<marker id="ah-%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (n, c)
        for n, c in (("acc", ACC), ("ok", OK), ("bad", BAD), ("mut", MUTED), ("blue", BLUE), ("fg", FG)))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">'
            '<defs>%s</defs>%s</svg>') % (W, h, escape(label), markers, body)


# --- the diagrams -----------------------------------------------------------

def d_network():
    b = []
    b.append(node(20, 16, 230, 62, "Your phone", "USB-C Ethernet", "10.20.30.50", stroke=ACC))
    b.append(node(310, 16, 230, 62, "JACE / supervisor", "head-end", "10.20.30.5"))
    b.append(line(135, 78, 135, 118))
    b.append(line(425, 78, 425, 118))
    b.append(box(20, 118, 520, 44, fill=BOX2))
    b.append(text(280, 145, "Controls switch  ·  BAS VLAN 10.20.30.0/24", size=14, anchor="middle", weight=700))
    for x in (100, 280, 460):
        b.append(line(x, 162, x, 200))
    b.append(node(20, 200, 160, 70, "RTU-1", "Device 1001", "10.20.30.11"))
    b.append(node(200, 200, 160, 70, "AHU-1", "Device 1002", "10.20.30.12"))
    b.append(node(380, 200, 160, 70, "BACnet router", "network 201", "10.20.30.20", stroke=BLUE))
    b.append(text(20, 300, "BACnet IP — UDP 47808, everything has an IP address", size=13, fill=MUTED))
    # MS/TP trunk
    b.append(line(460, 270, 460, 330, stroke=BLUE, sw=2.5))
    b.append(path("M60,330 H460", stroke=BLUE, sw=2.5, dash="7 5"))
    for i, x in enumerate((60, 200, 340)):
        b.append(line(x + 60, 330, x + 60, 356, stroke=BLUE, sw=2.5))
        b.append(node(x, 356, 120, 66, "VAV-2-%02d" % (i + 1), "MAC %d" % (i + 1), "Dev 2010%d" % (i + 1)))
    b.append(text(480, 380, "…", size=22, fill=MUTED, anchor="middle"))
    b.append(text(20, 450, "BACnet MS/TP — RS-485 twisted pair, 38400 baud, network 201", size=13, fill=BLUE))
    b.append(text(20, 470, "No IP addresses: a scan shows them at the router’s IP plus net 201 / MAC.",
                  size=13, fill=MUTED))
    return svg(486, "".join(b), "BACnet IP controllers on a controls switch, with MS/TP VAV boxes behind a BACnet router")


def d_whois():
    b = []
    cols = [(70, "Your phone", ACC), (215, "RTU-1", LINE), (350, "AHU-1", LINE), (485, "Router", BLUE)]
    for x, t, c in cols:
        b.append(node(x - 62, 14, 124, 40, t, stroke=c, tsize=14))
        b.append(line(x, 54, x, 410, stroke=LINE, sw=1.5, dash="3 5"))
    b.append(text(285, 86, "Who-Is  \u2192  broadcast 10.20.30.255 : 47808", size=13, anchor="middle", fill=ACC, weight=700))
    for x in (215, 350, 485):
        b.append(line(70, 100, x - 4, 100 + (x - 70) * 0.07, stroke=ACC, sw=2, arrow="acc"))
    reps = [(215, 162, "I-Am  1001"), (350, 198, "I-Am  1002"), (485, 234, "I-Am  20101 (via router)")]
    for x, y, t in reps:
        b.append(line(x, y, 74, y, stroke=OK, sw=2, arrow="ok"))
        b.append(text(x - 8, y - 7, t, size=12.5, fill=OK, mono=True, anchor="end"))
    b.append(text(285, 272, "Each I-Am carries: instance, max APDU, segmentation, vendor ID",
                  size=12.5, anchor="middle", fill=MUTED))
    b.append(line(70, 318, 211, 318, stroke=FG, sw=2, arrow="fg"))
    b.append(text(225, 322, "ReadProperty  Object_Name", size=12.5, mono=True))
    b.append(line(215, 358, 74, 358, stroke=FG, sw=2, arrow="fg"))
    b.append(text(225, 362, "Ack  \u201cRTU-1\u201d", size=12.5, mono=True))
    b.append(text(285, 398, "Then the tool asks each device for its name and object list",
                  size=12.5, anchor="middle", fill=MUTED))
    return svg(420, "".join(b), "Sequence: phone broadcasts Who-Is, devices answer I-Am, then the phone reads each device's name")


def d_subnets():
    b = []
    b.append(box(16, 14, 528, 124, fill="none", stroke=OK, dash="6 5"))
    b.append(text(30, 38, "Subnet A  \u00b7  10.20.30.0/24", size=14, fill=OK, weight=700))
    b.append(node(36, 54, 200, 64, "Your phone", "10.20.30.50", stroke=ACC))
    b.append(node(324, 54, 200, 64, "RTU-1", "10.20.30.11"))
    b.append(line(236, 86, 320, 86, stroke=OK, sw=2.5, arrow="ok"))
    b.append(text(278, 78, "scan", size=12, anchor="middle", fill=OK))
    # unicast drawn first so the router box sits on top of it
    b.append(path("M210,118 V280 C210,300 424,296 424,318", stroke=ACC, sw=2.5, arrow="acc"))
    b.append(text(222, 162, "Add by IP: 10.20.40.15", size=12, fill=ACC, mono=True))
    # broadcast blocked
    b.append(path("M80,118 V223 H168", stroke=BAD, sw=2.5, dash="5 4"))
    b.append(cross(176, 223))
    b.append(text(30, 252, "a scan stops here", size=12, fill=BAD))
    b.append(node(186, 196, 200, 54, "IP router / firewall", "between VLANs", stroke=BLUE))
    b.append(box(16, 282, 528, 128, fill="none", stroke=MUTED, dash="6 5"))
    b.append(text(30, 306, "Subnet B  \u00b7  10.20.40.0/24", size=14, fill=MUTED, weight=700))
    b.append(node(324, 322, 200, 64, "AHU-2", "10.20.40.15"))
    b.append(text(36, 348, "Add device by IP", size=14, fill=ACC, weight=700))
    b.append(text(36, 368, "(or a BBMD) gets", size=13, fill=MUTED))
    b.append(text(36, 386, "you across", size=13, fill=MUTED))
    return svg(424, "".join(b), "A broadcast scan stops at the router between subnets; a directed unicast request crosses it")


def d_bbmd():
    b = []
    b.append(box(16, 14, 528, 132, fill="none", stroke=MUTED, dash="6 5"))
    b.append(text(530, 38, "Subnet A  \u00b7  10.20.30.0/24", size=14, fill=MUTED, weight=700, anchor="end"))
    b.append(node(36, 54, 220, 70, "BBMD A", "in the JACE", "10.20.30.5", stroke=BLUE))
    b.append(node(304, 54, 220, 70, "RTU-1", "10.20.30.11"))
    b.append(box(16, 284, 528, 132, fill="none", stroke=MUTED, dash="6 5"))
    b.append(text(530, 308, "Subnet B  \u00b7  10.20.40.0/24", size=14, fill=MUTED, weight=700, anchor="end"))
    b.append(node(36, 324, 220, 70, "BBMD B", "BACnet router", "10.20.40.1", stroke=BLUE))
    b.append(node(304, 324, 220, 70, "AHU-2", "10.20.40.15"))
    b.append(line(80, 128, 80, 318, stroke=BLUE, sw=2.5, arrow="blue"))
    b.append(line(116, 318, 116, 128, stroke=BLUE, sw=2.5, arrow="blue"))
    b.append(text(132, 196, "Forwarded-NPDU", size=12.5, fill=BLUE, mono=True))
    b.append(text(132, 214, "unicast UDP 47808", size=12, fill=MUTED))
    b.append(text(132, 230, "each BBMD lists the", size=12, fill=MUTED))
    b.append(text(132, 246, "other in its BDT", size=12, fill=MUTED))
    b.append(line(256, 359, 300, 359, stroke=OK, sw=2.5, arrow="ok"))
    b.append(text(278, 350, "local", size=11, anchor="middle", fill=OK))
    b.append(node(380, 168, 160, 60, "Foreign device", "phone / VPN laptop", stroke=ACC))
    b.append(path("M380,186 C330,176 300,150 260,118", stroke=ACC, sw=2.5, arrow="acc"))
    b.append(text(540, 250, "1. Register-Foreign-Device", size=11.5, fill=ACC, mono=True, anchor="end"))
    b.append(text(540, 266, "2. Distribute-Broadcast", size=11.5, fill=ACC, mono=True, anchor="end"))
    return svg(430, "".join(b), "Two BBMDs forward broadcasts between subnets; a foreign device registers with one BBMD")


def d_objects():
    b = []
    b.append(node(20, 16, 230, 64, "Device 1001", "object type 8", "\"RTU-1\"", stroke=ACC))
    b.append(text(270, 44, "The controller is itself an object;", size=13, fill=MUTED))
    b.append(text(270, 62, "its Object_List names all the others.", size=13, fill=MUTED))
    objs = [("AI 1", "SA-T"), ("AI 2", "RA-T"), ("BO 1", "SF-C"), ("MSV 1", "HVAC-MODE"), ("AV 3", "OCC-CLG-SP")]
    b.append(line(44, 80, 44, 96 + 4 * 40 + 20))
    for i, (o, n) in enumerate(objs):
        y = 96 + i * 40
        hi = o == "AV 3"
        b.append(line(44, y + 18, 64, y + 18))
        b.append(box(64, y, 186, 34, stroke=ACC if hi else LINE, fill=BOX2 if hi else BOX, r=8))
        b.append(text(76, y + 22, o, size=13, mono=True, fill=ACC if hi else FG, weight=600))
        b.append(text(140, y + 22, n, size=13, mono=True, fill=FG if hi else MUTED))
    # property table for AV 3
    b.append(path("M250,277 C270,277 270,120 290,120", stroke=ACC, sw=2))
    props = [("Object_Name", "OCC-CLG-SP"), ("Present_Value", "74.0"), ("Units", "degrees-Fahrenheit"),
             ("Status_Flags", "normal"), ("Priority_Array", "16 slots"), ("Relinquish_Default", "74.0"),
             ("Description", "Occupied cooling SP")]
    b.append(box(290, 96, 254, 26 + len(props) * 30, stroke=ACC))
    b.append(text(304, 116, "Properties of AV 3", size=13, fill=ACC, weight=700))
    for i, (k, v) in enumerate(props):
        y = 144 + i * 30
        b.append(text(304, y, k, size=11.5, fill=MUTED, mono=True))
        b.append(text(530, y, v, size=12.5, anchor="end", weight=600))
    return svg(338, "".join(b), "A BACnet device object lists its point objects; each object has properties like Present_Value and Units")


PRIO_NAMES = {1: "Manual life safety", 2: "Automatic life safety", 5: "Critical equipment",
              6: "Minimum on/off", 8: "Manual operator"}


def _ladder(x, y, slots, rowh=22, w=250, names=True, active=None):
    out = []
    for i in range(1, 17):
        yy = y + (i - 1) * rowh
        val = slots.get(i)
        is_act = i == active
        fill = "#3a2a12" if is_act else (BOX2 if val else BOX)
        stroke = ACC if is_act else LINE
        out.append(box(x, yy, w, rowh - 3, fill=fill, stroke=stroke, r=4, sw=1.2))
        out.append(text(x + 10, yy + rowh - 8, str(i), size=11.5, mono=True, fill=MUTED if not val else FG))
        if val:
            out.append(text(x + 36, yy + rowh - 8, val, size=12, fill=ACC if is_act else FG, weight=700))
        else:
            label = PRIO_NAMES.get(i, "") if names else ""
            out.append(text(x + 36, yy + rowh - 8, (label + "  ·  " if label else "") + "NULL",
                            size=11, fill="#6b757e", italic=not label))
    return "".join(out)


def d_priority():
    b = []
    b.append(text(20, 26, "Priority_Array  (1 = highest)", size=14, weight=700))
    b.append(_ladder(20, 40, {8: "55.0 °F  — operator override", 16: "72.0 °F  — control program"},
                     w=300, active=8))
    b.append(box(20, 40 + 16 * 22 + 14, 300, 34, fill=BOX, stroke=MUTED, dash="4 4", r=6))
    b.append(text(32, 40 + 16 * 22 + 36, "Relinquish_Default  72.0 °F", size=12.5, fill=MUTED, mono=True))
    # PV callout
    yy = 40 + 7 * 22 + 9
    b.append(line(322, yy, 360, yy, stroke=ACC, sw=2.5))
    b.append(box(360, yy - 40, 184, 80, fill="#2a2116", stroke=ACC))
    b.append(text(452, yy - 14, "Present_Value", size=12.5, anchor="middle", fill=MUTED, mono=True))
    b.append(text(452, yy + 14, "55.0 °F", size=24, anchor="middle", fill=ACC, weight=800))
    b.append(text(452, yy + 32, "", size=10))
    b.append(text(360, yy + 70, "The lowest-numbered slot", size=12.5, fill=FG))
    b.append(text(360, yy + 88, "that isn’t NULL wins.", size=12.5, fill=FG))
    b.append(text(360, yy + 116, "Slot 16 is still there,", size=12.5, fill=MUTED))
    b.append(text(360, yy + 134, "just outranked.", size=12.5, fill=MUTED))
    b.append(text(360, 40 + 16 * 22 + 36, "Used only when all", size=12, fill=MUTED))
    b.append(text(360, 40 + 16 * 22 + 52, "16 slots are NULL", size=12, fill=MUTED))
    return svg(40 + 16 * 22 + 66, "".join(b), "A 16-slot priority array: slot 8 at 55 F outranks slot 16 at 72 F, so Present_Value is 55 F")


def d_release():
    b = []
    rh = 17
    for x, title, slots, act, pv in ((16, "Before", {8: "55.0  operator", 16: "72.0  program"}, 8, "55.0"),
                                     (300, "After", {16: "72.0  program"}, 16, "72.0")):
        b.append(text(x, 24, title, size=15, weight=800, fill=ACC if title == "After" else FG))
        b.append(_ladder(x, 36, slots, rowh=rh, w=244, names=False, active=act))
        b.append(text(x, 36 + 16 * rh + 24, "Present_Value = %s °F" % pv, size=13.5, weight=700,
                      fill=ACC, mono=True))
    b.append(line(262, 36 + 7 * rh + 8, 296, 36 + 7 * rh + 8, stroke=ACC, sw=2.5, arrow="acc"))
    b.append(text(280, 36 + 7 * rh - 4, "", size=10))
    b.append(box(16, 36 + 16 * rh + 40, 528, 46, fill=BOX2, stroke=ACC))
    b.append(text(280, 36 + 16 * rh + 68, "WriteProperty  Present_Value = NULL  @ priority 8", size=13,
                  anchor="middle", fill=ACC, mono=True, weight=600))
    return svg(36 + 16 * rh + 98, "".join(b), "Writing NULL at priority 8 empties that slot so control falls to the program at 16")


def d_objectid():
    b = []
    b.append(text(20, 26, "Object Identifier — 32 bits", size=14, weight=700))
    x0, wbit = 20, 520 / 32
    b.append(box(x0, 40, 10 * wbit, 40, fill="#2a2116", stroke=ACC, r=6))
    b.append(box(x0 + 10 * wbit, 40, 22 * wbit, 40, fill=BOX2, stroke=BLUE, r=6))
    b.append(text(x0 + 5 * wbit, 66, "type · 10 bits", size=13, anchor="middle", fill=ACC, weight=700))
    b.append(text(x0 + 21 * wbit, 66, "instance · 22 bits", size=13, anchor="middle", fill=BLUE, weight=700))
    b.append(text(x0, 100, "0 – 1023", size=12, fill=MUTED, mono=True))
    b.append(text(540, 100, "0 – 4,194,303", size=12, fill=MUTED, mono=True, anchor="end"))
    ex = [("Analog Value 3", "2", "3", "0x00800003", "8388611"),
          ("Device 1001", "8", "1001", "0x020003E9", "33555433")]
    for i, (name, t, inst, hx, dec) in enumerate(ex):
        y = 130 + i * 92
        b.append(box(20, y, 520, 76, fill=BOX))
        b.append(text(36, y + 26, name, size=14, weight=700))
        b.append(text(36, y + 52, "type %s  × 4,194,304  +  %s" % (t, inst), size=12.5, mono=True, fill=MUTED))
        b.append(text(524, y + 26, hx, size=14, mono=True, anchor="end", fill=ACC, weight=600))
        b.append(text(524, y + 52, "= %s" % dec, size=12.5, mono=True, anchor="end", fill=FG))
    b.append(text(20, 330, "4,194,303 (all 22 bits set) is reserved as the “any device” wildcard.",
                  size=12.5, fill=MUTED))
    return svg(344, "".join(b), "A BACnet Object Identifier packs a 10-bit object type and a 22-bit instance number into 32 bits")


def d_statusflags():
    b = []
    b.append(text(20, 26, "Status_Flags  {IN_ALARM, FAULT, OVERRIDDEN, OUT_OF_SERVICE}", size=13.5, weight=700, mono=True))
    flags = [("IN_ALARM", BAD, "Value is outside its alarm limits", "Check the equipment, then the limits"),
             ("FAULT", BAD, "Sensor or input is unreliable", "Open/shorted wire, failed sensor"),
             ("OVERRIDDEN", ACC, "Overridden locally at the device", "HOA switch or local panel, not BACnet"),
             ("OUT_OF_SERVICE", BLUE, "Disconnected from its hardware", "Value is whatever was written; set it back")]
    for i, (f, c, what, act) in enumerate(flags):
        y = 44 + i * 78
        b.append(box(20, y, 520, 66, fill=BOX, stroke=c))
        b.append(box(20, y, 8, 66, fill=c, stroke=c, r=3))
        b.append(text(44, y + 26, f, size=14, mono=True, weight=700, fill=c))
        b.append(text(44, y + 50, what, size=13))
        b.append(text(528, y + 26, "bit %d" % i, size=12, mono=True, anchor="end", fill=MUTED))
        b.append(text(528, y + 50, act, size=12, anchor="end", fill=MUTED))
    b.append(text(20, 44 + 4 * 78 + 16, "All four false = “Normal”. A commanded priority array does NOT set OVERRIDDEN.",
                  size=12.5, fill=MUTED))
    return svg(44 + 4 * 78 + 30, "".join(b), "The four BACnet status flags and what each one means")


def d_outofservice():
    b = []
    for i, (oos, pv, note, col) in enumerate(((False, "72.4 °F", "Sensor drives the value. Writes are refused.", OK),
                                              (True, "65.0 °F", "Value is whatever you write. Sensor ignored.", BLUE))):
        y = 20 + i * 170
        b.append(text(20, y + 14, "Out_Of_Service = %s" % ("TRUE" if oos else "FALSE"), size=14, mono=True,
                      weight=700, fill=col))
        b.append(node(20, y + 30, 130, 60, "Sensor", "10k thermistor"))
        # switch
        sx = 190
        b.append(line(150, y + 60, sx, y + 60, stroke=FG, sw=2.5))
        b.append('<circle cx="%d" cy="%d" r="4" fill="%s"/>' % (sx, y + 60, FG))
        b.append('<circle cx="%d" cy="%d" r="4" fill="%s"/>' % (sx + 40, y + 60, FG))
        if oos:
            b.append(line(sx, y + 60, sx + 34, y + 38, stroke=BLUE, sw=2.5))
        else:
            b.append(line(sx, y + 60, sx + 40, y + 60, stroke=OK, sw=2.5))
        b.append(line(sx + 40, y + 60, 270, y + 60, stroke=FG, sw=2.5, arrow="fg"))
        b.append(node(272, y + 30, 268, 60, "AI 1  SA-T", "Present_Value  " + pv, stroke=col))
        if oos:
            b.append(path("M406,%d L406,%d" % (y + 128, y + 94), stroke=ACC, sw=2.5, arrow="acc"))
            b.append(text(416, y + 124, "your write", size=12, fill=ACC))
        b.append(text(20, y + 118, note, size=13, fill=MUTED))
    b.append(text(20, 352, "Set it back to FALSE when you’re done, or the point stays frozen.", size=13, fill=ACC,
                  weight=600))
    return svg(366, "".join(b), "Out_Of_Service disconnects an input from its sensor so its Present_Value can be written")


def _diamond(cx, cy, w, h, label1, label2=None):
    pts = "%s,%s %s,%s %s,%s %s,%s" % (cx, cy - h / 2, cx + w / 2, cy, cx, cy + h / 2, cx - w / 2, cy)
    out = '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.5"/>' % (pts, BOX2, ACC)
    if label2:
        out += text(cx, cy - 3, label1, size=12.5, anchor="middle", weight=700)
        out += text(cx, cy + 14, label2, size=12.5, anchor="middle", weight=700)
    else:
        out += text(cx, cy + 5, label1, size=12.5, anchor="middle", weight=700)
    return out


def d_scanflow():
    b = []
    b.append(node(130, 10, 220, 40, "Scan found nothing", stroke=BAD, tsize=14))
    qs = [("On the same network", "as the controls?", "No", "Join the controls Wi-Fi,", "or plug into its switch"),
          ("BACnet IP turned", "on in the device?", "No", "Turn it on in the", "device setup (port 47808)"),
          ("Does the device", "answer a ping?", "No", "Wrong network, or the", "device is off / unplugged"),
          ("Device on a", "different subnet?", "Yes", "Add device by IP,", "or enter the site BBMD")]
    y = 112
    b.append(line(240, 50, 240, y - 44, stroke=MUTED, arrow="mut"))
    for i, (q1, q2, take, a1, a2) in enumerate(qs):
        col = BAD if i < 3 else OK
        b.append(_diamond(240, y, 230, 84, q1, q2))
        b.append(line(355, y, 368, y, stroke=col, sw=2, arrow="ok" if i >= 3 else "bad"))
        b.append(text(361, y - 10, take, size=11.5, anchor="middle", fill=col, weight=700))
        b.append(box(370, y - 32, 180, 64, fill=BOX, stroke=col, r=8))
        b.append(text(460, y - 6, a1, size=11.5, anchor="middle"))
        b.append(text(460, y + 12, a2, size=11.5, anchor="middle", fill=MUTED))
        if i < len(qs) - 1:
            b.append(line(240, y + 42, 240, y + 70, stroke=MUTED, arrow="mut"))
            b.append(text(250, y + 60, "Yes" if take == "No" else "No", size=11.5, fill=MUTED, weight=700))
        y += 112
    b.append(text(280, y - 40, "Still nothing? Call the controls contractor with your phone’s IP address.",
                  size=12.5, anchor="middle", fill=MUTED))
    return svg(y - 24, "".join(b), "Troubleshooting flow when a BACnet IP scan finds no devices")


def d_whotocall():
    b = []
    rows = [("IT / network team", BLUE, "The network side",
             ["No IP address, or the wrong one", "Which VLAN the controls are on", "Firewall or port 47808 blocked",
              "Guest Wi-Fi with client isolation"]),
            ("Controls contractor", ACC, "The BACnet side",
             ["Devices found but values look wrong", "Stuck overrides, schedules, sequences",
              "Device IDs, BBMD, points list", "A controller that dropped offline"]),
            ("HVAC mechanical", OK, "The equipment itself",
             ["Compressor, fan belt, refrigerant", "Tripped breaker or safety",
              "Valve or damper physically stuck", "Noise, leaks, ice, no heat at all"])]
    y = 14
    for name, col, sub, items in rows:
        b.append(box(16, y, 528, 150, stroke=col))
        b.append(box(16, y, 8, 150, fill=col, stroke=col, r=3))
        b.append(text(40, y + 30, name, size=16, weight=800, fill=col))
        b.append(text(528, y + 30, sub, size=12.5, anchor="end", fill=MUTED))
        for i, it in enumerate(items):
            b.append(text(44, y + 60 + i * 24, "•  " + it, size=13.5))
        y += 164
    return svg(y, "".join(b), "Who to call: IT for the network, the controls contractor for BACnet, HVAC mechanical for the equipment")


def d_bacnetvsmodbus():
    b = []
    b.append(box(16, 14, 528, 186, stroke=ACC))
    b.append(text(32, 42, "BACnet  ·  Analog Input 1", size=15, weight=800, fill=ACC))
    for i, (k, v) in enumerate((("Object_Name", "RTU-3 SA-T"), ("Present_Value", "55.2"),
                                ("Units", "degrees-Fahrenheit"), ("Status_Flags", "normal"),
                                ("Description", "Supply air temperature"))):
        b.append(text(36, 72 + i * 25, k, size=12.5, mono=True, fill=MUTED))
        b.append(text(526, 72 + i * 25, v, size=13.5, anchor="end", weight=600))
    b.append(text(280, 224, "The device describes its own data.", size=13, anchor="middle", fill=ACC, weight=600))
    b.append(box(16, 244, 528, 132, stroke=MUTED))
    b.append(text(32, 272, "Modbus  ·  holding register 40101", size=15, weight=800, fill=MUTED))
    b.append(text(36, 304, "raw value", size=12.5, mono=True, fill=MUTED))
    b.append(text(526, 304, "0x0228  =  552", size=15, anchor="end", mono=True, weight=700))
    b.append(text(36, 332, "name? units? scale?", size=12.5, mono=True, fill=MUTED))
    b.append(text(526, 332, "?", size=15, anchor="end", weight=700, fill=BAD))
    b.append(text(36, 358, "Only the vendor’s register map says it’s supply air in tenths of °F.",
                  size=12.5, fill=FG))
    return svg(390, "".join(b), "A self-describing BACnet point compared with a bare Modbus register")


def d_multistate():
    b = []
    b.append(text(20, 26, "MSV 1  HVAC-MODE", size=14, weight=700, mono=True))
    states = ["Off", "Heat", "Cool", "Auto"]
    for i, s in enumerate(states):
        y = 44 + i * 50
        act = i == 2
        b.append(box(20, y, 120, 40, fill="#2a2116" if act else BOX, stroke=ACC if act else LINE, r=8))
        b.append(text(80, y + 26, str(i + 1), size=16, anchor="middle", mono=True, weight=700, fill=ACC if act else FG))
        b.append(line(140, y + 20, 226, y + 20, stroke=ACC if act else LINE, sw=2, arrow="acc" if act else None))
        b.append(box(230, y, 150, 40, fill="#2a2116" if act else BOX, stroke=ACC if act else LINE, r=8))
        b.append(text(305, y + 26, s, size=15, anchor="middle", weight=700, fill=ACC if act else FG))
    b.append(text(80, 260, "Present_Value", size=12, anchor="middle", mono=True, fill=MUTED))
    b.append(text(305, 260, "State_Text", size=12, anchor="middle", mono=True, fill=MUTED))
    b.append(text(400, 92, "Number_Of_States = 4", size=12, mono=True, fill=MUTED))
    b.append(text(400, 154, "Present_Value 3", size=13, fill=ACC, weight=700))
    b.append(text(400, 172, "means “Cool”", size=13, fill=ACC, weight=700))
    b.append(text(400, 216, "Counting starts at 1.", size=12.5, fill=MUTED))
    b.append(text(400, 234, "0 is never valid.", size=12.5, fill=MUTED))
    return svg(274, "".join(b), "A multi-state value: Present_Value numbers map to names through State_Text")


def d_packet():
    b = []
    layers = [("IP", "10.20.30.50  \u2192  10.20.30.255", MUTED),
              ("UDP", "port 47808  =  0xBAC0", ACC),
              ("BVLC", "81 0B 00 0C   Original-Broadcast-NPDU", BLUE),
              ("NPDU", "01 20 FF FF 00 FF   to all networks", BLUE),
              ("APDU", "10 08   Unconfirmed request: Who-Is", OK)]
    top, H = 14, 280
    for i, (name, detail, col) in enumerate(layers):
        x = 16 + i * 14
        y = top + i * 50
        h = H - i * 50 - i * 12
        b.append(box(x, y, 528 - i * 28, h, fill=BOX if i % 2 == 0 else BOX2, stroke=col))
        b.append(text(x + 14, y + 28, name, size=14, weight=800, fill=col))
        b.append(text(x + 74, y + 28, detail, size=12.5, mono=True, fill=FG))
    b.append(text(280, top + H + 26, "A complete Who-Is is 12 bytes of BACnet after the UDP header.",
                  size=12.5, anchor="middle", fill=MUTED))
    return svg(top + H + 40, "".join(b), "Layers of a BACnet IP Who-Is packet: IP, UDP 47808, BVLC, NPDU, APDU")


def d_writeflow():
    b = []
    steps = [("Read and note", "Present_Value, who holds it (Commanded At), the fallback"),
             ("Write at priority 8", "One point, one value. Tell whoever runs the system."),
             ("Verify", "Re-read the point and look at the equipment itself"),
             ("Release", "Write NULL at the same priority (Release to Auto)"),
             ("Verify it went back", "Commanded At empty or back to the program’s slot")]
    for i, (t, d) in enumerate(steps):
        y = 16 + i * 74
        col = ACC if i in (1, 3) else FG
        if i < len(steps) - 1:
            b.append(line(40, y + 40, 40, y + 74, stroke=LINE, sw=2.5))
        b.append('<circle cx="40" cy="%d" r="20" fill="%s" stroke="%s" stroke-width="2"/>' % (y + 20, BOX2, col))
        b.append(text(40, y + 26, str(i + 1), size=16, anchor="middle", weight=800, fill=col))
        b.append(text(76, y + 16, t, size=15, weight=800, fill=col))
        b.append(text(76, y + 38, d, size=13, fill=MUTED))
    return svg(16 + 5 * 74 - 8, "".join(b), "Safe write cycle: read, write at priority 8, verify, release, verify")


DIAGRAMS = {
    "network": (d_network, "BACnet IP devices sit on the controls network. MS/TP devices hang off a router and show up at the router’s IP with a network number and MAC."),
    "whois": (d_whois, "Discovery: one broadcast Who-Is, one I-Am back from each device, then a read for each device’s name."),
    "subnets": (d_subnets, "A scan stays inside your subnet. Reaching another one needs Add device by IP or a BBMD."),
    "bbmd": (d_bbmd, "BBMDs pass broadcasts between subnets. A phone or laptop elsewhere registers as a foreign device to join in."),
    "objects": (d_objects, "Device → objects → properties. A points list is one row per object."),
    "priority": (d_priority, "Sixteen slots, one winner: the lowest-numbered slot that holds a value."),
    "release": (d_release, "Releasing empties your slot; it doesn’t write a value. Control drops to whatever is next."),
    "objectid": (d_objectid, "Type and instance packed into one 32-bit number. The decoder tool does this math for you."),
    "statusflags": (d_statusflags, "Four true/false flags on every point. Anything but all-false deserves a look."),
    "outofservice": (d_outofservice, "Out_Of_Service is how commissioning techs fake a sensor reading, and how points get left frozen."),
    "scanflow": (d_scanflow, "Work down the list; most empty scans stop at the first question."),
    "whotocall": (d_whotocall, "Match the symptom to the trade before you pick up the phone."),
    "bacnetvsmodbus": (d_bacnetvsmodbus, "The same temperature, as each protocol hands it to you."),
    "multistate": (d_multistate, "Multi-state points are numbers; State_Text gives them names."),
    "packet": (d_packet, "What one Who-Is looks like on the wire."),
    "writeflow": (d_writeflow, "The whole job, start to finish. Steps 4 and 5 are the ones people skip."),
}


def figure(name):
    fn, cap = DIAGRAMS[name]
    return '<figure class="diagram"><div class="dg-scroll">%s</div><figcaption>%s</figcaption></figure>' % (
        fn(), escape(cap))
