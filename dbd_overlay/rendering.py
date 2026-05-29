from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterator

from PIL import Image, ImageColor, ImageDraw, ImageSequence, ImageTk


def iter_image_frames(path: Path) -> Iterator[tuple[Image.Image, int]]:
    with Image.open(path) as image:
        for frame in ImageSequence.Iterator(image):
            duration = int(frame.info.get("duration", image.info.get("duration", 100)) or 100)
            yield frame.convert("RGBA"), max(duration, 20)


def render_frame(
    image: Image.Image,
    size: int,
    zoom: float,
    border_width: int,
    border_color: str,
    corner_radius: int,
    rotation_degrees: float = 0,
) -> Image.Image:
    size = max(80, int(size))
    zoom = max(0.2, float(zoom))
    src = image.convert("RGBA")
    if rotation_degrees:
        src = src.rotate(rotation_degrees, expand=True, resample=Image.Resampling.BICUBIC)

    target = max(1, int(size * zoom))
    src.thumbnail((target, target), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - src.width) // 2
    y = (size - src.height) // 2
    canvas.alpha_composite(src, (x, y))

    radius = max(0, min(corner_radius, size // 2))
    if radius:
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
        canvas.putalpha(Image.composite(canvas.getchannel("A"), Image.new("L", (size, size), 0), mask))

    if border_width > 0:
        draw = ImageDraw.Draw(canvas)
        color = ImageColor.getrgb(border_color)
        inset = border_width // 2
        draw.rounded_rectangle(
            (inset, inset, size - 1 - inset, size - 1 - inset),
            radius=max(0, radius - inset),
            outline=color + (230,),
            width=border_width,
        )
    return canvas


class AnimatedImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.frames = list(iter_image_frames(path))
        if not self.frames:
            raise ValueError(f"No frames found in {path}")
        self.index = 0

    def next_frame(self) -> tuple[Image.Image, int]:
        frame, duration = self.frames[self.index]
        self.index = (self.index + 1) % len(self.frames)
        return frame, duration

