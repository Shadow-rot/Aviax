import random
import logging
import os
import re
import aiofiles
import aiohttp
import traceback
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

def create_glass_card_background(size):
    """Create glassmorphic card with gradient border"""
    card = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    width, height = size
    
    # Outer glow
    for i in range(20, 0, -1):
        alpha = int(30 * (i / 20))
        draw.rounded_rectangle(
            [(-i, -i), (width + i, height + i)],
            radius=35 + i,
            fill=(100, 50, 200, alpha)
        )
    
    # Gradient border effect
    for i in range(6, 0, -1):
        # Top left to bottom right gradient colors
        ratio = i / 6
        r = int(80 + 150 * ratio)
        g = int(60 + 100 * ratio)
        b = int(200 + 50 * ratio)
        alpha = int(180 * ratio)
        
        draw.rounded_rectangle(
            [(i, i), (width - i, height - i)],
            radius=32,
            outline=(r, g, b, alpha),
            width=2
        )
    
    # Glass background
    draw.rounded_rectangle(
        [(6, 6), (width - 6, height - 6)],
        radius=30,
        fill=(25, 25, 45, 240)
    )
    
    # Inner highlight
    for y in range(height // 3):
        alpha = int(25 * (1 - y / (height // 3)))
        draw.line([(15, y + 10), (width - 15, y + 10)], fill=(255, 255, 255, alpha))
    
    return card

def create_album_art_card(thumbnail_path, size=(320, 320)):
    """Create modern album art with rounded corners"""
    try:
        thumb = Image.open(thumbnail_path)
        thumb = resize_to_fill(thumb, size[0], size[1])
        
        # Enhance thumbnail
        enhancer = ImageEnhance.Sharpness(thumb)
        thumb = enhancer.enhance(1.6)
        enhancer = ImageEnhance.Contrast(thumb)
        thumb = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Color(thumb)
        thumb = enhancer.enhance(1.4)
        
        # Create rounded corners
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), size], radius=25, fill=255)
        
        # Apply mask
        thumb_rgba = thumb.convert('RGBA')
        output = Image.new('RGBA', size, (0, 0, 0, 0))
        output.paste(thumb_rgba, (0, 0), mask)
        
        return output
    except:
        return None

def draw_modern_icon(draw, center_x, center_y, icon_type, size=18, color=(255, 255, 255, 255)):
    """Draw sleek modern icons"""
    
    if icon_type == 'play':
        # Play triangle
        offset = size // 4
        points = [
            (center_x - size//2 + offset, center_y - size),
            (center_x - size//2 + offset, center_y + size),
            (center_x + size + offset, center_y)
        ]
        draw.polygon(points, fill=color)
        
    elif icon_type == 'pause':
        # Pause bars
        bar_width = size // 2.5
        spacing = size // 4
        draw.rounded_rectangle(
            [(center_x - spacing - bar_width//2, center_y - size),
             (center_x - spacing + bar_width//2, center_y + size)],
            radius=3,
            fill=color
        )
        draw.rounded_rectangle(
            [(center_x + spacing - bar_width//2, center_y - size),
             (center_x + spacing + bar_width//2, center_y + size)],
            radius=3,
            fill=color
        )
        
    elif icon_type == 'skip_back':
        # Skip backward
        bar_w = size // 4
        draw.rounded_rectangle(
            [(center_x - size - 3, center_y - size),
             (center_x - size + bar_w, center_y + size)],
            radius=2,
            fill=color
        )
        # Double triangles
        for offset in [0, -size//1.5]:
            points = [
                (center_x + size//3 + offset, center_y),
                (center_x - size//2 + offset, center_y - size*0.9),
                (center_x - size//2 + offset, center_y + size*0.9)
            ]
            draw.polygon(points, fill=color)
        
    elif icon_type == 'skip_forward':
        # Skip forward
        # Double triangles
        for offset in [0, size//1.5]:
            points = [
                (center_x - size//3 + offset, center_y),
                (center_x + size//2 + offset, center_y - size*0.9),
                (center_x + size//2 + offset, center_y + size*0.9)
            ]
            draw.polygon(points, fill=color)
        
        bar_w = size // 4
        draw.rounded_rectangle(
            [(center_x + size - bar_w, center_y - size),
             (center_x + size + 3, center_y + size)],
            radius=2,
            fill=color
        )

def create_control_button(size, icon_type, is_primary=False):
    """Create glassmorphic control buttons"""
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    cx, cy = size[0] // 2, size[1] // 2
    
    if is_primary:
        # Large pink/magenta gradient button
        radius = 48
        
        # Outer glow
        for i in range(25, 0, -1):
            alpha = int(100 * (i / 25))
            draw.ellipse(
                [cx - radius - i*2.5, cy - radius - i*2.5,
                 cx + radius + i*2.5, cy + radius + i*2.5],
                fill=(255, 100, 180, alpha)
            )
        
        # Gradient fill
        for r in range(radius, 0, -1):
            ratio = (radius - r) / radius
            red = int(255 - 30 * ratio)
            green = int(80 + 70 * ratio)
            blue = int(150 + 50 * ratio)
            
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=(red, green, blue, 255)
            )
        
        # Top highlight
        highlight_r = int(radius / 2.5)
        for r in range(highlight_r, 0, -1):
            alpha = int(180 * (r / highlight_r))
            draw.ellipse(
                [cx - r - radius//4, cy - r - radius//3,
                 cx + r - radius//4, cy + r - radius//3],
                fill=(255, 255, 255, alpha)
            )
        
        icon_color = (255, 255, 255, 255)
        icon_size = 20
        
    else:
        # Glass secondary buttons
        radius = 32
        
        # Soft glow
        for i in range(8, 0, -1):
            alpha = int(40 * (i / 8))
            draw.ellipse(
                [cx - radius - i*2, cy - radius - i*2,
                 cx + radius + i*2, cy + radius + i*2],
                fill=(150, 100, 200, alpha)
            )
        
        # Glass circle
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(50, 50, 80, 200)
        )
        
        # Border gradient
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(150, 120, 220, 180),
            width=2
        )
        
        # Top highlight
        for r in range(radius // 2, 0, -1):
            alpha = int(60 * (r / (radius // 2)))
            draw.ellipse(
                [cx - r - 8, cy - r - 10,
                 cx + r - 8, cy + r - 10],
                fill=(255, 255, 255, alpha)
            )
        
        icon_color = (200, 200, 220, 255)
        icon_size = 15
    
    # Draw icon
    draw_modern_icon(draw, cx, cy, icon_type, icon_size, icon_color)
    
    return button

def create_gradient_progress_bar(width, height, progress):
    """Pink/purple gradient progress bar"""
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    
    radius = height // 2
    
    # Background track
    draw.rounded_rectangle(
        [(0, 0), (width, height)],
        radius=radius,
        fill=(60, 60, 90, 200)
    )
    
    # Progress with gradient
    if progress > 0:
        fill_width = max(height, int(width * progress))
        
        # Create gradient progress
        for x in range(fill_width):
            ratio = x / fill_width if fill_width > 0 else 0
            r = int(255 - 50 * ratio)
            g = int(80 + 100 * ratio)
            b = int(150 + 80 * ratio)
            
            for y in range(height):
                draw.point((x, y), fill=(r, g, b, 255))
        
        # Apply rounded mask
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (fill_width, height)], radius=radius, fill=255)
        
        progress_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        progress_layer.paste(bar, (0, 0), mask)
        bar = progress_layer
        
        # Playhead with glow
        head_x = fill_width
        head_y = height // 2
        head_r = height + 4
        
        draw = ImageDraw.Draw(bar)
        
        # Glow around playhead
        for i in range(10, 0, -1):
            alpha = int(120 / (i / 4 + 1))
            draw.ellipse(
                [head_x - head_r - i*2, head_y - head_r - i*2,
                 head_x + head_r + i*2, head_y + head_r + i*2],
                fill=(255, 150, 200, alpha)
            )
        
        # Playhead
        draw.ellipse(
            [head_x - head_r, head_y - head_r,
             head_x + head_r, head_y + head_r],
            fill=(255, 255, 255, 255)
        )
    
    return bar

def draw_text_with_glow(draw, pos, text, font, color=(255, 255, 255, 255), glow_color=(150, 100, 255, 100)):
    """Text with colored glow effect"""
    # Outer glow
    for offset in [(0, 3), (0, -3), (3, 0), (-3, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]:
        draw.text((pos[0] + offset[0], pos[1] + offset[1]), text, font=font, fill=glow_color)
    
    # Inner shadow
    draw.text((pos[0] + 1, pos[1] + 1), text, font=font, fill=(0, 0, 0, 120))
    
    # Main text
    draw.text(pos, text, font=font, fill=color)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_modern.png"
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
        title = title[:45] + "..." if len(title) > 45 else title
        
        duration = video_data.get("duration", "Live")
        thumbnail_url = video_data.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        channel = video_data.get("channel", {}).get("name", "Unknown Artist")
        channel = channel[:30] + "..." if len(channel) > 30 else channel
        
        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        # Create space background
        canvas = Image.new('RGB', (1280, 720), (10, 10, 20))
        draw = ImageDraw.Draw(canvas)
        
        # Add stars
        for _ in range(150):
            x = random.randint(0, 1280)
            y = random.randint(0, 720)
            size = random.randint(1, 3)
            alpha = random.randint(100, 255)
            draw.ellipse([x, y, x + size, y + size], fill=(255, 255, 255, alpha))
        
        # Nebula effect background
        bg = Image.open(temp_path)
        bg = resize_to_fill(bg, 1280, 720)
        bg = bg.filter(ImageFilter.GaussianBlur(40))
        
        # Heavy darken
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.15)
        
        # Purple tint
        purple_overlay = Image.new('RGBA', (1280, 720), (80, 40, 120, 100))
        bg = bg.convert('RGBA')
        bg = Image.alpha_composite(bg, purple_overlay)
        
        canvas = canvas.convert('RGBA')
        canvas = Image.alpha_composite(canvas, bg)
        
        # Glass card
        card_width = 420
        card_height = 600
        card_x = 1280 - card_width - 100
        card_y = (720 - card_height) // 2
        
        glass_card = create_glass_card_background((card_width, card_height))
        canvas.paste(glass_card, (card_x, card_y), glass_card)
        
        # Album art
        album_art = create_album_art_card(temp_path, (320, 320))
        if album_art:
            art_x = card_x + (card_width - 320) // 2
            art_y = card_y + 40
            canvas.paste(album_art, (art_x, art_y), album_art)
        
        draw = ImageDraw.Draw(canvas)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 28)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 18)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 14)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
        
        # Title below album
        title_y = card_y + 390
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
        title_x = card_x + (card_width - title_w) // 2
        draw_text_with_glow(draw, (title_x, title_y), title, title_font, (255, 255, 255, 255))
        
        # Artist
        artist_y = title_y + 38
        bbox = draw.textbbox((0, 0), channel, font=artist_font)
        artist_w = bbox[2] - bbox[0]
        artist_x = card_x + (card_width - artist_w) // 2
        draw.text((artist_x, artist_y), channel, font=artist_font, fill=(180, 180, 200, 255))
        
        # Progress bar
        progress = random.uniform(0.35, 0.75) if duration != "Live" else 1.0
        bar_width = 340
        bar_height = 5
        bar_x = card_x + (card_width - bar_width) // 2
        bar_y = card_y + 480
        
        progress_bar = create_gradient_progress_bar(bar_width, bar_height, progress)
        canvas.paste(progress_bar, (bar_x, bar_y), progress_bar)
        
        # Time stamps
        current = "02:23" if duration != "Live" else "LIVE"
        total = duration
        
        draw.text((bar_x - 2, bar_y - 18), current, font=time_font, fill=(180, 180, 200, 255))
        
        bbox = draw.textbbox((0, 0), total, font=time_font)
        total_w = bbox[2] - bbox[0]
        draw.text((bar_x + bar_width - total_w + 2, bar_y - 18), total, font=time_font, fill=(180, 180, 200, 255))
        
        # Control buttons
        button_y = card_y + 510
        center_x = card_x + card_width // 2
        
        # Skip back
        skip_back = create_control_button((70, 70), 'skip_back', False)
        canvas.paste(skip_back, (center_x - 110, button_y), skip_back)
        
        # Play button
        play_btn = create_control_button((100, 100), 'play', True)
        canvas.paste(play_btn, (center_x - 50, button_y - 15), play_btn)
        
        # Skip forward
        skip_forward = create_control_button((70, 70), 'skip_forward', False)
        canvas.paste(skip_forward, (center_x + 40, button_y), skip_forward)
        
        # Left side branding
        try:
            brand_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 48)
            sub_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 20)
        except:
            brand_font = title_font
            sub_font = artist_font
        
        brand_x = 80
        brand_y = 200
        
        # "Music" text with gradient effect
        music_text = "Music"
        draw_text_with_glow(draw, (brand_x, brand_y), music_text, brand_font, 
                           (255, 100, 200, 255), (150, 50, 200, 120))
        
        # "Player" text
        player_text = "Player"
        draw_text_with_glow(draw, (brand_x, brand_y + 55), player_text, brand_font, 
                           (255, 255, 255, 255), (150, 100, 255, 100))
        
        # Subtitle
        draw.text((brand_x, brand_y + 120), "Now Playing", font=sub_font, fill=(150, 150, 180, 255))
        
        # Watermark
        draw.text((1280 - 150, 695), "@siyaprobot", font=time_font, fill=(100, 100, 120, 200))
        
        # Save
        os.remove(temp_path)
        canvas = canvas.convert('RGB')
        canvas.save(cache_path, quality=96, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Modern thumbnail generation failed: {e}")
        traceback.print_exc()
        return None