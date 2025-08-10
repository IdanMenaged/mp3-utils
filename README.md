# mp3-utils
scripts to help with my mp3 player
## dependencies
`pip install yt-dlp mutagen Pillow requests`
<br> also you may need to install ffmpeg

## usage
### formatting an album from a youtube playlist
`python main.py`
<br> answer the prompts
<br> output should appear in the same directory as the script
<br> you can now copy-paste the directory into your player

## what does this actually do
1. download the youtube videos as mp3 files
2. add meta data (specifically id3 tags) to set stuff like album, artist, and cover
3. number the tracks so the album shows up in the correct order
4. compress the album cover to a smaller size

## TODO
- rtl support