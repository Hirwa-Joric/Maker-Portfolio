"""
Assemble the console model from the checked-in STL parts, add materials,
lighting, wiring illustrations and cameras, then save the editable Blender scene.

Run from the repository root:
  blender --background --python 3d/blender/assemble.py

The saved model documents the completed physical console. Measurements and
photographs check the explanatory geometry. Hidden wire routes and unmeasured
dimensions remain approximate (see docs/GEOMETRY.md).

Environment options:
  CONSOLE_ONLY=hero,top   select render jobs; "none" saves the scene without rendering
  CONSOLE_SAMPLES=96      EEVEE samples per render
  CONSOLE_NOSAVE=1        leave the saved scene unchanged
  CONSOLE_OUT=<folder>    write render images to another directory
  CONSOLE_STAMP=1         include the descriptive caption strip

Model coordinates are millimetres: x toward the passenger, y toward the rear,
z upward, with the origin at the notch stitch crease on the deck. Blender uses
metres and negates model y once; mesh faces are rewound to preserve normals.
Table views use the measured free-state bow. Car views use the fitted pose.
The rendered car surroundings are simplified context, not a measured full-car model.
"""

import bpy
import bmesh
import math
import os
import struct

import numpy as np
from mathutils import Matrix, Vector

# --------------------------------------------------------------------------------------------
# Paths and global settings
# --------------------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # .../car-console/3d
STL_DIR = os.path.join(ROOT, "stl")                # checked-in part set
RENDER_DIR = os.environ.get("CONSOLE_OUT") or os.path.join(ROOT, "renders")
BLEND_PATH = os.path.join(HERE, "console.blend")

PROJECT = "Custom Aftermarket Car Center Console Upgrade"
CAPTION = "Current model of the completed console; dimensions and hidden routes approximate"
STAMP = os.environ.get("CONSOLE_STAMP") == "1"     # no strip on the renders unless CONSOLE_STAMP=1

RES = (1600, 1000)
SMOOTH_ANGLE = math.radians(35.0)

# Recorded light cycle: blue, red, green, with approximately 0.55 seconds per colour.
FPS = 30
_BLUE, _RED, _GREEN = (0.10, 0.02, 1.00), (1.00, 0.02, 0.05), (0.02, 0.75, 0.08)
CYCLE = [(1, _BLUE), (18, _RED), (34, _GREEN), (51, _BLUE), (67, _RED), (84, _GREEN), (100, _BLUE)]
GREEN_FRAME = 42
# Adjacent equal-colour keys keep each step constant until the next switch.
CYCLE_KEYS = []
for _i, (_f, _c) in enumerate(CYCLE):
    CYCLE_KEYS.append((_f, _c))
    if _i + 1 < len(CYCLE):
        CYCLE_KEYS.append((CYCLE[_i + 1][0] - 1, _c))
FIBRE_GLOW = float(os.environ.get("CONSOLE_GLOW", "0.8"))
HEAD_GLOW = 7.0
LED_VIEW = tuple(os.environ.get("CONSOLE_LEDVIEW", "Standard|Medium High Contrast|-0.3").split("|"))


# The recorded light cycle in IMG_3437 switches blue -> red -> green,
# approximately 0.55 seconds per colour. At 30 fps, hold keys alternate
# 17 and 16 frames per colour; there are no crossfades.

# part set (all in 3d/stl).
DECK_WINGS = ["deck", "deck_vinyl", "deck_felt", "notch_lip", "notch_skirt", "notch_skirt_car",
              "wing_left", "wing_right", "band_left", "band_right", "band_roll_left", "band_roll_right"]
FITTINGS = ["clock_body", "clock_bezel", "clock_face", "clock_dial_centre", "clock_marks",
            "button", "button_face", "cup_ring", "cup", "slot", "pocket", "bar",
            "plate", "plate_screws", "usb", "usb_body", "usb_ring", "usb_cap", "usb_cap_open",
            "v12", "v12_body", "v12_ring", "v12_cap"]
LOOSE_PARTS = ["head_l", "head_r", "head_loose", "head_boots", "lead_loose", "fibre_l", "fibre_r",
               "qi_frame", "qi_chrome", "qi_insert", "qi_icon", "qi_led", "qi_screw",
               "qi_cable_red", "qi_cable_black", "plug", "plug_lead", "ctrl", "ctrl_leads"]


def mm(x, y, z):
    """Shared-frame millimetres -> Blender metres (with the handedness fix)."""
    return Vector((x * 0.001, -y * 0.001, z * 0.001))


# --------------------------------------------------------------------------------------------
# Values from params.scad / the part files that this script needs (model frame, mm)
# --------------------------------------------------------------------------------------------
FELT_Z = -12.0
CUP_C = (51.0, 100.0)
# socket centres after the plate turn (params plate_rot 1.2 deg about plate_c (-30.5, 101.5): plate_xf())
USB_C = (-30.03, 79.0)
V12_C = (-30.97, 124.0)
CTRL_C = (61.0, 100.0, -70.0)                    # ctrl_c = cup_c + (10, 0), z -80..-60
HEADS = {                                        # centre, nose axis (loose.scad head_c / head_ax)
    "head_r": ((98.0, 149.0, -18.5), (0.0, 1.0, 0.0)),
    "head_l": ((-76.0, 161.0, -18.5), (-0.34, 0.94, 0.0)),    # moved 3 Oct (was -78, 157)
    "head_loose": ((-70.8, -75.4, -60.9), (-1.0, 0.0, 0.0)),   # loose.scad head_loose_pos (3483 fit)
}
HEAD_L, HEAD_BOOT, HEAD_STUB = 31.0, 3.0, 4.0
# Qi pad pose in the car (loose.scad, re-fitted on IMG_3483)
QI_TOP_C = (10.6, -224.3, -64.3)
QI_ROT, QI_TILT = -19.6, 20.1                    # deg: yaw (passenger end forward), front edge lower
QI_SIZE = (174.0, 121.0, 15.0)
QI_EXIT_LOCAL = (-87.0 - 5.0, 8.0, 7.0)          # cord leaves the driver end (u, v, w from the bottom)
PLUG_TIP = (44.0, -281.0, -50.0)                 # tip, pointing -x, unplugged in the tray
PLUG_EXIT_END = (101.0, -256.5, -50.0)           # end of the ribbed cable exit (local x 57, +y)
WCLIP = (-96.0, -2.0, -14.0)                     # P-clip at the driver notch corner (W1 + third lead)
QI_LEAD_END = (97.0, -100.0, -20.0)              # params qi_lead end (where qi_cable_* start)


def qi_xform_pt(q):
    """Pad-local (u, v, w from the bottom) -> model mm, as loose.scad qi_xform_pt()."""
    a, t = math.radians(QI_ROT), math.radians(QI_TILT)
    u = q[0] * math.cos(a) - q[1] * math.sin(a)
    v = q[0] * math.sin(a) + q[1] * math.cos(a)
    w = q[2] - QI_SIZE[2]
    return (QI_TOP_C[0] + u, QI_TOP_C[1] + v * math.cos(t) - w * math.sin(t),
            QI_TOP_C[2] + v * math.sin(t) + w * math.cos(t))


def qi_top_z_at(y):
    return QI_TOP_C[2] + math.tan(math.radians(QI_TILT)) * (y - QI_TOP_C[1])


def head_rear(name):
    c, a = HEADS[name]
    a = np.array(a) / np.linalg.norm(a)
    return np.array(c) - a * HEAD_L / 2, a


def head_stub_end(name):
    r, a = head_rear(name)
    if name == "head_l":       # loose.scad: the driver head's cable leaves the boot toward +x (head_stub_end_l)
        return tuple(r - a * HEAD_BOOT + np.array([HEAD_STUB, 0.0, 0.0]))
    return tuple(r - a * (HEAD_BOOT + HEAD_STUB))


# Free-state front bow: +x displacement in millimetres, checked against photos 3491/3488 and the scan.
# Both rims bend together; deck and notch parts use the bow only forward of y = -110.



BOW = [(0, 0.0), (-25, 0.6), (-50, 1.3), (-75, 1.8), (-100, 2.6), (-125, 3.0), (-150, 3.6), (-175, 4.6),
       (-200, 5.6), (-225, 6.5), (-250, 8.0), (-275, 8.5)]
BOW_FULL = ("wing_left", "wing_right", "band_left", "band_right", "band_roll_left", "band_roll_right",
            "fibre_l", "fibre_r")
BOW_RAMPED = ("deck", "deck_vinyl", "deck_felt", "notch_lip", "notch_skirt")
# Car-context translation in model millimetres, registered to camera 3483.

CTX_SHIFT = (0.0, -7.0, 3.0)


# --------------------------------------------------------------------------------------------
# 0. Empty scene
# --------------------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = PROJECT
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'

col_console = bpy.data.collections.new("Console assembly")
col_context = bpy.data.collections.new("Car context (low detail, GEOMETRY section 11)")
col_table = bpy.data.collections.new("Table (table views only)")
col_rig = bpy.data.collections.new("Lights and cameras")
for c in (col_console, col_context, col_table, col_rig):
    scene.collection.children.link(c)


# --------------------------------------------------------------------------------------------
# 1. Materials
# --------------------------------------------------------------------------------------------
def new_mat(name, base=(0.03, 0.03, 0.03), rough=0.5, metal=0.0, spec=0.5, **kw):
    m = bpy.data.materials.new(name)
    if hasattr(m, "use_nodes") and not m.node_tree:
        m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*base, 1.0)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Specular IOR Level"].default_value = spec
    for k, v in kw.items():
        sock = p.inputs[k]
        sock.default_value = (*v, 1.0) if isinstance(v, tuple) and len(v) == 3 else v
    m.diffuse_color = (*base, 1.0)
    return m


def principled(m):
    return m.node_tree.nodes.get("Principled BSDF")


def add_bump(m, kind="pebble", scale=500.0, strength=0.3, distance=0.0004, rough_var=None, colors=None):
    """Procedural bump in object space (metres). 'pebble' = leatherette grain (Voronoi + noise),
    'felt' = fine fuzzy noise, 'brushed' = streaks along x, 'fibre' = MDF speckle,
    'weave' = carbon-weave checker (clock dial centre), 'mottle' = soft colour variation."""
    nt = m.node_tree
    p = principled(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    if kind == "pebble":
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.feature = 'SMOOTH_F1'
        bump.invert = True          # pebble tops raised, grooves between them
        vor.inputs["Scale"].default_value = scale
        noi = nt.nodes.new("ShaderNodeTexNoise")
        noi.inputs["Scale"].default_value = scale * 2.2
        noi.inputs["Detail"].default_value = 4.0
        nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
        nt.links.new(tc.outputs["Object"], noi.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMath")
        mix.operation = 'MULTIPLY_ADD'
        nt.links.new(noi.outputs["Fac"], mix.inputs[0])
        mix.inputs[1].default_value = 0.25
        nt.links.new(vor.outputs["Distance"], mix.inputs[2])
        nt.links.new(mix.outputs[0], bump.inputs["Height"])
        if rough_var:
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = rough_var[0]
            mr.inputs["To Max"].default_value = rough_var[1]
            nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], p.inputs["Roughness"])
    elif kind in ("felt", "fibre", "mottle"):
        noi = nt.nodes.new("ShaderNodeTexNoise")
        noi.inputs["Scale"].default_value = scale
        noi.inputs["Detail"].default_value = 12.0 if kind != "mottle" else 3.0
        noi.inputs["Roughness"].default_value = 0.75 if kind != "mottle" else 0.5
        nt.links.new(tc.outputs["Object"], noi.inputs["Vector"])
        nt.links.new(noi.outputs["Fac"], bump.inputs["Height"])
        if colors:
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = (*colors[0], 1)
            ramp.color_ramp.elements[1].color = (*colors[1], 1)
            nt.links.new(noi.outputs["Fac"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    elif kind == "brushed":
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0, 60.0, 60.0)
        noi = nt.nodes.new("ShaderNodeTexNoise")
        noi.inputs["Scale"].default_value = scale
        noi.inputs["Detail"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], noi.inputs["Vector"])
        nt.links.new(noi.outputs["Fac"], bump.inputs["Height"])
    elif kind == "weave":
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(45))
        chk = nt.nodes.new("ShaderNodeTexChecker")
        chk.inputs["Scale"].default_value = scale
        chk.inputs["Color1"].default_value = (*colors[0], 1)
        chk.inputs["Color2"].default_value = (*colors[1], 1)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], chk.inputs["Vector"])
        nt.links.new(chk.outputs["Color"], p.inputs["Base Color"])
        nt.links.new(chk.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])


def make_emissive(m, color, strength):
    p = principled(m)
    p.inputs["Emission Color"].default_value = (*color, 1.0)
    p.inputs["Emission Strength"].default_value = strength


MAT = {}
# --- leatherette and coverings (IMG_3483/3486/3491: black pebble grain, smooth black roll on the rims)
MAT["leather"] = new_mat("Leatherette black pebble", base=(0.024, 0.024, 0.025), rough=0.55,
                         spec=0.45, **{"Coat Weight": 0.08, "Coat Roughness": 0.35})
add_bump(MAT["leather"], "pebble", scale=560.0, strength=0.28, distance=0.0004, rough_var=(0.46, 0.66))
MAT["smooth_black"] = new_mat("Band roll smooth black (glossy)", base=(0.016, 0.016, 0.017), rough=0.2,
                              spec=0.5, **{"Coat Weight": 0.35, "Coat Roughness": 0.12})
MAT["felt"] = new_mat("Needle felt black", base=(0.016, 0.016, 0.017), rough=1.0, spec=0.1,
                      **{"Sheen Weight": 0.45, "Sheen Roughness": 0.4, "Sheen Tint": (0.5, 0.5, 0.52)})
add_bump(MAT["felt"], "felt", scale=2600.0, strength=0.45, distance=0.0004)
MAT["mdf"] = new_mat("Fibreboard (MDF look)", base=(0.42, 0.29, 0.16), rough=0.85, spec=0.3)
add_bump(MAT["mdf"], "fibre", scale=900.0, strength=0.25, distance=0.0003,
         colors=((0.30, 0.19, 0.10), (0.52, 0.36, 0.21)))
MAT["board_black"] = new_mat("Wall board bare matte black", base=(0.02, 0.02, 0.021), rough=0.75, spec=0.35)
MAT["lining"] = new_mat("Lining vinyl fine grain", base=(0.026, 0.026, 0.028), rough=0.48, spec=0.45,
                        **{"Coat Weight": 0.05, "Coat Roughness": 0.3})
add_bump(MAT["lining"], "pebble", scale=1500.0, strength=0.25, distance=0.00025, rough_var=(0.40, 0.58))
MAT["knit"] = new_mat("Lining knit backing grey", base=(0.20, 0.20, 0.205), rough=0.95, spec=0.2,
                      **{"Sheen Weight": 0.6, "Sheen Roughness": 0.4})
add_bump(MAT["knit"], "felt", scale=3200.0, strength=0.35, distance=0.0002)
# --- metals
MAT["chrome"] = new_mat("Chrome polished", base=(0.92, 0.92, 0.94), rough=0.04, metal=1.0)
MAT["stainless_pol"] = new_mat("Stainless polished", base=(0.80, 0.80, 0.81), rough=0.1, metal=1.0)
MAT["stainless"] = new_mat("Stainless brushed", base=(0.74, 0.74, 0.75), rough=0.26, metal=1.0,
                           **{"Anisotropic": 0.6})
add_bump(MAT["stainless"], "brushed", scale=40.0, strength=0.08, distance=0.0001)
MAT["zinc"] = new_mat("Zinc plated steel", base=(0.62, 0.63, 0.64), rough=0.38, metal=1.0)
# Black-oxide Phillips pan heads; plate and clip screws in photos 3483/3491/3497/3502–3504.

MAT["zinc_dark"] = new_mat("Black-oxide screw", base=(0.03, 0.03, 0.032), rough=0.4, metal=0.5)
# Yellow-zinc plating on the 12 V socket body beneath the deck (3502/3481/3482).
MAT["zinc_yellow"] = new_mat("Yellow zinc plated steel", base=(0.78, 0.66, 0.32), rough=0.4, metal=1.0)
MAT["metal_worn"] = new_mat("Metal bar matte worn grey", base=(0.2, 0.2, 0.21), rough=0.6, metal=0.8)
add_bump(MAT["metal_worn"], "mottle", scale=300.0, strength=0.15, distance=0.0002,
         colors=((0.15, 0.15, 0.16), (0.26, 0.26, 0.27)))
MAT["aluminium"] = new_mat("Aluminium machined (LED heads)", base=(0.86, 0.87, 0.89), rough=0.25, metal=1.0)
MAT["tinned"] = new_mat("Tinned copper tip", base=(0.70, 0.70, 0.68), rough=0.3, metal=1.0)
# --- plastics, rubber, print
MAT["plastic"] = new_mat("Plastic black matte", base=(0.025, 0.025, 0.026), rough=0.62, spec=0.45)
MAT["plastic_gloss"] = new_mat("Plastic black gloss", base=(0.018, 0.018, 0.019), rough=0.15, spec=0.5)
MAT["plastic_semi"] = new_mat("Plastic black semigloss (cup)", base=(0.03, 0.03, 0.032), rough=0.32, spec=0.5)
MAT["plastic_tex"] = new_mat("Plastic black textured (plug head)", base=(0.03, 0.03, 0.031), rough=0.7)
add_bump(MAT["plastic_tex"], "felt", scale=1200.0, strength=0.2, distance=0.0002)
MAT["rubber"] = new_mat("Rubber black", base=(0.028, 0.028, 0.028), rough=0.72, spec=0.35)
MAT["dark_grey"] = new_mat("Dark grey moulding", base=(0.10, 0.10, 0.105), rough=0.55, spec=0.4)
MAT["label"] = new_mat("Plain label (blank, no brand)", base=(0.42, 0.42, 0.41), rough=0.6)
MAT["insulator"] = new_mat("Insulator yellowish", base=(0.75, 0.58, 0.20), rough=0.6)
MAT["qi_insert"] = new_mat("Qi pad inset matte black", base=(0.016, 0.016, 0.017), rough=0.85, spec=0.3)
MAT["qi_icon"] = new_mat("Qi icon white print", base=(0.85, 0.85, 0.83), rough=0.5)
MAT["qi_led"] = new_mat("Qi dots white", base=(0.85, 0.85, 0.85), rough=0.3)
make_emissive(MAT["qi_led"], (1.0, 1.0, 1.0), 0.6)
# Worn dark-red socket ring; colour sampled from photo 3491.

MAT["red_ring"] = new_mat("Red ring dull worn", base=(0.10, 0.03, 0.024), rough=0.5, spec=0.35)
add_bump(MAT["red_ring"], "mottle", scale=700.0, strength=0.12, distance=0.0002,
         colors=((0.045, 0.02, 0.016), (0.12, 0.035, 0.028)))
# --- clock (3483/3491: khaki/olive chapter ring, light carbon-weave centre, white marks; no emblem)
# Khaki-olive dial with G >= R, checked against photographs 3491 and 3483.
MAT["dial"] = new_mat("Clock dial khaki/olive", base=(0.40, 0.42, 0.18), rough=0.45, spec=0.4)   # Dial colour under the scene lighting.

MAT["dial_centre"] = new_mat("Clock dial centre carbon weave", base=(0.50, 0.53, 0.43), rough=0.4)
add_bump(MAT["dial_centre"], "weave", scale=1600.0, strength=0.12, distance=0.0001,
         colors=((0.42, 0.45, 0.36), (0.60, 0.63, 0.52)))
# clock body: high-gloss black so the ~2 mm black ring outside the chrome stands out from the matte deck
MAT["clock_gloss"] = new_mat("Clock body black gloss", base=(0.004, 0.004, 0.005), rough=0.35, spec=0.25,
                             **{"Coat Weight": 0.15, "Coat Roughness": 0.04})
# A rough base beneath a thin clear coat keeps the body dark with a sharp highlight.

MAT["marker"] = new_mat("Clock marks white", base=(0.92, 0.92, 0.90), rough=0.35)
# The clear fibre emits the animated colour when the lights are on.
# IMG_3439 shows the powered USB ring and labels glowing blue with the cap open.
# set_usb() opens the cap and enables that glow in the powered views;
# the photograph-comparison views keep the cap and ring in their recorded state.
MAT["usb_blue"] = new_mat("USB ring + labels (blue LED, lit when powered)", base=(0.01, 0.01, 0.02), rough=0.8,
                          spec=0.05, **{"Emission Color": (0.0, 0.0, 1.0), "Emission Strength": 0.0})
# Low specularity keeps white reflections from diluting the blue glow.
USB_GLOW = 2.5                               # emission strength of the lit ring (scaled by the render's glow gain)
# Unlit fibre: a milky, glossy cream-white rod with low transmission (3483/3491/3498/3501).

MAT["fibre"] = new_mat("Side-glow fibre clear (animated glow)", base=(0.86, 0.86, 0.82), rough=0.2, spec=0.4,
                       **{"Transmission Weight": 0.15, "IOR": 1.49, "Coat Weight": 0.4, "Coat Roughness": 0.1,
                          "Subsurface Weight": 0.4, "Subsurface Scale": 0.001})
MAT["fibre"].use_raytrace_refraction = True
MAT["fibre"].surface_render_method = 'DITHERED'
make_emissive(MAT["fibre"], CYCLE[0][1], FIBRE_GLOW)
MAT["led_front"] = new_mat("LED head light (animated)", base=(0.2, 0.2, 0.2), rough=0.3)
make_emissive(MAT["led_front"], CYCLE[0][1], HEAD_GLOW)
# the band's fibre seat (groove) under the clear fibre: smooth light grey, no grain 
MAT["fibre_seat"] = new_mat("Band fibre seat smooth light grey", base=(0.30, 0.30, 0.29), rough=0.4, spec=0.4)
# button: brushed face darker than the polished ring, black gap (SEEN 3483 c4_3483_button)
MAT["stainless_face"] = new_mat("Stainless brushed face (darker)", base=(0.45, 0.45, 0.46), rough=0.33, metal=1.0,
                                **{"Anisotropic": 0.6})
add_bump(MAT["stainless_face"], "brushed", scale=40.0, strength=0.1, distance=0.0001)
MAT["gap_black"] = new_mat("Gap black matte", base=(0.006, 0.006, 0.006), rough=0.9, spec=0.2)
# clear nylon-insulated female spades on the socket tabs (SEEN 3502/3503/3481), and the seam thread
MAT["spade_clear"] = new_mat("Spade sleeve clear yellowish nylon", base=(0.80, 0.66, 0.32), rough=0.3, spec=0.5,
                             **{"Transmission Weight": 0.5, "IOR": 1.45})
MAT["spade_clear"].surface_render_method = 'DITHERED'
MAT["thread"] = new_mat("Seam stitch thread black", base=(0.008, 0.008, 0.009), rough=0.75, spec=0.3)
# Grey double topstitching on the gear boot; rough chrome trim reflects the cabin lights broadly.


MAT["knob_chrome"] = new_mat("Knob trim chrome (bright)", base=(0.95, 0.95, 0.96), rough=0.25, metal=1.0)
MAT["thread_grey"] = new_mat("Boot stitch thread grey", base=(0.10, 0.10, 0.103), rough=0.75, spec=0.25)
# --- wiring
MAT["wire_red"] = new_mat("Wire red PVC", base=(0.42, 0.015, 0.012), rough=0.35, spec=0.5)
MAT["wire_black"] = new_mat("Wire black PVC", base=(0.02, 0.02, 0.021), rough=0.35, spec=0.5)
MAT["wire_salmon"] = new_mat("Wire salmon PVC", base=(0.62, 0.28, 0.20), rough=0.4, spec=0.5)
MAT["wire_blue"] = new_mat("Wire blue PVC", base=(0.02, 0.07, 0.30), rough=0.4, spec=0.5)
MAT["heatshrink"] = new_mat("Heat-shrink black", base=(0.02, 0.02, 0.02), rough=0.55, spec=0.4)
MAT["nylon"] = new_mat("Nylon clip black", base=(0.025, 0.025, 0.026), rough=0.45, spec=0.5)
MAT["guide"] = new_mat("Exploded guide line", base=(0.55, 0.56, 0.58), rough=0.6, spec=0.3)
# --- car context: plain dark greys, deliberately plainer (and a little lighter) than the black panel
MAT["ctx_body"] = new_mat("Context console dark grey", base=(0.045, 0.045, 0.047), rough=0.6, spec=0.4)
MAT["ctx_panel"] = new_mat("Context trim panel grey", base=(0.035, 0.035, 0.037), rough=0.5, spec=0.45)
MAT["ctx_deep"] = new_mat("Context deep recess grey", base=(0.018, 0.018, 0.019), rough=0.7, spec=0.3)
MAT["ctx_seat"] = new_mat("Context seat dark grey", base=(0.022, 0.022, 0.023), rough=0.5, spec=0.45)
add_bump(MAT["ctx_seat"], "pebble", scale=420.0, strength=0.25, distance=0.0004)
MAT["ctx_dash"] = new_mat("Context dash dark grey", base=(0.014, 0.014, 0.015), rough=0.8, spec=0.3)
add_bump(MAT["ctx_dash"], "pebble", scale=300.0, strength=0.2, distance=0.0004)
MAT["ctx_boot"] = new_mat("Context gear boot grey", base=(0.025, 0.025, 0.026), rough=0.38, spec=0.5)
MAT["ctx_knob"] = new_mat("Context knob glossy grey", base=(0.018, 0.018, 0.019), rough=0.45, spec=0.35,
                          **{"Coat Weight": 0.25, "Coat Roughness": 0.18})
MAT["ctx_satin"] = new_mat("Context satin silver-grey", base=(0.55, 0.56, 0.58), rough=0.32, metal=0.85)
MAT["ctx_button"] = new_mat("Context button grey", base=(0.06, 0.06, 0.062), rough=0.45, spec=0.45)
MAT["ctx_glass"] = new_mat("Context display dark glass", base=(0.006, 0.006, 0.007), rough=0.06, spec=0.6)
# footwell mats: near-black patterned mats (SEEN 3483; the mid-grey planes read 70-90 / 255)
MAT["ctx_carpet"] = new_mat("Context floor mat near-black", base=(0.02, 0.02, 0.021), rough=0.95, spec=0.2)
add_bump(MAT["ctx_carpet"], "mottle", scale=260.0, strength=0.5, distance=0.0008,
         colors=((0.011, 0.011, 0.012), (0.032, 0.032, 0.034)))
# --- table views: plain warm-brown surface (IMG_3491 / 3487 table), plain backdrop wall
MAT["table"] = new_mat("Table plain warm brown", base=(0.13, 0.048, 0.02), rough=0.42, spec=0.45,
                       **{"Coat Weight": 0.12, "Coat Roughness": 0.3})
add_bump(MAT["table"], "mottle", scale=8.0, strength=0.0, distance=0.0,
         colors=((0.11, 0.04, 0.017), (0.15, 0.058, 0.025)))

# animate the fibre and LED-head emission colour: hard colour steps (CONSTANT keys), as in IMG_3437
for key in ("fibre", "led_front"):
    sock = principled(MAT[key]).inputs["Emission Color"]
    for f, c in CYCLE_KEYS:
        sock.default_value = (*c, 1.0)
        sock.keyframe_insert("default_value", frame=f)
    sock.default_value = (*CYCLE[0][1], 1.0)


def set_leds(on, gain=1.0):
    """LEDs on (animated glow) or off (clear fibres, as in the daylight photos). When lit, the clear core's
    own whitish scatter is turned down so the colour stays saturated under AgX. `gain` multiplies every LED
    emission (fibres, head openings, the loose head's nose light): a render with a negative exposure offset
    passes 2^|EV| so the lit colours keep their sampled values while the daylit surfaces get darker."""
    pf = principled(MAT["fibre"])
    pf.inputs["Emission Strength"].default_value = FIBRE_GLOW * gain if on else 0.0
    # lit: the fibre's own (dim, whitish) reflection of the daylight is part of its sampled colour, so it follows the
    # gain too (base colour and specular level x gain); otherwise a darker exposure made the lit fibres over-saturated
    pf.inputs["Base Color"].default_value = (0.06 * gain, 0.06 * gain, 0.065 * gain, 1) if on else (0.86, 0.86, 0.82, 1)
    pf.inputs["Transmission Weight"].default_value = 0.3 if on else 0.15
    pf.inputs["Specular IOR Level"].default_value = min(0.5, 0.12 * gain) if on else 0.4   # own highlight would whiten the glow
    pf.inputs["Coat Weight"].default_value = 0.0 if on else 0.4
    pf.inputs["Subsurface Weight"].default_value = 0.0 if on else 0.4
    principled(MAT["led_front"]).inputs["Emission Strength"].default_value = HEAD_GLOW * gain if on else 0.0
    for lt in LED_LIGHTS:                    # small coloured light at the loose head's nose
        lt.hide_render = not on
        lt.hide_viewport = not on
        lt.data.energy = LED_LIGHT_ENERGY * gain
    # LEDs-on renders: Standard view transform keeps the emissive colours saturated (AgX desaturates them)
    vs_ = bpy.context.scene.view_settings
    if on:
        vs_.view_transform, look, vs_.exposure = LED_VIEW[0], LED_VIEW[1], float(LED_VIEW[2])
    else:
        vs_.view_transform, look, vs_.exposure = "AgX", None, 0.0
    for lk in ([look] if look else ["AgX - Medium High Contrast", "Medium High Contrast", "None"]):
        try:
            vs_.look = lk
            break
        except TypeError:
            continue


LED_LIGHTS = []
LED_LIGHT_ENERGY = 0.35                      # W, the loose head's nose light (scaled by set_leds' gain)


# --------------------------------------------------------------------------------------------
# 2. Import the STLs
# --------------------------------------------------------------------------------------------
M_FIX = Matrix.Diagonal((0.001, -0.001, 0.001, 1.0))   # mm -> m, mirror y (handedness fix)


def stl_is_binary(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(80)
        n = struct.unpack("<I", f.read(4))[0]
    return 84 + 50 * n == size


def import_stl(path, name):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    obj = new[0]
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col_console.objects.link(obj)
    obj.name = name
    obj.data.name = name
    me = obj.data
    me.transform(M_FIX)
    me.flip_normals()                  # the mirror reverses winding; restore outward normals
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-7)
    # drop float-rounding slivers (area < 0.001 mm2 and needle-thin): their random normals otherwise
    # leave dark shading lines across smooth surfaces (seen on the deck_vinyl near the rear arch)
    slivers = []
    for f in bm.faces:
        a = f.calc_area()
        if a < 1e-9:
            L = max(e.calc_length() for e in f.edges)
            if a < 1e-3 * L * L:
                slivers.append(f)
    if slivers:
        bmesh.ops.delete(bm, geom=slivers, context='FACES_ONLY')
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(math.pi) < SMOOTH_ANGLE
        else:
            e.smooth = True            # crack left by a removed sliver: do not split the shading there
    bm.to_mesh(me)
    bm.free()
    me.update()
    return obj


def find_stl(name):
    dirs = (STL_DIR,)
    for d in dirs:
        p = os.path.join(d, name + ".stl")
        if os.path.exists(p):
            if not stl_is_binary(p):          # the importer below requires binary STL
                print(f"[assemble] WARNING {p} is not a binary STL; skipped")
                continue
            return p
    return None


parts = {}
for name in DECK_WINGS + FITTINGS + LOOSE_PARTS:
    p = find_stl(name)
    if p is None:
        print(f"[assemble] WARNING part {name} not found")
        continue
    parts[name] = import_stl(p, name)
print(f"[assemble] imported {len(parts)} STLs: {', '.join(sorted(parts))}")

# sanity check of the mirror + re-wind: the vinyl's top skin (z = 0) must face up (+Z)
_me = parts["deck_vinyl"].data
_top = [p for p in _me.polygons if p.center.z > -0.00001 and abs(p.normal.z) > 0.99]
_a_up = sum(p.area for p in _top if p.normal.z > 0)
_a_all = sum(p.area for p in _top)
print(f"[assemble] normal check: {100 * _a_up / max(_a_all, 1e-12):.4f} % of the deck_vinyl top skin "
      f"(by area) faces up")
# area-weighted: the vinyl carries a few float-rounding slivers of ~1e-4 mm2 with random winding
assert _top and _a_up > 0.999 * _a_all, "face winding is inverted after the handedness fix"


# --------------------------------------------------------------------------------------------
# 3. Material assignment (per object, and per face where one STL holds several materials)
# --------------------------------------------------------------------------------------------
def face_data(obj):
    """Face centres and normals in shared-frame mm (x, y, z), undoing the Blender mirror."""
    me = obj.data
    n = len(me.polygons)
    c = np.empty(n * 3)
    nn = np.empty(n * 3)
    me.polygons.foreach_get("center", c)
    me.polygons.foreach_get("normal", nn)
    c = c.reshape(-1, 3) * 1000.0
    nn = nn.reshape(-1, 3)
    c[:, 1] *= -1.0
    nn[:, 1] *= -1.0
    return c, nn


def assign(obj, mats, index_fn=None):
    me = obj.data
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    if index_fn is not None:
        c, nn = face_data(obj)
        idx = np.asarray(index_fn(c, nn)).astype(np.int32)
        me.polygons.foreach_set("material_index", idx)
        me.update()


def radial(c, cx, cy):
    return np.hypot(c[:, 0] - cx, c[:, 1] - cy)


SIMPLE = {
    "deck": "mdf", "deck_vinyl": "leather", "deck_felt": "felt", "notch_lip": "leather",
    "band_left": "leather", "band_right": "leather",
    "band_roll_left": "smooth_black", "band_roll_right": "smooth_black",
    "clock_body": "clock_gloss", "clock_bezel": "chrome", "clock_face": "dial",
    "clock_dial_centre": "dial_centre", "clock_marks": "marker",
    "button": "stainless_pol", "button_face": "stainless_face",
    "cup_ring": "chrome", "slot": "plastic_gloss", "pocket": "plastic", "bar": "metal_worn",
    "plate": "plastic", "plate_screws": "zinc_dark",
    "usb": "plastic", "usb_ring": "usb_blue", "usb_cap": "rubber", "usb_cap_open": "rubber",
    "v12": "chrome", "v12_ring": "red_ring", "v12_cap": "rubber",
    "fibre_l": "fibre", "fibre_r": "fibre", "head_boots": "rubber", "lead_loose": "wire_black",
    "ctrl_leads": "wire_black",
    "qi_frame": "leather", "qi_chrome": "chrome", "qi_insert": "qi_insert", "qi_icon": "qi_icon",
    "qi_led": "qi_led", "qi_screw": "stainless_pol",
    "qi_cable_red": "wire_red", "qi_cable_black": "wire_black", "plug_lead": "wire_black",
}
for name, key in SIMPLE.items():
    if name in parts:
        assign(parts[name], [MAT[key]])


# tables read straight from params.scad, so the face rules follow any later edit there
def scad_table(name, path=os.path.join(ROOT, "scad", "params.scad")):
    import re
    txt = open(path).read()
    m = re.search(r"^" + name + r"\s*=\s*(\[.*?\]);", txt, re.S | re.M)
    body = re.sub(r"//[^\n]*", "", m.group(1))
    return eval(body)


def scad_value(name, path=os.path.join(ROOT, "scad", "params.scad")):
    import re
    m = re.search(r"^" + name + r"\s*=\s*([-0-9.]+)\s*;", open(path).read(), re.M)
    return float(m.group(1))


BAND_PTS = np.array(scad_table("band_pts"), float)          # [y, x_inner, x_fibre, x_outer, z_top]
FIBRE_END = {1: scad_value("wing_tip_y") + scad_value("fibre_end_back_p"),
             -1: scad_value("wing_tip_y") + scad_value("fibre_end_back_d")}
FIBRE_CLIMB_Y = scad_value("band_end_y")


# Apply smooth light-grey material only beneath the full-width fibre.
# The last fib_taper millimetres taper to a point; that region and the closing groove retain leatherette.







SEAT_END_MARGIN = scad_value("fib_taper", os.path.join(ROOT, "scad", "loose.scad"))
for name, s_ in (("band_right", 1), ("band_left", -1)):
    if name in parts:
        def seat_idx(c, nn, s_=s_):
            y = c[:, 1]
            xf = np.interp(y, BAND_PTS[:, 0], BAND_PTS[:, 2])
            zt = np.interp(y, BAND_PTS[:, 0], BAND_PTS[:, 4])
            m = ((np.abs(s_ * c[:, 0] - xf) < 1.9) & (c[:, 2] < zt - 0.9) & (c[:, 2] > zt - 4.4)
                 & (y < FIBRE_CLIMB_Y + 0.5) & (y > FIBRE_END[s_] + SEAT_END_MARGIN))
            return m.astype(int)
        assign(parts[name], [MAT["leather"], MAT["fibre_seat"]], seat_idx)

# button: the face gap's floor and the ring's inner wall are black (3483 shows a thin dark gap)
BUTTON_C = (91.5, 33.0)
if "button" in parts:
    assign(parts["button"], [MAT["stainless_pol"], MAT["gap_black"]],
           lambda c, nn: (radial(c, *BUTTON_C) < 6.42) & (c[:, 2] > 0.4) & (c[:, 2] < 2.1))

# walls (wings.scad ): leatherette on the outward faces, smooth black on the top of the rear
# segment behind the band (y > 242, 3491 crops), bare matte black board everywhere else
for name, s in (("wing_right", 1.0), ("wing_left", -1.0)):
    if name in parts:
        def wing_idx(c, nn, s=s):
            idx = np.zeros(len(c), dtype=int)
            idx[s * nn[:, 0] > 0.3] = 1
            idx[(c[:, 1] > 241.0) & (nn[:, 2] > 0.35)] = 2
            return idx
        assign(parts[name], [MAT["board_black"], MAT["leather"], MAT["smooth_black"]], wing_idx)


# notch lining (deck.scad , nose tip to nose tip): fine vinyl on the faces that look into the open
# notch, grey knit on the back and the raw cut edges. "Into the notch" = inboard along the arms, -y on
# the back edge, toward the corner centres (+-67, -20) round the R14 back corners, and away from the
# nose centres (+-125, -206) round the arm noses.
def skirt_idx(c, nn):
    x, y = c[:, 0], c[:, 1]
    s = np.sign(x)
    s[s == 0] = 1.0
    inx = np.zeros(len(c))
    iny = np.zeros(len(c))
    arm = (y <= -20.0) & (y > -196.0)
    inx[arm] = -s[arm]
    cor = (y > -20.0) & (np.abs(x) > 67.0)
    dx = s[cor] * 67.0 - x[cor]
    dy = -20.0 - y[cor]
    d = np.hypot(dx, dy) + 1e-9
    inx[cor] = dx / d
    iny[cor] = dy / d
    back = (y > -20.0) & (np.abs(x) <= 67.0)
    iny[back] = -1.0
    nose = y <= -196.0
    dx = x[nose] - s[nose] * 125.0
    dy = y[nose] + 206.0
    d = np.hypot(dx, dy) + 1e-9
    inx[nose] = dx / d
    iny[nose] = dy / d
    facing = nn[:, 0] * inx + nn[:, 1] * iny
    return (facing <= 0.15).astype(int)


for nm_ in ("notch_skirt", "notch_skirt_car"):
    if nm_ in parts:
        assign(parts[nm_], [MAT["lining"], MAT["knit"]], skirt_idx)

# cup: black, with the flat dark-grey outer bottom (3502)
if "cup" in parts:
    assign(parts["cup"], [MAT["plastic_semi"], MAT["dark_grey"]],
           lambda c, nn: (c[:, 2] < -58.5) & (nn[:, 2] < -0.6))
# USB body under the deck: dark grey threaded body and nut (3502), tinned push-on tabs
if "usb_body" in parts:
    assign(parts["usb_body"], [MAT["dark_grey"], MAT["tinned"]], lambda c, nn: c[:, 2] < -32.2)
# 12 V body: yellow-zinc threaded cup and round ring nut, yellowish insulator disc at the bottom of the bore
# Material reference: photographs 3502 and 3503.
if "v12_body" in parts:
    assign(parts["v12_body"], [MAT["zinc_yellow"], MAT["insulator"]],
           lambda c, nn: (c[:, 2] < -33.4) & (c[:, 2] > -34.6) & (radial(c, *V12_C) < 10.6))
# The controller label is a separate blank pale rectangle on its down-facing surface.

if "ctrl" in parts:
    assign(parts["ctrl"], [MAT["plastic"]])


# cigarette plug (loose.scad): silver pin + knurled cap at the tip (x < 52.5), silver spring contacts
# standing proud of the Ø21 barrel, chrome collar at x 84-87, textured black head
def plug_idx(c, nn):
    x = c[:, 0]
    r = np.hypot(c[:, 1] - PLUG_TIP[1], c[:, 2] - PLUG_TIP[2])
    idx = np.zeros(len(c), dtype=int)
    idx[x < 52.6] = 1
    idx[(x >= 52.6) & (x < 83.8) & (r > 11.0)] = 1
    idx[(x >= 83.8) & (x <= 87.2)] = 2
    idx[x > 87.2] = 3
    return idx


if "plug" in parts:
    assign(parts["plug"], [MAT["plastic"], MAT["stainless_pol"], MAT["chrome"], MAT["plastic_tex"]], plug_idx)

# Aluminium LED heads with luminous nose openings and end faces; colour follows the fibre cycle.


for name, (ctr, ax) in HEADS.items():
    if name not in parts:
        continue
    ctr = np.array(ctr)
    d = np.array(ax) / np.linalg.norm(ax)

    def head_idx(c, nn, ctr=ctr, d=d):
        v = c - ctr
        t = v @ d
        r = np.linalg.norm(v - np.outer(t, d), axis=1)
        return ((t > HEAD_L / 2 - 6.4) & (r < 2.95)) | ((t > HEAD_L / 2 - 0.75) & (r < 6.0))

    assign(parts[name], [MAT["aluminium"], MAT["led_front"]], head_idx)

missing = [n for n, o in parts.items() if not o.data.materials]
for n in missing:
    print(f"[assemble] WARNING no material rule for {n}; using matte black plastic")
    assign(parts[n], [MAT["plastic"]])


# --------------------------------------------------------------------------------------------
# 3b. Split a few STLs so each piece can be shown or posed on its own
# --------------------------------------------------------------------------------------------
def split_copy(obj, keep, name):
    """New object holding a copy of obj's mesh with only the faces where keep[i] is True."""
    me = obj.data.copy()
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    dead = [f for f, k in zip(bm.faces, keep) if not k]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    col_console.objects.link(o)
    return o


# head_boots holds the boots of all three heads: split by nearest head so each follows its head
if "head_boots" in parts:
    hb = parts.pop("head_boots")
    c, _ = face_data(hb)
    refs = {n: head_rear(n)[0] for n in ("head_l", "head_r", "head_loose")}
    keys = list(refs)
    dist = np.stack([np.linalg.norm(c - refs[k], axis=1) for k in keys], axis=1)
    lab = dist.argmin(axis=1)
    for i, k in enumerate(keys):
        nm = "head_boot_" + k.split("_", 1)[1]
        parts[nm] = split_copy(hb, lab == i, nm)
    bpy.data.objects.remove(hb, do_unlink=True)

# plug_lead (W1) and lead_loose run from outside the panel through the corner clip (y = -2) to under the
# deck. "_inside" copies keep only the under-deck run, for the views without the car (table, underside).
for nm in ("plug_lead", "lead_loose"):
    if nm in parts:
        c, _ = face_data(parts[nm])
        parts[nm + "_inside"] = split_copy(parts[nm], c[:, 1] >= WCLIP[1], nm + "_inside")

LOOSE_ITEMS = ("qi_frame", "qi_chrome", "qi_insert", "qi_icon", "qi_led", "qi_screw", "plug",
               "head_loose", "head_boot_loose")
QI_PAD = ("qi_frame", "qi_chrome", "qi_insert", "qi_icon", "qi_led", "qi_screw")
OUTSIDE_LEADS = ("qi_cable_red", "qi_cable_black", "plug_lead", "lead_loose")
INSIDE_LEADS = ("plug_lead_inside", "lead_loose_inside")


# blank controller label: its own thin rectangle on the down-facing face, ~2/3 of it (SEEN 3502; )
def _label_mesh():
    x0, x1, y0, y1 = CTRL_C[0] - 13.0, CTRL_C[0] + 13.0, CTRL_C[1] - 15.0, CTRL_C[1] + 15.0
    z0, z1 = CTRL_C[2] - 10.0 - 0.22, CTRL_C[2] - 10.0 + 0.05
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new("ctrl_label")
    me.from_pydata([mm(*q) for q in v], [], f)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("ctrl_label", me)
    col_console.objects.link(o)
    me.materials.append(MAT["label"])
    return o


if "ctrl" in parts:
    parts["ctrl_label"] = _label_mesh()


# shape keys (vertices are in Blender metres: model x = X * 1000, model y = -Y * 1000, z = Z * 1000)
def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def add_key(obj, name, offset_fn):
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if me.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    k = obj.shape_key_add(name=name, from_mix=False)
    k.data.foreach_set("co", (co + offset_fn(co)).ravel())
    k.value = 0.0
    return k


_BOW_Y = np.array([b[0] for b in BOW][::-1], float)
_BOW_X = np.array([b[1] for b in BOW][::-1], float)


def bow_offset(ramped):
    def fn(co):
        y = -co[:, 1] * 1000.0
        dx = np.interp(y, _BOW_Y, _BOW_X)
        if ramped:                     # deck / notch parts: 0 behind y -110, full by -190 (notch edges at -100 unshifted)
            dx = dx * _sstep((-110.0 - y) / 80.0)
        out = np.zeros_like(co)
        out[:, 0] = dx / 1000.0
        return out
    return fn


for nm_ in BOW_FULL + BOW_RAMPED:
    if nm_ in parts:
        add_key(parts[nm_], "free_on_table", bow_offset(nm_ in BOW_RAMPED))


# outside leads in the car follow CTX_SHIFT where they lie on the car (weight 1) and stay put where they enter
# the panel (weight 0): the Qi cord round its end under the passenger lining, W1 and the third head's lead behind
# the driver notch-corner clip (y > -7)
def ctx_shift_offset(kind):
    d = np.array([CTX_SHIFT[0], -CTX_SHIFT[1], CTX_SHIFT[2]]) / 1000.0
    def fn(co):
        x, y, z = co[:, 0] * 1000.0, -co[:, 1] * 1000.0, co[:, 2] * 1000.0
        if kind == "qi":
            dist = np.sqrt((x - QI_LEAD_END[0]) ** 2 + (y - QI_LEAD_END[1]) ** 2 + (z - QI_LEAD_END[2]) ** 2)
            w = _sstep((dist - 15.0) / 45.0)
        else:
            w = _sstep((-7.0 - y) / 40.0)
        return np.outer(w, d)
    return fn


for nm_, kind in (("qi_cable_red", "qi"), ("qi_cable_black", "qi"), ("plug_lead", "clip"), ("lead_loose", "clip")):
    if nm_ in parts:
        add_key(parts[nm_], "car_context_shift", ctx_shift_offset(kind))


def set_keys(view):
    for o in parts.values():
        sk = o.data.shape_keys if o.type == 'MESH' else None
        if sk is None:
            continue
        for kb in sk.key_blocks[1:]:
            if kb.name == "free_on_table":
                kb.value = 1.0 if view in ("table", "table87") else 0.0
            elif kb.name == "car_context_shift":
                kb.value = 1.0 if view in ("car", "top") else 0.0


# --------------------------------------------------------------------------------------------
# 4. Mesh helpers for the context and the small wiring hardware (vertices in model mm)
# --------------------------------------------------------------------------------------------
def mk_mesh(name, verts, faces, mat, col, bevel=0.0, segs=3, smooth=True, recalc=True, tag=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([mm(*v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = smooth
    for e in bm.edges:
        e.smooth = (len(e.link_faces) == 2 and e.calc_face_angle(math.pi) < SMOOTH_ANGLE)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    me.materials.append(mat)
    if bevel > 0:
        b = o.modifiers.new("Bevel", 'BEVEL')
        b.width = bevel * 0.001
        b.segments = segs
        b.limit_method = 'ANGLE'
        b.angle_limit = math.radians(40)
        b.harden_normals = True
    if tag:
        o["ctx_group"] = tag
    return o


def box_vf(x0, x1, y0, y1, z0, z1):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return v, f


def box(name, x0, x1, y0, y1, z0, z1, mat, col=None, bevel=0.0, segs=3, tag=None):
    v, f = box_vf(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))
    return mk_mesh(name, v, f, mat, col or col_context, bevel, segs, tag=tag)


def obox(name, ctr, size, R, mat, col=None, bevel=0.0, segs=3, tag=None):
    """Oriented box: centre, full size along its local axes, R = 3x3 (columns = local axes, model frame)."""
    R = np.array(R, dtype=float)
    v, f = box_vf(-size[0] / 2, size[0] / 2, -size[1] / 2, size[1] / 2, -size[2] / 2, size[2] / 2)
    v = [tuple(np.array(ctr) + R @ np.array(p)) for p in v]
    return mk_mesh(name, v, f, mat, col or col_context, bevel, segs, tag=tag)


def rot_x(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def rot_z(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def prism(name, poly, a0, a1, mat, axis="z", col=None, bevel=0.0, segs=3, tag=None):
    """Polygon extruded: axis 'z' -> poly in (x, y), from z = a0 to a1; axis 'x' -> poly in (y, z)."""
    n = len(poly)
    if axis == "z":
        v = [(p[0], p[1], a0) for p in poly] + [(p[0], p[1], a1) for p in poly]
    else:
        v = [(a0, p[0], p[1]) for p in poly] + [(a1, p[0], p[1]) for p in poly]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    f += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mk_mesh(name, v, f, mat, col or col_context, bevel, segs, tag=tag)


def frame_of(d):
    d = np.array(d, dtype=float)
    d /= np.linalg.norm(d)
    ref = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(ref, d)
    u /= np.linalg.norm(u)
    w = np.cross(d, u)
    return u, w, d


def cyl(name, p0, p1, r0, r1=None, mat=None, col=None, n=40, tag=None, bevel=0.0):
    """Frustum between two points (model mm), with caps."""
    r1 = r0 if r1 is None else r1
    p0, p1 = np.array(p0, float), np.array(p1, float)
    u, w, d = frame_of(p1 - p0)
    v = []
    for p, r in ((p0, r0), (p1, r1)):
        for i in range(n):
            a = 2 * math.pi * i / n
            v.append(tuple(p + r * (math.cos(a) * u + math.sin(a) * w)))
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    f += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mk_mesh(name, v, f, mat, col or col_context, bevel=bevel, tag=tag)


def loft(name, rings, mat, col=None, tag=None):
    """Closed loft through rings of equal point count (each a list of model points), capped."""
    n = len(rings[0])
    v = [tuple(p) for ring in rings for p in ring]
    f = [tuple(range(n - 1, -1, -1)), tuple(range((len(rings) - 1) * n, len(rings) * n))]
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        f += [(a + i, a + (i + 1) % n, b + (i + 1) % n, b + i) for i in range(n)]
    return mk_mesh(name, v, f, mat, col or col_context, tag=tag)


def boolean_diff(obj, cutter):
    m = obj.modifiers.new("Cut", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.solver = 'EXACT'
    m.object = cutter
    cutter.hide_render = True
    cutter.hide_viewport = True


# Deck seam stitching runs 2.5 mm inboard of each rim, from y = -15 to y = 190 (photo 3483).


def _stitch_mesh(pitch=4.0, dash=2.6, w=0.7, z0=-0.05, z1=0.16, inset=2.5):
    V, Fc = [], []
    for s_ in (1, -1):
        for yc in np.arange(-15.0, 190.0 + 1e-6, pitch):
            xi = float(np.interp(yc, BAND_PTS[:, 0], BAND_PTS[:, 1])) - inset
            dxdy = (float(np.interp(yc + 1, BAND_PTS[:, 0], BAND_PTS[:, 1]))
                    - float(np.interp(yc - 1, BAND_PTS[:, 0], BAND_PTS[:, 1]))) / 2.0
            t = np.array([s_ * dxdy, 1.0])
            t /= np.linalg.norm(t)
            n = np.array([t[1], -t[0]])
            c = np.array([s_ * xi, yc])
            base = len(V)
            for z in (z0, z1):
                for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    q = c + a * t * dash / 2 + b * n * w / 2
                    V.append((float(q[0]), float(q[1]), z))
            Fc += [tuple(base + i for i in f) for f in
                   ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))]
    return mk_mesh("deck_stitch", V, Fc, MAT["thread"], col_console, smooth=False)


parts["deck_stitch"] = _stitch_mesh()


# --------------------------------------------------------------------------------------------
# 5. Low-detail car context (GEOMETRY.md section 11; plain dark grey, no logos, no lettering)
# --------------------------------------------------------------------------------------------
# console half-width = wall inner face - 2 (section 11.1)
HW = [(-211, 141.0), (-190, 139.5), (-100, 130.5), (0, 120.5), (100, 112.5), (200, 105.0), (290, 103.0),
      (650, 103.0)]


def hw_poly(y0, y1):
    ys = [y0] + [y for y, _ in HW if y0 < y < y1] + [y1]
    xs = list(np.interp(ys, [p[0] for p in HW], [p[1] for p in HW]))
    right = [(x, y) for x, y in zip(xs, ys)]
    left = [(-x, y) for x, y in zip(xs, ys)][::-1]
    return right + left


def notch_x(y):
    """|x| of the notch open edge (section 3/4): 77 + 0.21 (-y)."""
    return 77.0 + 0.21 * (-y)


# 1. console body: lower part below the walls' bottom edges (visible under the walls), the hidden
#    recess under the deck (top below -90, y 0..170), and the supports under the arms (top -14)
prism("Console body (lower)", hw_poly(-211, 650), -330, -125, MAT["ctx_body"])
prism("Console recess under the deck (hidden)", hw_poly(0, 170), -125, -90, MAT["ctx_deep"])
prism("Console top behind the armrest nose (hidden)", hw_poly(165, 650), -125, -14, MAT["ctx_body"])
for s, side in ((1, "passenger"), (-1, "driver")):
    ys = list(np.linspace(-211, -3, 12))
    inner = [(s * (notch_x(y) + 3.0), y) for y in ys]
    outer = [(s * float(np.interp(y, [p[0] for p in HW], [p[1] for p in HW])), y) for y in ys][::-1]
    poly = inner + outer
    if s < 0:
        poly = poly[::-1]
    # passenger side dark (in 3483 leather runs down to the boot there; any gap must read dark)
    prism(f"Arm support under the {side} arm", poly, -125, -14, MAT["ctx_deep"] if s > 0 else MAT["ctx_body"])
box("Well floor, passenger half (dark)", 0, 118, -211, -3, -126.5, -124.5, MAT["ctx_deep"])
# 2. gear-lever well: back wall behind the lining, driver-half shift panel, passenger-half floor
box("Well back wall", -82, 82, -3.5, 2, -125, -14, MAT["ctx_deep"])
SLOPE = math.degrees(math.atan2(19.0, 105.0))       # shift panel: z -14 at y -16 -> -33 at y -121


def shift_z(y):
    return -14.0 if y >= -16 else -14.0 + (y + 16.0) * 19.0 / 105.0


shift = prism("Shift-button panel (driver half)",
              [(-3, -14), (-16, -14), (-121, -33), (-128, -33.5), (-128, -125), (-3, -125)],
              -97, -4, MAT["ctx_panel"], axis="x")
cub = box("cubby cutter", -91, -15, -85, -30, -68.5, 10, MAT["ctx_deep"])
boolean_diff(shift, cub)
box("X-mat in the cubby (rubber)", -90, -16, -84, -31, -68.5, -67.6, MAT["ctx_deep"])
for nm, x, y, w, l in (("EV MODE", -37, -17, 34, 13), ("ECO", -76, -87, 19, 13), ("NORMAL", -52, -87, 25, 13),
                       ("SPORT", -27, -87, 19, 13), ("P", -57, -113, 30, 17), ("HOLD", -26, -121, 24, 16)):
    z = shift_z(y)
    obox(f"Shift button {nm} (plain)", (x, y, z + 1.0), (w, l, 3.0), rot_x(SLOPE if y < -16 else 0),
         MAT["ctx_button"], bevel=1.2)
box("Shift indicator strip", -5, 4, -128, -3.5, -125, -40, MAT["ctx_deep"])


# 3. Gear boot and knob, sized against IMG_3483–3485.
# The knob has a wide black body, glossy insert, chrome U trim and a collar.
# A stitched leather boot widens towards its base. Loft sections below describe
# the silhouette in the fitted-camera view; the cabin geometry is illustrative.
def bez(p0, p1, p2, t):
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def sup_ring(cx, cy, z, wx, wy, n=4.0, N=64, a0=0.0, a1=2 * math.pi, closed=True):
    pts = []
    for i in range(N if closed else N + 1):
        a = a0 + (a1 - a0) * i / N
        ca, sa = math.cos(a), math.sin(a)
        pts.append((cx + wx / 2 * math.copysign(abs(ca) ** (2 / n), ca),
                    cy + wy / 2 * math.copysign(abs(sa) ** (2 / n), sa), z))
    return pts


# knob body sections (z, width x, length y, centre x, centre y): rounded-square superellipses; the foot leans ~4 mm
# toward the passenger (SEEN 3483: collar centre ~4 mm right of the top's centre)
KNOB_SEC = [(-8, 40.5, 36, 42.6, -143.5), (0, 43.5, 39, 41.8, -144.5), (10, 45.5, 41.5, 40.7, -145.5),
            (20, 47, 42.5, 39.7, -146), (30, 47.5, 42.5, 38.9, -146), (38, 47.5, 42.5, 38.5, -146),
            (41.5, 46.5, 41.5, 38.3, -146), (43.8, 44, 39, 38.2, -146), (45.6, 39, 34, 38.2, -146),
            (46.8, 30, 26, 38.2, -146), (47.6, 18, 15.5, 38.2, -146), (47.9, 7, 6, 38.2, -146)]
KNOB_SEC_F = [KNOB_SEC[0]] + [tuple(np.array(KNOB_SEC[i]) * (1 - u) + np.array(KNOB_SEC[i + 1]) * u)
                              for i in range(len(KNOB_SEC) - 1) for u in (0.5, 1.0)]     # finer for smooth shading
knob_obj = loft("Gear knob (body, glossy black)", [sup_ring(cx, cy, z, wx, wy) for z, wx, wy, cx, cy in KNOB_SEC_F],
                MAT["ctx_knob"])
COLLAR_SEC = [(-17, 34, 37, 43.4, -142.6), (-12.5, 37, 40, 43.3, -142.8), (-8.5, 37.5, 40.5, 43.1, -143),
              (-5.5, 35, 38, 42.9, -143.3)]
loft("Gear knob collar (glossy black)", [sup_ring(cx, cy, z, wx, wy) for z, wx, wy, cx, cy in COLLAR_SEC],
     MAT["ctx_knob"])
_KZ = np.array([k[0] for k in KNOB_SEC], float)


def knob_cx(z):
    return float(np.interp(z, _KZ, [k[3] for k in KNOB_SEC]))


def knob_rear(z):
    return float(np.interp(z, _KZ, [k[4] + k[2] / 2 for k in KNOB_SEC]))


def knob_u_edge(hw_top, hw_bot, z_b, n_top=9, n_rear=11):
    """One edge of the chrome U (model mm): left rail along the top from the front edge to the rear-top shoulder, down
    the rear face tapering in to the bottom corner, across, and back up the right side. Shrink-wrapped onto the knob."""
    zt, yf, yr = 45.0, -165.0, knob_rear(38)
    half = [(hw_top, yf + 3 + (yr - yf - 6) * s, zt) for s in np.linspace(0, 1, n_top)]
    half += [(hw_top + (hw_bot - hw_top) * s ** 1.3, knob_rear(zt - 3 - (zt - 3 - z_b) * s) + 0.3,
              zt - 3 - (zt - 3 - z_b) * s) for s in np.linspace(0, 1, n_rear)]
    return ([(knob_cx(z) - h, y, z) for h, y, z in half] + [(knob_cx(z) + h, y, z) for h, y, z in reversed(half)])


_uo, _ui = knob_u_edge(19.0, 12.5, 2.0), knob_u_edge(17.0, 9.0, 13.0)
_nu = len(_uo)
_uv = _uo + _ui
_uf = [(i, i + 1, _nu + i + 1, _nu + i) for i in range(_nu - 1)]
u_trim = mk_mesh("Gear knob chrome U trim (polished)", _uv, _uf, MAT["knob_chrome"], col_context, smooth=True)
_sub = u_trim.modifiers.new("Subdivide", 'SUBSURF')
_sub.levels = _sub.render_levels = 2
_sub.subdivision_type = 'SIMPLE'
_sw = u_trim.modifiers.new("Onto the knob", 'SHRINKWRAP')
_sw.target = knob_obj
_sw.wrap_method = 'NEAREST_SURFACEPOINT'
_sw.wrap_mode = 'OUTSIDE_SURFACE'
_sw.offset = 0.00025
_so = u_trim.modifiers.new("Thickness", 'SOLIDIFY')
_so.thickness = 0.0006
_so.offset = 1.0

# boot: a cone along a leaning spine from the bunched base deep in the well (behind the notch's back edge) up into the
# collar; rx 48 -> 15, ry 40 -> 16 (SEEN 3483: ~222 px under the collar, ~350 at frame y 2000, ~455 at 2300)
B0, B1, B2 = np.array([45.0, -35.0, -125.0]), np.array([45.0, -110.0, -80.0]), np.array([43.4, -142.6, -15.0])
BOOT_SEAM_A = math.radians(101.0)     # the seam runs down the rear (+90 deg = toward the rear cameras), a little to the
BOOT_SEAM_W = math.radians(3.2)       #   driver side of it (SEEN 3483); double row 2 x 3.2 deg apart, on a low welt
BOOT_FLANK = 12.0                     # mm, passenger-flank bulge (8-14)


def boot_frame(t):
    c = bez(B0, B1, B2, t)
    tan = 2 * (1 - t) * (B1 - B0) + 2 * t * (B2 - B1)
    tan /= np.linalg.norm(tan)
    ux = np.array([1.0, 0, 0]) - tan[0] * tan
    ux /= np.linalg.norm(ux)
    return c, ux, np.cross(tan, ux)


def boot_r(t, a):
    rx, ry = 48.0 - 33.0 * t, 40.0 - 24.0 * t
    # the passenger flank bunches outward in the upper half (SEEN 3483, enhanced crop: a matte, creased flank reaches the
    # lining at frame x ~1590, y 1650-1900, ~10-13 mm beyond a round cone; it hid the car's tray rim there)
    if math.cos(a) > 0:
        rx += BOOT_FLANK * math.cos(a) ** 2 * math.exp(-((t - 0.78) / 0.14) ** 2)
    # soft folds: a few rings bunch (stronger toward the base) plus slanting creases; a low welt along the seam
    da = math.atan2(math.sin(a - BOOT_SEAM_A), math.cos(a - BOOT_SEAM_A))
    wr = (1.0 + 0.035 * (1.2 - t) * math.sin(2 * math.pi * 3.5 * t)
          + 0.03 * math.sin(5 * a + 11.0 * t) * math.sin(math.pi * min(1.0, t * 1.15))
          + 0.025 * math.exp(-(da / (1.6 * BOOT_SEAM_W)) ** 2))
    return wr * rx, wr * ry


def boot_pt(t, a, lift=0.0):
    c, ux, uy = boot_frame(t)
    rx, ry = boot_r(t, a)
    d = rx * math.cos(a) * ux + ry * math.sin(a) * uy
    return tuple(c + d * (1.0 + lift / max(1.0, np.linalg.norm(d))))


NR, NT = 96, 29
rings = [[boot_pt(k / (NT - 1), 2 * math.pi * i / NR) for i in range(NR)] for k in range(NT)]
boot_obj = loft("Gear boot (stitched leather cone)", rings, MAT["ctx_boot"])
def ctx_tube(name, pts_mm, mat, r):
    """Thin round tube (curve) through the points, in the car context."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r * 0.001
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts_mm) - 1)
    for pt, p in zip(sp.points, pts_mm):
        pt.co = (*mm(*p), 1.0)
    o = bpy.data.objects.new(name, cu)
    col_context.objects.link(o)
    o.data.materials.append(mat)
    return o


for _k, _da in (("a", -BOOT_SEAM_W), ("b", BOOT_SEAM_W)):
    ctx_tube(f"Gear boot seam stitching {_k}", [boot_pt(t, BOOT_SEAM_A + _da, lift=0.3) for t in np.linspace(0.0, 0.985, 80)],
             MAT["thread_grey"], 0.35)
# the car's tray rim must not cut the boot (it used to hide its sides and pinch it into a bottle): a slightly larger
# copy of the boot is subtracted from the rim and its satin line below
boot_cut = loft("Gear boot cutter (hidden)", [[boot_pt(k / (NT - 1), 2 * math.pi * i / NR, lift=1.0) for i in range(NR)]
                                              for k in range(NT)], MAT["ctx_boot"])


# 4. Qi tray. The pad pose was re-fitted on IMG_3483 (tilt 20.1 deg, front lower, top centre z -64.3), so
#    the tray floor follows the pad's underside and drops toward the front wall;
#    section 11's flat floor at -60 would cut through the pad. Rear rim just behind the pad's raised edge.
TT = math.tan(math.radians(QI_TILT))


def tray_floor_z(y):
    return QI_TOP_C[2] + TT * (y - QI_TOP_C[1]) - QI_SIZE[2] / math.cos(math.radians(QI_TILT)) - 0.6


# The tray rim stops at x = +62 beneath the passenger boot flank.
# Its hidden extent is inferred; photograph 3483 shows no exposed rim in this gap.


_rim = box("Qi tray rear rim", -106, 62, -143.5, -128, -125, -30, MAT["ctx_panel"], bevel=2.5)
_rim_line = box("Qi tray rim satin line", -100, 62, -144.3, -143.2, -33.5, -30.6, MAT["ctx_satin"])
for _o in (_rim, _rim_line):
    boolean_diff(_o, boot_cut)
prism("Qi tray floor (follows the pad)",
      [(-143.5, tray_floor_z(-143.5)), (-305, tray_floor_z(-305)), (-305, -125), (-143.5, -125)],
      -126, 126, MAT["ctx_deep"], axis="x")
for s in (1, -1):
    box(f"Qi tray side wall ({'passenger' if s > 0 else 'driver'})", s * 111, s * 141, -305, -211, -125, -14,
        MAT["ctx_body"], bevel=2)
# 5. tray front wall with the car's own 12 V outlet and USB/AUX block (the panel's plug lies unplugged)
box("Tray front wall", -112, 112, -340, -302, -125, -20, MAT["ctx_panel"])
cyl("Car 12 V outlet bezel (satin)", (-39, -302.5, -65), (-39, -299.0, -65), 14.0, mat=MAT["ctx_satin"])
cyl("Car 12 V outlet mouth", (-39, -299.5, -65), (-39, -298.8, -65), 10.5, mat=MAT["ctx_deep"])
obox("Car 12 V outlet cap (open)", (-62, -296.0, -72), (17, 3.0, 17), rot_z(-25), MAT["ctx_knob"], bevel=2.5)
box("Car USB/AUX block", -7, 40, -303.5, -301.0, -80, -50, MAT["ctx_deep"], bevel=1.0)
box("Car USB/AUX lid (open)", 40, 43, -326, -301.5, -80, -50, MAT["ctx_panel"], bevel=0.8)
# 6. lower stack bezel (TRC row): face at y -270, z -24..+40, TRC OFF button (plain)
box("Lower stack bezel", -135, 135, -330, -270, -24, 40, MAT["ctx_panel"], bevel=3)
box("TRC button (plain)", -100, -82, -272.5, -269.0, -11, 5, MAT["ctx_button"], bevel=1.5)
# 7. climate panel: near-vertical face (y -246 at the bottom, -256 at the top), display, button row
prism("Climate panel", [(-246, 40), (-256, 118), (-336, 118), (-336, 40)], -145, 145, MAT["ctx_panel"],
      axis="x", bevel=3)
LEAN = math.degrees(math.atan2(10.0, 78.0))


def climate_face_y(z):
    return -246.0 - (z - 40.0) * 10.0 / 78.0


obox("Climate display (dark glass, blank)", (5, climate_face_y(84) + 0.4, 84), (170, 1.6, 44), rot_x(LEAN),
     MAT["ctx_glass"], bevel=0.6)
for i in range(9):
    x = -84 + i * 21.5
    obox(f"Climate button {i + 1} (plain)", (x, climate_face_y(50) + 1.2, 50), (17, 2.4, 6), rot_x(LEAN),
         MAT["ctx_button"], bevel=0.8)
# 8. climate knobs: face centres (-98, -220, 88) and (108, -220, 92); axis rearward and 30 deg up.
# (SEEN 3483 tips_zoom / c_ltip / c_rtip, 3484 p3484_tips): no full satin ring. Each knob = a dark
# ribbed grip ~47 across, a thin chrome bezel round the black face (34), and a tall satin HOOD over the top and
# back only (~200 deg, ~62 across, rising to z ~ +122 behind the knob). The hood leaves the passenger tip visible.
KD = np.array([0.0, math.cos(math.radians(30)), math.sin(math.radians(30))])
KUP = np.array([0.0, -math.sin(math.radians(30)), math.cos(math.radians(30))])     # "up", square to the axis
KSIDE = np.array([1.0, 0.0, 0.0])


def ribbed_grip(name, fc, r, t0, t1, ribs=36, depth=0.7, mat=None):
    rings = []
    for t in (t0, t1):
        c = fc - KD * t
        ring = []
        for i in range(ribs * 2):
            a = math.pi * i / ribs
            rr = r if i % 2 == 0 else r - depth
            ring.append(tuple(c + rr * (math.cos(a) * KSIDE + math.sin(a) * KUP)))
        rings.append(ring)
    return loft(name, rings, mat)


def knob_hood(name, fc, t_back, t_top, t_side, r_in=24.8, r_out=29.0, top=1.25, half=100.0, N=40, mat=None):
    """Satin hood: shell round the knob axis over +-half deg from "up", taller on top (outer radius x top there).
    It runs from the panel (t_back behind the face) forward to a slanted front edge: t_top behind the face at the
    top, t_side at the sides, so it covers the top of the grip further forward (3484 p3484_tips)."""
    def prof(r, stretch):
        pts = []
        for i in range(N + 1):
            ph = math.radians(-half + 2 * half * i / N)
            k = 1.0 + (stretch - 1.0) * max(0.0, math.cos(ph)) ** 2
            pts.append((r * math.sin(ph), r * math.cos(ph) * k, t_side + (t_top - t_side) * max(0.0, math.cos(ph))))
        return pts
    P = prof(r_out, top) + prof(r_in, 1.0)[::-1]          # closed outline: outer arc, then inner arc back
    rings = [[tuple(fc - KD * t_back + q[0] * KSIDE + q[1] * KUP) for q in P],
             [tuple(fc - KD * q[2] + q[0] * KSIDE + q[1] * KUP) for q in P]]
    return loft(name, rings, mat)


for nm, fc in (("driver", (-98.0, -220.0, 88.0)), ("passenger", (108.0, -220.0, 92.0))):
    fc = np.array(fc)
    # sizes from the photos (3484 / 3483, face incl. bezel = section 11's 34): grip ~48, hood ~58 wide
    ribbed_grip(f"Climate knob grip ({nm}, dark ribbed)", fc, 24.0, 30.0, 1.6, mat=MAT["ctx_knob"])
    cyl(f"Climate knob bezel ({nm}, chrome)", fc - KD * 1.9, fc + KD * 0.35, 17.3, mat=MAT["chrome"], n=56)
    cyl(f"Climate knob face ({nm}, blank)", fc - KD * 1.0, fc + KD * 0.8, 15.8, mat=MAT["ctx_knob"], n=48)
    knob_hood(f"Climate knob hood ({nm}, satin)", fc, 40.0, 12.0, 24.0, mat=MAT["ctx_satin"])
# 9. car silver pillars beside the stack. (SEEN 3483/3484): a wide satin strip running continuously
# from the knob hood down to under the arm nose: top at (+-128, -250, +100) (joins the hood's outer side), bottom
# (+-128, -215, -15), ~19 wide 
for s in (1, -1):
    p0, p1 = np.array([s * 128.0, -250.0, 100.0]), np.array([s * 128.0, -215.0, -15.0])   # ends under the nose
    a = (p1 - p0) / np.linalg.norm(p1 - p0)
    wdir = np.array([1.0, 0, 0]) - a[0] * a
    wdir /= np.linalg.norm(wdir)
    ndir = np.cross(a, wdir)
    obox(f"Silver pillar ({'passenger' if s > 0 else 'driver'})", (p0 + p1) / 2,
         (19.0, 5.0, float(np.linalg.norm(p1 - p0)) + 6), np.c_[wdir, ndir, a], MAT["ctx_satin"], bevel=1.5)
    # The stack side stops at y = -232 so its upper corner stays beneath the rim.
    
    
    box(f"Stack side ({'passenger' if s > 0 else 'driver'})", s * 136, s * 144, -336, -232, -125, 40,
        MAT["ctx_panel"], bevel=3)
# 10. dash above with the vent and hazard row (y -296..-326, z +140..+160), plain dark slots
prism("Dash upper", [(-258, 118), (-300, 136), (-328, 162), (-620, 196), (-620, 118)], -430, 430,
      MAT["ctx_dash"], axis="x", bevel=4)
for x0, x1 in ((-175, -60), (-40, 60), (75, 190)):
    obox(f"Vent slot x {x0}..{x1} (dark)", ((x0 + x1) / 2, -312.3, 147.9), (x1 - x0, 1.6, 16),
         rot_x(math.degrees(math.atan2(28.0, 26.0))), MAT["ctx_deep"], bevel=0.5)
box("Hazard switch (plain)", 4, 20, -314, -305, 142, 156, MAT["ctx_button"], bevel=1.2)
# 11. armrest: nose top edge at y ~155 on the centre line curving to ~174 at x +-90, top +40, 200 wide.
# Armrest height and fore-aft position are coupled in photo 3483.
# The inferred lid height uses the middle of the plausible range: z = +40.
xs = np.linspace(-100, 100, 21)
nose = [(float(x), 155.0 + 19.0 * (x / 90.0) ** 2) for x in xs]
arm_poly = [nose[-1]] + [(100.0, 560.0), (-100.0, 560.0)] + nose[:-1]
prism("Armrest lid", arm_poly, 6, 40, MAT["ctx_seat"], bevel=13, segs=5, tag="armrest")
box("Armrest box", -103, 103, 295, 600, -125, 6, MAT["ctx_body"], bevel=4)
# 12. seats (inner bolsters outboard of the walls, |x| 145-255, beside y +10..+450), footwell mats
for s, side in ((1, "passenger"), (-1, "driver")):
    def sx(a, b):
        return (s * a, s * b) if s > 0 else (s * b, s * a)
    # heights not measured (section 11.12): cushion well below the deck, inner bolster a little higher
    box(f"Seat inner bolster ({side})", *sx(147, 255), 10, 450, -330, -140, MAT["ctx_seat"], bevel=42, segs=6)
    box(f"Seat cushion ({side})", *sx(235, 640), 0, 460, -330, -180, MAT["ctx_seat"], bevel=48, segs=6)
    box(f"Seat outer bolster ({side})", *sx(620, 700), 10, 450, -330, -150, MAT["ctx_seat"], bevel=40, segs=6)
    obox(f"Seat back ({side})", (s * 420, 545, 60), (560, 110, 520), rot_x(-14), MAT["ctx_seat"],
         bevel=45, segs=6)
    box(f"Footwell mat ({side})", *sx(152, 700), -720, -46, -330, -326, MAT["ctx_carpet"], bevel=6)
bpy.ops.mesh.primitive_plane_add(size=5.0, location=mm(0, 0, -331))
floor = bpy.context.active_object
for c in floor.users_collection:
    c.objects.unlink(floor)
col_context.objects.link(floor)
floor.name = "Floor"
floor.data.materials.append(MAT["ctx_deep"])
# the whole car context follows the re-fitted Cam 3483 (CTX_SHIFT); objects are created in place,
# so the shift is their location (displacement in Blender axes = mm() of the model shift)
for o in col_context.objects:
    o.location = o.location + mm(*CTX_SHIFT)

# table for the table views: plain warm-brown plane through the walls' bottom line z = -120 - 0.008 y
TBL = lambda y: -120.15 - 0.008 * y          # noqa: E731  table height under a point (model mm)
tv = [(-1600, -1600, TBL(-1600)), (1600, -1600, TBL(-1600)), (1600, 1600, TBL(1600)), (-1600, 1600, TBL(1600))]
mk_mesh("Table (plain warm brown)", tv, [(0, 3, 2, 1)], MAT["table"], col_table, recalc=False)   # normal up after the mirror


# --------------------------------------------------------------------------------------------
# 6. World, lights, cameras, render settings
# --------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("Environment")
scene.world = world
if hasattr(world, "use_nodes") and not world.node_tree:
    world.use_nodes = True
wnt = world.node_tree
bg = wnt.nodes.get("Background")
# lighting/reflection environment: soft gradient (bright above, dark below); camera rays see a flat backdrop
tc = wnt.nodes.new("ShaderNodeTexCoord")
sep = wnt.nodes.new("ShaderNodeSeparateXYZ")
mr = wnt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -1.0
mr.inputs["From Max"].default_value = 1.0
ramp = wnt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.004, 0.004, 0.005, 1)
ramp.color_ramp.elements[1].position = 0.95
ramp.color_ramp.elements[1].color = (0.06, 0.063, 0.07, 1)
wnt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
wnt.links.new(sep.outputs["Z"], mr.inputs["Value"])
wnt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
lp = wnt.nodes.new("ShaderNodeLightPath")
mixc = wnt.nodes.new("ShaderNodeMix")
mixc.data_type = 'RGBA'
gain_mix = wnt.nodes.new("ShaderNodeMix")
gain_mix.data_type = 'RGBA'
gain_mix.blend_type = 'MULTIPLY'
gain_mix.inputs["Factor"].default_value = 1.0
wnt.links.new(ramp.outputs["Color"], gain_mix.inputs["A"])
wnt.links.new(lp.outputs["Is Camera Ray"], mixc.inputs["Factor"])
wnt.links.new(gain_mix.outputs["Result"], mixc.inputs["A"])
WORLD = {   # per view: (backdrop seen by the camera, tint/gain of the lighting environment)
    "car": ((0.012, 0.012, 0.014, 1), (1.0, 1.0, 1.0, 1)),
    "studio": ((0.075, 0.077, 0.082, 1), (1.0, 1.0, 1.0, 1)),
    "table": ((0.15, 0.14, 0.125, 1), (1.3, 1.2, 1.05, 1)),
}
mixc.inputs["B"].default_value = WORLD["car"][0]
gain_mix.inputs["B"].default_value = WORLD["car"][1]
wnt.links.new(mixc.outputs["Result"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0


def look_at(obj, target, right=None):
    """Point -Z of obj at target. With `right`, the frame's horizontal axis follows that world direction."""
    if right is None:
        d = Vector(target) - obj.location
        obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return
    zc = (obj.location - Vector(target)).normalized()
    xc = Vector(right)
    xc = (xc - xc.dot(zc) * zc).normalized()
    yc = zc.cross(xc)
    obj.rotation_euler = Matrix((xc, yc, zc)).transposed().to_euler()


def area_light(name, loc, target, size, power, size_y=None, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = power
    ld.color = color
    if size_y:
        ld.shape = 'RECTANGLE'
        ld.size = size
        ld.size_y = size_y
    else:
        ld.shape = 'DISK'
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    col_rig.objects.link(o)
    o.location = loc
    look_at(o, target)
    return o


LIGHTS = {
    # in the car: daylight through the windscreen (front, high), roof, side windows, rear window
    "wind": area_light("Windscreen daylight", mm(0, -900, 950), mm(0, -40, 0), 1.6, 30.0, size_y=0.7,
                       color=(1.0, 0.98, 0.95)),
    "roof": area_light("Roof softbox", mm(-80, 250, 1150), mm(0, 0, 0), 1.4, 16.0, size_y=0.8),
    "side_l": area_light("Driver window", mm(-1100, -60, 520), mm(0, -20, -20), 1.0, 7.0,
                         color=(0.95, 0.97, 1.0)),
    "side_r": area_light("Passenger window", mm(1100, -60, 520), mm(0, -20, -20), 1.0, 7.0,
                         color=(0.95, 0.97, 1.0)),
    "rear": area_light("Rear window", mm(150, 1300, 700), mm(0, 0, -20), 1.2, 8.0),
    # top view: two long soft boxes at 45 deg from the sides (their reflections miss the camera)
    "top_l": area_light("Top side box (driver)", mm(-700, 8, 700), mm(0, 8, 0), 1.6, 13.0, size_y=0.6),
    "top_r": area_light("Top side box (passenger)", mm(700, 8, 700), mm(0, 8, 0), 1.6, 13.0, size_y=0.6),
    # underside
    "u_key": area_light("Under key", mm(380, 300, -800), mm(0, 20, -40), 1.2, 15.0),
    "u_fill": area_light("Under fill", mm(-450, -300, -700), mm(0, 20, -40), 1.2, 8.0),
    "u_rim": area_light("Under rim (rear)", mm(0, 900, -300), mm(0, 20, -40), 1.0, 6.0),
    # table: warm ceiling lights and a cooler window, as in the room of 3486-3491
    "t_ceil": area_light("Table ceiling light", mm(900, 700, 1500), mm(0, 0, -120), 2.4, 60.0,
                         color=(1.0, 0.93, 0.82)),
    "t_win": area_light("Table window", mm(-1400, -900, 900), mm(0, 0, -100), 1.6, 24.0, color=(0.92, 0.96, 1.0)),
    "t_fill": area_light("Table fill", mm(1200, 600, 500), mm(0, 0, -60), 1.4, 9.0, color=(1.0, 0.95, 0.88)),
}
# coloured glow at the loose third head's nose (LEDs on): a small point light parented to head_loose, so it follows
# every pose of the head; colour keyed to the same cycle as the fibres (video IMG_3437_01/02/05/06)
if "head_loose" in parts:
    _hc, _ha = HEADS["head_loose"]
    _ld = bpy.data.lights.new("Loose head nose glow", 'POINT')
    _ld.energy = LED_LIGHT_ENERGY
    _ld.shadow_soft_size = 0.002
    for f_, c_ in CYCLE_KEYS:
        _ld.color = c_
        _ld.keyframe_insert("color", frame=f_)
    _lo = bpy.data.objects.new("Loose head nose glow", _ld)
    col_rig.objects.link(_lo)
    _lo.parent = parts["head_loose"]
    _lo.location = mm(*(np.array(_hc) + np.array(_ha) * (HEAD_L / 2 + 4.0)))
    LED_LIGHTS.append(_lo)

LIGHT_SETS = {
    "car": ("wind", "roof", "side_l", "side_r", "rear"),
    "top": ("top_l", "top_r", "roof"),
    "under": ("u_key", "u_fill", "u_rim"),
    "table": ("t_ceil", "t_win", "t_fill"),
    "explode": ("roof", "side_l", "side_r", "rear", "wind"),
}


def camera(name, loc, target, lens=40.0, ortho=None, right=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.01
    cd.clip_end = 20.0
    cd.sensor_width = 36.0
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    o = bpy.data.objects.new(name, cd)
    col_rig.objects.link(o)
    o.location = loc
    if target is not None:
        look_at(o, target, right)
    return o


def fitted_camera(name, loc_m, euler_deg, lens, fit):
    o = camera(name, Vector(loc_m), None, lens=lens)
    o.rotation_euler = tuple(math.radians(a) for a in euler_deg)
    o.data.sensor_fit = fit
    o.data.sensor_height = 36.0
    return o


# hero: 3/4 view fitted in the car, from behind on the passenger side, over the armrest
CAM_HERO = camera("Cam hero", mm(470, 470, 720), mm(-10, -45, -15), lens=32.0)
# Cam 3483 (GEOMETRY section 12): the photo is portrait 1134 x 2016; this landscape render keeps the
# same pose and the photo's long-side (vertical) field of view, so the photo's frame is the central
# 562 px wide column of the 1600 x 1000 render and the sides show more of the car.
# Re-fitted 3 Oct (f fixed at 1673 px) to the clock, button, cup, plate and slot plus both arm noses and both rim
# tips: noses within 9 px, tips within 11 px, fittings within 20 px. The old pose (-0.0300, -0.1100, 0.3830) /
# (25.38, -4.32, -1.07) put both tips and noses ~30 px too high (the "front drop" was a camera error).
CAM_3483 = fitted_camera("Cam 3483", (-0.0238, -0.1108, 0.3893), (25.83, -3.46, -0.84), 25.09, 'VERTICAL')
# top: straight down, orthographic; car front to the LEFT, passenger at the top (as IMG_3491)
CAM_TOP = camera("Cam top", mm(0, 8, 1500), mm(0, 8, 0), ortho=0.66)
CAM_TOP.rotation_euler = (0.0, 0.0, -math.pi / 2)
# Cam 3491 (section 12) and Cam 3487 (wall fit cam3487_wall.npy), f = 2800 px at 4032 wide
CAM_3491 = fitted_camera("Cam 3491", (-0.0282, -0.0511, 0.5778), (4.16, 3.04, -85.55), 25.0, 'HORIZONTAL')
# Cam 3487 fits the near-wall outline and both walls' tips and rear ends in the table pose.
# Near-wall median residual: 2.3 px; far tip: 29 px; far rear corner: 9 px at 4032 px width.
# The passenger tip appears about 12 mm further forward in the photograph than in the model;
# the loose arm can flex between poses (GEOMETRY, section 15).
CAM_3487 = fitted_camera("Cam 3487", (-0.77070, 0.07117, 0.23318), (71.067, -0.905, -95.901), 25.0, 'HORIZONTAL')
# underside: from below, front of the car to the LEFT, driver side at the top (as IMG_3502)
CAM_UNDER = camera("Cam underside", mm(15, 70, -640), mm(0, 70, -20), lens=40.0, right=mm(0, 1, 0))
# exploded view
CAM_EXPL = camera("Cam exploded", mm(560, 900, 470), mm(0, -50, -55), lens=33.0)

# render settings
scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [
    e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = 99                    # two full colour loops (2 x 1.65 s), so playback loops cleanly
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.film_transparent = False
ee = scene.eevee
ee.taa_render_samples = int(os.environ.get("CONSOLE_SAMPLES", "96"))
ee.use_raytracing = True
ee.use_shadows = True
ee.use_fast_gi = True
try:
    ee.ray_tracing_options.resolution_scale = '1'
except Exception:
    pass
vs = scene.view_settings
vs.view_transform = 'AgX'
for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
    try:
        vs.look = look
        break
    except TypeError:
        continue
vs.exposure = 0.0

# stamp strip (project name + caption): only with CONSOLE_STAMP=1
r = scene.render
r.use_stamp = STAMP
for attr in ("use_stamp_date", "use_stamp_time", "use_stamp_render_time", "use_stamp_frame",
             "use_stamp_frame_range", "use_stamp_memory", "use_stamp_hostname", "use_stamp_camera",
             "use_stamp_lens", "use_stamp_scene", "use_stamp_marker", "use_stamp_filename",
             "use_stamp_sequencer_strip", "use_stamp_compositing_time"):
    if hasattr(r, attr):
        setattr(r, attr, False)
r.use_stamp_note = True
r.stamp_font_size = 14
r.stamp_foreground = (0.92, 0.92, 0.92, 1.0)
r.stamp_background = (0.0, 0.0, 0.0, 0.6)

# compositor: soft bloom so the LEDs and fibres glow
comp = bpy.data.node_groups.new("Console compositing", "CompositorNodeTree")
comp.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
rl = comp.nodes.new("CompositorNodeRLayers")
glare = comp.nodes.new("CompositorNodeGlare")
for tname in ("Bloom", "Fog Glow"):
    try:
        glare.inputs["Type"].default_value = tname
        break
    except Exception:
        continue
glare.inputs["Threshold"].default_value = 0.55
glare.inputs["Strength"].default_value = 0.35
glare.inputs["Size"].default_value = 0.45
gout = comp.nodes.new("NodeGroupOutput")
comp.links.new(rl.outputs["Image"], glare.inputs["Image"])
comp.links.new(glare.outputs[0], gout.inputs[0])
scene.compositing_node_group = comp


# --------------------------------------------------------------------------------------------
# 7. Poses: exploded offsets and table poses
# --------------------------------------------------------------------------------------------
EXPLODE_LIFT = 40
EXPLODE = {
    # deck layers apart; the notch lip and lining travel with the leatherette skin
    "deck_vinyl": (0, 0, 0), "notch_lip": (0, 0, 0), "notch_skirt": (0, 0, 0),
    "deck": (0, 0, -45), "deck_felt": (0, 0, -90),
    # fittings lifted; socket bodies and the slot's pocket/bar lowered under the felt
    "plate": (0, 0, 45), "plate_screws": (0, 0, 82),
    "usb": (0, 0, 66), "usb_ring": (0, 0, 84), "usb_cap": (0, 0, 104), "usb_cap_open": (0, 0, 104), "usb_body": (0, 0, -150),
    "v12": (0, 0, 66), "v12_ring": (0, 0, 82), "v12_cap": (0, 0, 100), "v12_body": (0, 0, -150),
    "cup": (0, 0, 72), "cup_ring": (0, 0, 92),
    "clock_body": (0, 0, 96), "clock_face": (0, 0, 104), "clock_dial_centre": (0, 0, 104),
    "clock_marks": (0, 0, 104), "clock_bezel": (0, 0, 113),
    "button": (0, 0, 52), "button_face": (0, 0, 60),
    "slot": (0, 0, 44), "pocket": (0, 0, -160), "bar": (0, 0, -195),
    # walls pulled outward with their bands; each light chain (head -> fibre) travels with its wall
    "wing_right": (160, 0, 0), "band_right": (160, 0, 30), "band_roll_right": (160, 0, 30),
    "fibre_r": (160, 0, 30), "head_r": (160, 0, 30), "head_boot_r": (160, 0, 30),
    "wing_left": (-160, 0, 0), "band_left": (-160, 0, 30), "band_roll_left": (-160, 0, 30),
    "fibre_l": (-160, 0, 30), "head_l": (-160, 0, 30), "head_boot_l": (-160, 0, 30),
    # controller lowered under the cup (its blank label with it); the seam stitching travels with the skin
    "ctrl": (0, 0, -165), "ctrl_label": (0, 0, -165), "deck_stitch": (0, 0, 0),
    # the separate plug and third head: moved forward beside the pad (the pad is laid flat, see QI_EXP_TOP)
    "plug": (-20, -200, 20), "head_loose": (-60, -290, 40), "head_boot_loose": (-60, -290, 40),
}
EXPLODE = {k: (v[0], v[1], v[2] + EXPLODE_LIFT) for k, v in EXPLODE.items()}


def xoff(name):
    return EXPLODE.get(name, (0, 0, EXPLODE_LIFT))


SM = Matrix.Diagonal((0.001, -0.001, 0.001, 1.0))
SMI = SM.inverted()


def M_model(R3=None, t=(0, 0, 0)):
    M = Matrix.Identity(4)
    if R3 is not None:
        for i in range(3):
            for j in range(3):
                M[i][j] = float(R3[i][j])
    M[0][3], M[1][3], M[2][3] = t
    return M


def to_blender(Mm):
    return SM @ Mm @ SMI


def apply_model(Mm, p):
    v = Mm @ Vector((p[0], p[1], p[2], 1.0))
    return (v[0], v[1], v[2])


# Table poses read off IMG_3491 through Cam 3491 (back-projected onto the table, corrected for height):
#   pad centre (-14, -327), long side turned -21.5 deg (passenger end forward), screw at the rear/driver
#   corner as in the photo; plug tip (-20, -480) with the head toward (+x, +y) at 46 deg; third head nose
#   toward (-0.29, -0.96) at (-169, -391). Positions +-10 mm.
QI_TAB_TOP = (-14.0, -327.0, TBL(-327.0) + QI_SIZE[2])
M_QI_CAR = M_model(t=QI_TOP_C) @ M_model(rot_x(QI_TILT)) @ M_model(rot_z(QI_ROT))
M_QI_TAB = M_model(t=QI_TAB_TOP) @ M_model(rot_z(-21.5))
MM_QI = M_QI_TAB @ M_QI_CAR.inverted()
PLUG_TAB_TIP = (-20.0, -480.0, TBL(-480.0) + 15.5)
MM_PLUG = M_model(t=PLUG_TAB_TIP) @ M_model(rot_z(46.0)) @ M_model(t=tuple(-v for v in PLUG_TIP))
HEAD_TAB_C = (-169.0, -391.0, TBL(-391.0) + 6.5)
MM_HEAD = M_model(t=HEAD_TAB_C) @ M_model(rot_z(73.3)) @ M_model(t=tuple(-v for v in HEADS["head_loose"][0]))
TABLE_POSE = {n: to_blender(MM_QI) for n in QI_PAD}
TABLE_POSE["plug"] = to_blender(MM_PLUG)
TABLE_POSE["head_loose"] = to_blender(MM_HEAD)
TABLE_POSE["head_boot_loose"] = to_blender(MM_HEAD)
# Table pose for photograph 3487. Loose pad and plug positions differ from photograph 3491.
# Positions are registered to camera 3487 with approximately 15 mm uncertainty; the third head is hidden.




QI_TAB_TOP_87 = (-70.0, -365.0, TBL(-365.0) + QI_SIZE[2])
MM_QI_87 = M_model(t=QI_TAB_TOP_87) @ M_model(rot_z(-30.0)) @ M_QI_CAR.inverted()
PLUG_TAB_TIP_87 = (68.0, -423.0, TBL(-423.0) + 15.5)
MM_PLUG_87 = M_model(t=PLUG_TAB_TIP_87) @ M_model(rot_z(73.0)) @ M_model(t=tuple(-v for v in PLUG_TIP))
TABLE_POSE_87 = {n: to_blender(MM_QI_87) for n in QI_PAD}
TABLE_POSE_87["plug"] = to_blender(MM_PLUG_87)
# exploded view: the separate Qi pad laid flat (untilted, long side across) in front of the arm tips
QI_EXP_TOP = (0.0, -360.0, 30.0)
MM_QI_EXP = M_model(t=QI_EXP_TOP) @ M_QI_CAR.inverted()


def explode_pt(x, y, z, anchor):
    """A point that moves with `anchor` in the exploded view."""
    if anchor in QI_PAD:
        return apply_model(MM_QI_EXP, (x, y, z))
    o = xoff(anchor)
    return (x + o[0], y + o[1], z + o[2])


def set_pose(view):
    set_keys(view)
    for name, o in parts.items():
        if view == "explode":
            o.matrix_world = to_blender(MM_QI_EXP) if name in QI_PAD else Matrix.Translation(mm(*xoff(name)))
        elif view == "table" and name in TABLE_POSE:
            o.matrix_world = TABLE_POSE[name]
        elif view == "table87" and name in TABLE_POSE_87:
            o.matrix_world = TABLE_POSE_87[name]
        elif view in ("car", "top") and name in LOOSE_ITEMS:
            o.matrix_world = Matrix.Translation(mm(*CTX_SHIFT))     # with the car context (CTX_SHIFT)
        else:
            o.matrix_world = Matrix.Identity(4)


# --------------------------------------------------------------------------------------------
# 8. Wiring (APPROXIMATE PATHS) and small hardware, from the routes (params.scad section 5,
#    GEOMETRY section 9). Each control point names an anchor part: in the exploded view the point moves
#    with that part, so the wires stretch between the exploded parts.
# --------------------------------------------------------------------------------------------
col_wires = bpy.data.collections.new("Wiring under the deck (approximate paths)")
col_wires_x = bpy.data.collections.new("Wiring and guide lines, exploded view (approximate)")
col_wires_t = bpy.data.collections.new("Table-state cables (table views, approximate)")
col_wires_u = bpy.data.collections.new("Cable tails (underside view, approximate)")
col_wires_t87 = bpy.data.collections.new("Table-state cables, IMG_3487 layout (approximate)")
for c in (col_wires, col_wires_x, col_wires_t, col_wires_u, col_wires_t87):
    scene.collection.children.link(c)


def tube(name, pts_mm, mat, col, r=1.5, res=10):
    """Swept round tube through the points (Bezier, auto handles: passes through every point)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r * 0.001
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts_mm) - 1)
    for bp, p in zip(sp.bezier_points, pts_mm):
        bp.co = mm(*p)
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    sp.resolution_u = res
    o = bpy.data.objects.new(name, cu)
    col.objects.link(o)
    o.data.materials.append(mat)
    o["approximate"] = True
    return o


def offset_path(pts, d):
    """Shift a polyline sideways (horizontal, perpendicular to its direction) by d mm (zip cords)."""
    P = np.array([p[:3] for p in pts], float)
    out = []
    for i in range(len(P)):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        n = np.cross(t, [0, 0, 1.0])
        n = n / (np.linalg.norm(n) + 1e-9)
        out.append(tuple(P[i] + d * n) + tuple(pts[i][3:]))
    return out


def pclip(name, ring_c, cable_dir, cable_r, screw_dir, col, off=(0, 0, 0), width=6.5, t=0.9):
    """Black nylon P-clip: strap from a pan-head screw on the felt, round the cable, back to the screw."""
    rc = np.array(ring_c, float) + np.array(off, float)
    d = np.array(cable_dir, float)
    d /= np.linalg.norm(d)
    u = np.array(screw_dir, float)
    u = u - (u @ d) * d
    u[2] = 0.0
    u /= np.linalg.norm(u)
    fz = FELT_Z + off[2] - t / 2
    R = cable_r + t / 2 + 0.15
    cz = min(rc[2], fz - R)
    c = np.array([rc[0], rc[1], cz])
    S = c + u * (R + 7.0)
    S[2] = fz
    path = [S, np.array([c[0], c[1], fz]) + u * 1.0]
    for k in range(25):
        a = math.pi / 2 - 2 * math.pi * k / 24          # round the cable, starting at the top
        path.append(c + R * (math.cos(a) * u + math.sin(a) * np.array([0, 0, 1.0])))
    path.append(np.array([c[0], c[1], fz - t]) + u * 1.0)
    path.append(S - np.array([0, 0, t]))
    v = []
    for p in path:
        v += [tuple(p - d * width / 2), tuple(p + d * width / 2)]
    f = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(path) - 1)]
    o = mk_mesh(name, v, f, MAT["nylon"], col, recalc=False)
    sol = o.modifiers.new("Thickness", 'SOLIDIFY')
    sol.thickness = t * 0.001
    sh = S - np.array([0, 0, t + 0.1])
    cyl(name + " screw", sh, sh - np.array([0, 0, 1.7]), 3.1, 2.6, mat=MAT["zinc_dark"], col=col, n=24)
    for k, R3 in enumerate((rot_z(0), rot_z(90))):             # Phillips cross in the black-oxide head (3502-3504)
        obox(name + f" screw cross {k}", sh - np.array([0, 0, 1.62]), (3.4, 0.6, 0.25), R3, MAT["gap_black"], col)
    return o


def connector(name, ctr, direction, col, off=(0, 0, 0), d=7.0, length=22.0):
    """Two mated ribbed in-line connectors (black), centred at ctr along direction."""
    c = np.array(ctr, float) + np.array(off, float)
    a = np.array(direction, float)
    a /= np.linalg.norm(a)
    cyl(name, c - a * length / 2, c + a * length / 2, d / 2 - 0.8, mat=MAT["plastic"], col=col, n=28)
    cyl(name + " body", c - a * length * 0.28, c + a * length * 0.28, d / 2, mat=MAT["plastic"], col=col, n=28)
    for k in (-0.42, -0.36, 0.36, 0.42):
        q = c + a * length * k
        cyl(name + f" rib {k}", q - a * 0.6, q + a * 0.6, d / 2 - 0.2, mat=MAT["plastic"], col=col, n=28)


F = "deck_felt"
HL = head_stub_end("head_l")
HR = head_stub_end("head_r")
MOULD_END = (-51.0 + 14.0 * 0.482, 59.0 + 14.0 * 0.876, -14.0)      # end of W1's moulded end (plug_lead)
# routes (model mm) with anchors; z = -15 lies on the felt, cords slightly closer to it
# Driver branch: beside the slot pocket and around its rear end to the head’s +x stub.
# Keep the slot opening x = -78.5..-63.5, y = 54..138 clear (photo 3502).


LED_D = [(5, 41, -15.2, F), (-30, 50, -15.2, F), (-50, 53, -15.2, F), (-58.5, 60, -15.2, F), (-59, 80, -15.2, F),
         (-59, 124, -15.2, F), (-59, 139, -16.0, F), (-61, 143, -17.5, "head_l"), (*HL, "head_l")]
LED_P = [(25, 32, -15.2, F), (75, 34, -15.2, F), (98, 44, -15.2, F), (100, 74, -15.2, F),
         (100, 116, -15.2, F), (98.5, 122, -17.5, "head_r"), (*HR, "head_r")]
JUMPER = [(25, 32, -15.2, F), (15, 37, -15.2, F), (5, 41, -15.2, F)]
QI_LEAD = [(5, 54, -13.4, F), (95, 24, -13.4, F), (101, 0, -13.4, F), (101, -56, -13.4, F),
           (100, -96, -15, F), (QI_LEAD_END[0], QI_LEAD_END[1], QI_LEAD_END[2], F)]
# Loosely curved red/black splice bundle with sleeves; clips remain at y = 59 and 97 (3502).

SPLICE = [(5, 50, -13.6, F), (8.5, 66, -13.8, F), (3, 84, -13.6, F), (6.5, 102, -13.8, F), (2.5, 120, -13.7, F),
          (5, 134, -13.6, F)]


def splice_at(y):
    ys_ = [p[1] for p in SPLICE]
    return (float(np.interp(y, ys_, [p[0] for p in SPLICE])), y, float(np.interp(y, ys_, [p[2] for p in SPLICE])))


def splice_sub(y0, y1, n=6):
    return [(*splice_at(y0 + (y1 - y0) * i / n), F) for i in range(n + 1)]


# sleeves: the photo reads ~30-50 mm sleeves with ~10-15 mm gaps, but the bundle is only ~95 long here (y 39-134,
# GEOMETRY section 9), so three ~26 sleeves with ~9 gaps (3-4 separate wires show in the gaps)
SPLICE_SLEEVES = ((44, 70), (79, 105), (114, 133))
SPLICE_12V = [(5, 118, -13.6, F), (-10, 122, -16, F), (-22, 124, -26, "v12_body"), (-30.5, 124, -40, "v12_body"),
              (-30.5, 124, -44.5, "v12_body")]
# socket tails with slack (SEEN 3502/3503/3481): salmon from W1's moulded end to the USB's -x tab,
# a second salmon loop from the USB's +x tab to the 12 V side tab, blue from the moulded end past both sockets to
# the 12 V centre terminal and on in a ~40 mm loop toward the passenger and back
USB_TAB = {-1: (USB_C[0] - 5.0, USB_C[1], -36.0), 1: (USB_C[0] + 5.0, USB_C[1], -36.0)}
V12_TAB = (V12_C[0] + 4.0, V12_C[1], -39.5)
V12_STUD = (V12_C[0], V12_C[1], -41.5)
TAIL_SALMON = [(*MOULD_END, F), (-47, 69, -20, F), (-52, 76, -30, "usb_body"), (-44, 73, -40, "usb_body"),
               (-37, 77, -43, "usb_body"), (USB_TAB[-1][0], USB_TAB[-1][1], -42.5, "usb_body")]
TAIL_SALMON_2 = [(USB_TAB[1][0], USB_TAB[1][1], -42.5, "usb_body"), (-19, 84, -44, "usb_body"),
                 (-13, 100, -34, F), (-16, 116, -38, "v12_body"), (-22, 125, -47, "v12_body"),
                 (V12_TAB[0], V12_TAB[1], -46.0, "v12_body")]
TAIL_BLUE = [(*MOULD_END, F), (-48, 90, -20, F), (-47, 110, -30, F), (-40, 131, -42, "v12_body"),
             (-22, 141, -28, F), (-9, 140, -18, F), (-12, 129, -30, F), (-24, 125.5, -44, "v12_body"),
             (V12_STUD[0], V12_STUD[1], -47.5, "v12_body")]
BTN_W1 = [(91.5, 33, -12.4, F), (84, 36, -13.3, F), (82.5, 29.5, -13.3, F), (89, 30, -13.3, F)]
BTN_W2 = [(92.5, 34, -12.4, F), (99, 37, -13.3, F), (99, 44, -13.3, F), (94, 42, -13.3, F)]
CTRL_DC = [(61, 147, -70, "ctrl"), (64, 150, -45, "ctrl"), (65, 150, -18, F), (70, 161, -15, F),
           (42, 160, -15, F), (20, 150, -15, F), (5, 134, -15, F)]
CTRL_OUT = [(61, 67, -70, "ctrl"), (58, 60, -45, "ctrl"), (45, 50, -18, F), (25, 32, -15, F)]
W1_UNDER = [(-96, -2, -14, F), (-80, 14, -14, F), (-62, 39, -14, F), (-51, 59, -14, F)]


def _on_pad(x, y):
    return (x, y, qi_top_z_at(y) + (2.5 + 0.4) / math.cos(math.radians(QI_TILT)))


W1_OUTSIDE = ([(*PLUG_EXIT_END, "plug"), (97, -248, -58, "plug"), (90, -243, qi_top_z_at(-243) + 5.5, "qi_frame")]
              + [(*_on_pad(x, y), "qi_frame") for x, y in ((72, -237), (62, -232), (25, -214), (-12, -192),
                                                          (-34, -170))]
              + [(-17, -155, -32.5, F), (-38, -131, -29.5, F), (-62, -100, -26.5, F), (-76, -70, -21, F),
                 (-84, -40, -14.5, F), (-89, -18, -13.5, F), (-94, -6, -13.8, F)])
LEAD3 = ([(*tuple(head_rear("head_loose")[0] - head_rear("head_loose")[1] * HEAD_BOOT), "head_loose"),
          (-46, -74.5, -60.3, "head_loose"), (-40, -70, -53, "head_loose"), (-37, -62, -41, F),
          (-40, -50, -30.5, F), (-45, -38, -23.5, F), (-52, -28, -15.5, F), (-64, -18, -13.6, F),
          (-77, -11.5, -13.5, F), (-89, -5.5, -14, F), (*WCLIP, F), (-91, 14, -14, F), (-82, 34, -14.3, F),
          (-71, 45.5, -14.7, F), (-57, 50, -15, F)])      # loose.scad lead_loose_pts (ends outside the slot pocket)
QI_CORD = ([(*qi_xform_pt(QI_EXIT_LOCAL), "qi_frame"), (-85, -180, -60, "qi_frame")]
           + [(*p, F) for p in ((-88, -165, -42), (-84, -152, -31), (-72, -140, -30.5), (-52, -112, -29),
                                (-31, -80, -24), (-11, -40, -18), (4, -15, -13.5), (32, -11, -15), (62, -13, -19),
                                (86, -32, -29), (94, -70, -33), (96, -97, -33))]
           + [(*QI_LEAD_END, F)])

# assembled view: tubes for the routes no STL models (the controller leads, W1, the third head's lead and
# the Qi cord outside the panel are STLs from loose.scad)
UNDER_WIRES = [
    ("LED branch, driver (approximate)", "wire_black", 1.5, LED_D),
    ("LED branch, passenger (approximate)", "wire_black", 1.5, LED_P),
    ("Lead between the in-line connectors (approximate)", "wire_black", 1.5, JUMPER),
    ("Qi lead under the deck, red (approximate)", "wire_red", 0.8, offset_path(QI_LEAD, 0.85)),
    ("Qi lead under the deck, black (approximate)", "wire_black", 0.8, offset_path(QI_LEAD, -0.85)),
    ("Splice bundle, red (approximate)", "wire_red", 0.8, [(x + 0.9, y, z, a) for x, y, z, a in SPLICE]),
    ("Splice bundle, black (approximate)", "wire_black", 0.8, [(x - 0.9, y, z, a) for x, y, z, a in SPLICE]),
    ("Splice red branch to the 12 V centre (approximate)", "wire_red", 0.8, SPLICE_12V),
    ("W1 salmon tail to the USB socket (approximate)", "wire_salmon", 0.8, TAIL_SALMON),
    ("Salmon loop USB to the 12 V side tab (approximate)", "wire_salmon", 0.8, TAIL_SALMON_2),
    ("W1 blue tail to the 12 V socket, with its loop (approximate)", "wire_blue", 0.8, TAIL_BLUE),
    ("Splice bundle, second red (approximate)", "wire_red", 0.8,
     [(x, y, z + 0.9, a) for x, y, z, a in offset_path(SPLICE, 2.1)]),
    ("Splice bundle, third red (approximate)", "wire_red", 0.8,
     [(x, y, z - 0.5, a) for x, y, z, a in offset_path(SPLICE, -2.3)]),
    ("Splice bundle, second black (approximate)", "wire_black", 0.8,
     [(x, y, z - 1.0, a) for x, y, z, a in offset_path(SPLICE, 1.3)]),
    ("Loose red wire, cut end (approximate)", "wire_red", 0.8,
     [(5, 134, -14, F), (30, 148, -14, F), (55, 156, -14, F), (72, 153, -14, F), (78, 146, -14, F),
      (75, 140, -14, F)]),
    ("Cylinder B26 cable (approximate)", "wire_black", 1.0,
     [(-52.5, 66, -13.6, F), (-55, 58, -13.8, F), (-57, 50, -14.5, F)]),
    ("Button wire end 1 (approximate)", "wire_red", 0.8, BTN_W1),
    ("Button wire end 2, bare tip (approximate)", "wire_red", 0.8, BTN_W2),
]
EXPLODE_ONLY_WIRES = [
    ("Controller DC lead", "wire_black", 1.5, CTRL_DC),
    ("Controller output lead", "wire_black", 1.5, CTRL_OUT),
    ("Feed W1 (plug lead)", "wire_black", 2.5, [p for p in W1_OUTSIDE if p[3] != "qi_frame"] + W1_UNDER),
    ("Third head lead", "wire_black", 1.5, LEAD3),
    ("Qi cord red", "wire_red", 0.8, offset_path(QI_CORD, 0.85)),
    ("Qi cord black", "wire_black", 0.8, offset_path(QI_CORD, -0.85)),
]


def build_wires(wires, col, exploded):
    for name, key, rad, pts in wires:
        if exploded:
            P = [explode_pt(x, y, z, a) for x, y, z, a in pts]
            name = name + " (exploded)"
        else:
            P = [(x, y, z) for x, y, z, a in pts]
        tube(name, P, MAT[key], col, r=rad)


def build_hardware(col, exploded):
    """Clips, connectors, heat-shrink sleeves, the bare wire tip and cylinder B26 (all on the felt)."""
    def o(anchor=F):
        return xoff(anchor) if exploded else (0, 0, 0)
    sfx = " (exploded)" if exploded else ""
    pclip("P-clip, driver notch corner (W1 + third lead)" + sfx, (-96, -2, -14.5), (1, 1, 0), 2.6, (-1, 1, 0),
          col, o())
    # screw INBOARD of the cable (SEEN 3502/3504/3481, toward the notch)
    pclip("P-clip, Qi lead under the passenger arm" + sfx, (101, -56, -13.4), (0, 1, 0), 1.7, (-1, 0, 0), col, o())
    for y in (59, 97):
        pclip(f"Splice clip y {y}" + sfx, (5, y, -13.6), (0, 1, 0), 2.0, (1, 0, 0), col, o())
    pclip("Fibre P-clip, passenger" + sfx, (101, 182, -15), (0, 1, 0), 2.0, (-1, 0, 0), col,
          o("fibre_r") if exploded else (0, 0, 0))
    pclip("Fibre P-clip, driver" + sfx, (-90, 200, -15), (-0.25, 1, 0), 2.0, (1, 0, 0), col,
          o("fibre_l") if exploded else (0, 0, 0))
    connector("In-line connector 1" + sfx, (25, 32, -15.2), (1, 0.1, 0), col, o())
    connector("In-line connector 2" + sfx, (5, 41, -15.2), (-0.93, 0.37, 0), col, o())
    ox = np.array(o())
    for k, (y0, y1) in enumerate(SPLICE_SLEEVES):
        tube(f"Heat-shrink sleeve {k + 1}" + sfx, [tuple(np.array(q[:3]) + ox) for q in splice_sub(y0, y1)],
             MAT["heatshrink"], col, r=2.4)
    # clear nylon-insulated female spades on the socket tabs (SEEN 3502/3503/3481), approximate
    for k, (p_, anc) in enumerate(((USB_TAB[-1], "usb_body"), (USB_TAB[1], "usb_body"), (V12_TAB, "v12_body"),
                                   (V12_STUD, "v12_body"))):
        oa = np.array(o(anc))
        L_ = 12.0 if k < 3 else 8.0
        cyl(f"Spade sleeve {k + 1} (clear)" + sfx, np.array(p_) + oa + np.array([0, 0, 4.0]),
            np.array(p_) + oa - np.array([0, 0, L_ - 4.0]), 2.0, 1.8, mat=MAT["spade_clear"], col=col, n=20)
    cyl("Button wire bare tinned tip" + sfx, np.array((95.3, 42.6, -13.3)) + ox, np.array((93.6, 41.8, -13.3)) + ox,
        0.55, mat=MAT["tinned"], col=col, n=12)
    # cylinder B26 (unidentified, black, ~7.5 x 25, small side holes not modelled). Params put it at
    # (-66, 69), inside the pocket block's footprint, so it is set beside the block, passenger side of the bar's
    # front end. it stands off the felt, near-vertical, its cable entering the top (SEEN 3502/3503)
    cyl("Cylinder B26 (unidentified part)" + sfx, np.array((-52.5, 66, -13.0)) + ox, np.array((-52.5, 70, -38)) + ox,
        3.75, mat=MAT["plastic"], col=col, n=24)


build_wires(UNDER_WIRES, col_wires, False)
build_hardware(col_wires, False)
build_wires(UNDER_WIRES + EXPLODE_ONLY_WIRES, col_wires_x, True)
build_hardware(col_wires_x, True)


# exploded-view guide lines from each lifted / lowered part to its hole
def _ez(name, z):
    return z + xoff(name)[2]


GUIDES = [
    ("USB socket", USB_C[0], USB_C[1], _ez("usb", -4.0), _ez(F, -12.0)),
    ("USB body", USB_C[0], USB_C[1] + 13, _ez(F, -12.0), _ez("usb_body", -3.5)),
    ("12 V socket", V12_C[0], V12_C[1], _ez("v12", 2.0), _ez(F, -12.0)),
    ("12 V body", V12_C[0], V12_C[1] + 16, _ez(F, -12.0), _ez("v12_body", 2.0)),
    ("Cup", CUP_C[0], CUP_C[1], _ez("cup", -60.0), _ez(F, -12.0)),
    ("Controller", CTRL_C[0], CTRL_C[1], _ez(F, -12.0), _ez("ctrl", -60.0)),
    ("Clock", 0.0, 25.5, _ez("clock_body", -2.5), _ez("deck_vinyl", 0.0)),
    ("Button", 91.5, 33.0, _ez("button", -10.5), _ez("deck_vinyl", 0.0)),
    ("Slot to pocket", -71.0, 96.0, _ez("slot", -12.0), _ez("pocket", -11.8)),
]
for name, x, y, z0, z1 in GUIDES:
    tube(f"Guide: {name}", [(x, y, z0), (x, y, z1)], MAT["guide"], col_wires_x, r=0.4)

# table-state cables (table views): from the panel's exits down to the table and over to the pad, the plug
# and the third head in their table poses (layout read off IMG_3491; paths approximate)
QI_EXIT_TAB = apply_model(MM_QI, qi_xform_pt(QI_EXIT_LOCAL))
PLUG_EXIT_TAB = apply_model(MM_PLUG, PLUG_EXIT_END)
HEAD_BOOT_TAB = apply_model(MM_HEAD, tuple(head_rear("head_loose")[0] - head_rear("head_loose")[1] * HEAD_BOOT))


def on_table(x, y, r):
    return (x, y, TBL(y) + r)


# The Qi cord crosses the notch floor diagonally from the passenger lining to its connector (3491).

QI_CORD_TAB = ([QI_EXIT_TAB] + [on_table(x, y, 0.85) for x, y in ((-108, -268), (-112, -236), (-106, -206),
                                                                     (-52, -181), (18, -151), (78, -126))]
               + [(92, -117, -92), (96.5, -107, -48), QI_LEAD_END])
tube("Qi cord on the table, red (approximate)", offset_path(QI_CORD_TAB, 0.85), MAT["wire_red"], col_wires_t, r=0.8)
tube("Qi cord on the table, black (approximate)", offset_path(QI_CORD_TAB, -0.85), MAT["wire_black"], col_wires_t,
     r=0.8)
obox("Qi cord 2-pin connector (table)", on_table(-109, -210, 2.5), (7, 25, 5), rot_z(-8), MAT["plastic"],
     col_wires_t, bevel=1.0)
# Photographic reference (3491): both black cables drop from the driver back-corner clip INTO the notch and cross the
# notch floor toward the pad (photo anchors on the table, +-15: (-86,-81) (-43,-95) (-9,-113) loop (15,-105)
# (11,-120) (-20,-195) (-40,-255) at the pad's rear edge); W1 then runs round the pad's driver end to the plug,
# the third head's lead comes from the head at (-169,-398) past the pad's driver end (-113,-341). Nothing runs
# along the outside of the driver arm.
W1_TAB = ([PLUG_EXIT_TAB] + [on_table(x, y, 2.5) for x, y in ((-26, -398), (-72, -404), (-128, -372), (-124, -300),
                                                              (-90, -250), (-42, -246), (-20, -195), (12, -120),
                                                              (16, -106), (-10, -112), (-45, -95), (-80, -76))]
          + [(-89, -40, -95), (-93, -13, -45), WCLIP])
tube("Feed W1 on the table (approximate)", W1_TAB, MAT["wire_black"], col_wires_t, r=2.5)
LEAD3_TAB = ([HEAD_BOOT_TAB] + [on_table(x, y, 1.5) for x, y in ((-150, -372), (-124, -341), (-126, -298),
                                                                  (-92, -255), (-46, -242), (-25, -199),
                                                                  (8, -123), (11, -109), (-11, -116), (-46, -99),
                                                                  (-83, -79))]
             + [(-95, -47, -95), (-97, -17, -44), WCLIP])
tube("Third head lead on the table (approximate)", LEAD3_TAB, MAT["wire_black"], col_wires_t, r=1.5)

# IMG_3487 layout (approximate): W1 from the plug (behind the pad) toward the camera and right under the driver
# wall's front sweep into the notch; the Qi cord from the pad's near-right corner right with its connector
PLUG_EXIT_87 = apply_model(MM_PLUG_87, PLUG_EXIT_END)
QI_EXIT_87 = apply_model(MM_QI_87, qi_xform_pt(QI_EXIT_LOCAL))
W1_87 = ([PLUG_EXIT_87] + [on_table(x, y, 2.5) for x, y in ((40, -368), (18, -352), (28, -330), (48, -312),
                                                              (40, -262), (-10, -182), (-50, -120), (-80, -76))]
         + [(-90, -42, -95), (-94, -14, -45), WCLIP])
tube("Feed W1 on the table, 3487 layout (approximate)", W1_87, MAT["wire_black"], col_wires_t87, r=2.5)
QI_87 = ([QI_EXIT_87] + [on_table(x, y, 0.85) for x, y in ((-160, -312), (-118, -294), (-121, -258), (-105, -222),
                                                             (-84, -181), (-40, -150), (30, -138), (78, -126))]
         + [(92, -117, -92), (96.5, -107, -48), QI_LEAD_END])
tube("Qi cord on the table, red, 3487 layout (approximate)", offset_path(QI_87, 0.85), MAT["wire_red"], col_wires_t87,
     r=0.8)
tube("Qi cord on the table, black, 3487 layout (approximate)", offset_path(QI_87, -0.85), MAT["wire_black"],
     col_wires_t87, r=0.8)
obox("Qi cord 2-pin connector (table, 3487)", on_table(-114, -284, 2.5), (7, 25, 5), rot_z(-25), MAT["plastic"],
     col_wires_t87, bevel=1.0)
# Dark backing beneath the two steel-bar holes for the table views (3483/3497).

for yb in (96.0 - 26.0, 96.0 + 26.0):
    for col_ in (col_table,):
        cyl(f"Bar hole backing y {yb:.0f}", (-71.0, yb, -38.6), (-71.0, yb, -39.2), 3.2, mat=MAT["gap_black"],
            col=col_, n=24)

# Underside cables drape from the clip across the notch and out of frame (3502/3503).
# The third head’s ribbed inline connector sits about 40 mm beyond the clip.


tube("W1 tail (underside view)", [WCLIP, (-96, -26, -24), (-88, -70, -40), (-66, -130, -50), (-36, -205, -55),
                                  (-14, -300, -58)], MAT["wire_black"], col_wires_u, r=2.5)
tube("Third head lead tail (underside view)", [WCLIP, (-90, -24, -22), (-82, -62, -34), (-58, -122, -44),
                                               (-26, -192, -50), (0, -290, -54)],
     MAT["wire_black"], col_wires_u, r=1.5)
connector("Third head lead in-line connector (underside view)", (-85.5, -45, -29), (0.18, -1, -0.3), col_wires_u)
tube("Qi cord tail red (underside view)", offset_path([QI_LEAD_END, (95, -125, -34), (90, -160, -45),
                                                       (84, -192, -50)], 0.85), MAT["wire_red"], col_wires_u, r=0.8)
tube("Qi cord tail black (underside view)", offset_path([QI_LEAD_END, (95, -125, -34), (90, -160, -45),
                                                         (84, -192, -50)], -0.85), MAT["wire_black"], col_wires_u,
     r=0.8)


# --------------------------------------------------------------------------------------------
# 9. View switching
# --------------------------------------------------------------------------------------------
def set_parts(view):
    hide = set()
    if view in ("table", "table87", "under", "explode"):
        hide |= set(OUTSIDE_LEADS)
    if view in ("car", "top", "explode"):
        hide |= set(INSIDE_LEADS)
    if view == "under":
        hide |= set(LOOSE_ITEMS)
    if view == "explode":
        hide |= {"ctrl_leads"}
    if view == "table87":                  # the third head is not on the open table in IMG_3487
        hide |= {"head_loose", "head_boot_loose"}
    # the notch lining hangs differently in the car (notch_skirt_car) and free on the table (notch_skirt)
    hide |= {"notch_skirt"} if view in ("car", "top") else {"notch_skirt_car"}
    for n, o in parts.items():
        o.hide_render = n in hide
        o.hide_viewport = n in hide


def set_collections(view):
    vis = {
        col_context: view in ("car", "top"),
        col_table: view in ("table", "table87"),
        col_wires: view in ("car", "top", "table", "table87", "under"),
        col_wires_x: view == "explode",
        col_wires_t: view == "table",
        col_wires_t87: view == "table87",
        col_wires_u: view == "under",
    }
    for c, v in vis.items():
        c.hide_render = not v
        c.hide_viewport = not v
    for o in col_context.objects:          # armrest hidden in the straight-down view (it covers the rear)
        if o.get("ctx_group") == "armrest":
            o.hide_render = view == "top"
            o.hide_viewport = view == "top"


def set_lights(which):
    for key, o in LIGHTS.items():
        o.hide_render = key not in LIGHT_SETS[which]
        o.hide_viewport = key not in LIGHT_SETS[which]


def set_world(kind):
    mixc.inputs["B"].default_value = WORLD[kind][0]
    gain_mix.inputs["B"].default_value = WORLD[kind][1]


def set_view(view):
    set_pose(view)
    set_parts(view)
    set_collections(view)
    set_lights({"car": "car", "top": "top", "under": "under", "table": "table", "table87": "table",
                "explode": "explode"}[view])
    set_world({"car": "car", "top": "car", "under": "studio", "table": "table", "table87": "table",
               "explode": "studio"}[view])


# --------------------------------------------------------------------------------------------
# 10. Renders
# --------------------------------------------------------------------------------------------
os.makedirs(RENDER_DIR, exist_ok=True)


# Per-render exposure offsets keep the dial and button below clipping.
# GLOW_COMP scales emission and bloom threshold by 2^|EV| to retain the lit fibre colours.
# CONSOLE_EVOFF="hero.png:-0.9,fibres_green.png:-0.9" overrides individual offsets.











EXPOSURE_OFFSET = {"top.png": -0.7, "hero.png": -1.0, "fibres_green.png": -1.0}
GLOW_COMP = {"hero.png", "fibres_green.png"}
for _kv in filter(None, os.environ.get("CONSOLE_EVOFF", "").split(",")):
    EXPOSURE_OFFSET[_kv.split(":")[0]] = float(_kv.split(":")[1])
GLARE_THRESHOLD = glare.inputs["Threshold"].default_value


def set_usb(powered, gain=1.0):
    """Powered views (LEDs on): the USB cap is flipped open (usb_cap_open.stl, as in IMG_3439) and the blue ring and
    labels glow. Views matched to the 3 Oct photos (LEDs off): cap closed and ring dark, as photographed."""
    for name, show in (("usb_cap_open", powered), ("usb_cap", not powered)):
        if name in parts:
            parts[name].hide_render = not show
            parts[name].hide_viewport = not show
    principled(MAT["usb_blue"]).inputs["Emission Strength"].default_value = USB_GLOW * gain if powered else 0.0


def render(fname, cam, frame, view, caption, leds=True):
    scene.camera = cam
    scene.frame_set(frame)
    set_view(view)
    ev = EXPOSURE_OFFSET.get(fname, 0.0)
    gain = 2.0 ** (-ev) if (leds and fname in GLOW_COMP and ev < 0) else 1.0
    set_leds(leds, gain)
    set_usb(leds, gain)
    glare.inputs["Threshold"].default_value = GLARE_THRESHOLD * gain     # same bloom on the LEDs, less on the chrome
    scene.view_settings.exposure += ev
    r.stamp_note_text = f"{PROJECT} | {CAPTION} | {caption}" if STAMP else ""
    r.filepath = os.path.join(RENDER_DIR, fname)
    bpy.ops.render.render(write_still=True)
    print(f"[assemble] wrote {r.filepath}")


ONLY = os.environ.get("CONSOLE_ONLY", "")   # e.g. CONSOLE_ONLY=hero,top to iterate quickly
JOBS = [
    # file, camera, frame, view, caption, LEDs on
    ("hero.png", CAM_HERO, 1, "car", "fitted in the car (car context low detail)", True),
    ("in_car_3483.png", CAM_3483, 1, "car",
     "camera of IMG_3483 (photo = centre strip), LEDs off", False),
    ("top.png", CAM_TOP, 1, "top", "fitted, straight down, front to the left (armrest hidden)", True),
    ("table_top_3491.png", CAM_3491, 1, "table", "table, camera of IMG_3491, LEDs off (as photographed)", False),
    ("table_side_3487.png", CAM_3487, 1, "table87", "table, camera of IMG_3487, LEDs off (as photographed)", False),
    ("underside.png", CAM_UNDER, 1, "under", "underside, front left, driver side top, LEDs off (as 3502)",
     False),
    ("exploded.png", CAM_EXPL, 1, "explode", "exploded; wiring paths approximate", True),
    ("fibres_green.png", CAM_HERO, GREEN_FRAME, "car", f"fibre colour cycle, frame {GREEN_FRAME}", True),
]
for fname, cam, frame, view, caption, leds in JOBS:
    if ONLY and fname.split(".")[0] not in ONLY.split(","):
        continue
    render(fname, cam, frame, view, caption, leds)

# --------------------------------------------------------------------------------------------
# 11. Save the assembled scene (frame 1, fitted, context visible, hero camera)
# --------------------------------------------------------------------------------------------
set_view("car")
_ev = EXPOSURE_OFFSET.get("hero.png", 0.0)        # same exposure / glow balance as hero.png
_gain = 2.0 ** (-_ev) if ("hero.png" in GLOW_COMP and _ev < 0) else 1.0
set_leds(True, _gain)
set_usb(True, _gain)
glare.inputs["Threshold"].default_value = GLARE_THRESHOLD * _gain
scene.view_settings.exposure += _ev
scene.camera = CAM_HERO
scene.frame_set(1)
r.stamp_note_text = f"{PROJECT} | {CAPTION}" if STAMP else ""
if not os.environ.get("CONSOLE_NOSAVE"):
    bpy.context.preferences.filepaths.save_version = 0     # no console.blend1 backup
    r.filepath = "//../renders/"
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"[assemble] saved {BLEND_PATH}")
