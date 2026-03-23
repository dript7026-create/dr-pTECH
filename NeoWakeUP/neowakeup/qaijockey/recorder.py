"""AVI capture for QAIJockey runs."""

from __future__ import annotations

import numpy as np

_DMG_BGR = [
    (224, 248, 232),
    (112, 192, 136),
    (86, 104, 52),
    (32, 24, 8),
]

GB_W = 160
GB_H = 144


class AVIRecorder:
    def __init__(self, output_path: str, fps: int = 60, scale: int = 3) -> None:
        import cv2

        self.output_path = output_path
        self.fps = fps
        self.scale = scale
        self.out_w = GB_W * scale
        self.out_h = GB_H * scale
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self._writer = cv2.VideoWriter(output_path, fourcc, float(fps), (self.out_w, self.out_h))
        if not self._writer.isOpened():
            raise RuntimeError(f"[REC] VideoWriter could not open '{output_path}'.")
        self.frame_count = 0
        self._cv2 = cv2

    def write_pil(self, pil_img) -> None:
        import numpy as _np

        arr = _np.array(pil_img)
        if arr.shape[2] == 4:
            arr = arr[:, :, :3]
        bgr = arr[:, :, ::-1].copy()
        self._write_bgr(bgr)

    def write_shades(self, shades: np.ndarray) -> None:
        h, w = shades.shape
        bgr = np.zeros((h, w, 3), dtype=np.uint8)
        for shade, colour in enumerate(_DMG_BGR):
            bgr[shades == shade] = colour
        self._write_bgr(bgr)

    def _write_bgr(self, bgr: np.ndarray) -> None:
        h, w = bgr.shape[:2]
        if (w, h) != (self.out_w, self.out_h):
            bgr = self._cv2.resize(bgr, (self.out_w, self.out_h), interpolation=self._cv2.INTER_NEAREST)
        self._writer.write(bgr)
        self.frame_count += 1

    def close(self) -> None:
        self._writer.release()
        print(f"[REC] {self.frame_count} frames written -> {self.output_path}")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()