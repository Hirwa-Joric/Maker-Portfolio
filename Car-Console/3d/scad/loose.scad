// This file defines a later explanatory model; photo/scan tags check it against the finished panel.
// =====================================================================================================
// loose.scad -- lights, loose items and underside hardware for the
//   "Custom Aftermarket Car Center Console Upgrade" — completed-build model
//   (Explanatory assembly model; dimensions approximate).
//
// Every part is modelled IN ITS FINAL POSITION in the shared frame of params.scad : mm, origin =
// middle of the notch's back edge at deck-top level (the stitch crease), +x passenger, +y rear, z up,
// deck top z = 0. The frame is LEFT-handed; assemble.py flips y for photo-true renders (a right-handed
// viewer of the raw STLs shows everything mirrored, exactly like the other part files).
//
// Export one part at a time (binary STL):
//   openscad --backend manifold --export-format binstl -o head_l.stl -D 'part="head_l"' loose.scad
// part =
//   LIGHTS   "head_l" (driver, -x) | "head_r" (passenger, +x) | "head_loose" (third head, in the car's tray)
//            "head_boots"  black cable boots + short cable stubs of all three heads
//            "lead_loose"  the third head's thin lead (with its ribbed in-line connector) to the notch clip
//            "fibre_l" | "fibre_r"  clear side-glow fibre (round core + flat fin), head -> under the deck ->
//                                   loop up in the rear corner -> along the middle of the band top
//   QI PAD   "qi_frame" (leatherette body) | "qi_chrome" (edge strip) | "qi_insert" (matte black panel)
//            "qi_icon" (white printed wireless symbol, generic) | "qi_led" (two small dots) | "qi_screw"
//            "qi_cable_red" | "qi_cable_black" (bonded zip cord to the panel; the black part also carries
//                                               the pad grommet and the 2-pin in-line connector)
//   POWER    "plug" (fused right-angle cigarette plug) | "plug_lead" (its round black lead = feed W1,
//                                               from the plug to the moulded end under the deck)
//   UNDER    "ctrl" (LED controller on the cup's outer bottom, with its DC plug and strain relief)
//            "ctrl_leads" (its two leads, routes from params; OPTIONAL, see notes) | "bar" (metal bar)
//   PREVIEW  "all" (coloured, model frame) | "all_photo" (the same mirrored in y = as photographed)
//            "lights" | "qi" | "power" | "under"  (coloured groups, previews only)
//
// Sources (GEOMETRY.md sections 8-11; tags as in params.scad):
//   [S] scan (qi_pad_scan.stl / plug_scan.stl / panel scan), [T] tape, [P] photographs 3483-3504,
//   [I] inferred. SEEN = visible in the named photo; INFERRED = a modelling choice, not seen.
//   Heads: 3502 (both under-deck heads, grooves, boots), 3491/3483/3501 (the loose third head).
//   Fibres: 3501/3490 (round clear core in the band's seam, tapered front end, no fin visible on top),
//           3502 (flat clear fin under the deck, P-clips), path tables from params.scad.
//   Qi pad: 3491 rectified through the fitted camera (outline, inset panel, dots, screw, icon, cable exit),
//           3486/3501 (chrome strip low on the side, rounded leatherette top edge, screw post), scan size.
//   Plug: 3491 (zoom: tip, barrel, spring contacts, chrome collar, head, ribbed exit), 3484 (in the tray),
//           scan 70 x 40 x 31.
//   Controller: 3502 (box, ribbed short ends, corner ear, DC barrel plug + ribbed boot, strain relief).
//   Bar: 3502/3503 (flat worn-grey bar, small corner radius, two empty holes).
// No brand marks: the controller's label/QR code and the plug's printing are not modelled; the wireless
// symbol is a generic bolt-and-arcs charging icon.
//
// params.scad is shared and read-only: values used only here are defined below with a comment.
//
// Exports are written to 3d/stl/; assembled views are rendered into 3d/renders/.
// "bar" is ALSO modelled by fittings.scad (same params, corner radius 4 there, 3 here from 3503); only one
// bar.stl should be assembled -- 3d/stl/bar.stl comes from fittings.scad.
//
// Fitted poses are defined below from IMG_3483: Qi-pad yaw -19.6 degrees, tilt 20.1 degrees,
// top centre z -64.3; third head at (-70.8, -75.4, -60.9); plug tip at (44, -281, -50).
// Fibre waypoints keep the rear loops clear of the deck.
// four head grooves (3485/3502); driver head moved and its cable stub turned toward
// +x so nothing shows through the slot; the third head's lead ends beside the pocket block, outside the slot's
// opening; fibres end per side (params fibre_top_pts); the Qi cord's 2-pin connector slid ~43 mm along the cord so
// it lies over the NORMAL/SPORT buttons as in 3483.
// =====================================================================================================

include <params.scad>

part = "all";

// =====================================================================================================
// 0. helpers
// =====================================================================================================
eps = 0.01;
function unit(v) = v / norm(v);
function clamp01(t) = min(max(t, 0), 1);
function smooth01(t) = let (u = clamp01(t)) u * u * (3 - 2 * u);
function cumlen(P) = [for (i = 0, s = 0; i < len(P);
                           s = s + (i < len(P) - 1 ? norm(P[i + 1] - P[i]) : 0), i = i + 1) s];
// centripetal Catmull-Rom through the control points (passes through every point, no overshoot loops)
function _kn(a, b, t) = t + pow(max(norm(b - a), 1e-4), 0.5);
function cr_seg(p0, p1, p2, p3, n) =
    let (t0 = 0, t1 = _kn(p0, p1, t0), t2 = _kn(p1, p2, t1), t3 = _kn(p2, p3, t2))
    [for (i = [0 : n - 1]) let (u = t1 + (t2 - t1) * i / n,
        A1 = ((t1 - u) * p0 + (u - t0) * p1) / (t1 - t0),
        A2 = ((t2 - u) * p1 + (u - t1) * p2) / (t2 - t1),
        A3 = ((t3 - u) * p2 + (u - t2) * p3) / (t3 - t2),
        B1 = ((t2 - u) * A1 + (u - t0) * A2) / (t2 - t0),
        B2 = ((t3 - u) * A2 + (u - t1) * A3) / (t3 - t1))
        ((t2 - u) * B1 + (u - t1) * B2) / (t2 - t1)];
function spline(P, step = 2) =
    let (n = len(P), Q = concat([2 * P[0] - P[1]], P, [2 * P[n - 1] - P[n - 2]]))
    concat([for (i = [0 : n - 2])
               each cr_seg(Q[i], Q[i + 1], Q[i + 2], Q[i + 3], max(1, ceil(norm(P[i + 1] - P[i]) / step)))],
           [P[n - 1]]);
// point and unit tangent at arc length s along a sampled path
function at_len(P, L, s) =
    let (k = max([for (i = [0 : len(P) - 2]) if (L[i] <= s) i]), f = (s - L[k]) / max(L[k + 1] - L[k], 1e-6))
    [P[k] + f * (P[k + 1] - P[k]), unit(P[k + 1] - P[k])];
function circle2(r, n) = [for (i = [0 : n - 1]) let (a = 360 * i / n) [r * cos(a), r * sin(a)]];

// Generic sweep: closed tube with end caps. P = path points, Dref = per-point reference direction for
// the profile's first axis (made perpendicular to the tangent), profs = per-point 2D profiles (CCW, same
// point count). Faces follow OpenSCAD's convention (clockwise seen from outside).
module sweep(P, Dref, profs) {
    n = len(P);
    m = len(profs[0]);
    T = [for (i = [0 : n - 1]) unit(P[min(i + 1, n - 1)] - P[max(i - 1, 0)])];
    D = [for (i = [0 : n - 1]) unit(Dref[i] - (Dref[i] * T[i]) * T[i])];
    B = [for (i = [0 : n - 1]) cross(T[i], D[i])];
    pts = [for (i = [0 : n - 1]) for (q = profs[i]) P[i] + q[0] * D[i] + q[1] * B[i]];
    faces = concat(
        [[for (j = [0 : m - 1]) j]],
        [[for (j = [m - 1 : -1 : 0]) (n - 1) * m + j]],
        [for (i = [0 : n - 2]) for (j = [0 : m - 1]) let (j2 = (j + 1) % m)
            [i * m + j, (i + 1) * m + j, (i + 1) * m + j2, i * m + j2]]);
    polyhedron(points = pts, faces = faces, convexity = 10);
}
// round cable of diameter d along smoothed control points (reference "up" keeps the seam on top)
module cable(ctrl, d, step = 2, nseg = 14) {
    P = spline(ctrl, step);
    sweep(P, [for (p = P) [0, 0, 1]], [for (p = P) circle2(d / 2, nseg)]);
}
// local +z -> unit direction ax, then move to c
module orient(c, ax) {
    translate(c) rotate([0, 0, atan2(ax[1], ax[0])]) rotate([0, acos(max(-1, min(1, ax[2]))), 0]) children();
}
// ribbed strain relief along local +z from z = 0: r0 at the root to r1 at the end, nr ribs
module ribbed(len_, r0, r1, nr, rib = 0.6) {
    cylinder(r1 = r0, r2 = r1, h = len_, $fn = 32);
    for (i = [0 : nr - 1]) let (z = len_ * (i + 0.5) / nr, r = r0 + (r1 - r0) * z / len_)
        translate([0, 0, z - 0.6]) cylinder(r = r + rib, h = 1.2, $fn = 32);
}

// =====================================================================================================
// 1. ALUMINIUM LED HEADS  (params: led_head_d 13, led_head_l 31, led_head_boot 3, led_head_grooves 3,
//    led_head_open_d 5.5; poses head_P_c/_axis, head_D_c/_axis, head_loose_c/_axis)
// =====================================================================================================
head_ch        = 0.6;    // end chamfers                                             [P] 3502 (turned edges) ~0.5-1
head_groove_w  = 1.2;    // turned groove width                                      [P] 3502/3491 1-1.5
head_groove_d  = 0.7;    // groove depth                                             [I] 0.5-1
head_groove_z0 = 2.2;    // first groove from the rear (cable) face; pitch below     [P] 3491: grooves fill the rear ~third
head_groove_p  = 2.6;    //   -> 4 grooves at 2.2 / 4.8 / 7.4 / 10.0 (rear ~36 %)     [P] 3485 full res, 3502 
head_open_depth= 6;      // depth of the fibre entry in the nose                     [I]
head_cable_d   = third_lead_d;   // cable at the boot (same thin lead on all three)  [P] 3502/3491 ~3
head_stub      = 4;      // cable stub left on the under-deck heads (the LED branches continue it) [I]

// Third head, as fitted: params' head_loose_c (-63, -43, -40) +-15 projects 140 px off the head in IMG_3483.
// Re-measured there through Cam 3483: centre pixel (676, 2143) and apparent size 5.9 px/mm (length 182 px,
// diameter 78 px) -> camera depth 476 (457-495) -> (-70.8, -75.4, -60.9): lying on the X-mat at the left wall
// of the cubby, nose toward -x (axis from the image: (-1, -0.02, -0.07) ~ params' (-1, 0, 0)). [P] 3483;
// range y -67..-85, z -43..-79 from the size uncertainty.
head_loose_pos = [-70.8, -75.4, -60.9];
function head_ax(which) = unit(which == "r" ? head_P_axis : which == "l" ? head_D_axis : head_loose_axis);
function head_c(which)  = which == "r" ? head_P_c : which == "l" ? head_D_c : head_loose_pos;
function head_nose(which) = head_c(which) + head_ax(which) * led_head_l / 2;
function head_rear(which) = head_c(which) - head_ax(which) * led_head_l / 2;
function head_boot_end(which) = head_rear(which) - head_ax(which) * led_head_boot;

module led_head_local() {      // axis +z, rear (cable) face at z = 0, nose at z = led_head_l
    R = led_head_d / 2; Lh = led_head_l;
    prof = concat(
        [[0, 0], [R - head_ch, 0], [R, head_ch]],
        [for (k = [0 : led_head_grooves - 1]) let (z0 = head_groove_z0 + k * head_groove_p) each [
            [R, z0], [R - head_groove_d, z0 + 0.25], [R - head_groove_d, z0 + head_groove_w - 0.25],
            [R, z0 + head_groove_w]]],
        [[R, Lh - head_ch], [R - head_ch, Lh], [0, Lh]]);
    difference() {
        rotate_extrude($fn = 72) polygon(prof);
        translate([0, 0, Lh - head_open_depth]) cylinder(d = led_head_open_d, h = head_open_depth + 1, $fn = 40);
        translate([0, 0, Lh - 0.5]) cylinder(d1 = led_head_open_d, d2 = led_head_open_d + 1.2, h = 0.51, $fn = 40);
        translate([0, 0, -1]) cylinder(d = head_cable_d + 0.4, h = 3, $fn = 24);     // cable entry
    }
}
module head(which) { orient(head_rear(which), head_ax(which)) led_head_local(); }

// black boot on the rear face (+ short cable stub), local -z from the rear face
module boot_local(stub) {
    translate([0, 0, -led_head_boot]) cylinder(r1 = head_cable_d / 2 + 0.9, r2 = led_head_d / 2 - 2.6,
                                               h = led_head_boot + 0.2, $fn = 36);   // 0.2 into the rear face
    if (stub > 0) translate([0, 0, -led_head_boot - stub]) cylinder(d = head_cable_d, h = stub + 0.2, $fn = 24);
}
// driver head: its cable leaves the boot toward +x (a stub along the axis pointed forward into the
// slot pocket's opening and showed through the slot); assemble.py's LED_D branch starts at head_stub_end_l
head_stub_dir_l = [1, 0, 0];
function head_stub_end_l() = head_boot_end("l") + head_stub_dir_l * head_stub;
module head_boots() {
    orient(head_rear("r"), head_ax("r")) boot_local(head_stub);
    orient(head_rear("l"), head_ax("l")) boot_local(0);
    hull() {                                                          // short bend out of the boot
        translate(head_boot_end("l") + head_ax("l") * 0.4) sphere(d = head_cable_d, $fn = 20);
        translate(head_boot_end("l") - head_ax("l") * 0.8 + head_stub_dir_l * 1.2) sphere(d = head_cable_d, $fn = 20);
    }
    hull() {
        translate(head_boot_end("l") - head_ax("l") * 0.8 + head_stub_dir_l * 1.2) sphere(d = head_cable_d, $fn = 20);
        translate(head_stub_end_l()) sphere(d = head_cable_d, $fn = 20);
    }
    orient(head_rear("loose"), head_ax("loose")) boot_local(0.5);   // lead_loose continues from here
}

// third head's lead: boot end -> out of the tray cubby -> across the shift panel's rear row -> P-clip at
// the driver notch corner (wclip_notch) -> under the deck to the connector area near the bar's front end.
// Route INFERRED from 3483 (lead leaves the grooved end up and toward +x, climbs out of the cubby toward the
// notch's driver corner) and GEOMETRY section 9 (same clip as W1, connector area near the bar's front).
lead_loose_pts = [head_boot_end("loose"), [-46, -74.5, -60.3], [-40, -70, -53], [-37, -62, -41], [-40, -50, -30.5],
                  [-45, -38, -23.5], [-52, -28, -15.5], [-64, -18, -13.6], [-77, -11.5, -13.5],
                  [-89, -5.5, -14], wclip_notch, [-91, 14, -14], [-82, 34, -14.3], [-71, 45.5, -14.7],
                  [-57, 50, -15]];   // ends beside cylinder B26, in front of the pocket block (it used
                                     //   to end at (-67, 62), inside the slot's opening, and showed through the slot)
lead_conn_back = 40;     // ribbed in-line connector this far (centre) before the clip  [P] 3483 "30-50 outside the clip"
lead_conn      = [7, 22];   // its diameter and length                              [P] 3502/3503 ribbed connectors ~7 x 20-25
module lead_loose() {
    P = spline(lead_loose_pts, 2);
    L = cumlen(P);
    sweep(P, [for (p = P) [0, 0, 1]], [for (p = P) circle2(third_lead_d / 2, 14)]);
    kc = [for (i = [0 : len(P) - 1]) if (norm(P[i] - wclip_notch) < 0.01) i];
    sc = L[len(kc) > 0 ? kc[0] : len(P) - 1] - lead_conn_back;
    q = at_len(P, L, sc);
    orient(q[0] - q[1] * lead_conn[1] / 2, q[1]) inline_conn(lead_conn[0], lead_conn[1]);
}
// mated ribbed in-line connector (two halves, ribbed sleeves at both ends), local +z
module inline_conn(d, l) {
    cylinder(d = d - 1.6, h = l, $fn = 28);
    translate([0, 0, l * 0.22]) cylinder(d = d, h = l * 0.56, $fn = 32);
    for (k = [0 : 2]) {
        translate([0, 0, 1 + k * 1.6]) cylinder(d = d - 0.6, h = 0.9, $fn = 28);
        translate([0, 0, l - 1.9 - k * 1.6]) cylinder(d = d - 0.6, h = 0.9, $fn = 28);
    }
}

// =====================================================================================================
// 2. SIDE-GLOW FIBRES  (params: fibre_core_d 3.5, fibre_fin [4, 0.8], fibre_P_under / fibre_D_under,
//    fibre_top_pts(side), fibre_end_y, fibre_climb_y)
// =====================================================================================================
fib_insert   = 3.5;   // fibre pushed this far into the head's nose opening              [I]
fib_step     = 2;     // sampling step along the path                                   (model detail)
fib_core_n   = 18;    // facets round the core                                          (model detail)
fib_fin_ramp = 6;     // the fin grows to full width over this length after the nose    [P] 3502 (flat ribbon right at the nose)
fib_fin_min  = 0.3;   // fin stub left inside the head (keeps the sweep non-degenerate) (model detail)
fib_taper    = 10;    // front end: tapers over the last 10 mm ...                      [P] 3501/3490 (pointed end)
fib_taper_to = 0.35;  //   ... to 35 % of the section                                   [P]
fib_twist    = 20;    // on the band the fin turns from flat (under-deck) to pointing DOWN into the
                      //   seam over the first 20 mm forward of fibre_climb_y           [I] (fin not visible on top: 3501/3490)
// Under the deck the fin lies flat (horizontal) and points INBOARD [I]: 3502 shows the flat fin but not
// which side; inboard keeps it clear of the wall's inner face in the rear corner (outboard would cut
// 0.75 into the wall at y 238-247).
// Rear-corner waypoint [I]: params' point 5 of the under-deck run ((+-99.5, 244, -8)) is replaced by two
// waypoints, (x, fib_corner_y0, -13.3) and (x, fib_corner_y1, -8.6), so the loop stays under the felt to the
// board's rear end (deck_board_outline_r ends at y 242 under the rim) and turns up only behind it. With the
// params point the swept core cut 2.4-3.9 mm into the board's rear corner. Shift <= 1.6 mm.
fib_corner_y0 = 242;
fib_corner_y1 = 245.6;
function fibre_under(side) =
    let (u = side > 0 ? fibre_P_under : fibre_D_under)
    concat([for (i = [0 : 3]) u[i]], [[u[3][0], fib_corner_y0, -13.3], [u[4][0], fib_corner_y1, -8.6]],
           [for (i = [5 : len(u) - 1]) u[i]]);
function fibre_ctrl(side) =
    let (w = side > 0 ? "r" : "l")
    concat([head_nose(w) - head_ax(w) * fib_insert], fibre_under(side), fibre_top_pts(side));
function fibre_prof(sc, fin_len) =
    let (r = fibre_core_d / 2 * sc, h = fibre_fin[1] / 2 * sc, a0 = asin(h / r),
         Lf = r + max(fib_fin_min, fin_len * sc))
    concat([for (i = [0 : fib_core_n]) let (a = a0 + (360 - 2 * a0) * i / fib_core_n) [r * cos(a), r * sin(a)]],
           [[Lf, -h], [Lf, h]]);
module fibre(side) {
    P = spline(fibre_ctrl(side), fib_step);
    L = cumlen(P);
    Lt = L[len(L) - 1];
    Wd = [for (p = P) (p[2] > 8.5 && p[1] < fibre_climb_y + 0.5) ? smooth01((fibre_climb_y - p[1]) / fib_twist) : 0];
    Dref = [for (i = [0 : len(P) - 1]) (1 - Wd[i]) * [-side, 0, 0] + Wd[i] * [0, 0, -1]];
    profs = [for (i = [0 : len(P) - 1])
        fibre_prof(1 - (1 - fib_taper_to) * smooth01((L[i] - (Lt - fib_taper)) / fib_taper),
                   fibre_fin[0] * smooth01((L[i] - fib_insert) / fib_fin_ramp))];
    sweep(P, Dref, profs);
}

// =====================================================================================================
// 3. QI PAD  (params: qi_size [174, 121, 15], qi_corner_r 15)
//    Pad-local frame: u along the long side, v along the short side, w up from the pad's bottom face.
//    Shape from IMG_3491 rectified onto the pad's top plane through the fitted camera (6 px/mm) [P],
//    side layers from 3486/3501 [P], footprint and thickness from the scan [S].
// =====================================================================================================
// FITTED POSE in the car's tray ahead of the gear lever. GEOMETRY section 11.4 gives centre (10, -213),
// top z -44 (-14..-70 over all camera tilts), long side across x, "about 12 deg front lower, low confidence".
// Re-fitted here on IMG_3483 through Cam 3483 by matching the visible icon strokes (three left arcs + bolt,
// known sizes from the 3491 rectification): rms 2.3-2.4 px. Yaw and tilt are robust (-18.5..-21 deg, 16..23 deg
// front lower at every depth); the depth is weak (best at icon top z -75; within 0.35 px for -62..-95; 3.3 px at -44).
// Chosen: the photo solution at the depth nearest section 11 (icon top z -65). The pad then lies wedged
// diagonally: rear-left corner up at the tray's rear rim (top corner ~(-51, -143, -35)), front-right corner down
// at the front wall (~(72, -305, -94); section 11 puts the wall at y -300, -285..-330). NOTE for the car context: section 11's flat tray floor at z -60 must drop toward the front
// wall (~ -100) or the pad intersects it. [P] 3483; INFERRED that it rests on the rim / floor.
qi_top_c    = [10.6, -224.3, -64.3];   // centre of the pad's TOP face (model mm)
qi_rot      = -19.6;       // yaw: pad-local u axis turned this far (passenger end forward); 0 = long side along x
qi_tilt     = 20.1;        // front edge lower by this angle (rotation about x)
// pad orientation: screw, cable exit and edge dip on the REAR (+v) long edge / driver (-u) end, as 3415 (old,
// in the car: screw at the rear edge, driver half) and 3491/3486 (cable exit on the screw's short end) [P].
// SHAPE (pad-local mm) [P] 3491 rectified unless stated
qi_dip_c    = 44;          // shallow concave dip in the rear long edge, centred here along u ...
qi_dip_len  = 45;          //   ... over this length ...                                   (40-50)
qi_dip_d    = 3.5;         //   ... this deep (old 3417/3438 read 7-11; the new view gives 3-4)  (3-5)
qi_base_s   = 0.4;         // body side stands this far inside the footprint (chrome strip = footprint)
qi_chrome_w = [2.6, 4.4];  // chrome strip, low on the side: w from / to                  [P] 3486/3501 (thin bright line ~1/4 up)
qi_edge_r   = 3;           // leatherette rolled over the top edge                         [P] 3486 (~2-4)
qi_ins_c    = [2.6, -1.9]; // matte black inset panel centre ...                           [P] 3491 rect: u -74..79.2, v -43.3..39.5
qi_ins_size = [153.5, 83];  //   ... size ...
qi_ins_r    = 1.5;         //   ... nearly square corners ...                              [P]
qi_ins_t    = 1.5;         //   ... thickness ...                                          [I]
qi_ins_drop = 1;           //   ... top this far below the frame top                       [P] 3486 (small step) [I]
qi_fit      = 0.05;        // hair gap round the insert                                    (model detail)
qi_dots     = [[52.5, -6.7, 0], [-50.5, -45.6, 1]];   // two small white dots [u, v, on frame?]: one on the inset
                            //   right of the icon, one on the frame just off the inset's corner [P] 3491 rect; 3486 the same pair
qi_dot_d    = 2;           //                                                              [P] ~2
qi_screw_p  = [-43.7, 42.5];  // silver screw post on the rear frame band, driver end        [P] 3491 rect; 3486; 3415 (old)
qi_screw_d  = 6.5;         //                                                              [P] 3491 ~6.5-8 incl. glare
qi_screw_h  = 4.5;         // stands this far above the frame top                          [P] 3486 (short post) [S] max 5-7 above the top (noisy)
qi_icon_t   = 0.15;        // printed decal thickness                                      [I]
qi_icon_c   = [2.2, -1.45];// icon centre (bolt and arc centres)                           [P] 3491 rect
qi_arc_r    = [18.3, 27.6, 36.9];  // arc centre-line radii, each side of the bolt         [P] 3491 rect: outer edges 19.75 / 29.05 / 38.3
qi_arc_half = [29, 32, 33];//   half-angles about the long axis (from stroke heights and areas) [P] 3491 rect
qi_arc_w    = 2.9;         //   stroke                                                     [P] 3491 rect (stroke areas)
qi_bolt     = [[3.9, 16.4], [-7.1, -0.9], [-0.75, -0.2], [-3.9, -16.4], [7.1, 0.9], [0.75, 0.2]];
                           // lightning bolt 32.7 x 14.2, given as (u, up = -v); point-symmetric [P] 3491 rect
qi_exit     = [-qi_size[0] / 2, 8, 7];   // zip cord leaves the screw end of the pad here (u, v, w) [P] 3491 rect, 3486
qi_grommet  = [5, 5];      // its black grommet: diameter, length                          [P] 3486 (small, dark)
qi_wire_d   = 1.6;         // bonded red/black zip cord, 2 x 1.6 (from GEOMETRY section 9)
qi_conn_at  = 128;         // 2-pin in-line connector this far along the cord from the pad: centre ~(-40, -94),
                           //   over the NORMAL/SPORT buttons as SEEN in 3483 (was 85, which put it
                           //   ~35 toward the driver and ~25 forward). 3491 on the table reads ~80-85 from the pad
                           //   along a different (table) route, so the in-car value is set from 3483 [P] +-15
qi_conn     = [25, 7, 5];  // its length, width, height (20-30 long)                        [P] 3491/3483
// cord route in the car, pad -> beside its driver end -> over the tray's rear rim -> across the shift panel (driver
// half; the connector lies there, 3483) -> down to the notch's back edge -> behind the gear boot -> up the
// boot's passenger side -> under the passenger lining to the end of params' qi_lead (97, -100, -20).
// INFERRED from 3483 (both red/black runs: driver side with the connector, passenger side of the boot), +-20.
qi_cord_mid = [[-85, -180, -60], [-88, -165, -42], [-84, -152, -31], [-72, -140, -30.5],
               [-52, -112, -29], [-31, -80, -24], [-11, -40, -18], [4, -15, -13.5], [32, -11, -15],
               [62, -13, -19], [86, -32, -29], [94, -70, -33], [96, -97, -33]];

function qi_xform_pt(q) =         // pad-local (u, v, w) -> model, same transform as qi_place()
    let (a = qi_rot, t = qi_tilt, u = q[0] * cos(a) - q[1] * sin(a), v = q[0] * sin(a) + q[1] * cos(a), w = q[2] - qi_size[2])
    qi_top_c + [u, v * cos(t) - w * sin(t), v * sin(t) + w * cos(t)];
function qi_top_z_at(y) = qi_top_c[2] + tan(qi_tilt) * (y - qi_top_c[1]);   // the pad's top plane (tilt is about x)
module qi_place() { translate(qi_top_c) rotate([qi_tilt, 0, 0]) rotate([0, 0, qi_rot]) translate([0, 0, -qi_size[2]]) children(); }
function qi_dip(u) = abs(u - qi_dip_c) < qi_dip_len / 2 ? qi_dip_d * 0.5 * (1 + cos(360 * (u - qi_dip_c) / qi_dip_len)) : 0;
// pad outline inset by s (CCW in u, v); same point count for every s (needed by the loft)
function qi_outline(s = 0) =
    let (A = qi_size[0] / 2 - s, Bh = qi_size[1] / 2 - s, rc = qi_corner_r - s, Ns = 12, Nc = 10, Nl = 48)
    concat(
        [for (k = [0 : Ns - 1]) [A, -Bh + rc + (2 * Bh - 2 * rc) * k / Ns]],
        [for (k = [0 : Nc - 1]) let (a = 90 * k / Nc) [A - rc + rc * cos(a), Bh - rc + rc * sin(a)]],
        [for (k = [0 : Nl - 1]) let (u = (A - rc) - (2 * A - 2 * rc) * k / Nl) [u, Bh - qi_dip(u)]],
        [for (k = [0 : Nc - 1]) let (a = 90 + 90 * k / Nc) [-A + rc + rc * cos(a), Bh - rc + rc * sin(a)]],
        [for (k = [0 : Ns - 1]) [-A, Bh - rc - (2 * Bh - 2 * rc) * k / Ns]],
        [for (k = [0 : Nc - 1]) let (a = 180 + 90 * k / Nc) [-A + rc + rc * cos(a), -Bh + rc + rc * sin(a)]],
        [for (k = [0 : Nl - 1]) [-A + rc + (2 * A - 2 * rc) * k / Nl, -Bh]],
        [for (k = [0 : Nc - 1]) let (a = 270 + 90 * k / Nc) [A - rc + rc * cos(a), -Bh + rc + rc * sin(a)]]);
// loft through inset outlines; layers = [[w, s], ...] bottom to top
module qi_loft(layers) {
    O = [for (L = layers) qi_outline(L[1])];
    sweep([for (L = layers) [0, 0, L[0]]], [for (L = layers) [1, 0, 0]], O);
}
module rrect(size, r) { offset(r = r) square([size[0] - 2 * r, size[1] - 2 * r], center = true); }

module qi_frame() qi_place() {
    H = qi_size[2];
    difference() {
        qi_loft(concat([[0, 1.0], [0.6, qi_base_s], [H - qi_edge_r, qi_base_s]],
                       [for (k = [1 : 8]) let (a = 90 * k / 8)
                           [H - qi_edge_r + qi_edge_r * sin(a), qi_base_s + qi_edge_r * (1 - cos(a))]]));
        translate([qi_ins_c[0], qi_ins_c[1], H - qi_ins_drop - qi_ins_t]) linear_extrude(qi_ins_t + qi_ins_drop + 1)
            rrect(qi_ins_size + [2, 2] * qi_fit, qi_ins_r + qi_fit);
    }
}
module qi_chrome() qi_place() {
    w0 = qi_chrome_w[0]; w1 = qi_chrome_w[1]; wm = (w0 + w1) / 2;
    difference() {
        qi_loft([[w0, qi_base_s + 0.2], [w0 + 0.25, 0.08], [wm, 0], [w1 - 0.25, 0.08], [w1, qi_base_s + 0.2]]);
        translate([0, 0, w0 - 1]) linear_extrude(w1 - w0 + 2) polygon(qi_outline(qi_base_s + 0.4));
    }
}
module qi_insert() qi_place()
    translate([qi_ins_c[0], qi_ins_c[1], qi_size[2] - qi_ins_drop - qi_ins_t]) linear_extrude(qi_ins_t) rrect(qi_ins_size, qi_ins_r);
module qi_led() qi_place() for (p = qi_dots)
    translate([p[0], p[1], qi_size[2] - (p[2] > 0 ? 0 : qi_ins_drop) - 0.1]) {
        cylinder(d = qi_dot_d, h = 0.2, $fn = 24);
        translate([0, 0, 0.2]) scale([1, 1, 0.25 / (qi_dot_d / 2)]) sphere(d = qi_dot_d, $fn = 24);
    }
module qi_icon_2d() {
    mirror([0, 1, 0]) {                                  // (u, up) -> (u, v = -up)
        polygon(qi_bolt);
        for (k = [0 : len(qi_arc_r) - 1], side = [0, 180]) {
            r = qi_arc_r[k]; ha = qi_arc_half[k];
            pts = [for (i = [0 : 16]) let (a = side - ha + 2 * ha * i / 16) r * [cos(a), sin(a)]];
            for (i = [0 : 15]) hull() {
                translate(pts[i]) circle(d = qi_arc_w, $fn = 16);
                translate(pts[i + 1]) circle(d = qi_arc_w, $fn = 16);
            }
        }
    }
}
module qi_icon() qi_place()
    translate([qi_icon_c[0], qi_icon_c[1], qi_size[2] - qi_ins_drop - 0.02]) linear_extrude(qi_icon_t + 0.02) qi_icon_2d();
module qi_screw() qi_place() translate([qi_screw_p[0], qi_screw_p[1], qi_size[2] - qi_ins_drop - 0.1]) difference() {
    union() {
        cylinder(d = qi_screw_d, h = qi_ins_drop + 0.1 + qi_screw_h - 1, $fn = 40);
        translate([0, 0, qi_ins_drop + 0.1 + qi_screw_h - 1]) scale([1, 1, 1 / (qi_screw_d / 2 - 0.3)])
            sphere(r = qi_screw_d / 2 - 0.3, $fn = 40);              // 1 mm domed head
    }
    for (a = [0, 90]) rotate([0, 0, a]) translate([0, 0, qi_ins_drop + 0.1 + qi_screw_h]) cube([3.8, 0.9, 1.6], center = true);
}
// zip cord: two wires side by side (red at +B, black at -B, B horizontal), along a shared smoothed path
function qi_cord_path() = spline(concat([qi_xform_pt(qi_exit + [-qi_grommet[1], 0, 0])], qi_cord_mid, [qi_lead[len(qi_lead) - 1]]), 2);
module qi_wire(sgn) {
    P = qi_cord_path();
    n = len(P);
    T = [for (i = [0 : n - 1]) unit(P[min(i + 1, n - 1)] - P[max(i - 1, 0)])];
    Bv = [for (i = [0 : n - 1]) unit(cross(T[i], [0, 0, 1]))];
    Q = [for (i = [0 : n - 1]) P[i] + sgn * Bv[i] * qi_wire_d / 2];
    sweep(Q, [for (p = Q) [0, 0, 1]], [for (p = Q) circle2(qi_wire_d / 2, 12)]);
}
module qi_cable_red() qi_wire(1);
module qi_cable_black() {
    qi_wire(-1);
    // grommet at the pad (pointing -u out of the screw end)
    g0 = qi_xform_pt(qi_exit + [0.5, 0, 0]);
    orient(g0, [-cos(qi_rot), -sin(qi_rot), 0]) cylinder(d = qi_grommet[0], h = qi_grommet[1] + 0.5, $fn = 28);
    // 2-pin connector, qi_conn_at along the cord
    P = qi_cord_path(); L = cumlen(P);
    q = at_len(P, L, qi_conn_at);
    hz = unit(cross(q[1], [0, 0, 1]));
    translate(q[0]) multmatrix([[q[1][0], hz[0], 0, 0], [q[1][1], hz[1], 0, 0], [q[1][2], hz[2], 1, 0], [0, 0, 0, 1]])
        difference() {
            cube([qi_conn[0], qi_conn[1], qi_conn[2]], center = true);
            translate([0, 0, qi_conn[2] / 2]) cube([0.8, qi_conn[1] + 1, 1.2], center = true);   // the mating seam
        }
}

// =====================================================================================================
// 4. FUSED RIGHT-ANGLE CIGARETTE PLUG AND ITS LEAD  (params: plug_size [70, 40, 31], w1_d 5, w1_pts,
//    wclip_notch). Local frame: axis +x from the tip (x = 0) to the head's end (x = 70).
// =====================================================================================================
plug_tip_fit  = [44, -281, -50];    // tip, pointing -x, unplugged in the tray (GEOMETRY 11.5). Checked in 3483:
                                    //   this point projects onto the visible tip (1303, 1181) vs (1295, 1182) SEEN.
                                    //   It stands ~22 above the re-fitted pad's top there; what it rests on (the
                                    //   front wall's lower lip?) is not visible [I].
plug_exit_up  = 0;       // the ribbed exit points rearward (+y), level [P] 3483/3484 (exit toward the camera)
plug_pin      = [3.5, 2.5];   // spring-loaded centre pin: diameter, length            [P] 3491 zoom
plug_cap      = [9.5, 6];     // knurled screw-off fuse cap: diameter, length          [P] 3491 zoom (silver, knurled)
plug_barrel_d = 21;           // black barrel (standard 12 V plug)                     [P] 3491 zoom 19-21
plug_barrel_x = [8.5, 40];    // barrel from / to (nose rounded down to the cap)       [P] 3491: tip to head ~45
plug_spring   = [15, 13, 1.6, 4];   // two silver side contacts: length, start x, proud, width [P] 3491 zoom
plug_collar   = [23.5, 3];    // chrome collar between barrel and head: diameter, length [P] 3491 zoom
plug_head_d   = plug_size[2]; // head diameter = the plug's height lying down (31)     [S]
plug_head_r   = 4;            // rounded end edge                                       [P]
plug_exit_x   = 57;           // ribbed exit leaves the head's side here                [P] 3491 zoom (mid-head)
plug_exit_len = plug_size[1] - plug_head_d;   // 9: exit sticks out so the width is 40  [S]
// lead route (INFERRED from 3483: a black lead crosses the pad diagonally toward the rear-left, over its
// raised rear edge, down the well's driver side to the corner clip), then params' under-deck run w1_pts to the
// moulded end (W1 = the plug's lead: GEOMETRY section 9, confidence 0.75).
function on_pad(x, y) = [x, y, qi_top_z_at(y) + (w1_d / 2 + 0.4) / cos(qi_tilt)];   // lying on the sloping top
plug_lead_mid = [[97, -248, -58], [90, -243, qi_top_z_at(-243) + 5.5], on_pad(72, -237), on_pad(62, -232), on_pad(25, -214), on_pad(-12, -192), on_pad(-34, -170),
                 [-17, -155, -32.5], [-38, -131, -29.5], [-62, -100, -26.5], [-76, -70, -21], [-84, -40, -14.5],
                 [-89, -18, -13.5], [-94, -6, -13.8]];
plug_moulded  = [7.5, 14];    // moulded end under the deck (black, with a clear collar): diameter, length [P] 3502/3503

module plug_local() {
    R = plug_barrel_d / 2;
    // pin + knurled cap (silver in the photos; one STL, material per assemble.py if wanted: x < 8.5)
    translate([-0.01, 0, 0]) rotate([0, 90, 0]) cylinder(d = plug_pin[0], h = plug_pin[1] + 0.5, $fn = 24);
    translate([plug_pin[1], 0, 0]) rotate([0, 90, 0]) difference() {
        cylinder(d = plug_cap[0], h = plug_cap[1], $fn = 48);
        for (k = [0 : 23]) rotate([0, 0, k * 15]) translate([plug_cap[0] / 2, 0, -1]) cylinder(d = 0.9, h = plug_cap[1] + 2, $fn = 8);
    }
    // barrel with a rounded nose
    rotate([0, 90, 0]) rotate_extrude($fn = 64) polygon(concat(
        [[0, plug_barrel_x[0]]],
        [for (k = [0 : 8]) let (a = 90 * k / 8) [5 + (R - 5) * sin(a), plug_barrel_x[0] + 5 * (1 - cos(a))]],
        [[R, plug_barrel_x[1] + 0.01], [0, plug_barrel_x[1] + 0.01]]));
    // two side spring contacts (on the sides that face sideways when the plug lies down)
    for (s = [-1, 1]) translate([plug_spring[1] + plug_spring[0] / 2, s * (R + plug_spring[2] / 2 - 0.6), 0])
        scale([1, 1, 1]) cube([plug_spring[0], plug_spring[2] + 1.2, plug_spring[3]], center = true);
    // chrome collar and head
    translate([plug_barrel_x[1], 0, 0]) rotate([0, 90, 0]) cylinder(d = plug_collar[0], h = plug_collar[1] + 0.01, $fn = 64);
    hx0 = plug_barrel_x[1] + plug_collar[1]; hl = plug_size[0] - hx0;
    translate([hx0, 0, 0]) rotate([0, 90, 0]) rotate_extrude($fn = 72) polygon(concat(
        [[0, 0], [plug_head_d / 2, 0]],
        [for (k = [0 : 8]) let (a = 90 * k / 8) [plug_head_d / 2 - plug_head_r + plug_head_r * cos(a), hl - plug_head_r + plug_head_r * sin(a)]],
        [[0, hl]]));
    // ribbed right-angle exit, from inside the head out through its side
    translate([plug_exit_x, 0, 0]) rotate([-90, 0, 0]) translate([0, 0, plug_head_d / 2 - 3.37])
        ribbed(plug_exit_len + 3.37, 4.6, w1_d / 2 + 0.6, 5, 0.5);
}
// the exit points local +y; place: local x -> model +x, local y -> rearward and plug_exit_up up
module plug() translate(plug_tip_fit) rotate([plug_exit_up, 0, 0]) plug_local();
function plug_exit_end() = plug_tip_fit + [plug_exit_x, 0, 0] + (plug_head_d / 2 + plug_exit_len) * [0, cos(plug_exit_up), sin(plug_exit_up)];
module plug_lead() {
    ctrl = concat([plug_exit_end() - 2 * [0, cos(plug_exit_up), sin(plug_exit_up)]], plug_lead_mid, w1_pts);
    cable(ctrl, w1_d, 2.5, 16);
    // moulded end at the last point, continuing the cable direction
    n = len(w1_pts);
    orient(w1_pts[n - 1], unit(w1_pts[n - 1] - w1_pts[n - 2])) {
        translate([0, 0, -1]) cylinder(d = plug_moulded[0], h = plug_moulded[1], $fn = 32);
        translate([0, 0, plug_moulded[1] - 1]) cylinder(d = plug_moulded[0] + 0.6, h = 3, $fn = 32);   // collar
    }
}

// =====================================================================================================
// 5. CONTROLLER ON THE CUP BODY  (params: ctrl_size [46 along y, 36 across x, 20], ctrl_c, ctrl_dc_plug_len,
//    ctrl_out_relief_len, ctrl_dc_lead, ctrl_out_lead). Mounting face (with the ears) up against the cup's
//    flat outer bottom (z -60); the plain label face looks down.
// =====================================================================================================
ctrl_rb      = 2;        // edge radius                                          [P] 3502 (crisp moulded box) 1.5-3
ctrl_ear     = [7, 8, 2, 3];   // corner ears: length beyond the end face, width, thickness, hole Ø  [P] 3502 (ear + hole at one corner)
ctrl_ear_dx  = 11;       // ear centre off the box centre line (x); diagonally opposite corners [P] 3502 / [I] the second ear
ctrl_rib_n   = 6;        // ribs (slots) at each short end of the label face     [P] 3502: 6 slots each end
ctrl_rib     = [1.8, 5, 1.2, 4];   // slot width, length in from the end, depth, pitch          [P] 3502
ctrl_dc_body = [9, 13];  // DC barrel plug body: diameter, length                [P] 3502 / ctrl_ends
ctrl_dc_boot = [7.5, 4.6, 3];   // its ribbed boot: root Ø, end Ø, ribs (length = ctrl_dc_plug_len - body) [P]
ctrl_out_rel = [6, 4, 4];       // strain relief: root Ø, end Ø, ribs           [P] 3502 / ctrl_ends
ctrl_lead_d  = 3.5;      // controller lead diameter (both)                      [P] 3502 ~3-4
module ctrl() {
    W = ctrl_size[1]; L = ctrl_size[0]; H = ctrl_size[2];
    translate(ctrl_c) {
        difference() {
            union() {
                hull() for (sx = [-1, 1], sy = [-1, 1], sz = [-1, 1])
                    translate([sx * (W / 2 - ctrl_rb), sy * (L / 2 - ctrl_rb), sz * (H / 2 - ctrl_rb)]) sphere(r = ctrl_rb, $fn = 20);
                for (e = [[-1, -1], [1, 1]]) hull() {
                    translate([e[0] * ctrl_ear_dx, e[1] * (L / 2 - 2), H / 2 - ctrl_ear[2] / 2]) cube([ctrl_ear[1], 1, ctrl_ear[2]], center = true);
                    translate([e[0] * ctrl_ear_dx, e[1] * (L / 2 + ctrl_ear[0] - ctrl_ear[1] / 2), H / 2 - ctrl_ear[2]])
                        cylinder(d = ctrl_ear[1], h = ctrl_ear[2], $fn = 32);
                }
            }
            for (e = [[-1, -1], [1, 1]])
                translate([e[0] * ctrl_ear_dx, e[1] * (L / 2 + ctrl_ear[0] - ctrl_ear[1] / 2), H / 2 - ctrl_ear[2] - 1])
                    cylinder(d = ctrl_ear[3], h = ctrl_ear[2] + 2, $fn = 24);
            // ribbed short ends: slots across the label-face edge, wrapping onto the end faces
            for (sy = [-1, 1], i = [0 : ctrl_rib_n - 1]) let (x = (i - (ctrl_rib_n - 1) / 2) * ctrl_rib[3])
                translate([x, sy * (L / 2 - ctrl_rib[1] / 2 + 1), -H / 2 + ctrl_rib[2] / 2 - 0.5])
                    cube([ctrl_rib[0], ctrl_rib[1] + 2, ctrl_rib[2] + 1], center = true);
        }
        // DC barrel plug + ribbed boot at the +y end (axis on the end-face centre, as ctrl_dc_lead starts)
        translate([0, L / 2 - 0.5, 0]) rotate([-90, 0, 0]) {
            cylinder(d = ctrl_dc_body[0], h = ctrl_dc_body[1] + 0.5, $fn = 36);
            translate([0, 0, ctrl_dc_body[1] + 0.5 - 0.3])
                ribbed(ctrl_dc_plug_len - ctrl_dc_body[1] + 0.3, ctrl_dc_boot[0] / 2, ctrl_dc_boot[1] / 2, ctrl_dc_boot[2], 0.5);
        }
        // ribbed strain relief at the -y end (ctrl_out_lead starts at its end)
        translate([0, -L / 2 + 0.5, 0]) rotate([90, 0, 0])
            ribbed(ctrl_out_relief_len + 0.5, ctrl_out_rel[0] / 2, ctrl_out_rel[1] / 2, ctrl_out_rel[2], 0.45);
    }
}
module ctrl_leads() {      // OPTIONAL: routes are params' ctrl_dc_lead / ctrl_out_lead (climbs [I])
    cable(ctrl_dc_lead, ctrl_lead_d, 2, 14);
    cable(ctrl_out_lead, ctrl_lead_d, 2, 14);
}

// =====================================================================================================
// 6. metal BAR under the slot  (params: bar_c, bar_size [18.5 across x, 89 along y], bar_t, bar_hole_dy,
//    bar_hole_d, bar_top_z)
// =====================================================================================================
bar_r = 3;               // corner radius: nearly square corners                [P] 3503 (~3 % of the length) 2-4
module bar() translate([bar_c[0], bar_c[1], bar_top_z - bar_t]) difference() {
    linear_extrude(bar_t) rrect(bar_size, bar_r);
    for (s = [-1, 1]) translate([0, s * bar_hole_dy / 2, -1]) cylinder(d = bar_hole_d, h = bar_t + 2, $fn = 32);
}

// =====================================================================================================
// 7. dispatch
// =====================================================================================================
module grp_lights() {
    color("#c9cdd2") { head("l"); head("r"); head("loose"); }
    color("#151515") { head_boots(); lead_loose(); }
    color("#bfe4ff", 0.85) { fibre(-1); fibre(1); }
}
module grp_qi() {
    color("#222222") qi_frame();
    color("#e6e6e6") qi_chrome();
    color("#0e0e0e") qi_insert();
    color("white") { qi_icon(); qi_led(); }
    color("#cfcfcf") qi_screw();
    color("#c81e1e") qi_cable_red();
    color("#111111") qi_cable_black();
}
module grp_power() { color("#1a1a1a") plug(); color("#101010") plug_lead(); }
module grp_under() { color("#1e1e1e") ctrl(); color("#2a2a2a") ctrl_leads(); color("#8a8c8e") bar(); }

if      (part == "head_l")         head("l");
else if (part == "head_r")         head("r");
else if (part == "head_loose")     head("loose");
else if (part == "head_boots")     head_boots();
else if (part == "lead_loose")     lead_loose();
else if (part == "fibre_l")        fibre(-1);
else if (part == "fibre_r")        fibre(1);
else if (part == "qi_frame")       qi_frame();
else if (part == "qi_chrome")      qi_chrome();
else if (part == "qi_insert")      qi_insert();
else if (part == "qi_icon")        qi_icon();
else if (part == "qi_led")         qi_led();
else if (part == "qi_screw")       qi_screw();
else if (part == "qi_cable_red")   qi_cable_red();
else if (part == "qi_cable_black") qi_cable_black();
else if (part == "plug")           plug();
else if (part == "plug_lead")      plug_lead();
else if (part == "ctrl")           ctrl();
else if (part == "ctrl_leads")     ctrl_leads();
else if (part == "bar")            bar();
else if (part == "lights")         grp_lights();
else if (part == "qi")             grp_qi();
else if (part == "power")          grp_power();
else if (part == "under")          grp_under();
else if (part == "all")            { grp_lights(); grp_qi(); grp_power(); grp_under(); }
else if (part == "all_photo")      mirror([0, 1, 0]) { grp_lights(); grp_qi(); grp_power(); grp_under(); }
