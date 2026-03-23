// ...existing code...
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>

#ifdef _WIN32
#include <direct.h>
#define SEP "\\"
#else
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#define SEP "/"
#endif

#define MAX_CMD 4096
#define MAX_PATH 1024

const char *image_exts[] = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"};
const int num_image_exts = 6;
const char *video_exts[] = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"};
const int num_video_exts = 6;

int ends_with_ci(const char *s, const char *ext) {
    if (!s || !ext) return 0;
    size_t ls = strlen(s), le = strlen(ext);
    if (le > ls) return 0;
    const char *p = s + ls - le;
    for (size_t i = 0; i < le; ++i) {
        char a = p[i], b = ext[i];
        if (a >= 'A' && a <= 'Z') a += 'a' - 'A';
        if (b >= 'A' && b <= 'Z') b += 'a' - 'A';
        if (a != b) return 0;
    }
    return 1;
}

int is_image_file(const char *name) {
    for (int i=0;i<num_image_exts;i++) if (ends_with_ci(name, image_exts[i])) return 1;
    return 0;
}
int is_video_file(const char *name) {
    for (int i=0;i<num_video_exts;i++) if (ends_with_ci(name, video_exts[i])) return 1;
    return 0;
}

void ensure_dir(const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) {
#ifdef _WIN32
        _mkdir(path);
#else
        mkdir(path, 0755);
#endif
    }
}

int run_ffmpeg_extract_frames(const char *video, const char *outdir) {
    char cmd[MAX_CMD];
    ensure_dir(outdir);
    snprintf(cmd, sizeof(cmd),
        "ffmpeg -y -i \"%s\" -vsync 0 \"%s%frame_%%05d.png\" >nul 2>nul",
        video, outdir SEP);
    // fallback correct snprintf usage:
    // but to avoid platform formatting issues, build safer:
    snprintf(cmd, sizeof(cmd),
        "ffmpeg -y -i \"%s\" -vsync 0 \"%s%sframe_%%05d.png\" >nul 2>nul",
        video, outdir, SEP);
    return system(cmd);
}

/* Write Python depth estimator using spatial-distinguishment sampling of 32 neighbors.
   No scipy required; uses Pillow + numpy. */
int write_python_depth_script(const char *script_path) {
    FILE *f = fopen(script_path, "w");
    if (!f) return 0;
    fprintf(f,
"import sys, os\n"
"from PIL import Image\n"
"import numpy as np\n"
"\n"
"def luminance(arr):\n"
"    return (0.299*arr[...,0] + 0.587*arr[...,1] + 0.114*arr[...,2]).astype(np.float32)\n"
"\n"
"def sample_ring_neighbors(L, radius, samples=32):\n"
"    H,W = L.shape\n"
"    out = np.zeros((H,W,samples), dtype=np.float32)\n"
"    angles = np.linspace(0, 2*np.pi, samples, endpoint=False)\n"
"    for i,ang in enumerate(angles):\n"
"        dx = int(round(radius*np.cos(ang)))\n"
"        dy = int(round(radius*np.sin(ang)))\n" 
"        shifted = np.roll(np.roll(L, dy, axis=0), dx, axis=1)\n"
"        out[...,i] = shifted\n"
"    return out\n"
"\n"
"def compute_spatial_depth(arr):\n"
"    # arr: HxWx3 uint8\n"
"    H,W,_ = arr.shape\n"
"    L = luminance(arr)\n"
"    # sample multiple radii to capture local neighborhood (approx 32 neighbors total)\n"
"    neigh = sample_ring_neighbors(L, 1, samples=16)\n"
"    neigh2 = sample_ring_neighbors(L, 3, samples=16)\n" 
"    neigh_all = np.concatenate([neigh, neigh2], axis=2)\n"
"    neigh_mean = neigh_all.mean(axis=2)\n" 
"    neigh_std = neigh_all.std(axis=2)\n"
"    # local gradient via simple finite differences\n"
"    gx = np.abs(np.roll(L, -1, axis=1) - np.roll(L, 1, axis=1))\n"
"    gy = np.abs(np.roll(L, -1, axis=0) - np.roll(L, 1, axis=0))\n"
"    grad = np.hypot(gx, gy)\n"
"    # circularity / focality measure: variance across ring neighbors\n"
"    circ = neigh_std\n" 
"    # Heuristic: darker than neighbors -> farther (positive), high gradient -> nearer (negative), high circularity -> nearer\n"
"    depth = 0.9*(neigh_mean - L) - 1.2*(grad/(grad.max()+1e-9)) - 0.8*(circ/(circ.max()+1e-9))\n"
"    # combine and normalize\n"
"    depth = depth - depth.min()\n"
"    depth = depth / (depth.max()+1e-9)\n"
"    # invert so brighter => near (0..1 mapped to Z closer)\n"
"    depth = 1.0 - depth\n"
"    return (depth*255).astype(np.uint8)\n"
"\n"
"def process_image(in_path, out_path):\n"
"    img = Image.open(in_path).convert('RGB')\n"
"    arr = np.array(img, dtype=np.uint8)\n"
"    depth = compute_spatial_depth(arr)\n"
"    depth_img = Image.fromarray(depth)\n"
"    depth_img.save(out_path)\n" 
"    print('WROTE', out_path)\n"
"\n"
"def process_dir(src, dst):\n"
"    if not os.path.exists(dst): os.makedirs(dst)\n"
"    files = sorted([f for f in os.listdir(src) if f.lower().endswith(('.png','.jpg','.jpeg'))])\n"
"    for f in files:\n"
"        in_p = os.path.join(src,f)\n"
"        out_p = os.path.join(dst, os.path.splitext(f)[0] + '_depth.png')\n"
"        process_image(in_p, out_p)\n"
"\n"
"def main():\n"
"    if len(sys.argv) < 3:\n"
"        print('Usage: python img_to_depth.py <in_path> <out_path_or_outdir>')\n"
"        return\n"
"    src = sys.argv[1]\n"
"    dst = sys.argv[2]\n"
"    if os.path.isdir(src):\n"
"        process_dir(src, dst)\n"
"    else:\n"
"        process_image(src, dst)\n"
"\n"
"if __name__ == '__main__':\n"
"    main()\n"
    );
    fclose(f);
    return 1;
}

/* Blender script: build explicit mesh from color image + depth map (per-image or per-frame sequence).
   Downsamples mesh if image large. */
int write_blender_script(const char *script_path) {
    FILE *f = fopen(script_path, "w");
    if (!f) return 0;
    fprintf(f,
"import bpy, sys, os\n"
"import bmesh\n"
"from mathutils import Vector\n"
"argv = sys.argv\n"
"if '--' in argv:\n"
"    idx = argv.index('--')\n"
"    color_path = argv[idx+1]\n"
"    depth_path = argv[idx+2]\n" 
"    outblend = argv[idx+3]\n"
"else:\n"
"    print('Expected: -- <color> <depth_or_depth_dir> <outblend>'); sys.exit(1)\n"
"\n"
"bpy.ops.wm.read_factory_settings(use_empty=True)\n"
"depth_is_dir = os.path.isdir(depth_path)\n"
"if depth_is_dir:\n"
"    depth_files = sorted([os.path.join(depth_path,f) for f in os.listdir(depth_path) if f.lower().endswith('_depth.png')])\n" 
"    if not depth_files:\n"
"        print('No depth files found'); sys.exit(1)\n"
"    depth_img_path = depth_files[0]\n"
"else:\n"
"    depth_img_path = depth_path\n"
"\n"
"# load color image for texture\n"
"color_img = bpy.data.images.load(color_path)\n"
"depth_img = bpy.data.images.load(depth_img_path)\n"
"\n"
"# use PIL within blender for pixel read if available, fallback to bpy image pixels\n"
"try:\n"
"    from PIL import Image\n"
"    pil_color = Image.open(color_path).convert('RGB')\n" 
"    pil_depth = Image.open(depth_img_path).convert('L')\n" 
"    W, H = pil_color.size\n" 
"    color_pixels = pil_color.load()\n" 
"    depth_pixels = pil_depth.load()\n    use_pil = True\n" 
"except Exception:\n"
"    use_pil = False\n" 
"    W = color_img.size[0]\n"
"    H = color_img.size[1]\n"
"\n"
"# downsample factor to limit verts\n"
"max_dim = 256\n" 
"step = max(1, max(W, H) // max_dim)\n"
"nx = (W + step - 1)//step\n"
"ny = (H + step - 1)//step\n"
"\n"
"mesh = bpy.data.meshes.new('img_mesh')\n"
"obj = bpy.data.objects.new('img_obj', mesh)\n"
"bpy.context.collection.objects.link(obj)\n"
"bm = bmesh.new()\n"
"\n"
"# create verts grid\n"
"verts = []\n"
"for j in range(0, H, step):\n"
"    row = []\n" 
"    vj = (j / float(H) - 0.5) * 2.0\n"
"    for i in range(0, W, step):\n"
"        vi = (i / float(W) - 0.5) * 2.0\n"
"        if use_pil:\n"
"            d = depth_pixels[i,j]\n" 
"        else:\n"
"            # bpy image stores pixels as floats RGBA\n"
"            px_idx = (j*W + i)*4\n"
"            d = int(depth_img.pixels[px_idx]*255)\n"
"        z = (d/255.0) * 1.0  # scale depth\n" 
"        v = bm.verts.new((vi, vj, z))\n"
"        row.append(v)\n"
"    verts.append(row)\n"
"\n"
"bm.verts.ensure_lookup_table()\n"
"# create faces\n"
"for y in range(len(verts)-1):\n"
"    for x in range(len(verts[y])-1):\n"
"        v1 = verts[y][x]\n" 
"        v2 = verts[y][x+1]\n" 
"        v3 = verts[y+1][x+1]\n" 
"        v4 = verts[y+1][x]\n"
"        try:\n"
"            bm.faces.new((v1,v2,v3,v4))\n"
"        except Exception:\n"
"            pass\n"
"\n"
"bm.to_mesh(mesh)\n"
"bm.free()\n"
"\n"
"# create UVs and assign material with color image\n"
"mesh.uv_layers.new(name='UVMap')\n"
"uv_layer = mesh.uv_layers.active.data\n"
"loop_index = 0\n"
"for poly in mesh.polygons:\n"
"    for idx in poly.loop_indices:\n"
"        loop = mesh.loops[idx]\n" 
"        v = mesh.vertices[loop.vertex_index]\n"
"        # map back to uv by reversing the earlier normalization\n"
"        u = (v.co.x/2.0 + 0.5)\n"
"        vcoord = (v.co.y/2.0 + 0.5)\n"
"        uv_layer[loop_index].uv = (u, 1.0 - vcoord)\n"
"        loop_index += 1\n"
"\n"
"mat = bpy.data.materials.new('MatColor')\n"
"mat.use_nodes = True\n"
"nodes = mat.node_tree.nodes\n"
"links = mat.node_tree.links\n"
"nodes.clear()\n"
"out = nodes.new('ShaderNodeOutputMaterial')\n"
"bsdf = nodes.new('ShaderNodeBsdfPrincipled')\n" 
"tex = nodes.new('ShaderNodeTexImage')\n" 
"tex.image = color_img\n"
"links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])\n"
"links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])\n"
"obj.data.materials.append(mat)\n"
"\n"
"# optionally smooth normals\n"
"for p in obj.data.polygons:\n"
"    p.use_smooth = True\n"
"\n"
"# set scene frame range if sequence depth provided\n"
"if depth_is_dir:\n"
"    # load sequence into texture node\n"
"    tex.image.source = 'SEQUENCE'\n" 
"    tex.image.filepath = depth_files[0]\n" 
"    tex.image.filepath_from_user(depth_files[0])\n" 
"    tex.image.frames = len(depth_files)\n" 
"    tex.image.frame_start = 1\n" 
"    tex.image.reload()\n" 
"    bpy.context.scene.frame_start = 1\n"
"    bpy.context.scene.frame_end = len(depth_files)\n"
"\n"
"bpy.ops.wm.save_as_mainfile(filepath=outblend)\n"
"print('Saved', outblend)\n"
    );
    fclose(f);
    return 1;
}

int write_supporting_scripts(const char *outdir) {
    char py_depth[MAX_PATH]; snprintf(py_depth, sizeof(py_depth), "%s%sscripts_image_to_depth.py", outdir, SEP);
    char py_blend[MAX_PATH]; snprintf(py_blend, sizeof(py_blend), "%s%sscripts_blender_mesh.py", outdir, SEP);
    ensure_dir(outdir);
    if (!write_python_depth_script(py_depth)) return 0;
    if (!write_blender_script(py_blend)) return 0;
    return 1;
}

int run_python_depth_single(const char *py_path, const char *inpath, const char *outpath) {
    char cmd[MAX_CMD];
    snprintf(cmd, sizeof(cmd), "python \"%s\" \"%s\" \"%s\" >nul 2>nul", py_path, inpath, outpath);
    return system(cmd);
}
int run_python_depth_batch(const char *py_path, const char *indir, const char *outdir) {
    char cmd[MAX_CMD];
    snprintf(cmd, sizeof(cmd), "python \"%s\" \"%s\" \"%s\" >nul 2>nul", py_path, indir, outdir);
    return system(cmd);
}

int run_blender_script(const char *py_blend, const char *color, const char *depth, const char *outblend) {
    char cmd[MAX_CMD];
    snprintf(cmd, sizeof(cmd), "blender --background --python \"%s\" -- \"%s\" \"%s\" \"%s\" >nul 2>nul", py_blend, color, depth, outblend);
    return system(cmd);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <media_folder_or_file> <out_folder>\n", argv[0]);
        return 1;
    }
    const char *media = argv[1];
    const char *outdir = argv[2];
    ensure_dir(outdir);

    char scripts_dir[MAX_PATH];
    snprintf(scripts_dir, sizeof(scripts_dir), "%s%sscripts", outdir, SEP);
    ensure_dir(scripts_dir);
    char py_depth[MAX_PATH]; snprintf(py_depth, sizeof(py_depth), "%s%sscripts_image_to_depth.py", scripts_dir, SEP);
    char py_blend[MAX_PATH]; snprintf(py_blend, sizeof(py_blend), "%s%sscripts_blender_mesh.py", scripts_dir, SEP);

    if (!write_python_depth_script(py_depth) || !write_blender_script(py_blend)) {
        fprintf(stderr, "Failed to write helper scripts\n");
        return 1;
    }

    struct stat st;
    if (stat(media, &st) != 0) {
        fprintf(stderr, "Media path not found: %s\n", media);
        return 1;
    }

    if (S_ISREG(st.st_mode)) {
        const char *base = strrchr(media, '\\') ? strrchr(media, '\\')+1 : strrchr(media, '/') ? strrchr(media, '/')+1 : media;
        if (is_image_file(base)) {
            char depth_out[MAX_PATH]; snprintf(depth_out, sizeof(depth_out), "%s%ss_%s_depth.png", outdir, SEP, base);
            printf("Computing spatial depth for image: %s\n", media);
            run_python_depth_single(py_depth, media, depth_out);
            char outblend[MAX_PATH]; snprintf(outblend, sizeof(outblend), "%s%ss_%s_mesh.blend", outdir, SEP, base);
            printf("Building mesh in Blender: %s\n", outblend);
            run_blender_script(py_blend, media, depth_out, outblend);
        } else if (is_video_file(base)) {
            char name_noext[MAX_PATH]; strncpy(name_noext, base, sizeof(name_noext)); char *dot = strrchr(name_noext, '.'); if (dot) *dot = 0;
            char frames_dir[MAX_PATH]; snprintf(frames_dir, sizeof(frames_dir), "%s%s%s_frames", outdir, SEP, name_noext);
            ensure_dir(frames_dir);
            printf("Extracting frames: %s -> %s\n", media, frames_dir);
            run_ffmpeg_extract_frames(media, frames_dir);
            char depth_frames_dir[MAX_PATH]; snprintf(depth_frames_dir, sizeof(depth_frames_dir), "%s%s%s_depths", outdir, SEP, name_noext);
            ensure_dir(depth_frames_dir);
            printf("Computing spatial depth for frames in: %s\n", frames_dir);
            run_python_depth_batch(py_depth, frames_dir, depth_frames_dir);
            // use first color frame for texture in Blender and provide depth directory for animation
            char first_frame[MAX_PATH];
            snprintf(first_frame, sizeof(first_frame), "%s%sframe_00001.png", frames_dir, SEP);
            char outblend[MAX_PATH]; snprintf(outblend, sizeof(outblend), "%s%s%s_anim_mesh.blend", outdir, SEP, name_noext);
            printf("Building animated mesh in Blender: %s\n", outblend);
            run_blender_script(py_blend, first_frame, depth_frames_dir, outblend);
        } else {
            printf("Unsupported file type: %s\n", media);
        }
    } else if (S_ISDIR(st.st_mode)) {
        DIR *dir = opendir(media);
        if (!dir) { perror("opendir"); return 1; }
        struct dirent *entry;
        while ((entry = readdir(dir)) != NULL) {
            if (entry->d_type != DT_REG) continue;
            if (is_image_file(entry->d_name) || is_video_file(entry->d_name)) {
                char fullpath[MAX_PATH]; snprintf(fullpath, sizeof(fullpath), "%s%s%s", media, SEP, entry->d_name);
                char cmd[MAX_CMD];
                snprintf(cmd, sizeof(cmd), "\"%s\" \"%s\" \"%s\"", argv[0], fullpath, outdir);
                system(cmd);
            }
        }
        closedir(dir);
    } else {
        printf("Unsupported media path type.\n");
    }

    printf("Finished. Outputs in: %s\n", outdir);
    printf("Ensure python packages installed: pip install pillow numpy\n");
    return 0;
}
// ...existing code...