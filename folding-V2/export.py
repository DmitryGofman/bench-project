"""Export the V2 deliverables from the built app (headless Chromium).

    python3 export.py        # needs: pip install playwright (Chromium is pre-installed)

Writes project.json, parts.json, hardware.csv, schedule.csv, cutting-plan.txt, freecad.py,
drawing-table.svg and drawing-bench.svg next to this file. project.json loads through
Export -> Load a saved design with no adjustments.
"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
APP = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'app', 'index.html'))
CHROMIUM = os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium')


def export(pg, key):
    return pg.evaluate("(k)=>EXPORTS.filter(e=>e.k===k)[0].make()", key)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROMIUM, args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    pg = b.new_page()
    pg.goto(APP); pg.wait_for_timeout(800)
    pg.evaluate("selectVariant('V2')")
    pg.evaluate("S.params.fold=0; rebuild();")
    out = {'project.json': 'design.json', 'parts.json': 'parts.json', 'hardware.csv': 'hw.csv',
           'schedule.csv': 'cut.csv', 'cutting-plan.txt': 'nest.txt', 'freecad.py': 'freecad.py',
           'drawing-table.svg': 'draw.svg'}
    for fn, k in out.items():
        open(os.path.join(HERE, fn), 'w', encoding='utf-8').write(export(pg, k))
    pg.evaluate("S.params.fold=100; rebuild();")
    open(os.path.join(HERE, 'drawing-bench.svg'), 'w', encoding='utf-8').write(export(pg, 'draw.svg'))
    b.close()
print('exported to', HERE)
