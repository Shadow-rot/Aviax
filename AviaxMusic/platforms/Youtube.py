import os,re,json,yt_dlp,random,asyncio,aiohttp
from typing import Union,Optional,Tuple,List,Dict
from pathlib import Path
from functools import lru_cache
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch,Playlist
from AviaxMusic.utils.database import is_on_off
from AviaxMusic.utils.formatters import time_to_seconds
from config import API_URL,VIDEO_API_URL,API_KEY
D=Path("downloads");C=Path("cookies");D.mkdir(exist_ok=True)
AE=("mp3","m4a","webm");VE=("mp4","webm","mkv");MS=250;AR=10;CS=16384
_s:Optional[aiohttp.ClientSession]=None;_y:Dict[str,yt_dlp.YoutubeDL]={}
async def gs()->aiohttp.ClientSession:
 global _s
 if _s is None or _s.closed:_s=aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300,connect=10),connector=aiohttp.TCPConnector(limit=20,ttl_dns_cache=300),headers={"User-Agent":"Mozilla/5.0"})
 return _s
async def cs():
 global _s
 if _s and not _s.closed:await _s.close()
@lru_cache(maxsize=1)
def gc()->Optional[str]:
 if not C.exists():return None
 ck=list(C.glob("*.txt"));return str(random.choice(ck))if ck else None
def gy(o:Dict)->yt_dlp.YoutubeDL:
 k=json.dumps(o,sort_keys=True)
 if k not in _y:_y[k]=yt_dlp.YoutubeDL(o)
 return _y[k]
def cc(v:str,e:Tuple[str,...])->Optional[str]:
 for x in e:
  p=D/f"{v}.{x}"
  if p.exists():return str(p)
 return None
async def af(v:str,ab:str,dl:int)->Optional[str]:
 u=f"{ab}/{v}?api={API_KEY}";s=await gs()
 for _ in range(AR):
  try:
   async with s.get(u)as r:
    if r.status!=200:return None
    d=await r.json();st=d.get("status","").lower()
    if st=="done":
     du=d.get("link")
     if not du:return None
     f=d.get("format","mp3");p=D/f"{v}.{f}"
     async with s.get(du)as fr:
      with open(p,'wb')as fl:
       async for ch in fr.content.iter_chunked(CS):fl.write(ch)
     return str(p)
    elif st=="downloading":await asyncio.sleep(dl)
    else:return None
  except:return None
 return None
async def da(l:str)->Optional[str]:
 v=l.split('v=')[-1].split('&')[0];c=cc(v,AE)
 if c:return c
 return await af(v,f"{API_URL}/song",4)
async def dv(l:str)->Optional[str]:
 v=l.split('v=')[-1].split('&')[0];c=cc(v,VE)
 if c:return c
 return await af(v,f"{VIDEO_API_URL}/video",8)
async def gz(l:str)->Optional[int]:
 ck=gc()
 if not ck:return None
 p=await asyncio.create_subprocess_exec("yt-dlp","--cookies",ck,"-J",l,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
 so,_=await p.communicate()
 if p.returncode!=0:return None
 try:i=json.loads(so);return sum(f.get('filesize',0)for f in i.get('formats',[]))
 except:return None
class YouTubeAPI:
 B="https://www.youtube.com/watch?v=";P="https://youtube.com/playlist?list=";R=re.compile(r"(?:youtube\.com|youtu\.be)")
 async def exists(s,l:str,v:bool=False)->bool:return bool(s.R.search(s.B+l if v else l))
 async def url(s,m:Message)->Optional[str]:
  ms=[m]+([m.reply_to_message]if m.reply_to_message else[])
  for mg in ms:
   for e in(mg.entities or[])+(mg.caption_entities or[]):
    if e.type==MessageEntityType.TEXT_LINK:return e.url.split("?si=")[0]
    if e.type==MessageEntityType.URL:t=mg.text or mg.caption;return t[e.offset:e.offset+e.length].split("?si=")[0]
  return None
 @lru_cache(maxsize=128)
 async def _f(s,l:str,v:bool=False)->Dict:
  l=(s.B+l if v else l).split("&")[0];rs=VideosSearch(l,limit=1);r=(await rs.next())["result"][0];dr=r["duration"];ds=int(time_to_seconds(dr))if dr!="None"else 0
  return{"title":r["title"],"dur":dr,"dur_sec":ds,"thumb":r["thumbnails"][0]["url"].split("?")[0],"id":r["id"],"link":r["link"]}
 async def details(s,l:str,v:bool=False)->Tuple:d=await s._f(l,v);return d["title"],d["dur"],d["dur_sec"],d["thumb"],d["id"]
 async def title(s,l:str,v:bool=False)->str:return(await s._f(l,v))["title"]
 async def duration(s,l:str,v:bool=False)->str:return(await s._f(l,v))["dur"]
 async def thumbnail(s,l:str,v:bool=False)->str:return(await s._f(l,v))["thumb"]
 async def track(s,l:str,v:bool=False)->Tuple[Dict,str]:
  d=await s._f(l,v)
  return{"title":d["title"],"link":d["link"],"vidid":d["id"],"duration_min":d["dur"],"thumb":d["thumb"]},d["id"]
 async def video(s,l:str,v:bool=False)->Tuple[int,str]:
  l=(s.B+l if v else l).split("&")[0];dl=await dv(l)
  if dl:return 1,dl
  ck=gc()
  if not ck:return 0,"No cookies"
  p=await asyncio.create_subprocess_exec("yt-dlp","--cookies",ck,"-g","-f","best[height<=?720][width<=?1280]",l,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
  so,se=await p.communicate();return(1,so.decode().split("\n")[0])if so else(0,se.decode())
 async def playlist(s,l:str,lm:int,u:int,v:bool=False)->List[str]:
  l=s.P+l if v else l
  try:p=await Playlist.get(l);return[vd["id"]for vd in(p.get("videos",[]))[:lm]if vd and vd.get("id")]
  except:return[]
 async def formats(s,l:str,v:bool=False)->Tuple[List[Dict],str]:
  l=(s.B+l if v else l).split("&")[0];ck=gc()
  if not ck:return[],l
  o={"quiet":True,"cookiefile":ck};yd=gy(o)
  try:
   i=await asyncio.get_event_loop().run_in_executor(None,lambda:yd.extract_info(l,download=False))
   fm=[]
   for f in i.get("formats",[]):
    if"dash"in str(f.get("format","")).lower():continue
    try:fm.append({"format":f["format"],"filesize":f["filesize"],"format_id":f["format_id"],"ext":f["ext"],"format_note":f["format_note"],"yturl":l})
    except KeyError:continue
   return fm,l
  except:return[],l
 async def slider(s,l:str,ix:int,v:bool=False)->Tuple:
  l=(s.B+l if v else l).split("&")[0];sr=VideosSearch(l,limit=10);r=(await sr.next())["result"][ix]
  return r["title"],r["duration"],r["thumbnails"][0]["url"].split("?")[0],r["id"]
 async def download(s,l:str,my,video:bool=False,videoid:bool=False,songaudio:bool=False,songvideo:bool=False,format_id:Optional[str]=None,title:Optional[str]=None)->Union[Tuple[str,bool],str,Tuple[None,None]]:
  l=(s.B+l if videoid else l).split("&")[0];lp=asyncio.get_event_loop()
  def yd(o:Dict)->str:
   ck=gc()
   if not ck:raise Exception("No cookies")
   o.update({"cookiefile":ck,"geo_bypass":True,"nocheckcertificate":True,"quiet":True,"no_warnings":True})
   y=gy(o);i=y.extract_info(l,download=False);ou=D/f"{i['id']}.{i['ext']}"
   if ou.exists():return str(ou)
   y.download([l]);return str(ou)
  if songaudio or songvideo:return await da(l)or f"downloads/{l}.mp3"
  if video:
   dl=await dv(l)
   if dl:return dl,True
   if await is_on_off(1):
    f=await da(l)
    return(f,True)if f else(None,None)
   ck=gc()
   if not ck:return None,None
   p=await asyncio.create_subprocess_exec("yt-dlp","--cookies",ck,"-g","-f","best[height<=?720][width<=?1280]",l,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
   so,_=await p.communicate()
   if so:return so.decode().split("\n")[0],False
   sz=await gz(l)
   if not sz or(sz/(1024*1024))>MS:return None,None
   o={"format":"(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])","outtmpl":"downloads/%(id)s.%(ext)s"}
   f=await lp.run_in_executor(None,yd,o);return f,True
  return(await da(l),True)