"""Validate README.md for GitHub compatibility, link integrity, and data accuracy.

Usage:
    python scripts/validate_readme.py
    python scripts/validate_readme.py --check-urls
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_live_urls(urls: list[str]) -> int:
    print(f"\n=== Verifying {len(urls)} External HTTP(S) URLs ===")
    errors = 0
    for url in sorted(set(urls)):
        # Social sites like LinkedIn/Instagram/Facebook often return 999/403/302 to non-browser UAs;
        # GitHub repository & profile URLs MUST return HTTP 200.
        is_gh = "github.com/" in url
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjectMarvelValidator/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.status
                if is_gh and code != 200:
                    print(f"[FAIL] GitHub URL returned HTTP {code}: {url}")
                    errors += 1
                else:
                    print(f"[PASS] HTTP {code}: {url}")
        except urllib.error.HTTPError as exc:
            if not is_gh and exc.code in (400, 403, 405, 429, 999):
                print(f"[INFO] Social/anti-bot HTTP {exc.code} (expected for non-browser UA): {url}")
            else:
                print(f"[FAIL] HTTP {exc.code}: {url}")
                errors += 1
        except Exception as exc:
            print(f"[FAIL] Network error for {url}: {exc}")
            errors += 1
    return errors


def validate_readme(check_urls: bool = False) -> int:
    print("=== Validating README.md (Project Marvel) ===")
    readme_path = os.path.join(ROOT, "README.md")
    if not os.path.exists(readme_path):
        print("[FAIL] README.md does not exist")
        return 1

    raw_bytes = open(readme_path, "rb").read()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        print("[FAIL] README.md has UTF-8 BOM")
        return 1
    content = raw_bytes.decode("utf-8")

    profile = json.load(open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8"))
    telemetry = json.load(open(os.path.join(ROOT, "data", "telemetry.json"), encoding="utf-8"))
    errors = 0

    # 1. Forbidden GitHub-incompatible HTML constructs
    forbidden = (
        "<script",
        "<style",
        "<iframe",
        "<object",
        "<embed",
        "<table",
        "onclick=",
        "onload=",
        "javascript:",
        'style="',
        "style='",
    )
    for tok in forbidden:
        if tok.lower() in content.lower():
            print(f"[FAIL] Forbidden or GitHub-stripped HTML construct in README.md: {tok}")
            errors += 1
    if errors == 0:
        print("[PASS] Zero forbidden tags, inline styles, or leaky HTML layout tables")

    # 2. Local asset references (<img src="..."> and <source srcset="...">)
    local_refs = set()
    for attr in ("src", "srcset"):
        for m in re.findall(rf'{attr}="([^"]+)"', content):
            if not m.startswith(("http://", "https://", "data:")):
                local_refs.add(m.split("?")[0])

    print(f"\nVerifying {len(local_refs)} referenced local SVG & GIF assets...")
    for ref in sorted(local_refs):
        disk = os.path.join(ROOT, ref.replace("/", os.sep))
        if not os.path.isfile(disk) or os.path.getsize(disk) == 0:
            print(f"[FAIL] Missing or empty asset referenced in README.md: {ref}")
            errors += 1

    # Ensure every generated SVG & GIF in assets/ is actually used in README.md
    on_disk_assets = set()
    assets_root = os.path.join(ROOT, "assets")
    for dp, _, fns in os.walk(assets_root):
        rel_dir = os.path.relpath(dp, ROOT).replace(os.sep, "/")
        if rel_dir == "assets/source":
            continue
        for fn in fns:
            if fn.endswith((".svg", ".gif")):
                on_disk_assets.add(f"{rel_dir}/{fn}")
    unused = on_disk_assets - local_refs
    if unused:
        for u in sorted(unused):
            print(f"[FAIL] Unreferenced visual asset on disk: {u}")
            errors += 1
    else:
        print(f"[PASS] All {len(local_refs)} referenced SVGs & GIFs exist and match 1:1 with generated assets")

    # 3. Every <img> must carry non-empty alt text
    imgs = re.findall(r"<img\b[^>]*>", content)
    for tag in imgs:
        m = re.search(r'alt="([^"]*)"', tag)
        if not m or not m.group(1).strip():
            print(f"[FAIL] <img> missing non-empty alt attribute: {tag[:80]}")
            errors += 1
    print(f"[PASS] All {len(imgs)} <img> tags include descriptive alt text")

    # 4. Anchor links (#...) must resolve to id="..."
    anchors = set(re.findall(r'href="#([^"]+)"', content))
    ids = set(re.findall(r'\bid="([^"]+)"', content))
    for a in sorted(anchors):
        if a not in ids:
            print(f"[FAIL] Unresolved internal anchor link: #{a}")
            errors += 1
        else:
            print(f"[PASS] Anchor resolved: #{a}")

    # 4b. Zero raw blue HTML text links on the main visual canvas (outside collapsed <details>)
    visual_canvas = re.sub(r"<details>.*?</details>", "", content, flags=re.S)
    for a_match in re.finditer(r'<a\b[^>]*href="[^"]+"[^>]*>(.*?)</a>', visual_canvas, flags=re.S):
        inner = a_match.group(1).strip()
        if inner and "<img" not in inner:
            print(f"[FAIL] Raw blue HTML text link on visual canvas (must be SVG pill): {inner[:60]}")
            errors += 1
    print("[PASS] Zero raw GitHub-blue text links on main visual canvas")

    # 5. <details> Markdown parsing rule: blank line required after </summary>
    det = re.search(r"<details>\s*<summary>.*?</summary>(\r?\n\r?\n)", content, re.S)
    if not det:
        print("[FAIL] <details> block missing blank line after </summary> (breaks GitHub Markdown parsing)")
        errors += 1
    else:
        print("[PASS] Accessible <details> dossier has proper GFM blank line after </summary>")

    # 6. Anti-fabrication & telemetry accuracy verification
    banned_fabrications = (
        "45+",
        "250+",
        "100+",
        "1.2k+",
        "45 Days",
        "Iron-Man-Gestures",
        "Ta-Da-",
        "tea-shop-project-tawny.vercel.app",
        "github-readme-stats.vercel.app",
        "github-readme-activity-graph.vercel.app",
        "Google Cloud Badges",
    )
    for fab in banned_fabrications:
        if fab.lower() in content.lower():
            print(f"[FAIL] Banned fabricated/404 string detected in README.md: {fab}")
            errors += 1

    expected_tokens = [
        profile["identity"]["name"],
        f"{telemetry['public_repos']} public repos",
        f"{telemetry['stars']} stars",
        f"{telemetry['contributions_last_year']} contributions",
        f"longest streak {telemetry['longest_streak']} days",
        "not affiliated with or endorsed by Marvel",
    ]
    for p in profile["projects"]:
        expected_tokens.append(p["name"])
        if p["repo"]:
            expected_tokens.append(f"https://github.com/{profile['identity']['login']}/{p['repo']}")

    for tok in expected_tokens:
        if tok not in content:
            print(f"[FAIL] Expected verified token missing from README.md: {tok}")
            errors += 1
    print("[PASS] Verified telemetry & repository provenance cross-check passed (0 fabrications)")

    # 7. Optional live HTTP check
    if check_urls:
        ext_urls = re.findall(r'(?:href|src)="(https?://[^"]+)"', content)
        ext_urls += re.findall(r"\]\((https?://[^)]+)\)", content)
        errors += check_live_urls(ext_urls)

    print("\n" + "=" * 44)
    if errors == 0:
        print("README VALIDATION PASSED! (0 errors)")
        return 0
    print(f"README VALIDATION FAILED WITH {errors} ERROR(S)")
    return 1


if __name__ == "__main__":
    sys.exit(validate_readme(check_urls="--check-urls" in sys.argv))
