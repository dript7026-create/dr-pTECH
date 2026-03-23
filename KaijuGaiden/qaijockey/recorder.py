"""
qaijockey/recorder.py — AVI capture for QAIJockey runs.

Records every emulator frame to an XVID-encoded AVI file.
Accepts PIL Images directly from pyboy.screen.image and writes them
upscaled to the output video with nearest-neighbour interpolation
(pixel-art correct, no blurring).

Output format:
  Codec : XVID (cross-platform, installed with OpenCV)
  FPS   : user-configurable (default 60)
  Size  : GB native 160×144, upscaled by SCALE factor (default ×3 = 480×432)
  Colour: DMG 4-shade greenscale palette rendered via PyBoy's own colour map

Usage:
    rec = AVIRecorder("dist/run.avi", fps=60, scale=3)
    # inside game loop:
    rec.write_pil(pyboy.screen.image)
    # when done:
    rec.close()
"""

from __future__ import annotations

import numpy as np


# ── DMG greenscale palette for shade-array renders ───────────────────────────
# Index = shade value 0-3 (0=lightest, 3=darkest), value = BGR tuple
_DMG_BGR = [
    (224, 248, 232),   # shade 0 — lightest (off-white)
    (112, 192, 136),   # shade 1 — light green
    ( 86, 104,  52),   # shade 2 — dark green
    ( 32,  24,   8),   # shade 3 — darkest
]

GB_W = 160
GB_H = 144


class AVIRecorder:
    """
    Writes Game Boy screen frames to an XVID AVI file.

    Two write paths:
      write_pil(pil_img) — use the PIL Image from pyboy.screen.image directly.
                           Colour-accurate preview of what PyBoy renders.
      write_shades(fb)   — render from a raw shade array (works headless / no
                           SDL) using the DMG greenscale palette.
    """

    def __init__(self,
                 output_path: str,
                 fps: int = 60,
                 scale: int = 3) -> None:
        import cv2

        self.output_path = output_path
        self.fps   = fps
        self.scale = scale
        self.out_w = GB_W * scale
        self.out_h = GB_H * scale

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self._writer = cv2.VideoWriter(
            output_path, fourcc, float(fps), (self.out_w, self.out_h)
        )
        if not self._writer.isOpened():
            raise RuntimeError(
                f"[REC] VideoWriter could not open '{output_path}'.\n"
                "      Check that the XVID codec is available on this system."
            )

        self.frame_count = 0
        self._cv2 = cv2

    # ── Write helpers ──────────────────────────────────────────────────────────

    def write_pil(self, pil_img) -> None:
        """
        Write a frame from a PIL Image (e.g. pyboy.screen.image).
        Converts RGBA → RGB → BGR → upscale → write.
        """
        import numpy as _np

        # PIL → numpy RGB
        arr = _np.array(pil_img)
        if arr.shape[2] == 4:
            arr = arr[:, :, :3]          # drop alpha

        # RGB → BGR (OpenCV convention)
        bgr = arr[:, :, ::-1].copy()

        self._write_bgr(bgr)

    def write_shades(self, shades: np.ndarray) -> None:
        """
        Write a frame from a shade array (H×W uint8, values 0–3).
        Renders with the DMG greenscale palette.
        """
        h, w = shades.shape
        bgr = np.zeros((h, w, 3), dtype=np.uint8)
        for shade, colour in enumerate(_DMG_BGR):
            bgr[shades == shade] = colour
        self._write_bgr(bgr)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _write_bgr(self, bgr: np.ndarray) -> None:
        h, w = bgr.shape[:2]
        if (w, h) != (self.out_w, self.out_h):
            bgr = self._cv2.resize(
                bgr, (self.out_w, self.out_h),
                interpolation=self._cv2.INTER_NEAREST
            )
        self._writer.write(bgr)
        self.frame_count += 1

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Flush and close the video file."""
        self._writer.release()
        print(f"[REC] {self.frame_count} frames written → {self.output_path}")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
