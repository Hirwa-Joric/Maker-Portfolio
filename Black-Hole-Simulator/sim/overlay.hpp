// Straight lines and glowing points drawn over the traced image: the curved-space
// sheet, the suns' trails, the tidal radius and debris. They are projected without
// bending, so they only approximate what light shows.
#pragma once
#include "gl_tools.hpp"
#include "tracer.hpp"
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <cmath>
#include <vector>

class Overlay {
public:
    void create() {
        lineProgram = gl::program("shaders/overlay.vert", "shaders/overlay.frag");
        pointProgram = gl::program("shaders/overlay.vert", "shaders/overlay.frag", "#define POINTS 1");
        glGenVertexArrays(1, &vao);
        glGenBuffers(1, &buffer);
    }

    void setView(const glm::mat4& viewProjection, const glm::vec3& eyePosition) {
        transform = viewProjection;
        eye = eyePosition;
    }

    // mode: GL_LINES for separate segments, GL_LINE_STRIP for one path.
    // Lines fade out between fadeFrom and fadeTo r_s from the hole's axis.
    void lines(const std::vector<glm::vec3>& points, GLenum mode, const glm::vec4& tint,
               float fadeFrom = 1e8f, float fadeTo = 2e8f) {
        if (points.size() < 2) return;
        glUseProgram(lineProgram);
        glUniformMatrix4fv(gl::at(lineProgram, "uViewProjection"), 1, GL_FALSE, glm::value_ptr(transform));
        glUniform4fv(gl::at(lineProgram, "uTint"), 1, glm::value_ptr(tint));
        glUniform2f(gl::at(lineProgram, "uFade"), fadeFrom, fadeTo);
        upload(points.data(), points.size() * sizeof(glm::vec3), false);
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glDrawArrays(mode, 0, GLsizei(points.size()));
        glDisable(GL_BLEND);
    }

    // The rubber-sheet picture of curved space: a grid below the disk that sinks into
    // a well under the hole and under each sun, deeper for more mass. The depth
    // follows the Newtonian potential, softened at each body's size; it is a picture
    // of gravity's strength, while the bending of light comes from the tracer.
    static float sheetHeight(float x, float z, const std::vector<Sun>& suns) {
        const float base = -2.5f, scale = 8.0f;
        float depth = scale / std::sqrt(x * x + z * z + 1.0f);
        for (const Sun& sun : suns) {
            const float dx = x - sun.centre.x, dz = z - sun.centre.z;
            depth += scale * sun.mass / std::sqrt(dx * dx + dz * dz + sun.radius * sun.radius);
        }
        return base - depth;
    }

    void curvedSheet(const std::vector<Sun>& suns, const glm::vec4& tint) {
        const int cells = 60;
        const float spacing = 1.0f;
        std::vector<glm::vec3> grid((cells + 1) * (cells + 1));
        for (int i = 0; i <= cells; ++i)
            for (int j = 0; j <= cells; ++j) {
                const float x = (float(i) - cells / 2) * spacing, z = (float(j) - cells / 2) * spacing;
                grid[i * (cells + 1) + j] = glm::vec3(x, sheetHeight(x, z, suns), z);
            }
        std::vector<glm::vec3> segments;
        segments.reserve(4 * cells * (cells + 1));
        for (int i = 0; i <= cells; ++i)
            for (int j = 0; j <= cells; ++j) {
                const glm::vec3& p = grid[i * (cells + 1) + j];
                if (i < cells) { segments.push_back(p); segments.push_back(grid[(i + 1) * (cells + 1) + j]); }
                if (j < cells) { segments.push_back(p); segments.push_back(grid[i * (cells + 1) + j + 1]); }
            }
        lines(segments, GL_LINES, tint, 16.0f, 30.0f);
    }

    // Gravity made visible: arrows on the sheet showing the Newtonian pull of the hole
    // and the suns at each point (longer and warmer = stronger, on a log scale), and a
    // white arrow on each sun for the net pull it feels.
    void gravityArrows(const std::vector<Sun>& suns) {
        auto pull = [&](const glm::vec3& p, const Sun* except) {
            glm::vec3 g = -0.5f * p / std::pow(std::max(glm::length(p), 1.0f), 3.0f); // GM = 1/2
            for (const Sun& sun : suns) {
                if (&sun == except || sun.mass <= 0.0f) continue;
                const glm::vec3 d = sun.centre - p;
                const float r = std::max(glm::length(d), sun.radius);
                g += 0.5f * sun.mass * d / (r * r * r);
            }
            return g;
        };
        // strength mapped to 0..1 between the hole's pull at 30 r_s and at 3 r_s
        auto level = [](float g) { return glm::clamp(std::log(g / 5.6e-4f) / std::log(100.0f), 0.08f, 1.0f); };
        constexpr int bins = 5;
        std::vector<glm::vec3> byStrength[bins];
        const float spacing = 3.0f;
        for (int i = -9; i <= 9; ++i)
            for (int j = -9; j <= 9; ++j) {
                const float x = i * spacing, z = j * spacing;
                const float r = std::sqrt(x * x + z * z);
                if (r < 3.5f) continue; // the steepest part of the hole's well
                const glm::vec3 g = pull(glm::vec3(x, 0.0f, z), nullptr);
                const glm::vec2 flat(g.x, g.z);
                if (glm::length(flat) <= 0.0f) continue;
                const float t = level(glm::length(flat));
                const glm::vec2 d = glm::normalize(flat), side(-d.y, d.x);
                const float length = std::min(2.4f * t, 0.7f * (r - 2.0f)); // tips stay out of the well
                auto onSheet = [&](glm::vec2 q) { return glm::vec3(q.x, sheetHeight(q.x, q.y, suns) + 0.05f, q.y); };
                const glm::vec2 base(x, z), tip = base + length * d;
                auto& out = byStrength[std::min(bins - 1, int(t * bins))];
                out.insert(out.end(), {onSheet(base), onSheet(tip),
                                       onSheet(tip), onSheet(tip - 0.35f * length * d + 0.2f * length * side),
                                       onSheet(tip), onSheet(tip - 0.35f * length * d - 0.2f * length * side)});
            }
        for (int b = 0; b < bins; ++b) {
            const float t = (b + 0.5f) / bins;
            lines(byStrength[b], GL_LINES, glm::vec4(glm::mix(glm::vec3(0.35f, 0.65f, 1.0f), glm::vec3(1.0f, 0.5f, 0.2f), t), 0.85f));
        }
        std::vector<glm::vec3> onSuns;
        for (const Sun& sun : suns) {
            if (sun.mass <= 0.0f) continue;
            const glm::vec3 g = pull(sun.centre, &sun);
            const glm::vec3 d = glm::normalize(g);
            const glm::vec3 across = glm::normalize(glm::cross(d, std::abs(d.y) < 0.9f ? glm::vec3(0, 1, 0) : glm::vec3(1, 0, 0)));
            const float length = 2.0f + 3.0f * level(glm::length(g));
            const glm::vec3 start = sun.centre + (sun.radius + 0.2f) * d, tip = start + length * d;
            onSuns.insert(onSuns.end(), {start, tip, tip, tip - 0.3f * length * d + 0.18f * length * across,
                                         tip, tip - 0.3f * length * d - 0.18f * length * across});
        }
        lines(onSuns, GL_LINES, glm::vec4(1.0f, 1.0f, 1.0f, 0.9f));
    }

    // A circle in the disk plane.
    void ring(float radius, const glm::vec4& tint) {
        std::vector<glm::vec3> circle;
        for (int k = 0; k <= 128; ++k) {
            const float a = 6.2831853f * float(k) / 128.0f;
            circle.push_back(radius * glm::vec3(std::cos(a), 0.0f, std::sin(a)));
        }
        lines(circle, GL_LINE_STRIP, tint);
    }

    // Glowing points (position, colour pairs); light adds up. Points behind the
    // shadow are hidden.
    void points(const std::vector<glm::vec3>& positionColour, float shadowAngle, float size) {
        if (positionColour.empty()) return;
        glUseProgram(pointProgram);
        glUniformMatrix4fv(gl::at(pointProgram, "uViewProjection"), 1, GL_FALSE, glm::value_ptr(transform));
        glUniform3fv(gl::at(pointProgram, "uEye"), 1, glm::value_ptr(eye));
        glUniform1f(gl::at(pointProgram, "uShadowAngle"), shadowAngle);
        glUniform1f(gl::at(pointProgram, "uPointSize"), size);
        upload(positionColour.data(), positionColour.size() * sizeof(glm::vec3), true);
        glEnable(GL_PROGRAM_POINT_SIZE);
        glEnable(GL_BLEND);
        glBlendFunc(GL_ONE, GL_ONE);
        glDrawArrays(GL_POINTS, 0, GLsizei(positionColour.size() / 2));
        glDisable(GL_BLEND);
    }

private:
    void upload(const void* data, size_t bytes, bool withColour) {
        glBindVertexArray(vao);
        glBindBuffer(GL_ARRAY_BUFFER, buffer);
        glBufferData(GL_ARRAY_BUFFER, GLsizeiptr(bytes), data, GL_STREAM_DRAW);
        const GLsizei stride = GLsizei((withColour ? 2 : 1) * sizeof(glm::vec3));
        glEnableVertexAttribArray(0);
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, nullptr);
        if (withColour) {
            glEnableVertexAttribArray(1);
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, reinterpret_cast<void*>(sizeof(glm::vec3)));
        } else {
            glDisableVertexAttribArray(1);
        }
    }

    GLuint lineProgram = 0, pointProgram = 0, vao = 0, buffer = 0;
    glm::mat4 transform{1.0f};
    glm::vec3 eye{0.0f};
};
