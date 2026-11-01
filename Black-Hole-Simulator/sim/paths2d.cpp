// BlackHole2D: parallel light rays passing the hole, seen from above.
//
// The rays are integrated on the CPU in double precision with the same equation
// as the 3D tracer, restricted to one plane: x'' = -3/2 h^2 x / r^5, h = |x cross x'|,
// lengths in Schwarzschild radii. Each ray leaves a fading trail.
#include "capture.hpp"
#include "gl_tools.hpp"
#include "settings.hpp"
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

namespace {

constexpr double halfWidth = 1e11 / physical::schwarzschildRadiusM; // about 7.9 r_s either side
constexpr double stepLength = physical::c / physical::schwarzschildRadiusM; // light's distance in 1 s, about 0.024 r_s

struct LightRay {
    glm::dvec2 x, v;
    double h2 = 0.0;
    bool stopped = false;
    std::vector<glm::vec2> path;

    LightRay(glm::dvec2 start, glm::dvec2 direction) : x(start), v(glm::normalize(direction)) {
        const double h = x.x * v.y - x.y * v.x;
        h2 = h * h;
        path.push_back(glm::vec2(x));
    }

    glm::dvec2 pull(glm::dvec2 p) const {
        const double r2 = glm::dot(p, p);
        return -1.5 * h2 * p / (r2 * r2 * std::sqrt(r2));
    }

    // One fourth-order Runge-Kutta step covering about `length` of path.
    void step(double length) {
        if (stopped) return;
        const double dt = length / glm::length(v);
        const glm::dvec2 a1 = pull(x);
        const glm::dvec2 a2 = pull(x + 0.5 * dt * v);
        const glm::dvec2 a3 = pull(x + 0.5 * dt * v + 0.25 * dt * dt * a1);
        const glm::dvec2 a4 = pull(x + dt * v + 0.5 * dt * dt * a2);
        x += dt * v + dt * dt / 6.0 * (a1 + a2 + a3);
        v += dt / 6.0 * (a1 + 2.0 * a2 + 2.0 * a3 + a4);
        path.push_back(glm::vec2(x));
        const double r = glm::length(x);
        stopped = r < 1.0 || r > 60.0; // fell in, or long gone from view
    }
};

std::vector<LightRay> fireRays(int count, double halfHeight) {
    std::vector<LightRay> rays;
    for (int i = 0; i < count; ++i) {
        const double y = count == 1 ? 0.0 : 0.8 * halfHeight * (2.0 * i / (count - 1) - 1.0);
        rays.emplace_back(glm::dvec2(-halfWidth, y), glm::dvec2(1.0, 0.0));
    }
    return rays;
}

struct Vertex { glm::vec2 p; glm::vec4 colour; };

struct Painter {
    GLuint program = 0, vao = 0, buffer = 0;
    void create() {
        program = gl::program("shaders/paths2d.vert", "shaders/paths2d.frag");
        glGenVertexArrays(1, &vao);
        glGenBuffers(1, &buffer);
        glBindVertexArray(vao);
        glBindBuffer(GL_ARRAY_BUFFER, buffer);
        glEnableVertexAttribArray(0);
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex), nullptr);
        glEnableVertexAttribArray(1);
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, sizeof(Vertex), reinterpret_cast<void*>(sizeof(glm::vec2)));
    }
    void draw(const std::vector<Vertex>& vertices, GLenum mode) {
        if (vertices.empty()) return;
        glBindVertexArray(vao);
        glBindBuffer(GL_ARRAY_BUFFER, buffer);
        glBufferData(GL_ARRAY_BUFFER, GLsizeiptr(vertices.size() * sizeof(Vertex)), vertices.data(), GL_STREAM_DRAW);
        glDrawArrays(mode, 0, GLsizei(vertices.size()));
    }
};

bool paused = false, restart = false;
std::string stillsDir = "stills";

} // namespace

int main(int argc, char** argv) {
    const Settings settings = readSettings(argc, argv);
    paused = settings.startPaused;
    stillsDir = settings.captureDir + "/stills";
    if (!glfwInit()) { std::fprintf(stderr, "GLFW could not start\n"); return 1; }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
    GLFWwindow* window = glfwCreateWindow(settings.windowW, settings.windowH,
                                          physical::windowTitle("2D light paths").c_str(), nullptr, nullptr);
    if (!window) { std::fprintf(stderr, "no OpenGL 4.1 window\n"); glfwTerminate(); return 1; }
    glfwMakeContextCurrent(window);
    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) { std::fprintf(stderr, "GLEW could not start\n"); return 1; }
    glfwSetKeyCallback(window, [](GLFWwindow* w, int key, int, int action, int) {
        if (action != GLFW_PRESS) return;
        if (key == GLFW_KEY_SPACE) paused = !paused;
        if (key == GLFW_KEY_R) restart = true;
        if (key == GLFW_KEY_ESCAPE) glfwSetWindowShouldClose(w, GLFW_TRUE);
        if (key == GLFW_KEY_P) {
            int fw = 0, fh = 0;
            glfwGetFramebufferSize(w, &fw, &fh);
            capture::saveStill(fw, fh, stillsDir);
        }
    });

    Painter painter;
    painter.create();
    int pixelsW = 0, pixelsH = 0;
    glfwGetFramebufferSize(window, &pixelsW, &pixelsH);
    double halfHeight = halfWidth * pixelsH / pixelsW;
    std::vector<LightRay> rays = fireRays(settings.rayCount, halfHeight);
    capture::Video video;
    if (!settings.videoPath.empty() && !video.start(settings.videoPath, pixelsW, pixelsH)) return 1;

    std::vector<Vertex> hole;
    hole.push_back({glm::vec2(0.0f), glm::vec4(1, 0, 0, 1)});
    for (int k = 0; k <= 100; ++k) {
        const float a = 6.2831853f * float(k) / 100.0f;
        hole.push_back({glm::vec2(std::cos(a), std::sin(a)), glm::vec4(1, 0, 0, 1)}); // the horizon, r = r_s
    }

    for (int frame = 0; !glfwWindowShouldClose(window); ++frame) {
        if (restart) { rays = fireRays(settings.rayCount, halfHeight); restart = false; }
        glfwGetFramebufferSize(window, &pixelsW, &pixelsH);
        halfHeight = halfWidth * pixelsH / pixelsW; // circles stay round in any window shape
        glViewport(0, 0, pixelsW, pixelsH);
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        const glm::mat4 projection = glm::ortho(float(-halfWidth), float(halfWidth), float(-halfHeight), float(halfHeight));
        glUseProgram(painter.program);
        glUniformMatrix4fv(gl::at(painter.program, "uProjection"), 1, GL_FALSE, glm::value_ptr(projection));
        glUniform1f(gl::at(painter.program, "uPointSize"), 2.0f);
        painter.draw(hole, GL_TRIANGLE_FAN);

        if (!paused)
            for (LightRay& ray : rays)
                for (int k = 0; k < settings.stepsPerFrame; ++k) ray.step(stepLength);

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        std::vector<Vertex> heads;
        for (const LightRay& ray : rays) {
            std::vector<Vertex> trail;
            const size_t n = ray.path.size();
            for (size_t i = 0; i < n; ++i) { // older parts of the trail fade
                const float opacity = n > 1 ? std::max(float(i) / float(n - 1), 0.05f) : 1.0f;
                trail.push_back({ray.path[i], glm::vec4(1, 1, 1, opacity)});
            }
            painter.draw(trail, GL_LINE_STRIP);
            heads.push_back({glm::vec2(ray.x), glm::vec4(1, 0, 0, 1)});
        }
        glDisable(GL_BLEND);
        glEnable(GL_PROGRAM_POINT_SIZE);
        painter.draw(heads, GL_POINTS);

        video.add();
        if (!video.ok()) break;
        glfwSwapBuffers(window);
        glfwPollEvents();
        if (settings.frameLimit > 0 && frame + 1 >= settings.frameLimit) break;
    }
    video.stop();
    glfwDestroyWindow(window);
    glfwTerminate();
    return video.ok() ? 0 : 1;
}
