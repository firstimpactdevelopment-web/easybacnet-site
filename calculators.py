"""BACnet instance-number calculators: /bacnet-instance-calculators/.

Many VRF gateways, boiler cascades and zone gateways number their BACnet objects with a
formula: the unit's address is built into the instance number (Fujitsu TTrruu, Daikin
N x 256 + member, Mitsubishi MMGGPP...), or into the device instance of a virtual
per-unit device (Samsung, Lennox, Sinclair...). The points list only prints unit 1, so
techs end up doing the arithmetic by hand for 40-200 units. Each page here does it.

One page per brand when the whole brand uses one scheme, one page per hardware model
when the scheme belongs to that hardware. Every formula and every point comes from a
verified points_data/ file (whose notes quote the manufacturer's manual); this module
only adds the arithmetic. Object names are shown exactly as printed (never generated).

Built from build_site.main(); returns (sitemap_paths, llms_lines) like points_library.
"""
import json
import os
import shutil

import points_library as PL

ROOT = "bacnet-instance-calculators"
PUBLISHED = "2026-11-05"
HERE = PL.HERE
esc = PL.esc


def load(rel):
    with open(os.path.join(HERE, "points_data", rel + ".json"), encoding="utf-8") as f:
        d = json.load(f)
    d["_rel"] = rel
    return d


def lib_href(rel):
    return "/" + PL.ROOT + "/" + rel + ".html"


# ---------------------------------------------------------------------------
# Group builders. An "object" group is a block of objects whose instance moves with
# the unit address: off(p) is the part of the printed instance that stays fixed and
# enc(o, v) builds the instance for the unit values v. A "device" group is a virtual
# BACnet device per unit: dev(v) is its device instance, the objects inside are fixed.
# Each formula exists twice: Python (static example tables) and JavaScript (the live
# calculator). tools/check_calculators.py compares the two.
# ---------------------------------------------------------------------------

def G(gid, label, uses, match, off, enc, js_enc, js_dec, note=None, js_skip=None, js_info=None):
    return dict(kind="object", id=gid, label=label, uses=uses, match=match, off=off, enc=enc,
                js={"enc": js_enc, "dec": js_dec, "skip": js_skip, "info": js_info}, note=note)


def D(gid, label, uses, match, dev, js_dev, js_ddec, note=None):
    return dict(kind="device", id=gid, label=label, uses=uses, match=match, off=lambda p: p["instance"],
                dev=dev, js={"dev": js_dev, "ddec": js_ddec}, note=note)


def V(vid, label, rel, groups):
    return dict(id=vid, label=label, rel=rel, groups=groups)


def I(k, label, lo, hi, default, hint="", hexin=False):
    return dict(k=k, label=label, min=lo, max=hi, default=default, hint=hint, hex=hexin)


def typ(*types):
    return lambda p: p["type"] in types


def between(lo, hi, types=None):
    return lambda p: lo <= p["instance"] < hi and (types is None or p["type"] in types)


def desc_prefix(prefix):
    return lambda p: (p.get("description") or "").startswith(prefix)


ALL = lambda p: p["type"] != "DEV"

CALCS = []

# ---------------------------------------------------------------------------
# Fujitsu UTY-VBGX (the Fujitsu Airstage VRF BACnet gateway): TTrruu
# ---------------------------------------------------------------------------
CALCS.append(dict(
    slug="fujitsu", brand="Fujitsu", hw="UTY-VBGX VRF gateway", kind="object",
    title="Fujitsu BACnet Instance Calculator (UTY-VBGX VRF)",
    desc="Work out every Fujitsu UTY-VBGX BACnet instance from the refrigerant system and indoor unit "
         "address. System 02, unit 05 setpoint = AO 100205. Free calculator.",
    lede="Fujitsu's UTY-VBGX gateway puts the refrigerant system and unit address inside every instance "
         "number. Enter the addresses and get the full object list for that unit, or paste an instance to "
         "see which unit it belongs to.",
    answer="On a Fujitsu UTY-VBGX every indoor unit object is a 6-digit number <span class=\"mono\">TT rr uu</span>: "
           "a 2-digit point code (10-17), the refrigerant system address (00-99) and the indoor unit address "
           "(00-63). Outdoor unit objects use point codes 30-33 with the outdoor unit address (0-3) at the end. "
           "So the setpoint command for refrigerant system 2, indoor unit 5 is <strong>AO 100205</strong>.",
    formula_line="instance = point code x 10000 + refrigerant system x 100 + unit address",
    formula=[("TT", "Point code: which object of the unit (10-17 indoor, 30-33 outdoor)", "10-17, 30-33"),
             ("rr", "Refrigerant system address", "00-99"),
             ("uu", "Indoor unit address (outdoor unit address for OU objects)", "00-63 (OU 0-3)")],
    where="The addresses are the ones the Fujitsu configuration tool shows for each unit after it scans the "
          "VRF network. Gateway-wide and batch objects (all units at once) sit at fixed low instances 0-2.",
    example=dict(rr=2, uu=5, ou=0), example_text="refrigerant system 02, indoor unit 05",
    inputs=[I("rr", "Refrigerant system address", 0, 99, 1),
            I("uu", "Indoor unit address", 0, 63, 1),
            I("ou", "Outdoor unit address", 0, 3, 0)],
    primary="uu",
    variants=[V("v", "UTY-VBGX", "fujitsu/uty-vbgx", [
        G("iu", "Indoor unit objects", ["rr", "uu"], between(100000, 300000), lambda p: p["instance"] // 10000,
          lambda o, v: o * 10000 + v["rr"] * 100 + v["uu"],
          "function(o,v){return o*10000+v.rr*100+v.uu;}",
          "function(i){var t=Math.floor(i/10000);if(t<10||t>17)return null;return{o:t,v:{rr:Math.floor(i/100)%100,uu:i%100}};}"),
        G("ou", "Outdoor unit objects", ["rr", "ou"], between(300000, 400000), lambda p: p["instance"] // 10000,
          lambda o, v: o * 10000 + v["rr"] * 100 + v["ou"],
          "function(o,v){return o*10000+v.rr*100+v.ou;}",
          "function(i){var t=Math.floor(i/10000);if(t<30||t>33)return null;return{o:t,v:{rr:Math.floor(i/100)%100,ou:i%100}};}",
          note="Fujitsu's manual is not consistent here: its detailed object pages give ForcedOff_Setting 30rruu, "
               "CapacitySave_Status 32rruu and CapacitySave_Setting 33rruu instead of the summary-table numbers used "
               "below. Check outdoor unit objects against a scan of the gateway."),
    ])],
    faq=[("Why does my Fujitsu indoor unit setpoint read AO 100101?",
          "100101 is point code 10 (setpoint), refrigerant system 01, indoor unit 01. Every other indoor unit "
          "uses the same point codes with its own system and unit address in the last four digits."),
         ("What is the device instance of the UTY-VBGX?",
          "It is set in the Fujitsu configuration tool. The object table shows 144000 and the configuration "
          "section says 144; give each gateway its own value. The calculator only changes the object instances.")],
    files=["fujitsu/uty-vbgx"],
))

# ---------------------------------------------------------------------------
# Mitsubishi Electric: four hardware-specific 6-digit schemes
# ---------------------------------------------------------------------------
def me_group(cc, label, key, lo, hi, note=None):
    return G("c%02d" % cc, label, [key],
             lambda p, cc=cc: p["instance"] // 10000 == cc and (p["instance"] // 100) % 100 == 1,
             lambda p: p["instance"] % 100,
             lambda o, v, cc=cc, key=key: cc * 10000 + v[key] * 100 + o,
             "function(o,v){return %d*10000+v.%s*100+o;}" % (cc, key),
             "function(i){if(Math.floor(i/10000)!==%d)return null;return{o:i%%100,v:{%s:Math.floor(i/100)%%100}};}" % (cc, key),
             note=note)


CALCS.append(dict(
    slug="mitsubishi-electric-bac-hd150", brand="Mitsubishi Electric", hw="BAC-HD150 BM Adapter", kind="object",
    title="Mitsubishi BAC-HD150 BACnet Instance Calculator",
    desc="Calculate Mitsubishi Electric BAC-HD150 BACnet instances (MMGGPP) for any M-NET number and group. "
         "M-NET 1, group 12 setpoint = AV 11210. Free calculator.",
    lede="The BAC-HD150 BM Adapter numbers every CITY MULTI group's objects as M-NET number, group number and "
         "point number. Enter the M-NET number and group to get that group's instances.",
    answer="BAC-HD150 instances are six digits <span class=\"mono\">MM GG PP</span>: M-NET number (01-03), "
           "group number (01-50) and point number. Leading zeros drop off the real number, so M-NET 1, group 12, "
           "Set Temp (point 10) is <strong>AV 11210</strong>, and M-NET 2, group 3, On Off Setup is <strong>BO 20301</strong>.",
    formula_line="instance = M-NET number x 10000 + group x 100 + point",
    formula=[("MM", "M-NET number", "01-03"), ("GG", "Group number", "01-50 (99 = collective)"),
             ("PP", "Point number (same for every group)", "01-38")],
    where="M-NET and group numbers are the ones set in the BAC-HD150 Setting Tool. System Forced Off for all "
          "groups is fixed at 999921.",
    example=dict(mm=1, gg=12), example_text="M-NET 01, group 12",
    inputs=[I("mm", "M-NET number", 1, 3, 1), I("gg", "Group number", 1, 50, 1)],
    primary="gg",
    variants=[V("v", "BAC-HD150", "mitsubishi-electric/bac-hd150", [
        G("grp", "Group objects", ["mm", "gg"],
          lambda p: 10100 < p["instance"] < 10200, lambda p: p["instance"] % 100,
          lambda o, v: v["mm"] * 10000 + v["gg"] * 100 + o,
          "function(o,v){return v.mm*10000+v.gg*100+o;}",
          "function(i){var m=Math.floor(i/10000),g=Math.floor(i/100)%100;if(m<1||m>3||g<1||g>50)return null;return{o:i%100,v:{mm:m,gg:g}};}"),
        G("mnet", "M-NET objects", ["mm"], lambda p: p["instance"] == 19981, lambda p: 81,
          lambda o, v: v["mm"] * 10000 + 9900 + o,
          "function(o,v){return v.mm*10000+9900+o;}",
          "function(i){if(i%10000!==9981)return null;return{o:81,v:{mm:Math.floor(i/10000)}};}"),
    ])],
    faq=[("Why is the instance five digits, not six?",
          "MMGGPP starts with a zero for M-NET 01 (010101), and BACnet stores numbers, so it shows as 10101. "
          "M-NET 02 and 03 give 2xxxx and 3xxxx."),
         ("Which setpoint object should I use?",
          "Single-setpoint groups use Set Temp (point 10). Dual-setpoint groups use Set Temp Cool/Heat (24/25), "
          "which only work with Old Model Compatibility Mode turned off.")],
    files=["mitsubishi-electric/bac-hd150"],
))

CALCS.append(dict(
    slug="mitsubishi-electric-ae-c400-ew-c50", brand="Mitsubishi Electric", hw="AE-C400 / EW-C50", kind="object",
    title="Mitsubishi AE-C400 / EW-C50 BACnet Instance Calculator",
    desc="Calculate Mitsubishi Electric AE-C400 / EW-C50 BACnet instances (CCNNPP) for groups, outdoor units, "
         "PI controllers and chillers. Group 7 setpoint = AV 10710.",
    lede="With the BACnet license, the AE-C400 and EW-C50 number objects by class, address and point. Enter an "
         "address to get the group, outdoor unit, PI controller, interlocked unit and chiller objects for it.",
    answer="AE-C400 / EW-C50 instances are six digits <span class=\"mono\">CC NN PP</span>: an object class "
           "(01 group, 41 PI controller, 51 outdoor unit, 61 interlocked unit, 71 chiller system, 91 chiller unit), "
           "the address (01-50) and the point. Group 7 Set Temp is <strong>AV 10710</strong>; outdoor unit 51 "
           "(class address 01) COP is <strong>AI 510101</strong>.",
    formula_line="instance = class x 10000 + address x 100 + point",
    formula=[("CC", "Object class: 01 group, 41 PI controller, 51 outdoor unit, 61 interlocked unit, 71 chiller system, 91 chiller unit", "01-91"),
             ("NN", "Address of that group or unit (99 = collective)", "01-50"),
             ("PP", "Point number", "01-88")],
    where="For outdoor units (class 51) the address is the M-NET outdoor address minus 50, so M-NET address 51 "
          "is 01. Group and other addresses come from the controller's initial settings.",
    example=dict(nn=7), example_text="address 07",
    inputs=[I("nn", "Address (group, unit or controller)", 1, 50, 1,
              "Outdoor units: M-NET address minus 50")],
    primary="nn",
    variants=[V("v", "AE-C400 / EW-C50", "mitsubishi-electric/ae-c400-ew-c50", [
        me_group(1, "Group objects (class 01)", "nn", 1, 50),
        me_group(41, "PI controller objects (class 41)", "nn", 1, 50),
        me_group(51, "Outdoor unit objects (class 51)", "nn", 1, 50),
        me_group(61, "Interlocked unit objects (class 61)", "nn", 1, 50),
        me_group(71, "Chiller system objects (class 71)", "nn", 1, 50),
        me_group(91, "Chiller unit objects (class 91)", "nn", 1, 50),
    ])],
    faq=[("What does the first part of an AE-C400 instance mean?",
          "It is the object class. 01 is a group, 41 a PI controller, 51 an outdoor unit, 61 an interlocked unit, "
          "71 a chiller system and 91 a chiller unit. 10710 is class 01 (leading zero dropped), address 07, point 10."),
         ("Do I need anything enabled first?",
          "The BACnet connection license must be registered and the controller must show ONLINE. Apportioned "
          "energy objects also need the Charge license.")],
    files=["mitsubishi-electric/ae-c400-ew-c50"],
))

CALCS.append(dict(
    slug="mitsubishi-electric-pac-yg31cda", brand="Mitsubishi Electric", hw="PAC-YG31CDA (G-50A)", kind="object",
    title="Mitsubishi PAC-YG31CDA BACnet Instance Calculator",
    desc="Calculate Mitsubishi Electric PAC-YG31CDA (G-50A) BACnet instances (AAGGPP) for any G-50A number "
         "and group. G-50A 2, group 4 room temp = AI 20409.",
    lede="The legacy PAC-YG31CDA BACnet interface serves up to ten G-50A controllers and numbers each group's "
         "objects by G-50A number, group and point.",
    answer="PAC-YG31CDA instances are six digits <span class=\"mono\">AA GG PP</span>: the G-50A number (01-10), "
           "the group number (01-50) and the point. G-50A 2, group 4, Room Temp (point 09) is <strong>AI 20409</strong>. "
           "System Forced Off is one object per G-50A at <span class=\"mono\">AA9921</span>.",
    formula_line="instance = G-50A number x 10000 + group x 100 + point",
    formula=[("AA", "G-50A number set in the PAC-YG31CDA software", "01-10"),
             ("GG", "Group number on that G-50A", "01-50"), ("PP", "Point number", "01-23")],
    where="Each G-50A gets a number 1-10 linked to its IP address in the PAC-YG31CDA software; that number is "
          "the first two digits.",
    example=dict(aa=2, gg=4), example_text="G-50A 02, group 04",
    inputs=[I("aa", "G-50A number", 1, 10, 1), I("gg", "Group number", 1, 50, 1)],
    primary="gg",
    variants=[V("v", "PAC-YG31CDA", "mitsubishi-electric/pac-yg31cda", [
        G("grp", "Group objects", ["aa", "gg"], lambda p: 10100 < p["instance"] < 10200,
          lambda p: p["instance"] % 100,
          lambda o, v: v["aa"] * 10000 + v["gg"] * 100 + o,
          "function(o,v){return v.aa*10000+v.gg*100+o;}",
          "function(i){var a=Math.floor(i/10000),g=Math.floor(i/100)%100;if(g<1||g>50)return null;return{o:i%100,v:{aa:a,gg:g}};}"),
        G("sys", "G-50A system objects", ["aa"], lambda p: p["instance"] == 19921, lambda p: 21,
          lambda o, v: v["aa"] * 10000 + 9900 + o,
          "function(o,v){return v.aa*10000+9900+o;}",
          "function(i){if(i%10000!==9921)return null;return{o:21,v:{aa:Math.floor(i/10000)}};}"),
    ])],
    faq=[("Is the PAC-YG31CDA the same numbering as the BAC-HD150?",
          "The pattern is the same (system, group, point) and most point numbers match, but the first two digits "
          "are the G-50A number (01-10) instead of the M-NET number. Use the calculator for your hardware.")],
    files=["mitsubishi-electric/pac-yg31cda"],
))

CALCS.append(dict(
    slug="mitsubishi-electric-procon-bac-ip-50", brand="Mitsubishi Electric", hw="Procon BAC-IP/50", kind="object",
    title="Mitsubishi Procon BAC-IP/50 BACnet Instance Calculator",
    desc="Calculate Procon BAC-IP/50 BACnet instances (1UUUPP) for any unit address 001-050. Unit 017 setpoint "
         "command = AO 101709. Free calculator.",
    lede="The Procon BAC-IP/50 gives every unit on its G-50 a block of objects numbered 1, the 3-digit unit "
         "address and the point number.",
    answer="Procon BAC-IP/50 unit objects are <span class=\"mono\">1 UUU PP</span>: a leading 1, the unit address "
           "(001-050) and the point number. Unit 017's setpoint command (point 09) is <strong>AO 101709</strong>. "
           "Outdoor (OC/BC) error codes use the same pattern with addresses 051-100 and point 22.",
    formula_line="instance = 100000 + unit address x 100 + point",
    formula=[("1", "Fixed first digit", "1"), ("UUU", "Unit address (OC/BC addresses 051-100 for point 22)", "001-100"),
             ("PP", "Point number", "01-27")],
    where="Unit addresses are the M-NET addresses of the units on the G-50. Only the master unit of each group "
          "accepts commands. System objects (100023-100027) are fixed.",
    example=dict(uuu=17, yyy=51), example_text="unit address 017",
    inputs=[I("uuu", "Unit address", 1, 50, 1), I("yyy", "OC/BC (outdoor) address", 51, 100, 51)],
    primary="uuu",
    variants=[V("v", "BAC-IP/50", "mitsubishi-electric/procon-bac-ip-50", [
        G("unit", "Unit objects", ["uuu"], lambda p: 100100 < p["instance"] < 100200,
          lambda p: p["instance"] % 100,
          lambda o, v: 100000 + v["uuu"] * 100 + o,
          "function(o,v){return 100000+v.uuu*100+o;}",
          "function(i){var u=Math.floor((i-100000)/100);if(i<100000||u<1||u>50)return null;return{o:i%100,v:{uuu:u}};}"),
        G("ocbc", "Outdoor unit (OC/BC) error code", ["yyy"], lambda p: p["instance"] == 105122, lambda p: 22,
          lambda o, v: 100000 + v["yyy"] * 100 + o,
          "function(o,v){return 100000+v.yyy*100+o;}",
          "function(i){var u=Math.floor((i-100000)/100);if(i%100!==22||u<51||u>100)return null;return{o:22,v:{yyy:u}};}"),
    ])],
    faq=[("Why do my commands to a unit do nothing?",
          "Only the group's master unit accepts commands on the BAC-IP/50; writes to slave unit addresses have no effect.")],
    files=["mitsubishi-electric/procon-bac-ip-50"],
))

# ---------------------------------------------------------------------------
# Daikin DMS502B71: N x 256 + member
# ---------------------------------------------------------------------------
CALCS.append(dict(
    slug="daikin-dms502b71", brand="Daikin", hw="DMS502B71 VRV BACnet interface", kind="object",
    title="Daikin DMS502B71 BACnet Instance Calculator (VRV)",
    desc="Calculate Daikin DMS502B71 BACnet instances for any VRV unit number 000-255: instance = unit x 256 + "
         "member. Unit 012 setpoint = AV 3082.",
    lede="The Daikin DMS502B71 BACnet interface gives every VRV indoor unit group the same 35-member object "
         "template. Enter the unit number to get that group's instances.",
    answer="On the DMS502B71, instance = <strong>unit number x 256 + member number</strong>. The unit number "
           "(000-255) is the XXX at the end of each object name. Unit 012's setpoint (member 10, TempAdjust_012) "
           "is 12 x 256 + 10 = <strong>AV 3082</strong>.",
    formula_line="instance = unit number x 256 + member number",
    formula=[("N", "Unit number, also the XXX in the object name", "000-255"),
             ("member", "Member number of the object in the template", "1-35")],
    where="Units 000-063 are on DIII-Net port 1, 064-127 on port 2, and 128-255 on ports 3 and 4 (DAM411B51 "
          "option). Members 17 (centralized control) and 21 (forced system stop) only exist for units 000, 064, "
          "128 and 192.",
    example=dict(n=12), example_text="unit 012",
    inputs=[I("n", "Unit number (XXX)", 0, 255, 0)],
    primary="n",
    variants=[V("v", "DMS502B71", "daikin/dms502b71", [
        G("unit", "Indoor unit group objects", ["n"], ALL, lambda p: p["instance"],
          lambda o, v: v["n"] * 256 + o,
          "function(o,v){return v.n*256+o;}",
          "function(i){var o=i%256;if(o<1||o>35)return null;return{o:o,v:{n:Math.floor(i/256)}};}",
          js_skip="function(o,v){return (o===17||o===21)&&v.n%64!==0?'Only on units 000, 064, 128 and 192':'';}",
          js_info="function(v){return 'DIII-Net port '+(v.n<64?'1':v.n<128?'2':'3 or 4 (DAM411B51 option)')+'.';}"),
    ])],
    faq=[("How do I find the unit number for a Daikin VRV group?",
          "It is the three digits at the end of the object names the interface publishes (for example "
          "StartStopCommand_012), 000-255. Divide any instance by 256: the whole number is the unit, the "
          "remainder is the member."),
         ("Why do some units have no CL_Rejection or SystemForcedOff object?",
          "Members 17 and 21 exist only once per DIII-Net line, on units 000, 064, 128 and 192.")],
    files=["daikin/dms502b71"],
))

# ---------------------------------------------------------------------------
# Toshiba BMS-IFBN1281U: n x 256 + function code
# ---------------------------------------------------------------------------
CALCS.append(dict(
    slug="toshiba-bms-ifbn1281u", brand="Toshiba", hw="BMS-IFBN1281U BN interface", kind="object",
    title="Toshiba BMS-IFBN1281U BACnet Instance Calculator",
    desc="Calculate Toshiba BMS-IFBN1281U BACnet instances for central control address 1-128: address x 256 + "
         "function code. Unit 10 setpoint = AO 2692.",
    lede="Toshiba Carrier's BN interface gives every indoor unit the same block of objects, numbered from the "
         "unit's central control address and a fixed function code.",
    answer="On the BMS-IFBN1281U, instance = <strong>central control address x 256 + function code</strong>. "
           "The ON/OFF status code is 0x02, so unit 10's run status is 10 x 256 + 2 = <strong>BI 2562</strong> and "
           "its setpoint command (code 0x84) is <strong>AO 2692</strong>.",
    formula_line="instance = central control address x 256 + function code",
    formula=[("n", "Central control address of the indoor unit (*** in the object name)", "1-128 (64 on TCC-LINK)"),
             ("code", "Function code of the object", "0x01-0xEF")],
    where="Every indoor unit needs a central control address before the BN interface's air conditioner search "
          "mode will find it; objects only exist for units it found.",
    example=dict(n=10), example_text="central control address 10",
    inputs=[I("n", "Central control address", 1, 128, 1)],
    primary="n",
    variants=[V("v", "BMS-IFBN1281U", "toshiba/bms-ifbn1281u", [
        G("unit", "Indoor unit objects", ["n"], ALL, lambda p: p["instance"] - 256,
          lambda o, v: v["n"] * 256 + o,
          "function(o,v){return v.n*256+o;}",
          "function(i){var n=Math.floor(i/256);if(n<1)return null;return{o:i%256,v:{n:n}};}"),
    ])],
    faq=[("What is the BN interface's own device instance?",
          "By default it is the last byte of its IP address (100 at the factory IP), so changing the IP changes "
          "the device instance unless 'User Setting' is chosen in the engineering tool.")],
    files=["toshiba/bms-ifbn1281u"],
))

# ---------------------------------------------------------------------------
# Gree GMS GW (made by CoolAutomation for Gree)
# ---------------------------------------------------------------------------
def gree_groups():
    c0 = G("c0", "Common objects (class 0)", ["line", "addr"], lambda p: p["instance"] < 1048576,
           lambda p: p["instance"] - 256,
           lambda o, v: (v["line"] - 1) * 131072 + v["addr"] * 256 + o,
           "function(o,v){return (v.line-1)*131072+v.addr*256+o;}",
           "function(i){if(i>=1048576)return null;return{o:i%256,v:{line:Math.floor(i/131072)+1,addr:Math.floor((i%131072)/256)}};}")
    c1 = G("c1", "Series-specific objects (class 1)", ["line", "addr"], lambda p: p["instance"] >= 1048576,
           lambda p: p["instance"] - 1048576 - 256,
           lambda o, v: 1048576 + (v["line"] - 1) * 131072 + v["addr"] * 256 + o,
           "function(o,v){return 1048576+(v.line-1)*131072+v.addr*256+o;}",
           "function(i){if(i<1048576||i>=2097152)return null;var r=i-1048576;return{o:r%256,v:{line:Math.floor(r/131072)+1,addr:Math.floor((r%131072)/256)}};}")
    return [c0, c1]


CALCS.append(dict(
    slug="gree", brand="Gree", hw="GMS GW BACnet converter", kind="object",
    title="Gree BACnet Instance Calculator (GMS GW Converter)",
    desc="Calculate Gree GMS GW BACnet instances for any line and remote control address, for DWUNI and "
         "R-series units. Line 1, address 5 setpoint = AV 1280.",
    lede="Gree's GMS GW 1 and GMS GW 12 converters number every split unit's objects from its line and remote "
         "control address. Pick the unit series, enter the address and get the instances.",
    answer="GMS GW instance = <span class=\"mono\">class x 1048576 + (line - 1) x 131072 + remote control address "
           "x 256 + object number</span>. Common objects are class 0, series-specific ones class 1. Line 1, address "
           "5 setpoint (object 0) is 5 x 256 + 0 = <strong>AV 1280</strong>.",
    formula_line="instance = class x 1048576 + (line - 1) x 131072 + address x 256 + object",
    formula=[("class", "0 = common objects, 1 = series-specific objects", "0-1"),
             ("line", "RS-485 line of the converter (the gateway shows units as L<line>.<address>)", "1-2"),
             ("address", "Remote control address set on the unit's wired controller", "0-63"),
             ("object", "Object number inside the unit's block", "0-255")],
    where="Each split unit's remote control address (0-63 per line) is set on its wired controller; the gateway "
          "shows it as L1.005 and so on. GMS GW 1 handles one unit, GMS GW 12 up to 12 units on two lines.",
    example=dict(line=1, addr=5), example_text="line 1, address 05 (L1.005)",
    inputs=[I("line", "Line", 1, 2, 1), I("addr", "Remote control address", 0, 63, 1)],
    primary="addr",
    variants=[V("dwuni", "M / W / P / X series (DWUNI controller)", "gree/gms-gw-dwuni", gree_groups()),
              V("r", "R series", "gree/gms-gw-r-series", gree_groups())],
    faq=[("Why are some Gree objects above one million?",
          "Series-specific objects are class 1, which adds 1048576 (2 to the power of 20) to the instance. They "
          "differ between DWUNI (M/W/P/X) and R-series units, so pick the right series."),
         ("Who makes the Gree GMS GW?",
          "The converter is made by CoolAutomation for Gree, which is why its numbering looks like the "
          "CoolMasterNet scheme.")],
    files=["gree/gms-gw-dwuni", "gree/gms-gw-r-series"],
))

# ---------------------------------------------------------------------------
# CoolAutomation CoolMasterNet / CooLink (multi-brand): VA x 256 + index
# ---------------------------------------------------------------------------
CALCS.append(dict(
    slug="coolautomation-coolmasternet", brand="CoolAutomation", hw="CoolMasterNet / CooLink", kind="object",
    title="CoolMasterNet BACnet Instance Calculator (VA x 256)",
    desc="Calculate CoolMasterNet and CooLink BACnet instances from the virtual address: VA x 256 + index. "
         "VA 12 setpoint = AV 3072. Works for any AC brand behind it.",
    lede="CoolAutomation gateways serve every indoor unit, whatever the AC brand, as the same 16 objects at its "
         "virtual address (VA). Enter the VA to get the instances.",
    answer="On CoolMasterNet and CooLink gateways, instance = <strong>VA x 256 + object index</strong> (the VA "
           "sits in bits 21-8, the index in bits 7-0). VA 12's setpoint is 12 x 256 + 0 = <strong>AV 3072</strong> "
           "and its on/off is <strong>BV 3072</strong>. LG VRF outdoor service objects (PRO) use the same scheme.",
    formula_line="instance = VA x 256 + object index",
    formula=[("VA", "Virtual address given to the unit by 'va auto' (or set by hand)", "1-16383"),
             ("index", "Object index inside the unit's block", "0-255")],
    where="Run 'va auto' on the gateway so each indoor unit gets a virtual address; the 'va' command lists them. "
          "The gateway's own device instance defaults to 64.",
    example=dict(va=12, ova=1), example_text="VA 12",
    inputs=[I("va", "Indoor unit VA", 1, 16383, 1), I("ova", "LG outdoor unit VA (PRO objects)", 1, 16383, 1)],
    primary="va",
    variants=[dict(id="v", label="CoolMasterNet", rel=None, groups=[], multi=[
        ("coolautomation/coolmasternet-bacnet",
         G("iu", "Indoor unit objects", ["va"], ALL, lambda p: p["instance"] - 256,
           lambda o, v: v["va"] * 256 + o,
           "function(o,v){return v.va*256+o;}",
           "function(i){var a=Math.floor(i/256);if(a<1)return null;return{o:i%256,v:{va:a}};}")),
        ("coolautomation/coolmasternet-lg-vrf-outdoor",
         G("ou", "LG VRF outdoor unit objects (PRO)", ["ova"], ALL, lambda p: p["instance"] - 256,
           lambda o, v: v["ova"] * 256 + o,
           "function(o,v){return v.ova*256+o;}",
           "function(i){var a=Math.floor(i/256);if(a<1)return null;return{o:i%256,v:{ova:a}};}",
           note="CoolAutomation's guide does not say how outdoor units get their VA; read it from the gateway.")),
    ])],
    faq=[("Does this work for Daikin, Mitsubishi, LG and Samsung units on a CoolMasterNet?",
          "Yes. The gateway uses the same 16 objects and the same VA x 256 numbering whatever brand is behind it. "
          "Modes, fan speeds or louvers a unit does not support are simply unused.")],
    files=["coolautomation/coolmasternet-bacnet", "coolautomation/coolmasternet-lg-vrf-outdoor"],
))

# ---------------------------------------------------------------------------
# Intesis multi-unit VRF servers (hardware-specific)
# ---------------------------------------------------------------------------
CALCS.append(dict(
    slug="intesis-hitachi-inbachit", brand="Intesis", hw="INBACHIT016O000 / 064O000 (Hitachi H-Link)", kind="object",
    title="Intesis Hitachi VRF BACnet Instance Calculator",
    desc="Calculate Intesis INBACHIT016O000 / 064O000 (Hitachi H-Link) BACnet instances: indoor = index x 100 "
         "+ offset. Index 23 setpoint command = AO 2300.",
    lede="The Intesis BACnet server for Hitachi VRF gives each indoor unit a block at its MAPS index x 100 and "
         "each outdoor unit a block at address x 25 + 1000.",
    answer="Indoor unit instance = <strong>index x 100 + offset</strong>, where the index is the unit's number in "
           "Intesis MAPS (not always its H-Link address). Outdoor unit instance = <strong>address x 25 + 1000 + "
           "offset</strong>. Indoor index 23's setpoint command is <strong>AO 2300</strong>; outdoor address 2's "
           "outdoor air temperature is <strong>AI 1050</strong>.",
    formula_line="indoor = index x 100 + offset; outdoor = address x 25 + 1000 + offset",
    formula=[("index", "Indoor unit index in Intesis MAPS", "1-16 or 1-64"),
             ("address", "Outdoor unit address", "0-63"), ("offset", "Object offset in the block", "0-11 / 0-6")],
    where="Use the index Intesis MAPS shows for the unit, which is not necessarily its H-Link address. Objects 0-2 "
          "command all units at once.",
    example=dict(idx=23, oa=2), example_text="indoor index 23, outdoor address 2",
    inputs=[I("idx", "Indoor unit index (MAPS)", 1, 64, 1), I("oa", "Outdoor unit address", 0, 63, 0)],
    primary="idx",
    variants=[V("v", "INBACHIT", "intesis/inbachit064o000", [
        G("iu", "Indoor unit objects", ["idx"], between(100, 200), lambda p: p["instance"] - 100,
          lambda o, v: v["idx"] * 100 + o,
          "function(o,v){return v.idx*100+o;}",
          "function(i){var x=Math.floor(i/100);if(x<1)return null;return{o:i%100,v:{idx:x}};}"),
        G("ou", "Outdoor unit objects", ["oa"], between(1000, 1025), lambda p: p["instance"] - 1000,
          lambda o, v: v["oa"] * 25 + 1000 + o,
          "function(o,v){return v.oa*25+1000+o;}",
          "function(i){if(i<1000)return null;return{o:(i-1000)%25,v:{oa:Math.floor((i-1000)/25)}};}"),
    ])],
    faq=[("Why does one instance match both an indoor and an outdoor unit?",
          "The two formulas overlap above 1000 (indoor index 10 starts at 1000, so does outdoor address 0), and "
          "the object type does not always tell them apart. The calculator lists every possible match; check the "
          "object name on the device.")],
    files=["intesis/inbachit064o000"],
))

CALCS.append(dict(
    slug="intesis-panasonic-inbacpan", brand="Intesis", hw="INBACPAN016O000 / 064O000 / 128O000 (Panasonic P-Link)",
    kind="object",
    title="Intesis Panasonic VRF BACnet Instance Calculator",
    desc="Calculate Intesis INBACPAN (Panasonic P-Link) BACnet instances: indoor = unit x 100 + (line - 1) x "
         "20000. Line 1, unit 8 setpoint command = AO 800.",
    lede="The Intesis BACnet server for Panasonic VRF numbers every indoor and outdoor unit from its P-Link line "
         "and address.",
    answer="Indoor unit base = <strong>unit x 100 + (line - 1) x 20000</strong>; outdoor unit base = "
           "<strong>outdoor x 25 + (line - 1) x 1000 + 10000</strong>; add the object offset. Line 1, indoor unit 8 "
           "setpoint command is <strong>AO 800</strong>; line 2, outdoor unit 3 high pressure is <strong>AI 11076</strong>.",
    formula_line="indoor = unit x 100 + (line-1) x 20000 + offset; outdoor = OU x 25 + (line-1) x 1000 + 10000 + offset",
    formula=[("line", "P-Link line (the 128-unit model has two)", "1-2"),
             ("unit", "Indoor unit address on that line", "1-64"),
             ("OU", "Outdoor unit address on that line", "1-31"), ("offset", "Object offset", "0-17 / 0-3")],
    where="Outdoor units are addressed 1-31 per line and indoor units 1-64 per line, as configured in Intesis MAPS. "
          "Objects 0-2 command all units.",
    example=dict(line=1, u=8, o=1), example_text="line 1, indoor unit 8",
    inputs=[I("line", "P-Link line", 1, 2, 1), I("u", "Indoor unit address", 1, 64, 1),
            I("o", "Outdoor unit address", 1, 31, 1)],
    primary="u",
    variants=[V("v", "INBACPAN", "intesis/inbacpan064o000", [
        G("iu", "Indoor unit objects", ["line", "u"], between(100, 200), lambda p: p["instance"] - 100,
          lambda o, v: v["u"] * 100 + (v["line"] - 1) * 20000 + o,
          "function(o,v){return v.u*100+(v.line-1)*20000+o;}",
          "function(i){var r=i%20000,u=Math.floor(r/100);if(u<1)return null;return{o:r%100,v:{line:Math.floor(i/20000)+1,u:u}};}"),
        G("ou", "Outdoor unit objects", ["line", "o"], between(10025, 10050), lambda p: p["instance"] - 10025,
          lambda o, v: v["o"] * 25 + (v["line"] - 1) * 1000 + 10000 + o,
          "function(o,v){return v.o*25+(v.line-1)*1000+10000+o;}",
          "function(i){if(i<10000)return null;var r=(i-10000)%1000;return{o:r%25,v:{line:Math.floor((i-10000)/1000)+1,o:Math.floor(r/25)}};}",
          note="Room Temperature: the summary tables print AI FI+0, its detail page AI FI+1. This list uses FI+1; check on site."),
    ])],
    faq=[("What is the gateway's own device instance?",
          "246 by default, configurable in Intesis MAPS. The calculator only works out the object instances inside it.")],
    files=["intesis/inbacpan064o000"],
))

CALCS.append(dict(
    slug="intesis-samsung-inbacsam", brand="Intesis", hw="INBACSAM004O000-064O000 (Samsung NASA)", kind="object",
    title="Intesis Samsung NASA BACnet Instance Calculator",
    desc="Calculate Intesis INBACSAM (Samsung NASA) BACnet instances: identifier x 100 + offset. Identifier 14 "
         "room temperature = AI 1401. Free calculator.",
    lede="The Intesis BACnet server for Samsung NASA gives every indoor unit a block of objects at its MAPS "
         "identifier x 100.",
    answer="Indoor unit instance = <strong>identifier x 100 + offset</strong>, where the identifier (1-64) is the "
           "number assigned to the unit in Intesis MAPS. Identifier 14's room temperature is <strong>AI 1401</strong> "
           "and its on/off command is <strong>BO 1400</strong>.",
    formula_line="instance = identifier x 100 + offset",
    formula=[("identifier", "Indoor unit identifier assigned in Intesis MAPS", "1-64"),
             ("offset", "Object offset in the unit's block", "0-8")],
    where="The identifier is assigned in Intesis MAPS after scanning the bus; it is not the unit's NASA address "
          "(indoor 0-63, outdoor 0-15). Outdoor communication errors are fixed at BI 0-15.",
    example=dict(id=14), example_text="identifier 14",
    inputs=[I("id", "Indoor unit identifier (MAPS)", 1, 64, 1)],
    primary="id",
    variants=[V("v", "INBACSAM", "intesis/inbacsam064o000", [
        G("iu", "Indoor unit objects", ["id"], between(100, 200), lambda p: p["instance"] - 100,
          lambda o, v: v["id"] * 100 + o,
          "function(o,v){return v.id*100+o;}",
          "function(i){var x=Math.floor(i/100);if(x<1)return null;return{o:i%100,v:{id:x}};}",
          note="Hot-water, AHU, ERV and chiller units reuse the same block with a different object set (see the manual)."),
    ])],
    faq=[("Is this the same as Samsung's own MIM-B17BN gateway?",
          "No. Samsung's DMS2.5 BACnet gateway makes one virtual device per unit; this Intesis server puts every "
          "unit in one device. Use the Samsung MIM-B17BN calculator for that gateway.")],
    files=["intesis/inbacsam064o000"],
))

# ---------------------------------------------------------------------------
# LG (ACP BACnet, AC Smart BACnet, AC Smart 5, BNU-BAC): type x 65536 + hex address x 256 + point
# ---------------------------------------------------------------------------
def lg_group(gid, label, key, ptype, prefix):
    base = ptype * 65536
    return G(gid, label, [key], desc_prefix(prefix), lambda p, base=base: p["instance"] - base,
             lambda o, v, base=base, key=key: base + v[key] * 256 + o,
             "function(o,v){return %d+v.%s*256+o;}" % (base, key),
             "function(i){if(Math.floor(i/65536)!==%d)return null;return{o:i%%256,v:{%s:Math.floor((i%%65536)/256)}};}"
             % (ptype, key))


CALCS.append(dict(
    slug="lg", brand="LG", hw="ACP BACnet / AC Smart BACnet", kind="object",
    title="LG BACnet Instance Calculator (ACP / AC Smart VRF)",
    desc="Work out LG ACP BACnet and AC Smart BACnet instances from the hex unit address: address x 256 + point. "
         "Unit 1A on/off = BO 6657, setpoint = AV 6669.",
    lede="LG's BACnet gateways build every object number from the product type, the unit address and the point "
         "number. Enter the address as LG shows it (for example 1A) and get that unit's objects.",
    answer="On LG's ACP BACnet and AC Smart BACnet, instance = <span class=\"mono\">product type x 65536 + unit "
           "address x 256 + point</span>, and the address is read as <strong>hex</strong>. Indoor units are type 0, "
           "so unit 1A (= 26) has on/off <strong>BO 6657</strong>, mode MO 6663, fan speed MO 6667 and setpoint "
           "<strong>AV 6669</strong>. Ventilation units add 65536, outdoor units 196608.",
    formula_line="instance = product type x 65536 + hex address x 256 + point",
    formula=[("product type", "0 indoor unit, 1 ventilation (ERV), 2 AHU, 3 outdoor unit, 4 AWHP, 5 general", "0-5"),
             ("address", "LG unit address, read as hex (1A = 26)", "00-FF"),
             ("point", "Point number from LG's table", "1-49")],
    where="Use the unit address set on the indoor unit or shown by the ACP / AC Smart (for example 1A or 2F). "
          "LG's AC Smart 5 and older BNU-BAC gateways print the same formula and the same point numbers for the "
          "points they share. Each product type sits in its own BACnet device: Device ID (default 9000) for "
          "indoor units, +1 ERV, +3 outdoor unit data.",
    example=dict(addr=0x1A, vaddr=0, oaddr=0), example_text="indoor unit 1A",
    inputs=[I("addr", "Indoor unit address (hex)", 0, 255, 0x1A, "As LG shows it, e.g. 1A", hexin=True),
            I("vaddr", "Ventilation (ERV) address (hex)", 0, 255, 0, hexin=True),
            I("oaddr", "Outdoor unit address (hex)", 0, 255, 0, hexin=True)],
    primary="addr",
    variants=[V("v", "ACP BACnet", "lg/acp-bacnet", [
        lg_group("iu", "Indoor unit objects (type 0)", "addr", 0, "[Indoor unit]"),
        lg_group("erv", "Ventilation (ERV) objects (type 1)", "vaddr", 1, "[Ventilation]"),
        lg_group("odu", "Outdoor unit objects (type 3)", "oaddr", 3, "[Outdoor unit]"),
    ])],
    faq=[("Why is LG unit 1A's on/off 6657 and not 1A01?",
          "It is the same number: 0x1A01 in hex is 6657 in decimal. LG puts the hex unit address in the middle "
          "byte, so address x 256 + point gives the decimal instance your BMS shows."),
         ("Does AC Smart use the same numbers as the ACP?",
          "Yes. LG's AC Smart BACnet manual prints the same formula and the same indoor, ERV and outdoor tables. "
          "AC Smart 5 adds points 50 and up; BNU-BAC has a shorter list but the same numbers for the points it has.")],
    files=["lg/acp-bacnet"],
))

# ---------------------------------------------------------------------------
# Device-ID schemes (one virtual BACnet device per unit)
# ---------------------------------------------------------------------------
CALCS.append(dict(
    slug="samsung-mim-b17bn", brand="Samsung", hw="MIM-B17BN DMS2.5 BACnet gateway", kind="device",
    title="Samsung MIM-B17BN BACnet Device ID Calculator",
    desc="Work out Samsung DMS2.5 (MIM-B17BN) BACnet device IDs from DNET and the unit address a.b.c. Gateway 9, "
         "indoor 01.01.32 = device 941732.",
    lede="Samsung's DMS2.5 BACnet gateway makes every unit its own BACnet device and builds the device ID from "
         "the network number and the unit address. Enter them to get the device ID, or decode one.",
    answer="The device ID is three parts written one after the other: <span class=\"mono\">DNET | CPP | XX</span>. "
           "DNET is the gateway's network number (1-40), CPP = 400 + 16 x a + b for unit address a.b.c, and XX is "
           "the indoor address c (00-63) or 64 for an outdoor unit. Samsung's example: network 9, indoor unit "
           "01.01.32 gives 9 | 417 | 32 = <strong>941732</strong>.",
    formula_line="device ID = DNET x 100000 + (400 + 16a + b) x 100 + XX",
    formula=[("DNET", "Network No. set on the gateway's BACnet page (default 9)", "1-40"),
             ("a", "OnOff (centralized) controller address, first part of a.b.c", "0-15"),
             ("b", "Interface module (outdoor unit) address, second part", "0-15"),
             ("XX", "Indoor unit address c, or 64 for an outdoor unit or the gateway", "00-64")],
    where="Samsung shows unit addresses as a.b.c, for example 01.01.32: OnOff controller, interface module "
          "(outdoor unit), indoor unit. Each gateway on the same network needs its own Network No. Inside every "
          "unit device the object instances are small fixed numbers, listed under each unit type below.",
    example=dict(dnet=9, a=1, b=1, c=32, n=0), example_text="network 9, unit 01.01.32",
    inputs=[I("dnet", "Network No. (DNET)", 1, 40, 9), I("a", "OnOff controller address (a)", 0, 15, 1),
            I("b", "Interface module / outdoor address (b)", 0, 15, 1), I("c", "Indoor unit address (c)", 0, 63, 0),
            I("n", "Controller / SIM / DI-DO address", 0, 15, 0, "Only for those three device types")],
    primary="c",
    variants=[V("v", "MIM-B17BN", "samsung/mim-b17bn", [
        D(gid, label, ["dnet", "a", "b", "c"], desc_prefix(prefix),
          lambda v: v["dnet"] * 100000 + (400 + 16 * v["a"] + v["b"]) * 100 + v["c"],
          "function(v){return v.dnet*100000+(400+16*v.a+v.b)*100+v.c;}",
          "function(d){var x=d%100,c=Math.floor(d/100)%1000,n=Math.floor(d/100000);if(x>63||c<400||c>655)return null;return{dnet:n,a:Math.floor((c-400)/16),b:(c-400)%16,c:x};}")
        for gid, label, prefix in [("iu", "Indoor unit", "[Indoor unit]"), ("ahu", "AHU kit", "[AHU kit]"),
                                   ("ehs", "EHS (air-to-water)", "[EHS]"), ("erv", "ERV / ERV Plus", "[ERV]")]
    ] + [
        D("odu", "Outdoor unit (interface module)", ["dnet", "a", "b"], desc_prefix("[Outdoor unit]"),
          lambda v: v["dnet"] * 100000 + (400 + 16 * v["a"] + v["b"]) * 100 + 64,
          "function(v){return v.dnet*100000+(400+16*v.a+v.b)*100+64;}",
          "function(d){var c=Math.floor(d/100)%1000;if(d%100!==64||c<400||c>655)return null;return{dnet:Math.floor(d/100000),a:Math.floor((c-400)/16),b:(c-400)%16};}"),
        D("gw", "BACnet gateway", ["dnet"], desc_prefix("[Gateway]"),
          lambda v: v["dnet"] * 100000 + 90064,
          "function(v){return v.dnet*100000+90064;}",
          "function(d){if(d%100000!==90064)return null;return{dnet:Math.floor(d/100000)};}"),
        D("cc", "Centralized (OnOff) controller", ["dnet", "n"], desc_prefix("[Central ctrl]"),
          lambda v: v["dnet"] * 100000 + v["n"] * 100 + 64,
          "function(v){return v.dnet*100000+v.n*100+64;}",
          "function(d){var c=Math.floor(d/100)%1000;if(d%100!==64||c>15)return null;return{dnet:Math.floor(d/100000),n:c};}",
          note="Samsung gives only the CPP range 000-015; 000 + the controller's address is our reading of it."),
        D("sim", "SIM / PIM", ["dnet", "n"], desc_prefix("[SIM/PIM]"),
          lambda v: v["dnet"] * 100000 + (100 + v["n"]) * 100 + 64,
          "function(v){return v.dnet*100000+(100+v.n)*100+64;}",
          "function(d){var c=Math.floor(d/100)%1000;if(d%100!==64||c<100||c>115)return null;return{dnet:Math.floor(d/100000),n:c-100};}",
          note="Samsung gives only the CPP range 100-115; 100 + the module's address is our reading of it."),
        D("ddc", "DMS DI/DO", ["dnet", "n"], desc_prefix("[DDC]"),
          lambda v: v["dnet"] * 100000 + (300 + v["n"]) * 100 + 64,
          "function(v){return v.dnet*100000+(300+v.n)*100+64;}",
          "function(d){var c=Math.floor(d/100)%1000;if(d%100!==64||c<300||c>315)return null;return{dnet:Math.floor(d/100000),n:c-300};}",
          note="Samsung gives only the CPP range 300-315; 300 + the module's address is our reading of it."),
        D("mc", "DVM chiller", [], desc_prefix("[DVM chiller]"), None, "null", "null",
          note="The manual's device ID table does not cover DVM chillers; read the device ID from a scan."),
    ])],
    faq=[("Is the Samsung device ID a sum or the digits put together?",
          "The digits put together: network number, then the 3-digit CPP code, then the 2-digit address. "
          "9, 417 and 32 make 941732. As arithmetic that is DNET x 100000 + CPP x 100 + XX."),
         ("What device ID does an outdoor unit get?",
          "The same DNET and CPP as the indoor units behind it, with 64 as the last two digits. Network 9, outdoor "
          "unit 01.01 works out to 941764 (our worked example from Samsung's table, not printed in the manual)."),
         ("Are the address parts hex or decimal?",
          "Samsung's manual does not say. Its only example (01.01.32) reads the same either way. If your DMS shows "
          "letters in an address, confirm the device ID with a scan.")],
    files=["samsung/mim-b17bn"],
))

CALCS.append(dict(
    slug="lennox-vrf-bacnet-gateway", brand="Lennox", hw="VRF BACnet gateway V0CTRL95P-3", kind="device",
    title="Lennox VRF BACnet Gateway Device ID Calculator",
    desc="Work out Lennox VRF BACnet gateway (V0CTRL95P-3) device IDs: bus, unit type and address. Bus 1, "
         "indoor unit 12 = device 1012. Free calculator.",
    lede="The Lennox V0CTRL95P-3 makes every VRF indoor and outdoor unit its own BACnet device, with a 4-digit "
         "device ID built from the bus, the unit type and the unit address.",
    answer="Device ID = <span class=\"mono\">bus | type | address</span>: bus (port) 0-3, type 0 for indoor or 1 "
           "for outdoor, then the 2-digit unit address. Bus 1, indoor unit 12 is <strong>1012</strong>; bus 0, "
           "outdoor unit 5 is <strong>105</strong> (written 0105). Inside each device the object instances are fixed.",
    formula_line="device ID = bus x 1000 + type x 100 + address",
    formula=[("bus", "RS-485 bus (port) on the gateway", "0-3"), ("type", "0 = indoor unit, 1 = outdoor unit", "0-1"),
             ("address", "Unit address (indoor 00-63, outdoor 00-31)", "00-63")],
    where="Lennox's own examples are 0001 (bus 0, indoor unit 01) and 1105 (bus 1, outdoor unit 05). A leading "
          "zero is dropped in the real device instance.",
    example=dict(bus=1, addr=12, oaddr=5), example_text="bus 1, indoor unit 12",
    inputs=[I("bus", "Bus (port)", 0, 3, 0), I("addr", "Indoor unit address", 0, 63, 1),
            I("oaddr", "Outdoor unit address", 0, 31, 0)],
    primary="addr",
    variants=[V("v", "V0CTRL95P-3", "lennox/vrf-bacnet-gateway-v0ctrl95p-3", [
        D("iu", "Indoor unit device", ["bus", "addr"], desc_prefix("[Indoor unit]"),
          lambda v: v["bus"] * 1000 + v["addr"],
          "function(v){return v.bus*1000+v.addr;}",
          "function(d){if(d>3999||Math.floor(d/100)%10!==0||d%100>63)return null;return{bus:Math.floor(d/1000),addr:d%100};}"),
        D("ou", "Outdoor unit device", ["bus", "oaddr"], desc_prefix("[Outdoor unit]"),
          lambda v: v["bus"] * 1000 + 100 + v["oaddr"],
          "function(v){return v.bus*1000+100+v.oaddr;}",
          "function(d){if(d>3999||Math.floor(d/100)%10!==1||d%100>31)return null;return{bus:Math.floor(d/1000),oaddr:d%100};}"),
    ])],
    faq=[("Why do indoor and outdoor Lennox devices have the same object numbers?",
          "Each unit is its own BACnet device, so AI 1 is room temperature inside an indoor unit device and "
          "ambient temperature inside an outdoor unit device. The device ID tells you which one you are reading.")],
    files=["lennox/vrf-bacnet-gateway-v0ctrl95p-3"],
))


def xye_groups(with_hthm=False):
    gs = [
        D("iu", "Indoor unit device", ["net", "port", "addr"],
          desc_prefix("[Indoor unit]") if with_hthm else ALL,
          lambda v: v["net"] * 10000 + v["port"] * 1000 + v["addr"],
          "function(v){return v.net*10000+v.port*1000+v.addr;}",
          "function(d){var r=d%10000,x=r%1000;if(Math.floor(r/1000)>3||x>63)return null;return{net:Math.floor(d/10000),port:Math.floor(r/1000),addr:x};}"),
        D("ou", "Outdoor unit device", ["net", "port", "oaddr"],
          desc_prefix("[Outdoor unit]") if with_hthm else (lambda p: False),
          lambda v: v["net"] * 10000 + v["port"] * 1000 + 100 + v["oaddr"],
          "function(v){return v.net*10000+v.port*1000+100+v.oaddr;}",
          "function(d){var r=d%10000,x=r%1000;if(Math.floor(r/1000)>3||x<100||x>131)return null;return{net:Math.floor(d/10000),port:Math.floor(r/1000),oaddr:x-100};}",
          note=None if with_hthm else "Outdoor unit objects are in section 4-2 of the Sinclair manual and are not in this list."),
    ]
    if with_hthm:
        gs.append(D("hthm", "HTHM (high-temperature hydro module) device", [], desc_prefix("[HTHM unit]"),
                    None, "null", "null",
                    note="The manual gives no device instance rule for HTHM units; read it from a scan."))
    return gs


XYE_FORMULA = [("network", "BACnet network number set on the gateway's web page", "2-254"),
               ("port", "RS-485 port (0 = the one next to the Ethernet jack)", "0-3"),
               ("address", "Indoor unit address (outdoor: 100 + outdoor address)", "0-63 (OU 0-31)")]

CALCS.append(dict(
    slug="sinclair-gw-bac", brand="Sinclair", hw="SDV5 VRF BACnet gateway GW-BAC", kind="device",
    title="Sinclair SDV5 GW-BAC BACnet Device ID Calculator",
    desc="Work out Sinclair SDV5 GW-BAC BACnet device instances: network x 10000 + port x 1000 + address. "
         "Network 2, port 1, unit 7 = device 21007.",
    lede="The Sinclair GW-BAC makes every SDV5 indoor and outdoor unit its own BACnet device. Its device instance "
         "comes from the gateway's network number, the RS-485 port and the unit address.",
    answer="Indoor unit device instance = <strong>network number x 10000 + port x 1000 + indoor address</strong>; "
           "outdoor units add 100 to the address. Network 2, port 1, indoor unit 7 is <strong>21007</strong>; "
           "outdoor unit 3 on the same port is <strong>21103</strong>. Every indoor unit device has the same object instances.",
    formula_line="device = network x 10000 + port x 1000 + address (outdoor + 100)",
    formula=XYE_FORMULA,
    where="Set a BACnet network number of 2-254 that nothing else uses on the gateway's web page, then restart "
          "it. Ports are numbered 0-3, port 0 being the one next to the Ethernet jack.",
    example=dict(net=2, port=1, addr=7, oaddr=3), example_text="network 2, port 1, indoor unit 7",
    inputs=[I("net", "BACnet network number", 2, 254, 2), I("port", "RS-485 port", 0, 3, 0),
            I("addr", "Indoor unit address", 0, 63, 0), I("oaddr", "Outdoor unit address", 0, 31, 0)],
    primary="addr",
    variants=[V("v", "GW-BAC", "sinclair/sdv5-gw-bac", xye_groups())],
    faq=[("Is the Sinclair GW-BAC the same as the Systemair gateway?",
          "They use the same device instance formula. The Systemair SYS GW IMS BAC(A) list also covers outdoor "
          "units and HTHM modules; it has its own calculator.")],
    files=["sinclair/sdv5-gw-bac"],
))

CALCS.append(dict(
    slug="systemair-sys-gw-ims-bac", brand="Systemair", hw="SYS GW IMS BAC(A) VRF gateway", kind="device",
    title="Systemair SYS GW IMS BAC BACnet Device ID Calculator",
    desc="Work out Systemair SYS GW IMS BAC(A) BACnet device instances for SYSVRF units: network x 10000 + port "
         "x 1000 + address. Network 5, port 2, unit 14 = 52014.",
    lede="The Systemair SYS GW IMS BAC(A) (IMMP-BAC in the manual) makes every SYSVRF indoor and outdoor unit its "
         "own BACnet device, numbered from the network number, port and unit address.",
    answer="Indoor unit device instance = <strong>network number x 10000 + port x 1000 + indoor address</strong>; "
           "outdoor units add 100 to the address. Network 5, port 2, indoor unit 14 is <strong>52014</strong>; "
           "outdoor unit 0 on that port is <strong>52100</strong>.",
    formula_line="device = network x 10000 + port x 1000 + address (outdoor + 100)",
    formula=XYE_FORMULA,
    where="Set a BACnet network number of 2-254 on the gateway's web page (each gateway needs a different one) "
          "and restart it. Port 0 is the RS-485 port next to the Ethernet port.",
    example=dict(net=5, port=2, addr=14, oaddr=0), example_text="network 5, port 2, indoor unit 14",
    inputs=[I("net", "BACnet network number", 2, 254, 2), I("port", "RS-485 port", 0, 3, 0),
            I("addr", "Indoor unit address", 0, 63, 0), I("oaddr", "Outdoor unit address", 0, 31, 0)],
    primary="addr",
    variants=[V("v", "SYS GW IMS BAC(A)", "systemair/sys-gw-ims-bac-a", xye_groups(with_hthm=True))],
    faq=[("What do the Systemair error code numbers mean?",
          "0 is no error; then blocks of 20 per letter (1-20 = A0-AU, 21-40 = b, 41-60 = C and so on). The "
          "unit's service manual gives the meaning of each code.")],
    files=["systemair/sys-gw-ims-bac-a"],
))

PROTONODE_FILES = [
    ("laars/htd-protonode", "Laars HTD"), ("laars/magnatherm-protonode", "Laars Mascot / Magnatherm"),
    ("laars/multiburner-protonode", "Laars multi-burner"), ("laars/omnitherm-protonode", "Laars OmniTherm"),
    ("laars/sola-protonode", "Laars Sola"), ("laars/sv2-protonode", "Laars SV2 gas valve"),
    ("peerless/purefire-852if", "Peerless PureFire 852IF"), ("peerless/purefire-pfa-1", "Peerless PureFire PFA"),
    ("raypak/protonode-gateway", "Raypak VERSA IC"),
    ("aerco/c-more-acs-protonode", "AERCO C-More with ACS / BMS II"),
    ("aerco/c-more-bst-whm-protonode", "AERCO C-More with BST / WHM"),
    ("aerco/ecs-smartplate-protonode", "AERCO ECS / SmartPlate"), ("aerco/modulex-bcm-protonode", "AERCO Modulex BCM"),
    ("bosch/ssb-boiler-protonode", "Buderus SSB boilers"),
    ("thermal-solutions/apex-panasonic-4109-universal-gateway", "Thermal Solutions Apex (4109)"),
    ("thermal-solutions/concert-4716-universal-gateway", "Thermal Solutions Apex / Arctic (Concert 4716)"),
    ("thermal-solutions/tsbc-universal-gateway", "Thermal Solutions TSBC"),
    ("thermal-solutions/eva-evo-rm7800", "Thermal Solutions EVA/EVO RM7800"),
    ("thermal-solutions/eva-evo-rwf40", "Thermal Solutions EVA/EVO RWF40"),
    ("thermal-solutions/eva-evo-rwf55", "Thermal Solutions EVA/EVO RWF55"),
    ("hamilton-engineering/bdb-cdb-protonode", "Hamilton BDB-CDB"),
]


def pn_group():
    return [D("dev", "Boiler / controller device", ["off", "node"], ALL,
              lambda v: v["off"] + v["node"],
              "function(v){return v.off+v.node;}",
              "function(d){var n=d-window.CALCV.off;if(n<1||n>255)return null;return{off:window.CALCV.off,node:n};}")]


CALCS.append(dict(
    slug="protonode", brand="ProtoNode", hw="boiler gateways (Laars, Peerless, Raypak, AERCO and more)", kind="device",
    title="ProtoNode BACnet Device Instance Calculator (Boilers)",
    desc="Work out the BACnet device instance of every boiler behind a ProtoNode: Node_Offset + Node-ID. "
         "Default offset 50000: node 3 = device 50003. Laars, Raypak...",
    lede="Boiler makers use FieldServer ProtoNode gateways to put Modbus boilers on BACnet. Every boiler becomes "
         "its own BACnet device numbered Node_Offset + Node-ID, and every one carries the same objects.",
    answer="Device instance = <strong>Node_Offset + Node-ID</strong>. Node_Offset is 50000 unless someone changed "
           "it in the ProtoNode Web Configurator, and the Node-ID is the boiler's Modbus address (on AERCO, the "
           "A-bank DIP switch value). Node-ID 3 is <strong>device 50003</strong>.",
    formula_line="device instance = Node_Offset + Node-ID",
    formula=[("Node_Offset", "ProtoNode setting, default 50000 (BN_Node_Offset on Raypak)", "0-4194000"),
             ("Node-ID", "Boiler's Modbus address / node ID (AERCO: A-bank DIP switches)", "1-255")],
    where="Each boiler on the ProtoNode's RS-485 bus shows up as its own BACnet device; inside it the object "
          "instances are the same on every boiler. Pick the equipment below to see its objects.",
    example=dict(off=50000, node=3), example_text="Node_Offset 50000, Node-ID 3",
    inputs=[I("off", "Node_Offset", 0, 4194000, 50000), I("node", "Node-ID (Modbus address)", 1, 255, 1)],
    primary="node",
    variants=[V(rel.split("/")[1], label, rel, pn_group()) for rel, label in PROTONODE_FILES],
    faq=[("Why does every boiler have the same object numbers?",
          "The ProtoNode makes one BACnet device per boiler from the same profile, so the objects repeat and only "
          "the device instance changes. Point your BMS at the right device instance and the objects line up."),
         ("Hamilton's BDB-CDB shows up at 50032. Why?",
          "Its ProtoNode profile uses Node-ID 32, so the default device is 50000 + 32.")],
    files=[rel for rel, _ in PROTONODE_FILES],
))

CARRIER_FILES = [
    ("carrier/rtu-open-v5", "RTU Open v5"), ("carrier/wshp-open-v3", "WSHP Open v3"),
    ("carrier/fan-coil-open", "Fan Coil Open"), ("carrier/unit-ventilator-open", "Unit Ventilator Open"),
    ("carrier/w2w-open", "Water-to-water (W2W) Open"),
    ("carrier/48-50a-rooftop-upc-open", "48/50A rooftop UPC Open"), ("carrier/48-50p-rooftop-upc-open", "48/50P rooftop UPC Open"),
    ("carrier/30hx-upc-open", "30HX chiller UPC Open"), ("carrier/aquaforce-30xa-upc-open", "AquaForce 30XA UPC Open"),
    ("carrier/aquasnap-30rap-upc-open", "AquaSnap 30RAP UPC Open"), ("carrier/aquasnap-30rb-upc-open", "AquaSnap 30RB UPC Open"),
]

CALCS.append(dict(
    slug="carrier-open-controllers", brand="Carrier", hw="Open controllers (RTU Open, WSHP Open, UPC Open...)", kind="device",
    title="Carrier Open Controller BACnet Device Instance Calculator",
    desc="Work out the default BACnet device instance of Carrier RTU Open, WSHP Open, Fan Coil Open and UPC Open "
         "controllers: 16101 + address. Address 23 = 1610123.",
    lede="Carrier's Open controllers ship with a default device instance built from 16101 and the two-digit "
         "rotary switch (MAC) address. Enter the address to get it.",
    answer="Default device instance = <strong>16101 followed by the 2-digit rotary address</strong>, i.e. "
           "1610100 + address. Address 23 gives <strong>1610123</strong>; address 5 gives <strong>1610105</strong>. "
           "The object instances inside are the same on every controller of that type.",
    formula_line="device instance = 1610100 + rotary address",
    formula=[("16101", "Fixed prefix in Carrier's default (16 is Carrier's BACnet vendor ID)", "16101"),
             ("address", "Rotary switch (MS/TP MAC) address, two digits", "00-99")],
    where="The address is set on the controller's two rotary switches (tens and ones). This is the factory "
          "default; if the device instance was changed in the controller's setup, read it from a scan.",
    example=dict(mac=23), example_text="rotary address 23",
    inputs=[I("mac", "Rotary switch address", 0, 99, 1)],
    primary="mac",
    variants=[V(rel.split("/")[1], label, rel, [
        D("dev", "Controller device", ["mac"], ALL, lambda v: 1610100 + v["mac"],
          "function(v){return 1610100+v.mac;}",
          "function(d){if(d<1610100||d>1610199)return null;return{mac:d-1610100};}")])
        for rel, label in CARRIER_FILES],
    faq=[("Why is my Carrier controller's device instance 16101xx?",
          "Carrier's default joins 16101 and the two-digit rotary address, so address 20 shows up as device "
          "1610120. Change the rotary address and the default device instance changes with it.")],
    files=[rel for rel, _ in CARRIER_FILES],
))

# ---------------------------------------------------------------------------
# Repeating blocks inside one controller
# ---------------------------------------------------------------------------
def heatnet_groups():
    return [
        G("bv32", "Per-boiler status flags (1000 series, 32 per boiler)", ["n"], between(1000, 1032, ("BV",)),
          lambda p: p["instance"], lambda o, v: o + 32 * (v["n"] - 1),
          "function(o,v){return o+32*(v.n-1);}",
          "function(i){if(i<1000||i>=1512)return null;return{o:1000+(i-1000)%32,v:{n:Math.floor((i-1000)/32)+1}};}"),
        G("bv16", "Per-boiler inputs and faults (2000 / 3000 series, 16 per boiler)", ["n"],
          lambda p: p["type"] == "BV" and (2000 <= p["instance"] < 2016 or (3000 <= p["instance"] < 3016 and p["instance"] not in (3012, 3013))),
          lambda p: p["instance"], lambda o, v: o + 16 * (v["n"] - 1),
          "function(o,v){return o+16*(v.n-1);}",
          "function(i){var b=i>=3000&&i<3256?3000:(i>=2000&&i<2256?2000:0);if(!b)return null;return{o:b+(i-b)%16,v:{n:Math.floor((i-b)/16)+1}};}"),
        G("ai", "Per-boiler analog inputs (one per boiler)", ["n"],
          lambda p: p["type"] == "AI" and p["instance"] in (48, 64, 80, 96, 112, 128, 152),
          lambda p: p["instance"], lambda o, v: o + v["n"] - 1,
          "function(o,v){return o+v.n-1;}",
          "function(i){if(i>=48&&i<144)return{o:48+16*Math.floor((i-48)/16),v:{n:(i-48)%16+1}};if(i>=152&&i<168)return{o:152,v:{n:i-151}};return null;}"),
    ]


CALCS.append(dict(
    slug="heatnet-v3", brand="HeatNet", hw="V3 boiler control (Hydrotherm KN, RBI)", kind="object",
    title="HeatNet V3 Boiler BACnet Instance Calculator",
    desc="Calculate HeatNet V3 per-boiler BACnet instances for boilers 1-16 (Hydrotherm KN/KN+, RBI FIII/Fusion/"
         "CK). Boiler 4 alarm = BV 1098, supply temp = AI 83.",
    lede="Mestek's HeatNet V3 control prints its per-boiler objects once as Boiler##_ with a formula. Enter the "
         "boiler number to get that boiler's instances.",
    answer="Boiler n's status flags are <strong>1000-series base + (n - 1) x 32</strong>, its 2000 and 3000-series "
           "inputs and faults <strong>base + (n - 1) x 16</strong>, and its analog inputs <strong>boiler 1 instance "
           "+ n - 1</strong>. Boiler 4's alarm is 1002 + 96 = <strong>BV 1098</strong> and its supply temperature is "
           "80 + 3 = <strong>AI 83</strong>.",
    formula_line="BV 1000s: base + 32(n-1); BV 2000s/3000s: base + 16(n-1); AI: base + (n-1)",
    formula=[("n", "Boiler number: 1 is the master or stand-alone boiler, members 2-16", "1-16"),
             ("base", "The boiler 1 instance printed in the object list", "")],
    where="Boiler numbers are the HeatNet cascade addresses; boiler 1 is the master (the one the BMS is wired to). "
          "Plant-level objects (setpoints, header temperature, boiler counts) are fixed.",
    example=dict(n=4), example_text="boiler 4",
    inputs=[I("n", "Boiler number", 1, 16, 1)],
    primary="n",
    variants=[V("kn", "Hydrotherm KN / KN+ (HeatNet V3 v2.00)", "hydrotherm/kn-heatnet-v3", heatnet_groups()),
              V("kn2", "Hydrotherm KN-2 / KN-4 / Ray (HeatNet BACnet bridge)", "hydrotherm/kn2-kn4-ray-heatnet-bacnet-bridge", heatnet_groups()),
              V("knsx", "Hydrotherm KN-SX (HeatNet BACnet bridge)", "hydrotherm/knsx-heatnet-bacnet-bridge", heatnet_groups()),
              V("rbi", "RBI FIII / Fusion / CK (HeatNet V3 v1.00)", "rbi/heatnet-v3-fiii-fusion-ck", heatnet_groups())],
    faq=[("Do I connect the BMS to every boiler?",
          "No. The BMS talks to the master (boiler 1) HeatNet control, which reports the per-boiler objects for "
          "the whole cascade.")],
    files=["hydrotherm/kn-heatnet-v3", "hydrotherm/kn2-kn4-ray-heatnet-bacnet-bridge",
           "hydrotherm/knsx-heatnet-bacnet-bridge", "rbi/heatnet-v3-fiii-fusion-ck"],
))

CALCS.append(dict(
    slug="hamilton-bdb-cdb", brand="Hamilton Engineering", hw="BDB-CDB (ProtoNode)", kind="object",
    title="Hamilton BDB-CDB BACnet Instance Calculator (BCB1-8)",
    desc="Calculate Hamilton Engineering BDB-CDB BACnet instances for each BCB block 1-8: BCB1 instance + 9 x "
         "(n - 1). BCB3 working status = AI 49.",
    lede="The Hamilton BDB-CDB profile repeats a 9-object block for each BCB board. Enter the BCB number to get "
         "its instances.",
    answer="BCB n's objects are <strong>the BCB1 instance + 9 x (n - 1)</strong>. BCB1 starts at AI 28, so BCB3's "
           "working status (BCB1 AI 31) is 31 + 18 = <strong>AI 49</strong> and BCB8 runs AI/MI 91-99.",
    formula_line="instance = BCB1 instance + 9 x (BCB - 1)",
    formula=[("BCB", "BCB block number", "1-8"), ("BCB1 instance", "Printed instance for BCB1", "28-36")],
    where="The cascade objects (setpoints, cascade sensors, anomaly) are fixed. The whole BDB-CDB is one BACnet "
          "device on the ProtoNode, 50032 by default.",
    example=dict(n=3), example_text="BCB3",
    inputs=[I("n", "BCB number", 1, 8, 1)],
    primary="n",
    variants=[V("v", "BDB-CDB", "hamilton-engineering/bdb-cdb-protonode", [
        G("bcb", "BCB block", ["n"], between(28, 37), lambda p: p["instance"], lambda o, v: o + 9 * (v["n"] - 1),
          "function(o,v){return o+9*(v.n-1);}",
          "function(i){if(i<28||i>99)return null;return{o:28+(i-28)%9,v:{n:Math.floor((i-28)/9)+1}};}"),
    ])],
    faq=[("What is the BDB-CDB's device instance?",
          "Node_Offset (default 50000) + Node-ID 32 = 50032. The ProtoNode calculator covers that part.")],
    files=["hamilton-engineering/bdb-cdb-protonode"],
))


def titus_match(p):
    import re
    m = re.search(r"(\d+)$", p["name"])
    return bool(m) and m.group(1) == "1" and p["instance"] % 60 == 0


CALCS.append(dict(
    slug="titus-t3sq-mcu2", brand="Titus", hw="T3SQ Digital (MCU 2 gateway)", kind="object",
    title="Titus T3SQ MCU 2 BACnet Instance Calculator (Zones)",
    desc="Calculate Titus Digital T3SQ (MCU 2) BACnet instances for zones 1-60: block start + zone - 1. Zone 17 "
         "setpoint = AO 16, space temp = AV 16.",
    lede="The MCU 2 lays out each object type in blocks of 60, one instance per diffuser zone. Enter the zone to "
         "get every object for it.",
    answer="Zone instance = <strong>block start + zone - 1</strong>, with every block 60 long. Zone 17's setpoint "
           "is <strong>AO 16</strong>, its space temperature <strong>AV 16</strong> and its supply temperature "
           "AV 60 + 16 = <strong>AV 76</strong>.",
    formula_line="instance = block start + zone - 1",
    formula=[("block start", "First instance of that object type's block (0, 60, 120...)", "0-419"),
             ("zone", "MCU 2 zone number", "1-60")],
    where="Zones are set up on the MCU 2; zones that are not set up return no data. Only master-diffuser data is "
          "available.",
    example=dict(z=17), example_text="zone 17",
    inputs=[I("z", "Zone", 1, 60, 1)],
    primary="z",
    variants=[V("v", "MCU 2", "titus/t3sq-digital-mcu2", [
        G("zone", "Zone objects", ["z"], titus_match, lambda p: p["instance"], lambda o, v: o + v["z"] - 1,
          "function(o,v){return o+v.z-1;}",
          "function(i){return{o:i-i%60,v:{z:i%60+1}};}"),
    ])],
    drop_unmatched=True,
    faq=[("Why does the name end in 1?",
          "Names are shown for zone 1 as printed (Space Temp 1, Setpoint 1); on the MCU the number at the end "
          "matches the zone.")],
    files=["titus/t3sq-digital-mcu2"],
))

CALCS.append(dict(
    slug="verdant-vx4", brand="Verdant", hw="VX4 thermostats (Online Connection Kit)", kind="object",
    title="Verdant VX4 BACnet Instance Calculator (Room Numbers)",
    desc="Calculate Verdant VX4 thermostat BACnet instances from the room number: base + room number read as "
         "hex. Room 101 room temperature = AV 500257.",
    lede="Verdant VX4 rooms all get the same 15 objects at a base number plus the room number - but the room "
         "number is read as hexadecimal. This does the conversion for you.",
    answer="Instance = <strong>base + the room number read as hex</strong>. Room 101 is hex 0x101 = 257, so its "
           "room temperature (base 500000) is <strong>AV 500257</strong>; room 215 is 0x215 = 533, so its guest "
           "setpoint is <strong>AV 300533</strong>.",
    formula_line="instance = base + hex-to-decimal(room number)",
    formula=[("base", "Fixed base for each object (100000, 200000 ... 1500000)", "100000-1500000"),
             ("room", "Room number, read as a hexadecimal number", "e.g. 101 -> 257")],
    where="Use the room number exactly as it is set on the thermostat (for example 101 or 2A0) and read it as "
          "hex. Verdant's sheet gives no worked example, so confirm one room against a scan before mapping a "
          "whole building.",
    example=dict(room=0x101), example_text="room 101",
    inputs=[I("room", "Room number", 0, 99999, 0x101, "As set on the thermostat, e.g. 101", hexin=True)],
    primary="room",
    variants=[V("v", "VX4", "verdant/vx4-bacnet-integration", [
        G("room", "Room objects", ["room"], ALL, lambda p: p["instance"], lambda o, v: o + v["room"],
          "function(o,v){return o+v.room;}",
          "function(i){var b=Math.floor(i/100000)*100000;if(b<100000)return null;return{o:b,v:{room:i-b}};}"),
    ])],
    faq=[("Why is room 101 not instance 500101?",
          "Verdant adds the room number read as hexadecimal. 101 in hex is 1 x 256 + 0 x 16 + 1 = 257, so room "
          "101's room temperature is AV 500257, not 500101."),
         ("Can I write the cool or heat setpoint?",
          "No. Cool Setpoint and Heat Setpoint are read-only; the writable setpoint is Guest Setpoint (60-90 F).")],
    files=["verdant/vx4-bacnet-integration"],
))

CALCS.append(dict(
    slug="gps-air-gridset", brand="GPS Air", hw="GridSet BACnet gateway (Hub-4 Pro)", kind="object",
    title="GPS Air GridSet BACnet Instance Calculator (Ports)",
    desc="Calculate GPS Air GridSet (smartIAQ Hub-4 Pro) BACnet instances for ports 1-4: port x 1000 + offset. "
         "Port 3 CO2 = AI 3003. Free calculator.",
    lede="The smartIAQ Hub-4 Pro gives each of its four ports the same block of objects at port x 1000.",
    answer="Instance = <strong>port x 1000 + offset</strong>, and object names start with 'Port N'. Port 3's CO2 is "
           "<strong>AI 3003</strong> and its fan mode command is <strong>MV 3036</strong>.",
    formula_line="instance = port x 1000 + offset",
    formula=[("port", "Hub-4 Pro port the device is plugged into", "1-4"), ("offset", "Object offset", "1-61")],
    where="Objects are created when a device first reports on a port, and only for the sensors and actuators that "
          "device has.",
    example=dict(port=3), example_text="port 3",
    inputs=[I("port", "Port", 1, 4, 1)],
    primary="port",
    variants=[V("v", "GridSet", "gps-air/gridset-bacnet-gateway", [
        G("port", "Port objects", ["port"], ALL, lambda p: p["instance"] - 1000, lambda o, v: v["port"] * 1000 + o,
          "function(o,v){return v.port*1000+o;}",
          "function(i){var p=Math.floor(i/1000);if(p<1||p>4)return null;return{o:i%1000,v:{port:p}};}"),
    ])],
    faq=[("Why is a port missing objects?",
          "The gateway only creates objects for the sensors and actuators the connected device actually has, "
          "and only after it first reports.")],
    files=["gps-air/gridset-bacnet-gateway"],
))

CALCS.append(dict(
    slug="setra-spm", brand="Setra", hw="Setra Power Meter (SPM) load device", kind="object",
    title="Setra SPM BACnet Instance Calculator (CT 1-3)",
    desc="Calculate Setra Power Meter (SPM) BACnet instances for CT 1-3 on a load device: CT 1 instance + 30 per "
         "CT. CT 2 real power = AI 62. Free calculator.",
    lede="Each Setra SPM load device prints only the CT 1 block and reserves the same block for CT 2 and CT 3, "
         "30 instances further on.",
    answer="CT n's objects are <strong>the CT 1 instance + 30 x (n - 1)</strong>: CT 1 is AI 30-52, CT 2 AI 60-82, "
           "CT 3 AI 90-112. CT 2's real power is <strong>AI 62</strong>; its polarity correction is <strong>BV 2</strong>.",
    formula_line="instance = CT 1 instance + 30 x (CT - 1); polarity = BV CT",
    formula=[("CT", "Current transformer number on the load", "1-3"), ("CT 1 instance", "Printed CT 1 instance", "30-52")],
    where="Load-level totals (voltage, power, energy) are fixed objects on each load device.",
    example=dict(ct=2), example_text="CT 2",
    inputs=[I("ct", "CT number", 1, 3, 1)],
    primary="ct",
    variants=[V("v", "SPM load device", "setra/setra-power-meter-spm-load-device", [
        G("ct", "CT block", ["ct"], between(30, 53, ("AI",)), lambda p: p["instance"], lambda o, v: o + 30 * (v["ct"] - 1),
          "function(o,v){return o+30*(v.ct-1);}",
          "function(i){if(i<30||i>112||(i-30)%30>22)return null;return{o:30+(i-30)%30,v:{ct:Math.floor((i-30)/30)+1}};}"),
        G("pol", "CT polarity correction", ["ct"], lambda p: p["type"] == "BV" and p["instance"] == 1,
          lambda p: 0, lambda o, v: v["ct"],
          "function(o,v){return v.ct;}",
          "function(i){if(i<1||i>3)return null;return{o:0,v:{ct:i}};}"),
    ])],
    faq=[("Why does the meter show more than one BACnet device?",
          "The SPM is a root device for the voltage inputs plus one load device per configured load. The CT "
          "blocks are inside each load device.")],
    files=["setra/setra-power-meter-spm-load-device"],
))


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def row_of(p, inst=None):
    return [p["type"], p["instance"] if inst is None else inst, p.get("name") or "",
            p.get("description") or "", p.get("access") or "R"]


def assemble(c):
    """Split each variant's points into groups (by match) and fixed objects."""
    out = []
    for var in c["variants"]:
        pairs = var.get("multi") or [(var["rel"], g) for g in var["groups"]]
        gs, fixed, seen_rel = [], [], {}
        for rel, g in pairs:
            d = seen_rel.get(rel) or load(rel)
            seen_rel[rel] = d
            pts = [p for p in d["points"] if g["match"](p) and (c["kind"] == "device" or p["type"] != "DEV")]
            if c["kind"] == "device":
                pts = [p for p in pts if p["type"] != "DEV"]
            gs.append(dict(g=g, pts=[row_of(p, g["off"](p)) for p in pts], rel=rel))
        if not c.get("drop_unmatched"):
            for rel, d in seen_rel.items():
                claimed = {id(p) for rel2, g in pairs if rel2 == rel for p in d["points"] if g["match"](p)}
                for p in d["points"]:
                    if id(p) in claimed or p["type"] == "DEV":
                        continue
                    if c["kind"] == "device":
                        continue
                    fixed.append(row_of(p))
        out.append(dict(id=var["id"], label=var["label"], groups=gs, fixed=fixed,
                        rel=var.get("rel") or pairs[0][0], model=seen_rel[pairs[0][0]]))
    return out


def js_data(c, vs):
    data = {
        "kind": c["kind"], "primary": c["primary"],
        "inputs": [{k: i[k] for k in ("k", "label", "min", "max", "default", "hint", "hex")} for i in c["inputs"]],
        "variants": [{
            "id": v["id"], "label": v["label"], "href": lib_href(v["rel"]),
            "fixed": v["fixed"],
            "groups": [{"id": x["g"]["id"], "label": x["g"]["label"], "uses": x["g"]["uses"],
                        "note": x["g"]["note"] or "", "pts": x["pts"]} for x in v["groups"]],
        } for v in vs],
    }
    funcs = {}
    for v in vs:
        for x in v["groups"]:
            g = x["g"]
            if g["id"] in funcs:
                continue
            js = ["%s:%s" % (k, s) for k, s in g["js"].items() if s]
            funcs[g["id"]] = "{" + ",".join(js) + "}"
    f = "{" + ",".join("%s:%s" % (json.dumps(k), s) for k, s in funcs.items()) + "}"
    return ("<script>window.CALC=%s;window.CALCF=%s;</script>"
            % (json.dumps(data, ensure_ascii=False).replace("</", "<\\/"), f))


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

CALC_CSS = """
<style>
.calc{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.2rem;margin:1.6rem 0}
.calc h2{margin:.2rem 0 .9rem}
.cin{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.8rem 1rem}
.cin label{display:block;font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:.3rem}
.cin input,.cin select,.crev input,.crev select,.crange input{width:100%;font:inherit;font-family:"IBM Plex Mono",monospace;color:var(--fg);background:var(--code);border:1px solid var(--line);border-radius:9px;padding:.6rem .7rem}
.cin .hint{display:block;color:var(--mut);font-size:.78rem;margin-top:.25rem}
.cin .wide{grid-column:1/-1}
#c-out h3{margin:1.5rem 0 .3rem;font-size:1.05rem}
.cuse{color:var(--mut);font-size:.86rem;margin:0 0 .4rem}
.cdev{font-size:1.05rem;margin:.2rem 0 .5rem}.cdev b{font-family:"IBM Plex Mono",monospace;color:var(--accent);font-size:1.25rem}
.cerr{color:#ffb4a8;font-weight:600}
.cskip{color:#ffb4a8;font-size:.8rem}
.cbar{display:flex;flex-wrap:wrap;gap:.6rem;align-items:flex-end;margin:1.2rem 0 .2rem}
.cbar button,.crev button{font:inherit;font-weight:700;font-size:.9rem;padding:.6rem 1rem;border-radius:9px;border:1px solid var(--accent);background:var(--accent);color:var(--ink);cursor:pointer}
.cbar button.sec,.crev button.sec{background:var(--panel2);color:var(--fg);border-color:var(--line)}
.crange{display:flex;gap:.4rem;align-items:center;color:var(--mut);font-size:.86rem}.crange input{width:5.5rem}
.crev{border-top:1px solid var(--line);margin-top:1.4rem;padding-top:1rem}
.crev .row{display:grid;grid-template-columns:minmax(120px,160px) 1fr auto;gap:.6rem;align-items:end}
.crev .row.dev{grid-template-columns:1fr auto}
.cres{margin:.8rem 0 0;padding:0;list-style:none}
.cres li{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:.65rem .8rem;margin:.45rem 0}
.cres .mono{color:var(--accent);font-weight:600}
.cres button{font:inherit;font-size:.8rem;margin-left:.5rem;padding:.15rem .55rem;border-radius:7px;border:1px solid var(--line);background:var(--panel);color:var(--fg);cursor:pointer}
table.fx{border-collapse:collapse;width:100%;font-size:.92rem;margin:.6rem 0 1.2rem}
table.fx th,table.fx td{text-align:left;padding:.5rem .7rem;border-bottom:1px solid var(--line);vertical-align:top}
table.fx th{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
table.fx td.m{font-family:"IBM Plex Mono",monospace;white-space:nowrap}
.formula{font-family:"IBM Plex Mono",monospace;background:var(--code);border:1px solid var(--line);border-radius:10px;padding:.8rem 1rem;overflow-x:auto;white-space:nowrap}
.calclist{list-style:none;padding:0;margin:.6rem 0 1.4rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:.8rem}
.calclist a{display:block;height:100%;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:.9rem 1rem;color:var(--fg);text-decoration:none}
.calclist a:hover{border-color:var(--accent)}
.calclist b{display:block;font-family:"Archivo",sans-serif;font-size:1.02rem;margin-bottom:.25rem}
.calclist span{display:block;color:var(--mut);font-size:.88rem}
.calclist code{display:block;margin-top:.45rem;font-family:"IBM Plex Mono",monospace;font-size:.76rem;color:#cfe1f2;white-space:normal}
@media (max-width:640px){.crev .row{grid-template-columns:1fr}.calc{padding:.9rem}}
</style>"""

ENGINE = r"""<script>
(function(){
var C=window.CALC,F=window.CALCF;if(!C)return;
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
var ACC={R:'Read',W:'Write',C:'Command'};
var INP={};C.inputs.forEach(function(i){INP[i.k]=i;});
function fmt(k,n){var i=INP[k];return i&&i.hex?n.toString(16).toUpperCase():String(n);}
function vi(){var s=$('ci-variant');return s?s.selectedIndex:0;}
function readV(){var v={},bad=[];C.inputs.forEach(function(i){
  var s=($('ci-'+i.k).value||'').trim(),n;
  if(i.hex){if(!/^[0-9a-fA-F]{1,5}$/.test(s)){bad.push(i.label);return;}n=parseInt(s,16);}
  else{if(!/^\d+$/.test(s)){bad.push(i.label);return;}n=parseInt(s,10);}
  if(n<i.min||n>i.max){bad.push(i.label+' ('+fmt(i.k,i.min)+'-'+fmt(i.k,i.max)+')');return;}
  v[i.k]=n;});window.CALCV=v;return{v:v,bad:bad};}
function uses(g,v){return g.uses.map(function(k){return INP[k].label+' '+fmt(k,v[k]);}).join(', ');}
function rowsOf(g,v){var f=F[g.id];return g.pts.map(function(p){
  return [p[0],C.kind==='device'?p[1]:f.enc(p[1],v),p[2],p[3],p[4],(f.skip?f.skip(p[1],v):'')];});}
function table(rs){var h='<div class="tablewrap"><table class="pts"><thead><tr><th>Type</th><th>Instance</th><th>Object name (as printed)</th><th>What it is</th><th>Access</th></tr></thead><tbody>';
  rs.forEach(function(r){h+='<tr><td class="t">'+esc(r[0])+'</td><td class="i">'+esc(r[1])+'</td><td class="n">'+esc(r[2])+'</td><td>'+esc(r[3])+(r[5]?' <span class="cskip">'+esc(r[5])+'</span>':'')+'</td><td>'+esc(ACC[r[4]]||r[4])+'</td></tr>';});
  return h+'</tbody></table></div>';}
function devOf(g,v){var f=F[g.id];return f.dev?f.dev(v):null;}
function render(){var r=readV(),out=$('c-out');
  if(r.bad.length){out.innerHTML='<p class="cerr">Check: '+esc(r.bad.join(', '))+'</p>';return;}
  var V=C.variants[vi()],v=r.v,h='';
  V.groups.forEach(function(g){var f=F[g.id];
    h+='<h3>'+esc(g.label)+'</h3>';
    if(g.uses.length)h+='<p class="cuse">For '+esc(uses(g,v))+(f.info?' &middot; '+esc(f.info(v)):'')+'</p>';
    if(C.kind==='device'){var d=devOf(g,v);h+='<p class="cdev">Device instance: <b>'+(d===null?'not documented':esc(d))+'</b></p>';}
    if(g.note)h+='<p class="count">'+esc(g.note)+'</p>';
    if(g.pts.length)h+=table(rowsOf(g,v));});
  if(V.fixed.length)h+='<h3>Fixed objects (the same whatever unit you enter)</h3>'+table(V.fixed.map(function(p){return p.concat(['']);}));
  h+='<p class="count">From the <a href="'+esc(V.href)+'">'+esc(V.label)+' points list</a>. Check against a scan of the live device before you map or write.</p>';
  out.innerHTML=h;
  try{var u=new URL(location.href);C.inputs.forEach(function(i){u.searchParams.set(i.k,fmt(i.k,v[i.k]));});
    if($('ci-variant'))u.searchParams.set('model',V.id);history.replaceState(null,'',u.pathname+'?'+u.searchParams.toString());}catch(e){}}
function csvq(s){s=String(s==null?'':s);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;}
function save(name,lines){var b=new Blob([lines.map(function(l){return l.map(csvq).join(',');}).join('\r\n')+'\r\n'],{type:'text/csv'});
  var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);}
function linesFor(V,v,onlyPrimary,head){var L=[];V.groups.forEach(function(g){
  if(onlyPrimary&&g.uses.indexOf(C.primary)<0)return;
  var who=uses(g,v);
  if(C.kind==='device'){var d=devOf(g,v);
    if(onlyPrimary){L.push([g.label,who,d===null?'':d]);return;}
    rowsOf(g,v).forEach(function(r){L.push([g.label,who,d===null?'':d,r[0],r[1],r[2],r[3],ACC[r[4]]||r[4]]);});}
  else rowsOf(g,v).forEach(function(r){L.push([g.label,who,r[0],r[1],r[2],r[3],ACC[r[4]]||r[4],r[5]]);});});
  if(!onlyPrimary&&C.kind!=='device')V.fixed.forEach(function(p){L.push(['Fixed','',p[0],p[1],p[2],p[3],ACC[p[4]]||p[4],'']);});
  return L;}
var HEAD_O=['Block','Unit','Type','Instance','Object name','Description','Access','Note'];
var HEAD_D=['Unit type','Unit','Device instance','Type','Instance','Object name','Description','Access'];
$('c-csv').addEventListener('click',function(){var r=readV();if(r.bad.length){render();return;}
  var V=C.variants[vi()];save(document.body.getAttribute('data-slug')+'-unit.csv',[C.kind==='device'?HEAD_D:HEAD_O].concat(linesFor(V,r.v,false)));});
$('c-rcsv').addEventListener('click',function(){var r=readV();if(r.bad.length){render();return;}
  var P=INP[C.primary],pf=function(id){var s=($(id).value||'').trim();return P.hex?parseInt(s,16):parseInt(s,10);};
  var a=pf('cr-from'),b=pf('cr-to');if(isNaN(a)||isNaN(b)||a>b||a<P.min||b>P.max||b-a>4096){$('cr-msg').textContent='Enter a range inside '+fmt(C.primary,P.min)+'-'+fmt(C.primary,P.max)+'.';return;}
  $('cr-msg').textContent='';var V=C.variants[vi()],L=[C.kind==='device'?['Unit type','Unit','Device instance']:HEAD_O];
  for(var n=a;n<=b;n++){var v={};for(var k in r.v)v[k]=r.v[k];v[C.primary]=n;window.CALCV=v;L=L.concat(linesFor(V,v,true));}
  save(document.body.getAttribute('data-slug')+'-'+fmt(C.primary,a)+'-'+fmt(C.primary,b)+'.csv',L);});
function inRange(v){for(var k in v){var i=INP[k];if(i&&(v[k]<i.min||v[k]>i.max))return false;}return true;}
function fill(vi2,v){var s=$('ci-variant');if(s)s.selectedIndex=vi2;for(var k in v){if(INP[k])$('ci-'+k).value=fmt(k,v[k]);}render();
  $('c-out').scrollIntoView({behavior:'smooth',block:'start'});}
var HITS=[];
function lookup(){var res=$('cr-res'),raw=($('cr-i').value||'').trim();HITS=[];
  if(!/^\d+$/.test(raw)){res.innerHTML='<li>Enter a whole number.</li>';return;}
  var i=parseInt(raw,10),t=$('cr-t')?$('cr-t').value:'',h='';readV();
  C.variants.forEach(function(V,vx){
    var lab=C.variants.length>1?' ('+esc(V.label)+')':'';
    V.groups.forEach(function(g){var f=F[g.id];
      if(C.kind==='device'){if(!f.ddec)return;var dv=f.ddec(i);if(!dv||!inRange(dv))return;
        if(C.variants.length>1&&vx!==vi())return;
        HITS.push([vx,dv]);h+='<li><span class="mono">Device '+i+'</span> = '+esc(g.label)+lab+': '+esc(uses(g,dv))+'<button type="button" data-h="'+(HITS.length-1)+'">Show its objects</button></li>';return;}
      var d=f.dec(i);if(!d||!inRange(d.v))return;
      g.pts.forEach(function(p){if(p[0]!==t||p[1]!==d.o)return;
        HITS.push([vx,d.v]);h+='<li><span class="mono">'+esc(t)+' '+i+'</span> = '+esc(p[2])+' &mdash; '+esc(p[3])+'<br><span class="count">'+esc(g.label)+lab+', '+esc(uses(g,d.v))+'</span><button type="button" data-h="'+(HITS.length-1)+'">Show this unit</button></li>';});});
    if(C.kind!=='device')V.fixed.forEach(function(p){if(p[0]===t&&p[1]===i)h+='<li><span class="mono">'+esc(t)+' '+i+'</span> = '+esc(p[2])+' &mdash; '+esc(p[3])+'<br><span class="count">Fixed object'+lab+'</span></li>';});});
  res.innerHTML=h||'<li>No object in this list decodes to '+(C.kind==='device'?'device '+i:esc(t)+' '+i)+'. Check the type, the number, or the model picked above.</li>';}
$('cr-go').addEventListener('click',lookup);$('cr-i').addEventListener('keydown',function(e){if(e.key==='Enter')lookup();});
$('cr-res').addEventListener('click',function(e){var b=e.target.closest('button[data-h]');if(!b)return;var x=HITS[+b.getAttribute('data-h')];fill(x[0],x[1]);});
try{var P=new URLSearchParams(location.search);C.inputs.forEach(function(i){if(P.has(i.k))$('ci-'+i.k).value=P.get(i.k);});
  var s=$('ci-variant');if(s&&P.get('model')){C.variants.forEach(function(V,x){if(V.id===P.get('model'))s.selectedIndex=x;});}}catch(e){}
C.inputs.forEach(function(i){$('ci-'+i.k).addEventListener('input',render);});
if($('ci-variant'))$('ci-variant').addEventListener('change',render);
render();
})();
</script>"""


def calc_path(c):
    return ROOT + "/" + c["slug"] + ".html"


def hub_path():
    return ROOT + "/index.html"


def full_title(c):
    return "%s %s" % (c["brand"], c["hw"])


def example_html(c, vs):
    """Static worked example (crawlers and no-JS readers see real numbers)."""
    v = c["example"]
    var = vs[0]
    rows = []
    for x in var["groups"]:
        g = x["g"]
        if c["kind"] == "device":
            d = g["dev"](v) if g.get("dev") else None
            rows.append("<tr><td>%s</td><td class=\"m\">%s</td><td>%s</td></tr>" % (
                esc(g["label"]), "&mdash;" if d is None else d,
                esc(", ".join("%s %s" % (next(i["label"] for i in c["inputs"] if i["k"] == k),
                                         format(v[k], "X") if next(i for i in c["inputs"] if i["k"] == k)["hex"] else v[k])
                              for k in g["uses"]))))
        else:
            for p in x["pts"][:6]:
                rows.append("<tr><td class=\"m\">%s %s</td><td>%s</td><td>%s</td></tr>" % (
                    esc(p[0]), g["enc"](p[1], v), esc(p[2]), esc(p[3])))
    if c["kind"] == "device":
        head = "<tr><th>Unit type</th><th>Device instance</th><th>For</th></tr>"
    else:
        head = "<tr><th>Object</th><th>Name (as printed)</th><th>What it is</th></tr>"
    return ('<h2>Worked example: %s</h2><p>The first objects for %s on the %s, worked out with the formula '
            'above%s:</p><div class="tablewrap"><table class="fx"><thead>%s</thead><tbody>%s</tbody></table></div>'
            % (esc(c["example_text"]), esc(c["example_text"]), esc(var["label"]),
               "" if len(vs) == 1 else " (" + esc(var["label"]) + ")", head, "".join(rows)))


def calc_body(c, vs):
    inputs = "".join(
        '<div><label for="ci-%(k)s">%(label)s</label><input id="ci-%(k)s" inputmode="%(mode)s" '
        'autocomplete="off" value="%(val)s">%(hint)s</div>'
        % {"k": i["k"], "label": esc(i["label"]), "mode": "text" if i["hex"] else "numeric",
           "val": format(i["default"], "X") if i["hex"] else i["default"],
           "hint": '<span class="hint">%s</span>' % esc(i["hint"]) if i["hint"] else
           '<span class="hint">%s-%s</span>' % (
               format(i["min"], "X") if i["hex"] else i["min"], format(i["max"], "X") if i["hex"] else i["max"])}
        for i in c["inputs"])
    variant = ""
    if len(vs) > 1:
        variant = ('<div class="wide"><label for="ci-variant">Equipment / model</label><select id="ci-variant">%s'
                   '</select></div>' % "".join('<option>%s</option>' % esc(v["label"]) for v in vs))
    types = sorted({p[0] for v in vs for x in v["groups"] for p in x["pts"]} |
                   {p[0] for v in vs for p in v["fixed"]})
    prim = next(i for i in c["inputs"] if i["k"] == c["primary"])
    pfmt = (lambda n: format(n, "X")) if prim["hex"] else str
    if c["kind"] == "device":
        rev = ('<div class="row dev"><div><label for="cr-i">Device instance</label><input id="cr-i" inputmode="numeric" '
               'placeholder="e.g. %s"></div><button type="button" id="cr-go">Decode</button></div>'
               % (lambda x: x["g"]["dev"](c["example"]) if x["g"].get("dev") else "")(vs[0]["groups"][0]))
        rev_h = "Which unit is this device?"
    else:
        rev = ('<div class="row"><div><label for="cr-t">Type</label><select id="cr-t">%s</select></div>'
               '<div><label for="cr-i">Instance</label><input id="cr-i" inputmode="numeric" placeholder="e.g. 100205"></div>'
               '<button type="button" id="cr-go">Decode</button></div>'
               % "".join('<option%s>%s</option>' % (' selected' if t == vs[0]["groups"][0]["pts"][0][0] else "", t)
                         for t in types))
        rev_h = "Which unit does this instance belong to?"
    return """
<section class="calc" aria-labelledby="calc-h">
<h2 id="calc-h">%(h)s calculator</h2>
<div class="cin">%(variant)s%(inputs)s</div>
<div class="cbar"><button type="button" id="c-csv">Download this unit (CSV)</button>
<span class="crange">or a range of %(plabel)s <input id="cr-from" value="%(pmin)s" aria-label="From"> to <input id="cr-to" value="%(pmax)s" aria-label="To"></span>
<button type="button" class="sec" id="c-rcsv">Download range (CSV)</button></div>
<p class="count" id="cr-msg" aria-live="polite"></p>
<div id="c-out" aria-live="polite"><p class="count">The calculator needs JavaScript. The formula and a worked example are below.</p></div>
<div class="crev"><h3>%(rev_h)s</h3>%(rev)s<ul class="cres" id="cr-res" aria-live="polite"></ul></div>
</section>""" % {"h": esc(c["brand"]), "variant": variant, "inputs": inputs, "plabel": esc(prim["label"].lower()),
                 "pmin": pfmt(prim["default"]), "pmax": pfmt(min(prim["max"], prim["default"] + 15)),
                 "rev_h": rev_h, "rev": rev}


def related(c):
    same = [x for x in CALCS if x is not c and x["brand"] == c["brand"]]
    grp = "vrf" if c in VRF else "plant"
    other = [x for x in CALCS if x is not c and x not in same and ((x in VRF) == (grp == "vrf"))]
    return (same + other)[:8]


def calc_page(c):
    vs = assemble(c)
    relpath = calc_path(c)
    url = PL.clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet instance calculators", "/" + hub_path()),
              ("%s %s" % (c["brand"], c["hw"].split(" (")[0]), None)]
    libs = []
    for rel in c["files"]:
        d = load(rel)
        libs.append('<li><a href="%s">%s %s BACnet points list</a> <span class="count">(%d objects)</span></li>'
                    % (lib_href(rel), esc(d["manufacturer"]), esc(d["model"]), len(d["points"])))
    m0 = vs[0]["model"]
    src = m0["source"]
    formula = "".join('<tr><td class="m">%s</td><td>%s</td><td class="m">%s</td></tr>' % (esc(a), esc(b), esc(r))
                      for a, b, r in c["formula"])
    faq = [("How do I work out a %s instance number?" % c["brand"],
            PL.html.unescape(_strip(c["answer"])))] + c["faq"] + [
        ("Is this %s calculator official?" % c["brand"],
         "No. It applies the formula printed in %s's own documentation to the points list in our library. "
         "Confirm the numbers against a scan of the live device before you map or write anything." % c["brand"])]
    faq_html = '<h2>Questions</h2><div class="faq">%s</div>' % "".join(
        "<details%s><summary>%s</summary><p>%s</p></details>" % (" open" if i == 0 else "", esc(q), esc(a))
        for i, (q, a) in enumerate(faq))
    rel_html = '<h2>More instance calculators</h2><ul class="calclist">%s</ul>' % "".join(card(x) for x in related(c))
    h1 = ('<p class="eyebrow">BACnet instance calculator &middot; %s</p>'
          '<h1><span class="mfr">%s</span> %s</h1>'
          '<p class="updated">Free browser tool &middot; nothing is uploaded &middot; %s</p>'
          % (esc(c["hw"]), esc(c["brand"]), esc(h1_rest(c)),
             PL.human_date(PUBLISHED)))
    body = """
<p class="lede">%(lede)s</p>
<div class="answer"><b>Short answer</b><p>%(answer)s</p></div>
%(calc)s
<h2>How the numbers are built</h2>
<p class="formula">%(fline)s</p>
<div class="tablewrap"><table class="fx"><thead><tr><th>Part</th><th>Meaning</th><th>Range</th></tr></thead><tbody>%(formula)s</tbody></table></div>
<p>%(where)s</p>
%(example)s
<h2>Source</h2>
<ul class="notes">%(libs)s</ul>
<p class="count">Formula and objects from %(srcline)s
(<a href="%(src)s" rel="nofollow noopener" target="_blank">manufacturer document &#8599;</a>), re-typed in our
points list. Object names are shown as printed.</p>
<div class="callout"><p><strong>Check it against the live device.</strong> The calculator applies the formula from
the manufacturer&rsquo;s documentation; the gateway in front of you may expose fewer objects or use other numbers after
a firmware change. <a href="/index.html">Easy BACnet</a> scans a network for BACnet IP devices from an Android phone and
reads every object on them &mdash; a quick way to confirm one unit before you map a whole building.</p></div>
%(faq)s
%(rel)s
""" % {"lede": esc(c["lede"]), "answer": c["answer"], "calc": calc_body(c, vs), "fline": esc(c["formula_line"]),
           "formula": formula, "where": esc(c["where"]), "example": example_html(c, vs), "libs": "".join(libs),
           "srcline": PL.source_line(m0), "src": esc(src["url"]), "faq": faq_html, "rel": rel_html}
    body = CALC_CSS + body + js_data(c, vs) + ENGINE
    app = {"@type": "WebApplication", "@id": url + "#app", "name": c["title"], "url": url,
           "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any (web browser)",
           "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
           "description": c["desc"], "publisher": {"@id": PL.ORG["@id"]},
           "about": {"@type": "Product", "name": full_title(c), "brand": {"@type": "Brand", "name": c["brand"]}},
           "datePublished": PUBLISHED, "dateModified": PUBLISHED}
    faq_ld = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    page_ld = {"@type": "WebPage", "@id": url, "url": url, "name": c["title"], "description": c["desc"],
               "isPartOf": {"@id": PL.BASE_URL + "/#site"}, "mainEntity": {"@id": url + "#app"},
               "dateModified": PUBLISHED, "publisher": {"@id": PL.ORG["@id"]}}
    jsonld = PL.graph(PL.ORG, page_ld, app, faq_ld, PL.breadcrumb_ld(crumbs, url))
    html_out = PL.shell(relpath, c["title"], c["desc"], h1, body, jsonld, crumbs)
    return nav_on(html_out).replace("<body>", '<body data-slug="%s">' % c["slug"], 1)


def _strip(s):
    import re
    return re.sub(r"<[^>]+>", "", s)


def h1_rest(c):
    """The page title without the brand, which the H1 shows separately in accent colour."""
    t = c["title"]
    for pref in (c["brand"], c["brand"].split()[0]):
        if t.startswith(pref + " "):
            return t[len(pref) + 1:]
    return t


def nav_on(html_out):
    return (html_out.replace('class="on">Points lists', '>Points lists', 1)
            .replace('>Calculators</a>', ' class="on">Calculators</a>', 1))


def card(c):
    return ('<li><a href="/%s"><b>%s %s</b><span>%s</span><code>%s</code></a></li>'
            % (calc_path(c), esc(c["brand"]), esc(c["hw"]), esc(c["lede"].split(". ")[0].rstrip(".") + "."),
               esc(c["formula_line"])))


VRF_SLUGS = {"fujitsu", "lg", "mitsubishi-electric-bac-hd150", "mitsubishi-electric-ae-c400-ew-c50",
             "mitsubishi-electric-pac-yg31cda", "mitsubishi-electric-procon-bac-ip-50", "daikin-dms502b71",
             "toshiba-bms-ifbn1281u", "gree", "coolautomation-coolmasternet", "intesis-hitachi-inbachit",
             "intesis-panasonic-inbacpan", "intesis-samsung-inbacsam", "samsung-mim-b17bn",
             "lennox-vrf-bacnet-gateway", "sinclair-gw-bac", "systemair-sys-gw-ims-bac"}
VRF = [c for c in CALCS if c["slug"] in VRF_SLUGS]

SECTIONS = [
    ("VRF and split AC: the address is inside the object instance",
     [c for c in VRF if c["kind"] == "object"]),
    ("VRF: every unit is its own BACnet device",
     [c for c in VRF if c["kind"] == "device"]),
    ("Boilers, zones and meters",
     [c for c in CALCS if c not in VRF]),
]

HUB_TITLE = "BACnet Instance Number Calculators by Brand | Easy BACnet"
HUB_DESC = ("Free BACnet instance calculators for Fujitsu, Mitsubishi Electric, Daikin, Samsung, Toshiba, LG "
            "and more: enter a unit address, get every object number.")


def hub_page():
    relpath = hub_path()
    url = PL.clean(relpath)
    crumbs = [("Home", "/index.html"), ("BACnet instance calculators", None)]
    secs = "".join('<h2>%s</h2><ul class="calclist">%s</ul>' % (esc(h), "".join(card(c) for c in cs))
                   for h, cs in SECTIONS if cs)
    h1 = ('<p class="eyebrow">Free tools &middot; %d calculators</p><h1>BACnet instance <span class="mfr">calculators</span></h1>'
          '<p class="updated">Updated %s</p>' % (len(CALCS), PL.human_date(PUBLISHED)))
    body = """
<p class="lede">Many gateways number their BACnet objects with a formula: the unit's address is built into every
instance number, or into the device instance of a virtual device per unit. The points list prints unit 1 and
leaves the arithmetic to you. These calculators do it for each brand or model.</p>
<div class="answer"><b>Short answer</b><p>Pick your brand or gateway below, enter the unit address the way the
gateway or its setup tool shows it, and you get that unit's full object list with real instance numbers. You can
download one unit or a range of units as CSV, or paste a mystery instance to find out which unit and point it is.
Where the whole brand uses one scheme there is one calculator for the brand; where the scheme belongs to one
piece of hardware, the calculator is for that hardware.</p></div>
%(secs)s
<div class="callout"><p><strong>Where the formulas come from.</strong> Every formula and object comes from a
manufacturer document in our <a href="/bacnet-points-lists/index.html">BACnet points-list library</a>, linked on each
page. Confirm one unit against a scan of the live device before you map a whole site &mdash;
<a href="/index.html">Easy BACnet</a> does that from an Android phone. Need to split a raw 32-bit Object Identifier
instead? Use the <a href="/bacnet-object-id-decoder.html">Object Identifier decoder</a>.</p></div>
""" % {"secs": secs}
    body = CALC_CSS + body
    items = [{"@type": "ListItem", "position": n + 1, "url": PL.clean(calc_path(c)), "name": c["title"]}
             for n, c in enumerate(CALCS)]
    page_ld = {"@type": "CollectionPage", "@id": url, "url": url, "name": HUB_TITLE, "description": HUB_DESC,
               "isPartOf": {"@id": PL.BASE_URL + "/#site"}, "publisher": {"@id": PL.ORG["@id"]},
               "mainEntity": {"@type": "ItemList", "itemListElement": items}, "dateModified": PUBLISHED}
    jsonld = PL.graph(PL.ORG, page_ld, PL.breadcrumb_ld(crumbs, url))
    return nav_on(PL.shell(relpath, HUB_TITLE, HUB_DESC, h1, body, jsonld, crumbs))


def links():
    """{library rel path: [(calculator url path, label)]} for the points-list pages."""
    out = {}
    for c in CALCS:
        for rel in c["files"]:
            out.setdefault(rel, []).append(("/" + calc_path(c), "%s %s" % (c["brand"], c["hw"])))
    return out


def build(write):
    out_dir = os.path.join(HERE, ROOT)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    paths = [hub_path()]
    write(hub_path(), hub_page())
    for c in CALCS:
        write(calc_path(c), calc_page(c))
        paths.append(calc_path(c))
    for p in paths:
        PL.LASTMOD[p] = PUBLISHED
    llms = ["", "## BACnet instance calculators (unit address -> every object instance)",
            "- All calculators: %s" % PL.clean(hub_path())]
    for c in CALCS:
        llms.append("- %s (%s): %s" % (c["title"], c["formula_line"], PL.clean(calc_path(c))))
    return paths, llms
