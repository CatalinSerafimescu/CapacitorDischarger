# 600V Capacitor Discharger

A professional, handheld capacitor discharger designed for safely discharging high-voltage capacitors in hobby electronics restoration — tube amplifiers, vintage radios, CRT televisions, and consumer power supplies.

---

## Features

- Discharges capacitors up to **600V** in **under 60 seconds** (up to ~1200µF)
- **Adaptive discharge:** controlled current above ~71V (slow resistive path); fast dump below (MOSFET-switched)
- **Red LED danger indicator:** ON above ~10V, OFF when safe — powered directly from the capacitor, no external supply
- **Integrated digital voltmeter:** 0–100V readout via 6:1 input divider (scales 0–600V → 0–100V)
- **Reverse polarity protection:** 1N4007 full-bridge rectifier
- Designed for **DIY assembly** with through-hole components

---

## Schematic

![Schematic](blocks/full_schematic.svg)

---

## Bill of Materials

See **[bom.md](bom.md)** for the full component list with sourced vs. to-buy status.

---

## Reference Designs

This design consolidates ideas from three published reference designs:

| Source | Designer | Reference File |
|--------|----------|----------------|
| [Pieraisa capacitor discharger kit](https://www.pieraisa.it) | Mark Maher/Pieraisa | [pieraisa.md](pieraisa.md) |
| [DIY 600V Capacitor Discharger — Constant Current](https://retronics.no/2024/03/30/diy-600-volts-capacitor-discharger-constant-current/) | Retronics.no | [600V_constant_current.md](600V_constant_current.md) |
| [Capacitor Discharger Deluxe – Smart, Fast & Safe High-Voltage Discharge](https://www.youtube.com/watch?v=5_QUd8iT3_g) | Manuel Caldeira / MAC Electronics | [deluxe.md](deluxe.md) |

---

## Improvements Over Reference Designs

### vs. Pieraisa
- Rated for **600V** (Pieraisa: 500V)
- **Automatic** threshold switching via MOSFET+NPN — no relay, no moving parts, no manual button
- Sharper LED cutoff: **~10.2V** Zener-defined threshold (Pieraisa: ~44V, divider-based)
- LED powered directly from HV+ — independent of relay state
- Correct **6:1 DVM divider** for the 600V range (Pieraisa's divider is mismatched at ~5:1)
- Each slow-path resistor explicitly stress-derated at 61% of rating at 600V

### vs. Retronics.no (constant current)
- **Faster discharge for large caps:** adaptive resistance allows higher initial current, not capped at 10mA
- Standard **FR4 through-hole PCB** — no aluminium PCB or SMD required
- No exotic ICs (Retronics requires LR8K4-G + 800V CoolMOS MOSFET pre-stage)
- **Integrated voltmeter** with calibration trimmer (not present in Retronics design)
- Defined **10.2V LED cutoff** (Retronics LED is always in the current path — no threshold)

### vs. DeLuxe (Manuel Caldeira)
- MOSFET upgraded to **STF7NM80 (800V)** — IRF840 (500V) is marginal at 600V
- Slow path split into **5× 4.7kΩ/5W** in series — distributes heat; single 820Ω/10W in DeLuxe is a thermal bottleneck at high voltage with large caps
- **R1 and R5 properly rated** for 600V: 1W, ≥600V working voltage (DeLuxe leaves ratings unspecified)
- **Zener-defined LED threshold at 10.2V** — DeLuxe LED fades naturally with no defined safe cutoff
- **Full voltmeter circuit added** with 6:1 divider, parasitic 15V supply, and optional calibration trimmer (not present in DeLuxe)
- Every component carries explicit power and voltage stress analysis in the BOM

---

## Generating the Schematic and BOM

### Schematic

Requires [schemdraw](https://schemdraw.readthedocs.io/):

```
pip install schemdraw
python blocks/gen_full_schematic.py
```

Outputs `blocks/full_schematic.svg`.

### BOM

```
python bom.py
```

This prints a summary to the terminal **and** writes `bom.md`.

The BOM (`bom.py`) is the single source of truth for all component data. It combines:
- **Design decisions** — part values, ratings, and stress calculations recorded directly in the BOM entries
- **Sourced components** — parts already in hand from the TME order (see [sourced_components.md](sourced_components.md)), marked `sourced` or `sourced_partial`
- **Parts to buy** — marked `buy`, with suggested part numbers

Schematic labels are generated from the same BOM data via the `LABEL` dictionary, so updating a value in `bom.py` automatically flows through to the schematic on the next generation run.
