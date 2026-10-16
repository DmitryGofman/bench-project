"""Writes comparison.md, cutting-list.csv and bom.csv from validation.json, p2_data.json and the two mini parts.csv files."""
import json, os, csv, math
HERE = os.path.dirname(os.path.abspath(__file__))
v = json.load(open(os.path.join(HERE, 'validation.json')))
d2 = json.load(open(os.path.join(HERE, 'p2_data.json')))
P1, P2 = v['P1'], v['P2']

def mini_rows(path):
    return {r['file']: r for r in csv.DictReader(open(path))}
m1 = mini_rows(os.path.join(HERE, '..', 'folding-P1', 'mini', 'parts.csv'))
m2 = mini_rows(os.path.join(HERE, 'mini', 'parts.csv'))
tot = lambda m: sum(float(r['volume_mm3']) for r in m.values())/1000

def pct(a, b): return f'{(b-a)/a*100:+.0f} %'

# ---------------- cutting list and BOM ----------------
parts = d2['parts']
rows = []
for p in parts:
    if p['kind'] == 'plate':
        rows.append([p['tag'].replace('-R', ''), p['name'], '18 mm birch plywood, 2 plies laminated = 36 mm', 4, f"{p['blank']} x {p['W']}", 'right and left, 2 plies each; profile in drawing-plates.svg / profiles-mm.dxf'])
    elif p['kind'] == 'lug':
        rows.append([p['tag'].replace('-R', ''), p['name'], '18 mm birch plywood, 2 plies laminated = 36 mm (offcuts)', 4, f"{p['blank']} x {p['W']}", 'right and left, 2 plies each'])
boards = {}
for p in parts:
    if p['kind'] == 'board': boards.setdefault(p['id'], []).append(p)
for k, bs in boards.items():
    rows.append([k, f"{k} board", 'sawn softwood 38 x 89', len(bs), f"{bs[0]['blank']}", {'S2': 'front seat', 'S3': 'rear seat', 'S4': 'table / backrest'}[k]])
with open(os.path.join(HERE, 'cutting-list.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'part', 'material', 'qty', 'size mm', 'note']); w.writerows(rows)

lay = d2['layout']; stack = lay['T']*2+lay['GAP']
sleeve = stack-10-15+0.5
bom = [
    ['H01', 4, 'M10 x 70 hex bolt, ISO 4017, A4-70 stainless (or HDG 8.8)', 'Pivots A and B, one per pivot per side (same as P1)'],
    ['H02', 4, 'M10 nyloc nut, ISO 10511, A4', 'Torque fully: the bolt clamps the sleeve, not the plywood'],
    ['H03', 8, 'M10 flat washer ISO 7089 (Ø20 x 2), A4', 'Head and nut side of each pivot'],
    ['H04', 4, f'Pivot sleeve: stainless tube OD14 x 1.5 wall, cut {sleeve:.1f} long, ends square & deburred', f'= {stack:.0f} plate stack - 10 - 15 counterbores + 0.5 float (P1: 54.5)'],
    ['H05', 4, 'Plain bushing ID14 / OD18 x 25, sintered bronze or POM', 'Pressed into the front plate and the table plate (head side), flush with the moving face'],
    ['H06', 4, 'Plain bushing ID14 / OD18 x 20, sintered bronze or POM', 'Pressed into the table plate and the rear plate (nut side)'],
    ['H07', 4, 'Thrust washer UHMW-PE or PTFE, ID14.5 / OD40 / 3.0 thick', 'Between the moving faces at each pivot'],
    ['H08', 2, 'Ball-lock quick-release pin Ø10, stainless, usable grip >= 75 mm, lanyard', 'One per side, through the front plate into the table plate (table / bench hole)'],
    ['H10', math.ceil(P2['production']['screws_5x70']*1.1), 'Exterior structural screw 5 x 70, countersunk Torx', f"{P2['production']['screws_5x70']} fitted + 10 % spare: 3 per lug (18) + boards (42). P1: {P1['production']['screws_5x70']} fitted"],
    ['H11', 1, 'Exterior PU / D4 adhesive or epoxy', 'Ply-to-ply lamination of every plate and lug, lugs to plates. Not on moving faces'],
    ['M01', 1, '18 mm birch plywood (exterior glue), 2440 x 1220', f"{P2['production']['plates']['plies']} plies nested on {P2['production']['plates']['sheets']} sheet (drawing-plate-nesting.svg)"],
    ['M02', P2['production']['bars_2400'], 'Sawn softwood 38 x 89, 2400 long', 'Seat and table boards S2, S3, S4 (P1: %d bars incl. frame members)' % P1['production']['bars_2400']],
]
with open(os.path.join(HERE, 'bom.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'qty', 'specification', 'note']); w.writerows(bom)

# ---------------- comparison.md ----------------
a, b = P1['metrics'], P2['metrics']; pa, pb = P1['production'], P2['production']
L = []
L.append('# P1 Rev 2 (laminated members) vs P2 (plywood plates): same checks, side by side\n')
L.append('Both use the same fold geometry (pivots A and B, 100° fold, seat 450, table 755, length 1520). Everything below is computed by `p2_validate.py` '
         'from `folding_p1_data.json` and `p2_data.json` unless it says "assumption". Full-size mm.\n')
L.append('## Does it still work? (same result for both)\n')
L.append('| Check | P1 Rev 2 | P2 |\n|---|---|---|')
L.append(f"| Clash sweep 0–100°, 0.25° steps, front seat held level and hands-off | {len(P1['clashes'])} clashes | {len(P2['clashes'])} clashes |")
L.append(f"| Clearance of every pair that is not a deliberate contact | ≥ {P1['min_clearance_of_all_other_pairs_mm']} mm | ≥ {P2['min_clearance_of_all_other_pairs_mm']} mm |")
L.append(f"| Hands-off: front frame hangs at (gravity solver; reproduces P1's stored curve to {P1['hands_off']['max_deviation_from_P1_stored_deg']}°) | {P1['hands_off']['hanging_angle_deg']}° | {P2['hands_off']['hanging_angle_deg']}° |")
L.append(f"| Hands-off: jams | none | none |")
L.append(f"| Hands-off: swing event (front frame leaves the floor, fold ≈ 27°) | {P1['hands_off']['jumps'][0][1]:.0f}° → {P1['hands_off']['jumps'][0][2]:.0f}° | {P2['hands_off']['jumps'][0][1]:.0f}° → {P2['hands_off']['jumps'][0][2]:.0f}° |")
fr = lambda r: f"{r[1]-r[0]:.1f}°" if abs(r[1]-r[0]) < 9 else f"{r[0]:.0f}° to {(0.0 if abs(r[1]) < 0.1 else r[1]):.0f}° (lifting is free, pressing down is blocked)"
L.append(f"| Table endpoint: free rotation of the front frame with the pin out | {fr(P1['free_rotation_at_table_deg'])} (locked by T4 and the floor) | {fr(P2['free_rotation_at_table_deg'])} (locked) |")
L.append(f"| Bench endpoint: free rotation range with the pin out | {fr(P1['free_rotation_at_bench_deg'])} | {fr(P2['free_rotation_at_bench_deg'])} |")
gp = lambda d: ', '.join(f"{k.replace('-R','')}: {x:.2f}" for k, x in d.items())
L.append(f"| Gap at the stops, table pose (mm) | {gp(P1['stop_gaps_table_mm'])} | {gp(P2['stop_gaps_table_mm'])} |")
L.append(f"| Gap at the stops, bench pose (mm) | {gp(P1['stop_gaps_bench_mm'])} | {gp(P2['stop_gaps_bench_mm'])} |")
L.append(f"| Lock-pin hole misalignment, table / bench | {P1['pin_misalignment_table_mm']} / {P1['pin_misalignment_bench_mm']} mm | {P2['pin_misalignment_table_mm']} / {P2['pin_misalignment_bench_mm']} mm |")
t1, t2 = P1['tipover'], P2['tipover']
L.append(f"| Tip-over, seat-edge margin (table, front / rear seat) | {t1['table']['seat_edge_margins_mm'][0][1]:.0f} / {t1['table']['seat_edge_margins_mm'][1][1]:.0f} mm | {t2['table']['seat_edge_margins_mm'][0][1]:.0f} / {t2['table']['seat_edge_margins_mm'][1][1]:.0f} mm |")
L.append(f"| Tip-over, bench: 90 kg on the edge + 150 N push on the backrest, safety factor | {t1['bench']['push_safety_factor']} | {t2['bench']['push_safety_factor']} |")
L.append('')
L.append('## What changes\n')
L.append('| | P1 Rev 2 | P2 | change |\n|---|---|---|---|')
def row(name, x, y, unit='', better=None):
    ch = pct(x, y) if isinstance(x, (int, float)) and x else ''
    L.append(f'| {name} | {x}{unit} | {y}{unit} | {ch} |')
row('Pieces in the bench (frames + boards)', a['pieces_total'], b['pieces_total'])
row('Frame pieces per side', a['pieces_per_side'], b['pieces_per_side'])
row('Member-to-member joints (glued laps, bolted lap)', pa['member_joints'], pb['member_joints'])
row('Screws 5 x 70', pa['screws_5x70'], pb['screws_5x70'])
row('M8 bolts', pa['m8_bolts'], pb['m8_bolts'])
row('Layers across the width', a['layers_across_width'], b['layers_across_width'])
row('Side stack width', a['stack_width_mm'], b['stack_width_mm'], ' mm')
row('Frame mass (softwood 500 kg/m³; plywood 680 kg/m³)', a['frame_mass_kg'], b['frame_mass_kg'], ' kg')
row('Bench mass', a['mass_kg'], b['mass_kg'], ' kg')
row('Sawn 38 x 89 bars (2400)', pa['bars_2400'], pb['bars_2400'])
L.append(f"| Plywood 18 mm sheets (2440 x 1220) | 0 | {pb['plates']['sheets']} (yield {pb['plates']['yield_on_sheets']*100:.0f} %) | |")
row('Sawing length (P1: crosscuts; P2: every outline, curves included)', pa['sawing_m'], pb['sawing_m'], ' m')
row('Material cost estimate (project prices; plywood sheet 240)', pa['total_cost'], pb['total_cost'])
L.append('')
L.append('Cost basis: sawn 38 x 89 at 3.0 per 1000 mm² per metre (the rate in `simple-G1/project.json`), the 18 mm birch sheet at 240 '
         '(also from that file). No labour, glue, hardware or VAT. Hardware is the same for both except the 6 M8 bolts and 38 fewer screws in P2.\n')
L.append('## Joints and strength (screening only, not a certification)\n')
t = P1['production']['t1_t2_bolted_lap']
L.append(f"* **P1's weakest connection is the bolted T1/T2 lap**: two M8 bolts carry the backrest-lean moment ({t['moment_kNmm']} kN·mm, {t['bolt_arm_mm']} mm apart): "
         f"{t['force_per_bolt_kN']} kN per bolt against {t['embedment_capacity_kN']} kN timber embedment, utilisation {t['utilisation']}. Fine for this load, thin margin for a bigger one. "
         "P2 has no such joint: T1 and T2 are one plate.")
L.append(f"* **The stop lugs are the critical glue lines in both designs.** At the 4 kN stop reaction quoted in P1's design review, T4 sees "
         f"{P1['production']['lug_glue_shear_MPa_at_4kN']['T4-R/T1-R']} MPa in P1 and {P2['production']['lug_glue_shear_MPa_at_4kN']['T4-R/TP-R']} MPa in P2 against about 1 MPa design shear for PU glue: no margin in either. "
         f"S1 improves from {P1['production']['lug_glue_shear_MPa_at_4kN']['S1-R/R4-R']} to {P2['production']['lug_glue_shear_MPa_at_4kN']['S1-R/RP-R']} MPa because it lands on a plate instead of one tie. T4 needs more area or a through bolt in either design.")
g = P2['grain_check']
L.append(f"* **P2's plates have to be plywood.** A solid panel has one grain direction; the front plate has a long leg at 60° and a horizontal seat bearer. "
         f"At {g['bending_stress_MPa']} MPa bending the cross-grain member would be at utilisation {g['solid_panel_utilisation_F1_off_grain_60deg']} (tension perpendicular to grain). "
         f"In 2 x 18 mm cross-ply birch it is {g['plywood_utilisation']} (P1's timber members: {g['P1_utilisation']}). Plywood strength is a conservative design value, not tested.")
L.append('')
L.append('## Printing the 1:5 mini versions (same generator, same method)\n')
L.append('| Part | P1: overhang / bed contact / height / volume | P2: overhang / bed contact / height / volume |\n|---|---|---|')
import re
def desc(r):
    n = r['print note']; ov = re.search(r'overhang (\d+)', n).group(1); ct = re.search(r'contact (\d+)', n).group(1)
    return f"{ov} mm² / {ct} mm² / {float(r['Z_mm']):.0f} mm / {float(r['volume_mm3'])/1000:.0f} cm³"
for k in ('Rear-assembly', 'Front-assembly', 'Table-assembly'):
    L.append(f'| {k} | {desc(m1[k])} | {desc(m2[k])} |')
L.append(f"| **Total volume** | {tot(m1):.0f} cm³ | {tot(m2):.0f} cm³ ({pct(tot(m1), tot(m2))}) |")
L.append('')
L.append('P1\'s front assembly has no flat face to lie on (it prints lying on its legs). P2\'s front plate has a flat face, so it can stand on its side with a 4200 mm² base, but then it is 152 mm tall and needs supports under the upper plate; its lowest-support orientation (lying, 61 mm tall) needs about the same as P1\'s.\n')
open(os.path.join(HERE, 'comparison.md'), 'w').write('\n'.join(L)+'\n')
print('\n'.join(L))
