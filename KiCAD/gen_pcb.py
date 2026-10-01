r"""Build CapacitorDischarger.kicad_pcb (2-layer, 120 × 90 mm) from the schematic: placement,
outline, HV slot, pre-routed Q2 escapes, Freerouting autoroute with voltage-aware clearances, DRC.

Run with KiCad's python:
    "C:\Program Files\KiCad\10.0\bin\python.exe" gen_pcb.py --freerouting PATH.jar

Board coordinates below are in mm from the board's top-left corner (+x right, +y down).
The single-sided 100 × 75 mm variant (board_1s.py) reuses these functions.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_kicad_sch  # noqa: E402  (symbol UUIDs, for schematic ↔ board links)
import hv_rules       # noqa: E402  (clearance = 1 mm per 100 V of worst-case difference)

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
STOCK_FP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
NAME = "CapacitorDischarger"
PCB = os.path.join(HERE, NAME + ".kicad_pcb")
PRO = os.path.join(HERE, NAME + ".kicad_pro")
OX, OY = 50.0, 50.0           # board origin on the page
W, H = 120.0, 90.0            # board size

# ── Net classes (track widths; clearances come from hv_rules via the .kicad_dru) ─
CLASSES = {
    "Default": dict(clearance=0.4, track_width=0.5, via_diameter=1.2, via_drill=0.6),
    "HV":      dict(clearance=0.4, track_width=1.5, via_diameter=2.4, via_drill=1.0),
    "HV_sig":  dict(clearance=0.4, track_width=0.8, via_diameter=1.6, via_drill=0.8),
    "GND":     dict(clearance=0.4, track_width=1.5, via_diameter=1.6, via_drill=0.8),
}
PATTERNS = [
    ("HV", "/PROBE_A"), ("HV", "/PROBE_B"), ("HV", "/BRIDGE_P"), ("HV", "/HVp"),
    ("HV", "Net-(R_slow*"), ("HV", "Net-(R_fast1-Pad2)"), ("HV", "Net-(Q2-D)"),
    ("HV_sig", "Net-(R_LED*"), ("HV_sig", "Net-(R_sig*"),
    ("GND", "/GND"),
]

# ── Placement: ref → (x, y, orientation°) ───────────────────────────────────
# Orientation is KiCad's: counter-clockwise on screen; 90 turns +x into -y.
PLACE = {
    # probes enter at the top edge; bridge right below (GND anodes outside), F1 under it
    "J3": (8.0, 8.4, 0), "J4": (28.5, 8.4, 0),
    "D4": (8.0, 17.0, 270), "D1": (17.52, 27.16, 90), "D3": (28.5, 27.16, 90), "D2": (38.02, 17.0, 270),
    "F1": (37.5, 40.0, 0),            # clip A (BRIDGE_P) x 13-32, clip B (HVp) x 43-62
    # fast path: R_fast1 flat along the top, TF1 under it, Q2 (tab down, HS-S01 clipped on)
    "R_fast1": (68.0, 9.0, 0),        # HVp (68, 9) → FAST_TF (108.64, 9)
    "TF1": (108.64, 17.0, 180),       # FAST_TF (108.64, 17) → DRAIN (85.78, 17); body 1 mm from R_fast1
    "Q2": (85.78, 24.0, 180),         # D 85.78, G 90.86, S 80.7
    # gate drive (LV) right of Q2; R1/R5 stand on their LV pad, HVp pad below the slot
    "R4": (98.0, 26.0, 180), "Q1": (102.0, 26.0, 0),                          # row y=26
    "C_byp2": (93.0, 31.0, 0), "R3": (105.5, 33.0, 90), "D9": (109.5, 31.0, 0),  # row y=31
    "R2": (102.0, 35.0, 90),
    "R1": (100.5, 50.0, 90), "R5": (113.0, 50.0, 90),   # bodies (LV) at y 39.8, HVp pads at y 50
    # slow path: flat, as five columns; R_slow1 (HVp) on the right, GND at R_slow5's foot
    "R_slow1": (52.0, 52.0, 270), "R_slow2": (41.0, 82.48, 90), "R_slow3": (30.0, 52.0, 270),
    "R_slow4": (19.0, 82.48, 90), "R_slow5": (8.0, 52.0, 270),
    # indicator side (standing chains as staircases, same as the single-sided board)
    "D_LED1": (94.5, 65.5, 270), "J6": (94.5, 77.96, 90), "D_clamp2": (89.0, 75.0, 270),
    "R_sig_bot1": (80.0, 75.5, 270), "R_sig_bot2": (76.0, 75.5, 270),
    "D_clamp1": (72.0, 78.5, 90), "J5": (66.0, 78.0, 90),
    # mounting holes (use nylon M3 screws)
    "H1": (61.0, 86.5, 0), "H2": (116.5, 86.5, 0), "H3": (116.5, 58.0, 0), "H4": (50.0, 20.0, 0),
}
for _i in range(5):
    PLACE[f"R_sig{_i + 1}"] = (66.0 + 5 * _i, 52.0 + 5.08 * _i, 270)
for _i in range(4):
    PLACE[f"R_LED{_i + 1}"] = (75.0 + 5 * _i, 52.0 + 5.08 * _i, 270)
SLOTS = [(95.0, 43.5, 118.0, 46.5)]          # milled slot under R1/R5 (600 V across each)
TEXTS = [("DANGER 600 V", 64.0, 44.0, 2.0), ("LV", 112.0, 22.0, 2.0),
         ("CAPACITOR DISCHARGER rev 2.1", 92.0, 87.0, 1.2)]
REFS_ON_FAB = {"R2", "R3", "R4", "C_byp2", "D9", "Q1", "D_LED1", "J6", "D_clamp2", "J5", "D_clamp1", "R_sig_bot1",
               "R_sig_bot2", *(f"R_sig{i}" for i in range(1, 6)), *(f"R_LED{i}" for i in range(1, 5))}
ZONES = []                                    # GND pours: (layer, x1, y1, x2, y2); none here
NO_POUR = []

# Pre-routes around Q2: its pins are 5.08 mm apart (inside the Q2 exception rule), which
# the autorouter would otherwise refuse to leave.
PREROUTES = [  # (net, layer, width, [(x, y), ...])
    ("Net-(Q2-D)", "F.Cu", 1.5, [(85.78, 24.0), (85.78, 17.0)]),
    ("/GATE", "F.Cu", 0.5, [(90.86, 24.0), (95.46, 26.0)]),
    ("/GND", "F.Cu", 1.5, [(80.7, 24.0), (80.7, 31.0)]),
    # D2's GND anode is boxed in by PROBE_B, BRIDGE_P and F1: take it to Q2's source on B.Cu
    ("/GND", "B.Cu", 1.5, [(38.02, 27.16), (46.5, 27.16), (50.5, 31.0), (80.7, 31.0)]),
]
VIAS = [("/GND", 80.7, 31.0, 1.6, 0.8)]   # (net, x, y, diameter, drill)
# chain links: adjacent pads, routed by hand
for _chain, _n in (("R_sig", 5), ("R_LED", 4)):
    for _i in range(1, _n):
        _x, _y, _ = PLACE[f"{_chain}{_i}"]
        PREROUTES.append((f"Net-({_chain}{_i}-Pad2)", "F.Cu", 0.8,
                          [(_x, _y + 5.08), PLACE[f"{_chain}{_i + 1}"][:2]]))

Q2_RULE = """
# Q2 (TO-220): legs bent out to 5.08 mm (2.9 mm copper gap); the device is rated 800 V
# between its pins.
(rule "Q2 pin field"
    (condition "(A.intersectsCourtyard('Q2') || B.intersectsCourtyard('Q2')) && (A.NetName == 'Net-(Q2-D)' || B.NetName == 'Net-(Q2-D)')")
    (constraint clearance (min 2.5mm)))
"""


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


# ── Project settings (net classes, board rules) ─────────────────────────────
def write_project_settings():
    pro = json.load(open(PRO, encoding="utf8"))
    template = pro["net_settings"]["classes"][0]
    classes = []
    for name, vals in CLASSES.items():
        c = dict(template)
        c.update(vals, name=name)
        c["priority"] = -1 if name == "Default" else list(CLASSES).index(name)
        classes.append(c)
    pro["net_settings"]["classes"] = classes
    pro["net_settings"]["netclass_patterns"] = [{"netclass": c, "pattern": p} for c, p in PATTERNS]
    rules = pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
    rules.update({"min_clearance": 0.3, "min_track_width": 0.25, "min_through_hole_diameter": 0.6,
                  "min_copper_edge_clearance": 0.5, "min_hole_clearance": 0.3})
    # write via a temp file and retry: on this machine the .kicad_pro is sometimes briefly
    # locked by another process (seen as "OSError: Invalid argument")
    tmp = PRO + ".tmp"
    with open(tmp, "w", encoding="utf8", newline="\n") as f:
        json.dump(pro, f, indent=2)
    for attempt in range(20):
        try:
            os.replace(tmp, PRO)
            break
        except OSError:
            if attempt == 19:
                raise
            import time
            time.sleep(0.5)


def write_dru(board):
    nets = [str(n) for n in board.GetNetsByName().keys()]
    open(os.path.join(HERE, NAME + ".kicad_dru"), "w", encoding="utf8", newline="\n").write(
        hv_rules.dru(nets, Q2_RULE))


# ── Netlist from the schematic ──────────────────────────────────────────────
def read_netlist():
    path = os.path.join(HERE, "pcb_build.net")
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", path,
                    os.path.join(HERE, NAME + ".kicad_sch")], check=True, capture_output=True)
    t = open(path, encoding="utf8").read()
    os.remove(path)
    comps = {}
    for m in re.finditer(r'\(comp\s*\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)', t):
        blk = t[m.end():t.find("\n\t\t)", m.end())]  # this component only
        fields = {"MPN": "", "Description": ""}
        fields.update({k: v.replace('\\"', '"') for k, v in
                  re.findall(r'\(field\s*\(name "(MPN|Description)"\)\s*"((?:[^"\\]|\\.)*)"', blk)})
        comps[m.group(1)] = dict(value=m.group(2), fp=m.group(3), pads={}, fields=fields)
    for m in re.finditer(r'\(net\s*\(code "\d+"\)\s*\(name "([^"]*)"\)(.*?)\n\t\t\)', t, re.S):
        for r, p in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', m.group(2)):
            comps[r]["pads"][p] = m.group(1)
    return comps


def lib_path(lib):
    if lib == "CapDis":
        return os.path.join(HERE, "CapDis.pretty")
    return os.path.join(STOCK_FP, lib + ".pretty")


# ── Board construction ──────────────────────────────────────────────────────
def add_rect(board, x1, y1, x2, y2, layer, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(pt(x1, y1))
    s.SetEnd(pt(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)


def add_text(board, txt, x, y, size=2.0, layer=pcbnew.F_SilkS, bold=True):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetBold(bold)
    board.Add(t)


def add_track(board, net, layer, width, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pt(x1, y1))
        tr.SetEnd(pt(x2, y2))
        tr.SetWidth(mm(width))
        tr.SetLayer(board.GetLayerID(layer))
        tr.SetNet(net)
        tr.SetLocked(True)
        board.Add(tr)


def add_zone(board, net, layer, x1, y1, x2, y2, keepout=False, name=""):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if keepout:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        z.SetZoneName(name)
    else:
        z.SetNet(net)
        z.SetMinThickness(mm(0.4))
        z.SetThermalReliefGap(mm(0.6))
        z.SetThermalReliefSpokeWidth(mm(1.0))
        z.SetLocalClearance(mm(0.4))
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        o.Append(mm(OX + x), mm(OY + y))
    board.Add(z)
    return z


def build_board():
    comps = read_netlist()
    board = pcbnew.NewBoard(PCB)
    board.GetDesignSettings().SetBoardThickness(mm(1.6))
    nets = {}
    for c in comps.values():
        for n in c["pads"].values():
            if n not in nets:
                nets[n] = pcbnew.NETINFO_ITEM(board, n)
                board.Add(nets[n])

    missing = set(comps) - set(PLACE)
    assert not missing, f"no placement for {missing}"
    for ref, c in comps.items():
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(lib_path(lib), name)
        assert fp is not None, c["fp"]
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        for k, v in c["fields"].items():
            fp.SetField(k, v)
            fp.GetField(k).SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH("/" + gen_kicad_sch.u(ref)))
        x, y, rot = PLACE[ref]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        if ref.startswith("H") and ref[1:].isdigit():
            fp.Reference().SetVisible(False)
        if ref in REFS_ON_FAB:   # too dense for silkscreen text: label on the assembly drawing
            fp.Reference().SetLayer(pcbnew.F_Fab)
        for p in fp.Pads():
            if p.GetNumber() in c["pads"]:
                p.SetNet(nets[c["pads"][p.GetNumber()]])
        board.Add(fp)

    add_rect(board, 0, 0, W, H, pcbnew.Edge_Cuts)
    for x1, y1, x2, y2 in SLOTS:
        add_rect(board, x1, y1, x2, y2, pcbnew.Edge_Cuts)
    for net, layer, width, pts in PREROUTES:
        add_track(board, nets[net], layer, width, pts)
    for net, x, y, dia, drill in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt(x, y))
        v.SetWidth(mm(dia))
        v.SetDrill(mm(drill))
        v.SetNet(nets[net])
        v.SetLocked(True)
        board.Add(v)

    for args in TEXTS:
        add_text(board, *args)
    pcbnew.SaveBoard(PCB, board)
    return board


def check_placement(board):
    """Print the pad coordinates that the comments in PLACE promise, for a quick sanity check."""
    for ref in ("J3", "J4", "D1", "D2", "D3", "D4", "F1", "Q2", "TF1", "R_fast1", "R_slow1", "R_slow5"):
        fp = board.FindFootprintByReference(ref)
        pads = sorted((p.GetNumber(), round(pcbnew.ToMM(p.GetPosition().x) - OX, 2),
                       round(pcbnew.ToMM(p.GetPosition().y) - OY, 2), p.GetNetname()) for p in fp.Pads())
        print(ref, pads)


def pair_classes(dsn, nets):
    """Give each HV net its own class and add a class_class clearance matrix from hv_rules, so
    Freerouting routes with the same voltage-aware clearances that the DRC checks."""
    t = open(dsn, encoding="utf8").read()
    vias = {m.group(1): m.group(2) for m in re.finditer(
        r'\(class (\S+) [^()]*\(circuit\s*\(use_via "([^"]+)"\)', t, re.S)}
    width = {name: int(c["track_width"] * 1000) for name, c in CLASSES.items()}
    start = t.index("    (class ")
    end = t.rindex(")", start, t.index("  (wiring"))     # closes (network
    hv = [n for n in hv_rules.HV_NETS if n in nets]
    lv = [n for n in nets if n and n not in hv and n != "/GND"]

    def cls(name, members, kind):
        via = vias.get("kicad_default" if kind == "Default" else kind, next(iter(vias.values())))
        m = " ".join(f'"{n}"' for n in members)
        return (f'    (class {name} {m}\n      (circuit\n        (use_via "{via}")\n      )\n'
                f'      (rule\n        (width {width[kind]})\n        (clearance {int(hv_rules.MIN_CLEAR * 1000)})\n'
                f'      )\n    )\n')
    kind = {n: "HV_sig" if n.startswith(("Net-(R_LED", "Net-(R_sig")) else "HV" for n in hv}
    body = cls("LV", lv, "Default") + cls("GND", ["/GND"], "GND")
    body += "".join(cls(f"HV{i}", [n], kind[n]) for i, n in enumerate(hv))
    for i, a in enumerate(hv):
        for j, b in enumerate(hv[i + 1:], i + 1):
            c = hv_rules.clearance(a, b)
            if c > hv_rules.MIN_CLEAR:
                body += f"    (class_class (classes HV{i} HV{j}) (rule (clearance {int(c * 1000)})))\n"
        c = int(hv_rules.clearance(a, "/GND") * 1000)
        body += f"    (class_class (classes HV{i} LV) (rule (clearance {c})))\n"
        body += f"    (class_class (classes HV{i} GND) (rule (clearance {c})))\n"
    open(dsn, "w", encoding="utf8").write(t[:start] + body + "  " + t[end:])


def autoroute(jar):
    board = pcbnew.LoadBoard(PCB)
    dsn = os.path.join(HERE, NAME + ".dsn")
    ses = os.path.join(HERE, NAME + ".ses")
    assert pcbnew.ExportSpecctraDSN(board, dsn)
    pair_classes(dsn, [str(n) for n in board.GetNetsByName().keys()])
    subprocess.run(["java", "-jar", jar, "-de", dsn, "-do", ses, "-mp", "40", "--gui.enabled=false"],
                   check=True)
    board = pcbnew.LoadBoard(PCB)
    assert pcbnew.ImportSpecctraSES(board, ses)
    pcbnew.SaveBoard(PCB, board)
    os.remove(dsn)
    os.remove(ses)


def finish():
    board = pcbnew.LoadBoard(PCB)
    gnd = board.FindNet("/GND")
    for layer, x1, y1, x2, y2 in ZONES:
        add_zone(board, gnd, layer, x1, y1, x2, y2)
    for ref in NO_POUR:
        bb = board.FindFootprintByReference(ref).GetCourtyard(pcbnew.F_CrtYd).BBox()
        add_zone(board, None, pcbnew.F_Cu, pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                 pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY,
                 keepout=True, name=f"no pour under {ref}")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)


def drc():
    rpt = os.path.join(HERE, "drc.rpt")
    subprocess.run([CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "-o", rpt, PCB],
                   capture_output=True)
    print(open(rpt, encoding="utf8").read()[-3000:])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--freerouting", help="path to freerouting.jar (skip routing if omitted)")
    ap.add_argument("--stage", default="all", choices=["all", "place", "route", "finish", "drc"])
    a = ap.parse_args()
    if a.stage in ("all", "place"):
        write_project_settings()
        board = build_board()
        write_dru(board)
        check_placement(board)
    if a.stage in ("all", "route") and a.freerouting:
        autoroute(a.freerouting)
    if a.stage in ("all", "finish"):
        finish()
    if a.stage in ("all", "finish", "drc"):
        drc()
