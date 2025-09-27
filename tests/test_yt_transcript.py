from academia_mcp.tools import yt_transcript


def test_yt_transcript_base() -> None:
    result = yt_transcript("https://www.youtube.com/watch?v=21EYKqUsPfg")
    assert result is not None
    assert "chatting with richard sutton" in result.lower()


def test_yt_transcript_short_link() -> None:
    result = yt_transcript("https://youtu.be/21EYKqUsPfg?si=iity_X55GIWUQWuT")
    assert result is not None
    assert "chatting with richard sutton" in result.lower()
