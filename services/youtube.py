"""YouTube video id parsing and transcript fetching."""

import re

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
