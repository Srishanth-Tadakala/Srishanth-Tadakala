import math
import os
from PIL import Image, ImageDraw

os.makedirs('assets/marvel', exist_ok=True)

WIDTH, HEIGHT = 320, 320
NUM_FRAMES = 36
CENTER = (WIDTH // 2, HEIGHT // 2)

frames = []

for frame_idx in range(NUM_FRAMES):
    progress = frame_idx / NUM_FRAMES
    angle = progress * 2 * math.pi

    im = Image.new('RGBA', (WIDTH, HEIGHT), (5, 8, 12, 255))
    draw = ImageDraw.Draw(im)

    # 1. Cosmic event horizon inside portal
    pulse = 0.5 + 0.5 * math.sin(progress * 2 * math.pi)
    core_rad = int(75 + 4 * pulse)
    # Deep purple & cosmic cyan core
    for r, col in [(core_rad + 20, (30, 10, 50, 60)), (core_rad + 10, (10, 30, 60, 100)), (core_rad, (15, 45, 75, 180)), (core_rad - 20, (5, 15, 30, 220))]:
        draw.ellipse([CENTER[0] - r, CENTER[1] - r, CENTER[0] + r, CENTER[1] + r], fill=col)

    # Central stars
    import random
    random.seed(999)
    for _ in range(30):
        sx = CENTER[0] + random.randint(-55, 55)
        sy = CENTER[1] + random.randint(-55, 55)
        if math.hypot(sx - CENTER[0], sy - CENTER[1]) < 55:
            b = random.randint(150, 255)
            draw.point((sx, sy), fill=(b, b, 255, 255))

    # 2. Geometric Mandala Rings (Doctor Strange Magic)
    # Inner octagram (8 points)
    for rot, col in [(angle * 0.8, (255, 150, 30, 180)), (-angle * 0.8, (255, 200, 50, 180))]:
        points = []
        for i in range(16):
            pt_ang = (i / 16) * 2 * math.pi + rot
            r = 78 if i % 2 == 0 else 64
            points.append((CENTER[0] + r * math.cos(pt_ang), CENTER[1] + r * math.sin(pt_ang)))
        draw.polygon(points, outline=col, width=1)

    # Middle geometric square patterns (rotating clockwise)
    sq_r = 92
    for sq_i in range(3):
        sq_ang = (sq_i * math.pi / 6) + angle * 0.5
        sq_pts = []
        for c in range(4):
            corner_ang = sq_ang + (c * math.pi / 2)
            sq_pts.append((CENTER[0] + sq_r * math.cos(corner_ang), CENTER[1] + sq_r * math.sin(corner_ang)))
        draw.polygon(sq_pts, outline=(255, 170, 40, 140), width=1)

    # 3. Outer Swirling Eldritch Fire Ring (Sparks and Particles)
    # 72 sparks rotating at varying speeds
    for sp in range(72):
        sp_base_ang = (sp / 72) * 2 * math.pi + angle * 1.5
        # Add particle turbulence
        rad_var = 105 + 18 * math.sin(sp * 4 + progress * 6)
        px = CENTER[0] + rad_var * math.cos(sp_base_ang)
        py = CENTER[1] + rad_var * math.sin(sp_base_ang)
        
        # Fire gradient: yellow core to orange-red tips
        spark_r = 1.5 + 1.5 * math.sin(sp + progress * 4)
        if sp % 3 == 0:
            c = (255, 240, 120, 255) # Bright gold
        elif sp % 3 == 1:
            c = (255, 140, 20, 220)  # Fiery orange
        else:
            c = (255, 80, 20, 180)   # Ember red
        
        draw.ellipse([px - spark_r, py - spark_r, px + spark_r, py + spark_r], fill=c)

    # 4. Tangential flame trails
    for tr in range(24):
        tr_ang = (tr / 24) * 2 * math.pi + angle * 2.0
        r_start = 102
        r_end = 125 + 6 * math.sin(tr * 2 + progress * 8)
        tx1 = CENTER[0] + r_start * math.cos(tr_ang)
        ty1 = CENTER[1] + r_start * math.sin(tr_ang)
        tx2 = CENTER[0] + r_end * math.cos(tr_ang + 0.18)
        ty2 = CENTER[1] + r_end * math.sin(tr_ang + 0.18)
        draw.line([tx1, ty1, tx2, ty2], fill=(255, 180, 40, 160), width=2)

    # Convert to RGB
    bg = Image.new('RGB', (WIDTH, HEIGHT), (5, 8, 12))
    bg.paste(im, mask=im.split()[3])
    frames.append(bg)

# Save as optimized animated GIF
output_path = 'assets/marvel/mystic-portal.gif'
frames[0].save(
    output_path,
    save_all=True,
    append_images=frames[1:],
    duration=50,
    loop=0,
    optimize=True
)
print(f"Mystic Portal GIF created at {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
