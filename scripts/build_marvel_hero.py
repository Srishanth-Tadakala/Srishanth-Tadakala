import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

os.makedirs('assets/marvel', exist_ok=True)

TARGET_W, TARGET_H = 2000, 480
bg_path = 'assets/marvel/hero-backdrop.jpg'

if os.path.exists(bg_path):
    bg = Image.open(bg_path)
    # Resize and crop to 2000x480
    bg_w, bg_h = bg.size
    scale = max(TARGET_W / bg_w, TARGET_H / bg_h)
    new_w, new_h = int(bg_w * scale), int(bg_h * scale)
    bg_resized = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Center crop
    left = (new_w - TARGET_W) // 2
    top = (new_h - TARGET_H) // 2
    canvas = bg_resized.crop((left, top, left + TARGET_W, top + TARGET_H))
else:
    canvas = Image.new('RGB', (TARGET_W, TARGET_H), (5, 11, 15))

# Darken slightly with a dark tech gradient for text contrast on left
overlay = Image.new('RGBA', (TARGET_W, TARGET_H), (0, 0, 0, 0))
draw_ol = ImageDraw.Draw(overlay)

# Gradient from left (darker for readability) to right (transparent to show Arc Reactor/portal)
for x in range(TARGET_W):
    if x < 1100:
        alpha = int(220 - (x / 1100) * 110) # 220 down to 110
    else:
        alpha = int(110 - ((x - 1100) / 900) * 80) # 110 down to 30
    draw_ol.line([(x, 0), (x, TARGET_H)], fill=(4, 9, 14, alpha))

canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay)
draw = ImageDraw.Draw(canvas)

# 1. Subtle Horizontal Tech Grid & Scanlines
for y in range(0, TARGET_H, 4):
    draw.line([(0, y), (TARGET_W, y)], fill=(0, 200, 232, 8), width=1)

# 2. Outer Futuristic Border with Tech Accents
border_col = (0, 230, 160, 240) # Emerald neon
cyan_col = (0, 200, 232, 255)
gold_col = (231, 189, 84, 255)
white_col = (232, 243, 240, 255)
muted_col = (165, 184, 178, 255)

# Outer border
draw.rounded_rectangle([(4, 4), (TARGET_W - 4, TARGET_H - 4)], radius=16, outline=cyan_col, width=2)
# Inner accent border
draw.rounded_rectangle([(8, 8), (TARGET_W - 8, TARGET_H - 8)], radius=12, outline=(10, 45, 60, 180), width=1)

# Corner Tech Brackets (Stark HUD)
bracket_len = 36
draw.line([(14, 14), (14 + bracket_len, 14)], fill=border_col, width=3)
draw.line([(14, 14), (14, 14 + bracket_len)], fill=border_col, width=3)

draw.line([(TARGET_W - 14, 14), (TARGET_W - 14 - bracket_len, 14)], fill=border_col, width=3)
draw.line([(TARGET_W - 14, 14), (TARGET_W - 14, 14 + bracket_len)], fill=border_col, width=3)

draw.line([(14, TARGET_H - 14), (14 + bracket_len, TARGET_H - 14)], fill=border_col, width=3)
draw.line([(14, TARGET_H - 14), (14, TARGET_H - 14 - bracket_len)], fill=border_col, width=3)

draw.line([(TARGET_W - 14, TARGET_H - 14), (TARGET_W - 14 - bracket_len, TARGET_H - 14)], fill=border_col, width=3)
draw.line([(TARGET_W - 14, TARGET_H - 14), (TARGET_W - 14, TARGET_H - 14 - bracket_len)], fill=border_col, width=3)

# 3. Load Fonts
def get_font(size, bold=True):
    font_names = [
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\consola.ttf"
    ]
    for fn in font_names:
        if os.path.exists(fn):
            try:
                return ImageFont.truetype(fn, size)
            except:
                pass
    return ImageFont.load_default()

font_kicker = get_font(18, bold=True)
font_title = get_font(74, bold=True)
font_subtitle = get_font(26, bold=True)
font_quote = get_font(22, bold=False)
font_meta = get_font(16, bold=True)
font_phil = get_font(20, bold=True)

# 4. Render Text Elements
# Header Tactical Line
draw.text((72, 48), "STARK INDUSTRIES // AUTONOMOUS SYSTEMS ARCHITECTURE", font=font_kicker, fill=cyan_col)
draw.text((680, 48), "• PROTOCOL: MULTIVERSE", font=font_kicker, fill=gold_col)

# Main Title: SRISHANTH TADAKALA (Dual layer glow)
for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
    draw.text((72 + dx, 82 + dy), "SRISHANTH TADAKALA", font=font_title, fill=(0, 100, 130, 140))
draw.text((72, 82), "SRISHANTH TADAKALA", font=font_title, fill=white_col)

# Subtitle Pill: > AI/ML SYSTEMS ARCHITECT
pill_x, pill_y = 72, 192
pill_w, pill_h = 580, 50
draw.rounded_rectangle([(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)], radius=10, 
                       fill=(8, 24, 32, 220), outline=border_col, width=2)
# glowing dot
draw.ellipse([(pill_x + 18, pill_y + 19), (pill_x + 30, pill_y + 31)], fill=border_col)
draw.text((pill_x + 42, pill_y + 10), "> AI/ML SYSTEMS ARCHITECT", font=font_subtitle, fill=border_col)

# Tagline Quote
draw.text((72, 270), '"Turning ideas into intelligent systems that solve real-world problems."', font=font_quote, fill=gold_col)

# Tactical Specs / Clearance Box
specs_y = 330
specs_items = [
    ("CLEARANCE: LEVEL 8", cyan_col),
    ("DIVISION: AUTONOMOUS AGENTS & VOICE AI", border_col),
    ("SYSTEM STATUS: OPERATIONAL", gold_col)
]
cur_x = 72
for label, col in specs_items:
    bbox = font_meta.getbbox(label)
    item_w = (bbox[2] - bbox[0]) + 28
    draw.rounded_rectangle([(cur_x, specs_y), (cur_x + item_w, specs_y + 36)], radius=6, 
                           fill=(6, 18, 24, 200), outline=(20, 60, 80, 220), width=1)
    draw.text((cur_x + 14, specs_y + 8), label, font=font_meta, fill=col)
    cur_x += item_w + 14

# Bottom Philosophy Banner
draw.text((72, 400), "BUILD • EXPLORE • LEARN • SHARE • EVOLVE", font=font_phil, fill=(0, 230, 160, 200))
draw.text((680, 400), "// MARVEL-INSPIRED COMMAND CONSOLE v3.0", font=font_meta, fill=(100, 140, 150, 180))

# Save enhanced hero banner
output_hero = 'assets/marvel/marvel-hero.png'
canvas.convert('RGB').save(output_hero, quality=95, optimize=True)
print(f"Hero banner created at {output_hero} ({os.path.getsize(output_hero) / 1024:.1f} KB)")
