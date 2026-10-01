"""Generate the project footprint library CapDis.pretty (parts with no stock KiCad footprint).

Dimensions come from the manufacturer datasheets (see the descr of each footprint).
Values marked VERIFY are inferred, so check them against the real part before ordering the PCB.

    python gen_footprints.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "CapDis.pretty")
M3D = "${KICAD10_3DMODEL_DIR}"


def f(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


def text(kind, val, x, y, layer, hide=False):
    h = "\n\t\t(hide yes)" if hide else ""
    tag = f'(property "{kind}" "{val}"' if kind != "user" else f'(fp_text user "{val}"'
    return (f'\t{tag}\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(layer "{layer}"){h}\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)')


def line(x1, y1, x2, y2, layer, w=0.12, dash=False):
    t = "dash" if dash else "solid"
    return (f'\t(fp_line\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n\t\t(stroke\n'
            f'\t\t\t(width {w})\n\t\t\t(type {t})\n\t\t)\n\t\t(layer "{layer}")\n\t)')


def rect(x1, y1, x2, y2, layer, w=0.12, dash=False):
    t = "dash" if dash else "solid"
    return (f'\t(fp_rect\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n\t\t(stroke\n'
            f'\t\t\t(width {w})\n\t\t\t(type {t})\n\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t)')


def circle(x, y, r, layer, w=0.12):
    return (f'\t(fp_circle\n\t\t(center {f(x)} {f(y)})\n\t\t(end {f(x + r)} {f(y)})\n\t\t(stroke\n'
            f'\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t)')


def pad(num, x, y, size, drill, shape="circle"):
    sx, sy = size if isinstance(size, tuple) else (size, size)
    return (f'\t(pad "{num}" thru_hole {shape}\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(sx)} {f(sy)})\n'
            f'\t\t(drill {f(drill)})\n\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t)')


def npth(x, y, d):
    return (f'\t(pad "" np_thru_hole circle\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(d)} {f(d)})\n'
            f'\t\t(drill {f(d)})\n\t\t(layers "*.Cu" "*.Mask")\n\t)')


def model(path, offset=(0, 0, 0), rot=(0, 0, 0)):
    o = " ".join(f(v) for v in offset)
    r = " ".join(f(v) for v in rot)
    return (f'\t(model "{path}"\n\t\t(offset\n\t\t\t(xyz {o})\n\t\t)\n\t\t(scale\n\t\t\t(xyz 1 1 1)\n'
            f'\t\t)\n\t\t(rotate\n\t\t\t(xyz {r})\n\t\t)\n\t)')


def footprint(name, descr, items, ref_at, val_at, mdl=None):
    # our own true-size body from gen_3d.py takes precedence over a stock stand-in
    if os.path.exists(os.path.join(HERE, "CapDis.3dshapes", name + ".step")):
        mdl = model("${KIPRJMOD}/CapDis.3dshapes/" + name + ".step")
    body = "\n".join(items)
    m = ("\n" + mdl) if mdl else ""
    s = (f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "gen_footprints.py")\n'
         f'\t(layer "F.Cu")\n\t(descr "{descr}")\n'
         + text("Reference", "REF**", *ref_at, "F.SilkS") + "\n"
         + text("Value", name, *val_at, "F.Fab") + "\n"
         + f'\t(attr through_hole)\n\t(duplicate_pad_numbers_are_jumpers no)\n{body}\n'
         + text("user", "${REFERENCE}", *ref_at, "F.Fab") + f"\n\t(embedded_fonts no){m}\n)\n")
    open(os.path.join(LIB, name + ".kicad_mod"), "w", encoding="utf8", newline="\n").write(s)


def axial(name, descr, L, D, P, drill, padd, mdl=None, crt=None):
    """crt: courtyard half-height (default: body radius + 0.5 mm)."""
    x0 = (P - L) / 2
    cy = crt if crt is not None else D / 2 + 0.5
    items = [rect(x0, -D / 2, x0 + L, D / 2, "F.SilkS"),
             line(padd / 2 + 0.3, 0, x0, 0, "F.SilkS"), line(P - padd / 2 - 0.3, 0, x0 + L, 0, "F.SilkS"),
             rect(x0, -D / 2, x0 + L, D / 2, "F.Fab", 0.1),
             rect(-padd / 2 - 0.5, -cy, P + padd / 2 + 0.5, cy, "F.CrtYd", 0.05),
             pad(1, 0, 0, padd, drill), pad(2, P, 0, padd, drill)]
    footprint(name, descr, items, (P / 2, 0), (P / 2, D / 2 + 1.5), mdl)  # ref inside the body outline


def vertical(name, descr, D, P, drill, padd, mdl=None, body_pad=1, margin=0.5):
    """Axial part standing on pad `body_pad` (body circle around it), other lead bent down."""
    bx = 0 if body_pad == 1 else P
    ox = P if body_pad == 1 else 0
    items = [circle(bx, 0, D / 2, "F.SilkS"), circle(bx, 0, D / 2, "F.Fab", 0.1),
             line(bx + (D / 2 if ox > bx else -D / 2), 0, ox - (padd / 2 + 0.3) * (1 if ox > bx else -1), 0, "F.SilkS"),
             rect(min(bx - D / 2, ox - padd / 2) - margin, -D / 2 - margin, max(bx + D / 2, ox + padd / 2) + margin,
                  D / 2 + margin, "F.CrtYd", 0.05),
             pad(1, 0, 0, padd, drill), pad(2, P, 0, padd, drill)]
    footprint(name, descr, items, (bx, -D / 2 - 1.2), (bx, D / 2 + 1.2), mdl)


def main():
    os.makedirs(LIB, exist_ok=True)

    # ── standing versions for the compact single-sided board ──
    vertical("R_Axial_Ohmite_45F_5W_Vertical",
             "Ohmite 45F 5 W wirewound standing on pad 1 (body ø8.7 x 23.8 mm), pitch 10.16 mm. "
             "Keep ≥3 mm between the body and the board.", 8.7, 10.16, 1.4, 2.8,
             model(f"{M3D}/Resistor_THT.3dshapes/R_Axial_Power_L25.0mm_W9.0mm_P10.16mm_Vertical.step"))
    vertical("R_Axial_Ohmite_27J_7W_Vertical",
             "Ohmite 27J 7 W wirewound standing on pad 1 (body ø10 x 32.1 mm), pitch 10.16 mm. "
             "Keep ≥3 mm between the body and the board.", 10.0, 10.16, 1.1, 2.4, margin=0.25)
    vertical("ThermalCutoff_SEFUSE_SF_Vertical",
             "SCHOTT SEFUSE SF/R thermal cutoff standing (body ø4 x 8.5 mm), pitch 10.16 mm "
             "(600 V can appear across it once open). Solder ≥5 mm from the body.", 4.0, 10.16, 1.3, 2.4,
             margin=0.25)  # tight: it is clamped against R_fast1
    vertical("R_Axial_DIN0516_L15.5mm_D5.0mm_P10.16mm_Vertical",
             "Yageo FMP300 3 W standing on pad 1 (body ø5 x 15.5 mm), pitch 10.16 mm for 600 V across the pads.",
             5.0, 10.16, 1.0, 2.4,
             model(f"{M3D}/Resistor_THT.3dshapes/R_Axial_DIN0516_L15.5mm_D5.0mm_P5.08mm_Vertical.step"))
    vertical("R_Axial_DIN0516_L15.5mm_D5.0mm_P10.16mm_Vertical_BodyOnPad2",
             "Yageo FMP300 3 W standing on pad 2 (body ø5 x 15.5 mm), pitch 10.16 mm; pad 1 is the bare "
             "high-voltage lead, so the body stays on the low-voltage side of the slot.",
             5.0, 10.16, 1.0, 2.4, body_pad=2)

    # Ohmite 40 Series 45F: body 23.8 × ø8.7 mm, leads 18 AWG (1.02 mm)
    axial("R_Axial_Ohmite_45F_5W",
          "Ohmite 40 Series 5 W wirewound (45F...), body 23.8x8.7 mm, lead 1.02 mm, pitch 30.48 mm. "
          "Mount ≥3 mm off the board. https://www.ohmite.com/res-40/",
          23.8, 8.7, 30.48, 1.4, 2.8,
          model(f"{M3D}/Resistor_THT.3dshapes/R_Axial_Power_L25.0mm_W9.0mm_P30.48mm.step"))
    # Ohmite 20 Series 27J: body 32.1 × ø10.0 mm max, leads 20 AWG (0.81 mm)
    axial("R_Axial_Ohmite_27J_7W",
          "Ohmite 20 Series 7 W wirewound (27J...), body 32.1x10 mm max, lead 0.81 mm, pitch 40.64 mm. "
          "Mount ≥3 mm off the board. https://www.ohmite.com/res-20/",
          32.1, 10.0, 40.64, 1.1, 2.4,
          model(f"{M3D}/Resistor_THT.3dshapes/R_Axial_Power_L38.0mm_W9.0mm_P40.64mm.step"))
    # SEFUSE SF/R: body 8.5 × ø4.0 mm, leads ø1.0; bend ≥3 mm and solder ≥5 mm from the body
    axial("ThermalCutoff_SEFUSE_SF_Axial",
          "SCHOTT SEFUSE SF/R thermal cutoff (SF129R0), body 8.5x4 mm, lead 1.0 mm, pitch 22.86 mm "
          "(solder ≥5 mm from body). Case is live (lead B). https://www.schott.com/sefuse",
          8.5, 4.0, 22.86, 1.3, 2.4, crt=2.4)  # tight: TF1 lies 1 mm from the R_fast body

    # Schurter CSO 0751.0506: 2 pins per clip at ±7.5 mm from clip centre, ø2.35 holes,
    # ø3.4 centre hole, clip centres 30 mm apart for 10.3×38 fuses. Clip 12 × 13.8 mm.
    items = []
    for sign, num in ((-1, 1), (1, 2)):
        cx = sign * 15
        # both pins and the centre hole share one copper bar: the clip is one conductor
        items += [pad(num, cx - 7.5, 0, 3.8, 2.35), pad(num, cx + 7.5, 0, 3.8, 2.35),
                  pad(num, cx, 0, (18.8, 4.4), 3.4, "rect"),
                  line(cx - 6, -6.9, cx + 6, -6.9, "F.SilkS"), line(cx - 6, 6.9, cx + 6, 6.9, "F.SilkS"),
                  rect(cx - 6, -6.9, cx + 6, 6.9, "F.Fab", 0.1)]
    items += [rect(-19, -5.15, 19, 5.15, "F.Fab", 0.1, dash=True),
              line(-4.5, 0, 4.5, 0, "F.SilkS"),
              rect(-24.9, -7.4, 24.9, 7.4, "F.CrtYd", 0.05)]
    footprint("Fuseholder_Clip-10.3x38mm_Schurter_CSO_0751.0506",
              "2x Schurter CSO 0751.0506 PCB fuse clips for a 10.3x38 mm cartridge (F1). Pins ø2.35 mm at "
              "±7.5 mm from each clip centre, clip centres 30 mm apart. https://www.schurter.com/en/datasheet/typ_CSO.pdf",
              items, (0, -8.6), (0, 8.6))

    # Phoenix MKDS 5/2-9,5 (1714971): pitch 9.52, pins 0.9 × 0.9 mm (drill 1.3), body 19.05 × 12.5;
    # pin row 4.6 mm from the rear face. Wire entry faces -Y.
    x0, x1 = -4.765, 9.52 + 4.765
    items = [pad(1, 0, 0, 3.0, 1.4, "rect"), pad(2, 9.52, 0, 3.0, 1.4),
             rect(x0, -7.9, x1, 4.6, "F.SilkS"), rect(x0, -7.9, x1, 4.6, "F.Fab", 0.1),
             line(x0, -6.4, x1, -6.4, "F.SilkS"),
             rect(x0 - 0.5, -8.4, x1 + 0.5, 5.1, "F.CrtYd", 0.05)]
    footprint("TerminalBlock_Phoenix_MKDS-5-2-9.5_1x02_P9.52mm",
              "Phoenix Contact MKDS 5/ 2-9,5 (1714971) 2-pole PCB terminal block, pitch 9.52 mm, 1000 V / 32 A, "
              "wire entry towards -Y. VERIFY which face the pin row is 4.6 mm from. "
              "https://www.phoenixcontact.com/en-pc/products/pcb-terminal-block-mkds-5-2-95-1714971",
              items, (4.76, -9.4), (4.76, 6.4))

    # STP10NK80Z in TO-220, standing, with the outer legs bent out to a 5.08 mm pitch
    # (2.9 mm copper gap between drain and gate/source instead of 0.6 mm).
    items = [pad(1, -5.08, 0, (2.2, 3.0), 1.2, "rect"), pad(2, 0, 0, (2.2, 3.0), 1.2, "oval"),
             pad(3, 5.08, 0, (2.2, 3.0), 1.2, "oval"),
             rect(-6.4, -3.26, 6.4, -1.88, "F.SilkS"),
             rect(-5.08, -3.26, 5.08, 1.36, "F.Fab", 0.1),
             rect(-6.7, -3.3, 6.7, 2.0, "F.CrtYd", 0.05)]  # tab edge: sits against the heatsink
    footprint("TO-220-3_Vertical_LegsSpread_P5.08mm",
              "TO-220-3 vertical, tab towards -Y, legs bent out to 5.08 mm pitch for HV spacing (G-D-S).",
              items, (0, -5), (0, 3.5),
              model(f"{M3D}/Package_TO_SOT_THT.3dshapes/TO-220-3_Vertical.step", (-2.54, 0, 0)) + "\n"
              + model("${KIPRJMOD}/CapDis.3dshapes/Heatsink_Stonecold_HS-S01_on_TO-220.step"))

    # Wakefield 647-10ABEP: 41.9 × 25.4 mm footprint, 25.4 mm tall, 2 solder pins ø2.4 mm on 25.4 mm
    # centres. Origin = heatsink centre; the TO-220 mounts on the -Y face.
    items = [pad(1, -12.7, 0, 4.0, 2.7), pad(2, 12.7, 0, 4.0, 2.7),
             rect(-20.95, -12.7, 20.95, 12.7, "F.SilkS"), rect(-20.95, -12.7, 20.95, 12.7, "F.Fab", 0.1),
             rect(-21.45, -12.7, 21.45, 12.7, "F.CrtYd", 0.05)]  # = body: Q2 touches the -Y face
    footprint("Heatsink_Wakefield_647-10ABEP_TO-220",
              "Wakefield 647-10ABEP TO-220 board-level heatsink, 41.9x25.4x25.4 mm, 2 pins ø2.4 on 25.4 mm. "
              "VERIFY pin axis and mounting-face side against the real part. Pins tied to GND. "
              "https://wakefieldthermal.com/content/data_sheets/647%20(1).pdf",
              items, (0, -14.5), (0, 14.5))
    print("footprints written to", LIB)


if __name__ == "__main__":
    main()
