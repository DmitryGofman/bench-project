# Furniture Kit — bench project build

Open `index.html` in a browser. It's a single self-contained file with no dependencies, using raw WebGL.

Based on Furniture Kit prototype 04 (`source-prototype04.html`, unchanged), with this project's designs added:

| Design | Variants | Matches folder | Notes |
|---|---|---|---|
| Folding picnic bench | P1 Rev 2 | `folding-P1/rev2/` | Fold slider (0–100°), hands-off or held-level motion, pivots / pins / bolts / screws shown in 3D, Hardware tab, mechanism checks |
| Folding picnic bench | V2 Simple | `folding-V2/` | From the video: three sub-assemblies, two pivots per side, no stop blocks, all 38×89. See `folding-V2/design-notes.md` |
| Simple garden bench | G1 | `simple-G1/` | Parametric; reproduces the exported parts.json part-for-part |
| Modern frame bench | M1, M2 | `modern-M1/`, `modern-M2/` | Parametric; reproduces the exported parts.json part-for-part |

The original bench / table / shelf designs are still there.

Every folder's `project.json` loads through **Export → Load a saved design** with no adjustments.

## What was added to the app
- **Profile parts** (`ctx.prism`): a convex side-view polygon extruded along X. These are used for the rounded pivot ends and stop blocks. They work in the 3D view, hidden-line drawing, picking, explode, clash check, flat patterns, and the FreeCAD and Fusion exports.
- **Hardware tab**: hardware schedule, moving interfaces (bearings, stops, locks), fixed joints and fabrication notes. All of these are supplied by the design. There is also a `hardware.csv` export.
- **Design-supplied checks** in the Checks tab: mechanism sweep, hands-off path, 3D fastener check and endpoint locking.

## Rebuild
```bash
python3 ../folding-V2/build.py        # V2: regenerates app-folding-data.js and re-validates by simulation
python3 make_app.py                   # source + designs-project.js + folding data -> index.html
python3 ../folding-V2/export.py       # V2 exports (needs playwright)
```
Edit `designs-project.js`, not `index.html`.

`folding-P1/rev2/app-folding-data.js` is the checked-in P1 data; P1's own `build.py` is not in this repo, so that file is the source of truth for P1.

