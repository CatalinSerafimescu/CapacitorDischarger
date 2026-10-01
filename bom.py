"""
Bill of Materials — 600V Capacitor Discharger
Single source of truth for component data, schematic labels, and procurement status.

To update a component:  edit the entry here; the schematic regenerates automatically.
To print a buy list:    python bom.py   (also writes bom.md and TO_BUY_list.csv)

status values
  'sourced'          — in hand (from TME order 2026-04-15, Mouser 39007986, or prior stock)
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
        "part_number": "1N4007  (Diotec, Mouser 637-1N4007)",
        "qty": 4,
        "status": "sourced",
        "notes": "Full-bridge for reverse-polarity protection. PIV 1000 V gives 400 V margin over 600 V rail.",
    },

    # ══ PROTECTION FUSE ══════════════════════════════════════════════════════
    {
        "refs": ["F1"],
        "value": "2 A / 1000 V DC gR",
        "schematic_label": "2A/1kV DC",
        "description": "Fuse, 2 A, 1000 VDC, gR (super-fast, full-range), 30 kA breaking capacity, ceramic, 10.3×38 mm cartridge",
        "part_number": "ESKA 1038820  (TME 1038820, in stock 2026-10-01; alt DF ELECTRIC 491602, Littelfuse KLKD002.T) — buy 2 (1 spare)",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Not in ComponentsDB inventory (checked 2026-10-01). Mounts in 2× Schurter CSO PCB clips (next entry). "
            "Single-fault protection: if Q1 fails open or D9 fails, Q2 turns fully on at 600 V and "
            "R_fast would see ~12 A / 7.2 kW — F1 opens the HV+ line on that fault. "
            "gR = full-range semiconductor-protection fuse: breaks any current that melts it, at 1000 VDC. "
            "Normal currents: ≤~40 mA continuous plus fast-dump pulses up to ~1.6 A peak (worst Q1 corner) decaying with "
            "τ = 50 Ω × C (worst-case pulse I²t ≈ 0.2 A²s for a 2 mF cap) — far below a 2 A fuse's "
            "melting I²t, so no nuisance operation. "
            "Must be a 600 VDC-rated cartridge — standard 5×20 glass fuses are only 250 V and must not be used."
        ),
    },
    {
        "refs": [],
        "value": "PCB fuse clip, 10.3×38 mm",
        "schematic_label": None,
        "description": "Fuse clip, PCB through-hole solder, for 10.3×38 mm cartridge fuses, silver-plated copper, 1500 VAC/VDC, 32 A",
        "part_number": "SCHURTER 0751.0506  (CSO, TME 0751.0506) — 2 per fuse",
        "qty": 2,
        "status": "buy",
        "notes": (
            "Holds F1. Replaces the earlier Keystone 3517, which is a clip for 5 mm (5×20) fuses and does not "
            "fit a 10.3 mm cartridge. Not in ComponentsDB inventory. KiCad footprint must be made from the CSO "
            "datasheet (stock library has no 10×38 clip footprint); keep ≥6 mm HV clearance around both clips."
        ),
    },

    # ══ SLOW DISCHARGE PATH ══════════════════════════════════════════════════
    {
        "refs": ["R_slow1", "R_slow2", "R_slow3", "R_slow4", "R_slow5"],
        "value": "4.7 kΩ / 5 W",
        "schematic_label": "4.7kΩ/5W",
        "description": "Resistor, wirewound, 4.7 kΩ, 5 W, ±1%, 460 V, axial THT",
        "part_number": "45F4K7E  (Ohmite, Mouser 588-45F4K7E)",
        "qty": 5,
        "status": "sourced",
        "notes": (
            "5 in series = 23.5 kΩ / 25 W / 1750 V working voltage. "
            "At 600 V: 25.5 mA, 3.06 W per resistor (61% of 5 W rating). "
            "Each resistor sees 120 V (well under 460 V part limit). "
            "Mount axial on ≥3 mm PCB standoff, in a row for airflow."
        ),
    },

    # ══ FAST DISCHARGE PATH ══════════════════════════════════════════════════
    {
        "refs": ["R_fast"],
        "value": "50 Ω / 7 W",
        "schematic_label": "50Ω/7W",
        "description": "Resistor, wirewound, 50 Ω, 7 W, ±5%, axial THT",
        "part_number": "27J50RE  (Ohmite, Mouser 588-27J50RE)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Peak dissipation ≈ 80 W (up to ~130 W at the cold/low-hFE 83 V switch point) decaying with "
            "τ = 50 Ω × C_cap. Pulse energy ≈ ½·C·V_switch²: 2 J for 1 mF, ~85 J for a 47 mF/60 V cap "
            "(≈ the 10×/5 s overload limit of a 7 W wirewound — biggest practical cap). "
            "Continuous overload (live supply below the threshold) is handled by TF1, not F1. "
            "NOTE: ComponentsDB lists this part as 3 W — wrong; the Mouser order confirmation says 7 W."
        ),
    },
    {
        "refs": ["TF1"],
        "value": "Thermal cutoff 133 °C",
        "schematic_label": "SF129R0\n133°C",
        "description": (
            "Thermal cutoff (thermal fuse), one-shot, organic-pellet type, Tf 133 °C, "
            "15 A / 250 VAC, metal case, axial leads"
        ),
        "part_number": "SCHOTT SEFUSE SF129R0  (TME SF129R0; alt AUPO BF133) — buy 2 (1 spare)",
        "qty": 1,
        "status": "buy",
        "notes": (
            "In series between R_fast and Q2 drain, body clamped against R_fast (stainless wire or clip "
            "+ thin thermal compound). Protects R_fast when the probes touch a live supply below the "
            "~63 V threshold: Q2 stays on and R_fast sees 41–74 W continuously (48–63 V), while F1 "
            "(2 A) never blows. Simulated (scenario L, assumed thermal constants): opens in ~9 s at 48 V; "
            "no trip on a 47 mF/60 V dump (peak 49 °C). If it opens, the slow path still discharges the "
            "cap; replace TF1. Caveat: SEFUSE ratings are AC only — here it breaks ≤1.6 A at ≤83 V DC "
            "into a resistive load, which is well inside the 15 A contact rating but not datasheet-rated "
            "for DC. TF1's metal case is electrically live (HV net) — keep HV clearance to LV parts. "
            "Not in ComponentsDB inventory."
        ),
    },
    {
        "refs": ["Q2"],
        "value": "STP10NK80Z",
        "schematic_label": "STP10NK80Z\n800V 9A",
        "description": "MOSFET, N-channel, 800 V, 9 A, R_ds(on) 0.9 Ω typ, TO-220, THT",
        "part_number": "STP10NK80Z  (alt: STF7NM80, IXTP2N80)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "STP10NK80Z preferred over STF7NM80: 9 A vs 6 A, 0.9 Ω vs 1.7 Ω Rds(on) — less heat in MOSFET during fast discharge. "
            "Use standard TO-220 (not FP variant — FP has isolated tab but only 40 W Pd vs 160 W). "
            "Clip-on HS-S01 heatsink (HS1) over the TO-220 insulating set (MST 220). "
            "Bend the gate and source legs outward to a 5.08 mm pitch (PCB footprint) for drain spacing."
        ),
    },
    {
        "refs": [],
        "value": "TO-220 insulating mounting set",
        "schematic_label": None,
        "description": "Insulating mounting set for TO-220: insulating pad + shoulder bushing (+ M3 hardware)",
        "part_number": "Fischer Elektronik MST 220  (ComponentsDB; alt: Stonecold TO220-SET)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Required: the STP10NK80Z tab is the drain (up to 600 V), so without it the heatsink becomes "
            "a live HV part. Check the pad's breakdown rating (≥ 2 kV) and verify tab-to-heatsink "
            "isolation with an insulation tester / ≥ 600 V before first use."
        ),
    },
    {
        "refs": ["HS1"],
        "value": "HS-S01 U clip-on, TO-220",
        "schematic_label": None,
        "description": "Heatsink, TO-220, U-shaped slip-on, 19.05 × 13.21 × 6.35 mm, black anodised",
        "part_number": "Stonecold HS-S01  (TME, ComponentsDB comp_225 — 1 left)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Changed 2026-10-01 for the compact boards (was Wakefield 647-10ABEP, now unused). Q2 only "
            "dissipates in pulses: a normal dump puts ≲2 J in Q2, and the live-supply case is ~1–2 W for "
            "<10 s before TF1 opens. Not soldered (no pins): it rides on Q2's tab with the MST 220 "
            "insulating set, so it is electrically floating."
        ),
    },
    {
        "refs": [],
        "value": "Wakefield 647-10ABEP / 637-10ABPE",
        "schematic_label": None,
        "description": "Heatsinks, TO-220, board-mount with solder pins (3.8 / 5.8 °C/W)",
        "part_number": "647-10ABEP, 637-10ABPE  (Wakefield, Mouser order 39007986)",
        "qty": 2,
        "status": "sourced_unused",
        "notes": "Too big for the 100 × 75 / 120 × 90 mm boards; replaced by the HS-S01.",
    },

    # ══ GATE DRIVE ════════════════════════════════════════════════════════════
    {
        "refs": ["R4"],
        "value": "100 Ω",
        "schematic_label": "100Ω",
        "description": "Resistor, metal film, 100 Ω, 0.25 W, ±1%, axial THT",
        "part_number": "RN60D1000FB14  (Vishay, Mouser 71-RN60D-F-100)",
        "qty": 1,
        "status": "sourced",
        "notes": "Gate series resistor; limits gate charge current to prevent oscillation.",
    },
    {
        "refs": ["R5"],
        "value": "470 kΩ / 3 W",
        "schematic_label": "470kΩ/3W",
        "description": "Resistor, metal film, 470 kΩ, 3 W, ±1%, 750 V, axial THT",
        "part_number": "FMP300FRF73-470K  (YAGEO, Mouser 603-FMP300FRF73-470K)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Gate pull-up from HV+ rail; D9 clamps gate at 12 V when Q1 is off. "
            "At 600 V: P = (600−12)²/470 k ≈ 0.74 W (25% of 3 W rating). "
            "Sees up to ~590 V — 750 V part rating gives adequate margin."
        ),
    },
    {
        "refs": ["D9"],
        "value": "BZX85C12 / 12 V",
        "schematic_label": "BZX85C12\n12V",
        "description": "Zener diode, 12 V, 1.3 W, DO-41, THT",
        "part_number": "BZX85C12  (onsemi, Mouser 512-BZX85C12)",
        "qty": 1,
        "status": "sourced",
        "notes": "Clamps Q2 gate to 12 V when Q1 is off (safe for any gate oxide).",
    },

    # ══ THRESHOLD DETECTOR (Q1 NPN, ~63 V switch point) ═════════════════════
    {
        "refs": ["Q1"],
        "value": "MPSA42",
        "schematic_label": "MPSA42",
        "description": "BJT, NPN, 300 V Vce, 500 mA, TO-92, THT",
        "part_number": "MPSA42-FAI  (onsemi, TME MPSA42-FAI)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Saturates above threshold → pulls GATE_CTRL low → Q2 OFF (slow path only). "
            "Threshold ≈ 101 × (V_BE + I_B × 20 kΩ) with R3 = 10 kΩ; simulation gives 63 V (BF=150) "
            "and 68 V (BF=40); full corners (scenarios G3/G4): 55 V (BF=300, 60 °C) to 83 V "
            "(datasheet-min BF=25, 0 °C) → worst peak I_fast ≈ 1.6 A, still < 2 A. No hysteresis. "
            "300 V V_CEO gives safe margin in a 600 V circuit even if D9 opens. "
            "Drop-in replacement for 2N3904 (same TO-92 pinout, β ≈ 150). "
            "Confirmed in hand (ComponentsDB inventory, 2026-07-29)."
        ),
    },
    {
        "refs": ["R1"],
        "value": "1 MΩ / 3 W",
        "schematic_label": "1MΩ/3W",
        "description": "Resistor, metal film, 1 MΩ, 3 W, ±1%, 750 V, axial THT",
        "part_number": "FMP300FRF73-1M  (YAGEO, Mouser 603-FMP300FRF73-1M)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Top of R1/R2 threshold divider. At 600 V: 0.36 W (12% of 3 W rating). "
            "Sees ~594 V across it at 600 V — within the 750 V part rating. "
            "Threshold ≈ 63 V simulated (BF=150); 63–68 V across MPSA42 hFE corners — see Q1 notes."
        ),
    },
    {
        "refs": ["R2"],
        "value": "10 kΩ",
        "schematic_label": "10kΩ",
        "description": "Resistor, metal film, 10 kΩ, 0.25 W, ±1%, axial THT",
        "part_number": "MFR-25FTE52-10K  (YAGEO, Mouser 603-MFR-25FTE52-10K)",
        "qty": 1,
        "status": "sourced",
        "notes": "Bottom of R1/R2 divider; sets ~63 V threshold together with R1 and R3. Tune by swapping value if needed.",
    },
    {
        "refs": ["R3"],
        "value": "10 kΩ",
        "schematic_label": "10kΩ",
        "description": "Resistor, metal film, 10 kΩ, 0.25 W, ±1%, axial THT",
        "part_number": "MFR-25FTE52-10K  (YAGEO, Mouser 603-MFR-25FTE52-10K)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Q1 base current limiter. Reduced from 100 kΩ to 10 kΩ (2026-07-29): the stiffer base "
            "drive makes the threshold nearly hFE-independent — 63 V (BF=150) to 68 V (BF=40) "
            "simulated, vs 76–154 V with 100 kΩ. Second piece of the same 10 kΩ part as R2; "
            "inventory has spare 10 kΩ 0.25 W pieces beyond the single Mouser MFR-25 unit."
        ),
    },

    # ══ LED DANGER INDICATOR (~10.2 V cutoff) ════════════════════════════════
    {
        "refs": ["R_LED1", "R_LED2", "R_LED3", "R_LED4"],
        "value": "100 kΩ / 0.6 W",
        "schematic_label": "100kΩ/0.6W",
        "description": "Resistor, metal film, 100 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF1003A50",
        "qty": 4,
        "status": "sourced",
        "notes": (
            "4 in series = 400 kΩ current limiter. "
            "At 600 V: 1.47 mA through LED, 0.216 W per resistor (36% of 0.6 W). "
            "Each resistor sees ≤150 V (60% of 250 V rating) — improved derating vs 3-resistor design."
        ),
    },
    {
        "refs": ["D_LED"],
        "value": "BZX55C8V2 / 8.2 V",
        "schematic_label": "BZX55C8V2\n8.2V",
        "description": "Zener diode, 8.2 V, 0.5 W, DO-35, THT",
        "part_number": "BZX55C8V2-TAP  (Vishay, Mouser 78-BZX55C8V2-TAP)",
        "qty": 1,
        "status": "sourced",
        "notes": "Sets LED cutoff: V_Z (8.2 V) + V_f (2 V) ≈ 10.2 V. LED off below that.",
    },
    {
        "refs": ["LED1"],
        "value": "Red LED  Vf≈2V",
        "schematic_label": "Red  Vf≈2V",
        "description": "LED, red, 5 mm (T-1¾), low-current type (specified at 2 mA), Vf ≈ 1.8–2 V, diffused, THT",
        "part_number": "HLMP-4700  (Broadcom, low-current red, TME HLMP-4700)  — fallback: kit 5 mm red LED (ComponentsDB)",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Danger indicator. ON above ~10.2 V, OFF below. Bright at 2 mA (600 V); dim at 0.3 mA (100 V). "
            "A low-current (2 mA-rated) red LED is required for the 'LED ON = danger' indication to be "
            "visible: between ~10 V and ~63 V the chain current is only 0–130 µA (50 µA at 30 V) and a "
            "generic 20 mA kit LED is effectively dark below ~30–40 V. "
            "Off-board: front panel (Ø5.1 hole, flange in a recess behind the wall, glued), on a 2-wire cable "
            "to J6 — heat-shrink both legs."
        ),
    },
    {
        "refs": ["J6"],
        "value": "JST XH 2-pin",
        "schematic_label": None,
        "description": "Wire-to-board header, JST XH (2.5 mm) / XH2.54, 2-pin, vertical, THT + housing and 2 crimp contacts (LED1 cable)",
        "part_number": "B2B-XH-A + XHP-2  (ComponentsDB comp_156, XH2.54 connector kit)",
        "qty": 1,
        "status": "sourced",
        "notes": "Pin 1 = GND (LED cathode), pin 2 = LED_A (LED anode). Cable ~15 cm, 1 kV silicone wire, run along the left wall to the front panel.",
    },
    {
        "refs": ["D_clamp2"],
        "value": "BZX55C8V2 / 8.2 V",
        "schematic_label": None,
        "description": "Zener diode, 8.2 V, 0.5 W, DO-35, THT",
        "part_number": "BZX55C8V2-TAP  (ComponentsDB comp_126, same as D_LED)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Across J6 (K = LED_A, A = GND). With the LED unplugged or its wire broken, LED_A would float up to "
            "~HVp − 8 V through R_LED1-4 (≤ 1.5 mA); the clamp holds it at 8.2 V. In normal use it sees only the "
            "LED's ~2 V (leakage < 0.1 µA): no effect on the 10.2 V cutoff (sims 15/15 PASS)."
        ),
    },

    # ══ DVM SIGNAL DIVIDER (10 000:1, 600 V → 60 mV for the PM-128) ═════════
    {
        "refs": ["R_sig1", "R_sig2", "R_sig3", "R_sig4", "R_sig5"],
        "value": "100 kΩ / 0.6 W",
        "schematic_label": "100kΩ/0.6W",
        "description": "Resistor, metal film, 100 kΩ, 0.6 W, ±1%, 250 V, axial THT",
        "part_number": "MF006FF1003A50",
        "qty": 5,
        "status": "sourced",
        "notes": (
            "Top of the 10 000:1 divider: 5 × 100 kΩ in series = 500 kΩ. "
            "At 600 V: 1.2 mA string current, 0.14 W per resistor. Each sees ≤120 V (well within 250 V)."
        ),
    },
    {
        "refs": ["R_sig_bot1", "R_sig_bot2"],
        "value": "100 Ω / 0.6 W (2 in parallel = 50 Ω)",
        "schematic_label": "100Ω 1%",
        "description": "Resistor, metal film, 100 Ω, 0.6 W, ±1%, 50 ppm/°C, axial THT",
        "part_number": "YAGEO MF0207FTE52-100R  (TME MF0207FTE-100R; any 100 Ω 1% metal film fits)",
        "qty": 2,
        "status": "buy",
        "notes": (
            "Two in parallel form the 50 Ω divider bottom (replaces a single 49.9 Ω, out of stock at TME): "
            "600 V → 60.0 mV → PM-128 shows '600' before trim; its trimmer R4 corrects the remaining ~1 %. "
            "1.2 mA total, ~36 µW each. If one ever opens, the reading doubles ('1200' at 600 V) — "
            "obviously wrong, never dangerous. Not in ComponentsDB inventory (only one 100 Ω, used as R4)."
        ),
    },
    {
        "refs": ["D_clamp"],
        "value": "1N4007",
        "schematic_label": None,
        "description": "Diode, rectifier, 1 A, 1000 V PIV, DO-41, THT",
        "part_number": "1N4007  (spare from the bridge batch, ComponentsDB)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Across R_sig_bot1/2 (anode = PM-128 VIN, cathode = GND). Normally sees ≤60 mV, so its leakage "
            "error is a few ppm. If both bottom resistors open, it holds VIN at ~0.7 V (meter shows overrange "
            "'1') instead of letting ~600 V through 500 kΩ into the meter input."
        ),
    },

    # ══ VOLTMETER ═════════════════════════════════════════════════════════════
    {
        "refs": ["DVM1"],
        "value": "Axiomet PM-128, 200 mV FS LCD",
        "schematic_label": None,
        "description": (
            "Digital panel meter, 3½-digit LCD, 13 mm digits, 199.9 mV full scale, input >100 MΩ, "
            "±0.5 %, 7–11 V DC supply at ~1 mA, decimal point by wire jumper, 68×44 mm"
        ),
        "part_number": "AXIOMET PM-128  (TME PAN.PM128) — 1 needed, 2nd optional as a spare",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Replaces the 0–100 V 3-wire LED module (its 0.525 MΩ input loaded the 6:1 divider beyond "
            "calibration range). Leave the factory RB wire jumper in (200 mV range), RA unfitted, and all "
            "decimal-point jumpers P1–P3 OFF, so 60 mV reads '600' (1 V resolution, up to 1999). "
            "Calibrate with its trimmer R4 against a known DC voltage (e.g. 100 V bench supply measured "
            "with a DMM). Datasheet: supply and measured input MUST have separate grounds, so BT1 floats "
            "(see BT1). ~1 mA from the floating 9 V on the DC jack (~500 h from an alkaline 9 V on a plug). "
            "Off-board, panel-mounted; connects to J5."
        ),
    },
    {
        "refs": ["J5"],
        "value": "1×2 header 2.54 mm",
        "schematic_label": None,
        "description": "Pin header, 1×2, 2.54 mm pitch, straight, THT (PM-128 input cable)",
        "part_number": "TE narrow flat pin header 2P  (ComponentsDB)",
        "qty": 1,
        "status": "sourced",
        "notes": "Pin 1 = VIN (divider output, ≤60 mV), pin 2 = circuit GND → PM-128 IN GND. LV zone only.",
    },

    # ══ DVM POWER (external floating 9 V via a panel DC jack) ═════════════════
    {
        "refs": ["BT1"],
        "value": "9 V ext. via DC jack",
        "schematic_label": "9V\next.",
        "description": "DC barrel jack, female, panel mount, 5.5×2.1 mm, M12 body (Ø12.2 hole), centre + — supply input for the PM-128 from any external FLOATING 9 V source",
        "part_number": "Mufa DC mama 5.5x2.1 (ComponentsDB comp_231, same jack as SursaTensiune J5)",
        "qty": 1,
        "status": "sourced",
        "notes": (
            "Left side wall of the enclosure, with an engraved FLOATING SUPPLY ONLY warning. Wired directly to the PM-128 supply pins, off-board; plug in a 9 V source "
            "to switch the meter on (7–11 V, ~1 mA). The source must FLOAT: a 9 V battery on a 5.5×2.1 plug or an "
            "isolated (double-insulated) adapter — never a supply whose − is earthed or tied to the device under "
            "test (PM-128: supply isolated from the input; circuit GND sits at the capacitor's negative terminal). "
            "Replaces the 9 V battery box (2026-10-01)."
        ),
    },

    # ══ BYPASS / DECOUPLING ═══════════════════════════════════════════════════
    {
        "refs": ["C_byp2"],
        "value": "100 nF / 50 V",
        "schematic_label": "100nF/50V",
        "description": "Capacitor, ceramic, 100 nF, 50 V, X7R, ±10%, 5 mm pitch, THT",
        "part_number": "K104K10X7RF5UH5",
        "qty": 1,
        "status": "sourced",
        "notes": "Q2 gate RC filter (τ ≈ R5 × C ≈ 47 ms, soft turn-on); also holds the gate low on hot-plug (scenario J).",
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
        "notes": "PCB entry for the J1/J2 banana-socket wires: J3 = PROBE_A, J4 = PROBE_B (both poles of each block on the same net; one block per probe keeps the leads apart).",
    },
    {
        "refs": [],
        "value": "Silicone wire 1.0 mm², red + black",
        "schematic_label": None,
        "description": (
            "Single-core wire, LAPP ÖLFLEX HEAT 180 SiF/A 1×1 mm², fine-stranded Cu, silicone, "
            "0.6/1 kV (IEC), 3 kV test, −50…+180 °C (banana sockets J1/J2 → J3/J4)"
        ),
        "part_number": "LAPP 1249584 (red) + 1249524 (black)  (TME HEAT180SIF-A1.0RD/BK, ComponentsDB)",
        "qty": 1,
        "status": "sourced",
        "notes": "0.6/1 kV rating is adequate for 600 V. Keep the two leads apart inside the enclosure.",
    },
    {
        "refs": [],
        "value": "Enclosure, 3D-printed PETG",
        "schematic_label": None,
        "description": "Enclosure, 3D-printed PETG (not PLA), 106.8 × 132.8 × 52 mm: base + screwed top cover, holding the single-sided PCB, PM-128, front-panel LED, 2 banana sockets and the 9 V DC jack",
        "part_number": "Self-printed — mechanical/enclosure/ (gen_enclosure.py → Enclosure_base / Enclosure_cover .stl/.step)",
        "qty": 1,
        "status": "buy",
        "notes": (
            "Designed for the single-sided 100 × 75 board. PLA softens at ~55–60 °C — too close to the power "
            "resistors; PETG (~80 °C) or ASA. Vents above R_slow are baffled (no straight path for a probe tip). "
            "Must be insulating: circuit GND sits at the capacitor's negative terminal. "
            "See mechanical/enclosure/README.md for print settings and assembly."
        ),
    },
    {
        "refs": [],
        "value": "Enclosure hardware",
        "schematic_label": None,
        "description": "4× M3 heat-set insert (Ø4.0 hole, ≤ 6 mm long), 4× M3×10 socket-head screw (cover), 2× M3×12 nylon screw + 2× M3 nut (PCB H1/H3), 4 stick-on rubber feet",
        "part_number": "Any — M3 hardware, PMMA rod Ø5",
        "qty": 1,
        "status": "buy",
        "notes": "Cover screws are ≥ 10 mm from any HV part (box corners); the PCB screws must be nylon (H1/H3 sit next to HV copper).",
    },

    # ══ SOURCED BUT UNUSED IN CURRENT DESIGN ══════════════════════════════════
    {
        "refs": [],
        "value": "0–100 V panel voltmeter, 3-wire",
        "schematic_label": None,
        "description": "Digital panel voltmeter module, 0–100 V, 3-wire, LED display, 5–30 V supply, 12–15 mA, input 0.525 MΩ (measured)",
        "part_number": "Voltmetru de panou 0-100V cu 3 fire  (ComponentsDB)",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "Replaced 2026-10-01 by the PM-128: 0.525 MΩ input loaded the 6:1 divider beyond the trimmer's range, display read V/6, 12–15 mA battery drain.",
    },
    {
        "refs": [],
        "value": "10 kΩ trimmer 3296W",
        "schematic_label": None,
        "description": "Potentiometer, cermet trimmer, 10 kΩ, 25-turn, 0.5 W, THT",
        "part_number": "3296W-1-103LF  (Bourns, TME 3296W-1-103LF)",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "Was R_cal (DVM trim); removed 2026-10-01 — the PM-128 is calibrated with its own trimmer R4.",
    },
    {
        "refs": [],
        "value": "10 µF / 25 V + 100 nF + JST XH 2-pin",
        "schematic_label": None,
        "description": "C_Vcc (EEAGA1E100H), C_byp1 (K104K10X7RF5UH5), former J6 (B2B-XH-A; ref J6 now reused for the LED cable)",
        "part_number": "EEAGA1E100H, K104K10X7RF5UH5, B2B-XH-A",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "Were the battery-fed Vcc rail on the PCB; removed 2026-10-01 — the floating battery now wires straight to the PM-128.",
    },
    {
        "refs": [],
        "value": "15 kΩ / 3 W",
        "schematic_label": None,
        "description": "Resistor, metal oxide, 15 kΩ, 3 W, ±5%, 500 V, Ø5×15 mm, axial THT",
        "part_number": "MOF3WS-15K",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "20 pcs sourced. Was R_drop1–4 (DVM Vcc dropper); removed 2026-07-29 — DVM (12–15 mA measured) is battery-powered now.",
    },
    {
        "refs": [],
        "value": "1N4744A / 15 V",
        "schematic_label": None,
        "description": "Zener diode, 15 V, 1 W, DO-41, THT",
        "part_number": "1N4744A-T50A  (onsemi, Mouser 512-1N4744AT50A)",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "Was D_Vcc (parasitic 15 V shunt regulator); removed 2026-07-29 together with the dropper.",
    },
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
        "value": "3386P-1-103LF",
        "schematic_label": None,
        "description": "Potentiometer, cermet trimmer, 10 kΩ, 1-turn, 0.5 W, THT",
        "part_number": "3386P-1-103LF  (Bourns, TME 3386P-1-103LF)",
        "qty": 0,
        "status": "sourced_unused",
        "notes": "5 pcs sourced. Single-turn variant of R_cal trimmer. Not placed — 3296W (25-turn) used instead for finer adjustment.",
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
    sourced = [i for i in BOM if i["status"] == "sourced"]
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
        refs = ", ".join(item["refs"]) or "—"
        print(f"  [{refs}]  qty {item['qty']}  ← {item['part_number']}")

    _section("SOURCED UNUSED")
    for item in unused:
        print(f"  {item['part_number']}  — {item['notes'][:100]}")


def write_bom_md(path: str = "bom.md") -> None:
    buy     = [i for i in BOM if i["status"] == "buy"]
    partial = [i for i in BOM if i["status"] == "sourced_partial"]
    sourced = [i for i in BOM if i["status"] == "sourced"]
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
        refs = ", ".join(item["refs"]) or "—"
        pn = item["part_number"] if item["refs"] else f"{item['value']} — {item['part_number']}"
        a(f"| {refs} | {item['qty']} | {pn} |")
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


def write_buy_csv(path: str = "TO_BUY_list.csv") -> None:
    """Shopping list (status 'buy' only), regenerated from BOM like bom.md."""
    import csv
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref(s)", "Qty", "Description", "Part Number / Suggestion"])
        for item in BOM:
            if item["status"] == "buy":
                w.writerow([", ".join(item["refs"]) or "—", item["qty"],
                            item["description"], item["part_number"]])
    print(f"Saved: {path}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print_summary()
    write_bom_md()
    write_buy_csv()
