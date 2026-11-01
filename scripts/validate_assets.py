"""Validate all generated SVG and source raster assets for Project Marvel.

Checks:
1. Every generated SVG in assets/{hero,nav,headers,dossier,arsenal,projects,command,archive,uplink,finale}:
   - Valid XML with <svg> root, explicit width, height, viewBox
   - Non-empty <title> element for screen-reader accessibility
   - Zero <script> tags, zero event handlers (onload/onclick), zero javascript: URIs
   - Zero external http(s):// image/font/import fetches (GitHub camo/<img> blocks them)
   - Individual SVG budget <= 250 KB; total SVG budget <= 2,048 KB
2. Every source raster image in assets/source/ (.webp, .png):
   - Valid image verified via Pillow with non-zero dimensions
3. Zero orphaned/legacy files directly in assets/ root or legacy subdirectories.
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
ACTIVE_SVG_DIRS = (
    "hero",
    "nav",
    "headers",
    "dossier",
    "arsenal",
    "projects",
    "command",
    "archive",
    "uplink",
    "finale",
)
MAX_SINGLE_SVG_KB = 250.0
MAX_TOTAL_SVG_KB = 2048.0
MISS_MINUTES_CAMEO_SVGS = {
    "assets/hero/hero.svg",
    "assets/hero/hero-mobile.svg",
    "assets/projects/sylvie.svg",
}


def _is_emerald_color(r: int, g: int, b: int) -> bool:
    return g >= r and g >= b


def _is_tva_miss_minutes_color(r: int, g: int, b: int) -> bool:
    return r >= g >= b


def validate_svgs() -> tuple[int, int, float]:
    print("=== Validating Self-Contained SVG Assets ===")
    errors = 0
    count = 0
    total_kb = 0.0

    for sub in ACTIVE_SVG_DIRS:
        folder = os.path.join(ASSETS, sub)
        if not os.path.isdir(folder):
            print(f"[FAIL] Missing asset directory: assets/{sub}")
            errors += 1
            continue
        files = sorted(f for f in os.listdir(folder) if f.endswith(".svg"))
        if not files:
            print(f"[FAIL] Empty SVG directory: assets/{sub}")
            errors += 1
        for fn in files:
            path = os.path.join(folder, fn)
            rel = f"assets/{sub}/{fn}"
            count += 1
            kb = os.path.getsize(path) / 1024.0
            total_kb += kb
            raw = open(path, encoding="utf-8").read()

            try:
                root = ET.fromstring(raw)
            except Exception as exc:
                print(f"[FAIL] {rel}: XML parse error: {exc}")
                errors += 1
                continue

            if not root.tag.endswith("svg"):
                print(f"[FAIL] {rel}: root tag is {root.tag}, expected <svg>")
                errors += 1
                continue

            w = root.attrib.get("width")
            h = root.attrib.get("height")
            vb = root.attrib.get("viewBox")
            if not (w and h and vb):
                print(f"[FAIL] {rel}: missing width/height/viewBox ({w}, {h}, {vb})")
                errors += 1

            titles = [el for el in root.iter() if el.tag.endswith("title") and (el.text or "").strip()]
            if not titles:
                print(f"[FAIL] {rel}: missing non-empty <title> accessibility tag")
                errors += 1

            lowered = raw.lower()
            for bad in ("<script", "javascript:", "onload=", "onclick=", "onerror=", "@import"):
                if bad in lowered:
                    print(f"[FAIL] {rel}: forbidden construct '{bad}' inside SVG")
                    errors += 1

            # Strip xmlns namespace declarations before checking for external http(s) fetches
            no_ns = re.sub(r'xmlns(?::\w+)?="https?://[^"]+"', "", raw)
            if re.search(r"https?://", no_ns):
                print(f"[FAIL] {rel}: external http(s) URL inside SVG (blocked by GitHub <img> sandbox)")
                errors += 1

            # Enforce Jet Black / Muted Moss / Neon Emerald color purity on HUD SVGs,
            # plus sanctioned Marvel TVA Miss Minutes Amber-Orange/Cream/Ink tokens on cameo SVGs
            no_refs = re.sub(r"url\(#[^)]+\)", "", re.sub(r"base64,[A-Za-z0-9+/=]+", "", raw))
            allow_tva = rel in MISS_MINUTES_CAMEO_SVGS
            has_tva_orange = False
            for hx in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", no_refs):
                full_hx = "".join(ch * 2 for ch in hx) if len(hx) == 3 else hx
                r_c, g_c, b_c = int(full_hx[0:2], 16), int(full_hx[2:4], 16), int(full_hx[4:6], 16)
                if r_c >= 220 and 85 <= g_c <= 190 and b_c <= 65:
                    has_tva_orange = True
                ok = _is_emerald_color(r_c, g_c, b_c) or (allow_tva and _is_tva_miss_minutes_color(r_c, g_c, b_c))
                if not ok:
                    print(f"[FAIL] {rel}: off-palette hex color #{hx} (R={r_c}, G={g_c}, B={b_c})")
                    errors += 1
            if allow_tva and not has_tva_orange:
                print(f"[FAIL] {rel}: expected authentic TVA Orange Miss Minutes cameo tokens, found none")
                errors += 1

            if kb > MAX_SINGLE_SVG_KB:
                print(f"[FAIL] {rel}: {kb:.1f} KB exceeds single-SVG budget ({MAX_SINGLE_SVG_KB} KB)")
                errors += 1
            else:
                print(f"[PASS] {rel:<36} {w:>4}x{h:<4}  {kb:6.1f} KB")

    if total_kb > MAX_TOTAL_SVG_KB:
        print(f"[FAIL] Total SVG payload {total_kb:.1f} KB exceeds {MAX_TOTAL_SVG_KB} KB budget")
        errors += 1
    else:
        print(f"\n[PASS] Total SVG payload: {total_kb:.1f} KB across {count} SVGs (budget <= {MAX_TOTAL_SVG_KB:.0f} KB)")
    return errors, count, total_kb


def validate_sources() -> int:
    print("\n=== Validating Source Artwork Assets (assets/source/) ===")
    errors = 0
    src_dir = os.path.join(ASSETS, "source")
    if not os.path.isdir(src_dir):
        print("[FAIL] Missing assets/source directory")
        return 1
    for fn in sorted(os.listdir(src_dir)):
        if not fn.lower().endswith((".webp", ".png", ".jpg", ".jpeg")):
            print(f"[FAIL] Unexpected file in assets/source: {fn}")
            errors += 1
            continue
        path = os.path.join(src_dir, fn)
        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                w, h, fmt = im.size[0], im.size[1], im.format
            kb = os.path.getsize(path) / 1024.0
            print(f"[PASS] assets/source/{fn:<22} {w:>4}x{h:<4} ({fmt}, {kb:.1f} KB)")
        except Exception as exc:
            print(f"[FAIL] assets/source/{fn}: corrupt image: {exc}")
            errors += 1
    return errors


def validate_gifs() -> int:
    print("\n=== Validating Animated Miss Minutes TVA GIF Modules (assets/tva/) ===")
    errors = 0
    tva_dir = os.path.join(ASSETS, "tva")
    if not os.path.isdir(tva_dir):
        print("[FAIL] Missing assets/tva directory")
        return 1
    files = sorted(f for f in os.listdir(tva_dir) if f.endswith(".gif"))
    if len(files) < 8:
        print(f"[FAIL] Expected 8 Miss Minutes GIFs (4 desktop + 4 mobile), found {len(files)}")
        errors += 1
    total_kb = 0.0
    for fn in files:
        path = os.path.join(tva_dir, fn)
        kb = os.path.getsize(path) / 1024.0
        total_kb += kb
        try:
            with Image.open(path) as im:
                w, h = im.size
                nf = getattr(im, "n_frames", 1)
                anim = getattr(im, "is_animated", False)
                if not anim or nf < 60:
                    print(f"[FAIL] assets/tva/{fn}: expected >=60 animated frames, got is_animated={anim}, n_frames={nf}")
                    errors += 1
                # Verify Emerald HUD + Authentic TVA Orange Miss Minutes palette governance across sampled frames
                has_tva_orange = False
                for f_idx in (0, nf // 3, (2 * nf) // 3):
                    im.seek(f_idx)
                    rgb = im.convert("RGB")
                    for _cnt, (r_c, g_c, b_c) in (rgb.getcolors(maxcolors=65536) or []):
                        if r_c >= 220 and 85 <= g_c <= 190 and b_c <= 65:
                            has_tva_orange = True
                        if not (_is_emerald_color(r_c, g_c, b_c) or _is_tva_miss_minutes_color(r_c, g_c, b_c)):
                            print(f"[FAIL] assets/tva/{fn}: off-palette pixel ({r_c},{g_c},{b_c}) at frame {f_idx}")
                            errors += 1
                            break
                if not has_tva_orange:
                    print(f"[FAIL] assets/tva/{fn}: missing authentic TVA Orange Miss Minutes pixels")
                    errors += 1
                if kb > 1024.0:
                    print(f"[FAIL] assets/tva/{fn}: {kb:.1f} KB exceeds 1024 KB single-GIF budget")
                    errors += 1
                else:
                    print(f"[PASS] assets/tva/{fn:<34} {w:>4}x{h:<4}  {nf:>3}f  {kb:6.1f} KB")
        except Exception as exc:
            print(f"[FAIL] assets/tva/{fn}: corrupt GIF: {exc}")
            errors += 1
    print(f"[PASS] Total TVA GIF payload: {total_kb:.1f} KB across {len(files)} animated GIFs")
    return errors


def check_orphans() -> int:
    print("\n=== Checking for Orphaned / Legacy Files in assets/ ===")
    allowed_dirs = set(ACTIVE_SVG_DIRS) | {"source", "tva"}
    errors = 0
    for entry in sorted(os.listdir(ASSETS)):
        full = os.path.join(ASSETS, entry)
        if os.path.isdir(full):
            if entry not in allowed_dirs:
                print(f"[FAIL] Legacy/orphaned directory present: assets/{entry}/")
                errors += 1
        else:
            print(f"[FAIL] Legacy/orphaned root file present: assets/{entry}")
            errors += 1
    if errors == 0:
        print("[PASS] assets/ tree is spotless (zero orphaned files or legacy folders)")
    return errors


if __name__ == "__main__":
    svg_errs, _, _ = validate_svgs()
    gif_errs = validate_gifs()
    src_errs = validate_sources()
    orp_errs = check_orphans()
    total_errs = svg_errs + gif_errs + src_errs + orp_errs
    if total_errs == 0:
        print("\nALL ASSETS VALIDATED SUCCESSFULLY! (0 errors)")
        sys.exit(0)
    print(f"\nASSET VALIDATION FAILED WITH {total_errs} ERROR(S)")
    sys.exit(1)
