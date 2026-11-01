#version 410 core
// Shows the traced image: upscales a small preview smoothly, adds the soft glow and
// the lens flare, then maps the bright linear light to the screen with a filmic curve.
in vec2 vUV;
out vec4 outColour;
uniform sampler2D uImage;
uniform sampler2D uGlowNear;   // averaged down 4x and blurred
uniform sampler2D uGlowFar;    // averaged down 16x and blurred: the wide halo
uniform sampler2D uFlare;      // the suns' lens flare (flare.frag)
uniform float uFlareStrength;
uniform float uScreenWidth;
uniform float uExposure;
uniform float uGlow;

// Catmull-Rom upscaling folded into nine bilinear taps, so a small preview
// stretched over the window stays crisp.
vec3 catmullRom(vec2 uv) {
    vec2 size = vec2(textureSize(uImage, 0));
    vec2 p = uv * size;
    vec2 centre = floor(p - 0.5) + 0.5;
    vec2 f = p - centre;
    vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f));
    vec2 w1 = 1.0 + f * f * (-2.5 + 1.5 * f);
    vec2 w2 = f * (0.5 + f * (2.0 - 1.5 * f));
    vec2 w3 = f * f * (-0.5 + 0.5 * f);
    vec2 wMid = w1 + w2;
    vec2 tA = (centre - 1.0) / size, tB = (centre + w2 / wMid) / size, tC = (centre + 2.0) / size;
    vec2 tx[3] = vec2[](vec2(tA.x, w0.x), vec2(tB.x, wMid.x), vec2(tC.x, w3.x));
    vec2 ty[3] = vec2[](vec2(tA.y, w0.y), vec2(tB.y, wMid.y), vec2(tC.y, w3.y));
    vec3 sum = vec3(0.0);
    for (int j = 0; j < 3; ++j)
        for (int i = 0; i < 3; ++i)
            sum += texture(uImage, vec2(tx[i].x, ty[j].x)).rgb * tx[i].y * ty[j].y;
    return max(sum, vec3(0.0));
}

// John Hable's filmic curve (shoulder 0.15, linear 0.5, angle 0.1, toe 0.2, 0.02/0.3).
vec3 hable(vec3 x) {
    const float A = 0.15, B = 0.50, C = 0.10, D = 0.20, E = 0.02, F = 0.30;
    return (x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F) - E / F;
}

void main() {
    bool small = float(textureSize(uImage, 0).x) < 0.95 * uScreenWidth;
    vec3 c = small ? catmullRom(vUV) : texture(uImage, vUV).rgb;
    vec3 halo = 0.55 * texture(uGlowNear, vUV).rgb + 0.45 * texture(uGlowFar, vUV).rgb;
    c = (c + 0.45 * uGlow * halo + uFlareStrength * texture(uFlare, vUV).rgb) * uExposure;
    vec3 mapped = clamp(hable(2.0 * max(c, vec3(0.0))) / hable(vec3(11.2)), 0.0, 1.0);
    outColour = vec4(pow(mapped, vec3(1.0 / 2.2)), 1.0);
}
