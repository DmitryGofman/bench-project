"""Folding bench P2 — production drawings: one A3 sheet per distinct timber part.

Every view, dimension, angle and hole callout is projected from the part solids
in parts.py (which come from the app's geometry export), so re-exporting the
geometry and re-running this script updates the whole set.

    MPLCONFIGDIR=/tmp/mpl uvx --no-config --managed-python --python 3.13 \
        --from cadgen==0.7.21 python drawings.py
"""
from cadgen.eng_drawing import Sheet, eng_drawing

from parts import BORE, PARTS, T

MATERIAL = "PINE 38×89 PLANED, PRESSURE-TREATED"


def end_angles(angles):
    """An end cut makes two corners that add up to 180°: dimension only the acute one
    (the other follows), so the two labels never print over each other."""
    keep = []
    for i, c in enumerate(angles):
        twin = [d for j, d in enumerate(angles) if j != i and abs(c[3] + d[3] - 180) < 1.0
                and ((c[1][0] - d[1][0]) ** 2 + (c[1][1] - d[1][1]) ** 2) ** 0.5 < 130]
        if twin and c[3] > 90:
            continue
        keep.append(c)
    return keep


def sheet_for(p, n):
    side = not p.board
    notes = [
        f"QTY {p.qty}" + (" — MAKE A LEFT AND A RIGHT (COUNTERBORES ON OPPOSITE FACES)." if side and p.holes else "."),
        f"CUT FROM 38×89 STOCK, LENGTH {round(p.length())} MM BEFORE ANGLE CUTS." if side else f"CUT TO {p.blank} MM.",
        "ANGLES ARE SAW CUTS BETWEEN THE FACES SHOWN; ROUNDED CORNERS R6–R10 AFTER CUTTING.",
        "BREAK ALL ARRISES R3. SEAL EVERY CUT END AND BORE.",
    ]
    L = p.length()
    scale = 1.0 if L <= 170 else 0.5 if L <= 560 else 0.2 if L <= 1300 else 0.1
    many = len(p.holes) > 2
    if many:   # a hole table keeps a crowded part readable
        for i, (kind, (hx, hy), cb) in enumerate(p.holes):
            d, dcb = BORE[kind]
            notes.append(f"H{i+1}: X {hx:.1f}  Y {hy:.1f}  Ø{d:g} THRU" + (f", CB Ø{dcb:g}×{cb:g}" if dcb and cb else "") +
                         "  (FROM LOWER-LEFT CORNER, TOP VIEW)")
    s = Sheet("A3", scale=scale, title=p.name.upper(), part_number=f"BP2-{p.id}", material=MATERIAL,
              revision="A", author="bench-project", notes=notes)
    top, front, right, iso = s.three_views(p.solid, iso=True, gap=46)
    top.overall()
    # cut angles — every corner that is not square, measured between the two cut faces
    for a, X, b, ang in end_angles(p.angles()):
        top.angle((X[0], X[1], T), (b[0], b[1], T), (a[0], a[1], T))
    # holes: callout + position from the part's left end and bottom edge
    for i, (kind, (hx, hy), cb) in enumerate(p.holes):
        d, dcb = BORE[kind]
        label = ("H%d " % (i + 1) if many else "") + {"pivot": "PIVOT BUSH", "pin": "LOCK PIN", "m8": "M8"}[kind]
        ang = 45 if hy >= 44.5 else -45          # callouts to the right, clear of the frame
        if many:   # the hole table carries the spec; tag each hole where it is
            top.note("H%d" % (i + 1), (hx, hy, T), offset=(5, 6 if hy >= 44.5 else -6))
            continue
        if dcb and cb:
            top.hole((hx, hy, T), d, thru=True, cbore=(dcb, cb), label=label, angle=ang)
        else:
            top.hole((hx, hy, T), d, thru=True, label=label, angle=ang)
        if not many:
            top.dim((0, 0, T), (hx, hy, T), orientation="h")
            top.dim((0, 0, T), (hx, hy, T), orientation="v")
    front.overall()
    return s


@eng_drawing(out="PDF/bench-P2-part-drawings.pdf")
def bench_parts():
    return [sheet_for(p, i) for i, p in enumerate(PARTS)]


if __name__ == "__main__":
    print(bench_parts())
