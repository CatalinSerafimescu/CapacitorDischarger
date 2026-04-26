"""
Bill of Materials — 600V Capacitor Discharger
Single source of truth for component data, schematic labels, and procurement status.

To update a component:  edit the entry here; the schematic regenerates automatically.
To print a buy list:    python bom.py

status values
  'sourced'          — in hand (from TME order 2026-04-15 or prior stock)
  'sourced_partial'  — can be built from sourced parts (see notes)
  'sourced_unused'   — ordered but not placed in this design
  'buy'              — must be ordered
"""

# ─── BOM entries ─────────────────────────────────────────────────────────────
# refs            list of reference designators (empty = not placed on schematic)
# value           human-readable value / rating string
# schematic_label short multi-line text shown on schematic (None = auto "ref\nvalue")
# description     full component spec for procurement / datasheet lookup
# part_number     sourced or suggested part number
# qty             quantity needed in the design
# status          see above
# notes           extra info, substitution rules, stress calculations
# ─────────────────────────────────────────────────────────────────────────────

BOM = [

    # ══ REVERSE POLARITY BRIDGE ══════════════════════════════════════════════
    {
        "refs": ["D1", "D2", "D3", "D4"],
        "value": "1N4007",
        "schematic_label": None,       # auto → "D1\n1N4007" etc.
        "description": "Diode, rectifier, 1 A, 1000 V PIV, DO-41, THT",
        "part_number": "1N4007",
        "qty": 4,
        "status": "buy",
        "notes": "Full-bridge for reverse-polarity protection. PIV 1000 V gives 400 V margin over 600 V rail.",
    },

    # ══ SLOW DISCHARGE PATH ══════════════════════════════════════════════════
    {
        "refs": ["R_slow1", "R_slow2", "R_slow3", "R_slow4", "R_slow5"],
        "value": "4.7 kΩ / 5 W",
        "schematic_label": "4.7kΩ/5W",
        "description": "Resistor, wirewound, 4.7 kΩ, 5 W, ±5%, axial THT",
        "part_number": "Ohmite WN5S4R70JE  (alt: Vishay RS5-4K7-J)",
        "qty": 5,
        "status": "buy",
        "notes": (
            "5 in series = 23.5 kΩ / 25 W / 1750 V working voltage. "
            "At 600 V: 25.5 mA, 3.06 W per resistor (61% of 5 W rating). "
            "Each resistor sees 120 V (well under 350 V part limit). "
            "Mount axial on ≥3 mm PCB standoff, in a row for airflow."
        ),
    },

    # ══ FAST DISCHARGE PATH ══════════════════════════════════════════════════
    {
        "refs": ["R_fast"],
        "value": "50 Ω / 5 W",
        "schematic_label": "50Ω/5W",
        "description": "Resistor, wirewound, 50 Ω, 5 W, ±5%, axial THT",
        "part_number": "Ohmite WN5S50RJE  (alt: Vishay RS5-50R-J)",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Peak dissipation ≈ 100 W for τ = 50 Ω × C_cap ms at switch-on (V_cap = 71 V). "
            "Energy for 1 mF cap = 2.5 J — well within TO-220 SOA."
        ),
    },
    {
        "refs": ["Q2"],
        "value": "STP10NK80Z",
        "schematic_label": "STP10NK80Z\n800V 9A",
        "description": "MOSFET, N-channel, 800 V, 9 A, R_ds(on) 0.9 Ω typ, TO-220, THT",
        "part_number": "STP10NK80Z  (alt: STF7NM80, IXTP2N80)",
        "qty": 1,
        "status": "buy",
        "notes": (
            "STP10NK80Z preferred over STF7NM80: 9 A vs 6 A, 0.9 Ω vs 1.7 Ω Rds(on) — less heat in MOSFET during fast discharge. "
            "Use standard TO-220 (not FP variant — FP has isolated tab but only 40 W Pd vs 160 W). "
            "Mount with clip-on heatsink ~10 °C/W (e.g. Wakefield 637-10ABPE) and mica/kapton washer."
        ),
    },
    {
        "refs": ["HS1"],
        "value": "~10 °C/W clip-on",
        "schematic_label": None,
        "description": "Heatsink, TO-220 clip-on, ~10 °C/W",
        "part_number": "Wakefield 637-10ABPE  (alt: any TO-220 clip-on ≤12 °C/W)",
        "qty": 1,
        "status": "buy",
        "notes": "For Q2 (STP10NK80Z). Not a schematic component; listed for completeness.",
    },

    # ══ GATE DRIVE ════════════════════════════════════════════════════════════
    {
        "refs": ["R4"],
        "value": "100 Ω",
        "schematic_label": "100Ω",
        "description": "Resistor, metal film, 100 Ω, 0.25 W, ±1%, axial THT",
        "part_number": "any 100 Ω / 0.25 W axial metal film",
        "qty": 1,
        "status": "buy",
        "notes": "Gate series resistor; limits gate charge current to prevent oscillation.",
    },
    {
        "refs": ["R5"],
        "value": "470 kΩ / 1 W",
        "schematic_label": "470kΩ/1W",
        "description": "Resistor, metal film, 470 kΩ, 1 W, ±1%, ≥600 V, axial THT",
        "part_number": "any 470 kΩ / 1 W axial metal film rated ≥600 V",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Gate pull-up from HV+ rail; D9 clamps gate at 12 V when Q1 is off. "
            "At 600 V: P = (600−12)²/470 k ≈ 0.74 W (74% of 1 W rating). "
            "Sees up to ~590 V — verify part is rated ≥600 V working voltage."
        ),
    },
    {
        "refs": ["D9"],
        "value": "BZX85C12 / 12 V",
        "schematic_label": "BZX85C12\n12V",
        "description": "Zener diode, 12 V, 1.3 W, DO-41, THT",
        "part_number": "BZX85C12",
        "qty": 1,
        "status": "buy",
        "notes": "Clamps Q2 gate to 12 V when Q1 is off (safe for any gate oxide).",
    },

    # ══ THRESHOLD DETECTOR (Q1 NPN, 71 V switch point) ══════════════════════
    {
        "refs": ["Q1"],
        "value": "2N3904",
        "schematic_label": "2N3904",
        "description": "BJT, NPN, 40 V Vce, 200 mA, TO-92, THT",
        "part_number": "2N3904",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Saturates when V_cap > 71 V → pulls GATE_CTRL low → Q2 OFF (slow path only). "
            "Threshold = 0.7 V × (R1 + R2) / R2 ≈ 71 V."
        ),
    },
    {
        "refs": ["R1"],
        "value": "1 MΩ / 1 W",
        "schematic_label": "1MΩ/1W",
        "description": "Resistor, metal film, 1 MΩ, 1 W, ±1%, ≥600 V, axial THT",
        "part_number": "any 1 MΩ / 1 W axial metal film rated ≥600 V",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Top of R1/R2 threshold divider. At 600 V: 0.36 W (36% of 1 W rating). "
            "Sees up to ~600 V — verify part is rated ≥600 V working voltage. "
            "V_th = 0.7 × (1 MΩ + 10 kΩ) / 10 kΩ ≈ 70.7 V."
        ),
    },
    {
        "refs": ["R2"],
        "value": "10 kΩ",
        "schematic_label": "10kΩ",
        "description": "Resistor, metal film, 10 kΩ, 0.25 W, ±1%, axial THT",
        "part_number": "any 10 kΩ / 0.25 W axial metal film",
        "qty": 1,
        "status": "buy",
        "notes": "Bottom of R1/R2 divider; sets 71 V threshold. Tune by swapping value if needed.",
    },
    {
        "refs": ["R3"],
        "value": "100 kΩ / 0.6 W",
        "schematic_label": "100kΩ/0.6W",
        "description": "Resistor, metal film, 100 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF1003A50",
        "qty": 1,
        "status": "sourced",
        "notes": "Q1 base current limiter.",
    },

    # ══ LED DANGER INDICATOR (~10.2 V cutoff) ════════════════════════════════
    {
        "refs": ["R_LED1", "R_LED2", "R_LED3"],
        "value": "100 kΩ / 0.6 W",
        "schematic_label": "100kΩ/0.6W",
        "description": "Resistor, metal film, 100 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF1003A50",
        "qty": 3,
        "status": "sourced",
        "notes": (
            "3 in series = 300 kΩ current limiter. "
            "At 600 V: 2 mA through LED, 0.4 W per resistor (67% of 0.6 W). "
            "Each resistor sees ≤200 V (within 250 V rating)."
        ),
    },
    {
        "refs": ["D_LED"],
        "value": "BZX55C8V2 / 8.2 V",
        "schematic_label": "BZX55C8V2\n8.2V",
        "description": "Zener diode, 8.2 V, 0.5 W, DO-35, THT",
        "part_number": "BZX55C8V2",
        "qty": 1,
        "status": "buy",
        "notes": "Sets LED cutoff: V_Z (8.2 V) + V_f (2 V) ≈ 10.2 V. LED off below that.",
    },
    {
        "refs": ["LED1"],
        "value": "Red LED  Vf≈2V",
        "schematic_label": "Red  Vf≈2V",
        "description": "LED, red, 5 mm, Vf ≈ 2 V, 20 mA max, THT",
        "part_number": "any 5 mm red LED (Vf ≈ 2 V)",
        "qty": 1,
        "status": "buy",
        "notes": "Danger indicator. ON above ~10.2 V, OFF below. Bright at 2 mA (600 V); dim at 0.3 mA (100 V).",
    },

    # ══ DVM SIGNAL DIVIDER (6:1, 0–600 V → 0–100 V) ══════════════════════
    {
        "refs": ["R_sig1", "R_sig2", "R_sig3", "R_sig4", "R_sig5"],
        "value": "100 kΩ / 0.6 W",
        "schematic_label": "100kΩ/0.6W",
        "description": "Resistor, metal film, 100 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF1003A50",
        "qty": 5,
        "status": "sourced",
        "notes": (
            "Top half of 6:1 divider: 5 × 100 kΩ in series = 500 kΩ. "
            "At 600 V: 1 mA string current, 0.1 W per resistor. Each sees ≤100 V (well within 250 V)."
        ),
    },
    {
        "refs": ["R_sig_bot"],
        "value": "100 kΩ / 0.6 W",
        "schematic_label": "100kΩ/0.6W",
        "description": "Resistor, metal film, 100 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF1003A50",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Bottom leg of 6:1 divider. "
            "Optional: add R_cal (200 kΩ trimmer) in series for full-scale calibration."
        ),
    },

    # ══ DVM Vcc DROPPER (parasitic 15 V supply) ═══════════════════════════════
    {
        "refs": ["R_drop1", "R_drop2", "R_drop3", "R_drop4"],
        "value": "15 kΩ / 3 W",
        "schematic_label": "15kΩ/3W",
        "description": "Resistor, metal oxide, 15 kΩ, 3 W, ±5%, 500 V, Ø5×15 mm, axial THT",
        "part_number": "MOF3WS-15K",
        "qty": 4,
        "status": "sourced",
        "notes": (
            "4 in series = 60 kΩ dropper from HV+ to 15 V Zener. "
            "At 600 V: 9.75 mA, 1.42 W per resistor (49% of 3 W rating). "
            "If DVM draws > 9 mA reduce to 3 × 15 kΩ (45 kΩ, 13 mA headroom)."
        ),
    },
    {
        "refs": ["D_Vcc"],
        "value": "1N4744A / 15 V",
        "schematic_label": "1N4744A\n15V",
        "description": "Zener diode, 15 V, 1 W, DO-41, THT",
        "part_number": "1N4744A",
        "qty": 1,
        "status": "buy",
        "notes": "Shunt regulator; holds DVM Vcc at 15 V. DVM live when V_cap > ~20 V.",
    },
    {
        "refs": ["C_Vcc"],
        "value": "10 µF / 25 V",
        "schematic_label": "10µF/25V",
        "description": "Capacitor, electrolytic, 10 µF, 25 V, Ø4×7 mm, 2.5 mm pitch, THT",
        "part_number": "EEAGA1E100H",
        "qty": 1,
        "status": "sourced",
        "notes": "Smoothing cap across D_Vcc. Observe polarity (+ toward D_Vcc anode / node_Vcc).",
    },

    # ══ OPTIONAL / CALIBRATION ════════════════════════════════════════════════
    {
        "refs": ["R_cal"],
        "value": "200 kΩ trimmer",
        "schematic_label": "200kΩ trim",
        "description": "Potentiometer, wirewound trimmer, 200 kΩ, 500 mW, ±10%, THT",
        "part_number": "T93YA200K",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Optional. Place in series with R_sig_bot to calibrate DVM full-scale reading. "
            "Set trimmer so DVM reads 50.0 V when V_cap = 300 V (known reference)."
        ),
    },

    # ══ BYPASS / DECOUPLING ═══════════════════════════════════════════════════
    {
        "refs": ["C_byp1", "C_byp2"],
        "value": "100 nF / 50 V",
        "schematic_label": "100nF/50V",
        "description": "Capacitor, ceramic, 100 nF, 50 V, X7R, ±10%, 5 mm pitch, THT",
        "part_number": "K104K10X7RF5UH5",
        "qty": 2,
        "status": "sourced",
        "notes": "Local decoupling near Q1 base/emitter and DVM module Vcc pin.",
    },

    # ══ INPUT TERMINALS ═══════════════════════════════════════════════════════
    {
        "refs": ["J1"],
        "value": "SLB4-G-21",
        "schematic_label": None,
        "description": "Banana socket, 4 mm, 1 kV, 32 A, green, panel-mount, Ø12.2 mm hole",
        "part_number": "SLB4-G-21",
        "qty": 1,
        "status": "sourced",
        "notes": "PROBE_A — positive input terminal.",
    },
    {
        "refs": ["J2"],
        "value": "SLB4-G-22",
        "schematic_label": None,
        "description": "Banana socket, 4 mm, 1 kV, 32 A, black, panel-mount, Ø12.2 mm hole",
        "part_number": "SLB4-G-22",
        "qty": 1,
        "status": "sourced",
        "notes": "PROBE_B — negative input terminal.",
    },
    {
        "refs": ["J3", "J4"],
        "value": "MKDS5/2-9.5",
        "schematic_label": None,
        "description": "PCB screw terminal block, 2-pin, 32 A, 1 kV, 9.5 mm pitch, THT",
        "part_number": "MKDS5/2-9.5",
        "qty": 2,
        "status": "sourced",
        "notes": "Alternative / auxiliary input terminals on the PCB.",
    },

    # ══ SOURCED BUT UNUSED IN CURRENT DESIGN ══════════════════════════════════
    {
        "refs": [],
        "value": "820 kΩ / 0.6 W",
        "schematic_label": None,
        "description": "Resistor, metal film, 820 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF8203A50",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "100 pcs sourced. Not used in current design revision.",
    },
    {
        "refs": [],
        "value": "1.8 MΩ / 0.6 W",
        "schematic_label": None,
        "description": "Resistor, metal film, 1.8 MΩ, 0.6 W, ±1%, 350 V, axial THT",
        "part_number": "MF0207FTE-1M8",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "5 pcs sourced. Not used in current design revision.",
    },
    {
        "refs": [],
        "value": "2.2 MΩ / 0.6 W",
        "schematic_label": None,
        "description": "Resistor, metal film, 2.2 MΩ, 0.6 W, ±1%, 350 V, axial THT",
        "part_number": "MBB0207VC2204FCT00",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "10 pcs sourced. Not used in current design revision.",
    },
    {
        "refs": [],
        "value": "LM393AP",
        "schematic_label": None,
        "description": "IC, dual comparator, 300 ns, 2–30 V supply, DIP-8, THT",
        "part_number": "LM393AP",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "3 pcs sourced. Not used — NPN transistor threshold detector chosen instead.",
    },
    {
        "refs": [],
        "value": "CT2900A test leads",
        "schematic_label": None,
        "description": "Test leads set, 12 A, 1.2 m, −20 to +80 °C",
        "part_number": "CT2900A",
        "qty": 1,
        "status": "sourced",
        "notes": "Probes for the tool. Not a PCB component.",
    },
]

# ─── Schematic label lookup ────────────────────────────────────────────────────
# LABEL[ref] → the multi-line string used in gen_full_schematic.py
# First line is always the ref designator; second line(s) from schematic_label
# or falls back to value.
LABEL: dict[str, str] = {}
for _item in BOM:
    _suffix = _item["schematic_label"] if _item["schematic_label"] is not None else _item["value"]
    for _ref in _item["refs"]:
        LABEL[_ref] = f"{_ref}\n{_suffix}"


# ─── Reporting ────────────────────────────────────────────────────────────────
def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def print_summary() -> None:
    buy     = [i for i in BOM if i["status"] == "buy"]
    partial = [i for i in BOM if i["status"] == "sourced_partial"]
    sourced = [i for i in BOM if i["status"] == "sourced" and i["refs"]]
    unused  = [i for i in BOM if i["status"] == "sourced_unused"]

    _section("TO BUY")
    for item in buy:
        refs = ", ".join(item["refs"]) if item["refs"] else "—"
        print(f"  [{refs}]  qty {item['qty']}")
        print(f"    {item['description']}")
        print(f"    P/N: {item['part_number']}")
        if item["notes"]:
            print(f"    Note: {item['notes'][:120]}")
        print()

    _section("NEEDS ASSEMBLY FROM SOURCED PARTS")
    for item in partial:
        refs = ", ".join(item["refs"])
        print(f"  [{refs}]  qty {item['qty']}")
        print(f"    {item['description']}")
        print(f"    P/N: {item['part_number']}")
        print(f"    Note: {item['notes'][:160]}")
        print()

    _section("SOURCED (in hand)")
    for item in sourced:
        refs = ", ".join(item["refs"])
        print(f"  [{refs}]  qty {item['qty']}  ← {item['part_number']}")

    _section("SOURCED UNUSED")
    for item in unused:
        print(f"  {item['part_number']}  — {item['notes'][:100]}")


def write_bom_md(path: str = "bom.md") -> None:
    buy     = [i for i in BOM if i["status"] == "buy"]
    partial = [i for i in BOM if i["status"] == "sourced_partial"]
    sourced = [i for i in BOM if i["status"] == "sourced" and i["refs"]]
    unused  = [i for i in BOM if i["status"] == "sourced_unused"]

    lines: list[str] = []
    a = lines.append

    a("# Bill of Materials — 600V Capacitor Discharger\n")
    a("> Generated by `bom.py`. Edit that file to update this document.\n")

    # ── To Buy ───────────────────────────────────────────────────────────────
    a("## To Buy\n")
    a("| Ref(s) | Qty | Description | Part Number / Suggestion |")
    a("|--------|-----|-------------|--------------------------|")
    for item in buy:
        refs = ", ".join(item["refs"]) if item["refs"] else "—"
        pn   = item["part_number"].replace("|", "\\|")
        desc = item["description"].replace("|", "\\|")
        a(f"| {refs} | {item['qty']} | {desc} | {pn} |")
    a("")

    # ── Needs assembly from sourced parts ────────────────────────────────────
    if partial:
        a("## Needs Assembly from Sourced Parts\n")
        a("| Ref(s) | Qty | Description | How to Build |")
        a("|--------|-----|-------------|--------------|")
        for item in partial:
            refs  = ", ".join(item["refs"])
            desc  = item["description"].replace("|", "\\|")
            notes = item["notes"].replace("|", "\\|") if item["notes"] else ""
            a(f"| {refs} | {item['qty']} | {desc} | {notes} |")
        a("")

    # ── Sourced (in hand) ────────────────────────────────────────────────────
    a("## Sourced (In Hand)\n")
    a("| Ref(s) | Qty | Part Number |")
    a("|--------|-----|-------------|")
    for item in sourced:
        refs = ", ".join(item["refs"])
        a(f"| {refs} | {item['qty']} | {item['part_number']} |")
    a("")

    # ── Sourced but unused ───────────────────────────────────────────────────
    a("## Sourced — Not Used in Current Revision\n")
    a("| Part Number | Description | Notes |")
    a("|-------------|-------------|-------|")
    for item in unused:
        desc  = item["description"].replace("|", "\\|")
        notes = (item["notes"] or "").replace("|", "\\|")
        a(f"| {item['part_number']} | {desc} | {notes} |")
    a("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved: {path}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print_summary()
    write_bom_md()
