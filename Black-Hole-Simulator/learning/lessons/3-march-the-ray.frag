#version 410 core
// Lesson 3: marching. Lesson 2 found the ball with a formula, but a ray bent by
// gravity has no simple formula. So instead we walk along the ray in small steps
// and check, after each one, whether we are inside the ball or far away.
// The picture is the same as lesson 2, computed the slow, general way.
//
// T: colour by how many steps each ray took (blue: few, red: many). Steps are a
// fixed fraction of the distance to the centre, so they are short near the ball.
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

void main() {
    vec3 dir = cameraRay();
    vec3 x = uEye;
    vec3 colour = sky(dir);
    int steps = 0;
    for (; steps < 2000; ++steps) {
        float r = length(x);
        if (r < 2.5) {                                    // inside the ball (radius 2.5): we hit it
            float light = max(dot(normalize(x), normalize(vec3(1.0, 1.0, 0.5))), 0.0);
            colour = vec3(0.9, 0.5, 0.3) * (0.15 + 0.85 * light);
            break;
        }
        if (r > 60.0) break;                              // far away: it reached the sky
        x += dir * max(0.02 * (r - 2.5), 0.002);           // a step of 2% of the gap to the ball
    }
    if (uCompare) {
        float k = clamp(float(steps) / 300.0, 0.0, 1.0);
        colour = mix(vec3(0.1, 0.3, 1.0), vec3(1.0, 0.2, 0.1), k);
    }
    outColour = vec4(colour, 1.0);
}
