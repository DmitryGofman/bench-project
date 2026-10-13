"""Folding bench P2 — every timber part as a build123d solid, in its own frame.

Source: geometry-P2.json, exported from the app (the same side profiles the 3D
view, the sweep and the cut list use). Each part is its side profile extruded
by its thickness, rotated so its longest straight edge lies along +X, with its
lower-left corner at the origin, and with its bores cut:

  pivot A / B   Ø22 bore for the 18/22 bushing, Ø35 counterbore
                (10 deep on the bolt-head member, 15 deep on the nut member)
  lock pin      Ø12.5 through
  M8 laps       Ø9 through, Ø24 × 12 counterbore on the outer face

Run `python parts.py` to print a summary; drawings.py imports PARTS.
"""
import json
import math
from pathlib import Path

from build123d import Align, Box, Cylinder, Location, Polygon, Pos, extrude

HERE = Path(__file__).parent
G = json.loads((HERE / "geometry-P2.json").read_text())
T = 38.0  # board thickness, mm

# which parts each hole goes through, and the counterbore on that member
PIVOT_A, PIVOT_B = tuple(G["A0"]), tuple(G["B"])
PIN = G["pin"]
M8 = [(m["y"], m["z"], m["joint"]) for m in G["marks"] if m["k"] == "m8"]
HOLES = {
    "F1": [("pivot", PIVOT_A, 10), ("pin", tuple(PIN["F1_hole"]), 0)],
    "T1": [("pivot", PIVOT_A, 15), ("pin", tuple(PIN["T1_table"]), 0), ("pin", tuple(PIN["T1_bench"]), 0)]
          + [("m8", (y, z), 12) for y, z, j in M8],
    "T2": [("pivot", PIVOT_B, 10)] + [("m8", (y, z), 12) for y, z, j in M8 if j == "J14"],
    "R3": [("pivot", PIVOT_B, 15)],
    "T4": [("m8", (y, z), 12) for y, z, j in M8 if j == "J20"],
}
BORE = {"pivot": (22.0, 35.0), "pin": (12.5, None), "m8": (9.0, 24.0)}


def hull(pts):
    pts = sorted(set(pts))
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def frame(poly):
    """Minimum-area bounding rectangle: its long side becomes +X, lower-left corner the origin."""
    h = hull(poly); best = None
    for i in range(len(h)):
        a, b = h[i], h[(i + 1) % len(h)]
        ang = -math.atan2(b[1] - a[1], b[0] - a[0])
        ca, sa = math.cos(ang), math.sin(ang)
        r = [(q[0]*ca - q[1]*sa, q[0]*sa + q[1]*ca) for q in h]
        w = max(q[0] for q in r) - min(q[0] for q in r); t = max(q[1] for q in r) - min(q[1] for q in r)
        if t > w: ang += math.pi/2; w, t = t, w
        if best is None or w*t < best[0] - 1e-6: best = (w*t, ang)
    ang = best[1]; ca, sa = math.cos(ang), math.sin(ang)
    rot = lambda q: (q[0]*ca - q[1]*sa, q[0]*sa + q[1]*ca)
    r = [rot(q) for q in poly]
    x0 = min(q[0] for q in r); y0 = min(q[1] for q in r)
    return lambda q: (rot(q)[0] - x0, rot(q)[1] - y0)


def straight_corners(poly, min_len=12.0):
    """Corners where two straight edges meet — also through a rounded-off corner:
    the virtual sharp corner is where the two edge lines intersect (that is the saw cut)."""
    n = len(poly); edges = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if math.hypot(b[0]-a[0], b[1]-a[1]) >= min_len: edges.append((a, b))
    out = []
    for k in range(len(edges)):
        (a1, b1), (a2, b2) = edges[k - 1], edges[k]
        d1 = (b1[0]-a1[0], b1[1]-a1[1]); d2 = (b2[0]-a2[0], b2[1]-a2[1])
        den = d1[0]*d2[1] - d1[1]*d2[0]
        if abs(den) < 1e-9: continue
        t = ((a2[0]-a1[0])*d2[1] - (a2[1]-a1[1])*d2[0]) / den
        X = (a1[0] + t*d1[0], a1[1] + t*d1[1])
        if math.hypot(X[0]-b1[0], X[1]-b1[1]) > 40 or math.hypot(X[0]-a2[0], X[1]-a2[1]) > 40: continue  # across an arc end
        u = (a1[0]-X[0], a1[1]-X[1]); v = (b2[0]-X[0], b2[1]-X[1])
        ang = math.degrees(math.acos(max(-1, min(1, (u[0]*v[0]+u[1]*v[1])/(math.hypot(*u)*math.hypot(*v))))))
        out.append((a1, X, b2, ang))
    return out


def ccw(pts):
    A = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if A > 0 else pts[::-1]


class Part:
    def __init__(self, src, qty):
        self.id, self.name, self.qty = src["id"], src["name"], qty
        self.blank = round(src["blank"] + src.get("cutAdj", 0))
        self.board = src["side"] == "C"
        poly = [tuple(q) for q in src["poly"]]
        if self.board:   # a board: its profile is the section; the drawing shows its length
            L = src["blank"] + (G["L"] - 1520)
            poly = [(0, 0), (L, 0), (L, 89.0), (0, 89.0)]
        tf = frame(poly)
        self.outline = ccw([tf(q) for q in poly])
        self.holes = [(kind, tf(c), cb) for kind, c, cb in HOLES.get(self.id, [])]
        xs = [q[0] for q in self.outline]; ys = [q[1] for q in self.outline]
        self.size = (max(xs) - min(xs), max(ys) - min(ys))
        solid = extrude(Polygon(*self.outline, align=None), amount=T)
        for kind, (hx, hy), cb in self.holes:
            d, dcb = BORE[kind]
            solid -= Pos(hx, hy, T / 2) * Cylinder(d / 2, T + 2)
            if dcb and cb:
                solid -= Pos(hx, hy, T - cb / 2 + 0.01) * Cylinder(dcb / 2, cb)
        self.solid = solid

    def angles(self):
        """Interior angles at the cut corners that are not square: (leg point, corner, leg point, degrees)."""
        return [c for c in straight_corners(self.outline) if abs(c[3] - 90) > 0.5 and abs(c[3] - 180) > 1]

    def length(self):
        return self.size[0]


def build():
    seen, parts = {}, []
    for src in G["parts"]:
        if src.get("ext"):
            continue
        key = src["id"]
        if key in seen:
            seen[key].qty += 1 if src["side"] == "C" else 0
            continue
        qty = 2 if src["side"] != "C" else 1
        seen[key] = Part(src, qty)
        parts.append(seen[key])
    for p in parts:   # boards: count instances, extensions included
        if p.id in ("S2", "S3", "S4"):
            p.qty = sum(1 for s in G["parts"] if s["id"] == p.id)
            p.blank = round(p.blank + (G["L"] - 1520))
    return parts


PARTS = build()

if __name__ == "__main__":
    for p in PARTS:
        print(f"{p.id:3} ×{p.qty}  {p.name:34} cut {p.blank:5} len {round(p.length()):5}  {p.size[0]:6.1f} × {p.size[1]:5.1f}  "
              f"holes {len(p.holes)}  angles {[round(a[3], 1) for a in p.angles()]}")
