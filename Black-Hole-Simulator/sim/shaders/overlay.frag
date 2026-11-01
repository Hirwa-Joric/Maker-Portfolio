#version 410 core
in vec3 vColour;
in float vFade;
out vec4 outColour;
uniform vec4 uTint;   // LINES: one colour and opacity for the whole line
void main() {
#if defined(POINTS)
    float d = 2.0 * length(gl_PointCoord - 0.5);   // a soft round dot; light adds up
    outColour = vec4(vColour * exp(-3.0 * d * d), 1.0);
#else
    outColour = vec4(uTint.rgb, uTint.a * vFade);
#endif
}
