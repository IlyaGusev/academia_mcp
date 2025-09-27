from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

from academia_mcp.settings import settings


def yt_transcript(video_url: str) -> str:
    """
    Tool to fetch the transcript of a YouTube video given its URL.

    Returns a transcript of the video as a single string.

    Args:
        video_url (str): YouTube video URL.
    """
    if "youtu.be/" in video_url:
        video_id = video_url.strip().split("youtu.be/")[-1]
    else:
        video_id = video_url.strip().split("v=")[-1]
    video_id = video_id.split("?")[0]
    proxy_config = None
    if settings.WEBSHARE_PROXY_USERNAME and settings.WEBSHARE_PROXY_PASSWORD:
        proxy_config = WebshareProxyConfig(
            proxy_username=settings.WEBSHARE_PROXY_USERNAME,
            proxy_password=settings.WEBSHARE_PROXY_PASSWORD,
        )
    api = YouTubeTranscriptApi(proxy_config=proxy_config)
    try:
        transcript = api.fetch(video_id)
    except Exception as e:
        return f"Error fetching transcript for video {video_url}: {e}"
    snippets = transcript.snippets
    return "\n".join([f"{int(entry.start)}: {' '.join(entry.text.split())}" for entry in snippets])
