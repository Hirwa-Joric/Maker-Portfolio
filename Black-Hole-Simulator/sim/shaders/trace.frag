#version 410 core
// Follows one light ray per pixel backwards from the camera through Schwarzschild
// spacetime. Lengths are in Schwarzschild radii (r_s = 1). The same file also
// paints the sky box and the disk's gas pattern once at start-up (BAKE_SKY, BAKE_GAS).
out vec4 outColour;

uniform ivec2 uImageSize;
uniform vec3  uEye;              // camera position
uniform vec3  uRight, uUp, uAhead;
uniform float uTanHalfFov, uAspect;
uniform vec2  uSubpixel;         // where in its pixel the ray starts; (0.5, 0.5) is the centre
uniform int   uStyle;            // 0 grid diagnostic, 1 standard, 2 shadow mask for measuring
uniform bool  uAngularGrid;      // a distant 15 degree grid, seen through the bent rays
uniform float uSpinTime;         // turns the gas
uniform float uPixelAngle;       // angle one pixel of this image covers
uniform float uStarAngle;        // star size: one pixel of the full-detail image
uniform float uSkyTexelAngle;
uniform float uStepScale;        // 1 = full accuracy, 2 = the moving preview's coarser steps
uniform float uRingAngle;        // > 0: draw the predicted shadow edge at this angle
uniform float uSkyGain;
uniform float uDiskGain;         // > 1 while the hole is swallowing debris
uniform vec2  uDiskRadii;        // inner and outer edge; (0, 0) hides the disk
uniform int   uBodyCount;
uniform vec4  uBodies[16];       // centre and radius of each sun
uniform vec3  uBodyColours[16];
uniform float uBodyMasses[16];   // as a fraction of the hole's mass (0: does not bend light)
uniform vec4  uBodyStretch[16];  // xyz: the axis a sun is stretched along; w: how much (1 = round)
uniform bool  uSunLensing;       // the suns' own gravity bends light too
uniform int   uStage;            // learning stages: 0 straight light, 1 bent light and a plain disk, 2 everything
uniform samplerCube uSky;
uniform sampler2D   uGas;
uniform int   uFace;             // BAKE_SKY: which side of the cube
uniform float uLogSpan;          // BAKE_GAS: log(outer / inner disk radius)

const float EXIT_RADIUS = 94.5;  // beyond the farthest camera and every object
const int   MAX_STEPS = 5000;    // rays that wind round the photon sphere stop here
const float TAU = 6.2831853;

// ---------------------------------------------------------------------------
// Light paths
//
// In Schwarzschild coordinates a light ray stays in one plane, and its path obeys
// u'' + u = 3/2 u^2, where u = 1/r and ' is d/d(angle). Writing the ray's position
// as an ordinary 3D vector x (with |x| = r), the same paths solve
//     d^2x/ds^2 = -3/2 h^2 x / r^5,        h = |x cross dx/ds| (constant),
// a central "force" that pulls only on rays passing sideways. No angles are
// needed, so nothing goes wrong at the poles of a coordinate system.
//
vec3 pull(vec3 x, float h2) {
    float r2 = dot(x, x);
    return -1.5 * h2 * x / (r2 * r2 * sqrt(r2));
}

// Fourth-order Runge-Kutta step of length dt along the parameter s (hole only).
void advance(inout vec3 x, inout vec3 v, float dt) {
    vec3 spin = cross(x, v);
    float h2 = dot(spin, spin);
    vec3 a1 = pull(x, h2);
    vec3 a2 = pull(x + 0.5 * dt * v, h2);
    vec3 a3 = pull(x + 0.5 * dt * v + 0.25 * dt * dt * a1, h2);
    vec3 a4 = pull(x + dt * v + 0.5 * dt * dt * a2, h2);
    x += dt * v + dt * dt / 6.0 * (a1 + a2 + a3);
    v += dt / 6.0 * (a1 + 2.0 * a2 + 2.0 * a3 + a4);
}

// The suns are far too light to matter in reality, but here they carry the same
// exaggerated masses as in their mutual gravity, so their bending shows. Far from
// a mass m, light is deflected by 4Gm/(c^2 b): twice the Newtonian pull, and only
// across the ray. This weak bending is applied as a half kick before and after each
// step of the hole's equation. Also returns the gap to the nearest sun's surface.
vec3 sunGradient(vec3 x, out float gap) {
    vec3 g = vec3(0.0);  // gradient of the suns' potential; GM = m/2 in these units
    gap = 1e9;
    for (int b = 0; b < uBodyCount; ++b) {
        if (uBodyMasses[b] <= 0.0) continue;
        vec3 d = x - uBodies[b].xyz;
        float d2 = max(dot(d, d), uBodies[b].w * uBodies[b].w);
        g += 0.5 * uBodyMasses[b] * d / (d2 * sqrt(d2));
        gap = min(gap, sqrt(d2) - uBodies[b].w);
    }
    return g;
}
vec3 kick(vec3 v, vec3 g, float dt) {
    return v - 2.0 * dt * (dot(v, v) * g - dot(g, v) * v); // across the ray; scales with |v|^2 like the hole's term
}

// The camera is at rest at radius r. Its local measuring rods are shorter radially
// than the coordinate r suggests, by sqrt(1 - 1/r), so a direction it sees has a
// smaller radial part in coordinates.
vec3 coordinateDirection(vec3 position, vec3 seen) {
    vec3 out_ = normalize(position);
    float radial = dot(seen, out_);
    return seen + (sqrt(1.0 - 1.0 / length(position)) - 1.0) * radial * out_;
}

// A sun stretched by the hole's tides is a sphere seen through a linear map:
// lengths along the axis shrink by the stretch s and lengths across grow by
// sqrt(s), so the sun is s times longer and 1/sqrt(s) times thinner.
vec3 unstretch(int b, vec3 q) {
    vec3 n = uBodyStretch[b].xyz;
    float k = uBodyStretch[b].w;
    return sqrt(k) * q + (1.0 / k - sqrt(k)) * dot(q, n) * n;
}

// Where along the segment from a to a + d (0 to 1) it first enters sun b; 2 if it
// misses. A step can be wider than a small sun, so the whole segment is tested,
// not only its end.
float entersBody(int b, vec3 a, vec3 d) {
    vec3 m = unstretch(b, a - uBodies[b].xyz);
    vec3 e = unstretch(b, d);
    float c = dot(m, m) - uBodies[b].w * uBodies[b].w;
    if (c <= 0.0) return 0.0;
    float bm = dot(m, e), ee = dot(e, e);
    float disc = bm * bm - ee * c;
    if (disc < 0.0 || bm > 0.0) return 2.0;
    float t = (-bm - sqrt(disc)) / ee;
    return t <= 1.0 ? t : 2.0;
}

// Outward direction of sun b's surface at p.
vec3 bodyNormal(int b, vec3 p) {
    return normalize(unstretch(b, unstretch(b, p - uBodies[b].xyz)));
}

// ---------------------------------------------------------------------------
// Appearance. None of this changes where light goes.

// PCG RXS-M-XS integer permutation, used for the stars and the noise.
uint pcg(uint n) {
    uint state = n * 747796405u + 2891336453u;
    uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
    return (word >> 22u) ^ word;
}
uint hashCell(vec3 cell) {
    uvec3 bits = floatBitsToUint(cell + vec3(0.0));
    return pcg(pcg(pcg(bits.z ^ 0x9e3779b9u) ^ bits.x) ^ bits.y);
}
float toUnit(uint bits) { return float(bits >> 8u) / 16777216.0; }
float random1(vec3 cell) { return toUnit(hashCell(cell)); }
vec3 random3(vec3 cell) {
    uint h = hashCell(cell);
    return vec3(toUnit(pcg(h ^ 0xa511e9b3u)), toUnit(pcg(h ^ 0x63d83595u)), toUnit(pcg(h ^ 0xb5297a4du)));
}

float smoothNoise(vec3 p) {
    vec3 c = floor(p), t = fract(p);
    t = t * t * (3.0 - 2.0 * t);
    float n000 = random1(c),                 n100 = random1(c + vec3(1, 0, 0));
    float n010 = random1(c + vec3(0, 1, 0)), n110 = random1(c + vec3(1, 1, 0));
    float n001 = random1(c + vec3(0, 0, 1)), n101 = random1(c + vec3(1, 0, 1));
    float n011 = random1(c + vec3(0, 1, 1)), n111 = random1(c + vec3(1, 1, 1));
    return mix(mix(mix(n000, n100, t.x), mix(n010, n110, t.x), t.y),
               mix(mix(n001, n101, t.x), mix(n011, n111, t.x), t.y), t.z);
}
float layeredNoise(vec3 p) {
    float sum = 0.0, weight = 0.5;
    for (int octave = 0; octave < 4; ++octave) {
        sum += weight * smoothNoise(p);
        p = p * 2.03 + 17.1;
        weight *= 0.5;
    }
    return sum;
}

// Colour of a black body at temperature T: Planck's law sampled at 680, 550 and
// 440 nm, scaled so that 6500 K is white. An approximation, not CIE integration.
vec3 planckColour(float T) {
    const vec3 lambda = vec3(0.680, 0.550, 0.440);   // micrometres
    const float c2 = 14387.76877;                     // hc/k in micrometre kelvin
    vec3 lambda5 = pow(lambda, vec3(5.0));
    vec3 at = 1.0 / (lambda5 * (exp(c2 / (lambda * clamp(T, 1000.0, 40000.0))) - 1.0));
    vec3 white = 1.0 / (lambda5 * (exp(c2 / (lambda * 6500.0)) - 1.0));
    vec3 colour = at / white;
    return colour / max(colour.r, max(colour.g, colour.b));
}

float gasPattern(float angle, float logRadius) {
    vec3 q = vec3(2.5 * cos(angle), 2.5 * sin(angle), 7.0 * logRadius);
    return layeredNoise(q + vec3(0.0, 0.0, 3.0 * layeredNoise(0.7 * q)));
}

// Light from the thin disk where a ray crosses it at P, travelling along dir.
// rgb: emitted colour; a: opacity there.
vec4 diskLight(vec3 P, vec3 dir) {
    float inner = uDiskRadii.x, outer = uDiskRadii.y;
    float r = length(P.xz);
    float x = r / inner;
    float edge = max(1.0 - inversesqrt(x), 0.0);
    // thin-disk profile: dark at the inner edge, brightest just outside, fading out
    float profile = 17.0 * edge / (x * x * x);
    float temperature = 5000.0 / 0.488 * pow(x, -0.75) * pow(max(edge, 1e-4), 0.25);
    // the gas turns at Kepler's rate, faster inside
    float angle = atan(P.z, P.x) - uSpinTime * pow(x, -1.5);
    float blur = max(log2(uPixelAngle / uStarAngle), 0.0);
    float gas = textureLod(uGas, vec2(angle / TAU, log(x) / log(outer / inner)), blur).r;
    // Doppler shift of gas orbiting at speed beta, then the climb out of the hole's pull
    vec3 orbit = normalize(vec3(-P.z, 0.0, P.x));
    float beta = min(sqrt(0.5 / max(r - 1.0, 0.05)), 0.95);
    float doppler = sqrt(1.0 - beta * beta) / (1.0 + beta * dot(orbit, dir));
    float shift = doppler * sqrt(max(1.0 - 1.0 / r, 0.0));
    float brightness = profile * shift * shift * shift * (0.35 + 1.3 * gas);
    vec3 colour = planckColour(temperature * shift) * brightness * 2.2 * uDiskGain;
    float opacity = smoothstep(inner, 1.35 * inner, r) * (1.0 - smoothstep(0.55 * outer, outer, r))
                  * clamp(0.45 + 0.9 * gas, 0.0, 1.0);
    return vec4(colour, opacity);
}

// The first version's disk: one colour family, brighter inside, opaque, no Doppler shift.
vec4 plainDisk(vec3 P) {
    float r = length(P.xz);
    return vec4(1.2 * pow(uDiskRadii.x / r, 2.0) * vec3(1.0, 0.55, 0.22), 1.0);
}

// Stars about a pixel wide, one chance per cell of a grid around the direction d.
vec3 starField(vec3 d, float cellsPerUnit, float chance, float sizeFactor, float crowding) {
    vec3 home = floor(d * cellsPerUnit), light = vec3(0.0);
    float sharp = uStarAngle * sizeFactor;
    float spread = max(sharp, 0.55 * uPixelAngle);       // a coarse preview spreads stars over a pixel
    float keep = (sharp * sharp) / (spread * spread);     // and dims them by the same area
    for (int i = -1; i <= 1; ++i)
    for (int j = -1; j <= 1; ++j)
    for (int k = -1; k <= 1; ++k) {
        vec3 cell = home + vec3(i, j, k);
        if (random1(cell) > chance * crowding) continue;
        float cosAngle = dot(d, normalize(cell + random3(cell)));
        if (cosAngle < 0.999) continue;
        float angle2 = 2.0 * (1.0 - cosAngle);
        float strength = (0.006 + 1.4 * pow(random1(cell + 7.7), 24.0)) * keep; // mostly faint
        vec3 tint = planckColour(mix(3200.0, 12000.0, random1(cell + 3.3)));
        light += tint * strength * exp(-angle2 / (2.0 * spread * spread));
    }
    return light;
}

vec3 skyColour(vec3 d) {
    vec3 galacticPole = normalize(vec3(0.35, 1.0, 0.55));
    float band = exp(-pow(dot(d, galacticPole) / 0.2, 2.0));
    float glow = layeredNoise(3.5 * d);
    float dust = smoothstep(0.45, 0.75, layeredNoise(7.0 * d + 5.0));
    vec3 milkyWay = 0.05 * mix(vec3(0.25, 0.22, 0.35), vec3(0.75, 0.58, 0.42), glow) * band * glow * (1.0 - 0.7 * dust);
    return milkyWay + starField(d, 420.0, 0.0035, 0.8, 1.0 + 3.0 * band)
                    + 1.5 * starField(d, 110.0, 0.01, 1.2, 1.0);
}

float angularGrid(vec3 d) {
    const float spacing = 0.261799388; // 15 degrees
    vec2 angles = vec2(atan(d.z, d.x), asin(clamp(d.y, -1.0, 1.0)));
    vec2 offset = abs(fract(angles / spacing + 0.5) - 0.5) * spacing;
    offset.x *= max(length(d.xz), 0.05);
    float width = max(1.2 * uPixelAngle, 0.0008);
    return 1.0 - smoothstep(width, 2.0 * width, min(offset.x, offset.y));
}

#if defined(BAKE_SKY)
void main() {
    vec2 s = 2.0 * gl_FragCoord.xy / vec2(uImageSize) - 1.0;
    vec3 d = uFace == 0 ? vec3( 1.0, -s.y, -s.x) : uFace == 1 ? vec3(-1.0, -s.y,  s.x)
           : uFace == 2 ? vec3( s.x,  1.0,  s.y) : uFace == 3 ? vec3( s.x, -1.0, -s.y)
           : uFace == 4 ? vec3( s.x, -s.y,  1.0) :              vec3(-s.x, -s.y, -1.0);
    outColour = vec4(skyColour(normalize(d)), 1.0);
}
#elif defined(BAKE_GAS)
void main() {
    vec2 uv = gl_FragCoord.xy / vec2(uImageSize);
    outColour = vec4(gasPattern(TAU * uv.x, uLogSpan * uv.y), 0.0, 0.0, 1.0);
}
#else
void main() {
    vec2 pixel = floor(gl_FragCoord.xy);
    if (pixel.x >= float(uImageSize.x) || pixel.y >= float(uImageSize.y)) { outColour = vec4(0.0); return; }

    // the viewing direction through this point of the pixel (row 0 is the bottom)
    vec2 screen = 2.0 * (pixel + uSubpixel) / vec2(uImageSize) - 1.0;
    vec3 seen = normalize(uAhead + uTanHalfFov * (screen.x * uAspect * uRight + screen.y * uUp));

    vec3 x = uEye;
    vec3 v = coordinateDirection(uEye, seen);
    float gap = 1e9;
    bool bend = uStage >= 1;                   // stage 0: light goes straight, as in ordinary ray tracing
    bool sunsBend = uSunLensing && uStage >= 2;
    vec3 g = sunsBend ? sunGradient(x, gap) : vec3(0.0);

    vec3 gathered = vec3(0.0);  // light from the gas crossed so far
    float seeThrough = 1.0;     // fraction of whatever lies beyond that still shows
    bool fell = false, escaped = false;
    int body = -1;

    for (int i = 0; i < MAX_STEPS; ++i) {
        float r = length(x);
        if (r < 1.0 || (bend && r < 1.5 && dot(x, v) < 0.0)) { fell = true; break; } // inside 1.5 r_s, inward light cannot turn
        // steps of 1% of r near the hole, growing to 8% where space is nearly flat
        float ds = r * min(clamp(r / 400.0, 0.01, 0.08) * uStepScale, 0.15);
        if (sunsBend) ds = min(ds, max(0.3 * gap, 0.05)); // short steps where a sun bends the ray
        vec3 before = x;
        float dt = ds / length(v);
        if (!bend) {
            x += dt * v;
        } else if (sunsBend) {
            v = kick(v, g, 0.5 * dt);
            advance(x, v, dt);
            g = sunGradient(x, gap);
            v = kick(v, g, 0.5 * dt);
        } else {
            advance(x, v, dt);
        }

        // the first sun this step's straight segment enters, if any
        vec3 segment = x - before;
        float hitAt = 2.0;
        for (int b = 0; b < uBodyCount; ++b) {
            // skip suns this step cannot reach (a stretched sun is at most stretch * radius long)
            if (distance(before, uBodies[b].xyz) > uBodies[b].w * max(uBodyStretch[b].w, 1.0) + 1.1 * ds) continue;
            float t = entersBody(b, before, segment);
            if (t < hitAt) { hitAt = t; body = b; }
        }
        if (uDiskRadii.y > 0.0 && before.y * x.y < 0.0) {
            float t = before.y / (before.y - x.y);
            vec3 P = before + t * segment;
            float rp = length(P.xz);
            if (t < hitAt && rp >= uDiskRadii.x && rp <= uDiskRadii.y) {
                vec4 light = uStage >= 2 ? diskLight(P, normalize(segment)) : plainDisk(P);
                gathered += seeThrough * light.a * light.rgb;
                seeThrough *= 1.0 - light.a;
                if (seeThrough < 0.02) { body = -1; break; }
            }
        }
        if (body >= 0) { x = before + hitAt * segment; v = segment; break; }
        if (length(x) > EXIT_RADIUS) { escaped = true; break; }
    }

    if (uStyle == 2) { outColour = vec4(fell ? 1.0 : 0.0, 0.0, 0.0, 1.0); return; }
    float sunlit = 0.0;  // alpha: how much of this pixel is a sun, for the lens flare

    vec3 travel = normalize(v);
    vec3 colour = gathered;
    if (escaped) {
        vec3 background = uStyle == 0 ? vec3(0.0)
                        : textureLod(uSky, travel, max(log2(uPixelAngle / uSkyTexelAngle), 0.0)).rgb;
        if (uAngularGrid) background += angularGrid(travel) * (uStyle == 0 ? 0.3 : 0.055);
        colour += seeThrough * uSkyGain * background;
    } else if (body >= 0) {
        float facing = max(dot(bodyNormal(body, x), -travel), 0.0);
        colour += seeThrough * uBodyColours[body] * (0.4 + 0.6 * facing) * smoothstep(0.0, 0.3, facing);
        sunlit = seeThrough;
    }
    if (any(isnan(colour)) || any(isinf(colour))) colour = vec3(0.0);
    float offCentre = acos(clamp(dot(seen, uAhead), -1.0, 1.0));
    if (uRingAngle > 0.0 && abs(offCentre - uRingAngle) < 0.7 * uPixelAngle) colour = vec3(0.3, 2.0, 1.1);
    outColour = vec4(min(colour, vec3(30000.0)), sunlit);
}
#endif
