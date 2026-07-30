import json
import httpx
from typing import Optional
from app.core.config import settings


async def enrich_exercise(exercise: dict) -> dict:
    """Add YouTube video metadata to an exercise dictionary."""
    youtube_query = exercise.get("youtube_query") or exercise.get("name", "")
    video_info = await search_youtube(youtube_query)
    exercise["video"] = video_info
    return exercise


async def search_youtube(query: str, max_results: int = 1) -> Optional[dict]:
    """Search YouTube for exercise videos."""
    if not settings.YOUTUBE_API_KEY or settings.YOUTUBE_API_KEY == "your-youtube-api-key-here":
        return {
            "video_id": None,
            "title": f"Search: {query}",
            "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
            "thumbnail": None
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": query + " exercise tutorial",
                    "type": "video",
                    "maxResults": max_results,
                    "key": settings.YOUTUBE_API_KEY,
                    "relevanceLanguage": "en",
                    "safeSearch": "strict"
                },
                timeout=10.0
            )
            data = response.json()
            if data.get("items"):
                item = data["items"][0]
                video_id = item["id"]["videoId"]
                return {
                    "video_id": video_id,
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                    "embed_url": f"https://www.youtube.com/embed/{video_id}"
                }
    except Exception as e:
        print(f"YouTube API error: {e}")
    
    return {
        "video_id": None,
        "title": query,
        "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
        "thumbnail": None
    }
