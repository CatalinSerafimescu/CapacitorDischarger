"""1:1 films for the single-sided board, A4 portrait, both images at the top of the page (rest of the sheet reusable).

    python gen_films.py        (needs PyMuPDF: pip install pymupdf)

Writes, in fab_1s/:
  1S_films_1to1.pdf
    page 1  B.Cu POSITIVE | B.Cu NEGATIVE   — toner transfer / photoresist (use whichever your process needs)
    page 2  B.Cu POSITIVE | B.Mask          — B.Mask: black = pad openings, the film for UV-cured solder mask
  1S_copper_components_1to1.pdf  B.Cu POSITIVE | components (F.Fab + F.SilkS) MIRRORED — both for toner transfer
  1S_solder_mask_1to1.pdf        B.Mask | B.Mask — two copies, stacked for a denser UV exposure film
The bottom-side images (B.Cu, B.Mask) are seen from the component side (not mirrored), so the print goes toner
side down on the copper. The components image is mirrored, so it reads correctly once transferred onto the
component side and lines up with the copper through the board. Two 100 mm boards don't fit side by side on 210 mm with printer margins, so both are turned
90° (75 x 100 mm); same rotation on every image, so positive and mask stay matched.
"""
import os
import subprocess
import tempfile

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
PCB = os.path.join(HERE, "CapacitorDischarger_1S.kicad_pcb")
FAB = os.path.join(HERE, "fab_1s")

MM = 72 / 25.4
OX, OY, BW, BH = 50.0, 50.0, 100.0, 75.0   # board outline on the KiCad plot page (gen_pcb.OX/OY, board_1s.W/H)
M = 1.0                                     # crop margin around the outline
TOP, LEFT, GAP = 12.0, 20.0, 16.0           # placement on A4 portrait, mm

PLOTS = {   # name: extra kicad-cli args
    "pos":  ["-l", "B.Cu,Edge.Cuts", "--drill-shape-opt", "1"],                # small drill marks centre the drill
    "neg":  ["-l", "B.Cu,Edge.Cuts", "--drill-shape-opt", "1", "--negative"],
    "mask": ["-l", "B.Mask,Edge.Cuts", "--drill-shape-opt", "0"],
    "comp": ["-l", "F.Fab,F.Silkscreen,Edge.Cuts", "--mirror"],              # mirrored for transfer onto the top
}
POS, MASK = ("pos", "B.Cu POSITIVE (black = copper)"), ("mask", "B.Mask (black = pad openings)")
COMP = ("comp", "Components F.Fab + F.SilkS, MIRRORED (transfer onto the component side)")
FILES = {   # file: pages, each page = images left to right
    "1S_films_1to1.pdf": [[POS, ("neg", "B.Cu NEGATIVE (white = copper)")], [POS, MASK]],
    "1S_copper_components_1to1.pdf": [[POS, COMP]],
    "1S_solder_mask_1to1.pdf": [[MASK, MASK]],
}


def plot(tmp, name, args):
    path = os.path.join(tmp, name + ".pdf")
    subprocess.run([CLI, "pcb", "export", "pdf", "--mode-single", "--black-and-white", *args, "-o", path, PCB],
                   check=True, capture_output=True)
    with open(path, "rb") as f:                # in memory: an open file would block the temp-dir cleanup
        return pymupdf.open("pdf", f.read())


def main():
    with tempfile.TemporaryDirectory() as tmp:
        src = {n: plot(tmp, n, a) for n, a in PLOTS.items()}
        w, h = BH + 2 * M, BW + 2 * M          # turned 90°
        os.makedirs(FAB, exist_ok=True)
        for fname, pages in FILES.items():
            doc = pymupdf.open()
            for n, items in enumerate(pages, 1):
                page = doc.new_page(width=210 * MM, height=297 * MM)
                for i, (name, label) in enumerate(items):
                    x0 = LEFT + i * (w + GAP)
                    r = pymupdf.Rect(x0, TOP, x0 + w, TOP + h) * MM
                    ox = OX
                    if "--mirror" in PLOTS[name]:   # kicad-cli mirrors about the plot page's vertical centre line
                        ox = src[name][0].rect.width / MM - OX - BW
                    clip = pymupdf.Rect(ox - M, OY - M, ox + BW + M, OY + BH + M) * MM
                    page.show_pdf_page(r, src[name], 0, clip=clip, rotate=90)
                    page.insert_text(pymupdf.Point(x0, TOP + h + 4) * MM, label, fontsize=7)
                page.insert_text(pymupdf.Point(LEFT, TOP + h + 9) * MM,
                                 f"CapacitorDischarger_1S  {fname[:-4]}  page {n}  -  print at 100 % (no fit to page), "
                                 f"no extra mirroring. Board {BW:.0f} x {BH:.0f} mm: check with a ruler. Toner side down.",
                                 fontsize=6)
            out = os.path.join(FAB, fname)
            doc.save(out)
            print("wrote", out)


if __name__ == "__main__":
    main()
