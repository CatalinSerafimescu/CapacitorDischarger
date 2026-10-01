"""Generate CapacitorDischarger.kicad_sch (flat, single sheet) from a part/net list.

Connectivity is defined by net labels on pin stubs (and by pins that touch,
for the resistor chains), so the netlist is exact by construction; check it
with check_kicad.py (kicad-cli netlist + ERC, compared to the SPICE netlist).

Run with KiCad's python or any python 3:  python gen_kicad_sch.py
"""
import math
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from bom import BOM  # noqa: E402

KICAD_SYMS = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
PROJECT = "CapacitorDischarger"
ROOT_UUID = "c3000000-0003-0003-0003-000000000003"
NS = uuid.UUID(ROOT_UUID)
G = 1.27  # schematic grid

# ── Footprints ──────────────────────────────────────────────────────────────
FP = {
    "R0207":   "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "R3W":     "Resistor_THT:R_Axial_DIN0516_L15.5mm_D5.0mm_P20.32mm_Horizontal",
    "R_slow":  "CapDis:R_Axial_Ohmite_45F_5W",
    "R_fast":  "CapDis:R_Axial_Ohmite_27J_7W",
    "DO41":    "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "DO35":    "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
    "TF":      "CapDis:ThermalCutoff_SEFUSE_SF_Axial",
    "C":       "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "TO92":    "Package_TO_SOT_THT:TO-92_Inline_Wide",
    "TO220":   "CapDis:TO-220-3_Vertical_LegsSpread_P5.08mm",
    "LED":     "LED_THT:LED_D5.0mm",
    "FUSE":    "CapDis:Fuseholder_Clip-10.3x38mm_Schurter_CSO_0751.0506",
    "MKDS":    "CapDis:TerminalBlock_Phoenix_MKDS-5-2-9.5_1x02_P9.52mm",
    "HDR2":    "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "MH":      "MountingHole:MountingHole_3.2mm_M3",
    "": "",
}


def u(*key):
    return str(uuid.uuid5(NS, "/".join(map(str, key))))


# ── Library symbol extraction ───────────────────────────────────────────────
def _block(text, start):
    d = 0
    for k in range(start, len(text)):
        if text[k] == "(":
            d += 1
        elif text[k] == ")":
            d -= 1
            if d == 0:
                return text[start:k + 1]
    raise ValueError("unbalanced")


_lib_cache = {}


def lib_symbol(lib, name):
    """Return the symbol s-expression text as stored in the .kicad_sym file."""
    if lib == "CapDis":
        path = os.path.join(HERE, "CapDis.kicad_sym")
    else:
        path = os.path.join(KICAD_SYMS, lib + ".kicad_sym")
    if path not in _lib_cache:
        _lib_cache[path] = open(path, encoding="utf8").read()
    t = _lib_cache[path]
    m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), t)
    if not m:
        raise KeyError(lib + ":" + name)
    s = _block(t, m.start() + 2)
    assert "(extends" not in s, f"{lib}:{name} uses extends; use the parent symbol"
    return s


def embed(lib, name):
    s = lib_symbol(lib, name)
    s = s.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    return "\t" + s.replace("\n", "\n\t")


def pins_of(lib, name):
    """{number: (x, y, angle)} in library coordinates (y up)."""
    s = lib_symbol(lib, name)
    out = {}
    for m in re.finditer(r"\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)", s):
        num = re.search(r'\(number "([^"]+)"', s[m.end():m.end() + 800]).group(1)
        out[num] = (float(m.group(1)), float(m.group(2)), int(m.group(3)))
    return out


# ── Parts ───────────────────────────────────────────────────────────────────
SYM = {
    "R": ("Device", "R"), "D": ("Device", "D"), "DZ": ("Device", "D_Zener"),
    "LED": ("Device", "LED"), "C": ("Device", "C"), "F": ("Device", "Fuse"),
    "BAT": ("Device", "Battery"), "NPN": ("Transistor_BJT", "Q_NPN_EBC"),
    "NMOS": ("Transistor_FET", "Q_NMOS_GDS"), "CONN1": ("Connector_Generic", "Conn_01x01"),
    "CONN2": ("Connector_Generic", "Conn_01x02"), "MH": ("Mechanical", "MountingHole"),
    "HS": ("Mechanical", "Heatsink"), "DVM": ("CapDis", "PM-128"),
}

parts = []   # dicts
texts = []   # (x, y, text, size)


def part(ref, kind, value, fp, x, y, rot=0, nets=None, on_board=True, in_bom=True):
    parts.append(dict(ref=ref, kind=kind, value=value, fp=FP[fp], x=x * G, y=y * G, rot=rot,
                      nets=nets or {}, on_board=on_board, in_bom=in_bom))


def note(x, y, txt, size=1.27):
    texts.append((x * G, y * G, txt, size))


def vchain(prefix, n, kind, value, fp, x, y0, top_net, bot_net):
    """Vertical chain of 2-pin parts whose pins touch (pitch 6 grid = 7.62 mm)."""
    for i in range(n):
        nets = {}
        if i == 0 and top_net:
            nets["1"] = top_net
        if i == n - 1 and bot_net:
            nets["2"] = bot_net
        part(f"{prefix}{i + 1}", kind, value, fp, x, y0 + 6 * i, 0, nets)


# Coordinates below are in grid units (1.27 mm). Page A3 = 330 × 233 grid.
wires = []      # segments in grid units
junctions = []  # grid points
labels = []     # (net, x, y, angle) free labels placed on wires


def W(*pts):
    for a, b in zip(pts, pts[1:]):
        wires.append((a, b))


# 1 ── Input, reverse-polarity bridge, fuse ───────────────────────────────────
note(8, 12, "1. INPUT + REVERSE-POLARITY BRIDGE + FUSE", 2)
part("J1", "CONN1", "SLB4-G-21", "", 18, 26, 180, {"1": "PROBE_A"}, on_board=False)
part("J2", "CONN1", "SLB4-G-22", "", 18, 50, 180, {"1": "PROBE_B"}, on_board=False)
part("J3", "CONN2", "MKDS5/2-9.5", "MKDS", 38, 26, 180, {"1": "PROBE_A", "2": "PROBE_A"})
part("J4", "CONN2", "MKDS5/2-9.5", "MKDS", 38, 50, 180, {"1": "PROBE_B", "2": "PROBE_B"})
note(8, 60, "J1/J2 = panel banana sockets (off-board), wired to J3/J4 with 1 mm² silicone wire (0.6/1 kV).\n"
            "Both poles of J3 = PROBE_A, both poles of J4 = PROBE_B: two blocks keep the input leads apart.")
# Device:D pin 1 = K (left at rot 0); rot 180 puts K on the right.
part("D1", "D", "1N4007", "DO41", 64, 24, 180, {"2": "PROBE_A", "1": "BRIDGE_P"})
part("D3", "D", "1N4007", "DO41", 64, 32, 180, {"2": "PROBE_B", "1": "BRIDGE_P"})
part("D4", "D", "1N4007", "DO41", 64, 40, 180, {"2": "GND", "1": "PROBE_A"})
part("D2", "D", "1N4007", "DO41", 64, 48, 180, {"2": "GND", "1": "PROBE_B"})
part("F1", "F", "2A 1000VDC gR", "FUSE", 88, 30, 90, {"1": "BRIDGE_P", "2": "HVp"})
note(80, 36, "F1: ESKA 1038820\n10.3×38 mm, 2× Schurter\nCSO 0751.0506 clips")

# 2 ── Slow path ─────────────────────────────────────────────────────────────
note(112, 12, "2. SLOW PATH", 2)
vchain("R_slow", 5, "R", "4k7 5W", "R_slow", 118, 24, "HVp", "GND")
note(112, 58, "5 × 4.7 kΩ / 5 W wirewound\n= 23.5 kΩ, 25 mA at 600 V")

# 3 ── Fast path ─────────────────────────────────────────────────────────────
note(150, 12, "3. FAST PATH (below ~63 V)", 2)
part("R_fast1", "R", "50R 7W", "R_fast", 172, 24, 0, {"1": "HVp"})
part("TF1", "F", "SF129R0 133°C", "TF", 172, 30, 0)               # pins touch R_fast1 and Q2 drain
part("Q2", "NMOS", "STP10NK80Z", "TO220", 170, 37, 0, {"1": "GATE", "3": "GND"})
part("HS1", "HS", "HS-S01 (clip-on)", "", 196, 37, 0, on_board=False)
note(150, 50, "TF1 (thermal cutoff, 133 °C) clamped to the R_fast1 body:\n"
              "opens if a live supply keeps Q2 on (R_fast1 > 7 W).\n"
              "Q2 tab = drain (HV): insulate HS1 from it with the Fischer MST 220 set.\n"
              "HS1 (HS-S01) slips onto the tab: no solder pins, electrically floating.")

# 4 ── Threshold detector & gate drive ──────────────────────────────────────
note(8, 74, "4. THRESHOLD (~63 V) + GATE DRIVE", 2)
part("R1", "R", "1M 3W", "R3W", 14, 88, 0, {"1": "HVp"})
part("R2", "R", "10k", "R0207", 14, 102, 0, {"2": "GND"})
part("R3", "R", "10k", "R0207", 24, 95, 90)
W((14, 91), (14, 95))
W((14, 95), (14, 99))
W((14, 95), (21, 95))
junctions += [(14, 95)]
part("Q1", "NPN", "MPSA42", "TO92", 36, 95, 0, {"1": "GND"})
W((27, 95), (32, 95))                       # R3 → Q1 base
part("R5", "R", "470k 3W", "R3W", 52, 86, 0, {"1": "HVp"})
part("D9", "DZ", "BZX85C12", "DO41", 52, 92, 270, {"2": "GND"})   # K touches R5 pin 2
part("R4", "R", "100R", "R0207", 62, 89, 90)
part("C_byp2", "C", "100nF 50V", "C", 72, 92, 0, {"2": "GND"})
W((38, 91), (38, 89), (52, 89))             # Q1 collector → GATE_TOP node
W((52, 89), (59, 89))                       # node → R4
W((65, 89), (72, 89))                       # R4 → C_byp2 / gate
W((72, 89), (78, 89))
junctions += [(52, 89), (72, 89)]
labels += [("GATE_TOP", 42, 89, 0), ("GATE", 78, 89, 0), ("BASE_DIV", 15, 95, 0)]
note(8, 110, "Above ~63 V: Q1 saturates → GATE_TOP low → Q2 off (slow path only).\n"
             "Below ~63 V: Q1 off → R5 pulls GATE_TOP up to 12 V (D9) → Q2 on (fast path).\n"
             "R4 + C_byp2: gate filter, keeps Q2 off during hot-plug.")

# 5 ── LED danger indicator ──────────────────────────────────────────────────
note(104, 74, "5. DANGER LED", 2)
vchain("R_LED", 4, "R", "100k 0.6W", "R0207", 112, 84, "HVp", None)
part("D_LED1", "DZ", "BZX55C8V2", "DO35", 112, 108, 270)   # K touches R_LED4 pin 2
part("LED1", "LED", "HLMP-4700 red", "LED", 112, 114, 90, {"1": "GND"})
note(104, 122, "LED off below\n8.2 V + 2 V ≈ 10.2 V")

# 6 ── Voltmeter divider + PM-128 ───────────────────────────────────────────
note(150, 74, "6. VOLTMETER: 10 000:1 DIVIDER → PM-128", 2)
vchain("R_sig", 5, "R", "100k 0.6W", "R0207", 160, 84, "HVp", None)
part("R_sig_bot1", "R", "100R 1%", "R0207", 170, 117, 0, {"2": "GND"})
part("R_sig_bot2", "R", "100R 1%", "R0207", 184, 117, 0, {"2": "GND"})
part("D_clamp1", "D", "1N4007", "DO41", 198, 117, 90, {"1": "GND"})  # A on top
part("J5", "CONN2", "PM-128 input", "HDR2", 224, 114, 0, {"2": "GND"})
W((160, 111), (160, 114), (170, 114))
W((170, 114), (184, 114))
W((184, 114), (198, 114))
W((198, 114), (220, 114))
junctions += [(170, 114), (184, 114), (198, 114)]
labels += [("SIGOUT", 162, 114, 0)]
part("DVM1", "DVM", "Axiomet PM-128", "", 244, 115, 0,
     {"1": "SIGOUT", "2": "GND", "3": "BATT_P", "4": "BATT_N"}, on_board=False)
part("BT1", "BAT", "9V, holder w/ switch", "", 266, 115, 0, {"1": "BATT_P", "2": "BATT_N"}, on_board=False)
note(150, 128, "600 V → 60 mV → display \"600\". Decimal-point jumpers P1–P3 open; calibrate with PM-128 trimmer R4.\n"
               "D_clamp1 holds VIN ≤ 0.7 V if both bottom resistors open.\n"
               "DVM1 + BT1 are off-board (soldered wires to the PM-128 pads). BT1 FLOATS: never connect\n"
               "the battery to circuit GND (PM-128 requires separate supply and input grounds).")

# 7 ── Mechanical ────────────────────────────────────────────────────────────
note(212, 12, "7. MECHANICAL", 2)
for i in range(4):
    part(f"H{i + 1}", "MH", "M3 (nylon screw)", "MH", 216 + 10 * i, 26, 0, in_bom=False)

note(8, 150, "PCB ZONES\n"
             "HV: J3/J4, bridge, F1, R_slow1-5, R_fast1, TF1, Q2, the R_LED/R_sig chains, the HVp pads of R1/R5.\n"
             "LV: Q1, R2-R4, D9, C_byp2, D_LED1, LED1, divider bottom, J5. R1/R5 cross a milled slot.\n"
             "Clearance = 1 mm per 100 V of worst-case difference, 6 mm HV to GND/LV (hv_rules.py).", 1.5)


# ── Geometry helpers ────────────────────────────────────────────────────────
def pin_pos(p, num):
    lib, name = SYM[p["kind"]]
    px, py, ang = pins_of(lib, name)[num]
    r = math.radians(p["rot"])
    rx = px * math.cos(r) - py * math.sin(r)
    ry = px * math.sin(r) + py * math.cos(r)
    out = (ang + 180 + p["rot"]) % 360  # outward direction, library frame (y up)
    return (round(p["x"] + rx, 2), round(p["y"] - ry, 2)), out


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def eff(justify=None, hide=False, size=1.27):
    j = f"\n\t\t\t\t(justify {justify})" if justify else ""
    return f"(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {size} {size})\n\t\t\t\t){j}\n\t\t\t)"


def prop(name, value, x, y, hide=False, justify=None, ang=0):
    h = "\n\t\t\t(hide yes)" if hide else ""
    value = value.replace('"', '\\"')
    return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {fmt(x)} {fmt(y)} {ang}){h}'
            f'\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t{eff(justify)}\n\t\t)')


BOM_BY_REF = {}
for item in BOM:
    for r in item["refs"]:
        BOM_BY_REF[r] = item


def bom_item(ref):
    return BOM_BY_REF.get(ref) or BOM_BY_REF.get(ref.rstrip("0123456789")) or {}


def symbol_inst(p):
    lib, name = SYM[p["kind"]]
    x, y, rot = p["x"], p["y"], p["rot"]
    item = bom_item(p["ref"])
    vertical = rot in (0, 180) and p["kind"] in ("R", "C", "F", "BAT")
    if vertical:
        rp, vp, j = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), "left"
    elif p["kind"] == "NMOS":
        rp, vp, j = (x + 6.35, y - 1.27), (x + 6.35, y + 1.27), "left"
    elif p["kind"] in ("NPN", "DVM", "CONN1", "CONN2", "HS", "MH"):
        rp, vp, j = (x + 1.27, y - 7.62), (x + 1.27, y - 5.08), "left"
    else:
        rp, vp, j = (x, y - 3.81), (x, y + 3.81), None
    if p["kind"] in ("D", "DZ", "LED") and rot in (90, 270):
        rp, vp, j = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), "left"
    fa = (360 - rot) % 360 if rot in (90, 270) else 0  # KiCad adds the symbol rotation
    ob = "yes" if p["on_board"] else "no"
    props = [
        prop("Reference", p["ref"], *rp, justify=j, ang=fa),
        prop("Value", p["value"], *vp, justify=j, ang=fa),
        prop("Footprint", p["fp"], x, y, hide=True),
        prop("Datasheet", "", x, y, hide=True),
        prop("Description", item.get("description", ""), x, y, hide=True),
        prop("MPN", item.get("part_number", ""), x, y, hide=True),
    ]
    pins = "\n".join(f'\t\t(pin "{n}"\n\t\t\t(uuid "{u(p["ref"], "pin", n)}")\n\t\t)'
                     for n in pins_of(lib, name))
    return (f'\t(symbol\n\t\t(lib_id "{lib}:{name}")\n\t\t(at {fmt(x)} {fmt(y)} {rot})\n\t\t(unit 1)'
            f'\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom {"yes" if p["in_bom"] else "no"})\n\t\t(on_board {ob})'
            f'\n\t\t(in_pos_files {ob})\n\t\t(dnp no)\n\t\t(uuid "{u(p["ref"])}")\n'
            + "\n".join(props) + ("\n" + pins if pins else "") +
            f'\n\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"'
            f'\n\t\t\t\t\t(reference "{p["ref"]}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')


def wire(a, b, key):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})\n\t\t)'
            f'\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{u("w", key)}")\n\t)')


def label(net, at, ang, key):
    j = {0: "left", 90: "left", 180: "right", 270: "right"}[ang]
    return (f'\t(label "{net}"\n\t\t(at {fmt(at[0])} {fmt(at[1])} {ang})\n\t\t{eff(j)}'
            f'\n\t\t(uuid "{u("l", key)}")\n\t)')


def junction(x, y, key):
    return (f'\t(junction\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)'
            f'\n\t\t(uuid "{u("j", key)}")\n\t)')


def text(x, y, s, size, key):
    s = s.replace('"', '\\"').replace("\n", "\\n")
    return (f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {fmt(x)} {fmt(y)} 0)'
            f'\n\t\t{eff("left top", size=size)}\n\t\t(uuid "{u("t", key)}")\n\t)')


def build():
    body = []
    used = []
    for p in parts:
        if SYM[p["kind"]] not in used:
            used.append(SYM[p["kind"]])
    lib_syms = "\n".join(embed(lib, name) for lib, name in used)

    for p in parts:
        body.append(symbol_inst(p))
        for num, net in p["nets"].items():
            (px, py), out = pin_pos(p, num)
            d = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[out]
            end = (round(px + d[0] * 2 * G, 2), round(py + d[1] * 2 * G, 2))
            body.append(wire((px, py), end, f"{p['ref']}.{num}"))
            body.append(label(net, end, out, f"{p['ref']}.{num}"))
    for i, (a, b) in enumerate(wires):
        body.append(wire((a[0] * G, a[1] * G), (b[0] * G, b[1] * G), f"free{i}"))
    for i, (x, y) in enumerate(junctions):
        body.append(junction(x * G, y * G, i))
    for i, (net, x, y, ang) in enumerate(labels):
        body.append(label(net, (x * G, y * G), ang, f"free{i}"))
    for i, (x, y, s, size) in enumerate(texts):
        body.append(text(x, y, s, size, i))

    head = f"""(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{ROOT_UUID}")
\t(paper "A3")
\t(title_block
\t\t(title "600V Capacitor Discharger")
\t\t(date "2026-10-01")
\t\t(rev "2.0")
\t\t(company "DIY")
\t\t(comment 1 "Generated by gen_kicad_sch.py - edit the script, not this file")
\t\t(comment 2 "Netlist matches simulation/discharger.cir.tmpl (check_kicad.py)")
\t)
\t(lib_symbols
{lib_syms}
\t)
"""
    tail = """\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
\t(embedded_fonts no)
)
"""
    return head + "\n".join(body) + "\n" + tail


# Board variants: same circuit, different footprints (project name → ref → footprint).
_V = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical"     # LV resistors, standing
_C = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical"     # chain resistors (≤150 V each)
_SMALL = {   # standing small parts + HS-S01 clip-on heatsink (both boards)
    "R1": "CapDis:R_Axial_DIN0516_L15.5mm_D5.0mm_P10.16mm_Vertical_BodyOnPad2",
    "R5": "CapDis:R_Axial_DIN0516_L15.5mm_D5.0mm_P10.16mm_Vertical_BodyOnPad2",
    **{f"R_sig{i}": _C for i in range(1, 6)}, **{f"R_LED{i}": _C for i in range(1, 5)},
    "R2": _V, "R3": _V, "R4": _V, "R_sig_bot1": _V, "R_sig_bot2": _V,
    "D9": "Diode_THT:D_DO-41_SOD81_P5.08mm_Vertical_AnodeUp",
    "D_clamp1": "Diode_THT:D_DO-41_SOD81_P5.08mm_Vertical_AnodeUp",
    "D_LED1": "Diode_THT:D_DO-35_SOD27_P5.08mm_Vertical_AnodeUp",
    "HS1": None,     # HS-S01 clips onto Q2: mechanical only, no solder pins
}
VARIANTS = {
    "CapacitorDischarger": dict(_SMALL),                              # 2-layer, power resistors flat
    "CapacitorDischarger_1S": {                                       # single-sided, 100 × 75 mm
        **_SMALL,
        **{f"R_slow{i}": "CapDis:R_Axial_Ohmite_45F_5W_Vertical" for i in range(1, 6)},
        "R_fast1": "CapDis:R_Axial_Ohmite_27J_7W_Vertical",
        "TF1": "CapDis:ThermalCutoff_SEFUSE_SF_Vertical",
        "H2": None, "H4": None,   # only two mounting holes fit
    },
}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=PROJECT, choices=list(VARIANTS))
    PROJECT = ap.parse_args().project
    for p in parts:
        fp = VARIANTS[PROJECT].get(p["ref"], p["fp"])
        if fp is None:           # not on this board
            p["on_board"] = False
        else:
            p["fp"] = fp
    out = os.path.join(HERE, PROJECT + ".kicad_sch")
    open(out, "w", encoding="utf8", newline="\n").write(build())
    print("wrote", out, len(parts), "symbols")
