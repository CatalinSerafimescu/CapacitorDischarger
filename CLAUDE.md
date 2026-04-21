# Capacitor Discharger Tool — Project Documentation

## Project Overview

Design an electrical schematic for a professional Capacitor Discharger tool intended for safely discharging high-voltage capacitors in electronics repair and lab environments.

---

## Requirements

### Voltage Rating
- Must support capacitors up to **600V**
- Input/output probes and sockets are already sourced, rated for 1000V (adequate margin)

### Discharge Performance
- Discharge time must be **under 1 minute** even for large capacitors
- Adaptive discharge behavior (see below)

### Adaptive Discharge
- **High voltage (above threshold):** Controlled, safe discharge — current-limited to protect resistors and probes
- **Low voltage (below threshold):** Discharge speed decreases naturally as voltage drops; this is acceptable

### Discharge Resistor Network
- Preferred: **series of power-rated resistors** to distribute heat dissipation
- Avoid single large ceramic resistor
- Resistors must be rated to handle the energy stored in large capacitors

### Voltage Indication — LED
- **Red LED** powered directly from the capacitor (no external power source)
- **LED ON = dangerous** (high voltage present); **LED OFF = safe**
- LED extinguishes when capacitor voltage drops below threshold (~5V or 10V — to be finalized)
- LED must be visible during use

### Voltage Indication — Digital Voltmeter
- **Digital voltmeter** (already sourced): 0–100V, 3-wire, powered by 5–30V DC
- Requires a **6:1 voltage divider** on the input to scale 0–600V down to 0–100V
- Divider must be high-impedance / high-voltage rated

### Reverse Polarity Protection
- Must be protected against reverse polarity connection
- Preferred solution: **IC-based protection** (e.g., ideal diode controller such as LTC4359, MAX16141, or similar)
- Diode bridge solution is **2nd option**

---

## Already Sourced Components

See **[sourced_components.md](sourced_components.md)** for the complete list of sourced components and their specifications.

---

### PCB Design — High Discharge Current
- PCB must be designed to handle **peak discharge currents up to 2A** through the discharge path
- **Trace width:** minimum 1.5mm on all discharge current-carrying traces; prefer 2mm or copper pour
- **High-voltage clearance:** minimum 6mm between traces at different high potentials (≥1mm per 100V for 600V uncoated PCB)
- **Creepage distance:** minimum 6mm for 600V per IPC-2221 (external, uncoated board)
- **Input terminal pads:** minimum 4mm diameter copper pads; use 600V-rated screw terminals or banana jack pads
- **Power resistors:** footprints must allow physical standoff from PCB surface for airflow and heat dissipation
- **MOSFET:** include heatsink pad or mounting hole; TO-220 package with heatsink is preferred
- **Ground plane or copper pour** on discharge current return path to minimise resistance and inductance
- **HV and LV sections** should be physically separated on the PCB — keep control/LED circuitry away from the high-voltage discharge path
- **Avoid sharp 90° trace corners** on high-voltage nets; use 45° routing or curved traces

---

## Design Constraints & Notes
- The tool will be used in a lab/repair environment — reliability and safety are paramount
- Schematic must be practical for DIY assembly with through-hole or common SMD components
- Keep the design as simple as possible while meeting all requirements
- **Every component in the design must explicitly state its recommended type** — e.g., ceramic / metal-film / electrolytic / wirewound / metal-oxide for resistors and capacitors, package type for ICs and semiconductors. Do not leave component type ambiguous.
