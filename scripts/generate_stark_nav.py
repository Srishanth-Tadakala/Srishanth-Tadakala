import os

os.makedirs('assets/marvel', exist_ok=True)

nav_dossier = """<svg xmlns="http://www.w3.org/2000/svg" width="108" height="32" viewBox="0 0 108 32">
  <rect width="108" height="32" rx="16" fill="#071514" stroke="#00C8E8" stroke-width="1.2"/>
  <circle cx="20" cy="16" r="4" fill="#00C8E8"/>
  <text x="32" y="20" font-family="Courier, monospace" font-size="11" font-weight="900" fill="#E8F3F0" letter-spacing="1">DOSSIER</text>
</svg>"""

nav_arsenal = """<svg xmlns="http://www.w3.org/2000/svg" width="112" height="32" viewBox="0 0 112 32">
  <rect width="112" height="32" rx="16" fill="#071514" stroke="#E7BD54" stroke-width="1.2"/>
  <polygon points="20,10 24,18 16,18" fill="#E7BD54"/>
  <text x="32" y="20" font-family="Courier, monospace" font-size="11" font-weight="900" fill="#E8F3F0" letter-spacing="1">ARSENAL</text>
</svg>"""

nav_multiverse = """<svg xmlns="http://www.w3.org/2000/svg" width="134" height="32" viewBox="0 0 134 32">
  <rect width="134" height="32" rx="16" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
  <circle cx="20" cy="16" r="5" stroke="#00E6A0" stroke-width="1.5" fill="none"/>
  <circle cx="20" cy="16" r="2" fill="#00E6A0"/>
  <text x="34" y="20" font-family="Courier, monospace" font-size="11" font-weight="900" fill="#E8F3F0" letter-spacing="1">MULTIVERSE</text>
</svg>"""

nav_command = """<svg xmlns="http://www.w3.org/2000/svg" width="114" height="32" viewBox="0 0 114 32">
  <rect width="114" height="32" rx="16" fill="#071514" stroke="#00C8E8" stroke-width="1.2"/>
  <rect x="15" y="11" width="10" height="10" rx="2" stroke="#00C8E8" stroke-width="1.5" fill="none"/>
  <text x="34" y="20" font-family="Courier, monospace" font-size="11" font-weight="900" fill="#E8F3F0" letter-spacing="1">COMMAND</text>
</svg>"""

nav_archives = """<svg xmlns="http://www.w3.org/2000/svg" width="118" height="32" viewBox="0 0 118 32">
  <rect width="118" height="32" rx="16" fill="#071514" stroke="#E7BD54" stroke-width="1.2"/>
  <polygon points="20,11 25,21 15,21" stroke="#E7BD54" stroke-width="1.2" fill="none"/>
  <text x="32" y="20" font-family="Courier, monospace" font-size="11" font-weight="900" fill="#E8F3F0" letter-spacing="1">ARCHIVES</text>
</svg>"""

nav_comms = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="32" viewBox="0 0 100 32">
  <rect width="100" height="32" rx="16" fill="#00C8E8"/>
  <circle cx="18" cy="16" r="3" fill="#050B0B"/>
  <text x="28" y="20" font-family="Courier, monospace" font-size="11" font-weight="900" fill="#050B0B" letter-spacing="1">COMMS</text>
</svg>"""

files = {
    'assets/marvel/nav-dossier.svg': nav_dossier,
    'assets/marvel/nav-arsenal.svg': nav_arsenal,
    'assets/marvel/nav-multiverse.svg': nav_multiverse,
    'assets/marvel/nav-command.svg': nav_command,
    'assets/marvel/nav-archives.svg': nav_archives,
    'assets/marvel/nav-comms.svg': nav_comms,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print('Generated', path)
