# Enclosure: 3D-printable case for the single-sided board

There is one parametric FreeCAD script, [`gen_enclosure.py`](gen_enclosure.py), with all dimensions at the top.
[`assembly.py`](assembly.py) places the real board, the DC jack and stand-ins for the sockets, the PM-128 and the LED. It then
reports overlaps and HV distances. The result is saved as [`Enclosure_assembly.FCStd`](Enclosure_assembly.FCStd).

To regenerate, run both scripts inside FreeCAD (Python console or MCP), from `mechanical/enclosure/`:
```
exec(open("gen_enclosure.py", encoding="utf-8").read()); exec(open("assembly.py", encoding="utf-8").read())
```

The outside is **106.8 W × 132.8 D × 52 H mm**. It is designed for `CapacitorDischarger_1S` (100 × 75, FEPCU-075).

| Part | What it is | How to print |
|---|---|---|
| `Enclosure_base` (.step / .stl) | Open box: floor plus four walls, board standoffs, support posts, snap hooks, 4 screw bosses, socket, LED and jack holes, engraved 9 V warning | Floor down, no supports |
| `Enclosure_cover` (.step / .stl) | Top plate: meter window, baffled vents, lip inside the walls, 4 counterbored screw holes | **Upside down** (top on the bed), no supports |

- **Filament:** PETG or ASA, not PLA, because the resistors run hot.
- **Strength:** at least 3 perimeters and 25 % infill.
- **Style:** the same as the SursaTensiune case. It has R6 vertical corners, a 3 mm chamfer on the top edge and a 1.2 mm chamfer on the bottom edge.

## Layout
- **Front wall.** The sockets sit low (Z 15), in a 50 mm gap in front of the board.
  - **Danger LED (LED1)** at the top left, labelled "HV". It is on a 2-wire cable to J6 (JST XH) on the board.
  - It sits in a 5 mm panel clip (Ø8 collar, Ø6.5 body, 7 mm long) in a Ø6.6 hole at X 14.4. The hole is centred in the 8 mm gap between the front-left cover boss and the meter. Clip in from the front, LED pushed in from inside, no glue.
  - The black **−** socket (J2 → J4) and the green **+** socket (J1 → J3) are on the right, 20.5 mm apart.
  - Each socket lines up with the inner wire entry of its MKDS terminal block. Its M4 ring lug points straight into that entry, about 7 mm short of the block. The probe wires are short and straight, so they don't cross.
  - The terminal-block screws stay free to reach from the top.
- **Left wall, front end.** The 9 V DC jack sits low (Z 15) under an engraved warning triangle. Next to it:
  "9 V DC IN + centre / FLOATING SUPPLY ONLY / 9 V battery or isolated adapter. / NEVER an earthed / grounded supply!".
  The rear wall has no room for it: the board fills the box right up to it.
- **Cover.**
  - **PM-128 meter.** It sits above the socket gap: window 44.5 × 19.7 mm, plus two Ø3.2 holes 57.15 mm apart.
  - **Label.** "600 V MAX" is engraved under the meter.
  - **Vents.** Five 2 mm slots sit above R_slow1–5. Each slot has a solid baffle strip 3 mm below it, wide enough that no straight wire or probe tip can reach HV through a slot.
- **Board fixing.** The PCB has only 2 holes, so the base adds the rest:

  | Feature | Where | Job |
  |---|---|---|
  | 2 standoffs (6 mm) | H1, H3 | M3×12 **nylon** screws from the top, nuts in hex pockets under the floor |
  | 4 support posts | under J3/J4 (screwdriver force) and under the two F1 clip centres (pushing the fuse in) | carry the load |
  | 3 snap hooks | front-left, front-right and rear-left corners | a 45° ledge under the copper-free edge, and a nose 0.8 mm over the board top |
  | 4 side ribs | side walls | locate the board in X with 0.3 mm play |

  - The board clicks down into the hooks. To lift it out, take out the two screws and push the hooks outwards.
  - The board's top side has no copper, so the hooks only touch FR4. Leave the F1 clip centre holes empty, because the posts sit under them.
- **Cover fixing.** 4 × **M3×10** go into M3 heat-set inserts (Ø4.0 × 6.5 mm holes) in bosses hanging from the walls. The bosses have a 45° underside, so they print without support.
  - Three bosses are in corners. The fourth sits on the rear wall at X 20, so the LED cable can rise from J6 in that corner.
  - Opening the box needs a tool, which is right for an HV device. The magnets aren't needed.
- **Below the board.** The standoffs are 6 mm tall and all the HV copper is on the underside, so **trim every lead to ≤ 3 mm**. The stock TO-220 3D model shows uncut Q2 legs reaching the floor.

## Assembly
1. Fit the sockets (front wall) and the DC jack (left wall), with their nuts on the inside. Push the LED clip into the front wall from the outside,
   with its slots vertical so the body spreads up/down, away from the boss and the meter. Push the LED into it from inside:
   heat-shrink both legs, then crimp the XH housing onto ~15 cm of 1 kV silicone wire. Pin 1 = cathode (GND), pin 2 = anode.
2. Wire the sockets to J3/J4 with 1.5 mm² silicone wire (0.6/1 kV) and M4 ring lugs, and put heat-shrink over the lugs.
3. Press in the heat-set inserts.
4. Put the board on the standoffs, let it click into the hooks, and fit the two nylon screws. Plug the LED into J6
   (rear-left). Run its cable up and along the left wall, above the Q2 heatsink, then down to the front.
5. Fit the meter under the cover: two screws through the cover into the bezel. Wire the meter:
   - **Supply:** DC jack → PM-128 supply pins.
   - **Input:** J5 → PM-128 VIN / IN GND. This cable runs over the HV area, so use the same 1 kV silicone wire.
6. Leave the wires long enough that the cover can be laid down beside the box. Close it with the 4 M3×10 screws.
7. Stick rubber feet under the floor.

**9 V input:** any **floating** 9 V source on a 5.5×2.1 plug (centre +). A battery on a plug or a double-insulated adapter is fine. Never use a supply whose − is earthed or connected to the device under test, because circuit GND sits at the capacitor's negative terminal (see BOM, BT1).

## Fit check (FreeCAD, `assembly.py`)
- **Overlaps.** None between base and cover, or between either of them and the board, jack, sockets, meter or LED. The one exception is Q2's uncut 3D-model legs (see above).
- **Height.** The tallest part, R_fast1, tops out at Z 47.0, and the inner face of the cover is at Z 49.6.
  - Baffle strips → R_slow: ≥ 6.6 mm.
  - LED clip / LED flange → meter: 1.1 mm (clip → boss 0.75 mm). Both are LV; the meter only moves in Z when the cover goes on.
  - DC jack → meter: 8.3 mm.
- **HV clearances, all at least 6 mm:**
  - Meter → socket lugs/bolts: 6.9 mm.
  - Socket A metal → socket B metal: 12.5 mm.
  - Socket B → DC jack: 45.9 mm.
- **Tightest gap:** J3's terminal block and the front-right hook are 0.1 mm apart. That hook is 3 mm wide so it stays clear of the block.

## Check before printing
- **PM-128 (VERIFY):** 70 × 40 mm bezel, 23 mm deep, window 1.75 × 0.775 in, Ø3.2 holes 2.25 in apart (MPJA PM128 sheet). Measure your meter; the values are `MET`, `MET_WIN` and `MET_HOLE_*`.
- **Stäubli SLB4-G:** Ø12.1 hole with a flat 11.0 mm across, printed with the flat on top. The socket and nut in `assembly.py` are stand-ins; the real nut size isn't on the datasheet.
- **Heat-set inserts:** use one that fits a Ø4.0 hole and is ≤ 6 mm long. Otherwise change `INS_D` / `INS_L`. With `INS_D = 2.6` the screws thread straight into the PETG.
- **Test print:** print the front-right corner first (sockets, hook, boss) to check the socket fit and the hook snap.
