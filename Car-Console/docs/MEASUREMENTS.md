# My measurements: 3 Oct 2026

These are measurements of my finished console, read from the tape photographs IMG_3449–3482. The tables retain measurement ranges and confidence, including uncertainty from the tape position and camera angle. The photographs are in [measurement-photos/](../measurement-photos/).

## Fit and operation — my notes, 29 October 2026

- I measured the existing centre console and sized the panel to sit over it, leaving room for the components underneath.
- The silver button stays depressed when pressed and keeps the lights on after release. The drawing's hidden terminal routing remains separate from this confirmed operation.

## Tape-photo measurements

This is the measurement record for the **Custom Aftermarket Car Center Console Upgrade**. All sizes are in mm. Where a single number is given with a range in brackets, the number is the best value and the range is what the photos allow.

**How positions are given.** x is across the car, measured from the deck's centre line, with + toward the passenger. y is along the car, measured from the notch "stitch line" (the crease where the flat deck top meets the rolled lip at the back of the U-notch), with + toward the rear. z is height, with 0 at the deck's top surface.

**How sure** means: high = the tape reading is clear and the ends are clear; medium = the reading is clear but one end, the tape's position or a correction is uncertain; low = estimated from the photo using the tape as a scale, or the photos disagree.

**Three things changed the readings.**
- In many photos the tape hook was resting near an edge, not hooked over it. In those cases both ends were read off the tape and subtracted, instead of reading from 0.
- In the very close-up shots the tape sat a few mm above the part (on a raised socket, the clock or a bead). Where that matters the raw reading and the corrected value are both given.
- When the tape was laid right across the deck, it rested on the raised side rims, about 20 mm above the deck. Parts lying on the deck then look smaller than they are. In IMG_3457 the socket plate, known to be 102 long, measures only 93 against the tape, so every deck-level reading in that photo is about 9–10 % short. Those readings are shown raw and corrected (× 1.09).

---

The comparison column records initial estimates used while documenting the finished panel. It does not describe the pre-build design. [Geometry reference](GEOMETRY.md) and [params.scad](../3d/scad/params.scad) contain the current model values, including later checks against the scan.

## Table 1: Measured

### Wings (the two side boards)

| Feature | Measured (mm) | Initial documentation estimate | Photo(s) | How sure |
|---|---|---|---|---|
| Wing length along its top edge, rear end to front tip | **577** (573–579) | ~570 (model 565) | 3450 | medium: the hook end is outside the photo; assumed to be on the wing's rear end |
| Wing height, top edge to bottom edge, away from the rear end | **147** (144–148.5) | 150 | 3461 (147, edge to edge); 3460 (147–148 read from the hook, but the hook sat 2–4 mm past the edge, so ~144–145) | medium. Which wing and where along it are not shown (panel lifted out). The object in 3460 is ambiguous in isolation; the surrounding photographs support a wing |
| Wing height about 30 mm from the square (probably rear) end | **131** (128–135) | ~140 (spec: 150 − 10) | 3458 (131, hook not seated), 3459 (134–135 read from the hook) | medium: the hook was held by a finger ~4 mm past the edge; 134–135 if it was really hooked |
| Wing board thickness, bare edge at the rear end | **4.3** (4.2–4.4) | 5 | 3462 | medium. With its leatherette the finished wing is ~5–6: the other wing's covered end reads ~6, and (219 − 208) / 2 = 5.5 |
| Width across both wings at their rear ends, outside face to outside face (panel lifted out) | **219** (216–221) | ~217 (model 216) | 3462 | medium |
| Same place, inside face to inside face | **208** (205–211) | 206 (model) | 3462 | low (read off the same tape, which was not placed for this) |
| Height of the wing's top edge above the deck surface | **26** (25–27.5) at one point; **19.5** (19–20.5) at another, possibly further back | 5–15 (model ~7.5) | 3473, 3474 (both passenger side) | medium. The two spots differ by ~6 mm; where along the car each was taken is not certain |
| Width of the top-edge band, from the band's outer face to where the deck leatherette starts (driver side, at the notch line) | **18.5** | – | 3468 | high. Made up of: outer textured roll ~7.5 (about 5 of it visible from above), clear rod (fibre) ~3, narrow textured strip ~3, smooth black strip ~5 |
| Same top-edge band at the wing's front tip (panel lifted out) | **15** (13–16) | – | 3449 | low. Outer leatherette fold ~5, clear rod ~4, thin strip ~2, black bead ~5 |
| Side-glow fibre, visible width | **3–4** | ~4 | 3468 (2.9), 3465 (3.1–3.6), 3449 (4.0) | medium |
| Smooth black band at the top of the rim's inner face | **5.5** (4.5–6) | – | 3473 | low |
| Fibre centre to fibre centre across the car, fitted (about 45 mm behind the notch) | **233** (229–236) | ~217 | 3465 | medium |
| Width over the top at the same line, driver outer edge to passenger outer edge, fitted | **246–251** | ~217 | 3465 | low: the hook end is out of the photo, and the outermost strips may be the car's own console trim |
| Wing front tips, spread outside to outside, panel lifted out | **320** (310–330; tip to tip ~322) | not modelled | 3449 | medium. This is how far the free tips flare; it is not a fitted size |

### Deck (the flat top)

| Feature | Measured (mm) | Initial documentation estimate | Photo(s) | How sure |
|---|---|---|---|---|
| Deck length on the centre line, rear-arch edge to the notch stitch line | **188** (182–193) | 178 | 3456 | low–medium. 188 is the raw tape reading. The tape-height correction for the tape lifting near the notch gives 191, but three checks inside the same photo (the clock, the plate and the cup ring, placed with 3455's positions) put the stitch line only 182–186 from the arch. See "Limits of the tape-photo record" |
| Same, to the open front edge of the notch lip | **193** (187–199; raw tape 193) | 186 | 3456 | low–medium (same doubt) |
| Rolled lip at the back of the notch, width seen from above | **5** (4–7) | 8 | 3455, 3456 | medium |
| Rolled lip along the arms, width seen from above | **~3** | 8 | 3468 | low |
| Deck width between the side seams (edge of the flat pebble-grain top), about 45 mm behind the notch, fitted | **205** (200–210); raw tape 200 | ~200 | 3465 | medium. The tape lay above the deck (on the clock or the side rims), which makes the raw reading short; how far above is not certain |
| Deck width between the side seams at the cup line (panel lifted out) | **~207** (raw tape 189.5) | ~200 | 3457 | low. Raw value × 1.09 for the tape lying on the rims (see the third point at the top) |
| Deck width at the notch back edge, driver deck edge to the passenger stitch row | **~209** | ~200 | 3468 + 3469 (two halves of one tape pull) | low. This probably runs to a slightly different line on the passenger side (the outer edge of the smooth dark band, which also reads ~208.5 in 3465), so it does not show the deck getting wider |
| Notch width near its back corners, crease to crease | **~155** (150–158) | ~150 | 3468 + 3469 | low–medium. The open edge (where the lip drops into the notch) is ~3 further in on each side, so ~150. The notch gets wider toward the front (see below) |
| Notch inner corner radius | **~12** (10–20) | 8 | 3468, 3469 | low |
| Driver-side arm, outer edge of the side rim to the start of the notch lip | **~38** near the back corner; **~30.5** about 75 mm further forward | ~25 (flat strip only) | 3468 | low (carried across from the tape, not read on it) |

### Fittings on the deck

Positions across the car (x) were read in 3465 and 3457 with the tape lying above the deck, so they are shown corrected for that. The corrected positions and the short gaps between the parts (read in the close-ups) agree to within ~2 mm.

| Feature | Measured (mm) | Initial documentation estimate | Photo(s) | How sure |
|---|---|---|---|---|
| Socket plate length | **102** (100.5–105; raw tape 98.8) | 102 | 3453; 3456 gives 103 | medium (the tape sat on the sockets, above the plate) |
| Socket plate width | **40.5** (40–41.5) | 41 | 3466; 3453 gives 41; 3457 gives 40 after correction (37 raw) | high |
| Socket plate screw spacing | **~86 along × ~23 across** | 86.5 × 23 | 3453, 3455 | low (scaled from the tape) |
| Socket plate centre across the car | **x = −30** (−31 to −28) | −30 | 3465 (−27.5 raw, ~−28.5 corrected), 3457 (−28 raw, ~−31 corrected), gaps | medium |
| Cup chrome ring, outside diameter | **84** (79–85) | 80 | 3451, 3452 (both raw ~8.4 cm); 3457 gives 85 after correction (77.5 raw) | medium. 3465 gives 79, but that ring edge was carried 40 mm across from the tape |
| Cup chrome ring, inside diameter | **~72** (69–74) | 69 | 3451, 3452; 3457 gives 72.5 after correction | low (scaled) |
| Cup body (insert taken out), total height including its top lip | **64** (62.5–65.5) | ~55 deep | 3463 | medium (both readings agree; the top end of the tape is hidden under the thumb) |
| Cup depth, deck surface down to the cup floor | **57** (55–60) | 55 | 3472 | medium (worked out in 3D from a steep close-up; the plain sight-line reading of ~7 cm is wrong) |
| Cup ring centre across the car | **x = +50** (+49 to +51.5) | +48 | 3465 (+50 raw), 3457 (+47 raw, ~+51 corrected), gaps | medium |
| Gap from the cup ring's outer edge to the passenger seam | **~10** (9–11) | 12 | 3457, 3465 | medium |
| Clock centre | **x = 0** (on the centre line); **y = 21.5** behind the notch stitch line | (0, 22) | 3455 for y; 3465 and 3469 for x | high for x and for 3455's y; other photos put y at 25–34 (see "Limits of the tape-photo record") |
| Clock bright chrome ring (bezel) | **34** (32.5–36) | 34 | 3455 (32.6, close-up), 3465 (~33.5 corrected), 3456 (36), 3469 (~36) | low–medium. The dial window inside it is ~30 |
| Clock outer outline (where the leatherette stops) | **36** (35.4–39) | – | 3455 (35.4), 3465 (37), 3469 (37.5), 3456 (38–39) | medium. The dark ring between the chrome and the leatherette is either the clock's black edge or the wall of the hole in the leatherette |
| Silver button, outer metal ring | **16.5** (15–18) | 15 | 3464 (15.7), 3465 (15), 3469 (18) | low–medium |
| Silver button, flat face | **~12.5** (12–13.5) | 11.5 | 3469, 3456, 3457 | low |
| Silver button position | level with the clock along the car; centre ~25 behind the notch fold; ~14–18 in from the passenger seam, so **x ≈ +85** (+83 to +88) | (85, 25) | 3464, 3465, 3469 | low–medium. 3469's +92 was measured from the notch centre in a steep photo and is not used |
| Slot surround, outside width | **23** (22.9–24) | 24 | 3467; 3465 gives 23 | high. (3457 gives 26 after correction; not used) |
| Slot opening width | **15** (14.4–15.2) | 17 | 3467, 3457, 3465 | medium |
| Slot surround rim width (each long side) | **4.2** | ~3.5 | 3467 | medium |
| Slot surround length | **92** (88–94) | 92 | 3453 + 3456 (~93: the slot is 1.085 × the plate's 86 screw spacing), 3457 (~92 after correction), 3456 (~94) | low–medium. 3454's tape-scale figure of 88.5 is short: in that photo the plate's 86 screw spacing also reads only ~81, so the tape sat above the parts; 3467's 85 is scaled from a tilted close-up |
| Slot centre across the car | **x = −69** (−70 to −67) | −71 | 3465 (−67 raw, ~−69 corrected), 3457 (−64 raw, ~−70 corrected), gaps | medium |
| Gap, slot surround to socket plate | **~7.5** (6–9) | 8.5 | 3467, 3457, 3453, 3465 | medium |
| Gap, socket plate to cup ring | **~18.5** (17.5–19.5) | 17.5 | 3451, 3453 (scaled), 3457 and 3465 (corrected) | medium |
| Gap, driver seam to slot surround | **~21** (18–22) | 17 | 3465, 3457 (corrected) | low–medium |

---

## Relation to the current model

The tape observations remain the measurement record. The current model combines them with the finished-build scan and close-ups. Selected values are in [Geometry reference](GEOMETRY.md) and `../3d/scad/params.scad`; raw tape readings are not pending model changes.

## Construction details

I cut the panel from board, covered it in leatherette, fitted the components and wired the assembly. The photographs below show the finished construction. I use these details alongside the tape readings to check the explanatory model.

### Board and covering

The deck has a fibreboard core, a black pebble-grain leatherette top and felt underneath. The cable clips screw through the felt into the board. At the rear arch, the top covering wraps onto the underside and meets the felt (IMG_3477–3482). A separate leatherette strip with a grey knit backing lines the gear-lever notch; it hangs free along the passenger-side arm.

The side boards measure about 4.3 mm at the exposed rear edge. Their outer faces are covered in leatherette. The raised bands carry the side-glow fibres, with a smooth black strip along the inner edge. The tables above record the measured sections; exact material grades and concealed layers are not specified by those measurements.

### Lighting and fittings

Two aluminium LED heads feed the side-glow fibres at the rear corners of the deck. Nylon P-clips hold the fibres just ahead of the heads. A third head lights the gear-lever area. The controller sits on the outside bottom of the cup body; its label specifies a DC 5–12 V input (IMG_3481–3482).

The removable cup insert has a closed floor and a separate chrome ring. A four-screw socket plate carries the USB charger and red-ringed 12 V socket. Beneath the storage slot is a black-painted metal bar with rounded corners and two holes. The clock sits near the notch, with 12 facing the front, and runs on its own battery. These features are visible in IMG_3451–3469 and IMG_3477–3482.

### Wiring and operation

When I press the silver button, it stays down and keeps the lights on after release. The incoming two-core cable reaches the socket terminals; paired red/black leads, heat-shrink joints and in-line plugs connect the other components. A clipped lead runs along the passenger-side arm towards the separate Qi pad. The cigarette-lighter plug is shown unplugged in IMG_3476.

The [circuit guide](../circuit/README.md) separates the installed arrangement from the proposed protection revision. The installed drawing uses dashed lines for concealed routes. Its positive-side switch connection and Qi return are drawing assumptions; terminal continuity, fuse ratings and module ratings are not established by these photographs. Wire ends near the button are recorded by their position only, without labelling them disconnected or bare.

### Fit in the car

I measured the factory centre console and sized the panel to sit over it, leaving clearance underneath. I can lift the panel out as one assembly. The underside screws shown in IMG_3477–3482 hold clips and straps to the panel. The cup body extends about 60 mm below the deck top.

## Limits of the tape-photo record

These limits concern the photographs listed here. Later scan estimates and current model choices are recorded in [Geometry reference](GEOMETRY.md).

**Not measured with the tape in this set**
- How far the wing tip reaches ahead of the notch, and where the wing's rear end is along the car (the current model uses y = 293 from later shape checks).
- How far the flat arms run forward beside the notch (`arm_front_y`).
- Total deck thickness, and the depth of the notch lining skirt. Pixel estimates only: board ~6–10, visible lining ~28–32 below the deck.
- Slot pocket depth, and the depth of the socket bodies below the felt.
- Cup bottom diameter (rough photo estimate only: ~66–69).
- Clock height above the deck. Photos disagree: one suggests nearly flush or ≤4, another 5–8. The current model uses 3 mm, checked against the scan; this remains an approximate glass/chrome height.
- Deck length along the wing joints (`seam_rear_y`), and the arch shape away from its centre.
- Wireless pad size; the later scan estimate is 174 × 121 × 15 mm.
- Metal bar size. Its shape in 3481/3482 is about 4.5 : 1 (length : width), which did not fit the initial documentation estimate of 36 × 114 (3.2 : 1). A width of ~20–25 is more likely, but this was not tape-measured.
- Fuse rating in the plug tip (not visible), and whether the car's outlet is live with the car off (the car was on in every photo).

**Readings where the photos disagree (low confidence)**
- **Deck length on the centre line:** 188 raw in 3456 (191 after the tape-lift correction). But in the same photo the clock centre is 162.7 from the arch, and 3455 puts the clock 21.4 behind the stitch line, which gives ~184. The plate and cup ring rear edges in 3456 (36 and ~50 from the arch), with the plate and ring positions from 3455, give ~182–184. One of these is off by 4–8 mm; 188 is used until it is re-measured.
- **Positions along the car near the notch:** 3455 puts the plate's front edge ~42 behind the stitch line and the cup ring front ~49–50; 3456 puts the plate front ~49–52 and the clock centre ~25–28; 3469 puts the clock centre ~34 (steep photo, least reliable). The close-up 3455 was used for the clock; the plate, slot and cup positions along the car were left unchanged.
- **Deck width:** 200 raw at y ≈ 45 (3465) but the tape lay above the deck; ~207 corrected at the cup line (3457); ~209 at the notch line to a possibly different line (3468 + 3469). 205 is used.
- **Wing position across the car:** rear outer faces are 219 apart with the panel lifted out; near the notch in the car, the fibres are 233 apart and the outer band edges about 250 apart. The different sections and fitted/free poses must be compared separately; see [side walls and bands](GEOMETRY.md#6-side-walls).
- **Cup ring outside diameter:** 84 in the two close-ups and in 3457 after correction; 3465 gives 79, carried 40 mm across from the tape. Mostly settled now; a flat re-measure would close it.
- **Clock bezel:** 32.6 in the close-up (3455), ~36 in 3456 and 3469.
- **Wing height:** 147 edge to edge (3461) against 147–148 from the hook with the hook 2–4 past the edge (3460, so ~144–145).
- **Wing top height above the deck:** 26 at one spot, 19.5 at another. It may change along the wing, or the two readings may be of different features.
- **Wing length (577):** the hook end is outside the photo. The value assumes it was on the wing's rear end.
- **Which wing and where along it:** in the wing-height photos (3458–3461) the panel was lifted out, so which wing and which point along it are not shown.

**Unreadable or missing**
- The printing on the red wire, the markings on the nylon cable clips, the pin count of the small in-line plugs and the labels on the USB socket body are all too small or blurred to read.
- `IMG_3450.jpg`, `IMG_3455.jpg` and `IMG_3463.jpg` are usable photographs in the packaged set.
- IMG_3470, 3471 and 3475 are not in the folder.
