// Three suns around the hole. By default they pull on one another (N) and the hole
// can tear them apart (F): a sun is stretched by the hole's tides as it comes in,
// torn into debris inside the tidal radius, and destroyed if it hits another sun;
// the debris spirals into the hole. With both off, the suns follow scripted circles.
// An optional ghost copy (C) starts 1e-6 r_s away to show how sensitive the paths are.
//
// Units: r_s = c = 1, so the hole's GM is 1/2. The suns' masses (8%, 6% and 10% of
// the hole) are exaggerated on purpose so that their pull on one another shows.
// Disruption uses Paczynski-Wiita gravity, -GM/(r - r_s)^2, which puts the last
// stable circular orbit at 3 r_s, and a solar-star tidal radius; the stretching is
// a picture of the tide's strength, and the debris loses angular momentum by a
// made-up drag. None of this is relativistic stellar dynamics.
#pragma once
#include "physical_constants.hpp"
#include "tracer.hpp"
#include <glm/glm.hpp>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <random>
#include <vector>

class StarSystem {
public:
    // start: starting speed as a fraction of a circular orbit's. The red sun starts a
    // little slow, so the three soon disturb one another.
    struct Design { float orbit, tiltDeg, phase; glm::vec3 colour; float size, start; const char* name; };
    static constexpr int count = 3;
    const Design design[count] = {
        {13.0f,   6.0f, 0.0f, glm::vec3(1.00f, 0.80f, 0.55f) * 4.0f, 0.75f, 1.00f, "yellow"},
        {18.0f, -11.0f, 2.3f, glm::vec3(0.65f, 0.78f, 1.00f) * 5.0f, 0.55f, 1.00f, "blue-white"},
        {27.0f,  16.0f, 4.4f, glm::vec3(1.00f, 0.45f, 0.25f) * 3.0f, 1.00f, 0.85f, "red"},
    };
    const double mass[count] = {0.08, 0.06, 0.10};
    const double tidalRadius = physical::solarTidalRadiusRs(); // about 8.9 r_s
    static constexpr double timeUnitsPerSecond = 104.0;  // the inner sun orbits in about 4 s
    static constexpr size_t trailLength = 700;

    struct Particle { glm::dvec3 p, v; bool alive = true; };
    struct Debris { glm::dvec3 p, v; glm::vec3 colour; bool alive = true; };

    bool mutual = true;       // N
    bool ghost = false;       // C
    bool disruption = true;   // F
    bool demo = false;        // --tde-demo
    std::vector<Debris> debris;
    std::vector<glm::vec3> trail[2 * count]; // the suns' paths, then their ghosts'

    // Where a scripted sun is at time t (in film seconds).
    glm::vec3 scripted(int i, double t) const {
        const Design& d = design[i];
        const double angle = d.phase + 0.8 * std::pow(d.orbit / 10.0, -1.5) * t;
        const double tilt = glm::radians(double(d.tiltDeg));
        return glm::vec3(float(d.orbit * std::cos(angle)), float(d.orbit * std::sin(angle) * std::sin(tilt)),
                         float(d.orbit * std::sin(angle) * std::cos(tilt)));
    }

    // Starts the interacting suns from where the scripted ones are at time t.
    void restart(double t) {
        for (int i = 0; i < count; ++i) {
            const Design& d = design[i];
            const double r = d.orbit;
            const double angle = d.phase + 0.8 * std::pow(r / 10.0, -1.5) * t;
            const double tilt = glm::radians(double(d.tiltDeg));
            const double circular = disruption ? std::sqrt(0.5 * r) / (r - 1.0) : std::sqrt(0.5 / r);
            const double speed = d.start * circular;
            const glm::dvec3 along(std::cos(angle), std::sin(angle) * std::sin(tilt), std::sin(angle) * std::cos(tilt));
            const glm::dvec3 ahead(-std::sin(angle), std::cos(angle) * std::sin(tilt), std::cos(angle) * std::cos(tilt));
            real[i] = copy[i] = {r * along, speed * ahead, true};
        }
        copy[0].p.x += physical::ghostOffsetRs;
        if (demo) { // falls from 30 r_s; angular momentum and energy fix the 6 r_s closest approach
            const double far = 30.0, near = 6.0;
            const double v = std::sqrt((0.5 / (near - 1.0) - 0.5 / (far - 1.0)) / (far * far / (2.0 * near * near) - 0.5));
            real[0] = {glm::dvec3(far, 0.0, 0.0), glm::dvec3(0.0, 0.0, v), true};
            real[1].alive = real[2].alive = false;
            for (int i = 0; i < count; ++i) copy[i] = real[i];
        }
        clock = 0.0;
        debris.clear();
        feeding = 0.0;
        slowUntil = -1.0;
        slowness = 1.0;
        emptySince = -1.0;
        for (auto& t : trail) t.clear();
    }

    // Moves the interacting suns and debris on by `seconds` of film time; t is the
    // film time now. Once every sun is gone, new ones arrive a few seconds later.
    void advance(double seconds, double t) {
        if (!mutual || seconds <= 0.0) return;
        filmTime = t;
        const bool anyLeft = real[0].alive || real[1].alive || real[2].alive;
        if (anyLeft) emptySince = -1.0;
        else if (emptySince < 0.0) emptySince = t;
        else if (t - emptySince > 8.0) {
            std::printf("[stars] %.1f s: new suns arrive\n", t);
            restart(t);
        }
        // ease into and out of 10x slow motion while a star comes apart
        slowness += ((clock < slowUntil ? 0.1 : 1.0) - slowness) * std::min(1.0, 6.0 * seconds);
        const double start = clock, until = clock + seconds * timeUnitsPerSecond * slowness;
        while (clock < until) {
            double nearest = 10.0;
            for (const Particle& s : real) if (s.alive) nearest = std::min(nearest, glm::length(s.p));
            const double h = std::min({0.5, disruption ? 0.02 * std::pow(nearest, 1.5) : 0.5, until - clock});
            leapfrog(real, h, true);
            leapfrog(copy, h, false);
            collide(real, true);
            collide(copy, false);
            clock += h;
        }
        const int swallowed = moveDebris(clock - start);
        feeding = feeding * std::exp(-seconds / 1.5) + swallowed / 60.0;
    }

    // How brightly the disk glows while it swallows debris.
    float diskGain() const { return float(1.0 + std::min(feeding, 3.0)); }

    // The suns as the tracer sees them at time t.
    std::vector<Sun> suns(double t) const {
        std::vector<Sun> out;
        for (int i = 0; i < count; ++i) {
            if (mutual && !real[i].alive) continue;
            Sun sun{position(i, t), design[i].size, design[i].colour, float(mass[i])};
            if (mutual && disruption) { // stretched along the line to the hole as the tide grows
                const float r = glm::length(sun.centre);
                const float tide = std::min(float(tidalRadius) / r, 1.2f);
                sun.stretch = 1.0f + 0.6f * tide * tide * tide * tide;
                sun.axis = sun.centre / r;
            }
            out.push_back(sun);
        }
        if (mutual && ghost)
            for (int i = 0; i < count; ++i)
                if (copy[i].alive)
                    out.push_back({glm::vec3(copy[i].p), 0.6f * design[i].size, // a marker, so it bends no light
                                   design[i].colour * 0.35f + glm::vec3(0.3f, 0.5f, 1.0f), 0.0f});
        return out;
    }

    void extendTrails(double t) {
        for (int i = 0; i < count; ++i) {
            if (mutual && !real[i].alive) continue;
            trail[i].push_back(position(i, t));
            if (mutual && copy[i].alive) trail[count + i].push_back(glm::vec3(copy[i].p));
        }
        for (auto& path : trail)
            if (path.size() > trailLength) path.erase(path.begin(), path.end() - trailLength);
    }

private:
    glm::vec3 position(int i, double t) const { return mutual ? glm::vec3(real[i].p) : scripted(i, t); }

    glm::dvec3 holePull(const glm::dvec3& p) const {
        const double r = glm::length(p);
        return disruption ? -0.5 * p / (r * (r - 1.0) * (r - 1.0)) : -0.5 * p / (r * r * r);
    }

    glm::dvec3 pullOn(const Particle* group, int i) const {
        glm::dvec3 a = holePull(group[i].p);
        for (int j = 0; j < count; ++j) {
            if (j == i || !group[j].alive) continue;
            const glm::dvec3 d = group[j].p - group[i].p;
            const double d2 = glm::dot(d, d) + 0.25; // softened, so close passes stay finite
            a += 0.5 * mass[j] * d / (d2 * std::sqrt(d2));
        }
        return a;
    }

    // Kick, drift, kick.
    void leapfrog(Particle* group, double h, bool canDisrupt) {
        for (int i = 0; i < count; ++i) if (group[i].alive) group[i].v += 0.5 * h * pullOn(group, i);
        for (int i = 0; i < count; ++i) if (group[i].alive) group[i].p += h * group[i].v;
        for (int i = 0; i < count; ++i) {
            if (!group[i].alive) continue;
            group[i].v += 0.5 * h * pullOn(group, i);
            const double r = glm::length(group[i].p);
            if (r < 1.5) { // into the hole
                group[i].alive = false;
                if (canDisrupt) std::printf("[stars] %.1f s: the %s sun fell into the hole\n", filmTime, design[i].name);
            } else if (disruption && canDisrupt && r < tidalRadius) {
                group[i].alive = false;
                std::printf("[stars] %.1f s: the hole's tides tore the %s sun apart\n", filmTime, design[i].name);
                tearApart(i, 0.0);
            } else if (r > 60.0) { // a slingshot threw it out of the scene
                group[i].alive = false;
                if (canDisrupt) std::printf("[stars] %.1f s: the %s sun was flung out\n", filmTime, design[i].name);
            }
        }
    }

    // Two suns that touch destroy each other; the pieces fly apart.
    void collide(Particle* group, bool isReal) {
        for (int i = 0; i < count; ++i)
            for (int j = i + 1; j < count; ++j) {
                if (!group[i].alive || !group[j].alive) continue;
                if (glm::length(group[i].p - group[j].p) > double(design[i].size + design[j].size)) continue;
                group[i].alive = group[j].alive = false;
                if (!isReal) continue;
                std::printf("[stars] %.1f s: the %s and %s suns collided\n", filmTime, design[i].name, design[j].name);
                tearApart(i, 0.06);
                tearApart(j, 0.06);
            }
    }

    // A sun becomes a cloud of debris moving with it; burst adds a random scatter.
    void tearApart(int i, double burst) {
        std::uniform_real_distribution<double> unit(-1.0, 1.0);
        const glm::vec3 c = design[i].colour;
        const glm::vec3 colour = c / std::max(c.r, std::max(c.g, c.b));
        slowUntil = clock + 90.0;
        for (int k = 0; k < 1500; ++k) {
            glm::dvec3 offset;
            do offset = glm::dvec3(unit(random), unit(random), unit(random)); while (glm::dot(offset, offset) > 1.0);
            debris.push_back({real[i].p + double(design[i].size) * offset,
                              real[i].v * (1.0 + 0.01 * unit(random)) + burst * offset, colour});
        }
    }

    // Each piece at its own pace: smaller steps near the hole. Returns how many fell in.
    int moveDebris(double span) {
        int swallowed = 0;
        for (Debris& d : debris) {
            for (double t = 0.0; t < span && d.alive;) {
                const double dt = std::min({0.5, 0.02 * std::pow(glm::length(d.p), 1.5), span - t});
                d.v += 0.5 * dt * holePull(d.p);
                d.p += dt * d.v;
                d.v += 0.5 * dt * holePull(d.p);
                const glm::dvec3 out = glm::normalize(d.p);
                const glm::dvec3 radial = glm::dot(d.v, out) * out;
                d.v = radial + (d.v - radial) * (1.0 - 0.0015 * dt); // slowly losing angular momentum
                t += dt;
                const double r = glm::length(d.p);
                if (r < 1.05) { d.alive = false; ++swallowed; }
                else if (r > 150.0) d.alive = false;
            }
        }
        return swallowed;
    }

    Particle real[count], copy[count];
    double clock = 0.0, feeding = 0.0, slowUntil = -1.0, slowness = 1.0;
    double filmTime = 0.0, emptySince = -1.0;
    std::mt19937 random{7};
};
