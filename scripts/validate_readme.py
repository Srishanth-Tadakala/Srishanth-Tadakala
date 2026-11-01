import os
import re

def validate_readme(readme_path="README.md"):
    print("=== Validating README.md (Project Marvel) ===")
    if not os.path.exists(readme_path):
        print(f"[FAIL] {readme_path} does not exist!")
        return 1

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    errors = 0

    # 1. Check for forbidden tags
    forbidden = ["<script", "<style", "<iframe", "onclick=", "javascript:"]
    for item in forbidden:
        if item.lower() in content.lower():
            print(f"[FAIL] Forbidden token found: {item}")
            errors += 1

    # 2. Extract and verify all local image paths
    img_patterns = [
        r'src=["\']([^"\']+\.(?:png|jpg|jpeg|svg|gif|webp))["\']',
        r'!\[[^\]]*\]\(([^)]+\.(?:png|jpg|jpeg|svg|gif|webp))\)'
    ]
    referenced_assets = set()
    for pattern in img_patterns:
        for match in re.findall(pattern, content):
            if not match.startswith("http"):
                referenced_assets.add(match.split("?")[0].replace("/", os.sep))

    print(f"\nVerifying {len(referenced_assets)} referenced local assets...")
    for asset in sorted(referenced_assets):
        if os.path.exists(asset):
            print(f"[PASS] Asset exists: {asset}")
        else:
            print(f"[FAIL] Missing asset: {asset}")
            errors += 1

    # 3. Check for anchor links and targets
    anchor_hrefs = re.findall(r'href=["\']#([^"\']+)["\']', content)
    ids = set(re.findall(r'id=["\']([^"\']+)["\']', content))
    headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
    for h in headings:
        slug = re.sub(r'[^\w\s-]', '', h).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        ids.add(slug)

    print(f"\nVerifying {len(anchor_hrefs)} anchor navigation links...")
    for anchor in set(anchor_hrefs):
        if anchor in ids or any(anchor in x for x in ids):
            print(f"[PASS] Anchor link resolved: #{anchor}")
        else:
            print(f"[FAIL] Unresolved anchor link: #{anchor}")
            errors += 1

    # 4. Check required Marvel sections
    required_sections = [
        "SRISHANTH TADAKALA",
        "STARK INDUSTRIES",
        "DOSSIER",
        "TECHNOLOGY ARSENAL",
        "PROJECT MULTIVERSE",
        "Sylvie",
        "QueueLess",
        "A.R.C.A.N.E.",
        "COMMAND CENTER",
        "ACHIEVEMENT",
        "Build. Explore. Learn. Share. Evolve."
    ]
    print(f"\nVerifying required content sections...")
    for req in required_sections:
        if req.lower() in content.lower():
            print(f"[PASS] Section present: '{req}'")
        else:
            print(f"[FAIL] Missing section: '{req}'")
            errors += 1

    print("\n" + "="*30)
    if errors == 0:
        print("README VALIDATION PASSED! (0 errors)")
        return 0
    else:
        print(f"README VALIDATION FAILED WITH {errors} ERRORS")
        return errors

if __name__ == "__main__":
    exit(validate_readme())
