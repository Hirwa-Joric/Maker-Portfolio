#version 410 core
// The glow's passes. SHRINK averages the source under each texel of a smaller
// target (4 x 4 taps, any size ratio); SUNLIGHT does the same with the suns' light
// alone, for the lens flare. Otherwise: a 9-tap Gaussian blur along uStep, with
// taps two texels apart for a wider halo.
in vec2 vUV;
out vec4 outColour;
uniform sampler2D uSource;
uniform vec2 uTargetSize;
uniform vec2 uStep;

void main() {
#if defined(SHRINK) || defined(SUNLIGHT)
    vec3 sum = vec3(0.0);
    for (int y = 0; y < 4; ++y)
        for (int x = 0; x < 4; ++x) {
            vec4 texel = texture(uSource, (gl_FragCoord.xy - 0.5 + (vec2(x, y) + 0.5) / 4.0) / uTargetSize);
#if defined(SUNLIGHT)
            sum += texel.rgb * texel.a;   // only the light of the suns (alpha marks them)
#else
            sum += texel.rgb;
#endif
        }
    outColour = vec4(sum / 16.0, 1.0);
#else
    const float weight[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    vec2 uv = gl_FragCoord.xy / uTargetSize;
    vec3 sum = weight[0] * texture(uSource, uv).rgb;
    for (int i = 1; i < 5; ++i) {
        vec2 offset = float(2 * i) * uStep;
        sum += weight[i] * (texture(uSource, uv + offset).rgb + texture(uSource, uv - offset).rgb);
    }
    outColour = vec4(sum, 1.0);
#endif
}
