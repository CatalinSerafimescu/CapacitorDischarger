# Source 1: Pieraisa Kit — Reference Analysis

**Origin:** https://www.pieraisa.it/forum_share/KITS/Discharge.Tool.Datasheet.pdf
**Based on Mend It Mark design** https://www.youtube.com/watch?v=pNkEchLQWDU

**Rating:** 500V max, RDS = 120Ω min / 940Ω typ / 5640Ω max  

---

## Topology: Diode Bridge for Reverse Polarity Protection

- 4× 1N4007 diodes form a full bridge (D1+D3 on top rail, D4+D5 on bottom rail)
- Ensures discharge current always flows in the same direction through the circuit regardless of probe polarity
- Simple, passive, no IC needed
- **Limitation:** 1N4007 PIV = 1000V — right at the limit for 1000V designs; at 1000V, voltage spikes or transients will exceed the rating
- **Trade-off:** ~1.4V forward drop across two diodes in series (acceptable for high-voltage discharge, minimal energy loss)
- **For 1000V designs:** Need higher-rated diodes (e.g., 1N5408 = 1000V, or HV series like FR107, P6KE series), or move to IC-based protection

---

## Topology: Relay-Based Adaptive Discharge (Passive, Elegant)

- R2 (10kΩ, 7W) connects directly from the rectified high-voltage rail to the relay (RL1) coil
- At high capacitor voltage → sufficient current through R2 → relay energizes → connects low-resistance discharge path (R5 = 120–220Ω, 5W)
- As voltage drops → coil current decreases → relay drops out at its dropout voltage → circuit switches to higher resistance path (R1+R4 = 940Ω)
- **This is fully passive and automatic — no control IC, no comparator, no firmware**
- The relay dropout voltage determines the switching threshold (typically 8–10V for a 12V relay)
- **Key insight:** The relay coil itself acts as a current sensor and threshold detector simultaneously

---

## Resistor Network

| Resistor | Value | Power | Role |
|----------|-------|-------|------|
| R5 | 120 or 220Ω | 5W | Fast/low-resistance discharge path (relay energized) |
| R1 | 470Ω | 5W | Series discharge resistor (relay dropped out) |
| R4 | 470Ω | 5W | Series discharge resistor (relay dropped out), R1+R4 = 940Ω |
| R2 | 10kΩ | 7W | Relay coil current limiter / adaptive threshold setter |
| R6 | 4.7kΩ | 7W | Auxiliary discharge / part of resistor ladder |

- Multiple resistors in series distributes thermal load — no single large ceramic resistor
- Power rating must account for worst-case: E = ½CV² for largest expected capacitor

---

## Fast Discharge Override (Manual Switch)

- SW T2 and SW T4: two switches that bypass the diode bridge legs
- When both closed: R5 is connected directly in the discharge path, bypassing diode drops
- Activated by button W1 (labeled "FAST" mode)
- **Recommended use: only when voltage is above 70V** — below 70V the relay has dropped out and the slower path is sufficient
- At high voltage (>70V): R5 (120/220Ω) is included in the path, giving minimum resistance and maximum discharge current
- **Note:** Bypassing diodes means polarity protection is lost in fast discharge mode — user must ensure correct probe orientation
- **Design insight:** Fast mode is a user-initiated safety assist, not automatic — the operator judges when to use it based on voltage reading

---

## LED Danger Indicator

- Voltage divider: R3 (680kΩ) + R8 (100kΩ) scales down the capacitor voltage
  - Divider ratio: 100k / (680k + 100k) ≈ 0.128
- D2 (5.6V Zener, 1W) + R9 (470Ω) + LED1 form a threshold indicator
- **Behavior: LED ON = dangerous (high voltage present); LED OFF = safe**
  - High cap voltage → sufficient current through divider → D2 conducts → LED lights (warning)
  - Cap voltage drops below threshold → D2 stops conducting → LED goes OFF (safe to touch)
- The Zener threshold + divider ratio sets the turn-off point:
  - D2 threshold ≈ 5.6V at divider node → cap voltage at turn-off ≈ 5.6V / 0.128 ≈ **44V**
- Pieraisa's Zener-threshold approach is directly reusable for our design

---

## Voltmeter Integration

- Digital voltmeter W2 (P1): 3-wire type (VCC+, signal IN, GND)
- Powered from VCC rail (same as capacitor voltage through divider/relay)
- Input signal = output of R3/R8 voltage divider
- R3 (680kΩ) also doubles as the voltmeter VCC source resistor
- DVM range: 0–100V, so divider must scale max cap voltage to ≤100V
  - For 500V max: ratio needed = 100/500 = 0.2 → but actual ratio here is 0.128 → max reading = 64V at 500V (under-ranges slightly or voltmeter is calibrated)
  - **For our 600V design:** Need 6:1 divider (0–100V DVM → 6:1 → 0–600V range)

---

## Key Design Lessons from Pieraisa

1. **Relay-based adaptive discharge is an excellent passive approach** — worth adopting; need a 600V-capable relay or place relay on low-voltage side of divider
2. **Diode bridge polarity protection** works well but 1N4007 is marginal at high voltage; for our design use IC-based ideal diode (as per our requirement)
3. **Fast discharge bypass switch** is a useful safety feature — bypassing bridge or adding a direct low-resistance path
4. **Multiple series resistors** for discharge is validated — distribute heat across R1, R4, R5, R6
5. **Zener-based LED threshold** is clean — tune Zener voltage and divider ratio for desired safe threshold (5V or 10V per our requirement)
6. **Voltmeter powered from same rail** through a resistor — simple but means voltmeter only works when cap is charged; our design should ensure voltmeter has adequate power at all relevant voltages
