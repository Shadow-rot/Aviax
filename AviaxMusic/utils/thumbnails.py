import random
import logging
import os
import re
import aiofiles
import aiohttp
import traceback
import math
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch

logging.basicConfig(level=logging.INFO)

def resize_to_fill(image, target_width, target_height):
    img_ratio = image.size[0] / image.size[1]
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / img_ratio)
    
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height
    
    return resized.crop((left, top, right, bottom))

def create_planet_background(size):
    """Create beautiful planet with rings and space background"""
    canvas = Image.new('RGBA', size, (8, 10, 25, 255))
    draw = ImageDraw.Draw(canvas)
    width, height = size
    
    # Add stars
    for _ in range(200):
        x = random.randint(0, width)
        y = random.randint(0, height)
        star_size = random.randint(1, 3)
        brightness = random.randint(150, 255)
        draw.ellipse([x, y, x + star_size, y + star_size], 
                    fill=(brightness, brightness, brightness, random.randint(180, 255)))
    
    # Add some larger glowing stars
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        for i in range(5, 0, -1):
            alpha = 60 // i
            draw.ellipse([x - i, y - i, x + i, y + i], 
                        fill=(255, 255, 255, alpha))
    
    # Create planet (left side)
    planet_x = 250
    planet_y = 360
    planet_radius = 280
    
    # Planet glow
    for i in range(80, 0, -2):
        alpha = int(40 * (i / 80))
        glow_color = (150, 100, 200, alpha)
        draw.ellipse(
            [planet_x - planet_radius - i, planet_y - planet_radius - i,
             planet_x + planet_radius + i, planet_y + planet_radius + i],
            fill=glow_color
        )
    
    # Planet sphere with gradient
    for r in range(planet_radius, 0, -3):
        ratio = (planet_radius - r) / planet_radius
        
        # Purple to pink gradient
        red = int(80 + 120 * ratio)
        green = int(50 + 80 * ratio)
        blue = int(150 + 50 * ratio)
        
        draw.ellipse(
            [planet_x - r, planet_y - r, planet_x + r, planet_y + r],
            fill=(red, green, blue, 255)
        )
    
    # Add atmospheric glow on top edge
    for angle in range(0, 180, 2):
        rad = math.radians(angle)
        x = planet_x + math.cos(rad) * planet_radius
        y = planet_y - math.sin(rad) * planet_radius
        
        for i in range(15, 0, -1):
            alpha = int(80 * (i / 15) * math.sin(rad))
            draw.ellipse(
                [x - i, y - i, x + i, y + i],
                fill=(200, 150, 255, alpha)
            )
    
    # Create rings
    ring_layers = [
        (planet_radius + 60, planet_radius + 140, 40),
        (planet_radius + 150, planet_radius + 200, 30),
        (planet_radius + 210, planet_radius + 250, 25),
    ]
    
    for inner_r, outer_r, alpha_base in ring_layers:
        # Ring with perspective (ellipse)
        ring_height = int((outer_r - inner_r) * 0.3)
        
        # Outer ring edge
        for i in range(3):
            draw.ellipse(
                [planet_x - outer_r, planet_y - ring_height - i,
                 planet_x + outer_r, planet_y + ring_height - i],
                outline=(180, 140, 220, alpha_base + i * 10),
                width=2
            )
        
        # Inner ring edge (darker)
        draw.ellipse(
            [planet_x - inner_r, planet_y - int(ring_height * inner_r / outer_r),
             planet_x + inner_r, planet_y + int(ring_height * inner_r / outer_r)],
            outline=(100, 80, 140, alpha_base),
            width=1
        )
        
        # Fill between rings with gradient
        for r in range(int(inner_r), int(outer_r), 3):
            ring_h = int(ring_height * r / outer_r)
            ratio = (r - inner_r) / (outer_r - inner_r)
            alpha = int(alpha_base * (1 - ratio * 0.6))
            
            draw.ellipse(
                [planet_x - r, planet_y - ring_h,
                 planet_x + r, planet_y + ring_h],
                outline=(160 - int(40 * ratio), 120 - int(30 * ratio), 200, alpha),
                width=1
            )
    
    # Shadow on planet from rings
    shadow_start = planet_y - planet_radius // 3
    shadow_height = planet_radius // 2
    
    for y in range(shadow_height):
        ratio = y / shadow_height
        alpha = int(60 * (1 - ratio))
        y_pos = shadow_start + y
        
        # Calculate width at this y position (circular shadow)
        if abs(y_pos - planet_y) < planet_radius:
            shadow_width = int(math.sqrt(planet_radius**2 - (y_pos - planet_y)**2))
            draw.line(
                [(planet_x - shadow_width, y_pos), (planet_x + shadow_width, y_pos)],
                fill=(20, 10, 40, alpha)
            )
    
    # Add nebula clouds
    for _ in range(5):
        nx = random.randint(0, width)
        ny = random.randint(0, height)
        nsize = random.randint(100, 200)
        
        nebula = Image.new('RGBA', size, (0, 0, 0, 0))
        nebula_draw = ImageDraw.Draw(nebula)
        
        for i in range(nsize, 0, -10):
            alpha = int(20 * (i / nsize))
            color_choice = random.choice([
                (150, 80, 200, alpha),
                (200, 100, 180, alpha),
                (100, 120, 200, alpha)
            ])
            nebula_draw.ellipse(
                [nx - i, ny - i, nx + i, ny + i],
                fill=color_choice
            )
        
        nebula = nebula.filter(ImageFilter.GaussianBlur(30))
        canvas = Image.alpha_composite(canvas, nebula)
    
    return canvas

def create_glass_card_border(size):
    """Create glassmorphic card with beautiful gradient border"""
    card = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    width, height = size
    
    # Multiple outer glows
    for i in range(25, 0, -1):
        alpha = int(35 * (i / 25))
        glow_color = (120, 80, 220, alpha) if i > 12 else (180, 120, 255, alpha)
        draw.rounded_rectangle(
            [(-i, -i), (width + i, height + i)],
            radius=38 + i,
            fill=glow_color
        )
    
    # Multi-layer gradient border
    border_layers = [
        (8, (100, 70, 200, 200)),
        (6, (140, 90, 230, 220)),
        (4, (170, 120, 250, 240)),
        (2, (200, 150, 255, 255)),
    ]
    
    for width_val, color in border_layers:
        draw.rounded_rectangle(
            [(0, 0), (width - 1, height - 1)],
            radius=35,
            outline=color,
            width=width_val
        )
    
    # Inner glass background
    draw.rounded_rectangle(
        [(10, 10), (width - 10, height - 10)],
        radius=30,
        fill=(20, 20, 45, 250)
    )
    
    # Top highlight shine
    for y in range(height // 2):
        ratio = y / (height // 2)
        alpha = int(40 * (1 - ratio))
        draw.line(
            [(20, y + 15), (width - 20, y + 15)],
            fill=(255, 255, 255, alpha)
        )
    
    return card

def create_album_art_card(thumbnail_path, size=(340, 340)):
    """Create album art with perfect rounded corners and shadow"""
    try:
        thumb = Image.open(thumbnail_path)
        thumb = resize_to_fill(thumb, size[0], size[1])
        
        # Enhance
        enhancer = ImageEnhance.Sharpness(thumb)
        thumb = enhancer.enhance(1.8)
        enhancer = ImageEnhance.Contrast(thumb)
        thumb = enhancer.enhance(1.35)
        enhancer = ImageEnhance.Color(thumb)
        thumb = enhancer.enhance(1.5)
        
        # Create card with shadow
        card_size = (size[0] + 30, size[1] + 30)
        card = Image.new('RGBA', card_size, (0, 0, 0, 0))
        
        # Layered shadow
        for offset in range(12, 0, -1):
            shadow_alpha = int(80 * (offset / 12))
            shadow = Image.new('RGBA', card_size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle(
                [(15 - offset//2, 15 - offset//2 + offset),
                 (size[0] + 15 + offset//2, size[1] + 15 + offset//2 + offset)],
                radius=28,
                fill=(0, 0, 0, shadow_alpha)
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(offset))
            card = Image.alpha_composite(card, shadow)
        
        # Create rounded mask
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), size], radius=25, fill=255)
        
        # Apply mask to thumbnail
        thumb_rgba = thumb.convert('RGBA')
        output = Image.new('RGBA', size, (0, 0, 0, 0))
        output.paste(thumb_rgba, (0, 0), mask)
        
        # Paste on card
        card.paste(output, (15, 15), output)
        
        # Glossy overlay
        gloss = Image.new('RGBA', size, (0, 0, 0, 0))
        gloss_draw = ImageDraw.Draw(gloss)
        for y in range(size[1] // 2):
            alpha = int(60 * (1 - y / (size[1] // 2)))
            gloss_draw.line([(0, y), (size[0], y)], fill=(255, 255, 255, alpha))
        
        # Apply gloss mask
        gloss_masked = Image.new('RGBA', size, (0, 0, 0, 0))
        gloss_masked.paste(gloss, (0, 0), mask)
        card.paste(gloss_masked, (15, 15), gloss_masked)
        
        return card
        
    except Exception as e:
        logging.error(f"Album art creation failed: {e}")
        return None

def draw_perfect_icon(draw, cx, cy, icon_type, size=18, color=(255, 255, 255, 255)):
    """Draw pixel-perfect icons"""
    
    if icon_type == 'play':
        # Perfect triangle
        offset = size // 5
        points = [
            (cx - size//2 + offset, cy - size),
            (cx - size//2 + offset, cy + size),
            (cx + size + offset, cy)
        ]
        draw.polygon(points, fill=color)
        
    elif icon_type == 'skip_back':
        # Bar
        bar_w = int(size * 0.25)
        draw.rounded_rectangle(
            [(cx - size - 4, cy - size),
             (cx - size + bar_w, cy + size)],
            radius=2,
            fill=color
        )
        # Double triangles
        triangle_offset = [0, int(-size * 0.65)]
        for offset in triangle_offset:
            points = [
                (cx + size//3 + offset, cy),
                (cx - size//2 + offset, cy - int(size * 0.95)),
                (cx - size//2 + offset, cy + int(size * 0.95))
            ]
            draw.polygon(points, fill=color)
            
    elif icon_type == 'skip_forward':
        # Double triangles
        triangle_offset = [0, int(size * 0.65)]
        for offset in triangle_offset:
            points = [
                (cx - size//3 + offset, cy),
                (cx + size//2 + offset, cy - int(size * 0.95)),
                (cx + size//2 + offset, cy + int(size * 0.95))
            ]
            draw.polygon(points, fill=color)
        
        # Bar
        bar_w = int(size * 0.25)
        draw.rounded_rectangle(
            [(cx + size - bar_w, cy - size),
             (cx + size + 4, cy + size)],
            radius=2,
            fill=color
        )

def create_premium_button(size, icon_type, is_primary=False):
    """Create premium control buttons"""
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    cx, cy = size[0] // 2, size[1] // 2
    
    if is_primary:
        # Large pink play button
        radius = 50
        
        # Outer glow layers
        for i in range(30, 0, -1):
            alpha = int(100 * (i / 30))
            draw.ellipse(
                [cx - radius - i*2.5, cy - radius - i*2.5,
                 cx + radius + i*2.5, cy + radius + i*2.5],
                fill=(255, 100, 180, alpha)
            )
        
        # Gradient circle
        for r in range(radius, 0, -1):
            ratio = (radius - r) / radius
            red = int(255 - 25 * ratio)
            green = int(85 + 65 * ratio)
            blue = int(155 + 45 * ratio)
            
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=(red, green, blue, 255)
            )
        
        # Top shine highlight
        shine_r = int(radius * 0.45)
        shine_offset_x = int(-radius * 0.2)
        shine_offset_y = int(-radius * 0.25)
        
        for r in range(shine_r, 0, -1):
            alpha = int(200 * (r / shine_r))
            draw.ellipse(
                [cx + shine_offset_x - r, cy + shine_offset_y - r,
                 cx + shine_offset_x + r, cy + shine_offset_y + r],
                fill=(255, 255, 255, alpha)
            )
        
        # Icon
        draw_perfect_icon(draw, cx, cy, icon_type, 22, (255, 255, 255, 255))
        
    else:
        # Glass secondary buttons
        radius = 34
        
        # Subtle glow
        for i in range(12, 0, -1):
            alpha = int(50 * (i / 12))
            draw.ellipse(
                [cx - radius - i*2, cy - radius - i*2,
                 cx + radius + i*2, cy + radius + i*2],
                fill=(150, 110, 220, alpha)
            )
        
        # Glass circle with gradient
        for r in range(radius, 0, -1):
            ratio = r / radius
            alpha = int(180 + 40 * (1 - ratio))
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=(45, 45, 75, alpha)
            )
        
        # Bright border
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(160, 130, 240, 200),
            width=2
        )
        
        # Top shine
        shine_r = int(radius * 0.4)
        for r in range(shine_r, 0, -1):
            alpha = int(80 * (r / shine_r))
            draw.ellipse(
                [cx - r - 6, cy - r - 8,
                 cx + r - 6, cy + r - 8],
                fill=(255, 255, 255, alpha)
            )
        
        # Icon
        draw_perfect_icon(draw, cx, cy, icon_type, 16, (210, 210, 230, 255))
    
    return button

def create_gradient_bar(width, height, progress):
    """Beautiful gradient progress bar"""
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    
    radius = height // 2
    
    # Background track
    draw.rounded_rectangle(
        [(0, 0), (width, height)],
        radius=radius,
        fill=(60, 60, 90, 180)
    )
    
    # Progress fill
    if progress > 0:
        fill_width = max(height, int(width * progress))
        
        # Create gradient
        for x in range(fill_width):
            ratio = x / fill_width if fill_width > 0 else 0
            r = int(255 - 40 * ratio)
            g = int(85 + 95 * ratio)
            b = int(155 + 75 * ratio)
            
            for y in range(height):
                draw.point((x, y), fill=(r, g, b, 255))
        
        # Mask for rounded corners
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (fill_width, height)], radius=radius, fill=255)
        
        progress_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        progress_img.paste(bar, (0, 0), mask)
        bar = progress_img
        
        # Playhead
        head_x = fill_width
        head_y = height // 2
        head_r = height + 5
        
        draw = ImageDraw.Draw(bar)
        
        # Playhead glow
        for i in range(15, 0, -1):
            alpha = int(140 / (i / 6 + 1))
            draw.ellipse(
                [head_x - head_r - i*2, head_y - head_r - i*2,
                 head_x + head_r + i*2, head_y + head_r + i*2],
                fill=(255, 140, 200, alpha)
            )
        
        # Playhead circle
        draw.ellipse(
            [head_x - head_r, head_y - head_r,
             head_x + head_r, head_y + head_r],
            fill=(255, 255, 255, 255)
        )
        
        # Playhead shine
        shine_r = head_r // 2
        draw.ellipse(
            [head_x - shine_r - 2, head_y - shine_r - 3,
             head_x + shine_r - 2, head_y + shine_r - 3],
            fill=(255, 255, 255, 150)
        )
    
    return bar

def draw_text_glow(draw, pos, text, font, color=(255, 255, 255, 255), glow=(180, 120, 255, 100)):
    """Text with beautiful glow"""
    # Multiple glow layers
    for offset_x, offset_y, alpha_mult in [(0, 4, 0.8), (0, -4, 0.5), (4, 0, 0.5), (-4, 0, 0.5),
                                            (3, 3, 0.6), (-3, -3, 0.4), (3, -3, 0.4), (-3, 3, 0.4)]:
        glow_alpha = int(glow[3] * alpha_mult)
        draw.text((pos[0] + offset_x, pos[1] + offset_y), text, font=font,
                 fill=(glow[0], glow[1], glow[2], glow_alpha))
    
    # Shadow
    draw.text((pos[0] + 1, pos[1] + 2), text, font=font, fill=(0, 0, 0, 140))
    
    # Main text
    draw.text(pos, text, font=font, fill=color)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_premium_v2.png"
        if os.path.isfile(cache_path):
            return cache_path

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        
        video_data = None
        for result in (await results.next())["result"]:
            video_data = result
            break
        
        if not video_data:
            return None
        
        # Extract data
        title = re.sub(r"\W+", " ", video_data.get("title", "Unknown Title")).title()
        title = title[:42] + "..." if len(title) > 42 else title
        
        duration = video_data.get("duration", "Live")
        thumbnail_url = video_data.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        channel = video_data.get("channel", {}).get("name", "Unknown Artist")
        channel = channel[:28] + "..." if len(channel) > 28 else channel
        
        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        # Create planet background
        canvas = create_planet_background((1280, 720))
        
        # Add some atmospheric dust/particles
        dust = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        dust_draw = ImageDraw.Draw(dust)
        for _ in range(100):
            x = random.randint(0, 1280)
            y = random.randint(0, 720)
            size = random.randint(1, 2)
            dust_draw.ellipse([x, y, x + size, y + size],
                            fill=(200, 180, 255, random.randint(30, 80)))
        dust = dust.filter(ImageFilter.GaussianBlur(1))
        canvas = Image.alpha_composite(canvas, dust)
        
        # Glass card
        card_w, card_h = 440, 620
        card_x = 1280 - card_w - 80
        card_y = (720 - card_h) // 2
        
        glass_card = create_glass_card_border((card_w, card_h))
        canvas.paste(glass_card, (card_x, card_y), glass_card)
        
        # Album art
        album_art = create_album_art_card(temp_path, (340, 340))
        if album_art:
            art_x = card_x + (card_w - album_art.size[0]) // 2
            art_y = card_y + 35
            canvas.paste(album_art, (art_x, art_y), album_art)
        
        draw = ImageDraw.Draw(canvas)
        
        # Fonts
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 30)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 19)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 15)
            brand_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 52)
        except:
            title_font = artist_font = time_font = brand_font = ImageFont.load_default()
        
        # Song info
        info_y = card_y + 410
        
        # Title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
        title_x = card_x + (card_w - title_w) // 2
        draw_text_glow(draw, (title_x, info_y), title, title_font)
        
        # Artist
        artist_y = info_y + 40
        bbox = draw.textbbox((0, 0), channel, font=artist_font)
        artist_w = bbox[2] - bbox[0]
        artist_x = card_x + (card_w - artist_w) // 2
        draw.text((artist_x, artist_y), channel, font=artist_font, fill=(170, 170, 190, 255))
        
        # Progress bar
        progress = random.uniform(0.35, 0.75) if duration != "Live" else 1.0
        bar_w, bar_h = 360, 6
        bar_x = card_x + (card_w - bar_w) // 2
        bar_y = card_y + 500
        
        progress_bar = create_gradient_bar(bar_w, bar_h, progress)
        canvas.paste(progress_bar, (bar_x, bar_y), progress_bar)
        
        # Times
        current = "02:23"
        total = duration if duration != "Live" else "LIVE"
        
        draw.text((bar_x - 2, bar_y - 20), current, font=time_font, fill=(170, 170, 200, 255))
        bbox = draw.textbbox((0, 0), total, font=time_font)
        total_w = bbox[2] - bbox[0]
        draw.text((bar_x + bar_w - total_w + 2, bar_y - 20), total, font=time_font, fill=(170, 170, 200, 255))
        
        # Control buttons
        btn_y = card_y + 530
        center_x = card_x + card_w // 2
        
        # Skip back
        skip_back = create_premium_button((75, 75), 'skip_back', False)
        canvas.paste(skip_back, (center_x - 120, btn_y), skip_back)
        
        # Play
        play_btn = create_premium_button((105, 105), 'play', True)
        canvas.paste(play_btn, (center_x - 52, btn_y - 15), play_btn)
        
        # Skip forward
        skip_forward = create_premium_button((75, 75), 'skip_forward', False)
        canvas.paste(skip_forward, (center_x + 45, btn_y), skip_forward)
        
        # Left branding
        brand_x = 75
        brand_y = 220
        
        draw_text_glow(draw, (brand_x, brand_y), "Music", brand_font,
                      (255, 100, 200, 255), (200, 80, 255, 120))
        draw_text_glow(draw, (brand_x, brand_y + 62), "Player", brand_font,
                      (255, 255, 255, 255), (160, 120, 255, 100))
        
        draw.text((brand_x + 5, brand_y + 130), "Now Playing", font=artist_font, fill=(140, 140, 170, 255))
        
        # Watermark
        draw.text((1130, 695), "@siyaprobot", font=time_font, fill=(90, 90, 110, 180))
        
        # Cleanup
        os.remove(temp_path)
        canvas = canvas.convert('RGB')
        canvas.save(cache_path, quality=97, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Premium thumbnail failed: {e}")
        traceback.print_exc()
        return None