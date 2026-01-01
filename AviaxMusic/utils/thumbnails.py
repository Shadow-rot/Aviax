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

def apply_romantic_blur(image, blur_strength=8):
    return image.filter(ImageFilter.GaussianBlur(blur_strength))

def cinematic_color_grading(image):
    image = image.convert('RGB')
    
    pink_overlay = Image.new('RGB', image.size, (255, 150, 180))
    image = Image.blend(image, pink_overlay, alpha=0.12)
    
    orange_overlay = Image.new('RGB', image.size, (255, 180, 120))
    image = Image.blend(image, orange_overlay, alpha=0.08)
    
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.2)
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.1)
    
    return image.convert('RGBA')

def add_bokeh_glow(image):
    glow = image.copy()
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    
    enhancer = ImageEnhance.Brightness(glow)
    glow = enhancer.enhance(1.3)
    
    return Image.blend(image, glow, alpha=0.15)

def add_vignette(image, strength=0.6):
    width, height = image.size
    vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    
    for i in range(min(width, height) // 3):
        alpha = int((i / (min(width, height) // 3)) * 255 * strength)
        alpha = 255 - alpha
        draw.rectangle(
            [(i, i), (width - i, height - i)],
            outline=(0, 0, 0, alpha)
        )
    
    return Image.alpha_composite(image, vignette)

def create_glassmorphism_card(size, blur_amount=20):
    card = Image.new('RGBA', size, (255, 255, 255, 30))
    
    noise = Image.new('RGBA', size, (255, 255, 255, 0))
    noise_draw = ImageDraw.Draw(noise)
    for _ in range(size[0] * size[1] // 100):
        x = random.randint(0, size[0] - 1)
        y = random.randint(0, size[1] - 1)
        noise_draw.point((x, y), fill=(255, 255, 255, random.randint(10, 30)))
    
    card = Image.alpha_composite(card, noise)
    card = card.filter(ImageFilter.GaussianBlur(blur_amount))
    
    border_card = Image.new('RGBA', size, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_card)
    border_draw.rounded_rectangle(
        [(0, 0), size],
        radius=30,
        fill=(255, 255, 255, 35),
        outline=(255, 255, 255, 80),
        width=2
    )
    
    return Image.alpha_composite(card, border_card)

def draw_text_with_glow(canvas, draw, pos, text, font, color, glow_color=(255, 255, 255)):
    glow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    
    for offset in range(1, 8):
        alpha = int(100 / offset)
        glow_draw.text(pos, text, font=font, fill=(*glow_color, alpha))
    
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(5))
    canvas.paste(glow_layer, (0, 0), glow_layer)
    
    for adj in range(-2, 3):
        for adj_y in range(-2, 3):
            if adj != 0 or adj_y != 0:
                draw.text((pos[0] + adj, pos[1] + adj_y), text, font=font, fill=(0, 0, 0, 150))
    
    draw.text(pos, text, font=font, fill=color)

def draw_elegant_progress_bar(draw, x, y, width, height, progress):
    base_color = (50, 50, 60, 200)
    fill_color = (200, 220, 255, 255)
    knob_color = (255, 255, 255, 255)
    
    draw.rounded_rectangle(
        [(x, y), (x + width, y + height)],
        radius=height // 2,
        fill=base_color
    )
    
    if progress > 0:
        filled_width = int(width * progress)
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + height)],
            radius=height // 2,
            fill=fill_color
        )
        
        knob_x = x + filled_width
        knob_y = y + height // 2
        knob_radius = height + 4
        
        for r in range(3):
            alpha = 50 - (r * 15)
            draw.ellipse(
                [knob_x - knob_radius - r*2, knob_y - knob_radius - r*2,
                 knob_x + knob_radius + r*2, knob_y + knob_radius + r*2],
                fill=(255, 255, 255, alpha)
            )
        
        draw.ellipse(
            [knob_x - knob_radius, knob_y - knob_radius,
             knob_x + knob_radius, knob_y + knob_radius],
            fill=knob_color
        )

def create_music_controls(size):
    controls = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(controls)
    
    center_x = size[0] // 2
    center_y = size[1] // 2
    
    play_radius = 35
    draw.ellipse(
        [center_x - play_radius, center_y - play_radius,
         center_x + play_radius, center_y + play_radius],
        fill=(255, 255, 255, 200),
        outline=(255, 255, 255, 255),
        width=2
    )
    
    play_points = [
        (center_x - 10, center_y - 15),
        (center_x - 10, center_y + 15),
        (center_x + 15, center_y)
    ]
    draw.polygon(play_points, fill=(0, 0, 0, 255))
    
    prev_x = center_x - 120
    next_x = center_x + 120
    
    for x in [prev_x, next_x]:
        direction = -1 if x == prev_x else 1
        draw.polygon([
            (x + direction * 15, center_y),
            (x - direction * 5, center_y - 12),
            (x - direction * 5, center_y + 12)
        ], fill=(255, 255, 255, 200))
        
        draw.line(
            [(x - direction * 8, center_y - 12), (x - direction * 8, center_y + 12)],
            fill=(255, 255, 255, 200),
            width=3
        )
    
    return controls

def create_rounded_badge(size, text, bg_color, icon="", font_size=20):
    badge = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=size[1] // 2,
        fill=(*bg_color, 220)
    )
    
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    full_text = f"{icon} {text}" if icon else text
    bbox = draw.textbbox((0, 0), full_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size[0] - text_width) // 2
    text_y = (size[1] - text_height) // 2
    
    draw.text((text_x, text_y), full_text, font=font, fill=(255, 255, 255, 255))
    
    return badge

def add_subtle_watermark(image, text, opacity=70):
    watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)
    
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 22)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = image.size[0] - text_width - 35
    y = image.size[1] - text_height - 30
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
    
    image = Image.alpha_composite(image, watermark)
    return image

def smart_truncate(text, max_length=40):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_romantic.png"
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
        published = video_data.get("publishedTime", "Recently")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        youtube_img = Image.open(temp_path)
        background = resize_to_fill(youtube_img, 1280, 720)
        
        background = apply_romantic_blur(background, blur_strength=10)
        
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.7)
        
        background = cinematic_color_grading(background)
        
        background = add_bokeh_glow(background)
        
        dark_overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 80))
        background = Image.alpha_composite(background, dark_overlay)
        
        background = add_vignette(background, strength=0.5)
        
        draw = ImageDraw.Draw(background)
        
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 64)
            artist_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 36)
            time_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 28)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
        
        card_width, card_height = 950, 450
        card = create_glassmorphism_card((card_width, card_height), blur_amount=25)
        card_x = (1280 - card_width) // 2
        card_y = (720 - card_height) // 2
        background.paste(card, (card_x, card_y), card)
        
        title_text = smart_truncate(title, 35)
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (1280 - title_width) // 2
        title_y = card_y + 50
        
        draw_text_with_glow(
            background, draw, (title_x, title_y), 
            title_text, title_font, (255, 255, 255, 255),
            glow_color=(255, 200, 220)
        )
        
        artist_text = smart_truncate(channel, 35)
        artist_bbox = draw.textbbox((0, 0), artist_text, font=artist_font)
        artist_width = artist_bbox[2] - artist_bbox[0]
        artist_x = (1280 - artist_width) // 2
        artist_y = title_y + 90
        
        draw_text_with_glow(
            background, draw, (artist_x, artist_y),
            artist_text, artist_font, (230, 230, 255, 255)
        )
        
        bar_width = 750
        bar_height = 8
        bar_x = (1280 - bar_width) // 2
        bar_y = artist_y + 80
        
        if duration != "Live":
            progress = random.uniform(0.25, 0.65)
        else:
            progress = 1.0
        
        draw_elegant_progress_bar(draw, bar_x, bar_y, bar_width, bar_height, progress)
        
        draw_text_with_glow(
            background, draw, (bar_x, bar_y + 25),
            "00:00", time_font, (255, 255, 255, 255)
        )
        
        duration_text = duration if duration != "Live" else "LIVE"
        duration_bbox = draw.textbbox((0, 0), duration_text, font=time_font)
        duration_width = duration_bbox[2] - duration_bbox[0]
        draw_text_with_glow(
            background, draw,
            (bar_x + bar_width - duration_width, bar_y + 25),
            duration_text, time_font, (255, 255, 255, 255)
        )
        
        controls = create_music_controls((300, 80))
        controls_x = (1280 - 300) // 2
        controls_y = bar_y + 80
        background.paste(controls, (controls_x, controls_y), controls)
        
        views_badge = create_rounded_badge((140, 45), views, (60, 60, 80), "👁", 22)
        background.paste(views_badge, (35, 35), views_badge)
        
        time_badge = create_rounded_badge((190, 45), published, (70, 50, 90), "📅", 22)
        background.paste(time_badge, (35, 95), time_badge)
        
        if duration != "Live":
            duration_badge = create_rounded_badge((130, 45), duration, (50, 70, 90), "⏱", 22)
            background.paste(duration_badge, (1280 - 165, 35), duration_badge)
        else:
            live_badge = create_rounded_badge((130, 45), "LIVE", (200, 50, 80), "🔴", 22)
            background.paste(live_badge, (1280 - 165, 35), live_badge)
        
        hd_badge = create_rounded_badge((90, 45), "HD", (180, 60, 100), "", 22)
        background.paste(hd_badge, (1280 - 125, 95), hd_badge)
        
        background = add_subtle_watermark(background, "@siyaprobot", opacity=75)
        
        os.remove(temp_path)
        background = background.convert('RGB')
        background.save(cache_path, quality=98, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail generation failed for {videoid}: {e}")
        traceback.print_exc()
        return None