#version 410 core
// Lesson 6: the gas is moving. It orbits at a large fraction of the speed of
// light, so the side coming towards us is Doppler-shifted brighter and bluer, and
// the side going away dimmer and redder. All of it also loses energy climbing out
// of the hole's gravity (gravitational redshift). Both shifts multiply into one
// factor g; the brightness goes as g^3 and the colour is a black body at the gas
// temperature times g. Hotter gas sits closer in.
//
// T: switch the shifts off, back to lesson 5's evenly coloured disk.
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

// Colour of a black body at temperature T (kelvin), from Planck's law at three
// wavelengths, scaled so 6500 K is white.
vec3 blackBody(float T) {
    const vec3 lambda = vec3(0.680, 0.550, 0.440);           // micrometres: red, green, blue
    vec3 at = 1.0 / (pow(lambda, vec3(5.0)) * (exp(14387.8 / (lambda * T)) - 1.0));
    vec3 white = 1.0 / (pow(lambda, vec3(5.0)) * (exp(14387.8 / (lambda * 6500.0)) - 1.0));
    vec3 c = at / white;
    return c / max(c.r, max(c.g, c.b));
}

vec3 diskColour(vec3 P, vec3 travel) {
    float r = length(P.xz);
    float brightness = pow(3.0 / r, 2.0) * 1.3;
    if (uCompare) return vec3(1.0, 0.6, 0.25) * min(brightness, 1.0);
    vec3 orbit = normalize(vec3(-P.z, 0.0, P.x));          // which way the gas moves here
    float beta = min(sqrt(0.5 / (r - 1.0)), 0.95);           // its speed as a fraction of light's
    float doppler = sqrt(1.0 - beta * beta) / (1.0 + beta * dot(orbit, travel));
    float g = doppler * sqrt(1.0 - 1.0 / r);                 // times the climb out of the hole's pull
    vec3 c = blackBody(6000.0 * pow(3.0 / r, 0.75) * g) * brightness * g * g * g;
    return pow(c / (1.0 + c), vec3(1.0 / 2.2));              // squeeze bright values below 1, then brighten midtones for the screen
}

void main() {
    vec3 x = uEye, v = cameraRay();
    vec3 spin = cross(x, v);
    float h2 = dot(spin, spin);
    vec3 colour = vec3(0.0);
    for (int i = 0; i < 2000; ++i) {
        float r = length(x);
        if (r < 1.5 && dot(x, v) < 0.0) break;
        if (r > 60.0) { colour = sky(normalize(v)); break; }
        vec3 before = x;
        rk4(x, v, h2, 0.02 * r / length(v));
        if (before.y * x.y < 0.0) {
            vec3 P = mix(before, x, before.y / (before.y - x.y));
            float rp = length(P.xz);
            if (rp > 3.0 && rp < 10.0) { colour = diskColour(P, normalize(x - before)); break; }
        }
    }
    outColour = vec4(colour, 1.0);
}
