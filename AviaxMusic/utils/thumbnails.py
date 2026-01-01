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

def apply_modern_blur_effect(image):
    """Apply beautiful depth blur with clarity zones"""
    # Light blur to maintain thumbnail details
    blurred = image.filter(ImageFilter.GaussianBlur(12))
    
    # Create a clarity mask (center is clearer)
    width, height = image.size
    mask = Image.new('L', (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Radial gradient for clarity
    for i in range(min(width, height) // 2, 0, -1):
        alpha = int(255 * (1 - i / (min(width, height) // 2)))
        mask_draw.ellipse(
            [(width//2 - i, height//2 - i), (width//2 + i, height//2 + i)],
            fill=alpha
        )
    
    # Blend: center = more original, edges = more blur
    return Image.composite(image, blurred, mask)

def create_glassmorphism_overlay(size, alpha=180):
    """Modern glass effect background"""
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Gradient from top to bottom
    for y in range(size[1]):
        gradient_alpha = int(alpha * (0.4 + 0.6 * (y / size[1])))
        draw.line([(0, y), (size[0], y)], fill=(10, 10, 30, gradient_alpha))
    
    return overlay

def create_album_card(thumbnail_path, size=(380, 380)):
    """Create a floating album art card with shadows"""
    try:
        thumb = Image.open(thumbnail_path)
        thumb = resize_to_fill(thumb, size[0], size[1])
        
        # Enhance the thumbnail
        enhancer = ImageEnhance.Sharpness(thumb)
        thumb = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Contrast(thumb)
        thumb = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Color(thumb)
        thumb = enhancer.enhance(1.3)
        
        # Create card with shadow
        card_size = (size[0] + 60, size[1] + 60)
        card = Image.new('RGBA', card_size, (0, 0, 0, 0))
        
        # Multiple shadow layers for depth
        for offset in range(20, 0, -2):
            shadow_alpha = int(120 * (offset / 20))
            shadow = Image.new('RGBA', card_size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle(
                [(30 - offset//2, 30 - offset//2 + offset), 
                 (size[0] + 30 + offset//2, size[1] + 30 + offset//2 + offset)],
                radius=25,
                fill=(0, 0, 0, shadow_alpha)
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(offset//2))
            card = Image.alpha_composite(card, shadow)
        
        # White border/frame
        frame_draw = ImageDraw.Draw(card)
        frame_draw.rounded_rectangle(
            [(28, 28), (size[0] + 32, size[1] + 32)],
            radius=20,
            fill=(255, 255, 255, 255)
        )
        
        # Paste thumbnail
        thumb_rgba = thumb.convert('RGBA')
        card.paste(thumb_rgba, (30, 30))
        
        # Glossy overlay
        gloss = Image.new('RGBA', size, (0, 0, 0, 0))
        gloss_draw = ImageDraw.Draw(gloss)
        for y in range(size[1] // 2):
            alpha = int(80 * (1 - y / (size[1] // 2)))
            gloss_draw.line([(0, y), (size[0], y)], fill=(255, 255, 255, alpha))
        
        card.paste(gloss, (30, 30), gloss)
        
        return card
    except:
        return None

def create_sleek_button(size, icon_type, is_primary=False):
    """Ultra-modern control buttons"""
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    cx, cy = size[0] // 2, size[1] // 2
    
    if is_primary:
        # Large primary button with glow
        radius = 50
        
        # Outer glow
        for i in range(25, 0, -1):
            alpha = int(60 * (i / 25))
            draw.ellipse(
                [cx - radius - i*2, cy - radius - i*2,
                 cx + radius + i*2, cy + radius + i*2],
                fill=(255, 100, 180, alpha)  # Pink glow
            )
        
        # Button gradient
        for r in range(radius, 0, -1):
            ratio = r / radius
            color_val = int(255 * ratio)
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=(color_val, color_val, color_val, 255)
            )
        
        # Highlight
        highlight_r = radius // 3
        for r in range(highlight_r, 0, -1):
            alpha = int(150 * (r / highlight_r))
            draw.ellipse(
                [cx - r - 10, cy - r - 10, cx + r - 10, cy + r - 10],
                fill=(255, 255, 255, alpha)
            )
        
        icon_size = 24
        icon_color = (30, 30, 30, 255)
    else:
        # Secondary buttons - glass style
        radius = 36
        
        # Soft glow
        for i in range(10, 0, -1):
            alpha = int(40 * (i / 10))
            draw.ellipse(
                [cx - radius - i*3, cy - radius - i*3,
                 cx + radius + i*3, cy + radius + i*3],
                fill=(255, 255, 255, alpha)
            )
        
        # Glass background
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(255, 255, 255, 200)
        )
        
        # Highlight
        for r in range(radius // 2, 0, -1):
            alpha = int(100 * (r / (radius // 2)))
            draw.ellipse(
                [cx - r - 8, cy - r - 8, cx + r - 8, cy + r - 8],
                fill=(255, 255, 255, alpha)
            )
        
        icon_size = 16
        icon_color = (60, 60, 60, 255)
    
    # Draw icons
    if icon_type == 'play':
        points = [
            (cx - icon_size//2 + 4, cy - icon_size),
            (cx - icon_size//2 + 4, cy + icon_size),
            (cx + icon_size + 4, cy)
        ]
        draw.polygon(points, fill=icon_color)
        
    elif icon_type == 'pause':
        bar_width = icon_size // 3
        draw.rounded_rectangle(
            [(cx - icon_size//2, cy - icon_size), (cx - icon_size//2 + bar_width, cy + icon_size)],
            radius=3, fill=icon_color
        )
        draw.rounded_rectangle(
            [(cx + icon_size//2 - bar_width, cy - icon_size), (cx + icon_size//2, cy + icon_size)],
            radius=3, fill=icon_color
        )
        
    elif icon_type == 'skip_prev':
        draw.polygon([
            (cx + 10, cy), (cx - 2, cy - 12), (cx - 2, cy + 12)
        ], fill=icon_color)
        draw.polygon([
            (cx, cy), (cx - 12, cy - 12), (cx - 12, cy + 12)
        ], fill=icon_color)
        
    elif icon_type == 'skip_next':
        draw.polygon([
            (cx - 10, cy), (cx + 2, cy - 12), (cx + 2, cy + 12)
        ], fill=icon_color)
        draw.polygon([
            (cx, cy), (cx + 12, cy - 12), (cx + 12, cy + 12)
        ], fill=icon_color)
        
    elif icon_type == 'shuffle':
        # X pattern with arrows
        draw.line([(cx - 12, cy - 10), (cx + 10, cy - 10)], fill=icon_color, width=3)
        draw.polygon([(cx + 10, cy - 10), (cx + 14, cy - 13), (cx + 14, cy - 7)], fill=icon_color)
        
        draw.line([(cx - 12, cy + 10), (cx + 10, cy + 10)], fill=icon_color, width=3)
        draw.polygon([(cx + 10, cy + 10), (cx + 14, cy + 7), (cx + 14, cy + 13)], fill=icon_color)
        
        draw.line([(cx - 10, cy - 7), (cx + 8, cy + 7)], fill=icon_color, width=3)
        
    elif icon_type == 'repeat':
        # Circular arrows
        draw.arc([cx - 14, cy - 14, cx + 14, cy + 14], start=40, end=320, fill=icon_color, width=3)
        draw.polygon([(cx + 10, cy - 11), (cx + 7, cy - 14), (cx + 13, cy - 14)], fill=icon_color)
        draw.polygon([(cx - 10, cy + 11), (cx - 7, cy + 14), (cx - 13, cy + 14)], fill=icon_color)
    
    return button

def create_progress_bar_modern(width, height, progress):
    """Sleek progress bar with animated feel"""
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    
    radius = height // 2
    
    # Background track with glow
    for i in range(3, 0, -1):
        draw.rounded_rectangle(
            [(-i, -i), (width + i, height + i)],
            radius=radius + i,
            fill=(255, 255, 255, 20 // i)
        )
    
    draw.rounded_rectangle(
        [(0, 0), (width, height)],
        radius=radius,
        fill=(255, 255, 255, 80)
    )
    
    # Progress fill with gradient
    if progress > 0:
        fill_width = int(width * progress)
        
        # Gradient fill
        for x in range(fill_width):
            ratio = x / fill_width if fill_width > 0 else 0
            r = int(255 - 80 * ratio)
            g = int(120 + 100 * ratio)
            b = int(200 - 20 * ratio)
            
            draw.line([(x, 0), (x, height)], fill=(r, g, b, 255))
        
        # Apply rounded corners
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (fill_width, height)], radius=radius, fill=255)
        
        filled = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        filled.paste(bar, (0, 0), mask)
        bar = filled
        
        # Playhead
        head_x = fill_width
        head_y = height // 2
        head_r = height + 6
        
        # Playhead glow
        for i in range(12, 0, -1):
            alpha = int(100 / (i / 6 + 1))
            draw.ellipse(
                [head_x - head_r - i*2, head_y - head_r - i*2,
                 head_x + head_r + i*2, head_y + head_r + i*2],
                fill=(255, 200, 220, alpha)
            )
        
        # Playhead circle
        draw.ellipse(
            [head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r],
            fill=(255, 255, 255, 255)
        )
        
        # Inner shadow on playhead
        inner_r = head_r - 3
        draw.ellipse(
            [head_x - inner_r, head_y - inner_r, head_x + inner_r, head_y + inner_r],
            fill=(240, 240, 240, 255)
        )
    
    return bar

def create_info_pill(text, emoji="", width=None):
    """Modern info pills with icons"""
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 15)
    except:
        font = ImageFont.load_default()
    
    display_text = f"{emoji}  {text}" if emoji else text
    
    temp = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp)
    bbox = temp_draw.textbbox((0, 0), display_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    if width:
        pill_w = width
    else:
        pill_w = text_w + 32
    pill_h = text_h + 18
    
    pill = Image.new('RGBA', (pill_w, pill_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pill)
    
    # Glow
    for i in range(5, 0, -1):
        draw.rounded_rectangle(
            [(-i, -i), (pill_w + i, pill_h + i)],
            radius=(pill_h + i*2) // 2,
            fill=(255, 255, 255, 15 // i)
        )
    
    # Background with gradient
    draw.rounded_rectangle(
        [(0, 0), (pill_w, pill_h)],
        radius=pill_h // 2,
        fill=(30, 30, 50, 220)
    )
    
    # Highlight at top
    for y in range(pill_h // 2):
        alpha = int(40 * (1 - y / (pill_h // 2)))
        draw.line([(5, y + 2), (pill_w - 5, y + 2)], fill=(255, 255, 255, alpha))
    
    # Border
    draw.rounded_rectangle(
        [(0, 0), (pill_w, pill_h)],
        radius=pill_h // 2,
        outline=(255, 255, 255, 100),
        width=2
    )
    
    # Text centered
    text_x = (pill_w - text_w) // 2
    text_y = (pill_h - text_h) // 2 - bbox[1]
    
    # Text shadow
    draw.text((text_x + 1, text_y + 1), display_text, font=font, fill=(0, 0, 0, 100))
    draw.text((text_x, text_y), display_text, font=font, fill=(255, 255, 255, 255))
    
    return pill

def draw_premium_text(draw, pos, text, font, color=(255, 255, 255, 255), shadow=True):
    """Text with premium shadow effect"""
    if shadow:
        # Soft shadow
        for i in range(3, 0, -1):
            alpha = 40 // i
            draw.text((pos[0] + i, pos[1] + i), text, font=font, fill=(0, 0, 0, alpha))
    
    # Main text
    draw.text(pos, text, font=font, fill=color)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_premium.png"
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
        title = title[:50] + "..." if len(title) > 50 else title
        
        duration = video_data.get("duration", "Live")
        thumbnail_url = video_data.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        views = video_data.get("viewCount", {}).get("short", "N/A")
        channel = video_data.get("channel", {}).get("name", "Unknown Artist")
        channel = channel[:35] + "..." if len(channel) > 35 else channel
        
        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        # Create canvas
        canvas = Image.new('RGB', (1280, 720), (15, 15, 25))
        
        # Background with blur
        bg = Image.open(temp_path)
        bg = resize_to_fill(bg, 1280, 720)
        bg = apply_modern_blur_effect(bg)
        
        # Darken background
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.4)
        
        canvas.paste(bg, (0, 0))
        
        # Glass overlay
        glass = create_glassmorphism_overlay((1280, 720), 200)
        canvas = Image.alpha_composite(canvas.convert('RGBA'), glass)
        
        # Album card - centered
        album_card = create_album_card(temp_path, (380, 380))
        if album_card:
            card_x = (1280 - album_card.size[0]) // 2
            card_y = 80
            canvas = Image.alpha_composite(canvas, Image.new('RGBA', canvas.size, (0, 0, 0, 0)))
            canvas.paste(album_card, (card_x, card_y), album_card)
        
        draw = ImageDraw.Draw(canvas)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 36)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 24)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
        
        # Title and artist below album
        info_y = 490
        
        # Title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
        title_x = (1280 - title_w) // 2
        draw_premium_text(draw, (title_x, info_y), title, title_font, (255, 255, 255, 255))
        
        # Artist
        bbox = draw.textbbox((0, 0), channel, font=artist_font)
        artist_w = bbox[2] - bbox[0]
        artist_x = (1280 - artist_w) // 2
        draw_premium_text(draw, (artist_x, info_y + 50), channel, artist_font, (200, 200, 220, 255))
        
        # Progress bar
        progress = random.uniform(0.3, 0.7) if duration != "Live" else 1.0
        bar_width = 800
        bar_height = 6
        bar_x = (1280 - bar_width) // 2
        bar_y = 570
        
        progress_bar = create_progress_bar_modern(bar_width, bar_height, progress)
        canvas.paste(progress_bar, (bar_x, bar_y), progress_bar)
        
        # Time stamps
        current = "2:34" if duration != "Live" else "LIVE"
        total = duration
        
        draw_premium_text(draw, (bar_x - 55, bar_y - 4), current, time_font, (220, 220, 240, 255), False)
        
        bbox = draw.textbbox((0, 0), total, font=time_font)
        total_w = bbox[2] - bbox[0]
        draw_premium_text(draw, (bar_x + bar_width + 15, bar_y - 4), total, time_font, (220, 220, 240, 255), False)
        
        # Control buttons
        button_y = 610
        center_x = 640
        spacing = 110
        
        # Skip previous
        skip_prev = create_sleek_button((80, 80), 'skip_prev', False)
        canvas.paste(skip_prev, (center_x - spacing*2 - 40, button_y), skip_prev)
        
        # Previous track
        prev_btn = create_sleek_button((80, 80), 'skip_prev', False)
        canvas.paste(prev_btn, (center_x - spacing - 40, button_y), prev_btn)
        
        # Play button (large)
        play_btn = create_sleek_button((110, 110), 'play', True)
        canvas.paste(play_btn, (center_x - 55, button_y - 15), play_btn)
        
        # Next track
        next_btn = create_sleek_button((80, 80), 'skip_next', False)
        canvas.paste(next_btn, (center_x + spacing - 40, button_y), next_btn)
        
        # Skip next
        skip_next = create_sleek_button((80, 80), 'skip_next', False)
        canvas.paste(skip_next, (center_x + spacing*2 - 40, button_y), skip_next)
        
        # Bottom controls
        shuffle_btn = create_sleek_button((70, 70), 'shuffle', False)
        canvas.paste(shuffle_btn, (center_x - 200, button_y + 95), shuffle_btn)
        
        repeat_btn = create_sleek_button((70, 70), 'repeat', False)
        canvas.paste(repeat_btn, (center_x + 130, button_y + 95), repeat_btn)
        
        # Info pills at top
        views_pill = create_info_pill(views, "👁")
        canvas.paste(views_pill, (30, 30), views_pill)
        
        if duration != "Live":
            duration_pill = create_info_pill(duration, "⏱")
            canvas.paste(duration_pill, (1280 - duration_pill.size[0] - 30, 30), duration_pill)
            
            quality_pill = create_info_pill("HD 4K", "✨")
            canvas.paste(quality_pill, (1280 - quality_pill.size[0] - 30, 85), quality_pill)
        else:
            live_pill = create_info_pill("LIVE NOW", "🔴")
            canvas.paste(live_pill, (1280 - live_pill.size[0] - 30, 30), live_pill)
        
        # Watermark
        draw.text((1280 - 150, 695), "@siyaprobot", font=time_font, fill=(255, 255, 255, 80))
        
        # Save
        os.remove(temp_path)
        canvas = canvas.convert('RGB')
        canvas.save(cache_path, quality=95, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Premium thumbnail generation failed: {e}")
        traceback.print_exc()
        return None