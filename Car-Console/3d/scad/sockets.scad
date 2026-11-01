// This file defines a later explanatory model; photo/scan tags check it against the finished panel.
// =====================================================================================================
// sockets.scad -- socket plate for the
//   "Custom Aftermarket Car Center Console Upgrade" — completed-build model
//   (Explanatory assembly model; dimensions approximate).
//
// Black plate (40.5 x 102, four Phillips screws) carrying a USB charger socket at the front (cap
// CLOSED, as on 3 Oct) and a 12 V socket with a red face ring and a torn cap at the rear.
//
// Every part is modelled IN ITS FINAL POSITION in the shared frame of params.scad : mm, origin =
// middle of the notch's back edge at deck-top level, +x passenger, +y rear, z up, deck top z = 0.
// The frame is LEFT-handed and assemble.py flips y for photo-true renders, so all lettering here is
// modelled mirrored to read correctly AFTER that flip (photo_true_text = true).
//
// Export one part at a time (binary STL):
//   openscad --backend manifold --export-format binstl -o plate.stl -D 'part="plate"' sockets.scad
// part = "plate" | "screws" (-> plate_screws.stl) | "usb" | "usb_body" | "usb_ring" | "usb_cap"
//        | "v12" | "v12_body" | "v12_ring" | "v12_cap"
//        | "all" (coloured overview, previews only) | "all_photo" (the same, mirrored in y = as photographed)
//        | "context" (all + a see-through deck slab, previews only)
//
// Photos (SEEN): 3483 (in the car from above: plate, screws, cap lettering, hinge at +x, pull tab at -x,
// red ring, chrome mouth, torn cap with cigarette icon, flap remnant and plate notch at +x),
// 3486 (oblique: plate thickness, the USB's flange + cap, the low 12 V ring), 3491/3497/3498 (top views),
// 3502/3503 (underside: USB dark grey body with a nut, 12 V zinc threaded cup with a yellowish insulator).
// The USB trident logo printed on the real cap is NOT modelled (no logos); its "USB" / "CHARGER" words are.
// the plate and EVERYTHING on it turn by params plate_rot (1.2 deg, rear end toward -x) about
// plate_c (on_plate()); the 12 V cap sits off-centre (toward the front, a little +x) so the chrome mouth shows only
// as a crescent (3483/3491/3497); the 12 V body below the felt is a round yellow-zinc threaded cup with a round ring nut (3502),
// not a large hex nut.
// =====================================================================================================

include <params.scad>

part = "all";
photo_true_text = true;   // see the header
usb_cap_open    = false;  // false = closed, as photographed on 3 Oct. true = swung open over its hinge
                          // (shows the ports, the blue ring and the PD / QC3.0 labels)
usb_cap_open_angle = 180;   // swing of the open cap about its hinge [P] IMG_3439: flipped right over toward the
                            // cup holder, inside face up, lying almost flat (the old value was 165)
usb_cap_open_reach = 8;     // open cap slid out by its stretched strap [P] IMG_3439: ~10 mm gap between the
                            // socket flange and the open cap

// -----------------------------------------------------------------------------------------------------
// Extra values used only in this file (not in params.scad). [P] photo, [S] scan, [T] tape, [I] inferred.
// -----------------------------------------------------------------------------------------------------
eps    = 0.01;
seat   = 0.3;                // parts standing on the deck reach this far into the vinyl [I]
z_top  = plate_t;            // plate top, 4 [S]
z_felt = felt_z;             // felt underside, -12

// Plate
plate_edge_r  = 0.8;         // softened top edge [P] 3486
plate_notch   = [2.4, 13];   // notch in the plate's +x edge beside the 12 V socket (depth across, length
                             //   along y) [P] 3483 2.4 x 12.8; the socket's hinge block sits in it
plate_notch_dy= -0.5;        // notch centre relative to v12_c[1] [P] 3483

// Screws
screw_head_d  = 6.6;         // Phillips pan heads [P] 3483 6.5-7
screw_head_h  = 1.6;         // [I]
screw_len     = 10;          // shank into the deck board [I]

// USB socket (B05)
usb_bezel_d   = 35;          // black flange on the plate [P] 3483 35-36 (seen under the cap's rear edge)
usb_bezel_top = 8.0;         // flange top [P] 3486 (flange + cap stack); cap top = usb_cap_top_z 11 [S]
usb_bezel_er  = 1.5;         // rounded top edge
usb_lip_id    = 31;          // inner edge of the flange lip
usb_face_z    = 6.6;         // port face, recessed below the flange top [I]
usb_cap_d     = 33.5;        // cap disc incl. its dark rim [P] 3483 33.5
usb_cap_bot   = 8.0;
usb_cap_rim_w = 1.0;         // raised rim round the cap top [P] 3483
usb_cap_inner_d = 21;        // embossed inner circle [P] 3483 21
usb_cap_text  = ["USB", "CHARGER"];   // words on the cap [P] 3483 (trident logo omitted)
usb_hinge     = [15.2, 21.7, 11];     // hinge block at +x: x from, x to (local), length along y [P] 3483:
                                      //   overhangs the plate edge (20.25) by ~1.5, ~11 long
usb_hinge_top = 9.8;
usb_tab_r     = 4.65;        // semicircular pull tab at -x, 9.3 wide, reaching 2.8 past the plate edge [P] 3483
usb_tab_x     = -18.4;       //   centre of its round end (local x) -> tip at -23
usb_tab_z     = [8.3, 9.5];
// ports and labels under the cap, visible in IMG_3427/3439
usb_ring_od   = 29;  usb_ring_w = 1.0;  usb_ring_h = 1.0;  usb_ring_sink = 0.8;
usbc_x        = 6.5;          usba_x = -6.0;
usbc_open     = [3.26, 8.94]; usba_open = [5.0, 12.5];
// below the deck [P] 3502/3503: dark grey round body with a nut, push-on tabs
usb_body_d    = 28;   usb_body_bot = -30;
usb_nut_af    = 30;   usb_nut_t    = 5;
usb_tab_len   = 8;

// 12 V socket (B06) (params: v12_ring_d 35, v12_mouth_d 25, v12_top_z 10)
v12_ring_top  = 6.6;         // red ring top, low [P] 3486 (ring well below the USB cap) [S] ring 5-7
v12_ring_id   = 25.7;
v12_lip_od    = 25.5;        // chrome mouth lip [P] 3483 26.4 outer / 22 inner
v12_lip_top   = 8.4;         // [P] 3486 [S]
v12_bore      = 21;          // standard bore
v12_depth     = 40;          // bore depth from the lip top [I] (standard socket)
v12_cup_d     = 25;          // zinc threaded cup [P] 3502/3503
v12_ring_nut  = [29, 4.5, 24];   // round ring nut on the felt: diameter, thickness, knurl grooves [P] 3502 (round, no hex) [I] size
v12_cap_d     = 21.8;        // cap head [P] 3483 (chrome visible 22-26.4)
v12_cap_off   = [0.9, -1.5];  // the torn cap head sits off-centre in the mouth , ~1.75 toward the front
                             //   and a little toward +x, so the chrome lip shows only as a crescent on the far side:
                             //   3483 (car) crescent on the -x / rear side, 3491 (table) chrome on the rear (+y) side,
                             //   the cap toward the front. The loose torn cap may sit a little differently in the two
                             //   photos (x component: 3483 +x, 3491 slightly -x); the front offset is common [P] 1.5-2
v12_cap_top   = 9.0;         // head top; its raised centre reaches v12_top_z (10) [S]
v12_cap_centre_d = 15.5;     // raised centre with the cigarette icon [P] 3483 15.5
v12_tear      = [-75, -25];  // torn-away part of the cap head, angles (deg from +x toward +y): toward
                             //   +x / front, "1-2 o'clock" seen from behind [P] 3483/3486
v12_flap      = [17.5, 24.0, 4.0, -1.5]; // flap remnant: local x from, x to, width along y, centre y [P] 3483 (overlay check)
v12_hinge_blk = [17.9, 20.3, 12];        // hinge block in the plate notch: x from, x to, length along y [P] 3483

usb_rim_top   = usb_bezel_top;
v12_bore_bot  = v12_lip_top - v12_depth;     // -31.6
v12_cup_bot   = v12_bore_bot - 2;            // -33.6

// -----------------------------------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------------------------------
module rrect(size, r) { rr = max(0.01, min(r, size[0] / 2 - 0.01, size[1] / 2 - 0.01));
                        offset(r = rr) square([size[0] - 2 * rr, size[1] - 2 * rr], center = true); }
module stadium(w, l) { hull() for (s = [-1, 1]) translate([0, s * (l - w) / 2]) circle(d = w, $fn = 32); }
module ring2d(od, id) { difference() { circle(d = od); circle(d = id); } }
module at(c) translate([c[0], c[1], 0]) children();
// a part laid out at c on the unturned plate, moved and turned with the plate (params plate_rot about plate_c)
module on_plate(c) { q = plate_xf(c); translate([q[0], q[1], 0]) rotate([0, 0, plate_rot]) children(); }
// forces a boolean pass, which removes the zero-area triangles rotate_extrude leaves on the axis
module clean() intersection() { children(); translate([-1000, -1000, -1000]) cube(2000); }
usb_core_d   = 27.5;   // port block inside the plate/deck hole, below the port face (hidden) [I]
usb_core_bot = -4;
module place2d(M, t) multmatrix([[M[0][0], M[0][1], 0, t[0]], [M[1][0], M[1][1], 0, t[1]], [0, 0, 1, 0], [0, 0, 0, 1]]) children();

// Lettering orientation, model = M * glyph. In the real car seen from above with the front up:
// +x = right, +y = down. "Tops toward +x, reading toward +y" is the cap's USB / CHARGER and the PD label.
function M_tops(dirx) = photo_true_text
    ? (dirx > 0 ? [[0, 1], [1, 0]] : [[0, -1], [-1, 0]])       // tops +x reading +y  /  tops -x reading -y
    : (dirx > 0 ? [[0, 1], [-1, 0]] : [[0, -1], [1, 0]]);      // plain right-handed equivalents
// glyph on an arc at angle a (0 = the -x side, positive toward +y), tops toward the centre
function M_arc(a) = photo_true_text ? [[sin(a), cos(a)], [cos(a), -sin(a)]] : [[-sin(a), cos(a)], [-cos(a), -sin(a)]];
arc_sense = photo_true_text ? 1 : -1;   // letter order along the arc so the word reads the right way

module threaded_rod(d, z0, z1, pitch = 1.5, depth = 0.5) {
    difference() {
        translate([0, 0, z0]) cylinder(d = d, h = z1 - z0, $fn = 64);
        for (z = [z0 + pitch : pitch : z1 - pitch / 2])
            translate([0, 0, z]) rotate_extrude($fn = 64)
                polygon([[d / 2 + 0.3, -pitch * 0.38], [d / 2 - depth, 0], [d / 2 + 0.3, pitch * 0.38]]);
    }
}
module hex_nut(af, t, z0) {
    r0 = 0.485 * af;
    translate([0, 0, z0]) intersection() {
        cylinder(d = af / cos(30), h = t, $fn = 6);
        cylinder(h = t, r1 = r0, r2 = r0 + t * tan(60), $fn = 64);
        cylinder(h = t, r1 = r0 + t * tan(60), r2 = r0, $fn = 64);
    }
}
function screw_pts() = [for (sx = [-1, 1], sy = [-1, 1])        // unturned layout; place with on_plate()
    [plate_c[0] + sx * plate_screw_dx / 2, plate_c[1] + sy * plate_screw_dy / 2]];

// =====================================================================================================
// PLATE: black matte 40.5 x 102, R5, 4 thick, softened top edge, notch at the 12 V hinge
// =====================================================================================================
module plate() on_plate(plate_c) translate([-plate_c[0], -plate_c[1], 0]) {   // laid out unturned, turned as one
    difference() {
        at(plate_c) hull() {
            translate([0, 0, -seat]) linear_extrude(z_top + seat - plate_edge_r) rrect(plate_size, plate_r);
            translate([0, 0, -seat]) linear_extrude(z_top + seat) rrect(plate_size - [2 * plate_edge_r, 2 * plate_edge_r], plate_r - plate_edge_r);
        }
        for (c = [usb_c, v12_c]) at(c) translate([0, 0, -1]) cylinder(d = socket_hole_d, h = z_top + 2, $fn = 96);
        for (p = screw_pts())    at(p) translate([0, 0, -1]) cylinder(d = plate_screw_d, h = z_top + 2, $fn = 24);
        // notch in the +x edge beside the 12 V socket
        translate([plate_c[0] + plate_size[0] / 2 - plate_notch[0], v12_c[1] + plate_notch_dy - plate_notch[1] / 2, -1])
            cube([plate_notch[0] + 1, plate_notch[1], z_top + 2]);
    }
}

// =====================================================================================================
// SCREWS: Phillips pan heads, shank into the board
// =====================================================================================================
module plate_screw() {
    r = screw_head_d / 2;
    difference() {
        union() {
            rotate_extrude($fn = 48) polygon(concat([[0, z_top - 0.2], [r, z_top - 0.2], [r, z_top + 0.5]],
                [for (a = [10 : 10 : 90]) [r * cos(a), z_top + 0.5 + (screw_head_h - 0.5) * sin(a)]]));
            translate([0, 0, -screw_len]) cylinder(d = plate_screw_d - 0.1, h = screw_len + z_top, $fn = 24);
        }
        translate([0, 0, z_top + screw_head_h - 0.7]) linear_extrude(2) {
            square([3.6, 0.75], center = true);
            square([0.75, 3.6], center = true);
        }
    }
}
module screws() for (p = screw_pts()) on_plate(p) plate_screw();

// =====================================================================================================
// USB SOCKET (local frame = socket centre)
// =====================================================================================================
// Black flange with the port face inside, and the hinge lugs at +x.
module usb_local() clean() {
    R = usb_bezel_d / 2; rr = usb_bezel_er;
    difference() {
        union() {
            translate([0, 0, usb_core_bot]) cylinder(d = usb_core_d, h = z_top - usb_core_bot, $fn = 96);
            rotate_extrude($fn = 128) polygon(concat(
                [[0, z_top - seat], [R, z_top - seat]],
                [for (a = [0 : 15 : 90]) [R - rr + rr * cos(a), usb_rim_top - rr + rr * sin(a)]],
                [[usb_lip_id / 2 + 0.4, usb_rim_top], [usb_lip_id / 2, usb_rim_top - 0.4],
                 [usb_lip_id / 2, usb_face_z], [0, usb_face_z]]));
            // hinge lugs at +x (two lugs with a gap for the cap's knuckle)
            difference() {
                translate([0, 0, z_top - 0.1]) linear_extrude(usb_hinge_top - z_top + 0.1)
                    translate([(usb_hinge[0] + usb_hinge[1]) / 2, 0]) rrect([usb_hinge[1] - usb_hinge[0], usb_hinge[2]], 0.8);
                translate([usb_hinge[1] - 4.2, -1.9, usb_hinge_top - 2.6]) cube([5, 3.8, 3]);
            }
        }
        // groove for the blue ring
        translate([0, 0, usb_face_z - usb_ring_sink]) linear_extrude(usb_ring_sink + 1)
            ring2d(usb_ring_od + 0.2, usb_ring_od - 2 * usb_ring_w - 0.2);
        // port openings
        translate([usbc_x, 0, usb_face_z - 8]) linear_extrude(9) stadium(usbc_open[0], usbc_open[1]);
        translate([usba_x, 0, usb_face_z - 9]) linear_extrude(10) rrect(usba_open, 0.5);
    }
    // contact tongues inside the ports, standing on the port floors
    translate([usbc_x, 0, usb_face_z - 8.5]) linear_extrude(8.5 - 1.0) square([0.7, 6.6], center = true);
    translate([usba_x + 0.9, 0, usb_face_z - 9.5]) linear_extrude(9.5 - 1.5) square([1.9, 11.0], center = true);
}

// Below the plate: dark grey threaded body, nut tightened against the felt, rear cap and two tabs.
module usb_body_local() clean() {
    union() {
        threaded_rod(usb_body_d, usb_body_bot, usb_core_bot + 0.5);
        hex_nut(usb_nut_af, usb_nut_t, z_felt - usb_nut_t);
        translate([0, 0, usb_body_bot - 2]) cylinder(d = usb_body_d - 4, h = 2 + eps, $fn = 64);
        for (sx = [-1, 1]) translate([sx * 5 - 0.4, -3.15, usb_body_bot - 2 - usb_tab_len])
            difference() {
                cube([0.8, 6.3, usb_tab_len + 0.5]);
                translate([-1, 3.15, 2.5]) rotate([0, 90, 0]) cylinder(d = 1.6, h = 3, $fn = 24);
            }
    }
}

// Blue LED ring in the port face, with the printed PD / QC3.0 labels (they light with the ring).
// Labels: tops pointing AWAY from their ports (PD on the +x side of the USB-C port -> tops +x;
// QC3.0 on the -x side of the USB-A port -> tops -x), reading along the ports.
module usb_ring_local() {
    translate([0, 0, usb_face_z - usb_ring_sink]) linear_extrude(usb_ring_h)
        ring2d(usb_ring_od, usb_ring_od - 2 * usb_ring_w);
    usb_labels();
}
module usb_labels() {
    f  = "Liberation Sans:style=Bold";
    lw = 0.35;                    // bracket line width
    lx = usbc_x + 3.0;            // PD bracket line, +x of the USB-C port
    sy = 6.0;                     // bracket ends, beyond the port ends (+-4.47)
    translate([0, 0, usb_face_z - 0.05]) linear_extrude(0.25) {
        place2d(M_tops(+1), [lx + 1.7, 0])
            text("PD", size = 2.0, font = f, spacing = 1.1, halign = "center", valign = "center", $fn = 16);
        // bracket round the USB-C port, open toward the port
        translate([lx - lw / 2, -sy]) square([lw, 2 * sy]);
        for (s = [-1, 1]) translate([usbc_x - 1.4, s * sy - lw / 2]) square([lx - usbc_x + 1.4 + lw / 2, lw]);
        place2d(M_tops(-1), [usba_x - 4.4, 0])
            text("QC3.0", size = 1.9, font = f, spacing = 1.1, halign = "center", valign = "center", $fn = 16);
    }
}

// Rubber cap, CLOSED (local frame): disc with a raised rim, embossed inner circle and lettering,
// strap + knuckle into the hinge lugs at +x, semicircular pull tab at -x.
module usb_cap_closed_local() clean() {
    R  = usb_cap_d / 2;
    zt = usb_cap_top_z - 0.4;                 // cap face 10.6; rim and lettering reach usb_cap_top_z (11)
    difference() {
        union() {
            // disc, rounded edge
            rotate_extrude($fn = 128) intersection() {
                offset(r = 0.8, $fn = 16) offset(delta = -0.8) translate([-1, usb_cap_bot]) square([R + 1, zt - usb_cap_bot]);
                translate([0, usb_cap_bot - 1]) square([R + 1, zt - usb_cap_bot + 2]);
            }
            // raised rim
            translate([0, 0, zt - eps]) rotate_extrude($fn = 128)
                translate([R - 0.6 - usb_cap_rim_w, 0]) offset(r = 0.2, $fn = 12) offset(delta = -0.2)
                    square([usb_cap_rim_w, usb_cap_top_z - zt + eps]);
            // skirt that drops inside the flange lip
            translate([0, 0, usb_face_z + 0.4]) linear_extrude(usb_cap_bot - usb_face_z - 0.4 + eps)
                ring2d(usb_lip_id - 0.4, usb_lip_id - 2.6);
            // lettering, raised 0.3 (tops toward +x, reading front to rear) [P] 3483
            translate([0, 0, zt - eps]) linear_extrude(0.3 + eps) {
                place2d(M_tops(+1), [6.0, 0])
                    text(usb_cap_text[0], size = 3.6, font = "Liberation Sans:style=Bold", halign = "center", valign = "center", $fn = 16);
                // "CHARGER" on an arc on the -x side, tops toward the centre
                n = len(usb_cap_text[1]);
                for (i = [0 : n - 1]) let (a = arc_sense * (i - (n - 1) / 2) * 17, rr = 7.6)
                    place2d(M_arc(a), [-rr * cos(a), rr * sin(a)])
                        text(usb_cap_text[1][i], size = 2.0, font = "Liberation Sans:style=Bold", halign = "center", valign = "center", $fn = 12);
            }
            // pull tab at -x
            translate([0, 0, usb_tab_z[0]]) linear_extrude(usb_tab_z[1] - usb_tab_z[0])
                hull() {
                    translate([usb_tab_x, 0]) circle(r = usb_tab_r, $fn = 48);
                    translate([-R + 2, -usb_tab_r]) square([0.1, 2 * usb_tab_r]);
                }
            // strap to the hinge and the knuckle (sits in the lugs' gap)
            translate([R - 2, -1.7, zt - 1.2]) cube([usb_hinge[1] - 3.2 - R + 2, 3.4, 1.2]);
            hull() {
                translate([usb_hinge[1] - 4.2, -1.7, zt - 1.2]) cube([1, 3.4, 1.2]);
                translate([usb_hinge[1] - 2.2, 0, usb_hinge_top - 1.2]) rotate([90, 0, 0]) cylinder(r = 1.1, h = 3.4, center = true, $fn = 32);
            }
        }
        // embossed inner circle (thin groove)
        translate([0, 0, zt - 0.25]) linear_extrude(1) ring2d(usb_cap_inner_d + 0.25, usb_cap_inner_d - 0.25);
    }
}
module usb_cap_open_local() {
    hx = usb_hinge[1] - 2.2; hz = usb_hinge_top - 1.2;
    zt = usb_cap_top_z - 0.4;
    // flipped over the knuckle, then slid out along +x by the stretched strap, with the strap bridging the gap
    translate([usb_cap_open_reach, 0, 0])
        translate([hx, 0, hz]) rotate([0, usb_cap_open_angle, 0]) translate([-hx, 0, -hz]) usb_cap_closed_local();
    if (usb_cap_open_reach > 0)
        translate([hx - 1, -1.7, 2 * hz - zt]) cube([usb_cap_open_reach + 2, 3.4, 1.2]);
}

// =====================================================================================================
// 12 V SOCKET (local frame = socket centre)
// =====================================================================================================
// Polished chrome mouth lip (above the plate) with the upper bore
module v12_local() clean() {
    rotate_extrude($fn = 128) polygon(concat(
        [[v12_bore / 2, z_top - seat - 1.5], [v12_lip_od / 2, z_top - seat - 1.5]],
        [for (a = [0 : 15 : 90]) [v12_lip_od / 2 - 1.0 + 1.0 * cos(a), v12_lip_top - 1.0 + 1.0 * sin(a)]],
        [[v12_bore / 2 + 0.6, v12_lip_top], [v12_bore / 2, v12_lip_top - 0.6]]));
}
// Zinc threaded cup through plate and deck, nut on the felt, yellowish insulator, stud and tabs
module v12_body_local() {
    difference() {
        union() {
            threaded_rod(v12_cup_d, v12_cup_bot, z_top - 1.7);
            // round ring nut tightened against the felt, fine knurl round its edge (3502: round, yellow zinc)
            translate([0, 0, z_felt - v12_ring_nut[1]]) difference() {
                cylinder(d = v12_ring_nut[0], h = v12_ring_nut[1] + eps, $fn = 96);
                for (k = [0 : v12_ring_nut[2] - 1]) rotate([0, 0, k * 360 / v12_ring_nut[2]])
                    translate([v12_ring_nut[0] / 2, 0, -1]) cylinder(d = 1.2, h = v12_ring_nut[1] + 2, $fn = 12);
            }
        }
        translate([0, 0, v12_bore_bot]) cylinder(d = v12_bore, h = v12_depth, $fn = 64);
    }
    translate([0, 0, v12_bore_bot - eps]) cylinder(d = 7, h = 2.0, $fn = 32);                 // centre contact
    translate([0, 0, v12_cup_bot - 0.8]) cylinder(d = v12_bore, h = 0.8 + eps, $fn = 64);     // insulator disc
    translate([0, 0, v12_cup_bot - 9]) cylinder(d = 4, h = 9 + eps, $fn = 24);               // stud
    translate([0, 0, v12_cup_bot - 4.6]) cylinder(d = 7 / cos(30), h = 3.2 + eps, $fn = 6);  // nut on the stud
    translate([3.6, -3.15, v12_cup_bot - 10.4]) cube([0.8, 6.3, 9.3]);                        // push-on tab
}
// Red face ring (translucent red), low
module v12_ring_local() clean() {
    c = 1.2; ro = v12_ring_d / 2; ri = v12_ring_id / 2;
    rotate_extrude($fn = 128) polygon(concat(
        [[ri, z_top - seat], [ro, z_top - seat]],
        [for (a = [0 : 15 : 90]) [ro - c + c * cos(a), v12_ring_top - c + c * sin(a)]],
        [[ri + 0.4, v12_ring_top], [ri, v12_ring_top - 0.4]]));
}
// Cigarette pictogram, built directly in model coordinates: in the real car seen from behind the
// cigarette runs from upper left (filter end, smoke above it) to lower right (glowing tip) [P] 3483.
module cigarette_icon() {
    u = [1, 1] / sqrt(2);  n = [u[1], -u[0]];          // along the cigarette / across it
    module seg(p0, p1, w) hull() { translate(p0) circle(d = w, $fn = 12); translate(p1) circle(d = w, $fn = 12); }
    seg(-u * 4.2, u * 2.2, 1.5);                       // cigarette body
    seg(u * 3.0, u * 4.4, 1.5);                        // glowing tip, separated by a small gap
    // two smoke wisps above the filter end (toward -y in the real car = image up)
    for (k = [0, 1]) translate(-u * 4.0 + [-0.6 + 1.6 * k, -1.6]) seg([0, 0], [0.7, -1.4], 0.55);
}
// Torn cap: plug in the bore, head inside the chrome lip with a torn-away segment, raised centre with
// the icon; the hinge block in the plate notch and the torn flap remnant sticking out at +x.
module v12_cap_local() {
    difference() {
        union() {
            translate([0, 0, v12_lip_top - 3.5]) cylinder(d = v12_bore - 0.4, h = 3.5 + eps, $fn = 64);   // plug in the bore
            translate([v12_cap_off[0], v12_cap_off[1], 0]) {  // head, off-centre (covers the lip on that side)
                hull() {
                    translate([0, 0, v12_lip_top - 0.4]) cylinder(d = v12_cap_d, h = v12_cap_top - v12_lip_top + 0.4 - 0.4, $fn = 96);
                    translate([0, 0, v12_lip_top - 0.4]) cylinder(d = v12_cap_d - 0.8, h = v12_cap_top - v12_lip_top + 0.4, $fn = 96);
                }
                translate([0, 0, v12_cap_top - eps]) cylinder(d = v12_cap_centre_d, h = v12_top_z - 0.3 - v12_cap_top + eps, $fn = 96);
                translate([0, 0, v12_top_z - 0.3 - eps]) linear_extrude(0.3 + eps) cigarette_icon();
            }
        }
        // torn-away segment of the head (outside the raised centre), with a ragged edge
        translate([v12_cap_off[0], v12_cap_off[1], v12_lip_top - 4]) linear_extrude(10)
            difference() {
                polygon([[0, 0], for (a = [v12_tear[0] : 5 : v12_tear[1]]) (20 + ((a / 5) % 2 == 0 ? 0 : -9.87)) * [cos(a), sin(a)]]);
                circle(d = v12_cap_centre_d + 1.2, $fn = 64);
            }
    }
    // hinge block in the plate notch (top a little below the plate top)
    translate([v12_hinge_blk[0], plate_notch_dy - v12_hinge_blk[2] / 2, -seat])
        cube([v12_hinge_blk[1] - v12_hinge_blk[0], v12_hinge_blk[2], z_top - 0.5 + seat]);
    // flap remnant: thin strip from the ring edge out past the plate edge, drooping toward the deck
    hull() {
        translate([v12_flap[0], v12_flap[3] - v12_flap[2] / 2, z_top + 0.2]) cube([0.5, v12_flap[2], 0.9]);
        translate([v12_flap[1] - 0.5, v12_flap[3] - v12_flap[2] / 2 + 0.3, 1.4]) cube([0.5, v12_flap[2] - 0.6, 0.8]);
    }
}

// =====================================================================================================
// Placed parts
// =====================================================================================================
module usb()      on_plate(usb_c) usb_local();
module usb_body() on_plate(usb_c) usb_body_local();
module usb_ring() on_plate(usb_c) usb_ring_local();
module usb_cap()  on_plate(usb_c) if (usb_cap_open) usb_cap_open_local(); else usb_cap_closed_local();
module v12()      on_plate(v12_c) v12_local();
module v12_body() on_plate(v12_c) v12_body_local();
module v12_ring() on_plate(v12_c) v12_ring_local();
module v12_cap()  on_plate(v12_c) v12_cap_local();

module all_parts() {
    color([0.12, 0.12, 0.12]) plate();
    color([0.55, 0.55, 0.57]) screws();
    color([0.09, 0.09, 0.09]) usb();
    color([0.35, 0.35, 0.37]) usb_body();
    color([0.18, 0.42, 1.00]) usb_ring();
    color([0.07, 0.07, 0.07]) usb_cap();
    color([0.86, 0.87, 0.90]) v12();
    color([0.66, 0.67, 0.64]) v12_body();
    color([0.75, 0.10, 0.10]) v12_ring();
    color([0.07, 0.07, 0.07]) v12_cap();
}
module deck_context() {
    color([0.55, 0.50, 0.40], 0.25) difference() {
        translate([-75, 30, z_felt]) cube([95, 135, -z_felt]);
        for (c = [usb_c, v12_c]) at(c) translate([0, 0, z_felt - 1]) cylinder(d = socket_hole_d, h = -z_felt + 2);
    }
}

if      (part == "plate")     plate();
else if (part == "screws")    screws();
else if (part == "usb")       usb();
else if (part == "usb_body")  usb_body();
else if (part == "usb_ring")  usb_ring();
else if (part == "usb_cap")   usb_cap();
else if (part == "v12")       v12();
else if (part == "v12_body")  v12_body();
else if (part == "v12_ring")  v12_ring();
else if (part == "v12_cap")   v12_cap();
else if (part == "all")       all_parts();
else if (part == "all_photo") mirror([0, 1, 0]) all_parts();
else if (part == "context")   { all_parts(); deck_context(); }
else echo(str("sockets.scad: unknown part \"", part, "\""));
