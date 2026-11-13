#!/usr/bin/env python3
"""Commercial-style OduwaCoin layouts: full-bleed cinematic scenes, bold headlines, punchy 15s Reel with a beat.

render_image(post, path)  -> 1080x1350 JPEG
render_reel(post, path)   -> 1080x1920 MP4, 15 s, three scenes + end card, synthesized music
post needs: theme, kicker, headline, body, cta, url (price posts: price, date_str)
"""
import math, os, random, shutil, subprocess, tempfile, wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import generate as G

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(HERE, "assets", "scenes")

# theme -> (main scene, second scene)
SCENE_FOR = {
    "staking": ("staking", "coin_hero"),
    "oduwapay": ("pay_screen", "coin_hero"),
    "education": ("network", "coin_hero"),
    "price": ("coin_hero", "staking"),
}
TEXT_BOTTOM = {"pay_screen", "coin_hero"}  # scenes whose subject sits in the upper half
_cache = {}


def scene(name, width):
    key = (name, width)
    if key not in _cache:
        im = Image.open(os.path.join(SCENES, name + ".png")).convert("RGB")
        h = int(im.height * width / im.width)
        _cache[key] = im.resize((width, h), Image.LANCZOS)
    return _cache[key]


def shade(W, H, top=0.42, bottom=0.45, strength=235):
    """Black gradients at top and bottom so text reads over any scene."""
    a = np.zeros((H, 1), np.float32)
    y = np.arange(H, dtype=np.float32) / H
    a[:, 0] = np.clip((top - y) / top, 0, 1) ** 1.4 * strength
    a[:, 0] = np.maximum(a[:, 0], np.clip((y - (1 - bottom)) / bottom, 0, 1) ** 1.2 * strength)
    a = np.repeat(a, W, axis=1).astype(np.uint8)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.putalpha(Image.fromarray(a))
    return im


def vignette(W, H):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse((-W * 0.25, -H * 0.15, W * 1.25, H * 1.15), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(W * 0.12))
    v = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    v.putalpha(Image.eval(m, lambda p: int((255 - p) * 0.66)))
    return v


def headline_layers(text, max_w, size, upper=True):
    """Headline lines: all white except the last line in gold. Returns list of RGBA images."""
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines = [l.upper() if upper else l for l in text.split("\n")]
    f = G.fit_font(tmp, lines, "Montserrat-Black.ttf", max_w, size, 52)
    out = []
    for i, l in enumerate(lines):
        last = i == len(lines) - 1 and len(lines) > 1
        out.append(G.text_layer([l], f, G.WHITE, align="left", gradient=last, spacing=1.0))
    return out


def brand_row(size=88):
    lg = G.logo(size)
    wm = G.text_layer(["ODUWACOIN"], G.font("Montserrat-ExtraBold.ttf", int(size * 0.36)), G.WHITE, tracking=5)
    w = lg.width + 22 + wm.width
    im = Image.new("RGBA", (w, size), (0, 0, 0, 0))
    im.alpha_composite(lg, (0, 0))
    im.alpha_composite(wm, (lg.width + 22, (size - wm.height) // 2 + 2))
    return im


def shadowed(img, radius=14, alpha=200):
    """Add a soft dark shadow behind an RGBA element for legibility."""
    pad = radius * 2
    out = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    a = img.getchannel("A").point(lambda v: min(255, int(v * alpha / 255)))
    sh.paste((0, 0, 0, 255), (pad, pad), a)
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(sh)
    out.alpha_composite(img, (pad, pad))
    return out, pad


# ------------------------------------------------------------------ image
def render_image(post, path):
    W, H = 1080, 1350
    theme = post.get("theme", "staking")
    main = scene(SCENE_FOR[theme][0], W)
    sname = SCENE_FOR[theme][0]
    bottom = sname in TEXT_BOTTOM
    off = {"pay_screen": 360, "coin_hero": 330, "staking": 300, "network": 170}.get(sname, 280)
    off = min(off, main.height - H)
    canvas = main.crop((0, off, W, off + H)).convert("RGBA")
    canvas.alpha_composite(vignette(W, H))
    canvas.alpha_composite(shade(W, H, top=0.22, bottom=0.62) if bottom else shade(W, H, top=0.46, bottom=0.42))
    M = 72
    canvas.alpha_composite(brand_row(84), (M, 64))

    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    k = G.text_layer([post["kicker"]], G.font("Montserrat-Bold.ttf", 30), G.GOLD, align="left", tracking=6)
    if post.get("price"):
        hl = [G.text_layer(["1 OWC ="], G.font("Montserrat-Black.ttf", 96), G.WHITE, align="left", spacing=1.0),
              G.text_layer([post["price"]], G.fit_font(tmp, [post["price"]], "Montserrat-Black.ttf", W - 2 * M, 150), None,
                           align="left", gradient=True, spacing=1.0)]
    else:
        hl = headline_layers(post["headline"], W - 2 * M, 96 if bottom else 112)
    bf = G.font("Lato-Bold.ttf", 38)
    body = "Live price from CoinGecko, " + post["date_str"] if post.get("price") else post["body"]
    blines = G.wrap(tmp, body, bf, W - 2 * M - 40)[:3]
    b = G.text_layer(blines, bf, G.WHITE, align="left", spacing=1.32)
    pl = G.pill(post["cta"].upper(), G.font("Montserrat-ExtraBold.ttf", 34))
    url = G.text_layer([post["url"]], G.font("Montserrat-SemiBold.ttf", 32), G.WHITE, align="left")
    bar = Image.new("RGBA", (90, 6), G.GOLD + (255,))

    yb = H - 70 - pl.height
    canvas.alpha_composite(pl, (M, yb))
    canvas.alpha_composite(url, (M + pl.width + 28, yb + (pl.height - url.height) // 2 + 2))
    yb -= 36 + b.height
    canvas.alpha_composite(b, (M, yb))
    if bottom:
        yb -= 24
        hl_h = sum(l.height - 6 for l in hl)
        y = yb - hl_h - k.height - 14
    else:
        canvas.alpha_composite(bar, (M, yb - 30))
        y = 196
    canvas.alpha_composite(k, (M, y))
    y += k.height + 14
    for l in hl:
        s, p = shadowed(l, 16, 170)
        canvas.alpha_composite(s, (M - p, y - p))
        y += l.height - 6
    canvas.convert("RGB").save(path, "JPEG", quality=93)


# ------------------------------------------------------------------ reel helpers
def ease_out(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def ease_back(k, s=1.7):
    k = max(0.0, min(1.0, k)) - 1
    return 1 + k * k * ((s + 1) * k + s)


def with_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return img


def paste_scaled(canvas, img, cx, cy, sc, alpha=1.0):
    if sc <= 0.01 or alpha <= 0.01:
        return
    if abs(sc - 1) > 0.002:
        img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    canvas.alpha_composite(with_alpha(img, alpha), (int(cx - img.width / 2), int(cy - img.height / 2)))


def ken_burns(src, W, H, t, dur, z0, z1, dx=0, dy=0, yc=0.5):
    k = ease_out(t / dur) * 0.6 + (t / dur) * 0.4
    z = z0 + (z1 - z0) * k
    cw, ch = W / z, H / z
    cx = src.width / 2 + dx * k
    cy = src.height * yc + dy * k
    x0 = max(0, min(src.width - cw, cx - cw / 2))
    y0 = max(0, min(src.height - ch, cy - ch / 2))
    return src.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")


def sweep(img, k):
    """Diagonal light sweep across an element's opaque pixels; k in 0..1 is band position."""
    w, h = img.size
    band = np.zeros((h, w), np.float32)
    xs = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.5
    c = -0.3 * w + k * 1.8 * w
    band = np.clip(1 - np.abs(xs - c) / (w * 0.09), 0, 1) ** 2
    a = np.array(img.getchannel("A"), np.float32) / 255 * band * 230
    hi = Image.new("RGBA", (w, h), (255, 248, 220, 0))
    hi.putalpha(Image.fromarray(a.astype(np.uint8)))
    out = img.copy()
    out.alpha_composite(hi)
    return out


class Particles:
    def __init__(self, W, H, n=70, seed=7):
        r = random.Random(seed)
        self.W, self.H = W, H
        self.p = [(r.uniform(0, W), r.uniform(0, H), r.uniform(18, 70), r.uniform(1.5, 5), r.uniform(0, 6.28)) for _ in range(n)]
        dot = Image.new("L", (40, 40), 0)
        ImageDraw.Draw(dot).ellipse((12, 12, 28, 28), fill=255)
        self.dot = dot.filter(ImageFilter.GaussianBlur(4))

    def draw(self, canvas, t, alpha=1.0):
        layer = Image.new("L", (self.W, self.H), 0)
        for x, y, v, s, ph in self.p:
            yy = (y - v * t) % self.H
            xx = x + 14 * math.sin(t * 0.8 + ph)
            d = self.dot.resize((int(8 * s), int(8 * s)))
            tw = 0.55 + 0.45 * math.sin(t * 3 + ph)
            layer.paste(Image.eval(d, lambda p, tw=tw: int(p * tw * alpha)), (int(xx), int(yy)), d)
        canvas.paste(Image.new("RGBA", (self.W, self.H), G.GOLD_LIGHT + (255,)), (0, 0), layer)


# ------------------------------------------------------------------ music
def music(path, seconds=15.0, sr=44100, bpm=120):
    """Royalty-free synthesized commercial beat: kick, clap, hats, bass, chord pad, risers and impacts."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    beat = 60 / bpm
    rng = np.random.default_rng(3)

    def env(length, decay):
        x = np.arange(int(length * sr)) / sr
        return np.exp(-x / decay)

    def add(sig, at, gain=1.0):
        i = int(at * sr)
        if i >= n:
            return
        j = min(n, i + len(sig))
        out[i:j] += sig[: j - i] * gain

    # kick (from 0.0), clap on 2 and 4, hats on off-beats; drop drums out for the first beat
    kx = np.arange(int(0.45 * sr)) / sr
    kick = np.sin(2 * np.pi * (45 * kx + 90 * 0.06 * (1 - np.exp(-kx / 0.06)))) * np.exp(-kx / 0.18)
    clap = rng.standard_normal(int(0.25 * sr)) * env(0.25, 0.05)
    clap = np.convolve(clap, np.ones(6) / 6, "same")
    hat = np.diff(rng.standard_normal(int(0.06 * sr) + 1)) * env(0.06, 0.012)
    nb = int(seconds / beat)
    for b in range(nb):
        at = b * beat
        if at > seconds - 1.0:
            break
        add(kick, at, 0.9)
        if b % 2 == 1:
            add(clap, at, 0.28)
        add(hat, at + beat / 2, 0.16)
        if b >= 4:
            add(hat, at + beat / 4, 0.07)
            add(hat, at + 3 * beat / 4, 0.07)

    # sidechain pump
    pump = np.ones(n)
    for b in range(nb):
        i = int(b * beat * sr)
        L = min(n - i, int(beat * sr))
        if L > 0:
            pump[i:i + L] = 0.35 + 0.65 * (1 - np.exp(-np.arange(L) / (0.09 * sr)))

    # chords: Am - F - C - G, one bar (4 beats) each
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    roots = [55.0, 43.65, 65.41, 49.0]
    bar = 4 * beat
    pad = np.zeros(n)
    bass = np.zeros(n)
    for c in range(int(seconds / bar) + 1):
        i0, i1 = int(c * bar * sr), min(n, int((c + 1) * bar * sr))
        if i0 >= n:
            break
        tt = t[i0:i1]
        for f in chords[c % 4]:
            for det in (-0.6, 0.6):
                ph = 2 * np.pi * (f + det) * tt
                pad[i0:i1] += (2 * ((ph / (2 * np.pi)) % 1) - 1) * 0.05
        r = roots[c % 4]
        # 8th-note bass
        for e in range(8):
            j0 = i0 + int(e * beat / 2 * sr)
            j1 = min(i1, j0 + int(beat / 2 * sr * 0.9))
            if j0 >= j1:
                continue
            x = np.arange(j1 - j0) / sr
            bass[j0:j1] += np.tanh(2.5 * np.sin(2 * np.pi * r * 2 * x)) * np.exp(-x / 0.2) * 0.33
    k = int(sr / 1800)
    pad = np.convolve(pad, np.ones(k) / k, "same")
    out += pad * pump + bass * pump

    # risers into the cuts and impacts on them
    for cut in (5.0, 10.0):
        L = int(1.0 * sr)
        x = np.arange(L) / L
        noise = rng.standard_normal(L)
        noise = noise - np.convolve(noise, np.ones(8) / 8, "same")
        add(noise * x ** 2 * 0.22, cut - 1.0)
        ix = np.arange(int(1.2 * sr)) / sr
        boom = np.sin(2 * np.pi * 42 * ix) * np.exp(-ix / 0.45) * 0.9 + rng.standard_normal(len(ix)) * np.exp(-ix / 0.08) * 0.25
        add(boom, cut)
    # opening hit
    ix = np.arange(int(1.0 * sr)) / sr
    add(np.sin(2 * np.pi * 40 * ix) * np.exp(-ix / 0.4) * 0.8, 0.0)

    # fades
    fi = int(0.05 * sr)
    out[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.8 * sr)
    out[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    out = np.tanh(out * 1.1)
    out /= max(1e-6, np.max(np.abs(out))) / 0.6
    data = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


# ------------------------------------------------------------------ reel
def render_reel(post, path, seconds=15, fps=30):
    W, H = 1080, 1920
    theme = post.get("theme", "staking")
    s1, s2 = SCENE_FOR[theme]
    bottom = s1 in TEXT_BOTTOM
    src1, src2 = scene(s1, 1300), scene(s2, 1300)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    M = 80
    T1, T2 = 5.0, 10.0  # cuts (on the beat)

    sh = shade(W, H, top=0.42, bottom=0.40)
    sh_b = shade(W, H, top=0.18, bottom=0.55)
    sh2 = shade(W, H, top=0.30, bottom=0.55)
    vg = vignette(W, H)
    parts = Particles(W, H)
    brand = brand_row(92)

    # scene 1 elements
    kick = G.text_layer([post["kicker"]], G.font("Montserrat-Bold.ttf", 38), G.GOLD, align="left", tracking=7)
    if post.get("price"):
        hl_src = "1 OWC =\n" + post["price"]
    else:
        hl_src = post["headline"]
    hls = []
    for l in headline_layers(hl_src, W - 2 * M, 122 if bottom else 150, upper=not post.get("price")):
        s, p = shadowed(l, 18, 170)
        hls.append((s, p, l.height))

    # scene 2: body text, large
    bf = G.font("Montserrat-ExtraBold.ttf", 64)
    body = ("Live price from CoinGecko.\n" + post["date_str"]) if post.get("price") else post["body"]
    blines = []
    for para in body.split("\n"):
        blines += G.wrap(tmp, para, bf, W - 2 * M)
    blines = blines[:5]
    bl_imgs = [shadowed(G.text_layer([l], bf, G.WHITE, align="left", spacing=1.0), 16, 200) for l in blines]

    # end card
    big_logo = G.logo(430)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W / 2 - 520, 700 - 520, W / 2 + 520, 700 + 520), fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    wm = G.text_layer(["ODUWACOIN"], G.font("Montserrat-Black.ttf", 96), None, gradient=True, tracking=6)
    tag = G.text_layer(["Africa's own Layer 1 blockchain"], G.font("Lato-Bold.ttf", 44), G.WHITE)
    cta = G.pill(post["cta"].upper(), G.font("Montserrat-ExtraBold.ttf", 50), padx=64, pady=30)
    url = G.text_layer([post["url"]], G.font("Montserrat-SemiBold.ttf", 46), G.WHITE)
    handle = G.text_layer(["@oduwacoin"], G.font("Montserrat-SemiBold.ttf", 34), G.GREY)

    pl = G.pill(post["cta"].upper(), G.font("Montserrat-ExtraBold.ttf", 42))
    tmpd = tempfile.mkdtemp()
    n = int(seconds * fps)
    for f in range(n):
        t = f / fps
        if t < T1:
            c = ken_burns(src1, W, H, t, T1, 1.22, 1.04, dy=-40, yc=0.5)
            c.alpha_composite(vg)
            c.alpha_composite(sh_b if bottom else sh)
            parts.draw(c, t, 0.5)
            a = ease_out((t - 0.15) / 0.4)
            c.alpha_composite(with_alpha(brand, a), (M, 110))
            ka = ease_out((t - 0.35) / 0.4)
            ky = (H - 290 - sum(lh - 8 for _, _, lh in hls) - kick.height - 20) if bottom else 300
            c.alpha_composite(with_alpha(kick, ka), (M + int((1 - ka) * -60), ky))
            y = ky + kick.height + 20
            for i, (img, p, lh) in enumerate(hls):
                st = 0.6 + i * 0.32
                k = (t - st) / 0.32
                if k > 0:
                    sc = 1 + (1 - ease_out(k)) * 0.55
                    im = img
                    if 1.9 + i * 0.2 < t < 2.9 + i * 0.2:
                        im = sweep(img, (t - 1.9 - i * 0.2) / 1.0)
                    w2, h2 = im.width * sc, im.height * sc
                    x = M - p
                    if sc != 1:
                        im = im.resize((int(w2), int(h2)), Image.BILINEAR)
                    c.alpha_composite(with_alpha(im, ease_out(k * 1.4)), (x, int(y - p - (h2 - img.height) / 2)))
                y += lh - 8
            # CTA teaser at bottom
            ca = ease_out((t - 2.6) / 0.5)
            if ca > 0:
                c.alpha_composite(with_alpha(pl, ca), (M, (H - 220 if bottom else H - 260) + int((1 - ca) * 50)))
        elif t < T2:
            tt = t - T1
            c = ken_burns(src2, W, H, tt, T2 - T1, 1.02, 1.16, dx=30, yc=0.52)
            c.alpha_composite(vg)
            c.alpha_composite(sh2)
            parts.draw(c, t, 0.7)
            c.alpha_composite(brand, (M, 110))
            y = H - 160 - sum(im.height - 2 * p - 2 for im, p in bl_imgs)
            for i, (img, p) in enumerate(bl_imgs):
                k = ease_out((tt - 0.25 - i * 0.28) / 0.45)
                if k > 0:
                    c.alpha_composite(with_alpha(img, k), (M - p, y - p + int((1 - k) * 70)))
                y += img.height - 2 * p - 2
        else:
            tt = t - T2
            c = Image.new("RGBA", (W, H), (6, 6, 6, 255))
            c.paste(Image.new("RGBA", (W, H), (150, 105, 10, 255)), (0, 0), glow)
            parts.draw(c, t, 1.0)
            # rotating light rays behind logo
            k = ease_back((tt - 0.05) / 0.55)
            paste_scaled(c, big_logo, W / 2, 700, max(0.0, k) * (1 + 0.02 * math.sin(tt * 3)), min(1, max(0, (tt) / 0.25)))
            wa = ease_out((tt - 0.55) / 0.45)
            c.alpha_composite(with_alpha(wm, wa), ((W - wm.width) // 2, 990 + int((1 - wa) * 40)))
            ta = ease_out((tt - 0.85) / 0.45)
            c.alpha_composite(with_alpha(tag, ta), ((W - tag.width) // 2, 1110 + int((1 - ta) * 30)))
            ck = ease_back((tt - 1.3) / 0.45)
            if ck > 0:
                im = cta
                if 2.0 < tt < 3.0:
                    im = sweep(cta, tt - 2.0)
                paste_scaled(c, im, W / 2, 1330, ck)
            ua = ease_out((tt - 1.6) / 0.4)
            c.alpha_composite(with_alpha(url, ua), ((W - url.width) // 2, 1440))
            c.alpha_composite(with_alpha(handle, ua), ((W - handle.width) // 2, H - 150))
        # flash on cuts
        for cut in (T1, T2):
            d = t - cut
            if -0.05 < d < 0.22:
                fa = max(0.0, 1 - abs(d - 0.0) / 0.22) * 0.85
                c = Image.blend(c, Image.new("RGBA", (W, H), (255, 236, 180, 255)), fa)
        c.convert("RGB").save(os.path.join(tmpd, f"f{f:04d}.jpg"), quality=94)

    wav = os.path.join(tmpd, "music.wav")
    music(wav, seconds)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmpd, "f%04d.jpg"),
        "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-preset", "medium", "-crf", "19",
        "-r", str(fps), "-g", str(fps * 2), "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-movflags", "+faststart", "-shortest", path,
    ], check=True)
    shutil.rmtree(tmpd)
