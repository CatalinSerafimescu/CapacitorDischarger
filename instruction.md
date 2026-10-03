# Build instructions: 600 V capacitor discharger (single-sided board + 3D-printed case)

This guide covers building, wiring, testing, calibrating and using the unit.
- Part data: [bom.md](bom.md).
- Design details: [README.md](README.md), [KiCAD/PCB_info.md](KiCAD/PCB_info.md), [simulation/](simulation/README.md).
- Enclosure: [mechanical/enclosure/README.md](mechanical/enclosure/README.md).

> **HV warning.** This tool is connected to capacitors charged up to 600 V. While a capacitor is connected,
> circuit GND sits at the capacitor's negative terminal and most of the board sits at hundreds of volts.
> Work on the board only with the probes disconnected. Close the cover before use.

---

## 1. What you are building

```
 probe + ─► banana J1 (green) ─► J3 ┐                     ┌─► R_slow1-5 (23.5 kΩ) ─────────────────► GND   always on
 probe − ─► banana J2 (black) ─► J4 ┴─► bridge D1-D4 ─► F1 ┼─► R_fast1 (50 Ω) ─► TF1 ─► Q2 ─────────► GND   only below ~63 V
                                       (any polarity)      ├─► R1/R2 ► Q1 ► R5/D9 (threshold, gate drive of Q2)
                                                           ├─► R_LED1-4 ► D_LED1 ► J6 ═ cable ═► LED1 (front panel)   on above ~10 V
                                                           └─► R_sig1-5 ► R_sig_bot (10 000:1) ► J5 ═ cable ═► PM-128 (cover)
 floating 9 V ─► DC jack (left wall) ═ cable ═► PM-128 supply
```

- **Above ~63 V:** only R_slow is connected, so the current stays at 25 mA or less. A 1 mF cap at 600 V takes about 45 s to discharge.
- **Below ~63 V:** Q2 adds R_fast, so the rest goes in under a second.
- **LED:** it is ON above ~10.2 V and OFF below.
- **Meter:** it reads in volts, with 1 V resolution ("600" at 600 V).
- **Protection:**
  - F1 (2 A, 1000 V DC) opens if Q2 fails short at high voltage.
  - TF1 (133 °C, mounted on R_fast) opens if the probes stay on a live supply below 63 V.

---

## 2. Parts and tools

Every part is in [bom.md](bom.md) with its inventory ID. The **still to buy** list is
[TO_BUY_list.csv](TO_BUY_list.csv). It includes the fuse, the CSO clips, TF1, the HLMP-4700 LED and the enclosure hardware:
- 4× M3 heat-set inserts.
- 4× M3×10 screws.
- 2× M3×12 **nylon** screws and nuts.
- Rubber feet.

**Wire:**
- **Probe leads (J1/J2 → J3/J4):** 1.5 mm² silicone, rated 0.6/1 kV.
- **J5 cable, LED cable and 9 V wires:** thin silicone wire rated 1 kV. They run over HV parts.
- **Lugs:** M4 ring lugs for the banana sockets.

**Tools:**
- UV exposure box, NaOH developer, etchant, 0.8–3.4 mm drills and a saw or rotary tool for the slot.
- Soldering iron, multimeter, JST XH crimp tool and heat-shrink.
- Soldering iron tip for the heat-set inserts.

---

## 3. Making the PCB (Bungard FEPCU-075, 100 × 75 mm, positive photoresist)

The board is **single-sided**: copper only on the bottom, no vias, no jumpers. Parts go on the top.

1. **Print the film.** Print [KiCAD/fab_1s/1S_B.Cu_exposure_1to1.pdf](KiCAD/fab_1s/1S_B.Cu_exposure_1to1.pdf) on transparency. Set the size to **100 %** (not fit-to-page) and toner density to maximum. Check the 100 × 75 mm outline with a ruler.
   - The film is a positive, drawn as seen from the component side. **Lay it toner side down on the copper.**
   - For toner transfer, or for a negative photoresist, use page 1 of [KiCAD/fab_1s/1S_films_1to1.pdf](KiCAD/fab_1s/1S_films_1to1.pdf): B.Cu positive and negative side by side, same orientation.
2. **Expose and develop.** Expose, then develop in NaOH (about 7 g/l). Rinse, then etch: sodium persulfate at 40–45 °C, or FeCl₃.
   - Do a test strip first, because exposure time depends on your UV box.
   - To strip the leftover resist, re-expose the whole board and develop again, or use acetone.
3. **Drill.** The small marks in each pad help centre the drill.

   | Drill | Holes | Parts |
   |---|---|---|
   | 0.8 mm | 37 | small resistors, D_LED1, D_clamp2, Q1, C_byp2 |
   | 1.0 mm | 8 | J5, J6, R1, R5 |
   | 1.1 mm | 14 | D1–D4, D9, D_clamp1, R_fast1 |
   | 1.2 mm | 3 | Q2 |
   | 1.3 mm | 2 | TF1 |
   | 1.4 mm | 14 | J3, J4, R_slow1–5 |
   | 2.35 mm | 4 | F1 clip pins |
   | 3.4 mm | 2 | F1 clip centre holes (leave them empty) |
   | 3.2 mm | 2 | H1, H3 mounting holes |

4. **Cut the slot.** It is the 17.5 × 3 mm outlined rectangle under R1/R5. Cut it with a saw or rotary tool. Its job is to lengthen the 600 V creepage path between the two pads of R1 and of R5.
5. **Protect the copper (recommended).** Clean the board and coat the copper side with your green solder mask, leaving the pads open. For UV mask, the film is the B.Mask image on page 2 of [KiCAD/fab_1s/1S_films_1to1.pdf](KiCAD/fab_1s/1S_films_1to1.pdf), and the board goes in the jig in [mechanical/mask_jig/](mechanical/mask_jig/README.md). If you don't have it, use PCB lacquer. Uncoated copper also works, because the clearances are designed for it.

---

## 4. Board assembly (low parts first)

Use [KiCAD/fab_1s/1S_assembly_top.pdf](KiCAD/fab_1s/1S_assembly_top.pdf) as the placement map. Almost every part stands vertically.

1. **Small resistors, standing:** R_sig1–5, R_LED1–4, R_sig_bot1/2, R2–R4. Put the body on the pad marked by the outline circle.
2. **Diodes and zeners** (check the band):
   - D_LED1 and D_clamp2: both BZX55C8V2.
   - D9: BZX85C12.
   - D_clamp1 and D1–D4: 1N4007.

   D_clamp2 sits next to J6. Its cathode connects to LED_A and its anode to GND.
3. **Small parts:** Q1 (MPSA42, flat side as drawn), C_byp2, J5 (pin header), and **J6 (JST XH 2-pin)**.
4. **R1 and R5 (3 W):** the body stands on the LV pad, and the bare lead crosses the slot to the HVp pad. Keep that lead straight and clear of everything else.
5. **J3 and J4 (MKDS 5):** wire entries face the board edge.
6. **F1 clips (Schurter CSO):** solder both pins of each clip. Leave the centre holes empty, because the case has support posts under them.
7. **R_slow1–5 (5 W):** standing, about 3 mm above the board. The gap between bodies is for airflow.
8. **R_fast1 (7 W) and TF1:** stand R_fast1 up. Clamp TF1's body against it with stainless wire or a clip, using a thin layer of thermal compound. TF1's metal case is at HV.
9. **Q2 (STP10NK80Z):**
   - Bend the gate and source legs out to the 5.08 mm pitch.
   - Slip the HS-S01 heatsink onto the tab with the **Fischer MST 220** insulator under it.
   - **Check** with an ohmmeter that the heatsink is not connected to the tab (drain): it must read open.
10. **Trim every lead to ≤ 3 mm** under the board. The case standoffs are only 6 mm high, and all the HV copper is on the underside.
11. **Clean off all flux** with isopropyl alcohol. Flux residue leaks at 600 V.

**Cold checks (multimeter):**

| Check | Expected |
|---|---|
| F1 fitted: clip A ↔ clip B | ~0 Ω |
| R_fast1 pad ↔ Q2 drain (through TF1) | ~0 Ω |
| HVp (F1 clip B, red lead) ↔ GND ring (black lead) | ≈ 22 kΩ: 23.5 kΩ for R_slow, in parallel with the divider chains. With the leads reversed it reads low, through Q2's body diode and R_fast1. |
| Q2 heatsink ↔ Q2 tab | open |

---

## 5. Enclosure

Full details are in [mechanical/enclosure/README.md](mechanical/enclosure/README.md).
1. **Print.** Print `Enclosure_base.stl` floor-down and `Enclosure_cover.stl` upside-down, both in **PETG or ASA (not PLA)**, with no supports. Use at least 3 perimeters and 25 % infill.
2. **Test print (recommended).** Print the front-right corner first to check the socket fit and how the board hooks snap.
3. **Heat-set inserts.** Press the 4 M3 inserts into the corner bosses with the soldering iron.
4. **Check before printing:**
   - **PM-128:** measure yours. The script assumes 70 × 40 mm, 23 mm deep, a 44.5 × 19.7 mm window and holes 57.15 mm apart (`MET*` in `gen_enclosure.py`).
   - **Insert hole:** it is Ø4.0 × 6.5 mm (`INS_D`, `INS_L`).

---

## 6. Wiring and final assembly

1. **Banana sockets (front wall):**
   - Fit the green socket J1 on the right ("+") and the black J2 next to it ("−"). Their nuts go inside, and the flat of each hole is on top.
   - Crimp M4 ring lugs on 1.5 mm² silicone wire. Bolt them to the sockets and heat-shrink the lugs.
   - Each lug points straight at its terminal block: J1 → **J3**, J2 → **J4**.
   - Both poles of a block are the same probe, so use either entry.
2. **DC jack (left wall, under the warning).** Fit it with its nut inside.
3. **Front-panel LED (LED1, HLMP-4700):**
   - Heat-shrink both legs.
   - Crimp the XH housing onto about 15 cm of 1 kV wire: **pin 1 = cathode (GND), pin 2 = anode.**
   - Push the LED in from inside so its flange sits in the recess, then glue it.
4. **Board:** put it on the standoffs and press it down until the 3 hooks click. Fit the two **nylon** M3×12 screws (H1, H3), with nuts in the hex pockets under the floor.
5. **Connect the probe wires** into J3/J4 and tighten the screws. They stay reachable from the top.
6. **Plug the LED into J6** (rear-left). Run the cable up and along the left wall, above the Q2 heatsink, then down to the front panel.
7. **PM-128:**
   - Leave the factory **RB** wire jumper in place. Don't fit **RA**, and leave the decimal-point jumpers **P1–P3 open**.
   - Mount the meter under the cover with two screws through the cover into its bezel.
   - **Supply:** DC jack centre (+) → PM-128 +9 V; jack sleeve (−) → PM-128 −9 V. **Never connect the jack to circuit GND.**
   - **Input:** J5 pin 1 (VIN) → PM-128 VIN; J5 pin 2 (GND) → PM-128 IN GND. Use a 2-pin plug on the J5 header.
8. **Close up.** Leave the cover wires long enough that the cover can lie beside the box. Close it with 4× M3×10 screws and stick rubber feet under the floor.

**Wiring table**

| From | To | Wire |
|---|---|---|
| J1 green socket (M4 lug) | J3 (either entry) | 1.5 mm² silicone, 1 kV |
| J2 black socket (M4 lug) | J4 (either entry) | 1.5 mm² silicone, 1 kV |
| DC jack centre (+) / sleeve (−) | PM-128 +9 V / −9 V | thin silicone, 1 kV |
| J5 pin 1 / pin 2 | PM-128 VIN / IN GND | thin silicone, 1 kV |
| J6 pin 1 / pin 2 (XH) | LED1 cathode / anode | thin silicone, 1 kV |

**9 V supply:** any **floating** 9 V source on a 5.5×2.1 plug (centre +), drawing ~1 mA. A 9 V battery on a plug or a double-insulated adapter is fine. Never use a supply whose − is earthed or tied to the device under test (see the warning on the case).

---

## 7. Tests

Do them in this order. Use capacitors rated above the test voltage.

1. **Meter power.**
   - Probes open, 9 V plugged in: the PM-128 shows `0` (or `000`).
   - The jack sleeve ↔ GND ring reads open.
2. **Low voltage.**
   - Charge an electrolytic to about 24 V from a bench supply (e.g. 1000 µF / 35 V through 100 Ω), then disconnect the supply.
   - Touch the probes to it: the LED lights, the meter reads ~24 and drops fast, and the LED goes out around 10 V.
   - **Don't test on a live bench supply below 63 V.** The tool is then a 50 Ω load, and TF1 (one-shot) will open within seconds.
3. **Mid voltage.**
   - Charge a 470 µF / 450 V capacitor to 300 V from a current-limited HV source, then disconnect the source.
   - Expect: the meter reads ~300, the slow phase lasts ~15 s down to 63 V, then a fast drop, and the LED goes off around 10 V. *(Simulation B: 14.7 s.)*
4. **Full voltage.**
   - Charge a 1 mF cap rated ≥ 700 V to 600 V (or a series stack of caps with balancing resistors).
   - Expect ~45 s total *(simulation A: 45.2 s)*, peak R_slow current ≈ 25 mA, and fast-path peak ~1.2 A.
   - Repeat 5×, letting it cool in between. The R_slow bodies must not discolour, and the case must stay below ~60 °C.
5. **Reverse polarity.** Repeat a 300 V discharge with the probes swapped. It should behave the same, and the meter still reads positive.
6. **Probes shorted together.** Nothing happens: no source, no current.

---

## 8. Calibration (PM-128 trimmer R4)

The divider is 10 000:1 within 1 %. The PM-128 trimmer R4 corrects the remaining error.

- **Best method:** apply a steady DC voltage of 100–300 V from an HV bench supply (the tool draws V / ~22 kΩ, e.g. 14 mA at 300 V). Measure it with a DMM at the probes and turn R4 until the display matches. Then check at a second voltage.
- **Without an HV supply:**
  1. Unplug J5.
  2. Feed a stable ~50 mV (a resistor divider from the 9 V) into PM-128 VIN / IN GND.
  3. Set R4 so the display shows the DMM reading in mV × 10. For example, 50.0 mV should read `500`.
  4. Reconnect J5.

  This doesn't correct the divider's own ±1 %.

---

## 9. Using the tool

1. Plug in the 9 V source and check that the meter shows `0`.
2. Connect both probes to the capacitor (any polarity). The LED lights and the meter shows the voltage.
3. Wait until **the LED is off and the meter reads 0–1**, then keep the probes on for a few more seconds.
4. Check with a separate multimeter before touching the capacitor. Electrolytics recover a few volts after discharge.
5. **Limits:**
   - 600 V maximum.
   - **Never** on live circuits or mains-connected equipment.
   - With large caps (≥ 1 mF at 600 V, ~180 J), let the resistors cool between discharges.

---

## 10. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Discharge slows down and never finishes below ~63 V | TF1 has opened (live supply, or Q2 stuck on). Replace TF1 and check Q1/D9/Q2. The slow path still works. |
| Nothing discharges, LED and meter dead with a charged cap | F1 is blown (check for a shorted Q2 first), or a probe wire is loose in J3/J4. |
| LED never lights | LED plugged in backwards on J6 (pin 1 = cathode), LED wire broken, or D_LED1/D_clamp2 fitted backwards. |
| Meter shows `1` (overrange) as soon as a charged cap is connected | R_sig_bot1/2 open, so the meter input sits at D_clamp1's 0.7 V. Check the divider bottom and J5. |
| Meter dead | 9 V not plugged in, polarity reversed at the jack, or supply below 7 V. |
| Meter reads ~10× too low or high | Decimal-point or RA/RB jumpers changed on the PM-128 (see §6). |
