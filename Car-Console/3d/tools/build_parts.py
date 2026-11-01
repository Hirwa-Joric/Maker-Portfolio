#!/usr/bin/env python3
"""Export the 54 console parts from OpenSCAD; run from any working directory."""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

MODEL = Path(__file__).resolve().parents[1]
GROUPS = {
    "deck": {"deck": "deck", "vinyl": "deck_vinyl", "felt": "deck_felt",
             "lip": "notch_lip", "skirt": "notch_skirt", "skirt_car": "notch_skirt_car"},
    "wings": {"right": "wing_right", "left": "wing_left", "band_right": "band_right",
              "band_left": "band_left", "band_roll_right": "band_roll_right",
              "band_roll_left": "band_roll_left"},
    "fittings": {name: name for name in "clock_body clock_bezel clock_face clock_dial_centre clock_marks button button_face cup_ring cup slot pocket bar".split()},
    "sockets": {name: ("plate_screws" if name == "screws" else name)
                for name in "plate screws usb usb_body usb_ring usb_cap v12 v12_body v12_ring v12_cap".split()},
    "loose": {name: name for name in "head_l head_r head_loose head_boots lead_loose fibre_l fibre_r qi_frame qi_chrome qi_insert qi_icon qi_led qi_screw qi_cable_red qi_cable_black plug plug_lead ctrl ctrl_leads".split()},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=MODEL / "stl", help="output directory")
    parser.add_argument("--openscad", default=os.environ.get("OPENSCAD", "openscad"))
    args = parser.parse_args()
    executable = shutil.which(args.openscad)
    if executable is None:
        parser.error("OpenSCAD was not found; install it or pass --openscad /path/to/openscad")
    args.out.mkdir(parents=True, exist_ok=True)
    jobs = [(group, part, name, []) for group, parts in GROUPS.items()
            for part, name in parts.items()]
    jobs.append(("sockets", "usb_cap", "usb_cap_open", ["-D", "usb_cap_open=true"]))
    with tempfile.TemporaryDirectory(prefix=".console-export-", dir=args.out) as staging:
        for index, (group, part, name, extra) in enumerate(jobs, 1):
            target = Path(staging) / (name + ".stl")
            command = [executable, "--backend", "Manifold", "--export-format", "binstl",
                       "-D", f'part="{part}"', *extra, "-o", str(target),
                       str(MODEL / "scad" / (group + ".scad"))]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode or not target.exists():
                raise RuntimeError(f"{name}: OpenSCAD export failed\n{result.stderr}")
            data = target.read_bytes()
            if len(data) < 84:
                raise RuntimeError(f"{name}: truncated STL")
            triangles = struct.unpack_from("<I", data, 80)[0]
            if not triangles or len(data) != 84 + 50 * triangles:
                raise RuntimeError(f"{name}: invalid or empty binary STL")
            print(f"[{index}/{len(jobs)}] {name}: {triangles} triangles", flush=True)
        for _, _, name, _ in jobs:
            os.replace(Path(staging) / (name + ".stl"), args.out / (name + ".stl"))
    print(f"Exported {len(jobs)} parts to {args.out.resolve()}")


if __name__ == "__main__":
    main()
