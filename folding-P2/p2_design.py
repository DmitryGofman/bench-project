"""P2 — plate-built version of the folding picnic bench.

Same fold geometry as P1 Rev 2 (pivots A and B, 100 deg fold, seat 450, table 755, L 1520); what changes is how
it is built. Every rigid assembly side is ONE plate, in three x-layers (rear | table | front), plus three small stop
lugs per side. Everything that P1 did with 13 laminated members per side becomes 6 pieces.

Plates are 36 mm = two 18 mm birch plywood plies glued face to face (cross-ply). They must NOT be solid panel: a single
grain direction cannot serve both the long leg F1 (60 deg) and the seat bearer F2 (horizontal) in the same plate; the
cross-grain member would be ~6x over its tension-perpendicular capacity (see validation.json: grain_check).

Run:  python3 p2_design.py            -> writes p2_data.json (same schema as folding_p1_data.json + holes)
Then: python3 p2_validate.py          -> sweeps, hands-off simulation, metrics
"""
import json, math, os
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = json.load(open(os.path.join(HERE, '..', 'folding-P1', 'mini', 'folding_p1_data.json')))

T = 36.0          # plate and lug thickness: 2 x 18 mm birch plywood, laminated
GAP = 3.0         # face gap at the pivots (thrust washer), as P1
CLOSE_R = 20.0    # concave junctions are rounded to this radius (cut with a router / jigsaw + file)
R3_ROUND = 6.0    # the "R6" round-over the front seat slides over (from P1's design review)
RHO_PLY = 680.0   # kg/m3, birch plywood (P1's softwood is 500)
R3_DEEPEN = 2.0   # R3's underside goes 2 mm lower so the S1 lug overlaps it instead of touching edge-to-edge

# ---- x layout, anchored on P1's innermost member (R3 at 552) so the boards keep P1's lengths to within 12 mm.
# Pivot stacks are 75 mm (plate 36 + 3 gap + plate 36); order across the width: rear | table | front.
X_R = (552.0, 552.0 + T)                       # rear plate           552..588
X_T = (X_R[1] + GAP, X_R[1] + GAP + T)         # table plate          591..627
X_F = (X_T[1] + GAP, X_T[1] + GAP + T)         # front plate          630..666
X_S1 = (X_R[1], X_R[1] + T)                    # rear stop lug on the rear plate's outer face, reaches into the table layer
X_T45 = (X_T[1], X_T[1] + T)                   # table stop lugs T4/T5 on the table plate's outer face, reach into the front layer

P = {p['tag']: p for p in P1['parts']}

def poly(tag, edit=None):
    pts = [list(q) for q in P[tag]['poly']]
    return Polygon(pts).buffer(0)

def r3_poly():
    """R3 with its front-top corner rounded (R6) and its underside 2 mm lower"""
    pts = [list(q) for q in P['R3-R']['poly']]
    pts = [[q[0], q[1]-R3_DEEPEN if abs(q[1]-323) < 1e-6 else q[1]] for q in pts]
    g = Polygon(pts)
    # round the corner at (-44.5, 412): erode/dilate only around that vertex
    c = Polygon([(-44.5-R3_ROUND*2, 412-R3_ROUND*2), (-44.5+R3_ROUND*2, 412-R3_ROUND*2),
                 (-44.5+R3_ROUND*2, 412+1), (-44.5-R3_ROUND*2, 412+1)])
    rounded = g.buffer(-R3_ROUND, join_style=1).buffer(R3_ROUND, join_style=1, resolution=16)
    return unary_union([g.difference(c), rounded.intersection(c)])

def plate(tags, r3=False):
    shapes = [r3_poly() if (t == 'R3-R') else poly(t) for t in tags]
    u = unary_union(shapes)
    # round every concave junction: closing with radius CLOSE_R (adds a fillet, never removes material)
    u = u.buffer(CLOSE_R, join_style=1, resolution=16).buffer(-CLOSE_R, join_style=1, resolution=16)
    assert u.geom_type == 'Polygon', 'plate is not one connected piece'
    return u

def ring(r, nd=2):
    c = list(r.coords)[:-1]
    return [[round(x, nd), round(y, nd)] for x, y in c]

def plate_part(pid, tag, name, asm, x, geom):
    ext = Polygon(geom.exterior).exterior
    if not geom.exterior.is_ccw: ext = Polygon(list(geom.exterior.coords)[::-1]).exterior
    b = geom.bounds
    mr = geom.minimum_rotated_rectangle.exterior.coords
    e = sorted(math.dist(mr[i], mr[i+1]) for i in range(2))
    return dict(id=pid, tag=tag, name=name, asm=asm, side='R', g='plate', kind='plate', x0=x[0], x1=x[1],
                poly=ring(geom.exterior), holes=[ring(i) for i in geom.interiors],
                blank=round(e[1]), W=round(e[0]), area=round(geom.area, 1), rho=RHO_PLY)

def lug_part(src, pid, name, x):
    p = dict(P[src]); p = {k: p[k] for k in ('asm', 'side', 'poly', 'blank', 'W')}
    p.update(id=pid, tag=pid+'-R', name=name, g='stop', kind='lug', x0=x[0], x1=x[1], holes=[], rho=RHO_PLY)
    return p

rear = plate(['R1-R', 'R2-R', 'R3-R', 'R4-R', 'R5-R'])
front = plate(['F1-R', 'F2-R', 'F3-R'])
table = plate(['T1-R', 'T2-R'])

parts = [
    plate_part('RP', 'RP-R', 'RP · Rear plate (legs, bearer, tie, foot)', 'rear', X_R, rear),
    lug_part('S1-R', 'S1', 'S1 · Bench bearing stop lug', X_S1),
    plate_part('FP', 'FP-R', 'FP · Front plate (long leg, bearer, brace)', 'front', X_F, front),
    plate_part('TP', 'TP-R', 'TP · Table / back plate (apron, pivot extension)', 'top', X_T, table),
    lug_part('T4-R', 'T4', 'T4 · Table spread stop lug', X_T45),
    lug_part('T5-R', 'T5', 'T5 · Bench stop wedge lug', X_T45),
]
for p in parts:
    if p['id'] in ('S1', 'T4', 'T5'):
        p['x0'], p['x1'] = (X_S1 if p['id'] == 'S1' else X_T45)
# boards: same planks as P1, ends flush with the outer plate face of the assembly they sit on
BOARD_X = {'S2': X_F[1], 'S3': X_R[1], 'S4': 760.0}      # 666, 588, 760  (P1: 672, 590, 760)
for b in P1['parts']:
    if b['side'] == 'C':
        b = dict(b); e = BOARD_X[b['id']]
        b.update(x0=-e, x1=e, kind='board', holes=[], blank=int(2*e), rho=500.0)
        parts.append(b)

out = dict(P1)
out['name'] = 'P2'
out['parts'] = parts
out['layout'] = dict(T=T, GAP=GAP, X_R=X_R, X_T=X_T, X_F=X_F, X_S1=X_S1, X_T45=X_T45, CLOSE_R=CLOSE_R)
for k in ('marks', 'joints', 'interfaces', 'hardware', 'validation'):
    out.pop(k, None)
out['mini'] = dict(
    pivotA=dict(head='FP-R', nut='TP-R', head_x=X_F[1], nut_x=X_T[0]),      # front plate <-> table plate
    pivotB=dict(head='TP-R', nut='RP-R', head_x=X_T[1], nut_x=X_R[0]),      # table plate <-> rear plate
    pin=dict(front='FP-R', top='TP-R'))
out['validation'] = dict(pin=P1['validation']['pin'])        # lock-pin holes: same positions as P1 (same A, same radius)
json.dump(out, open(os.path.join(HERE, 'p2_data.json'), 'w'), separators=(',', ':'))
for p in parts:
    print(f"{p['tag']:6s} x {p['x0']:.0f}..{p['x1']:.0f}  {p['kind']:5s} " + (f"blank {p['blank']}x{p['W']}  area {p['area']:.0f} mm2  holes {len(p['holes'])}" if p['kind'] == 'plate' else ''))

# ---- P2's own hands-off curve (gravity solver, calibrated on P1 in p2_validate.py), stored in the data file
import sys
sys.path.insert(0, HERE)
from handsoff import simulate
from kin import Bench
bn = Bench(os.path.join(HERE, 'p2_data.json'))
curve, phi_eq, com, mass = simulate(bn, step=0.25)
out['handsoff'] = [[round(th, 2), round(ph, 3)] for th, ph in curve if abs(th*2-round(th*2)) < 1e-9]
json.dump(out, open(os.path.join(HERE, 'p2_data.json'), 'w'), separators=(',', ':'))
print(f'hands-off: front frame hangs at {phi_eq:.1f} deg, front assembly {mass:.1f} kg, ends at {out["handsoff"][-1][1]:.2f} deg')
