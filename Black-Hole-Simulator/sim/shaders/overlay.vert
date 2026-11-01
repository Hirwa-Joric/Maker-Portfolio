#version 410 core
// Lines and glowing points drawn over the traced image (not bent by the hole).
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aColour;
uniform mat4  uViewProjection;
uniform vec3  uEye;
uniform float uShadowAngle;   // POINTS: hide points behind the shadow
uniform float uPointSize;
uniform vec2  uFade;          // LINES: fade out between these distances from the axis
out vec3 vColour;
out float vFade;
void main() {
    gl_Position = uViewProjection * vec4(aPosition, 1.0);
    vColour = aColour;
    vFade = 1.0 - smoothstep(uFade.x, uFade.y, length(aPosition.xz));
#if defined(POINTS)
    vec3 toPoint = aPosition - uEye;
    bool hidden = length(toPoint) > length(uEye)
               && acos(clamp(dot(normalize(toPoint), normalize(-uEye)), -1.0, 1.0)) < uShadowAngle;
    if (hidden) vColour = vec3(0.0);
    gl_PointSize = uPointSize;
#endif
}
