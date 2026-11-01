import os
import base64

os.makedirs('assets/marvel', exist_ok=True)

def img_to_b64(path):
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().replace('.', '')
    if ext == 'jpg': ext = 'jpeg'
    with open(path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/{ext};base64,{data}"

arcane_b64 = img_to_b64('assets/marvel/project-arcane.jpg')
sylvie_b64 = img_to_b64('assets/project-sylvie.png')
friday_b64 = img_to_b64('assets/project-friday.png')
queue_b64 = img_to_b64('assets/project-queueless.png')

# -------------------------------------------------------------
# 1. MULTIVERSE ELDRITCH DIVIDER (DOCTOR STRANGE + STARK HUD)
# -------------------------------------------------------------
multiverse_divider = """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="32" viewBox="0 0 1000 32">
  <defs>
    <filter id="portalGlow" x="-20%" y="-100%" width="140%" height="300%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <linearGradient id="portalBeam" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF9900" stop-opacity="0"/>
      <stop offset="25%" stop-color="#E7BD54" stop-opacity="0.8"/>
      <stop offset="50%" stop-color="#00E6A0" stop-opacity="1"/>
      <stop offset="75%" stop-color="#00C8E8" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#00C8E8" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <style>
    @keyframes runeSpin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes beamPulse {
      0%, 100% { opacity: 0.7; }
      50% { opacity: 1; filter: drop-shadow(0 0 4px #00E6A0); }
    }
    .rune { transform-origin: 500px 16px; animation: runeSpin 12s linear infinite; }
    .beam-line { animation: beamPulse 3s ease-in-out infinite; }
  </style>

  <!-- Baseline -->
  <line x1="20" y1="16" x2="470" y2="16" stroke="#1A3B37" stroke-width="1.5"/>
  <line x1="530" y1="16" x2="980" y2="16" stroke="#1A3B37" stroke-width="1.5"/>

  <!-- Glowing Laser Beam Center -->
  <line x1="150" y1="16" x2="850" y2="16" stroke="url(#portalBeam)" stroke-width="2.5" class="beam-line" filter="url(#portalGlow)"/>

  <!-- Left & Right Tech Accents -->
  <polygon points="150,12 156,16 150,20 144,16" fill="#00C8E8"/>
  <polygon points="850,12 856,16 850,20 844,16" fill="#E7BD54"/>

  <!-- Center Doctor Strange Magical Mandala Star -->
  <g class="rune">
    <circle cx="500" cy="16" r="14" fill="#071514" stroke="#E7BD54" stroke-width="1.5"/>
    <polygon points="500,4 511,16 500,28 489,16" fill="none" stroke="#00E6A0" stroke-width="1"/>
    <polygon points="508,8 508,24 492,24 492,8" fill="none" stroke="#FF9900" stroke-width="1"/>
  </g>
  <circle cx="500" cy="16" r="3" fill="#FFFFFF" filter="url(#portalGlow)"/>
</svg>"""

with open('assets/marvel/multiverse-divider.svg', 'w', encoding='utf-8') as f:
    f.write(multiverse_divider.strip())
print('Generated assets/marvel/multiverse-divider.svg')


# -------------------------------------------------------------
# 2. STARK INDUSTRIES COMMAND CONSOLE TELEMETRY SVG (820x240)
# -------------------------------------------------------------
stark_telemetry = """<svg xmlns="http://www.w3.org/2000/svg" width="820" height="240" viewBox="0 0 820 240">
  <defs>
    <filter id="starkGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <style>
    @keyframes arcSpin {
      0% { stroke-dashoffset: 260; transform: rotate(0deg); }
      50% { stroke-dashoffset: 60; transform: rotate(180deg); }
      100% { stroke-dashoffset: 260; transform: rotate(360deg); }
    }
    @keyframes pulseGlow {
      0%, 100% { opacity: 0.8; }
      50% { opacity: 1; filter: drop-shadow(0 0 6px #00C8E8); }
    }
    .arc-spin { transform-origin: 320px 150px; animation: arcSpin 5s ease-in-out infinite; }
    .glow-num { animation: pulseGlow 2.5s infinite; }
  </style>

  <!-- Container Box -->
  <rect x="2" y="2" width="816" height="236" rx="14" fill="#071514" stroke="#00C8E8" stroke-width="1.4"/>
  <rect x="6" y="6" width="808" height="228" rx="10" fill="none" stroke="#1A3B37" stroke-width="1"/>

  <!-- Header -->
  <g transform="translate(20, 24)">
    <circle cx="8" cy="8" r="5" fill="#00C8E8"/>
    <text x="22" y="12" font-family="Courier, monospace" font-size="12" font-weight="900" fill="#00C8E8" letter-spacing="1.5">STARK INDUSTRIES // TELEMETRY COMMAND CONSOLE</text>
    <text x="770" y="12" font-family="Courier, monospace" font-size="10" fill="#E7BD54" text-anchor="end">SYS-CLEARANCE: L8</text>
  </g>

  <!-- Top 4 Metric Pills -->
  <g transform="translate(20, 40)">
    <!-- Pill 1: Repos -->
    <rect x="0" y="0" width="185" height="42" rx="8" fill="#0A1E1D" stroke="#1A3B37"/>
    <text x="14" y="26" font-family="Courier, monospace" font-size="11" fill="#A5B8B2">Repositories</text>
    <text x="170" y="28" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="900" fill="#00E6A0" text-anchor="end" class="glow-num">45+</text>

    <!-- Pill 2: Stars -->
    <rect x="198" y="0" width="185" height="42" rx="8" fill="#0A1E1D" stroke="#1A3B37"/>
    <text x="212" y="26" font-family="Courier, monospace" font-size="11" fill="#A5B8B2">Total Stars</text>
    <text x="368" y="28" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="900" fill="#E7BD54" text-anchor="end" class="glow-num">250+</text>

    <!-- Pill 3: Followers -->
    <rect x="396" y="0" width="185" height="42" rx="8" fill="#0A1E1D" stroke="#1A3B37"/>
    <text x="410" y="26" font-family="Courier, monospace" font-size="11" fill="#A5B8B2">Followers</text>
    <text x="566" y="28" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="900" fill="#00C8E8" text-anchor="end" class="glow-num">100+</text>

    <!-- Pill 4: Contributions -->
    <rect x="594" y="0" width="185" height="42" rx="8" fill="#0A1E1D" stroke="#1A3B37"/>
    <text x="608" y="26" font-family="Courier, monospace" font-size="11" fill="#A5B8B2">Contributions</text>
    <text x="764" y="28" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="900" fill="#00E6A0" text-anchor="end" class="glow-num">1.2k+</text>
  </g>

  <!-- Lower Left Card: Stark Mission Analytics -->
  <g transform="translate(20, 94)">
    <rect width="383" height="130" rx="8" fill="#0A1E1D" stroke="#1A3B37"/>
    <text x="14" y="22" font-family="Courier, monospace" font-size="11" font-weight="800" fill="#00C8E8">◈ NEURAL NETWORK METRICS</text>
    
    <g transform="translate(14, 42)" font-family="Courier, monospace" font-size="11" fill="#E8F3F0">
      <text x="0" y="0">★ Reactor Stars:</text>       <text x="145" y="0" font-weight="bold" fill="#E7BD54">250+</text>
      <text x="0" y="20">⚡ Kernel Commits:</text>     <text x="145" y="20" font-weight="bold" fill="#00E6A0">1,200+</text>
      <text x="0" y="40">⑂ Multi-Agent PRs:</text>   <text x="145" y="40" font-weight="bold" fill="#00C8E8">45+</text>
      <text x="0" y="60">◎ Telemetry Issues:</text>   <text x="145" y="60" font-weight="bold" fill="#A5B8B2">30+</text>
      <text x="0" y="80">◈ Active Systems:</text>    <text x="145" y="80" font-weight="bold" fill="#00E6A0">25+ Repos</text>
    </g>

    <!-- Arc Reactor Core Ring Visualizer -->
    <g transform="translate(0, 0)">
      <circle cx="320" cy="74" r="36" stroke="#1A3B37" stroke-width="4" fill="#071514"/>
      <circle cx="320" cy="74" r="36" stroke="#00C8E8" stroke-width="4" stroke-dasharray="226" stroke-linecap="round" fill="none" class="arc-spin" filter="url(#starkGlow)"/>
      <polygon points="320,52 338,84 302,84" fill="none" stroke="#E7BD54" stroke-width="1.5"/>
      <circle cx="320" cy="74" r="7" fill="#00E6A0" filter="url(#starkGlow)"/>
    </g>
  </g>

  <!-- Lower Right Card: Language Arsenal Breakdown -->
  <g transform="translate(415, 94)">
    <rect width="383" height="130" rx="8" fill="#0A1E1D" stroke="#1A3B37"/>
    <text x="14" y="22" font-family="Courier, monospace" font-size="11" font-weight="800" fill="#E7BD54">◈ TECHNOLOGY ARSENAL RATIO</text>

    <!-- Language Bars -->
    <g transform="translate(14, 40)" font-family="Courier, monospace" font-size="10.5">
      <!-- Python -->
      <g transform="translate(0, 0)">
        <circle cx="4" cy="4" r="4" fill="#3572A5"/>
        <text x="16" y="8" fill="#E8F3F0">Python (PyTorch/LangGraph)</text>
        <rect x="220" y="2" width="100" height="7" rx="3.5" fill="#1A3B37"/>
        <rect x="220" y="2" width="62.8" height="7" rx="3.5" fill="#00E6A0"/>
        <text x="350" y="8" fill="#00E6A0" text-anchor="end" font-weight="bold">62.8%</text>
      </g>
      <!-- JavaScript -->
      <g transform="translate(0, 18)">
        <circle cx="4" cy="4" r="4" fill="#F1E05A"/>
        <text x="16" y="8" fill="#E8F3F0">JavaScript (WebGL2/Audio)</text>
        <rect x="220" y="2" width="100" height="7" rx="3.5" fill="#1A3B37"/>
        <rect x="220" y="2" width="14.1" height="7" rx="3.5" fill="#F1E05A"/>
        <text x="350" y="8" fill="#F1E05A" text-anchor="end" font-weight="bold">14.1%</text>
      </g>
      <!-- TypeScript -->
      <g transform="translate(0, 36)">
        <circle cx="4" cy="4" r="4" fill="#3178C6"/>
        <text x="16" y="8" fill="#E8F3F0">TypeScript (React19/ThreeJS)</text>
        <rect x="220" y="2" width="100" height="7" rx="3.5" fill="#1A3B37"/>
        <rect x="220" y="2" width="8.7" height="7" rx="3.5" fill="#00C8E8"/>
        <text x="350" y="8" fill="#00C8E8" text-anchor="end" font-weight="bold">8.7%</text>
      </g>
      <!-- HTML/CSS -->
      <g transform="translate(0, 54)">
        <circle cx="4" cy="4" r="4" fill="#E34C26"/>
        <text x="16" y="8" fill="#E8F3F0">Modern CSS/SVG HUDs</text>
        <rect x="220" y="2" width="100" height="7" rx="3.5" fill="#1A3B37"/>
        <rect x="220" y="2" width="5.1" height="7" rx="3.5" fill="#E7BD54"/>
        <text x="350" y="8" fill="#E7BD54" text-anchor="end" font-weight="bold">5.1%</text>
      </g>
      <!-- Other -->
      <g transform="translate(0, 72)">
        <circle cx="4" cy="4" r="4" fill="#89E051"/>
        <text x="16" y="8" fill="#E8F3F0">Other (SQL, C++, GLSL)</text>
        <rect x="220" y="2" width="100" height="7" rx="3.5" fill="#1A3B37"/>
        <rect x="220" y="2" width="9.3" height="7" rx="3.5" fill="#A5B8B2"/>
        <text x="350" y="8" fill="#A5B8B2" text-anchor="end" font-weight="bold">9.3%</text>
      </g>
    </g>
  </g>
</svg>"""

with open('assets/marvel/stark-telemetry.svg', 'w', encoding='utf-8') as f:
    f.write(stark_telemetry.strip())
print('Generated assets/marvel/stark-telemetry.svg')


# -------------------------------------------------------------
# 3. PROJECT CARD: A.R.C.A.N.E. / IRON-MAN GESTURES (660x280)
# -------------------------------------------------------------
card_arcane = f"""<svg xmlns="http://www.w3.org/2000/svg" width="660" height="280" viewBox="0 0 660 280">
  <defs>
    <filter id="arcaneGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <style>
    @keyframes hudPulse {{
      0%, 100% {{ stroke-opacity: 0.6; }}
      50% {{ stroke-opacity: 1; filter: drop-shadow(0 0 5px #00C8E8); }}
    }}
    .border-arcane {{ animation: hudPulse 3.5s infinite ease-in-out; }}
  </style>

  <!-- Container Box -->
  <rect x="2" y="2" width="656" height="276" rx="14" fill="#071514" stroke="#00C8E8" stroke-width="1.4" class="border-arcane"/>

  <!-- Left: High-Res Project Thumbnail -->
  <g transform="translate(24, 24)">
    <rect width="228" height="228" rx="12" fill="#0A1E1D" stroke="#1A3B37"/>
    <image href="{arcane_b64}" x="2" y="2" width="224" height="224" rx="10" preserveAspectRatio="xMidYMid slice"/>
    <rect x="2" y="2" width="224" height="224" rx="10" fill="none" stroke="#00C8E8" stroke-width="1.2" stroke-opacity="0.6"/>
    <!-- Arc Reactor Badge -->
    <circle cx="204" cy="204" r="16" fill="#0A1E1D" stroke="#00C8E8" stroke-width="1.5"/>
    <polygon points="204,194 212,208 196,208" fill="#E7BD54"/>
  </g>

  <!-- Right: Metadata & Content -->
  <g transform="translate(274, 34)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="900" fill="#E8F3F0">A.R.C.A.N.E. / J.A.R.V.I.S.</text>
    <text x="0" y="20" font-family="Courier, monospace" font-size="12" font-weight="bold" fill="#00C8E8">Holographic Wearables &amp; HUD Engine</text>

    <!-- Description -->
    <text x="0" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">Real-time computer-vision controlled</text>
    <text x="0" y="66" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">holographic superhero HUDs, nanotech armor</text>
    <text x="0" y="84" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">deployment &amp; mystic arts mechanics at 60 FPS.</text>

    <!-- Tech Badges -->
    <g transform="translate(0, 110)">
      <rect x="0" y="0" width="80" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="40" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">MediaPipe</text>
      
      <rect x="86" y="0" width="76" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="124" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00C8E8" text-anchor="middle">WebGL2</text>
      
      <rect x="168" y="0" width="76" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="206" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#E7BD54" text-anchor="middle">Three.js</text>
      
      <rect x="250" y="0" width="72" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="286" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">WebGPU</text>
    </g>

    <!-- Action Buttons -->
    <g transform="translate(0, 154)">
      <rect x="0" y="0" width="124" height="32" rx="16" fill="#00C8E8"/>
      <text x="62" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="800" fill="#050B0B" text-anchor="middle">View Repo →</text>
      
      <rect x="134" y="0" width="120" height="32" rx="16" fill="#071514" stroke="#00C8E8" stroke-width="1.2"/>
      <text x="194" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" text-anchor="middle">Interactive Demo</text>
    </g>
  </g>
</svg>"""

with open('assets/marvel/card-arcane.svg', 'w', encoding='utf-8') as f:
    f.write(card_arcane.strip())
print('Generated assets/marvel/card-arcane.svg')

print('All Marvel assets generated successfully!')
