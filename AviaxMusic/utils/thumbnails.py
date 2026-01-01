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

def resize_image(max_width, max_height, image):
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    new_width = int(width_ratio * image.size[0])
    new_height = int(height_ratio * image.size[1])
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def smart_truncate(text, line1_max=40, line2_max=40):
    words = text.split(" ")
    line1, line2 = "", ""
    
    for word in words:
        if len(line1) + len(word) + 1 <= line1_max:
            line1 += (" " if line1 else "") + word
        elif len(line2) + len(word) + 1 <= line2_max:
            line2 += (" " if line2 else "") + word
        else:
            break
    
    if line2 and len(line2) > line2_max - 3:
        line2 = line2[:line2_max - 3] + "..."
    
    return [line1.strip(), line2.strip()]

def create_gradient(width, height, color1, color2, color3=None):
    gradient = Image.new('RGBA', (width, height), color1)
    overlay = Image.new('RGBA', (width, height), color2)
    mask = Image.new('L', (width, height))
    
    mask_data = []
    for y in range(height):
        for x in range(width):
            radial = ((x - width/2)**2 + (y - height/2)**2)**0.5
            max_distance = ((width/2)**2 + (height/2)**2)**0.5
            intensity = int(180 * (1 - radial / max_distance))
            mask_data.append(max(0, min(255, intensity)))
    
    mask.putdata(mask_data)
    gradient = Image.composite(overlay, gradient, mask)
    
    if color3:
        accent = Image.new('RGBA', (width, height), color3)
        gradient = Image.blend(gradient, accent, alpha=0.15)
    
    return gradient

def create_circular_thumbnail(img, size, border_width, border_colors):
    crop_size = int(size * 1.4)
    center_x, center_y = img.size[0] / 2, img.size[1] / 2
    
    img = img.crop((
        center_x - crop_size/2,
        center_y - crop_size/2,
        center_x + crop_size/2,
        center_y + crop_size/2
    ))
    
    inner_size = size - 2 * border_width
    img = img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
    
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    if isinstance(border_colors, tuple):
        border_img = Image.new("RGBA", (size, size), border_colors)
    else:
        border_img = create_gradient(size, size, border_colors[0], border_colors[1])
    
    border_mask = Image.new("L", (size, size), 0)
    border_draw = ImageDraw.Draw(border_mask)
    border_draw.ellipse((0, 0, size, size), fill=255)
    
    result.paste(border_img, (0, 0), border_mask)
    
    img_mask = Image.new("L", (inner_size, inner_size), 0)
    img_draw = ImageDraw.Draw(img_mask)
    img_draw.ellipse((0, 0, inner_size, inner_size), fill=255)
    
    result.paste(img, (border_width, border_width), img_mask)
    
    return result

def draw_text_shadow(canvas, draw, pos, text, font, color, shadow_offset=(4, 4), shadow_blur=6):
    shadow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    
    shadow_x = pos[0] + shadow_offset[0]
    shadow_y = pos[1] + shadow_offset[1]
    shadow_draw.text((shadow_x, shadow_y), text, font=font, fill=(0, 0, 0, 180))
    
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas.paste(shadow_layer, (0, 0), shadow_layer)
    
    draw.text(pos, text, font=font, fill=color)

def create_progress_bar(draw, start_pos, length, height, progress, colors):
    bar_rect = [start_pos, (start_pos[0] + length, start_pos[1] + height)]
    draw.rounded_rectangle(bar_rect, radius=height//2, fill=(40, 40, 40, 200))
    
    if progress > 0:
        filled_length = int(length * progress)
        filled_rect = [start_pos, (start_pos[0] + filled_length, start_pos[1] + height)]
        draw.rounded_rectangle(filled_rect, radius=height//2, fill=colors[0])
        
        circle_center = (start_pos[0] + filled_length, start_pos[1] + height//2)
        circle_radius = height//2 + 3
        draw.ellipse([
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius
        ], fill=colors[1])

def create_info_badge(text, color, position, canvas):
    badge = Image.new('RGBA', (150, 50), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge)
    
    badge_draw.rounded_rectangle([(0, 0), (150, 50)], radius=25, fill=(*color, 200))
    
    try:
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 22)
    except:
        font = ImageFont.load_default()
    
    bbox = badge_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_pos = ((150 - text_width) // 2, (50 - text_height) // 2)
    
    badge_draw.text(text_pos, text, font=font, fill=(255, 255, 255))
    canvas.paste(badge, position, badge)

async def gen_thumb(videoid: str):
    try:
        cache_path = f"cache/{videoid}_enhanced.png"
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
        views = video_data.get("viewCount", {}).get("short", "Unknown Views")
        channel = video_data.get("channel", {}).get("name", "Unknown Channel")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    return None
                
                temp_path = f"cache/temp_{videoid}.png"
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(await resp.read())
        
        youtube_img = Image.open(temp_path)
        resized_bg = resize_image(1280, 720, youtube_img)
        
        background = resized_bg.convert("RGBA").filter(ImageFilter.GaussianBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.4)
        
        color_scheme = [
            (random.randint(80, 160), random.randint(40, 120), random.randint(100, 180)),
            (random.randint(20, 80), random.randint(60, 140), random.randint(120, 200)),
            (random.randint(140, 200), random.randint(80, 140), random.randint(60, 120))
        ]
        
        gradient = create_gradient(1280, 720, color_scheme[0], color_scheme[1], color_scheme[2])
        background = Image.blend(background, gradient, alpha=0.35)
        
        draw = ImageDraw.Draw(background)
        
        try:
            title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 52)
            main_font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 32)
            small_font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 28)
        except:
            title_font = ImageFont.load_default()
            main_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        circle_thumb = create_circular_thumbnail(
            youtube_img, 
            440, 
            8, 
            (color_scheme[0], color_scheme[1])
        )
        background.paste(circle_thumb, (100, 140), circle_thumb)
        
        text_x = 600
        title_lines = smart_truncate(title)
        
        draw_text_shadow(background, draw, (text_x, 160), title_lines[0], title_font, (255, 255, 255))
        if title_lines[1]:
            draw_text_shadow(background, draw, (text_x, 220), title_lines[1], title_font, (255, 255, 255))
        
        draw_text_shadow(background, draw, (text_x, 300), f"🎵 {channel}", main_font, (240, 240, 240))
        draw_text_shadow(background, draw, (text_x, 345), f"👁 {views}", small_font, (220, 220, 220))
        
        if duration != "Live":
            progress = random.uniform(0.15, 0.75)
            create_progress_bar(
                draw, 
                (text_x, 420), 
                600, 
                10, 
                progress, 
                (color_scheme[1], color_scheme[2])
            )
            
            draw_text_shadow(background, draw, (text_x, 445), "00:00", small_font, (255, 255, 255))
            draw_text_shadow(background, draw, (1120, 445), duration, small_font, (255, 255, 255))
        else:
            create_progress_bar(draw, (text_x, 420), 600, 10, 1.0, ((255, 50, 50), (255, 100, 100)))
            create_info_badge("🔴 LIVE", (255, 0, 0), (text_x, 450), background)
        
        try:
            controls = Image.open("AviaxMusic/assets/play_icons.png")
            controls = controls.resize((600, 70), Image.Resampling.LANCZOS)
            background.paste(controls, (text_x, 510), controls)
        except:
            pass
        
        os.remove(temp_path)
        background.save(cache_path, quality=95)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Thumbnail generation failed for {videoid}: {e}")
        traceback.print_exc()
        return None