import math
import os
from PIL import Image, ImageDraw, ImageFilter

os.makedirs('assets/marvel', exist_ok=True)

WIDTH, HEIGHT = 320, 320
NUM_FRAMES = 36
CENTER = (WIDTH // 2, HEIGHT // 2)

frames = []

for frame_idx in range(NUM_FRAMES):
    progress = frame_idx / NUM_FRAMES
    angle_offset = progress * 2 * math.pi

    # Create dark obsidian background
    im = Image.new('RGBA', (WIDTH, HEIGHT), (5, 11, 15, 255))
    draw = ImageDraw.Draw(im)

    # 1. Subtle Background Grid & Concentric HUD Circles
    for r in [150, 135, 110, 85]:
        draw.ellipse([CENTER[0] - r, CENTER[1] - r, CENTER[0] + r, CENTER[1] + r], 
                     outline=(10, 45, 60, 120), width=1)

    # Crosshairs
    draw.line([CENTER[0] - 155, CENTER[1], CENTER[0] - 120, CENTER[1]], fill=(0, 200, 232, 160), width=1)
    draw.line([CENTER[0] + 120, CENTER[1], CENTER[0] + 155, CENTER[1]], fill=(0, 200, 232, 160), width=1)
    draw.line([CENTER[0], CENTER[1] - 155, CENTER[0], CENTER[1] - 120], fill=(0, 200, 232, 160), width=1)
    draw.line([CENTER[0], CENTER[1] + 120, CENTER[0], CENTER[1] + 155], fill=(0, 200, 232, 160), width=1)

    # 2. Outer Rotating Tech Ticks (40 ticks)
    for i in range(40):
        tick_angle = (i / 40) * 2 * math.pi + angle_offset * 0.5
        r1, r2 = 138, 145
        if i % 5 == 0:
            r1, r2 = 134, 147
            color = (0, 230, 160, 220)
        else:
            color = (0, 180, 210, 100)
        x1 = CENTER[0] + r1 * math.cos(tick_angle)
        y1 = CENTER[1] + r1 * math.sin(tick_angle)
        x2 = CENTER[0] + r2 * math.cos(tick_angle)
        y2 = CENTER[1] + r2 * math.sin(tick_angle)
        draw.line([x1, y1, x2, y2], fill=color, width=2)

    # 3. Doctor Strange Eldritch Spark Ring (counter-rotating with gold/orange sparks)
    num_sparks = 24
    for s in range(num_sparks):
        s_angle = (s / num_sparks) * 2 * math.pi - angle_offset * 1.2
        s_r = 120 + 6 * math.sin(s * 3 + progress * 8)
        sx = CENTER[0] + s_r * math.cos(s_angle)
        sy = CENTER[1] + s_r * math.sin(s_angle)
        spark_color = (255, 180 + int(40 * math.sin(s)), 50, 200)
        draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=spark_color)

    # 4. Arc Reactor Metallic Housing Ring (radius 95)
    r_house = 98
    draw.ellipse([CENTER[0] - r_house, CENTER[1] - r_house, CENTER[0] + r_house, CENTER[1] + r_house],
                 outline=(0, 230, 200, 240), width=3)
    
    # Inner housing ring
    r_house_inner = 75
    draw.ellipse([CENTER[0] - r_house_inner, CENTER[1] - r_house_inner, CENTER[0] + r_house_inner, CENTER[1] + r_house_inner],
                 outline=(10, 60, 80, 220), width=2)

    # 5. 10 Copper/Palladium Induction Coils
    num_coils = 10
    pulse = 0.5 + 0.5 * math.sin(progress * 2 * math.pi)
    for c in range(num_coils):
        c_angle = (c / num_coils) * 2 * math.pi + angle_offset * 0.25
        # Draw trapezoidal coil
        r_mid = 86
        cx = CENTER[0] + r_mid * math.cos(c_angle)
        cy = CENTER[1] + r_mid * math.sin(c_angle)
        
        # Coil block
        coil_len = 16
        c_x1 = CENTER[0] + (r_house_inner + 2) * math.cos(c_angle - 0.12)
        c_y1 = CENTER[1] + (r_house_inner + 2) * math.sin(c_angle - 0.12)
        c_x2 = CENTER[0] + (r_house - 2) * math.cos(c_angle - 0.08)
        c_y2 = CENTER[1] + (r_house - 2) * math.sin(c_angle - 0.08)
        c_x3 = CENTER[0] + (r_house - 2) * math.cos(c_angle + 0.08)
        c_y3 = CENTER[1] + (r_house - 2) * math.sin(c_angle + 0.08)
        c_x4 = CENTER[0] + (r_house_inner + 2) * math.cos(c_angle + 0.12)
        c_y4 = CENTER[1] + (r_house_inner + 2) * math.sin(c_angle + 0.12)
        
        # Copper/Gold gradient feel
        draw.polygon([(c_x1, c_y1), (c_x2, c_y2), (c_x3, c_y3), (c_x4, c_y4)], 
                     fill=(230, 160 + int(30 * pulse), 40, 230), outline=(255, 220, 100, 255))
        
        # Glow around each coil
        glow_r = 3
        draw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r], fill=(0, 255, 230, 180))

    # 6. Central Arc Reactor Core (Pulsing Cyan Plasma Lens)
    core_r = int(52 + 5 * pulse)
    # Layered concentric glow
    for g_r, alpha in [(core_r + 14, 40), (core_r + 8, 80), (core_r + 3, 140), (core_r, 220)]:
        draw.ellipse([CENTER[0] - g_r, CENTER[1] - g_r, CENTER[0] + g_r, CENTER[1] + g_r],
                     fill=(0, int(200 + 40 * pulse), int(230 + 25 * pulse), alpha))
    
    # Central Triangle (Mark VI Arc Reactor Motif)
    tri_r = 32
    tri_pts = []
    for t in range(3):
        t_ang = (t / 3) * 2 * math.pi - math.pi / 2 + angle_offset * 0.1
        tx = CENTER[0] + tri_r * math.cos(t_ang)
        ty = CENTER[1] + tri_r * math.sin(t_ang)
        tri_pts.append((tx, ty))
    
    draw.polygon(tri_pts, fill=(5, 25, 35, 180), outline=(255, 255, 255, 240))
    
    # Ultra-bright center core dot
    draw.ellipse([CENTER[0] - 14, CENTER[1] - 14, CENTER[0] + 14, CENTER[1] + 14], fill=(240, 255, 255, 255))
    draw.ellipse([CENTER[0] - 8, CENTER[1] - 8, CENTER[0] + 8, CENTER[1] + 8], fill=(255, 255, 255, 255))

    # Convert to RGB with black background for smooth GIF rendering
    bg = Image.new('RGB', (WIDTH, HEIGHT), (5, 11, 15))
    bg.paste(im, mask=im.split()[3])
    frames.append(bg)

# Save as optimized animated GIF
output_path = 'assets/marvel/arc-reactor.gif'
frames[0].save(
    output_path,
    save_all=True,
    append_images=frames[1:],
    duration=50, # 20 fps, 1.8s loop
    loop=0,
    optimize=True
)
print(f"Arc Reactor GIF created at {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
