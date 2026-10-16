# Mini folding picnic bench P1 Rev 2 — 1:5 printable test model

A 1:5 version of the folding bench (table ⇄ bench) for printing and checking the mechanism before building
the full-size one. Generated from the same geometry as the full-size design, so every member, pivot, stop and
lock-pin position is the real one divided by 5.

**Three printed parts, one per rigid assembly.** Everything that moves together is a single piece: both side
frames and the planks of each assembly are fused. The full-size laps and glue joints are gone.

| Printed part | Qty | Fuses (full-size parts) | Moves with |
|---|---|---|---|
| `Rear-assembly` | 1 | R1 R2 R3 R4 R5 S1 on both sides + S3 seat planks | fixed (floor) |
| `Front-assembly` | 1 | F1 F2 F3 on both sides + S2 seat planks | swings on pivot A |
| `Table-assembly` | 1 | T1 T2 T4 T5 on both sides + S4 table planks | swings on pivot B |

The planks are not individually connected: each seat / the table is one solid with shallow grooves where the
plank gaps are. Nothing is glued; the only assembly is the four pivots and the lock pins.

![isometric, one colour per printed part](preview-iso-parts.png)
*Table pose, one colour per printed part. Bench pose: `preview-iso-parts-bench.png` (made by `render_iso.py`).*
![side views: table, 50° and bench](preview-side-views.png)

## Files
| | |
|---|---|
| `step/mini-bench-P1-table.step` | Full assembly, table pose (fold 0°), lock pins in |
| `step/mini-bench-P1-mid-fold-50deg.step` | Same, 50° folded, front seat in its hands-off position, pins pulled |
| `step/mini-bench-P1-bench.step` | Same, bench pose (100°), pins in |
| `stl/parts/*.stl` | The 3 printed parts, **already oriented for printing** |
| `parts.csv` | Printed size, volume and support estimate per part |
| `build_mini.py` + `folding_p1_data.json` | Generator and its source geometry |
| `render_iso.py` | The isometric picture |

## Load into Fusion
1. *File → Open → Open from my computer* (or *Insert → Insert into Current Design*) and pick a `.step` file. Units are mm.
2. It arrives as four sub-components: **Rear frame (fixed)**, **Front frame (swings on A)**,
   **Table-back frame (swings on B)**, **Hardware**. Each printed part is one body; the rear and front frames each arrive as one fused body. Floor is Z = 0.
3. If it lands on its side, rotate it (Fusion is Y-up by default; the model is Z-up).
4. To play the mechanism, ground the rear frame and add two **revolute joints** (axis = X):
   * **Pivot B**: Table-back frame ↔ Rear frame, origin at Y = 0, Z = 73.5 (table pose)
   * **Pivot A**: Front frame ↔ Table-back frame, origin at Y = −71.5, Z = 133.5 (table pose)

   Joint limit on B: 0–100° (the table lowers its far edge and becomes the backrest). The front frame is only
   attached at A, so it swings freely like the real one; the app's hands-off path keeps it roughly level (0° at
   both ends, about 44° tilt at 50° fold). Fusion does not simulate contact by default, so use the three STEP
   poses to check the end positions.

## What is, and isn't, 1:5
* **Depth, height, member sections (7.6 × 17.8 mm), pivot positions and stops: exactly 1:5.** The fold geometry is
  planar, so this is what decides whether the mechanism works.
* **Width is not scaled.** True 1:5 would give 304 mm panels. The default is 190 mm overall (table panel) so
  everything fits a 220 × 220 mm bed. For true width: `python3 build_mini.py --width 304` (needs a ~310 mm bed).
* Layer gaps in X are the full-size 3 mm gaps / 5 = **0.6 mm**. The fused frames keep the stepped layers,
  because the layers are what let the three frames pass each other.
* The plank gaps on the panels are cosmetic grooves 0.8 mm deep (not through). The old 6 mm gaps are filled in.
* R3's front-top corner has the 1.2 mm radius (full-size "R6") that the front seat slides over.
* R3's bottom edge is 0.2 mm lower than the original so it overlaps S1 instead of touching it edge to edge (that
  line contact would be a non-manifold edge in the fused print). S1's top, which carries the table, is unchanged.

## Printing
* Sizes: Table assembly 190 × 101 mm (86 mm tall); Front assembly 170 × 168 mm (61 mm tall, lying down); Rear
  assembly 137 × 119 mm (90 mm tall). All fit a 220 mm bed. The STL files are already in the recommended orientation
  (`parts.csv` has the numbers).
* **All three need supports:**
  * `Table-assembly`: panel face down on the plate (about 170 cm² of flat contact), frames pointing up. Only about
    11 cm² of overhang (the stops and the pivot extension). The easiest of the three.
  * `Rear-assembly`: seat panel face down on the plate (about 43 cm² of flat contact), legs pointing up. About
    32 cm² of overhang (the low tie, foot and bearers). Supports on the build plate only.
  * `Front-assembly`: lies low on its inclined legs, 61 mm tall. It has **no flat face on the plate**
    (about 20 mm² of line contact), so it floats on supports. Use a wide brim and supports down to the plate;
    about 24 cm² of overhang. This is the hardest part to print. If it gives trouble, an earlier commit has the front
    frame sides and seat panel as separate parts.
* PLA/PETG, 0.4 mm nozzle, 0.16–0.2 mm layers, ≥ 3 walls, 25 %+ infill. The table assembly is the biggest
  (190 cm³ solid); use low infill.
* Holes are drawn at nominal size (pivot Ø3.4, lock pin Ø2.2). Printed holes come out small; run a 3.5 mm
  drill through the pivot holes and check one pivot before assembling everything.
* Solid volume of all three ≈ 450 cm³. Expect roughly 200–300 g of filament at normal infill, plus supports.

## Hardware (starting spec, check what you have)
| Qty | Item | Where |
|---|---|---|
| 4 | M3 × 14 socket-head screw | Pivots A and B, one per side each; head sits in a Ø6.6 × 3.4 counterbore, flush |
| 4 | M3 nyloc nut | in the Ø6.8 × 4.4 nut counterbore on the inner face |
| 4 | M3 washer, 0.5 mm thin type | between the two moving faces at each pivot (sets the 0.6 mm gap) |
| 2 | Ø2 mm rod, ~25 mm (or 1.75 mm filament with a bent end) | lock pins: through the front assembly into the table assembly (table hole or bench hole) |

Pivot tightening: snug the nyloc until the play just goes, then back off until the joint swings freely. It clamps
the faces, because there is no sleeve at this scale. A drop of thread-lock helps.

## Assembly
Three parts, no glue.
1. Fit pivot **B**: table assembly ↔ rear assembly. Fit pivot **A**: front assembly ↔ table assembly. Use the thin
   washer between the faces. The head sides are the outer faces of the table assembly at B and the front assembly at A.
2. Fold with the lock pins out; fit them at 0° (table) and at 100° (bench).

## What was checked
* Source mechanism: swept 0–100° in 0.25° steps, held-level and hands-off, over every timber pair: 0 clashes
  (reproduces the full-size validation).
* The finished mini solids (the three fused assemblies, bolts and pins) swept every 5° from 0° to 100° with the real 3D
  kernel: 0 interferences.
* The lock-pin holes line up with the pin at both endpoints (0° and 100°).
* Each fused part is a single connected solid; all 3 STL are closed, manifold solids.
* **Not** checked: the printed fit and tolerance (needs a physical print), strength, friction at the pivots, how
  well your slicer supports the front assembly.

## Notes
* The front-seat "hands-off" motion in the 50° file is the simulated gravity path from the original design.
* `folding_p1_data.json` is the `FOLDING_P1` object extracted from `app/index.html`, because the original
  `folding-P1/rev2/` folder is not in this repository.

## Other designs
`build_mini.py --data <json> --out <dir>` builds the same kind of mini model from any design file in this schema. `folding-P2/p2_data.json` (the plywood-plate option, see `folding-P2/README.md`) is built this way.
