# Solder-mask jig (single-sided board)

`Mask_jig.step` / `.stl`, made by `gen_mask_jig.py` (run in the FreeCAD GUI). For `CapacitorDischarger_1S`
(100 × 75 mm, Bungard FEPCU-075, 1.5 mm). 120.8 × 95.8 × 4.4 mm, print floor-down, no supports.

- **Pocket** 100.8 × 75.8 mm (0.4 mm per side around the board), **1.4 mm deep**: the 1.5 mm board sits 0.1 mm
  proud, so the film is pressed onto the board and then lies flat on the 10 mm frame. If your board is thinner
  than 1.4 mm, put a paper shim under it.
- **2 × Ø3.2 through holes** at the board's M3 holes H1 and H3, laid out for the board **copper side up**.
  Use Ø3 drill-bit shanks or M3 screws pushed up from below as registration pins. H1 and H3 aren't symmetric,
  so the board only fits one way round.
- Corner reliefs (square board corners in an FDM pocket) and 2 × Ø12 holes to push the board out from below.

## Use (UV solder mask)
1. Etched board **drilled**, cleaned, copper side up in the pocket. Pins up through H1 and H3.
2. Film: the B.Mask image on page 2 of `KiCAD/fab_1s/1S_films_1to1.pdf`, printed on transparency, **toner side down**.
   Punch or drill Ø3.2 through the two big H1/H3 dots. For a denser film, print it twice and stack the copies.
3. Paste on the board, film down over the pins, squeegee from the centre outwards. Excess goes into the gap and
   onto the frame. Tape the film edges to the frame.
4. Pull the pins out **downwards**, lay a sheet of glass on top for even pressure, expose. Ordinary picture-frame
   glass passes 395–405 nm LEDs well but cuts a lot at 365 nm: expose longer, or skip the glass with a 365 nm lamp.
5. Paste squeezed onto the frame cures there too. Cover the frame with one layer of packing tape before step 3 and
   peel it off afterwards, so the frame stays flat for the next board.
6. The HV slot under R1/R5 is already cut at this point (instruction.md step 4), so paste can squeeze through
   it onto the jig floor. Wipe the slot clean before exposing. Don't leave cured mask in it.
