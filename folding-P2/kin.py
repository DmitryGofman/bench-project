"""Shared kinematics for the folding bench (table pose = fold 0; y horizontal, z up, floor z=0)."""
import json, math, itertools
from shapely.geometry import Polygon, LineString, box
from shapely import affinity

def rot2(p, c, deg):
    a = math.radians(deg); x = p[0]-c[0]; y = p[1]-c[1]
    return [c[0]+x*math.cos(a)-y*math.sin(a), c[1]+x*math.sin(a)+y*math.cos(a)]

class Bench:
    def __init__(self, path):
        self.F = json.load(open(path)); F = self.F
        self.B, self.A0, self.H = F['B'], F['A0'], F['handsoff']
        self.parts = F['parts']
        for p in self.parts:
            p['_poly'] = Polygon(p['poly'], [h for h in p.get('holes', [])]).buffer(0)
    def phi_table(self, th):
        H = self.H; i = 0
        while i < len(H)-2 and H[i+1][0] > th: i += 1
        a, b = H[i], H[i+1]; f = 0 if a[0] == b[0] else (th-a[0])/(b[0]-a[0]); return a[1]+f*(b[1]-a[1])
    def shape(self, p, th, phi):
        """shapely geometry of part p when the table has turned to th (deg, <=0) and the front frame by phi about A"""
        g = p['_poly']; asm = p['asm']
        if asm == 'rear': return g
        if asm == 'top': return affinity.rotate(g, th, origin=tuple(self.B))
        A = rot2(self.A0, self.B, th)
        g = affinity.rotate(g, phi, origin=tuple(self.A0))
        return affinity.translate(g, A[0]-self.A0[0], A[1]-self.A0[1])
    def rho(self, p): return p.get('rho', 500.0)
    def xover(self, p, q):
        return min(p['x1'], q['x1']) - max(p['x0'], q['x0'])
