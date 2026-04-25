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
| `G_threshold_sweep`    | DC sweep 0→200 V | — | Confirm 71 V switch point |

## Adding a scenario

1. Add an entry to `scenarios.py::SCENARIOS` with `name`, `template`, `v0`, `cdut`, `tstep`, `tstop`, and an `assertions` function.
2. The assertions function receives a `pandas.DataFrame` (columns = ngspice output names) and returns `list[(bool, str)]`.
3. Run `python run_sim.py <your_name>`.

## Key nodes

| Node | Meaning |
|------|---------|
| `V(HVp)` | Capacitor voltage |
| `V(n_gate)` | MOSFET gate (~12 V = on, <1 V = off) |
| `V(n_sigout)` | DVM signal output (should be V_cap/6) |
| `V(n_vcc)` | DVM Vcc rail (~15 V while V_cap > 20 V) |
| `I(V_islow)` | Slow path current |
| `I(V_ifast)` | Fast path (MOSFET) current |
| `I(V_iled)` | LED chain current |
| `I(V_idrop)` | DVM Vcc dropper current |
