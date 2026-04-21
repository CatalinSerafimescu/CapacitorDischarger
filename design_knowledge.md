# Capacitor Discharger — Design Knowledge Base

---

# PART 1: Reference Designs

## Source 1: Pieraisa Kit (500V, Italian design)

See `pieraisa.md` for full analysis.

**Key lessons:**
1. Relay-based adaptive discharge is an excellent passive approach (no IC, no firmware)
2. Diode bridge polarity protection works but 1N4007 is marginal at high voltage — prefer IC-based ideal diode
3. Fast discharge bypass switch is a useful safety feature
4. Multiple series resistors validated for heat distribution
5. Zener-based LED threshold is clean and reusable — tune Zener + divider ratio for desired cutoff voltage
6. Voltmeter powered from same rail works, but only when cap is charged — ensure adequate voltage at all relevant levels

---

## Source 2: Capacitor Discharger DeLuxe (MAC / Electronics Old & New, REV 1.0, 2025-12-22)

See `deluxe.md` for full analysis.

**Key lessons:**
1. MOSFET + NPN transistor gives clean automatic threshold switching with no moving parts (vs. relay)
2. 71V threshold set by R1/R2 divider + Q1 Vbe — above: slow controlled discharge; below: fast discharge via low-side MOSFET
3. Gate clamp zener (12V) protects MOSFET gate and sets clean gate drive regardless of cap voltage
4. Q1 can be any common NPN (2N3904, BC547) — no high-voltage rating needed
5. IRF840 is marginal at 600V (rated 500V Vds) — substitute with 700V+ device (e.g. STF7NM80, IXTP2N80)
6. 1N4007 bridge adequate for 600V (PIV = 1000V) but IC-based protection is our preference
7. PCB is compact (74×30mm) — design fits a handheld tool form factor

---

# PART 2: Our Design Knowledge & Decisions

---

## PCB Design — High Discharge Current Requirements

### Peak Current Analysis

| Path | Condition | Resistance | Peak current |
|------|-----------|------------|--------------|
| High-V path | V_cap = 600V, R ≈ 820Ω | 820Ω | ~731mA |
| Low-V path (via MOSFET) | V_cap = 71V (switch point), R = 56Ω | 56Ω | **~1.27A** |

Design target: traces and pads must handle **2A continuous** with adequate margin.

### Trace Width

Per IPC-2221A (1oz copper, 10°C temperature rise):
- 1A → ~0.5mm minimum
- 2A → ~1.0mm minimum
- **Recommendation: 1.5–2.0mm on all discharge-path traces**; use copper pour (polygon fill) on GND and HV discharge return nodes

### High-Voltage Clearance and Creepage (600V, uncoated PCB)

| Metric | Rule of thumb | 600V value |
|--------|---------------|------------|
| Air clearance | 1mm per 100V | **≥6mm** |
| Creepage (external, uncoated) | IPC-2221, 300–900V range | **≥6mm** |
| Creepage (conformal coated) | Reduced per IEC 60664-1 | ~3mm (if coated) |

- Apply between: HV input traces, discharge resistor pads, MOSFET drain pad, and any GND/LV traces
- The DeLuxe PCB (74×30mm) achieves this by physically separating the HV resistor area from the control section

### Input Terminal Pads

- Use **≥4mm diameter** copper pads (confirmed from DeLuxe Gerbers)
- Screw terminals or banana jack sockets rated for ≥600V, ≥2A
- 1.5mm slotted drill holes (as in DeLuxe) suit standard 4mm banana terminals
- Solder with adequate fillet; consider through-hole reinforcement for mechanical stress

### Power Resistors

- Use **axial wirewound** resistors (e.g. Arcol HS, Vishay RH series) — better pulse energy handling than ceramic
- Mount with **minimum 3mm standoff** from PCB surface for convection cooling
- Orient resistors so airflow is not blocked by adjacent tall components
- Footprint pad spacing must match resistor body length at rated wattage (10W axial body ≈ 30–40mm)

### MOSFET

- TO-220 package preferred — easy heatsink attachment
- Include **heatsink mounting hole** on PCB or thermal pad area
- Place MOSFET at board edge for heatsink clearance
- Drain pad should connect directly to the wide discharge trace; avoid long thin drain neck

### Layout Zones

```
[ INPUT TERMINALS ] ─── [ HV DISCHARGE PATH ] ─── [ POWER RESISTORS ]
                               │
                         [ MOSFET + Heatsink ]
                               │
                    ─────────────────────────────
                    [ CONTROL / BIAS CIRCUIT     ]   ← Low voltage
                    [ LED + VOLTMETER DIVIDER    ]   ← Keep separated from HV
```

- Physical separation of ≥10mm between HV discharge traces and LV bias/LED/voltmeter traces
- Route voltmeter divider resistors away from the discharge current loop to avoid inductive interference

### Additional Notes

- **No 90° corners** on HV traces — use 45° or curved routing
- **Conformal coating** strongly recommended on finished board — especially over HV traces, divider resistors, and input pad area
- **Silkscreen warning** on PCB: mark polarity, voltage rating, and "HIGH VOLTAGE" near input terminals

---
