# Schematic Generation Plan

## Part 1 — HV Section (`hv_section.kicad_sch`)

**Components:**
- J1, J2 (banana sockets), J3, J4 (screw terminals) — input connectors
- D1–D4 (1N4007) — full-bridge rectifier
- R_slow1–R_slow5 (4.7 kΩ / 5W) — slow discharge path, series string to GND
- R_fast (50 Ω / 5W) — fast discharge path resistor
- Q2 (STF7NM80, TO-220) — MOSFET switch

**Interface nets (global labels):**
- `HV+` — rectified rail output
- `GATE` — Q2 gate input (driven by LV section)
- `GND`

---

## Part 2 — LV Section (`lv_section.kicad_sch`)

**Components:**
- Q1 (2N3904), R1 (1 MΩ), R2 (10 kΩ), R3 (100 kΩ), R4 (100 Ω), R5 (470 kΩ), D9 (12V Zener) — threshold detector + gate drive
- R_LED1–R_LED3 (100 kΩ), D_LED (8.2V Zener), LED1 (red 5mm) — danger indicator
- R_sig1–R_sig5 (100 kΩ), R_sig_bot (100 kΩ), R_cal (200 kΩ trimmer) — DVM divider
- R_drop1–R_drop4 (15 kΩ / 3W), D_Vcc (15V Zener), C_Vcc (10 µF), C_byp1, C_byp2 (100 nF) — DVM Vcc dropper
- DVM connector (3-pin: GND, Vcc, Signal)

**Interface nets consumed (global labels):**
- `HV+`, `GATE`, `GND`

---

## Part 3 — Assembly (`schematic.kicad_sch`)

- Combine both files into one `schematic.kicad_sch`
- Merge `lib_symbols` sections (deduplicate)
- Verify all global label pairs are matched
- Add `sheet_instances`, `title_block`, PWR_FLAGs
