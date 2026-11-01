"""Vendor open-licensed design resources used by the profile build.

* Fonts (SIL Open Font License 1.1) from github.com/google/fonts
* Brand icons (CC0 1.0) from Simple Icons (cdn.jsdelivr.net/npm/simple-icons)

Run once (requires network):  python scripts/vendor_resources.py
"""
import os, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "scripts", "vendor")
FONTS = {
    "Orbitron.ttf": "https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf",
    "Rajdhani-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-SemiBold.ttf",
    "Rajdhani-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-Bold.ttf",
    "JetBrainsMono.ttf": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "OFL-Orbitron.txt": "https://github.com/google/fonts/raw/main/ofl/orbitron/OFL.txt",
    "OFL-Rajdhani.txt": "https://github.com/google/fonts/raw/main/ofl/rajdhani/OFL.txt",
    "OFL-JetBrainsMono.txt": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/OFL.txt",
}
ICONS = [
    "python", "typescript", "javascript", "cplusplus", "c", "langchain", "pytorch", "tensorflow", "keras",
    "scikitlearn", "numpy", "pandas", "opencv", "mediapipe", "huggingface", "openai", "ollama",
    "threedotjs", "react", "nextdotjs", "fastapi", "nodedotjs", "express", "socketdotio", "vite",
    "tailwindcss", "mongodb", "postgresql", "supabase", "redis", "sqlite", "docker", "git", "github",
    "githubactions", "googlecloud", "vercel", "netlify", "render", "amazons3", "firebase", "linux",
    "figma", "postman", "pytest", "instagram", "facebook", "gmail", "linkedin", "webgl", "websocket",
]


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return len(data)
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"


os.makedirs(os.path.join(VENDOR, "fonts"), exist_ok=True)
os.makedirs(os.path.join(VENDOR, "icons"), exist_ok=True)
for name, url in FONTS.items():
    print("font", name, fetch(url, os.path.join(VENDOR, "fonts", name)))
for slug in ICONS:
    dest = os.path.join(VENDOR, "icons", slug + ".svg")
    res = fetch(f"https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{slug}.svg", dest)
    if not isinstance(res, int):
        res = fetch(f"https://cdn.jsdelivr.net/npm/simple-icons@11.15.0/icons/{slug}.svg", dest)
    if not isinstance(res, int) and os.path.exists(dest):
        os.remove(dest)
    print("icon", slug, res)

