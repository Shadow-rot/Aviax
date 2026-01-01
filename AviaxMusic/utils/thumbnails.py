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
    """Create stunning planet with detailed rings"""
    canvas = Image.new('RGBA', size, (5, 8, 22, 255))
    draw = ImageDraw.Draw(canvas)
    width, height = size
    
    # Stars - more realistic
    for _ in range(250):
        x = random.randint(0, width)
        y = random.randint(0, height)
        star_size = random.choice([1, 1, 1, 2, 2, 3])
        brightness = random.randint(180, 255)
        alpha = random.randint(200, 255)
        draw.ellipse([x, y, x + star_size, y + star_size], 
                    fill=(brightness, brightness, brightness, alpha))
    
    # Twinkling stars
    for _ in range(40):
        x = random.randint(0, width)
        y = random.randint(0, height)
        for i in range(6, 0, -1):
            alpha = 80 // i
            draw.ellipse([x - i, y - i, x + i, y + i], 
                        fill=(255, 255, 255, alpha))
    
    # Planet position
    planet_x = 220
    planet_y = 360
    planet_radius = 300
    
    # Planet outer glow
    for i in range(100, 0, -2):
        alpha = int(45 * (i / 100))
        draw.ellipse(
            [planet_x - planet_radius - i, planet_y - planet_radius - i,
             planet_x + planet_radius + i, planet_y + planet_radius + i],
            fill=(140, 90, 210, alpha)
        )
    
    # Planet sphere with realistic gradient
    for r in range(planet_radius, 0, -2):
        ratio = (planet_radius - r) / planet_radius
        
        # Purple to lavender gradient
        red = int(100 + 140 * ratio)
        green = int(60 + 100 * ratio)
        blue = int(180 + 60 * ratio)
        
        draw.ellipse(
            [planet_x - r, planet_y - r, planet_x + r, planet_y + r],
            fill=(red, green, blue, 255)
        )
    
    # Atmospheric lighting on edge
    for angle in range(0, 180, 1):
        rad = math.radians(angle)
        distance = planet_radius
        x = planet_x + math.cos(rad) * distance
        y = planet_y - math.sin(rad) * distance
        
        for i in range(20, 0, -1):
            alpha = int(100 * (i / 20) * math.sin(rad))
            draw.ellipse(
                [x - i, y - i, x + i, y + i],
                fill=(220, 180, 255, alpha)
            )
    
    # Ring system - multiple detailed rings
    ring_sets = [
        # (inner_radius, outer_radius, base_alpha, color)
        (planet_radius + 50, planet_radius + 130, 55, (200, 160, 240)),
        (planet_radius + 140, planet_radius + 180, 45, (180, 140, 220)),
        (planet_radius + 190, planet_radius + 240, 40, (160, 120, 200)),
        (planet_radius + 250, planet_radius + 280, 30, (140, 100, 180)),
    ]
    
    for inner_r, outer_r, base_alpha, color in ring_sets:
        ring_h_ratio = 0.28
        
        # Draw ring with gradient and texture
        for r in range(int(inner_r), int(outer_r), 2):
            ring_h = int((outer_r - inner_r) * ring_h_ratio * r / outer_r)
            
            # Calculate alpha gradient
            ratio = (r - inner_r) / (outer_r - inner_r)
            alpha = int(base_alpha * (1 - ratio * 0.5))
            
            # Add some variation for texture
            if random.random() > 0.7:
                alpha = int(alpha * random.uniform(0.7, 1.0))
            
            draw.ellipse(
                [planet_x - r, planet_y - ring_h,
                 planet_x + r, planet_y + ring_h],
                outline=(color[0], color[1], color[2], alpha),
                width=1
            )
        
        # Ring edges (brighter)
        outer_h = int((outer_r - inner_r) * ring_h_ratio)
        for i in range(3):
            alpha_edge = base_alpha + 20 - i * 5
            draw.ellipse(
                [planet_x - outer_r + i, planet_y - outer_h,
                 planet_x + outer_r - i, planet_y + outer_h],
                outline=(color[0] + 20, color[1] + 20, color[2] + 20, alpha_edge),
                width=1
            )
    
    # Ring shadow on planet
    shadow_y_start = planet_y - planet_radius // 2
    shadow_height = int(planet_radius * 0.6)
    
    for y in range(shadow_height):
        y_pos = shadow_y_start + y
        if abs(y_pos - planet_y) < planet_radius:
            shadow_width = int(math.sqrt(planet_radius**2 - (y_pos - planet_y)**2))
            ratio = y / shadow_height
            alpha = int(80 * (1 - ratio * 0.6))
            
            draw.line(
                [(planet_x - shadow_width, y_pos), (planet_x + shadow_width, y_pos)],
                fill=(15, 10, 35, alpha)
            )
    
    # Nebula clouds
    for _ in range(8):
        nx = random.randint(0, width)
        ny = random.randint(0, height)
        nsize = random.randint(120, 220)
        
        nebula = Image.new('RGBA', size, (0, 0, 0, 0))
        nebula_draw = ImageDraw.Draw(nebula)
        
        for i in range(nsize, 0, -15):
            alpha = int(25 * (i / nsize))
            colors = [
                (160, 100, 220, alpha),
                (200, 120, 200, alpha),
                (120, 100, 200, alpha)
            ]
            nebula_draw.ellipse(
                [nx - i, ny - i, nx + i, ny + i],
                fill=random.choice(colors)
            )
        
        nebula = nebula.filter(ImageFilter.GaussianBlur(35))
        canvas = Image.alpha_composite(canvas, nebula)
    
    return canvas

def create_glass_card(size):
    """Perfect glass morphism card"""
    card = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    width, height = size
    
    # Multi-layer glow
    for i in range(30, 0, -1):
        alpha = int(40 * (i / 30))
        glow_colors = [
            (110, 70, 200, alpha),
            (150, 100, 220, alpha),
            (130, 90, 210, alpha)
        ]
        color_index = (i // 10) % len(glow_colors)
        
        draw.rounded_rectangle(
            [(-i, -i), (width + i, height + i)],
            radius=40 + i,
            fill=glow_colors[color_index]
        )
    
    # Gradient border
    for i in range(10, 0, -1):
        ratio = i / 10
        r = int(90 + 110 * ratio)
        g = int(60 + 90 * ratio)
        b = int(190 + 50 * ratio)
        alpha = int(200 + 55 * ratio)
        
        draw.rounded_rectangle(
            [(i-1, i-1), (width - i, height - i)],
            radius=38,
            outline=(r, g, b, alpha),
            width=1
        )
    
    # Inner dark glass
    draw.rounded_rectangle(
        [(12, 12), (width - 12, height - 12)],
        radius=32,
        fill=(18, 20, 42, 248)
    )
    
    # Glossy top highlight
    for y in range(height // 2):
        alpha = int(50 * (1 - y / (height // 2)))
        draw.line([(22, y + 18), (width - 22, y + 18)], fill=(255, 255, 255, alpha))
    
    return card

def create_album_art(thumbnail_path, size=(360, 360)):
    """Perfect rounded album art with shadow"""
    try:
        thumb = Image.open(thumbnail_path)
        thumb = resize_to_fill(thumb, size[0], size[1])
        
        # Ultra enhance
        enhancer = ImageEnhance.Sharpness(thumb)
        thumb = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Contrast(thumb)
        thumb = enhancer.enhance(1.4)
        enhancer = ImageEnhance.Color(thumb)
        thumb = enhancer.enhance(1.6)
        
        # Create container with shadow
        container_size = (size[0] + 40, size[1] + 40)
        container = Image.new('RGBA', container_size, (0, 0, 0, 0))
        
        # Multi-layer shadow
        for offset in range(20, 0, -1):
            shadow_alpha = int(100 * (offset / 20))
            shadow = Image.new('RGBA', container_size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle(
                [(20 - offset//2, 20 - offset//2 + offset),
                 (size[0] + 20 + offset//2, size[1] + 20 + offset//2 + offset)],
                radius=30,
                fill=(0, 0, 0, shadow_alpha)
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(offset//2))
            container = Image.alpha_composite(container, shadow)
        
        # Rounded mask
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), size], radius=28, fill=255)
        
        # Apply mask
        thumb_rgba = thumb.convert('RGBA')
        masked_thumb = Image.new('RGBA', size, (0, 0, 0, 0))
        masked_thumb.paste(thumb_rgba, (0, 0), mask)
        
        container.paste(masked_thumb, (20, 20), masked_thumb)
        
        # Glossy effect
        gloss = Image.new('RGBA', size, (0, 0, 0, 0))
        gloss_draw = ImageDraw.Draw(gloss)
        for y in range(size[1] // 2):
            alpha = int(70 * (1 - y / (size[1] // 2)))
            gloss_draw.line([(0, y), (size[0], y)], fill=(255, 255, 255, alpha))
        
        gloss_masked = Image.new('RGBA', size, (0, 0, 0, 0))
        gloss_masked.paste(gloss, (0, 0), mask)
        container.paste(gloss_masked, (20, 20), gloss_masked)
        
        return container
        
    except Exception as e:
        logging.error(f"Album art error: {e}")
        return None

def draw_icon(draw, cx, cy, icon_type, size=16, color=(255, 255, 255, 255)):
    """Pixel-perfect control icons"""
    s = size
    
    if icon_type == 'play':
        points = [
            (cx - s//2 + s//4, cy - s),
            (cx - s//2 + s//4, cy + s),
            (cx + s + s//4, cy)
        ]
        draw.polygon(points, fill=color)
        
    elif icon_type == 'skip_prev':
        # Vertical bar
        draw.rounded_rectangle(
            [(cx - s - 5, cy - s), (cx - s + s//3, cy + s)],
            radius=2, fill=color
        )
        # Two triangles
        for offset in [0, -s//1.5]:
            points = [
                (cx + s//3 + offset, cy),
                (cx - s//2 + offset, cy - int(s * 0.9)),
                (cx - s//2 + offset, cy + int(s * 0.9))
            ]
            draw.polygon(points, fill=color)
    
    elif icon_type == 'skip_next':
        # Two triangles
        for offset in [0, s//1.5]:
            points = [
                (cx - s//3 + offset, cy),
                (cx + s//2 + offset, cy - int(s * 0.9)),
                (cx + s//2 + offset, cy + int(s * 0.9))
            ]
            draw.polygon(points, fill=color)
        # Vertical bar
        draw.rounded_rectangle(
            [(cx + s - s//3, cy - s), (cx + s + 5, cy + s)],
            radius=2, fill=color
        )

def create_button(size, icon_type, is_primary=False):
    """Beautiful control buttons"""
    btn = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(btn)
    cx, cy = size[0] // 2, size[1] // 2
    
    if is_primary:
        radius = 48
        
        # Massive glow
        for i in range(35, 0, -1):
            alpha = int(110 * (i / 35))
            draw.ellipse(
                [cx - radius - i*2.8, cy - radius - i*2.8,
                 cx + radius + i*2.8, cy + radius + i*2.8],
                fill=(255, 90, 170, alpha)
            )
        
        # Gradient button
        for r in range(radius, 0, -1):
            ratio = (radius - r) / radius
            red = int(255 - 20 * ratio)
            green = int(80 + 75 * ratio)
            blue = int(150 + 55 * ratio)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(red, green, blue, 255))
        
        # Highlight
        shine_r = int(radius * 0.42)
        shine_x, shine_y = int(-radius * 0.18), int(-radius * 0.22)
        for r in range(shine_r, 0, -1):
            alpha = int(220 * (r / shine_r))
            draw.ellipse(
                [cx + shine_x - r, cy + shine_y - r,
                 cx + shine_x + r, cy + shine_y + r],
                fill=(255, 255, 255, alpha)
            )
        
        draw_icon(draw, cx, cy, icon_type, 20, (255, 255, 255, 255))
        
    else:
        radius = 32
        
        # Soft glow
        for i in range(15, 0, -1):
            alpha = int(60 * (i / 15))
            draw.ellipse(
                [cx - radius - i*2.5, cy - radius - i*2.5,
                 cx + radius + i*2.5, cy + radius + i*2.5],
                fill=(140, 100, 210, alpha)
            )
        
        # Glass button
        for r in range(radius, 0, -1):
            ratio = r / radius
            alpha = int(170 + 60 * (1 - ratio))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(42, 42, 72, alpha))
        
        # Border
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                    outline=(150, 120, 230, 220), width=2)
        
        # Shine
        shine_r = int(radius * 0.38)
        for r in range(shine_r, 0, -1):
            alpha = int(90 * (r / shine_r))
            draw.ellipse([cx - r - 5, cy - r - 7, cx + r - 5, cy + r - 7],
                        fill=(255, 255, 255, alpha))
        
        draw_icon(draw, cx, cy, icon_type, 15, (200, 200, 220, 255))
    
    return btn

def create_progress_bar(width, height, progress):
    """Gradient progress bar"""
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    radius = height // 2
    
    # Track
    draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=(55, 55, 85, 200))
    
    if progress > 0:
        fill_w = max(height, int(width * progress))
        
        # Gradient
        for x in range(fill_w):
            ratio = x / fill_w if fill_w > 0 else 0
            r = int(255 - 35 * ratio)
            g = int(80 + 105 * ratio)
            b = int(150 + 80 * ratio)
            for y in range(height):
                draw.point((x, y), fill=(r, g, b, 255))
        
        # Mask
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (fill_w, height)], radius=radius, fill=255)
        
        progress_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        progress_img.paste(bar, (0, 0), mask)
        bar = progress_img
        
        # Playhead
        head_x, head_y = fill_w, height // 2
        head_r = height + 6
        
        draw = ImageDraw.Draw(bar)
        for i in range(18, 0, -1):
            alpha = int(150 / (i / 7 + 1))
            draw.ellipse([head_x - head_r - i*2, head_y - head_r - i*2,
                         head_x + head_r + i*2, head_y + head_r + i*2],
                        fill=(255, 130, 190, alpha))
        
        draw.ellipse([head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r],
                    fill=(255, 255, 255, 255))
        
        shine = head_r // 2
        draw.ellipse([head_x - shine - 1, head_y - shine - 2,
                     head_x + shine - 1, head_y + shine - 2],
                    fill=(255, 255, 255, 180))
    
    return bar

def draw_glow_text(draw, pos, text, font, color=(255, 255, 255, 255), glow=(170, 110, 240, 110)):
    """Text with glow"""
    offsets = [(0, 5), (0, -5), (5, 0), (-5, 0), (3, 3), (-3, -3), (3, -3), (-3, 3)]
    for dx, dy in offsets:
        mult = 0.7 if abs(dx) + abs(dy) > 4 else 0.9
        alpha = int(glow[3] * mult)
        draw.text((pos[0] + dx, pos[1] + dy), text, font=font,
                 fill=(glow[0], glow[1], glow[2], alpha))
    
    draw.text((pos[0] + 1, pos[1] + 2), text, font=font, fill=(0, 0, 0, 150))
    draw.text(pos, text, font=font, fill=color)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_final.png"
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
        
        title = re.sub(r"\W+", " ", video_data.get("title", "Unknown Title")).title()
        title = title[:40] + "..." if len(title) > 40 else title
        duration = video_data.get("duration", "Live")
        thumbnail_url = video_data.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        channel = video_data.get("channel", {}).get("name", "Unknown Artist")
        channel = channel[:26] + "..." if len(channel) > 26 else channel
        
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        # Background
        canvas = create_planet_background((1280, 720))
        
        # Dust particles
        dust = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        dust_draw = ImageDraw.Draw(dust)
        for _ in range(120):
            x, y = random.randint(0, 1280), random.randint(0, 720)
            size = random.randint(1, 2)
            dust_draw.ellipse([x, y, x + size, y + size],
                            fill=(210, 190, 255, random.randint(40, 90)))
        dust = dust.filter(ImageFilter.GaussianBlur(1))
        canvas = Image.alpha_composite(canvas, dust)
        
        # Card
        card_w, card_h = 450, 630
        card_x, card_y = 1280 - card_w - 70, (720 - card_h) // 2
        
        glass = create_glass_card((card_w, card_h))
        canvas.paste(glass, (card_x, card_y), glass)
        
        # Album
        album = create_album_art(temp_path, (360, 360))
        if album:
            art_x = card_x + (card_w - album.size[0]) // 2
            art_y = card_y + 30
            canvas.paste(album, (art_x, art_y), album)
        
        draw = ImageDraw.Draw(canvas)
        
        # Fonts
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 29)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 18)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 14)
            brand_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 54)
        except:
            title_font = artist_font = time_font = brand_font = ImageFont.load_default()
        
        # Song info
        info_y = card_y + 425
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
        title_x = card_x + (card_w - title_w) // 2
        draw_glow_text(draw, (title_x, info_y), title, title_font)
        
        artist_y = info_y + 38
        bbox = draw.textbbox((0, 0), channel, font=artist_font)
        artist_w = bbox[2] - bbox[0]
        artist_x = card_x + (card_w - artist_w) // 2
        draw.text((artist_x, artist_y), channel, font=artist_font, fill=(165, 165, 185, 255))
        
        # Progress
        progress = random.uniform(0.35, 0.75) if duration != "Live" else 1.0
        bar_w, bar_h = 370, 6
        bar_x, bar_y = card_x + (card_w - bar_w) // 2, card_y + 510
        
        pbar = create_progress_bar(bar_w, bar_h, progress)
        canvas.paste(pbar, (bar_x, bar_y), pbar)
        
        # Times
        current, total = "02:23", duration if duration != "Live" else "LIVE"
        draw.text((bar_x, bar_y - 22), current, font=time_font, fill=(165, 165, 195, 255))
        bbox = draw.textbbox((0, 0), total, font=time_font)
        draw.text((bar_x + bar_w - bbox[2] + bbox[0], bar_y - 22), total, font=time_font, fill=(165, 165, 195, 255))
        
        # Controls
        btn_y = card_y + 540
        center = card_x + card_w // 2
        
        skip_back = create_button((72, 72), 'skip_prev', False)
        canvas.paste(skip_back, (center - 115, btn_y), skip_back)
        
        play = create_button((102, 102), 'play', True)
        canvas.paste(play, (center - 51, btn_y - 15), play)
        
        skip_fwd = create_button((72, 72), 'skip_next', False)
        canvas.paste(skip_fwd, (center + 43, btn_y), skip_fwd)
        
        # Branding
        brand_x, brand_y = 70, 210
        draw_glow_text(draw, (brand_x, brand_y), "Music", brand_font,
                      (255, 90, 190, 255), (200, 70, 240, 130))
        draw_glow_text(draw, (brand_x, brand_y + 64), "Player", brand_font,
                      (255, 255, 255, 255), (150, 110, 240, 110))
        draw.text((brand_x + 6, brand_y + 135), "Now Playing", font=artist_font, fill=(135, 135, 165, 255))
        
        draw.text((1125, 695), "@siyaprobot", font=time_font, fill=(85, 85, 105, 200))
        
        os.remove(temp_path)
        canvas = canvas.convert('RGB')
        canvas.save(cache_path, quality=98, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail failed: {e}")
        traceback.print_exc()
        return None