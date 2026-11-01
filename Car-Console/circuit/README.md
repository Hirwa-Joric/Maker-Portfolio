# Console circuit — editable files and diagrams

I planned the circuit before starting construction of the console in January 2026. Start with **console_as_built** to inspect the installed arrangement. The [development sequence](../README.md#from-design-to-build) places the circuit planning and documentation in context. Dashed routes mark connections hidden in the photographs.

The silver button latches down and keeps the lights on after release. The installed drawing marks its hidden wires as dashed: the exact terminal routing and switched conductor still need checking. The proposed drawing specifies its own wiring and component ratings.

## Installed wiring

- [Open the KiCad project](console_as_built.kicad_pro), then its [schematic](console_as_built.kicad_sch).
- [Read the PDF](console_as_built.pdf), [PNG](console_as_built.png) or [SVG](console_as_built.svg).
- [Drawing generator](make_console_as_built.py), [project symbols](console_as_built.kicad_sym) and [symbol-library table](sym-lib-table) support editing and regeneration. Keep the project and library files together.

## Proposed improvement

The **console_improved** files describe a proposed revised circuit, not an installed upgrade. They are included separately by filename so the two versions can be inspected without confusing their status.

- [KiCad project](console_improved.kicad_pro) and [schematic](console_improved.kicad_sch)
- [PDF](console_improved.pdf), [PNG](console_improved.png) and [SVG](console_improved.svg)
- [Generator](gen_console_improved.py) and [custom symbols](console_custom.kicad_sym)

## Supporting files

`erc_*.rpt` are the saved electrical-rule-check reports; they are not certification of the physical wiring. Local KiCad preferences are excluded from version control.

## Regenerate the diagrams

Run from `circuit/`, with Python 3, KiCad 10 and Poppler installed:

```sh
python3 make_console_as_built.py
python3 gen_console_improved.py
kicad-cli sch export pdf --draw-hop-over -o console_as_built.pdf console_as_built.kicad_sch
kicad-cli sch export pdf --draw-hop-over -o console_improved.pdf console_improved.kicad_sch
kicad-cli sch export svg --draw-hop-over -o . console_as_built.kicad_sch
kicad-cli sch export svg --draw-hop-over -o . console_improved.kicad_sch
pdftoppm -png -singlefile -scale-to-x 3600 -scale-to-y -1 console_as_built.pdf console_as_built
pdftoppm -png -singlefile -scale-to-x 3600 -scale-to-y -1 console_improved.pdf console_improved
kicad-cli sch erc --severity-all -o erc_as_built.rpt console_as_built.kicad_sch
kicad-cli sch erc --severity-all -o erc_improved.rpt console_improved.kicad_sch
```

On macOS, `kicad-cli` is inside `/Applications/KiCad/KiCad.app/Contents/MacOS/`. The generators use KiCad’s installed symbol library; set `KICAD10_SYMBOL_DIR` when it is elsewhere. Regeneration replaces the generated schematics, libraries and project configuration. Keep manual schematic edits separately if they must be retained.

## Current checks

Both drawings passed electrical-rule checks in KiCad 10.0.6 on 1 November 2026: zero errors or warnings under the check settings listed in [erc_as_built.rpt](erc_as_built.rpt) and [erc_improved.rpt](erc_improved.rpt). The installed drawing was regenerated and visually checked after its explanatory notes were revised; all 25 electrical networks are unchanged. The proposed revision retains its 12 networks and remains a separate, uninstalled design. These software checks do not establish the safety or continuity of the physical circuit.
