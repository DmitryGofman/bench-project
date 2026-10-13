# Mini folding picnic bench P1 Rev 2 — 1:5 printable test model

A 1:5 version of the folding bench (table ⇄ bench) for printing in parts and checking the mechanism
before building the full-size one. Generated from the same geometry as the full-size design, so every
member, pivot, stop and lock-pin position is the real one divided by 5.

![side views: table, 50° and bench](preview-side-views.png)
*Right-hand side, table → 50° → bench. Blue = rear frame (fixed), red = front frame, green = table/back frame.*

## Files
| | |
|---|---|
| `step/mini-bench-P1-table.step` | Full assembly, table pose (fold 0°), lock pins in |
| `step/mini-bench-P1-mid-fold-50deg.step` | Same, 50° folded, front seat in its hands-off position, pins pulled |
| `step/mini-bench-P1-bench.step` | Same, bench pose (100°), pins in |
| `stl/parts/*.stl` | One STL per printed part, **already oriented flat for printing** (35 files) |
| `parts.csv` | Part list with printed size and volume |
| `build_mini.py` + `folding_p1_data.json` | Generator and its source geometry |

## Load into Fusion
1. *File → Open → Open from my computer* (or *Insert → Insert into Current Design*) and pick a `.step` file. Units are mm.
2. It arrives as an assembly of four sub-components: **Rear frame (fixed)**, **Front frame (swings on A)**,
   **Table-back frame (swings on B)**, **Hardware**. Every part is a named body. Floor is Z = 0.
3. If it lands on its side, rotate it (Fusion is Y-up by default; the model is Z-up).
4. To play the mechanism in Fusion, ground the rear frame and add two **revolute joints** (axis = X):
   * **Pivot B** — Table-back frame ↔ Rear frame, origin at Y = 0, Z = 73.5 (table pose)
   * **Pivot A** — Front frame ↔ Table-back frame, origin at Y = −71.5, Z = 133.5 (table pose)

   Joint limit on B: 0–100° (table lowers its far edge and becomes the backrest). The front frame is only
   attached at A, so it swings freely under your mouse like the real one does; the app's hands-off path
   shows it staying roughly level (0° at both ends, about 44° tilt at 50° fold). In Fusion, contact between
   bodies is not simulated by default, so use the three STEP poses to check the endpoints.

Importing the table-pose file and adding the joints there is easiest; the other two files are for checking
the endpoints against your joint motion.

## What is, and isn't, 1:5
* **Depth, height, member sections (7.6 × 17.8 mm), pivot positions and stops: exactly 1:5.** The fold
  geometry is planar, so this is what decides whether the mechanism works.
* **Width is not scaled.** True 1:5 would give 304 mm boards, which won't fit most beds. The default is a 190 mm
  overall width (S4 boards) so everything fits a 220 × 220 mm bed. For true width run
  `python3 build_mini.py --width 304` (needs a ~310 mm bed; all other parts are ≤ 142 mm).
* Layer gaps in X are the full-size 3 mm gaps / 5 = **0.6 mm**.
* R3's front-top corner has the 1.2 mm radius (full-size "R6") that S2 slides over while folding.

## Printing
* All 35 files lie flat: side plates print 7.6 mm tall, boards 7.6 mm tall. Largest part 190 × 17.8 mm (boards),
  largest plate F1 96 × 142 mm. Solid volume of all parts ≈ 440 cm³; at normal infill expect roughly 150–250 g of filament.
* PLA/PETG, 0.4 mm nozzle, 0.16–0.2 mm layers, ≥ 3 walls, 25 %+ infill. Plates are thin so walls matter more
  than infill. No supports needed.
* Left and right plates (`_L` / `_R`) are **mirror images, not copies**; print both files.
* Print one of everything in `parts.csv`; quantities are simply the files (S2 ×2, S3 ×2, S4 ×5, everything else L+R).
* Holes are drawn at nominal size (pivot Ø3.4, lock pin Ø2.2, pegs Ø2.0). Printed holes come out small; run a
  3.5 mm drill through the pivot holes and check one pivot before gluing a whole frame.

## Hardware (starting spec, check what you have)
| Qty | Item | Where |
|---|---|---|
| 4 | M3 × 14 socket-head screw | Pivots A and B, one per side each; head sits in a Ø6.6 × 3.4 counterbore, flush |
| 4 | M3 nyloc nut | in the Ø6.8 × 4.4 nut counterbore on the inner face |
| 4 | M3 washer, 0.5 mm thin type | between the two moving faces at each pivot (sets the 0.6 mm gap) |
| 2 | Ø2 mm rod, ~25 mm (or 1.75 mm filament with a bent end) | lock pins: through F1 into T1 (table hole or bench hole) |
| ~96 | 1.75 mm filament, cut ~6.5 mm | registration pegs for the glued laps and boards |
| – | Cyanoacrylate or PLA-friendly epoxy | fixed laps only, **never on a moving face** |

Pivot tightening: snug the nyloc until the play just goes, then back off until the joint swings freely — it
clamps the faces, there is no sleeve at this scale. A drop of thread-lock helps.

## Assembly
Build three rigid frames, each as a left and a right side, then join them with the pivots. The side plates are
the "layers" of the full-size design (R1/R2 → R3/R4/R5 → S1, and so on) and register on 1.75 mm pegs in the
holes marked by the full-size screw positions.

1. **Rear frame** (each side): R1 + R2 are the legs; glue R3 and R4 across them (3 pegs per lap), R5 on R2, S1 on R4.
   Then glue S3-1, S3-2 on the R3 bearers (left and right).
2. **Front frame** (each side): F1 (long leg) with F2 and F3 glued on; then S2-1, S2-2 on the F2 bearers.
3. **Table-back frame** (each side): T1 (bearer), T2 glued to T1 (J14), T4 and T5 on T1; then the five S4 boards across T1/T4/T5.
4. Fit the pivots: B (T2 ↔ R3) and A (F1 ↔ T1), with the thin washer between faces. Head sides are the outer faces of T2 and F1.
5. Fold with the lock pins out; fit them at 0° (table) and at 100° (bench).

## What was checked
* Source mechanism: swept 0–100° in 0.25° steps, held-level and hands-off, over every timber pair — 0 clashes
  (reproduces the full-size validation).
* The finished mini solids, with bolts and pins, swept every 5° from 0° to 100° with the real 3D kernel — 0 interferences.
* The lock-pin holes line up with the pin at both endpoints (0° and 100°).
* All STL are closed solids. All files re-import cleanly from STEP.
* **Not** checked: the printed fit/tolerance (needs a physical print), strength, or friction at the pivots.

## Notes
* The front-seat "hands-off" motion in the 50° file is the simulated gravity path from the original design.
* A few registration pegs were skipped where the full-size screw position sits too close to an edge or to
  another hole (one in J06, two in J21, one in J22). Those laps are glued only.
* `folding_p1_data.json` is the `FOLDING_P1` object extracted from `app/index.html`, because the original
  `folding-P1/rev2/` folder is not in this repository.
