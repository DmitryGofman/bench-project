"""Mini (1:5) printable version of the folding picnic bench P1 Rev 2.

    python3 build_mini.py              # writes step/, stl/, parts.csv next to this file
    python3 build_mini.py --width 304  # true 1:5 width (boards 304 mm: needs a big bed)

Source geometry: folding_p1_data.json (the FOLDING_P1 object that app/index.html embeds,
generated from the full-size design). Profile polygons are in the Y-Z plane in the TABLE
pose (fold = 0), floor at Z = 0, extruded along X.

What is scaled and what is not
  * Y / Z (depth, height, member sections, mechanism geometry): exactly 1:5.
  * X (width across the bench): reduced so the boards fit a ~220 mm bed. The mechanism is
    planar, so width does not change how it folds. --width sets the overall board length.
  * Layer gaps in X (0.6 mm) are the full-size 3 mm gaps / 5.
  * Hardware is re-chosen for the scale (M3 pivots, 2 mm lock pin, 1.75 mm filament pegs).

Requires: build123d, shapely, trimesh, numpy.
"""
import argparse, csv, itertools, json, math, os
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from build123d import (BuildLine, BuildSketch, BuildPart, Polyline, ThreePointArc, Line, make_face,
                       extrude, Plane, Axis, Pos, Rot, Cylinder, Compound, Color, Location, Vector,
                       export_step, export_stl, Mode, Align, fillet, Solid, Part)

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--width', type=float, default=190.0, help='overall board length S4, mm (mini scale)')
ap.add_argument('--scale', type=float, default=0.2)
ap.add_argument('--out', default=HERE)
ap.add_argument('--verify', action='store_true', help='also run a 3D solid interference sweep (slow)')
args = ap.parse_args()

S = args.scale
F = json.load(open(os.path.join(HERE, 'folding_p1_data.json')))
B, A0, L0 = F['B'], F['A0'], F['L0']
D = (args.width / S - L0) / 2.0          # full-size-units x shift of every part (as the app's d)

# ---------------- hardware / feature sizes (mini mm) ----------------
BOLT_HOLE = 3.4          # M3 clearance
HEAD_BORE, HEAD_DEPTH = 6.6, 3.4     # M3 cap head 5.5 x 3.0, flush
NUT_BORE, NUT_DEPTH = 6.8, 4.4       # M3 nyloc 5.5 AF x 4.0
PIN_HOLE = 2.2           # 2 mm rod / 1.75 mm filament lock pin
PEG_HOLE, PEG_DEPTH = 2.0, 3.5       # 1.75 mm filament pegs (glue registration)
ROUND_R3 = 1.2           # full-size R6 on the R3 front-top corner (S2 slides over it)

# ---------------- helpers ----------------
def rot2(p, c, deg):
    a = math.radians(deg); x = p[0]-c[0]; y = p[1]-c[1]
    return [c[0]+x*math.cos(a)-y*math.sin(a), c[1]+x*math.sin(a)+y*math.cos(a)]

PARTS = F['parts']
for p in PARTS:
    p['key'] = p['tag']                                  # R1-R, S2-1 ...
ID2PART = {}
for p in PARTS:
    ID2PART.setdefault(p['id'], p)
    ID2PART[p['tag']] = p

def round_corner(poly, idx, r):
    """replace vertex idx of a convex polygon with a fillet arc (as polyline points)."""
    n = len(poly); P = np.array(poly[idx]); a = np.array(poly[idx-1]); b = np.array(poly[(idx+1) % n])
    u = (a-P)/np.linalg.norm(a-P); v = (b-P)/np.linalg.norm(b-P)
    ang = math.acos(np.clip(u@v, -1, 1)); t = r/math.tan(ang/2)
    p1 = P+u*t; p2 = P+v*t; bis = (u+v); bis /= np.linalg.norm(bis)
    c = P+bis*(r/math.sin(ang/2))
    a1 = math.atan2(*(p1-c)[::-1]); a2 = math.atan2(*(p2-c)[::-1])
    da = (a2-a1+math.pi) % (2*math.pi)-math.pi
    pts = [list(c+r*np.array([math.cos(a1+da*k/8), math.sin(a1+da*k/8)])) for k in range(9)]
    return poly[:idx]+pts+poly[idx+1:]

def profile_wire_points(p):
    """scaled polygon; keep the pivot-end arcs of F1 / T2 as true arcs. -> list of segments."""
    poly = [[q[0]*S, q[1]*S] for q in p['poly']]
    centre = {'F1': A0, 'T2': B}.get(p['id'])
    if centre is None:
        return poly, None
    c = [centre[0]*S, centre[1]*S]; R = 44.5*S
    on = [abs(math.hypot(q[0]-c[0], q[1]-c[1])-R) < 0.02 for q in poly]
    n = len(poly)
    # find contiguous cyclic run of True
    start = next(i for i in range(n) if on[i] and not on[i-1])
    run = []; i = start
    while on[i % n]:
        run.append(i % n); i += 1
        if len(run) == n: break
    return poly, (run[0], run[len(run)//2], run[-1])

def prism(p, x0, x1, poly_override=None):
    """solid for part p between x0,x1 (full-size x, shifted by D already), mini mm."""
    poly, arc = profile_wire_points(p)
    if poly_override is not None:
        poly, arc = poly_override, None
    pl = Plane.YZ.offset(x0*S)
    with BuildPart() as bp:
        with BuildSketch(pl):
            with BuildLine():
                n = len(poly)
                if arc is None:
                    Polyline(*[tuple(q) for q in poly], close=True)
                else:
                    a0, am, a1 = arc
                    # arc a0..a1 (cyclic run) ; straight remainder a1 -> ... -> a0
                    ThreePointArc(tuple(poly[a0]), tuple(poly[am]), tuple(poly[a1]))
                    rest = []
                    i = (a1+1) % n
                    while i != a0:
                        rest.append(poly[i]); i = (i+1) % n
                    Polyline(tuple(poly[a1]), *[tuple(q) for q in rest], tuple(poly[a0]))
            make_face()
        extrude(amount=(x1-x0)*S)
    return bp.part

# ---------------- holes: described as cylinders in table-pose world coordinates ----------------
class Hole:
    def __init__(s, c0, axis, length, dia, kind):
        s.c0 = np.array(c0, float); s.axis = np.array(axis, float); s.len = length; s.r = dia/2; s.kind = kind
    @property
    def c1(s): return s.c0 + s.axis*s.len
    def solid(s):
        # cylinder along axis from c0, length len
        cyl = Cylinder(s.r, s.len, align=(Align.CENTER, Align.CENTER, Align.MIN))
        ax = tuple(s.axis)
        if ax == (1, 0, 0): cyl = Rot(0, 90, 0)*cyl
        elif ax == (-1, 0, 0): cyl = Rot(0, -90, 0)*cyl
        elif ax == (0, 0, -1): cyl = Rot(180, 0, 0)*cyl
        return Pos(*s.c0)*cyl

def seg_dist(a0, a1, b0, b1):
    d1 = a1-a0; d2 = b1-b0; r = a0-b0
    a = d1@d1; e = d2@d2; f = d2@r; c = d1@r; b = d1@d2; den = a*e-b*b
    s = np.clip((b*f-c*e)/den, 0, 1) if den > 1e-12 else 0.0
    t = (b*s+f)/e
    if t < 0: t = 0; s = np.clip(-c/a, 0, 1)
    elif t > 1: t = 1; s = np.clip((b-c)/a, 0, 1)
    return np.linalg.norm((a0+d1*s)-(b0+d2*t))

HOLES = {}        # key -> list[Hole]   key = (tag, side)  side in 'R','L','C'
def add_hole(tag, side, h): HOLES.setdefault((tag, side), []).append(h)

def xspan(p, side):
    """x0,x1 in full-size units (shifted), for side R / L / C."""
    if p['side'] == 'C': return p['x0']-D, p['x1']+D
    a, b = p['x0']+D, p['x1']+D
    return (a, b) if side == 'R' else (-b, -a)

def inside_part(p, side, h, margin):
    """does the hole (cylinder) stay inside the part with a wall margin? mini mm."""
    poly = Polygon([(q[0]*S, q[1]*S) for q in p['poly']])
    x0, x1 = [v*S for v in xspan(p, side)]
    c0, c1 = h.c0, h.c1
    if abs(h.axis[0]) > .5:        # X hole: (y,z) point inside poly
        return poly.buffer(-margin).contains(Point(c0[1], c0[2]))
    # vertical hole: segment in y,z must lie inside poly with margin; x inside x-range
    if not (x0+margin <= c0[0] <= x1-margin): return False
    # only the part of the hole that is inside the part (skip the 0.5 lead-in)
    e0 = c0 + h.axis*0.5
    seg = LineString([(e0[1], e0[2]), (c1[1], c1[2])])
    return poly.buffer(1e-6).contains(seg.buffer(h.r+margin-0.2, cap_style='flat'))

def place_x_holes(p, side, y, z, dia, face, depth, kind):
    """X-axis hole at (y,z) (full-size) entering from face 'x0'/'x1' (or through) of part p."""
    x0, x1 = [v*S for v in xspan(p, side)]
    yy, zz = y*S, z*S
    if depth is None:                                  # through
        h = Hole((x0-0.5, yy, zz), (1, 0, 0), (x1-x0)+1.0, dia, kind)
    elif face == 'x0':
        h = Hole((x0-0.5, yy, zz), (1, 0, 0), depth+0.5, dia, kind)
    else:
        h = Hole((x1+0.5, yy, zz), (-1, 0, 0), depth+0.5, dia, kind)
    add_hole(p['key'], side, h)

def other_face(p, side, towards_x):
    pass

# --- 1. structural holes -----------------------------------------------------------------
def by(tag): return next(p for p in PARTS if p['key'] == tag)
SIDES = ('R', 'L')
def outer_face(side):  return 'x1' if side == 'R' else 'x0'      # face away from bench centre
def inner_face(side):  return 'x0' if side == 'R' else 'x1'      # face towards bench centre

for side in SIDES:
    # pivot A: F1 (head, outer face) <-> T1 (nut, inner face)
    place_x_holes(by('F1-R'), side, A0[0], A0[1], BOLT_HOLE, None, None, 'pivot')
    place_x_holes(by('F1-R'), side, A0[0], A0[1], HEAD_BORE, outer_face(side), HEAD_DEPTH, 'bore')
    place_x_holes(by('T1-R'), side, A0[0], A0[1], BOLT_HOLE, None, None, 'pivot')
    place_x_holes(by('T1-R'), side, A0[0], A0[1], NUT_BORE, inner_face(side), NUT_DEPTH, 'bore')
    # pivot B: T2 (head, outer face = towards the front frame) <-> R3 (nut, inner face)
    place_x_holes(by('T2-R'), side, B[0], B[1], BOLT_HOLE, None, None, 'pivot')
    place_x_holes(by('T2-R'), side, B[0], B[1], HEAD_BORE, outer_face(side), HEAD_DEPTH, 'bore')
    place_x_holes(by('R3-R'), side, B[0], B[1], BOLT_HOLE, None, None, 'pivot')
    place_x_holes(by('R3-R'), side, B[0], B[1], NUT_BORE, inner_face(side), NUT_DEPTH, 'bore')
    # lock pin: one hole in F1, two in T1 (table / bench)
    pf = F['validation']['pin']
    place_x_holes(by('F1-R'), side, *pf['F1_hole'], PIN_HOLE, None, None, 'pin')
    place_x_holes(by('T1-R'), side, *pf['T1_table'], PIN_HOLE, None, None, 'pin')
    place_x_holes(by('T1-R'), side, *pf['T1_bench'], PIN_HOLE, None, None, 'pin')

# --- 2. glue-registration pegs from the screw / bolt positions of every joint ---------------------
dropped = []
def conflicts(key, h, margin=0.8):
    for o in HOLES.get(key, []):
        if seg_dist(h.c0, h.c1, o.c0, o.c1) < h.r+o.r+margin: return True
    return False

joints = {j['id']: j for j in F['joints']}
peg_count = {}
for m in F['marks']:
    if m['k'] not in ('screw', 'm8', 'boardscrew') or not m['joint']: continue
    j = joints[m['joint']]
    pa, pb = ID2PART[j['a']], ID2PART[j['b']]
    for side in SIDES:
        sx = 1 if side == 'R' else -1
        placed = []
        for p in (pa, pb):
            ps = 'C' if p['side'] == 'C' else side
            if m['k'] == 'boardscrew':
                # vertical peg: board bottom is the contact; bearer top is the contact
                xm = sx*(m['x']+D)*S
                board = pa if pa['side'] == 'C' else pb
                zc = min(q[1] for q in board['poly'])*S
                if p is board: h = Hole((xm, m['y']*S, zc-0.5), (0, 0, 1), PEG_DEPTH+0.5, PEG_HOLE, 'peg')
                else:          h = Hole((xm, m['y']*S, zc+0.5), (0, 0, -1), PEG_DEPTH+0.5, PEG_HOLE, 'peg')
            else:
                # contact plane between the two layers
                if abs(pa['x1']-pb['x0']) < 1e-6: xc = pa['x1']
                elif abs(pa['x0']-pb['x1']) < 1e-6: xc = pa['x0']
                else: raise SystemExit('no contact plane '+j['id'])
                xc = sx*(xc+D)*S
                lo = (p['x0'] + D)*S if side == 'R' else -(p['x1']+D)*S       # part's x range
                hi = (p['x1'] + D)*S if side == 'R' else -(p['x0']+D)*S
                if abs(xc-lo) < 1e-6: h = Hole((xc-0.5, m['y']*S, m['z']*S), (1, 0, 0), PEG_DEPTH+0.5, PEG_HOLE, 'peg')
                else:                  h = Hole((xc+0.5, m['y']*S, m['z']*S), (-1, 0, 0), PEG_DEPTH+0.5, PEG_HOLE, 'peg')
            ok = inside_part(p, ps, h, 0.8) and not conflicts((p['key'], ps), h)
            placed.append((p, ps, h, ok))
        # a peg is only useful if it fits in BOTH parts
        if all(o for *_, o in placed):
            for p, ps, h, _ in placed: add_hole(p['key'], ps, h)
            peg_count[(j['id'], side)] = peg_count.get((j['id'], side), 0)+1
        else:
            dropped.append((m['joint'], side, round(m['y'], 1), round(m['z'], 1)))
# T2 contact with T1 face: pegs only on the T1/T2 face (J14) and T1/T4, T1/T5 – done above.

# ---------------- build part solids ----------------
def make_part(p, side):
    x0, x1 = xspan(p, side)
    poly_override = None
    if p['id'] == 'R3':                                     # round the front-top corner (S2 slides over it)
        poly = [[q[0]*S, q[1]*S] for q in p['poly']]
        idx = next(i for i, q in enumerate(p['poly']) if abs(q[0]+44.5) < 1e-6 and abs(q[1]-412) < 1e-6)
        poly_override = round_corner(poly, idx, ROUND_R3)
    solid = prism(p, x0, x1, poly_override)
    for h in HOLES.get((p['key'], side), []):
        solid = solid - h.solid()
    return solid

class Body:
    pass
BODIES = []
for p in PARTS:
    for side in (SIDES if p['side'] == 'R' else ('C',)):
        b = Body(); b.p = p; b.side = side
        b.name = p['tag'] if side == 'C' else p['id']+'_'+side
        b.solid = make_part(p, side)
        BODIES.append(b)

# ---------------- hardware bodies (visual / hole-check only) ----------------
HW = []
def hw_cyl(name, r, x0, x1, y, z, asm, color):
    c = Cylinder(r, abs(x1-x0), align=(Align.CENTER, Align.CENTER, Align.CENTER))
    c = Pos((x0+x1)/2, y, z)*(Rot(0, 90, 0)*c)
    HW.append(dict(name=name, solid=c, asm=asm, color=color))
for side in SIDES:
    sx = 1 if side == 'R' else -1
    def X(v): return sx*(v+D)*S
    # pivot A bolt: head outer face of F1 (x1=710) -> nut in T1 (x0=631)
    ya, za = A0[0]*S, A0[1]*S
    hw_cyl(f'Pivot A bolt {side} shank', 1.5, X(710)-sx*HEAD_DEPTH, X(631)+sx*(NUT_DEPTH-0.4), ya, za, 'front', Color(0.15, 0.15, 0.17))
    hw_cyl(f'Pivot A bolt {side} head', 2.75, X(710)-sx*HEAD_DEPTH, X(710), ya, za, 'front', Color(0.15, 0.15, 0.17))
    yb, zb = B[0]*S, B[1]*S
    hw_cyl(f'Pivot B bolt {side} shank', 1.5, X(631)-sx*HEAD_DEPTH, X(552)+sx*(NUT_DEPTH-0.4), yb, zb, 'top', Color(0.15, 0.15, 0.17))
    hw_cyl(f'Pivot B bolt {side} head', 2.75, X(631)-sx*HEAD_DEPTH, X(631), yb, zb, 'top', Color(0.15, 0.15, 0.17))
    pin = F['validation']['pin']['F1_hole']
    hw_cyl(f'Lock pin {side}', 1.0, X(710)+sx*4, X(631)-sx*1, pin[0]*S, pin[1]*S, 'front', Color(0.25, 0.47, 0.92))
    HW[-1]['pin_dx'] = sx*18          # pulled-out offset used between the end stops

# ---------------- poses ----------------
H = F['handsoff']
def phi_of(th):
    i = 0
    while i < len(H)-2 and H[i+1][0] > th: i += 1
    a, b = H[i], H[i+1]
    f = 0 if a[0] == b[0] else (th-a[0])/(b[0]-a[0])
    return a[1]+f*(b[1]-a[1])

def pulled(h, fold, solid):
    """lock pins are engaged only at the two end stops; pull them out while folding"""
    if 'pin_dx' in h and 0 < fold < 100: return solid.moved(Location((h['pin_dx'], 0, 0)))
    return solid

def posed(solid, asm, th, phi):
    if th == 0 and phi == 0: return solid
    cB = Axis((0, B[0]*S, B[1]*S), (1, 0, 0)); cA = Axis((0, A0[0]*S, A0[1]*S), (1, 0, 0))
    if asm == 'rear': return solid
    if asm == 'top': return solid.rotate(cB, th)
    A = rot2(A0, B, th); dA = (A[0]-A0[0], A[1]-A0[1])
    return (solid.rotate(cA, phi)).move(Location((0, dA[0]*S, dA[1]*S)))

COLORS = {'rail': Color(0.80, 0.62, 0.40), 'slat': Color(0.86, 0.73, 0.52), 'stop': Color(0.86, 0.50, 0.20)}
def assembly(fold):
    th = -fold; phi = phi_of(th)
    groups = {'rear': [], 'front': [], 'top': [], 'hardware': []}
    for b in BODIES:
        s = posed(b.solid, b.p['asm'], th, phi)
        s = s.moved(Location((0, 0, 0)))
        s.label = b.name
        s.color = COLORS[b.p['g']]
        groups[b.p['asm']].append(s)
    for h in HW:
        s = posed(pulled(h, fold, h['solid']), h['asm'], th, phi); s.label = h['name']; s.color = h['color']
        groups['hardware'].append(s)
    top = []
    for k, title in (('rear', 'Rear frame (fixed)'), ('front', 'Front frame (swings on A)'),
                     ('top', 'Table-back frame (swings on B)'), ('hardware', 'Hardware')):
        c = Compound(children=groups[k], label=title); top.append(c)
    return Compound(children=top, label=f'Mini folding bench P1 - fold {fold} deg')

# ---------------- outputs ----------------
out = args.out
for d in ('step', 'stl/parts', 'stl/assembly'): os.makedirs(os.path.join(out, d), exist_ok=True)

for fold, nm in ((0, 'table'), (50, 'mid-fold-50deg'), (100, 'bench')):
    asm = assembly(fold)
    export_step(asm, os.path.join(out, 'step', f'mini-bench-P1-{nm}.step'))
    print('wrote step', nm)

# one body per timber part for printing, laid flat
rows = []
seen = set()
for b in BODIES:
    p = b.p
    s = b.solid
    thick = abs(xspan(p, b.side)[1]-xspan(p, b.side)[0])*S
    bb = s.bounding_box()
    plate = thick < min(bb.size.Y, bb.size.Z)      # side plate: extrusion axis (X) -> print Z
    # plates: extrusion axis X becomes print-Z, i.e. (x,y,z)->(y,z,x) = -120 deg about (1,1,1);
    # boards already lie flat (long X, thin Z).
    s2 = s.rotate(Axis((0, 0, 0), (1, 1, 1)), -120) if plate else s
    bb2 = s2.bounding_box()
    s2 = s2.moved(Location((-bb2.min.X, -bb2.min.Y, -bb2.min.Z)))
    fn = f'{b.name}.stl'
    export_stl(s2, os.path.join(out, 'stl', 'parts', fn), tolerance=0.005, angular_tolerance=0.1)
    bb3 = s2.bounding_box()
    rows.append([b.name, p['name'], p['g'], b.side, round(bb3.size.X, 1), round(bb3.size.Y, 1), round(bb3.size.Z, 1), round(s.volume, 0)])

with open(os.path.join(out, 'parts.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['file', 'part', 'group', 'side', 'X_mm', 'Y_mm', 'Z_mm', 'volume_mm3']); w.writerows(rows)

print('parts', len(BODIES), 'dropped pegs', len(dropped))
for d in dropped: print('  dropped', d)
print('pegs per joint/side', dict(sorted(peg_count.items())))

# ---------------- optional: 3D interference sweep, hands-off front seat ----------------
if args.verify:
    ITEMS = [(b.name, b.solid, b.p['asm'], 'part', None) for b in BODIES] + [(h['name'], h['solid'], h['asm'], 'hw', h) for h in HW]
    worst = {}
    for fold in range(0, 101, 5):
        th = -fold; phi = phi_of(th)
        P = [(n, posed(pulled(h, fold, s) if h else s, a, th, phi), a, k) for n, s, a, k, h in ITEMS]
        BB = [s.bounding_box() for _, s, _, _ in P]
        for i, j in itertools.combinations(range(len(P)), 2):
            (n1, s1, a1, k1), (n2, s2, a2, k2) = P[i], P[j]
            if a1 == a2 and not (k1 != k2 and False): continue       # rigid assemblies move together
            b1, b2 = BB[i], BB[j]
            if (b1.max.X < b2.min.X or b2.max.X < b1.min.X or b1.max.Y < b2.min.Y or b2.max.Y < b1.min.Y
                    or b1.max.Z < b2.min.Z or b2.max.Z < b1.min.Z): continue
            v = (s1 & s2).volume
            if v > 0.05:
                key = (n1, n2); worst[key] = max(worst.get(key, 0), v)
                print(f'  fold {fold:3d}: {n1} x {n2}: {v:.2f} mm3')
    print('3D sweep done; interfering pairs:', len(worst))
