#include "blastmonidz.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static float clampf(float value, float min_value, float max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static float luminance_of(unsigned char r, unsigned char g, unsigned char b) {
    return (0.2126f * (float)r + 0.7152f * (float)g + 0.0722f * (float)b) / 255.0f;
}

static int is_active_pixel(const unsigned char *pixel) {
    return pixel[3] > 24;
}

static void add_color_candidate(unsigned int counts[64], const unsigned char *pixel) {
    int rq = pixel[2] >> 6;
    int gq = pixel[1] >> 6;
    int bq = pixel[0] >> 6;
    counts[(rq << 4) | (gq << 2) | bq] += 1u;
}

static Color color_from_bucket(int bucket) {
    Color color;
    color.r = (unsigned char)(((bucket >> 4) & 0x3) * 85 + 42);
    color.g = (unsigned char)(((bucket >> 2) & 0x3) * 85 + 42);
    color.b = (unsigned char)((bucket & 0x3) * 85 + 42);
    color.a = 255;
    return color;
}

void blastmonidz_pixel_array_reset(BlastmonidzPixelArray *pixels) {
    if (!pixels) {
        return;
    }
    if (pixels->rgba) {
        free(pixels->rgba);
    }
    pixels->width = 0;
    pixels->height = 0;
    pixels->stride = 0;
    pixels->rgba = NULL;
}

void blastmonidz_asset_profile_reset(BlastmonidzAssetProfile *profile) {
    if (!profile) {
        return;
    }
    memset(profile, 0, sizeof(*profile));
}

int blastmonidz_analyze_pixel_array(const BlastmonidzPixelArray *pixels, BlastmonidzAssetProfile *profile) {
    int x;
    int y;
    int active_count = 0;
    int edge_count = 0;
    int curvature_count = 0;
    int bbox_left;
    int bbox_right;
    int bbox_top;
    int bbox_bottom;
    float luminance_sum = 0.0f;
    float luminance_sum_sq = 0.0f;
    float bottom_mass = 0.0f;
    float top_mass = 0.0f;
    float mirrored_vertical = 0.0f;
    float mirrored_horizontal = 0.0f;
    float modular_matches = 0.0f;
    float modular_total = 0.0f;
    unsigned int color_counts[64] = {0};
    int nonzero_colors = 0;
    int best_buckets[3] = {0, 0, 0};

    if (!pixels || !profile || !pixels->rgba || pixels->width <= 0 || pixels->height <= 0 || pixels->stride <= 0) {
        return 0;
    }

    blastmonidz_asset_profile_reset(profile);
    bbox_left = pixels->width;
    bbox_right = -1;
    bbox_top = pixels->height;
    bbox_bottom = -1;

    for (y = 0; y < pixels->height; ++y) {
        const unsigned char *row = pixels->rgba + y * pixels->stride;
        for (x = 0; x < pixels->width; ++x) {
            const unsigned char *pixel = row + x * 4;
            float luminance;
            if (!is_active_pixel(pixel)) {
                continue;
            }
            ++active_count;
            if (x < bbox_left) {
                bbox_left = x;
            }
            if (x > bbox_right) {
                bbox_right = x;
            }
            if (y < bbox_top) {
                bbox_top = y;
            }
            if (y > bbox_bottom) {
                bbox_bottom = y;
            }
            luminance = luminance_of(pixel[2], pixel[1], pixel[0]);
            luminance_sum += luminance;
            luminance_sum_sq += luminance * luminance;
            if (y >= pixels->height / 2) {
                bottom_mass += 1.0f;
            } else {
                top_mass += 1.0f;
            }
            add_color_candidate(color_counts, pixel);
        }
    }

    if (active_count == 0) {
        return 0;
    }

    for (y = bbox_top; y <= bbox_bottom; ++y) {
        for (x = bbox_left; x <= bbox_right; ++x) {
            const unsigned char *pixel = pixels->rgba + y * pixels->stride + x * 4;
            int active_neighbors = 0;
            int orthogonal_pairs = 0;
            int dx;
            int dy;
            if (!is_active_pixel(pixel)) {
                continue;
            }
            for (dy = -1; dy <= 1; ++dy) {
                for (dx = -1; dx <= 1; ++dx) {
                    int nx;
                    int ny;
                    const unsigned char *neighbor;
                    if (dx == 0 && dy == 0) {
                        continue;
                    }
                    nx = x + dx;
                    ny = y + dy;
                    if (nx < 0 || ny < 0 || nx >= pixels->width || ny >= pixels->height) {
                        continue;
                    }
                    neighbor = pixels->rgba + ny * pixels->stride + nx * 4;
                    if (is_active_pixel(neighbor)) {
                        ++active_neighbors;
                    }
                }
            }
            if (active_neighbors < 8) {
                ++edge_count;
            }
            if (x > 0 && x + 1 < pixels->width) {
                const unsigned char *left = pixels->rgba + y * pixels->stride + (x - 1) * 4;
                const unsigned char *right = pixels->rgba + y * pixels->stride + (x + 1) * 4;
                if (is_active_pixel(left) != is_active_pixel(right)) {
                    ++orthogonal_pairs;
                }
            }
            if (y > 0 && y + 1 < pixels->height) {
                const unsigned char *up = pixels->rgba + (y - 1) * pixels->stride + x * 4;
                const unsigned char *down = pixels->rgba + (y + 1) * pixels->stride + x * 4;
                if (is_active_pixel(up) != is_active_pixel(down)) {
                    ++orthogonal_pairs;
                }
            }
            if (orthogonal_pairs >= 2) {
                ++curvature_count;
            }
            if (x < pixels->width / 2) {
                const unsigned char *mirror = pixels->rgba + y * pixels->stride + (pixels->width - 1 - x) * 4;
                mirrored_vertical += (float)(is_active_pixel(pixel) == is_active_pixel(mirror));
            }
            if (y < pixels->height / 2) {
                const unsigned char *mirror = pixels->rgba + (pixels->height - 1 - y) * pixels->stride + x * 4;
                mirrored_horizontal += (float)(is_active_pixel(pixel) == is_active_pixel(mirror));
            }
            if (x + 1 < pixels->width) {
                const unsigned char *adjacent = pixels->rgba + y * pixels->stride + (x + 1) * 4;
                modular_matches += (float)(is_active_pixel(pixel) == is_active_pixel(adjacent));
                modular_total += 1.0f;
            }
        }
    }

    for (x = 0; x < 64; ++x) {
        if (color_counts[x] > 0u) {
            ++nonzero_colors;
        }
        if (color_counts[x] > color_counts[best_buckets[0]]) {
            best_buckets[2] = best_buckets[1];
            best_buckets[1] = best_buckets[0];
            best_buckets[0] = x;
        } else if (color_counts[x] > color_counts[best_buckets[1]]) {
            best_buckets[2] = best_buckets[1];
            best_buckets[1] = x;
        } else if (color_counts[x] > color_counts[best_buckets[2]]) {
            best_buckets[2] = x;
        }
    }

    profile->aspect_ratio = (float)(bbox_right - bbox_left + 1) / (float)((bbox_bottom - bbox_top + 1) > 0 ? (bbox_bottom - bbox_top + 1) : 1);
    profile->alpha_coverage = (float)active_count / (float)(pixels->width * pixels->height);
    profile->palette_depth = (float)nonzero_colors / 64.0f;
    profile->contrast = clampf((float)sqrt((luminance_sum_sq / active_count) - ((luminance_sum / active_count) * (luminance_sum / active_count))), 0.0f, 1.0f);
    profile->edge_density = (float)edge_count / (float)active_count;
    profile->curvature_bias = (float)curvature_count / (float)active_count;
    profile->symmetry_vertical = clampf(mirrored_vertical / ((pixels->width / 2) * (bbox_bottom - bbox_top + 1) + 1.0f), 0.0f, 1.0f);
    profile->symmetry_horizontal = clampf(mirrored_horizontal / ((pixels->height / 2) * (bbox_right - bbox_left + 1) + 1.0f), 0.0f, 1.0f);
    profile->modularity = clampf(modular_matches / (modular_total + 1.0f), 0.0f, 1.0f);
    profile->structural_mass = clampf(bottom_mass / (float)active_count, 0.0f, 1.0f);
    profile->foundation_bias = clampf((bottom_mass - top_mass) / (float)active_count * 0.5f + 0.5f, 0.0f, 1.0f);
    profile->hue_temperature = clampf((((float)profile->dominant_colors[0].r - (float)profile->dominant_colors[0].b) / 255.0f) * 0.5f + 0.5f, 0.0f, 1.0f);
    profile->silhouette_complexity = clampf(profile->edge_density * (0.5f + profile->curvature_bias), 0.0f, 1.0f);
    profile->proportional_tension = clampf(1.0f - (float)fabs(profile->aspect_ratio - 1.618f) / 1.618f, 0.0f, 1.0f);
    profile->dominant_colors[0] = color_from_bucket(best_buckets[0]);
    profile->dominant_colors[1] = color_from_bucket(best_buckets[1]);
    profile->dominant_colors[2] = color_from_bucket(best_buckets[2]);
    profile->hue_temperature = clampf((((float)profile->dominant_colors[0].r - (float)profile->dominant_colors[0].b) / 255.0f) * 0.5f + 0.5f, 0.0f, 1.0f);
    return 1;
}

void blastmonidz_design_organism_reset(BlastmonidzDesignOrganism *organism) {
    if (!organism) {
        return;
    }
    memset(organism, 0, sizeof(*organism));
}

void blastmonidz_design_organism_absorb(BlastmonidzDesignOrganism *organism, const BlastmonidzAssetProfile *profile) {
    int i;
    if (!organism || !profile) {
        return;
    }
    organism->assets_analyzed += 1;
    organism->mean_aspect_ratio += profile->aspect_ratio;
    organism->mean_alpha_coverage += profile->alpha_coverage;
    organism->mean_palette_depth += profile->palette_depth;
    organism->mean_contrast += profile->contrast;
    organism->mean_edge_density += profile->edge_density;
    organism->mean_curvature_bias += profile->curvature_bias;
    organism->mean_symmetry += (profile->symmetry_vertical + profile->symmetry_horizontal) * 0.5f;
    organism->mean_modularity += profile->modularity;
    organism->mean_structural_mass += profile->structural_mass;
    organism->mean_foundation_bias += profile->foundation_bias;
    organism->mean_hue_temperature += profile->hue_temperature;
    organism->mean_silhouette_complexity += profile->silhouette_complexity;
    organism->mean_proportional_tension += profile->proportional_tension;
    for (i = 0; i < 3; ++i) {
        organism->dominant_colors[i].r = (unsigned char)(organism->dominant_colors[i].r + profile->dominant_colors[i].r / 4);
        organism->dominant_colors[i].g = (unsigned char)(organism->dominant_colors[i].g + profile->dominant_colors[i].g / 4);
        organism->dominant_colors[i].b = (unsigned char)(organism->dominant_colors[i].b + profile->dominant_colors[i].b / 4);
        organism->dominant_colors[i].a = 255;
    }
}

void blastmonidz_design_organism_finalize(BlastmonidzDesignOrganism *organism) {
    float count;
    if (!organism || organism->assets_analyzed <= 0) {
        return;
    }
    count = (float)organism->assets_analyzed;
    organism->mean_aspect_ratio /= count;
    organism->mean_alpha_coverage /= count;
    organism->mean_palette_depth /= count;
    organism->mean_contrast /= count;
    organism->mean_edge_density /= count;
    organism->mean_curvature_bias /= count;
    organism->mean_symmetry /= count;
    organism->mean_modularity /= count;
    organism->mean_structural_mass /= count;
    organism->mean_foundation_bias /= count;
    organism->mean_hue_temperature /= count;
    organism->mean_silhouette_complexity /= count;
    organism->mean_proportional_tension /= count;
    organism->animation_elasticity = clampf((organism->mean_curvature_bias + organism->mean_silhouette_complexity + organism->mean_palette_depth) / 3.0f, 0.0f, 1.0f);
    organism->environmental_mutation_bias = clampf((organism->mean_palette_depth + organism->mean_contrast + organism->mean_hue_temperature) / 3.0f, 0.0f, 1.0f);
    organism->structural_discipline = clampf((organism->mean_modularity + organism->mean_foundation_bias + organism->mean_symmetry) / 3.0f, 0.0f, 1.0f);
    organism->ornamental_bias = clampf((organism->mean_curvature_bias + organism->mean_edge_density + organism->mean_proportional_tension) / 3.0f, 0.0f, 1.0f);
    snprintf(organism->theory_summary, sizeof(organism->theory_summary),
        "The archive reads as a compact construction grammar: moderate chromatic depth, high edge-led silhouette control, and a foundation-heavy massing strategy. In art-theory terms it privileges legible figure-ground contrast over painterly ambiguity; in architectural terms it behaves like prefabricated modular assembly with ornament applied at the contour rather than at the structural core; in construction terms it repeats reliable load-bearing motifs and then lets curvature and palette accents carry identity.");
}

void blastmonidz_describe_asset_profile(const BlastmonidzAssetProfile *profile, char *buffer, int buffer_size) {
    if (!profile || !buffer || buffer_size <= 0) {
        return;
    }
    snprintf(buffer, (size_t)buffer_size,
        "ratio %.2f | cover %.2f | palette %.2f | contrast %.2f | edge %.2f | curve %.2f | sym %.2f/%.2f | modular %.2f | mass %.2f | tension %.2f",
        profile->aspect_ratio,
        profile->alpha_coverage,
        profile->palette_depth,
        profile->contrast,
        profile->edge_density,
        profile->curvature_bias,
        profile->symmetry_vertical,
        profile->symmetry_horizontal,
        profile->modularity,
        profile->structural_mass,
        profile->proportional_tension);
}

void blastmonidz_describe_design_organism(const BlastmonidzDesignOrganism *organism, char *buffer, int buffer_size) {
    if (!organism || !buffer || buffer_size <= 0) {
        return;
    }
    snprintf(buffer, (size_t)buffer_size,
        "assets %d | elastic %.2f | env %.2f | structure %.2f | ornament %.2f | palette %.2f | symmetry %.2f",
        organism->assets_analyzed,
        organism->animation_elasticity,
        organism->environmental_mutation_bias,
        organism->structural_discipline,
        organism->ornamental_bias,
        organism->mean_palette_depth,
        organism->mean_symmetry);
}