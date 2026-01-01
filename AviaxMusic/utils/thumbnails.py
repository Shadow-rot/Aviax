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

def apply_subtle_blur(image, blur_strength=8):
    """Less blur to show more YouTube thumbnail details"""
    blurred = image.filter(ImageFilter.GaussianBlur(blur_strength))
    return Image.blend(image, blurred, 0.7)  # Only 70% blur, 30% original

def enhance_thumbnail_details(image):
    """Enhance the original thumbnail to show more details"""
    image = image.convert('RGB')
    
    # Sharpen details
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.3)
    
    # Light color grading
    overlay = Image.new('RGB', image.size, (100, 110, 140))
    image = Image.blend(image, overlay, alpha=0.08)
    
    # Boost contrast to show details
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    
    # Enhance colors
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.15)
    
    return image.convert('RGBA')

def add_subtle_vignette(image, strength=0.4):
    """Light vignette to keep thumbnail visible"""
    width, height = image.size
    vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    
    for i in range(min(width, height) // 2):
        alpha = int((i / (min(width, height) // 2)) * 255 * strength)
        alpha = 255 - alpha
        draw.ellipse(
            [(i, i), (width - i, height - i)],
            fill=(0, 0, 0, alpha)
        )
    
    return Image.alpha_composite(image, vignette)

def add_gradient_overlay(image):
    """Gentle gradient for text readability"""
    width, height = image.size
    gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    
    # Top gradient
    for y in range(height // 3):
        alpha = int(100 - (y / (height // 3)) * 100)
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    # Bottom gradient
    for y in range(height * 2 // 3, height):
        alpha = int(((y - height * 2 // 3) / (height // 3)) * 140)
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    return Image.alpha_composite(image, gradient)

def create_music_icon_button(size, icon_type, is_primary=False):
    """Premium music control icons"""
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    center_x = size[0] // 2
    center_y = size[1] // 2
    
    if is_primary:
        radius = 45
        # Outer glow rings
        for i in range(15, 0, -1):
            alpha = int(40 * (i / 15))
            draw.ellipse(
                [center_x - radius - i*3, center_y - radius - i*3,
                 center_x + radius + i*3, center_y + radius + i*3],
                fill=(255, 255, 255, alpha)
            )
        
        # Main button
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            fill=(255, 255, 255, 255)
        )
        
        # Inner gradient effect
        for i in range(radius // 3):
            alpha = int(40 * (1 - i / (radius // 3)))
            draw.ellipse(
                [center_x - i, center_y - i,
                 center_x + i, center_y + i],
                fill=(255, 255, 255, alpha)
            )
        
        icon_color = (0, 0, 0, 255)
        icon_size = 20
    else:
        radius = 32
        # Glass effect with glow
        for i in range(6, 0, -1):
            alpha = int(30 * (i / 6))
            draw.ellipse(
                [center_x - radius - i*2, center_y - radius - i*2,
                 center_x + radius + i*2, center_y + radius + i*2],
                fill=(255, 255, 255, alpha)
            )
        
        # Button background
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            fill=(255, 255, 255, 150)
        )
        
        # Border
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            outline=(255, 255, 255, 220),
            width=2
        )
        
        icon_color = (255, 255, 255, 255)
        icon_size = 14
    
    # Draw various music control icons
    if icon_type == 'play':
        # Play triangle
        play_points = [
            (center_x - icon_size//2 + 3, center_y - icon_size),
            (center_x - icon_size//2 + 3, center_y + icon_size),
            (center_x + icon_size + 3, center_y)
        ]
        draw.polygon(play_points, fill=icon_color)
        
    elif icon_type == 'skip_back':
        # Skip backward (double triangle + line)
        draw.polygon([
            (center_x + 8, center_y),
            (center_x - 4, center_y - 10),
            (center_x - 4, center_y + 10)
        ], fill=icon_color)
        draw.polygon([
            (center_x - 2, center_y),
            (center_x - 14, center_y - 10),
            (center_x - 14, center_y + 10)
        ], fill=icon_color)
        
    elif icon_type == 'skip_forward':
        # Skip forward (double triangle + line)
        draw.polygon([
            (center_x - 8, center_y),
            (center_x + 4, center_y - 10),
            (center_x + 4, center_y + 10)
        ], fill=icon_color)
        draw.polygon([
            (center_x + 2, center_y),
            (center_x + 14, center_y - 10),
            (center_x + 14, center_y + 10)
        ], fill=icon_color)
        
    elif icon_type == 'shuffle':
        # Modern shuffle icon (crossing arrows)
        # Top arrow
        draw.line([(center_x - 10, center_y - 8), (center_x + 8, center_y - 8)], 
                 fill=icon_color, width=2)
        draw.polygon([
            (center_x + 8, center_y - 8),
            (center_x + 12, center_y - 11),
            (center_x + 12, center_y - 5)
        ], fill=icon_color)
        
        # Bottom arrow
        draw.line([(center_x - 10, center_y + 8), (center_x + 8, center_y + 8)], 
                 fill=icon_color, width=2)
        draw.polygon([
            (center_x + 8, center_y + 8),
            (center_x + 12, center_y + 5),
            (center_x + 12, center_y + 11)
        ], fill=icon_color)
        
        # Crossing lines
        draw.line([(center_x - 8, center_y - 5), (center_x + 6, center_y + 5)], 
                 fill=icon_color, width=2)
        
    elif icon_type == 'repeat':
        # Repeat icon (circular with arrows)
        draw.arc([center_x - 12, center_y - 12, center_x + 12, center_y + 12],
                start=45, end=315, fill=icon_color, width=3)
        # Top arrow
        draw.polygon([
            (center_x + 8, center_y - 9),
            (center_x + 5, center_y - 12),
            (center_x + 11, center_y - 12)
        ], fill=icon_color)
        # Bottom arrow
        draw.polygon([
            (center_x - 8, center_y + 9),
            (center_x - 5, center_y + 12),
            (center_x - 11, center_y + 12)
        ], fill=icon_color)
    
    elif icon_type == 'heart':
        # Heart/like icon
        draw.ellipse([center_x - 12, center_y - 8, center_x - 2, center_y + 2], fill=icon_color)
        draw.ellipse([center_x + 2, center_y - 8, center_x + 12, center_y + 2], fill=icon_color)
        draw.polygon([
            (center_x - 12, center_y - 2),
            (center_x, center_y + 12),
            (center_x + 12, center_y - 2)
        ], fill=icon_color)
    
    elif icon_type == 'playlist':
        # Playlist icon (3 lines with dots)
        for i, y_offset in enumerate([-8, 0, 8]):
            draw.ellipse([center_x - 12, center_y + y_offset - 2,
                         center_x - 8, center_y + y_offset + 2], fill=icon_color)
            draw.rectangle([center_x - 4, center_y + y_offset - 1,
                          center_x + 12, center_y + y_offset + 1], fill=icon_color)
    
    return button

def draw_text_with_shadow(draw, pos, text, font, color=(255, 255, 255, 255)):
    """Simple shadow for text"""
    # Shadow
    for offset in range(1, 4):
        alpha = int(120 / offset)
        draw.text((pos[0] + offset, pos[1] + offset), text, font=font, 
                 fill=(0, 0, 0, alpha))
    # Main text
    draw.text(pos, text, font=font, fill=color)

def draw_centered_text_shadow(draw, y_pos, text, font, canvas_width, color=(255, 255, 255, 255)):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = (canvas_width - text_width) // 2
    draw_text_with_shadow(draw, (x_pos, y_pos), text, font, color)
    return x_pos

def draw_modern_progress_bar(draw, x, y, width, height, progress, current_time, total_time):
    """Sleek progress bar with time stamps"""
    # Outer glow
    for i in range(2, 0, -1):
        alpha = 30 // i
        draw.rounded_rectangle(
            [(x - i, y - i), (x + width + i, y + height + i)],
            radius=(height + i*2) // 2,
            fill=(255, 255, 255, alpha)
        )
    
    # Background
    draw.rounded_rectangle(
        [(x, y), (x + width, y + height)],
        radius=height // 2,
        fill=(255, 255, 255, 60)
    )
    
    # Progress fill
    if progress > 0:
        filled_width = int(width * progress)
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + height)],
            radius=height // 2,
            fill=(255, 255, 255, 250)
        )
        
        # Knob
        knob_x = x + filled_width
        knob_y = y + height // 2
        knob_radius = height + 4
        
        # Knob glow
        for i in range(6, 0, -1):
            alpha = int(50 / i)
            draw.ellipse(
                [knob_x - knob_radius - i*2, knob_y - knob_radius - i*2,
                 knob_x + knob_radius + i*2, knob_y + knob_radius + i*2],
                fill=(255, 255, 255, alpha)
            )
        
        # Knob circle
        draw.ellipse(
            [knob_x - knob_radius, knob_y - knob_radius,
             knob_x + knob_radius, knob_y + knob_radius],
            fill=(255, 255, 255, 255)
        )

def create_info_badge(text, icon="", bg_color=(0, 0, 0, 180), font_size=14):
    """Clean info badges"""
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    full_text = f"{icon} {text}" if icon else text
    temp_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox = temp_draw.textbbox((0, 0), full_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    padding_x = 14
    padding_y = 8
    badge_width = text_width + padding_x * 2
    badge_height = text_height + padding_y * 2
    
    badge = Image.new('RGBA', (badge_width, badge_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    
    # Glow
    for i in range(3, 0, -1):
        alpha = 25 // i
        draw.rounded_rectangle(
            [(-i, -i), (badge_width + i, badge_height + i)],
            radius=(badge_height + i*2) // 2,
            fill=(255, 255, 255, alpha)
        )
    
    # Background
    draw.rounded_rectangle(
        [(0, 0), (badge_width, badge_height)],
        radius=badge_height // 2,
        fill=bg_color
    )
    
    # Border
    draw.rounded_rectangle(
        [(0, 0), (badge_width, badge_height)],
        radius=badge_height // 2,
        outline=(255, 255, 255, 120),
        width=1
    )
    
    # Text
    text_x = padding_x
    text_y = padding_y - bbox[1]
    draw.text((text_x, text_y), full_text, font=font, fill=(255, 255, 255, 255))
    
    return badge

def format_number(num):
    """Format large numbers (1.2M, 450K, etc)"""
    try:
        if isinstance(num, str):
            return num
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        return str(num)
    except:
        return str(num)

def smart_truncate(text, max_length=55):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_ultimate.png"
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
        
        # Extract all data
        title = re.sub(r"\W+", " ", video_data.get("title", "Unsupported Title")).title()
        duration = video_data.get("duration", "Live")
        thumbnail_url = video_data.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        views = video_data.get("viewCount", {}).get("short", "Unknown")
        channel = video_data.get("channel", {}).get("name", "Unknown")
        published = video_data.get("publishedTime", "Recently")
        
        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        # Create background - SHOW MORE THUMBNAIL DETAILS
        youtube_img = Image.open(temp_path)
        background = resize_to_fill(youtube_img, 1280, 720)
        
        # Less blur, more details
        background = apply_subtle_blur(background, blur_strength=6)
        
        # Enhance details
        background = enhance_thumbnail_details(background)
        
        # Light brightness reduction
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.75)
        
        # Subtle vignette
        background = add_subtle_vignette(background, strength=0.3)
        
        # Gradient only for text areas
        background = add_gradient_overlay(background)
        
        draw = ImageDraw.Draw(background)
        
        # Load fonts - SMALLER TITLE
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 32)  # Smaller
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 22)
            info_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Top section - compact
        top_y = 50
        
        # Small title at top
        title_text = smart_truncate(title, 65)
        draw_centered_text_shadow(draw, top_y, title_text, title_font, 1280)
        
        # Channel name below title
        artist_text = smart_truncate(channel, 60)
        draw_centered_text_shadow(draw, top_y + 45, artist_text, artist_font, 1280, 
                                  color=(230, 230, 255, 255))
        
        # Bottom control section - MORE SPACE BETWEEN ICONS
        bottom_y = 580
        
        # Progress bar
        bar_width = 700
        bar_height = 5
        bar_x = (1280 - bar_width) // 2
        bar_y = bottom_y
        
        if duration != "Live":
            progress = random.uniform(0.25, 0.65)
            current_time = "1:23"
            total_time = duration
        else:
            progress = 1.0
            current_time = "LIVE"
            total_time = "LIVE"
        
        draw_modern_progress_bar(draw, bar_x, bar_y, bar_width, bar_height, progress, 
                                current_time, total_time)
        
        # Time labels
        draw.text((bar_x - 50, bar_y - 3), current_time, font=info_font, 
                 fill=(255, 255, 255, 240))
        time_bbox = draw.textbbox((0, 0), total_time, font=info_font)
        time_width = time_bbox[2] - time_bbox[0]
        draw.text((bar_x + bar_width + 15, bar_y - 3), total_time, font=info_font, 
                 fill=(255, 255, 255, 240))
        
        # Control buttons - MUCH MORE SPACE (100px between each)
        controls_y = bottom_y + 45
        center_x = 640
        button_spacing = 100  # Increased spacing
        
        # Shuffle (far left)
        shuffle_btn = create_music_icon_button((75, 75), 'shuffle', False)
        background.paste(shuffle_btn, (center_x - button_spacing*2 - 37, controls_y), shuffle_btn)
        
        # Skip back
        skip_back_btn = create_music_icon_button((75, 75), 'skip_back', False)
        background.paste(skip_back_btn, (center_x - button_spacing - 37, controls_y), skip_back_btn)
        
        # Play (center, larger)
        play_btn = create_music_icon_button((100, 100), 'play', True)
        background.paste(play_btn, (center_x - 50, controls_y - 12), play_btn)
        
        # Skip forward
        skip_forward_btn = create_music_icon_button((75, 75), 'skip_forward', False)
        background.paste(skip_forward_btn, (center_x + button_spacing - 37, controls_y), skip_forward_btn)
        
        # Repeat (far right)
        repeat_btn = create_music_icon_button((75, 75), 'repeat', False)
        background.paste(repeat_btn, (center_x + button_spacing*2 - 37, controls_y), repeat_btn)
        
        # Additional controls below (Heart and Playlist)
        extra_controls_y = controls_y + 95
        
        # Heart/Like button
        heart_btn = create_music_icon_button((65, 65), 'heart', False)
        background.paste(heart_btn, (center_x - 100 - 32, extra_controls_y), heart_btn)
        
        # Playlist button
        playlist_btn = create_music_icon_button((65, 65), 'playlist', False)
        background.paste(playlist_btn, (center_x + 100 - 32, extra_controls_y), playlist_btn)
        
        # Info badges - Top corners with MORE INFO
        # Top left badges
        views_badge = create_info_badge(views, "👁", (0, 0, 0, 200), 14)
        background.paste(views_badge, (25, 25), views_badge)
        
        published_badge = create_info_badge(published, "📅", (0, 0, 0, 200), 14)
        background.paste(published_badge, (25, 70), published_badge)
        
        # Top right badges
        if duration != "Live":
            duration_badge = create_info_badge(duration, "⏱", (0, 0, 0, 200), 14)
            badge_x = 1280 - duration_badge.size[0] - 25
            background.paste(duration_badge, (badge_x, 25), duration_badge)
            
            hd_badge = create_info_badge("HD", "🎬", (0, 0, 0, 200), 14)
            hd_x = 1280 - hd_badge.size[0] - 25
            background.paste(hd_badge, (hd_x, 70), hd_badge)
            
            quality_badge = create_info_badge("4K", "✨", (0, 0, 0, 200), 14)
            quality_x = 1280 - quality_badge.size[0] - 25
            background.paste(quality_badge, (quality_x, 115), quality_badge)
        else:
            live_badge = create_info_badge("LIVE", "🔴", (200, 0, 0, 220), 14)
            badge_x = 1280 - live_badge.size[0] - 25
            background.paste(live_badge, (badge_x, 25), live_badge)
        
        # Watermark
        draw.text((1280 - 140, 720 - 30), "@siyaprobot", 
                 font=info_font, fill=(255, 255, 255, 100))
        
        # Save
        os.remove(temp_path)
        background = background.convert('RGB')
        background.save(cache_path, quality=98, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail generation failed for {videoid}: {e}")
        traceback.print_exc()
        return None