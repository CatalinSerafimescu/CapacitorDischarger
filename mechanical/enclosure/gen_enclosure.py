"""Parametric 3D-printable enclosure for the single-sided discharger board (CapacitorDischarger_1S, 100 × 75).

Run inside the FreeCAD GUI (Python console or MCP):
    exec(open(r"<repo>/mechanical/enclosure/gen_enclosure.py", encoding="utf-8").read())
Creates document "CapDis_Enclosure" with objects Base and Cover, and exports
Enclosure_base / Enclosure_cover as .step and .stl next to this script.

Coordinates (mm): X = left→right seen from the front, Y = front→back, Z = up.
Origin = front-left-bottom outer corner. The board lies rotated 180° (its probe edge, KiCad y = 0, faces the
front): KiCad (x, y) → (BX0 + 100 − x, BY0 + y), see bxy().

Parts
- Base  = open box: floor + all 4 walls. Board on 2 screwed standoffs (H1, H3) + 4 support posts + 3 snap hooks,
          banana sockets and DC jack in the front wall. Everything is reachable from the top.
- Cover = top plate with the PM-128 meter, LED light pipe and baffled vents; lip inside the walls,
          4 × M3 screws into heat-set inserts (a tool is needed to open it — HV inside).
Print: Base floor-down; Cover upside-down (top on the bed). No slicer supports.
"""
import math
import os

import FreeCAD as App
import Part

V = App.Vector
HERE = os.path.dirname(os.path.abspath(globals().get("__file__", "")))
if not os.path.exists(os.path.join(HERE, "gen_enclosure.py")):
    HERE = r"E:\Catalin\Work\Electronics\CapacitorDischarger_Claude\mechanical\enclosure"

# ── Board (KiCAD/CapacitorDischarger_1S.kicad_pcb) ───────────────────────────
BOARD_W, BOARD_D, BOARD_T = 100.0, 75.0, 1.5
T = 2.4                          # wall / floor / top thickness
SIDE_GAP, REAR_GAP = 1.0, 3.0    # board edge ↔ inner wall (rear: room for the rear snap hook to flex)
FRONT_GAP = 50.0                 # inner front wall ↔ board front edge: banana sockets (36.5 deep) + ring lugs,
                                 # straight into the MKDS wire entries; the meter sits above them
BX0, BY0 = T + SIDE_GAP, T + FRONT_GAP
STANDOFF_H = 6.0                 # floor ↔ board bottom (HV copper is on the bottom: trim leads ≤ 3 mm)
ZB = T + STANDOFF_H              # board bottom
ZT = ZB + BOARD_T                # board top (component side)


def bxy(x, y):
    """KiCad board coordinates (mm from the top-left corner) → enclosure X, Y."""
    return BX0 + BOARD_W - x, BY0 + y


# ── Main dimensions ───────────────────────────────────────────────────────────
W = BOARD_W + 2 * (T + SIDE_GAP)            # 106.8
D = BY0 + BOARD_D + REAR_GAP + T            # 132.8
H = 52.0                                    # R_fast1 top = board + 37.1 → 47.0; inner top 49.6
R = 6.0                          # vertical corner radius
CT, CB = 3.0, 1.2                # top-edge chamfer, bottom chamfer (bed)
ZS = H - CT                      # base / cover split, where the top chamfer starts
ZI = H - T                       # inner face of the top

# ── Front wall: banana sockets in line with the J3 / J4 inner wire entries, DC jack ─
SOCK_Z = 15.0                    # MKDS wire entries are at board top + 3…9 → Z 12.9…18.9
SOCK_A_X = bxy(17.52, 0)[0]      # J3 (PROBE_A) pin at x 17.52 → green socket J1, "+"
SOCK_B_X = bxy(38.02, 0)[0]      # J4 (PROBE_B) pin at x 38.02 → black socket J2, "−"   (20.5 mm apart)
SOCK_D, SOCK_FLAT = 12.2, 11.0   # Stäubli SLB4-G: Ø12.1+0.1 hole with a flat, 11.0+0.1 across (anti-rotation);
                                 # flat on top (short bridge when printing)
# danger LED (LED1, 5 mm) on a 2-wire cable to J6 (XH): pushed in from inside, flange in a recess, glued.
# Top-left of the front, between the front-left boss (X ≤ 10.4) and the meter (X ≥ 18.4).
LED_X, LED_Z = 14.0, 38.0
LED_D, LED_FLANGE_D, LED_FLANGE_T = 5.1, 6.1, 1.0

# ── Left wall: 9 V input jack + warning ──────────────────────────────────────
# Panel DC jack 5.5×2.1, M12 body (as on SursaTensiune); in the front gap, below the meter (body X 2.4…19)
JACK_Y, JACK_Z, JACK_D = 28.0, SOCK_Z, 12.2
WARN = [("9 V DC IN   + centre", 5.0), ("FLOATING SUPPLY ONLY", 4.2),
        ("9 V battery or isolated adapter.", 3.4), ("NEVER an earthed / grounded supply!", 3.4)]
WARN_Y, WARN_Z, WARN_PITCH = 80.0, 36.0, 7.0     # centre of the text block, first baseline, line pitch
WARN_TRI = (JACK_Y, 33.0, 13.0)                  # warning triangle above the jack: Y, Z centre, side

# ── Board fixing ─────────────────────────────────────────────────────────────
BOARD_SCREWS = [bxy(5.5, 69.5), bxy(94.0, 40.0)]       # H1, H3: M3 nylon screws, nuts in hex pockets under the floor
STANDOFF_D = 6.5
SUPPORTS = [bxy(12.76, 3.5), bxy(33.26, 3.5),          # under J3 / J4 (screwdriver force on the terminals)
            bxy(22.5, 40.0), bxy(52.5, 40.0)]          # under the F1 clip centres (pushing the fuse in)
SUPPORT_D = 5.0
# snap hooks on the board edges (normal along Y): (board x of the hook centre, width, edge)
# widths keep the nose off J3's MKDS body (x ≥ 3.2), Q2's heatsink (y ≥ 4) and LED1 (y ≤ 71.2)
HOOKS = [(97.5, 4.0, "front"), (1.6, 3.0, "front"), (97.5, 4.0, "rear")]
HOOK_T, HOOK_GAP = 1.8, 0.2      # post thickness, post ↔ board edge
LEDGE = 1.5                      # ledge under the board (copper-free edge margin is 1.75)
NOSE, NOSE_GAP = 0.8, 0.15       # nose over the board top, play above the board
SIDE_RIBS_Y = (15.0, 60.0)       # board y of the X-locating ribs on both side walls (0.3 mm play)

M3_CLR, M3_NUT_F, M3_NUT_T = 3.4, 5.8, 2.6

# ── Cover: PM-128 meter, vents, lip + 4 screws ───────────────────────────────
MET = (70.0, 40.0, 23.0)         # PM-128 70 × 40, 23 deep behind the panel (MPJA PM128 sheet) — VERIFY on the part
MET_X, MET_Y = W / 2, 27.0       # meter Y 7…47: in front of the board, above the sockets (meter bottom Z 26.6)
MET_WIN = (44.5, 19.7)           # panel cutout = bezel window 1.75 × 0.775 in
MET_HOLE_P, MET_HOLE_D = 57.15, 3.2   # 2 screw holes 0.25 in outside the window ends, on its centre line
# vents above R_slow1-5 (top Z 38.8): 2 mm slots, each over a solid baffle strip 3 mm below the top.
# No straight line passes (strip margin 2.8 > gap·slot/top = 3·2/2.4 = 2.5) — no probe or wire can reach HV.
VENT_X = [bxy(x, 0)[0] for x in (58.0, 47.0, 36.0, 25.0, 14.0)]
VENT_Y = (BY0 + 49.5, BY0 + 66.5)
VENT_W, VENT_GAP, VENT_M, VENT_STRIP_T = 2.0, 3.0, 2.8, 1.2

LIP_GAP, LIP_W, LIP_H = 0.2, 1.6, 3.5    # clearance to the walls, lip width, depth below ZS
BOSS = 8.0                               # screw boss footprint
INS_D, INS_L = 4.0, 6.5                  # M3 heat-set insert (Ø4.0 hole, ≤ 6 mm long); cover screws M3×10
CBORE_D, CBORE_H = 6.2, 3.0              # counterbore for the M3 socket head
# boss centres and the walls each boss hangs from (front-left / front-right / rear-right corners; the
# rear-left one moves along the rear wall to X 20, clear of the LED cable rising from J6 in that corner)
BOSSES = [(T + BOSS / 2, T + BOSS / 2, "xy"), (W - T - BOSS / 2, T + BOSS / 2, "Xy"),
          (W - T - BOSS / 2, D - T - BOSS / 2, "XY"), (20.0, D - T - BOSS / 2, "Y")]


# ── Helpers ───────────────────────────────────────────────────────────────────
def rounded_box(w, d, h, r, ct, cb, origin=V(0, 0, 0)):
    s = Part.makeBox(w, d, h)
    s = s.makeFillet(r, [e for e in s.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > h - 1e-6])
    top = [e for e in s.Edges if all(abs(v.Point.z - h) < 1e-6 for v in e.Vertexes)]
    s = s.makeChamfer(ct, top)
    bot = [e for e in s.Edges if all(abs(v.Point.z) < 1e-6 for v in e.Vertexes)]
    s = s.makeChamfer(cb, bot)
    s.translate(origin)
    return s


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(d, p, axis, length):
    return Part.makeCylinder(d / 2, length, p, axis)


def hex_prism(cx, cy, flats, z0, z1):
    rc = flats / math.sqrt(3)
    pts = [V(cx + rc * math.cos(math.radians(60 * i)), cy + rc * math.sin(math.radians(60 * i)), z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


def rrect(x0, x1, y0, y1, r, z0, z1):     # box with rounded vertical edges
    s = box(x0, x1, y0, y1, z0, z1)
    return s.makeFillet(r, [e for e in s.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6])


def prism_yz(pts, x0, x1):                 # polygon in the YZ plane, extruded along X
    vs = [V(x0, y, z) for y, z in pts]
    return Part.Face(Part.makePolygon(vs + [vs[0]])).extrude(V(x1 - x0, 0, 0))


def d_hole(xc, zc, d, flat, depth):        # round hole through the front wall with a flat on top
    c = cyl(d, V(xc, -1, zc), V(0, 1, 0), depth + 2)
    return c.common(box(xc - d, xc + d, -2, depth + 2, zc - d, zc + flat - d / 2))


def hook(xc, width, edge, side):
    """Snap hook at a board edge (normal along Y): post from the floor, 45° ledge under the board, nose over it.
    side = -1: hook in front of the edge (board towards +Y), +1: behind it."""
    def y(d):                               # d > 0: away from the board
        return edge + side * d
    yi, yo = y(HOOK_GAP), y(HOOK_GAP + HOOK_T)
    zn = ZT + NOSE_GAP
    top = zn + 0.3 + NOSE + HOOK_GAP + 0.6
    pts = [(yo, T - 0.1), (yi, T - 0.1), (yi, ZB - LEDGE - HOOK_GAP), (y(-LEDGE), ZB), (yi, ZB),
           (yi, zn), (y(-NOSE), zn), (y(-NOSE), zn + 0.3), (yi, zn + 0.3 + NOSE + HOOK_GAP), (yi, top), (yo, top)]
    return prism_yz(pts, xc - width / 2, xc + width / 2)


def boss(xc, yc, walls, z0, z1):
    """Screw boss hanging from the walls named in `walls` (x/X = left/right, y/Y = front/rear wall) with a 45°
    underside towards each of them (prints without supports). z0 = where the underside meets the wall."""
    h = BOSS / 2
    s = box(xc - h, xc + h, yc - h, yc + h, z0, z1)
    if "x" in walls:
        s = s.fuse(box(T - 0.3, xc - h, yc - h, yc + h, z0, z1))
    if "X" in walls:
        s = s.fuse(box(xc + h, W - T + 0.3, yc - h, yc + h, z0, z1))
    if "y" in walls:
        s = s.fuse(box(xc - h, xc + h, T - 0.3, yc - h, z0, z1))
    if "Y" in walls:
        s = s.fuse(box(xc - h, xc + h, yc + h, D - T + 0.3, z0, z1))
    big = BOSS + 2
    for w in walls:                            # keep z ≥ z0 + (distance from that wall)
        if w in "xX":
            wx = T - 0.3 if w == "x" else W - T + 0.3
            sgn = 1 if w == "x" else -1
            pts = [V(wx, 0, z0), V(wx + sgn * big, 0, z0 + big), V(wx + sgn * big, 0, z1 + 1), V(wx, 0, z1 + 1)]
            keep = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, D, 0))
        else:
            wy = T - 0.3 if w == "y" else D - T + 0.3
            sgn = 1 if w == "y" else -1
            pts = [V(0, wy, z0), V(0, wy + sgn * big, z0 + big), V(0, wy + sgn * big, z1 + 1), V(0, wy, z1 + 1)]
            keep = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(W, 0, 0))
        s = s.common(keep)
    return s


def text(s, size, font=r"C:\Windows\Fonts\arialbd.ttf"):
    """Flat text faces in the XY plane, centred on the origin; None if unavailable."""
    try:
        wires = Part.makeWireString(s, font, size, 0)
        faces = []
        for ch in wires:
            if ch:
                faces.append(Part.Face(Part.Compound(ch), "Part::FaceMakerBullseye") if len(ch) > 1 else Part.Face(ch[0]))
        if not faces:
            return None
        t = Part.Compound(faces)
        bb = t.BoundBox
        t.translate(V(-bb.Center.x, -bb.Center.y, 0))
        return t
    except Exception as exc:
        print("text skipped:", s, exc)
        return None


def engrave_front(shape, s, x, z, size, depth=0.6):
    t = text(s, size)
    if t is None:
        return shape
    t.rotate(V(0, 0, 0), V(1, 0, 0), 90)            # XY → XZ, readable from the front
    t.translate(V(x, 0, z))
    return shape.cut(t.extrude(V(0, depth, 0)).translated(V(0, -0.01, 0)))


def engrave_left(shape, s, y, z, size, depth=0.6):
    """Engrave text (or ready-made faces centred on the origin, size=None) into the left wall, readable from
    the left side (text runs towards the front, -Y)."""
    t = text(s, size) if size else s
    if t is None:
        return shape
    t.rotate(V(0, 0, 0), V(1, 0, 0), 90)            # XY → XZ
    t.rotate(V(0, 0, 0), V(0, 0, 1), -90)           # text direction → -Y, face normal → -X
    t.translate(V(0, y, z))
    return shape.cut(t.extrude(V(depth, 0, 0)).translated(V(-0.01, 0, 0)))


def warn_triangle(side, stroke=1.0):
    """Warning sign: triangle outline + '!' as faces in the XY plane, centred on the origin."""
    def tri(a, dy=0.0):
        h = a * math.sqrt(3) / 2
        pts = [V(-a / 2, -h / 3 + dy, 0), V(a / 2, -h / 3 + dy, 0), V(0, 2 * h / 3 + dy, 0)]
        return Part.Face(Part.makePolygon(pts + [pts[0]]))
    inner = side - 2 * math.sqrt(3) * stroke                 # same centroid, edges `stroke` inside
    ring = tri(side).cut(tri(inner))
    bang = text("!", side * 0.42)
    if bang is not None:
        bang.translate(V(0, side * 0.04, 0))        # dot clear of the bottom edge
        ring = ring.fuse(bang)
    return ring


def engrave_top(shape, s, x, y, size, depth=0.6):
    t = text(s, size)
    if t is None:
        return shape
    t.translate(V(x, y, H + 0.01))
    return shape.cut(t.extrude(V(0, 0, -depth - 0.01)))


# ── Shell ─────────────────────────────────────────────────────────────────────
outer = rounded_box(W, D, H, R, CT, CB)
k = math.sqrt(2) - 1
inner = rounded_box(W - 2 * T, D - 2 * T, H - 2 * T, R - T, CT - k * T, max(CB - k * T, 0.2), V(T, T, T))
shell = outer.cut(inner)

cuts = [d_hole(SOCK_A_X, SOCK_Z, SOCK_D, SOCK_FLAT, T), d_hole(SOCK_B_X, SOCK_Z, SOCK_D, SOCK_FLAT, T),
        cyl(LED_D, V(LED_X, -1, LED_Z), V(0, 1, 0), T + 2),
        cyl(LED_FLANGE_D, V(LED_X, T - LED_FLANGE_T, LED_Z), V(0, 1, 0), LED_FLANGE_T + 1),
        cyl(JACK_D, V(-1, JACK_Y, JACK_Z), V(1, 0, 0), T + 2)]
# top: meter window + screw holes, light pipe bore, vent slots
cuts.append(box(MET_X - MET_WIN[0] / 2, MET_X + MET_WIN[0] / 2, MET_Y - MET_WIN[1] / 2, MET_Y + MET_WIN[1] / 2,
                ZI - 1, H + 1))
for dx in (-MET_HOLE_P / 2, MET_HOLE_P / 2):
    cuts.append(cyl(MET_HOLE_D, V(MET_X + dx, MET_Y, ZI - 1), V(0, 0, 1), T + 2))
for x in VENT_X:
    cuts.append(box(x - VENT_W / 2, x + VENT_W / 2, VENT_Y[0], VENT_Y[1], ZI - 1, H + 1))
shell = shell.cut(cuts[0].fuse(cuts[1:]))

# ── Split: cover = the chamfered top cap, base = the rest ────────────────────
cover = shell.common(box(-1, W + 1, -1, D + 1, ZS, H + 1))
base = shell.cut(box(-1, W + 1, -1, D + 1, ZS, H + 1)).cut(rrect(T, W - T, T, D - T, R - T, ZS - LIP_H - 1, ZS + 1))
# (the inner top chamfer starts below ZS: walls straight up to the split, so the lip fits)

# ── Base additions ────────────────────────────────────────────────────────────
adds = []
for (x, y) in BOARD_SCREWS:
    adds.append(cyl(STANDOFF_D, V(x, y, T - 0.1), V(0, 0, 1), STANDOFF_H + 0.1))
for (x, y) in SUPPORTS:
    adds.append(cyl(SUPPORT_D, V(x, y, T - 0.1), V(0, 0, 1), STANDOFF_H + 0.1))
for bx, wdt, edge in HOOKS:
    ex = bxy(bx, 0)[0]
    adds.append(hook(ex, wdt, BY0 if edge == "front" else BY0 + BOARD_D, -1 if edge == "front" else 1))
for by in SIDE_RIBS_Y:
    y = bxy(0, by)[1]
    adds.append(box(T - 0.1, BX0 - 0.3, y - 2, y + 2, ZB - 3, ZT + 1.5))
    adds.append(box(BX0 + BOARD_W + 0.3, W - T + 0.1, y - 2, y + 2, ZB - 3, ZT + 1.5))
bz1 = ZS - LIP_H - 0.1                                  # boss top (0.1 under the cover's lip blocks)
bz0 = bz1 - INS_L - 1.5 - BOSS                          # underside meets the walls here
for (x, y, walls) in BOSSES:
    adds.append(boss(x, y, walls, bz0, bz1))
base = base.fuse(adds)
bcuts = []
for (x, y) in BOARD_SCREWS:
    bcuts.append(cyl(M3_CLR, V(x, y, -1), V(0, 0, 1), T + STANDOFF_H + 2))
    bcuts.append(hex_prism(x, y, M3_NUT_F, -1, M3_NUT_T))
for (x, y, _) in BOSSES:
    bcuts.append(cyl(INS_D, V(x, y, bz1 - INS_L), V(0, 0, 1), INS_L + 1))
base = base.cut(bcuts[0].fuse(bcuts[1:]))
base = engrave_front(base, "+", SOCK_A_X + 12.5, SOCK_Z, 7)
base = engrave_front(base, "\u2212", SOCK_B_X - 12.5, SOCK_Z, 7)
base = engrave_front(base, "HV", LED_X + 9.0, LED_Z, 5)
for i, (line, size) in enumerate(WARN):
    base = engrave_left(base, line, WARN_Y, WARN_Z - i * WARN_PITCH, size)
base = engrave_left(base, warn_triangle(WARN_TRI[2]), WARN_TRI[0], WARN_TRI[1], None)

# ── Cover additions: lip, screw blocks, light pipe, vent baffles ─────────────
lz0 = ZS - LIP_H
lip_out = rrect(T + LIP_GAP, W - T - LIP_GAP, T + LIP_GAP, D - T - LIP_GAP, R - T - LIP_GAP, lz0, ZS + 0.1)
lip = lip_out.cut(rrect(T + LIP_GAP + LIP_W, W - T - LIP_GAP - LIP_W, T + LIP_GAP + LIP_W, D - T - LIP_GAP - LIP_W,
                        R - T - LIP_GAP - LIP_W, lz0 - 1, ZS + 1))
cadds = [lip]
for (x, y, _) in BOSSES:
    cadds.append(box(x - BOSS / 2, x + BOSS / 2, y - BOSS / 2, y + BOSS / 2, lz0, ZS + 0.1).common(lip_out))
sz1 = ZI - VENT_GAP
for x in VENT_X:
    hw = VENT_W / 2 + VENT_M
    y0, y1 = VENT_Y[0] - VENT_M, VENT_Y[1] + VENT_M
    cadds.append(box(x - hw, x + hw, y0, y1, sz1 - VENT_STRIP_T, sz1))                 # baffle strip
    cadds.append(box(x - hw, x + hw, y0 - 1.2, y0, sz1 - VENT_STRIP_T, ZI + 0.1))       # end ribs carry it
    cadds.append(box(x - hw, x + hw, y1, y1 + 1.2, sz1 - VENT_STRIP_T, ZI + 0.1))
cover = cover.fuse(cadds)
ccuts = []
for (x, y, _) in BOSSES:
    ccuts.append(cyl(M3_CLR, V(x, y, lz0 - 1), V(0, 0, 1), H))
    ccuts.append(cyl(CBORE_D, V(x, y, H - CBORE_H), V(0, 0, 1), CBORE_H + 1))
cover = cover.cut(ccuts[0].fuse(ccuts[1:]))
cover = engrave_top(cover, "600 V MAX", MET_X, MET_Y + MET[1] / 2 + 6, 5)

base, cover = base.removeSplitter(), cover.removeSplitter()

# ── Document + export ─────────────────────────────────────────────────────────
if "CapDis_Enclosure" in App.listDocuments():
    App.closeDocument("CapDis_Enclosure")
doc = App.newDocument("CapDis_Enclosure")
ob = doc.addObject("Part::Feature", "Base"); ob.Shape = base
oc = doc.addObject("Part::Feature", "Cover"); oc.Shape = cover
doc.recompute()
if App.GuiUp:
    ob.ViewObject.ShapeColor = (0.20, 0.20, 0.22)
    oc.ViewObject.ShapeColor = (0.85, 0.20, 0.10)
    oc.ViewObject.Transparency = 60
    import ImportGui
    ImportGui.export([ob], os.path.join(HERE, "Enclosure_base.step"))
    ImportGui.export([oc], os.path.join(HERE, "Enclosure_cover.step"))
else:
    base.exportStep(os.path.join(HERE, "Enclosure_base.step"))
    cover.exportStep(os.path.join(HERE, "Enclosure_cover.step"))
import MeshPart  # noqa: E402
for name, shp in (("Enclosure_base", base), ("Enclosure_cover", cover)):
    MeshPart.meshFromShape(Shape=shp, LinearDeflection=0.05, AngularDeflection=0.2).write(os.path.join(HERE, name + ".stl"))
print("W×D×H %.1f × %.1f × %.1f" % (W, D, H))
print("Base valid", base.isValid(), "vol %.0f" % base.Volume, "| Cover valid", cover.isValid(), "vol %.0f" % cover.Volume)
