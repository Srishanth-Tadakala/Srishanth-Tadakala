"""TVA // EMERALD CONTINUUM — Autonomous Miss Minutes GIF Animation Engine.

Procedurally rigs, animates, supersamples (2x SSAA), and optical-blooms 4 distinct
story-driven Miss Minutes intelligence modules (desktop 840px + mobile 420px = 8 GIFs)
in 100% cohesive Jet Black (#020403/#050907), Muted Moss Green (#162A1E/#254531/#588C69),
and Neon Emerald Green (#00FF88/#88FFC8).

Modules generated in assets/tva/:
  1. miss-minutes-welcome(.gif / -mobile.gif)   — Timedoor arrival, wave, TemPad biometric scan, portal dive
  2. miss-minutes-inspector(.gif / -mobile.gif) — Ceiling drop, Right->Left Sacred Timeline & Sylvie detective scan
  3. miss-minutes-operator(.gif / -mobile.gif)  — Console pop-up, high-speed holo-typing, Temporal Loom gear boost
  4. miss-minutes-uplink(.gif / -mobile.gif)    — Zero-G patrol, uplink packet dispatch, 360 cartwheel & dissolve
"""
from __future__ import annotations

import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR_FONTS = os.path.join(ROOT, "scripts", "vendor", "fonts")
OUT_DIR = os.path.join(ROOT, "assets", "tva")

# ─────────────── STRICT JET BLACK × MUTED MOSS × NEON EMERALD PALETTE ───────────────
VOID = (2, 4, 3)
PANEL_TOP = (8, 16, 11)
PANEL_BOT = (2, 4, 3)
LINE = (22, 42, 30)
BEZEL = (37, 69, 49)

MOSS = (88, 140, 105)
MOSS_BRIGHT = (122, 179, 139)

EMERALD_DARK = (8, 92, 50)
EMERALD_MID = (16, 184, 100)
EMERALD_FACE = (26, 228, 128)
EMERALD = (0, 255, 136)
MINT = (136, 255, 200)
WHITE_MINT = (232, 255, 244)
INK = (2, 11, 6)

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    key = (name, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(os.path.join(VENDOR_FONTS, name), size)
    return _FONT_CACHE[key]


def _lerp(a: float, b: float, t: float) -> float:
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _bezier(p0, p1, p2, p3, steps: int = 18) -> list[tuple[float, float]]:
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = (u**3) * p0[0] + 3 * (u**2) * t * p1[0] + 3 * u * (t**2) * p2[0] + (t**3) * p3[0]
        y = (u**3) * p0[1] + 3 * (u**2) * t * p1[1] + 3 * u * (t**2) * p2[1] + (t**3) * p3[1]
        pts.append((x, y))
    return pts


def _rot(x: float, y: float, cx: float, cy: float, deg: float) -> tuple[float, float]:
    rad = math.radians(deg)
    ca, sa = math.cos(rad), math.sin(rad)
    dx, dy = x - cx, y - cy
    return cx + dx * ca - dy * sa, cy + dx * sa + dy * ca


def _star_pts(cx: float, cy: float, r_out: float, r_in: float, n: int = 5, rot_deg: float = -90.0):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot_deg + i * 180.0 / n)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _build_palettes() -> tuple[Image.Image, list[int]]:
    """Deterministic 255-color emerald ramp (0..254) + slot 255 reserved for outer-corner transparency."""
    cols: list[tuple[int, int, int]] = []
    # 1. Fine Jet Black -> dark moss obsidian (64 continuous steps for zero-band dark gradients)
    for i in range(64):
        t = i / 63.0
        r = int(2 + t * 24)
        g = int(4 + t * 56)
        b = int(3 + t * 36)
        cols.append((r, max(g, r, b), b))
    # 2. Muted moss -> luminous sage (64 steps)
    for i in range(64):
        t = i / 63.0
        r = int(26 + t * 114)
        g = int(60 + t * 144)
        b = int(40 + t * 120)
        cols.append((r, max(g, r, b), b))
    # 3. Deep emerald plasma -> pure Neon Emerald #00FF88 (64 steps)
    for i in range(64):
        t = i / 63.0
        r = int((t**1.9) * 32)
        g = int(44 + t * 211)
        b = int(24 + t * 112)
        cols.append((r, max(g, r, b), b))
    # 4. Neon Emerald #00FF88 -> Hyper-Mint #88FFC8 -> Mint-White #F2FFF8 (63 steps -> 255 total)
    for i in range(63):
        t = i / 62.0
        r = int(t * 246)
        b = int(136 + t * 114)
        cols.append((r, 255, b))

    quant_flat: list[int] = []
    final_flat: list[int] = []
    for r, g, b in cols[:255]:
        c = (r, max(g, r, b), b)
        quant_flat.extend(c)
        final_flat.extend(c)
    # Slot 255: sentinel magenta during quantization so 0 interior pixels map to 255; VOID in final GIF palette
    quant_flat.extend((255, 0, 255))
    final_flat.extend(VOID)

    q_img = Image.new("P", (16, 16))
    q_img.putpalette(quant_flat)
    return q_img, final_flat


MASTER_PAL_IMG, FINAL_PALETTE = _build_palettes()
_CORNER_MASK_CACHE: dict[tuple[int, int], Image.Image] = {}


def _corner_exterior_mask(w: int, h: int) -> Image.Image:
    key = (w, h)
    if key not in _CORNER_MASK_CACHE:
        m = Image.new("L", (w, h), 255)
        md = ImageDraw.Draw(m)
        md.rounded_rectangle([0, 0, w - 1, h - 1], radius=12, fill=0)
        _CORNER_MASK_CACHE[key] = m
    return _CORNER_MASK_CACHE[key]


def quantize_emerald(im: Image.Image) -> Image.Image:
    """Silky noise-free quantization against our 255-step emerald ramp + clean rounded-corner transparency."""
    p_im = im.convert("RGB").quantize(palette=MASTER_PAL_IMG, dither=Image.Dither.NONE)
    p_im.putpalette(FINAL_PALETTE)
    p_im.paste(255, mask=_corner_exterior_mask(im.width, im.height))
    return p_im


# ─────────────── SHARED HUD CORRIDOR BACKGROUND PLATE ───────────────
def make_hud_plate(w: int, h: int, S: int, title: str, right_code: str, floor_y: int) -> Image.Image:
    """Render 2x supersampled Jet-Black + Muted-Moss HUD corridor background plate."""
    W, H = w * S, h * S
    im = Image.new("RGB", (W, H), VOID)
    dr = ImageDraw.Draw(im)

    for y in range(2 * S, H - 2 * S):
        t = y / H
        r = int(_lerp(PANEL_TOP[0], PANEL_BOT[0], t))
        g = int(_lerp(PANEL_TOP[1], PANEL_BOT[1], t))
        b = int(_lerp(PANEL_TOP[2], PANEL_BOT[2], t))
        dr.line([(2 * S, y), (W - 2 * S, y)], fill=(r, g, b))

    step = 20 * S
    for gx in range(step, W - 4 * S, step):
        dr.line([(gx, 26 * S), (gx, H - 4 * S)], fill=(13, 27, 19), width=max(1, S // 2))
    for gy in range(26 * S, H - 4 * S, step):
        dr.line([(4 * S, gy), (W - 4 * S, gy)], fill=(13, 27, 19), width=max(1, S // 2))

    # Perspective holographic catwalk floor grid
    fy = floor_y * S
    dr.line([(14 * S, fy), (W - 14 * S, fy)], fill=(32, 74, 48), width=S)
    vanish_x = W // 2
    for i in range(-9, 10):
        bx = vanish_x + i * 52 * S
        tx = vanish_x + int(i * 36 * S)
        dr.line([(tx, fy), (bx, H - 4 * S)], fill=(18, 42, 28), width=max(1, S // 2))
    for ry in (fy + 6 * S, fy + 12 * S):
        if ry < H - 4 * S:
            dr.line([(14 * S, ry), (W - 14 * S, ry)], fill=(20, 46, 30), width=max(1, S // 2))

    # Header telemetry strip
    f_mono = _load_font("JetBrainsMono.ttf", int(8.6 * S))
    cx_d, cy_d, d_r = 19 * S, 15 * S, 3 * S
    dr.polygon([(cx_d, cy_d - d_r), (cx_d + d_r, cy_d), (cx_d, cy_d + d_r), (cx_d - d_r, cy_d)], fill=EMERALD)
    dr.text((28 * S, 9 * S), title, font=f_mono, fill=EMERALD)
    rc_w = dr.textlength(right_code, font=f_mono)
    dr.text((W - 18 * S - rc_w, 9 * S), right_code, font=f_mono, fill=MOSS_BRIGHT)
    dr.line([(16 * S, 24 * S), (W - 16 * S, 24 * S)], fill=LINE, width=S)
    dr.line([(16 * S, 24 * S), (116 * S, 24 * S)], fill=EMERALD, width=int(1.5 * S))

    # Outer muted-moss architectural bezel + corner targeting brackets
    dr.rounded_rectangle([S, S, W - 2 * S, H - 2 * S], radius=12 * S, outline=BEZEL, width=int(1.5 * S))
    bL = 10 * S
    m = 6 * S
    for bx0, by0, sx, sy in ((m, m, 1, 1), (W - m, m, -1, 1), (W - m, H - m, -1, -1), (m, H - m, 1, -1)):
        dr.line([(bx0, by0 + sy * bL), (bx0, by0), (bx0 + sx * bL, by0)], fill=EMERALD, width=int(1.6 * S))

    return im


def draw_laser_bezel(dr: ImageDraw.ImageDraw, glow_dr: ImageDraw.ImageDraw, w: int, h: int, S: int, phase: float):
    """Animated orbiting neon-emerald photon beam traveling around the GIF's outer bezel."""
    W, H = w * S, h * S
    pts = [(12 * S, S), (W - 12 * S, S), (W - S, 12 * S), (W - S, H - 12 * S),
           (W - 12 * S, H - S), (12 * S, H - S), (S, H - 12 * S), (S, 12 * S), (12 * S, S)]
    segs = []
    tot = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, d))
        tot += d
    beam = 110 * S
    head = (phase % 1.0) * tot
    for offset in (0.0, tot):
        s0 = head - beam + offset
        s1 = head + offset
        acc = 0.0
        for a, b, d in segs:
            e0, e1 = acc, acc + d
            acc = e1
            lo, hi = max(s0, e0), min(s1, e1)
            if hi > lo and d > 0:
                t0, t1 = (lo - e0) / d, (hi - e0) / d
                p0 = (_lerp(a[0], b[0], t0), _lerp(a[1], b[1], t0))
                p1 = (_lerp(a[0], b[0], t1), _lerp(a[1], b[1], t1))
                glow_dr.line([p0, p1], fill=EMERALD, width=int(3.0 * S))
                dr.line([p0, p1], fill=MINT, width=int(1.5 * S))


# ─────────────── 3D TVA TIMEDOOR PORTAL RENDERER ───────────────
def draw_timedoor(
    canvas: Image.Image,
    glow: Image.Image,
    cx: float,
    cy: float,
    S: int,
    open_amt: float,
    skew: float = 1.0,
    phase: float = 0.0,
):
    """Draw a glowing 3D perspective TVA Timedoor rectangular holographic doorway."""
    if open_amt <= 0.02:
        return
    dr = ImageDraw.Draw(canvas, "RGBA")
    gdr = ImageDraw.Draw(glow, "RGBA")

    pw = (20 * open_amt) * S
    ph = (31 * min(1.0, open_amt * 1.35)) * S
    sk = 4.5 * S * skew

    tl = (cx - pw, cy - ph - sk * 0.4)
    tr = (cx + pw, cy - ph + sk * 0.4)
    br = (cx + pw, cy + ph - sk * 0.4)
    bl = (cx - pw, cy + ph + sk * 0.4)

    cone = [tl, tr, (tr[0] + 16 * S * skew, br[1] + 5 * S), (bl[0] + 7 * S * skew, bl[1] + 5 * S)]
    dr.polygon(cone, fill=(0, 255, 136, int(36 * open_amt)))
    gdr.polygon([tl, tr, br, bl], fill=(0, 255, 136, int(145 * open_amt)))

    dr.polygon([tl, tr, br, bl], fill=(16, 175, 96, int(135 * open_amt)))
    for i in range(1, 5):
        f = i / 5.0
        dr.line([(tl[0], _lerp(tl[1], bl[1], f)), (tr[0], _lerp(tr[1], br[1], f))],
                fill=(136, 255, 200, int(130 * open_amt)), width=max(1, S // 2))
    for i in range(1, 3):
        f = i / 3.0
        dr.line([(_lerp(tl[0], tr[0], f), _lerp(tl[1], tr[1], f)),
                 (_lerp(bl[0], br[0], f), _lerp(bl[1], br[1], f))],
                fill=(136, 255, 200, int(110 * open_amt)), width=max(1, S // 2))

    sf = (phase * 2.3) % 1.0
    dr.line([(tl[0], _lerp(tl[1], bl[1], sf)), (tr[0], _lerp(tr[1], br[1], sf))],
            fill=(232, 255, 244, int(210 * open_amt)), width=int(1.5 * S))

    gdr.line([tl, tr, br, bl, tl], fill=(0, 255, 136, 255), width=int(3.4 * S))
    dr.line([tl, tr, br, bl, tl], fill=(220, 255, 238, 255), width=int(1.5 * S))


# ─────────────── STUDIO-GRADE MISS MINUTES PROCEDURAL RIG ───────────────
def _draw_glove(
    dr: ImageDraw.ImageDraw,
    gdr: ImageDraw.ImageDraw,
    wx: float,
    wy: float,
    angle_deg: float,
    S: int,
    pose: str = "open",
    scale: float = 1.0,
):
    k = S * scale
    gdr.ellipse([wx - 6.5 * k, wy - 6.5 * k, wx + 6.5 * k, wy + 6.5 * k], fill=(0, 255, 136, 115))

    rad = math.radians(angle_deg)
    px = wx + math.cos(rad) * 4.4 * k
    py = wy + math.sin(rad) * 4.4 * k

    if pose in ("wave", "open"):
        for fa, fl in ((-38, 7.0), (-12, 8.0), (13, 7.6), (38, 6.2)):
            ang = math.radians(angle_deg + fa)
            fx = px + math.cos(ang) * fl * k
            fy = py + math.sin(ang) * fl * k
            dr.line([(px, py), (fx, fy)], fill=INK, width=int(4.0 * k))
            dr.ellipse([fx - 2.0 * k, fy - 2.0 * k, fx + 2.0 * k, fy + 2.0 * k], fill=INK)
            dr.line([(px, py), (fx, fy)], fill=WHITE_MINT, width=int(2.5 * k))
            dr.ellipse([fx - 1.25 * k, fy - 1.25 * k, fx + 1.25 * k, fy + 1.25 * k], fill=WHITE_MINT)
    elif pose == "point":
        ang = math.radians(angle_deg)
        fx = px + math.cos(ang) * 9.2 * k
        fy = py + math.sin(ang) * 9.2 * k
        dr.line([(px, py), (fx, fy)], fill=INK, width=int(4.0 * k))
        dr.ellipse([fx - 2.0 * k, fy - 2.0 * k, fx + 2.0 * k, fy + 2.0 * k], fill=INK)
        dr.line([(px, py), (fx, fy)], fill=WHITE_MINT, width=int(2.5 * k))
        dr.ellipse([fx - 1.3 * k, fy - 1.3 * k, fx + 1.3 * k, fy + 1.3 * k], fill=WHITE_MINT)

    r_p = 4.5 * k
    dr.ellipse([px - r_p - 0.8 * k, py - r_p - 0.8 * k, px + r_p + 0.8 * k, py + r_p + 0.8 * k], fill=INK)
    dr.ellipse([px - r_p, py - r_p, px + r_p, py + r_p], fill=WHITE_MINT)

    for sa in (-14, 10):
        a2 = math.radians(angle_deg + sa)
        dr.line(
            [(px + math.cos(a2) * 0.8 * k, py + math.sin(a2) * 0.8 * k),
             (px + math.cos(a2) * 3.0 * k, py + math.sin(a2) * 3.0 * k)],
            fill=INK,
            width=max(1, int(0.8 * k)),
        )

    c_perp = rad + math.pi / 2
    c0 = (wx - math.cos(c_perp) * 3.1 * k, wy - math.sin(c_perp) * 3.1 * k)
    c1 = (wx + math.cos(c_perp) * 3.1 * k, wy + math.sin(c_perp) * 3.1 * k)
    dr.line([c0, c1], fill=INK, width=int(3.6 * k))
    dr.line([c0, c1], fill=MINT, width=int(2.0 * k))


def _draw_boot(
    dr: ImageDraw.ImageDraw,
    gdr: ImageDraw.ImageDraw,
    ax: float,
    ay: float,
    facing: float,
    foot_deg: float,
    S: int,
    scale: float = 1.0,
    contact: float = 0.0,
):
    k = S * scale
    dir_s = 1.0 if facing >= 0 else -1.0

    if contact > 0.05:
        rw = (8.5 + 7.5 * contact) * k
        rh = (2.2 + 1.6 * contact) * k
        al = int(155 * (1.0 - 0.5 * contact))
        gdr.ellipse([ax - rw, ay + 3 * k - rh, ax + rw, ay + 3 * k + rh], outline=(0, 255, 136, al), width=int(1.4 * k))

    local_boot = [
        (-3.5 * k * dir_s, -1.5 * k),
        (3.0 * k * dir_s, -1.5 * k),
        (9.0 * k * dir_s, 0.8 * k),
        (9.4 * k * dir_s, 4.0 * k),
        (1.8 * k * dir_s, 4.4 * k),
        (0.5 * k * dir_s, 3.0 * k),
        (-0.8 * k * dir_s, 4.5 * k),
        (-4.0 * k * dir_s, 4.5 * k),
    ]
    pts = [_rot(ax + dx, ay + dy, ax, ay, foot_deg) for dx, dy in local_boot]
    gdr.polygon(pts, outline=(0, 255, 136, 170))
    dr.polygon(pts, fill=(11, 56, 32), outline=EMERALD)
    hx, hy = _rot(ax + 6.0 * k * dir_s, ay + 1.6 * k, ax, ay, foot_deg)
    dr.ellipse([hx - 1.7 * k, hy - 1.0 * k, hx + 1.7 * k, hy + 1.0 * k], fill=MINT)
    dr.ellipse([ax - 3.5 * k, ay - 2.9 * k, ax + 3.5 * k, ay - 0.2 * k], fill=EMERALD_MID, outline=MINT)


def _draw_rubber_limb(dr, gdr, p0, p1, p2, p3, S: int, scale: float = 1.0):
    k = S * scale
    pts = _bezier(p0, p1, p2, p3, steps=16)
    gdr.line(pts, fill=(0, 255, 136, 145), width=int(5.4 * k))
    dr.line(pts, fill=EMERALD, width=int(3.6 * k), joint="curve")
    dr.line(pts, fill=INK, width=int(1.9 * k), joint="curve")


def draw_miss_minutes(
    canvas: Image.Image,
    glow: Image.Image,
    cx: float,
    cy: float,
    R: float,
    S: int,
    *,
    facing: float = 0.35,
    tilt: float = 0.0,
    spin_deg: float = 0.0,        # rigid full-sprite cartwheel rotation (0..360)
    sx: float = 1.0,
    sy: float = 1.0,
    expr: str = "happy",
    mouth: str = "smile",
    hour_deg: float = -55.0,
    min_deg: float = 65.0,
    look: tuple[float, float] = (0.2, 0.0),
    l_hand: tuple[float, float, str] | None = None,
    r_hand: tuple[float, float, str] | None = None,
    l_foot: tuple[float, float, float, float] | None = None,
    r_foot: tuple[float, float, float, float] | None = None,
    holo_alpha: float = 1.0,
    scan_phase: float = 0.0,
    prop: str | None = None,
):
    """Render studio-grade holographic Miss Minutes onto canvas & optical glow buffer."""
    if holo_alpha <= 0.03:
        return

    scale = R / (28.0 * S)
    k = S * scale

    pad = int(R * 2.9)
    pw, ph = pad * 2, pad * 2
    spr = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    sglow = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    dr = ImageDraw.Draw(spr, "RGBA")
    gdr = ImageDraw.Draw(sglow, "RGBA")
    ox, oy = float(pad), float(pad)

    rx = R * sx
    ry = R * sy
    tilt_clamped = max(-24.0, min(24.0, tilt))

    lf = l_foot or (-0.38, 1.60, 0.0, 0.0)
    rf = r_foot or (0.38, 1.60, 0.0, 0.0)
    lh = l_hand or (-1.42, 0.34, "open")
    rh = r_hand or (1.42, -0.54, "wave")

    # 1. Rubber-Hose Legs & Boots
    for side, ft in ((-1.0, lf), (1.0, rf)):
        hx0, hy0 = _rot(ox + side * 0.34 * rx, oy + 0.84 * ry, ox, oy, tilt_clamped)
        fx, fy = ox + ft[0] * R, oy + ft[1] * R
        bend = (0.25 if facing >= 0 else -0.25) * R
        c1 = (_lerp(hx0, fx, 0.35) + bend, _lerp(hy0, fy, 0.40))
        c2 = (_lerp(hx0, fx, 0.70) + bend * 0.6, _lerp(hy0, fy, 0.72))
        _draw_rubber_limb(dr, gdr, (hx0, hy0), c1, c2, (fx, fy), S, scale)
        _draw_boot(dr, gdr, fx, fy, facing if abs(facing) > 0.05 else side, ft[2], S, scale, ft[3])

    arm_specs = [(-1.0, lh), (1.0, rh)]
    back_side = -1.0 if facing >= 0 else 1.0

    def _render_arm(side: float, hspec: tuple[float, float, str]):
        sx0, sy0 = _rot(ox + side * 0.94 * rx, oy + 0.08 * ry, ox, oy, tilt_clamped)
        wx, wy = ox + hspec[0] * R, oy + hspec[1] * R
        elbow_out = side * 0.30 * R
        elbow_down = 0.26 * R
        c1 = (_lerp(sx0, wx, 0.35) + elbow_out, _lerp(sy0, wy, 0.35) + elbow_down)
        c2 = (_lerp(sx0, wx, 0.70) + elbow_out * 0.4, _lerp(sy0, wy, 0.70) + elbow_down * 0.3)
        _draw_rubber_limb(dr, gdr, (sx0, sy0), c1, c2, (wx, wy), S, scale)
        ang = math.degrees(math.atan2(wy - c2[1], wx - c2[0]))
        _draw_glove(dr, gdr, wx, wy, ang, S, hspec[2], scale)
        return wx, wy

    for side, hspec in arm_specs:
        if side == back_side:
            _render_arm(side, hspec)

    # 2. Glowing Holographic Clock Body
    gdr.ellipse([ox - rx * 1.18, oy - ry * 1.18, ox + rx * 1.18, oy + ry * 1.18], fill=(0, 255, 136, 125))
    dr.ellipse([ox - rx * 1.07, oy - ry * 1.07, ox + rx * 1.07, oy + ry * 1.07], fill=INK, outline=EMERALD, width=int(2.2 * k))
    dr.ellipse([ox - rx * 0.99, oy - ry * 0.99, ox + rx * 0.99, oy + ry * 0.99], fill=EMERALD_DARK, outline=MINT, width=int(1.3 * k))
    dr.ellipse([ox - rx * 0.93, oy - ry * 0.93, ox + rx * 0.93, oy + ry * 0.93], fill=(14, 178, 96, 245))
    dr.ellipse([ox - rx * 0.87 - rx * 0.04, oy - ry * 0.87 - ry * 0.05, ox + rx * 0.83, oy + ry * 0.81], fill=(28, 232, 130, 245))
    dr.ellipse([ox - rx * 0.65 - rx * 0.08, oy - ry * 0.65 - ry * 0.10, ox + rx * 0.52, oy + ry * 0.45], fill=(64, 250, 156, 175))

    # 3. 12 Clock Hour Ticks + Minute Sub-Ticks + Rotating Dial Hands
    for i in range(60):
        ang = math.radians(i * 6 + tilt_clamped - 90)
        ca, sa = math.cos(ang), math.sin(ang)
        if i % 5 == 0:
            cardinal = (i % 15 == 0)
            r_in = 0.74 if cardinal else 0.78
            r_out = 0.89
            dr.line(
                [(ox + ca * rx * r_in, oy + sa * ry * r_in), (ox + ca * rx * r_out, oy + sa * ry * r_out)],
                fill=INK,
                width=int((2.6 if cardinal else 1.7) * k),
            )
        else:
            px_d, py_d = ox + ca * rx * 0.85, oy + sa * ry * 0.85
            dr.ellipse([px_d - 0.5 * k, py_d - 0.5 * k, px_d + 0.5 * k, py_d + 0.5 * k], fill=(6, 78, 42, 200))

    f_shift = facing * 0.11 * rx
    hub_x, hub_y = _rot(ox + f_shift * 0.45, oy + 0.03 * ry, ox, oy, tilt_clamped)
    for h_deg, h_len, h_w in ((hour_deg, 0.46, 2.0), (min_deg, 0.66, 1.4)):
        ang = math.radians(h_deg + tilt_clamped - 90)
        dr.line(
            [(hub_x, hub_y), (hub_x + math.cos(ang) * rx * h_len, hub_y + math.sin(ang) * ry * h_len)],
            fill=(6, 86, 46, 190),
            width=int(h_w * k),
        )

    # 4. Pie-Cut Eyes, Eyebrows, Clock-Pin Nose & Smile
    eye_y = oy - 0.17 * ry
    for eside in (-1.0, 1.0):
        ex, ey = _rot(ox + f_shift + eside * 0.23 * rx, eye_y, ox, oy, tilt_clamped)
        ew = 0.175 * rx * (1.20 if (expr == "detective" and eside > 0) else 1.0)
        eh = 0.275 * ry * (1.16 if expr in ("ooh", "detective") and eside > 0 else 1.0)

        is_wink = (expr == "wink" and eside > 0)
        is_blink = (expr == "blink")
        is_proud = (expr == "proud")
        is_squint = (expr == "detective" and eside < 0)

        if is_wink or is_blink or is_proud:
            arc_box = [ex - ew, ey - eh * 0.45, ex + ew, ey + eh * 0.55]
            start_a, end_a = (195, 345) if (is_wink or is_proud) else (15, 165)
            dr.arc(arc_box, start=start_a, end=end_a, fill=INK, width=int(2.4 * k))
        else:
            eh_eff = eh * (0.52 if is_squint else 1.0)
            dr.ellipse([ex - ew - 1.2 * k, ey - eh_eff - 1.2 * k, ex + ew + 1.2 * k, ey + eh_eff + 1.2 * k], fill=INK)
            dr.ellipse([ex - ew, ey - eh_eff, ex + ew, ey + eh_eff], fill=WHITE_MINT)

            px_p = ex + look[0] * ew * 0.36
            py_p = ey + look[1] * eh_eff * 0.32
            pw_p, ph_p = ew * 0.58, eh_eff * 0.64
            dr.ellipse([px_p - pw_p, py_p - ph_p, px_p + pw_p, py_p + ph_p], fill=INK)
            pie = [
                (px_p + 0.05 * pw_p, py_p - 0.05 * ph_p),
                (px_p + 1.15 * pw_p, py_p - 0.72 * ph_p),
                (px_p + 1.15 * pw_p, py_p - 0.12 * ph_p),
            ]
            dr.polygon(pie, fill=WHITE_MINT)
            dr.ellipse([px_p - 0.52 * pw_p, py_p - 0.58 * ph_p, px_p - 0.16 * pw_p, py_p - 0.22 * ph_p], fill=WHITE_MINT)

        by_off = -eh - (3.8 if expr != "ooh" else 5.8) * k
        b_tilt = (-8 * eside) if expr == "detective" else (6 * eside if expr == "happy" else 0)
        bx0, by0 = _rot(ex - ew * 0.85, ey + by_off, ex, ey, b_tilt)
        bx1, by1 = _rot(ex, ey + by_off - 2.5 * k, ex, ey, b_tilt)
        bx2, by2 = _rot(ex + ew * 0.85, ey + by_off + 0.5 * k, ex, ey, b_tilt)
        dr.line(_bezier((bx0, by0), (bx1, by1), (bx1, by1), (bx2, by2), 10), fill=INK, width=int(2.1 * k))

    nr = 2.3 * k
    nx, ny = _rot(ox + f_shift * 0.85, oy + 0.05 * ry, ox, oy, tilt_clamped)
    dr.ellipse([nx - nr, ny - nr, nx + nr, ny + nr], fill=INK)
    dr.ellipse([nx - nr * 0.45, ny - nr * 0.55, nx + nr * 0.25, ny + nr * 0.15], fill=MINT)

    mx, my = _rot(ox + f_shift * 0.9, oy + 0.30 * ry, ox, oy, tilt_clamped)
    mw = 0.40 * rx
    if mouth == "ooh":
        dr.ellipse([mx - 0.14 * rx, my - 0.11 * ry, mx + 0.14 * rx, my + 0.17 * ry], fill=INK)
        dr.ellipse([mx - 0.08 * rx, my + 0.04 * ry, mx + 0.08 * rx, my + 0.14 * ry], fill=EMERALD_FACE)
    elif mouth == "open":
        m_pts = [
            (mx - mw, my - 0.04 * ry),
            (mx, my + 0.02 * ry),
            (mx + mw, my - 0.04 * ry),
            (mx + mw * 0.78, my + 0.25 * ry),
            (mx, my + 0.34 * ry),
            (mx - mw * 0.78, my + 0.25 * ry),
        ]
        dr.polygon(m_pts, fill=INK)
        t_pts = [
            (mx - mw * 0.82, my - 0.02 * ry),
            (mx + mw * 0.82, my - 0.02 * ry),
            (mx + mw * 0.72, my + 0.08 * ry),
            (mx - mw * 0.72, my + 0.08 * ry),
        ]
        dr.polygon(t_pts, fill=WHITE_MINT)
        dr.ellipse([mx - mw * 0.42, my + 0.14 * ry, mx + mw * 0.42, my + 0.31 * ry], fill=(56, 232, 146, 255))
        dr.polygon(m_pts, outline=INK, width=int(2.0 * k))
    else:
        s_pts = _bezier(
            (mx - mw, my - 0.04 * ry),
            (mx - mw * 0.45, my + 0.26 * ry),
            (mx + mw * 0.45, my + 0.26 * ry),
            (mx + mw, my - 0.04 * ry),
            16,
        )
        dr.line(s_pts, fill=INK, width=int(2.5 * k), joint="curve")

    if mouth != "ooh":
        for dside in (-1.0, 1.0):
            dx_c = mx + dside * (mw + 1.8 * k)
            dy_c = my - 0.05 * ry
            dr.arc(
                [dx_c - 2.6 * k, dy_c - 2.6 * k, dx_c + 2.6 * k, dy_c + 2.6 * k],
                start=120 if dside < 0 else 300,
                end=240 if dside < 0 else 420,
                fill=INK,
                width=int(1.7 * k),
            )

    # 5. Front Arm & Interactive TVA Props
    front_wx, front_wy = ox, oy
    for side, hspec in arm_specs:
        if side != back_side:
            front_wx, front_wy = _render_arm(side, hspec)

    if prop == "tempad":
        tx_p, ty_p = front_wx + (7 * k if facing >= 0 else -17 * k), front_wy - 3 * k
        cone = [(tx_p + 5 * k, ty_p + 6 * k), (tx_p - 17 * k, ty_p + 38 * k), (tx_p + 27 * k, ty_p + 38 * k)]
        dr.polygon(cone, fill=(0, 255, 136, 56))
        gdr.polygon(cone, fill=(0, 255, 136, 95))
        # Animated laser scan line inside cone
        sf = (scan_phase * 1.9) % 1.0
        ly_s = _lerp(ty_p + 8 * k, ty_p + 36 * k, sf)
        hw_s = _lerp(3 * k, 20 * k, sf)
        dr.line([(tx_p + 5 * k - hw_s * 0.8, ly_s), (tx_p + 5 * k + hw_s * 1.0, ly_s)], fill=WHITE_MINT, width=int(1.5 * k))
        dr.rounded_rectangle([tx_p, ty_p, tx_p + 11 * k, ty_p + 7.5 * k], radius=int(1.6 * k), fill=INK, outline=EMERALD, width=int(1.5 * k))
        dr.rectangle([tx_p + 2 * k, ty_p + 2 * k, tx_p + 9 * k, ty_p + 5.5 * k], fill=MINT)
    elif prop == "magnifier":
        dir_m = 1.0 if facing >= 0 else -1.0
        lx_m = front_wx + dir_m * 9.5 * k
        ly_m = front_wy - 9.5 * k
        lr_m = 10.5 * k
        dr.line([(front_wx, front_wy), (lx_m - dir_m * lr_m * 0.65, ly_m + lr_m * 0.65)], fill=MINT, width=int(2.6 * k))
        gdr.ellipse([lx_m - lr_m, ly_m - lr_m, lx_m + lr_m, ly_m + lr_m], outline=(0, 255, 136, 220), width=int(3.0 * k))
        dr.ellipse([lx_m - lr_m, ly_m - lr_m, lx_m + lr_m, ly_m + lr_m], fill=(0, 255, 136, 48), outline=WHITE_MINT, width=int(2.0 * k))
        dr.arc([lx_m - lr_m * 0.72, ly_m - lr_m * 0.72, lx_m + lr_m * 0.72, ly_m + lr_m * 0.72], 200, 265, fill=WHITE_MINT, width=int(1.5 * k))

    # Optional rigid full-sprite 360 cartwheel rotation (keeps eyes/mouth/limbs 100% locked together!)
    if abs(spin_deg) > 0.5:
        spr = spr.rotate(-spin_deg, resample=Image.Resampling.BICUBIC)
        sglow = sglow.rotate(-spin_deg, resample=Image.Resampling.BICUBIC)

    # 6. Holographic CRT Scanline & Materialization Alpha Modulation
    px_s = spr.load()
    band_y = int(((scan_phase * 1.7) % 1.0) * ph)
    for yy in range(ph):
        scan_mul = 0.89 if (yy // max(1, S)) % 2 == 0 else 1.0
        boost = 26 if abs(yy - band_y) < 4 * S else 0
        for xx in range(pw):
            r, g, b, a = px_s[xx, yy]
            if a > 0:
                ng = min(255, int(g * scan_mul) + boost)
                nr = min(ng, int(r * scan_mul) + boost // 2)
                nb = min(ng, int(b * scan_mul) + int(boost * 0.7))
                px_s[xx, yy] = (nr, ng, nb, int(a * holo_alpha))

    if holo_alpha < 0.99:
        gpx = sglow.load()
        for yy in range(ph):
            for xx in range(pw):
                r, g, b, a = gpx[xx, yy]
                if a > 0:
                    gpx[xx, yy] = (r, g, b, int(a * holo_alpha))

    dest_x, dest_y = int(cx - ox), int(cy - oy)
    glow.alpha_composite(sglow, (dest_x, dest_y))
    canvas.alpha_composite(spr, (dest_x, dest_y))


def draw_speech_hud(
    dr: ImageDraw.ImageDraw,
    gdr: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    S: int,
    tag: str,
    msg: str,
    progress: float = 1.0,
    verified_badge: bool = False,
):
    """Draw a dedicated non-overlapping upper holographic TVA speech & telemetry bar (100% ASCII-safe glyphs)."""
    box = [x * S, y * S, (x + w) * S, (y + h) * S]
    gdr.rounded_rectangle(box, radius=6 * S, outline=(0, 255, 136, 105), width=int(2.0 * S))
    dr.rounded_rectangle(box, radius=6 * S, fill=(5, 18, 11, 232), outline=EMERALD, width=int(1.2 * S))
    dr.rectangle([x * S, (y + 4) * S, (x + 3) * S, (y + h - 4) * S], fill=EMERALD)

    f_tag = _load_font("JetBrainsMono.ttf", int(7.8 * S))
    dr.text(((x + 10) * S, (y + 4) * S), tag, font=f_tag, fill=MINT)

    # Auto-fit message font size so text NEVER overflows box width
    max_tw = (w - (36 if verified_badge else 18)) * S
    fs = int(12.6 * S)
    f_msg = _load_font("Rajdhani-Bold.ttf", fs)
    while dr.textlength(msg, font=f_msg) > max_tw and fs > int(9.0 * S):
        fs -= 1
        f_msg = _load_font("Rajdhani-Bold.ttf", fs)

    n_chars = max(1, int(len(msg) * min(1.0, progress)))
    shown = msg[:n_chars]
    tx0, ty0 = (x + 10) * S, (y + 15) * S
    dr.text((tx0, ty0), shown, font=f_msg, fill=WHITE_MINT)

    # Crisp vector terminal block cursor (replaces missing Unicode '▌')
    if progress < 0.98:
        cur_x = tx0 + dr.textlength(shown, font=f_msg) + 2 * S
        dr.rectangle([cur_x, ty0 + 2 * S, cur_x + 4 * S, ty0 + fs - 1 * S], fill=EMERALD)

    # Crisp vector checkmark badge (replaces missing Unicode '✓')
    if verified_badge:
        vx, vy = (x + w - 16) * S, (y + h // 2) * S
        dr.ellipse([vx - 6 * S, vy - 6 * S, vx + 6 * S, vy + 6 * S], fill=(10, 68, 38), outline=EMERALD, width=S)
        dr.line([(vx - 3 * S, vy), (vx - 0.8 * S, vy + 2.5 * S), (vx + 3.5 * S, vy - 2.5 * S)], fill=WHITE_MINT, width=int(1.6 * S))


def _walk_kinematics(cycle: float, facing: float) -> tuple[float, tuple, tuple, tuple, tuple]:
    ph = cycle * 2 * math.pi
    dir_s = 1.0 if facing >= 0 else -1.0
    bob = -abs(math.sin(ph)) * 3.2
    s1 = math.sin(ph)
    s2 = math.sin(ph + math.pi)
    lf = (-0.12 + 0.45 * s1 * dir_s, 1.56 - max(0.0, math.cos(ph)) * 0.22, -13 * s1 * dir_s, 1.0 if s1 < -0.7 else 0.0)
    rf = (0.12 + 0.45 * s2 * dir_s, 1.56 - max(0.0, math.cos(ph + math.pi)) * 0.22, -13 * s2 * dir_s, 1.0 if s2 < -0.7 else 0.0)
    lh = (-1.14 - 0.34 * s1 * dir_s, 0.30 + 0.16 * abs(s1), "open")
    rh = (1.14 - 0.34 * s2 * dir_s, 0.30 + 0.16 * abs(s2), "open")
    return bob, lh, rh, lf, rf


def _finalize_frame(plate: Image.Image, overlay: Image.Image, glow: Image.Image, w: int, h: int, S: int) -> Image.Image:
    """Apply dual-radius optical Gaussian bloom, clamp negligible alpha for optimal LZW delta compression, and downsample."""
    b_wide = glow.filter(ImageFilter.GaussianBlur(radius=5.0 * S))
    b_tight = glow.filter(ImageFilter.GaussianBlur(radius=1.7 * S))
    # Threshold ultra-faint alpha (< 4) to 0 so static background regions remain bit-identical across frames
    a_ch = b_wide.getchannel("A").point(lambda a: 0 if a < 4 else a)
    b_wide.putalpha(a_ch)

    frame = plate.convert("RGBA")
    frame.alpha_composite(b_wide)
    frame.alpha_composite(b_tight)
    frame.alpha_composite(overlay)
    rgb = frame.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
    return quantize_emerald(rgb)


# ─────────────── SCENE 1: TIMEDOOR ARRIVAL, WAVE & BIOMETRIC SCAN ───────────────
def build_scene_welcome(mobile: bool = False) -> str:
    w, h = (420, 152) if mobile else (840, 140)
    S = 2
    n_frames = 84
    floor_y = h - 14
    plate = make_hud_plate(
        w, h, S,
        "TVA // AI INTELLIGENCE - MISS MINUTES" if mobile else "TVA // AUTONOMOUS INTELLIGENCE - MISS MINUTES v6.16",
        "UNIT: LIVE" if mobile else "TIMELINE: 616 // ACTIVE",
        floor_y,
    )

    x_left = 50 if mobile else 74
    x_mid = 195 if mobile else 400
    x_right = w - (50 if mobile else 74)
    R = (18.5 if mobile else 20.5) * S
    base_cy = (floor_y - (31 if mobile else 34)) * S

    frames: list[Image.Image] = []
    for fi in range(n_frames):
        u = fi / n_frames
        ov = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        gl = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov, "RGBA")
        gdr = ImageDraw.Draw(gl, "RGBA")
        draw_laser_bezel(dr, gdr, w, h, S, u)

        td_left = math.sin(min(1.0, u / 0.22) * math.pi) if u < 0.22 else 0.0
        td_right = math.sin(((u - 0.78) / 0.22) * math.pi) if u > 0.78 else 0.0
        draw_timedoor(ov, gl, x_left * S, (floor_y - 31) * S, S, td_left, skew=1.0, phase=u)
        draw_timedoor(ov, gl, x_right * S, (floor_y - 31) * S, S, td_right, skew=-1.0, phase=u)

        prop = None
        sx_m, sy_m, tilt = 1.0, 1.0, 0.0
        holo_a = 1.0
        v_badge = False
        if u < 0.16:
            t = _smoothstep(u / 0.16)
            cx = _lerp(x_left, x_left + (36 if mobile else 72), t) * S
            arc = math.sin(t * math.pi) * 12 * S
            cy = base_cy - arc
            holo_a = min(1.0, t * 1.6)
            sx_m, sy_m = (0.92, 1.08) if t < 0.7 else (1.09, 0.91)
            facing = 0.55
            expr, mouth = "happy", "open"
            lh, rh = (-1.15, -0.35, "open"), (1.35, -0.55, "wave")
            lf, rf = (-0.42, 1.42, -16, 0.0), (0.48, 1.48, 14, 1.0 if t > 0.85 else 0.0)
            msg_tag = "TIMEDOOR // ARRIVAL"
            msg_txt = "HEY Y'ALL! MISS MINUTES ONLINE!" if mobile else "HEY Y'ALL! WELCOME TO SRISHANTH'S AI MULTIVERSE!"
            msg_p = t
        elif u < 0.42:
            t = (u - 0.16) / 0.26
            cx = (x_left + (36 if mobile else 72)) * S
            cy = base_cy + math.sin(t * 4 * math.pi) * 1.6 * S
            facing = 0.18
            expr = "wink" if 0.35 < t < 0.72 else "happy"
            mouth = "open" if int(t * 9) % 2 == 0 else "smile"
            wave_osc = math.sin(t * 6 * math.pi) * 0.30
            lh = (-1.16, 0.36, "open")
            rh = (1.40 + wave_osc * 0.38, -0.74 + abs(wave_osc) * 0.15, "wave")
            lf, rf = (-0.36, 1.58, 0.0, 0.0), (0.36, 1.58, 0.0, 0.0)
            tilt = wave_osc * 7
            msg_tag = "TVA // COMPANION BRIEFING"
            msg_txt = "9 SACRED AI REPOS LIVE & READY!" if mobile else "HEY Y'ALL! GUIDING YOU ACROSS 9 VERIFIED AI REPOSITORIES!"
            msg_p = min(1.0, 0.35 + t * 1.1)
        elif u < 0.60:
            t = _smoothstep((u - 0.42) / 0.18)
            cx = _lerp(x_left + (36 if mobile else 72), x_mid, t) * S
            bob, lh, rh, lf, rf = _walk_kinematics(t * 2.0, 0.7)
            cy = base_cy + bob * S
            facing, tilt = 0.72, 6.0
            expr = "blink" if 0.44 < t < 0.58 else "happy"
            mouth = "smile"
            msg_tag = "SCAN // PERSONNEL DOSSIER"
            msg_txt = "SCANNING ENGINEER CLEARANCE..." if mobile else "VERIFYING ENGINEER: SRISHANTH TADAKALA // AI & ML..."
            msg_p = t
        elif u < 0.80:
            t = (u - 0.60) / 0.20
            cx = x_mid * S
            cy = base_cy + math.sin(t * 2 * math.pi) * 1.3 * S
            facing = 0.45
            expr = "proud" if t > 0.55 else "happy"
            mouth = "open" if t > 0.55 else "smile"
            lh = (-1.12, 0.28, "open")
            rh = (1.26, 0.04, "point")
            lf, rf = (-0.35, 1.58, 0.0, 0.0), (0.38, 1.58, 0.0, 0.0)
            prop = "tempad"
            v_badge = t > 0.35
            msg_tag = "CLEARANCE // LEVEL 616 [VERIFIED]"
            msg_txt = "VERIFIED! DIVING TO DOSSIER >>" if mobile else "TIMELINE VERIFIED! HOPPING THROUGH TIMEDOOR TO DOSSIER >>"
            msg_p = min(1.0, t * 1.5)
        else:
            t = _smoothstep((u - 0.80) / 0.20)
            cx = _lerp(x_mid, x_right, t) * S
            arc = math.sin(max(0.0, (t - 0.35) / 0.65) * math.pi) * 13 * S if t > 0.35 else 0.0
            bob, lh, rh, lf, rf = _walk_kinematics(t * 2.2, 0.85)
            cy = base_cy + (bob * S if t <= 0.35 else -arc)
            if t > 0.45:
                lh, rh = (-1.32, -0.42, "open"), (1.42, -0.60, "point")
                tilt = 15.0
            else:
                tilt = 8.0
            facing = 0.85
            holo_a = max(0.0, 1.0 - max(0.0, (t - 0.72) / 0.28))
            expr, mouth = "happy", "open"
            v_badge = True
            msg_tag = "TIMEDOOR // NEXT: 01 DOSSIER"
            msg_txt = "SEE YA IN THE DOSSIER BELOW!" if mobile else "TIMEDOOR LOCKED >> MEET ME AT PROJECT MULTIVERSE BELOW!"
            msg_p = 1.0

        # Dedicated upper telemetry speech band (y=28..59) — never overlaps Miss Minutes (top >= 71px)!
        sh_x = 18 if mobile else 208
        sh_w = (w - 36) if mobile else 424
        draw_speech_hud(dr, gdr, sh_x, 28, sh_w, 31, S, msg_tag, msg_txt, msg_p, verified_badge=v_badge)

        draw_miss_minutes(
            ov, gl, cx, cy, R, S,
            facing=facing, tilt=tilt, sx=sx_m, sy=sy_m,
            expr=expr, mouth=mouth,
            hour_deg=-55 + u * 360, min_deg=65 + u * 720,
            look=(0.25 * facing, 0.05),
            l_hand=lh, r_hand=rh, l_foot=lf, r_foot=rf,
            holo_alpha=holo_a, scan_phase=u * 3, prop=prop,
        )
        frames.append(_finalize_frame(plate, ov, gl, w, h, S))

    os.makedirs(OUT_DIR, exist_ok=True)
    fn = "miss-minutes-welcome-mobile.gif" if mobile else "miss-minutes-welcome.gif"
    out_p = os.path.join(OUT_DIR, fn)
    frames[0].save(out_p, save_all=True, append_images=frames[1:], duration=50, loop=0, transparency=255, optimize=True)
    return out_p


# ─────────────── SCENE 2: SACRED TIMELINE & REPOSITORY DETECTIVE (RIGHT -> LEFT) ───────────────
def build_scene_inspector(mobile: bool = False) -> str:
    w, h = (420, 152) if mobile else (840, 140)
    S = 2
    n_frames = 88
    floor_y = h - 14
    plate = make_hud_plate(
        w, h, S,
        "TVA // MULTIVERSE BRANCH SCANNER" if mobile else "TVA // SACRED TIMELINE & REPOSITORY INSPECTOR",
        "NEXUS: 0 BUGS" if mobile else "AUDITING 6 FLAGSHIP TIMELINES",
        floor_y,
    )

    pdr = ImageDraw.Draw(plate)
    f_node = _load_font("JetBrainsMono.ttf", int(7.4 * S))
    nodes = (
        [(88, "F.R.I.D.A.Y.", False), (210, "SYLVIE", True), (332, "A.E.R.I.S.", False)]
        if mobile
        else [(130, "F.R.I.D.A.Y.", False), (280, "AI SALES", False), (430, "SYLVIE", True), (580, "A.E.R.I.S.", False), (715, "OMNIACTION", False)]
    )
    tl_y = (100 if mobile else 94) * S
    pts_tl = [(x_px, tl_y + math.sin(x_px / (48.0 * S)) * 4.5 * S) for x_px in range(26 * S, (w - 26) * S, 6 * S)]
    pdr.line(pts_tl, fill=(24, 96, 56), width=int(2.0 * S))
    for nx_n, nlab, is_nexus in nodes:
        ny_n = tl_y + math.sin((nx_n * S) / (48.0 * S)) * 4.5 * S
        pdr.ellipse([nx_n * S - 4 * S, ny_n - 4 * S, nx_n * S + 4 * S, ny_n + 4 * S], fill=EMERALD_DARK, outline=EMERALD, width=S)
        lw = pdr.textlength(nlab, font=f_node)
        tx_n = nx_n * S - lw / 2 - (4 * S if is_nexus else 0)
        pdr.text((tx_n, ny_n + 6 * S), nlab, font=f_node, fill=MINT if is_nexus else MOSS_BRIGHT)
        if is_nexus:
            # Crisp vector 5-point star next to SYLVIE (zero missing font glyph!)
            pdr.polygon(_star_pts(tx_n + lw + 6 * S, ny_n + 10.5 * S, 3.8 * S, 1.6 * S), fill=EMERALD)

    x_start = w - (52 if mobile else 78)
    x_sylvie = 210 if mobile else 430
    x_end = 50 if mobile else 74
    R = (18.5 if mobile else 20.5) * S
    base_cy = (floor_y - (31 if mobile else 34)) * S

    frames: list[Image.Image] = []
    for fi in range(n_frames):
        u = fi / n_frames
        ov = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        gl = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov, "RGBA")
        gdr = ImageDraw.Draw(gl, "RGBA")
        draw_laser_bezel(dr, gdr, w, h, S, (u + 0.35) % 1.0)

        sy_y = tl_y + math.sin((x_sylvie * S) / (48.0 * S)) * 4.5 * S
        gdr.ellipse([x_sylvie * S - 8 * S, sy_y - 8 * S, x_sylvie * S + 8 * S, sy_y + 8 * S], fill=(0, 255, 136, 170))
        dr.ellipse([x_sylvie * S - 4 * S, sy_y - 4 * S, x_sylvie * S + 4 * S, sy_y + 4 * S], fill=WHITE_MINT)

        # Ceiling Timedoor at top-right (to the right of centered speech bar!) & Exit Timedoor at left
        if u < 0.20:
            op = math.sin((u / 0.20) * math.pi)
            pw_c = int(24 * op * S)
            cy_ceil = (62 if mobile else 36) * S
            gdr.rounded_rectangle([(x_start * S - pw_c), cy_ceil - 3 * S, (x_start * S + pw_c), cy_ceil + 3 * S], radius=3 * S, fill=(0, 255, 136, 220))
            dr.rounded_rectangle([(x_start * S - pw_c), cy_ceil - 2 * S, (x_start * S + pw_c), cy_ceil + 2 * S], radius=2 * S, fill=WHITE_MINT)
        td_left = math.sin(((u - 0.80) / 0.20) * math.pi) if u > 0.80 else 0.0
        draw_timedoor(ov, gl, x_end * S, (floor_y - 31) * S, S, td_left, skew=1.0, phase=u)

        prop = "magnifier"
        sx_m, sy_m, tilt, holo_a = 1.0, 1.0, -5.0, 1.0
        v_badge = False
        if u < 0.16:
            t = _smoothstep(u / 0.16)
            cx = x_start * S
            cy = _lerp((68 if mobile else 50) * S, base_cy, t)
            sx_m, sy_m = (0.88, 1.13) if t < 0.78 else (1.13, 0.87)
            holo_a = min(1.0, t * 1.7)
            facing = -0.65
            expr, mouth = "happy", "open"
            lh, rh = (-1.35, -0.52, "open"), (1.25, -0.45, "open")
            lf, rf = (-0.42, 1.50, 10, 1.0 if t > 0.82 else 0.0), (0.42, 1.50, -10, 1.0 if t > 0.82 else 0.0)
            prop = None
            tag, txt, mp = "DETECTIVE // DROP-IN", ("INSPECTING REPO TIMELINES..." if mobile else "DROPPING IN TO INSPECT ALL 6 PROJECT TIMELINES!"), t
        elif u < 0.44:
            t = _smoothstep((u - 0.16) / 0.28)
            cx = _lerp(x_start, x_sylvie + 28, t) * S
            bob, _, rh, lf, rf = _walk_kinematics(t * 2.4, -0.75)
            cy = base_cy + bob * S
            facing, tilt = -0.75, -7.0
            lh = (-1.30, -0.15, "point")
            expr, mouth = "detective", "smile"
            tag = "MAGNIFIER // DEEP CODE AUDIT"
            txt = "397+16 & 115 TESTS PASSING!" if mobile else "AUDITING TESTS: 397+16 (F.R.I.D.A.Y.) & 115 (QUEUELESS) PASSING!"
            mp = min(1.0, 0.2 + t * 1.2)
        elif u < 0.72:
            t = (u - 0.44) / 0.28
            cx = (x_sylvie + 26) * S
            cy = base_cy - abs(math.sin(t * 2 * math.pi)) * 4.5 * S
            facing, tilt = -0.45, -3.0
            expr = "ooh" if t < 0.48 else "happy"
            mouth = "ooh" if t < 0.45 else "open"
            lh = (-1.35, -0.20, "point")
            rh = (1.32, -0.62, "wave")
            lf, rf = (-0.36, 1.58, 0, 0), (0.36, 1.58, 0, 0)
            v_badge = t > 0.45
            # Orbiting discovery star-sparks around SYLVIE node
            for si in range(4):
                sa = math.radians(si * 90 + t * 360)
                sx_p = x_sylvie * S + math.cos(sa) * 14 * S
                sy_p = sy_y + math.sin(sa) * 10 * S
                dr.polygon(_star_pts(sx_p, sy_p, 3.2 * S, 1.3 * S), fill=WHITE_MINT)
            tag = "NEXUS DISCOVERY // SYLVIE"
            txt = "OOH! SYLVIE AI MEMORY NEXUS!" if mobile else "OOH! SYLVIE LOCAL AI COMPANION — CONTEXTUAL MEMORY NEXUS!"
            mp = min(1.0, t * 1.6)
        else:
            t = _smoothstep((u - 0.72) / 0.28)
            cx = _lerp(x_sylvie + 26, x_end, t) * S
            bob, lh, rh, lf, rf = _walk_kinematics(t * 2.5, -0.85)
            arc = math.sin(max(0.0, (t - 0.5) / 0.5) * math.pi) * 12 * S if t > 0.5 else 0.0
            cy = base_cy + bob * S - arc
            facing, tilt = -0.85, -10.0
            holo_a = max(0.0, 1.0 - max(0.0, (t - 0.75) / 0.25))
            expr, mouth = "wink" if t < 0.45 else "happy", "smile"
            prop = None
            v_badge = True
            tag = "TIMEDOOR // NEXT: COMMAND"
            txt = "ALL REPOS SACRED >> COMMAND!" if mobile else "ALL 6 TIMELINES STABLE >> HEADING TO COMMAND CENTER!"
            mp = 1.0

        sh_x = 18 if mobile else 196
        sh_w = (w - 36) if mobile else 448
        draw_speech_hud(dr, gdr, sh_x, 28, sh_w, 31, S, tag, txt, mp, verified_badge=v_badge)

        draw_miss_minutes(
            ov, gl, cx, cy, R, S,
            facing=facing, tilt=tilt, sx=sx_m, sy=sy_m,
            expr=expr, mouth=mouth,
            hour_deg=15 - u * 360, min_deg=180 - u * 720,
            look=(-0.28, 0.06),
            l_hand=lh, r_hand=rh, l_foot=lf, r_foot=rf,
            holo_alpha=holo_a, scan_phase=u * 3.2, prop=prop,
        )
        frames.append(_finalize_frame(plate, ov, gl, w, h, S))

    fn = "miss-minutes-inspector-mobile.gif" if mobile else "miss-minutes-inspector.gif"
    out_p = os.path.join(OUT_DIR, fn)
    frames[0].save(out_p, save_all=True, append_images=frames[1:], duration=50, loop=0, transparency=255, optimize=True)
    return out_p


# ─────────────── SCENE 3: COMMAND CENTER HOLO-CONSOLE OPERATOR ───────────────
def build_scene_operator(mobile: bool = False) -> str:
    w, h = (420, 152) if mobile else (840, 140)
    S = 2
    n_frames = 84
    floor_y = h - 14
    plate = make_hud_plate(
        w, h, S,
        "TVA // TEMPORAL LOOM TELEMETRY DESK" if mobile else "TVA // TEMPORAL LOOM & LIVE TELEMETRY OPERATOR",
        "LOOM: 100%" if mobile else "PYTHON 63.5% // 400+ CONTRIB",
        floor_y,
    )

    # Place 2 holographic consoles at outer flanks so Miss Minutes stands BESIDE them without blocking labels!
    pdr = ImageDraw.Draw(plate)
    f_sm = _load_font("JetBrainsMono.ttf", int(7.2 * S))
    term_x = 58 if mobile else 112
    loom_x = w - (58 if mobile else 112)
    op_left = term_x + (56 if mobile else 72)
    op_right = loom_x - (56 if mobile else 72)

    for is_loom, (wx_c, wlab) in enumerate(((term_x, "CODE" if mobile else "HOLO-TERM"), (loom_x, "LOOM" if mobile else "LOOM CORE"))):
        hw_b = 34 if mobile else 46
        bx0, by0 = (wx_c - hw_b) * S, (floor_y - 40) * S
        bx1, by1 = (wx_c + hw_b) * S, (floor_y - 8) * S
        pdr.rounded_rectangle([bx0, by0, bx1, by1], radius=5 * S, fill=(7, 26, 16), outline=MOSS, width=S)
        lw = pdr.textlength(wlab, font=f_sm)
        pdr.text((wx_c * S - lw / 2, by0 + 3 * S), wlab, font=f_sm, fill=MINT)
        if not is_loom:
            pdr.line([((wx_c - hw_b + 8) * S, by0 + 18 * S), ((wx_c + hw_b - 12) * S, by0 + 18 * S)], fill=EMERALD, width=int(1.5 * S))
            pdr.line([((wx_c - hw_b + 8) * S, by0 + 24 * S), ((wx_c + 6) * S, by0 + 24 * S)], fill=MOSS_BRIGHT, width=int(1.5 * S))

    R = (18.5 if mobile else 20.5) * S
    base_cy = (floor_y - (31 if mobile else 34)) * S

    frames: list[Image.Image] = []
    rnd = random.Random(616)
    glyph_seeds = [(rnd.uniform(-18, 18), rnd.uniform(0, 1), rnd.choice(["01", "AI", "PY", "TS", "OK"])) for _ in range(9)]
    f_gl = _load_font("JetBrainsMono.ttf", int(8.0 * S))

    for fi in range(n_frames):
        u = fi / n_frames
        ov = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        gl = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov, "RGBA")
        gdr = ImageDraw.Draw(gl, "RGBA")
        draw_laser_bezel(dr, gdr, w, h, S, (u + 0.62) % 1.0)

        # Spinning Temporal Loom holographic gear centered cleanly in lower bay of Right Console
        gear_cx, gear_cy = loom_x * S, (floor_y - 19) * S
        gear_spd = 720 if 0.56 < u < 0.86 else 180
        gr = 7.2 * S
        dr.ellipse([gear_cx - gr, gear_cy - gr, gear_cx + gr, gear_cy + gr], outline=EMERALD, width=int(1.5 * S))
        for gi in range(6):
            ga = math.radians(gi * 60 + u * gear_spd)
            dr.line([(gear_cx, gear_cy), (gear_cx + math.cos(ga) * gr, gear_cy + math.sin(ga) * gr)], fill=MINT, width=S)

        # Center Temporal Loom live ECG / commit waveform
        if not mobile:
            wf_pts = []
            surge = 2.0 if 0.56 < u < 0.86 else 1.0
            for xx in range(280 * S, 560 * S, 4 * S):
                amp = math.sin((xx / (14.0 * S)) - u * 12 * math.pi) * 6.5 * S * surge
                wf_pts.append((xx, (floor_y - 22) * S + amp))
            gdr.line(wf_pts, fill=(0, 255, 136, 175), width=int(2.6 * S))
            dr.line(wf_pts, fill=MINT, width=int(1.4 * S))

        sx_m, sy_m, tilt, holo_a = 1.0, 1.0, 0.0, 1.0
        v_badge = False
        if u < 0.15:
            t = _smoothstep(u / 0.15)
            cx = op_left * S
            cy = _lerp((floor_y + 8) * S, base_cy, t)
            holo_a = min(1.0, t * 1.5)
            facing = -0.55
            expr, mouth = "happy", "smile"
            lh, rh = (-1.2, 0.2, "open"), (1.2, 0.2, "open")
            lf, rf = (-0.36, 1.55, 0, 0), (0.36, 1.55, 0, 0)
            tag, txt, mp = "CONSOLE // BOOT", "PEEKABOO! TELEMETRY DESK LIVE!", t
        elif u < 0.46:
            # Facing Left toward HOLO-TERM, typing at super-speed on floating holo-keyboard!
            t = (u - 0.15) / 0.31
            cx = op_left * S
            cy = base_cy + math.sin(t * 10 * math.pi) * 1.4 * S
            facing = -0.65
            expr = "detective" if 0.3 < t < 0.7 else "happy"
            mouth = "open" if int(t * 10) % 2 == 0 else "smile"
            ty_osc = math.sin(t * 16 * math.pi) * 0.25
            lh = (-1.36, 0.18 + ty_osc, "open")
            rh = (-0.95, 0.28 - ty_osc, "open")
            lf, rf = (-0.36, 1.58, 0, 0), (0.36, 1.58, 0, 0)
            # Floating tilted holographic keyboard bar
            kb_x = (op_left - 28) * S
            kb_y = (floor_y - 28) * S
            gdr.line([(kb_x - 10 * S, kb_y - 3 * S), (kb_x + 8 * S, kb_y + 4 * S)], fill=(0, 255, 136, 210), width=int(3 * S))
            dr.line([(kb_x - 10 * S, kb_y - 3 * S), (kb_x + 8 * S, kb_y + 4 * S)], fill=WHITE_MINT, width=int(1.6 * S))
            for gx_off, g_ph, g_ch in glyph_seeds:
                gy_t = (t * 2.2 + g_ph) % 1.0
                gx_p = (term_x + gx_off) * S
                gy_p = (floor_y - 42 - gy_t * 28) * S
                al = int(235 * (1.0 - gy_t))
                dr.text((gx_p, gy_p), g_ch, font=f_gl, fill=(136, 255, 200, al))
            tag = "TYPING // AUTO-SYNC ENGINE"
            txt = "CRUNCHING 400+ COMMITS @ 60FPS!" if mobile else "COMPILING LIVE TELEMETRY: PYTHON 63.5% // TYPESCRIPT 15.0%!"
            mp = min(1.0, 0.25 + t * 1.2)
        elif u < 0.62:
            # Jet-glides across center waveform to Right Loom Core!
            t = _smoothstep((u - 0.46) / 0.16)
            cx = _lerp(op_left, op_right, t) * S
            cy = base_cy - math.sin(t * math.pi) * 9 * S
            facing, tilt = 0.85, 10.0
            expr, mouth = "happy", "open"
            lh, rh = (-1.42, 0.10, "open"), (1.40, -0.35, "point")
            lf, rf = (-0.50, 1.48, -18, 0), (0.45, 1.52, 12, 0)
            tag = "LOOM // BOOSTING REACTOR"
            txt = "GLIDING TO TEMPORAL LOOM!" if mobile else "GLIDING TO TEMPORAL LOOM CORE — BOOSTING STREAK CADENCE!"
            mp = t
        elif u < 0.86:
            # Facing Right toward LOOM CORE, cranking power output to 100%!
            t = (u - 0.62) / 0.24
            cx = op_right * S
            cy = base_cy
            facing = 0.65
            expr = "proud" if t > 0.45 else "wink"
            mouth = "open"
            lh = (-1.15, -0.45, "wave")
            rh = (1.38, -0.15 + math.sin(t * 6 * math.pi) * 0.22, "point")
            lf, rf = (-0.38, 1.58, 0, 0), (0.38, 1.58, 0, 0)
            pr = int((12 + t * 24) * S)
            gdr.ellipse([gear_cx - pr, gear_cy - pr, gear_cx + pr, gear_cy + pr],
                        outline=(0, 255, 136, int(215 * (1.0 - t * 0.5))), width=int(2.6 * S))
            v_badge = True
            tag = "TEMPORAL OUTPUT // 100%"
            txt = "ALL SYSTEMS PURRIN' Y'ALL!" if mobile else "TEMPORAL LOOM AT 100% — 15D PEAK STREAK // 42 MAX DAILY COMMITS!"
            mp = 1.0
        else:
            t = _smoothstep((u - 0.86) / 0.14)
            cx = op_right * S
            cy = _lerp(base_cy, (floor_y + 10) * S, t)
            holo_a = 1.0 - t
            pw_f = int(26 * math.sin(t * math.pi) * S)
            gdr.ellipse([cx - pw_f, floor_y * S - 4 * S, cx + pw_f, floor_y * S + 4 * S], fill=(0, 255, 136, 230))
            dr.ellipse([cx - pw_f, floor_y * S - 2 * S, cx + pw_f, floor_y * S + 2 * S], fill=WHITE_MINT)
            facing = 0.0
            expr, mouth = "wink", "smile"
            lh, rh = (-1.2, -0.5, "open"), (1.38, -0.68, "wave")
            lf, rf = (-0.3, 1.5, 0, 0), (0.3, 1.5, 0, 0)
            v_badge = True
            tag, txt, mp = "TIMEDOOR // NEXT: UPLINK", "ZIPPING DOWN TO UPLINK DECK >>", 1.0

        sh_x = 18 if mobile else 196
        sh_w = (w - 36) if mobile else 448
        draw_speech_hud(dr, gdr, sh_x, 28, sh_w, 31, S, tag, txt, mp, verified_badge=v_badge)

        draw_miss_minutes(
            ov, gl, cx, cy, R, S,
            facing=facing, tilt=tilt, sx=sx_m, sy=sy_m,
            expr=expr, mouth=mouth,
            hour_deg=-90 + u * 720, min_deg=0 + u * 1440,
            look=(0.2 * facing, 0.08),
            l_hand=lh, r_hand=rh, l_foot=lf, r_foot=rf,
            holo_alpha=holo_a, scan_phase=u * 3.5,
        )
        frames.append(_finalize_frame(plate, ov, gl, w, h, S))

    fn = "miss-minutes-operator-mobile.gif" if mobile else "miss-minutes-operator.gif"
    out_p = os.path.join(OUT_DIR, fn)
    frames[0].save(out_p, save_all=True, append_images=frames[1:], duration=50, loop=0, transparency=255, optimize=True)
    return out_p


# ─────────────── SCENE 4: UPLINK PORTAL CONJURER & 360 CARTWHEEL FINALE ───────────────
def build_scene_uplink(mobile: bool = False) -> str:
    w, h = (420, 152) if mobile else (840, 140)
    S = 2
    n_frames = 84
    floor_y = h - 14
    plate = make_hud_plate(
        w, h, S,
        "TVA // UPLINK DISPATCH - OPEN A TIMEDOOR" if mobile else "TVA // MULTIVERSE UPLINK DISPATCHER - FOR ALL TIME. ALWAYS.",
        "5 CHANNELS" if mobile else "5 VERIFIED CHANNELS READY",
        floor_y,
    )

    R = (18.5 if mobile else 20.5) * S
    base_cy = (floor_y - (34 if mobile else 37)) * S
    beacons = ["IN", "GH", "MAIL", "IG", "FB"]
    f_bc = _load_font("JetBrainsMono.ttf", int(7.2 * S))

    frames: list[Image.Image] = []
    for fi in range(n_frames):
        u = fi / n_frames
        ov = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        gl = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov, "RGBA")
        gdr = ImageDraw.Draw(gl, "RGBA")
        draw_laser_bezel(dr, gdr, w, h, S, (u + 0.85) % 1.0)

        # Roaming zero-gravity figure-8 hover patrol across the bridge!
        span_x = 85 if mobile else 190
        cx = (w * 0.5 + math.sin(u * 2 * math.pi) * span_x) * S
        cy = base_cy + math.sin(u * 4 * math.pi) * 4.5 * S
        vel_x = math.cos(u * 2 * math.pi)
        facing = 0.45 if vel_x >= 0 else -0.45

        holo_a = 1.0
        if u < 0.12:
            holo_a = _smoothstep(u / 0.12)
        elif u > 0.88:
            holo_a = 1.0 - _smoothstep((u - 0.88) / 0.12)

        spin_deg = 0.0
        if 0.60 <= u < 0.82:
            # Rigid 360-degree mid-air joyful cartwheel spin!
            st = _smoothstep((u - 0.60) / 0.22)
            spin_deg = st * 360.0
            tilt = 0.0
            expr, mouth = "happy", "open"
            lh, rh = (-1.42, -0.60, "wave"), (1.42, -0.60, "wave")
            lf, rf = (-0.50, 1.38, -20, 0), (0.50, 1.38, 20, 0)
        else:
            tilt = math.sin(u * 2 * math.pi) * 7.0
            expr = "wink" if 0.28 < u < 0.44 else "happy"
            mouth = "open" if int(u * 14) % 2 == 0 else "smile"
            wave = math.sin(u * 6 * math.pi) * 0.24
            lh = (-1.34, -0.25 + wave, "open")
            rh = (1.44, -0.56 - wave, "wave")
            lf = (-0.38, 1.48 + wave * 0.3, -12, 0)
            rf = (0.40, 1.44 - wave * 0.3, 14, 0)

        # 5 glowing uplink channel nodes anchored along the catwalk + conjured energy pulses!
        for bi, blab in enumerate(beacons):
            bx_t = _lerp(66 if mobile else 170, w - (66 if mobile else 170), bi / 4.0) * S
            by_t = (floor_y - 8) * S
            active_b = abs((cx - bx_t) / S) < (58 if mobile else 95)
            gdr.ellipse([bx_t - 10 * S, by_t - 6 * S, bx_t + 10 * S, by_t + 6 * S],
                        fill=(0, 255, 136, 175 if active_b else 75))
            dr.rounded_rectangle([bx_t - 12 * S, by_t - 6 * S, bx_t + 12 * S, by_t + 6 * S], radius=4 * S,
                                 fill=(6, 28, 17, 235), outline=WHITE_MINT if active_b else EMERALD, width=S)
            tw = dr.textlength(blab, font=f_bc)
            dr.text((bx_t - tw / 2, by_t - 4.5 * S), blab, font=f_bc, fill=WHITE_MINT if active_b else MINT)
            if active_b:
                # Glowing energy beam linking Miss Minutes to the active uplink channel below!
                gdr.line([(cx, cy + R * 0.8), (bx_t, by_t - 6 * S)], fill=(0, 255, 136, int(145 * holo_a)), width=int(2.4 * S))
                dr.line([(cx, cy + R * 0.8), (bx_t, by_t - 6 * S)], fill=(220, 255, 238, int(170 * holo_a)), width=S)

        tag = "DISPATCH // FOR ALL TIME. ALWAYS."
        txt = "OPEN A TIMEDOOR BELOW Y'ALL!" if mobile else "OPEN A TIMEDOOR BELOW — SRISHANTH IS READY TO BUILD WITH Y'ALL!"
        sh_x = 18 if mobile else 186
        sh_w = (w - 36) if mobile else 468
        draw_speech_hud(dr, gdr, sh_x, 28, sh_w, 31, S, tag, txt, min(1.0, u * 2.4), verified_badge=(u > 0.45))

        draw_miss_minutes(
            ov, gl, cx, cy, R, S,
            facing=facing, tilt=tilt, spin_deg=spin_deg,
            expr=expr, mouth=mouth,
            hour_deg=0 + u * 360, min_deg=0 + u * 720,
            look=(0.15 * facing, 0.0),
            l_hand=lh, r_hand=rh, l_foot=lf, r_foot=rf,
            holo_alpha=holo_a, scan_phase=u * 3.0,
        )
        frames.append(_finalize_frame(plate, ov, gl, w, h, S))

    fn = "miss-minutes-uplink-mobile.gif" if mobile else "miss-minutes-uplink.gif"
    out_p = os.path.join(OUT_DIR, fn)
    frames[0].save(out_p, save_all=True, append_images=frames[1:], duration=50, loop=0, transparency=255, optimize=True)
    return out_p


def build_all_gifs() -> list[tuple[str, int]]:
    results = []
    for builder in (build_scene_welcome, build_scene_inspector, build_scene_operator, build_scene_uplink):
        for mob in (False, True):
            p = builder(mobile=mob)
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            results.append((rel, os.path.getsize(p)))
    return results


if __name__ == "__main__":
    built = build_all_gifs()
    for rel, sz in built:
        print(f"{sz / 1024:7.1f} KB  {rel}")
    print(f"{sum(sz for _, sz in built) / 1024:7.1f} KB  TOTAL ({len(built)} GIFs)")
