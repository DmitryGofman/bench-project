"""Isometric render of the mini bench with every printed part in its own colour.
    python3 render_iso.py [step_file] [out_png]"""
import sys, os, re, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from build123d import import_step
HERE = os.path.dirname(os.path.abspath(__file__))
step = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'step', 'mini-bench-P1-table.step')
png = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'preview-iso-parts.png')

COL = {'Rear-assembly': '#1f5fa8', 'Front-assembly': '#c1121f', 'Table-assembly': '#1b9e6b'}
NAMES = {'Rear-assembly': 'Rear assembly: both sides + seat panel (R1-R5, S1, S3)',
         'Front-assembly': 'Front assembly: both sides + seat panel (F1-F3, S2)',
         'Table-assembly': 'Table-back assembly: both sides + panel (T1, T2, T4, T5, S4)'}

root = import_step(step)
tris, cols = [], []
for g in root.children:
    for s in g.children:
        lab = s.label or ''
        if g.label.startswith('Hard'): c = '#222222'
        elif lab in COL: c = COL[lab]
        else: continue
        v, t = s.tessellate(0.03)
        V = np.array([[p.X, p.Y, p.Z] for p in v]); tris.append(V[np.array(t)]); cols.append(np.full(len(t), 0)); cols[-1] = [c]*len(t)
def subdivide(T, C, maxedge=3.5):
    """split big triangles so per-triangle depth sorting has no visible artefacts"""
    T = np.asarray(T); C = np.asarray(C, dtype=object)
    while True:
        e = np.max([np.linalg.norm(T[:, i]-T[:, (i+1) % 3], axis=1) for i in range(3)], axis=0)
        big = e > maxedge
        if not big.any(): return T, list(C)
        a, b, c = T[big][:, 0], T[big][:, 1], T[big][:, 2]
        ab, bc, ca = (a+b)/2, (b+c)/2, (c+a)/2
        new = np.concatenate([np.stack(x, 1) for x in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))])
        T = np.concatenate([T[~big], new]); C = np.concatenate([C[~big], np.tile(C[big], 4)])
T = np.concatenate(tris); C = sum(cols, [])
T, C = subdivide(T, C)

# isometric camera: from front-right-above (front of the table is -Y)
az, el = np.radians(35), np.radians(30)
f = -np.array([np.sin(az)*np.cos(el), -np.cos(az)*np.cos(el), np.sin(el)])   # view direction (towards scene)
up = np.array([0, 0, 1.0]); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
P = np.stack([T@r, T@u], -1); depth = (T@f).mean(1)
n = np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True)+1e-12
light = np.array([-0.4, -0.5, 0.8]); light /= np.linalg.norm(light)
sh = 0.55+0.45*np.abs(n@light)
rgb = np.array([matplotlib.colors.to_rgb(c) for c in C])*sh[:, None]
order = np.argsort(-depth)                                   # far first
fig, ax = plt.subplots(figsize=(13, 8.5), dpi=110)
ax.add_collection(PolyCollection(P[order], facecolors=np.clip(rgb[order], 0, 1), edgecolors=np.clip(rgb[order]*.8, 0, 1), linewidths=.15))
ax.autoscale_view(); ax.set_aspect('equal'); ax.axis('off')
name = os.path.basename(step)
pose = 'bench' if name.endswith('-bench.step') else 'mid-fold 50°' if 'mid-fold' in name else 'table'
design = (re.search(r'-(P\d)-', os.path.basename(step)) or [None, 'P1'])[1]
ax.set_title(f'Mini folding bench {design} (1:5), {pose} pose: one colour per printed part', fontsize=11)
if design != 'P1':        # the member lists in the legend are P1's; other designs get the plain names
    NAMES = {k: re.sub(r' \(.*\)', '', v) for k, v in NAMES.items()}
leg = [Patch(color=COL[k], label=NAMES[k]) for k in NAMES] + [Patch(color='#222222', label='Hardware (bolts, lock pins; not printed)')]
ax.legend(handles=leg, loc='center left', bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
plt.tight_layout(); plt.savefig(png, bbox_inches='tight'); print('wrote', png)
