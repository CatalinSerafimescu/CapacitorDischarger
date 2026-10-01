"""Generate simple true-size 3D bodies (STEP) for the CapDis footprints that have no stock model.

Needs CadQuery (pip install cadquery). The STEP files are committed in CapDis.3dshapes/, so this
only has to be re-run when a part changes. Coordinates are footprint-local in mm: x right,
y up (KiCad model space: y = -footprint y), z up from the board's top surface.

Dimensions are from the datasheets (see gen_footprints.py); heights marked VERIFY are estimates.
"""
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "CapDis.3dshapes")

GREEN = cq.Color(0.20, 0.45, 0.30)
SILVER = cq.Color(0.80, 0.80, 0.82)
WHITE = cq.Color(0.93, 0.92, 0.88)
CREAM = cq.Color(0.85, 0.80, 0.65)     # silicone-coated wirewound
BLUE = cq.Color(0.25, 0.45, 0.75)      # FMP300 metal film
DARK = cq.Color(0.15, 0.15, 0.15)
LEAD = 0.9                             # lead diameter for the drawings


def cyl_x(x0, x1, y, z, r):
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def cyl_z(x, y, z0, z1, r):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def save(name, parts):
    a = cq.Assembly(name=name)
    for i, (shape, color) in enumerate(parts):
        a.add(shape, name=f"p{i}", color=color)
    a.save(os.path.join(OUT, name + ".step"))
    print("wrote", name)


def flat_axial(name, L, D, P, standoff, color, lead=LEAD):
    """Axial body lying flat, leads bent down into pads 1 (x=0) and 2 (x=P)."""
    r, z = D / 2, standoff + D / 2
    x0 = (P - L) / 2
    save(name, [(cyl_x(x0, x0 + L, 0, z, r), color),
                (cyl_x(0, x0, 0, z, lead / 2).union(cyl_x(x0 + L, P, 0, z, lead / 2))
                 .union(cyl_z(0, 0, -3, z, lead / 2)).union(cyl_z(P, 0, -3, z, lead / 2)), SILVER)])


def standing_axial(name, L, D, P, standoff, color, body_x=0.0, lead=LEAD):
    """Axial body standing on the pad at body_x; the top lead bends over and down to the other pad."""
    other = P if body_x == 0 else 0.0
    top = standoff + L + 1.5
    wire = (cyl_z(body_x, 0, -3, top, lead / 2)
            .union(cyl_x(min(body_x, other), max(body_x, other), 0, top, lead / 2))
            .union(cyl_z(other, 0, -3, top, lead / 2)))
    save(name, [(cyl_z(body_x, 0, standoff, standoff + L, D / 2), color), (wire, SILVER)])


def main():
    os.makedirs(OUT, exist_ok=True)

    # power resistors, flat (2-layer board) and standing (single-sided board), 3 mm standoff
    flat_axial("R_Axial_Ohmite_45F_5W", 23.8, 8.7, 30.48, 3.0, CREAM, 1.02)
    flat_axial("R_Axial_Ohmite_27J_7W", 32.1, 10.0, 40.64, 3.0, CREAM, 0.81)
    standing_axial("R_Axial_Ohmite_45F_5W_Vertical", 23.8, 8.7, 10.16, 3.0, CREAM, lead=1.02)
    standing_axial("R_Axial_Ohmite_27J_7W_Vertical", 32.1, 10.0, 10.16, 3.0, CREAM, lead=0.81)
    # thermal cutoff: flat at R_fast's axis height (8 mm) so it lies against it; standing 5 mm up
    flat_axial("ThermalCutoff_SEFUSE_SF_Axial", 8.5, 4.0, 22.86, 6.0, SILVER, 1.0)
    standing_axial("ThermalCutoff_SEFUSE_SF_Vertical", 8.5, 4.0, 10.16, 5.0, SILVER, lead=1.0)
    # FMP300 3 W standing (R1, R5)
    standing_axial("R_Axial_DIN0516_L15.5mm_D5.0mm_P10.16mm_Vertical", 15.5, 5.0, 10.16, 1.0, BLUE, lead=0.8)
    standing_axial("R_Axial_DIN0516_L15.5mm_D5.0mm_P10.16mm_Vertical_BodyOnPad2", 15.5, 5.0, 10.16, 1.0, BLUE,
                   body_x=10.16, lead=0.8)

    # Phoenix MKDS 5/2-9,5: 19.05 x 12.5 x 21.5 mm body, wire entry towards footprint -Y (model +Y)
    body = box(-4.765, 14.285, -4.6, 7.9, 0, 21.5)
    for x in (0, 9.52):
        body = body.cut(box(x - 2.6, x + 2.6, 4.5, 8.0, 3.0, 9.0))            # wire entries
        body = body.cut(cyl_z(x, 1.5, 17.5, 21.6, 2.8))                       # screw wells
    screws = cyl_z(0, 1.5, 15.5, 18.5, 2.5).union(cyl_z(9.52, 1.5, 15.5, 18.5, 2.5))
    pins = box(-0.45, 0.45, -0.45, 0.45, -5, 0).union(box(9.07, 9.97, -0.45, 0.45, -5, 0))
    save("TerminalBlock_Phoenix_MKDS-5-2-9.5_1x02_P9.52mm", [(body, GREEN), (screws.union(pins), SILVER)])

    # Schurter CSO clips (12 x 13.8 x 20.7 mm) at x = ±15 + 10.3 x 38 mm fuse (axis height VERIFY)
    clips = None
    for cx in (-15, 15):
        c = (box(cx - 6, cx + 6, -6.9, -6.3, 0, 20.7).union(box(cx - 6, cx + 6, 6.3, 6.9, 0, 20.7))
             .union(box(cx - 6, cx + 6, -6.9, 6.9, 0, 1.0)))
        for px in (cx - 7.5, cx + 7.5):
            c = c.union(box(px - 1.0, px + 1.0, -0.4, 0.4, -4.1, 1.0))
        clips = c if clips is None else clips.union(c)
    zf = 13.0
    fuse_body = cyl_x(-9, 9, 0, zf, 5.15)
    caps = cyl_x(-19, -9, 0, zf, 5.15).union(cyl_x(9, 19, 0, zf, 5.15))
    save("Fuseholder_Clip-10.3x38mm_Schurter_CSO_0751.0506", [(clips.union(caps), SILVER), (fuse_body, WHITE)])

    # Stonecold HS-S01 U heatsink on Q2's tab (footprint TO-220 spread: tab towards -Y = model +Y)
    back = box(-6.6, 6.6, 3.6, 4.6, 3.0, 22.05)
    wings = box(-6.6, -5.6, 3.6, 9.95, 3.0, 22.05).union(box(5.6, 6.6, 3.6, 9.95, 3.0, 22.05))
    save("Heatsink_Stonecold_HS-S01_on_TO-220", [(back.union(wings), DARK)])


if __name__ == "__main__":
    main()
