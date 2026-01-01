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

def apply_modern_blur(image, blur_strength=12):
    return image.filter(ImageFilter.GaussianBlur(blur_strength))

def modern_color_grading(image):
    image = image.convert('RGB')
    
    # Subtle color overlay
    overlay = Image.new('RGB', image.size, (100, 120, 150))
    image = Image.blend(image, overlay, alpha=0.08)
    
    # Enhance colors
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.15)
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.08)
    
    return image.convert('RGBA')

def add_gradient_overlay(image, start_color=(0, 0, 0, 180), end_color=(0, 0, 0, 100)):
    width, height = image.size
    gradient = Image.new('RGBA', (width, height), start_color)
    draw = ImageDraw.Draw(gradient)
    
    for y in range(height):
        alpha = int(start_color[3] + (end_color[3] - start_color[3]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    return Image.alpha_composite(image, gradient)

def draw_centered_text(draw, y_pos, text, font, canvas_width, color=(255, 255, 255, 255), shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = (canvas_width - text_width) // 2
    
    if shadow:
        # Shadow
        for offset in range(1, 4):
            draw.text((x_pos + offset, y_pos + offset), text, font=font, fill=(0, 0, 0, 120))
    
    # Main text
    draw.text((x_pos, y_pos), text, font=font, fill=color)
    return x_pos, y_pos

def draw_minimal_progress_bar(draw, x, y, width, height, progress):
    # Background track
    draw.rounded_rectangle(
        [(x, y), (x + width, y + height)],
        radius=height // 2,
        fill=(255, 255, 255, 60)
    )
    
    # Filled progress
    if progress > 0:
        filled_width = int(width * progress)
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + height)],
            radius=height // 2,
            fill=(255, 255, 255, 220)
        )
        
        # Progress knob
        knob_x = x + filled_width
        knob_y = y + height // 2
        knob_radius = height + 2
        
        draw.ellipse(
            [knob_x - knob_radius, knob_y - knob_radius,
             knob_x + knob_radius, knob_y + knob_radius],
            fill=(255, 255, 255, 255)
        )

def create_play_button(size, play=True):
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    center_x = size[0] // 2
    center_y = size[1] // 2
    radius = 28
    
    # Button background
    draw.ellipse(
        [center_x - radius, center_y - radius,
         center_x + radius, center_y + radius],
        fill=(255, 255, 255, 230)
    )
    
    # Play icon
    if play:
        play_points = [
            (center_x - 8, center_y - 12),
            (center_x - 8, center_y + 12),
            (center_x + 12, center_y)
        ]
        draw.polygon(play_points, fill=(0, 0, 0, 255))
    
    return button

def create_small_badge(text, font_size=16):
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    temp_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    padding = 12
    badge_width = text_width + padding * 2
    badge_height = text_height + padding
    
    badge = Image.new('RGBA', (badge_width, badge_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    
    draw.rounded_rectangle(
        [(0, 0), (badge_width, badge_height)],
        radius=badge_height // 2,
        fill=(0, 0, 0, 140)
    )
    
    text_x = padding
    text_y = (badge_height - text_height) // 2 - bbox[1]
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))
    
    return badge

def smart_truncate(text, max_length=45):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

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
        
        title = re.sub(r"\W+", " ", video_data.get("title", "Unsupported Title")).title()
        duration = video_data.get("duration", "Live")
        thumbnail_url = video_data.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        views = video_data.get("viewCount", {}).get("short", "Unknown")
        channel = video_data.get("channel", {}).get("name", "Unknown")
        
        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        # Create background
        youtube_img = Image.open(temp_path)
        background = resize_to_fill(youtube_img, 1280, 720)
        
        # Apply effects
        background = apply_modern_blur(background, blur_strength=15)
        
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        background = modern_color_grading(background)
        background = add_gradient_overlay(background)
        
        draw = ImageDraw.Draw(background)
        
        # Load fonts - smaller sizes
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 42)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 28)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 20)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
        
        # Center content area
        center_y = 360  # Vertical center
        
        # Draw title (centered, smaller)
        title_text = smart_truncate(title, 50)
        draw_centered_text(draw, center_y - 80, title_text, title_font, 1280)
        
        # Draw artist/channel (centered, smaller)
        artist_text = smart_truncate(channel, 50)
        draw_centered_text(draw, center_y - 20, artist_text, artist_font, 1280, color=(220, 220, 255, 255))
        
        # Progress bar (centered, compact)
        bar_width = 600
        bar_height = 5
        bar_x = (1280 - bar_width) // 2
        bar_y = center_y + 35
        
        if duration != "Live":
            progress = random.uniform(0.25, 0.65)
        else:
            progress = 1.0
        
        draw_minimal_progress_bar(draw, bar_x, bar_y, bar_width, bar_height, progress)
        
        # Time labels (small, clean)
        draw.text((bar_x, bar_y + 15), "00:00", font=time_font, fill=(255, 255, 255, 200))
        
        duration_text = duration if duration != "Live" else "LIVE"
        duration_bbox = draw.textbbox((0, 0), duration_text, font=time_font)
        duration_width = duration_bbox[2] - duration_bbox[0]
        draw.text((bar_x + bar_width - duration_width, bar_y + 15), duration_text, font=time_font, fill=(255, 255, 255, 200))
        
        # Play button (centered, below progress)
        play_btn = create_play_button((80, 80))
        play_x = (1280 - 80) // 2
        play_y = center_y + 70
        background.paste(play_btn, (play_x, play_y), play_btn)
        
        # Small badges (top corners, compact)
        views_badge = create_small_badge(f"👁 {views}", 16)
        background.paste(views_badge, (25, 25), views_badge)
        
        if duration != "Live":
            duration_badge = create_small_badge(f"⏱ {duration}", 16)
            badge_x = 1280 - duration_badge.size[0] - 25
            background.paste(duration_badge, (badge_x, 25), duration_badge)
        else:
            live_badge = create_small_badge("🔴 LIVE", 16)
            badge_x = 1280 - live_badge.size[0] - 25
            background.paste(live_badge, (badge_x, 25), live_badge)
        
        # Clean watermark (bottom right, subtle)
        watermark_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 18)
        draw.text((1280 - 150, 720 - 40), "@siyaprobot", font=watermark_font, fill=(255, 255, 255, 80))
        
        # Save
        os.remove(temp_path)
        background = background.convert('RGB')
        background.save(cache_path, quality=95, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail generation failed for {videoid}: {e}")
        traceback.print_exc()
        return None