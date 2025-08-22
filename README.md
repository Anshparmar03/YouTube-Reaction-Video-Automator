# YouTube Reaction Video Automator

## Overview
This Python application automates the creation and uploading of reaction videos to your YouTube channel. It fetches the top 10 trending YouTube videos for a specified region, records your webcam reaction while playing each video, composites the original and reaction footage into a split-screen format (side-by-side), and uploads the result to your YouTube channel.

## Features
- **Fetch Trending Videos**: Retrieves the top 10 trending videos using the YouTube Data API v3.
- **Download Videos**: Downloads videos with `yt-dlp`.
- **Record Reaction**: Plays the video while capturing your live webcam reaction using OpenCV.
- **Split-Screen Compositing**: Combines original and reaction videos into a half-screen format using FFmpeg.
- **Upload to YouTube**: Uploads the final video to your channel via the YouTube API with OAuth authentication.

## How Will It Work:
1. Fetches top 10 trending videos for your region.
2. Downloads each video (note: against YouTube terms).
3. Plays the video while recording your webcam reaction.
4. Creates a split-screen video (original on left, reaction on right) with FFmpeg.
5. Uploads the video to your YouTube channel as a private video (editable to public).

## License
MIT License. This is a project made for fun and should be used respecting YouTube's terms and copyright laws.
```
