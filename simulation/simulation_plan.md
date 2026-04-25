# Simulation Plan — 600 V Capacitor Discharger

## Context

The schematic in `implementation_claude.md` and `blocks/full_schematic.svg` describes an adaptive 600 V capacitor discharger with five interacting analog blocks (slow R-string, MOSFET fast path with NPN threshold detector, LED danger indicator, 6:1 DVM signal divider, parasitic 15 V DVM Vcc dropper). Before committing to PCB, we want a transient simulation that proves every operating regime works: slow-only above 71 V, fast-path takeover below 71 V, LED on/off at the ~10 V cutoff, DVM signal tracking 1/6 of V_cap, and DVM Vcc losing regulation below V_cap ~195 V (Zener cutout) and DVM going dark below V_cap ~27 V. The simulation must also let us read instantaneous current through every branch so we can verify resistor stress numbers in `bom.py` and the timing claims in `implementation_claude.md` (e.g. 50 s for 1 mF / 600 V).

The project has **no existing SPICE infrastructure** (verified — no `.cir`/`.sp`/`.asc`/PySpice). All deliverables are new.

## Tooling decision

- **Engine: ngspice** — already shipped with KiCad 10 (as `ngspice.dll`) and also available standalone. Two ways to run; pick whichever is more convenient:
  - **(A) Standalone ngspice CLI (preferred for automated batch runs).** Install with `winget install ngspice` or `scoop install ngspice`, then `ngspice -b sim.cir`. KiCad's bundled DLL is **not** a standalone executable on Windows — there is no `ngspice.exe` inside `C:\Program Files\KiCad\10.0\bin\`, so KiCad cannot drive headless batch runs.
  - **(B) KiCad 10 Simulator GUI** (interactive, no extra install). See "Running in KiCad" below.
- Output: `wrdata` to dump CSV; post-process in Python with `numpy` + `matplotlib`. PySpice is **not** used (extra dependency for no gain since ngspice CLI suffices).
- **Models** ship in-tree as `simulation/models.lib`:
  - `1N4007`: `.model D BV=1000 IS=1e-9 N=2`.
  - `2N3904`: standard Gummel-Poon `.model` (well-known parameter set).
  - `STF7NM80`: vendor SPICE model from ST (download `STF7NM80.lib`); fallback = generic 800 V N-MOSFET subckt with `Vto=4 Kp=2 Rds=1.7`.
  - Zeners (BZX85C12 12 V, BZX55C8V2 8.2 V, 1N4744A 15 V): `.model DZxx D BV=Vz IBV=5mA N=1.5`.
  - LED: `.model DLED D IS=1e-20 N=2 Vj=2.0` to give Vf ≈ 2 V at 2 mA.
  - 10 µF electrolytic: ideal `C` (ESR irrelevant at these frequencies).

## Architecture

```
simulation/
  simulation_plan.md      # this file
  models.lib              # all .model / .subckt definitions
  discharger.cir.tmpl     # parameterised netlist with {{V0}} {{CDUT}} placeholders
  discharger_dc.cir.tmpl  # DC sweep variant for scenario G
  run_sim.py              # renders template, runs ngspice, parses .csv, plots, asserts
  scenarios.py            # list of (name, V0, Cdut, expected) tuples
  results/<scenario>/
      sim.cir             # rendered netlist actually fed to ngspice
      out.csv             # time + node voltages + branch currents
      plot.png            # multi-panel plot
      summary.txt         # PASS/FAIL line per assertion + key timestamps
  README.md               # how to run + how to read results
```

## Netlist structure (`discharger.cir.tmpl`)

The reverse-polarity bridge is a no-op for simulation purposes (DUT is connected straight; bridge polarity tested only in scenario F). All measurement points use **0 V voltage sources as ammeters** so currents are exact and easy to extract.

```
* 600V Capacitor Discharger — transient
.include models.lib
.param V0={{V0}} CDUT={{CDUT}}

* DUT capacitor with initial condition
C_dut HVp 0 {CDUT} IC={V0}

* --- Slow path (5 × 4.7 k) ---
V_islow HVp n_slow1 0           ; ammeter: I(V_islow) = slow current
R_slow1 n_slow1 n_slow2 4.7k
R_slow2 n_slow2 n_slow3 4.7k
R_slow3 n_slow3 n_slow4 4.7k
R_slow4 n_slow4 n_slow5 4.7k
R_slow5 n_slow5 0       4.7k

* --- Fast path (R_fast → Q2 drain → source → GND) ---
V_ifast HVp n_rfast 0
R_fast  n_rfast n_drain 50
M_Q2    n_drain n_gate 0 0 STF7NM80
* gate drive: pull-up R5 from HVp to gate, clamped by D9 to 12 V; Q1 collector pulls gate low
R5      HVp n_gate_top 470k
D_D9    0   n_gate_top DZ12               ; clamps n_gate_top at 12 V (cathode at top, BV=12)
R4      n_gate_top n_gate 100
* Q1 NPN: base from R1/R2 divider via R3, collector to n_gate_top, emitter to GND
R1      HVp n_base_top 1Meg
R2      n_base_top 0   10k
R3      n_base_top n_q1b 100k
Q1      n_gate_top n_q1b 0 Q2N3904

* --- LED danger indicator ---
V_iled  HVp n_led1 0
R_LED1  n_led1 n_led2 100k
R_LED2  n_led2 n_led3 100k
R_LED3  n_led3 n_dled 100k
D_DLED  n_dled n_led_a DZ8V2              ; 8.2 V Zener, reversed in chain
D_LED1  n_led_a 0      DLED               ; red LED, Vf ≈ 2 V

* --- DVM signal divider 6:1 ---
V_isig  HVp n_sig1 0
R_sig1  n_sig1 n_sig2 100k
R_sig2  n_sig2 n_sig3 100k
R_sig3  n_sig3 n_sig4 100k
R_sig4  n_sig4 n_sig5 100k
R_sig5  n_sig5 n_sigout 100k
R_sigb  n_sigout 0     100k                ; node n_sigout is the DVM signal probe

* --- DVM Vcc dropper + 15 V Zener + smoothing cap ---
V_idrop HVp n_drop1 0
R_drop1 n_drop1 n_drop2 15k
R_drop2 n_drop2 n_drop3 15k
R_drop3 n_drop3 n_drop4 15k
R_drop4 n_drop4 n_vcc   15k
D_DVcc  0       n_vcc   DZ15
C_Vcc   n_vcc 0 10u
* Optional resistive load to model DVM current draw (≈3 mA typical)
R_dvm_load n_vcc 0 5k

.ic V(HVp)={V0} V(n_vcc)=0

.tran 10m 120 uic                          ; 0–120 s, 10 ms step
.save V(HVp) V(n_gate) V(n_gate_top) V(n_sigout) V(n_vcc) V(n_led_a)
.save I(V_islow) I(V_ifast) I(V_iled) I(V_isig) I(V_idrop)

.control
run
wrdata results/{{NAME}}/out.csv
+   V(HVp) V(n_gate) V(n_gate_top) V(n_sigout) V(n_vcc) V(n_led_a)
+   I(V_islow) I(V_ifast) I(V_iled) I(V_isig) I(V_idrop)
quit
.endc
.end
```

## Scenarios (`scenarios.py`)

| Name | V0 | C_dut | Purpose | Expected (assertions) |
|---|---|---|---|---|
| `A_full_600V_1mF` | 600 V | 1 mF | full sweep, all regimes | t(V<71V) ≈ 31 s (not 50 s — parallel branches add ~15 mA load, effective R ~15 kΩ not 23.5 kΩ); t(V<10V) < 42 s; LED off ≤ ~10.2 V; max I_slow ≈ 25.5 mA; max I_fast > 1 A; V(n_sigout)/V(HVp) ≈ 1/6 within 1 % from 600 V down to 30 V |
| `B_mid_300V_470uF` | 300 V | 470 µF | typical hobby cap | LED on until V_cap ~10 V; t(V<71V) ≈ 10 s; V(n_vcc) ≥ 5 V while V(HVp) > 30 V (Zener regulates at 15 V above ~195 V; below that Vcc tracks V_cap/13; DVM goes dark at V_cap ~27 V by design) |
| `C_mid_100V_100uF` | 100 V | 100 µF | brief slow segment then fast | slow segment < 1 s; fast path turns on near t≈0.7 s; total to 10 V < 2 s |
| `D_low_50V_100uF` | 50 V | 100 µF | fast-path-only from t=0 | I_fast > 0 at t=0+; gate near 12 V; total to 10 V < 1 s |
| `E_below_LED_8V_100uF` | 8 V | 100 µF | LED stays OFF | I(V_iled) < 1 µA throughout; V(n_vcc) < 5 V (DVM dark) |
| `F_steady_state_600V` | 600 V | 100 mF (≈ rail) | quasi-steady probes | at t=1 s: I_slow=25.5 mA ±5%; I_drop=9.75 mA ±5%; V(n_vcc)=15 V ±0.5 V; V(n_sigout)=100 V ±2 V; V(n_gate)<1 V (Q2 off) |
| `G_threshold_sweep` | (DC sweep, not transient) | n/a | confirm 71 V switch point | DC sweep V(HVp) 0→200 V: V(n_gate) flips from ~12 V to <1 V at V(HVp) = 71 V ±3 V |

Scenario G uses a separate `.dc` analysis netlist (`discharger_dc.cir.tmpl`) — same topology but `.tran` swapped for `.dc V_HVp 0 200 0.5`, and `C_dut` replaced by a stimulus voltage source `V_HVp HVp 0 0`.

## Meter / probe placement (rationale)

| Quantity | How read | Conversion |
|---|---|---|
| V_cap (HV+) | `V(HVp)` | direct volts |
| Slow path I | `I(V_islow)` | direct A; P_total = V·I, per-resistor = I² × 4.7 k |
| Fast path I (through MOSFET) | `I(V_ifast)` | direct A; instantaneous P_R_fast = I² × 50 |
| LED chain I | `I(V_iled)` | direct; LED on iff > 50 µA |
| DVM signal divider I | `I(V_isig)` | direct; divider loading negligible vs DVM input |
| DVM Vcc dropper I | `I(V_idrop)` | direct; per-resistor P = I² × 15 k |
| Q2 gate state | `V(n_gate)` | <1 V = off, ~12 V = on |
| DVM signal output | `V(n_sigout)` | should equal V(HVp)/6 |
| DVM Vcc rail | `V(n_vcc)` | 15 V Zener-regulated while V_cap > ~195 V; tracks V_cap/13 below that; drops below 5 V (DVM dark) at V_cap ~27 V |
| LED anode (post-Zener) | `V(n_led_a)` | ≈ V_f ≈ 2 V when on, 0 when off |

Placing each ammeter as a **0 V source at the head of the branch** (between HVp and the first element of that branch) means the per-branch current is read directly with no extra arithmetic — Sonnet doesn't need to subtract anything.

## Running the simulation

### Option A — Standalone ngspice CLI (recommended for batch / automation)

ngspice 46 is already installed at `E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice.exe`.

Verify it works:
```
"E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice.exe" -v
```

`run_sim.py` must invoke it with the full path (it is not on the system PATH):
```python
NGSPICE = r"E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice.exe"
```

1. Run all scenarios:
   ```
   cd simulation
   python run_sim.py --all
   ```
   `run_sim.py` renders each `*.cir.tmpl` to `results/<name>/sim.cir`, then invokes `ngspice -b results/<name>/sim.cir`, parses `out.csv`, runs assertions, writes `summary.txt` and `plot.png`.
3. Run a single scenario:
   ```
   python run_sim.py A_full_600V_1mF
   ```
4. Inspect: open `results/<name>/plot.png` and `summary.txt`.

### Option B — KiCad 10 built-in Simulator (interactive GUI)

KiCad 10 ships ngspice as a DLL inside `C:\Program Files\KiCad\10.0\bin\ngspice.dll` and exposes it via the schematic editor's Simulator tool. Use this when you want to eyeball waveforms without leaving KiCad, or if you don't want to install standalone ngspice.

Two ways to load our netlist into KiCad's simulator:

**B1. Load a hand-written .cir directly (fastest)**

1. Open KiCad → **Tools → Simulator** (or open *any* schematic and use **Inspect → Simulator** — KiCad needs a schematic context window even to run a raw netlist).
2. In the Simulator window: **File → Open Workbook…** is for `.wbk` only. Instead use **Simulation → Settings…** *or* edit the netlist directly: click the **"Custom"** tab in Simulation Command, paste the contents of `simulation/results/<name>/sim.cir` (already rendered by `run_sim.py`), and uncheck "Generate netlist from schematic" so the simulator uses your custom netlist verbatim.
   - Alternative: launch KiCad's bundled ngspice in interactive mode from a terminal — it isn't on PATH, but you can call it via Python's `ctypes` against the DLL. Not worth it; just install standalone ngspice (Option A) if you want CLI.
3. Click **Run**. Add signals to the plot via **Add Signals…** — enter `V(HVp)`, `V(n_gate)`, `V(n_sigout)`, `V(n_vcc)`, `I(v_islow)`, `I(v_ifast)`, etc. (KiCad lower-cases vsource names).
4. Cursors: right-click on a trace → **Add Cursor** to read out (t, V) pairs. Use this to measure t(V_HVp = 71 V) and t(V_HVp = 10 V) for the timing assertions.
5. Export: **File → Export Plot as CSV** to compare with `out.csv` from Option A.

**B2. Build a KiCad schematic and let KiCad netlist it**

Only worth doing if you also want a KiCad-native schematic deliverable. Steps: place SPICE-modeled symbols (the `pspice` library has `R`, `C`, `D`, `Q_NPN`, `MOS_N` with editable model fields), wire them to match `discharger.cir.tmpl`, set initial condition on `C_dut` via `Symbol Properties → Simulation Model → Initial Condition (IC)`, and add a `.tran 10m 120 uic` directive via **Simulation → Settings**. Then **Run**. This duplicates information already in the `.cir` template — skip unless we decide to maintain the schematic in KiCad as a second source of truth.

**Common pitfalls in KiCad's simulator:**
- KiCad's simulator quietly **lower-cases all node and reference names**. `I(V_islow)` becomes `i(v_islow)`. Match case in plot expressions.
- `wrdata` works inside `.control` blocks but writes relative to KiCad's working directory (usually the project folder), not the netlist directory. Use absolute paths if you need scripted output from inside KiCad.
- KiCad 10 simulator does **not** support `.include` with relative paths the way the CLI does — if `models.lib` isn't found, copy its contents inline or use an absolute path.
- For long transients (scenario A is 120 s simulated time with 10 ms step = 12 000 points), KiCad's plotter is fine but the GUI may stutter on pan/zoom; export CSV and plot in Python if it gets sluggish.

### Sanity check (either option)

Smoke-test the Zener and MOSFET models in isolation **before** running the full discharger:

```
* zener_test.cir
.include models.lib
V1 1 0 PWL(0 0 1 20)
R1 1 2 1k
D1 0 2 DZ12
.tran 1m 1
.control
run
print V(2)
.endc
.end
```

Should clamp `V(2)` at ≈ 12 V once V1 > 12 V. Repeat for `DZ8V2`, `DZ15`, `DLED`. Five-line tests per device take <1 s and catch model errors before they confuse the main simulation.

## Critical files to be created

- `simulation/models.lib` — all device models in one file
- `simulation/discharger.cir.tmpl` — main transient netlist (above)
- `simulation/discharger_dc.cir.tmpl` — DC sweep variant for scenario G
- `simulation/scenarios.py` — table above as Python data, plus per-scenario assertion lambdas
- `simulation/run_sim.py` — for each scenario: render template → write `.cir` to `results/<name>/sim.cir` → `subprocess.run(["ngspice", "-b", "sim.cir"])` → load `out.csv` with `numpy.loadtxt` → compute derived quantities → run assertions → write `summary.txt` → produce `plot.png` (3 panels: V_cap & V_gate & V_sigout vs t; I_slow & I_fast vs t; I_led & I_drop & V_vcc vs t) → print PASS/FAIL line.
- `simulation/README.md` — short version of the "Running the simulation" section above, plus how to add a new scenario.

## Reuse from existing project

- `bom.py` — Sonnet should `from bom import BOM` and pull resistor / Zener / cap values from there rather than hard-coding them, so a BOM change auto-propagates to the netlist (mirror the same single-source-of-truth pattern as `gen_full_schematic.py`).
- Layout convention (HV section / LV section, grouped branches) from `blocks/gen_full_schematic.py` — keep the same grouping in the netlist comments so a reader can map netlist ↔ schematic.

## Execution order for Sonnet

1. Install ngspice (Option A); verify with `ngspice -v`. *Or* confirm KiCad 10 is installed if going Option B.
2. Create `simulation/models.lib` with the five device models above. Smoke-test each with the 5-line standalone netlist shown above before integrating.
3. Write `discharger.cir.tmpl` and run scenario **F (steady state, 100 mF rail) first** — easiest assertions, validates the topology before any timing math is involved.
4. Run scenario **G (DC threshold sweep)** — validates the Q1/Q2 gate logic in isolation.
5. Run **A → E** in order; each is a strictly easier transient than A.
6. Generate plots; eyeball them against the expected curves in `implementation_claude.md` §2 (timing) and §5 (LED cutoff).
7. Write `summary.txt` per scenario, plus a top-level `simulation/results/RESULTS.md` aggregating all PASS/FAIL.

## Verification

End-to-end test = `python simulation/run_sim.py --all` exits 0 and every scenario shows PASS in `RESULTS.md`. Spot-check expected against `implementation_claude.md`:

- Scenario A: time-to-71 V is **~31 s** (sim confirmed), not the 50 s single-path estimate. The 50 s figure assumes only the 23.5 kΩ slow path; in practice the LED chain, DVM signal divider, DVM Vcc dropper, and base divider add ~15 mA of parallel load, reducing effective R to ~15 kΩ and τ to ~15 s.
- Scenario F: I_slow = 600 V / 23.5 kΩ = **25.5 mA**; I_drop = (600−15)/60 kΩ = **9.75 mA**; per-resistor stresses match `bom.py` notes within 5 %.
- Scenario G: threshold at V_th = 0.7·(1 M+10 k)/10 k = **70.7 V** ±3 V tolerance for V_BE variation.

If any of those three numerical anchors disagrees with sim by > 10 %, stop and re-check models before running the rest.
