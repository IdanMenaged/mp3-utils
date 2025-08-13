import os
import io
import requests
from PIL import Image
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError


def parse_artists(input_str):
    """Return list if multiple artists entered, else a single string."""
    artists = [a.strip() for a in input_str.split(",") if a.strip()]
    return artists if len(artists) > 1 else artists[0]


def download_and_compress_image(url, max_size=(500, 500), quality=85):
    """Download an image from a URL, convert to RGB if needed, compress it, and return bytes."""
    response = requests.get(url)
    response.raise_for_status()
    img = Image.open(io.BytesIO(response.content))

    # Convert RGBA (or other modes) to RGB
    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail(max_size)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=quality)
    return output.getvalue()


def retag_directory(directory, album, artist_input, cover_data=None):
    artist_value = parse_artists(artist_input)

    for filename in os.listdir(directory):
        if not filename.lower().endswith(".mp3"):
            continue

        filepath = os.path.join(directory, filename)

        # Try to load existing EasyID3 tags or create new ones
        try:
            audio = EasyID3(filepath)
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(filepath)  # must save first to create ID3 header
            audio = EasyID3(filepath)

        # Set album, artist, and albumartist
        audio["album"] = album
        audio["artist"] = artist_value
        audio["albumartist"] = artist_value

        # Title from filename without extension
        title = os.path.splitext(filename)[0]

        # Detect track number from filename start (e.g., "01 Song.mp3")
        track_num = None
        parts = title.split(" ", 1)
        if parts[0].isdigit():
            track_num = parts[0]

        if track_num:
            audio["tracknumber"] = track_num

        audio.save(filepath)

        # Add cover if provided
        if cover_data:
            id3 = ID3(filepath)
            id3["APIC"] = APIC(
                encoding=3,         # UTF-8
                mime="image/jpeg",  # MIME type
                type=3,             # Cover (front)
                desc="Cover",
                data=cover_data
            )
            id3.save(filepath)

        print(f"Retagged: {filename}")


if __name__ == "__main__":
    directory = input("Enter path to directory: ").strip()
    album = input("Enter album name: ").strip()
    artist_input = input("Enter artist(s) [comma separated if multiple]: ").strip()
    cover_url = input("Enter URL of cover image (or leave empty to skip): ").strip()

    cover_data = None
    if cover_url:
        try:
            cover_data = download_and_compress_image(cover_url)
        except Exception as e:
            print(f"Failed to download or process cover image: {e}")

    if not os.path.isdir(directory):
        print("Error: directory does not exist")
    else:
        retag_directory(directory, album, artist_input, cover_data)
