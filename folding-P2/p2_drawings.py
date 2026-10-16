"""Drawings for P2 (and the P1/P2 layer comparison): SVG + DXF, all from p2_data.json / folding_p1_data.json."""
import json, math, os, sys
from shapely.geometry import Polygon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kin import Bench, rot2

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = Bench(os.path.join(HERE, '..', 'folding-P1', 'mini', 'folding_p1_data.json'))
P2 = Bench(os.path.join(HERE, 'p2_data.json'))
COL = {'rear': '#1f5fa8', 'top': '#1b9e6b', 'front': '#c1121f'}
LUG = '#e6851e'; BOARD = '#d9b87c'

def path_of(g, tf):
    out = []
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    for p in polys:
        for r in [p.exterior] + list(p.interiors):
            out.append('M' + ' L'.join('%.1f,%.1f' % tf(x, y) for x, y in r.coords) + 'Z')
    return ' '.join(out)

def pose_svg(bn, th, phi, tf, parts_filter=None):
    s = []
    for p in sorted(bn.parts, key=lambda p: (p['side'] == 'C', p.get('kind') == 'lug')):
        g = bn.shape(p, th, phi)
        if p['side'] == 'C':
            col, op, sw = BOARD, 1.0, 0.6
        elif p.get('kind') == 'lug' or p['g'] == 'stop':
            col, op, sw = LUG, 1.0, 0.6
        else:
            col, op, sw = COL[p['asm']], 0.78, 0.6
        s.append(f'<path d="{path_of(g, tf)}" fill="{col}" fill-opacity="{op}" stroke="#1a1a1a" stroke-width="{sw}" fill-rule="evenodd"/>')
    return '\n'.join(s)

def fold_sequence(bn, path, title, name):
    sc = 0.2; W = 5; cw = 1330*sc+30; ch = 800*sc+70
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw*W/1.0:.0f}" height="{ch+60:.0f}" font-family="Helvetica,Arial" font-size="11">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="14" y="20" font-size="15" font-weight="bold">{title}</text>',
           '<text x="14" y="38" fill="#444">Right-hand side, side view. Blue = rear frame (fixed), green = table / back frame, red = front frame, orange = stop lugs, tan = boards. Hands-off front seat (gravity solver).</text>']
    for i, th in enumerate([0, -25, -50, -75, -100]):
        phi = bn.phi_table(th)
        if abs(phi) < 0.05: phi = 0.0
        ox = 14+i*cw+160*0+ 810*sc*0
        x0 = ox+810*sc          # y = -810 at the left edge
        z0 = 70+800*sc
        tf = lambda y, z, x0=x0, z0=z0: (x0+y*sc, z0-z*sc)
        svg.append(f'<g>')
        svg.append(f'<line x1="{ox}" y1="{z0}" x2="{ox+cw-20}" y2="{z0}" stroke="#555" stroke-width="1.2"/>')
        svg.append(pose_svg(bn, th, phi, tf))
        for lab, pt, off in (('A', rot2(bn.A0, bn.B, th), (6, -8)), ('B', bn.B, (6, -8))):
            px, py = tf(*pt); svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="white" stroke="black" stroke-width="1.4"/><text x="{px+off[0]:.1f}" y="{py+off[1]:.1f}" font-weight="bold">{lab}</text>')
        pose = 'TABLE' if th == 0 else 'BENCH' if th == -100 else 'FOLDING'
        svg.append(f'<text x="{ox+4}" y="{70+800*sc+22}" font-size="12" font-weight="bold">{pose}   fold {-th}°   front frame {phi:.0f}°</text>')
        if th == 0:
            for z, lab in ((450, 'seat 450'), (755, 'table 755')):
                zz = z0-z*sc; svg.append(f'<line x1="{ox}" y1="{zz}" x2="{ox+8}" y2="{zz}" stroke="#222"/><text x="{ox+10}" y="{zz+4}" font-size="10">{lab}</text>')
        svg.append('</g>')
    svg.append('</svg>')
    open(path, 'w').write('\n'.join(svg))

def plates_sheet(bn, path):
    sc = 0.26; pad = 30
    items = [p for p in bn.parts if p['side'] == 'R']
    items.sort(key=lambda p: (p['kind'] != 'plate', p['asm']))
    # layout in a row-major grid, using each shape's bounding box in the table-pose frame
    cols = [('RP-R', 'FP-R', 'TP-R'), ('S1-R', 'T4-R', 'T5-R')]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1450" height="760" font-family="Helvetica,Arial" font-size="11">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="20" y="24" font-size="16" font-weight="bold">P2 plate and lug profiles, right-hand side (left is the mirror image). mm.</text>',
           '<text x="20" y="42" fill="#444">Each plate = two 18 mm birch plywood plies glued face to face, 36 mm. Profiles are in the table-pose frame: y horizontal (front = negative), z up from the floor. Inside corners R20, front-top corner of the rear plate R6.</text>']
    byTag = {p['tag']: p for p in bn.parts}
    pin = bn.F['validation']['pin']
    pos = {'RP-R': (30, 80), 'FP-R': (560, 80), 'TP-R': (30, 330), 'S1-R': (560, 400), 'T4-R': (820, 400), 'T5-R': (1070, 400)}
    for tag, (ox, oy) in pos.items():
        p = byTag[tag]; g = p['_poly']; b = g.bounds
        w = (b[2]-b[0])*sc; h = (b[3]-b[1])*sc
        tf = lambda y, z, b=b, ox=ox, oy=oy, h=h: (ox+(y-b[0])*sc, oy+h-(z-b[1])*sc)
        col = COL[p['asm']] if p['kind'] == 'plate' else LUG
        svg.append(f'<path d="{path_of(g, tf)}" fill="{col}" fill-opacity=".30" stroke="#111" stroke-width="1.4" fill-rule="evenodd"/>')
        svg.append(f'<text x="{ox}" y="{oy-8}" font-size="13" font-weight="bold">{p["name"]}   x {p["x0"]:.0f}..{p["x1"]:.0f}</text>')
        # overall dimensions
        svg.append(f'<line x1="{ox}" y1="{oy+h+14}" x2="{ox+w}" y2="{oy+h+14}" stroke="#444"/><text x="{ox+w/2-30:.0f}" y="{oy+h+28}">{b[2]-b[0]:.0f} (y)</text>')
        svg.append(f'<line x1="{ox+w+14}" y1="{oy}" x2="{ox+w+14}" y2="{oy+h}" stroke="#444"/><text x="{ox+w+18}" y="{oy+h/2:.0f}">{b[3]-b[1]:.0f} (z)</text>')
        svg.append(f'<text x="{ox}" y="{oy+h+44}" fill="#333">y {b[0]:.0f}..{b[2]:.0f}, z {b[1]:.0f}..{b[3]:.0f}; area {g.area/100:.0f} cm²</text>')
        # holes
        marks = []
        if tag == 'FP-R': marks = [(bn.A0, 'A  Ø10.5 + Ø30 x10 (head side, outer face)'), (pin['F1_hole'], 'L  Ø10.5 lock pin')]
        if tag == 'TP-R': marks = [(bn.A0, 'A  Ø10.5 + Ø30 x15 (nut side, inner face)'), (bn.B, 'B  Ø10.5 + Ø30 x10 (head side, outer face)'),
                                   (pin['T1_table'], 'L table'), (pin['T1_bench'], 'L bench')]
        if tag == 'RP-R': marks = [(bn.B, 'B  Ø10.5 + Ø30 x15 (nut side, inner face)')]
        for k, ((y, z), lab) in enumerate(marks):
            cx, cy = tf(y, z); r = 15*sc if 'Ø30' in lab else 5.25*sc
            svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="white" stroke="#c00" stroke-width="1.2"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.5" fill="#c00"/>')
            svg.append(f'<text x="{cx+12:.1f}" y="{cy+14+k*11:.1f}" fill="#900" font-size="10">{lab.split()[0]} ({y:.1f}, {z:.1f})</text>')
    # hole key
    svg.append('<text x="30" y="560" font-size="12" font-weight="bold">Holes (red): coordinates are (y, z) in the table-pose frame, mm</text>')
    notes = ['A pivot: M10 bolt, head in a Ø30 x 10 counterbore on the front plate outer face, nut in a Ø30 x 15 counterbore on the table plate inner face, 3 mm thrust washer between the faces.',
             'B pivot: head in a Ø30 x 10 counterbore on the table plate outer face (flush: the front seat slides past it), nut in Ø30 x 15 on the rear plate inner face.',
             f'Lock pin Ø10.5: one hole in the front plate, two in the table plate (table / bench), {bn.F["validation"]["pin"]["radius_from_A"]} mm from A. Match-drill at assembly.',
             'Lugs S1, T4, T5: 2 x 18 mm plywood, glued to the plate face (S1 on the rear plate outer face, T4/T5 on the table plate outer face) with 3 screws 5x70 each.']
    for i, t in enumerate(notes): svg.append(f'<text x="30" y="{582+i*18}" font-size="11">{t}</text>')
    svg.append('</svg>')
    open(path, 'w').write('\n'.join(svg))

def layers_sheet(path):
    sc = 2.2; pad = 30
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" font-family="Helvetica,Arial" font-size="11">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="20" y="24" font-size="16" font-weight="bold">Layers across the width, right-hand side (plan view, x to the right, outer face on the right)</text>',
           '<text x="20" y="42" fill="#444">Every bar is one piece; the three frames pass each other only because they sit in different x layers. P1 uses 8 layers, P2 uses 5.</text>']
    def block(bn, y0, title):
        svg.append(f'<text x="{pad}" y="{y0-12}" font-size="14" font-weight="bold">{title}</text>')
        rows = {'rear': 0, 'top': 1, 'front': 2}
        names = {'rear': 'rear', 'top': 'table', 'front': 'front'}
        cnt = {}
        xs = [p['x0'] for p in bn.parts if p['side'] == 'R'] + [p['x1'] for p in bn.parts if p['side'] == 'R']
        xmin, xmax = min(xs), max(xs)
        for p in sorted(bn.parts, key=lambda p: (rows[p['asm']], p['x0'], p['tag'])):
            if p['side'] != 'R': continue
            r = rows[p['asm']]; k = cnt.get((r, round(p['x0'])), 0); cnt[(r, round(p['x0']))] = k+1
            x = pad+(p['x0']-xmin)*sc; w = (p['x1']-p['x0'])*sc
            y = y0+r*72+k*17
            col = COL[p['asm']] if p.get('kind') != 'lug' and p['g'] != 'stop' else LUG
            svg.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="15" fill="{col}" fill-opacity=".7" stroke="#222"/><text x="{x+3:.1f}" y="{y+11}" font-size="10" fill="white" font-weight="bold">{p["tag"].replace("-R","")}</text>')
        for lab, r in names.items():
            pass
        for a, lab in ((0, 'rear frame'), (1, 'table frame'), (2, 'front frame')):
            svg.append(f'<text x="{pad+(xmax-xmin)*sc+14:.0f}" y="{y0+rows[["rear","top","front"][a]]*72+12}" fill="#333">{lab}</text>')
        svg.append(f'<line x1="{pad}" y1="{y0+3*72+2}" x2="{pad+(xmax-xmin)*sc:.0f}" y2="{y0+3*72+2}" stroke="#444"/>'
                   f'<text x="{pad}" y="{y0+3*72+18}">x {xmin:.0f} .. {xmax:.0f}  =  {xmax-xmin:.0f} mm stack</text>')
    block(P1, 90, 'P1 Rev 2: 13 members per side, 8 layers, 196 mm')
    block(P2, 420, 'P2: 3 plates + 3 lugs per side, 5 layers, 114 mm')
    svg.append('</svg>')
    open(path, 'w').write('\n'.join(svg))

def dxf(path):
    import ezdxf
    doc = ezdxf.new('R2010'); doc.units = 4        # mm
    msp = doc.modelspace()
    byTag = {p['tag']: p for p in P2.parts}
    x = 0.0
    for tag in ('RP-R', 'FP-R', 'TP-R', 'S1-R', 'T4-R', 'T5-R'):
        p = byTag[tag]; g = p['_poly']; b = g.bounds
        layer = tag.replace('-R', '')
        doc.layers.add(layer)
        dx = x-b[0]; dy = -b[1]
        msp.add_lwpolyline([(a+dx, c+dy) for a, c in g.exterior.coords[:-1]], close=True, dxfattribs={'layer': layer})
        for r in g.interiors:
            msp.add_lwpolyline([(a+dx, c+dy) for a, c in r.coords[:-1]], close=True, dxfattribs={'layer': layer})
        pin = P2.F['validation']['pin']
        holes = {'FP-R': [(P2.A0, 10.5), (pin['F1_hole'], 10.5)], 'TP-R': [(P2.A0, 10.5), (P2.B, 10.5), (pin['T1_table'], 10.5), (pin['T1_bench'], 10.5)],
                 'RP-R': [(P2.B, 10.5)]}.get(tag, [])
        doc.layers.add(layer+'_HOLES', color=1)
        for (hy, hz), d in holes:
            msp.add_circle((hy+dx, hz+dy), d/2, dxfattribs={'layer': layer+'_HOLES'})
        msp.add_text(f'{tag} ({p["name"]}) cut 4 plies (2 per side x 2 sides); lugs 4 plies', height=12, dxfattribs={'layer': layer}).set_placement((x, -40))
        x += (b[2]-b[0])+120
    doc.saveas(path)

if __name__ == '__main__':
    fold_sequence(P2, os.path.join(HERE, 'drawing-fold-sequence.svg'), 'P2 fold sequence: table to bench (hands-off)', 'P2')
    fold_sequence(P1, os.path.join(HERE, 'drawing-fold-sequence-P1.svg'), 'P1 Rev 2 fold sequence: table to bench (hands-off), for comparison', 'P1')
    plates_sheet(P2, os.path.join(HERE, 'drawing-plates.svg'))
    layers_sheet(os.path.join(HERE, 'drawing-layers.svg'))
    dxf(os.path.join(HERE, 'profiles-mm.dxf'))
    print('drawings written')
