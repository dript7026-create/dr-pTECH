from pathlib import Path

from PIL import Image


ROOT = Path(r"c:/Users/rrcar/Documents/drIpTECH/ecbmps_ccp_studio/build/assets/recraft")
RAW = ROOT / "raw_gutenberg"

TARGETS = [
    ("branding/splash_ecbmps.png", (1280, 720)),
    ("icons/ecbmps_icon_16.png", (16, 16)),
    ("icons/ecbmps_icon_32.png", (32, 32)),
    ("icons/ecbmps_icon_48.png", (48, 48)),
    ("icons/ecbmps_icon_64.png", (64, 64)),
    ("icons/ecbmps_icon_128.png", (128, 128)),
    ("icons/ecbmps_icon_256.png", (256, 256)),
    ("gui/ecbmps/frame_tl.png", (64, 64)),
    ("gui/ecbmps/frame_tr.png", (64, 64)),
    ("gui/ecbmps/frame_bl.png", (64, 64)),
    ("gui/ecbmps/frame_br.png", (64, 64)),
    ("gui/ecbmps/titlebar/titlebar_bg.png", (256, 36)),
    ("gui/ecbmps/titlebar/close_normal.png", (24, 24)),
    ("gui/ecbmps/titlebar/close_hover.png", (24, 24)),
    ("gui/ecbmps/titlebar/close_pressed.png", (24, 24)),
    ("gui/ecbmps/titlebar/minimize_normal.png", (24, 24)),
    ("gui/ecbmps/titlebar/minimize_hover.png", (24, 24)),
    ("gui/ecbmps/titlebar/maximize_normal.png", (24, 24)),
    ("gui/ecbmps/titlebar/maximize_hover.png", (24, 24)),
    ("gui/ecbmps/backgrounds/light.png", (800, 600)),
    ("gui/ecbmps/backgrounds/dark.png", (800, 600)),
    ("gui/ecbmps/backgrounds/sepia.png", (800, 600)),
    ("gui/ecbmps/backgrounds/night.png", (800, 600)),
    ("gui/ecbmps/scrollbar/thumb.png", (16, 16)),
    ("gui/ecbmps/scrollbar/track.png", (16, 64)),
]


def fit_and_crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((max(1, round(src_w * scale)), max(1, round(src_h * scale))), Image.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def main() -> None:
    for rel_path, size in TARGETS:
        src = RAW / rel_path
        dst = ROOT / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        image = Image.open(src).convert("RGBA")
        final = fit_and_crop(image, size)
        final.save(dst, format="PNG")
        print(f"Saved {dst}")


if __name__ == "__main__":
    main()
