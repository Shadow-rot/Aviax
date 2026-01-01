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

def smart_truncate(text, max_length=45):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def create_rounded_overlay(size, radius, color, opacity=180):
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle([(0, 0), size], radius=radius, fill=(*color, opacity))
    return overlay

def draw_text_with_stroke(draw, pos, text, font, fill_color, stroke_color=(0, 0, 0), stroke_width=3):
    x, y = pos
    for adj_x in range(-stroke_width, stroke_width + 1):
        for adj_y in range(-stroke_width, stroke_width + 1):
            draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
    draw.text(pos, text, font=font, fill=fill_color)

def create_glassmorphism_card(size, color=(255, 255, 255), blur_amount=15):
    card = Image.new('RGBA', size, (*color, 40))
    blurred = card.filter(ImageFilter.GaussianBlur(blur_amount))
    return blurred

def draw_progress_bar(draw, x, y, width, height, progress, color1, color2):
    draw.rounded_rectangle(
        [(x, y), (x + width, y + height)],
        radius=height // 2,
        fill=(30, 30, 30, 180)
    )
    
    if progress > 0:
        filled_width = int(width * progress)
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + height)],
            radius=height // 2,
            fill=color1
        )
        
        circle_x = x + filled_width
        circle_y = y + height // 2
        circle_radius = height // 2 + 4
        draw.ellipse(
            [circle_x - circle_radius, circle_y - circle_radius,
             circle_x + circle_radius, circle_y + circle_radius],
            fill=color2
        )

def create_info_badge(size, text, bg_color, icon=""):
    badge = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=size[1] // 2,
        fill=(*bg_color, 220)
    )
    
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", size[1] - 16)
    except:
        font = ImageFont.load_default()
    
    full_text = f"{icon} {text}" if icon else text
    bbox = draw.textbbox((0, 0), full_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size[0] - text_width) // 2
    text_y = (size[1] - text_height) // 2
    
    draw.text((text_x, text_y), full_text, font=font, fill=(255, 255, 255))
    
    return badge

def add_watermark(image, text, position='bottom_right', opacity=60):
    watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)
    
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    if position == 'bottom_right':
        x = image.size[0] - text_width - 30
        y = image.size[1] - text_height - 25
    elif position == 'bottom_left':
        x = 30
        y = image.size[1] - text_height - 25
    else:
        x = 30
        y = 30
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
    
    image.paste(watermark_layer, (0, 0), watermark_layer)
    return image

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_v5.png"
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
        
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5)
        
        vignette = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        vignette_draw = ImageDraw.Draw(vignette)
        for i in range(200):
            alpha = int((i / 200) * 120)
            vignette_draw.rectangle(
                [(i, i), (1280 - i, 720 - i)],
                outline=(0, 0, 0, alpha)
            )
        background.paste(vignette, (0, 0), vignette)
        
        overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 100))
        background = Image.alpha_composite(background.convert('RGBA'), overlay)
        
        draw = ImageDraw.Draw(background)
        
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 58)
            info_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 32)
            small_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 26)
            tiny_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 22)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            tiny_font = ImageFont.load_default()
        
        center_card = create_glassmorphism_card((900, 400), (20, 20, 20))
        card_x = (1280 - 900) // 2
        card_y = (720 - 400) // 2
        background.paste(center_card, (card_x, card_y), center_card)
        
        title_text = smart_truncate(title, 40)
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (1280 - title_width) // 2
        title_y = card_y + 40
        
        draw_text_with_stroke(draw, (title_x, title_y), title_text, title_font, (255, 255, 255))
        
        channel_text = f"🎵 {smart_truncate(channel, 30)}"
        channel_bbox = draw.textbbox((0, 0), channel_text, font=info_font)
        channel_width = channel_bbox[2] - channel_bbox[0]
        channel_x = (1280 - channel_width) // 2
        channel_y = title_y + 80
        
        draw_text_with_stroke(draw, (channel_x, channel_y), channel_text, info_font, (255, 255, 255))
        
        if duration != "Live":
            progress = random.uniform(0.2, 0.7)
            bar_width = 700
            bar_x = (1280 - bar_width) // 2
            bar_y = channel_y + 80
            
            draw_progress_bar(
                draw, bar_x, bar_y, bar_width, 12, progress,
                (100, 180, 255), (150, 200, 255)
            )
            
            draw_text_with_stroke(draw, (bar_x, bar_y + 25), "00:00", small_font, (255, 255, 255))
            
            duration_bbox = draw.textbbox((0, 0), duration, font=small_font)
            duration_width = duration_bbox[2] - duration_bbox[0]
            draw_text_with_stroke(
                draw,
                (bar_x + bar_width - duration_width, bar_y + 25),
                duration,
                small_font,
                (255, 255, 255)
            )
        else:
            bar_width = 700
            bar_x = (1280 - bar_width) // 2
            bar_y = channel_y + 80
            
            draw_progress_bar(
                draw, bar_x, bar_y, bar_width, 12, 1.0,
                (255, 50, 50), (255, 100, 100)
            )
            
            live_badge = create_info_badge((150, 45), "LIVE", (255, 0, 0), "🔴")
            live_x = (1280 - 150) // 2
            background.paste(live_badge, (live_x, bar_y + 25), live_badge)
        
        try:
            controls = Image.open("AviaxMusic/assets/play_icons.png")
            controls = controls.resize((600, 60), Image.Resampling.LANCZOS)
            controls_x = (1280 - 600) // 2
            controls_y = card_y + 300
            
            if controls.mode == 'RGBA':
                background.paste(controls, (controls_x, controls_y), controls)
            else:
                background.paste(controls, (controls_x, controls_y))
        except Exception as e:
            logging.warning(f"Could not load play icons: {e}")
        
        views_badge = create_info_badge((140, 40), views, (80, 80, 80), "👁")
        background.paste(views_badge, (30, 30), views_badge)
        
        time_badge = create_info_badge((180, 40), published, (60, 60, 60), "📅")
        background.paste(time_badge, (30, 85), time_badge)
        
        if duration != "Live":
            duration_corner_badge = create_info_badge((120, 40), duration, (40, 40, 40), "⏱")
            background.paste(duration_corner_badge, (1280 - 150, 30), duration_corner_badge)
        
        quality_badge = create_info_badge((90, 40), "HD", (200, 50, 50))
        background.paste(quality_badge, (1280 - 120, 85), quality_badge)
        
        background = add_watermark(background, "@siyaprobot", "bottom_right", opacity=70)
        
        os.remove(temp_path)
        background = background.convert('RGB')
        background.save(cache_path, quality=95, optimize=True)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail generation failed for {videoid}: {e}")
        traceback.print_exc()
        return None