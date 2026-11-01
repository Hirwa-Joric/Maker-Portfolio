// Shared dimensions for the documented console assembly, in millimetres.
// Geometry and uncertainty: ../../docs/GEOMETRY.md.
// Project chronology: ../../README.md#from-design-to-build.
//
// Origin: the notch back-edge stitch crease at deck-top level.
// +x points toward the passenger, +y toward the rear, +z upward.
// This frame is left-handed; assemble.py negates y and reverses face winding.
//
// Evidence tags: [S] finished-build scan; [T] tape photographs;
// [P] photographs and camera-aligned comparisons; [I] inferred geometry.
// Stated ranges describe measurement uncertainty, not manufacturing tolerances.
//
// Point lists generally describe the passenger half; mirror x for the driver.
// The driver rear arch and the two fibre ends have separate measured profiles.
// The table-state front bow is applied by assemble.py. The fit_* parameters
// describe optional deformation when the panel is installed in the car.
// Every part generator reads the shared tables below.

$fn = 96;

// ------------------------------------------------------------------ helpers
// mirror a passenger-half point list to the driver side
function mirror_x(pts) = [for (p = pts) [-p[0], p[1]]];
// close a right-half outline that starts and ends on x = 0 into a full symmetric outline
function full_outline(h) = concat(h, [for (i = [len(h) - 2 : -1 : 1]) [-h[i][0], h[i][1]]]);
// one column of a table as a [key, value] profile for lookup()
function prof(tbl, i) = [for (r = tbl) [r[0], r[i]]];
// linear interpolation in a table: column i at key y (clamped at the ends)
function tab(y, tbl, i) = lookup(y, prof(tbl, i));

// =====================================================================================================
// 1. DECK (flat top between the two side rims, plus the two flat arms beside the notch)
// =====================================================================================================
deck_board      = 8;     // fibreboard (MDF look) core [I] 6-10; only the total is constrained
deck_vinyl      = 1;     // pebble-grain leatherette on top [I]
deck_felt       = 3;     // black needle-felt underneath [I]
deck_thickness  = deck_board + deck_vinyl + deck_felt;   // 12: felt underside at z = -12 [P] (-11..-14)
deck_crown      = 1;     // the real deck has a ~1 mm crown; the model deck is flat [S] (info only)

// Visible flat top, passenger half, closed through the x = 0 axis. Path: back open edge of the notch
// (y = -6) -> back corner R14 -> notch side edge -> rounded arm nose -> rim inner face (deck seam)
// rearward -> horn tip -> rear arch -> centreline.
// Re-checked 3 Oct against the scan (z = +2 seam and z > -3 deck edge: within +-1.5) and against
// IMG_3491/3488 through re-fitted cameras (arch, notch, seams, band edges within 1-3 mm).
//   back edge / lip: [S] open edge at y = -6.3, stitch crease at y = 0; [T] lip 5 (4-7); [P] 3-6
//   notch side edge: notch_x(y) below, [S] driver side + [P] both sides (the scan's passenger edge is
//                    the sagging lining, not the board edge) +-3
//   arm nose: [S] y -217 (driver) / -222 (passenger); [P] 3491 re-check: driver nose front at y -218,
//             passenger nose (loose lining flap) at -222 -> model -218 (-210..-225)
//   seam (= rim inner face): [S] z = +2 rise, mean of sides, and [P] fibre line - 9.3; agree +-1.5
//   horn: [S]+[P] the arch runs tangentially into the rim inner face at y 229-240
//   rear arch: [S] outer edge of the rolled arch edge (apex 191; the flat top ends ~5 before it at the
//              centre and 1-2 before it near the horns). [T] 3456: 188 raw (183-193). [P] 182 in the
//              photo frame = the flat end (photo y is ~1-3 % short against the scan).
deck_outline_r = [
    [0, -6], [30, -6], [67, -6], [70.5, -6.5], [74, -8], [77, -10.5], [79.5, -13.5], [80.5, -17],
    [83.5, -30], [85.5, -40], [87.5, -50], [89.5, -60], [94, -80], [98, -100], [102, -120], [106.5, -140],
    [110.5, -160], [115, -180], [117, -190], [117.5, -198], [118.5, -207], [120.5, -213], [123.5, -217], [127, -218],
    [130.5, -216.5], [132.5, -212], [131, -200], [129.5, -190], [128, -180], [127, -170], [126, -160], [124.5, -150], [123.5, -140],
    [123, -130], [122.5, -120], [121.5, -110], [120.5, -100], [119.5, -90], [118.5, -80], [117.5, -70], [116.5, -60],
    [115.5, -50], [114, -40], [113, -30], [112, -20], [111.5, -10], [110.5, 0], [110, 10], [109, 20],
    [108, 30], [107, 40], [106.5, 50], [105.5, 60], [105, 70], [104, 80], [103.5, 90], [102.5, 100],
    [102, 110], [101, 120], [100.5, 130], [99.5, 140], [99, 150], [98, 160], [97, 170], [96.5, 180],
    [95.5, 190], [95, 200], [94, 210], [93, 220], [92.5, 230], [92.5, 238], [90, 229.5], [85, 223],
    [80, 215.5], [75, 210], [70, 206], [65, 202], [60, 200], [55, 198], [50, 196], [40, 193.5],
    [30, 193], [20, 193], [10, 192], [0, 191]
];
deck_outline = full_outline(deck_outline_r);

// Board/felt outline: the same, but under the rims the board runs out to the walls' inner faces
// (wall_inner_x) from the arm noses (y -218) to the end of the top band (y 242). [I] - the photos show
// the deck horn tucking under the rim and the rim padding needs support; not seen in section.
// (Outer x = wall_inner_x(y) = wall_face_pts - wing_thickness; regenerate this list if wall_face_pts changes.)
deck_board_outline_r = [
    [0, -6], [30, -6], [67, -6], [70.5, -6.5], [74, -8], [77, -10.5], [79.5, -13.5], [80.5, -17],
    [83.5, -30], [85.5, -40], [87.5, -50], [89.5, -60], [94, -80], [98, -100], [102, -120], [106.5, -140],
    [110.5, -160], [115, -180], [117, -190], [117.5, -198], [118.5, -207], [120.5, -213], [123.5, -217], [127, -218],
    [145, -218], [144, -210], [143, -200], [141.5, -190], [140, -180], [139, -170], [138, -160], [136.5, -150],
    [135.5, -140], [135, -130], [134.5, -120], [133.5, -110], [132.5, -100], [131.5, -90], [130.5, -80], [129.5, -70],
    [128.5, -60], [127.5, -50], [126, -40], [125, -30], [124, -20], [123.5, -10], [122.5, 0], [122, 10],
    [121, 20], [120, 30], [119, 40], [118.5, 50], [117.5, 60], [117, 70], [116, 80], [115.5, 90],
    [114.5, 100], [114, 110], [113, 120], [112.5, 130], [111.5, 140], [111, 150], [110, 160], [109, 170],
    [108.5, 180], [107.5, 190], [107, 200], [106, 210], [105, 220], [104.5, 230], [104.5, 240], [104.5, 242],
    [95, 242], [92.5, 238], [90, 229.5], [85, 223], [80, 215.5], [75, 210], [70, 206], [65, 202],
    [60, 200], [55, 198], [50, 196], [40, 193.5], [30, 193], [20, 193], [10, 192], [0, 191]
];
deck_board_outline = full_outline(deck_board_outline_r);

// Notch (the open U at the front of the deck that frames the gear lever)
notch_edge_a     = 77;     // notch side edge |x| = notch_edge_a + notch_edge_b * (-y)       [S]+[P] +-3
notch_edge_b     = 0.21;   //   (widens ~12 deg per side toward the front)                    [S] 0.206 [P] 0.215
function notch_x(y) = notch_edge_a + notch_edge_b * (-y);   // valid for y = -17 .. -190
notch_half_width = 80;     // open-edge half width at the back corners (y ~ -15): 160 wide.   [S] 158 [P] 163
                           //   [T] 150-155 (crease to crease 155) -- the tape is 3-5 % narrower, see md
notch_corner_r   = 14;     // back corner radius                        [S] 12-18 [P] R15 (driver 10-12, passenger 15-20) [T] 12 (10-20)
notch_lip        = 6;      // rolled lip at the back edge, width seen from above (y 0 .. -6)  [S] 6.3 [T] 5 (4-7) [P] 3-6
notch_lip_side   = 6;      // same along the arms: a crease runs ~6.5 outboard of the open edge on both arms
                           //   (the board edge), the lip rolls over inboard of it into the lining
                           //   [P] 3491 crease at |x| = 84 + 0.21*(-y) (passenger), ~103 at y -100 (driver);
                           //   scan texture shows the same crease. [T] ~3 (low) superseded. 5-7
notch_lip_r      = 3;      // roll radius where the lip turns down into the lining          [I] (keep notch_lip_r < notch_lip)
notch_crease_depth = 1.5;  // the stitch crease at y = 0 sits this far below the deck top   [S]
arm_front_y      = -218;   // arm nose tip (end of the flat arms)  [S] -217 D / -222 P; [P] 3491 -218 D, -222 P flap; -210..-225
arm_nose_r       = 6;      // nose rounding in plan                                          [P] ~6
arm_top_z        = 0;      // arm strips at deck level                                       [S] within +-2 of the deck plane
arm_droop        = 0;      // optional extra drop at the nose (scan hints 0..-4; free arms on the table) [S] 0..-4
// Notch lining: separate leatherette strip (grey knit back, raw cut edge) hanging from the notch edges
notch_lining_t     = 1.5;  // leatherette + thin foam                                       [T] (foam INFERRED)
notch_lining_depth = 30;   // visible lining below the deck along the arms                  [T] pixel estimate 28-32 (20-35)
notch_lining_sag_p = 12;   // passenger lining hangs inward (free, not glued) up to this much at y -60..-150 [S] 8-16 [T] 3479/3480 [P] 3491 5-7 (loose flap; 5-16)
notch_lining_sag_d = 3;    // driver lining: nearly straight                                 [S] 0-4
// The lining is a LOOSE flap and hangs differently in the car : SEEN 3483/3484/3485 the passenger
// lining's leather runs all the way down to the gear boot (no grey console gap), while on the table (3491) its lower
// edge sits only 5-7 inboard of the open edge. A car-state lining (deck.scad part "skirt_car" ->
// notch_skirt_car.stl, used by the in-car views only) sags further and hangs deeper on the passenger side:
notch_lining_sag_p_car   = 16;  // [S] 8-16 (top of the range) [P] 3483 c_pass / ov3483_notch
notch_lining_depth_p_car = 38;  // passenger depth in the car (driver stays notch_lining_depth) [P] 3483/3484 [I] 32-42

seam_rear_y     = 238;     // horn tip: where the deck top ends against the rim inner face   [S]+[P] 228-245
deck_half_width = 110.5;   // rim inner face (deck seam) at y = 0. The seam TAPERS: use band_pts col 1.
                           //   220 at y 0, 211 at 50, 205 at 100, 196 at 160, 190 at 200 (seam to seam)
                           //   [S] 222/213/206/196/189.5 [P] 218/211/202/195/187 [T] 205 (tape lay on the rims)
arch_roll       = 5;       // the leatherette rolls over the arch edge onto the underside; flat top ends
                           //   ~5 inside the outline at the apex, 1-2 near the horns          [S] [T] 3477
// rear arch alone (horn to horn), for code that wants it separately                     [S] +-2
arch_pts = [[92.5, 238], [90, 229.5], [85, 223], [80, 215.5], [75, 210], [70, 206], [65, 202], [60, 200],
            [55, 198], [50, 196], [40, 193.5], [30, 193], [20, 193], [10, 192], [0, 191],
            [-10, 192], [-20, 193], [-30, 193], [-40, 193.5], [-50, 196], [-55, 198], [-60, 200], [-65, 202],
            [-70, 206], [-75, 210], [-80, 215.5], [-85, 223], [-90, 229.5], [-92.5, 238]];
arch_apex_y     = 191;     // outer edge of the roll on the centreline [S] (flat top ends at 186) [T] 188 (183-193)
// DRIVER half of the rear arch , centre -> horn tip. The arch is NOT symmetric: SEEN 3491 (arch edge
// through Cam 3491) puts the driver half 2.5-4 mm further forward than the passenger half at |x| 56-85 (photo y at
// x -56 197.4, -66 200.8, -75 207.7, -84 217.9); the scan agrees there is a ~3 mm asymmetry at |x| 65 (driver 202.3,
// passenger 205.4) but puts the driver horn end at -84 near the old value (221.9), so the horn end is uncertain (+-2.5).
// The passenger half (arch_pts / deck_outline_r) is unchanged; deck.scad builds the arch from both halves.
arch_pts_d = [[-10, 192], [-20, 193], [-30, 193], [-40, 193.5], [-50, 195.7], [-55, 197], [-60, 198], [-65, 200.5],
              [-70, 203.5], [-75, 208], [-80, 213], [-85, 220], [-90, 228], [-92.5, 238]];

felt_z          = -deck_thickness;   // felt underside
felt_band_y     = [0, 24];  // raised felt strip across the underside from the notch back edge rearward, 24 wide
                            //   (20-27): [P] 3502 ~0..+24 at ~4.6 display px/mm, 3481 ~27 [T] 3480-3482
felt_band_h     = 2;        //   its height is NOT measured: 2 is a guess (1-4) [I]

// =====================================================================================================
// 2. SIDE WALLS ("wings") AND THEIR TOP BANDS (the raised side rims carrying the light fibre)
// =====================================================================================================
// BAND TABLE (passenger half). One row per station along the car:
//   [ y, x_inner (rim inner face = deck seam), x_fibre (fibre centre), x_outer (outer edge of the band
//     top, before the outer roll curls down), z_top (band top above the deck) ]
// Plan:  [S] seams (mean of sides) and [P] fibre line agree +-1.5 mm; band 18.5 wide [T] 3468
//        (16-19 along the deck [S]), narrowing to 15 at the tip [T] 3449 (low); fibre 9.3 from the inner
//        face [T] 3468. Forward of the arm noses (y < -218) the rim stands free: [S] driver side +2..5 and
//        [P]; the passenger rim splays another 5-10 mm on the table [S]. Tips 320 outside-outside [T][S].
//        Re-check [P] 3491 (re-fitted camera): band outer edge within 1 mm and fibre within 1-2 mm of this
//        table from y -100 to 240 on both rims. Near the tips the symmetric table is the mean of the two
//        free rims: the driver tip sits ~8 inboard (x -147, y -276), the passenger tip ~8 outboard
//        (x 164, y -271) [P] 3491 = [S] within 2 mm.
// Height: [S] band top, mean of both walls, every 10 mm, lightly smoothed (+-1.5; +-3 near the tip).
//        [T] 26 (3473, fitted) and 19.5 (3474, near the arch) both fit.
// First row = the pointed tip (R3-5, the smooth inner roll wraps round it). Rows -270/-265 :
// the tip is a narrow HOOKED point, ~10 wide 5 mm behind the point ([S] band (z > 8) 12.0 D / 9.4 P at y -270;
// [P] 3491/3488 tip crops), widening to the full band by -260. Last rows: the band ends at band_end_y; behind
// it the band and its smooth roll loft into the rear cap (rear_cap_pts).
band_pts = [
    [-275, 156.5, 156.5, 156.5, 56], [-270, 151.5, 156.5, 161.5, 55.5], [-265, 147.5, 153.5, 160.5, 54.5], [-260, 144, 151.5, 159, 53], [-250, 140.5, 148.5, 156.5, 50],
    [-240, 137.5, 146, 154.5, 47], [-230, 135, 144, 152.5, 44], [-220, 133.5, 142.5, 151.5, 41.5], [-210, 132, 141.5, 150.5, 39.5],
    [-200, 131, 140.5, 149.5, 37.5], [-190, 129.5, 139, 148, 35.5], [-180, 128, 137.5, 146.5, 34], [-170, 127, 136.5, 145.5, 32.5],
    [-160, 126, 135.5, 144.5, 31.5], [-150, 124.5, 134, 143, 30.5], [-140, 123.5, 133, 142, 29.5], [-130, 123, 132.5, 141.5, 29],
    [-120, 122.5, 132, 141, 28.5], [-110, 121.5, 131, 140, 28], [-100, 120.5, 130, 139, 28], [-90, 119.5, 129, 138, 28],
    [-80, 118.5, 128, 137, 28], [-70, 117.5, 127, 136, 28], [-60, 116.5, 126, 135, 27.5], [-50, 115.5, 125, 134, 27],
    [-40, 114, 123.5, 132.5, 27], [-30, 113, 122.5, 131.5, 27], [-20, 112, 121.5, 130.5, 27], [-10, 111.5, 121, 130, 27],
    [0, 110.5, 120, 129, 27.5], [10, 110, 119.5, 128.5, 27.5], [20, 109, 118.5, 127.5, 27.5], [30, 108, 117.5, 126.5, 28],
    [40, 107, 116.5, 125.5, 28], [50, 106.5, 116, 125, 28.5], [60, 105.5, 115, 124, 29], [70, 105, 114.5, 123.5, 29],
    [80, 104, 113.5, 122.5, 29.5], [90, 103.5, 113, 122, 29.5], [100, 102.5, 112, 121, 29], [110, 102, 111.5, 120.5, 29],
    [120, 101, 110.5, 119.5, 28.5], [130, 100.5, 110, 119, 28], [140, 99.5, 109, 118, 27.5], [150, 99, 108.5, 117.5, 26.5],
    [160, 98, 107.5, 116.5, 25], [170, 97, 106.5, 115.5, 24], [180, 96.5, 106, 115, 22.5], [190, 95.5, 105, 114, 21],
    [200, 95, 104.5, 113.5, 19.5], [210, 94, 103.5, 112.5, 17.5], [220, 93, 102.5, 111.5, 15.5], [230, 92.5, 102, 111, 13],
    [240, 92.5, 102, 111, 11.5], [242, 92.5, 102, 111, 11.5]
];
function band_inner_x(y) = tab(y, band_pts, 1);
function band_fibre_x(y) = tab(y, band_pts, 2);
function band_outer_x(y) = tab(y, band_pts, 3);
function band_top_z(y)   = tab(y, band_pts, 4);

band_end_y     = 242;    // the fibre groove (and the fibre on it) ends here, beside the arch horn [S][P][T] 235-250.
                         //   The band itself no longer stops square here : over y 228-248 it and its
                         //   smooth roll loft into the rear cap below and run on to the rear end.
// REAR CAP : behind the band the wall top is NOT the bare 5.5 board edge. The smooth inner roll
// sweeps diagonally outward out of the band (the fibre zone vanishes) and, with the outer pebble roll, carries on
// as a rounded padded strip 10-14 wide that tapers to a rounded end. SEEN 3491 rear crops (both rims), 3495
// (passenger rear end), 3488; [S] scan sections (width within 4 mm of the top) 18.6 @ 230, 14.2 @ 245,
// 11.5 @ 255, 10.5 @ 265, 9 @ 275, 7.9 @ 285 (mean of sides).
//   [y, x_inner, x_outer, z_top]   passenger half, +-2 (scan values)
rear_cap_pts = [[228, 92.5, 111, 13.5], [242, 95, 110.5, 11.5], [255, 97, 110, 11.2], [270, 98.5, 110, 11.2],
                [285, 100, 109.7, 10.5], [293, 101, 109.5, 8]];
rear_cap_y0    = 228;    // band -> cap loft starts here ...                                    [S][P]
rear_cap_y1    = 248;    //   ... and is complete here (the inner edge blends over 234-250 so the arch horn stays covered) [I]
rear_cap_roll  = 0.45;   // in the cap the smooth roll covers the inner ~45 % of the strip ([P] 3491/3495: the
                         //   smooth roll and the outer pebble roll run side by side to the end) [P] 0.4-0.5
rear_cap_end_r = 4;      // rounded end in plan                                                 [P] 3491/3495 R3-5
rear_cap_pad   = 8;      // inboard of the board the cap is a free padded edge this deep (not seen in section;
                         //   the scan only resolves the top 4 mm) [I] 5-9
function cap_inner_x(y) = tab(y, rear_cap_pts, 1);
function cap_outer_x(y) = tab(y, rear_cap_pts, 2);
function cap_top_z(y)   = tab(y, rear_cap_pts, 3);
band_w         = 18.5;   // band width at the notch line, inner face to outer edge              [T] 3468 high
band_w_tip     = 15;     // near the tip                                                       [T] 3449 low (13-16)
band_fibre_off = 9.3;    // fibre centre from the inner face (scale with width toward the tip)  [T] 3468 (8-11)
// band cross-section, measured from the INNER face outward (at the notch line)               [T] 3468 (27.7 px/mm)
band_roll_w    = 4.8;    // smooth black rounded roll on the inner top corner (~5 tall, top flush)  [T] 4.5-6
band_roll_h    = 5;      //   its height                                                        [T] 3473 5.5 (4.5-6)
band_strip     = [4.8, 7.9];    // narrow pebble strip                                          [T]
band_fibre_seat= [7.9, 10.7];   // clear side-glow fibre, centred at 9.3, top about flush        [T][P]
band_outer_roll= [10.7, 18.5];  // outer pebble roll, 5-6 flat on top                           [T]
band_outer_curl= 6;      // the outer roll curls this far down the wall's outer face            [T][P] 5-7
band_overhang  = 1;      // outer edge of the band top stands this far outside the board's outer face.
                         //   [S] driver face at z 0 averages 0.6 inside the band-top outer edge (-3..+4);
                         //   the outer roll's curl (z ~20) bulges ~2 outside it. 0-3 (was 2.5 [I])
band_cap_h     = 8;      // board top edge sits this far below the band top (padding/cap depth)  [I] 5-10
band_tip_r     = 4;      // the pointed front tip, plan and side                                [P] R3-5
// The rim's inner face rises vertically from the deck to the band top (27-29.5 tall mid-length) [S][T].
// Forward of the arm noses the inboard padding has no deck under it; give it a bottom at
// band_top - band_cap_h (not seen; [I]).

// WALL (board) plan: outer face of the covered board just below the band, passenger half [S]+[I]
//   = band outer edge - band_overhang along the band; rear segment from [S] (110-111) and [T] 219/2.
//   First row: the board ends inside the pointed band tip (156.5). Row -270 = band outer - 1 (160.5).
//   Last row at the rear end y 293.
//   Faces are modelled VERTICAL (wall_lean = 0); see wall_lean.
//   Check vs the scan's outer face at z 0: driver within +-4 except y -200 (-5, free rim); the passenger
//   wall stands 3-8 further out forward of y -100 and at y 125-200 (its free-state splay, see md section 3).
wall_face_pts = [
    [-275, 158.5], [-270, 160.5], [-260, 158], [-250, 155.5], [-240, 153.5], [-230, 151.5], [-220, 150.5], [-210, 149.5],
    [-200, 148.5], [-190, 147], [-180, 145.5], [-170, 144.5], [-160, 143.5], [-150, 142], [-140, 141], [-130, 140.5],
    [-120, 140], [-110, 139], [-100, 138], [-90, 137], [-80, 136], [-70, 135], [-60, 134], [-50, 133],
    [-40, 131.5], [-30, 130.5], [-20, 129.5], [-10, 129], [0, 128], [10, 127.5], [20, 126.5], [30, 125.5],
    [40, 124.5], [50, 124], [60, 123], [70, 122.5], [80, 121.5], [90, 121], [100, 120], [110, 119.5],
    [120, 118.5], [130, 118], [140, 117], [150, 116.5], [160, 115.5], [170, 114.5], [180, 114], [190, 113],
    [200, 112.5], [210, 111.5], [220, 110.5], [230, 110], [242, 110], [260, 110], [280, 109.8], [293, 109.5]
];
wing_board     = 4.3;    // bare board                                                         [T] 3462 (4.2-4.4)
wing_thickness = 5.5;    // board + outer leatherette ((219 - 208) / 2)                         [T] 5-5.5
function wall_face_x(y)  = lookup(y, wall_face_pts);
function wall_inner_x(y) = wall_face_x(y) - wing_thickness;
wall_lean      = 0;      // inward lean of the face toward the bottom, mm at the bottom edge. The scan's
                         //   lower walls have holes mid-length and the cavity is closed by false "web"
                         //   surfaces, so lean is NOT established: 0 (near-vertical where captured) [S]
wing_outer_x   = 110;    // outer face at the rear segment (rear reference; the walls taper) [S] 110-111 [T] 109.5

// SIDE OUTLINE of each wall in (y, z), one shape for both walls (mirror images within 2-5 mm [S])
wing_tip_y     = -275;   // pointed tip, on the TOP edge                                       [S] -271..-274 (tips may be clipped) [P] -275
wing_tip_z     = 56;     //                                                                    [S] 55-56 [P] 53-60
wing_rear_y    = 293;    // vertical rear end [P] 3491 top corners at z 8: 293.1 P / 293.6 D;
                         //   [S] 293.8 D / 291.2 P; tape 577 along the top favours the longer wall. 291-294
wing_rear_top_z= 11.2;   // flat rear segment top, y 240-293 (now the rear cap, rear_cap_pts)   [S] 10-12.5
wing_bottom_z0 = -120;   // straight bottom edge: z = wing_bottom_z0 + wing_bottom_slope * y   [S] table plane [P] 3489 (+-1.5)
wing_bottom_slope = -0.008;  //   0.45 deg, deeper at the rear (-119 at y -123, -122.3 at the rear end)
function wing_bottom_z(y) = wing_bottom_z0 + wing_bottom_slope * y;
wing_height       = 147.5;   // top minus bottom at y = 0                                       [T] 147 (144-148.5) [S] 148
wing_height_mid   = 150;     // at y 80-100                                                     [S] 149-150.7
wing_rear_height  = 133.5;   // rear segment                                                    [T] 131 (128-135) [S] 133.4
wing_rear_corner_r= 4;       // top-rear corner                                                 [S] R3-5
wing_rear_bottom_r= 3;       // bottom-rear corner                                              [S] R2-5
wing_sweep_join_y = -123;    // front sweep joins the bottom edge tangentially here             [P] 3489 (-115..-145) [S] >= -168
// band top / wall top edge, (y, z), tip to rear end                                            [S] (+-1.5; tip +-3)
wing_top_pts = [
    [-275, 56], [-270, 55.5], [-260, 53], [-250, 50], [-240, 47], [-230, 44], [-220, 41.5], [-210, 39.5],
    [-200, 37.5], [-190, 35.5], [-180, 34], [-170, 32.5], [-160, 31.5], [-150, 30.5], [-140, 29.5], [-130, 29],
    [-120, 28.5], [-110, 28], [-100, 28], [-90, 28], [-80, 28], [-70, 28], [-60, 27.5], [-50, 27],
    [-40, 27], [-30, 27], [-20, 27], [-10, 27], [0, 27.5], [10, 27.5], [20, 27.5], [30, 28],
    [40, 28], [50, 28.5], [60, 29], [70, 29], [80, 29.5], [90, 29.5], [100, 29], [110, 29],
    [120, 28.5], [130, 28], [140, 27.5], [150, 26.5], [160, 25], [170, 24], [180, 22.5], [190, 21],
    [200, 19.5], [210, 17.5], [220, 15.5], [230, 13], [240, 11.5], [250, 11], [260, 11.2], [270, 11.2],
    [280, 11.2]
];
function wing_top_z(y) = lookup(y, wing_top_pts);
// front sweep, frame-free: [d behind the tip, h above the extended bottom line]                [P] 3489 trace, [S] agrees +-3 above z -100
wing_sweep_dh = [
    [0, 174], [3.5, 149.5], [10, 124.5], [19, 99.5], [35, 74.5], [56, 49.5], [80.5, 30], [97, 20],
    [108, 14.4], [116, 9.8], [129, 5.1], [136, 3.2], [147, 1], [152, 0]
];
// CLOSED side outline (y, z), clockwise from the tip: top edge -> rear end (R4 / R3 corners) ->
// straight bottom edge -> front sweep back up to the tip. Extrude it across x (thickness wing_thickness)
// and bend it to follow wall_face_pts in plan (it is a thin board).
wing_outline_yz = [
    [-275, 56], [-270, 55.5], [-260, 53], [-250, 50], [-240, 47], [-230, 44], [-220, 41.5], [-210, 39.5],
    [-200, 37.5], [-190, 35.5], [-180, 34], [-170, 32.5], [-160, 31.5], [-150, 30.5], [-140, 29.5], [-130, 29],
    [-120, 28.5], [-110, 28], [-100, 28], [-90, 28], [-80, 28], [-70, 28], [-60, 27.5], [-50, 27],
    [-40, 27], [-30, 27], [-20, 27], [-10, 27], [0, 27.5], [10, 27.5], [20, 27.5], [30, 28],
    [40, 28], [50, 28.5], [60, 29], [70, 29], [80, 29.5], [90, 29.5], [100, 29], [110, 29],
    [120, 28.5], [130, 28], [140, 27.5], [150, 26.5], [160, 25], [170, 24], [180, 22.5], [190, 21],
    [200, 19.5], [210, 17.5], [220, 15.5], [230, 13], [240, 11.5], [250, 11], [260, 11.2], [270, 11.2],
    [280, 11.2], [287, 11.2], [291, 10.7], [292.5, 9.2], [293, 7.2], [293, -119.3], [292.5, -120.8], [291.5, -121.9],
    [290, -122.3], [280, -122.2], [250, -122], [200, -121.6], [150, -121.2], [100, -120.8], [50, -120.4], [0, -120],
    [-50, -119.6], [-100, -119.2], [-123, -119], [-128, -118], [-139, -115.7], [-146, -113.7], [-159, -108.9], [-167, -104.3],
    [-178, -98.6], [-194.5, -88.4], [-219, -68.7], [-240, -43.6], [-256, -18.5], [-265, 6.6], [-271.5, 31.7]
];
// NOTE: the board's own top edge is band_cap_h below the band / rear-cap top along its whole length (the
// the rear segment is capped by the padded strip of rear_cap_pts, see wings.scad). The outline's top
// chain still gives the side silhouette used by the checks. [I]
// Surfaces: outer face pebble leatherette; inner face below the deck bare matte black board; rim inner
// face above the deck pebble leatherette [T]. One rear end shows bare grey board [T] 3462 (which side: unknown).

// =====================================================================================================
// 3. FITTINGS ON THE DECK (centres in the model frame; heights = top above the deck surface)
//    Positions: [S] texture/height fits (+-1-2) cross-checked with [P] camera plan (agree +-3 in y,
//    +-1.5 in x) and [T] gaps. Sizes: [T] first.
// =====================================================================================================
clock_c        = [0, 25.5];   // [S] (1.5, 25.6) [P] (0.4, 23.6->~25.5) [T] 3456 25-28, 3455 21.5; x = 0 [T]   y +-2.5
clock_body_d   = 38.5;   // glossy black body, the widest part (= hole in the leatherette)  [T] 36 (35.4-39) [S] dark ring 38-40
                         //   [P] 3483 (re-measured 3 Oct against the cup ring, same scale): window ~30, chrome ~1,
                         //   black ring ~3 -> 38.5-39 outside (photographic estimate). 36-39
clock_d        = 32.5;   // thin polished chrome bezel, ~1 mm wide  [T] 34 (32.5-36) [P] 3483/3491 chrome 0.8-1 [S] 32-35
clock_window_d = 30.5;   // glass / dial window                       [T][P] 29.5-30.5
clock_t        = 3;      // total height above the deck: a LOW puck, not an 8 mm drum         [P] 2.5-4 [S] ~1 (0-3, chrome/glass read low)
clock_body_t   = 2.2;    // black body top                                                  [P] ~2.2
// dial: khaki/olive chapter ring, white batons, light carbon-weave centre, 12 toward -y; NO emblem.

button_c       = [91.5, 33];  // [S] (92.7, 34.0) [P] (91.0, 29->~31) [T] 3469 +92; 14-18 in from the passenger seam; x 86-93, y 28-35
button_head_d  = 16;     // polished stainless bezel ring                                    [T] 16.5 (15-18) [P] 15-16 [S] 14-16
button_face_d  = 12;     // brushed flat face                                                [T] 12.5 (12-13.5) [P] 11.5 (10.5-12.5)
button_proud   = 2.5;    //                                                                  [P] 2.1-2.5 (2-3.5) [S] 2.1
button_hole_d  = 12;     // hole in the deck (not seen; 16 if it is a 16 mm switch)           [I]

cup_c          = [51, 100];   // [S] (51.2, 100.4) [P] (50.9, 95.3->~98) [T] x 50 (49-51.5)   y +-3
cup_ring_od    = 84;     // chrome rolled half-round lip, outside                            [T] 84 (79-85) [S] 83 [P] 83-84
cup_ring_id    = 72;     //                                                                  [T] ~72 (69-74) [S] 74
cup_ring_crest_d = 79;   // crest of the half-round (lip ~6 wide)                            [P] [T] 3451/3452 ~5 wide
cup_ring_proud = 4.5;    // crest above the deck                                             [S] 5.1 [P] 3-5 (3.5-5.5)
cup_hole_d     = 75;     // hole in the deck (not seen; between ID and OD)                    [I]
cup_top_od     = 73;     // cup body outside diameter just under the ring                     [I]
cup_floor_z    = -56;    // inside floor                                                     [S] -54.5 [T] -57 (55-60)
cup_depth      = 60;     // outside bottom of the cup body below the deck top    [T] body 64 tall - ~4.5 above deck
cup_bottom_d   = 62;     // flat dark-grey outer bottom, rounded edge                        [P] 3502 (58-67)
cup_mat_disc_d = 25;     // floor mat: smooth central disc (thin ring outline) ...           [P] 23-27
cup_mat_rings  = 5;      //   ... surrounded by ~5 rings of small round dimples             [P]

plate_c        = [-30.5, 101.5]; // [S] (-30.5, 101.4) [P] (-30.8, 96.4->~99.5) [T] x -30 (-31..-28); front edge 50.5 [T] 3456 49-52
plate_size     = [40.5, 102];    // [T] 40.5 (high) x 102 (100.5-105) [S] 41.1 x 100.8
plate_r        = 5;      // corner radius                                                    [P]
plate_t        = 4;      // plate top above the deck                                         [S] 3.8-4.9
plate_rot      = 1.2;    // plate turned about plate_c, rear end toward the driver (-x).
                         //   SEEN 3491 (f3491_plate_slot): the plate's passenger long edge is turned 1.2-1.5 deg
                         //   against the slot; not resolved in the scan. 0.6-1.7. The plate, its screws, both
                         //   sockets (and their bodies) and the deck holes all turn together: use plate_xf().
usb_c          = [-30.5, 79];    // front socket (plate_c.y - 22.5) BEFORE the plate turn (use plate_xf(usb_c)) [S] (-29.7, 79.1) [P] +-2.5
v12_c          = [-30.5, 124];   // rear socket (plate_c.y + 22.5) BEFORE the plate turn (use plate_xf(v12_c)) [S] red ring (-32.3, 121.7) [P] +-2.5
// a point given in the plate's own (unturned) layout -> its place after the plate_rot turn about plate_c
function plate_xf(p) = let (d = [p[0] - plate_c[0], p[1] - plate_c[1]], c = cos(plate_rot), s = sin(plate_rot))
    [plate_c[0] + c * d[0] - s * d[1], plate_c[1] + s * d[0] + c * d[1]];
socket_hole_d  = 29;     // holes in the plate/deck (not measured)                            [I]
usb_cap_top_z  = 11;     // hinged black rubber cap CLOSED on 3 Oct (hinge on +x, tab on -x)  [S] 11.2 [P] 10.5-11
v12_top_z      = 10;     // 12 V socket: red face ring, chrome mouth, torn cap (flap on +x)  [S] 10.2 [P] 9-10
v12_ring_d     = 35;     // red face ring                                                    [P] 34-36 [S] 38
v12_mouth_d    = 25;     // chrome mouth                                                     [P] 24-26 [S] 27
plate_screw_dx = 24.5;   // four Phillips screws near the corners, spacing across   [P] 3491 25.2, 3483 23.4-25 [T] ~23 (low)
plate_screw_dy = 83.5;   //   ... and along                                         [P] 3491 83.5, 3483 83  [T] ~86 (low)
plate_screw_d  = 2.5;    //                                                                  [I]

slot_c         = [-71, 96];      // [T] x -69 (-70..-67) [P] (-72, 91.7->~95) [S] (-74.5, 96); gaps: plate 8.75 [T 7.5], seam 20 [T 21]  x +-3, y +-3
slot_surround  = [23, 92];       // black moulded surround, outside                          [T] 23 (22.9-24) high x 92 (88-94)
slot_rim       = 4.2;            // rim width (long sides)                                   [T]
slot_open      = [15, 84];       // opening                                                  [T] 15 x ~84
slot_cut       = [19, 86];       // cut in the deck (not seen; between opening and surround) [I]
slot_proud     = 2;              // surround top above the deck                              [S] 2.2 [P] 1-3
slot_depth     = 36;             // open down to the metal bar: bar top (slot floor) at z = -36 [P] 28-50 (low)

bar_c          = slot_c;         // metal bar centred under the slot                          [P] 3502/3503
bar_size       = [18.5, 89];     // matte worn-grey rounded rectangle                         [P] 17-20 x 87-94 (length:width ~4.5:1 [T])
bar_t          = 2.5;            //                                                          [P]
bar_hole_dy    = 52;             // two EMPTY holes, along y                                  [P] 49-56
bar_hole_d     = 4;              //                                                          [P]
bar_top_z      = -slot_depth;    // the bar caps a black pocket block standing proud of the felt

// =====================================================================================================
// 4. LIGHTS: three aluminium LED heads and two clear side-glow fibres
// =====================================================================================================
led_head_d      = 13;    // plain aluminium cylinder                                          [P] 12-14
led_head_l      = 31;    // metal length                                         [P] 29-35
led_head_boot   = 3;     // short black cable boot at the grooved end                         [P]
led_head_grooves= 4;     // four turned grooves on the rear ~35 % (cable end) [P] 3485 full res, 3502
led_head_open_d = 5.5;   // fibre entry in the smooth nose                                    [I]
// [x, y, z] centre and unit axis (nose direction). Both mounted heads lie LOOSE on the felt; not mirrored.
head_P_c    = [98, 149, -18.5];     // against the passenger wall's inner face                 [P] 3502 x 94-101, y 144-154
head_P_axis = [0, 1, 0];            // nose straight rearward (+-3 deg); nose at y ~166
head_D_c    = [-76, 161, -18.5];    // ~25 in from the driver wall (was (-78, 157): its boot and
                                    //   stub reached into the slot pocket's opening and showed through the slot) [P] 3502 +-6
head_D_axis = [-0.34, 0.94, 0];     // nose rearward and ~20 deg outward (10-35); grooved end (y ~146, boot ~143.6) just
                                    //   behind the bar's rear end (140.5), as 3502 ("nearly touches")
// third head: no fibre, on its own thin lead, OUTSIDE the panel. Fitted pose: in the car's small
// rubber-matted tray left of the gear lever (between ECO/NORMAL/SPORT and EV MODE), nose toward -x.
head_loose_c    = [-63, -43, -40];  // [P] 3483/3485 +-15
head_loose_axis = [-1, 0, 0];

fibre_core_d = 3.5;      // clear round core                                                  [T] 3-4 [P]
fibre_fin    = [4, 0.8]; // flat clear fin on one side (total ~7.5 wide); flat on the felt under the deck [P]
fibre_drop   = 2;        // fibre centre this far below the band top (core top about flush)  [P][T]
fibre_end_back = 21;     // MEAN: the fibre ends this far short of the band tip (tapered)  [P] 3491 (15-25)
fibre_end_y  = wing_tip_y + fibre_end_back;     // -254 (mean; used for the tip wrap of the smooth roll)
// per side : SEEN 3491 (z 50 back-projection) the passenger fibre ends at y -246.5 and the driver
// fibre at -256.3 (GEOMETRY 5.2: -247 / -256.5). The fibres and the band grooves use these.
fibre_end_back_p = 28;    // passenger: ends at -247   [P] 3491 (+-3)
fibre_end_back_d = 18.5;  // driver:    ends at -256.5 [P] 3491 (+-3)
function fibre_end_y_side(side) = wing_tip_y + (side > 0 ? fibre_end_back_p : fibre_end_back_d);
fibre_climb_y = band_end_y;          // where the fibre comes up onto the band (both sides)   [P] 3462/3481 237-254
// UNDER-DECK runs (3D, model frame), nose -> P-clip -> along the felt beside the wall -> free loop
// (R 10-15) up the inside corner between the deck's rear end and the wall's inner face -> onto the band.
fibre_P_under = [[98, 166, -18.5], [101, 182, -15], [101, 212, -14], [100, 236, -14], [99.5, 244, -8],
                 [99.5, 247, 0], [100.5, 246, 6], [101.5, 243, 9.5]];
fibre_D_under = [[-81.5, 176, -18.5], [-90, 200, -15], [-97, 226, -14], [-99.5, 238, -14], [-99.5, 245, -8],
                 [-99.5, 248, 0], [-100.5, 246.5, 6], [-101.5, 243, 9.5]];
// TOP run on the band (side = +1 passenger, -1 driver): forward from fibre_climb_y to fibre_end_y,
// in the seam between the pebble strip and the outer roll. No fibre on outer faces, rear ends,
// front sweeps or across the arch.
// Ends per side at fibre_end_y_side(side). Fitted-state offsets (fitp, section 7) are applied, so the fibre stays
// in its groove when fit_front_drop / fit_tip_dx* are used (they used to move only the band).
function fibre_top_pts(side) = let (fe = fibre_end_y_side(side)) [for (p = concat(
    [for (i = [len(band_pts) - 1 : -1 : 0]) let (r = band_pts[i])
        if (r[0] <= fibre_climb_y && r[0] > fe) [side * r[2], r[0], r[4] - fibre_drop]],
    [[side * band_fibre_x(fe), fe, band_top_z(fe) - fibre_drop]])) fitp(p, side)];
// fibre P-clips (black nylon, screw inboard): ring centre and screw            [P] 3502/3481 +-6
fclip_P_ring = [101, 182, -15];  fclip_P_screw = [92, 183, -12];
fclip_D_ring = [-90, 200, -15];  fclip_D_screw = [-81, 199, -12];

// =====================================================================================================
// 5. UNDERSIDE: controller, cables, clips (all on/under the felt; z = -14..-16 unless given)
//    [P] 3502-3504 (+ 3477-3482), positions +-8..10 unless stated
// =====================================================================================================
ctrl_size = [46, 36, 20];        // [length along y, width across x, height]; ribbed short ends, empty ears, plain label face
ctrl_c    = [cup_c[0] + 10, cup_c[1], -cup_depth - ctrl_size[2] / 2];   // lies flat on the cup's outer bottom (z -80..-60) +-6
ctrl_dc_plug_len = 24;           // DC barrel plug with ribbed boot at the +y end              [P]
ctrl_out_relief_len = 10;        // ribbed strain relief at the -y end                         [P]
inline_conn_1 = [25, 32, -15];   // two mated ribbed in-line connectors just ahead of the cup  [P] +-10
inline_conn_2 = [5, 41, -15];
// power feed W1: round black sheathed cable, ~5 dia, in through a screwed P-clip at the driver notch
// corner, to a moulded end with a clear collar; short salmon and blue tails go to the socket spades.
w1_d    = 5;
w1_pts  = [[-96, -2, -14], [-80, 14, -14], [-62, 39, -14], [-51, 59, -14]];
wclip_notch = [-96, -2, -14];    // P-clip holding W1 and the third head's thin lead
third_lead_d = 3;                // thin lead to the loose head; ribbed in-line connector 30-50 outside the clip
splice_bundle = [[5, 39, -15], [5, 134, -15]];   // red/black + 3-4 black heat-shrink sleeves, x 0-10
splice_clips  = [[7, 59, -12], [7, 97, -12]];    // two screwed black nylon clips (screws ~34 apart in 3502)
// The controller hangs at z -80..-60 under the cup, so its leads first climb the cup body to the felt.
// DC lead: plug end (+y) -> up behind the cup -> along the felt round the cup's rear -> splice bundle
ctrl_dc_lead  = [[ctrl_c[0], ctrl_c[1] + ctrl_size[0] / 2 + ctrl_dc_plug_len, ctrl_c[2]], [64, 150, -45],
                 [65, 150, -18], [70, 161, -15], [42, 160, -15], [20, 150, -15], [5, 134, -15]];
// output lead: strain relief (-y) -> up in front of the cup -> the two in-line connectors   [I] route, ends [P]
ctrl_out_lead = [[ctrl_c[0], ctrl_c[1] - ctrl_size[0] / 2 - ctrl_out_relief_len, ctrl_c[2]], [58, 60, -45],
                 [45, 50, -18], [25, 32, -15]];
led_branch_D  = [[5, 41, -15], [-66, 69, -15], [-65, 100, -15], [-66, 135, -15], [-72, 141, -16]];
led_branch_P  = [[25, 32, -15], [75, 34, -15], [98, 44, -15], [100, 74, -15], [100, 120, -15], [98, 132, -16]];
qi_lead       = [[5, 54, -15], [95, 24, -15], [101, 0, -15], [101, -56, -15], [100, -96, -15], [97, -100, -20]];
qi_lead_clip  = [101, -56, -12]; // screwed P-clip under the passenger arm
qi_lead_conn_from_pad = 85;      // small black 2-pin in-line connector (20-30 long) this far from the pad
button_wire_ends = [[89, 30, -13], [94, 42, -13]];   // two loose red wire ends under the button (one bare tip)
cyl_B26_c = [-66, 69, -16];      // unidentified black cylinder ~7.5 dia x 25 with small side holes (near the bar's front end)

// =====================================================================================================
// 6. LOOSE ITEMS
// =====================================================================================================
qi_size     = [174, 121, 15];  // wireless pad [across x, along y, thick]; chrome edge strip   [S] 171-177 x 119-123 x 15-17
qi_corner_r = 15;              // rounded corners (estimated from the scan view, 10-20)         [S]
plug_size   = [70, 40, 31];    // right-angle cigarette plug incl. exit; textured head, knurled tip [S] 64-73 x 38-42 x <=31

// =====================================================================================================
// 7. FITTED-STATE OPTIONS (default 0 = free state as scanned)
// =====================================================================================================
// Disabled in the renders: the fitted Cam 3483 pose accounts for the in-car front alignment
// without an additional droop (GEOMETRY section 12). If these are ever set, export a CAR-ONLY STL set: wings.scad
// (walls, bands, rolls), loose.scad (fibres, through fibre_top_pts) and deck.scad (notch edge, lip, lining and the
// arm outlines, x only -- the flat deck slabs cannot take fit_front_drop and deck.scad warns) all apply fitp().
fit_front_drop = 0;   // band tips may sit up to ~11 lower in the car (linear from y = 0)   [P] 3483 fit, low (0..-11)
fit_tip_dx     = 0;   // tips pushed in (negative) or out when fitted, both sides            [P] low (0..-5)
fit_tip_dx_p   = 0;   // extra per side, outward positive: passenger ...                      [P] 3491 free state: P tip ~8 out
fit_tip_dx_d   = 0;   //   ... driver (a mirrored wall cannot express a driver-only offset otherwise) D tip ~8 in
function fit_f(y) = max(0, min(1, -y / -wing_tip_y));                     // 0 at y >= 0 .. 1 at the tip
function fit_dx(side) = fit_tip_dx + (side > 0 ? fit_tip_dx_p : fit_tip_dx_d);
// fitted-state offset of a point; works in the model frame AND in the passenger-frame build of a mirrored part
// (x always pushed along sign(x)): side = +1 passenger, -1 driver
function fitp(p, side) = [p[0] + (p[0] >= 0 ? 1 : -1) * fit_dx(side) * fit_f(p[1]), p[1],
                          (len(p) > 2 ? p[2] : 0) + fit_front_drop * fit_f(p[1])];

