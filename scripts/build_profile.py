"""PROJECT MARVEL — Jet Black × Muted Moss Green × Neon Emerald Green Edition.

Generates every visual asset (self-contained glowing animated SVGs) and README.md from:
    data/profile.json     verified identity / projects / achievements (hand-curated, sourced)
    data/telemetry.json   live GitHub statistics  (scripts/fetch_telemetry.py)
    assets/source/*       original AI-generated artwork + avatar (color-graded to emerald/moss/black)
    scripts/vendor/       OFL fonts + CC0 Simple Icons

Why self-contained SVG?  GitHub proxies README images through camo and renders SVG
inside <img>, which forbids scripts and external fetches but *does* run CSS @keyframes,
SMIL animations, and SVG <filter> optical Gaussian bloom. Fonts are embedded as per-file
subsetted WOFF2 and artwork as emerald-graded WebP data-URIs.

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
import sys
from collections import defaultdict
from xml.sax.saxutils import escape as _esc

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import miss_minutes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8"))
T = json.load(open(os.path.join(ROOT, "data", "telemetry.json"), encoding="utf-8"))
LOGIN = P["identity"]["login"]
VENDOR = os.path.join(ROOT, "scripts", "vendor")
SRC = os.path.join(ROOT, "assets", "source")

# ─────────────── DESIGN TOKENS: JET BLACK × MUTED MOSS × NEON EMERALD ───────────────
VOID = "#020403"          # Pure Jet Black abyss
PANEL = "#050907"         # Jet Black HUD surface
PANEL_TOP = "#08100B"     # Upper carbon-moss glass gradient stop
PANEL_BOT = "#020403"     # Lower jet-black obsidian stop
PANEL2 = "#09120C"        # Recessed jet-moss sub-tile
LINE = "#162A1E"          # Recessed muted moss divider / track
BEZEL = "#254531"         # Crisp outer muted-moss architectural bezel (Dark & Light safe)

EMERALD = "#00FF88"       # Primary Electric Neon Emerald Green
EMERALD2 = "#00C466"      # Deep rich emerald plasma
MINT = "#88FFC8"          # Hyper-luminous mint-emerald core highlight
MOSS = "#588C69"          # Tactical Muted Moss Green
MOSS_BRIGHT = "#7AB38B"   # Luminous Sage-Moss secondary accent

TEXT = "#ECFFF4"          # Crisp emerald-ice white primary text
BODY_TEXT = "#C4E6D1"     # Pale emerald-mist body copy
MUTED = "#7FA88C"         # Muted moss-sage secondary labels
DIM = "#4A6E56"           # Subtle moss metadata & coordinates

FULL_W, MOBILE_W, TILE_W = 840, 420, 415

FONT_SPECS = {
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


# ─────────────── VFX EMERALD COLOR-GRADING + OPTICAL BLOOM ───────────────
_IMG_CACHE: dict = {}


def _emerald_grade(im: Image.Image) -> Image.Image:
    """Remap RGB sci-fi artwork into Jet Black + Muted Moss Green + Neon Emerald Green with bloom."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    out = Image.new("RGB", (w, h))
    opx = out.load()
    glow_layer = Image.new("RGB", (w, h), (0, 0, 0))
    gpx = glow_layer.load()

    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            lum = 0.23 * rf + 0.52 * gf + 0.25 * bf
            mx = max(rf, gf, bf)
            mn = min(rf, gf, bf)
            sat = (mx - mn) / (mx + 1e-6)
            warm = max(0.0, rf - bf)
            lc = lum ** 1.22

            if lc < 0.22:
                t = lc / 0.22
                nr = 0.008 + t * 0.050
                ng = 0.012 + t * 0.125
                nb = 0.009 + t * 0.075
            elif lc < 0.58:
                t = (lc - 0.22) / 0.36
                moss_mix = 1.0 - 0.45 * sat * (1.0 - warm)
                nr = (0.058 + t * 0.185) * moss_mix + (0.015 + t * 0.060) * (1.0 - moss_mix)
                ng = (0.137 + t * 0.350) * moss_mix + (0.160 + t * 0.560) * (1.0 - moss_mix)
                nb = (0.084 + t * 0.225) * moss_mix + (0.095 + t * 0.320) * (1.0 - moss_mix)
            else:
                t = (lc - 0.58) / 0.42
                core = t ** 1.7
                if warm > 0.18:
                    nr = 0.14 + 0.68 * core
                    ng = 0.72 + 0.28 * t
                    nb = 0.36 + 0.50 * core
                else:
                    nr = 0.02 + 0.86 * core
                    ng = 0.82 + 0.18 * t
                    nb = 0.44 + 0.48 * core
                bs = min(1.0, t * (0.65 + 0.55 * sat))
                gpx[x, y] = (int(18 * bs), int(255 * bs), int(136 * bs))

            opx[x, y] = (
                max(0, min(255, int(nr * 255))),
                max(0, min(255, int(ng * 255))),
                max(0, min(255, int(nb * 255))),
            )

    bloom_wide = glow_layer.filter(ImageFilter.GaussianBlur(radius=11))
    bloom_tight = glow_layer.filter(ImageFilter.GaussianBlur(radius=3.5))
    bloom = ImageChops.add(bloom_wide, bloom_tight, scale=1.35)
    return ImageChops.screen(out, bloom)


def _portrait_grade(im: Image.Image) -> Image.Image:
    """Subtle emerald-room studio shadow grade for human portrait while keeping natural skin."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 85:
                px[x, y] = (int(r * 0.52), min(255, int(g * 0.86 + 14)), int(b * 0.64 + 8))
            else:
                px[x, y] = (int(r * 0.86 + 6), min(255, int(g * 0.96 + 10)), int(b * 0.86 + 8))
    return rgb


def img_uri(name, w, h, crop=None, focus=(0.5, 0.5), scale=2, q=70, circle=False):
    key = (name, w, h, crop, focus, scale, q, circle)
    if key in _IMG_CACHE:
        return _IMG_CACHE[key]
    path = os.path.join(SRC, name)
    im = Image.open(path).convert("RGB")
    if name == "avatar.png" and crop is None:
        # Trim 4.5% outer border to remove baked-in warm ring from source avatar
        iw, ih = im.size
        pad = int(min(iw, ih) * 0.045)
        im = im.crop((pad, pad, iw - pad, ih - pad))
    if crop:
        im = im.crop(crop)
    else:
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
    im = _portrait_grade(im) if name == "avatar.png" else _emerald_grade(im)
    if circle:
        im = im.convert("RGBA")
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, im.size[0] - 1, im.size[1] - 1), fill=255)
        im.putalpha(mask)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=q, method=6)
    uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    _IMG_CACHE[key] = uri
    return uri


# ─────────────── UNIFIED EMERALD-TO-MOSS ICON SYSTEM ───────────────
# Every technology & uplink icon uses a calibrated 5-tier Neon Emerald -> Muted Moss ramp
BRAND = {
    # Languages (Electric Neon Emerald & Hyper-Mint)
    "python": ("Python", EMERALD), "typescript": ("TypeScript", MINT),
    "javascript": ("JavaScript", "#38F29B"), "cplusplus": ("C++", MOSS_BRIGHT),
    # AI / Agentic / GenAI (Neon Emerald core)
    "langchain": ("LangChain", EMERALD), "openai": ("OpenAI API", "#B8FFE0"),
    "ollama": ("Ollama", MINT), "huggingface": ("Hugging Face", "#45F5A1"),
    "groq": ("Groq LPU", EMERALD), "pgvector": ("pgvector", MINT),
    # ML / Deep Learning
    "pytorch": ("PyTorch", EMERALD), "tensorflow": ("TensorFlow", "#38F29B"),
    "scikitlearn": ("scikit-learn", MOSS_BRIGHT), "numpy": ("NumPy", MINT),
    "pandas": ("pandas", "#66CC8A"),
    # Computer Vision / 3D
    "opencv": ("OpenCV", EMERALD), "mediapipe": ("MediaPipe", MINT),
    "threedotjs": ("Three.js", "#B8FFE0"),
    # Frameworks
    "fastapi": ("FastAPI", EMERALD), "react": ("React", MINT),
    "nextdotjs": ("Next.js", "#C8FFE6"), "nodedotjs": ("Node.js", "#38F29B"),
    "vite": ("Vite", "#66D992"), "tailwindcss": ("Tailwind", MINT),
    # Data
    "postgresql": ("PostgreSQL", "#55D98B"), "supabase": ("Supabase", EMERALD),
    "mongodb": ("MongoDB", "#38F29B"), "redis": ("Redis", MOSS_BRIGHT),
    "sqlite": ("SQLite", "#68B884"),
    # Cloud / DevOps
    "docker": ("Docker", "#4CE896"), "githubactions": ("Actions", EMERALD),
    "googlecloud": ("Google Cloud", MINT), "vercel": ("Vercel", "#C8FFE6"),
    "render": ("Render", MOSS_BRIGHT),
    # Tools
    "git": ("Git", "#45F5A1"), "github": ("GitHub", "#5EFFB2"),
    "linux": ("Linux", MOSS_BRIGHT), "postman": ("Postman", "#55D98B"),
    "figma": ("Figma", MINT),
    # Social Uplinks
    "linkedin": ("LinkedIn", EMERALD), "gmail": ("Email", MINT),
    "instagram": ("Instagram", "#45F5A1"), "facebook": ("Facebook", MOSS_BRIGHT),
}
_ICON: dict[str, str] = {}
CUSTOM_ICONS = {
    "groq": (
        '<g fill="none" stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="5.5" y="5.5" width="13" height="13" rx="2.5"/>'
        '<path d="M9 2.5v3M15 2.5v3M9 18.5v3M15 18.5v3M2.5 9h3M2.5 15h3M18.5 9h3M18.5 15h3"/>'
        '<path d="M13 8.2L9.8 12.4h2.5L11 15.8l3.4-4.3h-2.5z" fill="{c}" stroke="none"/></g>'
    ),
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


def icon(slug, x, y, size, color=None, filt=""):
    col = color or BRAND[slug][1]
    s = size / 24
    fa = f' filter="url(#{filt})"' if filt else ""
    if slug in CUSTOM_ICONS:
        inner = CUSTOM_ICONS[slug].format(c=col)
        return f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.4f})"{fa}>{inner}</g>'
    return f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" d="{icon_path(slug)}" fill="{col}"{fa}/>'


GLYPHS = {
    "trophy": "M7 4h10v3a5 5 0 0 1-10 0z M7 5H4v1.5A3 3 0 0 0 7 9.5 M17 5h3v1.5a3 3 0 0 1-3 3 M10.5 12.5h3v3.5h-3z M8 19h8",
    "star": "M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z",
    "rocket": "M12 2.5c3 2.2 4.6 5.8 4.6 9.6l-1.8 3.9H9.2l-1.8-3.9c0-3.8 1.6-7.4 4.6-9.6z M9.3 16l-2.8 3.2 M14.7 16l2.8 3.2 M12 18v3.5 M12 8.2a1.7 1.7 0 1 0 0.01 0",
    "shield": "M12 2.5l7.5 2.8v6c0 4.6-3.2 8.4-7.5 10.2C7.7 19.7 4.5 15.9 4.5 11.3v-6z M8.6 12l2.4 2.4 4.5-4.8",
    "code": "M8 7l-5 5 5 5 M16 7l5 5-5 5 M13.8 4.5l-3.6 15",
}

# ─────────────── SVG DOCUMENT + OPTICAL GLOW FILTER ENGINE ───────────────
BASE_CSS = """
.pulse{animation:pulse 3s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.42}50%{opacity:1}}
.blink{animation:blink 1.4s steps(1) infinite}
@keyframes blink{50%{opacity:.18}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.css = [], [], []
        self.chars = defaultdict(set)
        self._ids = itertools.count()
        self._gsm = None
        self._glg = None
        self._grid = None

    def uid(self, p="i"):
        return f"{p}{next(self._ids)}"

    def glow_sm(self) -> str:
        """Crisp userSpaceOnUse optical neon bloom (works on straight <line>s too)."""
        if not self._gsm:
            fid = self.uid("gs")
            self.defs.append(
                f'<filter id="{fid}" filterUnits="userSpaceOnUse" x="-40" y="-40" width="{self.w + 80}" height="{self.h + 80}">'
                f'<feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="b"/>'
                f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            )
            self._gsm = fid
        return self._gsm

    def glow_lg(self) -> str:
        """Dual-kernel intense neon-emerald optical bloom (tight plasma core + wide emerald corona)."""
        if not self._glg:
            fid = self.uid("gl")
            self.defs.append(
                f'<filter id="{fid}" filterUnits="userSpaceOnUse" x="-60" y="-60" width="{self.w + 120}" height="{self.h + 120}">'
                f'<feGaussianBlur in="SourceGraphic" stdDeviation="6.2" result="b1"/>'
                f'<feGaussianBlur in="SourceGraphic" stdDeviation="2.0" result="b2"/>'
                f'<feMerge><feMergeNode in="b1"/><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            )
            self._glg = fid
        return self._glg

    def grid_pat(self) -> str:
        """Subtle 24x24 muted-moss holographic micro-grid texture for jet-black surfaces."""
        if not self._grid:
            pid = self.uid("gp")
            self.defs.append(
                f'<pattern id="{pid}" width="24" height="24" patternUnits="userSpaceOnUse">'
                f'<path d="M24 0H0v24" fill="none" stroke="#122419" stroke-width=".7" stroke-opacity=".55"/>'
                f'<circle cx="24" cy="24" r=".9" fill="{MOSS}" fill-opacity=".28"/></pattern>'
            )
            self._grid = pid
        return self._grid

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


BUILT: list = []


def write(rel, svg: Svg):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = svg.render()
    open(path, "w", encoding="utf-8").write(data)
    BUILT.append((rel, len(data.encode())))
    return rel


# ─────────────── SHARED GLOWING HUD COMPONENTS ───────────────
def brackets(x, y, w, h, color, L=14, sw=2, op=1, filt=""):
    p = (f"M{x},{y + L}V{y}H{x + L} M{x + w - L},{y}H{x + w}V{y + L} "
         f"M{x + w},{y + h - L}V{y + h}H{x + w - L} M{x + L},{y + h}H{x}V{y + h - L}")
    fa = f' filter="url(#{filt})"' if filt else ""
    return f'<path d="{p}" fill="none" stroke="{color}" stroke-width="{sw}" opacity="{op}"{fa}/>'


def laser_border(s: Svg, x, y, w, h, r, color=EMERALD, dur=9.0, beam=120, sw=1.6, begin=0.0):
    """Animated glowing neon-emerald photon pulse orbiting a rounded-rect bezel."""
    perim = 2 * (w + h) - 8 * r + 2 * math.pi * r
    gsm = s.glow_sm()
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" '
        f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
        f'stroke-dasharray="{beam} {perim:.1f}" opacity=".88" filter="url(#{gsm})">'
        f'<animate attributeName="stroke-dashoffset" from="{perim + beam:.1f}" to="{beam:.1f}" '
        f'dur="{dur}s" begin="{begin:.1f}s" repeatCount="indefinite"/></rect>'
    )


def panel(s: Svg, w, h, accent=EMERALD, label=None, code=None, r=12, dur=10.0):
    g, amb1, amb2, clip = s.uid("pg"), s.uid("a1"), s.uid("a2"), s.uid("pc")
    gsm = s.glow_sm()
    pat = s.grid_pat()
    s.defs.append(
        f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{PANEL_TOP}"/><stop offset="1" stop-color="{PANEL_BOT}"/></linearGradient>'
        f'<radialGradient id="{amb1}" cx="15%" cy="8%" r="65%">'
        f'<stop offset="0" stop-color="{accent}" stop-opacity=".13"/>'
        f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="{amb2}" cx="88%" cy="94%" r="55%">'
        f'<stop offset="0" stop-color="{MOSS}" stop-opacity=".12"/>'
        f'<stop offset="1" stop-color="{MOSS}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="{clip}"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}"/></clipPath>'
    )
    s.add(
        f'<g clip-path="url(#{clip})">'
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="url(#{g})"/>'
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="url(#{pat})"/>'
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="url(#{amb1})"/>'
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="url(#{amb2})"/>'
        f'</g>',
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" fill="none" stroke="{BEZEL}" stroke-width="1.5"/>',
        laser_border(s, 1, 1, w - 2, h - 2, r, accent, dur=dur, beam=105),
        brackets(6, 6, w - 12, h - 12, accent, 12, 1.7, .92, filt=gsm),
    )
    if label:
        s.add(
            f'<rect x="18" y="20" width="6" height="6" fill="{accent}" transform="rotate(45 21 23)" filter="url(#{gsm})"/>',
            s.text(32, 27, label, "mono", 10.5, accent, ls=1.2),
        )
        if code:
            s.add(s.text(w - 20, 27, code, "mono", 9.5, MOSS_BRIGHT, "end", ls=1))
        s.add(
            f'<line x1="18" y1="38" x2="{w - 18}" y2="38" stroke="{LINE}" stroke-width="1.2"/>',
            f'<line x1="18" y1="38" x2="106" y2="38" stroke="{accent}" stroke-width="1.6" filter="url(#{gsm})"/>',
        )
        for i in range(5):
            s.add(f'<line x1="{w - 18 - i * 6}" y1="34" x2="{w - 18 - i * 6}" y2="38" stroke="{accent}" opacity=".75"/>')


def chip(s: Svg, x, y, label, color=EMERALD, size=10, pad=7, h=20, glow=False):
    w = measure(label, "mono", size, .4) + pad * 2
    fa = f' filter="url(#{s.glow_sm()})"' if glow else ""
    s.add(
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="4" fill="{color}" fill-opacity=".10" '
        f'stroke="{color}" stroke-opacity=".55"{fa}/>',
        s.text(x + pad, y + h / 2 + size * .36, label, "mono", size, color, ls=.4),
    )
    return w


def spin(dur, reverse=False):
    a, b = ("360", "0") if reverse else ("0", "360")
    return f'<animateTransform attributeName="transform" type="rotate" from="{a}" to="{b}" dur="{dur}s" repeatCount="indefinite"/>'


def reactor(s: Svg, cx, cy, k=1.0, glow=True):
    """Glowing Neon-Emerald Reactor core with counter-rotating Muted-Moss sacred rune geometry."""
    rg = s.uid("rg")
    glg = s.glow_lg()
    gsm = s.glow_sm()
    s.defs.append(
        f'<radialGradient id="{rg}">'
        f'<stop offset="0" stop-color="{MINT}" stop-opacity=".65"/>'
        f'<stop offset=".35" stop-color="{EMERALD}" stop-opacity=".28"/>'
        f'<stop offset=".7" stop-color="{MOSS}" stop-opacity=".10"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></radialGradient>'
    )
    out = [f'<g transform="translate({cx} {cy}) scale({k})">']
    if glow:
        out.append(f'<circle r="165" fill="url(#{rg})" class="pulse"/>')
    ticks = "".join(
        f'<line x1="0" y1="-132" x2="0" y2="{-125 if i % 3 else -118}" '
        f'stroke="{EMERALD if i % 3 == 0 else MOSS}" transform="rotate({i * 5})"/>'
        for i in range(72)
    )
    out.append(f'<g stroke-width="1.3" opacity=".65">{ticks}</g>')
    # Sacred 8-node moss-emerald rune ring
    poly1 = " ".join(f"{110 * math.cos(math.radians(a)):.1f},{110 * math.sin(math.radians(a)):.1f}" for a in range(0, 360, 45))
    out.append(
        f'<g>{spin(44, True)}'
        f'<circle r="114" fill="none" stroke="{MOSS_BRIGHT}" stroke-width="1.6" stroke-dasharray="18 7 3 7" opacity=".9"/>'
        f'<polygon points="{poly1}" fill="none" stroke="{MOSS}" stroke-width="1.1" opacity=".65"/>'
        + "".join(f'<rect x="-3" y="-118" width="6" height="8" rx="1" fill="{EMERALD}" filter="url(#{gsm})" transform="rotate({i * 45})"/>' for i in range(8))
        + "</g>"
    )
    # High-intensity glowing Neon-Emerald plasma arcs
    out.append(
        f'<g filter="url(#{glg})">{spin(18)}'
        f'<circle r="96" fill="none" stroke="{EMERALD}" stroke-width="1.8" stroke-dasharray="3 7"/>'
        f'<path d="M0,-86 A86,86 0 0 1 74.5,-43" fill="none" stroke="{EMERALD}" stroke-width="4.2" stroke-linecap="round"/>'
        f'<path d="M0,86 A86,86 0 0 1 -74.5,43" fill="none" stroke="{EMERALD}" stroke-width="4.2" stroke-linecap="round"/></g>'
    )
    out.append(
        f'<g filter="url(#{gsm})">{spin(9, True)}'
        f'<path d="M-60,-30 A67,67 0 0 1 -30,-60" fill="none" stroke="{MINT}" stroke-width="2.8" stroke-linecap="round"/>'
        f'<path d="M60,30 A67,67 0 0 1 30,60" fill="none" stroke="{MINT}" stroke-width="2.8" stroke-linecap="round"/>'
        f'<circle r="44" fill="none" stroke="{EMERALD}" stroke-width="1.2" stroke-dasharray="8 5" opacity=".8"/></g>'
    )
    out.append("</g>")
    return "".join(out)


def particles(s: Svg, x0, y0, x1, y1, n, seed=7, colors=(EMERALD, MINT, MOSS_BRIGHT)):
    rnd = random.Random(seed)
    gsm = s.glow_sm()
    out = [f'<g filter="url(#{gsm})">']
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        d, r, c = rnd.uniform(5, 11), rnd.uniform(.9, 2.3), rnd.choice(colors)
        b = -rnd.uniform(0, d)
        rise = rnd.uniform(32, 84)
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{c}" opacity="0">'
            f'<animate attributeName="cy" values="{y:.0f};{y - rise:.0f}" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;.95;0" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>'
        )
    out.append("</g>")
    return "".join(out)


def scanline(s: Svg, x, y, w, h, dur=7, color=EMERALD, op=.13, band=74):
    g = s.uid("sl")
    s.defs.append(
        f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{color}" stop-opacity="{op}"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
    )
    return (
        f'<rect x="{x}" y="{y - band}" width="{w}" height="{band}" fill="url(#{g})">'
        f'<animate attributeName="y" values="{y - band};{y + h}" dur="{dur}s" repeatCount="indefinite"/></rect>'
    )


def sweep(s: Svg, x, y, w, h, dur=6, op=.20, band=96):
    g = s.uid("sw")
    s.defs.append(
        f'<linearGradient id="{g}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{EMERALD}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{EMERALD}" stop-opacity="{op}"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></linearGradient>'
    )
    return (
        f'<rect x="{x - band}" y="{y}" width="{band}" height="{h}" fill="url(#{g})">'
        f'<animate attributeName="x" values="{x - band};{x + w};{x + w}" keyTimes="0;.55;1" dur="{dur}s" repeatCount="indefinite"/></rect>'
    )


def svg_miss_minutes(s: Svg, cx: float, cy: float, scale: float = 1.0, wave_left: bool = False) -> str:
    """SMIL-animated holographic Miss Minutes vector cameo (hovering, clock hands ticking, waving & blinking)."""
    gsm = s.glow_sm()
    fg, ag = s.uid("mf"), s.uid("ma")
    s.defs.append(
        f'<radialGradient id="{fg}" cx="38%" cy="32%" r="68%">'
        f'<stop offset="0" stop-color="#40FA9C"/><stop offset=".6" stop-color="#1CE882"/>'
        f'<stop offset="1" stop-color="#0C9E56"/></radialGradient>'
        f'<radialGradient id="{ag}"><stop offset="0" stop-color="{EMERALD}" stop-opacity=".42"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></radialGradient>'
    )
    ticks = "".join(
        f'<line x1="0" y1="{-15.2 if i % 3 == 0 else -16.0}" x2="0" y2="-18.2" '
        f'stroke="#020B06" stroke-width="{1.6 if i % 3 == 0 else 1.0}" transform="rotate({i * 30})"/>'
        for i in range(12)
    )
    ws = -1 if wave_left else 1
    rs = -ws
    wave_arm = (
        f'<g><animateTransform attributeName="transform" type="rotate" '
        f'values="{-14 * ws} {18 * ws} 2;{18 * ws} {18 * ws} 2;{-14 * ws} {18 * ws} 2" dur="1.35s" repeatCount="indefinite"/>'
        f'<path d="M{18 * ws},2 Q{26 * ws},{-4} {28 * ws},{-14}" fill="none" stroke="{EMERALD}" stroke-width="3.6" stroke-linecap="round"/>'
        f'<path d="M{18 * ws},2 Q{26 * ws},{-4} {28 * ws},{-14}" fill="none" stroke="#020B06" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="{28.5 * ws}" cy="-15.5" r="4.2" fill="#E8FFF4" stroke="#020B06" stroke-width="1.1"/>'
        f'<circle cx="{26.0 * ws}" cy="-19.0" r="1.6" fill="#E8FFF4" stroke="#020B06" stroke-width=".8"/>'
        f'<circle cx="{28.8 * ws}" cy="-19.8" r="1.6" fill="#E8FFF4" stroke="#020B06" stroke-width=".8"/>'
        f'<circle cx="{31.4 * ws}" cy="-18.6" r="1.5" fill="#E8FFF4" stroke="#020B06" stroke-width=".8"/></g>'
    )
    rest_arm = (
        f'<path d="M{18 * rs},3 Q{25 * rs},9 {23 * rs},16" fill="none" stroke="{EMERALD}" stroke-width="3.4" stroke-linecap="round"/>'
        f'<path d="M{18 * rs},3 Q{25 * rs},9 {23 * rs},16" fill="none" stroke="#020B06" stroke-width="1.7" stroke-linecap="round"/>'
        f'<circle cx="{22.8 * rs}" cy="17.2" r="3.6" fill="#E8FFF4" stroke="#020B06" stroke-width="1.0"/>'
    )
    legs = (
        f'<path d="M-7,18 Q-10,25 -8,31 M7,18 Q10,25 8,31" fill="none" stroke="{EMERALD}" stroke-width="3.4" stroke-linecap="round"/>'
        f'<path d="M-7,18 Q-10,25 -8,31 M7,18 Q10,25 8,31" fill="none" stroke="#020B06" stroke-width="1.7" stroke-linecap="round"/>'
        f'<ellipse cx="-9.5" cy="32.5" rx="5.2" ry="2.6" fill="#0B3820" stroke="{EMERALD}" stroke-width="1.1"/>'
        f'<ellipse cx="9.5" cy="32.5" rx="5.2" ry="2.6" fill="#0B3820" stroke="{EMERALD}" stroke-width="1.1"/>'
    )
    eyes = ""
    for ex in (-4.8, 4.8):
        eyes += (
            f'<ellipse cx="{ex}" cy="-3.6" rx="3.5" ry="5.5" fill="#E8FFF4" stroke="#020B06" stroke-width="1.1"/>'
            f'<ellipse cx="{ex + 0.5 * ws}" cy="-3.3" rx="2.1" ry="3.5" fill="#020B06"/>'
            f'<polygon points="{ex + 0.5 * ws},-3.4 {ex + 2.8},-5.6 {ex + 2.8},-3.1" fill="#E8FFF4"/>'
            f'<path d="M{ex - 3.0},-10.4 Q{ex},-12.5 {ex + 3.0},-10.2" fill="none" stroke="#020B06" stroke-width="1.3" stroke-linecap="round"/>'
            f'<ellipse cx="{ex}" cy="-3.6" rx="3.6" ry="5.6" fill="#1CE882" stroke="#020B06" stroke-width="1.0" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;.88;.91;.95;1" dur="3.8s" repeatCount="indefinite"/></ellipse>'
        )
    return (
        f'<g transform="translate({cx:.1f} {cy:.1f}) scale({scale:.3f})">'
        f'<g><animateTransform attributeName="transform" type="translate" values="0,0;0,-5;0,0" dur="2.6s" repeatCount="indefinite"/>'
        f'<circle r="33" fill="url(#{ag})"/>'
        f'{legs}{rest_arm}'
        f'<circle r="21" fill="#020B06" stroke="{EMERALD}" stroke-width="1.8" filter="url(#{gsm})"/>'
        f'<circle r="19.2" fill="url(#{fg})" stroke="{MINT}" stroke-width=".9"/>'
        f'{ticks}'
        f'<g opacity=".55"><g>{spin(18)}<line x1="0" y1="0" x2="0" y2="-9.5" stroke="#05381E" stroke-width="1.6" stroke-linecap="round"/></g>'
        f'<g>{spin(4.5)}<line x1="0" y1="0" x2="0" y2="-13.8" stroke="#05381E" stroke-width="1.2" stroke-linecap="round"/></g></g>'
        f'{eyes}'
        f'<circle cx="0" cy="1.2" r="1.6" fill="#020B06"/>'
        f'<path d="M-7.8,5.6 C-4.0,11.8 4.0,11.8 7.8,5.6" fill="none" stroke="#020B06" stroke-width="1.8" stroke-linecap="round"/>'
        f'<path d="M-9.2,4.6 A2,2 0 0 0 -8.2,7.2 M9.2,4.6 A2,2 0 0 1 8.2,7.2" fill="none" stroke="#020B06" stroke-width="1.1"/>'
        f'{wave_arm}</g></g>'
    )


# ───────────────────────────── MODULE 01 · HERO ─────────────────────────────
HERO_SRC = (1376, 768)
REACTOR_SRC = (905, 365)


def hero(mobile=False):
    idn = P["identity"]
    if not mobile:
        W, H = FULL_W, 368
        crop = (0, 84, 1376, 674)
        k = W / 1376
        rx, ry = (REACTOR_SRC[0] - crop[0]) * k, (REACTOR_SRC[1] - crop[1]) * k
        img_w, img_h = W, H
    else:
        W, H = MOBILE_W, 568
        crop = (136, 0, 1376, 768)
        img_w, img_h = W, 264
        k = img_w / (crop[2] - crop[0])
        rx, ry = (REACTOR_SRC[0] - crop[0]) * k, (REACTOR_SRC[1] - crop[1]) * k
    s = Svg(W, H, f"{idn['name']} — {idn['title']}. {idn['tagline']}")
    gsm, glg = s.glow_sm(), s.glow_lg()
    pat = s.grid_pat()
    clip, ov, fade, top_v = s.uid("c"), s.uid("ov"), s.uid("fd"), s.uid("tv")
    s.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
    s.defs.append(
        f'<linearGradient id="{ov}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{VOID}" stop-opacity=".97"/>'
        f'<stop offset=".44" stop-color="{VOID}" stop-opacity=".76"/>'
        f'<stop offset=".76" stop-color="{VOID}" stop-opacity=".10"/>'
        f'<stop offset="1" stop-color="{VOID}" stop-opacity=".38"/></linearGradient>'
    )
    s.defs.append(
        f'<linearGradient id="{fade}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{VOID}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{VOID}" stop-opacity="1"/></linearGradient>'
        f'<linearGradient id="{top_v}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{VOID}" stop-opacity=".86"/>'
        f'<stop offset="1" stop-color="{VOID}" stop-opacity="0"/></linearGradient>'
    )
    uri = img_uri("hero.webp", img_w, img_h, crop=crop, q=70)
    s.add(
        f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{VOID}"/>'
        f'<image href="{uri}" width="{img_w}" height="{img_h}" preserveAspectRatio="xMidYMid slice"/>'
        f'<rect width="{W}" height="52" fill="url(#{top_v})"/>'
    )
    if not mobile:
        s.add(f'<rect width="{W}" height="{H}" fill="url(#{ov})"/>')
    else:
        s.add(f'<rect y="{img_h - 110}" width="{W}" height="112" fill="url(#{fade})"/>',
              f'<rect y="{img_h}" width="{W}" height="{H - img_h}" fill="url(#{pat})"/>')
    s.add(reactor(s, round(rx), round(ry), k=(.62 if not mobile else .34)))
    s.add(particles(s, W * .32 if not mobile else 0, 40, W, H - 20, 30 if not mobile else 18))
    s.add(scanline(s, 0, 0, W, H, 7.2, EMERALD, .13))
    s.add("</g>")

    # Glowing perimeter bezel + HUD targeting brackets
    s.add(
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="{BEZEL}" stroke-width="1.5"/>',
        laser_border(s, 1, 1, W - 2, H - 2, 16, EMERALD, dur=11.0, beam=160, sw=1.8),
        brackets(10, 10, W - 20, H - 20, EMERALD, 20, 2.1, filt=gsm),
    )

    # Top telemetry bar with live emerald waveform pulse
    s.add(
        f'<rect x="26" y="25" width="7" height="7" fill="{EMERALD}" transform="rotate(45 29.5 28.5)" filter="url(#{gsm})"/>',
        s.text(40, 33, "SYS://PROFILE.CORE // EMERALD.OS" if not mobile else "SYS://EMERALD.OS", "mono", 10, EMERALD, ls=1.5),
        f'<circle cx="{W - 86}" cy="29.5" r="3.8" fill="{EMERALD}" class="blink" filter="url(#{gsm})"/>',
        s.text(W - 26, 33, "ONLINE", "mono", 10, EMERALD, "end", ls=1.5),
    )
    if not mobile:
        # Subtle glowing ECG/telemetry pulse trace in top bar
        ecg = "M305,29 h38 l5,-7 l7,14 l6,-11 l4,4 h54"
        s.add(
            f'<path d="{ecg}" fill="none" stroke="{MOSS}" stroke-width="1.1" opacity=".55"/>',
            f'<path d="{ecg}" fill="none" stroke="{EMERALD}" stroke-width="1.5" filter="url(#{gsm})" '
            f'stroke-dasharray="28 130"><animate attributeName="stroke-dashoffset" from="158" to="0" dur="3.2s" repeatCount="indefinite"/></path>',
        )

    # Glowing display typography — immediate high contrast + dual neon-emerald bloom + specular sweep
    fs = 48 if not mobile else 40
    tx, y1, y2 = (36, 140, 195) if not mobile else (22, 318, 365)
    sh, tf1, tf2 = s.uid("sh"), s.uid("tf1"), s.uid("tf2")
    s.defs.append(
        f'<linearGradient id="{tf1}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#C8FFE4"/></linearGradient>'
        f'<linearGradient id="{tf2}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#96FFD0"/><stop offset="1" stop-color="{EMERALD}"/></linearGradient>'
        f'<linearGradient id="{sh}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="150" y2="0" gradientTransform="translate(-260 0)">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="-260 0;{W} 0;{W} 0" keyTimes="0;.48;1" dur="6.2s" repeatCount="indefinite"/></linearGradient>'
    )
    first, last = idn["name"].upper().split(" ", 1)
    for word, y, grad in ((first, y1, tf1), (last, y2, tf2)):
        # Underlying optical emerald bloom halo + crisp metallic foreground + moving specular highlight
        s.add(
            s.text(tx, y, word, "display", fs, EMERALD, ls=2.5, extra=f'opacity=".36" filter="url(#{glg})"'),
            s.text(tx, y, word, "display", fs, f"url(#{grad})", ls=2.5,
                   extra=f'stroke="{EMERALD}" stroke-opacity=".45" stroke-width="1"'),
            s.text(tx, y, word, "display", fs, f"url(#{sh})", ls=2.5),
        )

    # Role HUD chevron + secondary moss-glass capsule + tagline
    ry0 = y2 + 20 if not mobile else y2 + 18
    rw = measure(idn["title"].upper(), "display", 13.5, 2.8) + 32
    s.add(
        f'<path d="M{tx},{ry0} h{rw:.1f} l8,14 l-8,14 h-{rw:.1f} z" fill="{EMERALD}" fill-opacity=".14" '
        f'stroke="{EMERALD}" stroke-opacity=".85" filter="url(#{gsm})"/>',
        s.text(tx + 14, ry0 + 19, idn["title"].upper(), "display", 13.5, MINT, ls=2.8),
    )
    if not mobile:
        sub_short = "CS STUDENT · OPEN SOURCE"
        sw2 = measure(sub_short, "mono", 9.5, .9) + 20
        sx2 = tx + rw + 14
        s.add(
            f'<rect x="{sx2:.1f}" y="{ry0 + 2}" width="{sw2:.1f}" height="24" rx="4" fill="{VOID}" fill-opacity=".82" stroke="{MOSS}" stroke-opacity=".75"/>',
            s.text(sx2 + 10, ry0 + 18, sub_short, "mono", 9.5, MOSS_BRIGHT, ls=.9),
        )
    else:
        sub = "  ·  ".join(r.upper() for r in idn["roles"][1:])
        s.add(s.text(tx, ry0 + 48, sub, "mono", 9.5, MOSS_BRIGHT, ls=.6))

    ty = ry0 + 58 if not mobile else ry0 + 78
    maxw = 450 if not mobile else W - 44
    for i, line in enumerate(wrap(f"“{idn['tagline']}”", "body", 18.5 if not mobile else 17, maxw)):
        s.add(s.text(tx, ty + i * 23, line, "body", 18.5 if not mobile else 17, TEXT))

    by = H - 24
    s.add(
        f'<line x1="{tx}" y1="{by - 18}" x2="{W - 26}" y2="{by - 18}" stroke="{LINE}"/>',
        f'<line x1="{tx}" y1="{by - 18}" x2="{tx + 150}" y2="{by - 18}" stroke="{EMERALD}" stroke-width="1.6" filter="url(#{gsm})"/>',
        s.text(tx, by, "AGENTS · RAG · VOICE AI · COMPUTER VISION" if not mobile else "AGENTS · RAG · VOICE AI · CV",
               "mono", 10, EMERALD, ls=1.2),
    )
    if not mobile:
        s.add(
            svg_miss_minutes(s, W - 56, by - 58, scale=0.76, wave_left=True),
            f'<circle cx="{W - 224}" cy="{by - 3.5}" r="3.5" fill="{MINT}" class="blink" filter="url(#{gsm})"/>',
            s.text(W - 26, by, "CURRENT MISSION ▸ SYLVIE", "mono", 10, MINT, "end", ls=1.2),
        )
    else:
        s.add(svg_miss_minutes(s, W - 46, by - 52, scale=0.66, wave_left=True))
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
    w = int(measure(f"{num} {label}", "mono", 10.5, 1.2) + 42)
    s = Svg(w, 34, f"{label.title()} section")
    gsm = s.glow_sm()
    s.add(
        f'<rect x="1" y="1" width="{w - 2}" height="32" rx="7" fill="{PANEL}" stroke="{BEZEL}" stroke-width="1.4"/>',
        f'<line x1="14" y1="32" x2="{w - 14}" y2="32" stroke="{EMERALD}" stroke-width="1.5" stroke-opacity=".65" filter="url(#{gsm})"/>',
        f'<rect x="12" y="14" width="6" height="6" fill="{EMERALD}" transform="rotate(45 15 17)" filter="url(#{gsm})"/>',
        s.text(26, 21, num, "mono", 10.5, EMERALD, ls=1.2),
        s.text(26 + measure(num + " ", "mono", 10.5, 1.2), 21, label, "mono", 10.5, TEXT, ls=1.2),
    )
    return s


def section_header(num, title, subtitle, w):
    mobile = w < 600
    s = Svg(w, 76, f"{num} · {title}")
    gsm, glg = s.glow_sm(), s.glow_lg()
    pat = s.grid_pat()
    clip, amb = s.uid("hc"), s.uid("ha")
    s.defs.append(
        f'<clipPath id="{clip}"><rect x="1" y="1" width="{w - 2}" height="74" rx="10"/></clipPath>'
        f'<radialGradient id="{amb}" cx="8%" cy="50%" r="55%">'
        f'<stop offset="0" stop-color="{EMERALD}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></radialGradient>'
    )
    s.add(
        f'<g clip-path="url(#{clip})"><rect x="1" y="1" width="{w - 2}" height="74" fill="{PANEL}"/>'
        f'<rect x="1" y="1" width="{w - 2}" height="74" fill="url(#{pat})"/>'
        f'<rect x="1" y="1" width="{w - 2}" height="74" fill="url(#{amb})"/></g>',
        f'<rect x="1" y="1" width="{w - 2}" height="74" rx="10" fill="none" stroke="{BEZEL}" stroke-width="1.5"/>',
        laser_border(s, 1, 1, w - 2, 74, 10, EMERALD, dur=9.5, beam=90, sw=1.4),
    )
    hx, hy = 39, 38
    hexp = " ".join(f"{hx + 20 * math.cos(math.radians(a)):.1f},{hy + 20 * math.sin(math.radians(a)):.1f}" for a in range(30, 390, 60))
    s.add(
        f'<g transform="translate({hx} {hy})"><g>{spin(14)}<circle r="27" fill="none" stroke="{MOSS_BRIGHT}" stroke-width="1.3" stroke-dasharray="4 5" opacity=".85"/></g></g>',
        f'<polygon points="{hexp}" fill="{EMERALD}" fill-opacity=".12" stroke="{EMERALD}" stroke-width="1.5" filter="url(#{gsm})"/>',
        s.text(hx, hy + 5.5, num, "display", 15, MINT, "middle", extra=f'filter="url(#{gsm})"'),
    )
    ts = 20 if not mobile else 17
    s.add(
        s.text(80, 35, title, "display", ts, EMERALD, ls=2.5, extra=f'opacity=".30" filter="url(#{glg})"'),
        s.text(80, 35, title, "display", ts, TEXT, ls=2.5),
        s.text(80, 57, subtitle, "mono", 10 if not mobile else 9, MUTED, ls=.8),
    )
    tw = measure(title, "display", ts, 2.5)
    x1, x2, ly = 80 + tw + 18, w - 44, 29
    if x2 - x1 < 60:
        x1, ly = 80, 67
    L = x2 - x1
    s.add(
        f'<line x1="{x1:.0f}" y1="{ly}" x2="{x2}" y2="{ly}" stroke="{LINE}" stroke-width="2"/>',
        f'<line x1="{x1:.0f}" y1="{ly}" x2="{x2}" y2="{ly}" stroke="{EMERALD}" stroke-width="2.4" stroke-linecap="round" '
        f'filter="url(#{glg})" stroke-dasharray="84 {L + 84:.0f}">'
        f'<animate attributeName="stroke-dashoffset" values="84;{-L:.0f}" dur="3.2s" repeatCount="indefinite"/></line>',
        f'<g transform="translate({w - 24} {ly})" filter="url(#{gsm})"><g>{spin(8, True)}<rect x="-6" y="-6" width="12" height="12" fill="none" stroke="{EMERALD}" transform="rotate(45)"/></g>'
        f'<circle r="2.8" fill="{MINT}" class="pulse"/></g>',
    )
    return s


# ───────────────────────────── MODULE 02 · DOSSIER ─────────────────────────────
def dossier_personnel():
    idn, edu = P["identity"], P["education"]
    W, H = TILE_W, 444
    s = Svg(W, H, f"Personnel file: {idn['name']}, {idn['title']}. " + "; ".join(f"{e['degree']}, {e['school']} ({e['detail']})" for e in edu) + f". Origin: {idn['origin']}.")
    gsm, glg = s.glow_sm(), s.glow_lg()
    panel(s, W, H, EMERALD, "PERSONNEL FILE", "FILE 001", dur=11.5)
    cx, cy = 84, 114
    rg = s.uid("ar")
    s.defs.append(
        f'<radialGradient id="{rg}"><stop offset="0" stop-color="{EMERALD}" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></radialGradient>'
    )
    s.add(
        f'<circle cx="{cx}" cy="{cy}" r="70" fill="url(#{rg})" class="pulse"/>',
        f'<image href="{img_uri("avatar.png", 92, 92, circle=True, q=82)}" x="{cx - 46}" y="{cy - 46}" width="92" height="92"/>',
        f'<g transform="translate({cx} {cy})">'
        f'<circle r="47" fill="none" stroke="{EMERALD}" stroke-width="1.8" filter="url(#{gsm})"/>'
        f'<g filter="url(#{gsm})">{spin(15)}<circle r="56" fill="none" stroke="{EMERALD}" stroke-width="1.2" stroke-dasharray="4 6" opacity=".85"/>'
        f'<path d="M0,-56 A56,56 0 0 1 48.5,-28" fill="none" stroke="{MINT}" stroke-width="3.2" stroke-linecap="round"/></g>'
        f'<g>{spin(28, True)}<circle r="64" fill="none" stroke="{MOSS_BRIGHT}" stroke-width="1.2" stroke-dasharray="14 6 2 6" opacity=".8"/></g></g>',
    )
    first, last = idn["name"].upper().split(" ", 1)
    s.add(
        s.text(162, 92, first, "display", 17, TEXT, ls=1.5),
        s.text(162, 115, last, "display", 17, MINT, ls=1.5, extra=f'filter="url(#{gsm})"'),
        s.text(162, 139, idn["title"].upper(), "mono", 11, EMERALD, ls=1.5),
        f'<circle cx="166" cy="155" r="3.2" fill="{EMERALD}" class="blink" filter="url(#{gsm})"/>',
        s.text(176, 159, "ACTIVE · OPEN SOURCE", "mono", 9.5, MOSS_BRIGHT, ls=1),
    )
    fields = [
        ("CURRENT TRAINING", edu[0]["degree"], f"{edu[0]['school']} · {edu[0]['detail']}"),
        ("PRIOR TRAINING", edu[1]["degree"], f"{edu[1]['school']} · {edu[1]['detail']}"),
        ("ORIGIN", idn["origin"], "India"),
        ("DESIGNATION", " · ".join(idn["roles"][1:]), "Builds autonomous, human-like AI systems"),
    ]
    y = 206
    for i, (lab, val, det) in enumerate(fields):
        acc = EMERALD if i < 2 else MOSS_BRIGHT
        s.add(
            f'<rect x="20" y="{y - 13}" width="3" height="44" rx="1.5" fill="{acc}" filter="url(#{gsm})"/>',
            s.text(34, y, lab, "mono", 9.5, MUTED, ls=1.4),
            s.text(34, y + 19, val, "bold", 16.5, TEXT),
            s.text(34, y + 36, det, "body", 13.5, BODY_TEXT),
        )
        y += 58
    s.add(scanline(s, 8, 44, W - 16, H - 52, 8.5, EMERALD, .08, 60))
    return s


def dossier_mission():
    W, H = TILE_W, 444
    m = P["mission"]["current"]
    s = Svg(W, H, f"Mission brief. Current mission: {m}. Research interests: {', '.join(P['interests'])}. "
                  f"Learning: {', '.join(P['learning'])}. Philosophy: {'. '.join(P['identity']['philosophy'])}.")
    gsm, glg = s.glow_sm(), s.glow_lg()
    panel(s, W, H, MOSS_BRIGHT, "MISSION BRIEF", "STATUS: LIVE", dur=12.5)
    ip_x = W - 20 - measure("IN PROGRESS", "mono", 9, 1) - 10
    s.add(
        s.text(20, 64, "CURRENT MISSION", "mono", 9.5, EMERALD, ls=1.4),
        f'<circle cx="{ip_x:.1f}" cy="60.5" r="3.6" fill="{EMERALD}" class="blink" filter="url(#{gsm})"/>',
        s.text(W - 20, 64, "IN PROGRESS", "mono", 9, MINT, "end", ls=1),
    )
    y = 86
    for line in wrap(m, "body", 15.5, W - 40):
        s.add(s.text(20, y, line, "body", 15.5, TEXT))
        y += 20
    y += 14
    s.add(s.text(20, y, "RESEARCH VECTORS", "mono", 9.5, MOSS_BRIGHT, ls=1.4))
    x, y = 20, y + 10
    for idx, it in enumerate(P["interests"]):
        w = measure(it.upper(), "mono", 9.5, .4) + 14
        if x + w > W - 20:
            x, y = 20, y + 26
        chip(s, x, y, it.upper(), EMERALD if idx < 4 else MOSS_BRIGHT, 9.5)
        x += w + 6
    y += 48
    s.add(s.text(20, y, "IN TRAINING", "mono", 9.5, EMERALD, ls=1.4))
    y += 8
    s.css.append(".ld{animation:ld 2.6s ease-in-out infinite}@keyframes ld{0%{transform:translateX(-50px)}100%{transform:translateX(120px)}}")
    for i, it in enumerate(P["learning"]):
        yy = y + 14 + i * 22
        s.add(s.text(20, yy + 4, "▸", "mono", 11, EMERALD), s.text(36, yy + 4, it, "body", 14.5, TEXT))
        bx = W - 120
        clip = s.uid("lc")
        s.defs.append(f'<clipPath id="{clip}"><rect x="{bx}" y="{yy - 2}" width="100" height="5" rx="2.5"/></clipPath>')
        s.add(
            f'<rect x="{bx}" y="{yy - 2}" width="100" height="5" rx="2.5" fill="{LINE}"/>',
            f'<g clip-path="url(#{clip})"><rect x="{bx}" y="{yy - 2}" width="44" height="5" rx="2.5" fill="{EMERALD}" '
            f'filter="url(#{gsm})" class="ld" style="animation-delay:{i * .35:.2f}s"/></g>',
        )
    y += 22 * len(P["learning"]) + 30
    s.add(s.text(20, y, "DOCTRINE", "mono", 9.5, MOSS_BRIGHT, ls=1.4))
    words = [w.upper() for w in P["identity"]["philosophy"]]
    x, y = 20, y + 26
    n = len(words)
    word_ws = [measure(t, "display", 11.8, 1.2) for t in words]
    gap = (W - 40 - sum(word_ws)) / max(n - 1, 1)
    for i, (t, ww) in enumerate(zip(words, word_ws)):
        s.add(s.text(x, y, t, "display", 11.8, MOSS, ls=1.2))
        kt = f"0;{i / n:.3f};{(i + .9) / n:.3f};1"
        s.add(
            s.text(x, y, t, "display", 11.8, MINT, ls=1.2, extra=f'opacity="0" filter="url(#{glg})"').replace(
                "</text>", f'<animate attributeName="opacity" values="0;0;1;0" keyTimes="{kt}" dur="6s" repeatCount="indefinite"/></text>'
            )
        )
        x += ww
        if i < n - 1:
            s.add(s.text(x + gap / 2, y, "·", "display", 12, EMERALD, "middle"))
            x += gap
    return s


# ───────────────────────────── MODULE 03 · ARSENAL ─────────────────────────────
def arsenal_tile(cats, label, code):
    W = TILE_W
    H = 48 + len(cats) * 104
    names = [BRAND[i][0] for c in cats for i in c["items"]] + [e for c in cats for e in c.get("extra", [])]
    s = Svg(W, H, f"{label}: " + ", ".join(names))
    gsm = s.glow_sm()
    panel(s, W, H, EMERALD, label, code, dur=13.0)
    sock_g = s.uid("sg")
    s.defs.append(
        f'<radialGradient id="{sock_g}" cx="50%" cy="50%" r="60%">'
        f'<stop offset="0" stop-color="{EMERALD}" stop-opacity=".14"/>'
        f'<stop offset="1" stop-color="{PANEL2}" stop-opacity="1"/></radialGradient>'
    )
    y = 66
    k = 0
    total = sum(len(c["items"]) + len(c.get("extra", [])) for c in cats)
    for c in cats:
        s.add(s.text(20, y, c["cat"], "mono", 9.5, MOSS_BRIGHT, ls=1.4))
        lw = measure(c["cat"], "mono", 9.5, 1.4)
        s.add(f'<line x1="{26 + lw:.0f}" y1="{y - 3}" x2="{W - 20}" y2="{y - 3}" stroke="{LINE}" stroke-dasharray="2 3"/>')
        x = 20
        entries = [("icon", i) for i in c["items"]] + [("text", e) for e in c.get("extra", [])]
        for kind, it in entries:
            cy = y + 10
            s.add(f'<rect x="{x}" y="{cy}" width="52" height="52" rx="10" fill="url(#{sock_g})" stroke="{BEZEL}"/>')
            kt0 = k / total
            s.add(
                f'<rect x="{x}" y="{cy}" width="52" height="52" rx="10" fill="{EMERALD}" fill-opacity=".12" '
                f'stroke="{EMERALD}" stroke-width="1.5" filter="url(#{gsm})" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;0;0" '
                f'keyTimes="0;{kt0 * .8:.3f};{kt0 * .8 + .04:.3f};{kt0 * .8 + .13:.3f};1" dur="8.5s" repeatCount="indefinite"/></rect>'
            )
            if kind == "icon":
                s.add(icon(it, x + 13, cy + 13, 26))
                name = BRAND[it][0]
            else:
                big, name = it.split(" ", 1) if " " in it else (it, "")
                s.add(s.text(x + 26, cy + 31, big.upper(), "display", 10.5, EMERALD, "middle", ls=.5))
                name = name or big
            fs = 11.5
            while measure(name, "body", fs) > 58 and fs > 9:
                fs -= .5
            s.add(s.text(x + 26, cy + 70, name, "body", fs, BODY_TEXT, "middle"))
            x += 59
            k += 1
        y += 104
    return s


# ───────────────────────────── MODULE 04 · PROJECTS ─────────────────────────────
FOCUS = {"friday": (.6, .5), "sylvie": (.62, .45), "sales": (.62, .5), "aeris": (.72, .45), "omniaction": (.6, .5), "queueless": (.62, .55)}


def project_card(p, idx=0):
    W, IH = TILE_W, 196
    H = 450
    alt = f"{p['name']} — {p['summary']} Key facts: {'; '.join(p['facts'])}. Stack: {', '.join(p['stack'])}. Status: {p['status']}."
    s = Svg(W, H, alt)
    gsm, glg = s.glow_sm(), s.glow_lg()
    acc = p["accent"]
    clip, fade = s.uid("pc"), s.uid("pf")
    s.defs.append(f'<clipPath id="{clip}"><rect x="1" y="1" width="{W - 2}" height="{IH}" rx="12"/></clipPath>')
    s.defs.append(
        f'<linearGradient id="{fade}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset=".42" stop-color="{PANEL_TOP}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{PANEL_TOP}"/></linearGradient>'
    )
    panel(s, W, H, acc, dur=10.5 + idx * 0.7)
    s.add(
        f'<g clip-path="url(#{clip})">'
        f'<image href="{img_uri(p["id"] + ".webp", W, IH, focus=FOCUS.get(p["id"], (.5, .5)), q=68)}" '
        f'x="1" y="1" width="{W - 2}" height="{IH}" preserveAspectRatio="xMidYMid slice"/>'
        f'<rect x="1" y="1" width="{W - 2}" height="{IH}" fill="url(#{fade})"/>'
        f'{sweep(s, 1, 1, W, IH, 6.8, .22)}</g>',
        f'<line x1="14" y1="{IH}" x2="{W - 14}" y2="{IH}" stroke="{LINE}"/>',
        f'<line x1="20" y1="{IH}" x2="128" y2="{IH}" stroke="{acc}" stroke-width="1.6" filter="url(#{gsm})"/>',
        brackets(14, 14, W - 28, IH - 26, acc, 12, 1.6, .92, filt=gsm),
    )
    # Codename + glowing status capsule
    cw = measure(p["codename"], "mono", 9, .8) + 16
    s.add(
        f'<rect x="22" y="22" width="{cw:.0f}" height="20" rx="3" fill="{VOID}" fill-opacity=".84" stroke="{MOSS_BRIGHT}" stroke-opacity=".75"/>',
        s.text(30, 35.5, p["codename"], "mono", 9, MINT, ls=.8),
    )
    st = p["status"]
    sw_ = measure(st, "mono", 9, .8) + 28
    s.add(
        f'<rect x="{W - 22 - sw_:.0f}" y="{IH - 34}" width="{sw_:.0f}" height="20" rx="10" fill="{VOID}" fill-opacity=".86" '
        f'stroke="{acc}" stroke-opacity=".85" filter="url(#{gsm})"/>',
        f'<circle cx="{W - 22 - sw_ + 12:.0f}" cy="{IH - 24}" r="3.2" fill="{acc}" class="blink" filter="url(#{gsm})"/>',
        s.text(W - 22 - sw_ + 21, IH - 20.5, st, "mono", 9, acc, ls=.8),
    )
    if p["id"] == "sylvie":
        # TVA Nexus Watch Miss Minutes hologram cameo guarding the Sylvie AI project card
        s.add(svg_miss_minutes(s, 54, IH - 46, scale=0.64, wave_left=False))
    y = IH + 33
    s.add(
        s.text(20, y, p["name"], "display", 20, EMERALD, ls=2, extra=f'opacity=".26" filter="url(#{glg})"'),
        s.text(20, y, p["name"], "display", 20, TEXT, ls=2),
    )
    y += 24
    for line in wrap(p["summary"], "body", 15, W - 40)[:3]:
        s.add(s.text(20, y, line, "body", 15, BODY_TEXT))
        y += 19
    y += 10
    for f in p["facts"]:
        s.add(
            f'<rect x="22" y="{y - 8}" width="6" height="6" fill="{acc}" transform="rotate(45 25 {y - 5})" filter="url(#{gsm})"/>',
            s.text(36, y, f, "body", 14, TEXT),
        )
        y += 21
    x, cy = 20, H - 42
    for t in p["stack"]:
        w = measure(t.upper(), "mono", 9, .4) + 14
        if x + w > W - 20:
            break
        chip(s, x, cy, t.upper(), EMERALD if acc == EMERALD else MOSS_BRIGHT, 9)
        x += w + 6
    return s


def portal_pill(label: str, active: bool = True, sub: bool = False):
    """Self-contained glowing emerald/moss mini-capsule so zero raw blue HTML links appear."""
    fs = 9.0 if sub else 9.5
    text = f"▸ {label} ↗" if active else f"◆ {label} · PRIVATE"
    w = int(measure(text, "mono", fs, .9) + 24)
    h = 26 if sub else 28
    s = Svg(w, h, label)
    gsm = s.glow_sm()
    col = (MOSS_BRIGHT if sub else EMERALD) if active else MOSS
    s.add(
        f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="6" fill="{PANEL}" '
        f'stroke="{col}" stroke-opacity="{.65 if active else .4}" stroke-width="1.2"/>',
        (f'<line x1="10" y1="{h - 1}" x2="{w - 10}" y2="{h - 1}" stroke="{col}" stroke-width="1.3" opacity=".6" filter="url(#{gsm})"/>' if active else ""),
        s.text(w / 2, h / 2 + 3.5, text, "mono", fs, TEXT if (active and not sub) else col, "middle", ls=.9),
    )
    return s


# ───────────────────────────── MODULE 05 · COMMAND CENTER ─────────────────────────────
LEVELS = ["#09130D", "#133621", "#1B6B3D", "#00C466", "#00FF88"]


def heatmap(mobile=False):
    cal = T["calendar"]
    weeks = defaultdict(list)
    first = dt.date.fromisoformat(cal[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    for d in cal:
        dd = dt.date.fromisoformat(d["date"])
        weeks[(dd - start).days // 7].append((dd, d))
    keys = sorted(weeks)
    if mobile:
        keys = keys[-24:]
    W = MOBILE_W if mobile else FULL_W
    cell, gap = (12, 3) if mobile else (11, 3)
    x0, y0 = (40 if mobile else 56), 74
    H = y0 + 7 * (cell + gap) + (86 if mobile else 58)
    total, active = T["contributions_last_year"], T["active_days"]
    span = "24W WINDOW" if mobile else "LAST 12 MONTHS"
    shown = sum(d["count"] for k in keys for _, d in weeks[k])
    s = Svg(W, H, f"Contribution radar: {total} contributions and {active} active days in the last year (synced {T['synced_at']}).")
    gsm, glg = s.glow_sm(), s.glow_lg()
    panel(s, W, H, EMERALD, f"CONTRIBUTION RADAR // {span}", f"SYNC {T['synced_at']}", dur=14.0)
    last_month = None
    glow_cells = []
    for ci, k in enumerate(keys):
        x = x0 + ci * (cell + gap)
        for dd, d in weeks[k]:
            row = (dd.weekday() + 1) % 7
            yy = y0 + row * (cell + gap)
            lvl = d["level"]
            s.add(f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[lvl]}" stroke="#0E1E14" stroke-width=".6"/>')
            if lvl >= 3:
                glow_cells.append(f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[lvl]}"/>')
            if dd.day <= 7 and row == 0 and dd.month != last_month:
                s.add(s.text(x, y0 - 10, dd.strftime("%b").upper(), "mono", 9, MUTED, ls=.5))
                last_month = dd.month
    if glow_cells:
        # Optical neon bloom layer on high-activity contribution cells
        s.add(f'<g filter="url(#{gsm})" opacity=".85">{"".join(glow_cells)}</g>')
    for row, lab in ((1, "MON"), (3, "WED"), (5, "FRI")):
        s.add(s.text(x0 - 8, y0 + row * (cell + gap) + cell - 2, lab, "mono", 8.5, DIM, "end"))
    gw = len(keys) * (cell + gap)
    s.add(sweep(s, x0, y0 - 4, gw, 7 * (cell + gap) + 4, 7.5, .28, 64))
    by = y0 + 7 * (cell + gap) + 31
    best = T["best_day"]
    bd = dt.date.fromisoformat(best["date"]).strftime("%b %d").upper()
    stats = [(f"{total}", "CONTRIBUTIONS / YR"), (f"{active}", "ACTIVE DAYS"), (f"{best['count']}", f"PEAK · {bd}")]
    if mobile:
        stats = [(f"{shown}", "LAST 24 WEEKS"), (f"{total}", f"LAST 12MO · {active}D")]
    sx = x0
    for v, lab in stats:
        s.add(
            s.text(sx, by, v, "display", 16, MINT, extra=f'filter="url(#{gsm})"'),
            s.text(sx + measure(v, "display", 16) + 8, by, lab, "mono", 9, MUTED, ls=1),
        )
        sx += measure(v, "display", 16) + measure(lab, "mono", 9, 1) + 30
    lx = W - 20 - 5 * 14 - 34
    ly = by if not mobile else by + 30
    if mobile:
        lx = x0 + 34
    s.add(s.text(lx - 6, ly, "LESS", "mono", 8.5, DIM, "end"))
    for i, c in enumerate(LEVELS):
        fa = f' filter="url(#{gsm})"' if i == 4 else ""
        s.add(f'<rect x="{lx + i * 14}" y="{ly - 9}" width="10" height="10" rx="2" fill="{c}"{fa}/>')
    s.add(s.text(lx + 5 * 14 + 4, ly, "MORE", "mono", 8.5, DIM))
    return s


def _proj_name(repo):
    for p in P["projects"]:
        if p["repo"] == repo:
            return p["name"]
    return repo.replace("-", " ").replace("_", " ").strip()


def telemetry_tile():
    W, H = TILE_W, 264
    repos = {k: v for k, v in T["repos"].items() if k != LOGIN and not v["fork"]}
    last = max(repos.values(), key=lambda r: r["pushed_at"])["pushed_at"][:10]
    cells = [(T["public_repos"], "PUBLIC REPOS"), (T["stars"], "STARS EARNED"), (T["followers"], "FOLLOWERS"),
             (T["contributions_last_year"], "CONTRIB · 12MO"), (len(T["languages"]), "LANGUAGES"),
             (dt.date.fromisoformat(last).strftime("%b %d").upper(), "LAST PUSH")]
    s = Svg(W, H, "Telemetry: " + ", ".join(f"{l.lower()} {v}" for v, l in cells) + f" (synced {T['synced_at']}).")
    gsm = s.glow_sm()
    panel(s, W, H, EMERALD, "TELEMETRY // PUBLIC PROFILE", "LIVE", dur=10.0)
    cw = (W - 40) / 3
    for i, (v, lab) in enumerate(cells):
        cx, cy = 20 + (i % 3) * cw, 56 + (i // 3) * 82
        acc = EMERALD if i % 2 == 0 else MINT
        s.add(
            f'<rect x="{cx + 3:.0f}" y="{cy}" width="{cw - 6:.0f}" height="70" rx="8" fill="{PANEL2}" stroke="{BEZEL}"/>',
            f'<line x1="{cx + 14:.0f}" y1="{cy}" x2="{cx + 44:.0f}" y2="{cy}" stroke="{acc}" stroke-width="2.2" filter="url(#{gsm})"/>',
            s.text(cx + cw / 2, cy + 38, str(v), "display", 23 if len(str(v)) < 5 else 17, acc, "middle", extra=f'filter="url(#{gsm})"'),
            s.text(cx + cw / 2, cy + 58, lab, "mono", 8.5, MUTED, "middle", ls=.8),
        )
    s.add(s.text(20, H - 18, f"SOURCE: GITHUB API + PUBLIC CONTRIBUTION CALENDAR · {T['synced_at']}", "mono", 8, DIM, ls=.5))
    return s


def streak_tile():
    W, H = TILE_W, 264
    cur, lng, act = T["current_streak"], T["longest_streak"], T["active_days"]
    best = T["best_day"]
    s = Svg(W, H, f"Streak reactor: current streak {cur} days, longest streak {lng} days, {act} active days in the last year, peak day {best['count']} contributions on {best['date']}.")
    gsm, glg = s.glow_sm(), s.glow_lg()
    panel(s, W, H, MOSS_BRIGHT, "STREAK REACTOR", "CADENCE", dur=11.0)
    cx, cy, r = 100, 150, 66
    C = 2 * math.pi * r
    ratio = 0 if lng == 0 else min(cur / lng, 1)
    tgt = C * (1 - ratio)
    rg = s.uid("sr")
    s.defs.append(
        f'<radialGradient id="{rg}"><stop offset="0" stop-color="{EMERALD}" stop-opacity=".26"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></radialGradient>'
    )
    s.add(
        f'<g transform="translate({cx} {cy})">'
        f'<circle r="86" fill="url(#{rg})" class="pulse"/>'
        f'<g>{spin(38)}' +
        "".join(
            f'<line x1="0" y1="-84" x2="0" y2="{-79 if i % 4 else -74}" '
            f'stroke="{EMERALD if i % 4 == 0 else MOSS}" opacity=".7" transform="rotate({i * 7.5})"/>'
            for i in range(48)
        ) +
        f'</g><circle r="{r}" fill="none" stroke="{LINE}" stroke-width="9"/>'
        f'<circle r="{r}" fill="none" stroke="{EMERALD}" stroke-width="9" stroke-linecap="round" '
        f'stroke-dasharray="{C:.1f}" stroke-dashoffset="{tgt:.1f}" transform="rotate(-90)" filter="url(#{glg})"/>'
        f'<circle r="48" fill="none" stroke="{MOSS_BRIGHT}" stroke-width="1" stroke-dasharray="4 4" opacity=".6"/></g>',
        s.text(cx, cy + 9, str(cur), "display", 34, TEXT, "middle", extra=f'filter="url(#{gsm})"'),
        s.text(cx, cy + 28, "DAY STREAK", "mono", 8.5, EMERALD, "middle", ls=1.2),
    )
    rows = [(f"{lng} days", "LONGEST STREAK"), (f"{act} / 365", "ACTIVE DAYS"),
            (f"{best['count']} commits", "PEAK · " + dt.date.fromisoformat(best["date"]).strftime("%b %d, %Y").upper())]
    for i, (v, lab) in enumerate(rows):
        y = 92 + i * 52
        s.add(
            s.text(206, y, lab, "mono", 8.5, MUTED, ls=1),
            s.text(206, y + 22, v, "display", 16, MINT if i == 0 else TEXT, extra=(f'filter="url(#{gsm})"' if i == 0 else "")),
        )
    return s


# 6-tier Neon Emerald -> Mint -> Luminous Moss -> Deep Moss luminance spectrum
LANG_RAMP = [EMERALD, "#36E088", MINT, MOSS_BRIGHT, MOSS, "#375E44", "#284733"]


def language_tile():
    W, H = TILE_W, 264
    langs = T["languages"]
    tot = sum(langs.values()) or 1
    ordered = list(langs.items())
    top = ordered[:6]
    lcol = {k: LANG_RAMP[min(i, len(LANG_RAMP) - 1)] for i, (k, _) in enumerate(ordered)}
    s = Svg(W, H, "Language spectrum by code volume: " + ", ".join(f"{k} {v / tot * 100:.1f}%" for k, v in top))
    gsm = s.glow_sm()
    panel(s, W, H, EMERALD, "LANGUAGE SPECTRUM", "BY CODE VOLUME", dur=11.8)
    bclip = s.uid("bc")
    s.defs.append(f'<clipPath id="{bclip}"><rect x="20" y="54" width="{W - 40}" height="8" rx="4"/></clipPath>')
    bars = [f'<g clip-path="url(#{bclip})">']
    x = 20
    for k, v in ordered:
        w = (W - 40) * v / tot
        if w >= .5:
            bars.append(f'<rect x="{x:.1f}" y="54" width="{w + .4:.1f}" height="8" fill="{lcol[k]}"/>')
        x += w
    bars.append(sweep(s, 20, 54, W - 40, 8, 5.2, .45, 56) + "</g>")
    s.add("".join(bars))
    for i, (k, v) in enumerate(top):
        y = 92 + i * 26
        pct = v / tot * 100
        bw = max(154 * pct / (top[0][1] / tot * 100), 4)
        c = lcol[k]
        fa = f' filter="url(#{gsm})"' if i < 2 else ""
        s.add(
            f'<circle cx="25" cy="{y - 4}" r="4" fill="{c}"{fa}/>',
            s.text(36, y, k, "body", 14.5, TEXT),
            f'<rect x="148" y="{y - 8}" width="154" height="6" rx="3" fill="{LINE}"/>',
            f'<rect x="148" y="{y - 8}" width="{bw:.1f}" height="6" rx="3" fill="{c}"{fa}/>',
            s.text(W - 20, y, f"{pct:.1f}%", "mono", 10.5, MINT if i == 0 else MUTED, "end"),
        )
    s.add(s.text(20, H - 18, "AGGREGATED ACROSS PUBLIC PROJECT REPOS (EXCL. THIS PROFILE REPO)", "mono", 8, DIM, ls=.4))
    return s


def activity_tile():
    W, H = TILE_W, 264
    repos = [(k, v) for k, v in T["repos"].items() if k != LOGIN and not v["fork"] and v["language"]]
    repos.sort(key=lambda kv: kv[1]["pushed_at"], reverse=True)
    repos = repos[:5]
    s = Svg(W, H, "Mission log, most recent pushes: " + "; ".join(f"{_proj_name(k)} {v['pushed_at'][:10]}" for k, v in repos))
    gsm = s.glow_sm()
    panel(s, W, H, MOSS_BRIGHT, "MISSION LOG // RECENT PUSHES", "AUTO", dur=12.4)
    s.add(
        f'<line x1="104" y1="58" x2="104" y2="{58 + 40 * (len(repos) - 1)}" stroke="{MOSS}" stroke-width="1.8" opacity=".55"/>',
        f'<line x1="104" y1="58" x2="104" y2="98" stroke="{EMERALD}" stroke-width="2" filter="url(#{gsm})"/>',
    )
    for i, (k, v) in enumerate(repos):
        y = 60 + i * 40
        d = dt.date.fromisoformat(v["pushed_at"][:10])
        col = EMERALD if i == 0 else MOSS_BRIGHT
        s.add(
            s.text(20, y + 4, d.strftime("%Y·%m·%d"), "mono", 10, MINT if i == 0 else MUTED),
            f'<circle cx="104" cy="{y}" r="5" fill="{VOID}" stroke="{col}" stroke-width="2.2" filter="url(#{gsm})"/>',
            (f'<circle cx="104" cy="{y}" r="10" fill="none" stroke="{EMERALD}" class="pulse" filter="url(#{gsm})"/>' if i == 0 else ""),
            s.text(122, y + 5, _proj_name(k), "bold", 15, TEXT),
        )
        lang = v["language"].upper()
        lw = measure(lang, "mono", 8.5, .4) + 14
        chip(s, W - 20 - lw, y - 9, lang, EMERALD if i == 0 else MOSS_BRIGHT, 8.5, 7, 18)
    return s


# ───────────────────────────── MODULE 06 · ARCHIVE ─────────────────────────────
def achievements(mobile=False):
    items = []
    for a in P["achievements"]:
        d = a["detail"].replace("LIVE:public_repos", str(T["public_repos"]))
        items.append((a["icon"], a["title"], d))
    W = MOBILE_W if mobile else FULL_W
    cols = 2 if mobile else len(items)
    rows = math.ceil(len(items) / cols)
    rh = 172
    H = 56 + rows * rh + 8
    s = Svg(W, H, "Mission archive: " + "; ".join(f"{t} — {d}" for _, t, d in items))
    gsm, glg = s.glow_sm(), s.glow_lg()
    panel(s, W, H, EMERALD, "MISSION ARCHIVE // VERIFIED RECORDS", f"{len(items)} ENTRIES", dur=13.5)
    cw = (W - 40) / cols
    hg, rg = s.uid("hg"), s.uid("mr")
    s.defs.append(
        f'<linearGradient id="{hg}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{MINT}"/><stop offset=".5" stop-color="{EMERALD}"/>'
        f'<stop offset="1" stop-color="{MOSS}"/></linearGradient>'
        f'<radialGradient id="{rg}"><stop offset="0" stop-color="{EMERALD}" stop-opacity=".34"/>'
        f'<stop offset="1" stop-color="{EMERALD}" stop-opacity="0"/></radialGradient>'
    )
    for i, (ic, title, det) in enumerate(items):
        r_, c_ = divmod(i, cols)
        cx = (W / 2) if (mobile and r_ == rows - 1 and len(items) % cols) else (20 + c_ * cw + cw / 2)
        cy = 56 + r_ * rh + 48
        hexp = " ".join(f"{cx + 34 * math.cos(math.radians(a)):.1f},{cy + 34 * math.sin(math.radians(a)):.1f}" for a in range(-90, 270, 60))
        hexi = " ".join(f"{cx + 27 * math.cos(math.radians(a)):.1f},{cy + 27 * math.sin(math.radians(a)):.1f}" for a in range(-90, 270, 60))
        s.add(
            f'<circle cx="{cx:.1f}" cy="{cy}" r="52" fill="url(#{rg})" opacity=".35">'
            f'<animate attributeName="opacity" values=".22;.85;.22" dur="4.5s" begin="{i * .9:.1f}s" repeatCount="indefinite"/></circle>',
            f'<polygon points="{hexp}" fill="#05110A" stroke="url(#{hg})" stroke-width="2.5" filter="url(#{gsm})"/>',
            f'<polygon points="{hexi}" fill="none" stroke="{MOSS_BRIGHT}" stroke-opacity=".5"/>',
            f'<path transform="translate({cx - 14:.1f} {cy - 14}) scale(1.1667)" d="{GLYPHS[ic]}" '
            f'fill="none" stroke="{MINT}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" filter="url(#{gsm})"/>',
            s.text(cx, cy + 63, title, "bold", 15, TEXT, "middle"),
        )
        for j, line in enumerate(wrap(det, "body", 12.5, cw - 14)[:2]):
            s.add(s.text(cx, cy + 81 + j * 15, line, "body", 12.5, BODY_TEXT, "middle"))
    return s


# ───────────────────────────── MODULE 07 · UPLINK + FINALE ─────────────────────────────
def social_pill(soc, idx=0):
    W, H = 270, 54
    s = Svg(W, H, f"{soc['label']}: {soc['handle']}")
    gsm = s.glow_sm()
    col = BRAND[soc["key"]][1]
    amb = s.uid("sa")
    s.defs.append(
        f'<radialGradient id="{amb}" cx="12%" cy="50%" r="65%">'
        f'<stop offset="0" stop-color="{col}" stop-opacity=".18"/>'
        f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
    )
    s.add(
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="{PANEL}"/>',
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="url(#{amb})"/>',
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="none" stroke="{BEZEL}" stroke-width="1.5"/>',
        laser_border(s, 1, 1, W - 2, H - 2, 10, col, dur=8.5 + idx * 0.6, beam=70, sw=1.3),
        f'<rect x="1" y="5" width="4" height="{H - 10}" rx="2" fill="{col}" filter="url(#{gsm})"/>',
        f'<rect x="15" y="11" width="32" height="32" rx="8" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".6"/>',
        icon(soc["key"], 22, 18, 18, col, filt=gsm),
        s.text(59, 25, soc["label"].upper(), "display", 11, TEXT, ls=1.5),
    )
    hs = 10
    while measure(soc["handle"], "mono", hs) > W - 92 and hs > 7.5:
        hs -= .5
    s.add(
        s.text(59, 41, soc["handle"], "mono", hs, MUTED),
        s.text(W - 14, 25, "↗", "body", 15, col, "end", extra=f'filter="url(#{gsm})"'),
    )
    return s


def finale(mobile=False):
    W, H = (MOBILE_W, 384) if mobile else (FULL_W, 326)
    words = [w.upper() for w in P["identity"]["philosophy"]]
    s = Svg(W, H, f"{' · '.join(words)} — {P['identity']['name']}. Independent fan-inspired design; not affiliated with Marvel.")
    gsm, glg = s.glow_sm(), s.glow_lg()
    clip, ov = s.uid("fc"), s.uid("fo")
    s.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
    s.defs.append(
        f'<linearGradient id="{ov}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{VOID}" stop-opacity=".58"/>'
        f'<stop offset=".44" stop-color="{VOID}" stop-opacity=".08"/>'
        f'<stop offset=".72" stop-color="{VOID}" stop-opacity=".80"/>'
        f'<stop offset="1" stop-color="{VOID}" stop-opacity=".97"/></linearGradient>'
    )
    cy = 142 if not mobile else 132
    s.add(
        f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{VOID}"/>'
        f'<image href="{img_uri("finale.webp", W, H, focus=(.5, .5 if not mobile else .45), q=66)}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
        f'<rect width="{W}" height="{H}" fill="url(#{ov})"/>',
        f'<g transform="translate({W / 2} {cy})">'
        f'<g filter="url(#{gsm})">{spin(56)}<circle r="{120 if not mobile else 102}" fill="none" stroke="{EMERALD}" stroke-width="1.4" stroke-dasharray="2 9" opacity=".88"/></g>'
        f'<g>{spin(22, True)}<circle r="{96 if not mobile else 82}" fill="none" stroke="{MOSS_BRIGHT}" stroke-width="1.6" stroke-dasharray="30 12 4 12" opacity=".82"/></g></g>',
        particles(s, 0, 56, W, H - 56, 26 if not mobile else 16, seed=11),
        scanline(s, 0, 0, W, H, 8.0, EMERALD, .10),
        "</g>",
    )
    s.add(
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="{BEZEL}" stroke-width="1.5"/>',
        laser_border(s, 1, 1, W - 2, H - 2, 16, EMERALD, dur=12.0, beam=150, sw=1.8),
        brackets(10, 10, W - 20, H - 20, EMERALD, 18, 2, filt=gsm),
        s.text(W / 2, 34, "END OF TRANSMISSION // EMERALD CONTINUUM", "mono", 10 if not mobile else 9, EMERALD, "middle", ls=2.6, extra=f'opacity=".45" filter="url(#{gsm})"'),
        s.text(W / 2, 34, "END OF TRANSMISSION // EMERALD CONTINUUM", "mono", 10 if not mobile else 9, MINT, "middle", ls=2.6),
    )
    lines = [words] if not mobile else [words[:3], words[3:]]
    fs = 20 if not mobile else 17
    dot_gap = 28 if not mobile else 22
    n = len(words)
    k = 0
    base_y = H - 94 if not mobile else H - 128
    for li, ln in enumerate(lines):
        wws = [measure(wd, "display", fs, 2) for wd in ln]
        tw = sum(wws) + dot_gap * max(len(ln) - 1, 0)
        x = W / 2 - tw / 2
        y = base_y + li * 32
        for j, (wd, ww) in enumerate(zip(ln, wws)):
            s.add(s.text(x, y, wd, "display", fs, MOSS, ls=2))
            kt = f"0;{k / n * .8:.3f};{k / n * .8 + .08:.3f};{k / n * .8 + .32:.3f};1"
            s.add(
                s.text(x, y, wd, "display", fs, MINT, ls=2, extra=f'opacity="0" filter="url(#{glg})"').replace(
                    "</text>", f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt}" dur="7s" repeatCount="indefinite"/></text>'
                )
            )
            x += ww
            if j < len(ln) - 1:
                s.add(s.text(x + dot_gap / 2, y, "·", "display", fs, EMERALD, "middle", extra=f'filter="url(#{gsm})"'))
                x += dot_gap
            k += 1
    s.add(
        s.text(W / 2, H - 50, f"— {P['identity']['name'].upper()}", "mono", 11, TEXT, "middle", ls=2.5),
        s.text(W / 2, H - 24, "Original fan-inspired artwork & code · not affiliated with or endorsed by Marvel or Disney",
               "body", 11 if not mobile else 9.5, DIM, "middle"),
    )
    return s


def top_pill():
    label = f"▲ RETURN TO COMMAND DECK  ·  TELEMETRY SYNC {T['synced_at']}"
    w = int(measure(label, "mono", 9.5, 1.1) + 40)
    s = Svg(w, 32, "Return to top of profile")
    gsm = s.glow_sm()
    s.add(
        f'<rect x="1" y="1" width="{w - 2}" height="30" rx="7" fill="{PANEL}" stroke="{BEZEL}" stroke-width="1.5"/>',
        laser_border(s, 1, 1, w - 2, 30, 7, EMERALD, dur=8.0, beam=70, sw=1.3),
        s.text(w / 2, 19.5, label, "mono", 9.5, EMERALD, "middle", ls=1.1, extra=f'opacity=".42" filter="url(#{gsm})"'),
        s.text(w / 2, 19.5, label, "mono", 9.5, MINT, "middle", ls=1.1),
    )
    return s


# ───────────────────────────── README COMPILER ─────────────────────────────
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
    for idx, p in enumerate(P["projects"]):
        out[f"p_{p['id']}"] = write(f"assets/projects/{p['id']}.svg", project_card(p, idx))
        out[f"pl_{p['id']}"] = write(f"assets/projects/link-{p['id']}.svg", portal_pill(p["name"], active=bool(p["repo"])))
    for m in P["archive_more"]:
        short = m["label"].split(" — ")[0].upper()
        slug = m["repo"].lower().replace("_", "-")
        out[f"pa_{slug}"] = write(f"assets/projects/link-{slug}.svg", portal_pill(short, active=True, sub=True))
    out["pa_all"] = write("assets/projects/link-all-repos.svg", portal_pill(f"ALL {T['public_repos']} REPOSITORIES", active=True, sub=True))
    out["heat"] = write("assets/command/radar.svg", heatmap())
    out["heat_m"] = write("assets/command/radar-mobile.svg", heatmap(True))
    out["tele"] = write("assets/command/telemetry.svg", telemetry_tile())
    out["streak"] = write("assets/command/streak.svg", streak_tile())
    out["lang"] = write("assets/command/languages.svg", language_tile())
    out["log"] = write("assets/command/activity.svg", activity_tile())
    out["ach"] = write("assets/archive/records.svg", achievements())
    out["ach_m"] = write("assets/archive/records-mobile.svg", achievements(True))
    for idx, soc in enumerate(P["socials"]):
        out[f"s_{soc['key']}"] = write(f"assets/uplink/{soc['key']}.svg", social_pill(soc, idx))
    out["fin"] = write("assets/finale/finale.svg", finale())
    out["fin_m"] = write("assets/finale/finale-mobile.svg", finale(True))
    out["top"] = write("assets/finale/top.svg", top_pill())

    # Build or verify all 8 autonomous Miss Minutes TVA GIF modules
    gif_keys = ("welcome", "inspector", "operator", "uplink")
    need_gifs = "--skip-gifs" not in sys.argv
    if not need_gifs:
        for gk in gif_keys:
            if not os.path.isfile(os.path.join(ROOT, f"assets/tva/miss-minutes-{gk}.gif")):
                need_gifs = True
    if need_gifs:
        miss_minutes.build_all_gifs()
    for gk in gif_keys:
        out[f"mm_{gk}"] = f"assets/tva/miss-minutes-{gk}.gif"
        out[f"mm_{gk}_m"] = f"assets/tva/miss-minutes-{gk}-mobile.gif"

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
    A("&nbsp;\n".join(f'<a href="#{k}"><img src="{o["nav_" + k]}" height="34" alt="{n} {t.title()}"></a>' for k, n, t, _ in MODULES))
    A("\n<br><br>\n")
    A(picture(
        o["mm_welcome"],
        o["mm_welcome_m"],
        "TVA Autonomous Intelligence Miss Minutes — Timedoor arrival, greeting wave, and Level 616 engineer biometric scan",
    ))
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
    A('<p align="center">\n' + picture(
        o["mm_inspector"],
        o["mm_inspector_m"],
        "Miss Minutes Sacred Timeline Detective — dropping from ceiling Timedoor to audit 6 flagship AI project branches and Sylvie Nexus memory",
    ) + "\n</p>\n")
    A("<br>\n")
    # 03 multiverse
    A(header_block(*mods["multiverse"], o))
    cards = []
    portal_pills = []
    for p in P["projects"]:
        href = f"https://github.com/{LOGIN}/{p['repo']}" if p["repo"] else None
        cards.append((o[f"p_{p['id']}"], alt_of(o[f"p_{p['id']}"]), href))
        p_img = f'<img src="{o["pl_" + p["id"]]}" height="28" alt="{esc(p["name"])}">'
        portal_pills.append(f'<a href="{href}">{p_img}</a>' if href else p_img)
    A(tiles(*cards))
    archive_pills = []
    for m in P["archive_more"]:
        short = m["label"].split(" — ")[0]
        slug = m["repo"].lower().replace("_", "-")
        archive_pills.append(
            f'<a href="https://github.com/{LOGIN}/{m["repo"]}"><img src="{o["pa_" + slug]}" height="26" alt="{esc(short)}"></a>'
        )
    archive_pills.append(
        f'<a href="https://github.com/{LOGIN}?tab=repositories"><img src="{o["pa_all"]}" height="26" alt="All repositories"></a>'
    )
    A('<p align="center">\n' + "&nbsp;\n".join(portal_pills) + "\n</p>\n"
      '<p align="center">\n' + "&nbsp;\n".join(archive_pills) + "\n</p>\n")
    A("<br>\n")
    # 04 command
    A(header_block(*mods["command"], o))
    A('<p align="center">\n' + picture(o["heat"], o["heat_m"], alt_of(o["heat"])) + "\n</p>\n")
    A('<p align="center">\n' + picture(
        o["mm_operator"],
        o["mm_operator_m"],
        "Miss Minutes Temporal Loom Telemetry Operator — high-speed holographic code typing and reactor streak boost",
    ) + "\n</p>\n")
    A(tiles((o["tele"], alt_of(o["tele"]), None), (o["streak"], alt_of(o["streak"]), None),
            (o["lang"], alt_of(o["lang"]), None), (o["log"], alt_of(o["log"]), None)))
    A("<br>\n")
    # 05 archive
    A(header_block(*mods["archive"], o))
    A('<p align="center">\n' + picture(o["ach"], o["ach_m"], alt_of(o["ach"])) + "\n</p>\n")
    A("<br>\n")
    # 06 uplink
    A(header_block(*mods["uplink"], o))
    A('<p align="center">\n' + picture(
        o["mm_uplink"],
        o["mm_uplink_m"],
        "Miss Minutes Multiverse Uplink Dispatcher — zero-gravity patrol conjuring 5 verified communication channels and 360 celebratory spin",
    ) + "\n</p>\n")
    soc_tags = [
        f'<a href="{s_["url"]}"><img src="{o["s_" + s_["key"]]}" width="270" alt="{esc(s_["label"])}: {esc(s_["handle"])}"></a>'
        for s_ in P["socials"]
    ]
    A('<p align="center">\n' + "&nbsp;\n".join(soc_tags[:3]) + "\n</p>\n"
      '<p align="center">\n' + "&nbsp;\n".join(soc_tags[3:]) + "\n</p>\n")
    A("<br>\n")
    A('<div align="center">\n' + picture(o["fin"], o["fin_m"], alt_of(o["fin"])) + "\n")
    A(f'\n<br><br>\n<a href="#top"><img src="{o["top"]}" height="32" alt="Return to top of profile"></a>\n</div>\n')
    # Accessible plain-text version
    A("\n<details>\n<summary><sub>Plain-text dossier (accessible version)</sub></summary>\n")
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
