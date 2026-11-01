"""Screenshot the live GitHub profile page (real GitHub rendering) at desktop & mobile widths.

Usage: python scripts/capture_github.py [url] [outdir]
"""
from __future__ import annotations

import os
import subprocess
import sys

url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/Srishanth-Tadakala"
outdir = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else "previews/github")
os.makedirs(outdir, exist_ok=True)
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Note: Win32 desktop Chrome enforces a 500px minimum outer window width; 500px is below
# both GitHub's 768px mobile layout breakpoint and our <picture> 600px mobile art-direction breakpoint.
for name, w, h in [("github-desktop.png", 1440, 7200), ("github-mobile.png", 500, 9500)]:
    out = os.path.join(outdir, name)
    args = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={w},{h}",
        "--virtual-time-budget=12000",
        f"--screenshot={out}",
        url,
    ]
    if "mobile" in name:
        args.insert(
            4,
            "--user-agent=Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Mobile Safari/537.36",
        )
    subprocess.run(args, capture_output=True, text=True, timeout=180, check=False)
    print(name, os.path.exists(out) and os.path.getsize(out))
