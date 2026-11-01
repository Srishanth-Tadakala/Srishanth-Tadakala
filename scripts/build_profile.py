"""PROJECT MARVEL — cinematic GitHub profile builder.

Generates every visual asset (self-contained animated SVGs) and README.md from:
    data/profile.json     verified identity / projects / achievements (hand-curated, sourced)
    data/telemetry.json   live GitHub statistics  (scripts/fetch_telemetry.py)
    assets/source/*       original AI-generated artwork + avatar
    scripts/vendor/       OFL fonts + CC0 Simple Icons

Why self-contained SVG?  GitHub proxies README images through camo and renders SVG
inside <img>, which forbids scripts and external fetches but *does* run CSS
@keyframes and SMIL. So fonts are embedded as per-file subsetted WOFF2 and artwork
as WebP data-URIs; animations use SMIL/CSS only.

Usage:  python scripts/build_profile.py
"""
from __future__ import annotations

import base64
import datetime as dt
import io
import itertools
import json
import math
import os
import random
import re
from collections import defaultdict
from xml.sax.saxutils import escape as _esc

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8"))
T = json.load(open(os.path.join(ROOT, "data", "telemetry.json"), encoding="utf-8"))
LOGIN = P["identity"]["login"]
RAW = f"https://raw.githubusercontent.com/{LOGIN}/{LOGIN}/main/"
VENDOR = os.path.join(ROOT, "scripts", "vendor")
SRC = os.path.join(ROOT, "assets", "source")

# ───────────────────────────── design tokens ─────────────────────────────
VOID, PANEL, PANEL2, LINE = "#05070D", "#0A1222", "#0E1A2E", "#1C3352"
CYAN, CYAN2, GOLD, AMBER, RED = "#3FE0FF", "#00A8E8", "#F5B942", "#FF8A1F", "#FF3B4E"
TEXT, MUTED, DIM = "#E6F1FF", "#8AA4C8", "#5B7396"
FULL_W, MOBILE_W, TILE_W = 840, 420, 415

FONT_SPECS = {  # key: (file, variable-axes, css family, fallback stack)
    "display": ("Orbitron.ttf", {"wght": 800}, "Orbitron", "'Segoe UI', Arial, sans-serif"),
    "body": ("Rajdhani-SemiBold.ttf", None, "Rajdhani", "'Segoe UI', Arial, sans-serif"),
    "bold": ("Rajdhani-Bold.ttf", None, "RajdhaniBold", "'Segoe UI', Arial, sans-serif"),
    "mono": ("JetBrainsMono.ttf", {"wght": 500}, "JBMono", "Consolas, 'Courier New', monospace"),
}
_FONT_BYTES: dict[str, bytes] = {}
_FONT_OBJ: dict[str, TTFont] = {}


def _font_bytes(key):
    if key not in _FONT_BYTES:
        fn, axes, *_ = FONT_SPECS[key]
        f = TTFont(os.path.join(VENDOR, "fonts", fn))
        if axes:
            f = instancer.instantiateVariableFont(f, axes)
        buf = io.BytesIO()
        f.save(buf)
        _FONT_BYTES[key] = buf.getvalue()
        _FONT_OBJ[key] = TTFont(io.BytesIO(_FONT_BYTES[key]))
    return _FONT_BYTES[key]


def measure(text, font="body", size=14, ls=0.0):
    _font_bytes(font)
    f = _FONT_OBJ[font]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    fallback = cmap.get(ord("n"))
    w = sum(hmtx[cmap.get(ord(c), fallback)][0] for c in text)
    return w / upm * size + ls * max(len(text) - 1, 0)


def wrap(text, font, size, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if measure(trial, font, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def font_face(key, chars):
    fn, axes, fam, _ = FONT_SPECS[key]
    font = TTFont(io.BytesIO(_font_bytes(key)))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


def esc(s):
    return _esc(str(s), {'"': "&quot;"})


# ───────────────────────────── image embedding ─────────────────────────────
_IMG_CACHE = {}


def img_uri(name, w, h, crop=None, focus=(0.5, 0.5), scale=2, q=70, circle=False):
    key = (name, w, h, crop, focus, scale, q, circle)
    if key in _IMG_CACHE:
        return _IMG_CACHE[key]
    path = os.path.join(SRC, name)
    im = Image.open(path).convert("RGBA" if circle else "RGB")
    if crop:
        im = im.crop(crop)
    else:  # cover-crop to target aspect around focus point
        tw, th = w, h
        iw, ih = im.size
        if iw / ih > tw / th:
            nw = ih * tw / th
            x0 = min(max(focus[0] * iw - nw / 2, 0), iw - nw)
            im = im.crop((int(x0), 0, int(x0 + nw), ih))
        else:
            nh = iw * th / tw
            y0 = min(max(focus[1] * ih - nh / 2, 0), ih - nh)
            im = im.crop((0, int(y0), iw, int(y0 + nh)))
    im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    if circle:
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, im.size[0] - 1, im.size[1] - 1), fill=255)
        im.putalpha(mask)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=q, method=6)
    uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    _IMG_CACHE[key] = uri
    return uri


# ───────────────────────────── icons ─────────────────────────────
BRAND = {
    "python": ("Python", "#4B8BBE"), "typescript": ("TypeScript", "#3178C6"), "javascript": ("JavaScript", "#F7DF1E"),
    "cplusplus": ("C++", "#659AD2"), "langchain": ("LangChain", "#3FD0B0"), "openai": ("OpenAI API", "#FFFFFF"),
    "ollama": ("Ollama", "#FFFFFF"), "huggingface": ("Hugging Face", "#FFD21E"), "pytorch": ("PyTorch", "#EE4C2C"),
    "tensorflow": ("TensorFlow", "#FF6F00"), "scikitlearn": ("scikit-learn", "#F7931E"), "numpy": ("NumPy", "#4DABCF"),
    "pandas": ("pandas", "#B17CFF"), "opencv": ("OpenCV", "#8D7BFF"), "mediapipe": ("MediaPipe", "#2BC4D6"),
    "threedotjs": ("Three.js", "#FFFFFF"), "fastapi": ("FastAPI", "#05C3A9"), "react": ("React", "#61DAFB"),
    "nextdotjs": ("Next.js", "#FFFFFF"), "nodedotjs": ("Node.js", "#7BC86C"), "vite": ("Vite", "#8B91FF"),
    "tailwindcss": ("Tailwind", "#06B6D4"), "postgresql": ("PostgreSQL", "#6C8EF5"), "supabase": ("Supabase", "#3FCF8E"),
    "mongodb": ("MongoDB", "#5FCB5F"), "redis": ("Redis", "#FF4438"), "sqlite": ("SQLite", "#4FA8D8"),
    "docker": ("Docker", "#2496ED"), "githubactions": ("Actions", "#2088FF"), "googlecloud": ("Google Cloud", "#4285F4"),
    "vercel": ("Vercel", "#FFFFFF"), "render": ("Render", "#FFFFFF"), "git": ("Git", "#F05032"),
    "github": ("GitHub", "#FFFFFF"), "linux": ("Linux", "#FCC624"), "postman": ("Postman", "#FF6C37"),
    "figma": ("Figma", "#F24E1E"), "instagram": ("Instagram", "#E4405F"), "facebook": ("Facebook", "#4B8DFF"),
    "gmail": ("Email", "#EA4335"), "linkedin": ("LinkedIn", "#2D8CFF"),
    "groq": ("Groq LPU", "#F55036"), "pgvector": ("pgvector", "#3FE0FF"),
}
_ICON = {}
CUSTOM_ICONS = {
    # LPU processor die with pins and lightning core (24x24)
    "groq": (
        '<g fill="none" stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="5.5" y="5.5" width="13" height="13" rx="2.5"/>'
        '<path d="M9 2.5v3M15 2.5v3M9 18.5v3M15 18.5v3M2.5 9h3M2.5 15h3M18.5 9h3M18.5 15h3"/>'
        '<path d="M13 8.2L9.8 12.4h2.5L11 15.8l3.4-4.3h-2.5z" fill="{c}" stroke="none"/></g>'
    ),
    # 3D vector embedding axes + connected embedding nodes (24x24)
    "pgvector": (
        '<g fill="none" stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 18V5M4 18h14M4 18l9-8"/>'
        '<circle cx="17.5" cy="6.5" r="2.3" fill="{c}"/>'
        '<circle cx="13" cy="10" r="1.9" fill="{c}"/>'
        '<circle cx="9.5" cy="7" r="1.7" fill="{c}"/>'
        '<path d="M9.5 7L13 10l4.5-3.5" stroke-opacity=".75"/></g>'
    ),
}


def icon_path(slug):
    if slug not in _ICON:
        raw = open(os.path.join(VENDOR, "icons", slug + ".svg"), encoding="utf-8").read()
        _ICON[slug] = re.search(r'<path d="([^"]+)"', raw).group(1)
    return _ICON[slug]


def icon(slug, x, y, size, color=None):
    col = color or BRAND[slug][1]
    s = size / 24
    if slug in CUSTOM_ICONS:
        inner = CUSTOM_ICONS[slug].format(c=col)
        return f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.4f})">{inner}</g>'
    return f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" d="{icon_path(slug)}" fill="{col}"/>'


GLYPHS = {  # 24-unit stroke icons for medals
    "trophy": "M7 4h10v3a5 5 0 0 1-10 0z M7 5H4v1.5A3 3 0 0 0 7 9.5 M17 5h3v1.5a3 3 0 0 1-3 3 M10.5 12.5h3v3.5h-3z M8 19h8",
    "star": "M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z",
    "rocket": "M12 2.5c3 2.2 4.6 5.8 4.6 9.6l-1.8 3.9H9.2l-1.8-3.9c0-3.8 1.6-7.4 4.6-9.6z M9.3 16l-2.8 3.2 M14.7 16l2.8 3.2 M12 18v3.5 M12 8.2a1.7 1.7 0 1 0 0.01 0",
    "shield": "M12 2.5l7.5 2.8v6c0 4.6-3.2 8.4-7.5 10.2C7.7 19.7 4.5 15.9 4.5 11.3v-6z M8.6 12l2.4 2.4 4.5-4.8",
    "code": "M8 7l-5 5 5 5 M16 7l5 5-5 5 M13.8 4.5l-3.6 15",
}

# ───────────────────────────── SVG document ─────────────────────────────
BASE_CSS = f"""
.fu{{animation:fu .9s cubic-bezier(.2,.7,.2,1) both}}
@keyframes fu{{from{{opacity:0;transform:translateY(8px)}}}}
.fi{{animation:fi 1.2s ease both}}
@keyframes fi{{from{{opacity:0}}}}
.pulse{{animation:pulse 3.2s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
.blink{{animation:blink 1.4s steps(1) infinite}}
@keyframes blink{{50%{{opacity:.15}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
"""


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.css = [], [], []
        self.chars = defaultdict(set)
        self._ids = itertools.count()

    def uid(self, p="i"):
        return f"{p}{next(self._ids)}"

    def add(self, *parts):
        self.body.extend(parts)

    def text(self, x, y, s, font="body", size=14, fill=TEXT, anchor="start", ls=0, cls="", extra=""):
        self.chars[font].update(str(s))
        fam = FONT_SPECS[font][2]
        attrs = f'x="{x:.1f}" y="{y:.1f}" font-family="{fam}, {FONT_SPECS[font][3]}" font-size="{size}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        if ls:
            attrs += f' letter-spacing="{ls}"'
        if cls:
            attrs += f' class="{cls}"'
        return f'<text {attrs} fill="{fill}" {extra}>{esc(s)}</text>'

    def render(self):
        faces = "".join(font_face(k, v) for k, v in self.chars.items() if v)
        style = faces + BASE_CSS + "".join(self.css)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="ttl">'
                f'<title id="ttl">{esc(self.title)}</title><defs>{"".join(self.defs)}</defs>'
                f'<style>{style}</style>{"".join(self.body)}</svg>')


def write(rel, svg: Svg):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = svg.render()
    open(path, "w", encoding="utf-8").write(data)
    BUILT.append((rel, len(data.encode())))
    return rel


BUILT: list = []


# ───────────────────────────── shared components ─────────────────────────────
def brackets(x, y, w, h, color, L=14, sw=2, op=1):
    p = (f"M{x},{y + L}V{y}H{x + L} M{x + w - L},{y}H{x + w}V{y + L} "
         f"M{x + w},{y + h - L}V{y + h}H{x + w - L} M{x + L},{y + h}H{x}V{y + h - L}")
    return f'<path d="{p}" fill="none" stroke="{color}" stroke-width="{sw}" opacity="{op}"/>'


def panel(s: Svg, w, h, accent=CYAN, label=None, code=None, r=12):
    g = s.uid("pg")
    s.defs.append(f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0C1628"/>'
                  f'<stop offset="1" stop-color="#060B15"/></linearGradient>')
    s.add(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" fill="url(#{g})" stroke="#1E3A5F" stroke-width="1.5"/>',
          brackets(6, 6, w - 12, h - 12, accent, 12, 1.6, .9))
    if label:
        s.add(f'<rect x="18" y="20" width="6" height="6" fill="{accent}" transform="rotate(45 21 23)"/>',
              s.text(32, 27, label, "mono", 10.5, accent, ls=1.2))
        if code:
            s.add(s.text(w - 20, 27, code, "mono", 9.5, DIM, "end", ls=1))
        s.add(f'<line x1="18" y1="38" x2="{w - 18}" y2="38" stroke="{LINE}"/>')
        for i in range(0, 5):
            s.add(f'<line x1="{w - 18 - i * 6}" y1="35" x2="{w - 18 - i * 6}" y2="38" stroke="{accent}" opacity=".6"/>')


def chip(s: Svg, x, y, label, color=CYAN, size=10, pad=7, h=20):
    w = measure(label, "mono", size, .4) + pad * 2
    s.add(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="4" fill="{color}" fill-opacity=".08" '
          f'stroke="{color}" stroke-opacity=".45"/>',
          s.text(x + pad, y + h / 2 + size * .36, label, "mono", size, color, ls=.4))
    return w


def spin(dur, reverse=False):
    a, b = ("360", "0") if reverse else ("0", "360")
    return f'<animateTransform attributeName="transform" type="rotate" from="{a}" to="{b}" dur="{dur}s" repeatCount="indefinite"/>'


def reactor(s: Svg, cx, cy, k=1.0, glow=True):
    """Arc-reactor-inspired energy rings (original design) with a mystic rune ring."""
    rg = s.uid("rg")
    s.defs.append(f'<radialGradient id="{rg}"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>'
                  f'<stop offset=".45" stop-color="{CYAN2}" stop-opacity=".18"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>')
    out = [f'<g transform="translate({cx} {cy}) scale({k})">']
    if glow:
        out.append(f'<circle r="150" fill="url(#{rg})" class="pulse"/>')
    ticks = "".join(f'<line x1="0" y1="-128" x2="0" y2="{-122 if i % 3 else -116}" transform="rotate({i * 5})"/>' for i in range(72))
    out.append(f'<g stroke="{CYAN}" stroke-width="1.2" opacity=".45">{ticks}</g>')
    out.append(f'<g>{spin(46, True)}<circle r="112" fill="none" stroke="{GOLD}" stroke-width="1.6" '
               f'stroke-dasharray="18 7 3 7" opacity=".85"/>'
               + "".join(f'<rect x="-3" y="-116" width="6" height="8" fill="{AMBER}" transform="rotate({i * 45})"/>' for i in range(8))
               + "</g>")
    out.append(f'<g>{spin(20)}<circle r="96" fill="none" stroke="{CYAN}" stroke-width="2" stroke-dasharray="2 6"/>'
               f'<path d="M0,-86 A86,86 0 0 1 74.5,-43" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linecap="round"/>'
               f'<path d="M0,86 A86,86 0 0 1 -74.5,43" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linecap="round"/></g>')
    out.append(f'<g>{spin(9, True)}<path d="M-60,-30 A67,67 0 0 1 -30,-60" fill="none" stroke="{GOLD}" stroke-width="2.5"/>'
               f'<path d="M60,30 A67,67 0 0 1 30,60" fill="none" stroke="{GOLD}" stroke-width="2.5"/></g>')
    out.append("</g>")
    return "".join(out)


def particles(s: Svg, x0, y0, x1, y1, n, seed=7, colors=(GOLD, CYAN, AMBER)):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        d, r, c = rnd.uniform(5, 11), rnd.uniform(.8, 2.1), rnd.choice(colors)
        b = -rnd.uniform(0, d)
        rise = rnd.uniform(30, 80)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{c}" opacity="0">'
                   f'<animate attributeName="cy" values="{y:.0f};{y - rise:.0f}" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0;.9;0" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


def scanline(s: Svg, x, y, w, h, dur=7, color=CYAN, op=.10, band=70):
    g = s.uid("sl")
    s.defs.append(f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="{color}" stop-opacity="{op}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>')
    return (f'<rect x="{x}" y="{y - band}" width="{w}" height="{band}" fill="url(#{g})">'
            f'<animate attributeName="y" values="{y - band};{y + h}" dur="{dur}s" repeatCount="indefinite"/></rect>')


def sweep(s: Svg, x, y, w, h, dur=6, op=.16, band=90):
    g = s.uid("sw")
    s.defs.append(f'<linearGradient id="{g}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="{CYAN}" stop-opacity="{op}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>')
    return (f'<rect x="{x - band}" y="{y}" width="{band}" height="{h}" fill="url(#{g})">'
            f'<animate attributeName="x" values="{x - band};{x + w};{x + w}" keyTimes="0;.55;1" dur="{dur}s" repeatCount="indefinite"/></rect>')


# ───────────────────────────── MODULE 01 · HERO ─────────────────────────────
HERO_SRC = (1376, 768)
REACTOR_SRC = (905, 365)


def hero(mobile=False):
    idn = P["identity"]
    if not mobile:
        W, H = FULL_W, 360
        crop = (0, 84, 1376, 674)
        k = W / 1376
        rx, ry = (REACTOR_SRC[0] - crop[0]) * k, (REACTOR_SRC[1] - crop[1]) * k
        img_w, img_h = W, H
    else:
        W, H = MOBILE_W, 560
        crop = (136, 0, 1376, 768)
        img_w, img_h = W, 260
        k = img_w / (crop[2] - crop[0])
        rx, ry = (REACTOR_SRC[0] - crop[0]) * k, (REACTOR_SRC[1] - crop[1]) * k
    s = Svg(W, H, f"{idn['name']} — {idn['title']}. {idn['tagline']}")
    clip, ov, fade = s.uid("c"), s.uid("ov"), s.uid("fd")
    s.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
    s.defs.append(f'<linearGradient id="{ov}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{VOID}" stop-opacity=".96"/>'
                  f'<stop offset=".42" stop-color="{VOID}" stop-opacity=".72"/><stop offset=".75" stop-color="{VOID}" stop-opacity=".12"/>'
                  f'<stop offset="1" stop-color="{VOID}" stop-opacity=".35"/></linearGradient>')
    s.defs.append(f'<linearGradient id="{fade}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VOID}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{VOID}" stop-opacity="1"/></linearGradient>')
    uri = img_uri("hero.webp", img_w, img_h, crop=crop, q=68)
    s.add(f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{VOID}"/>'
          f'<image href="{uri}" width="{img_w}" height="{img_h}" preserveAspectRatio="xMidYMid slice"/>')
    if not mobile:
        s.add(f'<rect width="{W}" height="{H}" fill="url(#{ov})"/>')
    else:
        s.add(f'<rect y="{img_h - 110}" width="{W}" height="111" fill="url(#{fade})"/>')
    s.add(reactor(s, round(rx), round(ry), k=(.62 if not mobile else .33)))
    s.add(particles(s, W * .35 if not mobile else 0, 40, W, H - 20, 26 if not mobile else 16))
    s.add(scanline(s, 0, 0, W, H, 7.5))
    s.add("</g>")
    # HUD chrome
    s.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="#1E3A5F" stroke-width="1.5"/>',
          brackets(10, 10, W - 20, H - 20, CYAN, 18, 2))
    s.add(s.text(26, 34, "SYS://PROFILE.CORE", "mono", 10, CYAN, ls=1.5),
          f'<circle cx="{W - 84}" cy="30.5" r="3.5" fill="{CYAN}" class="blink"/>',
          s.text(W - 26, 34, "ONLINE", "mono", 10, CYAN, "end", ls=1.5))
    # title — immediately crisp & high-contrast from t=0s, with looping specular sweep
    fs = 48 if not mobile else 40
    if not mobile:
        tx, y1, y2 = 36, 138, 192
    else:
        tx, y1, y2 = 22, 314, 360
    sh, tf1, tf2 = s.uid("sh"), s.uid("tf1"), s.uid("tf2")
    s.defs.append(f'<linearGradient id="{tf1}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/>'
                  f'<stop offset="1" stop-color="#D7F7FF"/></linearGradient>')
    s.defs.append(f'<linearGradient id="{tf2}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8AF3FF"/>'
                  f'<stop offset="1" stop-color="#19B5EC"/></linearGradient>')
    s.defs.append(f'<linearGradient id="{sh}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="150" y2="0" gradientTransform="translate(-260 0)">'
                  f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".85"/>'
                  f'<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
                  f'<animateTransform attributeName="gradientTransform" type="translate" values="-260 0;{W} 0;{W} 0" keyTimes="0;.48;1" dur="6.5s" repeatCount="indefinite"/></linearGradient>')
    first, last = idn["name"].upper().split(" ", 1)
    for word, y, grad in ((first, y1, tf1), (last, y2, tf2)):
        s.add(s.text(tx, y, word, "display", fs, f"url(#{grad})", ls=2.5,
                     extra=f'stroke="{CYAN}" stroke-opacity=".35" stroke-width="1"'),
              s.text(tx, y, word, "display", fs, f"url(#{sh})", ls=2.5))
    # role + tagline — immediately legible from t=0s
    ry0 = y2 + 20 if not mobile else y2 + 18
    rw = measure(idn["title"].upper(), "display", 13.5, 2.8) + 32
    s.add(f'<path d="M{tx},{ry0} h{rw:.1f} l8,14 l-8,14 h-{rw:.1f} z" fill="{GOLD}" fill-opacity=".14" stroke="{GOLD}" stroke-opacity=".8"/>',
          s.text(tx + 14, ry0 + 19, idn["title"].upper(), "display", 13.5, GOLD, ls=2.8))
    if not mobile:
        sub_short = "CS STUDENT · OPEN SOURCE"
        sw2 = measure(sub_short, "mono", 9.5, .9) + 20
        sx2 = tx + rw + 14
        s.add(f'<rect x="{sx2:.1f}" y="{ry0 + 2}" width="{sw2:.1f}" height="24" rx="4" fill="{VOID}" fill-opacity=".75" stroke="{LINE}"/>',
              s.text(sx2 + 10, ry0 + 18, sub_short, "mono", 9.5, "#C7DCF5", ls=.9))
    else:
        sub = "  ·  ".join(r.upper() for r in idn["roles"][1:])
        s.add(s.text(tx, ry0 + 48, sub, "mono", 9.5, "#B4CCE8", ls=.6))
    ty = ry0 + 58 if not mobile else ry0 + 78
    maxw = 450 if not mobile else W - 44
    for i, line in enumerate(wrap(f"“{idn['tagline']}”", "body", 18.5 if not mobile else 17, maxw)):
        s.add(s.text(tx, ty + i * 23, line, "body", 18.5 if not mobile else 17, "#DCEEFF"))
    by = H - 24
    s.add(f'<line x1="{tx}" y1="{by - 18}" x2="{W - 26}" y2="{by - 18}" stroke="{LINE}"/>')
    s.add(s.text(tx, by, "AGENTS · RAG · VOICE AI · COMPUTER VISION" if not mobile else "AGENTS · RAG · VOICE AI · CV",
                 "mono", 10, CYAN, ls=1.2))
    if not mobile:
        s.add(f'<circle cx="{W - 222}" cy="{by - 3.5}" r="3.5" fill="{GOLD}" class="blink"/>',
              s.text(W - 26, by, "CURRENT MISSION ▸ SYLVIE", "mono", 10, GOLD, "end", ls=1.2))
    return s


# ───────────────────────────── NAV + SECTION HEADERS ─────────────────────────────
MODULES = [
    ("dossier", "01", "INTELLIGENCE DOSSIER", "// PERSONNEL FILE · MISSION BRIEF"),
    ("arsenal", "02", "TECHNOLOGY ARSENAL", "// SYSTEMS I BUILD WITH"),
    ("multiverse", "03", "PROJECT MULTIVERSE", "// REAL REPOSITORIES · REAL ENGINEERING"),
    ("command", "04", "COMMAND CENTER", "// LIVE GITHUB TELEMETRY · AUTO-SYNCED DAILY"),
    ("archive", "05", "MISSION ARCHIVE", "// VERIFIED MILESTONES"),
    ("uplink", "06", "COMMUNICATION UPLINK", "// OPEN A CHANNEL"),
]
NAV_LABELS = {
    "dossier": "DOSSIER",
    "arsenal": "ARSENAL",
    "multiverse": "MULTIVERSE",
    "command": "COMMAND",
    "archive": "ARCHIVE",
    "uplink": "UPLINK",
}


def nav_pill(num, label):
    w = int(measure(f"{num} {label}", "mono", 10.5, 1.2) + 40)
    s = Svg(w, 32, f"{label.title()} section")
    s.add(f'<rect x=".75" y=".75" width="{w - 1.5}" height="30.5" rx="6" fill="{PANEL}" stroke="{CYAN}" stroke-opacity=".6" stroke-width="1.2"/>',
          f'<rect x="12" y="13" width="6" height="6" fill="{GOLD}" transform="rotate(45 15 16)"/>',
          s.text(26, 20, num, "mono", 10.5, GOLD, ls=1.2),
          s.text(26 + measure(num + " ", "mono", 10.5, 1.2), 20, label, "mono", 10.5, TEXT, ls=1.2))
    return s


def section_header(num, title, subtitle, w):
    mobile = w < 600
    s = Svg(w, 74, f"{num} · {title}")
    s.add(f'<rect x=".75" y=".75" width="{w - 1.5}" height="72.5" rx="10" fill="{PANEL}" stroke="#1E3A5F" stroke-width="1.5"/>')
    # hex badge with rotating ring
    hx, hy = 38, 37
    hexp = " ".join(f"{hx + 20 * math.cos(math.radians(a)):.1f},{hy + 20 * math.sin(math.radians(a)):.1f}" for a in range(30, 390, 60))
    s.add(f'<g transform="translate({hx} {hy})"><g>{spin(14)}<circle r="27" fill="none" stroke="{GOLD}" stroke-width="1.2" stroke-dasharray="3 5" opacity=".7"/></g></g>',
          f'<polygon points="{hexp}" fill="{GOLD}" fill-opacity=".1" stroke="{GOLD}"/>',
          s.text(hx, hy + 5.5, num, "display", 15, GOLD, "middle"))
    ts = 20 if not mobile else 17
    s.add(s.text(78, 35, title, "display", ts, TEXT, ls=2.5),
          s.text(78, 56, subtitle, "mono", 10 if not mobile else 9, MUTED, ls=.8))
    tw = measure(title, "display", ts, 2.5)
    x1, x2, ly = 78 + tw + 18, w - 44, 29
    if x2 - x1 < 60:
        x1, ly = 78, 66
    L = x2 - x1
    s.add(f'<line x1="{x1:.0f}" y1="{ly}" x2="{x2}" y2="{ly}" stroke="{LINE}" stroke-width="2"/>',
          f'<line x1="{x1:.0f}" y1="{ly}" x2="{x2}" y2="{ly}" stroke="{CYAN}" stroke-width="2" stroke-linecap="round" '
          f'stroke-dasharray="70 {L + 70:.0f}"><animate attributeName="stroke-dashoffset" values="70;{-L:.0f}" dur="3.6s" repeatCount="indefinite"/></line>')
    s.add(f'<g transform="translate({w - 24} {ly})"><g>{spin(8, True)}<rect x="-6" y="-6" width="12" height="12" fill="none" stroke="{CYAN}" transform="rotate(45)"/></g>'
          f'<circle r="2.5" fill="{CYAN}" class="pulse"/></g>')
    return s


# ───────────────────────────── MODULE 01b · DOSSIER ─────────────────────────────
def dossier_personnel():
    idn, edu = P["identity"], P["education"]
    W, H = TILE_W, 440
    s = Svg(W, H, f"Personnel file: {idn['name']}, {idn['title']}. " + "; ".join(f"{e['degree']}, {e['school']} ({e['detail']})" for e in edu) + f". Origin: {idn['origin']}.")
    panel(s, W, H, CYAN, "PERSONNEL FILE", "FILE 001")
    cx, cy = 82, 112
    s.add(f'<image href="{img_uri("avatar.png", 92, 92, circle=True, q=80)}" x="{cx - 46}" y="{cy - 46}" width="92" height="92"/>',
          f'<g transform="translate({cx} {cy})"><circle r="48" fill="none" stroke="{CYAN}" stroke-width="1.5"/>'
          f'<g>{spin(16)}<circle r="56" fill="none" stroke="{CYAN}" stroke-width="1.2" stroke-dasharray="4 6" opacity=".8"/>'
          f'<path d="M0,-56 A56,56 0 0 1 48.5,-28" fill="none" stroke="{CYAN}" stroke-width="3"/></g>'
          f'<g>{spin(30, True)}<circle r="64" fill="none" stroke="{GOLD}" stroke-width="1" stroke-dasharray="14 6 2 6" opacity=".75"/></g></g>')
    first, last = idn["name"].upper().split(" ", 1)
    s.add(s.text(160, 92, first, "display", 17, TEXT, ls=1.5), s.text(160, 115, last, "display", 17, TEXT, ls=1.5),
          s.text(160, 139, idn["title"].upper(), "mono", 11, GOLD, ls=1.5),
          f'<circle cx="164" cy="155" r="3" fill="{CYAN}" class="blink"/>', s.text(173, 159, "ACTIVE · OPEN SOURCE", "mono", 9.5, CYAN, ls=1))
    fields = [
        ("CURRENT TRAINING", edu[0]["degree"], f"{edu[0]['school']} · {edu[0]['detail']}"),
        ("PRIOR TRAINING", edu[1]["degree"], f"{edu[1]['school']} · {edu[1]['detail']}"),
        ("ORIGIN", idn["origin"], "India"),
        ("DESIGNATION", " · ".join(idn["roles"][1:]), "Builds autonomous, human-like AI systems"),
    ]
    y = 204
    for i, (lab, val, det) in enumerate(fields):
        s.add(f'<rect x="20" y="{y - 13}" width="3" height="44" fill="{GOLD if i < 2 else CYAN}"/>',
              s.text(34, y, lab, "mono", 9.5, MUTED, ls=1.4),
              s.text(34, y + 19, val, "bold", 16.5, TEXT),
              s.text(34, y + 36, det, "body", 13.5, MUTED))
        y += 58
    s.add(scanline(s, 8, 44, W - 16, H - 52, 9, CYAN, .06, 60))
    return s


def dossier_mission():
    W, H = TILE_W, 440
    m = P["mission"]["current"]
    s = Svg(W, H, f"Mission brief. Current mission: {m}. Research interests: {', '.join(P['interests'])}. "
                  f"Learning: {', '.join(P['learning'])}. Philosophy: {'. '.join(P['identity']['philosophy'])}.")
    panel(s, W, H, GOLD, "MISSION BRIEF", "STATUS: LIVE")
    ip_x = W - 20 - measure("IN PROGRESS", "mono", 9, 1) - 10
    s.add(s.text(20, 64, "CURRENT MISSION", "mono", 9.5, GOLD, ls=1.4),
          f'<circle cx="{ip_x:.1f}" cy="60.5" r="3.5" fill="{RED}" class="blink"/>',
          s.text(W - 20, 64, "IN PROGRESS", "mono", 9, RED, "end", ls=1))
    y = 86
    for line in wrap(m, "body", 15.5, W - 40):
        s.add(s.text(20, y, line, "body", 15.5, TEXT))
        y += 20
    y += 14
    s.add(s.text(20, y, "RESEARCH VECTORS", "mono", 9.5, CYAN, ls=1.4))
    x, y = 20, y + 10
    for it in P["interests"]:
        w = measure(it.upper(), "mono", 9.5, .4) + 14
        if x + w > W - 20:
            x, y = 20, y + 26
        chip(s, x, y, it.upper(), CYAN, 9.5)
        x += w + 6
    y += 48
    s.add(s.text(20, y, "IN TRAINING", "mono", 9.5, CYAN, ls=1.4))
    y += 8
    s.css.append(".ld{animation:ld 2.8s ease-in-out infinite}@keyframes ld{0%{transform:translateX(-60px)}100%{transform:translateX(140px)}}")
    for i, it in enumerate(P["learning"]):
        yy = y + 14 + i * 22
        s.add(s.text(20, yy + 4, "▸", "mono", 11, GOLD), s.text(36, yy + 4, it, "body", 14.5, TEXT))
        bx = W - 120
        clip = s.uid("lc")
        s.defs.append(f'<clipPath id="{clip}"><rect x="{bx}" y="{yy - 2}" width="100" height="4" rx="2"/></clipPath>')
        s.add(f'<rect x="{bx}" y="{yy - 2}" width="100" height="4" rx="2" fill="{LINE}"/>',
              f'<g clip-path="url(#{clip})"><rect x="{bx}" y="{yy - 2}" width="40" height="4" rx="2" fill="{CYAN}" class="ld" '
              f'style="animation-delay:{i * .35:.2f}s"/></g>')
    y += 22 * len(P["learning"]) + 30
    s.add(s.text(20, y, "DOCTRINE", "mono", 9.5, GOLD, ls=1.4))
    words = [w.upper() for w in P["identity"]["philosophy"]]
    x, y = 20, y + 26
    n = len(words)
    word_ws = [measure(t, "display", 11.8, 1.2) for t in words]
    gap = (W - 40 - sum(word_ws)) / max(n - 1, 1)
    for i, (t, ww) in enumerate(zip(words, word_ws)):
        s.add(s.text(x, y, t, "display", 11.8, "#6E87AB", ls=1.2))
        kt = f"0;{i / n:.3f};{(i + .9) / n:.3f};1"
        s.add(s.text(x, y, t, "display", 11.8, GOLD, ls=1.2, extra='opacity="0"').replace(
            "</text>", f'<animate attributeName="opacity" values="0;0;1;0" keyTimes="{kt}" dur="6s" repeatCount="indefinite"/></text>'))
        x += ww
        if i < n - 1:
            s.add(s.text(x + gap / 2, y, "·", "display", 12, GOLD, "middle"))
            x += gap
    return s


# ───────────────────────────── MODULE 02 · ARSENAL ─────────────────────────────
def arsenal_tile(cats, label, code):
    W = TILE_W
    H = 48 + len(cats) * 104
    names = [BRAND[i][0] for c in cats for i in c["items"]] + [e for c in cats for e in c.get("extra", [])]
    s = Svg(W, H, f"{label}: " + ", ".join(names))
    panel(s, W, H, CYAN, label, code)
    y = 66
    k = 0
    total = sum(len(c["items"]) + len(c.get("extra", [])) for c in cats)
    for c in cats:
        s.add(s.text(20, y, c["cat"], "mono", 9.5, GOLD, ls=1.4))
        lw = measure(c["cat"], "mono", 9.5, 1.4)
        s.add(f'<line x1="{26 + lw:.0f}" y1="{y - 3}" x2="{W - 20}" y2="{y - 3}" stroke="{LINE}" stroke-dasharray="2 3"/>')
        x = 20
        entries = [("icon", i) for i in c["items"]] + [("text", e) for e in c.get("extra", [])]
        for kind, it in entries:
            cy = y + 10
            s.add(f'<rect x="{x}" y="{cy}" width="52" height="52" rx="10" fill="{PANEL2}" stroke="{LINE}"/>')
            # sequential highlight sweep across every chip in the tile
            kt0 = k / total
            s.add(f'<rect x="{x}" y="{cy}" width="52" height="52" rx="10" fill="{CYAN}" fill-opacity=".06" stroke="{CYAN}" opacity="0">'
                  f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{kt0 * .8:.3f};{kt0 * .8 + .04:.3f};{kt0 * .8 + .12:.3f};1" dur="9s" repeatCount="indefinite"/></rect>')
            if kind == "icon":
                s.add(icon(it, x + 13, cy + 13, 26))
                name = BRAND[it][0]
            else:
                big, name = it.split(" ", 1) if " " in it else (it, "")
                s.add(s.text(x + 26, cy + 31, big.upper(), "display", 10.5, CYAN, "middle", ls=.5))
                name = name or big
            fs = 11.5
            while measure(name, "body", fs) > 58 and fs > 9:
                fs -= .5
            s.add(s.text(x + 26, cy + 70, name, "body", fs, MUTED, "middle"))
            x += 59
            k += 1
        y += 104
    return s


# ───────────────────────────── MODULE 03 · PROJECTS ─────────────────────────────
FOCUS = {"friday": (.6, .5), "sylvie": (.62, .45), "sales": (.62, .5), "aeris": (.72, .45), "omniaction": (.6, .5), "queueless": (.62, .55)}


def project_card(p):
    W, IH = TILE_W, 196
    H = 448
    alt = f"{p['name']} — {p['summary']} Key facts: {'; '.join(p['facts'])}. Stack: {', '.join(p['stack'])}. Status: {p['status']}."
    s = Svg(W, H, alt)
    acc = p["accent"]
    clip, fade = s.uid("pc"), s.uid("pf")
    s.defs.append(f'<clipPath id="{clip}"><rect x="1" y="1" width="{W - 2}" height="{IH}" rx="12"/></clipPath>')
    s.defs.append(f'<linearGradient id="{fade}" x1="0" y1="0" x2="0" y2="1"><stop offset=".45" stop-color="#0C1628" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="#0C1628"/></linearGradient>')
    panel(s, W, H, acc)
    s.add(f'<g clip-path="url(#{clip})"><image href="{img_uri(p["id"] + ".webp", W, IH, focus=FOCUS.get(p["id"], (.5, .5)), q=64)}" '
          f'x="1" y="1" width="{W - 2}" height="{IH}" preserveAspectRatio="xMidYMid slice"/>'
          f'<rect x="1" y="1" width="{W - 2}" height="{IH}" fill="url(#{fade})"/>{sweep(s, 1, 1, W, IH, 7)}</g>')
    s.add(brackets(14, 14, W - 28, IH - 26, acc, 12, 1.5, .9))
    # codename + status tags
    cw = measure(p["codename"], "mono", 9, .8) + 16
    s.add(f'<rect x="22" y="22" width="{cw:.0f}" height="20" rx="3" fill="{VOID}" fill-opacity=".78" stroke="{GOLD}" stroke-opacity=".6"/>',
          s.text(30, 35.5, p["codename"], "mono", 9, GOLD, ls=.8))
    st = p["status"]
    sw_ = measure(st, "mono", 9, .8) + 28
    s.add(f'<rect x="{W - 22 - sw_:.0f}" y="{IH - 34}" width="{sw_:.0f}" height="20" rx="10" fill="{VOID}" fill-opacity=".8" stroke="{acc}" stroke-opacity=".7"/>',
          f'<circle cx="{W - 22 - sw_ + 12:.0f}" cy="{IH - 24}" r="3" fill="{acc}" class="blink"/>',
          s.text(W - 22 - sw_ + 21, IH - 20.5, st, "mono", 9, acc, ls=.8))
    y = IH + 32
    s.add(s.text(20, y, p["name"], "display", 20, TEXT, ls=2))
    y += 24
    for line in wrap(p["summary"], "body", 15, W - 40)[:3]:
        s.add(s.text(20, y, line, "body", 15, "#C9DBF2"))
        y += 19
    y += 10
    for i, f in enumerate(p["facts"]):
        s.add(f'<rect x="22" y="{y - 8}" width="6" height="6" fill="{acc}" transform="rotate(45 25 {y - 5})"/>',
              s.text(36, y, f, "body", 14, TEXT))
        y += 21
    x, cy = 20, H - 42
    for t in p["stack"]:
        w = measure(t.upper(), "mono", 9, .4) + 14
        if x + w > W - 20:
            break
        chip(s, x, cy, t.upper(), MUTED if acc == CYAN else GOLD, 9)
        x += w + 6
    return s


# ───────────────────────────── MODULE 04 · COMMAND CENTER ─────────────────────────────
LEVELS = ["#0F1B2D", "#0E4D64", "#108AA8", "#23C2E0", "#7FF3FF"]


def heatmap(mobile=False):
    cal = T["calendar"]
    weeks = defaultdict(list)
    first = dt.date.fromisoformat(cal[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # sunday-start like GitHub
    for d in cal:
        dd = dt.date.fromisoformat(d["date"])
        weeks[(dd - start).days // 7].append((dd, d))
    keys = sorted(weeks)
    if mobile:
        keys = keys[-24:]
    W = MOBILE_W if mobile else FULL_W
    cell, gap = (12, 3) if mobile else (11, 3)
    x0, y0 = (40 if mobile else 56), 74
    H = y0 + 7 * (cell + gap) + (86 if mobile else 56)
    total, active = T["contributions_last_year"], T["active_days"]
    span = "LAST 24 WEEKS" if mobile else "LAST 12 MONTHS"
    shown = sum(d["count"] for k in keys for _, d in weeks[k])
    s = Svg(W, H, f"Contribution radar: {total} contributions and {active} active days in the last year (synced {T['synced_at']}).")
    panel(s, W, H, CYAN, f"CONTRIBUTION RADAR // {span}", f"SYNC {T['synced_at']}")
    last_month = None
    for ci, k in enumerate(keys):
        x = x0 + ci * (cell + gap)
        for dd, d in weeks[k]:
            row = (dd.weekday() + 1) % 7
            s.add(f'<rect x="{x}" y="{y0 + row * (cell + gap)}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[d["level"]]}"/>')
            if dd.day <= 7 and row == 0 and dd.month != last_month:
                s.add(s.text(x, y0 - 10, dd.strftime("%b").upper(), "mono", 9, MUTED, ls=.5))
                last_month = dd.month
    for row, lab in ((1, "MON"), (3, "WED"), (5, "FRI")):
        s.add(s.text(x0 - 8, y0 + row * (cell + gap) + cell - 2, lab, "mono", 8.5, DIM, "end"))
    gw = len(keys) * (cell + gap)
    s.add(sweep(s, x0, y0 - 4, gw, 7 * (cell + gap) + 4, 8, .22, 60))
    by = y0 + 7 * (cell + gap) + 30
    best = T["best_day"]
    bd = dt.date.fromisoformat(best["date"]).strftime("%b %d").upper()
    stats = [(f"{total}", "CONTRIBUTIONS / YR"), (f"{active}", "ACTIVE DAYS"), (f"{best['count']}", f"PEAK · {bd}")]
    if mobile:
        stats = [(f"{shown}", "LAST 24 WEEKS"), (f"{total}", f"LAST 12MO · {active}D")]
    sx = x0
    for v, lab in stats:
        s.add(s.text(sx, by, v, "display", 16, CYAN), s.text(sx + measure(v, "display", 16) + 8, by, lab, "mono", 9, MUTED, ls=1))
        sx += measure(v, "display", 16) + measure(lab, "mono", 9, 1) + 30
    lx = W - 20 - 5 * 14 - 34
    ly = by if not mobile else by + 30
    if mobile:
        lx = x0 + 34
    s.add(s.text(lx - 6, ly, "LESS", "mono", 8.5, DIM, "end"))
    for i, c in enumerate(LEVELS):
        s.add(f'<rect x="{lx + i * 14}" y="{ly - 9}" width="10" height="10" rx="2" fill="{c}"/>')
    s.add(s.text(lx + 5 * 14 + 4, ly, "MORE", "mono", 8.5, DIM))
    return s


def _proj_name(repo):
    for p in P["projects"]:
        if p["repo"] == repo:
            return p["name"]
    return repo.replace("-", " ").replace("_", " ").strip()


def telemetry_tile():
    W, H = TILE_W, 262
    repos = {k: v for k, v in T["repos"].items() if k != LOGIN and not v["fork"]}
    last = max(repos.values(), key=lambda r: r["pushed_at"])["pushed_at"][:10]
    cells = [(T["public_repos"], "PUBLIC REPOS"), (T["stars"], "STARS EARNED"), (T["followers"], "FOLLOWERS"),
             (T["contributions_last_year"], "CONTRIB · 12MO"), (len(T["languages"]), "LANGUAGES"),
             (dt.date.fromisoformat(last).strftime("%b %d").upper(), "LAST PUSH")]
    s = Svg(W, H, "Telemetry: " + ", ".join(f"{l.lower()} {v}" for v, l in cells) + f" (synced {T['synced_at']}).")
    panel(s, W, H, CYAN, "TELEMETRY // PUBLIC PROFILE", "LIVE")
    cw = (W - 40) / 3
    for i, (v, lab) in enumerate(cells):
        cx, cy = 20 + (i % 3) * cw, 56 + (i // 3) * 82
        s.add(f'<rect x="{cx + 3:.0f}" y="{cy}" width="{cw - 6:.0f}" height="70" rx="8" fill="{PANEL2}" stroke="{LINE}"/>',
              f'<line x1="{cx + 14:.0f}" y1="{cy}" x2="{cx + 40:.0f}" y2="{cy}" stroke="{CYAN}" stroke-width="2"/>',
              s.text(cx + cw / 2, cy + 38, str(v), "display", 23 if len(str(v)) < 5 else 17, CYAN, "middle"),
              s.text(cx + cw / 2, cy + 58, lab, "mono", 8.5, MUTED, "middle", ls=.8))
    s.add(s.text(20, H - 18, f"SOURCE: GITHUB API + PUBLIC CONTRIBUTION CALENDAR · {T['synced_at']}", "mono", 8, DIM, ls=.5))
    return s


def streak_tile():
    W, H = TILE_W, 262
    cur, lng, act = T["current_streak"], T["longest_streak"], T["active_days"]
    best = T["best_day"]
    s = Svg(W, H, f"Streak reactor: current streak {cur} days, longest streak {lng} days, {act} active days in the last year, peak day {best['count']} contributions on {best['date']}.")
    panel(s, W, H, GOLD, "STREAK REACTOR", "CADENCE")
    cx, cy, r = 100, 150, 66
    C = 2 * math.pi * r
    ratio = 0 if lng == 0 else min(cur / lng, 1)
    tgt = C * (1 - ratio)
    s.add(f'<g transform="translate({cx} {cy})"><g>{spin(40)}' +
          "".join(f'<line x1="0" y1="-84" x2="0" y2="{-79 if i % 4 else -75}" stroke="{GOLD}" opacity=".5" transform="rotate({i * 7.5})"/>' for i in range(48)) +
          f'</g><circle r="{r}" fill="none" stroke="{LINE}" stroke-width="9"/>'
          f'<circle r="{r}" fill="none" stroke="{GOLD}" stroke-width="9" stroke-linecap="round" stroke-dasharray="{C:.1f}" stroke-dashoffset="{tgt:.1f}" transform="rotate(-90)"/>'
          f'<circle r="46" fill="{GOLD}" fill-opacity=".06" class="pulse"/></g>',
          s.text(cx, cy + 8, str(cur), "display", 34, TEXT, "middle"),
          s.text(cx, cy + 28, "DAY STREAK", "mono", 8.5, GOLD, "middle", ls=1.2))
    rows = [(f"{lng} days", "LONGEST STREAK"), (f"{act} / 365", "ACTIVE DAYS"),
            (f"{best['count']} commits", "PEAK · " + dt.date.fromisoformat(best["date"]).strftime("%b %d, %Y").upper())]
    for i, (v, lab) in enumerate(rows):
        y = 92 + i * 52
        s.add(s.text(206, y, lab, "mono", 8.5, MUTED, ls=1),
              s.text(206, y + 22, v, "display", 16, GOLD if i == 0 else TEXT))
    return s


LANG_COLOR = {"Python": "#5A9BD5", "TypeScript": "#4A90E2", "JavaScript": "#F1E05A", "HTML": "#F06A40", "CSS": "#A070E0",
              "Dockerfile": "#7FA7B8", "PLpgSQL": "#6F98C8", "Batchfile": "#C1F12E", "Mako": "#9AA3AD"}


def language_tile():
    W, H = TILE_W, 262
    langs = T["languages"]
    tot = sum(langs.values()) or 1
    top = list(langs.items())[:6]
    s = Svg(W, H, "Language spectrum by code volume: " + ", ".join(f"{k} {v / tot * 100:.1f}%" for k, v in top))
    panel(s, W, H, CYAN, "LANGUAGE SPECTRUM", "BY CODE VOLUME")
    bclip = s.uid("bc")
    s.defs.append(f'<clipPath id="{bclip}"><rect x="20" y="54" width="{W - 40}" height="8" rx="4"/></clipPath>')
    bars = [f'<g clip-path="url(#{bclip})">']
    x = 20
    for k, v in langs.items():
        w = (W - 40) * v / tot
        if w >= .5:
            bars.append(f'<rect x="{x:.1f}" y="54" width="{w + .4:.1f}" height="8" fill="{LANG_COLOR.get(k, MUTED)}"/>')
        x += w
    bars.append(sweep(s, 20, 54, W - 40, 8, 5.5, .35, 50) + "</g>")
    s.add("".join(bars))
    for i, (k, v) in enumerate(top):
        y = 92 + i * 26
        pct = v / tot * 100
        bw = max(154 * pct / (top[0][1] / tot * 100), 4)
        c = LANG_COLOR.get(k, MUTED)
        s.add(f'<circle cx="25" cy="{y - 4}" r="4" fill="{c}"/>', s.text(36, y, k, "body", 14.5, TEXT),
              f'<rect x="148" y="{y - 8}" width="154" height="6" rx="3" fill="{LINE}"/>',
              f'<rect x="148" y="{y - 8}" width="{bw:.1f}" height="6" rx="3" fill="{c}"/>',
              s.text(W - 20, y, f"{pct:.1f}%", "mono", 10.5, MUTED, "end"))
    s.add(s.text(20, H - 18, "AGGREGATED ACROSS PUBLIC PROJECT REPOS (EXCL. THIS PROFILE REPO)", "mono", 8, DIM, ls=.4))
    return s


def activity_tile():
    W, H = TILE_W, 262
    repos = [(k, v) for k, v in T["repos"].items() if k != LOGIN and not v["fork"] and v["language"]]
    repos.sort(key=lambda kv: kv[1]["pushed_at"], reverse=True)
    repos = repos[:5]
    s = Svg(W, H, "Mission log, most recent pushes: " + "; ".join(f"{_proj_name(k)} {v['pushed_at'][:10]}" for k, v in repos))
    panel(s, W, H, GOLD, "MISSION LOG // RECENT PUSHES", "AUTO")
    s.add(f'<line x1="104" y1="56" x2="104" y2="{56 + 40 * (len(repos) - 1)}" stroke="{LINE}" stroke-width="2"/>')
    for i, (k, v) in enumerate(repos):
        y = 60 + i * 40
        d = dt.date.fromisoformat(v["pushed_at"][:10])
        s.add(s.text(20, y + 4, d.strftime("%Y·%m·%d"), "mono", 10, GOLD if i == 0 else MUTED),
              f'<circle cx="104" cy="{y}" r="5" fill="{VOID}" stroke="{GOLD if i == 0 else CYAN}" stroke-width="2"/>',
              (f'<circle cx="104" cy="{y}" r="9" fill="none" stroke="{GOLD}" class="pulse"/>' if i == 0 else ""),
              s.text(122, y + 5, _proj_name(k), "bold", 15, TEXT))
        lang = v["language"].upper()
        lw = measure(lang, "mono", 8.5, .4) + 14
        chip(s, W - 20 - lw, y - 9, lang, CYAN, 8.5, 7, 18)
    return s


# ───────────────────────────── MODULE 05 · ARCHIVE ─────────────────────────────
def achievements(mobile=False):
    items = []
    for a in P["achievements"]:
        d = a["detail"].replace("LIVE:public_repos", str(T["public_repos"]))
        items.append((a["icon"], a["title"], d))
    W = MOBILE_W if mobile else FULL_W
    cols = 2 if mobile else len(items)
    rows = math.ceil(len(items) / cols)
    rh = 170
    H = 56 + rows * rh + 6
    s = Svg(W, H, "Mission archive: " + "; ".join(f"{t} — {d}" for _, t, d in items))
    panel(s, W, H, GOLD, "MISSION ARCHIVE // VERIFIED RECORDS", f"{len(items)} ENTRIES")
    cw = (W - 40) / cols
    hg = s.uid("hg")
    s.defs.append(f'<linearGradient id="{hg}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE29A"/>'
                  f'<stop offset=".5" stop-color="{GOLD}"/><stop offset="1" stop-color="{AMBER}"/></linearGradient>')
    for i, (ic, title, det) in enumerate(items):
        r_, c_ = divmod(i, cols)
        if mobile and r_ == rows - 1 and len(items) % cols:
            cx = W / 2
        else:
            cx = 20 + c_ * cw + cw / 2
        cy = 56 + r_ * rh + 48
        hexp = " ".join(f"{cx + 34 * math.cos(math.radians(a)):.1f},{cy + 34 * math.sin(math.radians(a)):.1f}" for a in range(-90, 270, 60))
        hexi = " ".join(f"{cx + 27 * math.cos(math.radians(a)):.1f},{cy + 27 * math.sin(math.radians(a)):.1f}" for a in range(-90, 270, 60))
        s.add(f'<circle cx="{cx:.1f}" cy="{cy}" r="44" fill="{GOLD}" opacity="0"><animate attributeName="opacity" values="0;.18;0" dur="5s" begin="{i * 1:.1f}s" repeatCount="indefinite"/></circle>',
              f'<polygon points="{hexp}" fill="#120E05" stroke="url(#{hg})" stroke-width="2.5"/>',
              f'<polygon points="{hexi}" fill="none" stroke="{GOLD}" stroke-opacity=".35"/>',
              f'<path transform="translate({cx - 14:.1f} {cy - 14}) scale(1.1667)" d="{GLYPHS[ic]}" fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
        s.add(s.text(cx, cy + 62, title, "bold", 15, TEXT, "middle"))
        for j, line in enumerate(wrap(det, "body", 12.5, cw - 14)[:2]):
            s.add(s.text(cx, cy + 80 + j * 15, line, "body", 12.5, MUTED, "middle"))
    return s


# ───────────────────────────── MODULE 06 · UPLINK + FINALE ─────────────────────────────
def social_pill(soc):
    W, H = 270, 52
    s = Svg(W, H, f"{soc['label']}: {soc['handle']}")
    col = BRAND[soc["key"]][1]
    s.add(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="10" fill="{PANEL}" stroke="#1E3A5F" stroke-width="1.5"/>',
          f'<rect x=".75" y=".75" width="4" height="{H - 1.5}" rx="2" fill="{col}"/>',
          f'<rect x="14" y="10" width="32" height="32" rx="8" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".5"/>',
          icon(soc["key"], 21, 17, 18, col),
          s.text(58, 24, soc["label"].upper(), "display", 11, TEXT, ls=1.5))
    hs = 10
    while measure(soc["handle"], "mono", hs) > W - 90 and hs > 7.5:
        hs -= .5
    s.add(s.text(58, 40, soc["handle"], "mono", hs, MUTED),
          s.text(W - 14, 24, "↗", "body", 15, col, "end"))
    return s


def finale(mobile=False):
    W, H = (MOBILE_W, 380) if mobile else (FULL_W, 320)
    words = [w.upper() for w in P["identity"]["philosophy"]]
    s = Svg(W, H, f"{' · '.join(words)} — {P['identity']['name']}. Independent fan-inspired design; not affiliated with Marvel.")
    clip, ov = s.uid("fc"), s.uid("fo")
    s.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
    s.defs.append(f'<linearGradient id="{ov}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VOID}" stop-opacity=".55"/>'
                  f'<stop offset=".45" stop-color="{VOID}" stop-opacity=".1"/><stop offset=".72" stop-color="{VOID}" stop-opacity=".78"/>'
                  f'<stop offset="1" stop-color="{VOID}" stop-opacity=".97"/></linearGradient>')
    cy = 140 if not mobile else 130
    s.add(f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{VOID}"/>'
          f'<image href="{img_uri("finale.webp", W, H, focus=(.5, .5 if not mobile else .45), q=62)}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
          f'<rect width="{W}" height="{H}" fill="url(#{ov})"/>',
          f'<g transform="translate({W / 2} {cy})"><g>{spin(60)}<circle r="{118 if not mobile else 100}" fill="none" stroke="{GOLD}" stroke-width="1.2" stroke-dasharray="1 9" opacity=".8"/></g>'
          f'<g>{spin(24, True)}<circle r="{96 if not mobile else 82}" fill="none" stroke="{AMBER}" stroke-width="1.5" stroke-dasharray="30 12 4 12" opacity=".7"/></g></g>',
          particles(s, 0, 60, W, H - 60, 22 if not mobile else 14, seed=11), "</g>")
    s.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="#1E3A5F" stroke-width="1.5"/>', brackets(10, 10, W - 20, H - 20, GOLD, 18, 2))
    s.add(s.text(W / 2, 34, "END OF TRANSMISSION", "mono", 10, GOLD, "middle", ls=3))
    lines = [words] if not mobile else [words[:3], words[3:]]
    fs = 20 if not mobile else 17
    dot_gap = 28 if not mobile else 22
    n = len(words)
    k = 0
    base_y = H - 92 if not mobile else H - 126
    for li, ln in enumerate(lines):
        wws = [measure(wd, "display", fs, 2) for wd in ln]
        tw = sum(wws) + dot_gap * max(len(ln) - 1, 0)
        x = W / 2 - tw / 2
        y = base_y + li * 32
        for j, (wd, ww) in enumerate(zip(ln, wws)):
            s.add(s.text(x, y, wd, "display", fs, "#7A93B8", ls=2))
            kt = f"0;{k / n * .8:.3f};{k / n * .8 + .08:.3f};{k / n * .8 + .32:.3f};1"
            s.add(s.text(x, y, wd, "display", fs, GOLD, ls=2, extra='opacity="0"').replace(
                "</text>", f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt}" dur="7s" repeatCount="indefinite"/></text>'))
            x += ww
            if j < len(ln) - 1:
                s.add(s.text(x + dot_gap / 2, y, "·", "display", fs, GOLD, "middle"))
                x += dot_gap
            k += 1
    s.add(s.text(W / 2, H - 50, f"— {P['identity']['name'].upper()}", "mono", 11, TEXT, "middle", ls=2.5))
    s.add(s.text(W / 2, H - 24, "Original fan-inspired artwork & code · not affiliated with or endorsed by Marvel or Disney",
                 "body", 11 if not mobile else 9.5, DIM, "middle"))
    return s


def top_pill():
    label = f"▲ RETURN TO COMMAND DECK  ·  TELEMETRY SYNC {T['synced_at']}"
    w = int(measure(label, "mono", 9.5, 1.1) + 36)
    s = Svg(w, 30, "Return to top of profile")
    s.add(f'<rect x=".75" y=".75" width="{w - 1.5}" height="28.5" rx="6" fill="{PANEL}" stroke="#1E3A5F" stroke-width="1.5"/>',
          s.text(w / 2, 18.5, label, "mono", 9.5, CYAN, "middle", ls=1.1))
    return s


# ───────────────────────────── README ─────────────────────────────
def picture(desktop, mobile, alt, width="100%"):
    return (f'<picture>\n  <source media="(max-width: 600px)" srcset="{mobile}">\n'
            f'  <img src="{desktop}" width="{width}" alt="{esc(alt)}">\n</picture>')


def build():
    out = {}
    out["hero"] = write("assets/hero/hero.svg", hero())
    out["hero_m"] = write("assets/hero/hero-mobile.svg", hero(True))
    for key, num, title, sub in MODULES:
        out[f"nav_{key}"] = write(f"assets/nav/{key}.svg", nav_pill(num, NAV_LABELS[key]))
        out[f"hdr_{key}"] = write(f"assets/headers/{key}.svg", section_header(num, title, sub, FULL_W))
        out[f"hdr_{key}_m"] = write(f"assets/headers/{key}-mobile.svg", section_header(num, title, sub, MOBILE_W))
    out["d1"] = write("assets/dossier/personnel.svg", dossier_personnel())
    out["d2"] = write("assets/dossier/mission.svg", dossier_mission())
    ars = P["arsenal"]
    out["a1"] = write("assets/arsenal/core.svg", arsenal_tile(ars[:4], "ARSENAL // CORE SYSTEMS", "TIER 1"))
    out["a2"] = write("assets/arsenal/support.svg", arsenal_tile(ars[4:], "ARSENAL // SUPPORT SYSTEMS", "TIER 2"))
    for p in P["projects"]:
        out[f"p_{p['id']}"] = write(f"assets/projects/{p['id']}.svg", project_card(p))
    out["heat"] = write("assets/command/radar.svg", heatmap())
    out["heat_m"] = write("assets/command/radar-mobile.svg", heatmap(True))
    out["tele"] = write("assets/command/telemetry.svg", telemetry_tile())
    out["streak"] = write("assets/command/streak.svg", streak_tile())
    out["lang"] = write("assets/command/languages.svg", language_tile())
    out["log"] = write("assets/command/activity.svg", activity_tile())
    out["ach"] = write("assets/archive/records.svg", achievements())
    out["ach_m"] = write("assets/archive/records-mobile.svg", achievements(True))
    for soc in P["socials"]:
        out[f"s_{soc['key']}"] = write(f"assets/uplink/{soc['key']}.svg", social_pill(soc))
    out["fin"] = write("assets/finale/finale.svg", finale())
    out["fin_m"] = write("assets/finale/finale-mobile.svg", finale(True))
    out["top"] = write("assets/finale/top.svg", top_pill())
    readme(out)


def header_block(key, num, title, sub, out):
    return (f'<a id="{key}"></a>\n<p align="center">\n'
            + picture(out[f"hdr_{key}"], out[f"hdr_{key}_m"], f"{num} · {title}") + "\n</p>\n")


def readme(o):
    idn = P["identity"]
    L = []
    A = L.append
    A("<!--  Generated by scripts/build_profile.py from data/profile.json + data/telemetry.json.\n"
      "      Edit the data files (not this file) and run:  python scripts/build_profile.py  -->")
    A('<a id="top"></a>\n<div align="center">\n')
    A(picture(o["hero"], o["hero_m"], f"{idn['name']} — {idn['title']} · {' · '.join(idn['roles'][1:])}. “{idn['tagline']}”"))
    A("\n<br><br>\n")
    A("&nbsp;\n".join(f'<a href="#{k}"><img src="{o["nav_" + k]}" height="32" alt="{n} {t.title()}"></a>' for k, n, t, _ in MODULES))
    A("\n</div>\n\n<br>\n")
    mods = {m[0]: m for m in MODULES}

    def _tile_tag(src, alt, h):
        img = f'<img src="{src}" width="{TILE_W}" alt="{esc(alt)}">'
        return f'<a href="{h}">{img}</a>' if h else img

    def tiles(*pairs):
        rows = []
        for i in range(0, len(pairs), 2):
            chunk = [_tile_tag(*it) for it in pairs[i:i + 2]]
            rows.append('<p align="center">\n' + "&nbsp;\n".join(chunk) + "\n</p>")
        return "\n".join(rows) + "\n"

    def alt_of(rel):
        txt = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        return re.search(r"<title[^>]*>(.*?)</title>", txt, re.S).group(1).replace("&amp;", "&").replace("&quot;", '"')

    # 01 dossier
    A(header_block(*mods["dossier"], o))
    A(tiles((o["d1"], alt_of(o["d1"]), None), (o["d2"], alt_of(o["d2"]), None)))
    A("<br>\n")
    # 02 arsenal
    A(header_block(*mods["arsenal"], o))
    A(tiles((o["a1"], alt_of(o["a1"]), None), (o["a2"], alt_of(o["a2"]), None)))
    A("<br>\n")
    # 03 multiverse
    A(header_block(*mods["multiverse"], o))
    cards = []
    for p in P["projects"]:
        href = f"https://github.com/{LOGIN}/{p['repo']}" if p["repo"] else None
        cards.append((o[f"p_{p['id']}"], alt_of(o[f"p_{p['id']}"]), href))
    A(tiles(*cards))
    links = " &nbsp;·&nbsp; ".join(
        (f'<a href="https://github.com/{LOGIN}/{p["repo"]}"><b>{p["name"]}</b></a>' if p["repo"] else f'<b>{p["name"]}</b> <sub>(private · in development)</sub>')
        for p in P["projects"])
    more = " &nbsp;·&nbsp; ".join(f'<a href="https://github.com/{LOGIN}/{m["repo"]}">{esc(m["label"].split(" — ")[0])}</a>' for m in P["archive_more"])
    A(f'<p align="center"><sub>OPEN A PORTAL &nbsp;▸&nbsp;</sub> {links}<br>\n'
      f'<sub>MORE IN THE ARCHIVE &nbsp;▸&nbsp; {more} &nbsp;·&nbsp; <a href="https://github.com/{LOGIN}?tab=repositories">all repositories</a></sub></p>\n')
    A("<br>\n")
    # 04 command
    A(header_block(*mods["command"], o))
    A('<p align="center">\n' + picture(o["heat"], o["heat_m"], alt_of(o["heat"])) + "\n</p>\n")
    A(tiles((o["tele"], alt_of(o["tele"]), None), (o["streak"], alt_of(o["streak"]), None),
            (o["lang"], alt_of(o["lang"]), None), (o["log"], alt_of(o["log"]), None)))
    A("<br>\n")
    # 05 archive
    A(header_block(*mods["archive"], o))
    A('<p align="center">\n' + picture(o["ach"], o["ach_m"], alt_of(o["ach"])) + "\n</p>\n")
    A("<br>\n")
    # 06 uplink
    A(header_block(*mods["uplink"], o))
    soc_tags = [
        f'<a href="{s_["url"]}"><img src="{o["s_" + s_["key"]]}" width="270" alt="{esc(s_["label"])}: {esc(s_["handle"])}"></a>'
        for s_ in P["socials"]
    ]
    A('<p align="center">\n' + "&nbsp;\n".join(soc_tags[:3]) + "\n</p>\n"
      '<p align="center">\n' + "&nbsp;\n".join(soc_tags[3:]) + "\n</p>\n")
    A("<br>\n")
    A('<div align="center">\n' + picture(o["fin"], o["fin_m"], alt_of(o["fin"])) + "\n")
    A(f'\n<br><br>\n<a href="#top"><img src="{o["top"]}" height="30" alt="Return to top of profile"></a>\n</div>\n')
    # accessible plain-text version
    A("\n<details>\n<summary><sub>📄 Plain-text dossier (accessible version)</sub></summary>\n")
    A(f"\n**{idn['name']}** — {' · '.join(idn['roles'])}  \n*“{idn['tagline']}”*\n")
    A("\n**Education**\n" + "".join(f"\n- {e['degree']} — {e['school']} ({e['detail']})" for e in P["education"]))
    A(f"\n- Origin: {idn['origin']}\n")
    A(f"\n**Current mission:** {P['mission']['current']}\n")
    A(f"\n**Interests:** {', '.join(P['interests'])}  \n**Learning:** {', '.join(P['learning'])}\n")
    A("\n**Projects**\n" + "".join(
        f"\n- **{p['name']}** — {p['summary']} " + (f"[Repository](https://github.com/{LOGIN}/{p['repo']})" if p["repo"] else "*(private, in development)*")
        for p in P["projects"]))
    A(f"\n\n**GitHub (synced {T['synced_at']}):** {T['public_repos']} public repos · {T['stars']} stars · "
      f"{T['contributions_last_year']} contributions in the last year · longest streak {T['longest_streak']} days\n")
    A("\n**Milestones**\n" + "".join(
        f"\n- {a['title']} — {a['detail'].replace('LIVE:public_repos', str(T['public_repos']))}" for a in P["achievements"]))
    A("\n\n**Contact:** " + " · ".join(f"[{s_['label']}]({s_['url']})" for s_ in P["socials"]))
    A(f"\n\n<sub>{' · '.join(idn['philosophy'])}. Independent fan-inspired design — not affiliated with or endorsed by Marvel or Disney.</sub>\n</details>\n")
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))


if __name__ == "__main__":
    build()
    tot = 0
    for rel, n in BUILT:
        tot += n
        print(f"{n / 1024:8.1f} KB  {rel}")
    print(f"{tot / 1024:8.1f} KB  TOTAL ({len(BUILT)} SVGs)")

