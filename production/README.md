# Production drawings — folding bench P2

`PDF/bench-P2-part-drawings.pdf` has 16 A3 sheets, one per distinct timber part. Each sheet shows:
- Third-angle top, front and right views, plus an isometric.
- Overall sizes.
- **Every non-square saw-cut angle.** Where an end cut makes two corners that add up to 180°, only the acute one is dimensioned.
- Hole callouts (pivot-bush bores with counterbores, lock-pin holes, M8 holes with counterbores) and hole positions. Crowded parts get a hole table instead.
- Quantity, cut length and notes.

It is made with the `engineering-drawing` skill (`.claude/skills/`, from earthtojake/text-to-cad, MIT), using cadgen 0.7.21.

| File | What |
|---|---|
| `geometry-P2.json` | exported from the app: side profiles, pivots, holes (same data as the 3D view, sweep and cut list) |
| `parts.py` | each part as a build123d solid in its own frame (min-area rectangle → +X), bores cut |
| `drawings.py` | the sheets |

Rebuild after changing the design in the app (re-export `geometry-P2.json` first):

```bash
cd production
MPLCONFIGDIR=/tmp/mpl uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.21 python drawings.py
cp PDF/bench-P2-part-drawings.pdf ../app/
```

Limits:
- **Dimensions are nominal.** No tolerances are stated because none were specified.
- **Rounded corners:** cut angles are measured at the virtual sharp corner, where the two saw cuts meet. Round the corners (R6–R10) after cutting.
- **Screw pilots** are not drawn. Their positions are in the assembly plan and the joint schedule.
