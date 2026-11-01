// This file defines a later explanatory model; photo/scan tags check it against the finished panel.
include <params.scad>

// =====================================================================================================
// deck.scad -- The deck of the "Custom Aftermarket Car Center Console Upgrade"
//   (Explanatory assembly model; dimensions approximate).
//
// Geometry: ../../docs/GEOMETRY.md sections 3, 4, 7 and 9; every shape is read from params.scad
// (deck_outline_r, deck_board_outline_r, band_pts, notch_*, arch_roll, felt_band_*, fitting centres and
// sizes). The few deck-only values that params.scad does not hold are defined below, each marked.
// Frame: mm, origin = notch stitch crease at deck-top level, +x passenger, +y rear, z up, deck top z = 0.
// The frame is LEFT-handed, so a right-handed viewer shows the parts mirrored (assemble.py flips y).
//
// Geometry represented here:
//   * A tapered deck, a widening notch and rounded arm noses.
//   * Board and felt extending beneath the padded rims to the side walls.
//   * A rolled lip around the full open edge, with a stitch crease behind it.
//   * An asymmetric rear arch with leatherette wrapped onto the underside.
//   * Free-hanging notch lining in table and fitted-car poses.
//   * A raised felt band, component holes and the clock recess.
//
// Parts selected by `part`:
//   "deck"      fibreboard core                          -> deck.stl
//   "vinyl"     leatherette skin and underside wrap      -> deck_vinyl.stl
//   "felt"      underside felt with its raised band      -> deck_felt.stl
//   "lip"       rolled notch lip                         -> notch_lip.stl
//   "skirt"     free-hanging lining on the table         -> notch_skirt.stl
//   "skirt_car" lining in the fitted-car pose            -> notch_skirt_car.stl
//   "lining"    alias for the lining selected by lining_state
//   "notch"     lip and lining; coloured preview
//   "all"       all parts; coloured preview
//
// Swept edges overlap flat parts by `ov` to avoid slivers. The felt has a small
// button-wire hole, plate holes follow plate_xf(), and fitp() applies the fitted
// offsets to the notch, rims and board outline. The lining tapers to a rounded
// point at each nose; the fitted passenger side hangs deeper beside the gear boot.
// =====================================================================================================

part = "deck";

// ---- deck-only values that are not in params.scad --------------------------------------------------
path_step     = 1;     // resample step (mm) of the swept edges
path_smooth   = 6;     // [1 2 1]/4 passes on the notch open edge: removes the table's polyline corners,
                       //   moves the edge < 0.2 mm (echoed)
arch_smooth   = 60;    // passes on the rear arch (the table points carry ~1 mm of scan noise; moves it < 0.8 mm, echoed)
lip_crest_z   = -0.5;  // crest of the notch roll, just below the deck top. [S] driver arm: -0.2..-0.6
                       //   2-4 mm in front of the crease [I] shape
lip_curl      = 60;    // the roll curls this far (deg) under itself before the lining drops        [I]
lip_core_s    = 3;     // under the roll the covered board edge stands this far in from the open edge [I]
lining_s0     = 1.5;   // lining sheet centre at its top edge, this far in from the open edge (under the
                       //   roll, so the roll overhangs it by ~0.75)                                 [I]
lining_top_z  = -5;    // lining top edge, hidden inside the roll                                   [I]
lining_steps  = 12;    // facets down the lining
lining_sag_exp= 0.6;   // < 1: the loose sheet bulges in right under the roll as a soft padded roll (was
                       //   1.0 = flat flap). [P] 3487/3486 padded roll with a crease along the top; [S] passenger arm: the
                       //   lining surface slopes in right below the edge; [P] 3491 broad band beyond the crease [I] 0.5-0.8
lining_nose_y = [-178, -218];  // the lining's depth tapers from full to lining_nose_d over these y before each nose, so
lining_nose_d = 8;     //   its lower edge rises to a tapered point ([P] 3487 c3487_lining, 3491) [I]
lining_beak_len = 14;  // over the last 14 mm of the lining path at each nose tip the lower edge curls up on a quarter
lining_beak_d   = 5.6; //   ellipse to this depth (just under the roll, lining_top_z = -5), so the lining ends in a
                       //   small rounded beak tucked under the rim instead of a square 8 mm end.                        //   SEEN 3487 (far arm, 3x) a rounded lining nose; 3492 / 3491 a small curled beak at the
                       //   arm front. Length 10-18 [I]
lining_state  = part == "skirt_car" ? "car" : "table";   // "table" (free, 3491/scan) or "car" (3483: passenger sags further, hangs deeper)
// Fitted-car pose, passenger side. The lining follows the silhouette in IMG_3483:
// full sag and depth continue towards the nose, with a convex bulge beside the boot.
// The hidden lower boundary is an estimate. These parameters affect only the
// fitted-car lining; the table pose uses the separate lining parameters above.
lining_car_sag_taper = [-196, -216];  // passenger sag stays full to here, then returns toward the nose      [P] 3483
lining_car_nose_y    = [-194, -218];  // passenger depth stays full to here, then tapers to the nose        [P] 3483
lining_car_bump      = 9;             // extra sag mid-arm (peak at lining_car_bump_y, half-width lining_car_bump_w): in 3483
lining_car_bump_y    = -110;          //   the lining's pebbled face reaches frame x ~1560-1600 over frame y 1650-2340 and meets
lining_car_bump_w    = 70;            //   the boot's flank; a 16 sag left a 5-10 mm slot down to the well floor  [P] 3483 6-12
lining_car_sag_exp   = 0.55;          // convex (padded) profile: the face bulges right under the roll and tilts up
                                      //   toward the camera, as the lit leather face in 3483 [P] [I] 0.4-0.6
arch_bottom_r = 2;     // round on the lower arch edge                                               [I]
arch_wrap     = 7;     // the top leatherette wraps this far onto the underside at the rear arch, the
                       //   felt starts there. [T] 3477 / [P] 3502 show the wrap; its width is [I]
ov            = 0.3;   // swept edges overlap the flat parts by this much (hidden)
pilot_depth   = 15;    // plate-screw pilot holes, measured from the deck top (model allowance)
pilot_floor   = 0.5;   // felt left closed under the pilot holes (the deck is only 12 thick)
btn_wire_hole = 4;     // the felt is not cut for the button, only a small hole for its two red leads [P] 3502 [I] size

// fitted-state x offsets (params fitp; 0 by default). The flat slabs cannot take fit_front_drop.
function fit2(P) = [for (p = P) let (q = fitp([p[0], p[1], 0], p[0] >= 0 ? 1 : -1)) [q[0], q[1]]];
if (fit_front_drop != 0)
    echo("WARNING deck.scad: fit_front_drop is not applied to the flat deck (arms, lip, lining); only the walls, bands and fibres drop");

z_vb = -deck_vinyl;                  // vinyl / board interface  (-1)
z_bf = -deck_vinyl - deck_board;     // board / felt interface   (-9)
z_bot = felt_z;                      // felt underside           (-12)

// =====================================================================================================
// polyline helpers
// =====================================================================================================
function unit(v) = v / norm(v);
function lperp(t) = [-t[1], t[0]];                 // 90 deg CCW: the inward (deck-side) normal here
function rev(L) = [for (i = [len(L) - 1 : -1 : 0]) L[i]];
function cumlen(C) = [for (i = 0, a = 0; i < len(C);
                           a = a + (i < len(C) - 1 ? norm(C[i + 1] - C[i]) : 0), i = i + 1) a];
function resample(C, step) =
    let (L = cumlen(C), T = L[len(L) - 1], M = max(2, round(T / step)),
         tx = [for (i = [0 : len(C) - 1]) [L[i], C[i][0]]],
         ty = [for (i = [0 : len(C) - 1]) [L[i], C[i][1]]])
    [for (k = [0 : M]) let (s = T * k / M) [lookup(s, tx), lookup(s, ty)]];
function smooth(R, k) =
    k <= 0 ? R
           : smooth(concat([R[0]], [for (i = [1 : len(R) - 2]) (R[i - 1] + 2 * R[i] + R[i + 1]) / 4],
                           [R[len(R) - 1]]), k - 1);
// distance from p to polyline Q (to report how far smoothing moved a curve)
function _pt_seg(p, a, b) = let (ab = b - a, t = max(0, min(1, ((p - a) * ab) / (ab * ab)))) norm(p - (a + t * ab));
function pt_poly(p, Q) = min([for (i = [0 : len(Q) - 2]) _pt_seg(p, Q[i], Q[i + 1])]);
// miter-scaled inward normal at vertex i (offsetting by s along it keeps both edges s away)
function vnorm(P, i) =
    let (n = len(P),
         t1 = unit(P[max(1, i)] - P[max(1, i) - 1]),
         t2 = unit(P[min(n - 1, i + 1)] - P[min(n - 1, i + 1) - 1]),
         n1 = lperp(t1), n2 = lperp(t2), b = unit(n1 + n2))
    b / max(0.35, b * n1);
function vnorms(P) = [for (i = [0 : len(P) - 1]) vnorm(P, i)];
// turn radius at vertex i over +-w vertices, LEFT turns only (they shrink inward offsets); else 1e9
function vradius(P, i, w = 3) =
    let (n = len(P), a = max(0, i - w), b = min(n - 1, i + w))
    (b - a < 2) ? 1e9 :
    let (t1 = unit(P[a + 1] - P[a]), t2 = unit(P[b] - P[b - 1]),
         ang = atan2(t1[0] * t2[1] - t1[1] * t2[0], t1 * t2),
         arc = (norm(P[a + 1] - P[a]) + norm(P[b] - P[b - 1])) / 2
               + (b - a > 2 ? cumlen([for (j = [a + 1 : b - 1]) P[j]])[b - a - 2] : 0))
    ang > 0.5 ? arc / (ang * PI / 180) : 1e9;
function polyarea(P) = 0.5 * sum([for (i = [0 : len(P) - 1]) let (a = P[i], b = P[(i + 1) % len(P)])
                                  a[0] * b[1] - a[1] * b[0]]);
function sum(v, i = 0, acc = 0) = i >= len(v) ? acc : sum(v, i + 1, acc + v[i]);

// closed solid swept through rings (each ring = the same CCW (s, z) section placed at one path vertex)
module sweep(rings) {
    n = len(rings);
    K = len(rings[0]);
    pts = [for (r = rings) each r];
    faces = concat(
        [[for (k = [0 : K - 1]) k]],                                             // start cap
        [for (i = [0 : n - 2], k = [0 : K - 1]) let (k1 = (k + 1) % K)
            [i * K + k, (i + 1) * K + k, (i + 1) * K + k1, i * K + k1]],          // sides
        [[for (k = [K - 1 : -1 : 0]) (n - 1) * K + k]]);                         // end cap
    polyhedron(points = pts, faces = faces, convexity = 8);
}
// place a section [[s, z], ...] at path vertex p with inward normal nv (s measured along nv)
function ring(p, nv, sec) = [for (q = sec) [p[0] + q[0] * nv[0], p[1] + q[0] * nv[1], q[1]]];

// =====================================================================================================
// 1. NOTCH OPEN EDGE (from deck_outline_r): driver arm/seam junction -> driver nose -> driver arm ->
//    back corner -> back edge -> passenger corner -> passenger arm -> passenger nose -> junction.
//    The junction is where the nose's outer side meets the rim inner face (band_inner_x).
// =====================================================================================================
_D     = deck_outline_r;
_i_tip = let (m = min([for (p = _D) p[1]])) [for (i = [0 : len(_D) - 1]) if (_D[i][1] == m) i][0];
_i_jn  = [for (i = [_i_tip + 1 : len(_D) - 1]) if (_D[i][0] >= band_inner_x(_D[i][1]) - 0.6) i][0];
_oe_half = [for (i = [0 : _i_jn]) _D[i]];                         // (0, -6) ... (132.5, -212)
_oe_raw  = fit2(concat([for (i = [len(_oe_half) - 1 : -1 : 1]) [-_oe_half[i][0], _oe_half[i][1]]], _oe_half));
OE   = smooth(resample(_oe_raw, path_step), path_smooth);
OE_N = vnorms(OE);
_oe_dev = max([for (p = _oe_raw) pt_poly(p, OE)]);

// lip width per vertex: notch_lip on the back edge, notch_lip_side along the arms, blended over the corners
_y_corner = -notch_lip - notch_corner_r;                          // the back corners end here (y -20)
function lip_w(y) = let (t = max(0, min(1, (y - _y_corner) / (-notch_lip - _y_corner))))
                    notch_lip_side + (notch_lip - notch_lip_side) * t;
// near the noses the open edge turns tighter than the lip is wide: scale the section in s there so the
// crease line never folds over (moving minimum over +-4 vertices; echoed)
_oe_rad   = [for (i = [0 : len(OE) - 1]) vradius(OE, i)];
_oe_raw_k = [for (i = [0 : len(OE) - 1]) min(1, max(0.2, (_oe_rad[i] - 0.5) / (lip_w(OE[i][1]) + ov)))];
OE_K      = [for (i = [0 : len(OE) - 1]) min([for (j = [max(0, i - 4) : min(len(OE) - 1, i + 4)]) _oe_raw_k[j]])];
// crease line = inner side of the lip band (shared exactly by the lip solid and the plate cut)
CREASE = [for (i = [0 : len(OE) - 1]) OE[i] + lip_w(OE[i][1]) * OE_K[i] * OE_N[i]];

// lip section, CCW in (s, z): s = distance in from the open edge toward the deck, z up.
// crease (s = L, z = -crease depth) -> rising to the crest -> over the roll (radius notch_lip_r, its
// outermost point = the open edge at s = 0) -> curling under -> the covered board edge -> down to the felt
// level -> back to the crease, overlapping the plate by ov below the groove.
function lip_sec(L) =
    let (R = notch_lip_r, zc = lip_crest_z - R, zcr = -notch_crease_depth, n1 = 5, n2 = 16)
    concat(
        [for (j = [0 : n1]) let (u = j / n1) [L - (L - R) * u, lip_crest_z + (zcr - lip_crest_z) * pow(1 - u, 2)]],
        [for (j = [1 : n2]) let (a = 90 - (90 + lip_curl) * j / n2) [R - R * cos(a), zc + R * sin(a)]],
        [[lip_core_s - 0.4, zc - R - 0.6], [lip_core_s, z_bot], [L + ov, z_bot], [L + ov, zcr - 0.5]]);
function lip_rings() = [for (i = [0 : len(OE) - 1])
    ring(OE[i], OE_K[i] * OE_N[i], lip_sec(lip_w(OE[i][1])))];

module lip() sweep(lip_rings());

// lip band polygon (open edge -> crease) and the notch region in front of the open edge, closed along the
// rim inner faces forward of the junctions (so the small gap between each nose and its rim is open too)
LIP_BAND = concat(OE, rev(CREASE));
_rim_fwd = fit2([for (y = [OE[len(OE) - 1][1] - 6 : -6 : wing_tip_y]) [band_inner_x(y), y]]);
NOTCH_POLY = concat(OE, _rim_fwd, [[band_inner_x(wing_tip_y), -400], [-band_inner_x(wing_tip_y), -400]],
                    rev([for (p = _rim_fwd) [-p[0], p[1]]]));

// =====================================================================================================
// 2. REAR EDGE (from deck_board_outline_r): wall inner face (104.5, 242) -> under the band end -> horn tip
//    (92.5, 238) -> rear arch -> driver side. The arch part is resampled and lightly smoothed.
// =====================================================================================================
_B    = deck_board_outline_r;
_i_r  = let (m = max([for (p = _B) p[1]])) [for (i = [0 : len(_B) - 1]) if (_B[i][1] == m) i][0];
_i_h  = [for (i = [_i_r : len(_B) - 1]) if (abs(_B[i][1] - seam_rear_y) < 1e-6) i][0];  // horn tip
_rc   = [for (i = [_i_r : _i_h - 1]) _B[i]];                     // (104.5, 242), (95, 242)
_ah   = [for (i = [_i_h : len(_B) - 1]) _B[i]];                  // (92.5, 238) ... (0, 191)
_arch_raw = concat(_ah, arch_pts_d);     // passenger half (horn -> centre) + the asymmetric driver half (params)
_arch = smooth(resample(_arch_raw, path_step), arch_smooth);
_arch_dev = max([for (p = _arch_raw) pt_poly(p, _arch)]);
RP   = concat(_rc, _arch, rev([for (p = _rc) [-p[0], p[1]]]));  // passenger wall -> driver wall
RP_N = vnorms(RP);
REAR_POLY = concat(RP, [[RP[len(RP) - 1][0], 400], [RP[0][0], 400]]);   // everything behind the rear edge

// rolled arch edge sections, CCW in (s, z): outer envelope = top round arch_roll, vertical side, bottom
// round arch_bottom_r, underside at z_bf - deck_vinyl; the board envelope is the same inset by deck_vinyl.
function _arc(c, r, a0, a1, n) = [for (j = [0 : n]) let (a = a0 + (a1 - a0) * j / n) [c[0] + r * cos(a), c[1] + r * sin(a)]];
function arch_vinyl_sec() =
    let (Ra = arch_roll, Rb = arch_bottom_r, t = deck_vinyl, zb = z_bf - t)
    concat([[Ra + ov, 0]],
           _arc([Ra, -Ra], Ra, 90, 180, 16),                     // (Ra, 0) -> (0, -Ra)
           _arc([Rb, zb + Rb], Rb, 180, 270, 8),                 // (0, zb + Rb) -> (Rb, zb)
           [[Rb + ov, zb], [Rb + ov, zb + t]],
           _arc([Rb, zb + Rb], Rb - t, 270, 180, 8),             // inner: (Rb, zb + t) -> (t, zb + Rb)
           _arc([Ra, -Ra], Ra - t, 180, 90, 16),                 // (t, -Ra) -> (Ra, -t)
           [[Ra + ov, -t]]);
function arch_board_sec() =
    let (Ra = arch_roll, Rb = arch_bottom_r, t = deck_vinyl, zb = z_bf - t)
    concat([[Ra + ov, -t]],
           _arc([Ra, -Ra], Ra - t, 90, 180, 16),
           _arc([Rb, zb + Rb], Rb - t, 180, 270, 8),
           [[Ra + ov, z_bf]]);
module arch_sweep(sec) sweep([for (i = [0 : len(RP) - 1]) ring(RP[i], RP_N[i], sec)]);

// =====================================================================================================
// 3. PLAN REGIONS
// =====================================================================================================
module board2d() polygon(fit2(deck_board_outline));
module plate2d() difference() { board2d(); polygon(NOTCH_POLY); polygon(LIP_BAND); }
module flat2d()  difference() { plate2d(); offset(r = arch_roll) polygon(REAR_POLY); }     // flat top skin / board
module felt2d()  difference() { plate2d(); offset(r = arch_wrap) polygon(REAR_POLY); }
module wrap2d()  difference() {                                     // leatherette wrapped onto the underside
    intersection() { plate2d(); offset(r = arch_wrap + ov) polygon(REAR_POLY); }
    offset(r = arch_bottom_r - ov) polygon(REAR_POLY);
}
// the leatherette also turns down the plate's cut faces where they would otherwise show bare board:
// into the stitched crease behind the lip (down to below the groove) and over the front end of the
// board under each rim (y = arm_front_y, beneath the free rim)
module crease_strip2d() intersection() { plate2d(); offset(r = deck_vinyl) polygon(LIP_BAND); }
module front_strip2d()  intersection() { plate2d(); translate([-300, arm_front_y - 1]) square([600, 1 + deck_vinyl]); }

// =====================================================================================================
// 4. HOLES (GEOMETRY.md section 7). The clock body sits in a hole in the leatherette only.
// =====================================================================================================
module holes2d(felt = false) {
    translate(cup_c) circle(d = cup_hole_d);                           // cup holder
    translate(button_c) circle(d = felt ? btn_wire_hole : button_hole_d);   // silver push button (felt: wire hole only)
    for (c = [usb_c, v12_c]) translate(plate_xf(c)) circle(d = socket_hole_d);   // USB and 12 V sockets (plate turn)
    translate(slot_c) square(slot_cut, center = true);                 // slot down to the metal bar
}
function plate_screws() = [for (sx = [-1, 1], sy = [-1, 1]) plate_xf(plate_c + [sx * plate_screw_dx / 2, sy * plate_screw_dy / 2])];
module holes3d(felt = false) translate([0, 0, z_bot - 3]) linear_extrude(height = -z_bot + 5) holes2d(felt);
module clock_hole() translate([clock_c[0], clock_c[1], z_vb - 0.5]) cylinder(d = clock_body_d, h = deck_vinyl + 1, $fn = 96);
module pilot_holes() {
    zb = max(-pilot_depth, z_bot + pilot_floor);
    for (p = plate_screws()) translate([p[0], p[1], zb]) cylinder(d = plate_screw_d, h = -zb + 1, $fn = 24);
}

// =====================================================================================================
// 5. LAYER SOLIDS
// =====================================================================================================
module slab(z0, z1) translate([0, 0, z0]) linear_extrude(height = z1 - z0) children();

crease_wrap_z = -notch_crease_depth - 1.5;   // the vinyl lines the crease's back wall down to here (hidden below)
module vinyl() difference() {
    union() {
        slab(z_vb, 0) flat2d();
        arch_sweep(arch_vinyl_sec());
        slab(z_bf - deck_vinyl, z_bf) wrap2d();
        slab(crease_wrap_z, z_vb + 0.01) crease_strip2d();
        slab(z_bf, z_vb + 0.01) front_strip2d();
    }
    holes3d(); clock_hole(); pilot_holes();
}
module board() difference() {
    union() {
        slab(z_bf, z_vb) flat2d();
        arch_sweep(arch_board_sec());
    }
    slab(crease_wrap_z - 0.01, z_vb + 0.01) crease_strip2d();
    slab(z_bf - 0.01, z_vb + 0.01) front_strip2d();
    holes3d(); pilot_holes();
}
module felt() difference() {
    union() {
        slab(z_bot, z_bf) felt2d();
        slab(z_bot - felt_band_h, z_bot + 0.01)                        // raised band across the underside
            intersection() { felt2d(); translate([-300, felt_band_y[0]]) square([600, felt_band_y[1] - felt_band_y[0]]); }
    }
    holes3d(felt = true); pilot_holes();
}

// =====================================================================================================
// 6. NOTCH LINING: hangs from under the roll along the open edge, nose tip to nose tip, notch_lining_depth
//    below the deck. Its lower edge swings into the notch by sag(y): passenger notch_lining_sag_p over
//    y -60..-150 (a loose flap), driver notch_lining_sag_d, ~1 on the back edge. Outer face (toward the
//    notch) leatherette, back grey knit, raw cut lower edge.
// =====================================================================================================
_i_tD = let (m = min([for (p = OE) if (p[0] < 0) p[1]])) [for (i = [0 : len(OE) - 1]) if (OE[i][0] < 0 && OE[i][1] == m) i][0];
_i_tP = let (m = min([for (p = OE) if (p[0] > 0) p[1]])) [for (i = [0 : len(OE) - 1]) if (OE[i][0] > 0 && OE[i][1] == m) i][0];
LP   = [for (i = [_i_tD : _i_tP]) OE[i]];
LP_N = [for (i = [_i_tD : _i_tP]) OE_N[i]];
function _ss(a, b, x) = let (t = max(0, min(1, (x - a) / (b - a)))) t * t * (3 - 2 * t);
// passenger flap: full sag mid-arm, almost straight by the nose (SEEN 3491 the flap is pointed and
// its notch-side edge runs straight back diagonally; the old ramp -150..-205 left it 3-8 too far into the notch)
function lining_sag(p) =
    let (y = p[1], back = 1, car = lining_state == "car", sp = car ? notch_lining_sag_p_car : notch_lining_sag_p,
         t0 = car ? lining_car_sag_taper[0] : -140, t1 = car ? lining_car_sag_taper[1] : -190,
         bump = car ? lining_car_bump * exp(-pow((y - lining_car_bump_y) / lining_car_bump_w, 2)) : 0)
    p[0] > 0 ? back + (sp - back) * _ss(_y_corner + 3, -60, y) + bump
                    - (sp - 1) * _ss(t0, t1, y)
             : back + (notch_lining_sag_d - back) * _ss(_y_corner + 3, -40, y);
// depth below the deck: full along the arms, tapering to the nose; in the car the passenger side hangs deeper
function lining_depth(p) =
    let (y = p[1],
         d0 = (lining_state == "car" && p[0] > 0)
              ? notch_lining_depth + (notch_lining_depth_p_car - notch_lining_depth) * _ss(_y_corner + 3, -60, y)
              : notch_lining_depth)
    let (ny = (lining_state == "car" && p[0] > 0) ? lining_car_nose_y : lining_nose_y)
    d0 + (lining_nose_d - d0) * _ss(ny[0], ny[1], y);
function lining_sec(sag, depth = notch_lining_depth, ex = lining_sag_exp) =
    let (m = lining_steps, zt = lining_top_z, zb = -depth, t = notch_lining_t,
         zs = [for (k = [0 : m]) zt + (zb - zt) * k / m],
         sc = [for (z = zs) lining_s0 - sag * pow((zt - z) / (zt - zb), ex)])
    concat([for (k = [0 : m]) [sc[k] - t / 2, zs[k]]], [for (k = [m : -1 : 0]) [sc[k] + t / 2, zs[k]]]);
// rounded beak at both ends of the lining path (nose tips): depth eases from lining_depth up to lining_beak_d with a
// vertical tangent at the very end (quarter ellipse over lining_beak_len of path length)
_LPL = cumlen(LP);
_LPT = _LPL[len(_LPL) - 1];
function beak_f(i) = let (s = min(_LPL[i], _LPT - _LPL[i]), t = max(0, min(1, s / lining_beak_len))) sqrt(max(0, 1 - (1 - t) * (1 - t)));
function lining_depth_i(i) = let (d = lining_depth(LP[i])) lining_beak_d + (max(d, lining_beak_d) - lining_beak_d) * beak_f(i);
// sag profile exponent: the car state's passenger side is more convex (padded), blended in over the back corner
function lining_exp(p) = (lining_state == "car" && p[0] > 0)
    ? lining_sag_exp + (lining_car_sag_exp - lining_sag_exp) * _ss(_y_corner + 3, -50, p[1]) : lining_sag_exp;
module lining() sweep([for (i = [0 : len(LP) - 1]) ring(LP[i], LP_N[i], lining_sec(lining_sag(LP[i]), lining_depth_i(i), lining_exp(LP[i])))]);

// =====================================================================================================
echo(str("deck: open edge ", len(OE), " pts (smoothing moved it <= ", round(_oe_dev * 100) / 100,
         " mm), lip section scaled to >= ", round(min(OE_K) * 100) / 100, " near the noses; arch ",
         len(_arch), " pts (smoothing <= ", round(_arch_dev * 100) / 100, " mm); lining ", len(LP), " pts"));
assert(notch_lip_r < notch_lip && notch_lip <= 2 * notch_lip_r, "notch_lip must lie in (notch_lip_r, 2 notch_lip_r]");
assert(arch_roll > deck_vinyl && arch_bottom_r > deck_vinyl && arch_roll + arch_bottom_r <= -z_bf + deck_vinyl,
       "arch rounds do not fit the deck edge");
assert(arch_wrap > arch_bottom_r + ov, "arch_wrap must exceed arch_bottom_r");

if (part == "deck")                            board();
else if (part == "vinyl")                      vinyl();
else if (part == "felt")                       felt();
else if (part == "lip")                        lip();
else if (part == "skirt" || part == "lining")  lining();
else if (part == "skirt_car")                  lining();   // lining_state follows part (car)
else if (part == "notch") {                    // preview only
    color([0.16, 0.16, 0.18]) lip();
    color([0.40, 0.40, 0.42]) lining();
}
else if (part == "all") {                      // preview only
    color([0.12, 0.12, 0.13]) vinyl();
    color([0.62, 0.48, 0.32]) board();
    color([0.25, 0.25, 0.27]) felt();
    color([0.16, 0.16, 0.18]) lip();
    color([0.40, 0.40, 0.42]) lining();
}
else assert(false, str("unknown part: ", part));
