"""Generate the PNG image set an MSIX AppxManifest needs from a single source logo.

Usage: python make_assets.py <source_image> <output_dir>
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

SIZES = {
    "Square44x44Logo.png": (44, 44),
    "Square71x71Logo.png": (71, 71),
    "Square150x150Logo.png": (150, 150),
    "Square310x310Logo.png": (310, 310),
    "Wide310x150Logo.png": (310, 150),
    "StoreLogo.png": (50, 50),
    "SplashScreen.png": (620, 300),
}


def make_canvas(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(source, size)
    canvas = Image.new("RGBA", size, (0, 0, 0, 255))
    offset = ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2)
    canvas.paste(fitted, offset, fitted if fitted.mode == "RGBA" else None)
    return canvas


def main() -> None:
    src_path, out_dir = sys.argv[1], sys.argv[2]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    source = Image.open(src_path).convert("RGBA")
    for name, size in SIZES.items():
        make_canvas(source, size).save(out / name)


if __name__ == "__main__":
    main()
