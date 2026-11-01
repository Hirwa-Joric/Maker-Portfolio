# Console model and circuit specification

## 1. Assembly

I designed the removable panel to bring a cup holder, storage slot, clock, USB and 12 V sockets and illuminated trim into one console. Its 12 V supply also powers a separate wireless pad on the front tray. I planned its shape and circuit before starting construction in January 2026. The saved model and drawings document the completed assembly.

## 2. Coordinates

See [Geometry reference](GEOMETRY.md). Dimensions use the notch crease as origin, x towards the passenger, y towards the rear and z upwards. Blender applies the documented y-axis conversion.

## 3. Components

| Group | Parts |
|---|---|
| Deck | Fibreboard, leatherette, underside felt, rolled notch lip and flexible lining |
| Side walls | Covered board, padded bands and smooth inner rolls |
| Fittings | Clock, silver button, cup, slot and metal support bar |
| Power | USB socket, 12 V socket, two-hole plate, feed plug and leads |
| Lighting | Controller, three LED heads, two fibres and cable clips |
| Wireless charging | Separate Qi pad with frame, insert, indicator and leads |

The model represents the board, coverings and component shapes. It does not specify material grades or electrical ratings; those are outside the dimensional measurements. [params.scad](../3d/scad/params.scad) defines model dimensions; the other five SCAD files define component geometry.

## 4. Outputs

Six OpenSCAD sources produce 54 STLs. Blender assigns materials, creates cabin context and approximate cables, sets cameras and renders eight views. [The model guide](../3d/README.md) contains the part list and rebuild commands. The meshes are presentation assets, not fabrication-certified parts.

## 5. Electrical documentation

### 5.1 Installed wiring

`console_as_built` documents visible connections and marks hidden routes with dashed lines. The feed supplies the socket and charging branches. The silver button latches down to keep the RGB lights on after release; the red-ringed fitting is a socket. Two LED heads feed the rim fibres and the third lights the gear-lever area. The clock runs on its own battery. The controller sits on the outside bottom of the cup body. The button's latching operation is confirmed; its terminal routing, the Qi return route and fuse/wire ratings require physical inspection.

### 5.2 Proposed protection revision

`console_improved` proposes separate fused branches and clearer returns. It is not installed or validated. Component and wire ratings are proposals requiring verification against loads, connectors, voltage and installation conditions. [The circuit guide](../circuit/README.md) links both editable projects, generators and diagrams.

## 6. Visual states

Powered views show the USB cap open and its blue ring lit. Views matched to unpowered photographs show it closed. Fibres cycle blue → red → green approximately every 0.55 seconds. Table and fitted poses account for flexible bands and loose Qi-pad/plug placement.

## 7. Evidence

The project includes 34 completed-build/detail images, 51 measurement/fit photographs, a finished-build scan and tape readings. Use [measurements](MEASUREMENTS.md) for observations and [shape checks](SHAPE-CORRECTIONS.md) for comparisons. Rendered views are separate from photographs.

## 8. Documentation limits

The model preserves visible geometry and the confirmed latching operation of the button. It does not establish concealed attachments, switch terminal routing, continuity, wire gauges, fuse values, or Qi input limits. Electrical assumptions are marked in the installed drawing; the proposed circuit specifies a separate design. The schematic is not a record of physical continuity or load testing.
