#version 410 core
// Lesson 1: a fragment shader runs once for every pixel, all at the same time.
// It knows only where its pixel is (gl_FragCoord) and a few values passed in from
// C++ (uniforms). Whatever it writes to outColour becomes that pixel's colour.
//
// T: every pixel works out its own ring pattern from its distance to the centre.
out vec4 outColour;
uniform vec2 uResolution;   // window size in pixels
uniform float uTime;        // seconds since the start
uniform bool uCompare;

void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;            // 0 to 1 across the window
    vec3 colour = vec3(uv.x, uv.y, 0.5 + 0.5 * sin(uTime)); // red grows rightwards, green upwards

    // the same position measured from the centre, in units of the window's height
    vec2 p = (gl_FragCoord.xy - 0.5 * uResolution) / uResolution.y;
    float distance = length(p);
    if (uCompare)
        colour *= 0.5 + 0.5 * sin(40.0 * distance - 3.0 * uTime);
    else if (distance < 0.2)
        colour = vec3(1.0);                             // a white disc in the middle

    outColour = vec4(colour, 1.0);
}
