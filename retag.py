import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError


def parse_artists(input_str):
    """Return list if multiple artists entered, else a single string."""
    artists = [a.strip() for a in input_str.split(",") if a.strip()]
    return artists if len(artists) > 1 else artists[0]


def retag_directory(directory, album, artist_input):
    artist_value = parse_artists(artist_input)

    for filename in os.listdir(directory):
        if not filename.lower().endswith(".mp3"):
            continue

        filepath = os.path.join(directory, filename)

        # Try to load existing tags or create new ones
        try:
            audio = EasyID3(filepath)
        except ID3NoHeaderError:
            audio = EasyID3()

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

        # Save changes
        audio.save(filepath)
        print(f"Retagged: {filename}")


if __name__ == "__main__":
    directory = input("Enter path to directory: ").strip()
    album = input("Enter album name: ").strip()
    artist_input = input("Enter artist(s) [comma separated if multiple]: ").strip()

    if not os.path.isdir(directory):
        print("Error: directory does not exist")
    else:
        retag_directory(directory, album, artist_input)
