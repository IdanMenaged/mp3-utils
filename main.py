import os
import requests
from PIL import Image
from io import BytesIO
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import yt_dlp

# === USER INPUT ===
playlist_url = input("YouTube playlist URL: ").strip()
album_name = input("Album name: ").strip()
artist_name = input("Artist name: ").strip()
cover_url = input("Cover image URL: ").strip()

# === DOWNLOAD & COMPRESS COVER IMAGE ===
print("[+] Downloading cover image...")
response = requests.get(cover_url)
if response.status_code != 200:
    raise Exception("Failed to download cover image")

img = Image.open(BytesIO(response.content))
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

# Build list of (title, url) in correct order
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
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(album_name, f"{idx:02d} - %(title)s.%(ext)s"),
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

# === ADD ID3 TAGS WITH TRACK NUMBERS, TITLE (with prefix), ALBUM ARTIST ===
print("[+] Adding ID3 tags...")
files = sorted([f for f in os.listdir(album_name) if f.lower().endswith(".mp3")])

for track_num, file in enumerate(files, start=1):
    file_path = os.path.join(album_name, file)

    # Extract title without number prefix and extension
    title_only = file.split(" - ", 1)[-1].rsplit(".", 1)[0]
    title_with_number = f"{track_num:02d} - {title_only}"

    # Basic tags
    try:
        audio = EasyID3(file_path)
    except Exception:
        audio = EasyID3()
    audio['album'] = album_name
    audio['artist'] = artist_name
    audio['albumartist'] = artist_name  # Album Artist tag
    audio['title'] = title_with_number
    audio['tracknumber'] = str(track_num)
    audio.save(file_path)

    # Add cover image
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
