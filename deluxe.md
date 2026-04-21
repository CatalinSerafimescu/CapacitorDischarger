# Capacitor Discharger DeLuxe — Schematic Analysis

**Source:** Schematic_Capacitor-Discharger-deluxe_2025-12-22.pdf  
**Designer:** MAC / Electronics Old & New — REV 1.0  
**Project born from:** frustration with slow resistor-based discharging of large caps (e.g. 33,000µF @ 80–100V)  
**Target use case:** Large electrolytic capacitors typical in vintage electronics restoration and repair

---

## Core Design Intent

> "At high voltage → controlled, safe discharge. As voltage drops → discharge speed increases."

The circuit automatically adjusts discharge resistance based on capacitor voltage — no manual switching needed.

---

## Circuit Topology

### 1. Reverse Polarity Protection — Diode Bridge
- **D1–D4:** 4× 1N4007, full-bridge rectifier
- Probes can be connected in either polarity; rectified rail is always correct polarity internally
- 1N4007 PIV = 1000V — adequate margin for 600V use
- Voltage drop: ~1.4V across two diodes in series (negligible at high voltage)

### 2. Voltage-Sensing / Threshold Circuit
- **R1 (1MΩ) + R2 (10kΩ):** Voltage divider from rectified rail to GND
- **R3 (100kΩ):** Base resistor into Q1
- **Q1 (MPSA42 or 2N3904 NPN):** Turns ON when cap voltage exceeds threshold

**Threshold calculation:**
```
V_base = V_cap × R2 / (R1 + R2) = V_cap × 10k / 1.01M
Q1 turns ON when V_base > 0.7V → V_cap > ~71V
```

### 3. Gate Drive Circuit
- **R5 (470kΩ):** Pulls IRF840 gate toward rail voltage
- **R4 (100Ω):** Series gate resistor (limits gate charge/discharge speed)
- **D9 (12V Zener, 1.3W):** Clamps gate to 12V max (protects IRF840 gate oxide)
- **Q1 collector → R4 → gate:** When Q1 is ON, pulls gate low (overrides R5 pull-up)

**Gate voltage with Q1 ON (KCL, R5=470k, R4=100Ω, Q1 Vce_sat=0.2V):**
```
V_gate ≈ (V_cap/R5 × R4) + 0.2V ≈ 0.33V at 600V → IRF840 OFF
```

**Gate voltage with Q1 OFF:**
```
V_gate = min(V_cap, 12V) via R5 and D9 clamp → IRF840 ON
```

### 4. Main Discharge Paths

| Condition | Q1 | IRF840 | Active Path | Resistance | Behavior |
|-----------|-----|--------|-------------|------------|----------|
| V_cap > 71V | ON | OFF | R7 (820Ω/10W) | 820Ω | Controlled, safe |
| V_cap < 71V | OFF | ON | IRF840 + R6 (56Ω/10W) | ~56Ω | Fast discharge |
| V_cap < 3–4V | OFF | OFF (Vgs < Vth) | None | ∞ | Fully discharged |

- **R7 (820Ω/10W):** Always-on high-resistance path — handles high-voltage discharge safely  
  - At 600V, peak power = 600²/820 = **439W** (brief pulse — acceptable for small caps)  
  - At 90V, peak power = 90²/820 = **9.9W** — right at rating; suitable for large caps (33,000µF range)
- **R6 (56Ω/10W):** Low-resistance fast path — active only below 71V via IRF840

### 5. LED Danger Indicator
- **R8 (100kΩ) + LED1:** Series from rail to GND
- Powers directly from capacitor — no external supply
- At 600V: I ≈ 6mA (bright)
- Dims as voltage drops; effectively invisible below ~3–5V
- **LED ON = charge present / dangerous; LED OFF = safe**

---

## Component List

| Ref | Value | Rating | Function |
|-----|-------|--------|----------|
| D1–D4 | 1N4007 | 1000V / 1A | Bridge rectifier (reverse polarity protection) |
| Q1 | MPSA42 or 2N3904 | NPN | Voltage threshold sense transistor |
| IRF840 | Power MOSFET | 500V / 8A | Main discharge switch |
| D9 | 12V Zener | 1.3W | IRF840 gate clamp |
| R1 | 1MΩ | — | Voltage divider top leg |
| R2 | 10kΩ | — | Voltage divider bottom leg (sets 71V threshold) |
| R3 | 100kΩ | — | Q1 base resistor |
| R4 | 100Ω | — | IRF840 gate series resistor |
| R5 | 470kΩ | — | IRF840 gate pull-up |
| R6 | 56Ω | 10W | Fast (low-V) discharge resistor |
| R7 | 820Ω | 10W | Slow (high-V) discharge resistor |
| R8 | 100kΩ | — | LED current limiter |
| LED1 | Red LED | — | Voltage/danger indicator |

---

## Design Notes & Observations

### Switching Threshold (71V)
- Derived from R1/R2 divider and Q1 Vbe (0.7V)
- Adjustable by changing R1 or R2: `V_th = 0.7 × (R1 + R2) / R2`
- Example: for 50V threshold → R1 ≈ 700kΩ; for 100V → R1 ≈ 1.43MΩ

### IRF840 Voltage Rating
- IRF840 rated for 500V Vds — **marginal for 600V use**
- For 600V designs, consider: IRFBF20 (900V), STP6NK90Z (900V), or IRFP9240 (200V P-ch, not suitable) — prefer a 700V+ N-ch MOSFET with similar gate characteristics
- Alternatively: IRF740 (400V — too low), IXTP2N80 (800V), STF7NM80 (800V)

### Q1 Transistor Note
- Original schematic listed MPSA42 (high-voltage NPN, 300V), but designer corrected: **any common NPN works** (2N3904, BC547, etc.)
- Q1 never sees more than a few volts (gate/base voltages are clamped) — voltage rating is irrelevant

### Reverse Polarity — Bridge vs. IC
- This design uses a 1N4007 bridge (passive, robust, no power needed)
- 1N4007 PIV = 1000V; adequate for 600V with margin
- Per our project preference, an IC-based ideal diode (e.g. LTC4359) would reduce voltage drop and is preferred — **bridge can be replaced if needed**

### R7 Power Handling — Large Capacitors
- At high voltage (>71V), only R7 (820Ω/10W) is in the discharge path
- **Safe for small/medium caps** at high voltage (energy = ½CV²; low C means low total energy)
- **Marginal for very large caps** (e.g. 33,000µF @ 90V → ~134J through R7 at ~9.9W average; borderline)
- For large caps at high voltage, consider increasing R7 wattage or splitting into 2× 1kΩ/10W in parallel = 500Ω/20W

---

## Adaptations Needed for Our Requirements

| Requirement | Original DeLuxe | Action Needed |
|-------------|-----------------|---------------|
| 600V rating | IRF840 = 500V (marginal) | Replace with 700V+ MOSFET (e.g. STF7NM80) |
| Voltmeter (0–100V DVM, 6:1 divider) | Not present | Add R_high (500kΩ) + R_low (100kΩ) divider; power DVM from divider output |
| IC-based polarity protection | 1N4007 bridge | Optional: replace bridge with LTC4359/MAX16141 |
| Series resistor network | R6 + R7 only | Current distribution is limited; consider 2 resistors per path for heat spread |
| LED threshold (5–10V cutoff) | Fades naturally below ~5V | Acceptable; or add Zener for sharper threshold (Pieraisa approach) |
| Digital voltmeter power | Not present | Tap from rectified rail via series resistor (e.g. 470kΩ) to power 5–30V DVM |

---

## Voltage Divider for Voltmeter (to add)

6:1 divider for 0–600V → 0–100V (DVM input):
```
R_high = 500kΩ (HV-rated, e.g. 5× 100kΩ/2W in series)
R_low  = 100kΩ (1% tolerance)
Divider ratio = 100k / (500k + 100k) = 1/6
At 600V input → 100V DVM input ✓
```
DVM powered from the R_low node (0–100V range covers the 5–30V DVM supply requirement only if cap voltage > 5V; for lower voltages DVM may power off — acceptable).

---

## Key Design Strengths

1. **Fully automatic adaptation** — no switches, no user interaction
2. **Simple, few components** — Q1, one MOSFET, two resistors, zener
3. **LED indicator** powered directly from cap — no external supply needed
4. **Inherent LED shutoff** at ~3–5V (safe voltage)
5. **Fast at low voltage** — 56Ω gives fast final discharge

---

## PCB Information (from Gerber v2.0, 2025-11-12)

- **Board size:** 73.66mm × 30.48mm (~74mm × 30mm) — compact, single PCB
- **Designed in:** EasyEDA v6.5.51
- **Layers:** 2-layer (top + bottom copper)
- **Notable pad/drill sizes:**
  - 4.0mm circular pads — large input/output terminal pads (high current)
  - 2.6×1.8mm oval+rect pads — power resistor pads (R6, R7 axial footprints)
  - 1.5mm slotted drill holes (×4, at corners) — input connectors (banana jack or screw terminal)
  - 0.75mm holes (×3, in-line) — TO-92 transistor Q1
  - 0.90mm slotted holes — diodes (D1–D4, D9)
  - 1.0–1.2mm holes — standard resistor/MOSFET leads

---

## Key Limitations vs. Our Requirements

1. IRF840 is marginal at 600V → needs substitute
2. No voltmeter circuit (must be added)
3. No IC-based polarity protection (bridge is functional but not preferred)
4. R7 (820Ω/10W) may overheat with very large caps at high voltage
