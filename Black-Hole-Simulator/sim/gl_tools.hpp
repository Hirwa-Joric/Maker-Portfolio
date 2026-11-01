// Small OpenGL helpers: shader programs from files, render targets and a
// full-screen triangle. Shader files are read from the working directory
// (CMake copies them next to the executables).
#pragma once
#include <GL/glew.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>

namespace gl {

inline std::string readText(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        std::fprintf(stderr, "cannot read %s (run from the build folder)\n", path.c_str());
        std::exit(1);
    }
    std::stringstream text;
    text << file.rdbuf();
    return text.str();
}

inline GLuint compile(GLenum kind, const std::string& source, const std::string& name) {
    GLuint shader = glCreateShader(kind);
    const char* text = source.c_str();
    glShaderSource(shader, 1, &text, nullptr);
    glCompileShader(shader);
    GLint ok = GL_FALSE;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[4096];
        glGetShaderInfoLog(shader, sizeof(log), nullptr, log);
        std::fprintf(stderr, "%s failed to compile:\n%s\n", name.c_str(), log);
        std::exit(1);
    }
    return shader;
}

// Builds a program from two shader files. `defines` is inserted after the
// #version line of both, so one file can hold several variants.
inline GLuint program(const std::string& vertexFile, const std::string& fragmentFile,
                      const std::string& defines = "") {
    std::string vertex = readText(vertexFile), fragment = readText(fragmentFile);
    if (!defines.empty()) {
        vertex.insert(vertex.find('\n') + 1, defines + "\n");
        fragment.insert(fragment.find('\n') + 1, defines + "\n");
    }
    GLuint vs = compile(GL_VERTEX_SHADER, vertex, vertexFile);
    GLuint fs = compile(GL_FRAGMENT_SHADER, fragment, fragmentFile);
    GLuint id = glCreateProgram();
    glAttachShader(id, vs);
    glAttachShader(id, fs);
    glLinkProgram(id);
    glDeleteShader(vs);
    glDeleteShader(fs);
    GLint ok = GL_FALSE;
    glGetProgramiv(id, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[4096];
        glGetProgramInfoLog(id, sizeof(log), nullptr, log);
        std::fprintf(stderr, "%s + %s failed to link:\n%s\n", vertexFile.c_str(), fragmentFile.c_str(), log);
        std::exit(1);
    }
    return id;
}

inline GLint at(GLuint program, const char* name) { return glGetUniformLocation(program, name); }

// A colour texture with a framebuffer that draws into it.
struct Target {
    GLuint texture = 0, framebuffer = 0;
    int w = 0, h = 0;

    void resize(int width, int height, GLenum format = GL_RGBA16F) {
        if (!texture) {
            glGenTextures(1, &texture);
            glGenFramebuffers(1, &framebuffer);
        }
        if (width == w && height == h) return;
        w = width; h = height;
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexImage2D(GL_TEXTURE_2D, 0, format, w, h, 0, GL_RGBA, GL_FLOAT, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0);
        if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE)
            std::fprintf(stderr, "render target %dx%d is incomplete\n", w, h);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
    }
    void bindForDrawing() const {
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        glViewport(0, 0, w, h);
    }
};

// One triangle that covers the screen; the vertex shader makes its corners
// from gl_VertexID, so no vertex data is needed.
struct ScreenTriangle {
    GLuint vao = 0;
    void create() { glGenVertexArrays(1, &vao); }
    void draw() const {
        glBindVertexArray(vao);
        glDrawArrays(GL_TRIANGLES, 0, 3);
    }
};

// Draws the bound program over the bound target in horizontal bands: macOS
// stops GPU work that runs too long in one submission.
inline void drawInBands(const ScreenTriangle& screen, int w, int fromRow, int toRow, int bandRows) {
    glEnable(GL_SCISSOR_TEST);
    for (int row = fromRow; row < toRow; row += bandRows) {
        glScissor(0, row, w, std::min(bandRows, toRow - row));
        screen.draw();
        glFlush();
    }
    glDisable(GL_SCISSOR_TEST);
}

} // namespace gl
