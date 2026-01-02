import os
import re
import json
import yt_dlp
import random
import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython import VideosSearch, Playlist

from config import API_URL, VIDEO_API_URL, API_KEY
from AviaxMusic.utils.database import is_on_off
from AviaxMusic.utils.formatters import time_to_seconds


def get_cookie() -> Optional[str]:
    cookies = list(Path("cookies").glob("*.txt")) if Path("cookies").exists() else []
    return str(random.choice(cookies)) if cookies else None


async def api_fetch(video_id: str, endpoint: str, retries: int = 10, delay: int = 4) -> Optional[str]:
    dl_dir = Path("downloads")
    dl_dir.mkdir(exist_ok=True)
    
    for ext in ["mp3", "m4a", "webm", "mp4", "mkv"]:
        if (f := dl_dir / f"{video_id}.{ext}").exists():
            return str(f)
    
    async with aiohttp.ClientSession() as session:
        for _ in range(retries):
            try:
                async with session.get(f"{endpoint}/{video_id}?api={API_KEY}") as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    
                    if data.get("status", "").lower() == "done":
                        if url := data.get("link"):
                            ext = data.get("format", "mp3").lower()
                            path = dl_dir / f"{video_id}.{ext}"
                            async with session.get(url) as r:
                                path.write_bytes(await r.read())
                            return str(path)
                    elif data.get("status", "").lower() == "downloading":
                        await asyncio.sleep(delay)
            except Exception:
                pass
    return None


async def download_audio(link: str) -> Optional[str]:
    return await api_fetch(link.split('v=')[-1].split('&')[0], API_URL)


async def download_video(link: str) -> Optional[str]:
    return await api_fetch(link.split('v=')[-1].split('&')[0], VIDEO_API_URL, delay=8)


async def get_file_size(link: str) -> Optional[int]:
    cookie = get_cookie()
    if not cookie:
        return None
    
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "--cookies", cookie, "-J", link,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    if proc.returncode == 0:
        info = json.loads(stdout.decode())
        return sum(f.get('filesize', 0) for f in info.get('formats', []))
    return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.list_base = "https://youtube.com/playlist?list="
        self.regex = re.compile(r"(?:youtube\.com|youtu\.be)")

    async def exists(self, link: str, videoid: bool = False) -> bool:
        return bool(self.regex.search(self.base + link if videoid else link))

    async def url(self, msg: Message) -> Optional[str]:
        for m in [msg, msg.reply_to_message] if msg.reply_to_message else [msg]:
            for entity in (m.entities or []) + (m.caption_entities or []):
                if entity.type == MessageEntityType.URL:
                    text = m.text or m.caption
                    url = text[entity.offset:entity.offset + entity.length]
                    return url.split("?si=")[0] if "?si=" in url else url
                elif entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url
        return None

    async def details(self, link: str, videoid: bool = False) -> Tuple:
        link = (self.base + link if videoid else link).split("&")[0]
        results = VideosSearch(link, limit=1)
        r = (await results.next())["result"][0]
        duration_sec = 0 if r["duration"] == "None" else int(time_to_seconds(r["duration"]))
        return r["title"], r["duration"], duration_sec, r["thumbnails"][0]["url"].split("?")[0], r["id"]

    async def title(self, link: str, videoid: bool = False) -> str:
        return (await self.details(link, videoid))[0]

    async def duration(self, link: str, videoid: bool = False) -> str:
        return (await self.details(link, videoid))[1]

    async def thumbnail(self, link: str, videoid: bool = False) -> str:
        return (await self.details(link, videoid))[3]

    async def video(self, link: str, videoid: bool = False) -> Tuple[int, str]:
        link = (self.base + link if videoid else link).split("&")[0]
        
        if file := await download_video(link):
            return 1, file
        
        cookie = get_cookie()
        if not cookie:
            return 0, "No cookies found"
        
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", cookie, "-g", "-f", "best[height<=?720][width<=?1280]", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, stderr.decode())

    async def playlist(self, link: str, limit: int, user_id: int, videoid: bool = False) -> List[str]:
        try:
            plist = await Playlist.get(self.list_base + link if videoid else link)
            return [v.get("id") for v in (plist.get("videos") or [])[:limit] if v and v.get("id")]
        except:
            return []

    async def track(self, link: str, videoid: bool = False) -> Tuple[Dict, str]:
        link = (self.base + link if videoid else link).split("&")[0]
        r = (await VideosSearch(link, limit=1).next())["result"][0]
        return {
            "title": r["title"],
            "link": r["link"],
            "vidid": r["id"],
            "duration_min": r["duration"],
            "thumb": r["thumbnails"][0]["url"].split("?")[0]
        }, r["id"]

    async def formats(self, link: str, videoid: bool = False) -> Tuple[List[Dict], str]:
        link = (self.base + link if videoid else link).split("&")[0]
        cookie = get_cookie()
        if not cookie:
            return [], link
        
        with yt_dlp.YoutubeDL({"quiet": True, "cookiefile": cookie}) as ydl:
            info = ydl.extract_info(link, download=False)
            return [
                {
                    "format": f["format"],
                    "filesize": f["filesize"],
                    "format_id": f["format_id"],
                    "ext": f["ext"],
                    "format_note": f["format_note"],
                    "yturl": link
                }
                for f in info["formats"]
                if "dash" not in f["format"].lower() and all(k in f for k in ["format", "filesize", "format_id", "ext", "format_note"])
            ], link

    async def slider(self, link: str, query_type: int, videoid: bool = False) -> Tuple:
        link = (self.base + link if videoid else link).split("&")[0]
        r = (await VideosSearch(link, limit=10).next())["result"][query_type]
        return r["title"], r["duration"], r["thumbnails"][0]["url"].split("?")[0], r["id"]

    async def download(self, link: str, mystic=None, video: bool = False, videoid: bool = False,
                      songaudio: bool = False, songvideo: bool = False, 
                      format_id: Optional[str] = None, title: Optional[str] = None) -> Union[Tuple[str, bool], str]:
        link = (self.base + link if videoid else link)
        
        if songvideo or songaudio:
            return await download_audio(link) or f"downloads/{link}.mp3"
        
        if video:
            if file := await download_video(link):
                return file, True
            
            cookie = get_cookie()
            if not cookie:
                return None, None
            
            if await is_on_off(1):
                return await download_audio(link), True
            
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp", "--cookies", cookie, "-g", "-f", "best[height<=?720][width<=?1280]", link,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if stdout:
                return stdout.decode().split("\n")[0], False
            
            if (size := await get_file_size(link)) and size / (1024 * 1024) <= 250:
                cookie = get_cookie()
                opts = {
                    "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                    "outtmpl": "downloads/%(id)s.%(ext)s",
                    "quiet": True,
                    "cookiefile": cookie
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    path = Path("downloads") / f"{info['id']}.{info['ext']}"
                    if not path.exists():
                        ydl.download([link])
                    return str(path), True
            return None, None
        
        return await download_audio(link), True