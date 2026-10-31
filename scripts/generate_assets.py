import os
from PIL import Image, ImageEnhance, ImageFilter

os.makedirs('assets', exist_ok=True)
os.makedirs('scripts', exist_ok=True)

# 1. Generate SVGs for Navigation & Buttons
nav_home = """<svg xmlns="http://www.w3.org/2000/svg" width="86" height="32" viewBox="0 0 86 32">
  <rect width="86" height="32" rx="16" fill="#00E6A0"/>
  <path d="M17 12L23 7.5L29 12V22C29 22.55 28.55 23 28 23H18C17.45 23 17 22.55 17 22V12Z" fill="#050B0B" stroke="#050B0B" stroke-width="1.5" stroke-linejoin="round"/>
  <path d="M21 23V16H25V23" stroke="#00E6A0" stroke-width="1.5" fill="#00E6A0"/>
  <text x="34" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#050B0B" letter-spacing="0.5">HOME</text>
</svg>"""

nav_about = """<svg xmlns="http://www.w3.org/2000/svg" width="92" height="32" viewBox="0 0 92 32">
  <rect width="92" height="32" rx="16" fill="#071514" stroke="#1A3B37" stroke-width="1"/>
  <circle cx="22" cy="13" r="3.5" stroke="#00E6A0" stroke-width="1.4" fill="none"/>
  <path d="M15 22C15 19.5 18 18.5 22 18.5C26 18.5 29 19.5 29 22" stroke="#00E6A0" stroke-width="1.4" stroke-linecap="round" fill="none"/>
  <text x="35" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">ABOUT</text>
</svg>"""

nav_projects = """<svg xmlns="http://www.w3.org/2000/svg" width="108" height="32" viewBox="0 0 108 32">
  <rect width="108" height="32" rx="16" fill="#071514" stroke="#1A3B37" stroke-width="1"/>
  <path d="M20 10L26 7L32 10L26 13L20 10Z" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <path d="M20 10V18L26 21V13M32 10V18L26 21" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <text x="38" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">PROJECTS</text>
</svg>"""

nav_skills = """<svg xmlns="http://www.w3.org/2000/svg" width="92" height="32" viewBox="0 0 92 32">
  <rect width="92" height="32" rx="16" fill="#071514" stroke="#1A3B37" stroke-width="1"/>
  <path d="M17 12L13 16L17 20M25 12L29 16L25 20M22 10L20 22" stroke="#00E6A0" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="34" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">SKILLS</text>
</svg>"""

nav_achieve = """<svg xmlns="http://www.w3.org/2000/svg" width="136" height="32" viewBox="0 0 136 32">
  <rect width="136" height="32" rx="16" fill="#071514" stroke="#1A3B37" stroke-width="1"/>
  <path d="M16 11H26V16C26 18.76 23.76 21 21 21C18.24 21 16 18.76 16 16V11Z" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <path d="M16 13H13C12.45 13 12 13.45 12 14C12 15.5 13 17 16 17M26 13H29C29.55 13 30 13.45 30 14C30 15.5 29 17 26 17M21 21V23M17 23H25" stroke="#00E6A0" stroke-width="1.3" stroke-linecap="round" fill="none"/>
  <text x="34" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">ACHIEVEMENTS</text>
</svg>"""

nav_learning = """<svg xmlns="http://www.w3.org/2000/svg" width="106" height="32" viewBox="0 0 106 32">
  <rect width="106" height="32" rx="16" fill="#071514" stroke="#1A3B37" stroke-width="1"/>
  <path d="M15 11C17 10 20 10 22 12C24 10 27 10 29 11V22C27 21 24 21 22 23C20 21 17 21 15 22V11Z" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <path d="M22 12V23" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <text x="34" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">LEARNING</text>
</svg>"""

nav_contact = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="32" viewBox="0 0 100 32">
  <rect width="100" height="32" rx="16" fill="#071514" stroke="#1A3B37" stroke-width="1"/>
  <rect x="14" y="11" width="14" height="10" rx="2" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <path d="M14 12L21 17L28 12" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
  <text x="34" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">CONTACT</text>
</svg>"""

nav_github = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="16" fill="#0A1E1D" stroke="#1A3B37" stroke-width="1"/>
  <path fill-rule="evenodd" clip-rule="evenodd" d="M16 7C11.03 7 7 11.03 7 16C7 19.98 9.58 23.35 13.16 24.54C13.61 24.62 13.78 24.34 13.78 24.1C13.78 23.89 13.77 23.17 13.77 22.38C11.51 22.82 10.97 21.84 10.79 21.33C10.69 21.07 10.25 20.27 9.87 20.06C9.55 19.89 9.1 19.47 9.86 19.46C10.57 19.45 11.08 20.11 11.25 20.38C12.06 21.75 13.37 21.36 13.89 21.12C13.97 20.53 14.21 20.13 14.47 19.9C12.45 19.67 10.33 18.89 10.33 15.41C10.33 14.42 10.68 13.6 11.26 12.96C11.17 12.73 10.86 11.8 11.35 10.55C11.35 10.55 12.11 10.31 13.84 11.48C14.56 11.28 15.33 11.18 16.1 11.18C16.87 11.18 17.64 11.28 18.36 11.48C20.09 10.3 20.85 10.55 20.85 10.55C21.34 11.8 21.03 12.73 20.94 12.96C21.52 13.6 21.87 14.41 21.87 15.41C21.87 18.9 19.74 19.67 17.72 19.9C18.05 20.18 18.33 20.73 18.33 21.58C18.33 22.8 18.32 23.78 18.32 24.1C18.32 24.34 18.48 24.63 18.94 24.54C22.42 23.35 25 19.97 25 16C25 11.03 20.97 7 16 7Z" fill="#E8F3F0"/>
</svg>"""

nav_linkedin = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#0077B5"/>
  <path d="M11 13H14V22H11V13ZM12.5 8.5C11.67 8.5 11 9.17 11 10C11 10.83 11.67 11.5 12.5 11.5C13.33 11.5 14 10.83 14 10C14 9.17 13.33 8.5 12.5 8.5ZM16 13H18.8V14.25H18.84C19.23 13.51 20.18 12.73 21.6 12.73C24.55 12.73 25.1 14.67 25.1 17.18V22H22.1V17.31C22.1 16.19 22.08 14.75 20.54 14.75C18.98 14.75 18.74 15.97 18.74 17.23V22H15.74V13H16Z" fill="#FFFFFF"/>
</svg>"""

nav_youtube = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#FF0000"/>
  <path d="M24.7 11.8C24.5 11 23.9 10.4 23.1 10.2C21.7 9.8 16 9.8 16 9.8C16 9.8 10.3 9.8 8.9 10.2C8.1 10.4 7.5 11 7.3 11.8C6.9 13.2 6.9 16 6.9 16C6.9 16 6.9 18.8 7.3 20.2C7.5 21 8.1 21.6 8.9 21.8C10.3 22.2 16 22.2 16 22.2C16 22.2 21.7 22.2 23.1 21.8C23.9 21.6 24.5 21 24.7 20.2C25.1 18.8 25.1 16 25.1 16C25.1 16 25.1 13.2 24.7 11.8Z" fill="#FFFFFF"/>
  <polygon points="14.2,18.5 19.2,16 14.2,13.5" fill="#FF0000"/>
</svg>"""

nav_instagram = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <defs>
    <radialGradient id="igGrad" cx="30%" cy="107%" r="150%">
      <stop offset="0%" stop-color="#fdf497"/>
      <stop offset="5%" stop-color="#fdf497"/>
      <stop offset="45%" stop-color="#fd5949"/>
      <stop offset="60%" stop-color="#d6249f"/>
      <stop offset="90%" stop-color="#285AEB"/>
    </radialGradient>
  </defs>
  <rect width="32" height="32" rx="8" fill="url(#igGrad)"/>
  <rect x="8.5" y="8.5" width="15" height="15" rx="4" stroke="#FFFFFF" stroke-width="1.8" fill="none"/>
  <circle cx="16" cy="16" r="3.8" stroke="#FFFFFF" stroke-width="1.8" fill="none"/>
  <circle cx="20.3" cy="11.7" r="1" fill="#FFFFFF"/>
</svg>"""

nav_x = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#000000" stroke="#1A3B37" stroke-width="1"/>
  <path d="M10 9L14.7 15.3L10 21H11.5L15.3 16.3L18.7 21H23L18.1 14.3L22.5 9H21L17.5 13.3L14.3 9H10ZM12.2 10.2H14.1L20.8 19.8H18.9L12.2 10.2Z" fill="#E8F3F0"/>
</svg>"""

nav_email = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#0A1E1D" stroke="#00E6A0" stroke-width="1"/>
  <rect x="8" y="10" width="16" height="12" rx="2" stroke="#00E6A0" stroke-width="1.4" fill="none"/>
  <path d="M8 11L16 17L24 11" stroke="#00E6A0" stroke-width="1.4" fill="none"/>
</svg>"""

btn_repo = """<svg xmlns="http://www.w3.org/2000/svg" width="116" height="30" viewBox="0 0 116 30">
  <rect width="116" height="30" rx="15" fill="#00E6A0"/>
  <text x="58" y="19" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#050B0B" text-anchor="middle">View Repo →</text>
</svg>"""

btn_demo = """<svg xmlns="http://www.w3.org/2000/svg" width="104" height="30" viewBox="0 0 104 30">
  <rect x="1" y="1" width="102" height="28" rx="14" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
  <text x="52" y="19" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" text-anchor="middle">Live Demo</text>
</svg>"""

btn_doc = """<svg xmlns="http://www.w3.org/2000/svg" width="124" height="30" viewBox="0 0 124 30">
  <rect x="1" y="1" width="122" height="28" rx="14" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
  <text x="62" y="19" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" text-anchor="middle">Documentation</text>
</svg>"""

svg_files = {
    'assets/nav-home.svg': nav_home,
    'assets/nav-about.svg': nav_about,
    'assets/nav-projects.svg': nav_projects,
    'assets/nav-skills.svg': nav_skills,
    'assets/nav-achievements.svg': nav_achieve,
    'assets/nav-learning.svg': nav_learning,
    'assets/nav-contact.svg': nav_contact,
    'assets/nav-github.svg': nav_github,
    'assets/nav-linkedin.svg': nav_linkedin,
    'assets/nav-youtube.svg': nav_youtube,
    'assets/nav-instagram.svg': nav_instagram,
    'assets/nav-x.svg': nav_x,
    'assets/nav-email.svg': nav_email,
    'assets/btn-view-repo.svg': btn_repo,
    'assets/btn-live-demo.svg': btn_demo,
    'assets/btn-doc.svg': btn_doc
}

for path, content in svg_files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print('Generated', path)

# 2. Generate Combined Navigation Bar SVG (for standalone or fallback preview)
nav_bar_full = """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="42" viewBox="0 0 1000 42">
  <defs>
    <filter id="navGlow" x="-5%" y="-20%" width="110%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect x="1" y="1" width="998" height="40" rx="20" fill="#071514" stroke="#00E6A0" stroke-width="1.2" stroke-opacity="0.8" filter="url(#navGlow)"/>
  
  <!-- Home Active -->
  <g transform="translate(10, 5)">
    <rect width="80" height="32" rx="16" fill="#00E6A0"/>
    <path d="M16 12L22 7.5L28 12V22C28 22.55 27.55 23 27 23H17C16.45 23 16 22.55 16 22V12Z" fill="#050B0B" stroke="#050B0B" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M20 23V16H24V23" stroke="#00E6A0" stroke-width="1.5" fill="#00E6A0"/>
    <text x="34" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#050B0B" letter-spacing="0.5">HOME</text>
  </g>

  <!-- About -->
  <g transform="translate(100, 5)">
    <circle cx="16" cy="13" r="3.5" stroke="#00E6A0" stroke-width="1.4" fill="none"/>
    <path d="M9 22C9 19.5 12 18.5 16 18.5C20 18.5 23 19.5 23 22" stroke="#00E6A0" stroke-width="1.4" stroke-linecap="round" fill="none"/>
    <text x="28" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">ABOUT</text>
  </g>

  <!-- Projects -->
  <g transform="translate(185, 5)">
    <path d="M14 10L20 7L26 10L20 13L14 10Z" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <path d="M14 10V18L20 21V13M26 10V18L20 21" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <text x="32" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">PROJECTS</text>
  </g>

  <!-- Skills -->
  <g transform="translate(290, 5)">
    <path d="M14 12L10 16L14 20M22 12L26 16L22 20M19 10L17 22" stroke="#00E6A0" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <text x="30" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">SKILLS</text>
  </g>

  <!-- Achievements -->
  <g transform="translate(378, 5)">
    <path d="M13 11H23V16C23 18.76 20.76 21 18 21C15.24 21 13 18.76 13 16V11Z" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <path d="M13 13H10C9.45 13 9 13.45 9 14C9 15.5 10 17 13 17M23 13H26C26.55 13 27 13.45 27 14C27 15.5 26 17 23 17M18 21V23M14 23H22" stroke="#00E6A0" stroke-width="1.3" stroke-linecap="round" fill="none"/>
    <text x="32" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">ACHIEVEMENTS</text>
  </g>

  <!-- Learning -->
  <g transform="translate(515, 5)">
    <path d="M12 11C14 10 17 10 19 12C21 10 24 10 26 11V22C24 21 21 21 19 23C17 21 14 21 12 22V11Z" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <path d="M19 12V23" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <text x="30" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">LEARNING</text>
  </g>

  <!-- Contact -->
  <g transform="translate(620, 5)">
    <rect x="11" y="11" width="14" height="10" rx="2" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <path d="M11 12L18 17L25 12" stroke="#00E6A0" stroke-width="1.3" fill="none"/>
    <text x="31" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">CONTACT</text>
  </g>

  <!-- Divider -->
  <line x1="770" y1="10" x2="770" y2="32" stroke="#1A3B37" stroke-width="1.5"/>

  <!-- Social Icons -->
  <g transform="translate(790, 7)">
    <!-- GitHub -->
    <g transform="translate(0, 0)">
      <circle cx="14" cy="14" r="14" fill="#0A1E1D" stroke="#1A3B37" stroke-width="1"/>
      <path fill-rule="evenodd" clip-rule="evenodd" d="M14 6C9.58 6 6 9.58 6 14C6 17.54 8.29 20.53 11.47 21.59C11.87 21.66 12.02 21.41 12.02 21.2C12.02 21.01 12.01 20.37 12.01 19.67C9.99 20.06 9.51 19.19 9.35 18.74C9.26 18.51 8.87 17.8 8.53 17.61C8.25 17.46 7.85 17.08 8.52 17.07C9.15 17.06 9.61 17.65 9.76 17.89C10.48 19.11 11.65 18.76 12.11 18.55C12.18 18.03 12.39 17.67 12.62 17.47C10.82 17.27 8.94 16.57 8.94 13.47C8.94 12.59 9.25 11.86 9.77 11.29C9.69 11.09 9.41 10.26 9.85 9.15C9.85 9.15 10.53 8.94 12.07 9.98C12.72 9.8 13.41 9.71 14.1 9.71C14.79 9.71 15.48 9.8 16.13 9.98C17.67 8.93 18.35 9.15 18.35 9.15C18.79 10.26 18.51 11.09 18.43 11.29C18.95 11.86 19.26 12.58 19.26 13.47C19.26 16.58 17.37 17.27 15.57 17.47C15.86 17.72 16.12 18.21 16.12 18.96C16.12 20.04 16.11 20.92 16.11 21.2C16.11 21.41 16.26 21.67 16.67 21.59C19.71 20.53 22 17.53 22 14C22 9.58 18.42 6 14 6Z" fill="#E8F3F0"/>
    </g>
    <!-- LinkedIn -->
    <g transform="translate(38, 0)">
      <rect width="28" height="28" rx="6" fill="#0077B5"/>
      <path d="M8 11H11V20H8V11ZM9.5 6.5C8.67 6.5 8 7.17 8 8C8 8.83 8.67 9.5 9.5 9.5C10.33 9.5 11 8.83 11 8C11 7.17 10.33 6.5 9.5 6.5ZM13 11H15.8V12.25H15.84C16.23 11.51 17.18 10.73 18.6 10.73C21.55 10.73 22.1 12.67 22.1 15.18V20H19.1V15.31C19.1 14.19 19.08 12.75 17.54 12.75C15.98 12.75 15.74 13.97 15.74 15.23V20H12.74V11H13Z" fill="#FFFFFF"/>
    </g>
    <!-- YouTube -->
    <g transform="translate(76, 0)">
      <rect width="28" height="28" rx="6" fill="#FF0000"/>
      <path d="M22 9.8C21.8 9 21.2 8.4 20.4 8.2C19 7.8 14 7.8 14 7.8C14 7.8 9 7.8 7.6 8.2C6.8 8.4 6.2 9 6 9.8C5.6 11.2 5.6 14 5.6 14C5.6 14 5.6 16.8 6 18.2C6.2 19 6.8 19.6 7.6 19.8C9 20.2 14 20.2 14 20.2C14 20.2 19 20.2 20.4 19.8C21.2 19.6 21.8 19 22 18.2C22.4 16.8 22.4 14 22.4 14C22.4 14 22.4 11.2 22 9.8Z" fill="#FFFFFF"/>
      <polygon points="12.2,16.5 17.2,14 12.2,11.5" fill="#FF0000"/>
    </g>
    <!-- Instagram -->
    <g transform="translate(114, 0)">
      <rect width="28" height="28" rx="6" fill="url(#igGrad)"/>
      <rect x="6.5" y="6.5" width="15" height="15" rx="4" stroke="#FFFFFF" stroke-width="1.8" fill="none"/>
      <circle cx="14" cy="14" r="3.8" stroke="#FFFFFF" stroke-width="1.8" fill="none"/>
      <circle cx="18.3" cy="9.7" r="1" fill="#FFFFFF"/>
    </g>
    <!-- X -->
    <g transform="translate(152, 0)">
      <rect width="28" height="28" rx="6" fill="#000000" stroke="#1A3B37" stroke-width="1"/>
      <path d="M8 8L12.7 14.3L8 20H9.5L13.3 15.3L16.7 20H21L16.1 13.3L20.5 8H19L15.5 12.3L12.3 8H8ZM10.2 9.2H12.1L18.8 18.8H16.9L10.2 9.2Z" fill="#E8F3F0"/>
    </g>
  </g>
</svg>"""

with open('assets/nav-bar.svg', 'w', encoding='utf-8') as f:
    f.write(nav_bar_full.strip())
print('Generated assets/nav-bar.svg')

print('All navigation SVGs generated successfully!')

