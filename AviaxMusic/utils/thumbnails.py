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
    blurred = image.filter(ImageFilter.GaussianBlur(12))
    
    width, height = image.size
    mask = Image.new('L', (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    for i in range(min(width, height) // 2, 0, -1):
        alpha = int(255 * (1 - i / (min(width, height) // 2)))
        mask_draw.ellipse(
            [(width//2 - i, height//2 - i), (width//2 + i, height//2 + i)],
            fill=alpha
        )
    
    return Image.composite(image, blurred, mask)

def create_glassmorphism_overlay(size, alpha=180):
    """Modern glass effect background"""
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(size[1]):
        gradient_alpha = int(alpha * (0.4 + 0.6 * (y / size[1])))
        draw.line([(0, y), (size[0], y)], fill=(10, 10, 30, gradient_alpha))
    
    return overlay

def create_album_card(thumbnail_path, size=(380, 380)):
    """Create a floating album art card with shadows"""
    try:
        thumb = Image.open(thumbnail_path)
        thumb = resize_to_fill(thumb, size[0], size[1])
        
        enhancer = ImageEnhance.Sharpness(thumb)
        thumb = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Contrast(thumb)
        thumb = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Color(thumb)
        thumb = enhancer.enhance(1.3)
        
        card_size = (size[0] + 60, size[1] + 60)
        card = Image.new('RGBA', card_size, (0, 0, 0, 0))
        
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
        
        frame_draw = ImageDraw.Draw(card)
        frame_draw.rounded_rectangle(
            [(28, 28), (size[0] + 32, size[1] + 32)],
            radius=20,
            fill=(255, 255, 255, 255)
        )
        
        thumb_rgba = thumb.convert('RGBA')
        card.paste(thumb_rgba, (30, 30))
        
        gloss = Image.new('RGBA', size, (0, 0, 0, 0))
        gloss_draw = ImageDraw.Draw(gloss)
        for y in range(size[1] // 2):
            alpha = int(80 * (1 - y / (size[1] // 2)))
            gloss_draw.line([(0, y), (size[0], y)], fill=(255, 255, 255, alpha))
        
        card.paste(gloss, (30, 30), gloss)
        
        return card
    except:
        return None

def draw_spotify_icon(draw, center_x, center_y, icon_type, size=20, color=(255, 255, 255, 255)):
    """Draw exact Spotify-style icons"""
    
    if icon_type == 'play':
        # Perfect triangle
        points = [
            (center_x - size//2, center_y - size),
            (center_x - size//2, center_y + size),
            (center_x + size, center_y)
        ]
        draw.polygon(points, fill=color)
        
    elif icon_type == 'pause':
        # Two rounded rectangles
        bar_width = size // 2.5
        bar_spacing = size // 3
        draw.rounded_rectangle(
            [(center_x - bar_spacing - bar_width//2, center_y - size),
             (center_x - bar_spacing + bar_width//2, center_y + size)],
            radius=int(bar_width * 0.4),
            fill=color
        )
        draw.rounded_rectangle(
            [(center_x + bar_spacing - bar_width//2, center_y - size),
             (center_x + bar_spacing + bar_width//2, center_y + size)],
            radius=int(bar_width * 0.4),
            fill=color
        )
        
    elif icon_type == 'skip_prev':
        # Bar + Triangle
        bar_width = size // 4
        draw.rounded_rectangle(
            [(center_x - size - 2, center_y - size),
             (center_x - size + bar_width, center_y + size)],
            radius=2,
            fill=color
        )
        points = [
            (center_x + size//2, center_y),
            (center_x - size//2, center_y - size),
            (center_x - size//2, center_y + size)
        ]
        draw.polygon(points, fill=color)
        
    elif icon_type == 'skip_next':
        # Triangle + Bar
        points = [
            (center_x - size//2, center_y),
            (center_x + size//2, center_y - size),
            (center_x + size//2, center_y + size)
        ]
        draw.polygon(points, fill=color)
        bar_width = size // 4
        draw.rounded_rectangle(
            [(center_x + size - bar_width, center_y - size),
             (center_x + size + 2, center_y + size)],
            radius=2,
            fill=color
        )
        
    elif icon_type == 'shuffle':
        # Spotify shuffle: crossed arrows
        line_width = int(size * 0.15)
        
        # Top right arrow
        draw.line([(center_x - size, center_y - size//2), (center_x + size//2, center_y - size//2)], 
                 fill=color, width=line_width)
        arrow_points = [
            (center_x + size//2, center_y - size//2),
            (center_x + size, center_y - size),
            (center_x + size, center_y)
        ]
        draw.polygon(arrow_points, fill=color)
        
        # Bottom left arrow
        draw.line([(center_x + size, center_y + size//2), (center_x - size//2, center_y + size//2)], 
                 fill=color, width=line_width)
        arrow_points = [
            (center_x - size//2, center_y + size//2),
            (center_x - size, center_y),
            (center_x - size, center_y + size)
        ]
        draw.polygon(arrow_points, fill=color)
        
        # Diagonal connector
        draw.line([(center_x - size//2, center_y - size//4), (center_x + size//2, center_y + size//4)], 
                 fill=color, width=line_width)
        
    elif icon_type == 'repeat':
        # Spotify repeat: circular arrows
        line_width = int(size * 0.15)
        
        # Top arrow path
        draw.arc(
            [(center_x - size, center_y - size), (center_x + size, center_y + size)],
            start=180, end=0, fill=color, width=line_width
        )
        
        # Top arrow head (right)
        arrow_size = size // 2
        arrow_points = [
            (center_x + size, center_y - size//4),
            (center_x + size - arrow_size, center_y - size),
            (center_x + size + arrow_size//2, center_y - size)
        ]
        draw.polygon(arrow_points, fill=color)
        
        # Bottom arrow path
        draw.arc(
            [(center_x - size, center_y - size), (center_x + size, center_y + size)],
            start=0, end=180, fill=color, width=line_width
        )
        
        # Bottom arrow head (left)
        arrow_points = [
            (center_x - size, center_y + size//4),
            (center_x - size + arrow_size, center_y + size),
            (center_x - size - arrow_size//2, center_y + size)
        ]
        draw.polygon(arrow_points, fill=color)
        
    elif icon_type == 'heart':
        # Spotify heart outline
        line_width = int(size * 0.12)
        
        # Left curve
        draw.arc(
            [(center_x - size, center_y - size//2), (center_x, center_y + size//2)],
            start=140, end=320, fill=color, width=line_width
        )
        # Right curve
        draw.arc(
            [(center_x, center_y - size//2), (center_x + size, center_y + size//2)],
            start=220, end=40, fill=color, width=line_width
        )
        # Bottom point
        points = [
            (center_x - size + line_width, center_y + line_width),
            (center_x, center_y + size),
            (center_x + size - line_width, center_y + line_width)
        ]
        draw.line(points, fill=color, width=line_width, joint='curve')
        
    elif icon_type == 'plus':
        # Add to playlist
        line_width = int(size * 0.2)
        # Horizontal
        draw.rounded_rectangle(
            [(center_x - size, center_y - line_width//2),
             (center_x + size, center_y + line_width//2)],
            radius=line_width//2,
            fill=color
        )
        # Vertical
        draw.rounded_rectangle(
            [(center_x - line_width//2, center_y - size),
             (center_x + line_width//2, center_y + size)],
            radius=line_width//2,
            fill=color
        )

def create_spotify_button(size, icon_type, is_primary=False):
    """Create Spotify-style control buttons"""
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    cx, cy = size[0] // 2, size[1] // 2
    
    if is_primary:
        # Large play button - white circle
        radius = 52
        
        # Soft shadow
        for i in range(15, 0, -1):
            alpha = int(80 * (i / 15))
            draw.ellipse(
                [cx - radius - i*3, cy - radius - i*3,
                 cx + radius + i*3, cy + radius + i*3],
                fill=(0, 0, 0, alpha)
            )
        
        # White circle
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(255, 255, 255, 255)
        )
        
        # Draw icon
        draw_spotify_icon(draw, cx + 2, cy, icon_type, 22, (0, 0, 0, 255))
        
    else:
        # Secondary buttons - subtle icons only (no background)
        draw_spotify_icon(draw, cx, cy, icon_type, 16, (180, 180, 180, 255))
    
    return button

def create_progress_bar_spotify(width, height, progress):
    """Spotify-style progress bar"""
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    
    radius = height // 2
    
    # Gray background track
    draw.rounded_rectangle(
        [(0, 0), (width, height)],
        radius=radius,
        fill=(80, 80, 80, 255)
    )
    
    # White progress
    if progress > 0:
        fill_width = max(height, int(width * progress))  # Minimum width = height for rounded corners
        
        # Create mask for rounded progress
        progress_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        progress_draw = ImageDraw.Draw(progress_img)
        
        progress_draw.rounded_rectangle(
            [(0, 0), (fill_width, height)],
            radius=radius,
            fill=(255, 255, 255, 255)
        )
        
        bar = Image.alpha_composite(bar, progress_img)
        
        # Playhead circle (only visible on hover in Spotify, but we'll show it)
        head_x = fill_width
        head_y = height // 2
        head_r = height * 1.5
        
        draw = ImageDraw.Draw(bar)
        draw.ellipse(
            [head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r],
            fill=(255, 255, 255, 255)
        )
    
    return bar

def create_info_pill(text, emoji="", width=None):
    """Modern info pills"""
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
    
    # Background
    draw.rounded_rectangle(
        [(0, 0), (pill_w, pill_h)],
        radius=pill_h // 2,
        fill=(30, 30, 50, 220)
    )
    
    # Highlight
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
    
    # Text
    text_x = (pill_w - text_w) // 2
    text_y = (pill_h - text_h) // 2 - bbox[1]
    
    draw.text((text_x + 1, text_y + 1), display_text, font=font, fill=(0, 0, 0, 100))
    draw.text((text_x, text_y), display_text, font=font, fill=(255, 255, 255, 255))
    
    return pill

def draw_premium_text(draw, pos, text, font, color=(255, 255, 255, 255), shadow=True):
    """Text with shadow"""
    if shadow:
        for i in range(3, 0, -1):
            alpha = 40 // i
            draw.text((pos[0] + i, pos[1] + i), text, font=font, fill=(0, 0, 0, alpha))
    
    draw.text(pos, text, font=font, fill=color)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_spotify.png"
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
        canvas = Image.new('RGB', (1280, 720), (18, 18, 18))  # Spotify dark background
        
        # Background with blur
        bg = Image.open(temp_path)
        bg = resize_to_fill(bg, 1280, 720)
        bg = apply_modern_blur_effect(bg)
        
        # Darken more for Spotify look
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.3)
        
        canvas.paste(bg, (0, 0))
        
        # Darker glass overlay
        glass = create_glassmorphism_overlay((1280, 720), 220)
        canvas = Image.alpha_composite(canvas.convert('RGBA'), glass)
        
        # Album card - centered
        album_card = create_album_card(temp_path, (380, 380))
        if album_card:
            card_x = (1280 - album_card.size[0]) // 2
            card_y = 70
            canvas = Image.alpha_composite(canvas, Image.new('RGBA', canvas.size, (0, 0, 0, 0)))
            canvas.paste(album_card, (card_x, card_y), album_card)
        
        draw = ImageDraw.Draw(canvas)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 38)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 24)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
        
        # Title and artist
        info_y = 480
        
        # Title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
        title_x = (1280 - title_w) // 2
        draw_premium_text(draw, (title_x, info_y), title, title_font, (255, 255, 255, 255))
        
        # Artist
        bbox = draw.textbbox((0, 0), channel, font=artist_font)
        artist_w = bbox[2] - bbox[0]
        artist_x = (1280 - artist_w) // 2
        draw_premium_text(draw, (artist_x, info_y + 52), channel, artist_font, (180, 180, 180, 255))
        
        # Progress bar - Spotify style
        progress = random.uniform(0.3, 0.7) if duration != "Live" else 1.0
        bar_width = 900
        bar_height = 5
        bar_x = (1280 - bar_width) // 2
        bar_y = 565
        
        progress_bar = create_progress_bar_spotify(bar_width, bar_height, progress)
        canvas.paste(progress_bar, (bar_x, bar_y), progress_bar)
        
        # Time stamps
        current = "2:34" if duration != "Live" else "LIVE"
        total = duration
        
        draw.text((bar_x - 60, bar_y - 4), current, font=time_font, fill=(180, 180, 180, 255))
        
        bbox = draw.textbbox((0, 0), total, font=time_font)
        total_w = bbox[2] - bbox[0]
        draw.text((bar_x + bar_width + 15, bar_y - 4), total, font=time_font, fill=(180, 180, 180, 255))
        
        # Control buttons - Spotify layout
        button_y = 600
        center_x = 640
        
        # Shuffle (far left)
        shuffle_btn = create_spotify_button((70, 70), 'shuffle', False)
        canvas.paste(shuffle_btn, (center_x - 260, button_y), shuffle_btn)
        
        # Previous
        prev_btn = create_spotify_button((70, 70), 'skip_prev', False)
        canvas.paste(prev_btn, (center_x - 140, button_y), prev_btn)
        
        # Play (large white circle)
        play_btn = create_spotify_button((120, 120), 'play', True)
        canvas.paste(play_btn, (center_x - 60, button_y - 25), play_btn)
        
        # Next
        next_btn = create_spotify_button((70, 70), 'skip_next', False)
        canvas.paste(next_btn, (center_x + 70, button_y), next_btn)
        
        # Repeat (far right)
        repeat_btn = create_spotify_button((70, 70), 'repeat', False)
        canvas.paste(repeat_btn, (center_x + 190, button_y), repeat_btn)
        
        # Bottom row - Heart and Plus
        bottom_y = button_y + 100
        
        heart_btn = create_spotify_button((60, 60), 'heart', False)
        canvas.paste(heart_btn, (center_x - 120, bottom_y), heart_btn)
        
        plus_btn = create_spotify_button((60, 60), 'plus', False)
        canvas.paste(plus_btn, (center_x + 60, bottom_y), plus_btn)
        
        # Info pills
        views_pill = create_info_pill(views, "👁")
        canvas.paste(views_pill, (30, 30), views_pill)
        
        if duration != "Live":
            duration_pill = create_info_pill(duration, "⏱")
            canvas.paste(duration_pill, (1280 - duration_pill.size[0] - 30, 30), duration_pill)
            
            quality_pill = create_info_pill("HD", "✨")
            canvas.paste(quality_pill, (1280 - quality_pill.size[0] - 30, 85), quality_pill)
        else:
            live_pill = create_info_pill("LIVE", "🔴")
            canvas.paste(live_pill, (1280 - live_pill.size[0] - 30, 30), live_pill)
        
        # Watermark
        draw.text((1280 - 150, 695), "@siyaprobot", font=time_font, fill=(120, 120, 120, 255))
        
        # Save
        os.remove(temp_path)
        canvas = canvas.convert('RGB')
        canvas.save(cache_path, quality=95, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Spotify thumbnail generation failed: {e}")
        traceback.print_exc()
        return None