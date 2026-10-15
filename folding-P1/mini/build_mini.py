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
import trimesh
from shapely.geometry import Polygon, Point, LineString, MultiPoint
from shapely.ops import unary_union
from build123d import (BuildLine, BuildSketch, BuildPart, Polyline, ThreePointArc, Line, make_face,
                       extrude, Plane, Axis, Pos, Rot, Cylinder, Box, Compound, Color, Location, Vector,
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
GROOVE_DEPTH = 0.8        # plank-line grooves on the panels (cosmetic)
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
def add_hole(key, h): HOLES.setdefault(key, []).append(h)

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
    add_hole((p['asm'], side), h)

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

# --- 2. each rigid side frame is ONE printed part (members fused); planks become one panel per group --------------
def conflicts(key, h, margin=0.8):
    for o in HOLES.get(key, []):
        if seg_dist(h.c0, h.c1, o.c0, o.c1) < h.r+o.r+margin: return True
    return False

FRAMES = {'rear': 'Rear-frame', 'front': 'Front-frame', 'top': 'Table-frame'}
PANELS = {'S2': ('Seat-panel-front', 'front'), 'S3': ('Seat-panel-rear', 'rear'), 'S4': ('Table-panel', 'top')}
FUSE_ALL = {'rear': 'Rear-assembly', 'front': 'Front-assembly'}   # both sides + seat panel = ONE print
PANEL_PEGS = 2                    # pegs per panel end and side (planks are not individually registered)
joints = {j['id']: j for j in F['joints']}

def panel_geometry(pid):
    planks = [p for p in PARTS if p['id'] == pid]
    y0 = min(min(q[0] for q in p['poly']) for p in planks); y1 = max(max(q[0] for q in p['poly']) for p in planks)
    z0 = min(min(q[1] for q in p['poly']) for p in planks); z1 = max(max(q[1] for q in p['poly']) for p in planks)
    gaps = []
    ps = sorted(planks, key=lambda p: min(q[0] for q in p['poly']))
    for p, q in zip(ps, ps[1:]):
        gaps.append((max(v[0] for v in p['poly']), min(v[0] for v in q['poly'])))
    return planks[0], y0, y1, z0, z1, gaps

# panel pegs: vertical, from the plank marks of the board-to-bearer joints
PEGS = []          # (panel id, side, y, bearer part, hole in frame, hole in panel)
dropped = []
for pid, (pname, asm) in PANELS.items():
    if asm in FUSE_ALL: continue                  # fused into the frame, no pegs needed
    pl, y0, y1, z0, z1, gaps = panel_geometry(pid)
    for side in SIDES:
        sx = 1 if side == 'R' else -1
        cand = []
        for m in F['marks']:
            if m['k'] != 'boardscrew' or not m['joint'] or not m['part'].startswith(pid): continue
            j = joints[m['joint']]
            plank = ID2PART[j['a']] if ID2PART[j['a']]['id'] == pid else ID2PART[j['b']]
            bearer = ID2PART[j['b']] if plank is ID2PART[j['a']] else ID2PART[j['a']]
            xm = sx*(m['x']+D)*S; zc = z0*S
            hf = Hole((xm, m['y']*S, zc+0.5), (0, 0, -1), PEG_DEPTH+0.5, PEG_HOLE, 'peg')
            hp = Hole((xm, m['y']*S, zc-0.5), (0, 0, 1), PEG_DEPTH+0.5, PEG_HOLE, 'peg')
            cand.append((m['y'], bearer, hf, hp))
        # candidates that fit the bearer, away from other holes; keep the outermost PANEL_PEGS in y, per end
        ok = [c for c in sorted(cand, key=lambda c: c[0]) if inside_part(c[1], side, c[2], 0.8) and not conflicts((asm, side), c[2])]
        chosen = ([ok[0], ok[-1]] if len(ok) >= 2 and PANEL_PEGS == 2 else ok[:PANEL_PEGS])
        for c in chosen:
            add_hole((asm, side), c[2]); add_hole(('panel', pid), c[3]); PEGS.append((pid, side, c[0]))
        if len(chosen) < PANEL_PEGS: dropped.append((pid, side, 'only %d peg(s) fit' % len(chosen)))

def round_r3(p):
    poly = [[q[0]*S, q[1]*S] for q in p['poly']]
    idx = next(i for i, q in enumerate(p['poly']) if abs(q[0]+44.5) < 1e-6 and abs(q[1]-412) < 1e-6)
    poly = round_corner(poly, idx, ROUND_R3)
    # R3's bottom edge (z 323) touches S1's top edge edge-to-edge once the slabs are fused, which is a
    # non-manifold line. Lower R3 by 0.2 mm so they overlap in a thin sliver instead (S1 top stays at 323).
    return [[q[0], q[1]-0.2] if abs(q[1]-323*S) < 1e-6 else q for q in poly]

def member_prism(p, side):
    x0, x1 = xspan(p, side)
    return prism(p, x0, x1, round_r3(p) if p['id'] == 'R3' else None)

class Body: pass
BODIES = []

def side_solid(asm, side):
    members = [p for p in PARTS if p['asm'] == asm and p['side'] == 'R']
    solid = member_prism(members[0], side)
    for p in members[1:]: solid = solid + member_prism(p, side)
    return solid, members

def panel_solid(pid):
    pl, y0, y1, z0, z1, gaps = panel_geometry(pid)
    xa, xb = xspan(pl, 'C')
    solid = prism(dict(poly=[[y0, z0], [y1, z0], [y1, z1], [y0, z1]], id='PANEL', tag=pid), xa, xb)
    for ga, gb in gaps:                                  # plank lines: shallow cosmetic grooves, not through
        solid = solid - Pos((xa+xb)/2*S, (ga+gb)/2*S, z1*S) * Box((xb-xa)*S+2, (gb-ga)*S, 2*GROOVE_DEPTH)
    return solid, pl

def finish(solid, keys, what):
    solid = solid.clean() if hasattr(solid, 'clean') else solid
    for k in keys:
        for h in HOLES.get(k, []): solid = solid - h.solid()
    assert len(solid.solids()) == 1, f'{what} is not one connected solid'
    return solid.solids()[0]

for asm, fname in FRAMES.items():
    if asm in FUSE_ALL:
        # whole rigid assembly: right side + left side + seat panel, one solid
        pid = next(k for k, v in PANELS.items() if v[1] == asm)
        sR, members = side_solid(asm, 'R'); sL, _ = side_solid(asm, 'L'); pn, pl = panel_solid(pid)
        solid = finish(sR + sL + pn, [(asm, 'R'), (asm, 'L')], FUSE_ALL[asm])
        b = Body(); b.p = dict(asm=asm, g='rail', name=FUSE_ALL[asm]+' (fused: both sides + '+pid+' panel, '+'+'.join(p['id'] for p in members)+')')
        b.members = members; b.side = 'RL'; b.name = FUSE_ALL[asm]; b.solid = solid
        BODIES.append(b)
        continue
    for side in SIDES:
        solid, members = side_solid(asm, side)
        solid = finish(solid, [(asm, side)], f'{fname}_{side}')
        b = Body(); b.p = dict(asm=asm, g='rail', name=fname+' (fused: '+'+'.join(p['id'] for p in members)+')')
        b.members = members; b.side = side; b.name = f'{fname}_{side}'; b.solid = solid
        BODIES.append(b)

for pid, (pname, asm) in PANELS.items():
    if asm in FUSE_ALL: continue
    solid, pl = panel_solid(pid)
    solid = finish(solid, [('panel', pid)], pname)
    b = Body(); b.p = dict(asm=asm, g='slat', name=pname); b.members = [pl]; b.side = 'C'; b.name = pname; b.solid = solid
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

# ---------------- print files ----------------
def overhang_area(b, flip):
    """mm2 of the stepped side frame that has no material directly below it (needs support),
    when the frame is printed with its X axis as build-Z. flip=False: smallest-x face on the bed."""
    slabs = {}
    for p in b.members:
        a, c = xspan(p, b.side)
        slabs.setdefault((round(a, 3), round(c, 3)), []).append(
            Polygon([(q[0]*S, q[1]*S) for q in p['poly']]).buffer(0))
    keys = sorted(slabs)
    if flip: keys = keys[::-1]
    fp = [unary_union(slabs[k]) for k in keys]
    return sum(fp[i].difference(fp[i-1]).area for i in range(1, len(fp)))

def score_mesh(P, T, com):
    """support proxy for a mesh already standing on z=0: sum(area*height) over faces overhanging more than 45 deg
    (they need supports), plus bed-contact area and whether the centre of mass sits over the contact patch."""
    tri = P[T]; n = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]); ar = np.linalg.norm(n, axis=1)/2
    n = n/(2*ar[:, None]+1e-12); zc = tri[:, :, 2].mean(1)
    over = (n[:, 2] < -0.7071) & (tri[:, :, 2].min(1) > 0.2)
    flat = (n[:, 2] < -0.99) & (tri[:, :, 2].max(1) < 0.05)
    contact = float(ar[flat].sum())
    stable = False
    if flat.any():
        pts = tri[flat].reshape(-1, 3)[:, :2]
        stable = bool(MultiPoint([tuple(q) for q in pts]).convex_hull.buffer(1e-6).contains(Point(com[0], com[1])))
    return float((ar[over]*zc[over]).sum()), float(ar[over].sum()), contact, stable

def best_orientation(s):
    """lay the assembly on each large flat face that is a supporting plane (all of the part lies on one side),
    spin it in-plane to the smallest footprint, and keep the stable, least-support option."""
    v, t = s.tessellate(0.02)
    mesh = trimesh.Trimesh(np.array([[p.X, p.Y, p.Z] for p in v]), np.array(t), process=True)
    normals = [n for fa, n in zip(mesh.facets_area, mesh.facets_normal) if fa >= 60]
    normals += [n for fa, n in zip(mesh.convex_hull.facets_area, mesh.convex_hull.facets_normal) if fa >= 150]
    cands = []
    for nrm in normals:
        M = trimesh.geometry.align_vectors(nrm, [0, 0, -1])
        P = trimesh.transform_points(mesh.vertices, M)
        T2, rect = trimesh.bounds.oriented_bounds_2D(P[:, :2])            # in-plane spin to the smallest footprint
        R = np.eye(4); R[:2, :2] = T2[:2, :2]; R[:2, 3] = T2[:2, 2]
        M = R @ M; P = trimesh.transform_points(mesh.vertices, M); zmin = P[:, 2].min(); P[:, 2] -= zmin
        if max(rect) > 215 and sorted(rect)[0] > 215: continue
        if rect[0] > 215 or rect[1] > 215: continue
        com = trimesh.transform_points([mesh.center_mass], M)[0]; com[2] -= zmin
        proxy, area, contact, stable = score_mesh(P, mesh.faces, com)
        cands.append((proxy, area, contact, P.max(0)-P.min(0), M, zmin, stable and contact >= 300))
    good = [c for c in cands if c[6]]
    proxy, area, contact, ext, M, zmin, ok = min(good or cands, key=lambda c: c[0])
    how = 'stable flat base' if ok else 'NO flat base: needs supports down to the plate and a brim'
    return M, zmin, ('%s; overhang %.0f mm2, bed contact %.0f mm2, height %.0f mm' % (how, area, contact, ext[2]))

rows = []
for b in BODIES:
    s = b.solid
    if b.side == 'C':                       # panels: already flat, long X, thin Z
        s2, note = s, 'flat'
    elif b.side == 'RL':                    # whole assembly (both sides + panel): width stays horizontal, tilt about X
        M, zmin, note = best_orientation(s)
        s2 = None
    else:                                   # side frames: X becomes build-Z, choose the end with less overhang
        a0, a1 = overhang_area(b, False), overhang_area(b, True)
        flip = a1 < a0
        s2 = s.rotate(Axis((0, 0, 0), (1, 1, 1)), -120)          # (x,y,z)->(y,z,x): smallest x on the bed
        if flip: s2 = s2.rotate(Axis.Y, 180)                     # largest x on the bed instead
        note = 'overhang %.0f mm2 (other way %.0f)' % (min(a0, a1), max(a0, a1))
    if s2 is None:                          # oriented with a trimesh transform
        v, t = s.tessellate(0.005, 0.1)
        m = trimesh.Trimesh(np.array([[p.X, p.Y, p.Z] for p in v]), np.array(t), process=True)
        m.apply_transform(M); m.apply_translation([-m.bounds[0][0], -m.bounds[0][1], -m.bounds[0][2]])
        m.export(os.path.join(out, 'stl', 'parts', f'{b.name}.stl'))
        ex = m.extents; size = (ex[0], ex[1], ex[2])
    else:
        bb2 = s2.bounding_box()
        s2 = s2.moved(Location((-bb2.min.X, -bb2.min.Y, -bb2.min.Z)))
        export_stl(s2, os.path.join(out, 'stl', 'parts', f'{b.name}.stl'), tolerance=0.005, angular_tolerance=0.1)
        bb3 = s2.bounding_box(); size = (bb3.size.X, bb3.size.Y, bb3.size.Z)
    rows.append([b.name, b.p['name'], b.side, round(size[0], 1), round(size[1], 1), round(size[2], 1), round(s.volume, 0), note])

with open(os.path.join(out, 'parts.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['file', 'part', 'side', 'X_mm', 'Y_mm', 'Z_mm', 'volume_mm3', 'print note']); w.writerows(rows)

print('printed parts', len(BODIES))
for r in rows: print('  ', r)
for d in dropped: print('  dropped', d)
print('panel pegs', len(PEGS))

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
            x = s1 & s2
            v = x.volume if x is not None else 0.0
            if v > 0.05:
                key = (n1, n2); worst[key] = max(worst.get(key, 0), v)
                print(f'  fold {fold:3d}: {n1} x {n2}: {v:.2f} mm3')
    print('3D sweep done; interfering pairs:', len(worst))
