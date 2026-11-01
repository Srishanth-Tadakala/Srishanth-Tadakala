"""Render GitHub-accurate local previews of README.md across viewports & themes.

Emulates GitHub's exact profile README container (.Box > .markdown-body: 848px inner
width on 1440px desktop, 640px on 1024px laptop, full-width on 390px mobile) in both
GitHub Dark (#0d1117) and GitHub Light (#ffffff) themes, then slices per-section
inspection crops into previews/crops/.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEWS = os.path.join(ROOT, "previews")
CROPS = os.path.join(PREVIEWS, "crops")
os.makedirs(CROPS, exist_ok=True)


def md_to_github_html(md: str) -> str:
    """Convert Markdown inside <details> while leaving raw HTML blocks intact."""
    def render_details(m: re.Match) -> str:
        inner = m.group(2)
        blocks = [b.strip() for b in re.split(r"\n{2,}", inner.strip()) if b.strip()]
        out = []
        for b in blocks:
            if b.startswith("- "):
                items = [re.sub(r"^-\s+", "", ln.strip()) for ln in b.splitlines() if ln.strip().startswith("- ")]
                items = [_inline(it) for it in items]
                out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            elif b.startswith("<"):
                out.append(_inline(b))
            else:
                lines = [_inline(ln.rstrip()) for ln in b.splitlines()]
                out.append("<p>" + "<br>\n".join(lines) + "</p>")
        return f"<details>{m.group(1)}\n" + "\n".join(out) + "\n</details>"

    def _inline(s: str) -> str:
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    return re.sub(r"<details>\s*(<summary>.*?</summary>)(.*?)</details>", render_details, md, flags=re.S)


def make_html(body: str, theme: str = "dark", mobile_width: int | None = None) -> str:
    dark = theme == "dark"
    bg = "#0d1117" if dark else "#ffffff"
    fg = "#e6edf3" if dark else "#1f2328"
    muted = "#8b949e" if dark else "#656d76"
    border = "#30363d" if dark else "#d0d7de"
    link = "#58a6ff" if dark else "#0969da"
    subtle = "#161b22" if dark else "#f6f8fa"
    base_uri = pathlib.Path(ROOT).as_uri() + "/"
    mob_css = f"html, body {{ width: {mobile_width}px; max-width: {mobile_width}px; overflow-x: hidden; }}" if mobile_width else ""

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <base href="{base_uri}">
  <title>GitHub Profile Preview ({theme})</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: {bg};
      color: {fg};
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
      font-size: 16px;
      line-height: 1.5;
    }}
    {mob_css}
    .gh-shell {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px 32px;
      display: flex;
      gap: 24px;
      align-items: flex-start;
    }}
    .gh-sidebar {{
      width: 296px;
      flex: 0 0 296px;
      border: 1px dashed {border};
      border-radius: 6px;
      padding: 16px;
      color: {muted};
      font-size: 13px;
      background: {subtle};
    }}
    .gh-readme-box {{
      flex: 1 1 auto;
      min-width: 0;
      border: 1px solid {border};
      border-radius: 6px;
      padding: 24px;
      background: {bg};
    }}
    .gh-readme-label {{
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 12px;
      color: {muted};
      margin-bottom: 12px;
    }}
    @media (max-width: 1100px) {{
      .gh-sidebar {{ width: 256px; flex-basis: 256px; }}
    }}
    @media (max-width: 767px) {{
      .gh-shell {{ display: block; padding: 8px; }}
      .gh-sidebar {{ display: none; }}
      .gh-readme-box {{ padding: 16px; }}
    }}
    .markdown-body {{ word-wrap: break-word; }}
    .markdown-body img {{
      max-width: 100%;
      height: auto;
      box-sizing: content-box;
      background-color: transparent;
    }}
    .markdown-body p, .markdown-body ul, .markdown-body details {{
      margin-top: 0;
      margin-bottom: 16px;
    }}
    .markdown-body a {{ color: {link}; text-decoration: none; }}
    .markdown-body sub {{ font-size: 75%; line-height: 0; position: relative; vertical-align: baseline; bottom: -0.25em; }}
    .markdown-body details summary {{ cursor: pointer; }}
  </style>
</head>
<body>
  <div class="gh-shell">
    <aside class="gh-sidebar">
      <strong>Srishanth Tadakala</strong><br>
      Srishanth-Tadakala<br><br>
      GitHub profile left sidebar placeholder (296px) to reproduce exact 848px README width.
    </aside>
    <main class="gh-readme-box">
      <div class="gh-readme-label">Srishanth-Tadakala / README.md</div>
      <article class="markdown-body">
{body}
      </article>
    </main>
  </div>
</body>
</html>
"""


def find_browser() -> str:
    for c in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ):
        if os.path.exists(c):
            return c
    raise RuntimeError("No Chrome/Edge executable found")


def slice_crops(img_path: str, prefix: str, step: int = 1100):
    with Image.open(img_path) as im:
        w, h = im.size
        # Trim solid trailing bottom whitespace/bg
        px = im.load()
        bg = px[w - 2, h - 2]
        last_y = h - 1
        while last_y > 400:
            if any(px[x, last_y] != bg for x in range(0, w, 8)):
                break
            last_y -= 2
        content_h = min(h, last_y + 40)
        idx = 1
        y = 0
        while y < content_h:
            y2 = min(content_h, y + step)
            crop_path = os.path.join(CROPS, f"{prefix}-{idx:02d}.png")
            im.crop((0, y, w, y2)).save(crop_path)
            y += step - 80
            idx += 1
        print(f"  -> sliced {idx - 1} crops (active height {content_h}px)")


def main():
    for f in os.listdir(CROPS):
        if f.endswith(".png"):
            os.remove(os.path.join(CROPS, f))
    md = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    body = md_to_github_html(md)

    dark_html = os.path.join(PREVIEWS, "_preview_dark.html")
    light_html = os.path.join(PREVIEWS, "_preview_light.html")
    mob_html = os.path.join(PREVIEWS, "_preview_mobile.html")
    open(dark_html, "w", encoding="utf-8").write(make_html(body, "dark"))
    open(light_html, "w", encoding="utf-8").write(make_html(body, "light"))
    open(mob_html, "w", encoding="utf-8").write(make_html(body, "dark", mobile_width=390))

    browser = find_browser()
    # Note: Windows desktop Chrome enforces a 500px minimum outer window width;
    # for mobile-390px we render inside a 500px window (<600px so <picture> mobile
    # sources trigger!) with body constrained to 390px, then crop to 390px.
    jobs = [
        ("desktop-1440px.png", dark_html, 1440, 6600, "desktop-dark", None),
        ("light-1440px.png", light_html, 1440, 6600, "desktop-light", None),
        ("laptop-1024px.png", dark_html, 1024, 8200, "laptop-dark", None),
        ("mobile-390px.png", mob_html, 500, 9600, "mobile-dark", 390),
    ]
    for out_name, html_file, w, h, crop_prefix, trim_w in jobs:
        out_path = os.path.abspath(os.path.join(PREVIEWS, out_name))
        url = pathlib.Path(html_file).as_uri()
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--allow-file-access-from-files",
            "--hide-scrollbars",
            f"--window-size={w},{h}",
            "--virtual-time-budget=1500",
            f"--screenshot={out_path}",
            url,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=False)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            if trim_w:
                with Image.open(out_path) as im:
                    im.crop((0, 0, trim_w, im.size[1])).save(out_path)
            print(f"[PASS] {out_name} ({os.path.getsize(out_path) / 1024:.1f} KB)")
            slice_crops(out_path, crop_prefix)
        else:
            raise RuntimeError(f"Failed to capture {out_name}")


if __name__ == "__main__":
    main()
