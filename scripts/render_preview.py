import os
import subprocess
import re

os.makedirs('previews', exist_ok=True)

# Read README.md
with open('README.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Simple markdown converter for markdown elements in README
html_body = md_content

# Convert markdown headers:
html_body = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
html_body = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
html_body = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)

# Convert blockquotes:
html_body = re.sub(r'^> \*(.*?)\*$', r'<blockquote><em>\1</em></blockquote>', html_body, flags=re.MULTILINE)
html_body = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', html_body, flags=re.MULTILINE)

# Convert bold and italics
html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
html_body = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_body)

# Convert markdown links [text](url)
html_body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_body)

# Convert markdown tables (like Core Engineering Stack)
def convert_md_table(match):
    lines = match.group(0).strip().split('\n')
    if len(lines) < 2:
        return match.group(0)
    html = ['<table class="data-table">']
    # Header
    headers = [c.strip() for c in lines[0].split('|')[1:-1]]
    html.append('  <thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>')
    html.append('  <tbody>')
    for line in lines[2:]:
        cells = [c.strip() for c in line.split('|')[1:-1]]
        html.append('    <tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
    html.append('  </tbody></table>')
    return '\n'.join(html)

table_regex = re.compile(r'(\|.+\|\n\|[-:\s|]+\|\n(?:\|.+\|\n?)+)')
html_body = table_regex.sub(convert_md_table, html_body)

# Convert unordered list items
html_body = re.sub(r'^\s*-\s+(.*?)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
html_body = re.sub(r'(<li>.*?</li>\n?)+', r'<ul>\g<0></ul>', html_body)

# Convert inline code `code`
html_body = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_body)

# Convert horizontal rule
html_body = re.sub(r'^---$', r'<hr/>', html_body, flags=re.MULTILINE)

# Construct full GitHub Dark Mode HTML document
html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>GitHub Profile Preview - Srishanth Tadakala</title>
  <style>
    body {{
      background-color: #0d1117;
      color: #e6edf3;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 24px;
      line-height: 1.5;
    }}
    .container {{
      max-width: 1012px;
      margin: 0 auto;
      background-color: #0d1117;
    }}
    table {{
      border-collapse: separate;
      border-spacing: 0;
      width: 100%;
    }}
    table[border="0"] td {{
      border: none !important;
      padding: 2px !important;
    }}
    .data-table {{
      border-collapse: collapse;
      margin: 16px 0;
    }}
    .data-table th, .data-table td {{
      padding: 8px 12px;
      border: 1px solid #30363d;
    }}
    .data-table th {{
      background-color: #161b22;
      color: #00E6A0;
    }}
    img {{
      max-width: 100%;
      height: auto;
      display: inline-block;
      vertical-align: middle;
    }}
    a {{
      color: #00C8E8;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    h1, h2, h3, h4 {{
      color: #00E6A0;
      border-bottom: 1px solid #21262d;
      padding-bottom: 6px;
      margin-top: 24px;
    }}
    blockquote {{
      margin: 0;
      padding: 0 1em;
      color: #8b949e;
      border-left: 0.25em solid #00E6A0;
    }}
    code {{
      background-color: #161b22;
      color: #00E6A0;
      padding: 0.2em 0.4em;
      border-radius: 4px;
      font-size: 85%;
    }}
    hr {{
      height: 0.25em;
      padding: 0;
      margin: 24px 0;
      background-color: #30363d;
      border: 0;
    }}
    ul {{
      padding-left: 2em;
    }}
    li {{
      margin-bottom: 4px;
    }}
    details {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 12px;
      margin: 16px 0;
    }}
    summary {{
      cursor: pointer;
      font-weight: 600;
      color: #00E6A0;
    }}
  </style>
</head>
<body>
  <div class="container">
    {html_body}
  </div>
</body>
</html>
"""

preview_file = os.path.abspath('preview.html')
with open(preview_file, 'w', encoding='utf-8') as f:
    f.write(html_doc)
print(f"Generated {preview_file}")

# Try to find Chrome or Edge
browser_path = None
candidates = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]
for c in candidates:
    if os.path.exists(c):
        browser_path = c
        break

if not browser_path:
    print("Warning: No Chrome or Edge executable found to capture screenshots.")
else:
    print(f"Using browser: {browser_path}")
    viewports = [
        ("desktop-1440px.png", 1440, 5200),
        ("laptop-1024px.png", 1024, 5800),
        ("mobile-390px.png", 420, 7200)
    ]
    import pathlib
    file_url = pathlib.Path(preview_file).as_uri()
    for name, w, h in viewports:
        out_path = os.path.abspath(os.path.join('previews', name))
        cmd = [
            browser_path,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--allow-file-access-from-files",
            f"--window-size={w},{h}",
            "--hide-scrollbars",
            f"--screenshot={out_path}",
            file_url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"[PASS] Captured {name} ({os.path.getsize(out_path) / 1024:.1f} KB)")
        else:
            print(f"[FAIL] Could not capture {name}: stderr={res.stderr} stdout={res.stdout}")

print("Preview rendering complete!")

