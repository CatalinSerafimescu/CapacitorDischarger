"""Place the board and the panel parts into the "CapDis_Enclosure" document (run gen_enclosure.py first) and
report collisions / clearances.

Run inside the FreeCAD GUI (Python console or MCP execute_code):
    exec(open(r"<repo>/mechanical/enclosure/assembly.py", encoding="utf-8").read())
Board: KiCAD/fab_1s/CapacitorDischarger_1S.step (kicad-cli export). DC jack: the SursaTensiune model of the same
part. Banana sockets (Stäubli SLB4-G), the PM-128 and the 5 mm LED are simple stand-ins drawn from their datasheets.
"""
import os

import FreeCAD as App
import Part

V, Rot, Pl = App.Vector, App.Rotation, App.Placement
E = os.path.dirname(os.path.abspath(globals().get("__file__", "")))
if not os.path.exists(os.path.join(E, "assembly.py")):
    E = r"E:\Catalin\Work\Electronics\CapacitorDischarger_Claude\mechanical\enclosure"
REPO = os.path.dirname(os.path.dirname(E))
JACK_STEP = os.path.join(os.path.dirname(REPO), "SursaTensiune", "mechanical", "dc_jack", "DC_jack_5.5x2.1_panel_10A.step")
g = {}
exec(open(os.path.join(E, "gen_enclosure.py"), encoding="utf-8").read().split("# ── Helpers")[0], g)


def socket(x):
    """SLB4-G: Ø14.5 × 2 collar outside, Ø12 insulating body (flat like the hole) 21 mm behind the panel,
    round M12 nut, brass M4 terminal bolt to 36.5 mm, M4 ring lug + crimp barrel (metal) to 46 mm."""
    z = g["SOCK_Z"]
    flat = g["SOCK_FLAT"] - g["SOCK_D"] / 2 - 0.1
    body = Part.makeCylinder(6.0, 21.0, V(x, 0, z), V(0, 1, 0)).common(Part.makeBox(14, 22, 6 + flat, V(x - 7, -0.5, z - 6)))
    collar = Part.makeCylinder(7.25, 2.0, V(x, -2.0, z), V(0, 1, 0))
    nut = Part.makeCylinder(8.0, 4.0, V(x, g["T"], z), V(0, 1, 0))
    insul = collar.fuse([body, nut])
    metal = Part.makeCylinder(2.0, 15.5, V(x, 21.0, z), V(0, 1, 0)).fuse(
        [Part.makeBox(8.0, 18.0, 1.0, V(x - 4.0, 28.0, z + 2.0)),            # ring lug on the bolt, barrel towards J3/J4
         Part.makeCylinder(2.2, 8.0, V(x, 38.0, z + 2.5), V(0, 1, 0))])
    return insul, metal


def led():
    """5 mm LED, flange (Ø5.8 × 1) in the recess behind the front wall, dome out of the panel, legs inside."""
    x, z, y_fl = g["LED_X"], g["LED_Z"], g["T"] - g["LED_FLANGE_T"]
    body = Part.makeCylinder(2.5, 7.6, V(x, y_fl, z), V(0, -1, 0)).fuse(
        Part.makeCylinder(2.9, 1.0, V(x, y_fl, z), V(0, 1, 0)))
    legs = Part.makeBox(3.0, 8.0, 0.5, V(x - 1.5, y_fl + 1.0, z - 0.25))
    return body.fuse(legs)


def meter():
    x0, y0 = g["MET_X"] - g["MET"][0] / 2, g["MET_Y"] - g["MET"][1] / 2
    return Part.makeBox(g["MET"][0], g["MET"][1], g["MET"][2], V(x0, y0, g["ZI"] - g["MET"][2]))


def place(doc_name="CapDis_Enclosure"):
    doc = App.getDocument(doc_name)
    for n in ("Board", "Jack", "Sock_A", "Sock_A_metal", "Sock_B", "Sock_B_metal", "Meter", "LED"):
        if doc.getObject(n):
            doc.removeObject(n)
    board = Part.read(os.path.join(REPO, "KiCAD", "fab_1s", "CapacitorDischarger_1S.step"))
    # kicad-cli: board top-left at (50, -50), top face z = 1.51 → rotate 180° about Z (probe edge to the front)
    bd = doc.addObject("Part::Feature", "Board")
    bd.Shape = board
    bd.Placement = Pl(V(g["BX0"] + 150.0, g["BY0"] - 50.0, g["ZB"]), Rot(V(0, 0, 1), 180))
    j = doc.addObject("Part::Feature", "Jack")
    j.Shape = Part.read(JACK_STEP)
    # model axis y, Ø13.8 flange ends at y = 1.8 → turned to +X, flange on the left face (X = 0), body into the box
    j.Placement = Pl(V(-1.8, g["JACK_Y"], g["JACK_Z"]), Rot(V(0, 0, 1), -90))
    for name, x in (("Sock_A", g["SOCK_A_X"]), ("Sock_B", g["SOCK_B_X"])):
        ins, met = socket(x)
        doc.addObject("Part::Feature", name).Shape = ins
        doc.addObject("Part::Feature", name + "_metal").Shape = met
    doc.addObject("Part::Feature", "Meter").Shape = meter()
    doc.addObject("Part::Feature", "LED").Shape = led()
    doc.recompute()
    if App.GuiUp:
        bd.ViewObject.ShapeColor = (0.10, 0.45, 0.20)
        j.ViewObject.ShapeColor = (0.6, 0.6, 0.6)
        doc.getObject("Sock_A").ViewObject.ShapeColor = (0.1, 0.6, 0.2)
        doc.getObject("Sock_B").ViewObject.ShapeColor = (0.1, 0.1, 0.1)
        for n in ("Sock_A_metal", "Sock_B_metal"):
            doc.getObject(n).ViewObject.ShapeColor = (0.85, 0.7, 0.3)
        doc.getObject("Meter").ViewObject.ShapeColor = (0.15, 0.15, 0.15)
        doc.getObject("LED").ViewObject.ShapeColor = (0.9, 0.1, 0.1)
    return doc


def check(doc):
    """Overlap volumes between the printed parts and everything else, and a few HV clearances."""
    base, cover = doc.getObject("Base").Shape, doc.getObject("Cover").Shape
    parts = {n: doc.getObject(n).Shape for n in ("Board", "Jack", "Sock_A", "Sock_A_metal", "Sock_B", "Sock_B_metal", "Meter", "LED")}
    print("base ∩ cover: %.2f mm³" % base.common(cover).Volume)
    for pn, ps in (("Base", base), ("Cover", cover)):
        for n, s in parts.items():
            if not ps.BoundBox.intersect(s.BoundBox):
                continue
            hits = [so for so in s.Solids if so.BoundBox.intersect(ps.BoundBox) and ps.common(so).Volume > 0.01]
            for so in hits:
                b = so.BoundBox
                print("  %s ∩ %s solid at X %.1f…%.1f Y %.1f…%.1f Z %.1f…%.1f: %.2f mm³"
                      % (pn, n, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, ps.common(so).Volume))
    m = parts["Meter"]
    for n in ("Sock_A_metal", "Sock_B_metal", "Jack"):
        print("meter ↔ %s: %.1f mm" % (n, m.distToShape(parts[n])[0]))
    print("socket A ↔ socket B metal: %.1f mm" % parts["Sock_A_metal"].distToShape(parts["Sock_B_metal"])[0])
    print("socket B ↔ jack: %.1f mm" % parts["Sock_B_metal"].distToShape(parts["Jack"])[0])
    print("LED ↔ meter: %.1f mm, LED ↔ base (excl. its hole): see overlaps above" % parts["LED"].distToShape(m)[0])
    bb = parts["Board"].BoundBox
    print("board top part Z %.1f, cover inner top Z %.1f" % (bb.ZMax, g["ZI"]))


doc = place()
check(doc)
