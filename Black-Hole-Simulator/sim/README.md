# Simulator source

A C++17/OpenGL 4.1 ray tracer for light around a Schwarzschild black hole, with an interactive 3D view and a separate 2D view of ray paths. The [project overview](../README.md) has the story, controls and still images.

## Build on macOS

Tested on Apple silicon with Apple Clang, CMake 4 and OpenGL 4.1. Install Apple's Command Line Tools (`xcode-select --install`) and Homebrew first. From this directory:

```sh
brew install cmake glfw glew glm ffmpeg
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
cd build
./BlackHole3D
```

Run from `build/`, where the build copies the `shaders/` folder. `./BlackHole2D` opens the 2D ray paths. Both programs take `--help`, and `--scales` prints the mass and derived scales without opening a window.

Run `ctest --test-dir build --output-on-failure` from this source directory to check the default ray count, frame-independent star timing and capture filenames/failures. These checks use FFmpeg but do not open a graphics window.

## Source map

| File | What it does |
|---|---|
| [app3d.cpp](app3d.cpp) | The 3D program: window, controls, the progressive view loop, recording, `--measure` and `--bench` |
| [shaders/trace.frag](shaders/trace.frag) | Follows each pixel's light ray (RK4 on x″ = −3/2 h² x / r⁵), the suns' weak-field bending, the disk, sky, tidally stretched suns and the three learning stages |
| [tracer.hpp](tracer.hpp) | Runs the trace on the GPU a few rows at a time, averages sub-pixel samples, builds the glow and lens flare, shows the image |
| [star_system.hpp](star_system.hpp) | The three suns: mutual gravity, tidal stretching and disruption, collisions, new suns, the ghost copy, or scripted circles |
| [overlay.hpp](overlay.hpp) | The curved-space sheet, gravity arrows, trails, tidal ring and debris drawn over the image |
| [toolbar.hpp](toolbar.hpp) | The on-screen switches and their small built-in font |
| [orbit_camera.hpp](orbit_camera.hpp) | The camera on its sphere round the hole, and the predicted shadow angle |
| [settings.hpp](settings.hpp) | Command-line options and help |
| [capture.hpp](capture.hpp) | Stills and video through FFmpeg |
| [gl_tools.hpp](gl_tools.hpp) | Shader loading, render targets and the full-screen triangle |
| [paths2d.cpp](paths2d.cpp) | The 2D program: parallel rays integrated on the CPU in double precision |
| [physical_constants.hpp](physical_constants.hpp) | The Sagittarius A* mass, SI constants and derived scales, shared by both programs |
| [shaders/](shaders/) | Display (filmic curve, upscaling), glow, flare, overlay and 2D shaders |

## Useful experiments

```sh
./BlackHole3D --scales
./BlackHole3D --cam 10,0,90 --no-suns --no-disk --res 1600x1200 --measure
./BlackHole3D --cam 40,-20,84 --sky-gain 3            # a sun's Einstein ring
./BlackHole3D --gravity --ghost --trails              # gravity arrows; suns pull and get torn apart
./BlackHole3D --cam 24,-40,70                          # close to the first tidal disruption
./BlackHole3D --stage 2                                # bent light with a plain teaching disk
./BlackHole3D --circles                                # scripted circles: nothing pulls or tears
./BlackHole3D --tde-demo --trails
./BlackHole3D --size 640x360 --res 640x360 --bench 12
./BlackHole2D --rays 24 --speed 4
```

The program prints a line when a sun is torn apart, collides, falls in or is flung out. `--look grid` swaps the starfield for a black sky and a brighter lensed grid. `--no-sun-lensing`, `--no-sheet`, `--flare 0` and `--no-buttons` turn off the newer views. The ghost copy starts 10⁻⁶ Schwarzschild radii (about 12.7 km) from the first sun. The star demonstrations use normalized units and accelerated playback, so screen time is not elapsed Galactic-Centre time. See [validation and limitations](VALIDATION.md).
