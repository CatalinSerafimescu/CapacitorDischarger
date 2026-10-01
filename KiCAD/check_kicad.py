"""Check CapacitorDischarger.kicad_sch: kicad-cli netlist must match the circuit that
simulation/discharger.cir.tmpl simulates (pin by pin), and ERC must have no errors.

    python check_kicad.py
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
SCH = os.path.join(HERE, "CapacitorDischarger.kicad_sch")

# Expected connectivity. Pin numbers: R/C/F 1-2; D/LED 1=K 2=A; Q1 1=E 2=B 3=C;
# Q2 1=G 2=D 3=S; PM-128 1=VIN 2=IN_GND 3=+9V 4=-9V; battery 1=+ 2=-.
# SPICE node in brackets.
EXPECTED = [
    # [n_probe_a]
    {"J1.1", "J3.1", "J3.2", "D1.2", "D4.1"},
    # [n_probe_b]
    {"J2.1", "J4.1", "J4.2", "D3.2", "D2.1"},
    # bridge output, before F1 (not in the sim)
    {"D1.1", "D3.1", "F1.1"},
    # [HVp]
    {"F1.2", "R_slow1.1", "R_fast1.1", "R5.1", "R1.1", "R_LED1.1", "R_sig1.1"},
    # slow chain [n_slow2..5]
    {"R_slow1.2", "R_slow2.1"}, {"R_slow2.2", "R_slow3.1"}, {"R_slow3.2", "R_slow4.1"},
    {"R_slow4.2", "R_slow5.1"},
    # [n_tf1] [n_drain]
    {"R_fast1.2", "TF1.1"}, {"TF1.2", "Q2.2"},
    # [n_gate_top] [n_gate]
    {"R5.2", "D9.1", "Q1.3", "R4.1"}, {"R4.2", "Q2.1", "C_byp2.1"},
    # [n_base_top] [n_q1b]
    {"R1.2", "R2.1", "R3.1"}, {"R3.2", "Q1.2"},
    # LED chain [n_led2..4] [n_dled] [n_led_a]
    {"R_LED1.2", "R_LED2.1"}, {"R_LED2.2", "R_LED3.1"}, {"R_LED3.2", "R_LED4.1"},
    {"R_LED4.2", "D_LED1.1"}, {"D_LED1.2", "LED1.2"},
    # signal chain [n_sig2..5] [n_sigout]
    {"R_sig1.2", "R_sig2.1"}, {"R_sig2.2", "R_sig3.1"}, {"R_sig3.2", "R_sig4.1"},
    {"R_sig4.2", "R_sig5.1"},
    {"R_sig5.2", "R_sig_bot1.1", "R_sig_bot2.1", "D_clamp1.2", "J5.1", "DVM1.1"},
    # [0]
    {"D4.2", "D2.2", "R_slow5.2", "Q2.3", "D9.2", "C_byp2.2", "R2.2", "Q1.1", "LED1.1",
     "R_sig_bot1.2", "R_sig_bot2.2", "D_clamp1.1", "J5.2", "DVM1.2"},
    # floating battery — must NOT touch GND
    {"BT1.1", "DVM1.3"}, {"BT1.2", "DVM1.4"},
]


# Off-board parts (on_board no) are left out of the exported netlist; ERC still
# checks that their pins are connected.
OFF_BOARD = ("J1.", "J2.", "DVM1.", "BT1.")
EXPECTED = [s for s in ({n for n in e if not n.startswith(OFF_BOARD)} for e in EXPECTED) if len(s) > 1]


def netlist():
    out = os.path.join(tempfile.gettempdir(), "capdis_check.net")
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, SCH],
                   check=True, capture_output=True)
    t = open(out, encoding="utf8").read()
    nets = {}
    for m in re.finditer(r'\(net\s*\(code "\d+"\)\s*\(name "([^"]*)"\)(.*?)\n\t\t\)', t, re.S):
        nodes = {f"{r}.{p}" for r, p in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', m.group(2))}
        nets[m.group(1)] = nodes
    return nets


def main():
    nets = netlist()
    ok = True
    got = [n for n in nets.values() if len(n) > 1]
    for exp in EXPECTED:
        if exp not in got:
            ok = False
            near = [(k, v) for k, v in nets.items() if v & exp]
            print("MISMATCH expected", sorted(exp))
            for k, v in near:
                print("    got", k, sorted(v))
    exp_all = set().union(*EXPECTED)
    for k, v in nets.items():
        if len(v) > 1 and v not in EXPECTED:
            ok = False
            print("UNEXPECTED net", k, sorted(v))
    for k, v in nets.items():
        if len(v) == 1 and v & exp_all:
            ok = False
            print("SINGLE-PIN net", k, sorted(v))

    rpt = os.path.join(tempfile.gettempdir(), "capdis_erc.rpt")
    subprocess.run([CLI, "sch", "erc", "--severity-error", "-o", rpt, SCH], capture_output=True)
    erc = open(rpt, encoding="utf8").read()
    m = re.search(r"Errors (\d+)", erc)
    if not m or int(m.group(1)):
        ok = False
        print(erc)
    print("netlist + ERC:", "PASS" if ok else "FAIL", f"({len(got)} nets checked)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
