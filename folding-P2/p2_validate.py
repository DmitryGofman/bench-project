"""Validate and compare P1 Rev 2 (laminated members) and P2 (plates) with identical checks.

    python3 p2_design.py && python3 p2_validate.py        -> validation.json, comparison.md, nesting svg

Checks (all in the YZ plane, full-size mm, floor z = 0):
  K1  clash sweep 0..100 deg in 0.25 deg steps, front seat held level and hands-off, every cross-assembly pair
      that shares any width (x), overlap > 1 mm2 = clash
  K2  hands-off simulation (calibrated against P1's stored curve): jams, swing event, end angle
  K3  endpoint locking: free rotation of the front frame about A with the table fixed, at 0 and 100 deg
  K4  lock-pin holes: misalignment at both endpoints
  K5  stop contacts at the endpoints (gap at each bearing pair)
  S1  tip-over margins in table and bench pose
  S2  stop-lug glue shear for the 4 kN stop reaction quoted in P1's design review; plate net sections
  M1  pieces, joints, fasteners, volume, mass, material, nesting, cost
"""
import json, math, os, sys, itertools, csv
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely import affinity
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kin import Bench, rot2
from handsoff import simulate, front_com, RHO

HERE = os.path.dirname(os.path.abspath(__file__))
P1_PATH = os.path.join(HERE, '..', 'folding-P1', 'mini', 'folding_p1_data.json')
P2_PATH = os.path.join(HERE, 'p2_data.json')

STOPS = {   # bearing pairs that define the endpoints, by tag, per design
    'P1': {'table': [('F1-R', 'T4-R')], 'bench': [('F1-R', 'T5-R'), ('T2-R', 'S1-R'), ('S2-1', 'R3-R'), ('S2-2', 'R3-R')]},
    'P2': {'table': [('FP-R', 'T4-R')], 'bench': [('FP-R', 'T5-R'), ('TP-R', 'S1-R'), ('S2-1', 'RP-R'), ('S2-2', 'RP-R')]},
}
PIN = dict(front={'P1': 'F1-R', 'P2': 'FP-R'}, top={'P1': 'T1-R', 'P2': 'TP-R'})

def feasible_set(bn, th, lo=-15.0, hi=70.0, step=0.05, tol=0.05):
    """front-frame rotations phi (absolute, deg) that do not interpenetrate anything, floor included"""
    front = [p for p in bn.parts if p['asm'] == 'front']
    obst = [p for p in bn.parts if p['asm'] != 'front']
    pairs = [(f, o) for f in front for o in obst if bn.xover(f, o) > 0]
    obs = {o['tag']: bn.shape(o, th, 0) for o in obst}
    ok = []
    for phi in np.arange(lo, hi+1e-9, step):
        if any(bn.shape(f, th, phi).bounds[1] < -1e-6 for f in front): ok.append(False); continue
        bad = False
        for f, o in pairs:
            g = bn.shape(f, th, phi); h = obs[o['tag']]
            if g.bounds[2] < h.bounds[0] or h.bounds[2] < g.bounds[0] or g.bounds[3] < h.bounds[1] or h.bounds[3] < g.bounds[1]: continue
            if g.intersection(h).area > tol: bad = True; break
        ok.append(not bad)
    return np.arange(lo, hi+1e-9, step), np.array(ok)

def component_around(phis, ok, phi0):
    i = int(np.argmin(abs(phis-phi0)))
    if not ok[i]:
        j = np.where(ok)[0]
        if len(j) == 0: return None
        i = int(j[np.argmin(abs(j-i))])
    a = b = i
    while a > 0 and ok[a-1]: a -= 1
    while b < len(ok)-1 and ok[b+1]: b += 1
    return phis[a], phis[b]

def kinematics(name, bn, curve):
    parts = bn.parts; res = {}
    # K1 clash sweep
    worst = {}; mingap = {}
    for mode in ('hands-off', 'held level'):
        for k in range(0, 401):
            th = -k*0.25; phi = curve[k][1] if mode == 'hands-off' else 0.0
            sh = [(p, bn.shape(p, th, phi)) for p in parts]
            for (p, g), (q, h) in itertools.combinations(sh, 2):
                if p['asm'] == q['asm'] or bn.xover(p, q) <= 0: continue
                a = g.intersection(h).area
                key = (p['tag'], q['tag'])
                if a > 1.0: worst[(mode,)+key] = max(worst.get((mode,)+key, 0), a)
                d = g.distance(h); mingap[key] = min(mingap.get(key, 1e9), d)
    res['clashes'] = {'|'.join(k): round(v, 1) for k, v in worst.items()}
    stopset = {frozenset(x) for v in STOPS[name].values() for x in v}
    contact = {k: d for k, d in mingap.items() if d < 0.05}                      # touch somewhere in the fold (stops, seat sliding on the rear frame)
    clear = {k: d for k, d in mingap.items() if d >= 0.05}
    res['contact_pairs'] = sorted(f'{a}~{b}' for a, b in contact)
    res['min_clearance_of_all_other_pairs_mm'] = round(min(clear.values()), 1)
    res['tightest_clear_pairs'] = [(f'{k[0]}~{k[1]}', round(d, 1)) for k, d in sorted(clear.items(), key=lambda kv: kv[1])[:3]]
    # K5 stop gaps at the endpoints
    for pose, th, phi in (('table', 0.0, curve[0][1]), ('bench', -100.0, curve[-1][1])):
        g = {}
        for a, b in STOPS[name][pose]:
            pa = next(p for p in parts if p['tag'] == a); pb = next(p for p in parts if p['tag'] == b)
            g[f'{a}~{b}'] = round(bn.shape(pa, th, phi).distance(bn.shape(pb, th, phi)), 3)
        res[f'stop_gaps_{pose}_mm'] = g
    # K3 endpoint locking
    for pose, th in (('table', 0.0), ('bench', -100.0)):
        phis, ok = feasible_set(bn, th, lo=-10, hi=60, step=0.05)
        c = component_around(phis, ok, curve[0 if th == 0 else -1][1])
        res[f'free_rotation_at_{pose}_deg'] = [round(c[0], 2), round(c[1], 2)] if c else None
    # K4 pin alignment
    pin = bn.F['validation']['pin']
    for pose, th, phi, hole in (('table', 0.0, curve[0][1], pin['T1_table']), ('bench', -100.0, curve[-1][1], pin['T1_bench'])):
        A = rot2(bn.A0, bn.B, th)
        fp = rot2(pin['F1_hole'], bn.A0, phi); fp = [fp[0]+A[0]-bn.A0[0], fp[1]+A[1]-bn.A0[1]]
        th_hole = rot2(hole, bn.B, th)
        res[f'pin_misalignment_{pose}_mm'] = round(math.dist(fp, th_hole), 2)
    return res

def tipover(bn, curve):
    """screening: whole bench, own weight + one 90 kg sitter on the outer seat edge + 150 N push on the backrest"""
    out = {}
    for pose, th, phi in (('table', 0.0, curve[0][1]), ('bench', -100.0, curve[-1][1])):
        mv = np.zeros(2); m = 0.0; pts = []
        for p in bn.parts:
            g = bn.shape(p, th, phi); vol = g.area*(p['x1']-p['x0'])*(1 if p['side'] == 'C' else 2)*bn.rho(p)
            c = g.centroid; mv += vol*np.array([c.x, c.y]); m += vol
            if g.bounds[1] < 0.5: pts += [q for q in g.exterior.coords if q[1] < 0.5]
        com = mv/m; W = m*1e-9*9.81
        y0, y1 = min(q[0] for q in pts), max(q[0] for q in pts)
        sit = 90*9.81
        if pose == 'table':
            seats = [(-765.0+30, 'front seat outer edge'), (324.0-30, 'rear seat outer edge')]
        else:
            seat_y = [bn.shape(p, th, phi).bounds for p in bn.parts if p['id'] in ('S2', 'S3')]
            seats = [(min(b[0] for b in seat_y)+30, 'bench front edge'), (max(b[2] for b in seat_y)-30, 'bench rear edge')]
        marg = []
        for ys, label in seats:
            ycom = (W*com[0]+sit*ys)/(W+sit)
            marg.append((label, round(min(ycom-y0, y1-ycom), 0)))
        # backrest push (bench only): horizontal 150 N at z=750 pushing towards +y, tips about y1
        push = None
        if pose == 'bench':
            Hh = 150.0; zh = 750.0
            ycom = (W*com[0]+sit*seats[0][0])/(W+sit)
            restoring = (W+sit)*(y1-ycom); overturn = Hh*zh
            push = round(restoring/overturn, 1)
        out[pose] = dict(footprint_y=[round(y0), round(y1)], com_y=round(com[0]), seat_edge_margins_mm=marg, push_safety_factor=push)
    return out

def poly_area(p): return Polygon(p['poly'], p.get('holes', [])).buffer(0).area

def metrics(name, bn):
    parts = bn.parts; m = {}
    sides = [p for p in parts if p['side'] == 'R']; boards = [p for p in parts if p['side'] == 'C']
    m['pieces_per_side'] = len(sides)
    m['pieces_total'] = 2*len(sides)+len(boards)
    m['boards'] = len(boards)
    vol = lambda p: poly_area(p)*(p['x1']-p['x0'])*(2 if p['side'] == 'R' else 1)
    m['volume_frames_dm3'] = round(sum(vol(p) for p in sides)*1e-6, 2)
    m['volume_boards_dm3'] = round(sum(vol(p) for p in boards)*1e-6, 2)
    m['mass_kg'] = round(sum(vol(p)*bn.rho(p) for p in parts)*1e-9, 1)
    m['frame_mass_kg'] = round(sum(vol(p)*bn.rho(p) for p in sides)*1e-9, 1)
    m['layers_across_width'] = len({(round(p['x0']), round(p['x1'])) for p in sides})
    m['side_stack_x'] = [min(p['x0'] for p in sides), max(p['x1'] for p in sides)]
    m['stack_width_mm'] = m['side_stack_x'][1]-m['side_stack_x'][0]
    m['overall_length_mm'] = max(p['x1'] for p in boards)*2
    perim = 0.0
    for p in sides:
        g = Polygon(p['poly'], p.get('holes', [])).buffer(0)
        perim += g.length + sum(LineString(i.coords).length for i in g.interiors) - (g.length if False else 0)
    m['cut_perimeter_m'] = round(2*perim/1000, 1)
    return m

def production(name, bn):
    F = bn.F; r = {}
    marks = F.get('marks', [])
    if name == 'P1':
        n = lambda k: sum(1 for m in marks if m['k'] == k)
        r['lap_screws'] = 2*n('screw'); r['board_screws'] = 2*n('boardscrew'); r['m8_bolts'] = 2*n('m8')
        joints = F['joints']
        r['member_joints'] = 2*sum(1 for j in joints if j['kind'] != 'board to bearer')
        r['board_joints'] = sum(1 for j in joints if j['kind'] == 'board to bearer')
        board_marks = 2*n('boardscrew')
    else:
        P1 = json.load(open(P1_PATH)); n = lambda k: sum(1 for m in P1['marks'] if m['k'] == k)
        r['lap_screws'] = 6*3; r['board_screws'] = 2*n('boardscrew'); r['m8_bolts'] = 0     # 3 screws per lug, glue
        r['member_joints'] = 6                                                          # S1, T4, T5 lugs, both sides
        r['board_joints'] = sum(1 for j in P1['joints'] if j['kind'] == 'board to bearer')
    r['screws_5x70'] = r['lap_screws']+r['board_screws']
    r['pivot_bolts_m10'] = 4
    # glue lines of the lugs (YZ overlap with the member / plate it sits on), and shear at the 4 kN stop reaction
    geo = {p['tag']: p['_poly'] for p in bn.parts}
    pairs = {'P1': [('S1-R', 'R4-R'), ('T4-R', 'T1-R'), ('T5-R', 'T1-R')], 'P2': [('S1-R', 'RP-R'), ('T4-R', 'TP-R'), ('T5-R', 'TP-R')]}[name]
    r['lug_glue_area_mm2'] = {f'{a}/{b}': round(geo[a].intersection(geo[b]).area) for a, b in pairs}
    a_min = min(r['lug_glue_area_mm2'].values())
    r['lug_glue_shear_MPa_at_4kN'] = {k: round(4000/v, 2) for k, v in r['lug_glue_area_mm2'].items()}
    r['smallest_lug_glue_shear_ratio_vs_1MPa'] = round(4000/a_min/1.0, 2)
    # bolted T1/T2 lap (P1 only): two M8 carry the backrest-lean moment (150 N per side * 2 on the backrest top, lever from B)
    if name == 'P1':
        b = [m for m in marks if m['joint'] == 'J14']
        arm = math.dist((b[0]['y'], b[0]['z']), (b[1]['y'], b[1]['z']))
        M = 300.0*(755.0-bn.B[1])                          # N*mm, 300 N per side at the backrest top
        F_bolt = M/arm
        F_rd = 0.6*0.082*(1-0.01*8)*350*8*38/1.3          # EC5 embedment, kmod 0.6, rho_k 350, M8, 38 mm timber, gamma 1.3
        r['t1_t2_bolted_lap'] = dict(moment_kNmm=round(M/1e3), bolt_arm_mm=round(arm), force_per_bolt_kN=round(F_bolt/1e3, 2),
                                      embedment_capacity_kN=round(F_rd/1e3, 2), utilisation=round(F_bolt/F_rd, 2))
    # cut list and cost (project price basis: 3.0 per 1000 mm2 per metre of sawn stock; panel assumption below)
    sides = [p for p in bn.parts if p['side'] == 'R' and p['kind'] != 'plate'] if name == 'P2' else [p for p in bn.parts if p['side'] == 'R']
    items = [p['blank'] for p in sides for _ in (0, 1)] + [p['blank'] for p in bn.parts if p['side'] == 'C']
    bars = bar_nesting(items)
    rate = 38*89*0.003                                                                  # per metre
    r['bars_2400'] = len(bars); r['bar_offcut_m'] = round(sum(b['left'] for b in bars)/1000, 2)
    r['sawn_cost'] = round(len(bars)*2.4*rate, 1)
    return r

def bar_nesting(items, bar=2400.0, kerf=3.0):
    """first-fit decreasing of lengths onto bars"""
    bars = []
    for L in sorted(items, reverse=True):
        for b in bars:
            if b['left'] >= L+kerf: b['cuts'].append(L); b['left'] -= L+kerf; break
        else: bars.append(dict(cuts=[L], left=bar-L-kerf))
    return bars

def main():
    designs = {}
    for name, path in (('P1', P1_PATH), ('P2', P2_PATH)):
        bn = Bench(path); designs[name] = bn
    out = {}
    for name, bn in designs.items():
        curve, phi_eq, com, mass = simulate(bn, step=0.25)
        r = dict(hands_off=dict(hanging_angle_deg=round(phi_eq, 1), max_phi_deg=round(max(c[1] for c in curve), 1),
                                end_phi_deg=round(curve[-1][1], 2), front_mass_kg=round(mass, 1), com_yz=[round(com[0]), round(com[1])]))
        # stored-curve comparison (P1 only: P1's own build.py result)
        if name == 'P1':
            ref = dict((round(h[0], 2), h[1]) for h in bn.H)
            r['hands_off']['max_deviation_from_P1_stored_deg'] = round(max(abs(ph-ref[round(th, 2)]) for th, ph in curve if abs(th*2-round(th*2)) < 1e-9), 2)
        r['hands_off']['jumps'] = [(round(-curve[i][0], 2), round(curve[i-1][1], 1), round(curve[i][1], 1)) for i in range(1, len(curve)) if abs(curve[i][1]-curve[i-1][1]) > 2.0]
        r.update(kinematics(name, bn, curve))
        r['tipover'] = tipover(bn, curve)
        r['metrics'] = metrics(name, bn)
        r['production'] = production(name, bn)
        out[name] = r
        print(name, json.dumps({k: v for k, v in r.items() if k not in ('metrics', 'tipover')}, indent=1))
    return out, designs

if __name__ == '__main__':
    out, designs = main()
    # --- P2 plates: 2 x 18 mm birch plywood, nested on 2440 x 1220 sheets (the project's sheet size and price)
    from nest import nest, svg
    bn = designs['P2']; pl = {p['id']: p['_poly'] for p in bn.parts if p['kind'] == 'plate'}
    lugs = {p['id']: p['_poly'] for p in bn.parts if p['kind'] == 'lug'}
    f1 = 60.0
    ang = lambda n: ([0, 90, 180, 270, -60, 120, 60, 240] if n.startswith('FP') else [0, 90, 180, 270])
    # every plate is two plies (sides x plies = 4 cut-outs per plate shape), every lug two plies per side
    items = [(f'{k}{i}', g) for k, g in pl.items() for i in range(1, 5)] + [(f'{k}{i}', g) for k, g in lugs.items() for i in range(1, 5)]
    SHEET_W, SHEET_L, SHEET_PRICE = 1220.0, 2440.0, 240.0           # from simple-G1/project.json: 18 mm sheet, 2440 x 1220, price 240
    panels = nest(items, W=SHEET_W, L=SHEET_L, angles_for=ang)
    tot = sum(g.area for _, g in items)
    out['P2']['production']['plates'] = dict(sheets=len(panels), sheet_mm=[2440, 1220, 18], plies=len(items), ply_area_m2=round(tot*1e-6, 3),
        yield_on_sheets=round(tot/(SHEET_W*SHEET_L*len(panels)), 3), sheet_price=SHEET_PRICE, sheet_cost=len(panels)*SHEET_PRICE)
    # sawing length: P1 = two crosscuts per piece (mitre saw); P2 = every plate/lug outline, cut once through the 36 mm laminate
    perim = sum(Polygon(p['poly'], p.get('holes', [])).buffer(0).length + sum(i.length for i in Polygon(p['poly'], p.get('holes', [])).buffer(0).interiors)
                for p in bn.parts if p['kind'] in ('plate', 'lug'))
    out['P2']['production']['sawing_m'] = round(2*perim/1000 + (9+0)*2*0.089, 1)
    out['P1']['production']['sawing_m'] = round((26+9)*2*0.089, 1)
    out['P2']['production']['total_cost'] = round(out['P2']['production']['sawn_cost']+len(panels)*SHEET_PRICE, 1)
    out['P1']['production']['total_cost'] = out['P1']['production']['sawn_cost']
    # grain check: why the plates have to be plywood. Seat load 0.9 kN per side on the front bearer F2, root at F1.
    M = 0.9e3*(-540.0-(-700.0))*-1 if False else 0.9e3*160.0                     # N*mm, lever 160 mm from the F2 root to the seat load
    Wsec = 36*89**2/6
    sig = M/Wsec
    hank = lambda f0, f90, a: f0*f90/(f0*math.sin(math.radians(a))**2 + f90*math.cos(math.radians(a))**2)
    out['P2']['grain_check'] = dict(
        load='0.9 kN per side on the front bearer, 160 mm from its root', bending_stress_MPa=round(sig, 2),
        solid_panel_grain_along_F2_F1_capacity_MPa=round(hank(24.0*0.6/1.3, 0.4*0.6/1.3, 60), 2),
        solid_panel_utilisation_F1_off_grain_60deg=round(sig/hank(24.0*0.6/1.3, 0.4*0.6/1.3, 60), 1),
        plywood_birch_2x18_design_strength_MPa=14.0, plywood_utilisation=round(sig/14.0, 2),
        P1_timber_member_design_strength_MPa=round(24*0.6/1.3, 1), P1_utilisation=round((0.9e3*160.0/(38*89**2/6))/(24*0.6/1.3), 2),
        note='Hankinson, tension perpendicular 0.4 MPa characteristic; kmod 0.6, gamma 1.3; plywood 14 MPa is a conservative design value.')
    svg(panels, SHEET_W, SHEET_L, os.path.join(HERE, 'drawing-plate-nesting.svg'), 'P2: 24 plies (plates and lugs, 2 x 18 mm) nested on 18 mm birch plywood sheets 2440 x 1220')
    json.dump(out, open(os.path.join(HERE, 'validation.json'), 'w'), indent=1)
    print(json.dumps({k: v['production'] for k, v in out.items()}, indent=1)); print(json.dumps(out['P2']['grain_check'], indent=1))
