#version 410 core
// Lesson 2: ray tracing. For each pixel, send a ray from the camera through that
// pixel and ask what it meets first. Here there is one ball (radius 2.5, at the
// centre) and a sky painted as a checkerboard. Light travels in straight lines.
//
// T: show how far each ray travelled before it hit the ball (brighter = nearer).
out vec4 outColour;
uniform vec2 uResolution;
uniform bool uCompare;
uniform vec3 uEye, uRight, uUp, uAhead;   // camera position and its three directions

// The ray through this pixel, for a 60 degree field of view.
vec3 cameraRay() {
    vec2 p = (2.0 * gl_FragCoord.xy - uResolution) / uResolution.y;
    return normalize(uAhead + 0.577 * (p.x * uRight + p.y * uUp));
}

// The sky: a checkerboard on a huge sphere, 15 degrees a square.
vec3 sky(vec3 d) {
    float longitude = atan(d.z, d.x), latitude = asin(clamp(d.y, -1.0, 1.0));
    float squares = floor(longitude / 0.2618) + floor(latitude / 0.2618);
    return mod(squares, 2.0) > 0.5 ? vec3(0.10, 0.12, 0.20) : vec3(0.22, 0.26, 0.40);
}

// Distance t along the ray to the ball, or -1 if it misses.
// Solve |origin + t*dir|^2 = radius^2, a quadratic in t; take the nearer answer.
float hitBall(vec3 origin, vec3 dir, float radius) {
    float b = dot(origin, dir);
    float c = dot(origin, origin) - radius * radius;
    float disc = b * b - c;
    if (disc < 0.0) return -1.0;
    return -b - sqrt(disc);
}

void main() {
    vec3 dir = cameraRay();
    float t = hitBall(uEye, dir, 2.5);
    vec3 colour = sky(dir);
    if (t > 0.0) {
        vec3 normal = normalize(uEye + t * dir);         // points out of the ball where we hit it
        float light = max(dot(normal, normalize(vec3(1.0, 1.0, 0.5))), 0.0);
        colour = uCompare ? vec3(1.0 - t / 30.0) : vec3(0.9, 0.5, 0.3) * (0.15 + 0.85 * light);
    }
    outColour = vec4(colour, 1.0);
}
