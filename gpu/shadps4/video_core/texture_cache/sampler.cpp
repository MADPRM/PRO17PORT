// SPDX-FileCopyrightText: Copyright 2024 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include <algorithm>
#include "spartanport_settings.h"
#include "video_core/renderer_vulkan/liverpool_to_vk.h"
#include "video_core/renderer_vulkan/vk_instance.h"
#include "video_core/texture_cache/sampler.h"

namespace VideoCore {

Sampler::Sampler(const Vulkan::Instance& instance, const AmdGpu::Sampler& sampler,
                 const AmdGpu::BorderColorBuffer border_color_base, const bool is_depth, float extra_lod_bias) {
    using namespace Vulkan;
    const bool game_anisotropy = AmdGpu::IsAnisoFilter(sampler.xy_mag_filter) ||
                                 AmdGpu::IsAnisoFilter(sampler.xy_min_filter);
    // spartanport: the menu's anisotropic filtering, on filtered and mipmapped surface textures
    // (not on point-sampled lookups, clamped render targets/LUTs, unmipmapped images or depth compares).
    const int forced = SpartanSettings::Get().startup_anisotropy;
    const bool repeating_uv =
        (sampler.clamp_x == AmdGpu::ClampMode::Wrap || sampler.clamp_x == AmdGpu::ClampMode::Mirror) &&
        (sampler.clamp_y == AmdGpu::ClampMode::Wrap || sampler.clamp_y == AmdGpu::ClampMode::Mirror);
    const bool has_mip_chain =
        sampler.mip_filter == AmdGpu::MipFilter::Linear && sampler.MaxLod() >= 4.0f &&
        sampler.MaxLod() > sampler.MinLod() + 1.0f;
    const bool force_anisotropy = forced > 1 && !is_depth && !sampler.force_unnormalized &&
                                  sampler.xy_min_filter != AmdGpu::Filter::Point &&
                                  sampler.xy_mag_filter != AmdGpu::Filter::Point &&
                                  (game_anisotropy || (repeating_uv && has_mip_chain));
    const bool anisotropy_enable =
        instance.IsAnisotropicFilteringSupported() && (game_anisotropy || force_anisotropy);
    const float requested = std::max(game_anisotropy ? sampler.MaxAniso() : 1.0f,
                                     force_anisotropy ? float(forced) : 1.0f);
    const float max_anisotropy =
        anisotropy_enable ? std::clamp(requested, 1.0f, instance.MaxSamplerAnisotropy()) : 1.0f;
    auto border_color = LiverpoolToVK::BorderColor(sampler.border_color_type);
    if (border_color == vk::BorderColor::eFloatCustomEXT &&
        !instance.IsCustomBorderColorSupported()) {
        LOG_WARNING(Render_Vulkan, "Custom border color is not supported, falling back to black");
        border_color = vk::BorderColor::eFloatOpaqueBlack;
    }

    const auto custom_color = [&]() -> std::optional<vk::SamplerCustomBorderColorCreateInfoEXT> {
        if (border_color == vk::BorderColor::eFloatCustomEXT) {
            const auto border_color_index = sampler.border_color_ptr.Value();
            const auto border_color_buffer = border_color_base.Address<std::array<float, 4>*>();
            const auto custom_border_color_array = border_color_buffer[border_color_index];

            const vk::SamplerCustomBorderColorCreateInfoEXT ret{
                .customBorderColor =
                    vk::ClearColorValue{
                        .float32 = custom_border_color_array,
                    },
                .format = vk::Format::eR32G32B32A32Sfloat,
            };
            return ret;
        } else {
            return std::nullopt;
        }
    }();

    const vk::SamplerCreateInfo sampler_ci = {
        .pNext = custom_color ? &*custom_color : nullptr,
        .magFilter = LiverpoolToVK::Filter(sampler.xy_mag_filter),
        .minFilter = LiverpoolToVK::Filter(sampler.xy_min_filter),
        .mipmapMode = LiverpoolToVK::MipFilter(sampler.mip_filter),
        .addressModeU = LiverpoolToVK::ClampMode(sampler.clamp_x),
        .addressModeV = LiverpoolToVK::ClampMode(sampler.clamp_y),
        .addressModeW = LiverpoolToVK::ClampMode(sampler.clamp_z),
        .mipLodBias = std::clamp(sampler.LodBias() + extra_lod_bias, -instance.MaxSamplerLodBias(),
                                 instance.MaxSamplerLodBias()),
        .anisotropyEnable = anisotropy_enable,
        .maxAnisotropy = max_anisotropy,
        // GCN compares per instruction; a plain read of a compare sampler is undefined in Vulkan.
        .compareEnable = is_depth,
        .compareOp = LiverpoolToVK::DepthCompare(sampler.depth_compare_func),
        .minLod = sampler.MinLod(),
        .maxLod = sampler.MaxLod(),
        .borderColor = border_color,
        .unnormalizedCoordinates = false, // Handled in shader due to Vulkan limitations.
    };
    auto [sampler_result, smplr] = instance.GetDevice().createSamplerUnique(sampler_ci);
    ASSERT_MSG(sampler_result == vk::Result::eSuccess, "Failed to create sampler: {}",
               vk::to_string(sampler_result));
    handle = std::move(smplr);
}

Sampler::~Sampler() = default;

} // namespace VideoCore
