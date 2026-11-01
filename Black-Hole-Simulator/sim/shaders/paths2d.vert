#version 410 core
layout(location = 0) in vec2 aPosition;
layout(location = 1) in vec4 aColour;
uniform mat4 uProjection;
uniform float uPointSize;
out vec4 vColour;
void main() {
    gl_Position = uProjection * vec4(aPosition, 0.0, 1.0);
    gl_PointSize = uPointSize;
    vColour = aColour;
}
