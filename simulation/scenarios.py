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


def _assert_tf1_intact(df, label):
    """TF1 (thermal cutoff on R_fast) must not trip on a normal discharge."""
    t_max = float(np.max(_col(df, "V(n_temp)")))
    tripped = float(np.max(_col(df, "V(n_tf_latch)"))) > 0.5
    return (not tripped and t_max < 118,
            f"{label}: TF1 intact, peak R_fast temp = {t_max:.0f} °C  (expected < Th 118 °C)")


def _q2_on_boundary(df):
    """Highest HVp at which Q2 conducts > 100 mA (DC sweep) — the effective
    fast-dump switch point, which sets the peak fast-path current."""
    hvp = _col(df, "V(HVp)")
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    on = hvp[i_fast > 0.1]
    return float(on.max()) if len(on) else None


# PM-128 divider: 5 × 100 kΩ over 2 × 100 Ω in parallel (50 Ω) → 600 V gives 60 mV, displayed "600"
DVM_RATIO = 50 / (500e3 + 50)


# ── Scenario definitions ───────────────────────────────────────────────────────

def _assertions_A(df):
    results = []
    # LED/DVM-divider/R5 branches add ~5 mA alongside the 25.5 mA slow path,
    # lowering effective R from 23.5k to ~20.5k. (Was ~16k before the Vcc
    # dropper branch was removed 2026-07-29 — discharge is ~25% slower now.)
    results.append(_assert_time_range(df, 63, 28, 48,  "A: t(V<63V)"))
    results.append(_assert_time_range(df, 10, 28, 52,  "A: t(V<10V)"))
    results.append(_assert_current_max(df, "I(V_islow)", 0.023, 0.028, "A: max I_slow"))

    # fast path kicks in below the ~63 V threshold — peak I_fast should exceed 1 A
    t = _t(df)
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    max_ifast = float(np.max(i_fast))
    results.append((max_ifast > 1.0,
                    f"A: max I_fast = {max_ifast:.2f} A  (expected > 1 A)"))

    # DVM ratio in range 30-600 V (relative error vs the ideal 10 000:1 divider)
    t = _t(df)
    hvp = _col(df, "V(HVp)")
    sig = _col(df, "V(n_sigout)")
    mask = (hvp >= 30) & (hvp <= 600)
    if np.any(mask):
        ratio = sig[mask] / hvp[mask]
        err = float(np.max(np.abs(ratio / DVM_RATIO - 1)))
        results.append((err < 0.01,
                        f"A: DVM ratio max error = {err*100:.2f}%  (tol 1%)"))

    # Reverse-polarity bridge (D1-D4) leaves a permanent residual across the
    # capacitor terminals (two diode drops) — well below the 10 V safe threshold.
    v_a = _col(df, "V(n_probe_a)")
    v_b = _col(df, "V(n_probe_b)")
    residual = float(v_a[-1] - v_b[-1])
    results.append((0.4 <= residual <= 2.5,
                    f"A: residual V(n_probe_a)-V(n_probe_b) at end = {residual:.3f} V  (expected 0.4-2.5 V)"))
    results.append(_assert_tf1_intact(df, "A"))
    return results


def _assertions_B(df):
    # DVM Vcc assertions removed 2026-07-29: the module (measured 12-15 mA)
    # is battery-powered now, so there is no Vcc rail in the HV circuit.
    results = []
    results.append(_assert_time_range(df, 63, 5, 20, "B: t(V<63V)"))
    results.append(_assert_time_range(df, 10, 5, 22, "B: t(V<10V)"))
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
    return results


def _assertions_F(df):
    results = []
    # At t=1s (quasi-steady with 100 mF cap ≈ rail stays at 600V)
    results.append(_assert_value_at_time(df, "I(V_islow)", 1.0,
                                          0.0242, 0.0268, "F: I_slow @1s"))
    results.append(_assert_value_at_time(df, "V(n_sigout)", 1.0,
                                          0.0590, 0.0610, "F: V(n_sigout) @1s (PM-128 '590'-'610')"))
    results.append(_assert_value_at_time(df, "V(n_gate)", 1.0,
                                          0, 1.0, "F: V(n_gate) @1s (Q2 off)"))
    return results


def _assertions_G(df):
    """DC sweep: gate should flip from ~12 V to <1 V at ~63 V.
    R3 = 10 kΩ (was 100 kΩ) stiffens the base drive so the threshold is
    nearly hFE-independent: 63 V at BF=150, 68 V at BF=40 (see G2)."""
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
        ok = 58 <= crossing <= 70
        results.append((ok,
                        f"G: gate threshold = {crossing:.1f} V  (expected 58-70 V)"))
    else:
        results.append((False, "G: no gate crossing found between 58-70 V"))
    return results


# Scenario H (DVM dropper vs LED-display module load) was removed 2026-07-29:
# the real module measured 12-15 mA, confirming the limitation it documented,
# and the parasitic Vcc dropper was replaced by a 9 V battery.


def _assertions_G2(df):
    """DC sweep, worst-case low-hFE Q1 (BF=40). With R3 = 100 kΩ this corner
    shifted the flip point to 154 V (measured); reducing R3 to 10 kΩ stiffens
    the base drive and pulls it back to ~68 V — only ~5 V above the BF=150
    nominal, keeping worst-case peak I_fast ≈ 1.3 A (< 2 A PCB limit)."""
    results = []
    hvp = _col(df, "V(HVp)")
    gate = _col(df, "V(n_gate)")
    lo_mask = hvp < 30
    if np.any(lo_mask):
        mean_gate_lo = float(np.mean(gate[lo_mask]))
        results.append((mean_gate_lo > 8,
                        f"G2: V(n_gate) at HVp<30V = {mean_gate_lo:.2f} V  (expected >8 V)"))
    # Sampled well past the crossing so the mean isn't skewed by the
    # transition region itself.
    hi_mask = hvp > 120
    if np.any(hi_mask):
        mean_gate_hi = float(np.mean(gate[hi_mask]))
        results.append((mean_gate_hi < 1,
                        f"G2: V(n_gate) at HVp>120V = {mean_gate_hi:.2f} V  (expected <1 V)"))
    crossing = None
    for i in range(1, len(gate)):
        if gate[i - 1] > 6 and gate[i] <= 6:
            crossing = float(hvp[i])
            break
    if crossing is not None:
        ok = 62 <= crossing <= 75
        results.append((ok,
                        f"G2: gate threshold (low-hFE) = {crossing:.1f} V  (expected 62-75 V)"))
    else:
        results.append((False, "G2: no gate crossing found in sweep range"))
    return results


def _assertions_G3(df):
    """Cold, datasheet-minimum hFE (BF=25, 0 °C): highest switch point.
    Peak fast-path current ≈ V_switch / 51 Ω must stay below the 2 A PCB limit."""
    v_on = _q2_on_boundary(df)
    if v_on is None:
        return [(False, "G3: Q2 never conducts in sweep")]
    i_pk = v_on / 51
    return [(70 <= v_on <= 85,
             f"G3: Q2 on below {v_on:.1f} V  (expected 70-85 V)"),
            (i_pk < 2.0,
             f"G3: worst-case peak I_fast ≈ {i_pk:.2f} A  (expected < 2 A)")]


def _assertions_G4(df):
    """Hot, high hFE (BF=300, 60 °C): lowest switch point (longest slow phase)."""
    v_on = _q2_on_boundary(df)
    if v_on is None:
        return [(False, "G4: Q2 never conducts in sweep")]
    return [(50 <= v_on <= 60,
             f"G4: Q2 on below {v_on:.1f} V  (expected 50-60 V)")]


def _assertions_H(df):
    """PM-128 divider: reading (= V(n_sigout) × 10 000, decimal point off)
    must track V_cap from 10 V to 600 V; with R_sigb open, D_clamp must keep
    the meter input below 0.8 V instead of ~600 V."""
    hvp = _col(df, "V(HVp)")
    reading = _col(df, "V(n_sigout)") * 1e4
    fault = _col(df, "V(n_sigout_f)")
    i600 = int(np.argmin(np.abs(hvp - 600)))
    i10 = int(np.argmin(np.abs(hvp - 10)))
    return [(595 <= reading[i600] <= 605,
             f"H: PM-128 reads {reading[i600]:.1f} at 600 V  (expected 595-605 before R4 trim)"),
            (9.9 <= reading[i10] <= 10.1,
             f"H: PM-128 reads {reading[i10]:.2f} at 10 V  (expected 9.9-10.1 — clamp leakage negligible)"),
            (float(fault.max()) < 0.8,
             f"H: divider bottom open → meter input max {fault.max():.3f} V  (expected < 0.8 V, display overrange)")]


def _assertions_I(df):
    """Reverse polarity: same discharge as A, opposite-sign residual,
    DVM still reads positive (the bridge rectifies)."""
    results = []
    results.append(_assert_time_range(df, 10, 28, 52, "I: t(V<10V)"))
    v_a = _col(df, "V(n_probe_a)")
    v_b = _col(df, "V(n_probe_b)")
    residual = float(v_a[-1] - v_b[-1])
    results.append((-2.5 <= residual <= -0.4,
                    f"I: residual V(n_probe_a)-V(n_probe_b) at end = {residual:.3f} V  (expected -2.5 to -0.4 V)"))
    sig0 = float(_col(df, "V(n_sigout)")[1]) * 1e4
    results.append((590 <= sig0 <= 605,
                    f"I: PM-128 reading at start = {sig0:.0f}  (expected 590-605, positive)"))
    results.append(_assert_tf1_intact(df, "I"))
    return results


def _assertions_J(df):
    """Hot plug onto a charged 600 V cap (1 µH leads, contact at 10 µs):
    Q2 must stay off — C_byp2 holds the gate while Q1 turns on."""
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    gate = _col(df, "V(n_gate)")
    hvp = _col(df, "V(HVp)")
    return [(float(hvp.max()) > 590,
             f"J: HVp reached {hvp.max():.0f} V  (contact made)"),
            (float(i_fast.max()) < 0.01,
             f"J: max I_fast = {i_fast.max()*1e3:.3f} mA  (expected < 10 mA)"),
            (float(gate.max()) < 1.0,
             f"J: max V(n_gate) = {gate.max():.3f} V  (expected < 1 V)")]


def _assertions_K(df):
    """Big low-voltage electrolytic (60 V / 47 mF ≈ 85 J, just below the
    switch point): the whole charge is fast-dumped into R_fast — TF1 must
    not nuisance-trip."""
    return [_assert_time_range(df, 10, 0, 60, "K: t(V<10V)"),
            _assert_tf1_intact(df, "K")]


def _assertions_L(df):
    """Probes on a live 48 V supply: Q2 stays on, R_fast would dissipate
    ~41 W continuously and F1 (2 A) never blows — TF1 must open."""
    t = _t(df)
    latch = _col(df, "V(n_tf_latch)")
    i_fast = np.abs(_col(df, "I(V_ifast)"))
    tripped = np.where(latch > 0.5)[0]
    results = [(float(i_fast.max()) < 2.0,
                f"L: max I_fast = {i_fast.max():.2f} A  (< 2 A: F1 alone would NOT protect R_fast)")]
    if not len(tripped):
        results.append((False, "L: TF1 never tripped"))
        return results
    t_trip = float(t[tripped[0]])
    results.append((t_trip < 30, f"L: TF1 opens at t = {t_trip:.1f} s  (expected < 30 s)"))
    results.append((float(i_fast[-1]) < 1e-3,
                    f"L: I_fast after trip = {i_fast[-1]*1e3:.3f} mA  (expected < 1 mA)"))
    return results


_TRAN_COLS = [
    "V(HVp)", "V(n_gate)", "V(n_gate_top)", "V(n_sigout)",
    "V(n_led_a)", "V(n_probe_a)", "V(n_probe_b)",
    "I(V_islow)", "I(V_ifast)", "I(V_iled)", "I(V_isig)",
    "V(n_temp)", "V(n_tf_latch)",
]

_CORNER_COLS = ["V(HVp)", "V(n_gate)", "V(n_gate_top)", "I(V_ifast)"]

_DC_COLS = [
    "V(HVp)", "V(n_gate)", "V(n_gate_top)", "V(n_sigout)", "V(n_led_a)",
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
    {
        "name":     "G2_threshold_lowbeta",
        "template": "discharger_dc_lowbeta.cir.tmpl",
        "v0":       None,
        "cdut":     None,
        "tstep":    None,
        "tstop":    None,
        "columns":  _DC_COLS,
        "assertions": _assertions_G2,
    },
    {
        "name":     "G3_threshold_cold_lowhfe",
        "template": "discharger_dc_corner.cir.tmpl",
        "v0":       None,
        "cdut":     None,
        "tstep":    None,
        "tstop":    None,
        "subs":     {"QMODEL": "QMPSA42_BF25", "TEMP": 0},
        "columns":  _CORNER_COLS,
        "assertions": _assertions_G3,
    },
    {
        "name":     "G4_threshold_hot_highhfe",
        "template": "discharger_dc_corner.cir.tmpl",
        "v0":       None,
        "cdut":     None,
        "tstep":    None,
        "tstop":    None,
        "subs":     {"QMODEL": "QMPSA42_BF300", "TEMP": 60},
        "columns":  _CORNER_COLS,
        "assertions": _assertions_G4,
    },
    {
        "name":     "H_dvm_divider_clamp",
        "template": "discharger_dc_dvm.cir.tmpl",
        "v0":       None,
        "cdut":     None,
        "tstep":    None,
        "tstop":    None,
        "columns":  ["V(HVp)", "V(n_sigout)", "V(n_sigout_f)"],
        "assertions": _assertions_H,
    },
    {
        "name":     "I_reverse_600V_1mF",
        "template": "discharger.cir.tmpl",
        "v0":       -600,
        "cdut":     1e-3,
        "tstep":    "10m",
        "tstop":    "120",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_I,
    },
    {
        "name":     "J_hotplug_600V",
        "template": "discharger.cir.tmpl",
        "v0":       600,
        "cdut":     1e-3,
        "tstep":    "100n",
        "tstop":    "5m",
        "subs": {
            "DUT": ("C_dut n_cap n_probe_b {CDUT} IC={V0}\n"
                    "L_lead n_cap n_plug 1u\n"
                    "S_plug n_plug n_probe_a n_ctl 0 SWPLUG\n"
                    "V_ctl n_ctl 0 PWL(0 0 10u 0 11u 1)"),
            "IC":  ".ic V(n_cap)={V0}",
        },
        "columns":  _TRAN_COLS,
        "assertions": _assertions_J,
    },
    {
        "name":     "K_bigcap_60V_47mF",
        "template": "discharger.cir.tmpl",
        "v0":       60,
        "cdut":     47e-3,
        "tstep":    "5m",
        "tstop":    "30",
        "columns":  _TRAN_COLS,
        "assertions": _assertions_K,
    },
    {
        "name":     "L_live_supply_48V",
        "template": "discharger.cir.tmpl",
        "v0":       48,
        "cdut":     1e-3,          # unused: DUT is a voltage source
        "tstep":    "10m",
        "tstop":    "60",
        "subs": {
            "DUT": ("V_live n_live n_probe_b {V0}\n"
                    "R_live n_live n_probe_a 0.5"),
            "IC":  "* live supply: no DUT initial condition",
        },
        "columns":  _TRAN_COLS,
        "assertions": _assertions_L,
    },
]
