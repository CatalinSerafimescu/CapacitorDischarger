"""Full 600V Capacitor Discharger schematic — schemdraw SVG.

Layout (left to right):
  Bridge → F1 → HV+ bus → Branch1(R_slow) | Branch2(R_fast+Q2) | Branch3(Q1 threshold)
                         | Branch4(LED) | Branch5(DVM sig divider 10 000:1 + clamp)
  → J5 → DVM1 Axiomet PM-128 (off-board), powered by floating BT1 9 V battery

HV section: bridge + R_slow + R_fast/TF1/Q2 + gate drive (R5/D9)
LV section: Q1 threshold, LED indicator, DVM divider, J5 → PM-128

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
    HV_BUS_END = 44     # GND bus / connector leads extend further right

    # F1 — protection fuse: opens on single-fault (Q1/D9 failure → Q2 full-on at 600V)
    # Starts at x=4, after the bridge top rail ends, so the bridge cannot bypass it.
    F1e = d.add(elm.Fuse().right().at((4, HV_Y)).length(3))
    d.add(elm.Label().at(((4 + F1e.end[0]) / 2, HV_Y + 0.5))
          .label(LABEL['F1'], halign='center', valign='bottom'))
    B5_X = 33           # DVM divider — last branch on the HV+ bus
    d.add(elm.Line().right().at(F1e.end).tox(B5_X))   # HV+ bus ends at last branch
    d.add(elm.Label().at((F1e.end[0] + 1.5, HV_Y + 0.5)).label('HV+'))
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
    # GATE DRIVE — R5 (470 kΩ) pull-up; D9 shunt clamp to GND holds
    # gate ≤12 V; C_byp2 gate RC filter
    # HV+ → R5 → GATE_CTRL node ── D9 (shunt to GND) ∥ C_byp2 (shunt to GND)
    # ═══════════════════════════════════════════════════════════════
    R5_X = 11
    d.add(elm.Dot().at((R5_X, HV_Y)))
    R5e = d.add(elm.Resistor().down().at((R5_X, HV_Y)).length(EL))
    rlabel(d, R5_X, HV_Y, R5e.end[1], LABEL['R5'])
    GATE_CTRL_NODE = R5e.end
    d.add(elm.Dot(open=True).at(GATE_CTRL_NODE).label('GATE_CTRL', loc='right'))

    # D9 — Zener shunt clamp, cathode at GATE_CTRL (top), anode to GND (bottom)
    D9_X = R5_X - 2
    d.add(elm.Line().left().at(GATE_CTRL_NODE).tox(D9_X))
    d.add(elm.Dot().at((D9_X, GATE_CTRL_NODE[1])))
    D9e = d.add(elm.Zener().up().at((D9_X, GATE_CTRL_NODE[1] - EL)).length(EL))
    rlabel(d, D9_X, GATE_CTRL_NODE[1], GATE_CTRL_NODE[1] - EL, LABEL['D9'])
    d.add(elm.Line().down().at((D9_X, GATE_CTRL_NODE[1] - EL)).toy(GND_Y))
    d.add(elm.Dot().at((D9_X, GND_Y)))

    # C_byp2 — 100 nF gate RC filter (τ = R5 × C ≈ 47 ms, soft Q2 turn-on)
    CBP2 = d.add(elm.Capacitor().down().at(GATE_CTRL_NODE).length(EL))
    rlabel(d, R5_X, GATE_CTRL_NODE[1], CBP2.end[1], LABEL['C_byp2'])
    d.add(elm.Line().down().at(CBP2.end).toy(GND_Y))
    d.add(elm.Dot().at((R5_X, GND_Y)))
    d.add(elm.Line().right().at((D9_X, GND_Y)).tox(R5_X))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 2 — R_fast (50 Ω / 7 W) + TF1 thermal cutoff + Q2 N-MOSFET (STP10NK80Z)
    # ═══════════════════════════════════════════════════════════════
    B2_X = 14
    d.add(elm.Dot().at((B2_X, HV_Y)))
    RF = d.add(elm.Resistor().down().at((B2_X, HV_Y)).length(EL))
    rlabel(d, B2_X, HV_Y, RF.end[1], LABEL['R_fast'])

    # TF1 — one-shot thermal cutoff clamped to the R_fast body: opens if a live
    # supply below the threshold keeps Q2 on (R_fast overload that F1 can't see)
    TF1e = d.add(elm.Fuse().down().at(RF.end).length(EL))
    rlabel(d, B2_X, RF.end[1], TF1e.end[1], LABEL['TF1'])

    # NFet.right(): drain=top, source=bottom, gate to the right
    q2 = d.add(elm.NFet().right().anchor('drain').at(TF1e.end)
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
    # BRANCH 3 — Q1 NPN Threshold Detector (~63 V switch point)
    # R1 (1 MΩ) → node_A → R2 (10 kΩ) → GND
    #             node_A → R3 (10 kΩ) → Q1 base
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
    # HV+ → R_LED1–R_LED4 (4 × 100 kΩ/0.6 W) → D_LED (BZX55C8V2, 8.2 V)
    #      → LED1 (red, Vf ≈ 2 V) → GND
    # ═══════════════════════════════════════════════════════════════
    B4_X = 28
    d.add(elm.Dot().at((B4_X, HV_Y)))
    cur = (B4_X, HV_Y)
    for i in range(1, 5):
        top = cur[1]
        r = d.add(elm.Resistor().down().at(cur).length(EL))
        rlabel(d, B4_X, top, r.end[1], LABEL[f'R_LED{i}'])
        cur = r.end
    DZ_top = cur[1]
    DZ_bot_y = DZ_top - EL
    DZ  = d.add(elm.Zener().up().at((B4_X, DZ_bot_y)).length(EL))
    rlabel(d, B4_X, DZ_top, DZ_bot_y, LABEL['D_LED'])
    L1_top = DZ_bot_y
    L1  = d.add(elm.LED().down().at((B4_X, DZ_bot_y)).length(EL))
    rlabel(d, B4_X, L1_top, L1.end[1], LABEL['LED1'])
    d.add(elm.Line().down().at(L1.end).toy(GND_Y))
    d.add(elm.Dot().at((B4_X, GND_Y)))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 5 — DVM Signal Divider 10 000:1  (600 V → 60 mV, PM-128 reads "600")
    # HV+ → 5 × 100 kΩ/0.6 W → node_sig → R_sig_bot1 ∥ R_sig_bot2 (2 × 100 Ω = 50 Ω) → GND
    # D_clamp across them: if the bottom opens, node_sig is held ≤ ~0.7 V
    # ═══════════════════════════════════════════════════════════════
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
    rlabel(d, B5_X, RSB_top, RSB.end[1], LABEL['R_sig_bot1'])
    d.add(elm.Line().down().at(RSB.end).toy(GND_Y))
    d.add(elm.Dot().at((B5_X, GND_Y)))

    # R_sig_bot2 — second 100 Ω in parallel with R_sig_bot1
    RSB2_X = B5_X + 3
    d.add(elm.Line().right().at(NODE_SIG).tox(RSB2_X))
    d.add(elm.Dot().at((RSB2_X, NODE_SIG[1])))
    RSB2 = d.add(elm.Resistor().down().at((RSB2_X, NODE_SIG[1])).length(EL))
    rlabel(d, RSB2_X, RSB_top, RSB2.end[1], LABEL['R_sig_bot2'])
    d.add(elm.Line().down().at(RSB2.end).toy(GND_Y))
    d.add(elm.Dot().at((RSB2_X, GND_Y)))

    # D_clamp — anode at node_sig, cathode to GND (parallel to R_sig_bot1/2)
    DCL_X = B5_X + 6
    d.add(elm.Line().right().at((RSB2_X, NODE_SIG[1])).tox(DCL_X))
    d.add(elm.Dot().at((DCL_X, NODE_SIG[1])))
    DCL = d.add(elm.Diode().down().at((DCL_X, NODE_SIG[1])).length(EL))
    rlabel(d, DCL_X, NODE_SIG[1], DCL.end[1], LABEL['D_clamp'])
    d.add(elm.Line().down().at(DCL.end).toy(GND_Y))
    d.add(elm.Dot().at((DCL_X, GND_Y)))

    # ═══════════════════════════════════════════════════════════════
    # J5 (2-pin) → DVM1 Axiomet PM-128 (off-board, panel-mounted)
    # PM-128 requires the supply and the measured input to have SEPARATE
    # grounds: BT1 (9 V, holder with ON/OFF switch) powers only the meter and
    # is NOT connected to circuit GND (floating). Circuit GND → meter IN GND.
    # ═══════════════════════════════════════════════════════════════
    CONN_X = HV_BUS_END + 0.5
    CONN_W = 6.0
    PIN_SIG_Y = NODE_SIG[1]
    PIN_GND_Y = GND_Y
    PIN_VP_Y  = HV_Y - 1.5 * EL
    PIN_VM_Y  = HV_Y - 3.0 * EL
    BOX_TOP = PIN_VP_Y + 1.8
    BOX_BOT = PIN_GND_Y - 0.8

    d.add(elm.Line().right().at((DCL_X, NODE_SIG[1])).tox(CONN_X))
    d.add(elm.Line().right().at((DCL_X, GND_Y)).tox(CONN_X))   # circuit GND → meter IN GND
    d.add(elm.Label().at((CONN_X - 2.5, PIN_SIG_Y + 0.4)).label('J5', halign='center', valign='bottom'))

    # Meter box outline
    d.add(elm.Line().right().at((CONN_X, BOX_TOP)).tox(CONN_X + CONN_W))
    d.add(elm.Line().down().at((CONN_X + CONN_W, BOX_TOP)).toy(BOX_BOT))
    d.add(elm.Line().left().at((CONN_X + CONN_W, BOX_BOT)).tox(CONN_X))
    d.add(elm.Line().up().at((CONN_X, BOX_BOT)).toy(BOX_TOP))
    for py in [PIN_GND_Y, PIN_SIG_Y]:
        d.add(elm.Line().right().at((CONN_X, py)).length(0.7))
        d.add(elm.Dot().at((CONN_X + 0.7, py)))
    d.add(elm.Label().at(((2 * CONN_X + CONN_W) / 2, BOX_TOP + 1.2))
          .label('DVM1  Axiomet PM-128\n200 mV FS, reads "600" at 600 V'))
    d.add(elm.Label().at((CONN_X + 0.9, PIN_SIG_Y)).label('VIN  (60 mV @ 600 V)', loc='right'))
    d.add(elm.Label().at((CONN_X + 0.9, PIN_GND_Y)).label('IN GND', loc='right'))

    # Floating battery loop on the meter's right side (supply pins)
    BOXR = CONN_X + CONN_W
    for py in [PIN_VP_Y, PIN_VM_Y]:
        d.add(elm.Dot().at((BOXR, py)))
    d.add(elm.Label().at((BOXR - 0.3, PIN_VP_Y)).label('+9V', halign='right', valign='center'))
    d.add(elm.Label().at((BOXR - 0.3, PIN_VM_Y)).label('−9V', halign='right', valign='center'))
    BAT_X = BOXR + 3
    d.add(elm.Line().right().at((BOXR, PIN_VP_Y)).tox(BAT_X))
    SW = d.add(elm.Switch().down().at((BAT_X, PIN_VP_Y)).length(EL))
    d.add(elm.Label().at((BAT_X + LABEL_OFST, (PIN_VP_Y + SW.end[1]) / 2))
          .label('ON/OFF\n(in holder)', halign='left', valign='center'))
    # .reverse() keeps the long bar (+) at the top, toward the switch
    BAT = d.add(elm.Battery().down().at(SW.end).toy(PIN_VM_Y).reverse())
    d.add(elm.Label().at((BAT_X + LABEL_OFST, (SW.end[1] + PIN_VM_Y) / 2))
          .label(LABEL['BT1'] + '\nfloating — NOT\ntied to circuit GND', halign='left', valign='center'))
    d.add(elm.Line().left().at((BAT_X, PIN_VM_Y)).tox(BOXR))

    # ─────────────────────────────────────────────────────────────
    d.save('E:/Catalin/Work/Electronics/CapacitorDischarger_Claude/blocks/full_schematic.svg')

print("Saved: blocks/full_schematic.svg")
