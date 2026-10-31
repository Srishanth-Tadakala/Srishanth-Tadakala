import os
import xml.etree.ElementTree as ET
from PIL import Image

def validate_svgs(asset_dir="assets"):
    print("=== Validating SVG Assets ===")
    errors = 0
    svg_files = [f for f in os.listdir(asset_dir) if f.endswith(".svg")]
    if not svg_files:
        print("Error: No SVG files found in assets directory!")
        return 1
    
    for f in svg_files:
        path = os.path.join(asset_dir, f)
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            if not root.tag.endswith("svg"):
                print(f"[FAIL] {f}: Root element is not <svg>")
                errors += 1
            else:
                w = root.attrib.get("width", "auto")
                h = root.attrib.get("height", "auto")
                vb = root.attrib.get("viewBox", "none")
                print(f"[PASS] {f} (width={w}, height={h}, viewBox={vb})")
        except Exception as e:
            print(f"[FAIL] {f}: XML Parsing Error: {e}")
            errors += 1
    return errors

def validate_images(asset_dir="assets"):
    print("\n=== Validating Image Assets ===")
    errors = 0
    img_files = [f for f in os.listdir(asset_dir) if f.endswith((".png", ".jpg", ".webp"))]
    if not img_files:
        print("Error: No image files found in assets directory!")
        return 1

    for f in img_files:
        path = os.path.join(asset_dir, f)
        try:
            with Image.open(path) as img:
                img.verify()
            # re-open to check dimensions
            with Image.open(path) as img:
                w, h = img.size
                fmt = img.format
                print(f"[PASS] {f}: {w}x{h} ({fmt}, {os.path.getsize(path) / 1024:.1f} KB)")
        except Exception as e:
            print(f"[FAIL] {f}: Corrupt image: {e}")
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

