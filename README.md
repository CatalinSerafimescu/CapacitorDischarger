# 600V Capacitor Discharger

A professional, handheld capacitor discharger designed for safely discharging high-voltage capacitors in hobby electronics restoration — tube amplifiers, vintage radios, CRT televisions, and consumer power supplies.

---

## Features

- Discharges capacitors up to **600V** in **under 60 seconds** (up to ~1200µF)
- **Adaptive discharge:** controlled current above ~63 V (slow resistive path); fast dump below (MOSFET-switched). Switch point 55–83 V across Q1 hFE (25–300) and 0–60 °C corners; peak fast-dump current ≤ 1.6 A
- **Red LED danger indicator:** ON above ~10V, OFF when safe — powered directly from the capacitor, no external supply. Uses a low-current (2 mA) LED: the chain current is only ~50 µA at 30 V, where a standard LED looks dark
- **Integrated digital voltmeter:** Axiomet PM-128 3½-digit LCD reading volts directly ("600" at 600 V, 1 V steps) via a 10 000:1 divider, powered by a floating internal 9V battery (holder with ON/OFF switch)
- **Reverse polarity protection:** 1N4007 full-bridge rectifier
- **Protection fuse:** 600V-rated 2A fuse on the HV+ line guards against single-fault conditions
- **Thermal cutoff on R_fast:** if the probes touch a *live* supply below the threshold, Q2 stays on and R_fast would dissipate 41–74 W indefinitely (the 2 A fuse never blows) — a one-shot 133 °C thermal fuse clamped to R_fast opens the fast path; the slow path keeps working. **Still: never connect the tool to a powered circuit.**
- Designed for **DIY assembly** with through-hole components
- A residual ~1.2–1.4V remains on the capacitor (two bridge-diode drops) — below the 10V safe threshold

---

## Schematic

![Schematic](blocks/full_schematic.svg)

---

## Bill of Materials

See **[bom.md](bom.md)** for the full component list with sourced vs. to-buy status.

**Note on DVM power:** the PM-128 draws ~1 mA from its own 9V battery (~500 h per alkaline cell). Its datasheet requires the supply and the measured input to have separate grounds, so the battery floats — it is **not** connected to circuit GND.

**Note on DVM calibration:** set with the PM-128's own trimmer (R4) against a known DC voltage. The meter's >100 MΩ input doesn't load the divider. (The earlier 0–100 V LED module was dropped: its 0.525 MΩ input made the 6:1 divider uncalibratable.)

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
- **Direct-reading voltmeter** with a 10 000:1 divider for the 600V range (Pieraisa's divider is mismatched at ~5:1)
- Each slow-path resistor explicitly stress-derated at 61% of rating at 600V

### vs. Retronics.no (constant current)
- **Faster discharge for large caps:** adaptive resistance allows higher initial current, not capped at 10mA
- Standard **FR4 through-hole PCB** — no aluminium PCB or SMD required
- No exotic ICs (Retronics requires LR8K4-G + 800V CoolMOS MOSFET pre-stage)
- **Integrated voltmeter**, calibratable (not present in Retronics design)
- Defined **10.2V LED cutoff** (Retronics LED is always in the current path — no threshold)

### vs. DeLuxe (Manuel Caldeira)
- MOSFET upgraded to **STP10NK80Z (800V, 0.9 Ω)** — IRF840 (500V) is marginal at 600V
- Slow path split into **5× 4.7kΩ/5W** in series — distributes heat; single 820Ω/10W in DeLuxe is a thermal bottleneck at high voltage with large caps
- **R1 and R5 properly rated** for 600V: 3W, 750V working voltage (DeLuxe leaves ratings unspecified)
- **Zener-defined LED threshold at 10.2V** — DeLuxe LED fades naturally with no defined safe cutoff; note the LED is dim below ~70V, so a low-current (2mA-rated) LED is used
- **Full voltmeter circuit added** with 10 000:1 divider, open-resistor input clamp, and battery-powered LCD meter (not present in DeLuxe)
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

This prints a summary to the terminal **and** writes `bom.md` and the shopping list `TO_BUY_list.csv`.

The BOM (`bom.py`) is the single source of truth for all component data. It combines:
- **Design decisions** — part values, ratings, and stress calculations recorded directly in the BOM entries
- **Sourced components** — parts already in hand from the TME order (see [sourced_components.md](sourced_components.md)), marked `sourced` or `sourced_partial`
- **Parts to buy** — marked `buy`, with suggested part numbers

Schematic labels are generated from the same BOM data via the `LABEL` dictionary, so updating a value in `bom.py` automatically flows through to the schematic on the next generation run.
