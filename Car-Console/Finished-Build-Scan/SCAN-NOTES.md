# Scan notes: the panel's 3D scan, aligned to the model frame

This record describes the completed panel scanned with Scaniverse in mesh mode on 3 October 2026 at 12:45. Dimensions derived from the scan are approximate. See the [project timeline](../README.md#from-design-to-build) for design and fabrication dates.

- **Source:** `scan_01_12-45.glb`. This file was not changed.
- **Numbers:** all values below are also in `scan-measurements.json`, which has point lists every 10 mm.
- **Units and frame:** everything is in mm in the shared model frame:
  - origin = the middle of the notch's back edge (the stitch line where the flat deck meets the rolled lip), at deck-top level;
  - +x = toward the passenger;
  - +y = toward the rear / armrest;
  - z = up, with the deck top at 0.
- **How each claim is marked:**
  - **SEEN** = read directly from the aligned scan.
  - **INFERRED** = a conclusion drawn from the scan, sometimes together with a photo.
  - Tape values come from [MEASUREMENTS.md](../docs/MEASUREMENTS.md).

## 1. Files

| File | What it is |
|---|---|
| `panel_scan_modelframe.stl` | The panel only, in mm, using the model-frame numbers as they are (the same convention as the OpenSCAD STLs). |
| `panel_scan_modelframe.glb` | The panel only, with texture, in **Blender metres** using assemble.py's convention: Blender (X, Y, Z) = (x/1000, −y/1000, z/1000). It sits exactly on top of the assembled parts and is not mirrored. The clock texture is simplified; the photographed dial carries the Toyota emblem documented in the measurements. |
| `qi_pad_scan.stl`, `plug_scan.stl` | The Qi pad and the cigarette plug, in mm, model frame, left where they lay on the table. |
| `qi_pad_and_plug_scan_modelframe.glb` | The same two objects with texture, in Blender metres. |
| `views/scan_top.png`, `scan_driver_side.png`, `scan_passenger_side.png`, `scan_front.png`, `scan_rear.png` | Orthographic views at 0.25 mm per pixel, with a 10 mm / 50 mm grid labelled in model-frame mm. |
| `views/scan_top_measured_features.png` | Top view with the fitted fittings, edges and seams drawn on. |
| `views/scan_plan_slices.png`, `views/scan_wall_outlines.png` | Horizontal slices, and the side outline of each wall. |
| `views/scan_top_with_qi_pad_and_plug.png` | Top view that includes the pad and the plug. |

**Handedness.** The shared frame (x passenger, y rear, z up) is left-handed.

- **STL files:** the triangles are re-wound so that their normals point outward in the model-frame numbers. A right-handed viewer therefore shows them mirrored, exactly like the SCAD STLs. assemble.py's `M_FIX` (y-flip plus `flip_normals`) corrects them in the same way.
- **GLB files:** these are already in Blender metres, so do **not** flip them again.
- **Raw transforms:** the 4×4 matrices from the raw import to either frame are in the JSON, under `transforms`.

The scan, aligned meshes, measurement JSON and exported views are included here. The exploratory alignment scripts are not included, so the raw-to-aligned transformation is documented rather than packaged as an executable pipeline. The saved matrices are under `transforms` in `scan-measurements.json`; the editable console model has its own [rebuild instructions](../3d/README.md#edit-and-regenerate).

## 2. Alignment and how good it is

1. **Table plane** (SEEN)
   - Method: RANSAC over the whole scene, then a robust least-squares refit on the table within 30–200 mm of the panel. This used 14,517 points, with an RMS residual of **2.15 mm**.
   - The wooden table is not flat everywhere: some areas are 8–16 mm off.
   - In the model frame, the table is z = −120.0 + 0.0046 x − 0.0073 y. Relative to the deck, that is a 0.26° roll and a 0.42° pitch.
2. **Splitting the scan into objects** (SEEN)
   - The scan's vertices were first merged where they shared a position. They had been split at the texture seams, which broke the mesh into 225 pieces.
   - Connected components were then found above the table, extended down to 1 mm above it within each object's footprint.
   - This gave three objects: the panel (8,533 vertices), the Qi pad (1,309) and the plug (309). Everything else was dropped, including the table, warped table patches and a chair at the edge of the scan.
3. **Deck plane** (SEEN)
   - Method: RANSAC plus least squares on upward-facing panel points 105–135 mm above the table. The fit used 1,376 inliers, with an RMS of **0.74 mm**.
   - Over the deck area, away from the fittings, z has a median of −0.4 and an RMS of 0.67; 90 % of points lie between −1.2 and +0.8.
   - The deck is 0.5° off parallel to the table and stands **120 mm above it**.
4. **Centre line** (SEEN)
   - Method: a mirror-symmetry search on the top-view outline, refined by fitting the midline of the two deck seams over y = 0–230. The seam midline is straight to **0.58 mm** (standard deviation). The final correction was −0.17°.
   - The free arms are not symmetric: the passenger arm splays 5–10 mm further out on the table. They were therefore not used to set the centre line.
5. **Orientation** (SEEN)
   - The free arm tips are at the front and the arch is at the rear.
   - The texture shows the chrome cup ring, the clock, the button, the plate with the red 12 V ring, and the slot.
   - The cup ends up at +x and the slot at −x (`scan_top.png`), which matches the photos.
   - The clock's 12 points forward (−y).
6. **Origin y** (SEEN)
   - y = 0 is placed on a dark crease in the texture across the back of the notch. At the crease the surface is about 1.5 mm below the deck. The flat deck (z > −2) starts at y = 0 ± 1.
   - The open edge of the lip is at **y = −6.3**, so the lip seen from above is 6.3 wide (tape: 5, range 4–7).
   - Uncertainty in the origin along y: about ±1.5 mm.

## 3. Scale check against the tape

There is **no consistent scale error.** The scan agrees with the tape to within −1.3 % to +1.7 % (mean about −0.3 %), so no correction was applied.

| Item | Tape | Scan | Difference |
|---|---|---|---|
| Wall length along the top edge | 577 (573–579) | driver 573, passenger 569 (plan length 567.5 / 562.5) | −0.6 % / −1.3 %. The thin tips may be slightly cut off |
| Width over the walls at the rear ends | 219 (216–221) | 219.5 at y = 280 (band level); 220.5 at z = 0 | +0.2 % |
| Wall height away from the rear end | 147 (144–148.5) | 147.9 on average for y = −125 to 150 (range 145–150) | +0.6 % |
| Wall height about 30 mm from the rear end | 131 (128–135) | 133 | +1.7 % |
| Cup chrome ring, outside / inside diameter | 84 / ~72 | 83 / 74 (the bright chrome band) | −1 % / +3 % |
| Socket plate | 102 × 40.5 | 100.8 × 41.1 (42.4 in the middle rows), read at half the plate's height | −1 % / +1.5 % |
| Deck length on the centre line | 188 (183–193) | 191.2 to the rolled arch edge; 186.3 to where the flat ends | in range |
| Band top above the deck | 26 and 19.5 | 27–29.5 for y = −100 to 130; 19.5 at y ≈ 195 | fits both readings |
| Band, outer face to deck seam, at the notch line | 18.5 | 19.6 (driver), 21.4 (passenger) | about +1–3 |
| Arm tips spread, outside to outside | 320 (310–330) | 321 | about 0 |
| Clock bezel | 34 (32.5–36) | 32–35 bright; dark outer ring 38–40 | fits |
| Cup depth | 57 (55–60) | floor at z = −54.5 | −2.5 (least reliable) |

## 4. Key shapes and dimensions (SEEN unless marked)

### Walls (side outline in `views/scan_wall_outlines.png`; full lists in `walls`)

The two walls match each other within about 2–4 mm in side view.

- **Front tips**
  - Driver: (x −149, y −273.8, z +55.8).
  - Passenger: (x +164, y −271.2, z +54.8).
- **Rear ends:** the rear end is a straight, nearly vertical edge.
  - Driver: y = 292–294, running from z ≈ +10 down to the table.
  - Passenger: y = 286–291; its lower part has holes.
  - The rear top corner is at z +10 (driver) and +12 (passenger). At the rear ends the walls' outer faces are at x −109 / +107.
- **Top edge**, as band-top height above the deck:

  | y | −270 | −230 | −190 | −150 | −110 | −50 | 0 | 50 | 90 | 130 | 170 | 210 | 250 | 270 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | driver z | 55.8 | 46.8 | 36.8 | 31.2 | 28.2 | 27.2 | 27.3 | 28.2 | 28.8 | 27.8 | 23.2 | 16.8 | 10.2 | 10.2 |
  | passenger z | 53.2 | 41.8 | 33.8 | 29.8 | 27.8 | 26.2 | 27.4 | 28.2 | 29.8 | 27.8 | 24.2 | 18.2 | 11.2 | 12.2 |

  So the top edge rises steeply over the front 100 mm to the tip. It is nearly level (27–30) from y −110 to 140. It then drops in an S-curve to a flat rear section at about +10–12, running from y ≈ 240 to the rear end. This matches the S-curve seen in the 3489 photo.
- **Front edge**, as y at each height (driver; the passenger side is within 3 mm):

  | z | +50 | +30 | +10 | −10 | −30 | −50 | −70 | −90 | −110 |
  |---|---|---|---|---|---|---|---|---|---|
  | y | −273 | −270 | −264 | −257 | −249 | −234 | −216 | −194 | −168 |

  The edge drops almost straight down from the tip, then curves back. It meets the table at **y ≈ −168** on both sides.
- **Bottom edge** (INFERRED, from the continuous contact strip in the scan plus the straight bottom edge seen in 3489): straight, and resting on the table from y −168 to the rear end. Wall height = band top minus the table plane.
- **Wall height every 25 mm** (driver / passenger):

  | y | −250 | −225 | −200 | −175 | −150 | −100 | −50 | 0 | 50 | 100 | 150 | 175 | 200 | 225 | 250 | 275 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | driver | 80 | 106 | 124 | 137 | 151 | 148 | 148 | 148 | 149 | 150 | 147 | 145 | 141 | 136 | 133 | 133 |
  | passenger | 76 | 103 | 121 | 136 | 148 | 146 | 145 | 147 | 148 | 149 | 147 | 144 | 141 | 135 | 133 | 134 |

  At y ≤ −175 the height is measured to the curved front edge.
- **Wall lean** (SEEN only where the lower wall was captured): the outer faces are near vertical, within about ±5 mm between z +20 and the bottom.

### Widths across the car (`widths_every_10mm`)

| y | −270 | −200 | −150 | −100 | −50 | 0 | 50 | 100 | 150 | 180 | 230 | 280 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Over the walls (band level, outside to outside) | 321 | 311 | 309 | 293 | 276.5 | 263 | 254.5 | 249 | 244.5 | 237.5 | 228.5 | 219.5 |
| Band top to band top | 312 | 286 | 263 | 258 | 252 | 234.5 | 221.5 | 214.5 | 206 | 200 | 199 | 206 |
| Deck, seam to seam | – | – | – | – | – | 222 | 213 | 206 | 197.5 | 192 | – | – |

- **The panel narrows toward the rear.** Every measure shows it.
  - The seam-to-seam deck width goes from 222 at the notch line to 192 at y = 180.
  - The tape notes said "probably no taper", based on ~205–209. The scan disagrees.
  - The seam here is defined as the point where the surface first rises above z = +2 toward the band. That may sit 1–3 mm outside the leatherette seam line.
- **Fitted versus free on the table** (INFERRED):
  - At y ≈ 45 the scan gives about 255 over the top, against the tape's 246–251 measured with the panel fitted.
  - The scan shows the panel standing free on the table. In the car, the side arms may be pressed in by a few mm.

### Notch and arms

- **Back edge:** a straight line across the notch, with the stitch line at y = 0 and the open edge at y = −6.3 (within ±0.5 from x −70 to +70).
- **Corners:** the corner radius is about 12–18.
- **Notch width** between the open edges:

  | y | −15 | −35 | −55 | −75 | −95 | −115 | −135 | −155 | −175 | −195 | −215 |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | width | 158 | 164 | 167.5 | 173 | 181 | 189 | 198 | 208.5 | 219 | 233 | 245.5 |

  - Taper: about 8.5° per side from y −25 to −105, then about 14° per side further forward.
  - The tape gave ~150 open edge to open edge (155 crease to crease) near the back corners. The scan is about 6–10 wider there.
- **Arm strips:** the flat strips on the arms beside the notch end at y ≈ −205 to −225. In front of that, the notch is bounded by the walls themselves: 276 wide at −235 and 300 at −265.
- **Arm strip height:** the strips sink below the deck plane going forward: about −2 at y −100 and −6 at y −150. INFERRED: this is either a real slope or the free arms sagging on the table.

### Rear arch (`arch.edge_by_x`)

The rear edge of the deck, as y at each x:

| x | 0 | ±20 | ±40 | ±50 | ±60 | ±70 | ±80 | ±90 | ±95 |
|---|---|---|---|---|---|---|---|---|---|
| y (driver / passenger) | 191.2 | 193.8 / 191.8 | 195.8 / 191.3 | 197.3 / 194.8 | 199.3 / 200.3 | 204.3 / 207.3 | 212.8 / 218.3 | 229.3 / 229.8 | 244.8 / 240.3 |

- The arch is flat between about x −10 and +40 and steepens beyond |x| = 60. It meets the walls at |x| ≈ 95–100, y ≈ 240–245.
- The flat deck ends about 5 mm before this edge: 186.3 at the apex. The rest is the rolled edge.
- The rear tips are listed in the "Walls" section above.

### Fittings, from texture and height (`fittings`)

The comparison column retains the initial documentation model used in this scan comparison. The saved model has since incorporated these measurements; see the [current fitting dimensions](../docs/GEOMETRY.md#7-fittings).

| Fitting | Scan (x, y) | Size / height | Initial documentation model |
|---|---|---|---|
| Clock | (1.5, 25.6) | bright Ø 32–35, dark ring Ø 38–40; top about **+1** (0 to +3) | (0, 21.5), 8 high |
| Button | (92.7, 34.0) | metal Ø 14–16; top +2.1 | (85, 25) |
| Cup ring | (51.2, 100.4) | chrome Ø 83 outside / 74 inside; ring top +5.1; floor −54.5 | (50, 90) |
| Socket plate | x −51.0 to −9.9, y 51.0 to 151.8; centre (−30.5, 101.4) | 41–42.4 × 101; top +3.8 to +4.9 | (−30, 96) |
| USB socket | (−29.7, 79.1) | top +11 (cap) | (−30, 73.5) |
| 12 V socket | red ring centre (−32.3, 121.7) | red ring Ø ≈ 38; top +10 | (−30, 118.5) |
| Slot surround | centre (−74.5, 96) | 19.5–26 × 86–95; raised +2.2 | (−69, 94) |

What these numbers mean:
- **Gaps:**
  - Plate to cup ring: 19.6 (tape 18.5).
  - Cup ring to the passenger seam: about 9 (tape ~10).
  - Button to the passenger seam: about 16 (tape 14–18).
  - Slot to plate: 11–13 (tape 7.5).
- **The scan shifted the documented fitting positions.** Compared with the initial documentation model, the scan puts the fittings **4–10 mm further back from the stitch line**. It agrees with 3456 (plate front edge 49–52; clock 25–28 behind the stitch; arch 188) rather than with 3455 (clock 21.5).
- **Button versus clock:** the button sits about 8 mm further back than the clock centre, so the two are not level. Its x of +92.7 matches 3469's "+92", which the tape notes had not used.
- **Clock height:** the clock is nearly flush in the scan. Treat this with care: glass and chrome can come out too low in LiDAR. Still, a clock 5–8 mm proud would normally show up, because the 2 mm button and the 4–5 mm plate both show clearly.

### Horizontal slices (`slices`; figure `views/scan_plan_slices.png`)

The JSON has point lists resampled every 10 mm.

| Slice | What it shows |
|---|---|
| z = +20 | Two clean closed loops around the two bands. |
| z = −3 (used instead of 0) | The deck edge outline: notch lip, arch roll and the walls. z = 0 itself lies on the deck surface and gives noise. |
| z = −40, −80, −115 | Fragments only, because the lower walls have holes and the area under the deck is filled with "web" surfaces. |
| z = −120 | At the table plane, so nothing usable. |

### Qi pad and plug (where they lay on the table, not fitted positions)

- **Qi pad:** a rounded rectangle about **174 × 121** (171–177 × 119–123), with its top about **15 mm** above the table. Centre at (x −16.7, y −424); long axis about 120° from +y. Its near edge lay about 60 mm, and its centre about 150 mm, in front of the arm tips. The wireless symbol is printed on its top.
- **Cigarette plug:** about 64–73 long × 38–42 wide (this includes the right-angle exit), up to 31 high. Centre at (162, −393). Most of its cable was not captured.

## 5. What the scan does not show (unreliable or missing)

- **The whole underside:** felt, metal bar, LED heads, controller, wiring, the cup body's outside and the socket bodies.
  - The panel stood on its walls, so the space under the deck was a dark cavity.
  - The scanner closed it with smooth "web" surfaces carrying smeared textures, visible in the front and rear views. **These are not real geometry.**
- **The lower walls:**
  - Large holes below about z −50: on the driver side at y −210 to −100 and 60 to 100, and in several places on the passenger side.
  - The bottom edge appears only as a thin strip where it meets the table.
  - The inner faces of the walls are mostly missing.
- **Deep or narrow openings:** the slot opening is filled over, the socket holes are filled, and the cup's inner wall comes out cone-shaped. The cup floor height is only approximate.
- **Shiny parts:** the heights of the chrome cup ring, the clock glass and the button may be off by 1–3 mm.
- **Small details:** the side-glow fibre, the LED heads at the arm tips, the stitching and the zigzag fold on the band are not resolved in the geometry. The fibre shows only as a light streak in the texture along the band tops.
- **Cables:** only two short pieces were captured, lying in the notch.
- **Texture bleed:** brown, table-coloured fragments sit along the outer sides of the arms near y −150 to −100. They come from the table texture bleeding onto the scan.
- **Fitted shape:** the scan shows the panel free-standing, so the arms are in their relaxed, asymmetric spread. The fitted widths in the car can differ by a few mm.
- **Accuracy:** texture-to-geometry registration is roughly 1–2 mm. Positions taken from the texture (fittings) carry that uncertainty, plus the ±1.5 mm in the origin's y.
