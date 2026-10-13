# Furniture Kit — bench project build

Open `index.html` in a browser. It's a single self-contained file with no dependencies, using raw WebGL.

Based on Furniture Kit prototype 04 (`source-prototype04.html`, unchanged), with this project's designs added:

| Design | Variants | Matches folder | Notes |
|---|---|---|---|
| Folding picnic bench | P1 Rev 2 | `folding-P1/rev2/` | Fold slider (0–100°), hands-off or held-level motion, pivots / pins / bolts / screws shown in 3D, Hardware tab, mechanism checks |
| Simple garden bench | G1 | `simple-G1/` | Parametric; reproduces the exported parts.json part-for-part |
| Modern frame bench | M1, M2 | `modern-M1/`, `modern-M2/` | Parametric; reproduces the exported parts.json part-for-part |

The original bench / table / shelf designs are still there.

Every folder's `project.json` loads through **Export → Load a saved design** with no adjustments.

## What was added to the app
- **Profile parts** (`ctx.prism`): a convex side-view polygon extruded along X. These are used for the rounded pivot ends and stop blocks. They work in the 3D view, hidden-line drawing, picking, explode, clash check, flat patterns, and the FreeCAD and Fusion exports.
- **Hardware tab**: hardware schedule, moving interfaces (bearings, stops, locks), fixed joints and fabrication notes. All of these are supplied by the design. There is also a `hardware.csv` export.
- **Design-supplied checks** in the Checks tab: mechanism sweep, hands-off path, 3D fastener check and endpoint locking.

## Concepts (`concepts.html`)
Four clean-sheet bench ↔ table designs built on a shared engine (`concepts-project.js`, assembled by `make_concepts.py` from `index.html`). All use 45 × 95 timber, which is the Israeli "2×4", with layered side frames, M12 pivots on Ø18 sleeves and Ø12 lock pins. Each one runs a live mechanism sweep: the side profile is stepped through the motion and every pair of parts sharing a layer is tested for overlap.

| Concept | Motion | Modes | Daybed |
|---|---|---|---|
| C1 Twin flip-back | backrest swings 75° on 1 pivot per end | two benches / picnic table | 1 m × 1.8 m, seat-to-seat |
| C2 Swing-top | whole top swings 105° on 1 pivot per end | table / bench with head-high back | — |
| C3 Level-lift | top on parallel links, stays level | table / daybed with fixed back | 1.5 m × 1.8 m |
| C4 Lift-off leaves | none: two loose leaves | table / backed lounger / flat daybed | 1.6 m × 1.8 m |

## Swing-top variants (`swing.html`)
The swing-top (C2) with a second bench that joins the main seat into a sofa, built in four ways. All four share arm planks fixed to the swing arms: armrests and carry handles in bench mode, slanted struts landing on stop blocks in table mode. They also share a rear kick foot so leaning back cannot tip the bench. *Convert* 0–50 % swings the top; 50–100 % moves the second bench.

| Variant | Second bench | Sofa |
|---|---|---|
| S1 Runner slide | legless, slides on UHMW-faced wooden ledgers | ≈ 800 deep, back + arms |
| S2 Free dock | loose 3-board stool-bench, dowel-docked | ≈ 700 deep |
| S3 Glide links | hung on parallel links, swings back level | ≈ 800 deep |
| S4 Tumble stool | box stool: seat upright, footrest / stored under the seat on its side | main seat + footrest |

Suppliers: `suppliers.html` (`suppliers-tel-aviv.md`).

## Mobile
`index.html` is responsive: at ≤760px the 3D view pins to the top and the controls and tables scroll beneath it. Touch: one finger orbits (or pans in Pan mode), two fingers pinch to zoom, tap selects a part. Source of the changes: `mobile.css`, `mobile.js` (patched in by `make_app.py`).

## Rebuild
```bash
python3 ../folding-P1/rev2/build.py   # regenerates geometry, drawings and app-folding-data.js
python3 make_app.py                   # source + designs-project.js + folding data -> index.html
```
Edit `designs-project.js`, not `index.html`.

Live site: https://dmitrygofman.github.io/bench-project/
