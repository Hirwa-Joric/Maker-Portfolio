#version 410 core
// Lesson 5: a thin disk of gas, lying flat around the hole from 3 to 10 r_s.
// The ray is the same bent ray as in lesson 4. After each step we check whether
// it crossed the disk's plane (y changed sign); if it did, between 3 and 10 r_s,
// the gas glows there: brighter close in, one colour family, and opaque.
// This is roughly what the first Python version drew.
//
// T: colour each crossing by its order: orange for a ray's first crossing, blue
// for its second, green for its third. The blue band above the shadow is the far
// side of the disk, seen over the top of the hole; light from it bent towards us.
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
    float h2 = dot(spin, spin);
    vec3 colour = vec3(0.0);
    int crossings = 0;
    for (int i = 0; i < 2000; ++i) {
        float r = length(x);
        if (r < 1.5 && dot(x, v) < 0.0) break;
        if (r > 60.0) { colour = sky(normalize(v)); break; }
        vec3 before = x;
        rk4(x, v, h2, 0.02 * r / length(v));
        if (before.y * x.y < 0.0) {                        // crossed the plane y = 0
            vec3 P = mix(before, x, before.y / (before.y - x.y));
            float rp = length(P.xz);
            if (rp > 3.0 && rp < 10.0) {
                const vec3 order[3] = vec3[](vec3(1.0, 0.55, 0.2), vec3(0.3, 0.6, 1.0), vec3(0.4, 1.0, 0.5));
                colour = uCompare ? order[min(crossings, 2)] : vec3(1.0, 0.6, 0.25) * min(pow(3.0 / rp, 2.0) * 1.3, 1.0);
                break;
            }
            ++crossings;
        }
    }
    outColour = vec4(colour, 1.0);
}
