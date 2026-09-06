"""YouTube video id parsing and transcript fetching."""

import re

from youtube_transcript_api import YouTubeTranscriptApi

_ID_PATTERNS = [
    r"[?&]v=([0-9A-Za-z_-]{11})",
    r"youtu\.be/([0-9A-Za-z_-]{11})",
    r"/shorts/([0-9A-Za-z_-]{11})",
    r"/embed/([0-9A-Za-z_-]{11})",
]


def extract_video_id(url):
    for pattern in _ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("That does not look like a YouTube link.")


def fetch_transcript(video_id):
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
    except Exception:
        raise ValueError("This video has no subtitles available.")
    text = " ".join(snippet.text for snippet in fetched)
    if not text.strip():
        raise ValueError("This video has no subtitles available.")
    return text
