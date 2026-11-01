# Sources and contributions

## My work

I developed this project to explore a black hole from different viewpoints and check the image against the physics. I chose Sagittarius A* as the mass scale and used the predicted shadow to test the renderer. From there, I explored bending starlight, interacting suns and tidal disruption. The visual design, controls, experiments and validation serve the same question: what can I learn by moving around a calculated image instead of looking at one still?

The references below identify the physics, rendering methods and libraries used in the project.

## Inspiration

Jean-Pierre Luminet, "Image of a spherical black hole with thin accretion disk", *Astronomy and Astrophysics* **75**, 228–235 (1979): the first calculated image of a black hole.

## Learning sources

- Peter Shirley, Trevor David Black and Steve Hollasch, [*Ray Tracing in One Weekend*](https://raytracing.github.io/books/RayTracingInOneWeekend.html): constructing rays through camera pixels and testing their intersections with objects.
- 20k, ["Implementing General Relativity: Rendering the Schwarzschild black hole, in C++"](https://20k.github.io/c%2B%2B/2024/05/31/schwarzschild.html), 31 May 2024: geodesic tracing, camera frames and deciding whether a ray escapes or enters the hole. The accompanying example integrates four-dimensional geodesics on the CPU using metric derivatives and Christoffel symbols. My current tracer uses the Cartesian photon-orbit equation with RK4 in a GLSL fragment shader.
- Rishabh Karthikeyan Hariharan, "Simulating a black hole in python", August 2025, [DOI 10.13140/RG.2.2.29922.85441](https://doi.org/10.13140/RG.2.2.29922.85441): backward ray tracing and relativistic frequency shifts. His published example describes a rotating Kerr black hole using Hamiltonian geodesics; my project uses the non-rotating Schwarzschild model.

## Current implementation

The interactive program combines a GLSL light tracer with a C++/OpenGL viewer, a preview sized to the GPU's measured speed, interacting suns, approximate tidal disruption, gravity views and a mode for measuring the shadow. I developed and tested these features together as an exploration of the image. The physical equations and published rendering methods are credited below.

The [Python companion](../prototype/) and [shader lessons](../learning/) explain the calculation in smaller steps. They are teaching examples prepared alongside the current program, rather than an archive of its early source files. [Validation](../sim/VALIDATION.md) records measured results and the limits of the model.

## Data

Sagittarius A* mass (4.30 million solar masses) from the GRAVITY Collaboration / [ESO](https://www.eso.org/public/news/eso2119/).

## Published methods used

- Weak-field light deflection, 4GM/(c²b), for the suns' bending of light.
- The Paczyński–Wiita potential (1980), for the approximate last stable orbit at 3 r_s.
- The PCG RXS-M-XS integer permutation for the stars and noise; see [Nathan Reed's explanation and references](https://www.reedbeta.com/blog/hash-functions-for-gpu-rendering/).
- [John Hable's filmic curve](https://filmicworlds.com/blog/filmic-tonemapping-operators/) for mapping bright light to the screen.
- Planck's law, sampled at 680, 550 and 440 nm and balanced to 6500 K; an illustrative approximation, not colour-matching integration.
- Catmull–Rom upscaling, Halton sample positions and a Gaussian blur for the preview, smoothing and glow.

## Libraries and tools

OpenGL, GLFW, GLEW and GLM for graphics and mathematics; FFmpeg for stills and video; NumPy for the Python prototype.

## AI assistance

I used Claude to explain concepts in simple terms, find the names of methods and terms, and suggest where to look for answers; I wrote all the code myself.
