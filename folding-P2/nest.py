"""Raster nesting of the P2 plates on edge-glued softwood panel (38 mm). Grain runs along the panel length (x).
Each plate may only be placed in orientations that keep its main member along the grain."""
import math, json
import numpy as np
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry import Polygon

RES = 5.0          # mm per cell
GAP = 6.0          # mm between parts (kerf + router clearance)

def mask(poly, res=RES):
    minx, miny, maxx, maxy = poly.bounds
    g = poly.buffer(GAP/2)
    minx, miny, maxx, maxy = g.bounds
    w = int(math.ceil((maxx-minx)/res)); h = int(math.ceil((maxy-miny)/res))
    im = Image.new('1', (w, h), 0); d = ImageDraw.Draw(im)
    def pts(r): return [((x-minx)/res, (y-miny)/res) for x, y in r.coords]
    d.polygon(pts(g.exterior), fill=1)
    for i in g.interiors: d.polygon(pts(i), fill=0)
    return np.array(im, dtype=bool), (minx, miny)

def nest(plates, W=600.0, L=2400.0, angles_for=None):
    """plates: list of (name, polygon). angles_for(name) -> list of rotation angles (deg) allowed.
    Returns list of panels, each a list of placements (name, angle, dx, dy, polygon)."""
    nx, ny = int((L+GAP)/RES), int((W+GAP)/RES)      # parts carry GAP/2 each side, panel edges need none
    panels = []
    order = sorted(plates, key=lambda t: -t[1].area)
    for name, poly in order:
        placed = False
        for pi in range(len(panels)+1):
            if pi == len(panels): panels.append(dict(grid=np.zeros((ny, nx), bool), items=[]))
            grid = panels[pi]['grid']; best = None
            for ang in angles_for(name):
                g = affinity.rotate(poly, ang, origin='centroid')
                m, (ox, oy) = mask(g)
                h, w = m.shape
                if h > ny or w > nx: continue
                for x in range(0, nx-w+1, 2):
                    if best and x > best[0]: break
                    for y in range(0, ny-h+1, 2):
                        if not (grid[y:y+h, x:x+w] & m).any():
                            if best is None or (x, y) < best[:2]: best = (x, y, ang, m, g, ox, oy)
                            break
            if best:
                x, y, ang, m, g, ox, oy = best
                grid[y:y+m.shape[0], x:x+m.shape[1]] |= m
                gg = affinity.translate(g, x*RES-ox, y*RES-oy)
                panels[pi]['items'].append((name, ang, gg)); placed = True; break
        assert placed, 'plate does not fit on the panel: ' + name
    # drop an empty trailing panel
    return [p for p in panels if p['items']]

def svg(panels, W, L, path, title):
    sc = 0.3; pad = 20
    h = len(panels)*(W*sc+40)+pad
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{L*sc+2*pad}" height="{h+20}" font-family="Helvetica,Arial" font-size="11">',
         f'<rect width="100%" height="100%" fill="white"/><text x="{pad}" y="14" font-size="13" font-weight="bold">{title}</text>']
    cols = {'RP': '#1f5fa8', 'FP': '#c1121f', 'TP': '#1b9e6b', 'S1': '#999', 'T4': '#999', 'T5': '#999'}
    for i, p in enumerate(panels):
        oy = pad+i*(W*sc+40)+10
        s.append(f'<text x="{pad}" y="{oy+10}">sheet {i+1}: {int(L)} x {int(W)}</text>')
        oy += 16
        s.append(f'<rect x="{pad}" y="{oy}" width="{L*sc}" height="{W*sc}" fill="#f3e9d2" stroke="#333"/>')
        for name, ang, g in p['items']:
            def d(r): return 'M'+' L'.join(f'{pad+x*sc:.1f},{oy+y*sc:.1f}' for x, y in r.coords)+'Z'
            path_d = d(g.exterior)+''.join(d(i) for i in g.interiors)
            s.append(f'<path d="{path_d}" fill="{cols[name[:2]]}" fill-opacity=".55" stroke="#222" fill-rule="evenodd"/>')
            c = g.centroid; s.append(f'<text x="{pad+c.x*sc-12:.0f}" y="{oy+c.y*sc:.0f}" font-weight="bold">{name}</text>')
    s.append('</svg>')
    open(path, 'w').write('\n'.join(s))
