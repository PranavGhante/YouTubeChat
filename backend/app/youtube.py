from urllib.parse import parse_qs, urlparse


class InvalidYouTubeUrlError(ValueError):
    pass


def extract_video_id(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if host.startswith("www."):
        host = host[4:]

    video_id = ""

    if host in {"youtube.com", "m.youtube.com"}:
        if path == "watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif path.startswith("embed/"):
            video_id = path.split("/", 1)[1].split("/", 1)[0]
        elif path.startswith("shorts/"):
            video_id = path.split("/", 1)[1].split("/", 1)[0]
    elif host == "youtu.be":
        video_id = path.split("/", 1)[0]

    if not _is_valid_video_id(video_id):
        raise InvalidYouTubeUrlError("Please enter a valid YouTube video URL.")

    return video_id


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    if hours:
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

    return f"{minutes:02d}:{remaining_seconds:02d}"


def _is_valid_video_id(video_id: str) -> bool:
    if len(video_id) != 11:
        return False

    return all(char.isalnum() or char in {"_", "-"} for char in video_id)
