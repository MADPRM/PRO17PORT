// SPDX-FileCopyrightText: Copyright 2024 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#version 450

layout (location = 0) in vec2 uv;
layout (location = 0) out vec4 color;

layout (binding = 0) uniform sampler2D texSampler;

layout (push_constant) uniform settings {
    float gamma;
    bool hdr;
    bool srgb_input;
    uint aa_mode;
    vec4 picture; // spartanport: x0, y0, x1, y1 of the part shown; the rest is black (cutscene bars)
} pp;

const float cutoff = 0.0031308, a = 1.055, b = 0.055, d = 12.92;
vec3 gamma(vec3 rgb) {
    return mix(
        a * pow(rgb, vec3(1.0 / (2.4 + 1.0 - pp.gamma))) - b,
        d * rgb / pp.gamma,
        lessThan(rgb, vec3(cutoff))
    );
}

// Exact inverse of gamma() at unit gamma, for buffers that are sRGB encoded but must be sampled
// through a UNORM view because Vulkan has no sRGB variant of the 10-bit format.
vec3 degamma(vec3 rgb) {
    return mix(
        pow(max(rgb + b, 0.0) / a, vec3(2.4)),
        rgb / d,
        lessThan(rgb, vec3(d * cutoff))
    );
}

float luma(vec3 rgb) {
    return dot(sqrt(max(rgb, vec3(0.0))), vec3(0.299, 0.587, 0.114));
}

vec4 apply_edge_aa(vec2 pos, uint mode) {
    vec2 rcp_frame = 1.0 / vec2(textureSize(texSampler, 0));
    vec4 rgbyM = texture(texSampler, pos);
    float lumaM = luma(rgbyM.rgb);
    float lumaN = luma(textureOffset(texSampler, pos, ivec2( 0, -1)).rgb);
    float lumaS = luma(textureOffset(texSampler, pos, ivec2( 0,  1)).rgb);
    float lumaW = luma(textureOffset(texSampler, pos, ivec2(-1,  0)).rgb);
    float lumaE = luma(textureOffset(texSampler, pos, ivec2( 1,  0)).rgb);

    float rangeMin = min(lumaM, min(min(lumaN, lumaS), min(lumaW, lumaE)));
    float rangeMax = max(lumaM, max(max(lumaN, lumaS), max(lumaW, lumaE)));
    float range = rangeMax - rangeMin;
    if (range < max(0.025, rangeMax * 0.0625)) {
        return rgbyM;
    }

    float lumaNW = luma(textureOffset(texSampler, pos, ivec2(-1, -1)).rgb);
    float lumaNE = luma(textureOffset(texSampler, pos, ivec2( 1, -1)).rgb);
    float lumaSW = luma(textureOffset(texSampler, pos, ivec2(-1,  1)).rgb);
    float lumaSE = luma(textureOffset(texSampler, pos, ivec2( 1,  1)).rgb);

    float lumaNS = lumaN + lumaS;
    float lumaWE = lumaW + lumaE;
    float subpixNSWE = lumaNS + lumaWE;
    float lumaNWSW = lumaNW + lumaSW;
    float lumaNESE = lumaNE + lumaSE;
    float lumaNWNE = lumaNW + lumaNE;
    float lumaSWSE = lumaSW + lumaSE;

    float edgeHorz = abs(-2.0 * lumaW + lumaNWSW) + abs(-2.0 * lumaM + lumaNS) * 2.0 + abs(-2.0 * lumaE + lumaNESE);
    float edgeVert = abs(-2.0 * lumaN + lumaNWNE) + abs(-2.0 * lumaM + lumaWE) * 2.0 + abs(-2.0 * lumaS + lumaSWSE);
    bool horzSpan = edgeHorz >= edgeVert;

    float lengthSign = horzSpan ? rcp_frame.y : rcp_frame.x;
    float luma1 = horzSpan ? lumaN : lumaW;
    float luma2 = horzSpan ? lumaS : lumaE;
    float gradient1 = luma1 - lumaM;
    float gradient2 = luma2 - lumaM;
    bool is1Steepest = abs(gradient1) >= abs(gradient2);
    float gradientScaled = 0.25 * max(abs(gradient1), abs(gradient2));

    if (is1Steepest) {
        lengthSign = -lengthSign;
    }
    float lumaLocalAverage = 0.5 * ((is1Steepest ? luma1 : luma2) + lumaM);

    vec2 posB = pos;
    if (horzSpan) {
        posB.y += lengthSign * 0.5;
    } else {
        posB.x += lengthSign * 0.5;
    }

    vec2 offNP = horzSpan ? vec2(rcp_frame.x, 0.0) : vec2(0.0, rcp_frame.y);
    vec2 posN = posB - offNP;
    vec2 posP = posB + offNP;
    float lumaEndN = luma(texture(texSampler, posN).rgb) - lumaLocalAverage;
    float lumaEndP = luma(texture(texSampler, posP).rgb) - lumaLocalAverage;
    bool doneN = abs(lumaEndN) >= gradientScaled;
    bool doneP = abs(lumaEndP) >= gradientScaled;

    const float steps[11] = float[11](1.0, 1.0, 1.0, 1.0, 1.5, 2.0, 2.0, 2.0, 2.0, 4.0, 8.0);
    for (int i = 0; i < 11 && (!doneN || !doneP); ++i) {
        if (!doneN) {
            posN -= offNP * steps[i];
            lumaEndN = luma(texture(texSampler, posN).rgb) - lumaLocalAverage;
            doneN = abs(lumaEndN) >= gradientScaled;
        }
        if (!doneP) {
            posP += offNP * steps[i];
            lumaEndP = luma(texture(texSampler, posP).rgb) - lumaLocalAverage;
            doneP = abs(lumaEndP) >= gradientScaled;
        }
    }

    float dstN = horzSpan ? (pos.x - posN.x) : (pos.y - posN.y);
    float dstP = horzSpan ? (posP.x - pos.x) : (posP.y - pos.y);
    bool goodSpan = ((dstN < dstP) ? (lumaEndN < 0.0) : (lumaEndP < 0.0)) != (lumaM - lumaLocalAverage < 0.0);
    float spanLength = dstP + dstN;
    float pixelOffset = (-min(dstN, dstP) / max(spanLength, 1e-6)) + 0.5;
    float pixelOffsetGood = goodSpan ? pixelOffset : 0.0;

    float subpix = clamp(abs((subpixNSWE * 2.0 + lumaNWSW + lumaNESE) / 12.0 - lumaM) / range, 0.0, 1.0);
    float subpixQuality = (mode == 1u) ? 0.85 : 0.75;
    float subpixOffset = (-2.0 * subpix + 3.0) * subpix * subpix;
    subpixOffset = subpixOffset * subpixOffset * subpixQuality;

    float finalOffset = max(pixelOffsetGood, subpixOffset);
    vec2 finalUv = pos;
    if (horzSpan) {
        finalUv.y += finalOffset * lengthSign;
    } else {
        finalUv.x += finalOffset * lengthSign;
    }
    return vec4(texture(texSampler, finalUv).rgb, rgbyM.a);
}

void main() {
    if (any(lessThan(uv, pp.picture.xy)) || any(greaterThan(uv, pp.picture.zw))) {
        color = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }
    vec4 color_linear = (pp.aa_mode != 0u) ? apply_edge_aa(uv, pp.aa_mode) : texture(texSampler, uv);
    if (pp.hdr) {
        color = color_linear;
    } else {
        if (pp.srgb_input) color_linear.rgb = degamma(color_linear.rgb);
        color = vec4(gamma(color_linear.rgb), color_linear.a);
    }
}
