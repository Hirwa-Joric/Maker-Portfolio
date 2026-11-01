#version 410 core
// Copies an image (with its alpha); with constant-alpha blending this keeps a running average.
in vec2 vUV;
out vec4 outColour;
uniform sampler2D uSource;
void main() { outColour = textureLod(uSource, vUV, 0.0); }
