// Runs the ray tracer on the GPU and turns its results into the picture.
//
// An image can be traced a few rows per frame (so the window stays responsive),
// averaged over several sub-pixel samples (smooth edges) and given a soft glow.
// The window keeps showing the last finished image until the next one is done.
#pragma once
#include "gl_tools.hpp"
#include "orbit_camera.hpp"
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <cmath>
#include <utility>
#include <vector>

struct Sun {
    glm::vec3 centre;
    float radius;
    glm::vec3 colour;
    float mass = 0.0f;  // fraction of the hole's mass; 0 = does not bend light
    float stretch = 1.0f;         // tidal stretching: this many times longer along axis, thinner across
    glm::vec3 axis{1.0f, 0.0f, 0.0f};
};

// Everything one traced image depends on.
struct View {
    OrbitCamera camera;
    float aspect = 4.0f / 3.0f;   // of the window
    int   style = 1;              // 0 grid diagnostic, 1 standard, 2 shadow mask
    bool  angularGrid = true;
    bool  disk = true;
    bool  predictionRing = false;
    bool  sunLensing = true;      // the suns' gravity bends light too
    int   stage = 2;              // learning stages: 0 straight light, 1 bent light and a plain disk, 2 everything
    float skyGain = 1.0f, diskGain = 1.0f, spinTime = 0.0f;
    std::vector<Sun> suns;
};

class Tracer {
public:
    static constexpr float diskInner = 3.0f, diskOuter = 10.0f;   // r_s
    static constexpr int skyUnit = 5, gasUnit = 6;                // texture units kept for the bakes

    void create() {
        screen.create();
        traceProgram = gl::program("shaders/screen.vert", "shaders/trace.frag");
        displayProgram = gl::program("shaders/screen.vert", "shaders/display.frag");
        shrinkProgram = gl::program("shaders/screen.vert", "shaders/glow.frag", "#define SHRINK 1");
        blurProgram = gl::program("shaders/screen.vert", "shaders/glow.frag");
        copyProgram = gl::program("shaders/screen.vert", "shaders/copy.frag");
        sunlightProgram = gl::program("shaders/screen.vert", "shaders/glow.frag", "#define SUNLIGHT 1");
        flareProgram = gl::program("shaders/screen.vert", "shaders/flare.frag");
        glGenQueries(4, timers);
        bakeSky(2048);
        bakeGas(1024, 256);
        glUseProgram(traceProgram);
        glUniform1i(gl::at(traceProgram, "uSky"), skyUnit);
        glUniform1i(gl::at(traceProgram, "uGas"), gasUnit);
        glUniform1f(gl::at(traceProgram, "uSkyTexelAngle"), skyTexelAngle);
        for (gl::Target* t : {&drawing, &finished, &mean, &glow[0], &glow[1], &glow[2], &glow[3], &sunlight, &flare})
            t->resize(4, 4);
    }

    // Starts tracing a w x h image. fullHeight is the height of the full-detail
    // image, which fixes the star size whatever this image's resolution.
    void begin(const View& view, int w, int h, int fullHeight, glm::vec2 subpixel, float stepScale) {
        drawing.resize(w, h);
        const OrbitCamera::Axes axes = view.camera.axes();
        const float pixel = 2.0f * OrbitCamera::tanHalfFov;
        glUseProgram(traceProgram);
        glUniform2i(gl::at(traceProgram, "uImageSize"), w, h);
        glUniform3fv(gl::at(traceProgram, "uEye"), 1, glm::value_ptr(view.camera.position()));
        glUniform3fv(gl::at(traceProgram, "uRight"), 1, glm::value_ptr(axes.right));
        glUniform3fv(gl::at(traceProgram, "uUp"), 1, glm::value_ptr(axes.up));
        glUniform3fv(gl::at(traceProgram, "uAhead"), 1, glm::value_ptr(axes.ahead));
        glUniform1f(gl::at(traceProgram, "uTanHalfFov"), OrbitCamera::tanHalfFov);
        glUniform1f(gl::at(traceProgram, "uAspect"), view.aspect);
        glUniform2f(gl::at(traceProgram, "uSubpixel"), subpixel.x, subpixel.y);
        glUniform1i(gl::at(traceProgram, "uStyle"), view.style);
        glUniform1i(gl::at(traceProgram, "uAngularGrid"), view.angularGrid);
        glUniform1f(gl::at(traceProgram, "uSpinTime"), view.spinTime);
        glUniform1f(gl::at(traceProgram, "uPixelAngle"), pixel / float(h));
        glUniform1f(gl::at(traceProgram, "uStarAngle"), pixel / float(fullHeight));
        glUniform1f(gl::at(traceProgram, "uStepScale"), stepScale);
        glUniform1f(gl::at(traceProgram, "uRingAngle"),
                    view.predictionRing ? float(predictedShadowAngle(view.camera.distance)) : 0.0f);
        glUniform1f(gl::at(traceProgram, "uSkyGain"), view.skyGain);
        glUniform1f(gl::at(traceProgram, "uDiskGain"), view.diskGain);
        glUniform2f(gl::at(traceProgram, "uDiskRadii"), view.disk ? diskInner : 0.0f, view.disk ? diskOuter : 0.0f);
        const int count = int(std::min<size_t>(view.suns.size(), 16));
        std::vector<glm::vec4> bodies(16, glm::vec4(0.0f));
        std::vector<glm::vec3> colours(16, glm::vec3(0.0f));
        std::vector<float> masses(16, 0.0f);
        std::vector<glm::vec4> stretches(16, glm::vec4(1, 0, 0, 1));
        for (int i = 0; i < count; ++i) {
            stretches[i] = glm::vec4(view.suns[i].axis, view.suns[i].stretch);
            bodies[i] = glm::vec4(view.suns[i].centre, view.suns[i].radius);
            colours[i] = view.suns[i].colour;
            masses[i] = view.suns[i].mass;
        }
        glUniform1i(gl::at(traceProgram, "uBodyCount"), count);
        glUniform4fv(gl::at(traceProgram, "uBodies"), 16, glm::value_ptr(bodies[0]));
        glUniform3fv(gl::at(traceProgram, "uBodyColours"), 16, glm::value_ptr(colours[0]));
        glUniform1fv(gl::at(traceProgram, "uBodyMasses"), 16, masses.data());
        glUniform4fv(gl::at(traceProgram, "uBodyStretch"), 16, glm::value_ptr(stretches[0]));
        glUniform1i(gl::at(traceProgram, "uSunLensing"), view.sunLensing);
        glUniform1i(gl::at(traceProgram, "uStage"), view.stage);
        aspect = view.aspect;
        coarse = stepScale > 1.0f;
        nextRow = 0;
        tracing = true;
        startedAt = glfwGetTime();
    }

    // Traces up to rowLimit more rows (0 = all that remain). True once the image is
    // finished and has become the image on show. Never waits for the GPU.
    bool proceed(int rowLimit) {
        if (!tracing) return false;
        GLint saved[4];
        glGetIntegerv(GL_VIEWPORT, saved);
        glDisable(GL_BLEND);
        drawing.bindForDrawing();
        glUseProgram(traceProgram);
        const int last = rowLimit > 0 ? std::min(drawing.h, nextRow + rowLimit) : drawing.h;
        const int timer = freeTimer();
        if (timer >= 0) {
            glBeginQuery(GL_TIME_ELAPSED, timers[timer]);
            timerRays[timer] = (last - nextRow) * drawing.w;
            timerCoarse[timer] = coarse;
        }
        gl::drawInBands(screen, drawing.w, nextRow, last, glm::clamp(40000 / drawing.w, 8, 64));
        if (timer >= 0) glEndQuery(GL_TIME_ELAPSED);
        nextRow = last;
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(saved[0], saved[1], saved[2], saved[3]);
        if (nextRow < drawing.h) return false;
        std::swap(drawing, finished);
        tracing = false;
        return true;
    }

    bool busy() const { return tracing; }
    int width() const { return tracing ? drawing.w : finished.w; }
    int height() const { return tracing ? drawing.h : finished.h; }
    double secondsSinceStart() const { return glfwGetTime() - startedAt; }

    // The running average of finished images (sub-pixel samples of one view).
    void restartAverage() { averaged = 0; }
    void addToAverage() {
        if (mean.w != finished.w || mean.h != finished.h) averaged = 0;
        mean.resize(finished.w, finished.h);
        GLint saved[4];
        glGetIntegerv(GL_VIEWPORT, saved);
        mean.bindForDrawing();
        glEnable(GL_BLEND);
        glBlendColor(0.0f, 0.0f, 0.0f, 1.0f / float(averaged + 1)); // the new sample's share
        glBlendFunc(GL_CONSTANT_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA);
        glUseProgram(copyProgram);
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, finished.texture);
        glUniform1i(gl::at(copyProgram, "uSource"), 0);
        screen.draw();
        glDisable(GL_BLEND);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(saved[0], saved[1], saved[2], saved[3]);
        ++averaged;
    }
    int samples() const { return averaged; }

    // Whole images of `count` samples per pixel (recording, measuring, benchmarking).
    void traceSamples(const View& view, int w, int h, int count) {
        restartAverage();
        for (int k = 0; k < count; ++k) {
            begin(view, w, h, h, subpixel(k), 1.0f);
            proceed(0);
            addToAverage();
        }
    }

    // Sample k's position in its pixel: the centre first, then Halton (2, 3) points.
    static glm::vec2 subpixel(int k) {
        if (k == 0) return glm::vec2(0.5f);
        auto halton = [](int i, int base) {
            float f = 1.0f, r = 0.0f;
            for (; i > 0; i /= base) { f /= base; r += f * float(i % base); }
            return r;
        };
        return glm::vec2(halton(k, 2), halton(k, 3));
    }

    // The soft glow: the image averaged down to 1/4 and 1/16 of the full-detail size
    // and blurred, so a small preview glows as wide on screen as the sharp image.
    void buildGlow(int fullW, int fullH) {
        GLint saved[4];
        glGetIntegerv(GL_VIEWPORT, saved);
        glDisable(GL_BLEND);
        glActiveTexture(GL_TEXTURE0);
        GLuint source = shownTexture();
        for (int level = 0; level < 2; ++level) {
            const int divide = level == 0 ? 4 : 16;
            const int w = std::max(1, fullW / divide), h = std::max(1, fullH / divide);
            gl::Target& a = glow[2 * level];
            gl::Target& b = glow[2 * level + 1];
            a.resize(w, h);
            b.resize(w, h);
            glUseProgram(shrinkProgram);
            glUniform1i(gl::at(shrinkProgram, "uSource"), 0);
            glUniform2f(gl::at(shrinkProgram, "uTargetSize"), float(w), float(h));
            a.bindForDrawing();
            glBindTexture(GL_TEXTURE_2D, source);
            screen.draw();
            glUseProgram(blurProgram);
            glUniform1i(gl::at(blurProgram, "uSource"), 0);
            glUniform2f(gl::at(blurProgram, "uTargetSize"), float(w), float(h));
            b.bindForDrawing();
            glBindTexture(GL_TEXTURE_2D, a.texture);
            glUniform2f(gl::at(blurProgram, "uStep"), 1.0f / float(w), 0.0f);
            screen.draw();
            a.bindForDrawing();
            glBindTexture(GL_TEXTURE_2D, b.texture);
            glUniform2f(gl::at(blurProgram, "uStep"), 0.0f, 1.0f / float(h));
            screen.draw();
            source = a.texture;
        }
        // the lens flare, from the suns' light alone
        sunlight.resize(std::max(1, fullW / 4), std::max(1, fullH / 4));
        flare.resize(std::max(1, fullW / 4), std::max(1, fullH / 4));
        glUseProgram(sunlightProgram);
        glUniform1i(gl::at(sunlightProgram, "uSource"), 0);
        glUniform2f(gl::at(sunlightProgram, "uTargetSize"), float(sunlight.w), float(sunlight.h));
        sunlight.bindForDrawing();
        glBindTexture(GL_TEXTURE_2D, shownTexture());
        screen.draw();
        glUseProgram(flareProgram);
        glUniform1i(gl::at(flareProgram, "uSunLight"), 0);
        glUniform1f(gl::at(flareProgram, "uAspect"), aspect);
        flare.bindForDrawing();
        glBindTexture(GL_TEXTURE_2D, sunlight.texture);
        screen.draw();
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(saved[0], saved[1], saved[2], saved[3]);
    }

    // Draws the image on show over the current framebuffer.
    void show(int screenWidth, float exposure, float glowStrength, float flareStrength) {
        glDisable(GL_BLEND);
        glUseProgram(displayProgram);
        const GLuint sources[4] = {shownTexture(), glow[0].texture, glow[2].texture, flare.texture};
        const char* names[4] = {"uImage", "uGlowNear", "uGlowFar", "uFlare"};
        for (int unit = 0; unit < 4; ++unit) {
            glActiveTexture(GL_TEXTURE0 + unit);
            glBindTexture(GL_TEXTURE_2D, sources[unit]);
            glUniform1i(gl::at(displayProgram, names[unit]), unit);
        }
        glActiveTexture(GL_TEXTURE0);
        glUniform1f(gl::at(displayProgram, "uScreenWidth"), float(screenWidth));
        glUniform1f(gl::at(displayProgram, "uExposure"), exposure);
        glUniform1f(gl::at(displayProgram, "uGlow"), glowStrength);
        glUniform1f(gl::at(displayProgram, "uFlareStrength"), flareStrength);
        screen.draw();
    }

    // The averaged image as floats (RGBA), for measuring.
    std::vector<float> readAverage(int& w, int& h) const {
        w = mean.w; h = mean.h;
        std::vector<float> rgba(size_t(w) * size_t(h) * 4);
        glBindTexture(GL_TEXTURE_2D, mean.texture);
        glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_FLOAT, rgba.data());
        return rgba;
    }

    // GPU timers finish a frame or two after their work; collect the ones that have.
    void collectTimers() {
        for (int i = 0; i < 4; ++i) {
            if (!timerBusy[i]) continue;
            GLint ready = 0;
            glGetQueryObjectiv(timers[i], GL_QUERY_RESULT_AVAILABLE, &ready);
            if (!ready) continue;
            GLuint64 ns = 0;
            glGetQueryObjectui64v(timers[i], GL_QUERY_RESULT, &ns);
            if (timerRays[i] > 0) {
                double& average = timerCoarse[i] ? nsPerCoarseRay : nsPerRay;
                const double sample = double(ns) / timerRays[i];
                average = average <= 0.0 ? sample : 0.7 * average + 0.3 * sample;
            }
            timerBusy[i] = false;
        }
    }
    // Estimated GPU time of one ray (coarse: the moving preview's larger steps).
    double rayCost(bool coarseSteps) const {
        if (coarseSteps) return nsPerCoarseRay > 0.0 ? nsPerCoarseRay : 0.5 * nsPerRay;
        return nsPerRay;
    }
    // Rows of the image being traced that fit in `ms` of GPU time.
    int rowsWithin(double ms) const {
        if (nsPerRay <= 0.0 || drawing.w <= 0) return 8;
        return glm::clamp(int(ms * 1e6 / (nsPerRay * drawing.w)), 1, 4000);
    }

private:
    GLuint shownTexture() const { return averaged > 0 ? mean.texture : finished.texture; }

    int freeTimer() {
        for (int i = 0; i < 4; ++i)
            if (!timerBusy[i]) { timerBusy[i] = true; return i; }
        return -1;
    }

    // The starry sky painted once into a cube map, so a ray's sky colour is one lookup.
    void bakeSky(int size) {
        const GLuint program = gl::program("shaders/screen.vert", "shaders/trace.frag", "#define BAKE_SKY 1");
        glGenTextures(1, &skyTexture);
        glActiveTexture(GL_TEXTURE0 + skyUnit);
        glBindTexture(GL_TEXTURE_CUBE_MAP, skyTexture);
        for (int face = 0; face < 6; ++face)
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + face, 0, GL_R11F_G11F_B10F, size, size, 0,
                         GL_RGB, GL_FLOAT, nullptr);
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        for (GLenum axis : {GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_R})
            glTexParameteri(GL_TEXTURE_CUBE_MAP, axis, GL_CLAMP_TO_EDGE);
        glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS);
        skyTexelAngle = 2.0f / float(size); // at the middle of a face
        GLuint framebuffer = 0;
        glGenFramebuffers(1, &framebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        glViewport(0, 0, size, size);
        glDisable(GL_BLEND);
        glUseProgram(program);
        glUniform2i(gl::at(program, "uImageSize"), size, size);
        glUniform1f(gl::at(program, "uStarAngle"), skyTexelAngle);
        glUniform1f(gl::at(program, "uPixelAngle"), skyTexelAngle);
        for (int face = 0; face < 6; ++face) {
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + face,
                                   skyTexture, 0);
            glUniform1i(gl::at(program, "uFace"), face);
            gl::drawInBands(screen, size, 0, size, 128);
        }
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glDeleteFramebuffers(1, &framebuffer);
        glGenerateMipmap(GL_TEXTURE_CUBE_MAP);
        glDeleteProgram(program);
        glActiveTexture(GL_TEXTURE0);
    }

    // The disk's gas pattern, painted once: angle across, log of the radius up.
    void bakeGas(int w, int h) {
        const GLuint program = gl::program("shaders/screen.vert", "shaders/trace.frag", "#define BAKE_GAS 1");
        glGenTextures(1, &gasTexture);
        glActiveTexture(GL_TEXTURE0 + gasUnit);
        glBindTexture(GL_TEXTURE_2D, gasTexture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R16F, w, h, 0, GL_RED, GL_FLOAT, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT); // round the disk
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        GLuint framebuffer = 0;
        glGenFramebuffers(1, &framebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, gasTexture, 0);
        glViewport(0, 0, w, h);
        glDisable(GL_BLEND);
        glUseProgram(program);
        glUniform2i(gl::at(program, "uImageSize"), w, h);
        glUniform1f(gl::at(program, "uLogSpan"), std::log(diskOuter / diskInner));
        gl::drawInBands(screen, w, 0, h, 128);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glDeleteFramebuffers(1, &framebuffer);
        glGenerateMipmap(GL_TEXTURE_2D);
        glDeleteProgram(program);
        glActiveTexture(GL_TEXTURE0);
    }

    gl::ScreenTriangle screen;
    GLuint traceProgram = 0, displayProgram = 0, shrinkProgram = 0, blurProgram = 0, copyProgram = 0;
    GLuint sunlightProgram = 0, flareProgram = 0;
    GLuint skyTexture = 0, gasTexture = 0;
    float skyTexelAngle = 0.0f;
    gl::Target drawing, finished, mean, glow[4], sunlight, flare;
    float aspect = 4.0f / 3.0f;
    int averaged = 0;
    int nextRow = 0;
    bool tracing = false, coarse = false;
    double startedAt = 0.0;
    GLuint timers[4] = {0, 0, 0, 0};
    int timerRays[4] = {0, 0, 0, 0};
    bool timerBusy[4] = {false, false, false, false};
    bool timerCoarse[4] = {false, false, false, false};
    double nsPerRay = 0.0, nsPerCoarseRay = 0.0;
};
