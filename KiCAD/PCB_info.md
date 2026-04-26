# PCB Design Notes — Capacitor Discharger

---

## Q: Where does the HV part end? I have to separate it from the LV part, right? How would I do that on the PCB?

**HV zone** — high voltage AND significant current:
- Input terminals (HVp, GND)
- Slow path: R_slow1–5 (4.7kΩ × 5) — carry up to 25mA at 600V, get hot
- Fast path: R_fast (50Ω) → Q2 drain/source — up to 1.35A peak

**Boundary components** — HVp on one pin, only µA on the other:
- R1 (1MΩ) → Q1 base divider
- R5 (470kΩ) → gate clamp
- R_LED1 (100kΩ) → LED chain
- R_sig1 (100kΩ) → signal divider
- R_drop1 (15kΩ) → Vcc dropper

**LV zone** — everything downstream of the zeners:
- D9 clamps n_gate_top to 12V → Q1, R2, R3, R4, C_byp2
- D_DVcc clamps Vcc to 15V → C_Vcc, C_byp1, DVM connector
- LED, R_cal trimmer, signal output

The standard separation method is a **PCB slot (moat)**:

```
┌─────────────────────────────────────────────────┐
│  HV ZONE                                        │
│  [Input+]──[R_slow1-5]──[GND]──[Input−]         │
│       └──[R_fast]──[Q2 TO-220 + heatsink]──[GND]│
│                                                  │
│  R1, R5, R_LED1, R_sig1, R_drop1 (top pins)     │
│                                                  │
│══════════ PCB SLOT (≥1mm wide) ════════════════  │  ← enforces creepage ≥6mm
│                                                  │
│  LV ZONE                                        │
│  R1, R5, R_LED1, R_sig1, R_drop1 (bottom pins)  │
│  Q1, D9, DVM connector, LED, Vcc caps, R_cal    │
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
3. The five boundary resistors straddle the slot — top pin in HV zone, body across the gap, bottom pin in LV zone
4. Leave 3–5mm air gap between consecutive resistor bodies (R_slow1–5) — reduces creepage risk between adjacent HV nodes
5. No copper pour under resistor bodies — bare FR4 only; reduces surface tracking risk under high dissipation
6. R_cal trimmer in LV zone near the DVM connector for easy access
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

**HVp to LV** — all five boundary resistors bridge the gap (not just R1 and R5):
- R1 (1MΩ), R5 (470kΩ), R_LED1 (100kΩ), R_sig1 (100kΩ), R_drop1 (15kΩ)

The HVp copper trace stays entirely in the HV zone. Each resistor's top pin solders to HVp in the HV zone, body spans the cut, bottom pin lands in the LV zone. Voltage is already reduced before the LV copper begins.

**LV signals** — zero copper contact with HVp. n_gate, n_vcc, n_sigout, n_led_a are all LV-only nodes, entirely within the LV copper zone. The only thing crossing the slot is the physical body of those five resistors.

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
│  n_gate, n_vcc, n_sigout ║             │
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

Yes — correct and intentional for this design. The LV section is **not isolated**: it derives all power directly from HVp through resistive dividers. All sections (slow path, fast path, gate drive, LED, signal divider, Vcc dropper) share the same GND, which is the negative terminal of the capacitor under test.

Splitting into separate GNDs would require an isolated DC-DC converter for Vcc and an isolated DVM reference — unnecessary complexity.

The DVM (3-wire: Vcc+, Vcc−, signal input) must share GND with the discharge path for the voltage reading to be correct — so shared GND is **required**, not just acceptable.

The one real concern: PCB GND is at whatever potential the capacitor's negative terminal is at relative to earth. Touching the PCB while probing is dangerous — handled by enclosure design, not circuit isolation. The probes are the only user-touch points and are rated 1000V.
