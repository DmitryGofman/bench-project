"""Planar kinematics + clash sweeps for the folding bench family (P1 / V2).

Side-view frame: y horizontal (front = -y), z up. Three rigid assemblies:
  rear  - fixed to the floor
  top   - rotates about B by th (0 = table, -100 = bench)
  front - pinned to `top` at A, free to swing by phi under gravity
Timber parts live in x-layers; two parts can only clash if their x ranges overlap.
"""
import math, json
import numpy as np

def rot(p, c, deg):
    a = math.radians(deg); x, y = p[0]-c[0], p[1]-c[1]
    return (c[0] + x*math.cos(a) - y*math.sin(a), c[1] + x*math.sin(a) + y*math.cos(a))

def sat_pen(A, B):
    """penetration depth of two convex polygons (0 if apart / touching)."""
    best = 1e9
    for P in (A, B):
        n = len(P)
        for i in range(n):
            ex, ey = P[(i+1) % n][0]-P[i][0], P[(i+1) % n][1]-P[i][1]
            L = math.hypot(ex, ey)
            if L < 1e-9: continue
            nx, ny = -ey/L, ex/L
            pa = [nx*q[0]+ny*q[1] for q in A]; pb = [nx*q[0]+ny*q[1] for q in B]
            ov = min(max(pa), max(pb)) - max(min(pa), min(pb))
            if ov <= 0: return 0.0
            best = min(best, ov)
    return best

class Model:
    def __init__(self, F):
        self.F = F
        self.B = tuple(F['B']); self.A0 = tuple(F['A0'])
        self.parts = [p for p in F['parts'] if p['side'] == 'R']
        self.cparts = []; seen = set()
        for p in F['parts']:
            if p['side'] == 'C':
                k = (p['id'], tuple(map(tuple, p['poly'])))
                if k not in seen: seen.add(k); self.cparts.append(p)
        self.all = self.parts + self.cparts

    def pose(self, th, phi):
        A = rot(self.A0, self.B, th); dA = (A[0]-self.A0[0], A[1]-self.A0[1])
        def tf(asm):
            if asm == 'top':   return lambda q: rot(q, self.B, th)
            if asm == 'front': return lambda q: tuple(np.add(rot(q, self.A0, phi), dA))
            return lambda q: tuple(q)
        out = []
        for p in self.all:
            f = tf(p['asm'])
            out.append((p, [f(q) for q in p['poly']]))
        return out

    def clashes(self, th, phi, tol=0.6, floor=True, pairs_only=None):
        """list of (idA, idB, depth) and floor penetration (mm)."""
        P = self.pose(th, phi); hits = []; fl = 0.0
        for i in range(len(P)):
            pa, qa = P[i]
            if floor:
                fl = max(fl, -min(q[1] for q in qa))
            for j in range(i+1, len(P)):
                pb, qb = P[j]
                if pa['asm'] == pb['asm']: continue
                if min(pa['x1'], pb['x1']) - max(pa['x0'], pb['x0']) <= 1.0: continue
                d = sat_pen(qa, qb)
                if d > tol: hits.append((pa['id'], pb['id'], round(d, 2)))
        return hits, fl

    def front_mass_centre(self):
        sx = sy = sz = 0.0
        for p in self.parts + self.cparts:
            if p['asm'] != 'front': continue
            poly = p['poly']; area = 0; cy = cz = 0
            for i in range(len(poly)):
                a, b = poly[i], poly[(i+1) % len(poly)]
                c = a[0]*b[1]-b[0]*a[1]; area += c; cy += (a[0]+b[0])*c; cz += (a[1]+b[1])*c
            area *= .5; cy /= 6*area; cz /= 6*area
            w = abs(area) * (p['x1']-p['x0'] if p['side'] == 'C' else 2*(p['x1']-p['x0']))
            sx += w; sy += w*cy; sz += w*cz
        return (sy/sx, sz/sx)

    def feasible(self, th, phi):
        h, fl = self.clashes(th, phi)
        return (not h) and fl < 0.3

    def handsoff(self, ths, phi0=0.0, step=0.25, span=130):
        """quasi-static: at each fold angle the front swings to the lowest centre of mass
        reachable from the previous pose without crossing a contact."""
        com = self.front_mass_centre(); phi = phi0; out = []
        for th in ths:
            # feasible interval around phi
            if not self.feasible(th, phi):
                # nudge to nearest feasible
                found = None
                for k in range(1, int(span/step)):
                    for s in (1, -1):
                        if self.feasible(th, phi + s*k*step): found = phi + s*k*step; break
                    if found is not None: break
                if found is None: out.append((th, None)); continue
                phi = found
            def zc(ph):
                A = rot(self.A0, self.B, th)
                c = rot(com, self.A0, ph)
                return c[1] + (A[1]-self.A0[1])
            # descend along feasible interval
            while True:
                moved = False
                for s in (1, -1):
                    n = phi + s*step
                    if self.feasible(th, n) and zc(n) < zc(phi) - 1e-9:
                        phi = n; moved = True; break
                if not moved: break
            out.append((th, phi))
        return out

def load_data(path, var):
    """read `var NAME = {...};` from a generated app data file."""
    t = open(path, encoding='utf-8').read()
    return json.loads(t[t.index('var %s = ' % var) + len('var %s = ' % var):t.rindex(';')])
