def get_embed_url(video_url: str) -> str:
    """
    Converts a standard YouTube URL to an embed URL.
    Returns the original URL if it's not a recognized YouTube URL or is empty.
    """
    if not video_url:
        return ""

    if video_url.startswith("https://youtu.be/"):
        return video_url.replace("https://youtu.be/", "https://www.youtube.com/embed/")

    if "watch?v=" in video_url:
        video_id = video_url.rsplit("watch?v=", maxsplit=1)[-1]
        if "&" in video_id:
            video_id = video_id.split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"

    return video_url


def get_device_filter(request) -> str:
    """
    Extracts the device type from the request query parameters.
    Defaults to 'PC' if not specified or invalid.
    """
    device_type = request.query_params.get("device", "PC")
    return "Mobile" if device_type.lower() == "mobile" else "PC"
