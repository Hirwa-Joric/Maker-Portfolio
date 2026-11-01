#version 410 core
// Lesson 4: gravity bends the light. Now the ball is a black hole, one
// Schwarzschild radius across (r_s = 1 in these units). Around it a light ray
// stays in one plane and follows
//     u'' + u = 3/2 u^2,   u = 1/r,
// which, written for the ray's position x, is a pull towards the centre:
//     x'' = -3/2 h^2 x / r^5,   h = |x cross x'| (fixed for each ray).
// Each step uses fourth-order Runge-Kutta: it samples the pull four times across
// the step and averages, which is far more accurate than one sample.
// A ray that heads inwards inside 1.5 r_s can never turn back: it falls in.
//
// T: switch gravity off. The hole is then just a small black ball, and the
// checkerboard is undistorted. With gravity, the black shadow is about 2.6 times
// wider than the hole, and the sky behind it is wrapped into rings.
out vec4 outColour;
uniform vec2 uResolution;
uniform bool uCompare;
uniform vec3 uEye, uRight, uUp, uAhead;

vec3 cameraRay() {
    vec2 p = (2.0 * gl_FragCoord.xy - uResolution) / uResolution.y;
    return normalize(uAhead + 0.577 * (p.x * uRight + p.y * uUp));
}

vec3 sky(vec3 d) {
    float longitude = atan(d.z, d.x), latitude = asin(clamp(d.y, -1.0, 1.0));
    float squares = floor(longitude / 0.2618) + floor(latitude / 0.2618);
    return mod(squares, 2.0) > 0.5 ? vec3(0.10, 0.12, 0.20) : vec3(0.22, 0.26, 0.40);
}

vec3 pull(vec3 x, float h2) {
    float r2 = dot(x, x);
    return -1.5 * h2 * x / (r2 * r2 * sqrt(r2));
}

void rk4(inout vec3 x, inout vec3 v, float h2, float dt) {
    vec3 a1 = pull(x, h2);
    vec3 a2 = pull(x + 0.5 * dt * v, h2);
    vec3 a3 = pull(x + 0.5 * dt * v + 0.25 * dt * dt * a1, h2);
    vec3 a4 = pull(x + dt * v + 0.5 * dt * dt * a2, h2);
    x += dt * v + dt * dt / 6.0 * (a1 + a2 + a3);
    v += dt / 6.0 * (a1 + 2.0 * a2 + 2.0 * a3 + a4);
}

void main() {
    vec3 x = uEye, v = cameraRay();
    vec3 spin = cross(x, v);
    float h2 = uCompare ? 0.0 : dot(spin, spin);   // h = 0 means no pull at all
    vec3 colour = vec3(0.0);                        // black unless the ray escapes
    for (int i = 0; i < 2000; ++i) {
        float r = length(x);
        if (r < 1.0 || (!uCompare && r < 1.5 && dot(x, v) < 0.0)) break; // fell in
        if (r > 60.0) { colour = sky(normalize(v)); break; }             // escaped
        rk4(x, v, h2, 0.02 * r / length(v));        // steps of 2% of the distance
    }
    outColour = vec4(colour, 1.0);
}
