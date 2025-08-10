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
# Resize so largest side is 500px to save space
img.thumbnail((500, 500), Image.Resampling.LANCZOS)
cover_buffer = BytesIO()
img.save(cover_buffer, format="JPEG", quality=85)
cover_data = cover_buffer.getvalue()

# === SETUP OUTPUT FOLDER ===
if not os.path.exists(album_name):
    os.makedirs(album_name)

# === DOWNLOAD PLAYLIST AS MP3 ===
print("[+] Downloading playlist...")
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(album_name, '%(title)s.%(ext)s'),
    'postprocessors': [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }
    ],
    'noplaylist': False
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([playlist_url])

# === ADD ID3 TAGS TO FILES ===
print("[+] Adding ID3 tags...")
for file in os.listdir(album_name):
    if file.lower().endswith(".mp3"):
        file_path = os.path.join(album_name, file)

        # Basic tags
        try:
            audio = EasyID3(file_path)
        except Exception:
            audio = EasyID3()
        audio['album'] = album_name
        audio['artist'] = artist_name
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

print("[✓] Done! Files saved in:", album_name)
