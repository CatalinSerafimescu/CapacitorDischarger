# PCB Design Notes — Capacitor Discharger

---

## Status — 2026-10-01: two boards, both script-generated

| Board | Files | Size | Copper | Parts | Height |
|---|---|---|---|---|---|
| **Single-sided, home etch** | `CapacitorDischarger_1S.*` + `fab_1s/` | **100 × 75 mm** (Bungard FEPCU-075) | B.Cu only, no jumpers | power resistors and small parts **standing** | ~40 mm (R_fast1 standing) |
| **2-layer, for a PCB fab** | `CapacitorDischarger.*` | **120 × 90 mm** (was 180 × 130) | both layers, autorouted | R_slow / R_fast / TF1 **flat**, small parts standing | ~25 mm |

Both pass DRC with schematic parity: **0 errors, 0 unconnected, 0 parity issues**. The only findings are 2 silkscreen notes where the R1/R5 outlines cross their milled slot, which is intended.

**Edit the scripts, not the KiCad files.** Run them from `KiCAD/`:

| Step | Command | Produces / checks |
|---|---|---|
| 0 | `python gen_3d.py` (needs CadQuery; only when a part changes) | `CapDis.3dshapes/`: true-size STEP bodies for the custom footprints (MKDS 5, CSO clips + fuse, Ohmite 45F/27J, SEFUSE, FMP300, HS-S01 on Q2) |
| 1 | `python gen_footprints.py` | `CapDis.pretty/`: custom footprints (F1 CSO clips, MKDS 5, Ohmite 45F/27J flat + standing, SEFUSE flat + standing, FMP300 standing, TO-220 with spread legs) |
| 2 | `python gen_kicad_sch.py` and `python gen_kicad_sch.py --project CapacitorDischarger_1S` | Two schematics: same circuit, footprints per board (`VARIANTS`) |
| 3 | `python check_kicad.py` | Netlist vs. `simulation/discharger.cir.tmpl`, pin by pin, plus ERC. **PASS.** |
| 4 | `"C:\Program Files\KiCad\10.0\bin\python.exe" gen_pcb.py --freerouting <freerouting-2.4.1.jar>` | 2-layer board: placement, slot, Q2/chain/GND pre-routes, Freerouting, DRC |
| 5 | `"C:\Program Files\KiCad\10.0\bin\python.exe" board_1s.py` | Single-sided board: placement and hand routes, DRC |

**Clearance rules (`hv_rules.py` → `*.kicad_dru`).**
- CLAUDE.md asks for ≥ 6 mm, based on 1 mm per 100 V. Each net pair gets **1 mm per 100 V of the worst-case difference it can actually see**. The worst case is taken over normal / reversed probes, F1 blown, TF1 open, and Q2 conducting at 85 V.
- **HV to GND/LV, probes and BRIDGE_P to anything: 6 mm.** HVp to the R_fast–TF1 node: 0.9 mm. Neighbouring chain nodes: 1.2–1.5 mm. Minimum 0.4 mm.
- The 2-layer board passes the same matrix to Freerouting as per-net classes plus `class_class` rules, so the router and the DRC agree.
- **One exception, the Q2 pin field.** Only drain-related items get 2.5 mm: the legs are bent out to 5.08 mm, and the part is rated 800 V between pins.

**Single-sided layout (100 × 75).**
- **Probes:** they enter at the top edge (J3 = PROBE_A, J4 = PROBE_B, both poles of each block on the same net).
- **Bridge and F1:** the bridge is four vertical diodes right below the probes, with the GND anodes on the outside. F1 sits below it, and its right clip is the HVp hub.
- **GND ring:** a 1.5 mm GND ring along the board edge joins both bridge anodes and every return. This is what lets a single layer work without jumpers.
- **Top-right pocket:** R_fast1 standing, with TF1 standing 0.5 mm from its body (clamp them together). Q2 has the HS-S01 slipped onto its tab. The gate drive is LV and runs along the GND ring. R1 and R5 stand on their LV pad, with the bare HVp lead across a 17.5 × 3 mm slot.
- **Bottom-left:** R_slow1–5 standing, 2.3 mm air between bodies.
- **Bottom-right:** the divider and LED chains as staircases, then D_LED1, LED1, the divider bottom, D_clamp1 and J5.
- **Holes:** two M3 holes, H1 and H3. Use nylon screws; H2 and H4 don't fit on this board.
- **`fab_1s/`:**
  - `1S_B.Cu_exposure_1to1.pdf`: positive, as seen from the component side. Print 1:1 on transparency and lay it **toner side down** on the copper. Small drill marks help centring the drill.
  - `1S_assembly_top.pdf`: part references and outlines.
  - `CapacitorDischarger_1S.drl`: hole sizes.
  - `CapacitorDischarger_1S.step`: 3D board with parts, for designing the enclosure (`fab_2l/CapacitorDischarger_2L.step` for the 2-layer board).
- **The slot** is the outlined rectangle: cut it with a saw or rotary tool.

**2-layer layout (120 × 90).**
- **Same top-left block** as the single-sided board.
- **Fast path:** R_fast1 lies flat along the top, with TF1 under it (1 mm body gap) and Q2 tab-down with the HS-S01.
- **Gate drive:** packed right of Q2, with R1/R5 across a 23 × 3 mm slot.
- **Slow path:** the R_slow columns are flat, bottom-left.
- **Divider and LED chains:** the same staircases as on the single-sided board.
- **No copper pours.** Four M3 holes; use nylon screws.

**Check before building:**
- **MKDS 5/2-9.5:** which face the pin row is 4.6 mm from. This sets the wire-entry side.
- **Schurter CSO clip:** the 3.4 mm centre hole is plated as part of the pad; make sure it doesn't foul the clip.
- **HS-S01 on Q2 with the MST 220 insulator:** check it fits. It must not touch R4/C_byp2 (2-layer) or the GND ring (single-sided).
- Print the board 1:1 and lay the real parts on it.

---

## Q: Where does the HV part end? I have to separate it from the LV part, right? How would I do that on the PCB?

**HV zone** — high voltage AND significant current:
- Input terminals (HVp, GND)
- Slow path: R_slow1–5 (4.7kΩ × 5) — carry up to 25mA at 600V, get hot
- Fast path: R_fast (50Ω) → Q2 drain/source — up to 1.35A peak

**Boundary components** — high voltage on one pin, LV on the other (they straddle the slot):
- R1 (1MΩ) → Q1 base divider
- R5 (470kΩ) → gate clamp
- R_LED4 (100kΩ) — bottom of the LED chain (top pin ≈ ¼ of HVp, bottom ≈ 10 V)
- R_sig5 (100kΩ) — bottom of the signal divider (top pin ≈ ⅕ of HVp, bottom ≤ 60 mV)

R_LED1–3 and R_sig1–4 are entirely HV (their nodes sit at 120–480 V) and stay in the HV zone.

**LV zone** — everything downstream of the zeners:
- D9 clamps n_gate_top to 12V → Q1, R2, R3, R4, C_byp2
- R_sig_bot1/2 + D_clamp, J5 (2-pin, to the off-board PM-128)
- LED

The standard separation method is a **PCB slot (moat)**:

```
┌─────────────────────────────────────────────────┐
│  HV ZONE                                        │
│  [Input+]──[R_slow1-5]──[GND]──[Input−]         │
│       └──[R_fast]──[Q2 TO-220 + heatsink]──[GND]│
│                                                  │
│  R1, R5, R_LED4, R_sig5 (top pins)              │
│                                                  │
│══════════ PCB SLOT (≥1mm wide) ════════════════  │  ← enforces creepage ≥6mm
│                                                  │
│  LV ZONE                                        │
│  R1, R5, R_LED4, R_sig5 (bottom pins)           │
│  Q1, D9, J5 (DVM), LED, R_sig_bot1/2, D_clamp   │
└─────────────────────────────────────────────────┘
```

Key PCB rules:

| Rule | Value |
|------|-------|
| Min trace clearance HV↔GND | 8mm |
| Min trace clearance HV↔LV signals | 6mm |
| Creepage (enforced by slot) | 6mm |
| HVp / GND return traces | 2mm min or copper pour |
| Q2 drain/source traces | 2mm min |
| Slow path resistors | standoff from PCB surface, no copper pour underneath |
| Spacing between consecutive resistor bodies | 3–5mm |
| Q2 | TO-220 with heatsink tab, mounting hole |

Practical layout tips:
1. Put input terminals and Q2 at the top edge — short HV current loop
2. Run the GND return as a copper pour directly under the discharge path
3. The four boundary resistors straddle the slot — top pin in HV zone, body across the gap, bottom pin in LV zone
4. Leave 3–5mm air gap between consecutive resistor bodies (R_slow1–5) — reduces creepage risk between adjacent HV nodes
5. No copper pour under resistor bodies — bare FR4 only; reduces surface tracking risk under high dissipation
6. R_sig_bot1/2 + D_clamp right next to J5 in the LV zone
7. DVM connector on the board edge, in LV zone only

---

## Q: The slot is an area where copper is missing, right? But then how do I pass GND from HV to LV?

The slot doesn't span the full board width — it's a targeted partial cut. GND routes **around the ends** of the slot:

```
                    board edge
┌──────────────────────────────────────────┐
│                                          │
│  HVp ══════════════════════              │
│                            ║             │
│  GND ══════════════════════╝ (HV zone)   │
│                     │                    │
│              ╔══════╝  ← GND goes        │
│              ║            around end     │
│   ┌──────────╨──────────────┐            │
│   │       S L O T           │  ← cut     │
│   └─────────────────────────┘            │
│              ║                           │
│              ╚══ GND (LV zone) ══════    │
│                                          │
│  LV signals ═════════════════════════    │
└──────────────────────────────────────────┘
```

- The slot interrupts the shortest surface path between HVp and LV signal traces → enforces ≥6mm creepage
- GND is at 0V so needs no separation from anything — routes freely around the slot end
- HVp never crosses the slot — stays entirely in the HV zone

---

## Q: Is the slot a physical cut in the board, or just a copper-free area? Is GND a copper pour? Does HVp reach the LV zone only through those resistors? Do LV signals have zero contact with HV?

**Slot** — physical cut through the PCB material (FR4 milled away), not just copper-free.  
Reason: surface contamination (flux residue, humidity, dust) allows current to creep along the PCB surface. A physical cut forces the creepage path to go around the slot edges through air, which is far more resistant. Copper-free alone is not sufficient.

**GND** — yes, copper pour for GND is the standard and correct approach. Individual traces for all other signals. This also minimises return-path inductance and resistance for the discharge current.

**HVp to LV** — all four boundary resistors bridge the gap (not just R1 and R5):
- R1 (1MΩ), R5 (470kΩ), R_LED4 (100kΩ), R_sig5 (100kΩ)

The HVp copper trace stays entirely in the HV zone. Each resistor's top pin solders to HVp in the HV zone, body spans the cut, bottom pin lands in the LV zone. Voltage is already reduced before the LV copper begins.

**LV signals** — zero copper contact with HVp. GATE, GATE_TOP, SIGOUT, LED_A are all LV-only nodes, entirely within the LV copper zone. The only thing crossing the slot is the physical body of those four resistors.

---

## Q: The slot does not have to cut the whole board, right? I want it to stay one piece.

Correct — the slot is a partial cut, not a full separation. It's a rectangle milled into the board, closed on both ends. The board stays physically one piece. GND copper connects around both ends of the slot.

```
┌────────────────────────────────────────┐
│  HVp ══════════════════                │
│                          ║             │
│  GND pour (HV zone)      ║             │
│                     ┌────╨─────────┐   │
│                     │   S L O T    │   │  ← partial cut, board stays one piece
│                     └──────────────┘   │
│  GND pour (LV zone)      ║             │
│                          ║             │
│  GATE, GATE_TOP, SIGOUT  ║             │
└────────────────────────────────────────┘
```

The only rule: shortest path from any HVp copper to any LV copper — measured along the board surface going around the slot — must be ≥6mm.

---

## Q: I have two 2-pin screw terminals to connect the banana sockets to the PCB. Should I use one connector for both probes (with a copper cut between pins), or two separate connectors?

Both screw terminals are in the HV zone — they are the PCB entry points for the two probes. Full chain:

```
Capacitor → banana plug → banana socket (on enclosure) → wire → PCB screw terminal
```

**Do not use one 2-pin connector for both probes.** Standard screw terminal pitch is 3.5–5mm — that puts 600V across a gap below the 6mm minimum. The connector body is not rated for that.

**Use two separate connectors**, one per probe, placed in the HV zone with ≥6mm copper clearance between the HV+ pad and GND pad on the PCB:

```
HV ZONE
┌────────────────────────────┐
│ [PROBE_A screw term]  HV+  │
│         ← ≥6mm →           │
│ [PROBE_B screw term]  GND  │
│                            │
│ discharge resistors, Q2... │
└────────────────────────────┘
```

Each connector uses one functional pin (the probe wire). The second pin of each 2-pin block can be left unused or used to daisy-chain to the discharge resistors.

---

## Q: Is it OK to link HV and LV to the same GND?

Yes — correct and intentional for this design. The LV section is **not isolated**: it derives all power directly from HVp through resistive dividers. All sections (slow path, fast path, gate drive, LED, signal divider) share the same GND, which is the negative terminal of the capacitor under test.

The PM-128 **input** (VIN / IN GND via J5) must share GND with the divider for the reading to be correct. Its **supply** is the opposite: the PM-128 needs separate supply and input grounds, so the 9 V battery (BT1) floats and never touches circuit GND.

The one real concern: PCB GND is at whatever potential the capacitor's negative terminal is at relative to earth. Touching the PCB while probing is dangerous — handled by enclosure design, not circuit isolation. The probes are the only user-touch points and are rated 1000V.
