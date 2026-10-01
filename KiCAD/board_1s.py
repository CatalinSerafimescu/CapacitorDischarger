"""Single-sided 100 × 75 mm board (Bungard FEPCU-075 photoresist blank): CapacitorDischarger_1S.

Hand-placed and hand-routed on B.Cu only (components on top, no jumpers). Clearances come
from hv_rules.py (1 mm per 100 V of worst-case difference; HV ↔ GND/LV stays 6 mm).

    python gen_kicad_sch.py --project CapacitorDischarger_1S
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" board_1s.py

Topology (no crossings on one layer):
  - probes enter at the top edge (J3, J4); the bridge sits right below them, GND anodes outside
  - BRIDGE_P drops to F1; F1's right clip is the HVp hub
  - GND runs as a ring along the board edge, joining both bridge anodes and every return
  - top-right pocket: R_fast1 + TF1 + Q2 (HS-S01) and the gate drive; R1/R5 cross a slot
  - bottom-left: R_slow1-5 standing; bottom-right: divider and LED chains as staircases
"""
import os
import shutil
import subprocess

import pcbnew

import gen_pcb as G
import hv_rules

HERE = os.path.dirname(os.path.abspath(__file__))
G.NAME = "CapacitorDischarger_1S"
G.PCB = os.path.join(HERE, G.NAME + ".kicad_pcb")
G.PRO = os.path.join(HERE, G.NAME + ".kicad_pro")
G.W, G.H = 100.0, 75.0
G.CLASSES = {
    "Default": dict(clearance=0.4, track_width=0.6, via_diameter=1.2, via_drill=0.6),
    "HV":      dict(clearance=0.4, track_width=1.5, via_diameter=2.4, via_drill=1.0),
    "HV_sig":  dict(clearance=0.4, track_width=0.8, via_diameter=1.6, via_drill=0.8),
    "GND":     dict(clearance=0.4, track_width=1.5, via_diameter=1.6, via_drill=0.8),
}
G.TEXTS = []
G.SLOTS = [(48.0, 19.5, 65.5, 22.5)]          # 17.5 x 3 mm, under R1 / R5 (600 V across each)

# ── Placement (mm from the top-left corner; orientation: 90 turns +x into -y) ─
P = {
    "J3": (8.0, 8.4, 0), "J4": (28.5, 8.4, 0),                       # PROBE_A, PROBE_B, entry from top
    "D4": (8.0, 17.0, 270), "D1": (17.52, 27.16, 90),                # PA: K/A on top row
    "D3": (28.5, 27.16, 90), "D2": (38.02, 17.0, 270),               # PB
    "F1": (37.5, 40.0, 0),                                           # clip A (BP) x 13-32, clip B (HVp) 43-62
    # fast path pocket
    "R_fast1": (70.84, 24.0, 270),   # body on HVp pad, FAST_TF pad below (70.84, 34.16)
    "TF1": (78.34, 24.0, 0),         # body on FAST_TF pad, 0.5 mm from R_fast1; DRAIN pad (88.5, 24)
    "Q2": (88.5, 14.0, 0),           # G 83.42, D 88.5, S 93.58; tab up, HS-S01 clipped behind it
    "R1": (56.0, 26.0, 90), "R5": (62.0, 26.0, 90),                  # HVp pad below the slot, body above
    # gate drive (LV)
    "R2": (52.0, 10.0, 90), "R3": (58.0, 9.0, 0), "Q1": (66.0, 10.0, 0),
    "D9": (74.5, 12.5, 90), "R4": (77.0, 15.84, 0), "C_byp2": (79.0, 9.0, 90),
    # slow path: standing, bodies on y = 55, pad 2 below
    "R_slow1": (58.0, 55.0, 270), "R_slow2": (47.0, 55.0, 270), "R_slow3": (36.0, 55.0, 270),
    "R_slow4": (25.0, 55.0, 270), "R_slow5": (14.0, 55.0, 270),            # 2.3 mm air between bodies
    # indicator side
    "D_LED1": (94.5, 57.5, 270), "J6": (94.5, 69.96, 90), "D_clamp2": (89.0, 67.0, 270),
    "R_sig_bot1": (80.0, 67.5, 270), "R_sig_bot2": (76.0, 67.5, 270),
    "D_clamp1": (72.0, 70.5, 90), "J5": (66.0, 70.0, 90),
    "H1": (5.5, 69.5, 0), "H3": (94.0, 40.0, 0),     # nylon M3; H2/H4 don't fit on this board
}
for i in range(5):   # staircases, 5 mm right and 5.08 mm down per resistor
    P[f"R_sig{i + 1}"] = (66.0 + 5 * i, 44.0 + 5.08 * i, 270)
for i in range(4):
    P[f"R_LED{i + 1}"] = (75.0 + 5 * i, 44.0 + 5.08 * i, 270)
G.PLACE = P

# ── Routes, all on B.Cu: (net, width, [points]) ─────────────────────────────
HVW, SW, LW = 1.5, 0.8, 0.6
R = [
    # GND ring: D4 anode → left edge → bottom → right → top → down to D2 anode
    ("/GND", HVW, [(8.0, 27.16), (2.5, 27.16), (2.5, 72.5), (97.5, 72.5), (97.5, 2.5), (46.5, 2.5),
                   (46.5, 27.16), (38.02, 27.16)]),
    # probes: both terminal poles and both diodes of each probe
    ("/PROBE_A", HVW, [(8.0, 8.4), (8.0, 17.0), (17.52, 17.0), (17.52, 8.4)]),
    ("/PROBE_B", HVW, [(28.5, 8.4), (28.5, 17.0), (38.02, 17.0), (38.02, 8.4)]),
    ("/BRIDGE_P", HVW, [(17.52, 27.16), (28.5, 27.16)]),
    ("/BRIDGE_P", HVW, [(23.0, 27.16), (23.0, 40.0)]),
    # HVp hub (F1 clip B) → R1, R5, R_fast1 / R_slow1 / chains
    ("/HVp", HVW, [(56.0, 40.0), (56.0, 26.0), (62.0, 26.0), (68.0, 26.0), (70.84, 24.0)]),
    ("/HVp", HVW, [(58.0, 40.0), (58.0, 55.0)]),
    ("/HVp", HVW, [(61.0, 40.0), (64.0, 42.0), (66.0, 44.0), (75.0, 44.0)]),
    # fast path
    ("Net-(R_fast1-Pad2)", HVW, [(70.84, 34.16), (78.34, 34.16), (78.34, 24.0)]),
    ("Net-(Q2-D)", HVW, [(88.5, 24.0), (88.5, 14.0)]),
    ("/GND", HVW, [(93.58, 14.0), (97.5, 14.0)]),
    # slow chain links (pad 2 of one → pad 1 of the next)
    *[(f"Net-(R_slow{i + 1}-Pad2)", HVW, [(P[f"R_slow{i + 1}"][0], 65.16), P[f"R_slow{i + 2}"][:2]])
      for i in range(4)],
    ("/GND", HVW, [(14.0, 65.16), (14.0, 72.5)]),
    # divider + LED staircases
    *[(f"Net-(R_sig{i + 1}-Pad2)", SW, [(66.0 + 5 * i, 49.08 + 5.08 * i), (71.0 + 5 * i, 49.08 + 5.08 * i)])
      for i in range(4)],
    *[(f"Net-(R_LED{i + 1}-Pad2)", SW, [(75.0 + 5 * i, 49.08 + 5.08 * i), (80.0 + 5 * i, 49.08 + 5.08 * i)])
      for i in range(3)],
    ("Net-(D_LED1-K)", LW, [(90.0, 64.32), (94.5, 57.5)]),
    ("/LED_A", LW, [(94.5, 62.58), (94.5, 67.46)]),
    ("/LED_A", LW, [(89.0, 67.0), (94.5, 67.46)]),
    ("/GND", LW, [(94.5, 69.96), (94.5, 72.5)]),
    ("/GND", LW, [(89.0, 72.08), (89.0, 72.5)]),
    ("/SIGOUT", LW, [(86.0, 69.4), (84.0, 67.5), (80.0, 67.5), (76.0, 67.5), (72.0, 67.5), (66.0, 67.5),
                     (66.0, 70.0)]),
    ("/SIGOUT", LW, [(72.0, 67.5), (72.0, 65.42)]),
    *[("/GND", LW, [(x, y), (x, 72.5)]) for x, y in ((80.0, 70.04), (76.0, 70.04), (72.0, 70.5), (68.54, 70.0))],
    # gate drive
    ("/BASE_DIV", LW, [(56.0, 15.84), (56.0, 12.0), (52.0, 10.0)]),
    ("/BASE_DIV", LW, [(56.0, 12.0), (58.0, 9.0)]),
    ("Net-(Q1-B)", LW, [(60.54, 9.0), (60.54, 12.5), (68.54, 12.5), (68.54, 10.0)]),
    ("/GATE_TOP", LW, [(62.0, 15.84), (71.08, 15.84), (74.5, 15.84), (77.0, 15.84)]),
    ("/GATE_TOP", LW, [(71.08, 15.84), (71.08, 10.0)]),
    ("/GATE_TOP", LW, [(74.5, 15.84), (74.5, 12.5)]),
    ("/GATE", LW, [(79.54, 15.84), (81.5, 14.0), (83.42, 14.0)]),
    ("/GATE", LW, [(79.0, 9.0), (79.54, 11.0), (79.54, 15.84)]),
    *[("/GND", LW, [(x, y), (x, 2.5)]) for x, y in ((52.0, 7.46), (66.0, 10.0), (74.5, 7.42), (79.0, 3.92))],
]
G.PREROUTES = [(net, "B.Cu", w, pts) for net, w, pts in R]
G.VIAS = []

Q2_RULE = """
# Q2 (TO-220): legs bent out to 5.08 mm; the device is rated 800 V between its pins.
(rule "Q2 pin field"
    (condition "(A.intersectsCourtyard('Q2') || B.intersectsCourtyard('Q2')) && (A.NetName == 'Net-(Q2-D)' || B.NetName == 'Net-(Q2-D)')")
    (constraint clearance (min 2.5mm)))
"""


def main():
    if not os.path.exists(G.PRO):
        shutil.copy(os.path.join(HERE, "CapacitorDischarger.kicad_pro"), G.PRO)
    G.write_project_settings()
    if os.path.exists(G.PCB):
        os.remove(G.PCB)
    board = G.build_board()
    # home-made board: no silkscreen print, so references go to the assembly (Fab) drawing
    for fp in board.GetFootprints():
        fp.Reference().SetLayer(pcbnew.F_Fab)
    pcbnew.SaveBoard(G.PCB, board)
    nets = [n for n in board.GetNetsByName().keys()]
    open(os.path.join(HERE, G.NAME + ".kicad_dru"), "w", encoding="utf8", newline="\n").write(
        hv_rules.dru([str(n) for n in nets], Q2_RULE))
    rpt = os.path.join(HERE, "drc_1s.rpt")
    subprocess.run([G.CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "-o", rpt, G.PCB],
                   capture_output=True)
    print(open(rpt, encoding="utf8").read()[-1500:])


if __name__ == "__main__":
    main()
