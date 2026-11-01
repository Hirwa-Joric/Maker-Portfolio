#!/usr/bin/env python3
"""
Generator for console_improved.kicad_sch

Custom Aftermarket Car Center Console Upgrade
PROPOSED PROTECTION REVISION (not installed or validated),
MODEL-SPEC.md section 5.2.

Writes, next to this script:
  console_improved.kicad_sch   the schematic (KiCad 10 format)
  console_improved.kicad_pro   minimal project file
  console_custom.kicad_sym     the custom symbols used (car outlet, plug, sockets, ...)
  sym-lib-table                project symbol-library table (merged, never clobbered)

Standard symbols (Device:Fuse, Switch:SW_Push, power:+12V/GND/PWR_FLAG) are copied
verbatim from the KiCad 10 library files so the schematic is self-contained.

Run:  python3 gen_console_improved.py
Then: kicad-cli sch erc console_improved.kicad_sch
"""

import json
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "console_improved"
CUSTOM_LIB = "console_custom"
KICAD_SYM_DIR = os.environ.get("KICAD10_SYMBOL_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
if not os.path.isdir(KICAD_SYM_DIR):
    raise SystemExit("Set KICAD10_SYMBOL_DIR to the symbols directory of your KiCad 10 installation.")

PROJECT_NAME = "Custom Aftermarket Car Center Console Upgrade"
VARIANT = "improved redesign (not what was originally built)"
DATE = "2026-10-03"

# deterministic UUIDs so regenerating gives a stable file
_NS = uuid.UUID("6f1c2a52-0d7e-4c55-9a59-2e4d3f0c9a11")
_ucount = [0]


def uid(tag=""):
    _ucount[0] += 1
    return str(uuid.uuid5(_NS, f"{BASE}:{_ucount[0]}:{tag}"))


ROOT_UUID = str(uuid.uuid5(_NS, BASE + ":root"))


def q(s):
    """Quote a string for a KiCad S-expression."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def f(v):
    """Format a coordinate (mm) without float noise."""
    v = round(v, 4)
    if abs(v) < 1e-9:
        v = 0.0
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def font(size=1.27, bold=False, italic=False, color=None):
    s = f"(font (size {f(size)} {f(size)})"
    if bold:
        s += " (thickness %s) (bold yes)" % f(size * 0.18)
    if italic:
        s += " (italic yes)"
    if color:
        s += " (color %d %d %d %s)" % (color[0], color[1], color[2], f(color[3] if len(color) > 3 else 1))
    return s + ")"


def effects(size=1.27, justify=None, hide=False, bold=False, italic=False, color=None):
    s = "(effects " + font(size, bold, italic, color)
    if justify:
        s += f" (justify {justify})"
    if hide:
        s += " (hide yes)"
    return s + ")"


# --------------------------------------------------------------------------
# library symbol helpers (coordinates in symbol space, y up)
# --------------------------------------------------------------------------

def _col(c):
    return f" (color {c[0]} {c[1]} {c[2]} {f(c[3])})" if c else ""


def g_rect(x1, y1, x2, y2, w=0.254, fill="background", stype="default", sc=None, fc=None):
    """sc = stroke colour, fc = fill colour (use with fill="color"); None = KiCad default."""
    return (f"(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) "
            f"(stroke (width {f(w)}) (type {stype}){_col(sc)}) (fill (type {fill}){_col(fc)}))")


def g_poly(pts, w=0.254, fill="none", stype="default", sc=None):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return f"(polyline (pts {p}) (stroke (width {f(w)}) (type {stype}){_col(sc)}) (fill (type {fill})))"


def g_circle(cx, cy, r, w=0.254, fill="none"):
    return (f"(circle (center {f(cx)} {f(cy)}) (radius {f(r)}) "
            f"(stroke (width {f(w)}) (type default)) (fill (type {fill})))")


def g_text(s, x, y, size=1.27, bold=False, justify=None):
    return f"(text {q(s)} (at {f(x)} {f(y)} 0) {effects(size, justify, bold=bold)})"


def g_pin(x, y, angle, length, name, number, etype="passive"):
    return (f"(pin {etype} line (at {f(x)} {f(y)} {angle}) (length {f(length)}) "
            f"(name {q(name)} {effects(1.27)}) (number {q(number)} {effects(1.27)}))")


def lib_prop(name, value, x=0, y=0, hide=False, size=1.27):
    h = " (hide yes)" if hide else ""
    return (f"(property {q(name)} {q(value)} (at {f(x)} {f(y)} 0) (show_name no) "
            f"(do_not_autoplace no){h} {effects(size)})")


def lib_symbol(name, ref, value, desc, units, common=None, pin_names_hide=False,
               pin_numbers_hide=True, pin_name_offset=1.016, jumpers=False,
               in_bom=True, on_board=True, keywords=""):
    """Return the symbol body (without library prefix)."""
    # Give each drawn terminal a unique ID; labels connect terminals within the component.
    if jumpers:
        seen, mapping, rewritten = {}, {}, {}
        for unit, items in units.items():
            rewritten[unit] = []
            pin_index = 0
            for item in items:
                match = re.search(r'\(number "([^"\n]+)"', item)
                if match:
                    old = match.group(1)
                    seen[old] = seen.get(old, 0) + 1
                    new = old if seen[old] == 1 else f"{old}_{seen[old]}"
                    mapping[(unit, pin_index)] = (old, new)
                    pin_index += 1
                    item = item[:match.start(1)] + new + item[match.end(1):]
                rewritten[unit].append(item)
        PIN_MAP[name] = mapping
        units, jumpers = rewritten, False
    out = [f"(symbol {q(name)}"]
    if pin_numbers_hide:
        out.append("(pin_numbers (hide yes))")
    pn = f"(pin_names (offset {f(pin_name_offset)})"
    if pin_names_hide:
        pn += " (hide yes)"
    out.append(pn + ")")
    out.append("(exclude_from_sim no)")
    out.append(f"(in_bom {'yes' if in_bom else 'no'})")
    out.append(f"(on_board {'yes' if on_board else 'no'})")
    out.append("(in_pos_files yes)")
    out.append(f"(duplicate_pin_numbers_are_jumpers {'yes' if jumpers else 'no'})")
    out.append(lib_prop("Reference", ref, 0, 0))
    out.append(lib_prop("Value", value, 0, 0))
    out.append(lib_prop("Footprint", "", hide=True))
    out.append(lib_prop("Datasheet", "", hide=True))
    out.append(lib_prop("Description", desc, hide=True))
    if keywords:
        out.append(lib_prop("ki_keywords", keywords, hide=True))
    if common:
        out.append(f"(symbol {q(name + '_0_1')} " + " ".join(common) + ")")
    for unit, items in units.items():
        out.append(f"(symbol {q(f'{name}_{unit}_1')} " + " ".join(items) + ")")
    out.append("(embedded_fonts no)")
    out.append(")")
    return "\n\t\t".join(out)


# --------------------------------------------------------------------------
# custom symbols
# --------------------------------------------------------------------------
PIN_MAP = {}    # symbol -> terminal identities, preserving the internal conductor group
CUSTOM = {}      # name -> body text
PINS = {}        # name -> {unit: [(number, x, y)]}  (pin end points, symbol space)


def add_custom(name, body, pins):
    CUSTOM[name] = body
    PINS[name] = pins


# 1) Car 12 V accessory outlet (part of the car, not of the build)
add_custom("CAR_12V_OUTLET", lib_symbol(
    "CAR_12V_OUTLET", "CAR", "Car 12 V outlet",
    "The car's own 12 V accessory outlet (lower centre stack). Switched with the car, "
    "protected by the car's own fuse. Not part of the build.",
    {1: [g_pin(7.62, 0, 180, 2.54, "+", "1"), g_pin(7.62, -5.08, 180, 2.54, "-", "2")]},
    common=[g_rect(-12.7, 5.08, 5.08, -10.16),
            g_circle(-4.445, -2.54, 3.81, 0.254, "none"),
            g_circle(-4.445, -2.54, 2.794, 0.1524, "none"),
            g_circle(-4.445, -2.54, 0.762, 0.1524, "outline")],
    in_bom=False, on_board=False), {1: [("1", 7.62, 0), ("2", 7.62, -5.08)]})

# 2) Fused cigarette plug P1 (fuse in the tip; minus contacts pass straight through)
add_custom("FUSED_CIG_PLUG", lib_symbol(
    "FUSED_CIG_PLUG", "P", "Fused 12 V plug",
    "Cigarette-lighter plug with the main fuse in its tip. Tip = +, side springs = -.",
    {1: [g_pin(-10.16, 0, 0, 2.54, "TIP", "1"), g_pin(10.16, 0, 180, 2.54, "+", "2"),
         g_pin(-10.16, -5.08, 0, 2.54, "-", "3"), g_pin(10.16, -5.08, 180, 2.54, "-", "3")]},
    common=[g_rect(-7.62, 3.81, 7.62, -8.89),
            g_poly([(-7.62, 0), (-3.175, 0)], 0.1524),
            g_rect(-3.175, 0.889, 3.175, -0.889, 0.254, "none"),
            g_poly([(-3.175, 0), (3.175, 0)], 0.1524),
            g_poly([(3.175, 0), (7.62, 0)], 0.1524),
            g_poly([(-7.62, -5.08), (7.62, -5.08)], 0.1524),
            g_text("fuse in tip", 0, 2.413, 1.4),
            g_text("tip +", -3.302, -2.413, 1.4), g_text("side -", -2.54, -7.112, 1.4)],
    pin_names_hide=True, jumpers=True),
    {1: [("1", -10.16, 0), ("2", 10.16, 0), ("3", -10.16, -5.08), ("3", 10.16, -5.08)]})

# 3) 2-pin in-line car connector (J1), both contacts pass through
add_custom("CONN_2P_INLINE", lib_symbol(
    "CONN_2P_INLINE", "J", "2-pin car connector",
    "Two-pin in-line car connector (plug + socket), contacts pass straight through.",
    {1: [g_pin(-6.35, 0, 0, 2.54, "+", "1"), g_pin(6.35, 0, 180, 2.54, "+", "1"),
         g_pin(-6.35, -5.08, 0, 2.54, "-", "2"), g_pin(6.35, -5.08, 180, 2.54, "-", "2")]},
    common=[g_rect(-3.81, 2.54, 3.81, -7.62),
            g_poly([(0, 2.54), (0, -7.62)], 0.1524, stype="dash"),
            g_poly([(-3.81, 0), (-0.635, 0)], 0.1524), g_poly([(0.635, 0), (3.81, 0)], 0.1524),
            g_poly([(-3.81, -5.08), (-0.635, -5.08)], 0.1524), g_poly([(0.635, -5.08), (3.81, -5.08)], 0.1524),
            g_text("+", -1.905, 1.27, 1.4), g_text("-", -1.905, -3.81, 1.4)],
    pin_names_hide=True, jumpers=True),
    {1: [("1", -6.35, 0), ("1", 6.35, 0), ("2", -6.35, -5.08), ("2", 6.35, -5.08)]})


def load_box(name, ref, value, desc, inner, top_txt, bot_txt):
    """Vertical two-pin load: + on top, - at the bottom."""
    body = [g_rect(-8.89, 6.35, 8.89, -6.35)] + inner + [
        g_text(top_txt, 0, 5.08, 1.4), g_text(bot_txt, 0, -5.08, 1.4)]
    add_custom(name, lib_symbol(
        name, ref, value, desc,
        {1: [g_pin(0, 8.89, 270, 2.54, "+", "1"), g_pin(0, -8.89, 90, 2.54, "-", "2")]},
        common=body, pin_names_hide=True),
        {1: [("1", 0, 8.89), ("2", 0, -8.89)]})


# 4) 12 V socket X2
load_box("SOCKET_12V", "X", "12 V socket",
         "Panel 12 V accessory (cigarette-lighter type) socket. Centre = +, shell = -.",
         [g_circle(0, 0, 3.302, 0.254), g_circle(0, 0, 2.286, 0.1524), g_circle(0, 0, 0.762, 0.1524, "outline")],
         "+ centre stud", "- shell")

# 5) Dual USB PD/QC socket X1
load_box("USB_PD_QC_SOCKET", "X", "Dual USB socket",
         "Round 12/24 V panel socket with USB-C PD and USB-A QC3.0 outputs and a blue LED ring.",
         [g_circle(0, 0, 3.302, 0.254),
          g_rect(-2.413, 0.508, -0.508, -0.508, 0.1524, "none"),
          g_rect(0.508, 0.762, 2.667, -0.762, 0.1524, "none"),
          g_text("C", -4.826, 0, 1.4), g_text("A", 4.826, 0, 1.4)],
         "+12V", "GND")

# 6) Qi charger pad U2
load_box("QI_CHARGER_PAD", "U", "Qi charger pad",
         "wireless (Qi) charging pad around a bought Qi module. Input must accept 12-14.6 V.",
         [g_circle(0, 0, 1.016, 0.1524), g_circle(0, 0, 2.032, 0.1524), g_circle(0, 0, 3.048, 0.1524)],
         "+12V in", "GND")

# 7) single in-line contact, two units (J2: pin 1 = +, pin 2 = -)
_contact_units = {}
_contact_pins = {}
for _u, _num, _sign in ((1, "1", "+"), (2, "2", "-")):
    _contact_units[_u] = [
        g_rect(-1.905, 2.54, 1.905, -2.54),
        g_poly([(-1.905, 0), (1.905, 0)], 0.1524, stype="dash"),
        g_poly([(0, 2.54), (0, 0.635)], 0.1524), g_poly([(0, -0.635), (0, -2.54)], 0.1524),
        g_pin(0, 5.08, 270, 2.54, _sign, _num), g_pin(0, -5.08, 90, 2.54, _sign, _num)]
    _contact_pins[_u] = [(_num, 0, 5.08), (_num, 0, -5.08)]
add_custom("CONN_2P_PLUG_SPLIT", lib_symbol(
    "CONN_2P_PLUG_SPLIT", "J", "2-pin plug",
    "Two-pin plug and socket, drawn one contact per unit (A = pin 1 +, B = pin 2 -).",
    _contact_units, pin_names_hide=True, jumpers=True), _contact_pins)

# 8) Bluetooth RGB controller U1
add_custom("BT_RGB_CONTROLLER", lib_symbol(
    "BT_RGB_CONTROLLER", "U", "Bluetooth RGB controller",
    "Bluetooth RGB LED controller, phone-app control, common-anode output (V+, R, G, B).",
    {1: [g_pin(-17.78, 2.54, 0, 2.54, "DC+", "1"), g_pin(-17.78, -2.54, 0, 2.54, "DC-", "2"),
         g_pin(17.78, 3.81, 180, 2.54, "V+", "3"), g_pin(17.78, 1.27, 180, 2.54, "R", "4"),
         g_pin(17.78, -1.27, 180, 2.54, "G", "5"), g_pin(17.78, -3.81, 180, 2.54, "B", "6")]},
    common=[g_rect(-15.24, 7.62, 15.24, -7.62),
            g_text("Bluetooth", -1.27, 3.302, 1.27, bold=True),
            g_text("RGB LED", -1.27, 1.016, 1.27, bold=True),
            g_text("controller", -1.27, -1.27, 1.27, bold=True),
            g_text("(phone app)", -1.27, -4.064, 1.4)]),
    {1: [("1", -17.78, 2.54), ("2", -17.78, -2.54), ("3", 17.78, 3.81), ("4", 17.78, 1.27),
         ("5", 17.78, -1.27), ("6", 17.78, -3.81)]})

# 9) 1-to-3 RGB splitter J3 (all same-name lines joined inside)
_sp_pins = []
_sp_items = []
for _i, _n in enumerate(("V+", "R", "G", "B")):
    _y = 3.81 - 2.54 * _i
    _sp_items.append(g_pin(-8.89, _y, 0, 2.54, _n, str(_i + 1)))
    _sp_pins.append((str(_i + 1), -8.89, _y))
    for _g in (17.78, 0, -17.78):
        _sp_items.append(g_pin(8.89, _y + _g, 180, 2.54, _n, str(_i + 1)))
        _sp_pins.append((str(_i + 1), 8.89, _y + _g))
add_custom("RGB_SPLITTER_1TO3", lib_symbol(
    "RGB_SPLITTER_1TO3", "J", "1-to-3 RGB splitter",
    "Passive 1-to-3 splitter for 4-wire common-anode RGB cables (V+, R, G, B), multi-pin in-line plugs.",
    {1: _sp_items},
    common=[g_rect(-6.35, 24.13, 6.35, -24.13),
            ],
    jumpers=True), {1: _sp_pins})

# 10) RGB LED head (aluminium) H1-H3
_led = [g_poly([(0.635, 1.905), (0.635, -1.905), (3.81, 0), (0.635, 1.905)], 0.254, "outline"),
        g_poly([(3.81, 1.905), (3.81, -1.905)], 0.254),
        g_poly([(4.445, 1.27), (5.715, 2.54)], 0.1524), g_poly([(5.715, 2.54), (4.953, 2.413)], 0.1524),
        g_poly([(5.715, 2.54), (5.588, 1.778)], 0.1524),
        g_poly([(4.445, 0.0), (5.715, 1.27)], 0.1524), g_poly([(5.715, 1.27), (4.953, 1.143)], 0.1524),
        g_poly([(5.715, 1.27), (5.588, 0.508)], 0.1524),
        # light out (optical, dashed arrow)
        g_poly([(7.62, 0), (11.43, 0)], 0.254, stype="dash"),
        g_poly([(10.414, 0.762), (11.43, 0), (10.414, -0.762)], 0.254)]
add_custom("RGB_LED_HEAD", lib_symbol(
    "RGB_LED_HEAD", "H", "RGB LED head",
    "Aluminium RGB LED head (common anode), about 12.5 mm x 35 mm, 4-wire cable.",
    {1: [g_pin(-7.62, 3.81 - 2.54 * i, 0, 2.54, n, str(i + 1)) for i, n in enumerate(("V+", "R", "G", "B"))]},
    common=[g_rect(-5.08, 5.08, 7.62, -5.08)] + _led),
    {1: [(str(i + 1), -7.62, 3.81 - 2.54 * i) for i in range(4)]})

# 11) Side-glow fibre (optical only, no electrical pins)
FIBRE = (190, 160, 255, 1)       # side-glow fibre (same light purple as the as-built sheet)
FIBRE_DK = (130, 100, 210, 1)
_fib = [g_poly([(0, 0), (38.1, 0)], 0.9, sc=FIBRE),
        g_poly([(0, -0.889), (38.1, -0.889)], 0.1524, sc=FIBRE_DK)]
for _k in range(10):
    _x = 1.905 + 3.81 * _k
    _fib.append(g_poly([(_x, 0.762), (_x + 0.889, 2.032)], 0.1524, stype="default", sc=FIBRE_DK))
add_custom("SIDE_GLOW_FIBRE", lib_symbol(
    "SIDE_GLOW_FIBRE", "FO", "Side-glow fibre",
    "Side-glow plastic optical fibre with fin, about 4 mm core. Optical only: no electrical connection.",
    {1: _fib}), {1: []})

# 12) Earth bus bar TB1 (all pins joined) - pin x offsets set to meet each return wire
TB_TOP = [0, 17.78, 60.96, 104.14, 147.32]   # J1-, X2-, X1-, J2B-, U1-
TB_BOT = [7.62, 25.4]                         # GND symbol, PWR_FLAG
TB_H = 3.81                                   # bar height (black, white "EARTH (-)" text on it)
_tb_items = [g_pin(x, 2.54, 270, 2.54, "GND", "1") for x in TB_TOP] + \
            [g_pin(x, -TB_H - 2.54, 90, 2.54, "GND", "1") for x in TB_BOT]
add_custom("EARTH_BUS_BAR", lib_symbol(
    "EARTH_BUS_BAR", "TB", "Earth bus bar",
    "Earth (negative) bus bar or lever connector on the panel underside: the panel's J- point.",
    {1: _tb_items},
    common=[g_rect(-5.08, 0, 152.4, -TB_H, 0.254, "color", sc=(0, 0, 0, 1), fc=(0, 0, 0, 1))],
    pin_names_hide=True, jumpers=True),
    {1: [("1", x, 2.54) for x in TB_TOP] + [("1", x, -TB_H - 2.54) for x in TB_BOT]})


# --------------------------------------------------------------------------
# standard library symbols (copied verbatim)
# --------------------------------------------------------------------------

def extract_lib_symbol(lib, name):
    path = os.path.join(KICAD_SYM_DIR, lib + ".kicad_sym")
    s = open(path, encoding="utf-8").read()
    key = f'\n\t(symbol "{name}"\n'
    i = s.find(key)
    if i < 0:
        raise SystemExit(f"symbol {lib}:{name} not found in {path}")
    j = i + 2
    depth, k = 0, j
    while True:
        c = s[k]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        elif c == '"':
            k += 1
            while s[k] != '"':
                if s[k] == "\\":
                    k += 1
                k += 1
        k += 1
    body = s[j:k + 1]
    if "(extends" in body:
        raise SystemExit(f"{lib}:{name} is a derived symbol; not supported")
    return body.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)


STD = [("Device", "Fuse"), ("Switch", "SW_Push"), ("power", "+12V"), ("power", "GND"), ("power", "PWR_FLAG")]
STD_PINS = {
    "Device:Fuse": {1: [("1", 0, 3.81), ("2", 0, -3.81)]},
    "Switch:SW_Push": {1: [("1", -5.08, 0), ("2", 5.08, 0)]},
    "power:+12V": {1: [("1", 0, 0)]},
    "power:GND": {1: [("1", 0, 0)]},
    "power:PWR_FLAG": {1: [("1", 0, 0)]},
}


# --------------------------------------------------------------------------
# schematic items
# --------------------------------------------------------------------------
ITEMS = []            # top-level schematic items, in order
PLACED = {}           # ref -> dict(lib_id, x, y, angle)


def xform(px, py, x, y, angle, mirror=None):
    """Symbol-space point -> sheet point (KiCad: symbol y up, sheet y down, CCW rotation)."""
    if mirror == "y":
        px = -px
    elif mirror == "x":
        py = -py
    sx, sy = px, -py
    for _ in range((angle // 90) % 4):
        sx, sy = sy, -sx          # rotate 90 deg CCW as seen on screen (y down)
    return round(x + sx, 4), round(y + sy, 4)


def pin_xy(ref, number, which=0, unit=None):
    p = PLACED[ref if unit is None else f"{ref}#{unit}"]
    pins = (STD_PINS.get(p["lib_id"]) or PINS[p["lib_id"].split(":", 1)[1]])[p["unit"]]
    hits = [(px, py) for n, px, py in pins if n == number]
    px, py = hits[which]
    return xform(px, py, p["x"], p["y"], p["angle"], p.get("mirror"))


def inst_prop(name, value, x, y, hide=False, size=1.27, justify=None, angle=0, bold=False):
    h = " (hide yes)" if hide else ""
    return (f"(property {q(name)} {q(value)} (at {f(x)} {f(y)} {angle}){h} (show_name no) "
            f"(do_not_autoplace no) {effects(size, justify, bold=bold)})")


def place(lib_id, ref, value, x, y, angle=0, unit=1, ref_at=None, val_at=None, desc="",
          hide_ref=False, hide_val=False, in_bom=True, on_board=True, mirror=None,
          ref_size=1.27, val_size=1.27, unit_count_key=None, field_angle=0):
    key = ref if unit_count_key is None else f"{ref}#{unit}"
    sym_uuid = uid(ref)
    PLACED[key] = dict(lib_id=lib_id, x=x, y=y, angle=angle, unit=unit, mirror=mirror, uuid=sym_uuid)
    rx, ry, rj = ref_at if ref_at else (x, y - 5, None)
    vx, vy, vj = val_at if val_at else (x, y + 5, None)
    if lib_id in STD_PINS:
        numbers = sorted({n for n, _, _ in STD_PINS[lib_id][unit]})
    else:
        numbers = sorted({n for n, _, _ in PINS[lib_id.split(":", 1)[1]][unit]})
    name = lib_id.split(":", 1)[1]
    if name in PIN_MAP:
        numbers = [new for (u, _), (_, new) in PIN_MAP[name].items() if u == unit]
    m = f" (mirror {mirror})" if mirror else ""
    lines = [
        "(symbol",
        f"(lib_id {q(lib_id)})",
        f"(at {f(x)} {f(y)} {angle}){m}",
        f"(unit {unit})",
        "(body_style 1)",
        "(exclude_from_sim no)",
        f"(in_bom {'yes' if in_bom else 'no'})",
        f"(on_board {'yes' if on_board else 'no'})",
        "(in_pos_files yes)",
        "(dnp no)",
        f"(uuid {q(sym_uuid)})",
        inst_prop("Reference", ref, rx, ry, hide_ref, ref_size, rj, angle=field_angle,
                  bold=not ref.startswith("#")),
        inst_prop("Value", value, vx, vy, hide_val, val_size, vj, angle=field_angle),
        inst_prop("Footprint", "", x, y, True),
        inst_prop("Datasheet", "", x, y, True),
        inst_prop("Description", desc, x, y, True),
    ]
    for n in numbers:
        lines.append(f"(pin {q(n)} (uuid {q(uid(ref + n))}))")
    lines.append(f"(instances (project {q(BASE)} (path {q('/' + ROOT_UUID)} "
                 f"(reference {q(ref)}) (unit {unit}))))")
    lines.append(")")
    ITEMS.append("\n\t\t".join(lines))
    if name in PIN_MAP:
        counts = {}
        for old, _ in PIN_MAP[name].values():
            counts[old] = counts.get(old, 0) + 1
        for index, (old, px, py) in enumerate(PINS[name][unit]):
            if counts[old] < 2:
                continue
            lx, ly = xform(px, py, x, y, angle, mirror)
            net = {("P1", "3"): "GND", ("J1", "1"): "+12V",
                   ("J1", "2"): "GND", ("J2", "2"): "GND",
                   ("TB1", "1"): "GND"}.get((ref, old), f"{ref}_internal_{old}")
            ITEMS.append(f"(label {q(net)} (at {f(lx)} {f(ly)} 0) "
                         f"{effects(0.7, 'left bottom', hide=True)} (uuid {q(uid('internal-net'))}))")


RED = (200, 0, 0, 1)
BLACK = (0, 0, 0, 1)
LEDC = (90, 70, 150, 1)     # LED cable (4-core), inner colours not seen
GREY = (110, 110, 110, 1)


def wire(pts, color=None, width=0.0):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        col = f" (color {color[0]} {color[1]} {color[2]} {f(color[3])})" if color else ""
        ITEMS.append(f"(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) "
                     f"(stroke (width {f(width)}) (type solid){col}) (uuid {q(uid('w'))}))")


def junction(x, y, color=(0, 0, 0, 0)):
    ITEMS.append(f"(junction (at {f(x)} {f(y)}) (diameter 0) (color {color[0]} {color[1]} {color[2]} {f(color[3])}) "
                 f"(uuid {q(uid('j'))}))")


def label(name, x, y, angle=0, size=1.27):
    just = "left bottom" if angle in (0, 90) else "right bottom"
    ITEMS.append(f"(label {q(name)} (at {f(x)} {f(y)} {angle}) {effects(size, just)} (uuid {q(uid('l'))}))")


def text(s, x, y, size=1.524, justify="left bottom", bold=False, italic=False, color=None, angle=0):
    ITEMS.append(f"(text {q(s)} (exclude_from_sim no) (at {f(x)} {f(y)} {angle}) "
                 f"{effects(size, justify, bold=bold, italic=italic, color=color)} (uuid {q(uid('t'))}))")


def text_box(s, x, y, w, h, size=1.524, fill=(255, 255, 230, 1), border=0.2, border_type="solid",
             border_color=None, bold=False):
    fc = f"(fill (type color) (color {fill[0]} {fill[1]} {fill[2]} {f(fill[3])}))" if fill else "(fill (type none))"
    bc = f" (color {border_color[0]} {border_color[1]} {border_color[2]} {f(border_color[3])})" if border_color else ""
    ITEMS.append(f"(text_box {q(s)} (exclude_from_sim no) (at {f(x)} {f(y)} 0) (size {f(w)} {f(h)}) "
                 f"(margins 1.5 1.5 1.5 1.5) (stroke (width {f(border)}) (type {border_type}){bc}) {fc} "
                 f"{effects(size, 'left top', bold=bold)} (uuid {q(uid('tb'))}))")


def rect(x1, y1, x2, y2, stype="dash", width=0.2, color=GREY):
    ITEMS.append(f"(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) "
                 f"(stroke (width {f(width)}) (type {stype}) (color {color[0]} {color[1]} {color[2]} {f(color[3])})) "
                 f"(fill (type none)) (uuid {q(uid('r'))}))")


def gline(pts, stype="solid", width=0.3, color=BLACK):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    ITEMS.append(f"(polyline (pts {p}) (stroke (width {f(width)}) (type {stype}) "
                 f"(color {color[0]} {color[1]} {color[2]} {f(color[3])})) (uuid {q(uid('p'))}))")


# --------------------------------------------------------------------------
# LAYOUT  (A3 landscape, mm; every connection point on the 1.27 mm grid)
# --------------------------------------------------------------------------
L = "console_custom:"
WPWR = 0.35     # power wire width
WLED = 0.25

# ---- header ----
text(PROJECT_NAME.upper(), 15.24, 22.86, 4.0, bold=True)
text("IMPROVED REDESIGN (not what was originally built)", 15.24, 30.48, 2.8, bold=True, color=(170, 0, 0, 1))
text("Proposed changes to the console circuit: separate fused branches and clearer connections. "
     "Proposed circuit revision. This arrangement has not been installed.", 15.24, 36.83, 1.6)

YP, YN = 63.5, 68.58          # + and - lines of the feed
YBUS = YP                      # fuse-block bus
COLS = [132.08, 175.26, 218.44, 261.62]   # F1..F4 columns
XDROP = 114.3                  # J1 minus drops to the earth bus here
YE = 142.24                    # earth bus pin level

# ---- car side ----
VAL = 2.0      # Value text size for parts on the power path (video legibility)
ANN = 1.4      # minimum size for small annotations
text("(in the car; not part of the build)", 12.7, 79.375, ANN, italic=True)
place(L + "CAR_12V_OUTLET", "CAR1", "Car 12 V outlet", 25.4, YP,
      ref_at=(26.67, 55.88, None), val_at=(26.67, 76.2, None), in_bom=False, on_board=False,
      val_size=VAL,
      desc="The car's own 12 V accessory outlet in the lower centre stack. Switched with the car; "
           "car's own fuse. Not part of the build.")
place(L + "FUSED_CIG_PLUG", "P1", "Fused plug, 10 A", 50.8, YP,
      ref_at=(50.8, 49.53, None), val_at=(50.8, 53.34, None), val_size=VAL,
      desc="Fused 12 V cigarette-lighter plug with a 10 A fuse in its tip (main fuse). Tip is always +.")
place(L + "CONN_2P_INLINE", "J1", "2-pin connector, 10 A min", 104.14, YP,
      ref_at=(104.14, 49.53, None), val_at=(104.14, 53.34, None),
      desc="Two-pin car connector rated at least 10 A, with grommet or strain relief at the board.")

wire([pin_xy("CAR1", "1"), pin_xy("P1", "1")], RED, WPWR)
wire([pin_xy("CAR1", "2"), pin_xy("P1", "3", 0)], BLACK, WPWR)
wire([pin_xy("P1", "2"), pin_xy("J1", "1", 0)], RED, WPWR)
wire([pin_xy("P1", "3", 1), pin_xy("J1", "2", 0)], BLACK, WPWR)
text("plugs in", 33.02, 61.976, ANN, italic=True)
text("W1: 1.5 mm² (16 AWG)", 79.375, 58.42, VAL, justify="bottom", bold=True)
text("red / black twin feed", 79.375, 61.595, ANN, justify="bottom")
text("red = +12 V", 79.375, 66.04, ANN, justify="bottom", color=RED)
text("black = earth", 79.375, 71.755, ANN, justify="bottom")

# ---- fuse block bus ----
j1p = pin_xy("J1", "1", 1)
j1n = pin_xy("J1", "2", 1)
XPWR = 120.65
wire([j1p, (XPWR, YBUS)], RED, WPWR)
wire([(XPWR, YBUS), (COLS[0], YBUS)], RED, WPWR)
for a, b in zip(COLS, COLS[1:]):
    wire([(a, YBUS), (b, YBUS)], RED, WPWR)
for c in COLS[:-1]:
    junction(c, YBUS, RED)
place("power:+12V", "#PWR01", "+12V", XPWR, YBUS, ref_at=(XPWR, YBUS + 3.81, None),
      val_at=(XPWR, YBUS - 4.064, None), hide_ref=True, desc="Fused +12 V (after P1)")
place("power:PWR_FLAG", "#FLG01", "PWR_FLAG", XPWR, YBUS, angle=180, ref_at=(XPWR, YBUS + 2, None),
      val_at=(XPWR, YBUS + 4, None), hide_ref=True, hide_val=True)

rect(124.46, 55.88, 271.78, 80.01)
text("4-WAY MINI BLADE FUSE BLOCK (on the panel underside, fed from J+)", 125.73, 59.69, 1.27, bold=True,
     color=(80, 80, 80, 1))

FUSES = [("F1", "5 A", "12 V socket X2"), ("F2", "5 A", "USB socket X1"),
         ("F3", "3 A", "Qi pad U2 via J2"), ("F4", "2 A", "push button SW1 -> lights")]
YF = 72.39
for (ref, val, feeds), c in zip(FUSES, COLS):
    place("Device:Fuse", ref, val, c, YF, ref_at=(c + 2.032, YF - 1.27, "left"),
          val_at=(c + 2.032, YF + 1.905, "left"), val_size=VAL,
          desc=f"Mini blade fuse {val} in the 4-way fuse block; feeds {feeds}")
    wire([(c, YBUS), pin_xy(ref, "1")], RED, WPWR)

# ---- the three load columns share one label layout ----
YL = 101.6


def col_labels(c, lines):
    """Small annotation lines to the right of a load symbol, under its Value."""
    for i, ln in enumerate(lines):
        text(ln, c + 10.16, YL + 3.302 + 2.286 * i, ANN)


def col_place(lib, ref, value, c, desc, val_size=VAL):
    place(lib, ref, value, c, YL, ref_at=(c + 10.16, YL - 3.81, "left"),
          val_at=(c + 10.16, YL - 0.635, "left"), val_size=val_size, desc=desc)


# ---- column 1: F1 -> X2 12 V socket ----
c = COLS[0]
col_place(L + "SOCKET_12V", "X2", "12 V socket", c,
          "Panel 12 V socket (the red-ringed fitting). Label 'max 60 W'. Ring terminal on centre stud; "
          "rubber boot over the back.")
wire([pin_xy("F1", "2"), pin_xy("X2", "1")], RED, WPWR)
wire([pin_xy("X2", "2"), (c, YE)], BLACK, WPWR)
text("0.75 mm²", c + 1.27, 85.09, ANN)
col_labels(c, ["max 60 W", "ring terminal on stud", "rubber boot on back"])

# ---- column 2: F2 -> X1 USB socket ----
c = COLS[1]
col_place(L + "USB_PD_QC_SOCKET", "X1", "Dual USB socket", c,
          "Dual USB PD/QC panel socket, 12/24 V input, blue LED ring.",
          val_size=1.8)   # 2.0 would run into the U2 box
wire([pin_xy("F2", "2"), pin_xy("X1", "1")], RED, WPWR)
wire([pin_xy("X1", "2"), (c, YE)], BLACK, WPWR)
text("0.5-0.75 mm²", c + 1.27, 85.09, ANN)
col_labels(c, ["USB-C PD +", "USB-A QC3.0"])

# ---- column 3: F3 -> J2 -> Qi pad U2 -> J2 -> earth ----
c = COLS[2]
place(L + "CONN_2P_PLUG_SPLIT", "J2", "2-pin plug, ~3 A", c, 86.36, unit=1, unit_count_key=True,
      ref_at=(c + 3.175, 85.725, "left"), val_at=(c + 3.175, 88.265, "left"),
      desc="Two-pin plug (about 3 A) so the Qi pad can be unplugged from the panel. Unit A = pin 1 (+).")
col_place(L + "QI_CHARGER_PAD", "U2", "Qi charger pad", c,
          "Qi wireless charger pad on the tray in front of the gear lever. Must accept 12-14.6 V.")
place(L + "CONN_2P_PLUG_SPLIT", "J2", "2-pin plug, ~3 A", c, 119.38, unit=2, unit_count_key=True,
      ref_at=(c + 3.175, 118.745, "left"), val_at=(c + 3.175, 121.285, "left"), hide_val=True,
      desc="Two-pin plug (about 3 A). Unit B = pin 2 (-).")
wire([pin_xy("F3", "2"), pin_xy("J2", "1", 0, unit=1)], RED, WPWR)
wire([pin_xy("J2", "1", 1, unit=1), pin_xy("U2", "1")], RED, WPWR)
wire([pin_xy("U2", "2"), pin_xy("J2", "2", 0, unit=2)], BLACK, WPWR)
wire([pin_xy("J2", "2", 1, unit=2), (c, YE)], BLACK, WPWR)
text("pin 1 (+)", c + 3.175, 91.44, ANN, italic=True)
text("pin 2 (-)", c + 3.175, 121.92, ANN, italic=True)
col_labels(c, ["on the tray in front", "of the gear lever"])

# ---- column 4: F4 -> SW1 -> U1 controller ----
c = COLS[3]
place("Switch:SW_Push", "SW1", "Silver push button (latching)", c, 86.36, angle=90, field_angle=90,
      ref_at=(c + 2.54, 85.09, "right"), val_at=(c + 2.54, 87.63, "right"), val_size=VAL,
      desc="Silver stainless anti-vandal push button, latching, rated at least 2 A DC. The only control: "
           "turns the RGB lights on.")
text("rated 2 A DC or more", c + 2.54, 91.44, ANN)
XU1, YU1 = c + 17.78, 104.14
place(L + "BT_RGB_CONTROLLER", "U1", "Bluetooth RGB controller", XU1, YU1,
      ref_at=(XU1 + 12.7, YU1 - 9.525, None), val_at=(c + 2.54, YU1 + 10.16, "left"), val_size=VAL,
      desc="Bluetooth RGB LED controller (phone app). Supply 12 V nominal, up to ~14.6 V with the engine running.")
text("12 V nominal, up to ~14.6 V", c + 2.54, YU1 + 14.605, ANN, justify="left bottom", bold=True,
     color=(170, 0, 0, 1))
sw_a, sw_b = pin_xy("SW1", "1"), pin_xy("SW1", "2")
sw_top, sw_bot = (sw_a, sw_b) if sw_a[1] < sw_b[1] else (sw_b, sw_a)
wire([pin_xy("F4", "2"), sw_top], RED, WPWR)
wire([sw_bot, pin_xy("U1", "1")], RED, WPWR)
wire([pin_xy("U1", "2"), (c, YE)], BLACK, WPWR)
text("switched +12 V", c + 1.27, 95.25, ANN, color=RED)

# ---- lighting: U1 -> J3 splitter -> H1..H3 -> fibres ----
XJ3 = 318.77                 # clear of the 2.0 mm SW1 value
place(L + "RGB_SPLITTER_1TO3", "J3", "1-to-3 RGB splitter", XJ3, YU1,
      ref_at=(XJ3, YU1 - 26.035, None), val_at=(XJ3, YU1 + 26.035, None),
      desc="1-to-3 splitter for the 4-wire LED cables (multi-pin in-line plugs).")
for n in ("3", "4", "5", "6"):
    a = pin_xy("U1", n)
    b = pin_xy("J3", str(int(n) - 2), 0)
    wire([a, b], LEDC, WLED)
XH = 349.25
HEADS = [("H1", YU1 - 17.78, 1), ("H2", YU1, 2), ("H3", YU1 + 17.78, 3)]
for ref, yh, grp in HEADS:
    place(L + "RGB_LED_HEAD", ref, "RGB LED head", XH, yh,
          ref_at=(XH - 5.08, yh + 7.62, "left"), val_at=(XH - 1.27, yh + 7.62, "left"),
          desc="Aluminium RGB LED head, common anode.")
    for i in range(4):
        a = pin_xy("J3", str(i + 1), grp)   # groups were added in order: input, +17.78, 0, -17.78
        b = pin_xy(ref, str(i + 1))
        wire([a, b], LEDC, WLED)
place(L + "SIDE_GLOW_FIBRE", "FO1", "side-glow fibre, top of left arm", XH + 12.7, YU1 - 17.78,
      ref_at=(XH + 12.7, YU1 - 17.78 - 3.175, "left"), val_at=(XH + 17.78, YU1 - 17.78 - 3.175, "left"),
      desc="Side-glow optical fibre along the top of the left (driver) side arm, as built (IMG_3490, 3501, 3502) (light only, no wires).")
place(L + "SIDE_GLOW_FIBRE", "FO2", "side-glow fibre, top of right arm", XH + 12.7, YU1,
      ref_at=(XH + 12.7, YU1 - 3.175, "left"), val_at=(XH + 17.78, YU1 - 3.175, "left"),
      desc="Side-glow optical fibre along the top of the right (passenger) side arm, as built (IMG_3490, 3501, 3502) (light only, no wires).")
text("(light only, no wires)", XH + 12.7, YU1 - 17.78 + 3.81, ANN, italic=True, color=(120, 80, 200, 1))
text("(light only, no wires)", XH + 12.7, YU1 + 3.81, ANN, italic=True, color=(120, 80, 200, 1))
text("H3: mount it properly", XH + 12.7, YU1 + 17.78 - 0.635, 1.4, bold=True)
text("or remove it", XH + 12.7, YU1 + 17.78 + 1.905, 1.4, bold=True)
text("4-core LED cables: V+ (common anode), R, G, B", XJ3, YU1 + 29.21, ANN, justify="bottom")

# ---- earth bus (black bar, white "EARTH (-)" on it) ----
TBY = YE + 2.54                       # bar top edge (sheet y); bar is TB_H tall
place(L + "EARTH_BUS_BAR", "TB1", "Earth bus bar (J-)", XDROP, TBY,
      ref_at=(137.16, 140.335, "left"), val_at=(142.24, 140.335, "left"),
      desc="Earth bus bar or lever connector on the panel underside (J-). Black wires only.")
for xt in (153.67, 196.85, 240.03):
    text("EARTH (-)", xt, TBY + TB_H / 2, 2.4, justify="", bold=True, color=(255, 255, 255, 1))
wire([j1n, (XDROP, j1n[1]), (XDROP, YE)], BLACK, WPWR)
YB = TBY + TB_H + 2.54                # bottom pin ends of the bar
place("power:GND", "#PWR02", "GND", XDROP + TB_BOT[0], YB,
      ref_at=(XDROP + TB_BOT[0], YB + 6.35, None), val_at=(XDROP + TB_BOT[0], YB + 3.81, None),
      hide_ref=True, desc="Panel 0 V / earth return")
place("power:PWR_FLAG", "#FLG02", "PWR_FLAG", XDROP + TB_BOT[1], YB, angle=180,
      ref_at=(XDROP + TB_BOT[1], YB + 4, None), val_at=(XDROP + TB_BOT[1], YB + 6, None),
      hide_ref=True, hide_val=True)
text("Every black return wire ends on TB1, which goes back to the car outlet through J1, W1 and P1.  "
     "No connection to the car body.", 147.32, 153.035, 1.27)

# ---- plain-words notes for each block ----
NOTE_FILL = (255, 253, 235, 1)
text_box("1  POWER IN (from the car)\n"
         "P1 plugs into the car's own 12 V outlet. That outlet is live only when the car is on and has its "
         "own fuse in the car. Nothing in the car's wiring is cut, and the plug cannot go in backwards "
         "(the tip is always +).\n"
         "P1 holds the main 10 A fuse in its tip. W1 is 1.5 mm² (16 AWG) red/black twin, thick enough for "
         "10 A. (Thinner 0.75-1.0 mm² wire would need a 7.5 A fuse instead.)\n"
         "J1 lets the whole panel unplug from the lead. It must be rated 10 A or more, with a grommet or "
         "strain relief where W1 enters the board.",
         15.24, 81.28, 93.98, 50.8, 1.8, NOTE_FILL)
text_box("2  FUSE BLOCK AND EARTH BUS\n"
         "Separate branch fuses (F1-F4) are proposed for the devices and their wires. Verify fuse "
         "coordination and conductor ratings; protection is not established by this drawing.\n"
         "All black returns meet on the earth bus bar TB1 (J-).",
         15.24, 135.89, 93.98, 31.75, 1.8, NOTE_FILL)

# ---- legend (left column, under note 2) ----
LX, LY = 15.24, 170.18
text_box("", LX, LY, 93.98, 25.4, 1.27, (255, 255, 255, 1))
text("LEGEND", LX + 2.54, LY + 4.445, 1.5, bold=True)
gline([(LX + 2.54, LY + 8.255), (LX + 12.7, LY + 8.255)], width=0.5, color=RED)
text("+12 V wire (red)", LX + 15.24, LY + 8.89, 1.4)
gline([(LX + 2.54, LY + 12.7), (LX + 12.7, LY + 12.7)], width=0.5, color=BLACK)
text("earth / 0 V return (black)", LX + 15.24, LY + 13.335, 1.4)
gline([(LX + 2.54, LY + 17.145), (LX + 12.7, LY + 17.145)], width=0.4, color=LEDC)
text("LED cable, 4-core (V+, R, G, B)", LX + 15.24, LY + 17.78, 1.4)
gline([(LX + 2.54, LY + 21.59), (LX + 12.7, LY + 21.59)], stype="dash", width=0.3, color=BLACK)
gline([(LX + 11.43, LY + 20.828), (LX + 12.7, LY + 21.59), (LX + 11.43, LY + 22.352)], width=0.3, color=BLACK)
text("light into a fibre (optical, no wires)", LX + 15.24, LY + 22.225, 1.4)
gline([(LX + 59.69, LY + 7.62), (LX + 67.31, LY + 7.62), (LX + 67.31, LY + 10.16), (LX + 59.69, LY + 10.16),
       (LX + 59.69, LY + 7.62)], stype="dash", width=0.2, color=GREY)
text("one fuse block", LX + 69.85, LY + 9.525, 1.4)
text("J2A / J2B = the two", LX + 59.69, LY + 14.605, 1.4)
text("contacts of plug J2", LX + 59.69, LY + 17.145, 1.4)
gline([(LX + 59.69, LY + 21.59), (LX + 67.31, LY + 21.59)], width=0.9, color=FIBRE)
text("side-glow fibre", LX + 69.85, LY + 22.225, 1.4)

NB_Y, NB_H = 157.48, 38.1
text_box("3  12 V SOCKET (X2)\n"
         "Fuse F1 5 A, 0.75 mm² wire. Centre stud = +, shell = -. Ring terminal on the stud (not a push-on "
         "spade) and a rubber boot over the back. Label it \"max 60 W\".",
         111.76, NB_Y, 40.64, NB_H, 1.75, NOTE_FILL)
text_box("4  USB SOCKET (X1)\n"
         "Fuse F2 5 A, 0.5-0.75 mm² wire. One round socket with USB-C PD and USB-A QC3.0 (about 30 W + 18 W, "
         "typical figures). Its blue ring lights when it has power.",
         154.94, NB_Y, 40.64, NB_H, 1.75, NOTE_FILL)
text_box("5  WIRELESS CHARGER (U2)\n"
         "Fuse F3 3 A. The wireless charging pad sits on the tray in front of the gear lever and unplugs at J2 "
         "(2-pin plug, about 3 A). Its Qi module must accept 12-14.6 V directly.",
         198.12, NB_Y, 40.64, NB_H, 1.75, NOTE_FILL)
text_box("6  RGB LIGHTS (the only switched circuit)\n"
         "Fuse F4 2 A. The silver push button SW1 is the only control on the console: press it and the RGB "
         "lights come on. It switches the +12 V feed to the Bluetooth controller U1, so use a latching button "
         "rated 2 A DC or more. Colours and modes are set in the phone app.\n"
         "U1 drives three aluminium RGB LED heads through the 1-to-3 splitter J3 (4 wires each: V+ common "
         "anode, R, G, B). H1 and H2 shine into the side-glow fibres along the tops of the two side arms. Mount H3 "
         "properly or remove it.\n"
         "The USB socket, the 12 V socket and the Qi pad do not go through the button: they are live whenever "
         "the car's outlet is live.",
         241.3, NB_Y, 165.1, NB_H, 1.75, NOTE_FILL)

# ---- parts list ----
PX, PY = 15.24, 200.66
text_box("", PX, PY, 110.49, 82.55, 1.27, (255, 255, 255, 1))
text("PARTS (recommended ratings for the redesign)", PX + 2.54, PY + 5.08, 1.6, bold=True)
PARTS = [
    ("P1", "Fused 12 V cigarette plug, 10 A fuse in the tip"),
    ("W1", "Feed lead, 1.5 mm² (16 AWG) red/black twin"),
    ("J1", "2-pin car connector, 10 A or more, with grommet"),
    ("F1-F4", "4-way mini blade fuse block: 5 A, 5 A, 3 A, 2 A"),
    ("X2", "12 V accessory socket, max 60 W, rubber boot"),
    ("X1", "Dual USB socket: USB-C PD + USB-A QC3.0"),
    ("J2", "2-pin plug for the Qi pad, about 3 A"),
    ("U2", "Qi wireless charger pad, 12-14.6 V input"),
    ("SW1", "Silver push button, latching, 2 A DC or more"),
    ("U1", "Bluetooth RGB LED controller (phone app)"),
    ("J3", "1-to-3 splitter, 4-pin in-line plugs"),
    ("H1-H3", "Aluminium RGB LED heads, common anode"),
    ("FO1, FO2", "Side-glow optical fibre with fin (light only)"),
    ("TB1", "Earth bus bar or lever connector (J-)"),
    ("CAR1", "The car's own 12 V outlet (not part of the build)"),
]
for i, (r, d) in enumerate(PARTS):
    yy = PY + 10.16 + i * 4.826
    text(r, PX + 2.54, yy, 1.6, bold=True)
    text(d, PX + 19.05, yy, 1.6)

# ---- wiring rules box (spec 5.2) ----
text_box("PROPOSED WIRING PRACTICES (verify ratings before implementation)\n"
         "-  Red = +12 V and black = earth, everywhere.\n"
         "-  One wire per crimp barrel, with the barrel matched to the wire size. No doubled wires.\n"
         "-  Spade connectors only on flat tabs; a ring terminal on the 12 V socket's centre stud.\n"
         "-  A rubber boot over the back of the 12 V socket, so the bare stud can never touch the seat-belt buckle.\n"
         "-  Sleeving and clips on every run, and grommets wherever a cable passes through the board.\n"
         "-  Keep every cable away from the seat rails, the seat-belt buckle, the gear lever and the "
         "EPB / drive-mode / EV switches.\n"
         "-  Mount the third LED head (H3) properly or remove it.\n"
         "-  No car-body earth and no fuse-box tap, unless I confirm that is how it was originally powered.\n"
         "-  Optional: if the new button has a 12 V LED ring, wire the ring from the switched side to earth.\n"
         "\n"
         "POWER BUDGET at 12 V: USB up to ~4.5 A, Qi pad ~1.5-2 A, lights ~0.5-1 A = about 7 A before anything is "
         "plugged into the 12 V socket. These are estimates, not measured currents. Verify the combined "
         "load against the outlet, wiring and connector ratings; the fuse is not a load regulator.",
         128.27, 200.66, 113.03, 82.55, 1.6, (245, 248, 255, 1))

# ---- note on the drawing ----
text_box("ABOUT THIS SHEET\n"
         "I designed the panel and planned its circuit before fabrication. This present-day drawing proposes "
         "a revised circuit; it is not the installed wiring and has not been built or validated. "
         "For the installed arrangement, see console_as_built.pdf. Ratings are recommendations; wire sizes "
         "and values are approximate.\n"
         "From the original build: the only control is a silver push button that turns on the RGB LEDs. The "
         "red-ringed part is a 12 V socket, not a switch.",
         243.84, 200.66, 162.56, 22.86, 1.7, (255, 240, 240, 1), border_color=(170, 0, 0, 1))
text_box("STILL TO CHECK before building this version\n"
         "-  The car's outlet: that it is off when the car is off, and its rating (usually 120 W / 10 A on a "
         "~15 A fuse; check the owner's manual).\n"
         "-  U1 and the Qi module must accept up to ~14.6 V (the original controller's label says 5-12 V).\n"
         "-  The original button latches; its current rating is unknown. Specify a switch rated 2 A DC or more.",
         243.84, 226.06, 162.56, 20.32, 1.55, (255, 255, 255, 1))


# --------------------------------------------------------------------------
# write files
# --------------------------------------------------------------------------

def build_schematic():
    libs = [extract_lib_symbol(lib, name) for lib, name in STD]
    for name, body in CUSTOM.items():
        libs.append(body.replace(f"(symbol {q(name)}", f"(symbol {q(CUSTOM_LIB + ':' + name)}", 1))
    tb = [
        f"(title {q(PROJECT_NAME + ' - improved')})",
        f"(date {q(DATE)})",
        '(rev "1")',
        f"(company {q('Console circuit: proposed revision')})",
        f"(comment 1 {q('IMPROVED REDESIGN, spec section 5.2 - NOT what was originally built')})",
        f"(comment 2 {q('Drawn ' + DATE)})",
        f"(comment 3 {q('Proposed revision; not installed or physically validated')})",
        f"(comment 4 {q('Removable centre-console panel')})",
    ]
    out = [
        "(kicad_sch",
        "\t(version 20260101)",
        '\t(generator "console_circuit_builder")',
        '\t(generator_version "1.0")',
        f"\t(uuid {q(ROOT_UUID)})",
        '\t(paper "A3")',
        "\t(title_block\n\t\t" + "\n\t\t".join(tb) + "\n\t)",
        "\t(lib_symbols\n\t" + "\n\t".join(libs) + "\n\t)",
    ]
    out += ["\t" + it for it in ITEMS]
    out.append('\t(sheet_instances (path "/" (page "1")))')
    out.append("\t(embedded_fonts no)")
    out.append(")")
    return "\n".join(out) + "\n"


def write_custom_lib():
    body = ["(kicad_symbol_lib", "\t(version 20251024)", '\t(generator "console_circuit_builder")',
            '\t(generator_version "1.0")']
    for name, sym in CUSTOM.items():
        body.append("\t" + sym)
    body.append(")")
    with open(os.path.join(HERE, CUSTOM_LIB + ".kicad_sym"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(body) + "\n")


def merge_sym_lib_table():
    """Add the project entries to ./sym-lib-table without removing anything already there."""
    path = os.path.join(HERE, "sym-lib-table")
    want = {
        CUSTOM_LIB: ("${KIPRJMOD}/" + CUSTOM_LIB + ".kicad_sym", "Custom symbols for the car console schematics"),
        "Device": ("${KICAD10_SYMBOL_DIR}/Device.kicad_sym", ""),
        "Switch": ("${KICAD10_SYMBOL_DIR}/Switch.kicad_sym", ""),
        "power": ("${KICAD10_SYMBOL_DIR}/power.kicad_sym", ""),
    }
    existing = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    have = set(re.findall(r'\(name\s+"?([^")\s]+)"?\)', existing))
    lines = [ln for ln in existing.strip().splitlines() if ln.strip() and ln.strip() != ")"] if existing else \
        ["(sym_lib_table", "  (version 7)"]
    for name, (uri, descr) in want.items():
        if name not in have:
            lines.append(f'  (lib (name "{name}")(type "KiCad")(uri "{uri}")(options "")(descr "{descr}"))')
    lines.append(")")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_project():
    path = os.path.join(HERE, BASE + ".kicad_pro")
    excl = []
    pro = {"meta": {"filename": BASE + ".kicad_pro", "version": 3},
           "erc": {"erc_exclusions": excl},
           "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
           "sheets": [[ROOT_UUID, "Root"]]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(pro, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    sch = build_schematic()
    with open(os.path.join(HERE, BASE + ".kicad_sch"), "w", encoding="utf-8") as fh:
        fh.write(sch)
    write_custom_lib()
    merge_sym_lib_table()
    write_project()
    print("wrote", os.path.join(HERE, BASE + ".kicad_sch"))
