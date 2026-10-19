"""Folding bench V2 — generator (geometry from Dima's sketch of the video bench, 2026-10-18).

    python3 build.py        # writes app-folding-data.js (var FOLDING_V2) + validation.json
    python3 ../app/make_app.py

Three sub-assemblies, two pivots per side:

  rear  (black)  seat rail R1 with a rounded front end (pivot B), two splayed legs R2/R3,
                 one low stretcher R4, three seat boards S1
  top   (blue)   apron T1 under four table boards S2, straight strut T2 down to pivot B
                 (rounded end). No stop blocks: the front seat stands on two feet in both poses.
  front (green)  arm F1 (rounded end at pivot A on the apron, runs to the floor), seat rail F2,
                 vertical leg F3 lapped on the inside of the rail (screwed from the side); F1 laps the rail. Three seat boards S3.

Folding: the top turns 100° about B. A is placed so that it ends at the same height it started
(|A_y - B_y| = h·tan 50°), so the front seat just translates 2·|A_y| rearward and lands in front of
the rear seat, standing on its own two feet in both poses. Side view: y horizontal (front = -y), z up.
"""
import copy, json, math, os
from shapely.geometry import Polygon, Point
from shapely.ops import nearest_points
import kin

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- stock -----------------------------------------------------------------------------------
T = 38.0                 # all timber 38 thick
W = 89.0                 # frame members 38 x 89
WT = 89.0                # table boards 38 x 89 — one stock size for everything, as in the video
WS = 89.0                # seat boards 38 x 89
GAP = 6.0

# ---- heights ---------------------------------------------------------------------------------
Z_RAIL = (323.0, 412.0)  # seat rails, on edge
Z_SEAT = 450.0
Z_APRON = (628.0, 717.0)
Z_TOP = 755.0

# ---- mechanism -------------------------------------------------------------------------------
FOLD = 100.0                                   # table -> bench rotation about B
B = (0.0, 367.5)                               # pivot B: centre of the rear rail's rounded front end
H = (Z_APRON[0] + Z_APRON[1])/2 - B[1]         # 305: A sits on the apron centre line
A0 = (-H*math.tan(math.radians(FOLD/2)), B[1] + H)   # pivot A: ends at the same height it starts
SHIFT = -2*A0[0]                               # the front seat moves this far rearward
R = W/2                                        # rounded ends: radius = half the plank width

STRUT_LEAN = 8.0         # strut leans forward going up (sketch)
LEG_SPLAY = 15.0         # rear frame legs splay out
TABLE_REAR = 20.0        # table rear edge (y)
N_TABLE, N_SEAT = 7, 3

# x layers (right-hand side; the left side mirrors). Adjacent layers are 3 mm apart only where a pivot is.
X = {'leg': (514, 552), 'rail': (552, 590), 'strut': (593, 631), 'apron': (631, 669),
     'arm': (672, 710), 'frail': (634, 672), 'fleg': (596, 634), 'stop': (669, 707)}     # front rail + leg inside the arm, arm outermost (video)
BOARD_X = {'rear': 590, 'top': 760, 'front': 672}     # board half-lengths
L0 = 1520


def r3(v): return round(float(v), 3)


def arc(c, r, a0, a1, n=24):
    return [(c[0] + r*math.cos(math.radians(a0 + (a1-a0)*i/n)), c[1] + r*math.sin(math.radians(a0 + (a1-a0)*i/n))) for i in range(n+1)]


def band_round_end(c, u_deg, z_cut, r=R):
    """plank with a full round end centred on c, running in direction u_deg (from +y, CCW),
    cut parallel to the floor at z = z_cut."""
    u = (math.cos(math.radians(u_deg)), math.sin(math.radians(u_deg)))
    n = (-u[1], u[0])
    p1 = (c[0] + r*n[0], c[1] + r*n[1]); p2 = (c[0] - r*n[0], c[1] - r*n[1])
    t1 = (z_cut - p1[1])/u[1]; t2 = (z_cut - p2[1])/u[1]
    e1 = (p1[0] + t1*u[0], z_cut); e2 = (p2[0] + t2*u[0], z_cut)
    # arc from +n round the back (-u) to -n
    a_n = math.degrees(math.atan2(n[1], n[0]))
    pts = arc(c, r, a_n, a_n + 180, 32) + [e2, e1]
    return [[r3(p[0]), r3(p[1])] for p in pts]


def rect(y0, y1, z0, z1):
    return [[r3(y1), r3(z0)], [r3(y1), r3(z1)], [r3(y0), r3(z1)], [r3(y0), r3(z0)]]


def splay_leg(top_y0, splay_deg, toward):
    """leg 89 wide, top cut at z 412, foot cut at z 0, foot displaced `toward` (-1 front, +1 rear)."""
    t = math.tan(math.radians(splay_deg)); wd = W/math.cos(math.radians(splay_deg)); d = Z_RAIL[1]*t*toward
    return [[r3(top_y0 + d), 0.0], [r3(top_y0 + wd + d), 0.0], [r3(top_y0 + wd), Z_RAIL[1]], [r3(top_y0), Z_RAIL[1]]]


def flat_of(poly):
    """marking-out outline (u along the plank, v across) with u, v >= 0, and the blank length."""
    n = len(poly); best = None
    for i in range(n):
        a, b = poly[i], poly[(i+1) % n]
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        if best is None or L > best[0]: best = (L, i)
    L, i = best; a, b = poly[i], poly[(i+1) % n]
    ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L; vx, vy = -uy, ux
    pts = [((q[0]-a[0])*ux + (q[1]-a[1])*uy, (q[0]-a[0])*vx + (q[1]-a[1])*vy) for q in poly]
    if sum(p[1] for p in pts)/len(pts) < 0: pts = [(u, -v) for u, v in pts]
    u0 = min(p[0] for p in pts); v0 = min(p[1] for p in pts)
    pts = [[r3(u-u0), r3(v-v0)] for u, v in pts]
    return pts, math.ceil(max(p[0] for p in pts) - 1e-6)


def lap_points(pa, pb, n, edge=15.0, avoid=()):
    """n fastener positions inside the overlap of two profiles, spread along its long axis."""
    ov = Polygon(pa).intersection(Polygon(pb))
    inner = ov.buffer(-edge)
    for c, rr in avoid: inner = inner.difference(Point(c).buffer(rr))
    if inner.is_empty: raise SystemExit('lap too small for fasteners (overlap %.0f mm²)' % ov.area)
    rr_ = list(ov.minimum_rotated_rectangle.exterior.coords)[:4]
    e = [(rr_[(i+1) % 4][0]-rr_[i][0], rr_[(i+1) % 4][1]-rr_[i][1]) for i in range(2)]
    ax = max(e, key=lambda v: math.hypot(*v)); L = math.hypot(*ax); ux, uy = ax[0]/L, ax[1]/L
    vx, vy = -uy, ux
    c = inner.centroid
    proj = [(q[0]-c.x)*ux + (q[1]-c.y)*uy for q in inner.exterior.coords] if inner.geom_type == 'Polygon' else [0]
    half = (max(proj) - min(proj))/2
    if n == 1: offs = [(0, 0)]
    elif n == 2: offs = [(-0.75, 0), (0.75, 0)]
    else: offs = [(-0.8, 0.25), (0, -0.25), (0.8, 0.25)]
    out = []
    width = 30.0
    # candidate grid inside the usable area; each fastener takes the free spot nearest its target
    x0, y0, x1, y1 = inner.bounds
    grid = [(x0 + i*2.0, y0 + j*2.0) for i in range(int((x1-x0)/2)+1) for j in range(int((y1-y0)/2)+1)]
    grid = [g for g in grid if inner.contains(Point(g))]
    for fu, fv in offs[:n]:
        tx, ty = c.x + fu*half*ux + fv*width*vx, c.y + fu*half*uy + fv*width*vy
        free = [g for g in grid if all(math.hypot(g[0]-q[0], g[1]-q[1]) >= 24.0 for q in out)]
        if not free: raise SystemExit('no room for %d fasteners in this lap' % n)
        g = min(free, key=lambda g: (g[0]-tx)**2 + (g[1]-ty)**2)
        out.append((r3(g[0]), r3(g[1])))
    return out, ov.area


def main():
    parts = []

    def part(pid, name, asm, layer, g, poly, note='', Wd=W):
        x0, x1 = X[layer]
        fl, blank = flat_of(poly)
        parts.append({'id': pid, 'tag': pid + '-R', 'name': pid + ' · ' + name, 'asm': asm, 'side': 'R', 'g': g,
                      'x0': x0, 'x1': x1, 'poly': poly, 'blank': blank, 'W': Wd, 'flat': fl, 'note': note})
        return poly

    def boards(pid, name, asm, n, w, y_near, direction, z0, z1, half):
        """n boards, first one's edge at y_near, laid toward `direction` (-1 front, +1 rear)."""
        out = []
        for k in range(n):
            a = y_near + direction*k*(w + GAP); b = a + direction*w
            poly = rect(min(a, b), max(a, b), z0, z1)
            parts.append({'id': pid, 'tag': '%s-%d' % (pid, k+1), 'name': pid + ' · ' + name, 'asm': asm, 'side': 'C',
                          'g': 'slat', 'x0': -half, 'x1': half, 'poly': poly, 'blank': int(2*half), 'W': w, 'stockW': w, 'flat': None,
                          'note': 'Rip from 38×140.' if w < 100 else ''})
            out.append((min(a, b), max(a, b)))
        return out

    # ---- rear (black) ---------------------------------------------------------------------
    y_rail_end = 335.0
    # rail: round front end on B, square rear end
    rail = [[r3(p[0]), r3(p[1])] for p in arc(B, R, 90, 270, 32)] + [[0.0, Z_RAIL[0]], [y_rail_end, Z_RAIL[0]], [y_rail_end, Z_RAIL[1]]]
    R1 = part('R1', 'Rear seat rail', 'rear', 'rail', 'rail', rail, 'Round the front end R44.5 on the pivot centre.')
    R2 = part('R2', 'Rear frame front leg', 'rear', 'leg', 'rail', splay_leg(45.0, LEG_SPLAY, -1), 'Splays %g° forward; both ends cut parallel to the floor.' % LEG_SPLAY)
    R3 = part('R3', 'Rear frame back leg', 'rear', 'leg', 'rail', splay_leg(195.0, LEG_SPLAY, +1), 'Splays %g° back; both ends cut parallel to the floor.' % LEG_SPLAY)
    R4 = part('R4', 'Rear frame stretcher', 'rear', 'rail', 'rail', rect(-10.0, 340.0, 100.0, 189.0))
    seat_rear_back = 334.0           # the table boards sweep a 349.5 radius about B: stay inside it
    seat_rear_front = seat_rear_back - (N_SEAT*WS + (N_SEAT-1)*GAP)
    # R5: bench stop. Lies over the back leg R3 (same angle, same y), glued + bolted to the stretcher;
    # its top is cut to the strut's underside in bench pose, so the strut lands on it.
    S1 = boards('S1', 'Rear seat board', 'rear', N_SEAT, WS, seat_rear_front, +1, Z_RAIL[1], Z_SEAT, BOARD_X['rear'])

    # ---- top (blue) ------------------------------------------------------------------------
    table_front = TABLE_REAR - (N_TABLE*WT + (N_TABLE-1)*GAP)
    T1 = part('T1', 'Table apron / backrest post', 'top', 'apron', 'rail', rect(table_front, TABLE_REAR, *Z_APRON))
    T2 = part('T2', 'Strut', 'top', 'strut', 'rail', band_round_end(B, 90 + STRUT_LEAN, Z_APRON[1]), 'Round end R44.5 on pivot B; top cut level with the apron top.')
    strut_b = Polygon([kin.rot(q, B, -FOLD) for q in T2])
    from shapely.geometry import LineString
    def under(y):
        g = strut_b.intersection(LineString([(y, -1000), (y, 2000)]))
        return min(c[1] for c in g.coords)
    tl = math.tan(math.radians(LEG_SPLAY))
    def leg_front(z): return 195.0 + (Z_RAIL[1] - z)*tl              # R3 front edge (from splay_leg(195, …, +1))
    wd = W/math.cos(math.radians(LEG_SPLAY))
    zt = Z_RAIL[0]
    for _ in range(4):                                             # top corners follow the strut underside
        zl, zr = under(leg_front(zt)), under(leg_front(zt) + wd)
        zt = (zl + zr)/2
    zb = 100.0
    R5 = part('R5', 'Bench stop', 'rear', 'strut', 'stop',
              [[r3(leg_front(zb)), zb], [r3(leg_front(zb) + wd), zb], [r3(leg_front(zr) + wd), r3(zr)], [r3(leg_front(zl)), r3(zl)]],
              'Lies over R3 at the same %g°; bottom flush with the stretcher, top cut to the strut underside (bench pose).' % LEG_SPLAY)
    S2 = boards('S2', 'Table / backrest board', 'top', N_TABLE, WT, TABLE_REAR, -1, Z_APRON[1], Z_TOP, BOARD_X['top'])

    # ---- front (green) -----------------------------------------------------------------------
    seat_front_near = seat_rear_front - GAP - SHIFT                       # lands next to the rear seat
    seat_front_far = seat_front_near - (N_SEAT*WS + (N_SEAT-1)*GAP)
    # arm angle: its outer foot corner lands exactly on the seat's far edge (nothing sticks out past the seat)
    lo, hi = 20.0, 60.0
    for _ in range(60):
        a = (lo + hi)/2
        outer = A0[0] - A0[1]*math.tan(math.radians(a)) - R/math.cos(math.radians(a))
        if outer > seat_front_far: lo = a
        else: hi = a
    ARM_LEAN = (lo + hi)/2
    F1 = part('F1', 'Arm (table leg)', 'front', 'arm', 'rail', band_round_end(A0, 270 - ARM_LEAN, 0.0),
              'Round end R44.5 on pivot A; foot cut parallel to the floor, outer corner flush with the seat end.')
    def arm_rear_flank(z):                     # the arm's table-side edge
        tl = math.tan(math.radians(ARM_LEAN))
        return A0[0] - (A0[1] - z)*tl + R/math.cos(math.radians(ARM_LEAN))
    # ---- stops: blocks on the apron's outer face, flush with its top and bottom, one face cut to the arm.
    # T3 meets the arm in table pose (stops the table opening further), T4 in bench pose (stops it folding further).
    def flank(rel):
        d = math.radians(270 - ARM_LEAN + rel)
        u = (math.cos(d), math.sin(d)); n = (-u[1], u[0])
        if n[1] < 0: n = (-n[0], -n[1])
        f0 = (A0[0] + R*n[0], A0[1] + R*n[1])
        return lambda z: f0[0] + (z - f0[1])/u[1]*u[0]
    ft, fb = flank(0.0), flank(FOLD)
    T3 = part('T3', 'Table stop', 'top', 'stop', 'stop',
              [[r3(ft(Z_APRON[1])), Z_APRON[1]], [r3(table_front), Z_APRON[1]], [r3(table_front), Z_APRON[0]], [r3(ft(Z_APRON[0])), Z_APRON[0]]],
              'Flush with the apron top, bottom and end; inner face cut to the arm (%.1f° from vertical).' % ARM_LEAN)
    T4_END = -120.0
    T4 = part('T4', 'Bench stop', 'top', 'stop', 'stop',
              [[r3(fb(Z_APRON[1])), Z_APRON[1]], [r3(fb(Z_APRON[0])), Z_APRON[0]], [T4_END, Z_APRON[0]], [T4_END, Z_APRON[1]]],
              'Flush with the apron top and bottom; face cut to the arm in bench pose (%.1f° from horizontal).' % abs(270 - ARM_LEAN + FOLD - 360))
    F3 = part('F3', 'Front seat leg', 'front', 'fleg', 'rail', rect(seat_front_far, seat_front_far + W, 0.0, Z_RAIL[1]),
              'Square cut; flush with the seat end, full height to the rail top, lapped on the inside face of F2.')
    rail_f = [[r3(seat_front_far), Z_RAIL[0]], [r3(arm_rear_flank(Z_RAIL[0])), Z_RAIL[0]],
              [r3(arm_rear_flank(Z_RAIL[1])), Z_RAIL[1]], [r3(seat_front_far), Z_RAIL[1]]]
    F2 = part('F2', 'Front seat rail', 'front', 'frail', 'rail', rail_f,
              'Inner end cut to the arm angle, so it ends under the arm and never shows past it.')
    S3 = boards('S3', 'Front seat board', 'front', N_SEAT, WS, seat_front_near, -1, Z_RAIL[1], Z_SEAT, BOARD_X['front'])

    # ---- pin L: one hole in the arm, two in the apron (table / bench) ------------------------
    psi = -50.0
    p0 = (A0[0] + 34*math.cos(math.radians(psi)), A0[1] + 34*math.sin(math.radians(psi)))
    pb = kin.rot(p0, A0, FOLD)

    # ---- fasteners -------------------------------------------------------------------------
    marks = [
        {'k': 'pivot', 'part': 'F1', 'asm': 'front', 'x': 710, 'y': r3(A0[0]), 'z': r3(A0[1]), 'label': 'A', 'joint': '', 'spec': ''},
        {'k': 'pivot', 'part': 'T2', 'asm': 'top', 'x': 631, 'y': r3(B[0]), 'z': r3(B[1]), 'label': 'B', 'joint': '', 'spec': ''},
        {'k': 'pin', 'part': 'F1', 'asm': 'front', 'x': 710, 'y': r3(p0[0]), 'z': r3(p0[1]), 'label': 'L', 'joint': '', 'spec': ''},
    ]
    joints = []
    keep_out = [(B, 40.0)]
    def lap(jid, a, pa, b, pb_, n, face_x, asm, k='screw', spec='Exterior PU glue + 3 × 5×70 screws', drive=None, kind='glued lap', avoid=()):
        pts, area = lap_points(pa, pb_, n, avoid=avoid)
        for y, z in pts:
            marks.append({'k': k, 'part': a, 'asm': asm, 'x': face_x, 'y': y, 'z': z, 'label': '', 'joint': jid, 'spec': spec})
        joints.append({'id': jid, 'kind': kind, 'a': a, 'b': b, 'fastener': spec, 'qty': n,
                       'drive': drive or 'from %s outer face into %s' % (a, b), 'lap_mm2': int(area)})
    def board_screws(jid, pid, rows, rail_id, x, z):
        k = 0
        for i, (y0, y1) in enumerate(rows):
            e = 14.0 if y1 - y0 < 100 else 25.0
            for y in (y0 + e, y1 - e):
                marks.append({'k': 'boardscrew', 'part': pid, 'asm': {'S1': 'rear', 'S2': 'top', 'S3': 'front'}[pid], 'x': x,
                              'y': r3(y), 'z': z, 'label': '', 'joint': jid, 'spec': ''})
            joints.append({'id': '%s' % jid if i == 0 else jid, 'kind': 'board to rail', 'a': '%s-%d' % (pid, i+1), 'b': rail_id,
                           'fastener': '2 × 5×70 screws per board end, pilot Ø3, countersunk', 'qty': 2,
                           'drive': 'down through board face, X = ±%g' % x})

    lap('J01', 'R1', R1, 'R2', R2, 3, 590, 'rear', avoid=keep_out)
    lap('J02', 'R1', R1, 'R3', R3, 3, 590, 'rear')
    lap('J03', 'R4', R4, 'R2', R2, 3, 590, 'rear')
    r5c = Polygon(R5).intersection(Polygon(R4)).intersection(Polygon(R3)).centroid
    lap('J04', 'R4', R4, 'R3', R3, 2, 590, 'rear', spec='Exterior PU glue + 2 × 5×70 screws (+ the R5 bolt)', avoid=[((r5c.x, r5c.y), 26.0)])
    board_screws('J05', 'S1', S1, 'R1', 571.0, Z_SEAT)
    marks.append({'k': 'm8', 'part': 'R5', 'asm': 'rear', 'x': 631, 'y': r3(r5c.x), 'z': r3(r5c.y), 'label': '', 'joint': 'J14', 'spec': 'M8×130 through R5 + R4 + R3'})
    joints.append({'id': 'J14', 'kind': 'glued + bolted lap', 'a': 'R5', 'b': 'R4 + R3', 'fastener': 'Exterior PU glue + 1 × M8×130 through R5, R4 and R3', 'qty': 1, 'drive': 'through'})
    lap('J06', 'T1', T1, 'T2', T2, 2, 669, 'top', k='m8', kind='bolted lap',
        spec='M8×80 hex bolt + 2 washers + nyloc, counterbored Ø24×12 both faces, glued', drive='through', avoid=keep_out)
    pin_keep = [(p0, 16.0), (pb, 16.0), (A0, 30.0)]
    for jid, pid, poly in (('J12', 'T3', T3), ('J13', 'T4', T4)):
        lap(jid, pid, poly, 'T1', T1, 2, 707, 'top', spec='Exterior PU glue + 1 × M8×80 + 2 × 5×70 screws', avoid=pin_keep, kind='glued + bolted lap')
        c = Polygon(poly).centroid
        marks.append({'k': 'm8', 'part': pid, 'asm': 'top', 'x': 707, 'y': r3(c.x), 'z': r3(c.y), 'label': '', 'joint': jid, 'spec': 'M8 through %s + T1' % pid})
    board_screws('J07', 'S2', S2, 'T1', 650.0, Z_TOP)
    lap('J08', 'F1', F1, 'F2', F2, 3, 710, 'front')
    lap('J09', 'F2', F2, 'F3', F3, 3, 672, 'front')
    board_screws('J11', 'S3', S3, 'F2', 653.0, Z_SEAT)

    # de-duplicate the per-board joint rows into one row per board (keep ids unique)
    jj = []; seen = {}
    for j in joints:
        if j['kind'] == 'board to rail':
            seen[j['id']] = seen.get(j['id'], 0) + 1
            j = dict(j); j['id'] = '%s.%d' % (j['id'], seen[j['id']])
        jj.append(j)
    joints = jj

    # ---- data set ---------------------------------------------------------------------------
    F = {'B': [r3(B[0]), r3(B[1])], 'A0': [r3(A0[0]), r3(A0[1])], 'rot': -FOLD, 'L0': L0, 'parts': parts, 'marks': marks, 'joints': joints}
    M = kin.Model(F)

    # ---- fastener checks --------------------------------------------------------------------
    bad = []
    def span(m):
        if m['k'] == 'boardscrew': return (m['x']-35, m['x']+3)
        if m['k'] == 'screw': return (m['x']-70, m['x'])
        if m['k'] == 'm8': return (m['x']-(130 if m['part'] == 'R5' else 80), m['x'])
        return (m['x']-80, m['x'])
    rad = {'screw': 4.0, 'boardscrew': 4.0, 'm8': 12.0, 'pivot': 15.0, 'pin': 6.0}
    for i in range(len(marks)):
        for j in range(i+1, len(marks)):
            a, b = marks[i], marks[j]
            if a['asm'] != b['asm'] and not ({a['k'], b['k']} & {'pivot', 'pin'}): continue
            sa, sb = span(a), span(b)
            if min(sa[1], sb[1]) - max(sa[0], sb[0]) <= 0: continue
            need = rad[a['k']] + rad[b['k']] + 4.0
            if math.hypot(a['y']-b['y'], a['z']-b['z']) < need:
                bad.append('%s %s / %s %s' % (a['part'], a['joint'] or a['label'], b['part'], b['joint'] or b['label']))
    byid = {p['id']: p for p in parts if p['side'] == 'R'}
    for m in marks:
        if m['k'] in ('screw', 'm8') and not Polygon(byid[m['part']]['poly']).buffer(-9).contains(Point(m['y'], m['z'])):
            bad.append('edge distance %s %s' % (m['part'], m['joint']))
    for q in (p0, pb):     # pin holes inside the apron with edge distance
        if not Polygon(T1).buffer(-10).contains(Point(q)): bad.append('pin hole near apron edge')
    if not Polygon(F1).buffer(-10).contains(Point(p0)): bad.append('pin hole near arm edge')

    # ---- kinematics -------------------------------------------------------------------------
    guided = []
    for k in range(0, int(FOLD*4) + 1):
        th = -k*0.25
        h, fl = M.clashes(th, 0.0)
        if h or fl > 0.3: guided.append((th, h, round(fl, 2)))
    ho = M.handsoff([-k*0.5 for k in range(0, int(FOLD*2) + 1)])
    jams = [th for th, p in ho if p is None]
    ho_pts = [[round(th, 2), round(p, 2)] for th, p in ho if p is not None]
    ho_bad = [(th, p) for th, p in ho_pts if M.clashes(th, p)[0]]

    # over-travel: can the table open past 0° or fold past 100° with the pin OUT, letting the
    # front seat rock on one foot? Search every front-seat tilt within ±15°.
    def overtravel(th_e, sign):
        for dth in (0.25, 0.5, 1.0, 2.0):
            for k in range(-60, 61):
                h, fl = M.clashes(th_e + sign*dth, k*0.25)
                if not h and fl < 0.3: return [th_e + sign*dth, k*0.25]
        return None
    over = {'table_opens': overtravel(0.0, +1), 'bench_folds': overtravel(-FOLD, -1)}

    def state(th, phi):
        h, fl = M.clashes(th, phi)
        if fl > 0.3: return 'blocked by floor'
        if h: return 'blocked by ' + '/'.join(sorted({x for a, b, _ in h for x in (a, b)}))
        return 'free (gravity only)'
    phi_t, phi_b = ho_pts[0][1], ho_pts[-1][1]
    rig = {
        'pin_out': {'table': {'front +1°': state(0, phi_t+1), 'front −1°': state(0, phi_t-1)},
                    'bench': {'front +1°': state(-FOLD, phi_b+1), 'front −1°': state(-FOLD, phi_b-1)}},
        # pin in: front locked to the top, the pair turns about B together
        'pin_in': {'table': {'fold +1°': state(-1, phi_t-1), 'unfold 1°': state(1, phi_t+1)},
                   'bench': {'fold 1° more': state(-FOLD-1, phi_b-1), 'unfold 1°': state(-FOLD+1, phi_b+1)}},
    }

    # ---- envelope ----------------------------------------------------------------------------
    pb_pose = M.pose(-FOLD, phi_b)
    back_top = max(q[1] for p, poly in pb_pose if p['asm'] == 'top' for q in poly)
    seat_b = [q[0] for p, poly in pb_pose if p['id'] in ('S1', 'S3') for q in poly]
    floor0 = [q[0] for p, poly in M.pose(0, 0) for q in poly if q[1] < 0.5]
    meta = {'backTop': int(round(back_top)), 'seatDepth': int(round(max(seat_b) - min(seat_b))),
            'tableDepth': int(round(TABLE_REAR - table_front)), 'tableHeight': int(Z_TOP), 'seatHeight': int(Z_SEAT),
            'footprintTable': [int(round(min(floor0))), int(round(max(floor0)))], 'boardW': WT, 'seatW': WS,
            'shift': round(SHIFT, 1), 'A': [r3(A0[0]), r3(A0[1])], 'B': list(B),
            'armLean': round(ARM_LEAN, 1), 'tableToSeats': [int(round(seat_rear_front - TABLE_REAR)), int(round(table_front - seat_front_near))]}

    # ---- hardware ----------------------------------------------------------------------------
    n_screw = 2*sum(1 for m in marks if m['k'] in ('screw', 'boardscrew'))
    n_m8 = 2*sum(1 for m in marks if m['k'] == 'm8' and m['part'] != 'R5')
    F['hardware'] = [
        {'id': 'H01', 'qty': 4, 'spec': 'M10×70 hex bolt, ISO 4017, A4-70 stainless (or HDG 8.8)', 'note': 'Pivots A and B, one per pivot per side.'},
        {'id': 'H02', 'qty': 4, 'spec': 'M10 nyloc nut, ISO 10511, A4', 'note': 'Torque fully: the bolt clamps the sleeve, not the timber.'},
        {'id': 'H03', 'qty': 8, 'spec': 'M10 flat washer ISO 7089 (Ø20×2), A4', 'note': 'Head and nut side of each pivot.'},
        {'id': 'H04', 'qty': 4, 'spec': 'Pivot sleeve: stainless tube OD14 × 1.5 wall, cut 54.5 long, ends square', 'note': '79 timber stack − 10 − 15 counterbores + 0.5 float.'},
        {'id': 'H05', 'qty': 8, 'spec': 'Plain bushing ID14 / OD18 × 20, oil-impregnated sintered bronze (or POM)', 'note': 'One in each member at each pivot, flush with the moving face.'},
        {'id': 'H06', 'qty': 4, 'spec': 'Thrust washer UHMW-PE, ID14.5 / OD40 / 3.0', 'note': 'Between the moving faces at each pivot.'},
        {'id': 'H07', 'qty': 2, 'spec': 'Ball-lock quick-release pin Ø10, stainless, grip ≥ 80, with lanyard', 'note': 'Optional (the video uses a rope). One per side, through F1 into T1 ("table" or "bench" hole): keeps the front seat from swinging while you lift the table.'},
        {'id': 'H08', 'qty': n_m8, 'spec': 'M8×80 hex bolt + 2 × ISO 7089 washers + M8 nyloc, A4', 'note': 'Strut to apron (2 per side), T3 and T4 to apron (1 each per side). Counterbore Ø24×12 where a face moves past another part.'},
        {'id': 'H09', 'qty': math.ceil(n_screw*1.1), 'spec': 'Exterior structural screw 5×70, countersunk Torx', 'note': '%d fitted + 10%% spare. Countersink flush.' % n_screw},
        {'id': 'H11', 'qty': 1, 'spec': 'Exterior PU / D4 wood adhesive', 'note': 'All fixed laps. Not on moving faces.'},
        {'id': 'H12', 'qty': 2, 'spec': 'M8×130 hex bolt + 2 × ISO 7089 washers + M8 nyloc, A4', 'note': 'Bench stop R5 through stretcher R4 and leg R3, 1 per side.'},
    ]
    F['interfaces'] = [
        {'id': 'P-A', 'what': 'Pivot A · F1 ↔ T1', 'type': 'pivot bearing', 'spec': 'M10 bolt clamps a Ø14 stainless sleeve; both members on Ø14/Ø18 bushings; 3 mm UHMW thrust washer. Counterbore Ø30: 10 deep on F1 outer face, 15 deep on T1 inner face.'},
        {'id': 'P-B', 'what': 'Pivot B · T2 ↔ R1', 'type': 'pivot bearing', 'spec': 'Same stack as A. Counterbore Ø30: 10 deep on T2 outer face, 15 deep on R1 inner face.'},
        {'id': 'ST-T', 'what': 'T3 ↔ F1 (table)', 'type': 'hard stop', 'spec': 'T3 face lies on the arm in table pose: the table cannot open past flat and the arm cannot swing out.'},
        {'id': 'ST-B', 'what': 'T4 ↔ F1 (bench)', 'type': 'hard stop', 'spec': 'T4 face lies on the arm in bench pose: the arm cannot fold further against the backrest.'},
        {'id': 'ST-S', 'what': 'R5 ↔ T2 (bench)', 'type': 'hard stop', 'spec': 'The strut lands on R5 in bench pose: the backrest cannot tip further back, even if the front seat rocks.'},
        {'id': 'FL', 'what': 'F1 + F3 feet ↔ floor (both poses)', 'type': 'support', 'spec': 'The front seat stands on two feet, so the floor sets it level in table and bench pose.'},
        {'id': 'SUP', 'what': 'S3 ↔ R1 (bench)', 'type': 'support contact', 'spec': 'In bench pose the front seat boards rest on the bare front part of R1 (0 … %d), in front of the rear seat.' % int(seat_rear_front)},
        {'id': 'LK', 'what': 'Lock pin L · F1 ↔ T1', 'type': 'positive lock', 'spec': 'Ø10 ball-lock pin; one Ø10.5 hole in F1, two in T1 (table / bench) %.0f mm from A. Match-drill in each pose.' % 34},
    ]
    F['fabrication'] = [
        {'part': 'Stock', 'detail': 'One stock size: 38×89 for every part. Everything is a straight saw cut except the round ends on R1, T2 and F1 (R44.5, jigsaw + sander, drill the pivot centre first).'},
        {'part': 'Rear frame', 'detail': 'R2 and R3 splay %g° (saw cuts at %g°). Glue + 3 screws through R1 into each leg and through R4 into each leg.' % (LEG_SPLAY, LEG_SPLAY)},
        {'part': 'Table', 'detail': 'T2 leans %g° forward; glue + 2 × M8 to T1. Apron and boards flush at both ends.' % STRUT_LEAN},
        {'part': 'Stops', 'detail': 'T3, T4 and R5 are 38×89 offcuts with straight cuts. T3/T4 sit flush with the apron top and bottom (T3 also with its end); cut their angled face against the arm with the bench assembled in each pose. R5 lies over leg R3 at the same angle; cut its top with the bench folded so the strut lands on it.'},
        {'part': 'Front seat', 'detail': 'F1 at %.1f° from vertical, outermost, laps F2 (glue + 3 screws from the F1 outer face). F2 inner end cut at the same angle under F1. F3 runs full height on the inside of F2, flush with the seat end: glue + 3 screws from the F2 outer face.' % ARM_LEAN},
        {'part': 'Pivots A, B', 'detail': 'Bore Ø18 in both members, press bushings flush with the moving faces, Ø14 sleeve, M10 tightened fully, 3 mm thrust washer.'},
        {'part': 'Lock pin', 'detail': 'Drill Ø10.5 through F1 into T1 in table pose; fold, then drill the bench hole through the same F1 hole.'},
    ]
    F['validation'] = {'overtravel': over, 'guided': len(guided), 'jams': len(jams) + len(ho_bad), 'fasteners': len(bad), 'rigidity': rig,
                       'pin': {'radius_from_A': 34.0, 'F1_hole': [r3(p0[0]), r3(p0[1])], 'T1_table': [r3(p0[0]), r3(p0[1])], 'T1_bench': [r3(pb[0]), r3(pb[1])]}}
    F['handsoff'] = ho_pts
    F['meta'] = meta

    js = '/* generated by folding-V2/build.py — do not edit by hand */\nvar FOLDING_V2 = ' + json.dumps(F, ensure_ascii=False, separators=(',', ':')) + ';\n'
    open(os.path.join(HERE, 'app-folding-data.js'), 'w', encoding='utf-8').write(js)
    json.dump({'validation': F['validation'], 'meta': meta, 'guided_clashes': guided[:20], 'jams': jams[:20], 'handsoff_bad': ho_bad[:20],
               'fastener_issues': bad, 'handsoff_samples': ho_pts[::10], 'joints': [(j['id'], j.get('lap_mm2')) for j in joints if j.get('lap_mm2')]},
              open(os.path.join(HERE, 'validation.json'), 'w'), indent=1, ensure_ascii=False, default=str)
    print('A', meta['A'], 'shift', meta['shift'])
    print('guided clashes %d, hands-off jams %d, hands-off clashes %d, fastener issues %d' % (len(guided), len(jams), len(ho_bad), len(bad)))
    for g in guided[:6]: print('  guided', g)
    for b in bad[:10]: print('  fastener', b)
    print('rigidity', json.dumps(rig, ensure_ascii=False))
    print('over-travel (pin out):', over)
    print('meta', meta)
    print('hands-off', ho_pts[::20])


if __name__ == '__main__':
    main()
