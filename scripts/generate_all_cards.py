import os
import base64
import random

os.makedirs('assets', exist_ok=True)
os.makedirs('assets/marvel', exist_ok=True)

def img_to_b64(path):
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().replace('.', '')
    if ext == 'jpg': ext = 'jpeg'
    with open(path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/{ext};base64,{data}"

avatar_b64 = img_to_b64('assets/avatar.png')
sylvie_b64 = img_to_b64('assets/project-sylvie.png')
friday_b64 = img_to_b64('assets/project-friday.png')
queue_b64 = img_to_b64('assets/project-queueless.png')

# 1. CYBER HEADER ANIMATED
cyber_header = """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="70" viewBox="0 0 1000 70">
  <defs>
    <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>
  <style>
    @keyframes pulseGlow {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; filter: drop-shadow(0 0 6px #00C8E8); }
    }
    @keyframes blink {
      0%, 49% { opacity: 1; }
      50%, 100% { opacity: 0; }
    }
    .hud-frame { animation: pulseGlow 4s infinite ease-in-out; }
    .cursor { animation: blink 0.8s infinite; }
  </style>
  <rect x="2" y="2" width="996" height="66" rx="12" fill="#071514" stroke="#00C8E8" stroke-width="1.5" class="hud-frame" />
  <path d="M14 8 H8 V18" stroke="#00C8E8" stroke-width="2.5" fill="none" />
  <path d="M986 8 H992 V18" stroke="#00C8E8" stroke-width="2.5" fill="none" />
  <path d="M14 62 H8 V52" stroke="#00C8E8" stroke-width="2.5" fill="none" />
  <path d="M986 62 H992 V52" stroke="#00C8E8" stroke-width="2.5" fill="none" />
  <circle cx="28" cy="35" r="5" fill="#00E6A0" filter="url(#neonGlow)">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.8s" repeatCount="indefinite" />
  </circle>
  <text x="42" y="39" font-family="Courier, monospace" font-size="12" font-weight="bold" fill="#00E6A0" letter-spacing="1.5">TELEMETRY: ONLINE</text>
  <text x="195" y="39" font-family="Courier, monospace" font-size="11" fill="#527068">|</text>
  <g transform="translate(215, 39)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace" font-size="13" font-weight="700" fill="#E8F3F0" letter-spacing="0.5">
      srishanth@stark-console:~$ <tspan fill="#00C8E8">python -m ai_agents.orchestrate --protocol=multiverse</tspan>
    </text>
    <rect x="670" y="-12" width="8" height="15" fill="#00E6A0" class="cursor" />
  </g>
  <rect x="880" y="22" width="100" height="26" rx="6" fill="#0A1E1D" stroke="#1A3B37" />
  <text x="930" y="39" font-family="Courier, monospace" font-size="10" font-weight="bold" fill="#E7BD54" text-anchor="middle">STARK v3.2</text>
</svg>"""
with open('assets/cyber-header-animated.svg', 'w', encoding='utf-8') as f:
    f.write(cyber_header.strip())

# 2. CARD ABOUT SVG
about_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="212" viewBox="0 0 600 212">
  <defs>
    <filter id="aboutGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect x="2" y="2" width="596" height="208" rx="14" fill="#071514" stroke="#00C8E8" stroke-width="1.2"/>
  <g transform="translate(20, 24)">
    <circle cx="8" cy="8" r="5" fill="#00C8E8"/>
    <text x="22" y="12" font-family="Courier, monospace" font-size="12" font-weight="900" fill="#00C8E8" letter-spacing="1">STARK PERSONNEL INTELLIGENCE DOSSIER</text>
  </g>
  <g transform="translate(22, 42)">
    <rect width="90" height="154" rx="12" fill="#0A1E1D" stroke="#00C8E8" stroke-width="1.5"/>
    <image href="{avatar_b64}" x="4" y="4" width="82" height="146" rx="8" preserveAspectRatio="xMidYMid slice"/>
    <path d="M4 14 H10 M4 4 V10" stroke="#00C8E8" stroke-width="1.5" fill="none"/>
    <path d="M86 14 H80 M86 4 V10" stroke="#00C8E8" stroke-width="1.5" fill="none"/>
    <path d="M4 144 H10 M4 150 V144" stroke="#00C8E8" stroke-width="1.5" fill="none"/>
    <path d="M86 144 H80 M86 150 V144" stroke="#00C8E8" stroke-width="1.5" fill="none"/>
  </g>
  <g transform="translate(126, 44)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11">
    <text x="0" y="10" fill="#E7BD54">🎓</text>
    <text x="18" y="10" font-weight="700" fill="#E8F3F0">Student @ Marwadi University</text>
    <text x="0" y="32" fill="#00E6A0">🎯</text>
    <text x="18" y="32" fill="#A5B8B2">CSE (AI/ML) | 2nd Year (Lateral)</text>
    <text x="0" y="54" fill="#E7BD54">📜</text>
    <text x="18" y="54" fill="#A5B8B2">Diploma in CSE — <tspan font-weight="bold" fill="#00E6A0">9.23 CGPA</tspan></text>
    <text x="0" y="76" fill="#00C8E8">📍</text>
    <text x="18" y="76" fill="#A5B8B2">From Chennur, Telangana, India</text>
    <text x="0" y="98" fill="#00E6A0">💡</text>
    <text x="18" y="98" font-weight="600" fill="#00E6A0">Autonomous Agents • Voice AI • RAG</text>
    <text x="0" y="120" fill="#00C8E8">🤝</text>
    <text x="18" y="120" font-weight="600" fill="#E8F3F0">Open Source Contributor • Level 8 Clearance</text>
  </g>
  <g transform="translate(126, 185)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-style="italic" fill="#00C8E8">"Turning ideas into intelligent systems that solve real-world problems."</text>
  </g>
</svg>"""
with open('assets/card-about.svg', 'w', encoding='utf-8') as f:
    f.write(about_svg.strip())

# 3. CARD SYLVIE SVG
card_sylvie = f"""<svg xmlns="http://www.w3.org/2000/svg" width="660" height="280" viewBox="0 0 660 280">
  <rect x="2" y="2" width="656" height="276" rx="14" fill="#071514" stroke="#00E6A0" stroke-width="1.4"/>
  <g transform="translate(24, 24)">
    <rect width="228" height="228" rx="12" fill="#0A1E1D" stroke="#1A3B37"/>
    <image href="{sylvie_b64}" x="2" y="2" width="224" height="224" rx="10" preserveAspectRatio="xMidYMid slice"/>
    <rect x="2" y="2" width="224" height="224" rx="10" fill="none" stroke="#00E6A0" stroke-width="1.2" stroke-opacity="0.6"/>
  </g>
  <g transform="translate(274, 34)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="900" fill="#E8F3F0">Sylvie V1 — Voice AI Companion</text>
    <text x="0" y="20" font-family="Courier, monospace" font-size="12" font-weight="bold" fill="#00E6A0">Next-Gen J.A.R.V.I.S. Protocol</text>
    <text x="0" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">Voice-first conversational intelligence with sub-150ms</text>
    <text x="0" y="66" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">barge-in, unified dialogue engine, and persistent</text>
    <text x="0" y="84" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">pgvector semantic memory.</text>
    <g transform="translate(0, 110)">
      <rect x="0" y="0" width="80" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="40" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">AI Agents</text>
      <rect x="86" y="0" width="76" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="124" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">Voice AI</text>
      <rect x="168" y="0" width="56" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="196" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">RAG</text>
      <rect x="230" y="0" width="70" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="265" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">Memory</text>
    </g>
    <g transform="translate(0, 154)">
      <rect x="0" y="0" width="124" height="32" rx="16" fill="#00E6A0"/>
      <text x="62" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="800" fill="#050B0B" text-anchor="middle">View Repo →</text>
      <rect x="134" y="0" width="110" height="32" rx="16" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
      <text x="189" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" text-anchor="middle">Live Demo</text>
    </g>
  </g>
</svg>"""
with open('assets/card-sylvie.svg', 'w', encoding='utf-8') as f:
    f.write(card_sylvie.strip())

# 4. CARD FRIDAY SVG
card_friday = f"""<svg xmlns="http://www.w3.org/2000/svg" width="660" height="280" viewBox="0 0 660 280">
  <rect x="2" y="2" width="656" height="276" rx="14" fill="#071514" stroke="#00C8E8" stroke-width="1.4"/>
  <g transform="translate(24, 24)">
    <rect width="228" height="228" rx="12" fill="#0A1E1D" stroke="#1A3B37"/>
    <image href="{friday_b64}" x="2" y="2" width="224" height="224" rx="10" preserveAspectRatio="xMidYMid slice"/>
    <rect x="2" y="2" width="224" height="224" rx="10" fill="none" stroke="#00C8E8" stroke-width="1.2" stroke-opacity="0.6"/>
  </g>
  <g transform="translate(274, 34)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="900" fill="#E8F3F0">F.R.I.D.A.Y. / DTIARS</text>
    <text x="0" y="20" font-family="Courier, monospace" font-size="12" font-weight="bold" fill="#00C8E8">Antarctic Digital Twin Protocol</text>
    <text x="0" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">Multi-agent industrial platform for remote telemetry,</text>
    <text x="0" y="66" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">predictive anomaly detection, and automated operations</text>
    <text x="0" y="84" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">of Indian Antarctic Research Stations.</text>
    <g transform="translate(0, 110)">
      <rect x="0" y="0" width="84" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="42" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00C8E8" text-anchor="middle">Digital Twin</text>
      <rect x="90" y="0" width="46" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="113" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00C8E8" text-anchor="middle">IoT</text>
      <rect x="142" y="0" width="76" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="180" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00C8E8" text-anchor="middle">AI Agents</text>
      <rect x="224" y="0" width="48" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="248" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00C8E8" text-anchor="middle">SHI</text>
    </g>
    <g transform="translate(0, 154)">
      <rect x="0" y="0" width="124" height="32" rx="16" fill="#00E6A0"/>
      <text x="62" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="800" fill="#050B0B" text-anchor="middle">View Repo →</text>
      <rect x="134" y="0" width="134" height="32" rx="16" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
      <text x="201" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" text-anchor="middle">Documentation</text>
    </g>
  </g>
</svg>"""
with open('assets/card-friday.svg', 'w', encoding='utf-8') as f:
    f.write(card_friday.strip())

# 5. CARD QUEUELESS SVG
card_queue = f"""<svg xmlns="http://www.w3.org/2000/svg" width="660" height="280" viewBox="0 0 660 280">
  <rect x="2" y="2" width="656" height="276" rx="14" fill="#071514" stroke="#00E6A0" stroke-width="1.4"/>
  <g transform="translate(24, 24)">
    <rect width="228" height="228" rx="12" fill="#0A1E1D" stroke="#1A3B37"/>
    <image href="{queue_b64}" x="2" y="2" width="224" height="224" rx="10" preserveAspectRatio="xMidYMid slice"/>
    <rect x="2" y="2" width="224" height="224" rx="10" fill="none" stroke="#00E6A0" stroke-width="1.2" stroke-opacity="0.6"/>
  </g>
  <g transform="translate(274, 34)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="900" fill="#E8F3F0">QueueLess — Smart Queue Management</text>
    <text x="0" y="20" font-family="Courier, monospace" font-size="12" font-weight="bold" fill="#00C8E8">Distributed Reactive Token Engine</text>
    <text x="0" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">Local-first reactive SPA with zero cloud subscriptions,</text>
    <text x="0" y="66" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">BroadcastChannel cross-tab synchronization, and 115</text>
    <text x="0" y="84" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11.5" fill="#A5B8B2">passing automated regression tests.</text>
    <g transform="translate(0, 110)">
      <rect x="0" y="0" width="80" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="40" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">Full Stack</text>
      <rect x="86" y="0" width="76" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="124" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">Real-time</text>
      <rect x="168" y="0" width="74" height="22" rx="6" fill="#0A1E1D" stroke="#1A3B37"/>
      <text x="205" y="15" font-family="Courier, monospace" font-size="9" font-weight="bold" fill="#00E6A0" text-anchor="middle">Analytics</text>
    </g>
    <g transform="translate(0, 154)">
      <rect x="0" y="0" width="124" height="32" rx="16" fill="#00E6A0"/>
      <text x="62" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="800" fill="#050B0B" text-anchor="middle">View Repo →</text>
      <rect x="134" y="0" width="110" height="32" rx="16" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
      <text x="189" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" fill="#E8F3F0" text-anchor="middle">Live Demo</text>
    </g>
  </g>
</svg>"""
with open('assets/card-queueless.svg', 'w', encoding='utf-8') as f:
    f.write(card_queue.strip())

# 6. CARD ACHIEVEMENTS SVG
achieve_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="770" height="212" viewBox="0 0 770 212">
  <rect x="2" y="2" width="766" height="208" rx="14" fill="#071514" stroke="#E7BD54" stroke-width="1.4"/>
  <g transform="translate(20, 24)">
    <circle cx="8" cy="8" r="5" fill="#E7BD54"/>
    <text x="22" y="12" font-family="Courier, monospace" font-size="12" font-weight="900" fill="#E7BD54" letter-spacing="1">AVENGERS MISSION ARCHIVES // ACHIEVEMENTS</text>
  </g>
  <g transform="translate(30, 56)">
    <g transform="translate(0, 0)">
      <polygon points="40,5 75,25 75,65 40,85 5,65 5,25" fill="#0A1E1D" stroke="#4285F4" stroke-width="2"/>
      <text x="40" y="50" font-size="20" text-anchor="middle" fill="#4285F4">☁️</text>
      <text x="40" y="105" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="bold" fill="#E8F3F0" text-anchor="middle">Google Cloud</text>
      <text x="40" y="120" font-family="Courier, monospace" font-size="9" fill="#4285F4" text-anchor="middle">Skills Badges</text>
    </g>
    <g transform="translate(145, 0)">
      <polygon points="40,5 75,25 75,65 40,85 5,65 5,25" fill="#0A1E1D" stroke="#E7BD54" stroke-width="2"/>
      <text x="40" y="50" font-size="20" text-anchor="middle" fill="#E7BD54">🏆</text>
      <text x="40" y="105" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="bold" fill="#E8F3F0" text-anchor="middle">Hackathons</text>
      <text x="40" y="120" font-family="Courier, monospace" font-size="9" fill="#E7BD54" text-anchor="middle">AI Prototyper</text>
    </g>
    <g transform="translate(290, 0)">
      <polygon points="40,5 75,25 75,65 40,85 5,65 5,25" fill="#0A1E1D" stroke="#00E6A0" stroke-width="2"/>
      <text x="40" y="50" font-family="Courier, monospace" font-size="18" font-weight="bold" text-anchor="middle" fill="#00E6A0">&lt;/&gt;</text>
      <text x="40" y="105" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="bold" fill="#E8F3F0" text-anchor="middle">Open Source</text>
      <text x="40" y="120" font-family="Courier, monospace" font-size="9" fill="#00E6A0" text-anchor="middle">Maintainer</text>
    </g>
    <g transform="translate(435, 0)">
      <polygon points="40,5 75,25 75,65 40,85 5,65 5,25" fill="#0A1E1D" stroke="#FF5722" stroke-width="2"/>
      <text x="40" y="50" font-size="20" text-anchor="middle" fill="#FF5722">🎯</text>
      <text x="40" y="105" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="bold" fill="#E8F3F0" text-anchor="middle">Problem Solver</text>
      <text x="40" y="120" font-family="Courier, monospace" font-size="9" fill="#FF5722" text-anchor="middle">DSA &amp; Logic</text>
    </g>
    <g transform="translate(580, 0)">
      <polygon points="40,5 75,25 75,65 40,85 5,65 5,25" fill="#0A1E1D" stroke="#00C8E8" stroke-width="2"/>
      <text x="40" y="52" font-size="22" font-weight="bold" text-anchor="middle" fill="#00C8E8">∞</text>
      <text x="40" y="105" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="bold" fill="#E8F3F0" text-anchor="middle">Continuous</text>
      <text x="40" y="120" font-family="Courier, monospace" font-size="9" fill="#00C8E8" text-anchor="middle">Learner</text>
    </g>
  </g>
</svg>"""
with open('assets/card-achievements.svg', 'w', encoding='utf-8') as f:
    f.write(achieve_svg.strip())

# 7. CARD NOW PLAYING SVG (28-BAR EQUALIZER)
bars_svg = []
for i in range(28):
    x = 210 + i * 11
    h_min = random.randint(4, 10)
    h_max = random.randint(22, 54)
    dur = round(random.uniform(0.6, 1.4), 2)
    delay = round(random.uniform(0.0, 0.9), 2)
    bars_svg.append(f'<rect x="{x}" y="35" width="6" rx="3" fill="#00E6A0" opacity="0.85"><animate attributeName="height" values="{h_min};{h_max};{h_min}" dur="{dur}s" begin="{delay}s" repeatCount="indefinite" /><animate attributeName="y" values="{75 - h_min};{75 - h_max};{75 - h_min}" dur="{dur}s" begin="{delay}s" repeatCount="indefinite" /><animate attributeName="fill" values="#00E6A0;#00C8E8;#00E6A0" dur="{dur*2}s" repeatCount="indefinite" /></rect>')

now_playing = f"""<svg xmlns="http://www.w3.org/2000/svg" width="668" height="212" viewBox="0 0 668 212">
  <rect x="2" y="2" width="664" height="208" rx="14" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
  <g transform="translate(20, 26)">
    <path d="M4 12 V16 M8 8 V20 M12 4 V24 M16 9 V19 M20 13 V15" stroke="#00E6A0" stroke-width="2" stroke-linecap="round"/>
    <text x="32" y="17" font-family="Courier, monospace" font-size="12" font-weight="900" fill="#00E6A0" letter-spacing="1">STARK AUDIO // FLOW STATE UPLINK</text>
  </g>
  <g transform="translate(24, 52)">
    <rect width="96" height="96" rx="10" fill="#0A1E1D" stroke="#1A3B37"/>
    <image href="{avatar_b64}" x="4" y="4" width="88" height="88" rx="8" preserveAspectRatio="xMidYMid slice"/>
    <rect x="4" y="4" width="88" height="88" rx="8" fill="none" stroke="#00C8E8" stroke-width="1" stroke-opacity="0.6"/>
  </g>
  <g transform="translate(136, 68)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="800" fill="#E8F3F0">Chasing Ideas Not People</text>
    <text x="0" y="22" font-family="Courier, monospace" font-size="12" fill="#00C8E8" font-weight="bold">LoFi • Deep Focus • System Build</text>
  </g>
  <g transform="translate(136, 95)">
    <line x1="0" y1="20" x2="480" y2="20" stroke="#1A3B37" stroke-width="1"/>
    {''.join(bars_svg)}
  </g>
  <g transform="translate(136, 170)">
    <line x1="0" y1="0" x2="440" y2="0" stroke="#1A3B37" stroke-width="4" stroke-linecap="round"/>
    <line x1="0" y1="0" x2="265" y2="0" stroke="#00C8E8" stroke-width="4" stroke-linecap="round"/>
    <circle cx="265" cy="0" r="5" fill="#00E6A0"/>
    <text x="495" y="4" font-family="Courier, monospace" font-size="11" font-weight="bold" fill="#A5B8B2" text-anchor="end">2:31 / 4:12</text>
  </g>
  <g transform="translate(615, 95)">
    <circle cx="16" cy="16" r="16" fill="#0A1E1D" stroke="#00E6A0" stroke-width="1.5"/>
    <polygon points="13,10 23,16 13,22" fill="#00E6A0"/>
  </g>
</svg>"""
with open('assets/card-now-playing.svg', 'w', encoding='utf-8') as f:
    f.write(now_playing.strip())

# 8. CARD STREAK SVG (HEATMAP & FLAME)
heatmap_cells = []
colors = ["#071514", "#0E3A2F", "#008A5E", "#00B87A", "#00E6A0"]
random.seed(42)
for col in range(22):
    for row in range(5):
        cx = 24 + col * 11
        cy = 82 + row * 11
        c = random.choices(colors, weights=[5, 10, 25, 35, 25])[0]
        heatmap_cells.append(f'<rect x="{cx}" y="{cy}" width="8" height="8" rx="2" fill="{c}"/>')

streak_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="586" height="212" viewBox="0 0 586 212">
  <rect x="2" y="2" width="582" height="208" rx="14" fill="#071514" stroke="#00E6A0" stroke-width="1.2"/>
  <g transform="translate(20, 24)">
    <circle cx="8" cy="8" r="5" fill="#00E6A0"/>
    <text x="22" y="12" font-family="Courier, monospace" font-size="12" font-weight="900" fill="#00E6A0" letter-spacing="1">STARK CONSECUTIVE CODING CADENCE</text>
  </g>
  <g transform="translate(22, 44)">
    <path d="M12 2C12 2 16 7 16 11C16 14 13.5 17 10 17C6.5 17 4 14 4 11C4 8 7 5 7 5C7 5 6 9 8 10C10 11 12 9 12 2Z" fill="#FFA500"/>
    <text x="28" y="16" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="22" font-weight="900" fill="#E8F3F0">45 Days</text>
    <text x="135" y="14" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" fill="#A5B8B2">Longer coding sessions for a better future.</text>
  </g>
  <g transform="translate(0, 0)">{''.join(heatmap_cells)}</g>
  <g transform="translate(24, 76)" font-family="Courier, monospace" font-size="8.5" fill="#527068">
    <text x="0">Jan</text><text x="44">Mar</text><text x="88">May</text><text x="132">Jul</text><text x="176">Sep</text><text x="210">Nov</text>
  </g>
  <g transform="translate(24, 146)">
    <text x="0" y="8" font-family="Courier, monospace" font-size="9" fill="#527068">Less</text>
    <rect x="28" y="0" width="8" height="8" rx="2" fill="#071514" stroke="#1A3B37"/>
    <rect x="40" y="0" width="8" height="8" rx="2" fill="#0E3A2F"/>
    <rect x="52" y="0" width="8" height="8" rx="2" fill="#008A5E"/>
    <rect x="64" y="0" width="8" height="8" rx="2" fill="#00B87A"/>
    <rect x="76" y="0" width="8" height="8" rx="2" fill="#00E6A0"/>
    <text x="92" y="8" font-family="Courier, monospace" font-size="9" fill="#527068">More</text>
  </g>
  <g transform="translate(290, 150)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-style="italic" fill="#E7BD54">"Discipline today</text>
    <text x="0" y="14" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-style="italic" fill="#E7BD54">Creates the freedom of tomorrow."</text>
  </g>
</svg>"""
with open('assets/card-streak.svg', 'w', encoding='utf-8') as f:
    f.write(streak_svg.strip())

print('All supplementary cards generated successfully!')
