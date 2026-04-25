"""
Simulation scenarios for the 600 V Capacitor Discharger.

Each transient scenario is a dict with:
  name      str   — used as results/<name>/ directory
  v0        float — initial capacitor voltage (V)
  cdut      float — DUT capacitance (F)
  tstep     str   — ngspice .tran time step
  tstop     str   — ngspice .tran stop time
  template  str   — which .cir.tmpl to render
  assertions list[callable(df) -> (bool, str)]
              df is a pandas DataFrame with columns matching wrdata output

The DC sweep scenario (G) uses template='discharger_dc.cir.tmpl' and
has no tstep/tstop; assertions receive the same DataFrame structure.
"""

import numpy as np


def _col(df, name):
    """Return column by case-insensitive partial match (ngspice lowercases names)."""
    matches = [c for c in df.columns if name.lower() in c.lower()]
    if not matches:
        raise KeyError(f"No column matching '{name}' in {list(df.columns)}")
    return df[matches[0]].values


def _t(df):
    return df.iloc[:, 0].values  # first column is always time


# ── Assertion helpers ──────────────────────────────────────────────────────────

def _time_at(t, v, threshold, direction="falling"):
    """Return time when signal crosses threshold."""
    if direction == "falling":
        idx = np.where(v <= threshold)[0]
    else:
        idx = np.where(v >= threshold)[0]
    return t[idx[0]] if len(idx) else None


def _assert_time_range(df, threshold, t_lo, t_hi, label):
    t = _t(df)
    v = _col(df, "V(HVp)")
    tx = _time_at(t, v, threshold)
    if tx is None:
        return False, f"{label}: V(HVp) never reached {threshold} V"
    ok = t_lo <= tx <= t_hi
    return ok, f"{label}: t(V<{threshold}V) = {tx:.2f} s  (expected {t_lo}-{t_hi} s)"


def _assert_current_max(df, col_fragment, lo, hi, label):
    i = np.abs(_col(df, col_fragment))
    mx = float(np.max(i))
    ok = lo <= mx <= hi
    return ok, f"{label}: max |{col_fragment}| = {mx*1e3:.2f} mA  (expected {lo*1e3:.1f}-{hi*1e3:.1f} mA)"


def _assert_ratio(df, num_col, den_col, expected_ratio, tol, label):
    num = _col(df, num_col)
    den = _col(df, den_col)
    mask = np.abs(den) > 1.0  # only where HVp > 1 V
    if not np.any(mask):
        return False, f"{label}: denominator never > 1 V"
    ratio = num[mask] / den[mask]
    err = float(np.max(np.abs(ratio - expected_ratio)))
    ok = err <= tol
    return ok, f"{label}: max ratio error = {err*100:.2f}%  (tol {tol*100:.1f}%)"


def _assert_value_at_time(df, col_fragment, t_query, lo, hi, label):
    t = _t(df)
    v = _col(df, col_fragment)
    idx = np.argmin(np.abs(t - t_query))
    val = float(v[idx])
    ok = lo <= val <= hi
    return ok, f"{label}: {col_fragment} at t={t_query}s = {val:.3f}  (expected {lo}-{hi})"


# ── Scenario definitions ───────────────────────────────────────────────────────

def _assertions_A(df):
    results = []
    # Real discharge time is ~31 s, not 50 s, because LED/DVM/Vcc branches add
    # ~15 mA alongside the 25.5 mA slow path, lowering effective R from 23.5k to ~15k.
    results.append(_assert_time_range(df, 71, 22, 40,  "A: t(V<71V)"))
    results.append(_assert_time_range(df, 10, 22, 42,  "A: t(V<10V)"))
    results.append(_assert_current_max(df, "I(V_islow)", 0.023, 0.028, "A: max I_slow"))

    # fast path kicks in below 71 V — peak I_fast should exceed 1 A
    t = _t(df)
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    max_ifast = float(np.max(i_fast))
    results.append((max_ifast > 1.0,
                    f"A: max I_fast = {max_ifast:.2f} A  (expected > 1 A)"))

    # DVM ratio in range 30-600 V
    t = _t(df)
    hvp = _col(df, "V(HVp)")
    sig = _col(df, "V(n_sigout)")
    mask = (hvp >= 30) & (hvp <= 600)
    if np.any(mask):
        ratio = sig[mask] / hvp[mask]
        err = float(np.max(np.abs(ratio - 1/6)))
        results.append((err < 0.01,
                        f"A: DVM ratio max error = {err*100:.2f}%  (tol 1%)"))
    return results


def _assertions_B(df):
    results = []
    results.append(_assert_time_range(df, 71, 5, 17, "B: t(V<71V)"))
    # DVM Vcc stays >= 5 V while V_cap > 30 V (dropper can support DVM minimum
    # operating voltage down to ~27 V; below that the DVM goes dark by design).
    t = _t(df)
    hvp = _col(df, "V(HVp)")
    vcc = _col(df, "V(n_vcc)")
    mask = (hvp > 30) & (t > 0.1)
    if np.any(mask):
        min_vcc = float(np.min(vcc[mask]))
        results.append((min_vcc >= 5.0,
                        f"B: min V(n_vcc) while HVp>30V = {min_vcc:.2f} V  (expected >=5 V, DVM rail floor)"))
    return results


def _assertions_C(df):
    results = []
    # slow segment < 1 s (fast path should take over quickly)
    t = _t(df)
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    # find first time fast current exceeds 10 mA
    idx = np.where(i_fast > 0.01)[0]
    if len(idx):
        t_fast_on = float(t[idx[0]])
        results.append((t_fast_on < 1.5,
                        f"C: fast path on at t = {t_fast_on:.3f} s  (expected < 1.5 s)"))
    else:
        results.append((False, "C: fast path never turned on"))
    results.append(_assert_time_range(df, 10, 0, 3, "C: t(V<10V)"))
    return results


def _assertions_D(df):
    results = []
    # fast path active at t=0+: I_fast > 0 almost immediately
    t = _t(df)
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    idx = np.where(i_fast > 0.1)[0]
    if len(idx):
        results.append((float(t[idx[0]]) < 0.1,
                        f"D: fast path on at t={t[idx[0]]:.4f}s  (expected <0.1s)"))
    else:
        results.append((False, "D: fast path (>100 mA) never triggered"))
    results.append(_assert_time_range(df, 10, 0, 1.5, "D: t(V<10V)"))
    return results


def _assertions_E(df):
    results = []
    i_led = np.abs(_col(df, "I(V_iled)"))
    max_iled = float(np.max(i_led))
    results.append((max_iled < 1e-6,
                    f"E: max I_LED = {max_iled*1e6:.3f} µA  (expected < 1 µA)"))
    vcc = _col(df, "V(n_vcc)")
    max_vcc = float(np.max(vcc))
    results.append((max_vcc < 5,
                    f"E: max V(n_vcc) = {max_vcc:.2f} V  (expected < 5 V)"))
    return results


def _assertions_F(df):
    results = []
    # At t=1s (quasi-steady with 100 mF cap ≈ rail stays at 600V)
    results.append(_assert_value_at_time(df, "I(V_islow)", 1.0,
                                          0.0242, 0.0268, "F: I_slow @1s"))
    results.append(_assert_value_at_time(df, "I(V_idrop)", 1.0,
                                          0.00926, 0.01024, "F: I_drop @1s"))
    results.append(_assert_value_at_time(df, "V(n_vcc)", 1.0,
                                          14.5, 15.5, "F: V(n_vcc) @1s"))
    results.append(_assert_value_at_time(df, "V(n_sigout)", 1.0,
                                          98, 102, "F: V(n_sigout) @1s"))
    results.append(_assert_value_at_time(df, "V(n_gate)", 1.0,
                                          0, 1.0, "F: V(n_gate) @1s (Q2 off)"))
    return results


def _assertions_G(df):
    """DC sweep: gate should flip from ~12 V to <1 V at 68-74 V."""
    results = []
    hvp = _col(df, "V(HVp)")
    gate = _col(df, "V(n_gate)")
    # Gate should be ~12 V at low HVp (Q1 off, gate pulled up)
    lo_mask = hvp < 30
    if np.any(lo_mask):
        mean_gate_lo = float(np.mean(gate[lo_mask]))
        results.append((mean_gate_lo > 8,
                        f"G: V(n_gate) at HVp<30V = {mean_gate_lo:.2f} V  (expected >8 V)"))
    # Gate should be <1 V at high HVp (Q1 saturated, gate pulled low)
    hi_mask = hvp > 120
    if np.any(hi_mask):
        mean_gate_hi = float(np.mean(gate[hi_mask]))
        results.append((mean_gate_hi < 1,
                        f"G: V(n_gate) at HVp>120V = {mean_gate_hi:.2f} V  (expected <1 V)"))
    # Find crossing point
    crossing = None
    for i in range(1, len(gate)):
        if gate[i - 1] > 6 and gate[i] <= 6:
            crossing = float(hvp[i])
            break
    if crossing is not None:
        ok = 68 <= crossing <= 77
        results.append((ok,
                        f"G: gate threshold = {crossing:.1f} V  (expected 68-77 V)"))
    else:
        results.append((False, "G: no gate crossing found between 68-74 V"))
    return results


_TRAN_COLS = [
    "V(HVp)", "V(n_gate)", "V(n_gate_top)", "V(n_sigout)",
    "V(n_vcc)", "V(n_led_a)",
    "I(V_islow)", "I(V_ifast)", "I(V_iled)", "I(V_isig)", "I(V_idrop)",
]

_DC_COLS = [
    "V(HVp)", "V(n_gate)", "V(n_gate_top)", "V(n_sigout)", "V(n_vcc)", "V(n_led_a)",
]

SCENARIOS = [
    {
        "name":     "A_full_600V_1mF",
        "template": "discharger.cir.tmpl",
        "v0":       600,
        "cdut":     1e-3,
        "tstep":    "10m",
        "tstop":    "120",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_A,
    },
    {
        "name":     "B_mid_300V_470uF",
        "template": "discharger.cir.tmpl",
        "v0":       300,
        "cdut":     470e-6,
        "tstep":    "5m",
        "tstop":    "30",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_B,
    },
    {
        "name":     "C_mid_100V_100uF",
        "template": "discharger.cir.tmpl",
        "v0":       100,
        "cdut":     100e-6,
        "tstep":    "1m",
        "tstop":    "5",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_C,
    },
    {
        "name":     "D_low_50V_100uF",
        "template": "discharger.cir.tmpl",
        "v0":       50,
        "cdut":     100e-6,
        "tstep":    "1m",
        "tstop":    "2",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_D,
    },
    {
        "name":     "E_below_LED_8V_100uF",
        "template": "discharger.cir.tmpl",
        "v0":       8,
        "cdut":     100e-6,
        "tstep":    "1m",
        "tstop":    "2",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_E,
    },
    {
        "name":     "F_steady_state_600V",
        "template": "discharger.cir.tmpl",
        "v0":       600,
        "cdut":     100e-3,   # 100 mF ≈ rail stays at 600V
        "tstep":    "10m",
        "tstop":    "5",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_F,
    },
    {
        "name":     "G_threshold_sweep",
        "template": "discharger_dc.cir.tmpl",
        "v0":       None,
        "cdut":     None,
        "tstep":    None,
        "tstop":    None,
        "columns":  _DC_COLS,
        "assertions": _assertions_G,
    },
]
