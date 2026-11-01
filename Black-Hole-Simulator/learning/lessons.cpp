// ShaderLessons: the ideas behind the simulator, one small fragment shader at a time.
//
// Keys 1-6 pick a lesson. T flips each lesson's comparison (shown in the title).
// R reloads the lesson after you edit its .frag file, so you can experiment.
// Drag or arrow keys orbit the camera, scroll zooms, ESC quits.
// ShaderLessons --lesson N [--compare] --save FILE.png renders one lesson to a picture.
#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

// One triangle that covers the window; the fragment shader then runs once per pixel.
const char* screenVertex = R"(#version 410 core
void main() {
    vec2 corner = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
    gl_Position = vec4(corner * 2.0 - 1.0, 0.0, 1.0);
})";

struct Lesson {
    std::string path, title;
};

std::vector<Lesson> findLessons() {
    std::vector<Lesson> lessons;
    for (const auto& entry : fs::directory_iterator(LESSON_DIR))
        if (entry.path().extension() == ".frag") {
            std::string name = entry.path().stem().string(); // "4-bend-the-light"
            std::string title = name.substr(name.find('-') + 1);
            std::replace(title.begin(), title.end(), '-', ' ');
            lessons.push_back({entry.path().string(), title});
        }
    std::sort(lessons.begin(), lessons.end(), [](const Lesson& a, const Lesson& b) { return a.path < b.path; });
    return lessons;
}

// Compiles a lesson; on an error prints the log and returns 0, so the last good
// version keeps running while you fix it.
GLuint build(const std::string& fragmentPath) {
    std::ifstream file(fragmentPath);
    std::stringstream text;
    text << file.rdbuf();
    const std::string fragment = text.str();
    auto compile = [](GLenum kind, const char* source, const std::string& name) -> GLuint {
        GLuint shader = glCreateShader(kind);
        glShaderSource(shader, 1, &source, nullptr);
        glCompileShader(shader);
        GLint ok = GL_FALSE;
        glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
        if (ok) return shader;
        char log[4096];
        glGetShaderInfoLog(shader, sizeof(log), nullptr, log);
        std::fprintf(stderr, "%s:\n%s\n", name.c_str(), log);
        glDeleteShader(shader);
        return 0;
    };
    GLuint vs = compile(GL_VERTEX_SHADER, screenVertex, "vertex");
    GLuint fs_ = compile(GL_FRAGMENT_SHADER, fragment.c_str(), fragmentPath);
    if (!vs || !fs_) return 0;
    GLuint program = glCreateProgram();
    glAttachShader(program, vs);
    glAttachShader(program, fs_);
    glLinkProgram(program);
    glDeleteShader(vs);
    glDeleteShader(fs_);
    return program;
}

struct State {
    std::vector<Lesson> lessons;
    int current = 0;
    bool compare = false, reload = true;
    float distance = 20.0f, azimuth = 0.0f, polar = 1.40f; // camera, in Schwarzschild radii and radians
    bool dragging = false;
    double lastX = 0.0, lastY = 0.0;
} state;

void updateTitle(GLFWwindow* window) {
    const Lesson& lesson = state.lessons[state.current];
    char title[256];
    std::snprintf(title, sizeof(title), "Lesson %d of %d: %s   |   T: compare (%s)   R: reload   1-%d: lessons",
                  state.current + 1, int(state.lessons.size()), lesson.title.c_str(),
                  state.compare ? "on" : "off", int(state.lessons.size()));
    glfwSetWindowTitle(window, title);
}

} // namespace

int main(int argc, char** argv) {
    std::string savePath;
    for (int i = 1; i < argc; ++i) {
        const std::string flag = argv[i];
        if (flag == "--lesson" && i + 1 < argc) state.current = std::atoi(argv[++i]) - 1;
        else if (flag == "--compare") state.compare = true;
        else if (flag == "--save" && i + 1 < argc) savePath = argv[++i];
    }
    state.lessons = findLessons();
    state.current = std::clamp(state.current, 0, int(state.lessons.size()) - 1);
    if (state.lessons.empty()) { std::fprintf(stderr, "no lessons in %s\n", LESSON_DIR); return 1; }
    if (!glfwInit()) return 1;
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
    GLFWwindow* window = glfwCreateWindow(800, 500, "Shader lessons", nullptr, nullptr);
    if (!window) return 1;
    glfwMakeContextCurrent(window);
    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) return 1;
    glfwSwapInterval(1);

    glfwSetKeyCallback(window, [](GLFWwindow* w, int key, int, int action, int) {
        if (action != GLFW_PRESS) return;
        if (key >= GLFW_KEY_1 && key < GLFW_KEY_1 + int(state.lessons.size())) {
            state.current = key - GLFW_KEY_1;
            state.compare = false;
            state.reload = true;
        }
        if (key == GLFW_KEY_T) { state.compare = !state.compare; updateTitle(w); }
        if (key == GLFW_KEY_R) state.reload = true;
        if (key == GLFW_KEY_ESCAPE) glfwSetWindowShouldClose(w, GLFW_TRUE);
    });
    glfwSetMouseButtonCallback(window, [](GLFWwindow* w, int button, int action, int) {
        if (button != GLFW_MOUSE_BUTTON_LEFT) return;
        state.dragging = action == GLFW_PRESS;
        glfwGetCursorPos(w, &state.lastX, &state.lastY);
    });
    glfwSetCursorPosCallback(window, [](GLFWwindow*, double x, double y) {
        if (state.dragging) {
            state.azimuth += 0.01f * float(x - state.lastX);
            state.polar = glm::clamp(state.polar - 0.01f * float(y - state.lastY), 0.05f, 3.09f);
        }
        state.lastX = x;
        state.lastY = y;
    });
    glfwSetScrollCallback(window, [](GLFWwindow*, double, double steps) {
        state.distance = glm::clamp(state.distance * float(std::pow(0.93, steps)), 3.0f, 80.0f);
    });

    GLuint vao = 0;
    glGenVertexArrays(1, &vao);
    GLuint program = 0;
    double last = glfwGetTime();
    while (!glfwWindowShouldClose(window)) {
        const double now = glfwGetTime();
        const float dt = float(std::min(now - last, 0.1));
        last = now;
        if (state.reload) {
            if (GLuint fresh = build(state.lessons[state.current].path)) {
                if (program) glDeleteProgram(program);
                program = fresh;
            }
            state.reload = false;
            updateTitle(window);
        }
        const bool saving = !savePath.empty();
        if (glfwGetKey(window, GLFW_KEY_LEFT) == GLFW_PRESS) state.azimuth -= 1.2f * dt;
        if (glfwGetKey(window, GLFW_KEY_RIGHT) == GLFW_PRESS) state.azimuth += 1.2f * dt;
        if (glfwGetKey(window, GLFW_KEY_UP) == GLFW_PRESS) state.polar = std::max(0.05f, state.polar - dt);
        if (glfwGetKey(window, GLFW_KEY_DOWN) == GLFW_PRESS) state.polar = std::min(3.09f, state.polar + dt);

        // the camera sits on a sphere around the origin and looks at it
        const glm::vec3 eye = state.distance * glm::vec3(std::sin(state.polar) * std::cos(state.azimuth),
                                                         std::cos(state.polar),
                                                         std::sin(state.polar) * std::sin(state.azimuth));
        const glm::vec3 ahead = -glm::normalize(eye);
        const glm::vec3 right = glm::normalize(glm::cross(ahead, glm::vec3(0, 1, 0)));
        const glm::vec3 up = glm::cross(right, ahead);

        int w = 0, h = 0;
        glfwGetFramebufferSize(window, &w, &h);
        glViewport(0, 0, w, h);
        if (program) {
            glUseProgram(program);
            glUniform2f(glGetUniformLocation(program, "uResolution"), float(w), float(h));
            glUniform1f(glGetUniformLocation(program, "uTime"), float(now));
            glUniform1i(glGetUniformLocation(program, "uCompare"), state.compare);
            glUniform3fv(glGetUniformLocation(program, "uEye"), 1, glm::value_ptr(eye));
            glUniform3fv(glGetUniformLocation(program, "uRight"), 1, glm::value_ptr(right));
            glUniform3fv(glGetUniformLocation(program, "uUp"), 1, glm::value_ptr(up));
            glUniform3fv(glGetUniformLocation(program, "uAhead"), 1, glm::value_ptr(ahead));
            glBindVertexArray(vao);
            glDrawArrays(GL_TRIANGLES, 0, 3);
        }
        if (saving) { // read the frame back and hand it to ffmpeg as a PNG
            std::vector<unsigned char> rgb(size_t(w) * h * 3);
            glPixelStorei(GL_PACK_ALIGNMENT, 1);
            glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, rgb.data());
            const std::string command = "ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s " + std::to_string(w) +
                                        "x" + std::to_string(h) + " -i - -vf vflip -frames:v 1 \"" + savePath + "\"";
            if (FILE* pipe = popen(command.c_str(), "w")) { std::fwrite(rgb.data(), 1, rgb.size(), pipe); pclose(pipe); }
            break;
        }
        glfwSwapBuffers(window);
        glfwPollEvents();
    }
    glfwTerminate();
    return 0;
}
