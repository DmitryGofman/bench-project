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

## Folding bench: parametric, reverse-engineered
The Rev 2 generator's data (side profile, pivots, hands-off path) is embedded in `index.html`. Its hands-off path is a quasi-static gravity solution: the front frame hangs from pivot A and, at each table angle, settles at the lowest centre of gravity it can reach without entering the floor or the other frames. `foldingSolve()` in `designs-project.js` re-derives this; it reproduces the stored path to 0.07° mean (1.25° max). The profile is therefore parametric, and every change is re-solved and re-swept live:
- **Front seat:** 0–3 extra boards.
- **Tabletop / backrest:** 0–2 extra boards at the front edge, 0–1 at the back edge.
- **Height:** −40 to +100 mm; the legs are lengthened along their own axis.
- **Tidy legs:** the R4 tie is cut flush with the back leg and the R5 foot is chamfered.

An extra rear-seat board is not offered: it hits the front seat in bench pose (38 mm).

## Assembly drawing
The **Assembly** view (and `assembly-drawing.svg`) is an exploded isometric with numbered balloons, the BOM and a title block. Balloon numbers match the BOM sheet and the Buy / BOM tab.

## Buy / BOM, files, drawing BOM (`extras-project.js`, patched in by `make_extras.py`)
- **Buy / BOM tab:**
  - A shopping list by category (timber, bolts/nuts/washers, pivot bearings, lock pins, wood screws, glue & finish, tools), with exact names, catalog / standard numbers, quantities from the live model, supplier links, phones and listed prices. Also downloads as CSV.
  - An assembly plan by sub-assembly in build order, listing the parts and the joint fasteners for each step. Also downloads as Markdown.
- **Drawing tab:** a BOM sheet (timber parts + hardware with catalog numbers and supplier links) under the drawing.
- **Export tab:** one-click download / open links for every generated file, *Download all as .zip*, and links to the files already in the project folder.

Rebuild order after editing: `python3 make_extras.py && python3 make_concepts.py`.

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
