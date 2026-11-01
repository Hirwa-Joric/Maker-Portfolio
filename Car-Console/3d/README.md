# Parametric console model

![Console assembly](renders/hero.png)

I began designing the console in 3D in November 2025 and started building it in January 2026. The saved model in this folder documents my completed assembly and its dimensions. See the [development sequence](../README.md#from-design-to-build) for the design, construction and documentation stages.

Open [console.blend](blender/console.blend) in Blender to inspect the complete assembly. The six OpenSCAD files define the geometry; 54 STL parts and eight rendered views are included.

## Edit and regenerate

Run these commands from the Car-Console folder. OpenSCAD and Blender must be installed.

```sh
python3 3d/tools/build_parts.py
blender --background --python 3d/blender/assemble.py
```

On macOS, Blender’s executable may be `/Applications/Blender.app/Contents/MacOS/Blender`. The exporter accepts `--openscad /path/to/openscad` and `--out /path/to/parts`. It stages all parts and checks their binary STL structure before replacing the output files.

The workflow is:

```text
scad/params.scad → part generators → stl/ → blender/assemble.py
                                             ├── blender/console.blend
                                             └── renders/*.png
```

Edit [params.scad](scad/params.scad) for dimensions and positions, then regenerate both the STLs and assembly. Material, camera and lighting changes belong in [assemble.py](blender/assemble.py). Regeneration overwrites the generated scene; save manual Blender edits under a separate name if they must be kept.

For a quick preview without replacing the saved scene or renders:

```sh
CONSOLE_ONLY=top CONSOLE_SAMPLES=16 CONSOLE_NOSAVE=1 CONSOLE_OUT=/tmp/console-preview \
  blender --background --python 3d/blender/assemble.py
```

`CONSOLE_ONLY` accepts comma-separated view names or `none` to save only the scene. `CONSOLE_SAMPLES` controls render samples (default 96), `CONSOLE_NOSAVE=1` preserves the scene file, and `CONSOLE_OUT` changes the render directory.

## Parts

| Part file | Parts it makes (STL names) | Written to |
|---|---|---|
| `scad/deck.scad` | `deck` (fibreboard), `deck_vinyl` (leatherette top), `deck_felt` (felt underneath), `notch_lip`, `notch_skirt` (the notch lining as it hangs on the table), `notch_skirt_car` (the same lining as it hangs in the car) | `stl/` |
| `scad/wings.scad` | `wing_left`, `wing_right` (side walls), `band_left`, `band_right` (padded rim on top of each wall, with the fibre groove), `band_roll_left`, `band_roll_right` (smooth black roll on the rim's inner edge) | `stl/` |
| `scad/fittings.scad` | `clock_body`, `clock_bezel`, `clock_face`, `clock_dial_centre`, `clock_marks`, `button`, `button_face`, `cup_ring`, `cup`, `slot`, `pocket`, `bar` | `stl/` |
| `scad/sockets.scad` | `plate`, `plate_screws` (part name `screws`), `usb`, `usb_body`, `usb_ring`, `usb_cap` (closed), `usb_cap_open` (the same cap flipped open on its strap, exported with `-D usb_cap_open=true`), `v12`, `v12_body`, `v12_ring`, `v12_cap` | `stl/` |
| `scad/loose.scad` | `head_l`, `head_r`, `head_loose` (the three LED heads), `head_boots`, `lead_loose`, `fibre_l`, `fibre_r`, the Qi pad (`qi_frame`, `qi_chrome`, `qi_insert`, `qi_icon`, `qi_led`, `qi_screw`, `qi_cable_red`, `qi_cable_black`), `plug`, `plug_lead`, `ctrl` (LED controller), `ctrl_leads` | `stl/` |


All parts are positioned in the model frame before export. `loose.scad` includes an optional bar preview; the assembled metal bar is exported from `fittings.scad`.

## Coordinates

Dimensions are in millimetres. The origin is the centre of the stitched crease at the back of the gear-lever notch, on the deck top. Positive x points towards the passenger, positive y towards the rear, and positive z upwards. This frame is left-handed. The assembly converts millimetres to metres, negates y once and reverses face winding. Raw STLs can therefore appear mirrored in a conventional viewer. The aligned GLB scan files already use the Blender frame and should not be flipped again.

The parameter tags identify the evidence behind dimensions: [S] scan, [T] tape, [P] photograph, [I] inferred. They describe the documentation measurements, not the date of initial design.

## Views

The PNGs are 1600 × 1000 pixels. Photographic comparisons refer to [measurement-photos/](../measurement-photos/).

| Render | What it shows | Compare with | LEDs |
|---|---|---|---|
| `hero.png` | The panel fitted in the car, seen from behind and above on the passenger side, with the low-detail car interior (seats, armrest, gear lever, climate knobs). The third LED head glows in the gear-lever area | No single photo; this is a presentation view. The content matches 3483–3485 | On, blue (the first colour of the cycle) |
| `in_car_3483.png` | The fitted panel through the camera fitted to IMG_3483 (in the car, from above and behind) | IMG_3483. The photo is portrait and the render landscape, so the photo matches the centre strip of the render | Off |
| `top.png` | The fitted panel straight down (no perspective), front to the left, armrest hidden | No single photo. It has the same orientation as IMG_3491, but shows the panel in the car | On, blue |
| `table_top_3491.png` | The panel out of the car on a plain table surface, through the camera fitted to IMG_3491, with the Qi pad, the plug and the third LED head where they lay in that photo | IMG_3491 (and the similar IMG_3488) | Off |
| `table_side_3487.png` | The panel on the table from low on the driver side, through the camera fitted to IMG_3487, with the loose items where they lay in that photo | IMG_3487 | Off |
| `underside.png` | Looking straight up at the underside, front to the left, driver side at the top. It shows the felt, the slot's bar, the socket bodies and their wires, the cup body with the controller on it, the two LED heads feeding the fibres through their clips, and the cables leaving the panel | IMG_3502 (same layout; not a fitted camera), and 3503, 3504 | Off |
| `exploded.png` | The parts pulled apart: walls with their bands and fibres, the leatherette, the fibreboard, the felt, the fittings, the socket plate, the Qi pad, the plug, the controller and the LED heads | No photo. The wiring paths are approximate | On, blue |
| `fibres_green.png` | The hero view at frame 42 of the colour cycle, when the fibres are green | The green phase of the video IMG_3437 (recorded demonstration) | On, green |


## Limits and checks

The [geometry reference](../docs/GEOMETRY.md) defines the current parameters and their uncertainty. The [shape checks](../docs/SHAPE-CORRECTIONS.md) explain the comparisons with the physical panel. Hidden wiring routes, interior cavities and the simplified cabin are approximate. These are presentation meshes, not fabrication-ready engineering drawings.

The six deck exports may contain coincident vertices and zero-area triangles from tessellation. Blender’s importer removes degenerate triangles. The optional [clean_stl.py](tools/clean_stl.py) utility welds vertices and checks closed, outward geometry; it and [stlcheck.py](tools/stlcheck.py) require NumPy.

The light animation switches blue → red → green at approximately 0.55 seconds per colour. The silver button controls the lights; the red-ringed component is a 12 V socket. The controller sits on the outside bottom of the cup body.
