"""Generate neon wave logo for SFlow."""
import math
from PIL import Image, ImageDraw, ImageFilter

def make_neon_wave(size: int) -> Image.Image:
    W = H = size
    scale = W / 512  # scale factor relative to base 512px design

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Dark warm background (near-black with a slight warm undertone)
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    radius = W // 6
    bg_draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=radius, fill=(12, 8, 4, 255))
    img = Image.alpha_composite(img, bg)

    # Wave parameters — slightly taller amplitude for a fatter-looking wave
    cy = H // 2
    amplitude = H * 0.27
    frequency = 2.2
    x_margin = W * 0.10

    def wave_y(x):
        t = (x - x_margin) / (W - 2 * x_margin)
        return cy + amplitude * math.sin(t * frequency * 2 * math.pi)

    xs = [x_margin + i * (W - 2 * x_margin) / 200 for i in range(201)]
    points = [(x, wave_y(x)) for x in xs]

    # Orange neon glow layers (outer → inner)
    glow_layers = [
        (int(28 * scale), (160,  50,   0,  20)),
        (int(18 * scale), (200,  80,   0,  45)),
        (int(11 * scale), (230, 110,   5,  90)),
        (int(7  * scale), (255, 140,  20, 150)),
        (int(4  * scale), (255, 175,  50, 200)),
        (max(1, int(2 * scale)), (255, 210, 100, 230)),
    ]

    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    for width, color in glow_layers:
        w = max(1, width)
        for i in range(len(points) - 1):
            glow_draw.line([points[i], points[i + 1]], fill=color, width=w)

    glow_blurred = glow_img.filter(ImageFilter.GaussianBlur(radius=max(1.0, 3.0 * scale)))
    img = Image.alpha_composite(img, glow_blurred)

    # Bright warm-white hot core
    core_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core_img)
    core_w = max(1, int(3 * scale))
    for i in range(len(points) - 1):
        core_draw.line([points[i], points[i + 1]], fill=(255, 240, 180, 255), width=core_w)
    img = Image.alpha_composite(img, core_img)

    return img


def to_ico(path: str):
    """Generate ICO with each size rendered natively (not scaled down)."""
    import struct, io as _io

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [make_neon_wave(s).convert("RGBA") for s in sizes]
    # largest first is ICO convention
    images = list(reversed(images))

    png_chunks = []
    for img in images:
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        png_chunks.append(buf.getvalue())

    n = len(images)
    data_offset = 6 + n * 16
    offsets, off = [], data_offset
    for chunk in png_chunks:
        offsets.append(off)
        off += len(chunk)

    out = _io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, n))           # ICONDIR header
    for i, img in enumerate(images):
        w = img.width  if img.width  < 256 else 0    # 0 encodes 256
        h = img.height if img.height < 256 else 0
        out.write(struct.pack("<BBBBHHII",
            w, h, 0, 0, 1, 32,
            len(png_chunks[i]), offsets[i]))
    for chunk in png_chunks:
        out.write(chunk)

    with open(path, "wb") as f:
        f.write(out.getvalue())


def make_neon_wave_transparent(size: int) -> Image.Image:
    """Wave only, transparent background (for use inside the pill widget)."""
    W = H = size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    amplitude = H * 0.25
    frequency = 2.2
    x_margin = W * 0.08

    def wave_y(x):
        t = (x - x_margin) / (W - 2 * x_margin)
        return H / 2 + amplitude * math.sin(t * frequency * 2 * math.pi)

    xs = [x_margin + i * (W - 2 * x_margin) / 200 for i in range(201)]
    points = [(x, wave_y(x)) for x in xs]

    glow_layers = [
        (10, (160,  50,   0,  30)),
        (7,  (200,  80,   0,  65)),
        (4,  (255, 130,  10, 130)),
        (2,  (255, 175,  50, 200)),
        (1,  (255, 215, 110, 240)),
    ]

    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    for width, color in glow_layers:
        for i in range(len(points) - 1):
            glow_draw.line([points[i], points[i + 1]], fill=color, width=width)

    glow_blurred = glow_img.filter(ImageFilter.GaussianBlur(radius=1))
    img = Image.alpha_composite(img, glow_blurred)

    core_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core_img)
    for i in range(len(points) - 1):
        core_draw.line([points[i], points[i + 1]], fill=(255, 240, 180, 255), width=1)
    img = Image.alpha_composite(img, core_img)
    return img


if __name__ == "__main__":
    logo_big   = make_neon_wave(512)
    logo_small = make_neon_wave_transparent(96)   # transparent bg for pill

    logo_big.save("logo.png")
    logo_small.save("logo_small.png")
    to_ico("sflow.ico")

    print("Generated: logo.png, logo_small.png, sflow.ico")
