# Simulation — 600 V Capacitor Discharger

Transient and DC-sweep SPICE simulations to verify every operating regime before PCB commit.

## Prerequisites

- **ngspice 46** at `E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice.exe`
- Python 3.x with `numpy`, `matplotlib`, `pandas`

Verify ngspice:
```
"E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice.exe" -v
```

## Running

```bash
cd simulation

# Run all scenarios
python run_sim.py --all

# Run one scenario
python run_sim.py A_full_600V_1mF

# List available scenarios
python run_sim.py --list
```

Results land in `results/<scenario_name>/`:
- `sim.cir` — rendered netlist fed to ngspice
- `out.csv` — time + node voltages + branch currents
- `plot.png` — 3-panel plot
- `summary.txt` — PASS/FAIL per assertion

Aggregate: `results/RESULTS.md`

## Scenarios

| Name | V0 | C_dut | Purpose |
|------|----|-------|---------|
| `A_full_600V_1mF`      | 600 V | 1 mF    | Full sweep, all regimes |
| `B_mid_300V_470uF`     | 300 V | 470 µF  | Typical hobby cap |
| `C_mid_100V_100uF`     | 100 V | 100 µF  | Brief slow then fast |
| `D_low_50V_100uF`      |  50 V | 100 µF  | Fast-path-only from t=0 |
| `E_below_LED_8V_100uF` |   8 V | 100 µF  | LED stays OFF |
| `F_steady_state_600V`  | 600 V | 100 mF  | Quasi-steady-state probes |
| `G_threshold_sweep`    | DC sweep 0→200 V | — | Confirm ~63 V switch point |
| `G2_threshold_lowbeta` | DC sweep 0→200 V | — | Worst-case low-hFE (BF=40) Q1 corner: switch point shifts only to ~68 V with R3 = 10 kΩ |
| `G3_threshold_cold_lowhfe` | DC sweep 0→200 V | — | Datasheet-min hFE (BF=25) at 0 °C: highest switch point (~83 V) → worst peak I_fast ≈ 1.6 A, still < 2 A |
| `G4_threshold_hot_highhfe` | DC sweep 0→200 V | — | BF=300 at 60 °C: lowest switch point (~55 V) |
| `H_dvm_divider_clamp` | DC sweep 0→600 V | — | PM-128 10 000:1 divider (5 × 100 kΩ over 2 × 100 Ω): reads 599.9 at 600 V (before R4 trim) and 10.00 at 10 V; with the bottom resistors open, D_clamp holds the meter input at 0.72 V |
| `I_reverse_600V_1mF` | −600 V | 1 mF | Reverse polarity: same 45 s discharge, −1.05 V residual, DVM still reads positive |
| `J_hotplug_600V` | 600 V | 1 mF | Probe contact onto a charged cap (1 µH leads, 1 µs contact): Q2 must not conduct |
| `K_bigcap_60V_47mF` | 60 V | 47 mF | ~85 J fast dump into R_fast — TF1 must not nuisance-trip |
| `L_live_supply_48V` | 48 V source | — | Probes on a live supply: R_fast would see ~41 W forever (F1 never blows) — TF1 must open |

(Scenario `H_dvm_led_module` was removed 2026-07-29: it documented that the parasitic Vcc dropper could not power a 20–30 mA LED-display DVM module; the real module measured 12–15 mA, so the dropper was replaced by an internal 9 V battery and the Vcc branch no longer exists in the netlists.)

## Adding a scenario

1. Add an entry to `scenarios.py::SCENARIOS` with `name`, `template`, `v0`, `cdut`, `tstep`, `tstop`, and an `assertions` function.
2. The assertions function receives a `pandas.DataFrame` (columns = ngspice output names) and returns `list[(bool, str)]`.
3. Run `python run_sim.py <your_name>`.

## Key nodes

| Node | Meaning |
|------|---------|
| `V(HVp)` | Post-bridge discharge-network rail — ~1.2 V below the actual capacitor voltage (two diode drops through the reverse-polarity bridge D1-D4); all existing assertions are written against this rail |
| `V(n_probe_a)`, `V(n_probe_b)` | Capacitor terminals (transient scenarios only) — `V(n_probe_a) - V(n_probe_b)` is the true cap voltage, including the ~0.4-2.5 V permanent residual left by the bridge |
| `V(n_gate)` | MOSFET gate (~12 V = on, <1 V = off) |
| `V(n_sigout)` | PM-128 input — V(HVp) / 10 000 (×10 000 = displayed reading) |
| `I(V_islow)` | Slow path current |
| `I(V_ifast)` | Fast path (MOSFET) current |
| `I(V_iled)` | LED chain current |
| `V(n_temp)` | R_fast/TF1 body temperature in °C (behavioural thermal model) |
| `V(n_tf_latch)` | TF1 state: > 0.5 V = thermal cutoff has opened (one-shot) |

## Model notes

- **Q2 (fast-path MOSFET):** `STP10NK80Z` is a generic SPICE level-1 model standing in for the sourced BOM part (0.9 Ω Rds(on), 800 V, 9 A). It is not a vendor-supplied model — replace with one if available.
- **Q1 (threshold detector):** `QMPSA42` uses BF=150 (optimistic hFE). `QMPSA42LB` is a worst-case corner with BF=40, matching real MPSA42 hFE at ~1 mA collector current. With R3 = 10 kΩ (reduced from 100 kΩ on 2026-07-29) the switch point is nearly hFE-independent: scenario G measures 63 V with the nominal model, scenario G2 measures 68 V at the low-hFE corner. (With the old R3 = 100 kΩ these were 76 V and 154 V — the reduction was made precisely to close that spread.)
- **TF1 thermal model (assumed values):** R_fast power heats a 3 J/K heat capacity that leaks to 25 °C ambient through 25 K/W; TF1 (SEFUSE SF129E) opens permanently at 133 °C. These thermal constants are estimates for an Ohmite 27J (7 W) body with the TCO clamped on — confirm on the bench (48 V PSU on the probes should open TF1 within roughly 5–20 s; a 47 mF/60 V dump must not).
- **Corners:** G3/G4 use `discharger_dc_corner.cir.tmpl` with per-scenario `QMODEL`/`TEMP` substitutions. Scenarios can pass extra template substitutions through a `"subs"` dict; the transient template takes `DUT` and `IC` overrides (defaults in `run_sim.py`).
- **Error handling:** `run_sim.py` fails a scenario if ngspice exits non-zero *or* prints `fatal`/`error` anywhere in its output.
- **DVM power:** not modeled — the module is powered by an internal 9 V battery (its measured 12–15 mA draw exceeded what the former parasitic dropper could supply), so it presents no load to the HV circuit. Only its 600 kΩ signal divider remains in the netlists.
