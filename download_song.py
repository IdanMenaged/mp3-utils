import os
import re
import requests
from PIL import Image
from io import BytesIO
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import yt_dlp

def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', ' ', name).strip()

# === USER INPUT ===
video_url = input("YouTube video URL: ").strip()
album_name = sanitize_name(input("Album name: ").strip())
artist_name_input = input("Artist name(s): ").strip()
cover_url = input("Cover image URL: ").strip()

# === PARSE MULTIPLE ARTISTS ===
if "&" in artist_name_input or "," in artist_name_input:
    artist_names = [a.strip() for a in artist_name_input.replace("&", ",").split(",") if a.strip()]
else:
    artist_names = [artist_name_input]

# === DOWNLOAD & COMPRESS COVER IMAGE ===
print("[+] Downloading cover image...")
response = requests.get(cover_url)
if response.status_code != 200:
    raise Exception("Failed to download cover image")

img = Image.open(BytesIO(response.content)).convert("RGB")
img.thumbnail((500, 500), Image.Resampling.LANCZOS)
cover_buffer = BytesIO()
img.save(cover_buffer, format="JPEG", quality=85)
cover_data = cover_buffer.getvalue()

# === SETUP OUTPUT FOLDER ===
if not os.path.exists(album_name):
    os.makedirs(album_name)

# === DOWNLOAD MP3 ===
print("[+] Downloading video...")
ydl_opts = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'outtmpl': os.path.join(album_name, "%(title)s.%(ext)s"),
    'postprocessors': [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }
    ],
    'noplaylist': True,
    'cookiesfrombrowser': ('firefox',),
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(video_url, download=True)

# === ADD ID3 TAGS ===
print("[+] Adding ID3 tags...")
video_title = sanitize_name(info.get('title', 'Unknown Title'))
file_name = f"{video_title}.mp3"
file_path = os.path.join(album_name, file_name)

try:
    audio = EasyID3(file_path)
except Exception:
    audio = EasyID3()

audio['album'] = album_name
audio['artist'] = artist_names
audio['albumartist'] = artist_names
audio['title'] = video_title
audio['tracknumber'] = "1"
audio.save(file_path)

id3 = ID3(file_path)
id3.add(APIC(
    encoding=3,
    mime='image/jpeg',
    type=3,
    desc='Cover',
    data=cover_data
))
id3.save(file_path)

print(f"[✓] Done! Track saved in: {album_name}/{file_name}")
