/*
 DripCraft - lightweight AI asset pipeline CLI
 Placeholder C module that provides simple subcommands for modeling, texturing, and animation.
 Designed to be invoked by Python/Blender integration as a deterministic, auditable step
 in the pipeline. Does not call external AI services directly; acts as a local adapter.

 Build (MinGW/GCC):
   gcc -O2 -std=c11 -o DripCraft.exe DripCraft.c

 Usage:
   DripCraft model <image.png> <out_dir>
   DripCraft texture <image.png> <out_dir>
   DripCraft animate <model_file> <out_dir>

 The program writes minimal artifact files into <out_dir> and prints a JSON status to stdout.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static int ensure_dir(const char *path) {
#ifdef _WIN32
    int rc = _mkdir(path);
    (void)rc;
#else
    int rc = mkdir(path, 0755);
    (void)rc;
#endif
    return 0;
}

static int copy_file(const char *src, const char *dst) {
    FILE *fs = fopen(src, "rb");
    if (!fs) return 1;
    FILE *fd = fopen(dst, "wb");
    if (!fd) { fclose(fs); return 2; }
    char buf[4096]; size_t n;
    while ((n = fread(buf, 1, sizeof(buf), fs)) > 0) fwrite(buf, 1, n, fd);
    fclose(fs); fclose(fd);
    return 0;
}

static void write_json(const char *outpath, const char *json) {
    FILE *f = fopen(outpath, "w");
    if (!f) return;
    fputs(json, f);
    fclose(f);
}

int cmd_model(const char *image, const char *outdir) {
    ensure_dir(outdir);
    /* fake model generation: copy image as "albedo.png" and create metadata */
    char dst_img[1024]; snprintf(dst_img, sizeof(dst_img), "%s/albedo.png", outdir);
    if (copy_file(image, dst_img) != 0) {
        printf("{\"status\":\"error\",\"msg\":\"failed to copy image\"}\n");
        return 3;
    }
    char meta[1024];
    snprintf(meta, sizeof(meta), "{\"status\":\"ok\",\"action\":\"model\",\"albedo\":\"%s\"}", dst_img);
    char meta_path[1024]; snprintf(meta_path, sizeof(meta_path), "%s/model.json", outdir);
    write_json(meta_path, meta);
    printf("%s\n", meta);
    return 0;
}

int cmd_texture(const char *image, const char *outdir) {
    ensure_dir(outdir);
    char dst_tex[1024]; snprintf(dst_tex, sizeof(dst_tex), "%s/texture.png", outdir);
    if (copy_file(image, dst_tex) != 0) {
        printf("{\"status\":\"error\",\"msg\":\"failed to copy texture image\"}\n");
        return 4;
    }
    char meta[1024]; snprintf(meta, sizeof(meta), "{\"status\":\"ok\",\"action\":\"texture\",\"texture\":\"%s\"}", dst_tex);
    char meta_path[1024]; snprintf(meta_path, sizeof(meta_path), "%s/texture.json", outdir);
    write_json(meta_path, meta);
    printf("%s\n", meta);
    return 0;
}

int cmd_animate(const char *model_file, const char *outdir) {
    ensure_dir(outdir);
    /* produce a small placeholder animation file */
    char anim_path[1024]; snprintf(anim_path, sizeof(anim_path), "%s/anim.txt", outdir);
    FILE *f = fopen(anim_path, "w");
    if (!f) { printf("{\"status\":\"error\",\"msg\":\"failed to write anim\"}\n"); return 5; }
    fprintf(f, "# placeholder animation for model %s\nframes: 10\n", model_file);
    fclose(f);
    char meta[1024]; snprintf(meta, sizeof(meta), "{\"status\":\"ok\",\"action\":\"animate\",\"anim\":\"%s\"}", anim_path);
    char meta_path[1024]; snprintf(meta_path, sizeof(meta_path), "%s/anim.json", outdir);
    write_json(meta_path, meta);
    printf("%s\n", meta);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <model|texture|animate> <input> <out_dir>\n", argv[0]);
        return 1;
    }
    const char *cmd = argv[1];
    const char *in = argv[2];
    const char *out = argv[3];
    if (strcmp(cmd, "model") == 0) return cmd_model(in, out);
    if (strcmp(cmd, "texture") == 0) return cmd_texture(in, out);
    if (strcmp(cmd, "animate") == 0) return cmd_animate(in, out);
    fprintf(stderr, "Unknown command: %s\n", cmd);
    return 2;
}
