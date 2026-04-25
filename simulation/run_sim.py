"""
run_sim.py — render templates, invoke ngspice, parse CSV, assert, plot.

Usage:
  python run_sim.py --all                   # run every scenario
  python run_sim.py A_full_600V_1mF         # run one scenario by name
  python run_sim.py --list                  # print available scenario names
"""

import argparse
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from scenarios import SCENARIOS

# ── Config ────────────────────────────────────────────────────────────────────
NGSPICE = r"E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice.exe"
SIM_DIR = Path(__file__).parent          # simulation/
RESULTS_DIR = SIM_DIR / "results"


# ── Template rendering ────────────────────────────────────────────────────────

def render_template(tmpl_path: Path, substitutions: dict) -> str:
    text = tmpl_path.read_text(encoding="utf-8")
    for key, value in substitutions.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    # Verify no placeholders remain
    remaining = re.findall(r"\{\{(\w+)\}\}", text)
    if remaining:
        raise ValueError(f"Unresolved placeholders in {tmpl_path.name}: {remaining}")
    return text


# ── ngspice invocation ────────────────────────────────────────────────────────

def run_ngspice(cir_path: Path) -> tuple[bool, str]:
    if not Path(NGSPICE).exists():
        return False, f"ngspice not found at {NGSPICE}"
    result = subprocess.run(
        [NGSPICE, "-b", str(cir_path)],
        capture_output=True, text=True, timeout=300,
        cwd=str(cir_path.parent),
    )
    combined = result.stdout + "\n" + result.stderr
    if result.returncode != 0:
        return False, f"ngspice exit {result.returncode}:\n{combined}"
    return True, combined


# ── CSV parsing ───────────────────────────────────────────────────────────────

def load_csv(csv_path: Path, col_names: list[str]) -> pd.DataFrame:
    """
    Parse ngspice wrdata output.

    wrdata writes no header; each row contains N pairs of (time, value),
    one pair per saved variable.  Layout:
        t0 V(HVp)_0  t0 V(n_gate)_0  ...
        t1 V(HVp)_1  t1 V(n_gate)_1  ...

    col_names must be the ordered list of variable names from the wrdata command
    (excluding the implicit time column).
    """
    raw = np.loadtxt(str(csv_path))
    if raw.ndim == 1:
        raw = raw.reshape(1, -1)

    n_vars = len(col_names)
    expected_cols = n_vars * 2
    if raw.shape[1] != expected_cols:
        raise ValueError(
            f"Expected {expected_cols} columns ({n_vars} vars × 2), "
            f"got {raw.shape[1]}"
        )

    # Column 0 of each pair is time (identical for all pairs); use the first.
    time_col = raw[:, 0]
    # Odd-indexed columns (1, 3, 5, …) are the variable values.
    value_cols = raw[:, 1::2]

    data = np.column_stack([time_col, value_cols])
    return pd.DataFrame(data, columns=["time"] + col_names)


# ── Plotting ──────────────────────────────────────────────────────────────────

def _col_fuzzy(df: pd.DataFrame, fragment: str):
    matches = [c for c in df.columns if fragment.lower() in c.lower()]
    if not matches:
        return None
    return df[matches[0]].values


def plot_transient(df: pd.DataFrame, scenario_name: str, out_path: Path):
    t = df.iloc[:, 0].values

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    fig.suptitle(f"Scenario: {scenario_name}", fontsize=12)

    # Panel 1: voltages
    ax = axes[0]
    for col, label, color in [
        ("V(HVp)",      "V_cap",     "tab:blue"),
        ("V(n_gate)",   "V_gate",    "tab:orange"),
        ("V(n_sigout)", "V_sigout",  "tab:green"),
        ("V(n_vcc)",    "V_vcc",     "tab:red"),
    ]:
        v = _col_fuzzy(df, col)
        if v is not None:
            ax.plot(t, v, label=label, color=color)
    ax.set_ylabel("Voltage (V)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # Panel 2: discharge currents
    ax = axes[1]
    for col, label, color in [
        ("I(V_islow)", "I_slow", "tab:blue"),
        ("I(V_ifast)", "I_fast", "tab:orange"),
    ]:
        v = _col_fuzzy(df, col)
        if v is not None:
            ax.plot(t, np.abs(v) * 1e3, label=label, color=color)
    ax.set_ylabel("Current (mA)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # Panel 3: LED / DVM currents + Vcc
    ax = axes[2]
    for col, label, scale, color in [
        ("I(V_iled)",  "I_LED (mA)",  1e3,  "tab:red"),
        ("I(V_idrop)", "I_drop (mA)", 1e3,  "tab:purple"),
        ("I(V_isig)",  "I_sig (mA)",  1e3,  "tab:brown"),
    ]:
        v = _col_fuzzy(df, col)
        if v is not None:
            ax.plot(t, np.abs(v) * scale, label=label, color=color)
    ax.set_ylabel("Current (mA)")
    ax.set_xlabel("Time (s)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=120)
    plt.close(fig)


def plot_dc_sweep(df: pd.DataFrame, scenario_name: str, out_path: Path):
    hvp = _col_fuzzy(df, "V(HVp)")
    if hvp is None:
        hvp = df.iloc[:, 0].values

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    fig.suptitle(f"Scenario: {scenario_name}", fontsize=12)

    ax = axes[0]
    for col, label, color in [
        ("V(n_gate)",     "V_gate",     "tab:orange"),
        ("V(n_gate_top)", "V_gate_top", "tab:blue"),
    ]:
        v = _col_fuzzy(df, col)
        if v is not None:
            ax.plot(hvp, v, label=label, color=color)
    ax.axvline(70.7, color="gray", linestyle="--", linewidth=0.8, label="71V threshold")
    ax.set_ylabel("Gate voltage (V)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    for col, label, color in [
        ("V(n_sigout)", "V_sigout", "tab:green"),
        ("V(n_vcc)",    "V_vcc",    "tab:red"),
    ]:
        v = _col_fuzzy(df, col)
        if v is not None:
            ax.plot(hvp, v, label=label, color=color)
    ax.set_ylabel("Voltage (V)")
    ax.set_xlabel("V_cap (V)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=120)
    plt.close(fig)


# ── Per-scenario runner ───────────────────────────────────────────────────────

def run_scenario(sc: dict) -> bool:
    name = sc["name"]
    results_path = RESULTS_DIR / name
    results_path.mkdir(parents=True, exist_ok=True)

    cir_path  = results_path / "sim.cir"
    csv_path  = results_path / "out.csv"
    plot_path = results_path / "plot.png"
    summ_path = results_path / "summary.txt"

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    # ── Render template ───────────────────────────────────────
    tmpl_path = SIM_DIR / sc["template"]
    is_dc = sc["template"].startswith("discharger_dc")

    # ngspice resolves paths relative to the netlist file; use absolute paths
    csv_abs     = str(csv_path).replace("\\", "/")
    models_abs  = str((SIM_DIR / "models.lib").resolve()).replace("\\", "/")

    if is_dc:
        subs = {
            "NAME":      name,
            "OUTCSV":    csv_abs,
            "MODELSLIB": models_abs,
        }
    else:
        subs = {
            "NAME":      name,
            "V0":        sc["v0"],
            "CDUT":      f"{sc['cdut']:.6e}",
            "TSTEP":     sc["tstep"],
            "TSTOP":     sc["tstop"],
            "OUTCSV":    csv_abs,
            "MODELSLIB": models_abs,
        }

    cir_text = render_template(tmpl_path, subs)
    cir_path.write_text(cir_text, encoding="utf-8")
    print(f"  Netlist:  {cir_path}")

    # ── Run ngspice ───────────────────────────────────────────
    print("  Running ngspice ...", end=" ", flush=True)
    ok, msg = run_ngspice(cir_path)
    if ok:
        print("done")
    else:
        print("FAILED")
        print(textwrap.indent(msg[:2000], "    "))
        summ_path.write_text(f"SCENARIO: {name}\nSTATUS: NGSPICE_FAILED\n\n{msg}\n")
        return False

    # ── Parse CSV ─────────────────────────────────────────────
    if not csv_path.exists():
        msg = f"  out.csv not created - ngspice may have written to a different path"
        print(msg)
        summ_path.write_text(f"SCENARIO: {name}\nSTATUS: CSV_MISSING\n\n{msg}\n")
        return False

    try:
        df = load_csv(csv_path, sc["columns"])
    except Exception as exc:
        print(f"  CSV parse error: {exc}")
        summ_path.write_text(f"SCENARIO: {name}\nSTATUS: CSV_PARSE_ERROR\n\n{exc}\n")
        return False

    print(f"  CSV rows: {len(df)}, columns: {list(df.columns)}")

    # ── Plot ──────────────────────────────────────────────────
    try:
        if is_dc:
            plot_dc_sweep(df, name, plot_path)
        else:
            plot_transient(df, name, plot_path)
        print(f"  Plot:     {plot_path}")
    except Exception as exc:
        print(f"  Plot error (non-fatal): {exc}")

    # ── Assertions ────────────────────────────────────────────
    assertion_results = sc["assertions"](df)
    all_pass = all(r[0] for r in assertion_results)

    summary_lines = [f"SCENARIO: {name}", f"STATUS: {'PASS' if all_pass else 'FAIL'}", ""]
    for passed, message in assertion_results:
        tag = "PASS" if passed else "FAIL"
        line = f"  [{tag}] {message}"
        summary_lines.append(line)
        print(line)

    summary_lines.append("")
    summ_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return all_pass


# ── Top-level results aggregator ──────────────────────────────────────────────

def write_results_md(pass_fail: dict[str, bool]):
    lines = ["# Simulation Results\n",
             "| Scenario | Result |",
             "|----------|--------|"]
    for name, passed in pass_fail.items():
        tag = "**PASS**" if passed else "**FAIL**"
        lines.append(f"| {name} | {tag} |")
    lines.append("")
    out = RESULTS_DIR / "RESULTS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nResults summary: {out}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run capacitor discharger simulations")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all",  action="store_true", help="Run all scenarios")
    group.add_argument("--list", action="store_true", help="List scenario names")
    group.add_argument("scenario", nargs="?", help="Run a single named scenario")
    args = parser.parse_args()

    scenario_map = {sc["name"]: sc for sc in SCENARIOS}

    if args.list:
        for name in scenario_map:
            print(name)
        return

    if args.all:
        targets = list(SCENARIOS)
    else:
        if args.scenario not in scenario_map:
            print(f"Unknown scenario '{args.scenario}'. Available:")
            for n in scenario_map:
                print(f"  {n}")
            sys.exit(1)
        targets = [scenario_map[args.scenario]]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    pass_fail: dict[str, bool] = {}
    for sc in targets:
        pass_fail[sc["name"]] = run_scenario(sc)

    write_results_md(pass_fail)

    total = len(pass_fail)
    passed = sum(1 for v in pass_fail.values() if v)
    print(f"\n{passed}/{total} scenarios PASSED")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
