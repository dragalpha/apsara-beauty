import os
from typing import List, Dict

from googleapiclient.discovery import build


def search_reviews(product_name: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Search YouTube for product review videos.
    Requires YOUTUBE_API_KEY via environment variable.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return []

    youtube = build("youtube", "v3", developerKey=api_key)

    query = f"{product_name} review"
    request = youtube.search().list(
        part="snippet",
        maxResults=max_results,
        q=query,
        type="video",
        safeSearch="moderate",
    )
    response = request.execute()

    results: List[Dict[str, str]] = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        results.append(
            {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            }
        )

    return results



