// The viewer sits on a sphere around the hole and always looks at its centre.
// Lengths are in Schwarzschild radii; the disk lies in the x-z plane.
#pragma once
#include <glm/glm.hpp>
#include <algorithm>
#include <cmath>

struct OrbitCamera {
    static constexpr float closest = 2.05f;        // just outside the photon sphere's shadow
    static constexpr float farthest = 78.7f;       // about 1e12 m
    static constexpr float tanHalfFov = 0.57735027f; // 60 degree vertical field of view
    static constexpr float edge = 0.01f;           // keeps the view off the poles

    float distance = 22.0f;
    float azimuth = 0.0f;  // around the disk's axis
    float polar = 1.5708f; // from the axis: pi/2 is the disk plane

    void place(float r, float azimuthDeg, float polarDeg) {
        distance = glm::clamp(r, closest, farthest);
        azimuth = glm::radians(azimuthDeg);
        polar = glm::clamp(glm::radians(polarDeg), edge, float(M_PI) - edge);
    }
    void turn(float dAzimuth, float dPolar) {
        azimuth += dAzimuth;
        polar = glm::clamp(polar + dPolar, edge, float(M_PI) - edge);
    }
    void zoom(float factor) { distance = glm::clamp(distance * factor, closest, farthest); }

    glm::vec3 position() const {
        return distance * glm::vec3(std::sin(polar) * std::cos(azimuth), std::cos(polar),
                                    std::sin(polar) * std::sin(azimuth));
    }

    // Unit vectors of the view: to the right, up the screen and straight ahead.
    struct Axes { glm::vec3 right, up, ahead; };
    Axes axes() const {
        const glm::vec3 ahead = -glm::normalize(position());
        const glm::vec3 right = glm::normalize(glm::cross(ahead, glm::vec3(0, 1, 0)));
        return {right, glm::cross(right, ahead), ahead};
    }

    bool operator==(const OrbitCamera& o) const {
        return distance == o.distance && azimuth == o.azimuth && polar == o.polar;
    }
    bool operator!=(const OrbitCamera& o) const { return !(*this == o); }
};

// Schwarzschild's prediction for a viewer at rest at radius r (in r_s): the shadow's
// edge lies at angle a from its centre, with sin a = (3 sqrt 3 / 2)(1 / r) sqrt(1 - 1 / r).
// (3 sqrt 3 / 2) r_s is the impact parameter of light grazing the photon sphere.
inline double predictedShadowAngle(double r) {
    const double s = 1.5 * std::sqrt(3.0) / r * std::sqrt(std::max(0.0, 1.0 - 1.0 / r));
    return std::asin(std::min(1.0, s));
}
