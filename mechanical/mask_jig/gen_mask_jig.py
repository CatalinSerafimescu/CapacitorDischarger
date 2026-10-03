"""Solder-mask jig for the single-sided board (CapacitorDischarger_1S, 100 x 75 mm, Bungard FEPCU-075, 1.5 mm).

Holds the etched PCB flush with a flat frame so the mask film lies flat on paste + frame.

Run inside the FreeCAD GUI (Python console or MCP):
    exec(open(r"<repo>/mechanical/mask_jig/gen_mask_jig.py", encoding="utf-8").read())
Creates document "MaskJig" with object Jig, exports Mask_jig.step / .stl next to this script.

Coordinates (mm): origin = bottom-left outer corner, X along the 100 mm board edge, Z = up.
The board lies COPPER SIDE UP (B.Cu), i.e. mirrored with respect to the KiCad top view.
- Pocket 1.4 deep for the 1.5 mm board: the copper sits 0.1 mm PROUD of the frame, so the film is pressed onto
  the board, never left hanging over a recessed board. Too low → a paper shim under the board.
- 2 x Ø3.2 through holes at the board's M3 holes H1 / H3: pins (Ø3 drill-bit shanks) pushed up from below register
  board + punched film; pull them out downwards before the glass goes on. H1 / H3 are not symmetric, so the board
  only fits one way round.
- Corner reliefs so the square board corners fit in an FDM pocket; 2 push-out holes to lift the board from below.
Print floor-down, no supports, 0.2 mm layers (all Z heights on the 0.2 grid).
"""
import os

import FreeCAD as App
import Part

V = App.Vector
OUT = r"E:\Catalin\Work\Electronics\CapacitorDischarger_Claude\mechanical\mask_jig"   # exec() under the MCP sees its own __file__

BW, BH = 100.0, 75.0           # board outline (KiCad Edge.Cuts, board_1s.py)
GAP = 0.4                      # clearance per side (board is hand-cut; the pins do the registering)
BORDER = 10.0                  # flat frame around the pocket, for the film
FLOOR = 3.0                    # floor under the board — also guides the pins
POCKET = 1.4                   # pocket depth, < board thickness
PIN_D = 3.2                    # board mounting holes are 3.2 mm
# KiCad top view, from the top-left corner, Y down: H1 (5.5, 69.5), H3 (94.0, 40.0).
# Copper side up: x -> BW - x, and Y up: y -> BH - y.
PINS = [(BW - x, BH - y) for x, y in [(5.5, 69.5), (94.0, 40.0)]]
RELIEF_D = 2.0                 # pocket corner reliefs
PUSH_D = 12.0                  # push-out holes
PUSH = [(33, 37.5), (67, 37.5)]

PX0 = PY0 = BORDER             # pocket corner
PW, PH = BW + 2 * GAP, BH + 2 * GAP
BX0, BY0 = PX0 + GAP, PY0 + GAP  # board corner
W, H, T = PW + 2 * BORDER, PH + 2 * BORDER, FLOOR + POCKET


def cyl(x, y, d, z0=-1, h=None):
    return Part.makeCylinder(d / 2, (h or T + 2), V(x, y, z0))


def build():
    jig = Part.makeBox(W, H, T)
    cut = [Part.makeBox(PW, PH, POCKET + 1, V(PX0, PY0, FLOOR))]
    cut += [cyl(x, y, RELIEF_D, FLOOR) for x in (PX0, PX0 + PW) for y in (PY0, PY0 + PH)]
    cut += [cyl(BX0 + x, BY0 + y, PIN_D) for x, y in PINS]
    cut += [cyl(BX0 + x, BY0 + y, PUSH_D) for x, y in PUSH]
    return jig.cut(Part.makeCompound(cut)).removeSplitter()


doc = App.newDocument("MaskJig") if "MaskJig" not in App.listDocuments() else App.getDocument("MaskJig")
for o in doc.Objects:
    doc.removeObject(o.Name)
shape = build()
obj = doc.addObject("Part::Feature", "Jig")
obj.Shape = shape
doc.recompute()
shape.exportStep(os.path.join(OUT, "Mask_jig.step"))
shape.exportStl(os.path.join(OUT, "Mask_jig.stl"))
print("Jig %.1f x %.1f x %.1f mm, pocket %.1f x %.1f x %.1f, pins at %s, valid=%s, volume=%.0f mm3"
      % (W, H, T, PW, PH, POCKET, PINS, shape.isValid(), shape.Volume))
