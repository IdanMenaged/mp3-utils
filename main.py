import os
import re
import requests
from PIL import Image
from io import BytesIO
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import yt_dlp

def sanitize_name(name):
    # Replace invalid filesystem chars with a space and strip extra spaces
    return re.sub(r'[<>:"/\\|?*]', ' ', name).strip()

# === USER INPUT ===
playlist_url = input("YouTube playlist URL: ").strip()
album_name = sanitize_name(input("Album name: ").strip())
artist_name_input = input("Artist name(s): ").strip()
cover_url = input("Cover image URL: ").strip()

# === PARSE MULTIPLE ARTISTS ===
# Split on "&" or "," and trim spaces
if "&" in artist_name_input or "," in artist_name_input:
    artist_names = [a.strip() for a in artist_name_input.replace("&", ",").split(",") if a.strip()]
else:
    artist_names = [artist_name_input]

# === DOWNLOAD & COMPRESS COVER IMAGE ===
print("[+] Downloading cover image...")
response = requests.get(cover_url)
if response.status_code != 200:
    raise Exception("Failed to download cover image")

img = Image.open(BytesIO(response.content)).convert("RGB")  # ensure RGB mode
img.thumbnail((500, 500), Image.Resampling.LANCZOS)  # Max 500px side
cover_buffer = BytesIO()
img.save(cover_buffer, format="JPEG", quality=85)
cover_data = cover_buffer.getvalue()

# === SETUP OUTPUT FOLDER ===
if not os.path.exists(album_name):
    os.makedirs(album_name)

# === FETCH PLAYLIST INFO (preserve order) ===
print("[+] Fetching playlist info...")
ydl_info_opts = {
    'extract_flat': True,
    'dump_single_json': True,
    'playlistend': 9999,
}
with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
    info = ydl.extract_info(playlist_url, download=False)

if 'entries' not in info or not info['entries']:
    raise Exception("No videos found in playlist")

playlist_videos = []
for e in info['entries']:
    if not e:
        continue
    url = e['url']
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"
    playlist_videos.append((e['title'], url))

# === DOWNLOAD MP3s IN ORDER ===
print("[+] Downloading playlist...")
for idx, (title, video_url) in enumerate(playlist_videos, start=1):
    safe_title = sanitize_name(title)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(album_name, f"{idx:02d} - {safe_title}.%(ext)s"),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }
        ],
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

# === ADD ID3 TAGS WITH MULTIPLE ARTISTS SUPPORT ===
print("[+] Adding ID3 tags...")
files = sorted([f for f in os.listdir(album_name) if f.lower().endswith(".mp3")])

for track_num, file in enumerate(files, start=1):
    file_path = os.path.join(album_name, file)

    # Extract title without number prefix and extension
    title_only = file.split(" - ", 1)[-1].rsplit(".", 1)[0]
    title_with_number = f"{track_num:02d} - {title_only}"

    try:
        audio = EasyID3(file_path)
    except Exception:
        audio = EasyID3()

    audio['album'] = album_name
    audio['artist'] = artist_names  # multiple artists as list
    audio['albumartist'] = artist_names  # same for album artist
    audio['title'] = title_with_number
    audio['tracknumber'] = str(track_num)
    audio.save(file_path)

    id3 = ID3(file_path)
    id3.add(APIC(
        encoding=3,  # UTF-8
        mime='image/jpeg',
        type=3,  # front cover
        desc='Cover',
        data=cover_data
    ))
    id3.save(file_path)

print(f"[✓] Done! {len(files)} tracks saved in: {album_name}")
