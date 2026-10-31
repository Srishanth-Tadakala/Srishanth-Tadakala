footer_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="48" viewBox="0 0 1000 48">
  <defs>
    <filter id="footGlow" x="-5%" y="-20%" width="110%" height="140%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Top Line -->
  <line x1="20" y1="4" x2="980" y2="4" stroke="#1A3B37" stroke-width="1"/>

  <!-- Left: Pillar Emblem -->
  <g transform="translate(24, 12)">
    <rect x="0" y="16" width="22" height="3" rx="1" fill="#E7BD54"/>
    <rect x="2" y="19" width="18" height="2" rx="0.5" fill="#E7BD54"/>
    <rect x="2" y="5" width="3" height="11" fill="#E7BD54"/>
    <rect x="7" y="5" width="3" height="11" fill="#E7BD54"/>
    <rect x="12" y="5" width="3" height="11" fill="#E7BD54"/>
    <rect x="17" y="5" width="3" height="11" fill="#E7BD54"/>
    <rect x="0" y="3" width="22" height="2" rx="0.5" fill="#E7BD54"/>
    <polygon points="11,0 0,3 22,3" fill="#E7BD54"/>
  </g>

  <!-- Left Quote -->
  <text x="56" y="24" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-style="italic" fill="#E7BD54">"Build. Explore. Learn. Share. Evolve."</text>
  <text x="286" y="24" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="10" font-weight="700" fill="#A5B8B2" letter-spacing="0.5">— SRISHANTH TADAKALA</text>

  <!-- Right Quote -->
  <text x="976" y="24" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" fill="#A5B8B2" text-anchor="end">A better future is built by people who keep learning.</text>

  <!-- Bottom Mystic Geometry Pattern -->
  <path d="M420 38 L460 38 L480 32 L500 42 L520 32 L540 38 L580 38" fill="none" stroke="#00E6A0" stroke-width="1.2" stroke-opacity="0.7" filter="url(#footGlow)"/>
</svg>"""

with open('assets/footer.svg', 'w', encoding='utf-8') as f:
    f.write(footer_svg.strip())

print('Generated assets/footer.svg successfully')

