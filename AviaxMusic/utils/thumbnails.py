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

def apply_advanced_blur(image, blur_strength=18):
    blurred = image.filter(ImageFilter.GaussianBlur(blur_strength))
    return Image.blend(image, blurred, 0.95)

def cinematic_grade(image):
    image = image.convert('RGB')
    
    # Deep blue-purple cinematic look
    overlay1 = Image.new('RGB', image.size, (80, 90, 140))
    image = Image.blend(image, overlay1, alpha=0.15)
    
    # Warm highlights
    overlay2 = Image.new('RGB', image.size, (255, 200, 150))
    image = Image.blend(image, overlay2, alpha=0.05)
    
    # Color enhancement
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.25)
    
    # Contrast boost
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.15)
    
    return image.convert('RGBA')

def add_advanced_gradient(image):
    width, height = image.size
    gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    
    # Multi-layer gradient
    for y in range(height):
        # Top to middle
        if y < height // 2:
            alpha = int(200 - (y / (height // 2)) * 120)
        # Middle to bottom
        else:
            alpha = int(80 + ((y - height // 2) / (height // 2)) * 100)
        
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    return Image.alpha_composite(image, gradient)

def create_glassmorphic_button(size, icon_type='play', is_primary=False):
    button = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(button)
    
    center_x = size[0] // 2
    center_y = size[1] // 2
    
    if is_primary:
        radius = 38
        # Glow effect for primary button
        for i in range(10, 0, -1):
            alpha = int(30 * (i / 10))
            draw.ellipse(
                [center_x - radius - i*2, center_y - radius - i*2,
                 center_x + radius + i*2, center_y + radius + i*2],
                fill=(255, 255, 255, alpha)
            )
        
        # Main button with gradient effect
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            fill=(255, 255, 255, 250)
        )
        
        # Inner shadow
        draw.ellipse(
            [center_x - radius + 2, center_y - radius + 2,
             center_x + radius - 2, center_y + radius - 2],
            outline=(0, 0, 0, 30),
            width=2
        )
        
        icon_color = (0, 0, 0, 255)
        icon_size = 16
    else:
        radius = 28
        # Glass effect for secondary buttons
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            fill=(255, 255, 255, 120)
        )
        
        # Border highlight
        draw.ellipse(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            outline=(255, 255, 255, 180),
            width=2
        )
        
        icon_color = (255, 255, 255, 255)
        icon_size = 12
    
    # Draw icons
    if icon_type == 'play':
        play_points = [
            (center_x - icon_size//2, center_y - icon_size),
            (center_x - icon_size//2, center_y + icon_size),
            (center_x + icon_size, center_y)
        ]
        draw.polygon(play_points, fill=icon_color)
        
    elif icon_type == 'prev':
        # Previous track icon
        draw.polygon([
            (center_x + icon_size//2, center_y),
            (center_x - icon_size//3, center_y - icon_size),
            (center_x - icon_size//3, center_y + icon_size)
        ], fill=icon_color)
        draw.rectangle(
            [center_x - icon_size//2 - 2, center_y - icon_size,
             center_x - icon_size//2, center_y + icon_size],
            fill=icon_color
        )
        
    elif icon_type == 'next':
        # Next track icon
        draw.polygon([
            (center_x - icon_size//2, center_y),
            (center_x + icon_size//3, center_y - icon_size),
            (center_x + icon_size//3, center_y + icon_size)
        ], fill=icon_color)
        draw.rectangle(
            [center_x + icon_size//2, center_y - icon_size,
             center_x + icon_size//2 + 2, center_y + icon_size],
            fill=icon_color
        )
        
    elif icon_type == 'shuffle':
        # Shuffle icon (crossed arrows)
        draw.line([center_x - icon_size, center_y - icon_size//2,
                   center_x + icon_size, center_y + icon_size//2],
                  fill=icon_color, width=2)
        draw.line([center_x - icon_size, center_y + icon_size//2,
                   center_x + icon_size, center_y - icon_size//2],
                  fill=icon_color, width=2)
        # Arrow heads
        draw.polygon([
            (center_x + icon_size - 4, center_y + icon_size//2 - 4),
            (center_x + icon_size, center_y + icon_size//2),
            (center_x + icon_size - 4, center_y + icon_size//2 + 4)
        ], fill=icon_color)
        
    elif icon_type == 'repeat':
        # Repeat icon (circular arrow)
        draw.arc([center_x - icon_size, center_y - icon_size,
                  center_x + icon_size, center_y + icon_size],
                 start=45, end=315, fill=icon_color, width=2)
        # Arrow head
        draw.polygon([
            (center_x + icon_size - 2, center_y - icon_size//2),
            (center_x + icon_size - 6, center_y - icon_size//2 - 4),
            (center_x + icon_size - 6, center_y - icon_size//2 + 4)
        ], fill=icon_color)
    
    return button

def create_frosted_card(size):
    card = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    # Main frosted glass
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=25,
        fill=(255, 255, 255, 25)
    )
    
    # Border glow
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=25,
        outline=(255, 255, 255, 60),
        width=2
    )
    
    # Inner glow
    draw.rounded_rectangle(
        [(3, 3), (size[0]-3, size[1]-3)],
        radius=23,
        outline=(255, 255, 255, 30),
        width=1
    )
    
    # Apply blur for glass effect
    card = card.filter(ImageFilter.GaussianBlur(8))
    
    return card

def draw_enhanced_text(canvas, draw, pos, text, font, color=(255, 255, 255, 255)):
    # Multi-layer shadow for depth
    for offset in range(6, 0, -1):
        alpha = int(80 / offset)
        draw.text((pos[0] + offset, pos[1] + offset), text, font=font, 
                 fill=(0, 0, 0, alpha))
    
    # Glow effect
    glow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    
    for i in range(1, 5):
        glow_draw.text(pos, text, font=font, fill=(255, 255, 255, 40 // i))
    
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(4))
    canvas.paste(glow_layer, (0, 0), glow_layer)
    
    # Main text
    draw.text(pos, text, font=font, fill=color)

def draw_centered_enhanced_text(canvas, draw, y_pos, text, font, canvas_width, color=(255, 255, 255, 255)):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = (canvas_width - text_width) // 2
    
    draw_enhanced_text(canvas, draw, (x_pos, y_pos), text, font, color)
    return x_pos, y_pos

def draw_premium_progress_bar(draw, x, y, width, height, progress):
    # Outer glow
    for i in range(3, 0, -1):
        alpha = 40 // i
        draw.rounded_rectangle(
            [(x - i, y - i), (x + width + i, y + height + i)],
            radius=(height + i*2) // 2,
            fill=(255, 255, 255, alpha)
        )
    
    # Background track with gradient effect
    draw.rounded_rectangle(
        [(x, y), (x + width, y + height)],
        radius=height // 2,
        fill=(255, 255, 255, 50)
    )
    
    # Inner shadow
    draw.rounded_rectangle(
        [(x + 1, y + 1), (x + width - 1, y + height - 1)],
        radius=height // 2,
        fill=(0, 0, 0, 20)
    )
    
    # Filled progress with gradient
    if progress > 0:
        filled_width = int(width * progress)
        
        # Progress fill
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + height)],
            radius=height // 2,
            fill=(255, 255, 255, 240)
        )
        
        # Highlight on progress
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + height // 2)],
            radius=height // 2,
            fill=(255, 255, 255, 40)
        )
        
        # Progress knob with glow
        knob_x = x + filled_width
        knob_y = y + height // 2
        knob_radius = height + 3
        
        # Knob glow
        for i in range(8, 0, -1):
            alpha = int(60 / i)
            draw.ellipse(
                [knob_x - knob_radius - i, knob_y - knob_radius - i,
                 knob_x + knob_radius + i, knob_y + knob_radius + i],
                fill=(255, 255, 255, alpha)
            )
        
        # Knob
        draw.ellipse(
            [knob_x - knob_radius, knob_y - knob_radius,
             knob_x + knob_radius, knob_y + knob_radius],
            fill=(255, 255, 255, 255)
        )
        
        # Knob highlight
        draw.ellipse(
            [knob_x - knob_radius + 2, knob_y - knob_radius + 2,
             knob_x + knob_radius - 2, knob_y + knob_radius - 2],
            fill=(255, 255, 255, 100)
        )

def create_premium_badge(text, icon="", font_size=16):
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    full_text = f"{icon} {text}" if icon else text
    temp_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox = temp_draw.textbbox((0, 0), full_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    padding_x = 16
    padding_y = 10
    badge_width = text_width + padding_x * 2
    badge_height = text_height + padding_y * 2
    
    badge = Image.new('RGBA', (badge_width, badge_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    
    # Glow effect
    for i in range(4, 0, -1):
        alpha = 30 // i
        draw.rounded_rectangle(
            [(-i, -i), (badge_width + i, badge_height + i)],
            radius=(badge_height + i*2) // 2,
            fill=(255, 255, 255, alpha)
        )
    
    # Main badge with frosted glass
    draw.rounded_rectangle(
        [(0, 0), (badge_width, badge_height)],
        radius=badge_height // 2,
        fill=(0, 0, 0, 160)
    )
    
    # Border
    draw.rounded_rectangle(
        [(0, 0), (badge_width, badge_height)],
        radius=badge_height // 2,
        outline=(255, 255, 255, 100),
        width=1
    )
    
    # Text
    text_x = padding_x
    text_y = padding_y - bbox[1]
    draw.text((text_x, text_y), full_text, font=font, fill=(255, 255, 255, 255))
    
    return badge

def add_floating_particles(image, count=30):
    particles = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(particles)
    
    for _ in range(count):
        x = random.randint(0, image.size[0])
        y = random.randint(0, image.size[1])
        size = random.randint(2, 6)
        alpha = random.randint(40, 120)
        
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=(255, 255, 255, alpha)
        )
    
    particles = particles.filter(ImageFilter.GaussianBlur(2))
    return Image.alpha_composite(image, particles)

def smart_truncate(text, max_length=45):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

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
        
        # Create premium background
        youtube_img = Image.open(temp_path)
        background = resize_to_fill(youtube_img, 1280, 720)
        
        # Advanced blur and effects
        background = apply_advanced_blur(background, blur_strength=20)
        
        # Brightness
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.55)
        
        # Color grading
        background = cinematic_grade(background)
        
        # Advanced gradient
        background = add_advanced_gradient(background)
        
        # Floating particles
        background = add_floating_particles(background, count=35)
        
        draw = ImageDraw.Draw(background)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 40)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 26)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
        
        # Center positioning
        center_y = 320
        
        # Frosted glass card
        card = create_frosted_card((900, 380))
        card_x = (1280 - 900) // 2
        card_y = center_y - 100
        background.paste(card, (card_x, card_y), card)
        
        # Title with enhanced text
        title_text = smart_truncate(title, 50)
        draw_centered_enhanced_text(background, draw, center_y - 80, title_text, title_font, 1280)
        
        # Artist/channel
        artist_text = smart_truncate(channel, 50)
        draw_centered_enhanced_text(background, draw, center_y - 25, artist_text, 
                                    artist_font, 1280, color=(230, 230, 255, 255))
        
        # Premium progress bar
        bar_width = 650
        bar_height = 6
        bar_x = (1280 - bar_width) // 2
        bar_y = center_y + 40
        
        if duration != "Live":
            progress = random.uniform(0.25, 0.65)
        else:
            progress = 1.0
        
        draw_premium_progress_bar(draw, bar_x, bar_y, bar_width, bar_height, progress)
        
        # Time labels
        draw.text((bar_x, bar_y + 18), "00:00", font=time_font, fill=(255, 255, 255, 220))
        
        duration_text = duration if duration != "Live" else "LIVE"
        duration_bbox = draw.textbbox((0, 0), duration_text, font=time_font)
        duration_width = duration_bbox[2] - duration_bbox[0]
        draw.text((bar_x + bar_width - duration_width, bar_y + 18), 
                 duration_text, font=time_font, fill=(255, 255, 255, 220))
        
        # Control buttons - arranged beautifully
        controls_y = center_y + 100
        center_x = 640
        
        # Shuffle button (far left)
        shuffle_btn = create_glassmorphic_button((70, 70), 'shuffle', False)
        background.paste(shuffle_btn, (center_x - 180, controls_y), shuffle_btn)
        
        # Previous button
        prev_btn = create_glassmorphic_button((70, 70), 'prev', False)
        background.paste(prev_btn, (center_x - 90, controls_y), prev_btn)
        
        # Play button (center - primary)
        play_btn = create_glassmorphic_button((90, 90), 'play', True)
        background.paste(play_btn, (center_x - 45, controls_y - 10), play_btn)
        
        # Next button
        next_btn = create_glassmorphic_button((70, 70), 'next', False)
        background.paste(next_btn, (center_x + 20, controls_y), next_btn)
        
        # Repeat button (far right)
        repeat_btn = create_glassmorphic_button((70, 70), 'repeat', False)
        background.paste(repeat_btn, (center_x + 110, controls_y), repeat_btn)
        
        # Premium badges
        views_badge = create_premium_badge(views, "👁", 15)
        background.paste(views_badge, (30, 30), views_badge)
        
        if duration != "Live":
            duration_badge = create_premium_badge(duration, "⏱", 15)
            badge_x = 1280 - duration_badge.size[0] - 30
            background.paste(duration_badge, (badge_x, 30), duration_badge)
            
            hd_badge = create_premium_badge("HD", "", 15)
            hd_x = 1280 - hd_badge.size[0] - 30
            background.paste(hd_badge, (hd_x, 80), hd_badge)
        else:
            live_badge = create_premium_badge("LIVE", "🔴", 15)
            badge_x = 1280 - live_badge.size[0] - 30
            background.paste(live_badge, (badge_x, 30), live_badge)
        
        # Elegant watermark
        watermark_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 16)
        draw.text((1280 - 145, 720 - 35), "@siyaprobot", 
                 font=watermark_font, fill=(255, 255, 255, 90))
        
        # Save
        os.remove(temp_path)
        background = background.convert('RGB')
        background.save(cache_path, quality=98, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail generation failed for {videoid}: {e}")
        traceback.print_exc()
        return None