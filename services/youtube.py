"""YouTube video id parsing and transcript fetching."""

import re

from youtube_transcript_api import (
    AgeRestricted,
    InvalidVideoId,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeTranscriptApi,
)

_ID_PATTERNS = [
    r"[?&]v=([0-9A-Za-z_-]{11})",
    r"youtu\.be/([0-9A-Za-z_-]{11})",
    r"/shorts/([0-9A-Za-z_-]{11})",
    r"/embed/([0-9A-Za-z_-]{11})",
]

_NO_SUBTITLES = "This video has no subtitles available."

# Every failure used to read as "no subtitles", which hid the real cause.
_ERROR_MESSAGES = [
    ((TranscriptsDisabled, NoTranscriptFound), _NO_SUBTITLES),
    ((VideoUnavailable, VideoUnplayable, InvalidVideoId), "That video is unavailable, private or removed."),
    ((AgeRestricted,), "Age restricted videos cannot be summarised."),
    ((RequestBlocked,), "YouTube is blocking transcript requests from this network. Try again later."),
]


def extract_video_id(url):
    for pattern in _ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("That does not look like a YouTube link.")


def _pick_transcript(listing):
    """English in any regional variant first, otherwise any language, manual before auto."""
    transcripts = sorted(listing, key=lambda transcript: transcript.is_generated)
    english = [t for t in transcripts if t.language_code.lower().startswith("en")]
    return (english or transcripts or [None])[0]


def _friendly_error(error):
    for kinds, message in _ERROR_MESSAGES:
        if isinstance(error, kinds):
            return message
    return "Could not fetch the transcript right now. Please try again."


def fetch_transcript(video_id):
    try:
        transcript = _pick_transcript(YouTubeTranscriptApi().list(video_id))
        fetched = transcript.fetch() if transcript else []
    except Exception as error:
        raise ValueError(_friendly_error(error))
    text = " ".join(snippet.text for snippet in fetched)
    if not text.strip():
        raise ValueError(_NO_SUBTITLES)
    return text
