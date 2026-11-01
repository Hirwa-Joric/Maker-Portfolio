#version 410 core
// Lens flare from the suns. This imitates a camera lens, not anything in space:
// light reflected between lens elements makes faint coloured ghosts on the line
// through the image centre, and the aperture's edges make six-pointed spikes.
// It is built from the traced suns' light, so a sun hidden behind the hole or the
// disk makes no flare.
in vec2 vUV;
out vec4 outColour;
uniform sampler2D uSunLight;   // the suns' light alone, at 1/4 of the image size
uniform float uAspect;

vec3 sunLight(vec2 uv) {
    vec2 inside = step(vec2(0.0), uv) * step(uv, vec2(1.0));
    return texture(uSunLight, uv).rgb * inside.x * inside.y;
}

void main() {
    vec3 sum = vec3(0.0);
    // ghosts: a sun at s throws an image of itself to centre + (centre - s) * scale
    const float scale[4] = float[](-0.35, 0.5, 0.95, 1.6);
    const vec3 tint[4] = vec3[](vec3(0.55, 0.8, 1.0), vec3(1.0, 0.7, 0.4),
                                vec3(0.6, 1.0, 0.75), vec3(0.85, 0.6, 1.0));
    for (int i = 0; i < 4; ++i) {
        vec2 source = vec2(0.5) + (vec2(0.5) - vUV) / scale[i];
        sum += tint[i] * sunLight(source) * 0.004;
    }
    // spikes: light from a sun further along each of six directions
    for (int d = 0; d < 6; ++d) {
        float angle = 0.2618 + 1.0472 * float(d);
        vec2 step_ = 0.005 * vec2(cos(angle) / uAspect, sin(angle));
        for (int k = 1; k <= 20; ++k)
            sum += sunLight(vUV + step_ * float(k)) * (0.05 * exp(-0.18 * float(k)));
    }
    outColour = vec4(sum, 1.0);
}
