"""Build app/concepts.html = the bench-project app (index.html) with only the four concept designs.

    python3 make_concepts.py
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
con = open(os.path.join(HERE, 'concepts-project.js'), encoding='utf-8').read()

def patch(old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, 'anchor found %d times (want %d): %r' % (n, count, old[:80])
    src = src.replace(old, new)

patch('<title>Furniture Kit — bench project</title>', '<title>Bench concepts</title>')
# concepts go in after the project designs; then only the concepts stay in the picker
patch("/* ---- folding picnic bench, Rev 2 --------------------------------------- */",
      con + "\n/* ---- folding picnic bench, Rev 2 --------------------------------------- */")
patch("""if(initGL()){
  selectDesign('folding');""", """Object.keys(DESIGNS).forEach(function(k){ if(!/^concept/.test(k)) delete DESIGNS[k]; });
if(initGL()){
  selectDesign('concept1');""")
patch("""    ' The schedule and exports still work; only the 3D view needs it.';
  selectDesign('folding');""", """    ' The schedule and exports still work; only the 3D view needs it.';
  selectDesign('concept1');""")
patch("""  var ids = ['folding','simple','modern'].concat(Object.keys(DESIGNS).filter(function(k){
    return ['folding','simple','modern'].indexOf(k) < 0; }));""", """  var ids = Object.keys(DESIGNS).sort();""")
patch('<p class="eyebrow">furniture-kit · prototype 04</p>', '<p class="eyebrow">bench project · four concepts</p>')
open(os.path.join(HERE, 'concepts.html'), 'w', encoding='utf-8').write(src)
print('app/concepts.html written, %d bytes' % len(src))
