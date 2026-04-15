#include <stdint.h>

int hope_depth_strength_i32(int brightness, int proximity, int eye_open, int motion, int preset_bias);
int hope_depth_project_x_i32(int x, int scene_center, int band_depth, int strength, int focus_px);
int hope_depth_project_y_i32(int y, int scene_center, int band_depth, int strength, int focus_px);

static int clamp_i32(int value, int low, int high)
{
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}

__declspec(dllexport) int hope_depth_strength_bridge(int base_strength, int hope_drive, int camera_drive, int comfort)
{
    int strength_term = clamp_i32(base_strength, 0, 1000) / 4;
    int hope_term = clamp_i32(hope_drive, 0, 1000) / 4;
    int camera_term = clamp_i32(camera_drive, 0, 1000) / 4;
    int comfort_term = clamp_i32(comfort, 0, 1000) / 4;
    int preset_term = clamp_i32(base_strength, 0, 1000) / 8;
    int mixed = hope_depth_strength_i32(strength_term, hope_term, camera_term, comfort_term, preset_term);
    return (mixed * 1000) / 255;
}

__declspec(dllexport) int hope_depth_project_x_bridge(int x, int scene_center, int band_depth, int strength, int focus_px)
{
    int band_term = clamp_i32(band_depth, 0, 1000) * 128 / 1000;
    int strength_term = clamp_i32(strength, 0, 1000) * 128 / 1000;
    int focus_term = clamp_i32(focus_px, -512, 512);
    return hope_depth_project_x_i32(x, scene_center, band_term, strength_term, focus_term);
}

__declspec(dllexport) int hope_depth_project_y_bridge(int y, int scene_center, int band_depth, int strength, int focus_px)
{
    int band_term = clamp_i32(band_depth, 0, 1000) * 128 / 1000;
    int strength_term = clamp_i32(strength, 0, 1000) * 128 / 1000;
    int focus_term = clamp_i32(focus_px, -384, 384);
    return hope_depth_project_y_i32(y, scene_center, band_term, strength_term, focus_term);
}
