# Capacitor Discharger — Implementation Plan

## Context

Build a professional handheld **600V Capacitor Discharger** for hobby electronics restoration — tube amps, vintage radios, CRT TVs, consumer linear/SMPS PSUs. The tool must:

- Discharge typical hobby caps (100µF–1mF at up to 600V) in **under 60 s**
- Adapt automatically: controlled current above ~71 V, fast dump below
- Red "danger" LED ON whenever V > ~10 V, OFF below (no external supply)
- Continuous **0–100 V digital voltmeter** readout via **6:1 input divider**
- Tolerate reverse probe polarity
- Reuse already-sourced components where possible; new parts limited to power-rated resistors (Ohmite WN-series), a higher-V MOSFET, and a handful of Zeners/diodes

This plan consolidates the **DeLuxe (MAC)** adaptive MOSFET topology, the **Pieraisa** parasitic DVM-power approach, and our PCB rules into one coherent design adapted for 600 V rating.

## Design decisions (confirmed with user)

| Decision | Chosen |
|---|---|
| Slow-path resistor network | **5× 4.7 kΩ / 5 W** Ohmite WN-series (or equivalent wirewound / ceramic cement) |
| Threshold detection | **Q1 NPN (DeLuxe-style)** — 2N3904 + divider, self-biased |
| DVM power | **Parasitic from cap rail (Pieraisa-adapted)** — dropper + 15 V Zener + smoothing cap |
| LED safe-cutoff | **~10 V** — 8.2 V Zener + red LED + 300 kΩ current limit |
| Polarity protection | **4× 1N4007 full-bridge** (bridge chosen over LTC4359: avoids a second HV bias rail that doubles circuit complexity for marginal gain at these voltages) |

## Topology

```
PROBE_A ─┐
         ├── [4× 1N4007 bridge] ─── HV+ RAIL ────────┬── R_slow  (5× 4.7kΩ/5W) ─────────────────── GND
PROBE_B ─┘                                           │
                                                     ├── R_fast (50Ω/5W) ── Q2 Drain
                                                     │                      Q2 Source ─ GND
                                                     │                      Q2 Gate ← R4 ← Q1_collector (GND when V>71V)
                                                     │                                   ← R5 ← HV+  (pull-up, clamped by D9 12V)
                                                     ├── R1 (1MΩ) ── node_A ── R2 (10kΩ) ── GND
                                                     │                 └── Q1 base (2N3904, emitter=GND)
                                                     ├── R_LED (3× 100kΩ) ── D_LED (8.2V Z) ── LED1 ── GND
                                                     ├── R_sig_top (5× 100kΩ) ── node_sig ── R_sig_bot (100kΩ) ── GND
                                                     │                            └── DVM Signal-In
                                                     └── R_drop (4× 15kΩ/3W) ── node_Vcc ── D_Vcc (15V Z) // C_Vcc (10µF) ── GND
                                                                                  └── DVM Vcc+
```

## Block-by-block design

### 1. Reverse-polarity protection
- **D1–D4**: 4× 1N4007 (DO-41 through-hole) — PIV 1000 V, I_F 1 A. 400 V margin over 600 V, ~1.4 V total forward drop (negligible at HV).

### 2. Slow discharge path (always on, dominant above 71 V)
- **R_slow**: 5× **4.7 kΩ / 5 W wirewound** in series (Ohmite WN series or equivalent ceramic cement).
- Total **23.5 kΩ / 25 W / 1750 V** working voltage.
- At 600 V: 25.5 mA, **3.06 W per resistor (61 % of rating)**, 120 V per resistor (well under 350 V part limit).
- 600 V → 71 V transition: τ · ln(600/71) = 23.5 s × 2.135 × C_cap
  - 100 µF → 5 s   ·   470 µF → 22 s   ·   1 mF → 50 s ✓   ·   1.2 mF → 60 s (practical ceiling)
- **Mount**: axial, ≥3 mm PCB standoff, in a row oriented for airflow.

### 3. Fast discharge path (MOSFET-switched, active below 71 V)
- **R_fast**: 50 Ω / 5 W wirewound (Ohmite WN or equivalent).
- **Q2**: **STF7NM80** (TO-220, 800 V V_ds, 6 A I_d, R_ds(on) 1.7 Ω typ). Alternatives: STP10NK80Z, IXTP2N80. IRF840 (500 V) rejected — marginal for 600 V.
- At switch-on (V_cap = 71 V): I_peak = 1.42 A, P_peak ≈ 100 W for τ = 50 Ω·C_cap seconds; energy for 1 mF cap = 2.5 J (trivial for TO-220 SOA).
- **Mount**: TO-220 at board edge with clip-on heatsink (~10 °C/W, e.g. Wakefield 637-10ABPE).

### 4. Threshold detector (Q1 NPN, DeLuxe-style)
| Ref | Value / Part | Source |
|---|---|---|
| Q1 | 2N3904 NPN TO-92 | **buy** |
| R1 | 1 MΩ / 1 W / ≥600 V metal film | **buy** |
| R2 | 10 kΩ / 0.25 W | **buy** |
| R3 | 100 kΩ / 0.6 W (Q1 base) | **stock** (MF006FF1003A50) |
| R4 | 100 Ω / 0.25 W (gate series) | **buy** |
| R5 | 470 kΩ / 1 W / ≥600 V metal film (gate pull-up) | **buy** |
| D9 | 12 V / 1.3 W Zener (BZX85C12) | **buy** |

- **Threshold**: V_th = 0.7 V · (R1 + R2) / R2 = **71 V**. Tune via R2 if desired.
- V_cap > 71 V → Q1 saturates → gate pulled to ~0.33 V → Q2 **OFF** → slow path only.
- V_cap < 71 V → Q1 off → gate pulled to V_rail clamped at 12 V by D9 → Q2 **ON** → fast path adds.

### 5. LED danger indicator (~10 V cutoff)
- **Chain**: HV+ → R_LED (3× 100 kΩ series = 300 kΩ) → D_LED (8.2 V / 0.5 W Zener, BZX55C8V2) → LED1 (5 mm red, V_f ≈ 2 V) → GND.
- **Cutoff**: V_cap > V_Z + V_f ≈ **10.2 V** → conduction; below → LED OFF.
- 600 V: I_LED ≈ 2 mA (bright);  100 V: 0.3 mA (dim-visible);  <10 V: 0.
- R_LED per-resistor stress: 200 V / 0.4 W at 600 V input (inside 250 V / 0.6 W rating).

### 6. DVM signal divider (6:1)
- **R_sig_top**: 5× 100 kΩ / 0.6 W / 250 V in series = 500 kΩ (each resistor sees 100 V at 600 V rail — well within 250 V rating).
- **R_sig_bot**: 1× 100 kΩ.
- Ratio **100 k / 600 k = 1/6**. At 600 V cap → 100 V at DVM signal pin (full scale).
- String current 1 mA total; 0.1 W per resistor (cool).
- **Optional calibration**: sourced 200 kΩ trimmer (T93YA200K) in series with R_sig_bot allows fine-tune of full-scale reading.

### 7. DVM Vcc dropper (parasitic, Pieraisa-adapted)
- **R_drop**: 4× **sourced MOF3WS-15K** (15 kΩ / 3 W / 500 V metal-oxide) in series = 60 kΩ / 12 W capacity.
- **D_Vcc**: 15 V / 1 W Zener (1N4744A) — shunt regulator.
- **C_Vcc**: 10 µF / 25 V electrolytic (reuse **sourced EEAGA1E100H**) across Zener for ripple smoothing.
- 600 V cap: I = (600−15) / 60 k = **9.75 mA** → P per resistor 1.42 W (49 % of 3 W — comfortable).
- DVM live when V_cap > ~20 V; below that DVM turns off (same behaviour as Pieraisa — acceptable because LED is also off by then).
- **Verify DVM current rating**: if the sourced DVM draws > 9 mA at 15 V V_cc, reduce R_drop to 3× 15 kΩ (45 kΩ, 13 mA headroom).

## Complete BOM

### Reuse from stock
| Qty | Used for | Part / sourced # |
|---|---|---|
| 10 | R3, R_LED×3, R_sig_top×5, R_sig_bot | 100 kΩ / 0.6 W / 250 V (MF006FF1003A50) |
| 4 | R_drop×4 | 15 kΩ / 3 W / 500 V MOF3WS-15K |
| 1 | C_Vcc | 10 µF / 25 V electrolytic (EEAGA1E100H) |
| 1 (optional) | DVM calibration trimmer | 200 kΩ (T93YA200K) |
| 2 | Input terminals | SLB4-G-21/-22 banana sockets or MKDS5/2-9.5 screw terminals |
| 2 (bypass) | Local decoupling near Q1/DVM | 100 nF / 50 V ceramic (K104K10X7RF5UH5) |

### To buy
| Qty | Ref | Part / value | Suggested P/N |
|---|---|---|---|
| 5 | R_slow | 4.7 kΩ / 5 W wirewound | Ohmite WN-series or Vishay AC05 |
| 1 | R_fast | 50 Ω / 5 W wirewound | Ohmite WN-series |
| 1 | Q2 | 800 V N-MOSFET TO-220 | STF7NM80 / STP10NK80Z / IXTP2N80 |
| 4 | D1–D4 | Bridge diodes | 1N4007 |
| 1 | Q1 | Small-signal NPN | 2N3904 |
| 1 | R1 | 1 MΩ / 1 W / ≥600 V metal film | any (verify voltage rating) |
| 1 | R2 | 10 kΩ / 0.25 W | any |
| 1 | R4 | 100 Ω / 0.25 W | any |
| 1 | R5 | 470 kΩ / 1 W / ≥600 V metal film | any (verify voltage rating) |
| 1 | D9 | 12 V / 1.3 W Zener | BZX85C12 |
| 1 | D_LED | 8.2 V / 0.5 W Zener | BZX55C8V2 |
| 1 | D_Vcc | 15 V / 1 W Zener | 1N4744A |
| 1 | LED1 | 5 mm red LED | any (V_f ≈ 2 V) |
| 1 | Heatsink | TO-220 clip-on, ~10 °C/W | Wakefield 637-10ABPE |

## PCB design rules (from `design_knowledge.md`)

- Trace width ≥ **1.5 mm** on all discharge-current nets (HV+, drain, source, slow/fast resistor strings); copper pour on GND return.
- HV clearance/creepage ≥ **6 mm** (IPC-2221, 600 V, uncoated).
- Input pads ≥ **4 mm** diameter.
- Axial power resistors on ≥ 3 mm standoff, aligned in a row for airflow.
- Q2 at board edge with heatsink mounting hole; wide drain trace, no narrow neck.
- Physical separation ≥ **10 mm** between HV section (bridge → R_slow / R_fast / Q2) and LV section (Q1, LED, DVM divider, Vcc dropper).
- No 90° corners on HV traces — use 45° or curves.
- Silkscreen: "HIGH VOLTAGE — UP TO 600 V DC" near input terminals; polarity hint; Zener / LED / electrolytic polarity marks.
- Conformal coating strongly recommended on finished board, especially across HV nets and divider strings.

## Critical files / deliverables

| File | Purpose |
|---|---|
| `schematic.kicad_sch` (new) | Full KiCad 7+ schematic — ideally mirror block structure above |
| `pcb.kicad_pcb` (new) | 2-layer PCB following the rules section |
| `bom.md` (new) | Consolidated BOM with sourced vs. to-buy status |
| `assembly_notes.md` (new) | Mount orientation for R_slow, Q2 heatsink, polarity of bridge / Zeners / electrolytic |
| `CLAUDE.md` (reference) | Top-level requirements, voltage rating, PCB rules |
| `design_knowledge.md` (reference) | PCB / layout guidance, reused verbatim |
| `deluxe.md`, `pieraisa.md` (reference) | Cross-check topology and component-value rationale |
| `sourced_components.md` (reference) | Confirm stock parts before ordering |

## Verification / test procedure

### Phase 1 — low-voltage bench test (≤ 30 V, on breadboard)
1. Wire up threshold + MOSFET + LED + DVM sections with breadboard jumpers; use a bench DC supply in place of cap+bridge.
2. Sweep 0 → 30 V at the "HV+" node:
   - LED turns ON above ~10 V, OFF below ✓
   - DVM reads proportionally (use optional 200 kΩ trimmer to zero the span)
   - At these voltages Q1 stays OFF, Q2 stays ON, fast path is live — verify with a small test cap (1 µF) that it discharges quickly.

### Phase 2 — mid-voltage test (100–300 V, assembled PCB, charged electrolytic)
1. Charge a 100 µF / 450 V cap to 300 V via a current-limited HV source (variac + bridge, or HV bench supply).
2. Connect probes; time the discharge with a scope on the DVM signal node (or the DVM itself).
3. Verify:
   - LED stays on until V_cap ≈ 10 V, then off
   - DVM tracks from 300 V down to ~20 V (then goes dark as dropper output dips below 5 V)
   - No visible smoke, resistor body temps < 80 °C after 10 consecutive discharges (IR gun)

### Phase 3 — full 600 V test (post-conformal-coat)
1. Charge a test cap rated ≥ 700 V (e.g. 470 µF / 700 V film or a test jig with 2× 450 V electrolytics in series) to exactly 600 V.
2. Discharge via tool; measure time with a stopwatch + DVM:
   - 470 µF / 600 V → expect ~22 s to reach 71 V, then sub-second fast path. Total < 25 s ✓
   - 1 mF / 600 V → expect ~50 s. Total < 52 s ✓
3. Repeat 5× to confirm repeatability. Inspect for discolouration on R_slow bodies.
4. **Safety checks**:
   - Reverse-polarity test: apply 50 V backwards, confirm bridge routes correctly, no smoke.
   - Probe short-circuit test: short probes together with tool powered — nothing should happen (no current unless a cap is attached).
   - Leave tool connected to a charged 1 mF / 600 V cap after discharge completes; verify MOSFET + dropper resistors do not heat up in steady state (MOSFET should be OFF below 71 V and no sustained current should flow after cap reaches ~10 V).

### Calibration
- With a known reference voltage (e.g. a 300 V bench HV supply), adjust the optional 200 kΩ trimmer in series with R_sig_bot until DVM reads 50.0 V (300 V / 6).
- Repeat at 100 V and 500 V to confirm linearity.
