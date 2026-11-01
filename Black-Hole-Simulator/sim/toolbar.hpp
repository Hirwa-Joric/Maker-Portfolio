// Switches stacked in the window's lower-left corner. Labels use a small built-in
// 5 x 7 pixel font, so no font files are needed. Coordinates are window points,
// y downwards, as GLFW reports the cursor.
#pragma once
#include "gl_tools.hpp"
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <algorithm>
#include <functional>
#include <string>
#include <vector>

class Toolbar {
public:
    struct Button {
        std::string label;
        std::function<bool()> isOn;
        std::function<void()> toggle;
    };
    std::vector<Button> buttons;
    bool visible = true;

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

    // Toggles the button under (x, y), if any. True when the click landed on one.
    bool click(double x, double y, int windowH) {
        if (!visible) return false;
        for (size_t i = 0; i < buttons.size(); ++i) {
            const Box b = box(i, windowH);
            if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
                buttons[i].toggle();
                return true;
            }
        }
        return false;
    }

    void draw(int windowW, int windowH) {
        if (!visible || buttons.empty()) return;
        std::vector<Vertex> v;
        for (size_t i = 0; i < buttons.size(); ++i) {
            const bool on = buttons[i].isOn();
            const Box b = box(i, windowH);
            rectangle(v, b.x, b.y, b.w, b.h, on ? glm::vec4(0.95f, 0.66f, 0.32f, 0.88f) : glm::vec4(0.08f, 0.09f, 0.12f, 0.72f));
            const glm::vec4 ink = on ? glm::vec4(0.07f, 0.06f, 0.05f, 1.0f) : glm::vec4(0.78f, 0.8f, 0.85f, 1.0f);
            float pen = b.x + padX;
            for (char c : buttons[i].label) {
                const unsigned char* rows = glyph(c);
                for (int r = 0; r < 7 && rows; ++r)
                    for (int col = 0; col < 5; ++col)
                        if (rows[r] & (16 >> col))
                            rectangle(v, pen + col * dot, b.y + padY + r * dot, dot, dot, ink);
                pen += 6 * dot;
            }
        }
        glUseProgram(program);
        const glm::mat4 projection = glm::ortho(0.0f, float(windowW), float(windowH), 0.0f);
        glUniformMatrix4fv(gl::at(program, "uProjection"), 1, GL_FALSE, glm::value_ptr(projection));
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glBindVertexArray(vao);
        glBindBuffer(GL_ARRAY_BUFFER, buffer);
        glBufferData(GL_ARRAY_BUFFER, GLsizeiptr(v.size() * sizeof(Vertex)), v.data(), GL_STREAM_DRAW);
        glDrawArrays(GL_TRIANGLES, 0, GLsizei(v.size()));
        glDisable(GL_BLEND);
    }

private:
    struct Vertex { glm::vec2 p; glm::vec4 colour; };
    struct Box { float x, y, w, h; };
    static constexpr float dot = 1.5f, padX = 8.0f, padY = 6.0f, gap = 4.0f, margin = 12.0f;

    Box box(size_t i, int windowH) const {
        size_t longest = 0;
        for (const Button& b : buttons) longest = std::max(longest, b.label.size());
        const float w = float(longest) * 6.0f * dot - dot + 2.0f * padX;
        const float h = 7.0f * dot + 2.0f * padY;
        const float fromBottom = float(buttons.size() - i) * (h + gap);
        return {margin, float(windowH) - margin - fromBottom + gap, w, h};
    }

    static void rectangle(std::vector<Vertex>& v, float x, float y, float w, float h, const glm::vec4& c) {
        const glm::vec2 a(x, y), b(x + w, y), d(x, y + h), e(x + w, y + h);
        v.insert(v.end(), {{a, c}, {b, c}, {e, c}, {a, c}, {e, c}, {d, c}});
    }

    // 5 x 7 capitals; each row's five low bits are the pixels, left to right.
    static const unsigned char* glyph(char c) {
        static const struct { char c; unsigned char rows[7]; } font[] = {
            {'A', {14, 17, 17, 31, 17, 17, 17}}, {'B', {30, 17, 17, 30, 17, 17, 30}},
            {'C', {14, 17, 16, 16, 16, 17, 14}}, {'D', {30, 17, 17, 17, 17, 17, 30}},
            {'E', {31, 16, 16, 30, 16, 16, 31}}, {'F', {31, 16, 16, 30, 16, 16, 16}},
            {'G', {14, 17, 16, 23, 17, 17, 15}}, {'H', {17, 17, 17, 31, 17, 17, 17}},
            {'I', {14, 4, 4, 4, 4, 4, 14}},      {'K', {17, 18, 20, 24, 20, 18, 17}},
            {'L', {16, 16, 16, 16, 16, 16, 31}}, {'M', {17, 27, 21, 21, 17, 17, 17}},
            {'N', {17, 25, 21, 19, 17, 17, 17}}, {'O', {14, 17, 17, 17, 17, 17, 14}},
            {'P', {30, 17, 17, 30, 16, 16, 16}}, {'R', {30, 17, 17, 30, 20, 18, 17}},
            {'S', {15, 16, 16, 14, 1, 1, 30}},   {'T', {31, 4, 4, 4, 4, 4, 4}},
            {'U', {17, 17, 17, 17, 17, 17, 14}}, {'V', {17, 17, 17, 17, 17, 10, 4}},
            {'W', {17, 17, 17, 21, 21, 21, 10}}, {'Y', {17, 17, 10, 4, 4, 4, 4}},
            {'1', {4, 12, 4, 4, 4, 4, 14}},      {'2', {14, 17, 1, 2, 4, 8, 31}},
            {'3', {31, 2, 4, 2, 1, 17, 14}},     {':', {0, 12, 12, 0, 12, 12, 0}},
        };
        for (const auto& g : font)
            if (g.c == c) return g.rows;
        return nullptr; // space and anything unknown: blank
    }

    GLuint program = 0, vao = 0, buffer = 0;
};
