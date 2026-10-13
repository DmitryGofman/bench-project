"""Patch app/index.html with extras-project.js: Buy / BOM tab, assembly plan,
drawing BOM sheet and one-click Files. Re-runnable: the script block between
the EXTRAS markers is replaced, the one-time HTML/CSS hooks are added once.

    python3 make_extras.py && python3 make_concepts.py
"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, 'index.html')
src = open(P, encoding='utf-8').read()
js = open(os.path.join(HERE, 'extras-project.js'), encoding='utf-8').read()
B, E = '/* <EXTRAS> */', '/* </EXTRAS> */'

def once(old, new):
    global src
    if new in src: return
    assert src.count(old) == 1, 'anchor %r found %d times' % (old[:60], src.count(old))
    src = src.replace(old, new)

CSS = """
  /* extras: Buy / BOM tab, files box */
  .buyhead{padding:12px 16px 8px;color:var(--dim);font-size:12px;line-height:1.6}
  .buyhead b{color:var(--fg);font-family:var(--sans)}
  .buyhead .ghost{margin-left:6px;text-decoration:none;display:inline-block}
  table.buy{margin:0 0 6px}
  table.buy td{white-space:normal;vertical-align:top;line-height:1.45}
  table.buy td a{color:var(--blue)}
  table.buy tr.cat td{background:#2b3138;color:var(--pencil);font-family:var(--sans);font-size:10px;
                      letter-spacing:.14em;text-transform:uppercase;padding:6px 16px}
  table.buy .small{font-size:11px} table.buy .ref{font-size:10px;color:var(--pencil)}
  .sa{margin:6px 16px 14px;border:1px solid var(--rule);border-left:2px solid var(--pencil);padding:8px 0 4px;background:var(--panel2)}
  .sa .sat{font-family:var(--sans);font-weight:600;padding:0 12px 6px}
  .sa ol{margin:6px 0 6px 28px;padding:0;color:var(--dim);font-size:12px;line-height:1.55}
  .sa .dim.small{padding:0 12px}
  .files{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:11.5px}
  .files a{color:var(--blue);text-decoration:none} .files a:hover{text-decoration:underline}
"""
once('</style>\n\n<div id="rail">', CSS + '</style>\n\n<div id="rail">')
once('<button data-p="hw">Hardware</button>', '<button data-p="hw">Hardware</button>\n    <button data-p="buy">Buy / BOM</button>')
once('<div class="pane" id="paneHw"><div id="hwBody" style="padding:4px 16px 24px"></div></div>',
     '<div class="pane" id="paneHw"><div id="hwBody" style="padding:4px 16px 24px"></div></div>\n'
     '    <div class="pane" id="paneBuy"><div id="buyBody" style="padding:0 0 24px"></div></div>')
once("checks:'paneChecks',hw:'paneHw',", "checks:'paneChecks',hw:'paneHw',buy:'paneBuy',")
once('<div class="pane" id="paneExport">\n      <div class="exp">',
     '<div class="pane" id="paneExport">\n      <div id="filesBox" style="padding:14px 16px 4px"></div>\n      <div class="exp">')
once('renderHardware(); renderCost(); renderExport();',
     'renderHardware(); renderCost(); renderExport(); renderBuy(); renderFiles();')
once("function renderDrawing(){\n  document.getElementById('svgWrap').innerHTML = svgDrawing(",
     "function renderDrawing(){\n  setTimeout(function(){ document.getElementById('svgWrap').insertAdjacentHTML('beforeend', svgBom(MODEL)); }, 0);\n"
     "  document.getElementById('svgWrap').innerHTML = svgDrawing(")
block = B + '\n' + js + '\n' + E + '\n'
if B in src:
    src = re.sub(re.escape(B) + r'.*?' + re.escape(E) + r'\n', lambda m: block, src, flags=re.S)
else:
    once('/* ---- rebuild ---- */', block + '/* ---- rebuild ---- */')
open(P, 'w', encoding='utf-8').write(src)
print('index.html patched with extras, %d bytes' % len(src))
