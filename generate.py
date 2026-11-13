#!/usr/bin/env python3
"""Generate OduwaCoin Instagram image (1080x1350 JPEG) and Reel (1080x1920 MP4).

Usage: python3 generate.py [--date YYYY-MM-DD] [--out DIR]
Writes DIR/image.jpg, DIR/reel.mp4, DIR/meta.json (captions, themes).
Prices come only from CoinGecko (ids=oduwa-coin).
"""
import argparse, datetime as dt, json, math, os, shutil, subprocess, tempfile, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
ASSETS = os.path.join(HERE, "assets")

BLACK = (8, 8, 8)
GOLD = (232, 182, 40)
GOLD_LIGHT = (255, 228, 138)
GOLD_DARK = (166, 116, 14)
WHITE = (242, 238, 228)
GREY = (170, 165, 155)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


# ---------------------------------------------------------------- data
def coingecko_price():
    """Current OWC/USD from CoinGecko only. Retries on rate limits; never falls back to another source."""
    import time
    url = "https://api.coingecko.com/api/v3/simple/price?ids=oduwa-coin&vs_currencies=usd"
    last = None
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "owc-autopost/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["oduwa-coin"]["usd"], []
        except Exception as e:
            last = e
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"CoinGecko price unavailable: {last}")


def fmt_usd(p):
    return f"${p:,.4f}" if p < 10 else f"${p:,.2f}"


# ---------------------------------------------------------------- drawing helpers
def gold_gradient(size):
    w, h = size
    g = Image.new("RGB", (1, max(h, 2)))
    for y in range(h):
        t = y / max(h - 1, 1)
        if t < 0.5:
            a, b, k = GOLD_LIGHT, GOLD, t / 0.5
        else:
            a, b, k = GOLD, GOLD_DARK, (t - 0.5) / 0.5
        g.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)))
    return g.resize((w, h))


def background(W, H, glow_y, phase=0.0):
    bg = Image.new("RGB", (W, H), BLACK)
    # radial gold glow
    glow = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(glow)
    r = int(W * 0.62)
    d.ellipse((W // 2 - r, glow_y - r, W // 2 + r, glow_y + r), fill=95)
    glow = glow.filter(ImageFilter.GaussianBlur(W * 0.16))
    bg.paste(Image.new("RGB", (W, H), (120, 84, 8)), (0, 0), glow)
    # subtle diagonal gold lines, drifting with phase
    lines = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(lines)
    step = 70
    off = int(phase * step) % step
    for x in range(-H, W + H, step):
        ld.line((x + off, 0, x + off + H, H), fill=16, width=2)
    bg.paste(Image.new("RGB", (W, H), GOLD), (0, 0), lines)
    # frame
    fd = ImageDraw.Draw(bg)
    m = 34
    fd.rectangle((m, m, W - m, H - m), outline=(120, 90, 20), width=2)
    return bg


def wrap(draw, text, fnt, max_w):
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            t = (line + " " + w).strip()
            if draw.textlength(t, font=fnt) <= max_w:
                line = t
            else:
                if line:
                    out.append(line)
                line = w
        out.append(line)
    return out


def fit_font(draw, lines, name, max_w, start, min_size=40):
    s = start
    while s > min_size:
        f = font(name, s)
        if all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f
        s -= 4
    return font(name, min_size)


class Layer:
    """A pre-rendered RGBA element positioned at (x, y), with an animation slot."""

    def __init__(self, img, x, y, start=0.0, dur=0.6, slide=40):
        self.img, self.x, self.y = img, x, y
        self.start, self.dur, self.slide = start, dur, slide

    def draw(self, canvas, t=None):
        if t is None:
            canvas.alpha_composite(self.img, (self.x, self.y))
            return
        k = (t - self.start) / self.dur
        if k <= 0:
            return
        k = min(k, 1.0)
        e = 1 - (1 - k) ** 3
        img = self.img
        if k < 1:
            a = img.getchannel("A").point(lambda v: int(v * e))
            img = img.copy()
            img.putalpha(a)
        canvas.alpha_composite(img, (self.x, self.y + int((1 - e) * self.slide)))


def text_layer(lines, fnt, fill, align="center", width=None, spacing=1.18, gradient=False, tracking=0):
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * spacing)

    def lw(l):
        return tmp.textlength(l, font=fnt) + tracking * max(len(l) - 1, 0)

    w = width or int(max(lw(l) for l in lines)) + 8
    h = lh * len(lines) + 8
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    for i, l in enumerate(lines):
        x = (w - lw(l)) / 2 if align == "center" else 0
        if tracking:
            for ch in l:
                md.text((x, i * lh), ch, font=fnt, fill=255)
                x += tmp.textlength(ch, font=fnt) + tracking
        else:
            md.text((x, i * lh), l, font=fnt, fill=255)
    fillimg = gold_gradient((w, h)) if gradient else Image.new("RGB", (w, h), fill)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(fillimg, (0, 0), mask)
    return out


def pill(text, fnt, padx=46, pady=22):
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = int(tmp.textlength(text, font=fnt))
    asc, desc = fnt.getmetrics()
    w, h = tw + padx * 2, asc + desc + pady * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
    im.paste(gold_gradient((w, h)), (0, 0), m)
    ImageDraw.Draw(im).text((padx, pady), text, font=fnt, fill=BLACK)
    return im


def logo(size):
    im = Image.open(os.path.join(ASSETS, "oduwacoin-original.png")).convert("RGBA")
    im = im.resize((size, size), Image.LANCZOS)
    # thin gold ring so the black badge stands out from the dark background
    ring = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    w = max(8, size // 30)
    ImageDraw.Draw(ring).ellipse((w // 2, w // 2, size * 4 - w // 2, size * 4 - w // 2), outline=GOLD + (255,), width=w)
    im.alpha_composite(ring.resize((size, size), Image.LANCZOS))
    return im


def sparkline(series, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if len(series) < 2:
        return im
    lo, hi = min(series), max(series)
    rng = (hi - lo) or 1
    pts = [(i * (w - 1) / (len(series) - 1), h - 10 - (v - lo) / rng * (h - 20)) for i, v in enumerate(series)]
    d = ImageDraw.Draw(im)
    d.polygon(pts + [(w - 1, h), (0, h)], fill=(232, 182, 40, 40))
    d.line(pts, fill=GOLD + (255,), width=5, joint="curve")
    x, y = pts[-1]
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=GOLD_LIGHT + (255,))
    return im


# ---------------------------------------------------------------- layouts
def build_layers(post, W, H, video=False):
    """Return (layers, glow_y). Layers stacked top-to-bottom, vertically centred."""
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    max_w = W - 200
    s = 1.0 if not video else 1.38
    blocks = []  # (layer_img, gap_after)

    lg = logo(int(230 * s))
    blocks.append((lg, int(44 * s)))
    blocks.append((text_layer([post["kicker"]], font("Montserrat-Bold.ttf", int(30 * s)), GOLD, tracking=6), int(30 * s)))

    if post.get("price"):
        pf = font("Montserrat-Black.ttf", int(170 * s))
        blocks.append((text_layer([post["price"]], pf, None, gradient=True), int(6 * s)))
        blocks.append((text_layer(["per 1 OWC (USD)"], font("Lato-Regular.ttf", int(38 * s)), WHITE), int(34 * s)))
        div = Image.new("RGBA", (int(120 * s), 6), GOLD + (255,))
        blocks.append((div, int(34 * s)))
        bf = font("Lato-Regular.ttf", int(40 * s))
        blocks.append((text_layer(["Live price from CoinGecko", post["date_str"]], bf, WHITE, spacing=1.35), int(52 * s)))
    else:
        hl_lines = post["headline"].split("\n")
        hf = fit_font(tmp, hl_lines, "Montserrat-Black.ttf", max_w, int(104 * s))
        blocks.append((text_layer(hl_lines, hf, None, gradient=True, spacing=1.08), int(30 * s)))
        div = Image.new("RGBA", (int(120 * s), 6), GOLD + (255,))
        blocks.append((div, int(34 * s)))
        bf = font("Lato-Regular.ttf", int(40 * s))
        blocks.append((text_layer(wrap(tmp, post["body"], bf, max_w - 40), bf, WHITE, spacing=1.35), int(52 * s)))

    blocks.append((pill(post["cta"].upper(), font("Montserrat-ExtraBold.ttf", int(34 * s))), int(28 * s)))
    blocks.append((text_layer([post["url"]], font("Montserrat-SemiBold.ttf", int(34 * s)), WHITE), 0))

    total = sum(b.height + g for b, g in blocks)
    y = (H - total) // 2 - (40 if video else 0)
    layers = []
    for i, (img, gap) in enumerate(blocks):
        layers.append(Layer(img, (W - img.width) // 2, y, start=0.25 + i * 0.32, dur=0.7))
        y += img.height + gap
    glow_y = layers[0].y + layers[0].img.height // 2
    # footer handle
    ft = text_layer(["@oduwacoin"], font("Montserrat-SemiBold.ttf", 26), GREY)
    layers.append(Layer(ft, (W - ft.width) // 2, H - 34 - 26 - ft.height, start=0.1, dur=0.5, slide=0))
    return layers, glow_y


STYLE = os.environ.get("OWC_STYLE", "commercial")


def render_image(post, path):
    if STYLE == "commercial":
        import commercial
        return commercial.render_image(post, path)
    W, H = 1080, 1350
    layers, gy = build_layers(post, W, H)
    canvas = background(W, H, gy).convert("RGBA")
    for l in layers:
        l.draw(canvas)
    canvas.convert("RGB").save(path, "JPEG", quality=92)


def render_reel(post, path, seconds=12, fps=30):
    if STYLE == "commercial":
        import commercial
        return commercial.render_reel(post, path)
    W, H = 1080, 1920
    layers, gy = build_layers(post, W, H, video=True)
    logo_layer = layers[0]
    tmpd = tempfile.mkdtemp()
    n = seconds * fps
    for f in range(n):
        t = f / fps
        canvas = background(W, H, gy, phase=t * 0.35).convert("RGBA")
        # gentle logo pulse after it appears
        for i, l in enumerate(layers):
            if i == 0 and t > l.start + l.dur:
                sc = 1 + 0.035 * math.sin((t - l.start) * 2.2)
                im = l.img.resize((int(l.img.width * sc), int(l.img.height * sc)), Image.BILINEAR)
                cx, cy = l.x + l.img.width // 2, l.y + l.img.height // 2
                canvas.alpha_composite(im, (cx - im.width // 2, cy - im.height // 2))
            else:
                l.draw(canvas, t)
        # fade out last 0.6s
        if t > seconds - 0.6:
            k = (t - (seconds - 0.6)) / 0.6
            canvas = Image.blend(canvas, Image.new("RGBA", (W, H), BLACK + (255,)), min(k, 1) * 0.85)
        canvas.convert("RGB").save(os.path.join(tmpd, f"f{f:04d}.png"), compress_level=1)
    # soft ambient pad (A minor add9) so the Reel isn't silent
    audio = (
        f"aevalsrc='0.06*sin(2*PI*220*t)+0.05*sin(2*PI*261.63*t)+0.045*sin(2*PI*329.63*t)+0.03*sin(2*PI*493.88*t)"
        f"*(0.6+0.4*sin(2*PI*0.25*t))':s=44100:d={seconds}"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmpd, "f%04d.png"),
        "-f", "lavfi", "-i", audio,
        "-af", f"afade=t=in:d=1.5,afade=t=out:st={seconds-1.5}:d=1.5,lowpass=f=2500",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-preset", "medium", "-crf", "20",
        "-r", str(fps), "-g", str(fps * 2), "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart", "-shortest", path,
    ], check=True)
    shutil.rmtree(tmpd)


# ---------------------------------------------------------------- selection
EPOCH = dt.date(2026, 11, 12)


def pick(theme, idx, date, price_data, reel=False):
    if theme == "price":
        price, series = price_data
        date_str = date.strftime("%b %d, %Y")
        change_line = ""
        if len(series) > 1:
            ch = (series[-1] - series[0]) / series[0] * 100
            change_line = f"7-day change: {ch:+.1f}%"
        post = dict(kicker="OWC PRICE UPDATE", price=fmt_usd(price), series=series, change_line=change_line,
                    date_str=date_str, cta="Buy OWC with USDT", url="oduwacoin.io/gift#buy")
        body = C.PRICE_CAPTIONS[idx % len(C.PRICE_CAPTIONS)].format(usd=fmt_usd(price), date=date_str)
        post["theme"] = "price"
        return post, C.make_caption("price", body, idx, reel)
    items = C.POSTS[theme]
    post = dict(items[idx % len(items)])
    post["theme"] = theme
    return post, C.make_caption(theme, post["caption"], idx, reel)


def plan(date):
    n = (date - EPOCH).days
    img_theme = C.THEMES[n % 4]
    vid_theme = C.THEMES[(n + 2) % 4]
    return n, img_theme, vid_theme


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone(dt.timedelta(hours=-8))).date().isoformat())
    ap.add_argument("--out", default=None)
    ap.add_argument("--image-only", action="store_true")
    a = ap.parse_args()
    date = dt.date.fromisoformat(a.date)
    out = a.out or os.path.join(HERE, "media", date.isoformat())
    os.makedirs(out, exist_ok=True)
    n, it, vt = plan(date)
    price_data = coingecko_price() if "price" in (it, vt) else (None, [])
    # each theme cycles its own items every 4 days
    img_post, img_cap = pick(it, n // 4, date, price_data)
    vid_post, vid_cap = pick(vt, n // 4 + 3, date, price_data, reel=True)
    render_image(img_post, os.path.join(out, "image.jpg"))
    if not a.image_only:
        render_reel(vid_post, os.path.join(out, "reel.mp4"))
    meta = dict(date=date.isoformat(), image=dict(theme=it, caption=img_cap), reel=dict(theme=vt, caption=vid_cap))
    with open(os.path.join(out, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
