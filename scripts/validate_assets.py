import os
import xml.etree.ElementTree as ET
from PIL import Image

def validate_svgs(dirs=["assets", "assets/marvel"]):
    print("=== Validating SVG Assets ===")
    errors = 0
    total = 0
    for d in dirs:
        if not os.path.exists(d): continue
        svg_files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".svg")]
        for path in svg_files:
            total += 1
            f = os.path.basename(path)
            try:
                tree = ET.parse(path)
                root = tree.getroot()
                if not root.tag.endswith("svg"):
                    print(f"[FAIL] {path}: Root element is not <svg>")
                    errors += 1
                else:
                    w = root.attrib.get("width", "auto")
                    h = root.attrib.get("height", "auto")
                    vb = root.attrib.get("viewBox", "none")
                    print(f"[PASS] {path} (width={w}, height={h}, viewBox={vb})")
            except Exception as e:
                print(f"[FAIL] {path}: XML Parsing Error: {e}")
                errors += 1
    return errors

def validate_images(dirs=["assets", "assets/marvel"]):
    print("\n=== Validating Image & GIF Assets ===")
    errors = 0
    for d in dirs:
        if not os.path.exists(d): continue
        img_files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith((".png", ".jpg", ".webp", ".gif"))]
        for path in img_files:
            try:
                with Image.open(path) as img:
                    img.verify()
                with Image.open(path) as img:
                    w, h = img.size
                    fmt = img.format
                    frames = getattr(img, "n_frames", 1)
                    frames_txt = f", {frames} frames" if frames > 1 else ""
                    print(f"[PASS] {path}: {w}x{h} ({fmt}{frames_txt}, {os.path.getsize(path) / 1024:.1f} KB)")
            except Exception as e:
                print(f"[FAIL] {path}: Corrupt image: {e}")
                errors += 1
    return errors

if __name__ == "__main__":
    errs = validate_svgs() + validate_images()
    if errs == 0:
        print("\nALL ASSETS VALIDATED SUCCESSFULLY! (0 errors)")
        exit(0)
    else:
        print(f"\nVALIDATION FAILED WITH {errs} ERRORS")
        exit(1)
