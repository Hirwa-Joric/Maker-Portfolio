# Geometry reference

Current model dimensions are defined in [params.scad](../3d/scad/params.scad). This reference records the model frame, major assemblies and measurement limits for my completed console. Photographs and the finished-build scan check the dimensions; the saved geometry can be compared with the physical panel.

## 1. Panel and scale

The removable deck surrounds the gear-lever opening and carries the clock, button, cup holder, storage slot and socket plate. Two covered side walls support wide top bands containing the light fibres. Values below are model dimensions in millimetres, not manufacturing tolerances.

## 2. Frame and measurements

The origin is the centre of the notch’s stitched back crease at deck-top height. Positive x points to the passenger, positive y to the rear and positive z upwards. Blender negates y once and converts millimetres to metres. Aligned GLB scans already use the Blender frame.

[S], [T], [P] and [I] in the source mean scan, tape, photograph and inferred. The [tape readings](MEASUREMENTS.md), [measurement data](../measurements.json) and [scan notes](../Finished-Build-Scan/SCAN-NOTES.md) retain the observations and uncertainty. The clock centre is y = 25.5; tape/photo estimates span approximately 21.5–28.

## 3. Deck

The outline tapers: the notch crease spans 221 mm, while the width around the cup is approximately 205 mm. The rear arch apex is at y = 191. The model stack is 8 mm fibreboard, 1 mm covering and 3 mm felt: 12 mm total, with thickness inferred from photographs. Source tables define the complete curved outline.

## 4. Notch and arms

The opening widens towards the front. Rounded deck-arm noses reach y = −218. Separate skirt meshes represent the flexible notch lining in fitted and table poses; their depth and folds are approximate.

## 5. Rims and top bands

Each band is 18.5 mm wide. The fibre lies on its top face, approximately 9.3 mm from the inner edge. The model uses a 3.5 mm fibre core, a 4 × 0.8 mm fin and a 2 mm drop into the groove.

### 5.1 Band table

Longitudinal position, lateral offset and top height are sampled in `params.scad`; `wings.scad` interpolates the cross-sections. The band is not a uniform round bead.

### 5.2 Fibre endpoints

The passenger fibre ends at y = −247 and the driver fibre at y = −256.5. At the rear, the fibres curve from the LED heads onto the band near y = 242. Local roll/padding thickness is inferred.

## 6. Side walls

Bare board thickness is 4.3 mm; covered thickness is 5.5 mm. The front tip is on the top edge at approximately (y, z) = (−275, 56), and the rear end is at y = 293. The wall is about 147.5 mm tall at y = 0. The source defines the changing profile and rear cap. The model is mostly symmetric; the physical panel varies by several millimetres.

## 7. Fittings

| Component | Centre (x, y) | Main dimensions |
|---|---|---|
| Clock | (0, 25.5) | Body Ø38.5; bezel Ø32.5; window Ø30.5; height 3 |
| Silver button | (91.5, 33) | Bezel Ø16; face Ø12; height 2.5; inferred hole Ø12 |
| Cup | (51, 100) | Ring Ø84 outside / Ø72 inside; ring height 4.5; body depth 60 |
| Socket plate | (−30.5, 101.5) | 40.5 × 102; rotation 1.2° |
| USB socket | (−30.5, 79) before plate rotation | Detailed in sockets.scad |
| 12 V socket | (−30.5, 124) before plate rotation | Detailed in sockets.scad |
| Storage slot | (−71, 96) | Surround 23 × 92; opening 15 × 84; inferred depth 36 |

The cup opening is approximately Ø75 in the model. The clock body, chrome bezel and glass are separate parts. The red-ringed fitting is a socket; the silver button latches down to keep the lights on after release.

## 8. Lights

### 8.1 LED heads

Passenger and driver heads are centred near (98, 149, −18.5) and (−76, 161, −18.5). The third is a loose light in the gear-lever area. These placements are approximate: the scan does not cover the underside.

### 8.2 Fibres and animation

Clear fibres carry light along the tops of the bands; supporting fins enter the grooves. They are not electrical wires. Animation cycles blue → red → green, approximately 0.55 seconds per colour, with abrupt changes.

## 9. Underside

The controller is 46 × 36 × 20, on the outside bottom of the cup body, centred near (61, 100, −70). The metal bar under the slot, felt, clips, plugs and cables appear in the underside view. Hidden routes remain inferred; the installed-wiring schematic uses dashed lines for them. The small black cylinder near the bar is unidentified.

## 10. Loose items

The Qi pad is 174 × 121 × 15 with rounded corners. Its frame, surround, insert, icon, indicator, fastener and leads are separate meshes. The 12 V plug and third LED head have distinct fitted and table placements.

## 11. Cabin context

The panel was sized to sit over the measured centre console, with clearance underneath for its components. The gear lever, well, climate panel, seats, armrest and mats are simplified presentation geometry based on photographs, not dimensioned vehicle CAD. `loose.scad` and `assemble.py` define the fitted Qi-pad and plug poses.

## 12. Cameras and poses

Three views use cameras fitted to IMG_3483, IMG_3491 and IMG_3487. Hero, top, underside and exploded views explain the construction. Table views apply the `free_on_table` shape key to the flexible front bands; the fitted scene uses the unbowed pose. Raw STL geometry is shared.

## 13. Editing

Change the tables in `params.scad`, export all parts with `python3 3d/tools/build_parts.py` from the project root, then run `blender --background --python 3d/blender/assemble.py`. [The model guide](../3d/README.md) describes selective rendering. Recheck the corresponding photographic view after geometry edits.

## 14. Geometry checks

The [comparison images](../3d/renders/compare/) place photographs beside model renders from fitted cameras. They support visible shape and layout, not hidden cavities or electrical continuity.

## 15. Remaining uncertainty

- Scan and tape agree to roughly 1.5%; texture-derived positions are approximate at the millimetre scale.
- Deck-layer thickness, storage depth and notch-lining depth are inferred.
- Band cross-section and wall lean are not established by a cut section.
- Underside placement and wiring rely on photographs, with larger uncertainty than the top surface.
- Cabin geometry is simplified. Measurements, material grades, fit tolerances and electrical ratings need verification before physical reproduction.
