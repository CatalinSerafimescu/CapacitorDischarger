# 600V Constant Current Capacitor Discharger — Circuit Analysis

**Source:** https://retronics.no/2024/03/30/diy-600-volts-capacitor-discharger-constant-current/  
**Schematic:** https://retronics.no/wp-content/uploads/2024/03/capdisc_constantcurrent2.jpg  
**GitHub:** https://github.com/donpivo/CapacitorDischarger/tree/main/Discharger_ConstantCurrent

---

## Operating Principle

Constant current discharge using the **LR8K4-G** high-voltage adjustable linear regulator configured as a current source. The LR8 maintains 1.2V (its internal reference) between its OUT and ADJ pins. A shunt resistor R1 between ADJ and OUT sets the discharge current:

```
I_discharge = V_ref / R1 = 1.2V / 120Ω = 10mA (constant)
```

This is a **true constant-current** discharge regardless of capacitor voltage (within operating range), unlike resistive designs where current drops with voltage.

---

## Full Component List (from BOM + KiCAD)

| Ref    | Value            | Package              | Function                             |
|--------|------------------|----------------------|--------------------------------------|
| U1     | LR8K4-G          | TO-252-2             | HV adjustable linear regulator (CC source) |
| Q1     | IPD80R1K0CEATMA1 | TO-252-2             | N-ch MOSFET, 800V, series pass / voltage limiter |
| D3     | ABS10            | Diode_Bridge_Diotec  | Bridge rectifier — polarity protection |
| D4     | 200V 3W          | D_SMB (handsoldering)| Zener — gate voltage clamp / voltage limiter |
| D2     | 10V 0.5W         | SOD-123              | Zener — Q1 gate-source protection     |
| D1     | LED              | 1206                 | Visual discharge indicator             |
| R1     | 120Ω             | 0805                 | LR8 current-set shunt (10mA)          |
| R2     | 100Ω 1W (KiCAD) / 1kΩ 1W (BOM) | 2512 | Protective fuse/series resistor    |
| R3     | 100kΩ 1W         | 2512                 | Gate voltage divider (1/3)            |
| R4     | 100kΩ 1W         | 2512                 | Gate voltage divider (2/3)            |
| R5     | 100kΩ 1W         | 2512                 | Gate voltage divider (3/3)            |
| C1     | 1µF              | 0805                 | LR8 output/ADJ filter                 |
| C2     | 100nF 250V       | 1206                 | Slows voltage rise, prevents transients |
| J1/J2  | Input pads       | TestPoint D4.0mm     | Probe connection                      |
| H1–H8  | M3 holes         | MountingHole 3.2mm   | PCB mounting                          |

> **Note:** R2 value discrepancy between KiCAD (100Ω 1W) and BOM (1kΩ 1W) — likely a revision difference. Either value functions as a protective series element.

---

## Circuit Topology

### 1. Polarity Protection — ABS10 Bridge Rectifier (D3)
- Input probes (J1/J2) feed into a full-bridge rectifier
- Output is always positive regardless of probe polarity
- Rated: 1kV, 1A — handles the full voltage range
- **Trade-off:** ~1.4V forward drop (2 diodes in series) — negligible at high voltage but dissipates heat

### 2. Voltage Limiting Stage — Q1 + D4 + R3/R4/R5
The LR8K4-G is rated for a maximum of **450V input**. To support 600V operation, a MOSFET source-follower stage limits the voltage seen by the LR8:

- **Q1 (IPD80R1K0CEATMA1):** 800V N-channel CoolMOS, very low RDS(on) (~1Ω)
  - Drain: connected to high-voltage rail (post-bridge, up to 600V)
  - Source: feeds LR8 input — clamped to ~200V max
  - Gate: driven by R3+R4+R5 voltage divider from input rail
- **D4 (200V zener):** In the gate drive network, clamps gate or Vds to limit LR8 input to ≤200V
- **D2 (10V zener):** Gate-source protection (Vgs clamp), prevents Vgs from exceeding 10V
- **C2 (100nF 250V):** Slows gate voltage rise, prevents transient spikes on power-up

**Operating behavior:**
- When Vcap > ~200V: Q1 absorbs excess voltage across Vds; LR8 sees ~200V
- When Vcap < ~200V: Q1 passes voltage through with minimal loss; LR8 follows input
- The 300kΩ divider (R3+R4+R5 in series) provides high-impedance gate bias with low power loss (~2mA at 600V)

### 3. Constant Current Source — U1 (LR8K4-G) + R1
- LR8K4-G configured with R1 (120Ω) between ADJ and OUT pins
- Internal Vref = 1.2V → I = 1.2V / 120Ω = **10mA constant**
- Current stays at 10mA for any input voltage within LR8 operating range

### 4. LED Indicator — D1
- LED is in the discharge current path
- Illuminates whenever current flows (capacitor voltage > LED Vf)
- Brightness decreases as voltage drops (current is constant, but at very low voltage the LED circuit changes behavior)
- No separate supply needed — powered directly from capacitor

### 5. Filtering — C1
- 1µF capacitor on LR8 output/ADJ node
- Stabilizes the regulation loop

---

## Discharge Performance

Constant current discharge follows:
```
dV/dt = I / C = 10mA / C
```

| Capacitor | Voltage | Discharge Time |
|-----------|---------|----------------|
| 100µF     | 600V    | 6 seconds      |
| 1000µF    | 600V    | 60 seconds     |
| 10000µF   | 600V    | 600 seconds    |
| 100µF     | 400V    | 4 seconds      |

> **Key insight:** Discharge time scales linearly with capacitance. For the 1 minute target, this design supports up to **1000µF at 600V**. Larger caps will take longer.

**Power dissipation during discharge (worst case, Vcap = 600V):**
- Total: V × I = 600V × 10mA = **6W** (distributed between Q1 and LR8)
- Q1 handles: (Vcap - 200V) × 10mA = 400V × 10mA = 4W
- LR8 handles: 200V × 10mA = 2W
- Heat on aluminum PCB is negligible at these power levels

---

## Design Decisions & Trade-offs

| Decision | Rationale |
|----------|-----------|
| LR8K4-G as CC source | Simple, elegant — just one IC + one resistor for constant current |
| MOSFET voltage limiter | Extends operation to 600V while protecting 450V-rated LR8 |
| Bridge rectifier D3 | Simple polarity protection without external supply |
| 3× series 100kΩ resistors | Distributes power dissipation vs. single resistor |
| Aluminum PCB | Better thermal performance vs. FR4 (requires hot-plate soldering) |
| 10mA current | Conservatively safe for probes and components at high voltage |

---

## Limitations Relative to Our Requirements

| Our Requirement | This Design | Gap |
|----------------|-------------|-----|
| Up to 1000V | Max 600V | LR8 + MOSFET stage would need redesign for 1000V |
| Under 1 min for large caps | ~60s for 1000µF | Fails for caps > 1000µF |
| No bridge rectifier | ABS10 bridge used | Conflicts with our preferred IC-based polarity protection |
| Digital voltmeter | Not included | Missing |
| 10:1 voltage divider | Not included | Missing |

---

## Applicable Ideas for Our Design

1. **LR8K4-G as current source:** Elegant approach — single IC sets constant current. But 450V limit means we need a MOSFET pre-stage for 1000V.
2. **MOSFET voltage limiter concept:** Using a CoolMOS MOSFET to absorb excess voltage above the regulator's rating is a valid technique to extend range. For 1000V, we'd need an 800V+ MOSFET and a higher zener voltage or different clamping strategy.
3. **Series resistor network (R3+R4+R5):** Distributing high-voltage bias resistors across multiple 1W components is a sound approach we should adopt.
4. **C2 for slowing voltage rise:** Good practice for protecting the IC from inrush transients.
5. **LED in discharge path:** Simple, no-power-required indicator — works for us as the high-voltage danger LED.

---

## Concerns for Adaptation to 1000V / Our Design

- **LR8K4-G is only rated to 450V input.** For 1000V, we cannot use it directly — even with a MOSFET pre-stage, we'd need Vgs clamping designed for a higher voltage swing, and the MOSFET Vds would see up to 800V.
- **Discharge current of 10mA may be insufficient** for large capacitors (>1000µF at 1000V would take >100 seconds).
- **Increasing current to 50–100mA** would require a different current-setting resistor (R1 = 1.2V / 50mA = 24Ω or 12Ω) but increases power dissipation proportionally.
- **Bridge rectifier vs. IC polarity protection:** The ABS10 solution is simple but our design spec requires IC-based protection.
