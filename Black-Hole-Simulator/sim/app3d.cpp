// BlackHole3D: fly around Sagittarius A* and watch light bend.
//
// Each frame the GPU follows light rays back from the camera (shaders/trace.frag).
// While the view moves, a small quick image is traced; once it stops, the image
// sharpens and its edges are smoothed over several samples per pixel.
#include "capture.hpp"
#include "overlay.hpp"
#include "settings.hpp"
#include "star_system.hpp"
#include "toolbar.hpp"
#include "tracer.hpp"
#include <GLFW/glfw3.h>
#include <glm/gtc/matrix_transform.hpp>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

namespace {

struct App {
    Settings settings;
    GLFWwindow* window = nullptr;
    int windowW = 0, windowH = 0;     // points
    int pixelsW = 0, pixelsH = 0;     // framebuffer pixels
    Tracer tracer;
    Overlay overlay;
    Toolbar toolbar;
    StarSystem stars;
    OrbitCamera camera;

    // controls
    bool paused = false;
    bool dragging = false;
    double pointerX = 0.0, pointerY = 0.0, lastInput = -1.0;
    bool lookChanged = false, restartStars = false, toggleVideo = false;
    bool inputLocked = false;          // while recording a scripted shot

    void openWindow() {
        if (!glfwInit()) { std::fprintf(stderr, "GLFW could not start\n"); std::exit(1); }
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
        if (!settings.videoPath.empty() || settings.benchmarkRuns > 0 || settings.measureShadow) {
            glfwWindowHint(GLFW_FOCUSED, GLFW_FALSE); // a background job: don't take the keyboard
            glfwWindowHint(GLFW_FOCUS_ON_SHOW, GLFW_FALSE);
        }
        window = glfwCreateWindow(settings.windowW, settings.windowH,
                                  physical::windowTitle("3D view").c_str(), nullptr, nullptr);
        if (!window) { std::fprintf(stderr, "no OpenGL 4.1 window\n"); glfwTerminate(); std::exit(1); }
        glfwMakeContextCurrent(window);
        glewExperimental = GL_TRUE;
        if (glewInit() != GLEW_OK) { std::fprintf(stderr, "GLEW could not start\n"); std::exit(1); }
        std::printf("OpenGL %s\n", reinterpret_cast<const char*>(glGetString(GL_VERSION)));
        glfwGetWindowSize(window, &windowW, &windowH);
        glfwGetFramebufferSize(window, &pixelsW, &pixelsH);
        if (!settings.imageSizeFixed) { settings.imageW = pixelsW; settings.imageH = pixelsH; }
        glfwSetWindowUserPointer(window, this);
        glfwSetMouseButtonCallback(window, onButton);
        glfwSetCursorPosCallback(window, onPointer);
        glfwSetScrollCallback(window, onScroll);
        glfwSetKeyCallback(window, onKey);
    }

    static App& of(GLFWwindow* w) { return *static_cast<App*>(glfwGetWindowUserPointer(w)); }

    static void onButton(GLFWwindow* w, int button, int action, int) {
        App& app = of(w);
        if (app.inputLocked || (button != GLFW_MOUSE_BUTTON_LEFT && button != GLFW_MOUSE_BUTTON_MIDDLE)) return;
        if (action == GLFW_PRESS && button == GLFW_MOUSE_BUTTON_LEFT) {
            double x = 0.0, y = 0.0;
            glfwGetCursorPos(w, &x, &y);
            if (app.toolbar.click(x, y, app.windowH)) return; // a switch, not the start of a drag
        }
        app.dragging = action == GLFW_PRESS;
        if (app.dragging) glfwGetCursorPos(w, &app.pointerX, &app.pointerY);
    }
    static void onPointer(GLFWwindow* w, double x, double y) {
        App& app = of(w);
        if (app.inputLocked) return;
        if (app.dragging) {
            app.camera.turn(0.01f * float(x - app.pointerX), -0.01f * float(y - app.pointerY));
            app.lastInput = glfwGetTime();
        }
        app.pointerX = x;
        app.pointerY = y;
    }
    static void onScroll(GLFWwindow* w, double, double steps) {
        App& app = of(w);
        if (app.inputLocked) return;
        app.camera.zoom(float(std::pow(0.93, steps)));
        app.lastInput = glfwGetTime();
    }
    static void onKey(GLFWwindow* w, int key, int, int action, int) {
        if (action != GLFW_PRESS) return;
        App& app = of(w);
        Settings& s = app.settings;
        switch (key) {
            case GLFW_KEY_ESCAPE: glfwSetWindowShouldClose(w, GLFW_TRUE); break;
            case GLFW_KEY_SPACE:  app.paused = !app.paused; break;
            case GLFW_KEY_L: s.style = 1 - s.style; app.lookChanged = true; break;
            case GLFW_KEY_E: app.flip(Switch::CurvedSpace); break;
            case GLFW_KEY_A: app.flip(Switch::Gravity); break;
            case GLFW_KEY_G: app.flip(Switch::SunsBendLight); break;
            case GLFW_KEY_H: app.flip(Switch::SkyGrid); break;
            case GLFW_KEY_O: app.flip(Switch::LensFlare); break;
            case GLFW_KEY_K: app.flip(Switch::Prediction); break;
            case GLFW_KEY_N: app.flip(Switch::StarsPull); break;
            case GLFW_KEY_F: app.flip(Switch::Tides); break;
            case GLFW_KEY_R: app.restartStars = true; break;
            case GLFW_KEY_U: app.toolbar.visible = !app.toolbar.visible; break;
            case GLFW_KEY_1: case GLFW_KEY_2: case GLFW_KEY_3:
                s.stage = key - GLFW_KEY_1;
                app.lookChanged = true;
                break;
            case GLFW_KEY_D: s.showDisk = !s.showDisk; app.lookChanged = true; break;
            case GLFW_KEY_C: s.ghostCopy = !s.ghostCopy; break;
            case GLFW_KEY_T: s.trails = !s.trails; break;
            case GLFW_KEY_P: {
                int fw = 0, fh = 0;
                glfwGetFramebufferSize(w, &fw, &fh);
                capture::saveStill(fw, fh, s.captureDir + "/stills");
                break;
            }
            case GLFW_KEY_V: app.toggleVideo = true; break;
            default: break;
        }
    }

    // The views that have both a key and an on-screen switch, in the switches' order.
    enum class Switch { Stage, CurvedSpace, Gravity, SunsBendLight, SkyGrid, LensFlare, Prediction, StarsPull, Tides };
    void flip(Switch which) { toolbar.buttons[size_t(which)].toggle(); }

    void addSwitches() {
        Settings& s = settings;
        toolbar.visible = s.buttons == 1 || (s.buttons == -1 && s.videoPath.empty());
        toolbar.buttons = {
            {stageLabel(), [&s] { return s.stage != 2; }, [this] { settings.stage = (settings.stage + 1) % 3; lookChanged = true; }},
            {"CURVED SPACE", [&s] { return s.curvedSheet; }, [&s] { s.curvedSheet = !s.curvedSheet; }},
            {"GRAVITY", [&s] { return s.gravityArrows; }, [&s] { s.gravityArrows = !s.gravityArrows; }},
            {"SUNS BEND LIGHT", [&s] { return s.sunLensing; }, [this] { settings.sunLensing = !settings.sunLensing; lookChanged = true; }},
            {"SKY GRID", [&s] { return s.angularGrid; }, [this] { settings.angularGrid = !settings.angularGrid; lookChanged = true; }},
            {"LENS FLARE", [&s] { return s.flareOn; }, [&s] { s.flareOn = !s.flareOn; }},
            {"PREDICTION", [&s] { return s.predictionRing; }, [this] { settings.predictionRing = !settings.predictionRing; lookChanged = true; }},
            {"STARS PULL", [&s] { return s.mutualGravity; }, [this] {
                settings.mutualGravity = !settings.mutualGravity;
                if (!settings.mutualGravity) settings.disruption = false; // scripted circles: nothing tears
                restartStars = true;
            }},
            {"TIDES TEAR STARS", [&s] { return s.disruption; }, [this] {
                settings.disruption = !settings.disruption;
                if (settings.disruption) settings.mutualGravity = true;
                restartStars = true;
            }},
        };
    }

    // The learning stages retrace the project's path: ordinary ray tracing, then light
    // bent by the hole with the first version's plain disk, then everything.
    std::string stageLabel() const {
        static const char* names[3] = {"STAGE 1: STRAIGHT LIGHT", "STAGE 2: BENT LIGHT", "STAGE 3: EVERYTHING"};
        return names[settings.stage];
    }

    void syncStarSettings() {
        stars.mutual = settings.mutualGravity;
        stars.ghost = settings.ghostCopy;
        stars.disruption = settings.disruption;
        stars.demo = settings.disruptionDemo;
    }

    View view(double time) const {
        View v;
        v.camera = camera;
        v.aspect = float(windowW) / float(windowH);
        v.style = settings.style;
        v.angularGrid = settings.angularGrid;
        v.disk = settings.showDisk;
        v.predictionRing = settings.predictionRing;
        v.sunLensing = settings.sunLensing;
        v.stage = settings.stage;
        v.skyGain = settings.skyGain;
        v.diskGain = stars.diskGain();
        v.spinTime = float(time);
        if (settings.showSuns) v.suns = stars.suns(time);
        return v;
    }

    // Lines and points over the image, seen from the camera of the image on show.
    void drawOverlays(const OrbitCamera& shown, const std::vector<Sun>& suns) {
        const glm::vec3 eye = shown.position();
        const glm::mat4 projection = glm::perspective(glm::radians(60.0f), float(windowW) / float(windowH), 0.05f, 1e4f);
        overlay.setView(projection * glm::lookAt(eye, glm::vec3(0.0f), glm::vec3(0, 1, 0)), eye);
        if (settings.curvedSheet)
            overlay.curvedSheet(suns, settings.style == 0 ? glm::vec4(0.4f, 0.4f, 0.4f, 0.35f)
                                                          : glm::vec4(0.35f, 0.5f, 0.85f, 0.22f));
        if (settings.gravityArrows) overlay.gravityArrows(suns);
        if (settings.trails && settings.showSuns) {
            for (int k = 0; k < 2 * StarSystem::count; ++k) {
                const bool isGhost = k >= StarSystem::count;
                if (isGhost && !(settings.mutualGravity && settings.ghostCopy)) continue;
                const glm::vec3 c = stars.design[k % StarSystem::count].colour;
                glm::vec3 tint = c / std::max(c.r, 1.0f);
                if (isGhost) tint = 0.5f * tint + glm::vec3(0.25f, 0.4f, 0.8f);
                overlay.lines(stars.trail[k], GL_LINE_STRIP, glm::vec4(tint, isGhost ? 0.4f : 0.55f));
            }
        }
        if (settings.disruption) overlay.ring(float(stars.tidalRadius), glm::vec4(1.0f, 0.45f, 0.3f, 0.35f));
        {
            std::vector<glm::vec3> glowing;
            for (const auto& d : stars.debris) {
                if (!d.alive) continue;
                const float r = float(glm::length(d.p));
                const float heat = glm::clamp(6.0f / r, 0.25f, 3.0f); // hotter as it falls in
                glowing.push_back(glm::vec3(d.p));
                glowing.push_back(0.35f * heat * d.colour);
            }
            overlay.points(glowing, float(predictedShadowAngle(shown.distance)), 3.5f * float(pixelsW) / float(windowW));
        }
    }

    void present() {
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(0, 0, pixelsW, pixelsH);
        tracer.show(pixelsW, settings.exposure, settings.glow, settings.flareOn ? settings.flare : 0.0f);
    }

    // --measure: which rays fall into the hole, and how wide is that region?
    int measureShadow() {
        View v = view(0.0);
        v.style = 2;
        tracer.traceSamples(v, settings.imageW, settings.imageH, 1);
        int W = 0, H = 0;
        const std::vector<float> mask = tracer.readAverage(W, H);
        auto fell = [&](int x, int y) { return mask[(size_t(y) * W + x) * 4] > 0.5f; };
        double inside = 0.0;
        std::vector<unsigned char> grey(size_t(W) * H);
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
                grey[size_t(y) * W + x] = fell(x, y) ? 255 : 0;
                inside += fell(x, y);
            }
        if (!capture::writePng("measure-mask.png", "gray", W, H, grey)) return 1;
        // Walk out from the centre in 16 directions to the last dark pixel; the median
        // of the 16 edges ignores stray pixels. A shadow of angular radius a is a circle
        // of radius tan(a) on the image plane.
        std::vector<double> edge;
        for (int k = 0; k < 16; ++k) {
            const double direction = k * M_PI / 8.0;
            double last = 0.0;
            for (double step = 0.0; step < std::min(W, H) / 2.0; step += 0.25) {
                const int x = int(W / 2.0 + step * std::cos(direction));
                const int y = int(H / 2.0 + step * std::sin(direction));
                if (fell(x, y)) last = step;
            }
            edge.push_back(last);
        }
        std::sort(edge.begin(), edge.end());
        const double edgePixels = 0.5 * (edge[7] + edge[8]);
        const double t = OrbitCamera::tanHalfFov;
        const double measured = std::atan(edgePixels * 2.0 * t / H);
        const double predicted = predictedShadowAngle(camera.distance);
        const double pixelArea = (2.0 * t * v.aspect / W) * (2.0 * t / H);
        const double fill = inside * pixelArea / (M_PI * std::pow(std::tan(measured), 2.0));
        std::printf("[measure] camera at %.2f r_s\n", camera.distance);
        std::printf("[measure] shadow edge in the render:   %.2f degrees\n", glm::degrees(measured));
        std::printf("[measure] Schwarzschild's prediction:  %.2f degrees\n", glm::degrees(predicted));
        std::printf("[measure] difference:                  %.2f %%\n", 100.0 * (measured - predicted) / predicted);
        std::printf("[measure] mask area / fitted-circle area: %.2f %%\n", 100.0 * fill);
        return 0;
    }

    // --bench N: trace the full image N times.
    int benchmark() {
        const View v = view(0.0);
        double total = 0.0;
        for (int i = 0; i < settings.benchmarkRuns && !glfwWindowShouldClose(window); ++i) {
            const double start = glfwGetTime();
            tracer.traceSamples(v, settings.imageW, settings.imageH, 1);
            tracer.buildGlow(settings.imageW, settings.imageH);
            glFinish();
            const double ms = 1000.0 * (glfwGetTime() - start);
            total += ms;
            std::printf("[bench] %dx%d image traced in %.1f ms\n", settings.imageW, settings.imageH, ms);
            present();
            glfwSwapBuffers(window);
            glfwPollEvents();
        }
        std::printf("[bench] average %.1f ms\n", total / settings.benchmarkRuns);
        return 0;
    }

    int run() {
        capture::Video video, liveVideo;
        if (!settings.videoPath.empty() && !video.start(settings.videoPath, pixelsW, pixelsH)) return 1;
        const bool recording = video.active();
        inputLocked = recording;
        std::printf("[controls] drag or arrows: rotate | scroll, W/S or +/-: zoom | SPACE: freeze time\n"
                    "           buttons (lower left) or keys: 1/2/3 learning stage | E curved space | A gravity\n"
                    "           G suns bend light | H sky grid\n"
                    "           O flare | K prediction | N stars pull | F tides tear stars | R new suns\n"
                    "           C/T ghost, trails | D disk\n"
                    "           L look | U hide buttons | P still | V video\n");

        // Detail levels: a quick preview while moving, then half and full detail once still.
        const float detail[3] = {settings.previewScale, std::max(settings.previewScale, 0.5f), 1.0f};
        OrbitCamera shown, traced;   // cameras of the image on show and the one being traced
        bool anythingShown = false;
        int shownLevel = -1, tracedLevel = -1;
        double time = 0.0, last = glfwGetTime(), nextLiveFrame = 0.0;
        double reportFrom = last;
        int frame = 0, framesSinceReport = 0, imagesSinceReport = 0, previewW = 0, previewH = 0;

        while (!glfwWindowShouldClose(window)) {
            const double now = glfwGetTime();
            const double dt = now - last;
            last = now;

            if (settings.orbitDegPerSec != 0.0f && !paused)
                camera.turn(glm::radians(settings.orbitDegPerSec) * float(recording ? 1.0 / 30.0 : dt), 0.0f);

            // follow the window: the image keeps its pixels instead of stretching
            int w = 0, h = 0;
            glfwGetWindowSize(window, &w, &h);
            glfwGetFramebufferSize(window, &pixelsW, &pixelsH);
            if (!recording && w > 0 && h > 0 && (w != windowW || h != windowH)) {
                windowW = w; windowH = h;
                if (!settings.imageSizeFixed) { settings.imageW = pixelsW; settings.imageH = pixelsH; }
                anythingShown = false;
                shownLevel = -1;
            }
            if (toggleVideo) {
                toggleVideo = false;
                if (liveVideo.active()) {
                    liveVideo.stop();
                    glfwSetWindowTitle(window, physical::windowTitle("3D view").c_str());
                } else if (liveVideo.start(capture::timestampedPath(settings.captureDir + "/footage", ".mp4"), pixelsW, pixelsH)) {
                    nextLiveFrame = now;
                    glfwSetWindowTitle(window, physical::windowTitle("REC - V to stop").c_str());
                }
            }

            // held keys: W/S or +/- zoom, arrows rotate (over the poles too)
            if (!inputLocked) {
                auto held = [&](int key) { return glfwGetKey(window, key) == GLFW_PRESS; };
                const float zoom = (held(GLFW_KEY_S) || held(GLFW_KEY_MINUS) || held(GLFW_KEY_KP_SUBTRACT) ? 1.0f : 0.0f)
                                 - (held(GLFW_KEY_W) || held(GLFW_KEY_EQUAL) || held(GLFW_KEY_KP_ADD) ? 1.0f : 0.0f);
                const float across = (held(GLFW_KEY_RIGHT) ? 1.0f : 0.0f) - (held(GLFW_KEY_LEFT) ? 1.0f : 0.0f);
                const float down = (held(GLFW_KEY_DOWN) ? 1.0f : 0.0f) - (held(GLFW_KEY_UP) ? 1.0f : 0.0f);
                if (zoom != 0.0f || across != 0.0f || down != 0.0f) {
                    const float k = float(std::min(dt, 0.1));
                    camera.zoom(std::exp(1.2f * zoom * k));
                    camera.turn(glm::radians(70.0f) * across * k, glm::radians(60.0f) * down * k);
                    lastInput = now;
                }
            }

            // time: the gas turns and the suns move; SPACE freezes it for the sharpest image
            const bool flowing = settings.spin != 0.0f && !paused && !recording;
            const double step = recording ? settings.spin / 30.0 : (flowing ? std::min(dt, 0.1) * settings.spin : 0.0);
            time = recording ? settings.spin * frame / 30.0 : time + step;
            syncStarSettings();
            if (restartStars) { stars.restart(time); restartStars = false; }
            stars.advance(step, time);
            if (settings.showSuns && step > 0.0) stars.extendTrails(time);
            const View current = view(time);

            bool idle = false;
            if (recording) {
                tracer.traceSamples(current, settings.imageW, settings.imageH, settings.samplesVideo);
                tracer.buildGlow(settings.imageW, settings.imageH);
                shown = camera;
                anythingShown = true;
                shownLevel = 2;
            } else {
                const bool moving = dragging || now - lastInput < 0.3 || flowing ||
                                    (settings.orbitDegPerSec != 0.0f && !paused);
                const bool changed = !anythingShown || camera != shown || flowing || lookChanged;
                if (lookChanged) { anythingShown = false; shownLevel = -1; lookChanged = false; }
                tracer.collectTimers();
                if (!tracer.busy()) {
                    if (changed || (!moving && shownLevel < 2)) {
                        tracedLevel = changed ? (moving ? 0 : 1) : shownLevel + 1;
                        float scale = detail[tracedLevel];
                        const double cost = tracer.rayCost(true);
                        if (tracedLevel == 0 && cost > 0.0) // size the preview for about 10 ms of GPU work
                            scale = glm::clamp(float(std::sqrt(10.0e6 / cost / (double(settings.imageW) * settings.imageH))), 0.15f, 0.8f);
                        tracer.begin(current, std::max(8, int(settings.imageW * scale)), std::max(6, int(settings.imageH * scale)),
                                     settings.imageH, glm::vec2(0.5f), tracedLevel == 0 ? 2.0f : 1.0f);
                        if (tracedLevel == 0) { previewW = tracer.width(); previewH = tracer.height(); }
                        traced = camera;
                    } else if (!moving && shownLevel == 2 && tracer.samples() < settings.samplesLive) {
                        tracedLevel = 3; // one more sample per pixel
                        tracer.begin(current, settings.imageW, settings.imageH, settings.imageH,
                                     Tracer::subpixel(tracer.samples()), 1.0f);
                        traced = camera;
                    }
                }
                // a preview is traced whole each frame; finer images get about 6 ms of GPU per frame
                const int rows = tracedLevel == 0 ? 0 : tracer.rowsWithin(6.0);
                if (tracer.busy() && tracer.proceed(rows)) {
                    if (tracedLevel < 2) tracer.restartAverage();
                    else {
                        if (tracedLevel == 2) tracer.restartAverage();
                        tracer.addToAverage();
                    }
                    tracer.buildGlow(settings.imageW, settings.imageH);
                    shown = traced;
                    anythingShown = true;
                    shownLevel = std::min(tracedLevel, 2);
                    ++imagesSinceReport;
                    if (settings.printTimes && tracedLevel == 2)
                        std::printf("[view] %dx%d image traced in %.1f ms (spread over frames)\n",
                                    settings.imageW, settings.imageH, 1000.0 * tracer.secondsSinceStart());
                    if (settings.printTimes && tracedLevel == 3 && tracer.samples() == settings.samplesLive)
                        std::printf("[view] edges smoothed: %d samples per pixel\n", settings.samplesLive);
                }
                idle = !tracer.busy() && !moving && !changed && shownLevel == 2 && tracer.samples() >= settings.samplesLive;
            }

            present();
            drawOverlays(anythingShown ? shown : camera, current.suns);
            toolbar.buttons[size_t(Switch::Stage)].label = stageLabel();
            toolbar.draw(windowW, windowH);
            video.add();
            if (!video.ok()) break;
            if (liveVideo.active() && now >= nextLiveFrame) { // what's on screen, 30 frames a second
                liveVideo.add();
                nextLiveFrame = std::max(nextLiveFrame + 1.0 / 30.0, now);
            }
            glfwSwapBuffers(window);
            if (idle) glfwWaitEventsTimeout(0.1); // nothing to do until the mouse or a key
            else glfwPollEvents();

            ++frame;
            ++framesSinceReport;
            if (settings.printTimes && glfwGetTime() - reportFrom >= 1.0) {
                const double span = glfwGetTime() - reportFrom;
                std::printf("[view] %.1f ms per frame, %.1f new images per second", 1000.0 * span / framesSinceReport,
                            imagesSinceReport / span);
                if (previewW) std::printf(", moving preview %dx%d", previewW, previewH);
                std::printf("\n");
                reportFrom = glfwGetTime();
                framesSinceReport = imagesSinceReport = 0;
            }
            if (settings.frameLimit > 0 && frame >= settings.frameLimit) break;
        }
        video.stop();
        liveVideo.stop();
        return video.ok() && liveVideo.ok() ? 0 : 1;
    }
};

} // namespace

int main(int argc, char** argv) {
    App app;
    app.settings = readSettings(argc, argv);
    app.paused = app.settings.startPaused;
    app.openWindow();
    app.camera.place(app.settings.camDistance, app.settings.camAzimuthDeg, app.settings.camPolarDeg);
    app.tracer.create();
    app.overlay.create();
    app.toolbar.create();
    app.addSwitches();
    app.syncStarSettings();
    if (app.settings.mutualGravity) app.stars.restart(0.0);
    int result = 0;
    if (app.settings.measureShadow) result = app.measureShadow();
    else if (app.settings.benchmarkRuns > 0) result = app.benchmark();
    else result = app.run();
    glfwDestroyWindow(app.window);
    glfwTerminate();
    return result;
}
