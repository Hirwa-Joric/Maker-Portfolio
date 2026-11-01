// This file defines a later explanatory model; photo/scan tags check it against the finished panel.
// =====================================================================================================
// fittings.scad -- deck fittings for the
//   "Custom Aftermarket Car Center Console Upgrade" — completed-build model
//   (Explanatory assembly model; dimensions approximate).
//
// Parts: clock (black body, chrome bezel, dial, dial centre, white marks + hands), silver push button
// (bezel + face), cup holder (chrome ring + black cup with its dimpled floor), slot (surround with its
// sleeve through the deck), the pocket block under the felt and the metal bar that closes it.
//
// Every part is modelled IN ITS FINAL POSITION in the shared frame of params.scad : mm, origin =
// middle of the notch's back edge at deck-top level (the stitch crease), +x passenger, +y rear, z up,
// deck top z = 0. The frame is LEFT-handed; assemble.py flips y for photo-true renders. Text on the dial
// is therefore modelled mirrored so that it reads correctly AFTER that flip (see photo_true_text).
//
// Export one part at a time (binary STL):
//   openscad --backend manifold --export-format binstl -o clock_body.stl -D 'part="clock_body"' fittings.scad
// part = "clock_body" | "clock_bezel" | "clock_face" | "clock_dial_centre" | "clock_marks"
//        | "button" | "button_face" | "cup_ring" | "cup" | "slot" | "pocket" | "bar"
//        | "all"       (coloured overview of every fitting, previews only)
//        | "all_photo" (the same, mirrored in y so a right-handed viewer shows the car as photographed)
//
// Sources (see GEOMETRY.md section 7): positions, sizes and heights come from params.scad. The
// photos used for the shapes below are named per value: 3483 (in the car, from above), 3486/3487
// (oblique / low side views on the table), 3491/3497/3498 (top views on the table), 3502/3503
// (underside). SEEN = visible in the named photo, INFERRED = a modelling choice.
// No brand marks: the car emblem and red text on the real dial and the USB trident are NOT modelled.
// =====================================================================================================

include <params.scad>

part = "all";
photo_true_text = true;   // true: dial numerals read correctly after assemble.py's y-flip (photo-true).
                          // false: they read correctly in a right-handed viewer of the raw model frame.

// -----------------------------------------------------------------------------------------------------
// Extra values used only in this file (not in params.scad). [P] = photo, [S] = scan, [I] = inferred.
// -----------------------------------------------------------------------------------------------------
eps  = 0.01;
seat = 0.3;               // parts standing on the deck reach this far into the vinyl, so no light gap [I]

// Clock (params: clock_c, clock_body_d 37, clock_d 32.5 bezel, clock_window_d 30.5, clock_t 3, clock_body_t 2.2)
clock_body_bot   = -2.5;  // the black body drops into its Ø36 hole in the leatherette (hidden) [I]
clock_body_edge  = 0.3;   // small rounding on the black body's top edge, so its top reads as a flat glossy black
                          //   ring ~2 mm wide outside the chrome (was 0.8, which rounded it into the
                          //   deck) [P] 3483/3491; 3487 shows ~1.5 of black side under the bezel
clock_bezel_bot  = 1.8;   // bezel sits 0.4 into the body top (no seam gap) [I]
clock_dial_d     = 31;    // dial disc, slightly larger than the window so its edge hides under the bezel [I]
clock_dial_top   = 1.5;   // dial surface 1.5 below the bezel top (window recess) [I] (3487: low puck)
clock_dial_t     = 0.3;
clock_centre_d   = 18;    // light carbon-weave centre disc [P] 3491 ~19, 3483 ~0.58 of the window
clock_baton      = 0.75;              // white hour batons: thin lines [P] 3483 (overlay check)
clock_baton_r    = [9.5, 13.4];       // from the centre disc's edge to the tick track [P] 3483
clock_tick       = [0.35, 0.7];       // minute ticks on the outer track [P] 3491 (small white ticks)
clock_tick_r     = 14.1;
clock_num_size   = 4.4;               // Arabic 12 / 3 / 6 / 9 at the quarters, ~3.2 tall [P] 3483 (white)
clock_num_narrow = 0.72;              // the real numerals are tall and narrow: Liberation Sans Bold squeezed [P] 3483
clock_num_r      = 11.3;
clock_mark_h     = 0.15;              // printed marks stand this proud of the dial (render only)
clock_hour_deg   = 305;               // hands set to 10:10 [I] (the photos show different times)
clock_min_deg    = 60;

// Silver push button (params: button_c, button_head_d 16, button_face_d 12, button_proud 2.5, button_hole_d 12)
button_ring_top  = 2.25;  // polished ring top; the brushed face stands 0.25 above it [P] 3487 (low, flat-topped)
button_edge_r    = 0.6;   // small rounding on the ring's edges [P] 3487/3491/3483
button_chamfer   = 0.8;   // 45 deg chamfer on the polished ring's outer top edge [P] 3483 c4_3483_button (bright
                          //   chamfered ring ~2 wide) [I] 0.6-1
button_gap       = 0.4;   // dark gap between the face and the ring; assemble.py gives the
                          //   gap's floor and walls a black material [P] 3491/3483
button_body_bot  = -10.5; // threaded body ends INSIDE the deck: 3502 shows no switch body below the felt [P]

// Cup holder (params: cup_c, cup_ring_od 84, cup_ring_id 72, cup_ring_crest_d 79, cup_ring_proud 4.5,
//   cup_top_od 73, cup_floor_z -56, cup_depth 60, cup_bottom_d 62, cup_mat_disc_d 25, cup_mat_rings 5)
cup_wall        = 2;      // cup wall, radial [I] (gives a bore of Ø69 at the top, Ø58 at the floor)
cup_out_fillet  = 5;      // rounded outer bottom edge [P] 3502
cup_in_fillet   = 2.5;    // inner floor-to-wall radius [I]
cup_disc_h      = 0.8;    // the smooth centre disc stands this proud of the mat [S] centre -54.4 vs edge -55.5
cup_disc_groove = [0.5, 0.35];   // thin ring outlining the disc (width, depth) [P] 3483/3491
cup_dimple_d    = 1.9;    // small round dimples [P] 3483 c8_3483_cup 1.5-2
cup_dimple_dep  = 0.5;
cup_dimple_pitch= 2.9;    // ring spacing [P] (about 5-6 rings between disc and wall)
cup_dimple_along= 3.6;    // spacing along each ring [P] 3483 ~3.5
cup_dimple_r0   = 14.6;   // first ring radius (just outside the Ø25 disc)

// Slot (params: slot_c, slot_surround 23 x 92, slot_rim 4.2, slot_open 15 x 84, slot_cut 19 x 86, slot_proud 2,
//   slot_depth 36; bar_size 18.5 x 89, bar_t 2.5, bar_hole_dy 52, bar_hole_d 4, bar_top_z -36)
slot_outer_r    = 4.5;    // outer corner radius of the moulded surround [P] 3483 (~R5)
slot_open_r     = 1.5;    // opening corner radius [P] 3483
slot_edge_r     = 1.2;    // rounded outer top edge of the surround [P] 3498/3486
slot_cut_r      = 0.6;    // the sleeve fills the deck cut-out (square in the deck file) [I]
bar_r           = 4;      // rounded ends of the bar [P] 3502/3503
pocket_size     = bar_size;          // the block's footprint equals the bar that caps it [P] 3502/3503
pocket_r        = bar_r;
pocket_top_z    = felt_z + 0.2;      // glued under the felt (0.2 overlap so no seam shows) [I]

// -----------------------------------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------------------------------
module rrect(size, r) {
    rr = max(0.01, min(r, size[0] / 2 - 0.01, size[1] / 2 - 0.01));
    offset(r = rr) square([size[0] - 2 * rr, size[1] - 2 * rr], center = true);
}
module rslab(size, r, z0, h) translate([0, 0, z0]) linear_extrude(height = h) rrect(size, r);
module at(c) translate([c[0], c[1], 0]) children();
// forces a boolean pass, which removes the zero-area triangles rotate_extrude leaves on the axis
module clean() intersection() { children(); translate([-1000, -1000, -1000]) cube(2000); }

// text placed with an explicit 2x2 matrix: model = M * glyph (columns = images of glyph x and glyph y)
module place2d(M, t) multmatrix([[M[0][0], M[0][1], 0, t[0]], [M[1][0], M[1][1], 0, t[1]], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
// upright glyph orientation on the deck: glyph up = toward the front (-y), glyph right = +x
// (photo-true after the y-flip); the alternative is plain OpenSCAD orientation.
M_UP = photo_true_text ? [[1, 0], [0, -1]] : [[1, 0], [0, 1]];

// =====================================================================================================
// CLOCK -- a LOW puck (3 mm), black body Ø36 as its widest part, thin chrome bezel, olive dial.
// =====================================================================================================
// [P] 3483: Arabic 12/3/6/9, white batons, khaki/olive chapter ring, light carbon centre, 12 toward
// the front (-y). [P] 3487: about 1.5 of black body side shows under the bezel. Emblem left out.

module clock_body() {
    rb = clock_body_d / 2;
    rd = clock_dial_d / 2 + 0.1;
    clean() at(clock_c) rotate_extrude($fn = 160)
        difference() {
            union() {
                translate([0, clock_body_bot]) square([rb - clock_body_edge, clock_body_t - clock_body_bot]);
                translate([0, clock_body_bot]) square([rb, clock_body_t - clock_body_bot - clock_body_edge]);
                translate([rb - clock_body_edge, clock_body_t - clock_body_edge]) circle(r = clock_body_edge, $fn = 32);
            }
            // seat for the dial (the dial top ends clock_dial_top above the deck)
            translate([-1, clock_dial_top - clock_dial_t]) square([rd + 1, 10]);
        }
}

module clock_bezel() {
    ro = clock_d / 2;              // 16.75
    ri = clock_window_d / 2;       // 15
    at(clock_c) rotate_extrude($fn = 160)
        offset(r = 0.25, $fn = 16) offset(delta = -0.25)
            polygon([[ri, clock_bezel_bot], [ro, clock_bezel_bot], [ro, clock_t - 0.55],
                     [ro - 0.35, clock_t - 0.2], [ro - 0.9, clock_t], [ri + 0.5, clock_t],
                     [ri, clock_t - 0.3]]);
}

// olive / khaki chapter-ring disc (the whole dial disc)
module clock_face() {
    at(clock_c) translate([0, 0, clock_dial_top - clock_dial_t]) cylinder(d = clock_dial_d, h = clock_dial_t, $fn = 160);
}

// light carbon-weave centre disc, a hair proud of the dial so it does not z-fight
module clock_dial_centre() {
    at(clock_c) translate([0, 0, clock_dial_top - eps]) cylinder(d = clock_centre_d, h = 0.05 + eps, $fn = 128);
}

// white printed marks (batons, ticks, numerals) and the hands with their centre post
module clock_marks() {
    z0 = clock_dial_top - 0.05;
    at(clock_c) {
        // hour batons at every hour except the quarters (numerals there); angle a clockwise from 12,
        // as seen from above in the real car: 12 = -y (front), 3 = +x (passenger)
        for (h = [1 : 11]) if (h % 3 != 0) {
            a = h * 30;
            translate([0, 0, z0]) linear_extrude(clock_mark_h + 0.05)
                polygon(baton_pts(a, clock_baton_r[0], clock_baton_r[1], clock_baton));
        }
        // minute ticks (skip the hour positions)
        for (m = [0 : 59]) if (m % 5 != 0) {
            translate([0, 0, z0]) linear_extrude(clock_mark_h + 0.05)
                polygon(baton_pts(m * 6, clock_tick_r - clock_tick[1] / 2, clock_tick_r + clock_tick[1] / 2, clock_tick[0]));
        }
        // Arabic numerals 12 / 3 / 6 / 9, all upright when the car is seen from behind with the front up
        for (q = [[0, "12"], [90, "3"], [180, "6"], [270, "9"]]) {
            p = dir(q[0]) * clock_num_r;
            translate([0, 0, z0]) linear_extrude(clock_mark_h + 0.05)
                place2d(M_UP, p) scale([clock_num_narrow, 1])
                    text(q[1], size = clock_num_size, font = "Liberation Sans:style=Bold",
                         halign = "center", valign = "center", spacing = 0.95, $fn = 24);
        }
        // hands (light, as in 3483) and centre post
        clock_hand(clock_hour_deg, 7.2, 1.5, 2.0, 1.85);
        clock_hand(clock_min_deg, 11.5, 1.05, 2.4, 2.1);
        translate([0, 0, z0]) cylinder(d = 1.8, h = 2.45 - z0, $fn = 32);
    }
}
// unit vector for a dial angle a (degrees clockwise from 12 as seen from above in the real car)
function dir(a) = [sin(a), -cos(a)];
function baton_pts(a, r0, r1, w) = let (u = dir(a), n = [-u[1], u[0]] * (w / 2))
    [u * r0 + n, u * r1 + n, u * r1 - n, u * r0 - n];
module clock_hand(a, len, w, tail, z) {
    u = dir(a); n = [-u[1], u[0]];
    translate([0, 0, z]) linear_extrude(0.2)
        polygon([-u * tail + n * w / 2, u * (len - w) + n * w / 2, u * len, u * (len - w) - n * w / 2, -u * tail - n * w / 2]);
}

// =====================================================================================================
// SILVER PUSH BUTTON -- polished stainless ring Ø16 with a brushed flat face Ø12, 2.5 proud.
// =====================================================================================================
// [P] 3483/3491/3487. Body ends inside the deck: no switch body below the felt (3502).
module button() {
    rh = button_head_d / 2;            // 8
    rf = button_face_d / 2 + button_gap;
    at(button_c) {
        rotate_extrude($fn = 96)
            union() {
                // ring: flat top from the face gap outward, 45 deg chamfer on the outer top edge, then straight
                // down to the deck; all edges softened by button_edge_r
                offset(r = button_edge_r / 2, $fn = 16) offset(delta = -button_edge_r / 2)
                    polygon([[rf, -seat], [rh, -seat], [rh, button_ring_top - button_chamfer],
                             [rh - button_chamfer, button_ring_top], [rf, button_ring_top]]);
                // ring floor under the face
                translate([0, -seat]) square([rf + eps, 1.0 + seat]);
            }
        // threaded body through the deck (rings stand in for the thread; hidden in the board)
        rotate_extrude($fn = 64)
            polygon(concat([[0, button_body_bot], [button_hole_d / 2 - 0.45, button_body_bot]],
                [for (i = [0 : 12]) each [[button_hole_d / 2, button_body_bot + i * 0.75 + 0.375],
                                          [button_hole_d / 2 - 0.45, button_body_bot + (i + 1) * 0.75]]],
                [[button_hole_d / 2 - 0.45, -seat + eps], [0, -seat + eps]]));
    }
}
module button_face() {
    rf = button_face_d / 2;
    clean() at(button_c) rotate_extrude($fn = 96)
        polygon([[0, 0.9], [rf, 0.9], [rf, button_proud - 0.3], [rf - 0.3, button_proud], [0, button_proud]]);
}

// =====================================================================================================
// CUP HOLDER -- chrome rolled lip OD 84 / ID 72, crest Ø79 at +4.5; black cup, floor -56, bottom -60.
// =====================================================================================================
// Ring profile: two quarter-ellipses meeting at the crest (inner 36 -> 39.5, outer 39.5 -> 42), the
// outer flank steeper, as in the low side view 3487 [P]. The ring rests on the deck and on the cup rim.
module cup_ring() {
    ri = cup_ring_id / 2; ro = cup_ring_od / 2; rc = cup_ring_crest_d / 2; h = cup_ring_proud;
    inner_offset = rc - ri; ao = ro - rc;
    at(cup_c) rotate_extrude($fn = 200)
        polygon(concat(
            [[ri, -seat]],
            [for (t = [180 : -7.5 : 90]) [rc + inner_offset * cos(t), h * sin(t)]],
            [for (t = [82.5 : -7.5 : 0]) [rc + ao * cos(t), h * sin(t)]],
            [[ro, -seat]]));
}

// Black drop-in cup: Ø73 under the ring tapering to Ø62 at the bottom (z -60), rounded bottom edge,
// bore Ø69 -> Ø58 at the floor (z -56). Floor mat: smooth Ø25 centre disc outlined by a thin ring,
// surrounded by about 5 rings of small round dimples [P] 3483/3491; [S] floor -54.4 (centre) / -55.5.
module cup() {
    zb  = -cup_depth;                         // -60 outside bottom
    zf  = cup_floor_z;                        // -56 inside floor
    rto = cup_top_od / 2;                     // 36.5
    rbo = cup_bottom_d / 2;                   // 31
    rti = rto - cup_wall;                     // 34.5
    rbi = rbo - cup_wall;                     // 29 (floor radius)
    at(cup_c) difference() {
        union() {
            difference() {
                // outer body
                rotate_extrude($fn = 200)
                    hull() {
                        translate([0, -eps]) square([rto, eps]);
                        translate([0, zb]) square([rbo - cup_out_fillet, cup_out_fillet]);
                        translate([rbo - cup_out_fillet, zb + cup_out_fillet]) circle(r = cup_out_fillet, $fn = 48);
                    }
                // bore, open at the top
                rotate_extrude($fn = 200)
                    hull() {
                        translate([0, 0]) square([rti, 1]);
                        translate([0, zf]) square([rbi - cup_in_fillet, cup_in_fillet]);
                        translate([rbi - cup_in_fillet, zf + cup_in_fillet]) circle(r = cup_in_fillet, $fn = 32);
                    }
            }
            // smooth centre disc of the floor mat
            translate([0, 0, zf - eps]) cylinder(d = cup_mat_disc_d, h = cup_disc_h + eps, $fn = 128);
        }
        // thin ring outlining the disc
        translate([0, 0, zf + cup_disc_h - cup_disc_groove[1]])
            difference() {
                cylinder(r = cup_mat_disc_d / 2 - 1.0, h = 1, $fn = 128);
                translate([0, 0, -1]) cylinder(r = cup_mat_disc_d / 2 - 1.0 - cup_disc_groove[0], h = 3, $fn = 128);
            }
        // dimples, cup_mat_rings rings
        for (k = [0 : cup_mat_rings - 1]) {
            r = cup_dimple_r0 + k * cup_dimple_pitch;
            n = round(2 * PI * r / cup_dimple_along);
            for (i = [0 : n - 1]) rotate([0, 0, (i + 0.5 * (k % 2)) * 360 / n])
                translate([r, 0, zf + cup_dimple_d / 2 - cup_dimple_dep]) sphere(d = cup_dimple_d, $fn = 12);
        }
    }
}

// =====================================================================================================
// SLOT -- black moulded surround 23 x 92 (rims 4.2), 2 proud; opening 15 x 84 straight down to the bar.
// =====================================================================================================
module slot() {
    at(slot_c) difference() {
        union() {
            // flange: straight foot, then a rounded outer top edge (stack of offset slabs, hulled)
            hull() {
                rslab(slot_surround, slot_outer_r, -seat, slot_proud - slot_edge_r + seat);
                for (t = [15 : 15 : 90]) {
                    d = slot_edge_r * (1 - cos(t));
                    rslab([slot_surround[0] - 2 * d, slot_surround[1] - 2 * d], slot_outer_r - d,
                          slot_proud - slot_edge_r + slot_edge_r * sin(t) - eps, eps);
                }
            }
            // sleeve through the deck cut-out, down to the felt
            rslab(slot_cut, slot_cut_r, felt_z, -felt_z + eps);
        }
        // opening
        rslab(slot_open, slot_open_r, felt_z - 1, -felt_z + slot_proud + 2);
        // small chamfer on the inner top edge
        hull() {
            rslab(slot_open, slot_open_r, slot_proud - 0.5, eps);
            rslab([slot_open[0] + 1.0, slot_open[1] + 1.0], slot_open_r + 0.5, slot_proud, 0.5);
        }
    }
}

// Pocket block under the felt: a black tube continuing the opening down to the bar (bar top = slot floor).
module pocket() {
    at(slot_c) difference() {
        rslab(pocket_size, pocket_r, bar_top_z, pocket_top_z - bar_top_z);
        rslab(slot_open, slot_open_r, bar_top_z - 1, pocket_top_z - bar_top_z + 2);
    }
}

// Matte worn-grey metal bar closing the pocket; two EMPTY holes 52 apart along y [P] 3502/3503/3483.
module bar() {
    at(bar_c) difference() {
        rslab(bar_size, bar_r, bar_top_z - bar_t, bar_t);
        for (s = [-1, 1]) translate([0, s * bar_hole_dy / 2, bar_top_z - bar_t - 1]) cylinder(d = bar_hole_d, h = bar_t + 2, $fn = 32);
    }
}

// =====================================================================================================
// Part selector
// =====================================================================================================
module all_fittings() {
    color([0.05, 0.05, 0.06]) clock_body();
    color([0.86, 0.87, 0.90]) clock_bezel();
    color([0.55, 0.55, 0.40]) clock_face();
    color([0.80, 0.80, 0.74]) clock_dial_centre();
    color([0.97, 0.97, 0.95]) clock_marks();
    color([0.82, 0.83, 0.85]) button();
    color([0.70, 0.71, 0.72]) button_face();
    color([0.88, 0.89, 0.92]) cup_ring();
    color([0.10, 0.10, 0.11]) cup();
    color([0.08, 0.08, 0.09]) slot();
    color([0.14, 0.14, 0.15]) pocket();
    color([0.42, 0.42, 0.43]) bar();
}

if      (part == "clock_body")        clock_body();
else if (part == "clock_bezel")       clock_bezel();
else if (part == "clock_face")        clock_face();
else if (part == "clock_dial_centre") clock_dial_centre();
else if (part == "clock_marks")       clock_marks();
else if (part == "button")            button();
else if (part == "button_face")       button_face();
else if (part == "cup_ring")          cup_ring();
else if (part == "cup")               cup();
else if (part == "slot")              slot();
else if (part == "pocket")            pocket();
else if (part == "bar")               bar();
else if (part == "all")               all_fittings();
else if (part == "all_photo")         mirror([0, 1, 0]) all_fittings();
else echo(str("fittings.scad: unknown part \"", part, "\""));
