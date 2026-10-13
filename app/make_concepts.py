"""Build the concept pages from the bench-project app (index.html) + concepts-project.js.

    python3 make_concepts.py

    concepts.html  four clean-sheet bench <-> table concepts (concept1..4)
    swing.html     swing-top with four ways to join the second bench (slide1..4)
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
con = open(os.path.join(HERE, 'concepts-project.js'), encoding='utf-8').read()

PAGES = [
    ('concepts.html', 'Bench concepts', 'concept', 'concept1', 'bench project · four concepts'),
    ('swing.html', 'Swing-top variants', 'slide', 'slide1', 'swing-top · four ways to join the second bench'),
]

for out, title, prefix, first, eyebrow in PAGES:
    src = BASE

    def patch(old, new, count=1):
        global src
        n = src.count(old)
        assert n == count, 'anchor found %d times (want %d): %r' % (n, count, old[:80])
        src = src.replace(old, new)

    patch('<title>Furniture Kit — bench project</title>', '<title>%s</title>' % title)
    # concepts go in after the project designs; then only this page's designs stay in the picker
    patch("/* ---- folding picnic bench, Rev 2 --------------------------------------- */",
          con + "\n/* ---- folding picnic bench, Rev 2 --------------------------------------- */")
    patch("""if(initGL()){
  selectDesign('folding');""", """Object.keys(DESIGNS).forEach(function(k){ if(k.indexOf('%s') !== 0) delete DESIGNS[k]; });
if(initGL()){
  selectDesign('%s');""" % (prefix, first))
    patch("""    ' The schedule and exports still work; only the 3D view needs it.';
  selectDesign('folding');""", """    ' The schedule and exports still work; only the 3D view needs it.';
  selectDesign('%s');""" % first)
    patch("""  var ids = ['folding','simple','modern'].concat(Object.keys(DESIGNS).filter(function(k){
    return ['folding','simple','modern'].indexOf(k) < 0; }));""", """  var ids = Object.keys(DESIGNS).sort();""")
    patch('<p class="eyebrow">furniture-kit · prototype 04</p>', '<p class="eyebrow">%s</p>' % eyebrow)
    open(os.path.join(HERE, out), 'w', encoding='utf-8').write(src)
    print('app/%s written, %d bytes' % (out, len(src)))
