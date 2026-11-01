#!/usr/bin/env python3
"""
Generate the installed-wiring schematic and custom symbols for KiCad 10.

Solid connections are visible in the photographs; dashed connections are inferred.
See ../docs/MODEL-SPEC.md for components and ../docs/PROJECT-DETAILS.md for
project chronology. The silver button latches down to keep the lights on; the controller
sits beneath the cup, with two heads feeding rim fibres and a third loose head.

Run: python3 make_console_as_built.py
Then: kicad-cli sch erc --severity-all console_as_built.kicad_sch
      kicad-cli sch export pdf --draw-hop-over -o console_as_built.pdf console_as_built.kicad_sch
"""
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SYMDIR = os.environ.get("KICAD10_SYMBOL_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
if not os.path.isdir(SYMDIR):
    raise SystemExit("Set KICAD10_SYMBOL_DIR to the symbols directory of your KiCad 10 installation.")
PROJECT = "console_as_built"
OUT = os.path.join(HERE, PROJECT + ".kicad_sch")
CUSTOM_LIB = "console_as_built"  # nickname for the custom symbols below

NS = uuid.UUID("3b1e7c52-9a0d-4f6e-8c21-5d7a40b2e911")
_counter = [0]


def U(key=None):
    """Deterministic UUID (stable between runs)."""
    if key is None:
        _counter[0] += 1
        key = "item-%d" % _counter[0]
    return str(uuid.uuid5(NS, PROJECT + ":" + key))


ROOT_UUID = U("root-sheet")

# ----------------------------------------------------------------- S-expr ---


class Q(str):
    """A string that must be written quoted."""


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def atom(x):
    if isinstance(x, Q):
        return '"' + esc(x) + '"'
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, float)):
        v = round(float(x), 4)
        if v == 0:
            v = 0.0
        s = ("%.4f" % v).rstrip("0").rstrip(".")
        return s
    return str(x)


def ser(node, ind=0):
    tab = "\t" * ind
    if not any(isinstance(c, list) for c in node):
        return tab + "(" + " ".join(atom(c) for c in node) + ")"
    head = []
    lines = []
    seen_list = False
    for c in node:
        if isinstance(c, list):
            seen_list = True
            # keep (xy ..) points on one line
            lines.append(ser(c, ind + 1))
        elif not seen_list:
            head.append(atom(c))
        else:
            lines.append("\t" * (ind + 1) + atom(c))
    return tab + "(" + " ".join(head) + "\n" + "\n".join(lines) + "\n" + tab + ")"


# ------------------------------------------------------------ primitives ----


def font(size=1.27, bold=False, italic=False, color=None):
    f = ["font", ["size", size, size]]
    if bold:
        f.append(["bold", "yes"])
    if italic:
        f.append(["italic", "yes"])
    if color:
        f.append(["color"] + list(color))
    return f


def effects(size=1.27, justify=None, bold=False, italic=False, color=None):
    e = ["effects", font(size, bold, italic, color)]
    if justify:
        e.append(["justify"] + justify.split())
    return e


def stroke(width=0, kind="default", color=None):
    s = ["stroke", ["width", width], ["type", kind]]
    if color:
        s.append(["color"] + list(color))
    return s


def fill(kind="none", color=None):
    f = ["fill", ["type", kind]]
    if color:
        f.append(["color"] + list(color))
    return f


# symbol-body graphics (library coordinates, y up)
def s_rect(x1, y1, x2, y2, w=0.254, fk="background", fc=None, sc=None):
    return ["rectangle", ["start", x1, y1], ["end", x2, y2],
            stroke(w, "default", sc), fill(fk, fc)]


def s_poly(pts, w=0, fk="none", fc=None, sc=None):
    return ["polyline", ["pts"] + [["xy", x, y] for x, y in pts],
            stroke(w, "default", sc), fill(fk, fc)]


def s_circle(cx, cy, r, w=0, fk="none", fc=None, sc=None):
    return ["circle", ["center", cx, cy], ["radius", r],
            stroke(w, "default", sc), fill(fk, fc)]


def s_text(s, x, y, size=1.27, justify=None, bold=False, angle=0, color=None):
    return ["text", Q(s), ["at", x, y, angle],
            effects(size, justify, bold, color=color)]


def s_pin(num, name, x, y, angle, length=2.54, etype="passive"):
    return ["pin", etype, "line", ["at", x, y, angle], ["length", length],
            ["name", Q(name), effects()], ["number", Q(num), effects()]]


def s_arrow(x1, y, x2, sc=None, w=0.2):
    """Small light arrow pointing +x (library coords)."""
    return [s_poly([(x1, y), (x2, y)], w, sc=sc),
            s_poly([(x2 - 0.9, y + 0.5), (x2, y), (x2 - 0.9, y - 0.5)], w, sc=sc)]


def lib_property(key, value, x, y, hide=False, size=1.27, justify=None):
    p = ["property", Q(key), Q(value), ["at", x, y, 0], ["show_name", "no"],
         ["do_not_autoplace", "no"]]
    if hide:
        p.append(["hide", "yes"])
    p.append(effects(size, justify))
    return p


def custom_symbol(name, ref, value, desc, items, ref_at=(0, 0), val_at=(0, 0),
                  hide_pin_names=True, pin_name_offset=0.508):
    sym = ["symbol", Q(CUSTOM_LIB + ":" + name),
           ["pin_numbers", ["hide", "yes"]]]
    pn = ["pin_names", ["offset", pin_name_offset]]
    if hide_pin_names:
        pn.append(["hide", "yes"])
    sym.append(pn)
    sym += [["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "no"],
            ["in_pos_files", "yes"], ["duplicate_pin_numbers_are_jumpers", "no"]]
    sym.append(lib_property("Reference", ref, ref_at[0], ref_at[1]))
    sym.append(lib_property("Value", value, val_at[0], val_at[1]))
    sym.append(lib_property("Footprint", "", 0, 0, hide=True))
    sym.append(lib_property("Datasheet", "", 0, 0, hide=True))
    sym.append(lib_property("Description", desc, 0, 0, hide=True))
    sym.append(["symbol", Q(name + "_1_1")] + items)
    sym.append(["embedded_fonts", "no"])
    return sym


def extract_lib_symbol(libname, symname):
    """Copy a symbol definition verbatim from a KiCad library file."""
    path = os.path.join(SYMDIR, libname + ".kicad_sym")
    text = open(path, encoding="utf-8").read()
    key = '\n\t(symbol "%s"\n' % symname
    start = text.index(key) + 1
    depth, i, in_str, esc_ = 0, start, False, False
    while True:
        c = text[i]
        if in_str:
            if esc_:
                esc_ = False
            elif c == "\\":
                esc_ = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1
    block = text[start:end]
    assert "(extends" not in block, "flatten derived symbols first"
    block = block.replace('(symbol "%s"' % symname,
                          '(symbol "%s:%s"' % (libname, symname), 1)
    # indent one more level to sit inside (lib_symbols ...)
    return "\n".join("\t" + ln for ln in block.split("\n"))


# ------------------------------------------------------ custom symbols ------

BLUE = (0, 90, 255, 1)
RED = (220, 0, 0, 1)
GREEN = (0, 150, 0, 1)
DARK = (60, 60, 60, 1)
FIBRE = (190, 160, 255, 1)
WIRE_GREEN = (0, 150, 0, 1)
# drawing colours for wires (NOT the real wire colours): red = + side, black = - side,
# purple = 4-core LED cables. Same code as the improved sheet.
W_POS = (200, 0, 0, 1)
W_NEG = (0, 0, 0, 1)
W_LED = (90, 70, 150, 1)
W_GREY = (90, 90, 90, 1)
WPWR = 0.3
WLED = 0.25

customs = []

# CAR1 - the car's own 12 V outlet (factory part, shown as the source)
customs.append(custom_symbol(
    "CAR_12V_OUTLET", "CAR", "Car 12 V outlet (factory)",
    "Car's own 12 V outlet, lower centre stack; likely live only with ignition on",
    [
        s_rect(-12.7, 6.35, 5.08, -6.35),
        s_circle(-3.81, 0, 4.2, 0.254),
        s_circle(-3.81, 0, 1.1, 0, "outline"),
        s_text("+", 3.3, 2.54, 1.27),
        s_text("-", 3.3, -2.54, 1.27),
        s_pin("1", "+", 10.16, 2.54, 180, 5.08, "power_out"),
        s_pin("2", "-", 10.16, -2.54, 180, 5.08, "power_out"),
    ], ref_at=(-3.81, 8.255), val_at=(-3.81, -8.255)))

# P1 - fused cigarette plug with the fuse in its tip
customs.append(custom_symbol(
    "FUSED_CIG_PLUG", "P", "Fused 12 V cigarette plug",
    "Right-angle fused 12 V cigarette plug with long lead; fuse in the unscrewing tip, value unknown",
    [
        s_rect(-10.16, 6.35, 10.16, -6.35),
        s_poly([(-10.16, 2.54), (-3.81, 2.54)], 0.254),
        s_rect(-3.81, 3.556, 3.81, 1.524, 0.254, "none"),
        s_poly([(-3.81, 2.54), (3.81, 2.54)], 0.15),
        s_poly([(3.81, 2.54), (10.16, 2.54)], 0.254),
        s_poly([(-10.16, -2.54), (10.16, -2.54)], 0.254),
        s_text("fuse ? A", 0, 5.0, 1.4, bold=True),
        s_text("tip +", -9.5, 0.85, 1.4, "left"),
        s_text("shell -", -9.5, -4.0, 1.4, "left"),
        s_pin("1", "TIP+", -15.24, 2.54, 0, 5.08),
        s_pin("2", "SHELL-", -15.24, -2.54, 0, 5.08),
        s_pin("3", "OUT+", 15.24, 2.54, 180, 5.08),
        s_pin("4", "OUT-", 15.24, -2.54, 180, 5.08),
    ], ref_at=(0, 8.255), val_at=(0, -8.255)))

# W1 - two-core feed cable, brown + / blue -
customs.append(custom_symbol(
    "FEED_CABLE_2C", "W", "Feed cable, brown/blue",
    "Round black two-core cable, brown (+) and blue (-), ~0.5-0.75 mm2",
    [
        s_rect(-7.62, 5.08, 7.62, -5.08, 0.254, "background"),
        s_poly([(-10.16, 2.54), (10.16, 2.54)], 0.35, sc=(140, 80, 20, 1)),
        s_poly([(-10.16, -2.54), (10.16, -2.54)], 0.35, sc=(0, 80, 220, 1)),
        s_text("brown +", 0, 3.85, 1.4),
        s_text("blue -", 0, -3.85, 1.4),
        s_pin("1", "BROWN_IN", -12.7, 2.54, 0, 2.54),
        s_pin("2", "BLUE_IN", -12.7, -2.54, 0, 2.54),
        s_pin("3", "BROWN_OUT", 12.7, 2.54, 180, 2.54),
        s_pin("4", "BLUE_OUT", 12.7, -2.54, 180, 2.54),
    ], ref_at=(0, 6.985), val_at=(0, -6.985)))

# X1 - dual USB socket with blue LED ring
customs.append(custom_symbol(
    "USB_PD_QC_SOCKET", "X", "Dual USB socket PD/QC",
    "Round 12/24 V panel socket: USB-C PD + USB-A QC3.0; blue LED ring lights only when powered",
    [
        s_rect(-7.62, 7.62, 7.62, -7.62),
        s_circle(0, 0, 5.7, 0.5, sc=BLUE),
        s_rect(-1.9, 2.6, 1.9, 1.3, 0.15, "none"),
        s_rect(-2.8, -0.9, 2.8, -2.7, 0.15, "none"),
        s_text("C", 0, 3.85, 1.4),
        s_text("A", 0, -3.95, 1.4),
        s_text("+", 1.5, 9.6, 1.27, "left"),
        s_text("-", 1.5, -9.6, 1.27, "left"),
        s_pin("1", "+", 0, 12.7, 270, 5.08),
        s_pin("2", "-", 0, -12.7, 90, 5.08),
    ], ref_at=(8.89, 2.54), val_at=(8.89, 0)))

# X2 - 12 V accessory socket (cigarette-lighter type), NOT a switch
customs.append(custom_symbol(
    "SOCKET_12V_ACC", "X", "12 V accessory socket",
    "Cigarette-lighter type 12 V socket: centre +, shell -; red trim ring never lit; not a switch",
    [
        s_rect(-7.62, 7.62, 7.62, -7.62),
        s_circle(0, 0, 6.1, 0.3, sc=RED),
        s_circle(0, 0, 4.6, 0.254),
        s_circle(0, 0, 0.9, 0, "outline"),
        s_text("+", 1.5, 9.6, 1.27, "left"),
        s_text("-", 1.5, -9.6, 1.27, "left"),
        s_pin("1", "CENTRE+", 0, 12.7, 270, 5.08),
        s_pin("2", "SHELL-", 0, -12.7, 90, 5.08),
    ], ref_at=(8.89, 2.54), val_at=(8.89, 0)))

# J2 - small two-pin plug between panel and Qi pad (mated pair)
customs.append(custom_symbol(
    "PLUG_2PIN_INLINE", "J", "2-pin plug (JST-SM style)",
    "Small 2-pin in-line plug (~2.5 mm, JST-SM style) so the Qi pad can be unplugged; 1-3 and 2-4 mate",
    [
        s_rect(-5.08, 4.445, -0.635, -4.445),
        s_rect(0.635, 4.445, 5.08, -4.445),
        s_poly([(-5.08, 2.54), (5.08, 2.54)], 0.2),
        s_poly([(-5.08, -2.54), (5.08, -2.54)], 0.2),
        s_poly([(-1.5, 3.2), (-0.635, 2.54), (-1.5, 1.88)], 0.2),
        s_poly([(-1.5, -1.88), (-0.635, -2.54), (-1.5, -3.2)], 0.2),
        s_pin("1", "PANEL+", -7.62, 2.54, 0, 2.54),
        s_pin("2", "PANEL-", -7.62, -2.54, 0, 2.54),
        s_pin("3", "PAD+", 7.62, 2.54, 180, 2.54),
        s_pin("4", "PAD-", 7.62, -2.54, 180, 2.54),
    ], ref_at=(0, 6.35), val_at=(0, -6.35)))

# U2 - Qi wireless charger pad, 12 V input
customs.append(custom_symbol(
    "QI_PAD_12V", "U", "Qi wireless charger pad",
    "Qi charging pad with leatherette frame and red status LED; module input rating requires checking",
    [
        s_rect(-7.62, 7.62, 12.7, -7.62),
        s_circle(5.08, 0, 1.5, 0.2),
        s_circle(5.08, 0, 3.0, 0.2),
        s_circle(5.08, 0, 4.5, 0.2),
        s_circle(10.9, 5.9, 0.6, 0, "color", RED, RED),
        s_text("Qi", -2.6, 5.3, 1.4),
        s_pin("1", "+12V", -12.7, 2.54, 0, 5.08),
        s_pin("2", "-", -12.7, -2.54, 0, 5.08),
    ], ref_at=(2.54, 9.525), val_at=(2.54, -9.525), hide_pin_names=False))

# U1 - Bluetooth RGB LED controller
customs.append(custom_symbol(
    "BT_RGB_CONTROLLER", "U", "Bluetooth RGB LED controller",
    "Bluetooth RGB LED controller, phone-app control, label INPUT DC 5-12V, DC barrel input; output assumed common-anode",
    [
        s_rect(-15.24, 12.7, 15.24, -12.7),
        s_text("LED CONTROLLER (Bluetooth)", 0, 10.4, 1.27, bold=True),
        s_text("INPUT DC 5-12V", 0, -10.4, 1.4),
        s_text("phone app: colours", 0, -6.6, 1.4),
        s_text("DC barrel in", -14.3, 6.2, 1.4, "left"),
        s_pin("1", "DC+", -20.32, 2.54, 0, 5.08),
        s_pin("2", "DC-", -20.32, -2.54, 0, 5.08),
        # outputs: short 1.27 mm pins so the purple LED-cable wires stay visible
        s_pin("3", "V+(anode*)", 16.51, 7.62, 180, 1.27),
        s_pin("4", "R", 16.51, 2.54, 180, 1.27),
        s_pin("5", "G", 16.51, -2.54, 180, 1.27),
        s_pin("6", "B", 16.51, -7.62, 180, 1.27),
    ], ref_at=(0, 14.605), val_at=(0, -14.605), hide_pin_names=False))

# J3 - 1-to-3 splitter for the 4-wire RGB head cables
spl = [s_rect(-5.08, 35.56, 5.08, -35.56),
       s_text("1 to 3", 0, 12.7, 1.4, bold=True),
       s_text("split", 0, -12.7, 1.4, bold=True)]
names = ["V+", "R", "G", "B"]
rows = [7.62, 2.54, -2.54, -7.62]
n = 1
for nm, y in zip(names, rows):
    spl.append(s_pin(str(n), nm, -6.35, y, 0, 1.27))
    n += 1
for off in (25.4, 0, -25.4):
    for nm, y in zip(names, rows):
        spl.append(s_pin(str(n), nm, 6.35, y + off, 180, 1.27))
        n += 1
customs.append(custom_symbol(
    "RGB_SPLITTER_1TO3", "J", "1-to-3 RGB splitter",
    "1-to-3 splitter with round multi-pin in-line plugs (likely the LED kit's); V+, R, G, B paralleled to each head",
    spl, ref_at=(0, 37.465), val_at=(0, -37.465), hide_pin_names=False,
    pin_name_offset=0.3))

# H1..H3 - aluminium RGB LED heads (common anode)
head = [s_rect(-5.08, 10.16, 10.16, -10.16, 0.254, "color", (225, 225, 230, 1)),
        s_poly([(-5.08, 7.62), (6.35, 7.62), (6.35, -7.62)], 0.2)]
for y, col, letter in ((2.54, RED, "R"), (-2.54, GREEN, "G"), (-7.62, BLUE, "B")):
    head += [
        s_poly([(-5.08, y), (0, y)], 0.2),
        s_poly([(2.032, y + 1.1), (2.032, y - 1.1), (0, y), (2.032, y + 1.1)],
               0.2, "color", col, col),
        s_poly([(0, y + 1.1), (0, y - 1.1)], 0.3, sc=col),
        s_poly([(2.032, y), (6.35, y)], 0.2),
        s_text(letter, -3.4, y + 1.3, 1.4),
    ]
head.append(s_text("V+", -3.0, 8.95, 1.4))
head += s_arrow(10.8, 1.27, 13.6, sc=(230, 120, 0, 1))
head += s_arrow(10.8, -1.27, 13.6, sc=(230, 120, 0, 1))
head += [s_pin("1", "V+", -6.35, 7.62, 0, 1.27),
         s_pin("2", "R", -6.35, 2.54, 0, 1.27),
         s_pin("3", "G", -6.35, -2.54, 0, 1.27),
         s_pin("4", "B", -6.35, -7.62, 0, 1.27)]
customs.append(custom_symbol(
    "RGB_LED_HEAD", "H", "RGB LED head (aluminium)",
    "Machined aluminium RGB LED head ~12.5 x 35 mm, common anode, 4-wire cable",
    head, ref_at=(2.54, 11.43), val_at=(2.54, -11.43)))

# FO1, FO2 - side-glow optical fibre (light only, no electrical pins)
customs.append(custom_symbol(
    "SIDE_GLOW_FIBRE", "FO", "Side-glow fibre",
    "Clear side-glow plastic optical fibre with fin (~4 mm core), lit from one end; light, not electricity",
    [
        s_rect(0, 1.0, 35.56, -1.0, 0.2, "color", FIBRE),
        s_poly([(0.8, -1.8), (34.76, -1.8)], 0.3, sc=(150, 120, 220, 1)),
    ], ref_at=(0, 2.54), val_at=(5.08, 2.54)))

# CLK1 - stick-on analog clock, own battery
customs.append(custom_symbol(
    "CLOCK_OWN_BATTERY", "CLK", "Analog stick-on clock",
    "Small analog car clock, ~34 mm, powered by its own battery",
    [
        s_circle(0, 0, 5.08, 0.3, "background"),
        s_poly([(0, 0), (0, 3.6)], 0.3),
        s_poly([(0, 0), (2.6, 0)], 0.3),
        s_poly([(0, 4.4), (0, 5.08)], 0.2),
        s_poly([(4.4, 0), (5.08, 0)], 0.2),
        s_poly([(0, -4.4), (0, -5.08)], 0.2),
        s_poly([(-4.4, 0), (-5.08, 0)], 0.2),
        s_circle(10.16, 0, 2.6, 0.254, "background"),
        s_text("+", 10.16, 0.3, 1.27, bold=True),
        s_text("own battery", 11.43, -4.4, 1.4),
    ], ref_at=(0, 6.985), val_at=(0, -6.985)))

# ------------------------------------------------------- schematic body -----

items = []


def wire(pts, dashed=False, color=None, width=0):
    """Draw wire segments; color = drawing colour (red + / black - / purple LED)."""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        items.append(["wire", ["pts", ["xy", x1, y1], ["xy", x2, y2]],
                      stroke(width, "dash" if dashed else "solid", color),
                      ["uuid", Q(U())]])


def junction(x, y, color=(0, 0, 0, 0)):
    items.append(["junction", ["at", x, y], ["diameter", 0],
                  ["color"] + list(color), ["uuid", Q(U())]])


def label(name, x, y, angle=0, justify="left bottom", size=1.27):
    items.append(["label", Q(name), ["at", x, y, angle],
                  effects(size, justify), ["uuid", Q(U())]])


def text(s, x, y, size=1.27, justify="left top", bold=False, color=None, angle=0):
    items.append(["text", Q(s), ["exclude_from_sim", "no"], ["at", x, y, angle],
                  effects(size, justify, bold, color=color), ["uuid", Q(U())]])


def g_rect(x1, y1, x2, y2, w=0.2, kind="solid", fk="none", fc=None, sc=None):
    items.append(["rectangle", ["start", x1, y1], ["end", x2, y2],
                  stroke(w, kind, sc), fill(fk, fc), ["uuid", Q(U())]])


def g_line(pts, w=0.2, kind="solid", sc=None):
    items.append(["polyline", ["pts"] + [["xy", x, y] for x, y in pts],
                  stroke(w, kind, sc), ["uuid", Q(U())]])


def place(lib_id, ref, value, x, y, pins, ref_at, val_at, desc="",
          ref_just=None, val_just=None, ref_size=1.27, val_size=1.27,
          ref_bold=True):
    node = ["symbol", ["lib_id", Q(lib_id)], ["at", x, y, 0], ["unit", 1],
            ["body_style", 1], ["exclude_from_sim", "no"], ["in_bom", "yes"],
            ["on_board", "no"], ["in_pos_files", "yes"], ["dnp", "no"],
            ["uuid", Q(U("sym:" + ref))]]

    def prop(key, val, at, hide=False, just=None, size=1.27, bold=False):
        p = ["property", Q(key), Q(val), ["at", at[0], at[1], 0]]
        if hide:
            p.append(["hide", "yes"])
        p += [["show_name", "no"], ["do_not_autoplace", "no"],
              effects(size, just, bold)]
        return p
    node.append(prop("Reference", ref, ref_at, just=ref_just, size=ref_size,
                     bold=ref_bold))
    node.append(prop("Value", value, val_at, just=val_just, size=val_size))
    node.append(prop("Footprint", "", (x, y), hide=True))
    node.append(prop("Datasheet", "", (x, y), hide=True))
    node.append(prop("Description", desc, (x, y), hide=True))
    for p in pins:
        node.append(["pin", Q(p), ["uuid", Q(U("pin:%s:%s" % (ref, p)))]])
    node.append(["instances", ["project", Q(PROJECT),
                                ["path", Q("/" + ROOT_UUID),
                                 ["reference", Q(ref)], ["unit", 1]]]])
    items.append(node)


C = CUSTOM_LIB + ":"

# ---- grid of the main drawing (mm, y down; all connection points on 1.27) --
Y_CHAIN = 50.8          # source chain row centre
YP, YM = 48.26, 53.34   # + and - conductors of the chain
Y_JP = 76.2             # J+ rail
Y_JM = 139.7            # J- rail
Y_MID = 107.95          # centre line of the ladder branches

X_X1, X_X2 = 45.72, 88.9
X_FEEDP, X_FEEDM = 124.46, 129.54
X_QI = 139.7
J2X, U2X = 152.4, 177.8
X_RGB = 210.82
SWX, SWY = 220.98, 91.44
X_SWV = 231.14          # SW1 -> U1 riser
X_RET = 228.6           # U1 DC- return to J-
U1X = 254.0
J3X = 289.56
HX = 314.96
FX = 330.2
NOTE = 1.27             # note text size in the drawing area
SMALL = 1.2

# ---- source chain: car outlet -> fused plug -> feed cable -------------------
VAL = 2.0               # Value text size for parts on the power path (video legibility)
place(C + "CAR_12V_OUTLET", "CAR1", "Car 12 V outlet", 30.48, Y_CHAIN,
      ["1", "2"], (26.67, 42.545), (26.67, 59.69), val_size=VAL,
      desc="Car's own 12 V outlet (factory), lower centre stack; live only with ignition on (likely)")
place(C + "FUSED_CIG_PLUG", "P1", "Fused 12 V plug", 60.96,
      Y_CHAIN, ["1", "2", "3", "4"], (60.96, 42.545), (60.96, 59.69), val_size=VAL,
      desc="Fused right-angle cigarette plug; fuse in the tip, value unknown (usually 10-15 A)")
place(C + "FEED_CABLE_2C", "W1", "Feed cable, brown/blue", 96.52, Y_CHAIN,
      ["1", "2", "3", "4"], (96.52, 43.815), (96.52, 58.42), val_size=VAL,
      desc="The plug's own lead (IMG_3488): round black two-core, brown (+) blue (-), ~0.5-0.75 mm2; "
           "enters through a clip at the driver-side notch corner (IMG_3502)")

# outlet -> plug: no photo shows the plug in an outlet (3476 held unplugged,
# 3483/3484 lying beside the empty car outlet) -> dashed
wire([(40.64, YP), (45.72, YP)], dashed=True, color=W_POS, width=WPWR)
wire([(40.64, YM), (45.72, YM)], dashed=True, color=W_NEG, width=WPWR)
# plug lead -> W1: SEEN. IMG_3488: one unbroken thick cable from the plug to the
# driver notch corner; IMG_3502/3503: it enters there through a clip and ends at
# the moulded end with the brown/blue tails -> solid
wire([(76.2, YP), (83.82, YP)], color=W_POS, width=WPWR)
wire([(76.2, YM), (83.82, YM)], color=W_NEG, width=WPWR)
label("+12V_IN", 76.835, YP)
# W1 brown -> J+ ; W1 blue -> J-  (seen). The blue riser crosses J+ (no joint).
wire([(109.22, YP), (X_FEEDP, YP), (X_FEEDP, Y_JP)], color=W_POS, width=WPWR)
wire([(109.22, YM), (X_FEEDM, YM), (X_FEEDM, Y_JM)], color=W_NEG, width=WPWR)

# ---- rails -----------------------------------------------------------------
jp = [X_X1, X_X2, X_FEEDP, X_QI, X_RGB]
for a, b in zip(jp, jp[1:]):
    wire([(a, Y_JP), (b, Y_JP)], color=W_POS, width=WPWR)
for x in (X_X2, X_FEEDP, X_QI):
    junction(x, Y_JP, W_POS)
jm = [X_X1, X_X2, X_FEEDM, X_QI, X_RET]
for a, b in zip(jm, jm[1:]):
    wire([(a, Y_JM), (b, Y_JM)], color=W_NEG, width=WPWR)
for x in (X_X2, X_FEEDM, X_QI):
    junction(x, Y_JM, W_NEG)
for x in (62.23, 170.18):
    label("J+", x, Y_JP, size=1.8)
    label("J-", x, Y_JM, size=1.8)

# ---- X1 USB socket, X2 12 V socket ----------------------------------------
place(C + "USB_PD_QC_SOCKET", "X1", "Dual USB socket", X_X1, Y_MID,
      ["1", "2"], (X_X1 + 8.89, Y_MID - 3.175), (X_X1 + 8.89, Y_MID + 0.635),
      desc="USB-C PD + USB-A QC3.0, 12/24 V, blue LED ring", ref_just="left",
      val_just="left", val_size=VAL)
wire([(X_X1, Y_JP), (X_X1, Y_MID - 12.7)], color=W_POS, width=WPWR)
wire([(X_X1, Y_MID + 12.7), (X_X1, Y_JM)], dashed=True,
     color=W_NEG, width=WPWR)                       # blue jumper to USB - *
place(C + "SOCKET_12V_ACC", "X2", "12 V socket", X_X2, Y_MID,
      ["1", "2"], (X_X2 + 8.89, Y_MID - 3.175), (X_X2 + 8.89, Y_MID + 0.635),
      desc="Cigarette-lighter type 12 V accessory socket, centre +, shell -; not a switch",
      ref_just="left", val_just="left", val_size=VAL)
wire([(X_X2, Y_JP), (X_X2, Y_MID - 12.7)], color=W_POS, width=WPWR)
wire([(X_X2, Y_MID + 12.7), (X_X2, Y_JM)], color=W_NEG, width=WPWR)

# ---- Qi pad branch ---------------------------------------------------------
place(C + "PLUG_2PIN_INLINE", "J2", "2-pin plug", J2X, Y_MID,
      ["1", "2", "3", "4"], (J2X, Y_MID - 6.985), (J2X, Y_MID + 7.62),
      desc="Small two-pin plug (JST-SM style) between panel and Qi pad")
wire([(X_QI, Y_JP), (X_QI, Y_MID - 2.54), (J2X - 7.62, Y_MID - 2.54)],
     color=W_POS, width=WPWR)
# pad - back to J-: the red/black cord is seen from the pad through J2 into the
# panel (3488, 3491, 3504), but inside, its black core cannot be told apart on the
# black felt and the joint is under heat-shrink -> still dashed *
wire([(X_QI, Y_JM), (X_QI, Y_MID + 2.54), (J2X - 7.62, Y_MID + 2.54)],
     dashed=True, color=W_NEG, width=WPWR)
place(C + "QI_PAD_12V", "U2", "Qi charger pad", U2X, Y_MID,
      ["1", "2"], (U2X + 2.54, Y_MID - 10.16), (U2X + 2.54, Y_MID + 10.16),
      desc="Qi wireless charger pad in the car's tray in front of the gear lever (IMG_3484); 12 V module",
      val_size=VAL)
wire([(J2X + 7.62, Y_MID - 2.54), (U2X - 12.7, Y_MID - 2.54)], color=W_POS, width=WPWR)
wire([(J2X + 7.62, Y_MID + 2.54), (U2X - 12.7, Y_MID + 2.54)], color=W_NEG, width=WPWR)

# ---- light circuit: SW1 -> U1 -> J3 -> H1..H3 ------------------------------
place("Switch:SW_Push", "SW1", "Silver push button, latching", SWX, SWY,
      ["1", "2"], (X_RGB + 2.54, 81.28), (X_RGB + 2.54, 85.09),
      desc="Flat stainless anti-vandal push button, ~12-16 mm; the only control; turns on the RGB lights",
      ref_just="left", val_just="left", val_size=VAL)
# SW1's own wiring is hidden in the deck: below the felt only two red wire ends
# show at the button's corner, one with a bare tinned tip (3502, 3481, 3482).
# Rev A drew these two links solid; rev B draws them dashed *
wire([(X_RGB, Y_JP), (X_RGB, SWY), (SWX - 5.08, SWY)], dashed=True,
     color=W_POS, width=WPWR)
wire([(SWX + 5.08, SWY), (X_SWV, SWY), (X_SWV, Y_MID - 2.54),
      (U1X - 20.32, Y_MID - 2.54)], dashed=True, color=W_POS, width=WPWR)   # switched +
label("SW_RGB", X_SWV, 104.14, angle=90)
wire([(U1X - 20.32, Y_MID + 2.54), (X_RET, Y_MID + 2.54), (X_RET, Y_JM)],
     color=W_NEG, width=WPWR)
place(C + "BT_RGB_CONTROLLER", "U1", "Bluetooth RGB LED controller", U1X, Y_MID,
      ["1", "2", "3", "4", "5", "6"], (U1X, Y_MID - 14.605), (U1X, Y_MID + 15.24),
      desc="Bluetooth RGB LED controller, INPUT DC 5-12V, phone app; lies on the bottom of the cup body "
           "(IMG_3502, 3481, 3482), DC plug at its rear end, LED lead at its front end",
      val_size=VAL)

place(C + "RGB_SPLITTER_1TO3", "J3", "1-to-3 splitter", J3X, Y_MID,
      [str(i) for i in range(1, 17)], (J3X, Y_MID - 37.465), (J3X, Y_MID + 37.465),
      desc="Black ribbed round in-line plugs just ahead of the cup (IMG_3502, 3481); "
           "where the cable splits three ways is hidden in the bundle")
for dy in (-7.62, -2.54, 2.54, 7.62):
    wire([(U1X + 16.51, Y_MID + dy), (J3X - 6.35, Y_MID + dy)], color=W_LED, width=WLED)

# Head order matches the improved sheet: H1/FO1 = driver (left), H2/FO2 = passenger.
# H1, H2 under the deck at the rear corners (3502); H3 loose outside (3484, 3488).
heads = [("H1", Y_MID - 25.4, "FO1", "RGB LED head: under deck, driver rear corner",
          "fibre on top of the driver arm",
          "Aluminium RGB LED head, common anode; lies under the deck at the driver-side rear corner (IMG_3502)"),
         ("H2", Y_MID, "FO2", "RGB LED head: under deck, passenger rear corner",
          "fibre on top of the passenger arm",
          "Aluminium RGB LED head, common anode; lies under the deck at the passenger-side rear corner (IMG_3502)"),
         ("H3", Y_MID + 25.4, None, "RGB LED head: loose in the car's tray",
          None,
          "Aluminium RGB LED head, common anode; loose, no fibre; lies in the car's small tray left of the gear lever (IMG_3484)")]
for ref, hy, fib, hval, fval, hdesc in heads:
    place(C + "RGB_LED_HEAD", ref, hval, HX, hy,
          ["1", "2", "3", "4"], (HX - 2.54, hy - 11.43), (HX + 2.54, hy - 11.43),
          desc=hdesc, ref_just="right",
          val_just="left", val_size=1.27)
    for dy in (-7.62, -2.54, 2.54, 7.62):
        wire([(J3X + 6.35, hy + dy), (HX - 6.35, hy + dy)], color=W_LED, width=WLED)
    if fib:
        place(C + "SIDE_GLOW_FIBRE", fib, fval,
              FX, hy, [], (FX, hy - 2.54), (FX + 5.715, hy - 2.54),
              desc="Side-glow fibre lit by the LED head (light, not electricity); runs along the top "
                   "of the side arm, in the middle of its band (IMG_3490, 3501)",
              ref_just="left bottom", val_just="left bottom", val_size=1.27)
        text("light, not wire", FX + 37.0, hy + 0.635, 1.4, "left",
             color=(120, 80, 200, 1))

text("H1 and H2 sit beneath the two rear corners.\nEach shines into a side-glow fibre along\nthe top of a side wall. H3 has no fibre;\nit lights the tray by the gear lever.\nAll three heads change colour together.",
     FX, Y_MID + 19.05, NOTE)

# ---- clock: separate, no wiring --------------------------------------------
g_rect(137.16, 40.64, 227.33, 69.85, 0.2)
text("SEPARATE: NOT WIRED", 139.065, 42.545, 1.27, bold=True)
place(C + "CLOCK_OWN_BATTERY", "CLK1", "Analog stick-on clock", 149.86, 57.15,
      [], (149.86, 50.165), (154.305, 65.405),
      desc="Analog clock with its own battery")
text("Runs on its own battery.\nIndependent of the console power supply.\nIt is not part of this circuit.",
     167.64, 52.07, NOTE)

# ---- explanatory notes in the drawing ---------------------------------------
text("Vehicle 12 V outlet at\nthe lower centre console.",
     13.97, 62.23, SMALL)
text("I connect the panel through\nthis fused 12 V plug.\nFuse rating: not recorded.",
     46.99, 62.23, SMALL)
text("The plug's two-core lead\nenters beneath the panel.\nBrown: positive.\nBlue: return.",
     81.28, 62.23, SMALL)

text("Positive junction at the\nUSB socket's + terminal.\nA jumper feeds the\n12 V socket centre.",
     12.7, 81.28, SMALL)
text("Return junction at the\n12 V socket's shell\nterminal.",
     12.7, 123.19, SMALL)

text("USB-C PD and USB-A QC3.0 socket.\nThe blue ring lights when powered.\nThe dashed return connection is\nnot visible in my photographs.",
     30.48, 143.51, NOTE)
text("12 V accessory socket:\ncentre positive, shell negative.\nThe red ring is unlit trim.",
     72.39, 143.51, NOTE)
text("A two-pin connector lets me unplug\nthe separate wireless charging pad.\nIts lead enters under the side wall.\nThe dashed return path is hidden\nin my photographs.",
     133.35, 143.51, NOTE)
text("The button latches down and keeps\nthe lights on after release.\nThe drawing places it in the + feed;\nthe actual switched conductor\nis not confirmed. Dashed routes\nare illustrative.",
     179.07, 143.51, NOTE)
text("Bluetooth controller, labelled 5-12 V.\nThe phone app sets colours and modes.\nThe controller sits beneath the cup.\nThe V+, R, G, B output arrangement\nis an assumption in this drawing.",
     236.22, 125.73, NOTE)
text("In-line connectors feed three heads.\nThe split is hidden in the bundle.\nThe drawing represents the LED\ncables as V+, R, G and B.\nAll heads change colour together.",
     279.4, 148.59, NOTE)

# ---- heading ---------------------------------------------------------------
text("INSTALLED-WIRING DOCUMENTATION", 12.7, 13.97, 3.2, bold=True)
text("Custom Aftermarket Car Center Console Upgrade", 12.7, 20.32, 2.3, bold=True)
text("I planned the circuit before construction. This October 2026 drawing documents my completed panel.\nDashed routes and the controller pin arrangement are illustrative; hidden connections are not verified.",
     12.7, 25.4, 1.4)

# ---- legend ----------------------------------------------------------------
LX, LY = 300.99, 12.7
g_rect(LX, LY, 407.67, LY + 38.1, 0.2)
text("LEGEND", LX + 2.54, LY + 2.54, 1.6, bold=True)
g_line([(LX + 2.54, LY + 9.525), (LX + 17.78, LY + 9.525)], 0.3, "solid", W_GREY)
text("solid = seen in photos", LX + 20.32, LY + 9.525, 1.4, "left")
g_line([(LX + 2.54, LY + 14.605), (LX + 17.78, LY + 14.605)], 0.3, "dash", W_GREY)
text("dashed = inferred", LX + 20.32, LY + 14.605, 1.4, "left")
g_line([(LX + 57.15, LY + 9.525), (LX + 69.85, LY + 9.525)], 0.5, "solid", W_POS)
text("red = + side", LX + 72.39, LY + 9.525, 1.4, "left", color=(170, 0, 0, 1))
g_line([(LX + 57.15, LY + 14.605), (LX + 69.85, LY + 14.605)], 0.5, "solid", W_NEG)
text("black = - side", LX + 72.39, LY + 14.605, 1.4, "left")
g_line([(LX + 2.54, LY + 19.685), (LX + 17.78, LY + 19.685)], 0.4, "solid", W_LED)
text("purple = LED cables (V+, R, G, B)", LX + 20.32, LY + 19.685, 1.4, "left")
text("Red / black / purple are drawing colours, not the real wire colours:\n"
     "W1 is really brown (+) / blue (-).",
     LX + 2.54, LY + 23.495, 1.4)
text("* or (likely) = inferred, not seen    ~ = estimate\n"
     "J+ / J- = the panel's + and - junction points",
     LX + 2.54, LY + 31.75, 1.4)

# ---- bottom notes: how it works ---------------------------------------------
BY = 170.18
BODY = 1.7
g_rect(10.16, BY, 140.97, 284.48, 0.25)
text("HOW IT WORKS (plain words)", 12.7, BY + 2.54, 2.0, bold=True)
text(
    "1. POWER. The fused cigarette plug P1 (fuse value unknown) is the panel's only\n"
    "    power input. Its own lead is the two-wire cable W1 (brown = +, blue = -), which\n"
    "    enters under the deck at the notch corner. The drawing connects P1 to the\n"
    "    car outlet; its behavior with the car switched off needs checking.\n"
    "2. J+ AND J-. Under the deck everything joins at two points: J+ (on the USB\n"
    "    socket's + tab) and J- (on the 12 V socket's shell tab). The red and black\n"
    "    branches split off in heat-shrunk joints beside the socket plate (3502).\n"
    "3. SOCKETS. The USB socket X1 and the 12 V socket X2 are wired straight across\n"
    "    J+ and J-, so they work whenever the car outlet is live.\n"
    "4. WIRELESS CHARGER. The Qi pad U2 gets 12 V through a small two-pin plug J2.\n"
    "5. LIGHTS. Press SW1: it latches down and keeps the RGB lights on after release.\n"
    "    The drawing assumes SW1 interrupts the + feed to controller U1. U1 drives\n"
    "    three RGB LED heads through the in-line plugs J3. A phone app sets the colours.\n"
    "6. FIBRES. Heads H1 and H2 sit under the deck at the rear corners and shine into\n"
    "    side-glow fibres FO1 and FO2, which run along the top of the two side arms.\n"
    "    Head H3 has no fibre and lies loose in the car's tray by the gear lever.\n"
    "7. CLOCK. It has its own battery and no wires.\n"
    "8. CURRENT AT 12 V (approx.): USB up to 4-4.5 A, Qi pad 1.5-2 A, lights 0.5-1 A.\n"
    "    About 7 A in total, before anything is plugged into the 12 V socket X2.\n"
    "9. PROTECTION. Only the fuse in the plug tip and the car's own outlet fuse.",
    12.7, BY + 8.255, BODY)
text("CONNECTIONS AND RATINGS TO VERIFY", 12.7, BY + 66.04, 1.8, bold=True)
text(
    "-  The fuse value printed in the plug tip.\n"
    "-  Whether the car's outlet stays live with the car fully off.\n"
    "-  Continuity from plug P1 through cable W1 to the supply junctions.\n"
    "-  The button terminal routing and which wire it breaks (+ assumed in this drawing).\n"
    "-  The return route of the Qi pad's - wire, and of the USB socket's - tab.\n"
    "-  Whether the red and black wires in one connector (IMG_3422) share a circuit.\n"
    "-  What the small black cylinder with holes is, on a cable beside the slot bar (3502).",
    12.7, BY + 71.12, BODY)

# ---- bottom notes: faults ---------------------------------------------------
FX0 = 144.78
FAULT = 1.75
g_rect(FX0, BY, 297.18, 284.48, 0.35, "solid", "color", (255, 240, 235, 1),
       (200, 0, 0, 1))
text("ITEMS REQUIRING PHYSICAL INSPECTION", FX0 + 2.54, BY + 2.54, 2.0, bold=True,
     color=(170, 0, 0, 1))
text(
    "These observations identify checks to make on the real wiring; photographs cannot verify continuity.\n"
    "\n"
    "WIRING AND CONNECTORS\n"
    "-  A red and a black wire share one lilac connector (IMG_3422): the colour code is broken.\n"
    "-  Two connectors on the 12 V socket's centre terminal (3482); one may sit on the stud (poor contact).\n"
    "-  One yellow connector on the USB socket body has no visible wire.\n"
    "-  Red wire ends at the button corner, one with a bare tip (IMG_3445, 3502): live if not in the button.\n"
    "-  Oversized blue connectors crimped on thin wire; some barrels hold two wires.\n"
    "\n"
    "FUSE AND CABLE SIZES\n"
    "-  Verify the installed fuse value and actual conductor sizes.\n"
    "-  Check protection against the ratings of every conductor, connector and load.\n"
    "-  Wire sizes estimated from photographs are not sufficient for this check.\n"
    "\n"
    "SAFETY AND PLACEMENT\n"
    "-  Bare 12 V centre stud and brass nut: a short if they touch the seat-belt buckle\n"
    "    (car earth) when the panel is turned over on the seat.\n"
    "-  Cables and the loose LED head lie across the EV MODE, drive-mode and EPB/HOLD\n"
    "    switches and the gear gate (3484); others run near the seat rails and buckle.\n"
    "-  Check that the wings do not block the seat-belt buckles or seat adjustment.\n"
    "-  If the outlet is live all the time, standby draw (controller, USB ring, Qi pad)\n"
    "    slowly drains the car's small 12 V battery.\n"
    "\n"
    "A proposed protection revision is on a separate sheet. It is not installed or validated.",
    FX0 + 2.54, BY + 8.255, FAULT)

# ---- bottom right: note on the drawing --------------------------------------
g_rect(300.99, BY, 407.67, 228.6, 0.25)
text("ABOUT THIS DRAWING", 303.53, BY + 2.54, 2.0, bold=True)
text(
    "I designed the panel in 3D and\n"
    "planned its circuit before fabrication.\n"
    "Then I cut, covered and wired it.\n"
    "Photos document the completed panel\n"
    "and help verify this illustration.\n"
    "\n"
    "This is a present-day explanatory\n"
    "drawing of the completed panel.\n"
    "Use it with the physical photographs.\n"
    "Dashed lines mark connections hidden\n"
    "in the evidence; values approximate.\n"
    "Parts without library symbols are\n"
    "shown as labelled boxes.",
    303.53, BY + 8.255, 1.85)

# ---------------------------------------------------------------- write -----

title_block = ["title_block",
               ["title", Q("Custom Aftermarket Car Center Console Upgrade - As-built")],
               ["date", Q("2026-10-03")],
               ["rev", Q("B")],
               ["company", Q("Console design and build documentation")],
               ["comment", 1, Q("Date drawn: 2026-10-03")],
               ["comment", 2, Q("Installed-wiring documentation; hidden connections are inferred")],
               ["comment", 3, Q("Solid wire = seen in photos, dashed wire = inferred; values approximate")],
               ["comment", 4, Q("Removable console panel; drawing documents the completed build")]]

lib_blocks = [extract_lib_symbol("Switch", "SW_Push")]
lib_blocks += [ser(s, 2) for s in customs]

parts = []
parts.append("(kicad_sch")
parts.append("\t(version 20260101)")
parts.append('\t(generator "console_circuit_builder")')
parts.append('\t(generator_version "1.0")')
parts.append('\t(uuid "%s")' % ROOT_UUID)
parts.append('\t(paper "A3")')
parts.append(ser(title_block, 1))
parts.append("\t(lib_symbols\n" + "\n".join(lib_blocks) + "\n\t)")
for it in items:
    parts.append(ser(it, 1))
parts.append(ser(["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], 1))
parts.append("\t(embedded_fonts no)")
parts.append(")")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(parts) + "\n")
print("wrote", OUT)

# ------------------------------------------- project symbol library + table --
# The schematic embeds every symbol, so it opens anywhere. The library file and
# table below also let KiCad's ERC find the custom symbols ("lib_symbol_issues").
LIBFILE = os.path.join(HERE, CUSTOM_LIB + ".kicad_sym")
lib_parts = ["(kicad_symbol_lib", "\t(version 20251024)",
             '\t(generator "console_circuit_builder")', '\t(generator_version "1.0")']
for sdef in customs:
    bare = list(sdef)
    bare[1] = Q(sdef[1].split(":", 1)[1])
    lib_parts.append(ser(bare, 1))
lib_parts.append(")")
with open(LIBFILE, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lib_parts) + "\n")

TABLE = os.path.join(HERE, "sym-lib-table")
entry = ('\t(lib (name "%s") (type "KiCad") (uri "${KIPRJMOD}/%s.kicad_sym") '
         '(options "") (descr "Custom symbols for the installed-wiring schematic"))'
         % (CUSTOM_LIB, CUSTOM_LIB))
if os.path.exists(TABLE):
    tbl = open(TABLE, encoding="utf-8").read()
    if '(name "%s")' % CUSTOM_LIB not in tbl:
        tbl = tbl.rstrip().rstrip(")").rstrip() + "\n" + entry + "\n)\n"
        open(TABLE, "w", encoding="utf-8").write(tbl)
else:
    open(TABLE, "w", encoding="utf-8").write(
        "(sym_lib_table\n\t(version 7)\n" + entry + "\n)\n")
print("wrote", LIBFILE, "and", TABLE)

# Minimal project file: lets KiCad/kicad-cli load ./sym-lib-table and draws
# hop-overs where the blue W1 return crosses the J+ rail (no joint there).
PRO = os.path.join(HERE, PROJECT + ".kicad_pro")
with open(PRO, "w", encoding="utf-8") as fh:
    fh.write('{\n  "meta": {\n    "filename": "%s.kicad_pro",\n    "version": 3\n  },\n'
             '  "schematic": {\n    "drawing": {\n      "hop_over_size_choice": 2\n    }\n  }\n}\n'
             % PROJECT)
print("wrote", PRO)
