"""poses.svg (side view, four fold angles) and the cut list table for design-notes.md.

    python3 report.py      # reads app-folding-data.js, writes poses.svg, cutlist.md
"""
import json, os, math
import kin

HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, 'app-folding-data.js'), encoding='utf-8').read()
F = json.loads(s[s.index('var FOLDING_V2 = ') + len('var FOLDING_V2 = '):s.rindex(';')])
M = kin.Model(F)
ho = dict((round(a, 2), b) for a, b in F['handsoff'])

COL = {'rear': '#555555', 'top': '#3d85f0', 'front': '#8cc152'}
POSES = [0, -35, -70, -100]
SC = 0.36                      # px per mm
PAD = 40
parts_labelled = set()

def phi_at(th):
    k = min(ho, key=lambda t: abs(t - th)); return ho[k]

W = 0; cells = []
for th in POSES:
    pose = M.pose(th, phi_at(th))
    ys = [q[0] for p, poly in pose for q in poly]; zs = [q[1] for p, poly in pose for q in poly]
    cells.append((th, pose, min(ys), max(ys)))
ymin = min(c[2] for c in cells); ymax = max(c[3] for c in cells)
cw = (ymax - ymin) * SC + 2*PAD; ch = 900*SC + 2*PAD + 30
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="monospace" font-size="11">' % (cw*len(POSES), ch),
       '<rect width="100%" height="100%" fill="#fff"/>']
for i, (th, pose, a, b) in enumerate(cells):
    ox = i*cw + PAD
    def X(y): return ox + (ymax - y) * SC            # back on the left, front on the right
    def Z(z): return PAD + 20 + (880 - z) * SC
    svg.append('<text x="%d" y="%d" font-weight="bold">%s</text>' % (ox, PAD, 'TABLE 0°' if th == 0 else ('BENCH 100°' if th == -100 else 'fold %d°' % -th)))
    svg.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#444" stroke-width="1.5"/>' % (i*cw+10, Z(0), (i+1)*cw-10, Z(0)))
    drawn = set()
    for p, poly in sorted(pose, key=lambda t: {'rear': 0, 'top': 1, 'front': 2}[t[0]['asm']]):
        # right-side parts and centre boards: draw each id once per pose
        pts = ' '.join('%.1f,%.1f' % (X(q[0]), Z(q[1])) for q in poly)
        key = (p['id'], tuple(round(q[0]) for q in poly), tuple(round(q[1]) for q in poly))
        if key in drawn: continue
        drawn.add(key)
        svg.append('<polygon points="%s" fill="%s" fill-opacity="0.55" stroke="#222" stroke-width="0.8"/>' % (pts, COL[p['asm']]))
        if len(poly) <= 5 or p['id'] in ('F1', 'T2', 'R1'):
            cy = sum(q[0] for q in poly)/len(poly); cz = sum(q[1] for q in poly)/len(poly)
            if p['id'] in ('F1', 'T2', 'R1'):
                n = len(poly)//2; cy = (poly[0][0] + poly[n][0])/2; cz = (poly[0][1] + poly[n][1])/2
            svg.append('<text x="%.1f" y="%.1f" font-size="9" text-anchor="middle" fill="#000">%s</text>' % (X(cy), Z(cz)+3, p['id']))
    A = kin.rot(F['A0'], F['B'], th)
    for nm, c in (('A', A), ('B', F['B'])):
        svg.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#c00"/><text x="%.1f" y="%.1f" fill="#c00" font-weight="bold">%s</text>' % (X(c[0]), Z(c[1]), X(c[0])+6, Z(c[1])-6, nm))
svg.append('<text x="%d" y="%d" fill="#555">side view, back on the left, front on the right. black = rear seat, blue = table / backrest, green = front seat + arm. Hands-off front-seat path.</text>' % (PAD, ch-8))
svg.append('</svg>')
open(os.path.join(HERE, 'poses.svg'), 'w', encoding='utf-8').write('\n'.join(svg))

# ---- cut list ---------------------------------------------------------------------------------
qty = {}
for p in F['parts']:
    k = p['id']
    qty.setdefault(k, {'p': p, 'n': 0})
    qty[k]['n'] += 1
rows = ['| Part | Qty | Stock | Blank length | Marking-out outline (length, width), mm |', '|---|---|---|---|---|']
order = ['R1', 'R2', 'R3', 'R4', 'S1', 'T1', 'T2', 'T3', 'S2', 'F1', 'F2', 'F3', 'S3']
for k in order:
    e = qty[k]; p = e['p']; n = e['n']
    # right-side parts are listed once per side already (R) -> the data holds one per pair; count both sides
    n = n*2 if p['side'] == 'R' else n
    if p['side'] == 'C': outline = 'rectangle %d × %d' % (p['blank'], p['W'])
    else:
        fl = p['flat']
        outline = ' → '.join('(%g, %g)' % (a, b) for a, b in fl) if len(fl) <= 6 and p['id'] not in ('R1',) else 'one end rounded R44.5 on the pivot; see drawing'
    name = p['name'].split(' · ')[1]
    rows.append('| %s %s | %d | 38 × %d | %d | %s |' % (k, name, n, p['W'], p['blank'], outline))
open(os.path.join(HERE, 'cutlist.md'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
print('poses.svg, cutlist.md written')
