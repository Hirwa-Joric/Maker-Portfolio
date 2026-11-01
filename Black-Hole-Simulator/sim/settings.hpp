// Command-line settings shared by the 3D explorer and the 2D ray-path view.
#pragma once
#include "physical_constants.hpp"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>

struct Settings {
    // window and output
    int   windowW = 800, windowH = 600;  // in points; a Retina screen doubles the pixels
    int   imageW = 0, imageH = 0;        // 3D: traced image size (0 = the pixels under the window)
    bool  imageSizeFixed = false;
    std::string videoPath;               // record every frame to this .mp4
    int   frameLimit = 0;                // quit after this many frames (0 = never)
    std::string captureDir = ".";        // P saves to <dir>/stills, V to <dir>/footage
    bool  printTimes = false;
    bool  startPaused = false;

    // 3D view
    float camDistance = 22.0f, camAzimuthDeg = 35.0f, camPolarDeg = 83.0f; // r_s, degrees
    float orbitDegPerSec = 0.0f;
    int   style = 1;                     // 1 = standard (stars, glowing gas), 0 = grid diagnostic
    bool  angularGrid = true;
    bool  showDisk = true;
    bool  showSuns = true;
    bool  predictionRing = false;
    bool  sunLensing = true;             // the suns bend light as well as the hole
    int   stage = 2;                     // learning stage: 0 straight light, 1 bent light, 2 everything
    bool  curvedSheet = true;            // the rubber-sheet grid under the disk
    bool  gravityArrows = false;         // arrows showing gravity's pull
    int   buttons = -1;                  // on-screen switches: -1 = except in recordings, 0 = never, 1 = always
    float flare = 1.0f;                  // lens flare strength (0 = off)
    bool  flareOn = true;
    float spin = 1.0f;                   // speed of the gas and the suns (0 = still)
    float exposure = 1.0f, glow = 1.0f, skyGain = 1.0f;
    float previewScale = 0.25f;          // image scale while the camera moves
    int   samplesLive = 8, samplesVideo = 3;

    // star experiments
    bool  mutualGravity = true;          // the suns pull on one another (off: scripted circles)
    bool  ghostCopy = false;
    bool  trails = false;
    bool  disruption = true;             // the hole's tides stretch and tear the suns
    bool  disruptionDemo = false;

    // measurements
    bool  measureShadow = false;
    int   benchmarkRuns = 0;

    // 2D
    int   rayCount = 24;
    int   stepsPerFrame = 1;
};

inline void printUsage(const char* program) {
    std::printf(
        "usage: %s [options]\n"
        "  --scales            print the Sagittarius A* mass and derived scales, then quit\n"
        "  --size WxH          window size in points (960x540 gives 1920x1080 video on a Retina Mac)\n"
        "  --cam R,AZ,POLAR    3D camera: distance in r_s, azimuth and polar angle in degrees (90 = disk plane)\n"
        "  --orbit DEG         3D: orbit the camera at DEG degrees per second\n"
        "  --look standard|grid  3D: stars and glowing gas (default) or the grid diagnostic\n"
        "  --grid / --no-grid  3D: show or hide the lensed angular grid (shown by default)\n"
        "  --no-disk           3D: hide the accretion disk (key D)\n"
        "  --no-suns           3D: no orbiting suns\n"
        "  --no-sun-lensing    3D: only the hole bends light, not the suns (key G)\n"
        "  --stage N           3D: learning stage 1 straight light, 2 bent light and a plain disk,\n"
        "                      3 everything (default; keys 1, 2, 3)\n"
        "  --no-sheet          3D: hide the curved-space sheet (key E)\n"
        "  --gravity           3D: show arrows for gravity's pull (key A)\n"
        "  --no-buttons        3D: hide the on-screen switches (key U); --buttons shows them in recordings\n"
        "  --flare F           3D: lens flare from the suns (default 1, 0 = off; key O)\n"
        "  --check             3D: draw the predicted shadow edge (key K)\n"
        "  --spin S            3D: speed of the gas and the suns (default 1, 0 = still)\n"
        "  --exposure E        3D: image brightness (default 1)\n"
        "  --glow G            3D: soft glow around bright parts (default 1, 0 = off)\n"
        "  --sky-gain G        3D: sky brightness (default 1; 6 makes the shadow's edge stand out)\n"
        "  --res WxH           3D: traced image size (default: the screen pixels under the window)\n"
        "  --preview F         3D: image scale while moving (default 0.25, 1 = never reduce)\n"
        "  --aa N              3D: samples per pixel (default 8 when still, 3 in recordings)\n"
        "  --nbody             3D: the suns pull on one another around a fixed hole (default; key N)\n"
        "  --circles           3D: scripted circular orbits instead, nothing pulls or tears\n"
        "  --ghost             3D: with --nbody, a copy started 1e-6 r_s away (about 12.7 km; key C)\n"
        "  --trails            3D: draw the suns' paths (key T)\n"
        "  --fates             3D: Paczynski-Wiita gravity, tidal stretching and disruption (default; key F)\n"
        "  --no-fates          3D: mutual gravity without tidal disruption\n"
        "  --tde-demo          3D: one star falls from 30 r_s on a grazing orbit (closest 6 r_s)\n"
        "  --measure           3D: measure the shadow against the prediction, print, quit\n"
        "  --bench N           3D: trace the full image N times, print the times, quit\n"
        "  --rays N            2D: fire N parallel light rays\n"
        "  --speed K           2D: integration steps per frame\n"
        "  --record FILE.mp4   write every frame to a video (needs ffmpeg)\n"
        "  --frames N          quit after N frames\n"
        "  --out DIR           where P saves stills (DIR/stills) and V saves video (DIR/footage)\n"
        "  --paused            start with time frozen (SPACE starts it)\n"
        "  --fps               print frame and trace times\n"
        "keys (3D): drag or arrows rotate, scroll or W/S or +/- zoom, SPACE freeze time,\n"
        "           1/2/3 learning stage, E sheet, A gravity arrows, G suns bend light, H grid,\n"
        "           O flare, K prediction ring, N suns pull, F tides tear suns, R new suns,\n"
        "           C ghost copy, T trails, D disk, L look, U buttons, P still, V video, ESC quit\n"
        "keys (2D): SPACE pause, R restart, P still, ESC quit\n", program);
}

inline Settings readSettings(int argc, char** argv) {
    Settings s;
    auto fail = [&](const std::string& message) {
        std::fprintf(stderr, "%s\n", message.c_str());
        printUsage(argv[0]);
        std::exit(1);
    };
    for (int i = 1; i < argc; ++i) {
        const std::string flag = argv[i];
        auto value = [&]() -> std::string {
            if (i + 1 >= argc) fail("missing value after " + flag);
            return argv[++i];
        };
        auto size = [&](int& w, int& h) {
            if (std::sscanf(value().c_str(), "%dx%d", &w, &h) != 2 || w <= 0 || h <= 0)
                fail("expected WxH after " + flag);
        };
        if      (flag == "--scales")    { physical::printScales(); std::exit(0); }
        else if (flag == "--help" || flag == "-h") { printUsage(argv[0]); std::exit(0); }
        else if (flag == "--size")      size(s.windowW, s.windowH);
        else if (flag == "--res")       { size(s.imageW, s.imageH); s.imageSizeFixed = true; }
        else if (flag == "--cam") {
            if (std::sscanf(value().c_str(), "%f,%f,%f", &s.camDistance, &s.camAzimuthDeg, &s.camPolarDeg) != 3)
                fail("expected R,AZ,POLAR after --cam");
        }
        else if (flag == "--orbit")     s.orbitDegPerSec = std::stof(value());
        else if (flag == "--look") {
            const std::string look = value();
            if (look == "standard") s.style = 1;
            else if (look == "grid") s.style = 0;
            else fail("--look takes standard or grid");
        }
        else if (flag == "--grid")      s.angularGrid = true;
        else if (flag == "--no-grid")   s.angularGrid = false;
        else if (flag == "--no-disk")   s.showDisk = false;
        else if (flag == "--no-suns")   s.showSuns = false;
        else if (flag == "--no-sun-lensing") s.sunLensing = false;
        else if (flag == "--stage")     s.stage = std::clamp(std::stoi(value()), 1, 3) - 1;
        else if (flag == "--no-sheet")  s.curvedSheet = false;
        else if (flag == "--gravity")   s.gravityArrows = true;
        else if (flag == "--no-buttons") s.buttons = 0;
        else if (flag == "--buttons")   s.buttons = 1;
        else if (flag == "--flare")     { s.flare = std::max(0.0f, std::stof(value())); s.flareOn = s.flare > 0.0f; if (!s.flareOn) s.flare = 1.0f; }
        else if (flag == "--check")     s.predictionRing = true;
        else if (flag == "--spin")      s.spin = std::stof(value());
        else if (flag == "--exposure")  s.exposure = std::stof(value());
        else if (flag == "--glow")      s.glow = std::stof(value());
        else if (flag == "--sky-gain")  s.skyGain = std::stof(value());
        else if (flag == "--preview")   s.previewScale = std::clamp(std::stof(value()), 0.1f, 1.0f);
        else if (flag == "--aa")        s.samplesLive = s.samplesVideo = std::max(1, std::stoi(value()));
        else if (flag == "--nbody")     s.mutualGravity = true;
        else if (flag == "--ghost")     s.ghostCopy = true;
        else if (flag == "--trails")    s.trails = true;
        else if (flag == "--fates")     s.disruption = s.mutualGravity = true;
        else if (flag == "--no-fates")  s.disruption = false;
        else if (flag == "--circles")   s.mutualGravity = s.disruption = false;
        else if (flag == "--tde-demo")  s.disruptionDemo = s.disruption = s.mutualGravity = true;
        else if (flag == "--measure")   s.measureShadow = true;
        else if (flag == "--bench")     s.benchmarkRuns = std::max(1, std::stoi(value()));
        else if (flag == "--rays")      s.rayCount = std::max(0, std::stoi(value()));
        else if (flag == "--speed")     s.stepsPerFrame = std::max(1, std::stoi(value()));
        else if (flag == "--record")    s.videoPath = value();
        else if (flag == "--frames")    s.frameLimit = std::max(0, std::stoi(value()));
        else if (flag == "--out")       s.captureDir = value();
        else if (flag == "--paused")    s.startPaused = true;
        else if (flag == "--fps")       s.printTimes = true;
        else fail("unknown option " + flag);
    }
    return s;
}
