// This file defines a later explanatory model; photo/scan tags check it against the finished panel.
// =====================================================================================================
// wings.scad -- the two side walls ("wings") with their padded top bands.
//   "Custom Aftermarket Car Center Console Upgrade" | Current model of the completed panel;
//   dimensions are checked against finished-build measurements and remain approximate.
//
// Geometry source: params.scad (shared, read-only) and ../../docs/GEOMETRY.md sections 5 and 6.
// Every shape below is built from the params tables (band_pts, wall_face_pts, wing_outline_yz, ...);
// the few extra values this file needs are defined in "EXTRA VALUES" with their sources.
// Frame: mm, origin = middle of the notch's back stitch crease at deck-top level, +x passenger,
// +y rear, z up, deck top z = 0 (left-handed; assemble.py flips y). Parts are exported in final position.
//
// WHAT EACH PART IS (built on the passenger side, +x; the driver side is its mirror image):
//   wall      the side wall: a thin covered board 5.5 thick (4.3 board + outer leatherette), bent in plan
//             along wall_face_pts (outer face), side outline = wing_outline_yz. Its top edge is band_cap_h
//             below the band / rear-cap top along the whole length (hidden inside them), to the square rear
//             end at y = wing_rear_y (293). (the rear segment used to be the bare half-round
//             board edge behind y 242; SEEN 3491/3495/3488 and the scan show a padded cap there instead.)
//             Materials (assemble.py): outer face (normal pointing outboard) = pebble leatherette, the
//             rear-segment top edge = leatherette, inner face / bottom / front sweep edge / rear end =
//             bare matte black board.
//   band      the padded rim on top of the wall, pebble leatherette: the vertical inner face that rises
//             from the deck (z = -1, on the deck board) to the band top, the narrow pebble strip, the fibre
//             seat (a round-bottomed groove centred on band_fibre_x at band top - fibre_drop, open from
//             fibre_climb_y to fibre_end_y, closing in a short taper ahead of it) and the outer pebble roll
//             that rounds over and curls down the outside of the wall. Forward of the arm noses (y < -218)
//             it has no deck under it and stops band_cap_h + 1 below its top; that bottom edge (the seam between
//             the pebble inner face and the bare board) runs up diagonally from deck level at the nose over
//             pad_ramp_front (30 mm; SEEN 3487 - it was a 3 mm vertical step). REAR CAP : over
//             y 228-248 the band lofts into the section of rear_cap_pts (the fibre zone vanishes, the inner
//             edge moves outward, the groove closes behind fibre_climb_y) and runs on to the rear end as a
//             rounded padded strip that tapers to a rounded end (R rear_cap_end_r in plan). Behind the deck's
//             rear end (y 242) its inboard part is a free padded edge rear_cap_pad deep.
//             The groove ends per side at fibre_end_y_side() (passenger -247, driver -256.5; 3491).
//   band_roll the smooth black roll on the band's inner top corner (0 .. 4.8 mm from the inner face).
//             At the tip it swings outward across the band and forms the rounded point ([P] 3490/3501).
//             At the rear it sweeps diagonally outward with the inner edge and runs on along the inner ~45 %
//             of the rear cap to the rounded end ([P] 3491 rear crops, 3495).
//   The clear fibre itself is NOT in this file (lights part); it lies in the seat of "band".
//
// part = "right"            passenger wall              -> wing_right.stl
//        "left"             driver wall                 -> wing_left.stl
//        "band_right"       passenger band (pebble)     -> band_right.stl
//        "band_left"        driver band (pebble)        -> band_left.stl
//        "band_roll_right"  passenger smooth roll       -> band_roll_right.stl
//        "band_roll_left"   driver smooth roll          -> band_roll_left.stl
//        "all"              everything, coloured        (preview only)
//        "context"          everything + deck / fibre STLs if present (preview only)
//        "section"          cross-sections at a few stations, laid out flat (preview only)
//
// SOURCE TAGS: [S] 3D scan, [T] tape photos 3449-3482, [P] photographs 3483-3504, [I] inferred.
// =====================================================================================================

include <params.scad>

part = "right";

// =====================================================================================================
// EXTRA VALUES (not in params.scad)
// =====================================================================================================
band_strip_drop = 1.0;   // the pebble strip and the seat edges sit this far below the two rolls' tops: the
                         //   fibre core (top at band top - 0.25) shows "slightly below the rolls on either
                         //   side" [P] 3490/3501 close-ups, GEOMETRY 8.2. [I] 0.5-1.2
seat_r          = fibre_core_d / 2 + 0.1;  // groove radius: the Ø3.5 core with 0.1 clearance [I]
roll_h          = band_roll_h;  // smooth roll height (5) [T] 3473
roll_r_in       = 2.4;   // smooth roll: radius of its inner top corner (it "rounds the inner top corner") [P] [I] 2-2.5
roll_r_out      = 0.9;   // smooth roll: small radius at its outer top corner, toward the strip [I]
curl_r          = 4;     // outer roll: radius where its flat top rounds over into the curl [I]; the curl
                         //   reaches band_outer_curl-ish (4 + 4 = 8 incl. the tuck) down the face [T][P] 5-7
curl_bulge      = 0;     // the curl's outermost point stands this far outside x_outer (band_pts col 3); below
                         //   it the roll eases back (tangent, no crease) to the wall face (x_outer -
                         //   band_overhang) at the board top. 3489 shows no seam or crease between band and
                         //   face, so the swell is a smooth 1 mm. [S] curl ~2 outside the face at z ~20;
                         //   [P] 3491 band edge = x_outer within 1 mm [I] 0-2
seat_edge_w     = 0.6;   // the outer roll's edge rounds down into the seat over this width [I]
pad_front_drop  = band_cap_h + 1;  // forward of the arm noses the inboard padding ends 9 below the band top:
                         //   md 5.2 says band top - 8; 1 mm lower so the padding laps the board's top edge [I]
pad_ramp        = 3;     // REAR: behind pad_rear_y the cap's inboard padding bottom rises over this length [I]
pad_ramp_front  = 30;    // FRONT: ahead of arm_front_y the padding bottom (= the seam between the pebble inner face
                         //   above and the bare board below) runs up DIAGONALLY over this length, from deck level at
                         //   the arm nose (y -218) to band top - pad_front_drop at y -248. SEEN
                         //   3487 (far-arm inner face, 3x) a straight diagonal seam from near the band top ~20 behind
                         //   the tip down and back to the rounded lining nose ~55-60 behind the tip (35-45 mm ramp,
                         //   scale INFERRED); [S] slices: the inner surface comes inboard gradually over y -242..-212.
                         //   It was 3 (a vertical step that showed as a teardrop bump on the band's inner edge in
                         //   top-down views). 25-40
seat_taper      = 3;     // the groove closes over +-3 mm around fibre_end_y (the fibre ends tapered) [P] 3490
nose_len        = band_pts[1][0] - band_pts[0][0];
                         //   = 5: band_pts converges from the full width at -270 to the point at -275
nose_p          = 1.5;   // plan shape of that convergence: 1 = straight V, 2 = ellipse. 1.5 gives a rounded
                         //   point ~R4 (band_tip_r, [P] R3-5) [I]
tip_x           = band_pts[0][3];          // the point (156.5)
wrap_y0         = fibre_end_y - seat_taper;  // smooth roll starts to swing outward here ...      [P] 3490/3501
wrap_y1         = wing_tip_y + 2;            // ... and is fully across the band here             [P] 3490/3501
roll_w_tip      = 13;    // at the tip the smooth roll covers this much of the (scaled) 18.5 band; the pebble
                         //   outer roll runs on underneath it on the outside to the point [P] 3490/3501 [I]
wall_face_n     = 8;     // extra points up each face of the wall section, so smooth shading over the long
                         //   faces does not band (vertical stripes on the near wall in 3487) [I]
pad_rear_y      = band_end_y;  // the deck board under the rim ends here (deck_board_outline_r); behind it the
                         //   cap's inboard part is a free padded edge rear_cap_pad deep (ramped over pad_ramp) [I]
seat_taper_rear = 3;     // the groove closes over 3 mm behind fibre_climb_y (the fibre dives into the cap) [P] 3491
wall_edge_r     = 0.8;   // the lower edge (bottom and front sweep) is leatherette-wrapped, slightly rounded:
                         //   3489 shows a thin dark rolled border all round the outline [P] [I] 0.5-1.5
wg_eps          = 0.05;
arc_n           = 8;     // facets per quarter round in the band profiles

// =====================================================================================================
// HELPERS
// =====================================================================================================
function clamp01(t) = max(0, min(1, t));
function sstep(t) = let (c = clamp01(t)) c * c * (3 - 2 * c);
function lerp(a, b, t) = a + (b - a) * t;
function qsort(v) = len(v) <= 1 ? v :
    let (p = v[floor(len(v) / 2)])
    concat(qsort([for (a = v) if (a < p) a]), [for (a = v) if (a == p) a], qsort([for (a = v) if (a > p) a]));
function dedupe(v, tol = 0.02) = [for (i = [0 : len(v) - 1]) if (i == 0 || v[i] - v[i - 1] > tol) v[i]];
function stations(v, lo, hi) = dedupe(qsort([for (y = v) if (y >= lo - 1e-9 && y <= hi + 1e-9) y]));
// smooth (C1) interpolation of a table column (rows sorted by key): cubic Hermite with finite-difference slopes.
// linear lookup() put a crease in the wall face at every 10 mm row, and smooth shading turned
// those into regular vertical stripes on the near wall in table_side_3487. Clamped at the ends.
function _slope(T, i, c) = let (n = len(T), a = max(0, i - 1), b = min(n - 1, i + 1)) (T[b][c] - T[a][c]) / (T[b][0] - T[a][0]);
function htab(y, T, c = 1) =
    let (n = len(T))
    y <= T[0][0] ? T[0][c] : y >= T[n - 1][0] ? T[n - 1][c] :
    let (i = max([for (k = [0 : n - 2]) if (T[k][0] <= y) k]), y0 = T[i][0], y1 = T[i + 1][0], h = y1 - y0,
         t = (y - y0) / h, t2 = t * t, t3 = t2 * t,
         m0 = _slope(T, i, c), m1 = _slope(T, i + 1, c))
    (2 * t3 - 3 * t2 + 1) * T[i][c] + (t3 - 2 * t2 + t) * h * m0 + (-2 * t3 + 3 * t2) * T[i + 1][c] + (t3 - t2) * h * m1;
// The tables carry 0.5 mm rounding steps that alternate row to row (slopes 0.05 / 0.1 per mm), so even a smooth
// interpolant ripples with a 20 mm period and the shading showed vertical stripes. The interior rows (y -250..220)
// are therefore lightly smoothed first ([1 2 1]/4, 6 passes: moves them < 0.4 mm); the tip and rear rows are kept.
function _sm1(T, c, lo, hi) = [for (i = [0 : len(T) - 1])
    (i > 0 && i < len(T) - 1 && T[i][0] >= lo && T[i][0] <= hi)
        ? [for (j = [0 : len(T[i]) - 1]) j == c ? (T[i - 1][c] + 2 * T[i][c] + T[i + 1][c]) / 4 : T[i][j]]
        : T[i]];
function _smc(T, cols, lo, hi, k = 0) = k >= len(cols) ? T : _smc(_sm1(T, cols[k], lo, hi), cols, lo, hi, k + 1);
function sm_tab(T, cols, n, lo = -250, hi = 220) = n <= 0 ? T : sm_tab(_smc(T, cols, lo, hi), cols, n - 1, lo, hi);
WF_S = sm_tab(wall_face_pts, [1], 6);
BP_S = sm_tab(band_pts, [1, 2, 3, 4], 6);
function wall_face_xs(y) = htab(y, WF_S, 1);

// side outline split into its top chain (tip -> top-rear corner) and bottom chain (tip -> front sweep ->
// bottom edge -> rear end), both with ascending y, so they can be used with lookup()
yz_max_y  = max([for (p = wing_outline_yz) p[0]]);
yz_i_rear = [for (i = [0 : len(wing_outline_yz) - 1]) if (wing_outline_yz[i][0] == yz_max_y) i][0];
top_chain = [for (i = [0 : yz_i_rear]) wing_outline_yz[i]];
bot_chain = concat([wing_outline_yz[0]],
                   [for (i = [len(wing_outline_yz) - 1 : -1 : yz_i_rear + 1]) wing_outline_yz[i]]);
// the front sweep (tip .. wing_sweep_join_y) is a traced point list; it is followed with a Catmull-Rom
// curve through exactly those points (8 samples per span, tangent into the straight bottom edge), so the
// edge renders smooth instead of polygonal. Deviation from the straight-segment polygon <= 1 mm. [I]
function cr_pt(p0, p1, p2, p3, t) =
    0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t);
sw_n   = len([for (p = bot_chain) if (p[0] <= wing_sweep_join_y + 1e-6) p]);   // points up to the join
sweep_smooth = concat(
    [for (i = [0 : sw_n - 2]) for (t = [0 : 7])
        let (p1 = bot_chain[i], p2 = bot_chain[i + 1],
             p0 = i > 0 ? bot_chain[i - 1] : 2 * p1 - p2, p3 = bot_chain[i + 2])
        cr_pt(p0, p1, p2, p3, t / 8)],
    [for (i = [sw_n - 1 : len(bot_chain) - 1]) bot_chain[i]]);
function out_top(y) = lookup(y, top_chain);
function out_bot(y) = lookup(y, sweep_smooth);   // front sweep forward of wing_sweep_join_y, bottom edge behind

// band columns with the rounded nose in plan (y wing_tip_y .. wing_tip_y + nose_len)
function nose_s(y) = y >= wing_tip_y + nose_len ? 1 :
    let (t = clamp01((wing_tip_y + nose_len - y) / nose_len)) pow(max(0, 1 - pow(t, nose_p)), 1 / nose_p);
function bx_nose(y, i) = y >= wing_tip_y + nose_len ? htab(y, BP_S, i)
                       : tip_x + (htab(wing_tip_y + nose_len, BP_S, i) - tip_x) * nose_s(y);
// REAR CAP blend weights (0 = band_pts, 1 = rear_cap_pts)
function rb_o(y) = sstep((y - rear_cap_y0) / (rear_cap_y1 - rear_cap_y0));             // outer edge, top: 228-248
function rb_i(y) = sstep((y - rear_cap_y0 - 6) / (rear_cap_y1 - rear_cap_y0 - 4));     // inner edge: 234-250
function rb_f(y) = sstep((y - fibre_climb_y) / 10);                                    // fibre zone fades: 242-252
function rb_r(y) = sstep((y - fibre_climb_y + 4) / 24);                                // roll share grows: 238-262
// band columns [1 inner, 2 fibre, 3 outer] and the top z, nose and rear cap included (no end rounding)
function bx(y, i) = i == 1 ? lerp(bx_nose(y, 1), htab(y, rear_cap_pts, 1), rb_i(y))
                  : i == 2 ? lerp(bx_nose(y, 2), htab(y, rear_cap_pts, 1), rb_f(y))   // -> pushed out by the roll (band_sta)
                  : lerp(bx_nose(y, 3), htab(y, rear_cap_pts, 2), rb_o(y));
function band_z(y) = lerp(htab(y, BP_S, 4), htab(y, rear_cap_pts, 3), rb_o(y));
// rounded end of the cap in plan: every x of the section is scaled toward the board's centre line
band_y_end = wing_rear_y - 0.03;
function end_s(y) = y <= wing_rear_y - rear_cap_end_r ? 1
    : let (t = clamp01((y - (wing_rear_y - rear_cap_end_r)) / rear_cap_end_r)) sqrt(max(0, 1 - t * t));
function end_xc(y) = wall_face_xs(y) - wing_thickness / 2;
function end_ring(y, ring) = let (s = end_s(y), c = end_xc(y)) s >= 1 ? ring : [for (q = ring) [c + (q[0] - c) * s, q[1]]];

// fitted-state options: params' fitp(p, side) (0 = free state as scanned; per side since the // so the driver wall can take its own offset although it is built as a mirror of the passenger build).

// build a closed solid from cross-section rings (each a CCW list of [x, z] seen with x right and z up,
// all with the same point count) at increasing y stations; s = side the part is built for
module loft(ys, ring2, s = 1) {
    R  = [for (y = ys) [for (q = ring2(y)) fitp([q[0], y, q[1]], s)]];
    nr = len(R);
    n  = len(R[0]);
    pts = [for (r = R) each r];
    side = [for (i = [0 : nr - 2]) for (j = [0 : n - 1])
                let (a = i * n + j, b = i * n + (j + 1) % n, c = (i + 1) * n + (j + 1) % n, d = (i + 1) * n + j)
                each [[a, b, c], [a, c, d]]];
    cap0 = [for (j = [n - 1 : -1 : 0]) j];
    cap1 = [for (j = [0 : n - 1]) (nr - 1) * n + j];
    polyhedron(points = pts, faces = concat(side, [cap0, cap1]), convexity = 10);
}

// quarter / partial elliptic arc points, angle a0 -> a1 (deg), centre c, radii rx, rz; n segments
function earc(c, rx, rz, a0, a1, n = arc_n, skip0 = false) =
    [for (i = [skip0 ? 1 : 0 : n]) let (a = a0 + (a1 - a0) * i / n) [c[0] + rx * cos(a), c[1] + rz * sin(a)]];

// =====================================================================================================
// WALL (covered board)
// =====================================================================================================
// the board exists where the front sweep has dropped below the board top (band top - band_cap_h)
function board_gap(y) = (band_z(y) - band_cap_h) - out_bot(y);
function y_board0(lo = wing_tip_y, hi = wing_tip_y + 25, n = 40) =
    n == 0 ? hi : let (m = (lo + hi) / 2) board_gap(m) > 0 ? y_board0(lo, m, n - 1) : y_board0(m, hi, n - 1);
wall_y0 = y_board0() + wg_eps;

// the board top is hidden inside the band / rear cap along the whole wall (no bare board edge)
function wall_top(y) = band_z(y) - band_cap_h;

function wall_ring(y) =
    let (xo = wall_face_xs(y), xi = xo - wing_thickness,
         zb = out_bot(y), zt = wall_top(y), h = zt - zb,
         rr = min(0.3, h / 2.2),                               // flat top under the band / cap
         rb = min(wall_edge_r, h / 4),                         // covered lower edge (bottom / front sweep)
         z0 = zb + rb, z1 = zt - rr)
    concat(earc([xi + rb, zb + rb], rb, rb, 180, 270, 3),
           earc([xo - rb, zb + rb], rb, rb, 270, 360, 3),
           [for (i = [1 : wall_face_n]) [xo, lerp(z0, z1, i / (wall_face_n + 1))]],      // up the outer face
           earc([xo - wing_thickness / 2, zt - rr], wing_thickness / 2, rr, 0, 180, 2 * arc_n),
           [for (i = [wall_face_n : -1 : 1]) [xi, lerp(z0, z1, i / (wall_face_n + 1))]]); // down the inner face

wall_ys = stations(concat(
    [wall_y0],
    [for (y = [ceil(wall_y0 / 2) * 2 : 2 : wing_rear_y]) y],   // same 2 mm grid as the band
    [for (p = wing_outline_yz) p[0]],
    [for (p = sweep_smooth) p[0]],
    [for (p = wall_face_pts) p[0]],
    [for (r = band_pts) r[0]],
    [for (r = rear_cap_pts) r[0]],
    [for (y = [rear_cap_y0 : 2 : rear_cap_y1 + 4]) y],
    [wing_rear_y]), wall_y0, wing_rear_y);

module wall_r(s = 1) { loft(wall_ys, function (y) wall_ring(y), s); }

// =====================================================================================================
// BAND (pebble body) and BAND ROLL (smooth black roll)
// =====================================================================================================
// groove opening factor: 1 = open (fibre lies in it), ~0 = closed ahead of the fibre's tapered end (fe, per
// side) and behind fibre_climb_y (where the fibre dives into the cap)
function seat_g(y, fe) = y > fibre_climb_y ? 0.02 + 0.98 * (1 - sstep((y - fibre_climb_y) / seat_taper_rear))
                       : y >= fe + seat_taper ? 1 : y <= fe - seat_taper ? 0.02
                       : 0.02 + 0.98 * sstep((y - (fe - seat_taper)) / (2 * seat_taper));
// how far the smooth roll has swung outward across the band at the tip (0 .. 1)
function wrap_t(y) = sstep((wrap_y0 - y) / (wrap_y0 - wrap_y1));
// inboard padding bottom: on the deck board (z = -deck_vinyl) from the arm noses to the board's rear end under
// the rim (pad_rear_y); forward of the noses it stops pad_front_drop below the band top, behind the deck it stops
// rear_cap_pad below the cap top (ramped over pad_ramp_front at the front, a straight diagonal; pad_ramp at the rear)
function pad_bot(y, zt) = y < arm_front_y ? lerp(-deck_vinyl, zt - pad_front_drop, clamp01((arm_front_y - y) / pad_ramp_front))
    : y <= pad_rear_y ? -deck_vinyl
    : lerp(-deck_vinyl, zt - rear_cap_pad, clamp01((y - pad_rear_y) / pad_ramp));

// all the numbers of one band station, shared by the body and the roll so their faces meet exactly
// (fe = this side's fibre end, for the groove)
function band_sta(y, fe) =
    let (xi = bx(y, 1), xf = bx(y, 2), xo = bx(y, 3), zt = band_z(y),
         w = xo - xi, k = w / band_w, rc = rb_o(y),
         sw = out_bot(y),                                     // front sweep (clips the nose from below)
         zb_out = min(max(zt - band_cap_h, sw), zt - 1.5),    // board top / outer bottom
         zb_in  = min(max(pad_bot(y, zt), sw), zb_out - 0.3), // inboard padding bottom
         vs = min(1, (zt - zb_out) / band_cap_h),             // vertical squeeze near the clipped nose
         xface = min(wall_face_xs(y), xo - band_overhang * k * (1 - rc)),  // wall outer face (= x_outer - 1 along
                                                              //   the band; flush with the cap's outer edge)
         xbin  = max(xface - wing_thickness, xi + 0.3 * w),   // wall inner face
         uR = xi + lerp(lerp(band_roll_w, roll_w_tip, wrap_t(y)) * k, rear_cap_roll * w, rb_r(y)),  // roll's outer edge
         g = seat_g(y, fe),
         sg = g >= 0.999 ? 1 : g * min(1, k),                 // groove scale (fibre size where open)
         ztop_s = zt - band_strip_drop * vs,                  // strip / seat-edge level
         zc = zt - fibre_drop,                                // groove centre (= fibre centre)
         dz = ztop_s - zc,
         hc = sqrt(max(0.01, seat_r * seat_r - dz * dz)),     // half chord of the groove at the strip level
         xs = max(xf, uR + 0.25 * k + sg * hc),               // groove centre x (= band_fibre_x where open)
         zr0 = zt - roll_h * vs)                              // smooth roll bottom
    [xi, xf, xo, zt, w, k, zb_out, zb_in, vs, xface, xbin, uR, sg, ztop_s, zc, dz, hc, xs, zr0];

function band_body_ring(y, fe) =
    let (s = band_sta(y, fe),
         xi = s[0], xo = s[2], zt = s[3], k = s[5], zb_out = s[6], zb_in = s[7], vs = s[8],
         xface = s[9], xbin = s[10], uR = s[11], sg = s[12], ztop_s = s[13], zc = s[14],
         dz = s[15], hc = s[16], xs = s[17], zr0 = s[18],
         cr_h = curl_r * k * (1 + rb_f(y)), cr_v = curl_r * vs,   // the cap's outer roll is rounder (R 4-5 top [S])
         xmax = xo + curl_bulge * k,
         th0 = atan2(dz, hc),
         // groove: arc from the right upper edge round the bottom to the left upper edge, scaled by sg
         groove = [for (i = [0 : 12]) let (a = th0 - (180 + 2 * th0) * i / 12,
                                           p = [xs + seat_r * cos(a), zc + seat_r * sin(a)])
                   [xs + sg * (p[0] - xs), ztop_s + sg * (p[1] - ztop_s)]],
         xr_edge = xs + sg * hc,                              // right edge of the seat
         e = seat_edge_w * k)
    concat(
        [[xi, zb_in], [xbin, zb_in], [xbin, zb_out], [xface, zb_out]],
        [for (i = [1 : arc_n]) let (t = i / arc_n)                                          // ease out of the
            [xface + (xmax - xface) * sstep(t), lerp(zb_out, zt - cr_v, t)]],               //   face -> swell
        earc([xmax - cr_h, zt - cr_v], cr_h, cr_v, 0, 90, arc_n, true),                    // round-over
        earc([xr_edge + e, ztop_s], e, zt - ztop_s, 90, 180, 4),                           // into the seat
        [for (i = [1 : len(groove) - 1]) groove[i]],                                       // seat groove
        [[uR, ztop_s], [uR, zr0]]                                                          // strip, roll seat
    );                                                                                     // -> (xi, zr0) below

function band_body_ring_closed(y, fe) = let (s = band_sta(y, fe))
    end_ring(y, concat(band_body_ring(y, fe), [[s[0], s[18]]]));

function band_roll_ring(y, fe) =
    let (s = band_sta(y, fe),
         xi = s[0], zt = s[3], k = s[5], vs = s[8], uR = s[11], zr0 = s[18], kr = k * (1 + rb_f(y)),
         ro_h = roll_r_out * k, ro_v = roll_r_out * vs, ri_h = roll_r_in * kr, ri_v = roll_r_in * vs)
    end_ring(y, concat([[xi, zr0], [uR, zr0]],
           earc([uR - ro_h, zt - ro_v], ro_h, ro_v, 0, 90, 4),
           earc([xi + ri_h, zt - ri_v], ri_h, ri_v, 90, 180, arc_n)));

band_y0 = wing_tip_y + 0.03;
function band_ys(fe) = stations(concat(
    [for (i = [0 : 24]) band_y0 + (wing_tip_y + nose_len - band_y0) * pow(i / 24, 2)],   // dense at the point
    [for (y = [wing_tip_y + nose_len : 2 : wing_rear_y - rear_cap_end_r]) y],
    [for (r = band_pts) r[0]],
    [for (r = rear_cap_pts) r[0]],
    [for (i = [0 : 15]) arm_front_y - pad_ramp_front * i / 15],
    [for (i = [0 : 6]) pad_rear_y + pad_ramp * i / 6],
    [for (i = [-3 : 3]) fe + seat_taper * i / 3],
    [for (i = [0 : 6]) fibre_climb_y + seat_taper_rear * i / 6],
    [for (i = [0 : 16]) (wing_rear_y - rear_cap_end_r) + (band_y_end - wing_rear_y + rear_cap_end_r) * (1 - pow(1 - i / 16, 2))],
    [band_y_end]), band_y0, band_y_end);

module band_r(s = 1)      { fe = fibre_end_y_side(s); loft(band_ys(fe), function (y) band_body_ring_closed(y, fe), s); }
module band_roll_r(s = 1) { fe = fibre_end_y_side(s); loft(band_ys(fe), function (y) band_roll_ring(y, fe), s); }

// =====================================================================================================
// PARTS
// =====================================================================================================
module side(s) { if (s > 0) children(); else mirror([1, 0, 0]) children(); }
module wall(s)      { side(s) wall_r(s); }
module band(s)      { side(s) band_r(s); }
module band_roll(s) { side(s) band_roll_r(s); }

module everything() {
    for (s = [1, -1]) {
        color([0.13, 0.13, 0.14]) wall(s);
        color([0.24, 0.24, 0.26]) band(s);
        color([0.05, 0.05, 0.05]) band_roll(s);
    }
}

// flat cross-sections for checking the band profile (preview only): stations laid out along x
module sections() {
    ys = [-272, -265, -250, -219, -150, 0, 150, 230, 241, 246, 255, 270, 285, 291];
    for (i = [0 : len(ys) - 1]) let (y = ys[i]) translate([i * 40 - bx(y, 1), 0, 0]) {
        color([0.24, 0.24, 0.26]) polygon(band_body_ring_closed(y, fibre_end_y));
        color([0.05, 0.05, 0.05]) translate([0, 0, 0.1]) polygon(band_roll_ring(y, fibre_end_y));
        if (y >= wall_y0) color([0.5, 0.5, 0.55]) translate([0, 0, -0.1]) polygon(wall_ring(y));
    }
}

if (part == "right")                wall(1);
else if (part == "left")            wall(-1);
else if (part == "band_right")      band(1);
else if (part == "band_left")       band(-1);
else if (part == "band_roll_right") band_roll(1);
else if (part == "band_roll_left")  band_roll(-1);
else if (part == "all")             everything();
else if (part == "section")         sections();
else if (part == "context") {
    everything();
    color([0.10, 0.10, 0.11]) import("../stl/deck_vinyl.stl");
    color([0.55, 0.40, 0.25]) import("../stl/deck.stl");
    color([0.85, 0.95, 1.00]) { import("../stl/fibre_l.stl"); import("../stl/fibre_r.stl"); }
}
