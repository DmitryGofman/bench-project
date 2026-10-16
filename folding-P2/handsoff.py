"""Quasi-static 'hands-off' simulation: the table is turned by hand, the front frame hangs from pivot A under gravity,
frictionless, resting on the floor and on the rear frame. Returns the front frame's absolute rotation phi(theta)."""
import math, itertools
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from kin import Bench, rot2

RHO = 500.0   # kg/m3, softwood (same for plates and boards)

def front_com(bn, board_cross=(89.0, 38.0)):
    """centre of mass (y,z) of the whole front assembly in table pose, and its mass (kg).
    plates/members count twice (left and right); boards by cross-section x length."""
    mv = np.zeros(2); m = 0.0
    for p in bn.parts:
        if p['asm'] != 'front': continue
        g = p['_poly']
        if p['side'] == 'C':
            vol = g.area*(p['x1']-p['x0'])
        else:
            vol = 2*g.area*(p['x1']-p['x0'])
        w = vol*bn.rho(p)                                    # mass-proportional weight
        c = g.centroid; mv += w*np.array([c.x, c.y]); m += w
    return mv/m, m*1e-9

def simulate(bn, step=0.25, verbose=False):
    A0 = np.array(bn.A0); com, mass = front_com(bn)
    v = com-A0
    phi_eq = math.degrees(math.atan2(-1, 0)-math.atan2(v[1], v[0]))      # rotation that puts the COM straight below A
    phi_eq = (phi_eq+180) % 360-180
    front = [p for p in bn.parts if p['asm'] == 'front']
    obst = [p for p in bn.parts if p['asm'] != 'front']
    pairs = [(f, o) for f in front for o in obst if bn.xover(f, o) > 0]
    def feasible(th, phi, tol=0.05):
        fs = {f['tag']: bn.shape(f, th, phi) for f in front}
        for f in front:
            if fs[f['tag']].bounds[1] < -1e-6: return False                    # below the floor
        for f, o in pairs:
            g = fs[f['tag']]; h = bn.shape(o, th, 0.0)
            if g.bounds[2] < h.bounds[0] or h.bounds[2] < g.bounds[0] or g.bounds[3] < h.bounds[1] or h.bounds[3] < g.bounds[1]: continue
            if g.intersection(h).area > tol: return False
        return True
    out = [(0.0, 0.0)]; phi = 0.0; contacts = []
    # table pose: foot on the floor
    assert feasible(0.0, 0.0), 'table pose is not feasible'
    n = int(round(100/step))
    for k in range(1, n+1):
        th = -k*step
        if not feasible(th, phi):                       # the support moved: back off to the nearest feasible phi
            for j in range(1, 800):
                for s in (+1, -1):
                    if feasible(th, phi+s*j*step*0.5): phi = phi+s*j*step*0.5; break
                else: continue
                break
            else: raise RuntimeError(f'JAM at fold {-th}: no feasible phi near {phi}')
        d = 1 if phi_eq > phi else -1                    # then slide towards the hanging equilibrium until blocked
        while abs(phi_eq-phi) > 1e-6:
            nxt = phi+d*min(0.25, abs(phi_eq-phi))
            if feasible(th, nxt): phi = nxt
            else:                                         # settle exactly on the contact: bisect to 0.004 deg
                lo, hi = phi, nxt
                for _ in range(6):
                    mid = (lo+hi)/2
                    if feasible(th, mid): lo = mid
                    else: hi = mid
                phi = lo
                break
        out.append((th, phi))
    return out, phi_eq, com, mass

if __name__ == '__main__':
    import sys, json
    path = sys.argv[1]
    bn = Bench(path)
    curve, phi_eq, com, mass = simulate(bn)
    print('COM (y,z) of front assembly', com.round(0), 'mass', round(mass, 1), 'kg   hanging angle phi_eq', round(phi_eq, 1))
    ref = dict((round(h[0], 2), h[1]) for h in bn.H)
    print('   fold   sim   P1-stored')
    for th, ph in curve:
        if abs(th/5-round(th/5)) < 1e-9: print(f'   {-th:4.0f}  {ph:5.1f}   {ref.get(round(th,2),float("nan")):5.1f}')
