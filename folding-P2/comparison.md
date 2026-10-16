# P1 Rev 2 (laminated members) vs P2 (plywood plates): same checks, side by side

Both use the same fold geometry (pivots A and B, 100° fold, seat 450, table 755, length 1520). Everything below is computed by `p2_validate.py` from `folding_p1_data.json` and `p2_data.json` unless it says "assumption". Full-size mm.

## Does it still work? (same result for both)

| Check | P1 Rev 2 | P2 |
|---|---|---|
| Clash sweep 0–100°, 0.25° steps, front seat held level and hands-off | 0 clashes | 0 clashes |
| Clearance of every pair that is not a deliberate contact | ≥ 5.0 mm | ≥ 5.0 mm |
| Hands-off: front frame hangs at (gravity solver; reproduces P1's stored curve to 0.27°) | 44.1° | 43.6° |
| Hands-off: jams | none | none |
| Hands-off: swing event (front frame leaves the floor, fold ≈ 27°) | 31° → 44° | 31° → 44° |
| Table endpoint: free rotation of the front frame with the pin out | 0.0° (locked by T4 and the floor) | 0.0° (locked) |
| Bench endpoint: free rotation range with the pin out | -10° to 0° (lifting is free, pressing down is blocked) | -10° to 0° (lifting is free, pressing down is blocked) |
| Gap at the stops, table pose (mm) | F1~T4: 0.00 | FP~T4: 0.00 |
| Gap at the stops, bench pose (mm) | F1~T5: 0.00, T2~S1: 0.00, S2-1~R3: 0.02, S2-2~R3: 0.01 | FP~T5: 0.00, TP~S1: 0.00, S2-1~RP: 0.02, S2-2~RP: 0.01 |
| Lock-pin hole misalignment, table / bench | 0.0 / 0.06 mm | 0.0 / 0.06 mm |
| Tip-over, seat-edge margin (table, front / rear seat) | 217 / 294 mm | 220 / 300 mm |
| Tip-over, bench: 90 kg on the edge + 150 N push on the backrest, safety factor | 4.3 | 4.4 |

## What changes

| | P1 Rev 2 | P2 | change |
|---|---|---|---|
| Pieces in the bench (frames + boards) | 35 | 21 | -40 % |
| Frame pieces per side | 13 | 6 | -54 % |
| Member-to-member joints (glued laps, bolted lap) | 24 | 6 | -75 % |
| Screws 5 x 70 | 98 | 60 | -39 % |
| M8 bolts | 6 | 0 | -100 % |
| Layers across the width | 8 | 5 | -38 % |
| Side stack width | 196 mm | 114.0 mm | -42 % |
| Frame mass (softwood 500 kg/m³; plywood 680 kg/m³) | 14.9 kg | 16.4 kg | +10 % |
| Bench mass | 36.3 kg | 37.8 kg | +4 % |
| Sawn 38 x 89 bars (2400) | 10 | 8 | -20 % |
| Plywood 18 mm sheets (2440 x 1220) | 0 | 1 (yield 45 %) | |
| Sawing length (P1: crosscuts; P2: every outline, curves included) | 6.2 m | 18.0 m | +190 % |
| Material cost estimate (project prices; plywood sheet 240) | 243.5 | 434.8 | +79 % |

Cost basis: sawn 38 x 89 at 3.0 per 1000 mm² per metre (the rate in `simple-G1/project.json`), the 18 mm birch sheet at 240 (also from that file). No labour, glue, hardware or VAT. Hardware is the same for both except the 6 M8 bolts and 38 fewer screws in P2.

## Joints and strength (screening only, not a certification)

* **P1's weakest connection is the bolted T1/T2 lap**: two M8 bolts carry the backrest-lean moment (116 kN·mm, 64 mm apart): 1.82 kN per bolt against 3.7 kN timber embedment, utilisation 0.49. Fine for this load, thin margin for a bigger one. P2 has no such joint: T1 and T2 are one plate.
* **The stop lugs are the critical glue lines in both designs.** At the 4 kN stop reaction quoted in P1's design review, T4 sees 0.95 MPa in P1 and 0.95 MPa in P2 against about 1 MPa design shear for PU glue: no margin in either. S1 improves from 0.56 to 0.4 MPa because it lands on a plate instead of one tie. T4 needs more area or a through bolt in either design.
* **P2's plates have to be plywood.** A solid panel has one grain direction; the front plate has a long leg at 60° and a horizontal seat bearer. At 3.03 MPa bending the cross-grain member would be at utilisation 12.4 (tension perpendicular to grain). In 2 x 18 mm cross-ply birch it is 0.22 (P1's timber members: 0.26). Plywood strength is a conservative design value, not tested.

## Printing the 1:5 mini versions (same generator, same method)

| Part | P1: overhang / bed contact / height / volume | P2: overhang / bed contact / height / volume |
|---|---|---|
| Rear-assembly | 3241 mm² / 4343 mm² / 90 mm / 150 cm³ | 1755 mm² / 4315 mm² / 90 mm / 122 cm³ |
| Front-assembly | 2380 mm² / 20 mm² / 61 mm / 110 cm³ | 3965 mm² / 4193 mm² / 152 mm / 99 cm³ |
| Table-assembly | 1113 mm² / 16910 mm² / 86 mm / 190 cm³ | 1107 mm² / 16910 mm² / 86 mm / 182 cm³ |
| **Total volume** | 449 cm³ | 403 cm³ (-10 %) |

P1's front assembly has no flat face to lie on (it prints lying on its legs). P2's front plate has a flat face, so it can stand on its side with a 4200 mm² base, but then it is 152 mm tall and needs supports under the upper plate; its lowest-support orientation (lying, 61 mm tall) needs about the same as P1's.

