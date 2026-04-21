"""Full 600V Capacitor Discharger schematic — schemdraw SVG.

Layout (left to right):
  Bridge → HV+ bus → Branch1(R_slow) | Branch2(R_fast+Q2) | Branch3(Q1 threshold)
                    | Branch4(LED) | Branch5(DVM sig divider) | Branch6(DVM Vcc dropper)
  → Voltmeter 3-pin connector

HV section: bridge + R_slow + R_fast/Q2 + gate drive (R5/D9)
LV section: Q1 threshold, LED indicator, DVM divider, DVM Vcc, connector

NFet.right() orientation: drain up, source down, gate to the right.
BjtNpn orientation: base left, collector upper-right, emitter lower-right.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import schemdraw
import schemdraw.elements as elm
from bom import LABEL

schemdraw.use('svg')

HV_Y  = 22   # y-coordinate of HV+ bus
GND_Y = 0    # y-coordinate of GND bus
EL    = 2.5  # standard element length

LABEL_OFST = 0.65   # horizontal gap: element column → label anchor

def rlabel(d, col_x, top_y, bot_y, text):
    """Place a label to the right of a vertical element."""
    mid_y = (top_y + bot_y) / 2
    d.add(elm.Label().at((col_x + LABEL_OFST, mid_y)).label(text, halign='left', valign='center'))

with schemdraw.Drawing(show=False) as d:
    d.config(fontsize=9, inches_per_unit=0.43)

    # ═══════════════════════════════════════════════════════════════
    # DIODE BRIDGE — D1–D4 (1N4007)  Reverse-polarity protection
    # ═══════════════════════════════════════════════════════════════
    MID_Y = (HV_Y + GND_Y) / 2   # 11

    # Left column: D4(GND→PROBE_A), D1(PROBE_A→HV+)
    d.add(elm.Diode().up().at((0, GND_Y)).length(MID_Y))
    rlabel(d, 0, MID_Y, GND_Y, LABEL['D4'])
    d.add(elm.Diode().up().at((0, MID_Y)).length(MID_Y))
    rlabel(d, 0, HV_Y, MID_Y, LABEL['D1'])

    # Right column: D2(GND→PROBE_B), D3(PROBE_B→HV+)
    d.add(elm.Diode().up().at((4, GND_Y)).length(MID_Y))
    d.add(elm.Label().at((4 - LABEL_OFST, (GND_Y + MID_Y) / 2)).label(LABEL['D2'], halign='right', valign='center'))
    d.add(elm.Diode().up().at((4, MID_Y)).length(MID_Y))
    d.add(elm.Label().at((4 - LABEL_OFST, (MID_Y + HV_Y) / 2)).label(LABEL['D3'], halign='right', valign='center'))

    # PROBE_A / PROBE_B terminals
    d.add(elm.Dot().at((0, MID_Y)))
    d.add(elm.Line().left(1.5).at((0, MID_Y)))
    d.add(elm.Dot(open=True).at((-1.5, MID_Y)).label('PROBE_A', loc='left'))

    d.add(elm.Dot().at((4, MID_Y)))
    d.add(elm.Line().right(1.5).at((4, MID_Y)))
    d.add(elm.Dot(open=True).at((5.5, MID_Y)).label('PROBE_B', loc='right'))

    # Top bridge rail: D1 cathode ── D3 cathode
    d.add(elm.Line().right().at((0, HV_Y)).tox(4))
    d.add(elm.Dot().at((2, HV_Y)))

    # Bottom bridge rail: D4 anode ── D2 anode
    d.add(elm.Line().right().at((0, GND_Y)).tox(4))
    d.add(elm.Ground().at((2, GND_Y)))

    # ═══════════════════════════════════════════════════════════════
    # HV+ BUS and GND BUS
    # ═══════════════════════════════════════════════════════════════
    B6_X = 38           # last branch — defines right end of HV+ bus
    HV_BUS_END = 42     # GND bus / connector leads extend further right
    d.add(elm.Line().right().at((2, HV_Y)).tox(B6_X))   # HV+ bus ends at last branch
    d.add(elm.Label().at((3.5, HV_Y + 0.5)).label('HV+'))
    d.add(elm.Line().right().at((2, GND_Y)).tox(HV_BUS_END))

    # Section labels above the HV+ bus
    d.add(elm.Label().at((9,  HV_Y + 1.8)).label('── HV SECTION ──'))
    d.add(elm.Label().at((30, HV_Y + 1.8)).label('── LV SECTION ──'))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 1 — R_slow: 5 × 4.7 kΩ / 5 W wirewound  (always-on)
    # ═══════════════════════════════════════════════════════════════
    B1_X = 7
    d.add(elm.Dot().at((B1_X, HV_Y)))
    cur = (B1_X, HV_Y)
    for i in range(1, 6):
        top = cur[1]
        r = d.add(elm.Resistor().down().at(cur).length(EL))
        rlabel(d, B1_X, top, r.end[1], LABEL[f'R_slow{i}'])
        cur = r.end
    d.add(elm.Line().down().at(cur).toy(GND_Y))
    d.add(elm.Dot().at((B1_X, GND_Y)))

    # ═══════════════════════════════════════════════════════════════
    # GATE DRIVE — R5 (470 kΩ) pull-up + D9 (12 V Zener) clamp
    # HV+ → R5 → D9 → GATE_CTRL
    # ═══════════════════════════════════════════════════════════════
    R5_X = 11
    d.add(elm.Dot().at((R5_X, HV_Y)))
    R5e = d.add(elm.Resistor().down().at((R5_X, HV_Y)).length(EL))
    rlabel(d, R5_X, HV_Y, R5e.end[1], LABEL['R5'])
    D9e = d.add(elm.Zener().down().length(EL))
    rlabel(d, R5_X, R5e.end[1], D9e.end[1], LABEL['D9'])
    d.add(elm.Dot(open=True).at(D9e.end).label('GATE_CTRL', loc='right'))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 2 — R_fast (50 Ω / 5 W) + Q2 N-MOSFET (STF7NM80)
    # ═══════════════════════════════════════════════════════════════
    B2_X = 14
    d.add(elm.Dot().at((B2_X, HV_Y)))
    RF = d.add(elm.Resistor().down().at((B2_X, HV_Y)).length(EL))
    rlabel(d, B2_X, HV_Y, RF.end[1], LABEL['R_fast'])

    # NFet.right(): drain=top, source=bottom, gate to the right
    q2 = d.add(elm.NFet().right().anchor('drain').at(RF.end)
               .label(LABEL['Q2'], loc='left'))

    # Q2 source → GND
    d.add(elm.Line().down().at(q2.source).toy(GND_Y))
    d.add(elm.Dot().at((q2.source[0], GND_Y)))

    # R4 (100 Ω gate series) from Q2.gate rightward → GATE_CTRL net
    R4e = d.add(elm.Resistor().right().at(q2.gate).length(EL))
    d.add(elm.Label().at(((q2.gate[0] + R4e.end[0]) / 2, q2.gate[1] + 0.4))
          .label(LABEL['R4'], halign='center', valign='bottom'))
    d.add(elm.Dot(open=True).at(R4e.end).label('GATE_CTRL', loc='right'))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 3 — Q1 NPN Threshold Detector (71 V switch point)
    # R1 (1 MΩ) → node_A → R2 (10 kΩ) → GND
    #             node_A → R3 (100 kΩ) → Q1 base
    #             Q1 emitter → GND,  Q1 collector → GATE_CTRL
    # ═══════════════════════════════════════════════════════════════
    B3_X = 20
    d.add(elm.Dot().at((B3_X, HV_Y)))
    R1e = d.add(elm.Resistor().down().at((B3_X, HV_Y)).length(EL))
    rlabel(d, B3_X, HV_Y, R1e.end[1], LABEL['R1'])
    d.add(elm.Dot().at(R1e.end))
    NODE_A = R1e.end

    R2e = d.add(elm.Resistor().down().length(EL))
    rlabel(d, B3_X, NODE_A[1], R2e.end[1], LABEL['R2'])
    d.add(elm.Line().down().at(R2e.end).toy(GND_Y))
    d.add(elm.Dot().at((B3_X, GND_Y)))

    # R3: node_A → rightward → Q1 base
    R3e = d.add(elm.Resistor().right().at(NODE_A).length(EL))
    d.add(elm.Label().at((R3e.end[0] + 0.1, NODE_A[1] + 0.4))
          .label(LABEL['R3'], halign='left', valign='bottom'))

    # Q1 NPN — base anchored at R3 end
    q1 = d.add(elm.BjtNpn(circle=True).anchor('base').at(R3e.end)
               .label(LABEL['Q1'], loc='right'))

    # Q1 emitter → GND
    d.add(elm.Line().down().at(q1.emitter).toy(GND_Y))
    d.add(elm.Dot().at((q1.emitter[0], GND_Y)))

    # Q1 collector → GATE_CTRL
    d.add(elm.Line().up().at(q1.collector).length(2.5))
    COLL_TOP = (q1.collector[0], q1.collector[1] + 2.5)
    d.add(elm.Dot(open=True).at(COLL_TOP).label('GATE_CTRL', loc='right'))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 4 — LED Danger Indicator (~10.2 V cutoff)
    # HV+ → R_LED1–R_LED3 (3 × 100 kΩ/0.6 W) → D_LED (BZX55C8V2, 8.2 V)
    #      → LED1 (red, Vf ≈ 2 V) → GND
    # ═══════════════════════════════════════════════════════════════
    B4_X = 28
    d.add(elm.Dot().at((B4_X, HV_Y)))
    cur = (B4_X, HV_Y)
    for i in range(1, 4):
        top = cur[1]
        r = d.add(elm.Resistor().down().at(cur).length(EL))
        rlabel(d, B4_X, top, r.end[1], LABEL[f'R_LED{i}'])
        cur = r.end
    DZ_top = cur[1]
    DZ  = d.add(elm.Zener().down().at(cur).length(EL))
    rlabel(d, B4_X, DZ_top, DZ.end[1], LABEL['D_LED'])
    L1_top = DZ.end[1]
    L1  = d.add(elm.LED().down().length(EL))
    rlabel(d, B4_X, L1_top, L1.end[1], LABEL['LED1'])
    d.add(elm.Line().down().at(L1.end).toy(GND_Y))
    d.add(elm.Dot().at((B4_X, GND_Y)))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 5 — DVM Signal Divider 6:1  (0–600 V → 0–100 V)
    # HV+ → 5 × 100 kΩ/0.6 W → node_sig → 100 kΩ → GND
    # ═══════════════════════════════════════════════════════════════
    B5_X = 33
    d.add(elm.Dot().at((B5_X, HV_Y)))
    cur = (B5_X, HV_Y)
    for i in range(1, 6):
        top = cur[1]
        r = d.add(elm.Resistor().down().at(cur).length(EL))
        rlabel(d, B5_X, top, r.end[1], LABEL[f'R_sig{i}'])
        cur = r.end
    NODE_SIG = cur
    d.add(elm.Dot().at(NODE_SIG))
    RSB_top = NODE_SIG[1]
    RSB = d.add(elm.Resistor().down().at(NODE_SIG).length(EL))
    rlabel(d, B5_X, RSB_top, RSB.end[1], LABEL['R_sig_bot'])
    d.add(elm.Line().down().at(RSB.end).toy(GND_Y))
    d.add(elm.Dot().at((B5_X, GND_Y)))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 6 — DVM Vcc Dropper (parasitic, 15 V regulated)
    # HV+ → 4 × 15 kΩ/3 W → node_Vcc → D_Vcc(15 V Z) ∥ C_Vcc(10 µF) → GND
    # ═══════════════════════════════════════════════════════════════
    d.add(elm.Dot().at((B6_X, HV_Y)))
    cur = (B6_X, HV_Y)
    for i in range(1, 5):
        top = cur[1]
        r = d.add(elm.Resistor().down().at(cur).length(EL))
        rlabel(d, B6_X, top, r.end[1], LABEL[f'R_drop{i}'])
        cur = r.end
    NODE_VCC = cur
    d.add(elm.Dot().at(NODE_VCC))

    # D_Vcc Zener on main column
    DVcc_top = NODE_VCC[1]
    DVcc = d.add(elm.Zener().down().at(NODE_VCC).length(EL))
    rlabel(d, B6_X, DVcc_top, DVcc.end[1], LABEL['D_Vcc'])
    d.add(elm.Line().down().at(DVcc.end).toy(GND_Y))
    d.add(elm.Dot().at((B6_X, GND_Y)))

    # C_Vcc in parallel — one column to the left
    CVCC_X = B6_X - 2
    d.add(elm.Line().left().at(NODE_VCC).tox(CVCC_X))
    d.add(elm.Dot().at((CVCC_X, NODE_VCC[1])))
    CVcc_top = NODE_VCC[1]
    CVcc = d.add(elm.Capacitor().down().at((CVCC_X, NODE_VCC[1])).length(EL))
    d.add(elm.Label().at((CVCC_X + LABEL_OFST, (CVcc_top + CVcc.end[1]) / 2))
          .label(LABEL['C_Vcc'], halign='left', valign='center'))
    d.add(elm.Line().down().at(CVcc.end).toy(GND_Y))
    d.add(elm.Line().right().at((CVCC_X, GND_Y)).tox(B6_X))

    # ═══════════════════════════════════════════════════════════════
    # VOLTMETER — 3-pin connector (GND / Signal / Vcc)
    # ═══════════════════════════════════════════════════════════════
    CONN_X = HV_BUS_END + 0.5
    CONN_W = 5.0

    PIN_GND_Y = GND_Y
    PIN_SIG_Y = NODE_SIG[1]
    PIN_VCC_Y = NODE_VCC[1]

    BOX_TOP = PIN_VCC_Y + 1.8
    BOX_BOT = PIN_GND_Y - 0.8

    # Lead wires from circuit nodes to connector left edge
    d.add(elm.Line().right().at(NODE_SIG).tox(CONN_X))
    d.add(elm.Line().right().at(NODE_VCC).tox(CONN_X))
    d.add(elm.Line().right().at((B6_X, GND_Y)).tox(CONN_X))

    # Connector box outline
    d.add(elm.Line().right().at((CONN_X, BOX_TOP)).tox(CONN_X + CONN_W))
    d.add(elm.Line().down().at((CONN_X + CONN_W, BOX_TOP)).toy(BOX_BOT))
    d.add(elm.Line().left().at((CONN_X + CONN_W, BOX_BOT)).tox(CONN_X))
    d.add(elm.Line().up().at((CONN_X, BOX_BOT)).toy(BOX_TOP))

    # Pin stubs
    for py in [PIN_GND_Y, PIN_SIG_Y, PIN_VCC_Y]:
        d.add(elm.Line().right().at((CONN_X, py)).length(0.7))
        d.add(elm.Dot().at((CONN_X + 0.7, py)))

    # Connector labels
    d.add(elm.Label().at(((2 * CONN_X + CONN_W) / 2, BOX_TOP + 1.2))
          .label('VOLTMETER\n(3-pin connector)'))
    d.add(elm.Label().at((CONN_X + 0.9, PIN_VCC_Y)).label('Vcc  15 V', loc='right'))
    d.add(elm.Label().at((CONN_X + 0.9, PIN_SIG_Y)).label('Signal  0–100 V', loc='right'))
    d.add(elm.Label().at((CONN_X + 0.9, PIN_GND_Y)).label('GND', loc='right'))

    # ─────────────────────────────────────────────────────────────
    d.save('E:/Catalin/Work/Electronics/CapacitorDischarger_Claude/blocks/full_schematic.svg')

print("Saved: blocks/full_schematic.svg")
