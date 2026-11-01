# Physical scales and validation

## Adopted model

The central mass is 4.30 × 10⁶ solar masses, the rounded GRAVITY estimate for Sagittarius A* reported by [ESO](https://www.eso.org/public/news/eso2119/). [physical_constants.hpp](physical_constants.hpp) is shared by both programs. Inside the tracer every length is measured in Schwarzschild radii, so the hole's radius is exactly 1 there.

| Quantity | Value |
|---|---|
| Mass | 8.550421 × 10³⁶ kg |
| Schwarzschild radius, 2GM/c² | 1.2699359 × 10¹⁰ m |
| Light-crossing time, r_s/c | 42.3605 s |
| Ghost initial displacement, 10⁻⁶ r_s | 12.6994 km |
| Solar-star tidal radius, R☉(M/M☉)⅓ | 8.90833 r_s |

`./BlackHole3D --scales` and `./BlackHole2D --scales` print these values without opening a window.

## Light paths

In Schwarzschild coordinates a light ray stays in a plane through the hole and obeys u″ + u = 3/2 u² (u = r_s/r, primes are derivatives with respect to the angle). Writing the position as a vector x with |x| = r, the same paths solve x″ = −3/2 h² x / r⁵, where h = |x × x′| is conserved. The tracer integrates this with fourth-order Runge–Kutta steps of 1% of r near the hole, growing to 8% far away (twice that in the moving preview). The camera is at rest at its radius; its viewing directions are converted to coordinate directions by shortening the radial part by √(1 − r_s/r). A ray heading inwards inside 1.5 r_s cannot turn back and is counted as captured.

## Shadow test

For a viewer at rest at radius r, the predicted angular radius of the shadow is

```text
sin(alpha) = (3 sqrt(3) / 2) (r_s / r) sqrt(1 - r_s / r)
```

The measurement mode traces which rays are captured, walks out from the image centre in 16 directions to the shadow's edge and compares the median with the prediction. Measured on 29 October 2026 at 1600 × 1200 pixels with the disk and suns hidden:

| Camera distance | Relative angular-radius error |
|---|---|
| 5 r_s | +0.00% |
| 10 r_s | −0.11% |
| 20 r_s | +0.26% |
| 40 r_s | +0.32% |
| 60 r_s | −0.37% |

Reproduce a row from `build/`, changing the distance:

```sh
./BlackHole3D --cam 10,0,90 --no-suns --no-disk --res 1600x1200 --measure
```

The error stays below 0.4%. Finite pixels limit the edge estimate, especially for small, distant shadows. The printed mask-area ratio compares the mask with a circle of the measured radius and can slightly exceed 100%. The test checks the shadow's geometry, not every part of the scene.

## Rendering performance

Measurements from the 29 October 2026 test session on an Apple silicon Mac, with OpenGL 4.1 on Metal, tracing the default 640 × 360 view:

| Mode | Time per image |
|---|---|
| Suns not bending light | 6.0 ms |
| Suns bending light (default) | 9.6 ms |

In the same session, the default moving view ran at about 77 frames per second. A still 1600 × 1200 image finished in about 98 ms. The resolution-comparison still uses a different 16:9 framing, at 160 × 90 and 1600 × 900; it illustrates the difference in detail rather than that timed 1600 × 1200 test.

## Approximations

- **The suns' masses are exaggerated** (8%, 6% and 10% of the hole) so that their pull on one another, and on light, is visible. A star like the Sun has about a four-millionth of the hole's mass.
- **The suns bend light in the weak-field limit**: a deflection of 4Gm/(c²b), applied as a small kick at each step around the exact equation for the hole. This is accurate far from a sun and approximate near its surface.
- **Mutual gravity is Newtonian** around a fixed hole (softened at close range); the suns are not models of the observed S stars. The hole's pull on the suns uses the Paczyński–Wiita potential, which puts the last stable circular orbit at 3 r_s but is not relativistic stellar dynamics. The red sun starts at 85% of circular speed so the three disturb one another early; in the recorded default run the hole tears the red sun apart at 3.6 s and the blue-white sun at 22.1 s. The orbits are chaotic, so live runs, whose time steps follow the frame rate, differ.
- **Tidal stretching** is a picture of the tide's strength: a sun becomes an ellipsoid of the same volume, longer along the line to the hole by 1 + 0.6 (r_t/r)⁴ (capped). It is not a stellar-structure calculation.
- **Disruption** uses a solar-star tidal radius, r_t ≈ 8.9 r_s, despite the exaggerated sizes and masses. The debris loses angular momentum through a made-up drag, without hydrodynamics. Suns that touch are both turned into debris; a sun beyond 60 r_s counts as flung out; new suns arrive 8 s after the last one goes.
- **The disk** is a thin surface: light is added where rays cross it, weighted by the transparency left, with Doppler and gravitational shifts. It is not a simulated gas volume, and the brightness and colour rules are illustrative, not calibrated.
- **The curved-space sheet and gravity arrows** are drawn straight over the image without bending. The sheet's depth follows the Newtonian potential of the hole and the suns; the arrows show the Newtonian pull. They are pictures of gravity, separate from the light calculation.
- **The lens flare** imitates a camera lens. It is not something in space.
- The glow, sky, sun sizes and playback speed are illustrative. Matching the mass does not make the image an observation of Sagittarius A*.

## Runtime regression checks

`ctest --test-dir build --output-on-failure` checks the default 2D ray count, star timing and capture behavior. With tidal disruption disabled, a one-second update and the same second divided into 30, 60 or 120 frames agree within 0.00004 Schwarzschild radii. This checks frame-rate consistency of the integrator, not the physical accuracy of the approximate stellar model. Capture checks preserve literal filenames containing shell punctuation and report a missing encoder as a failure.
