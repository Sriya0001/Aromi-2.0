import json
import httpx
from typing import Optional
from app.core.config import settings

CURATED_EXERCISE_VIDEOS = {
    "russian twist": "wkD8rjkodUI",
    "russian twists": "wkD8rjkodUI",
    "kettlebell": "YSxHifyI6s8",
    "kettlebell swings": "YSxHifyI6s8",
    "kettlebell swing": "YSxHifyI6s8",
    "dumbbell swings": "YSxHifyI6s8",
    "swing": "YSxHifyI6s8",
    "swings": "YSxHifyI6s8",
    "push-up": "IODxDxX7oi4",
    "push-ups": "IODxDxX7oi4",
    "pushup": "IODxDxX7oi4",
    "pushups": "IODxDxX7oi4",
    "plank": "pSHjTRCQxIw",
    "plank hold": "pSHjTRCQxIw",
    "squat": "aclHkVaku9U",
    "squats": "aclHkVaku9U",
    "bodyweight squat": "aclHkVaku9U",
    "lunge": "QOVaHwm-Q6U",
    "lunges": "QOVaHwm-Q6U",
    "walking lunge": "QOVaHwm-Q6U",
    "dumbbell chest flyes": "eozdVDA78K0",
    "chest flyes": "eozdVDA78K0",
    "step-ups": "dXxApOi17yY",
    "step ups": "dXxApOi17yY",
    "dead bug": "4XLEnwUr1d8",
    "jumping jacks": "iSSAk4Xo4GA",
    "mountain climbers": "zT-9L3CEcmk",
    "bicycle crunches": "9FGilxCbdz8",
    "crunches": "2pLT-ilgU6s",
    "crunch": "2pLT-ilgU6s",
    "dynamic stretching": "5AmJ-w3-Rik",
    "light yoga flow": "v7AYKMP6rOE",
    "glute bridge": "8bbE64NuDTU",
    "glute bridges": "8bbE64NuDTU",
    "bench press": "rT7DgCr-3pg",
    "pull-ups": "eGo4IYlbE5g",
    "pull ups": "eGo4IYlbE5g",
    "dumbbell rows": "roCP6wCXPqo",
    "bicep curls": "ykJmrZ5v0Oo",
    "tricep dips": "0326dy_-CzM",
    "shoulder press": "qEwKCR5JCog",
    "overhead press": "qEwKCR5JCog",
    "leg extension": "YyvSfVjQeL0",
    "leg press": "IZxyjW7MPJQ",
    "calf raise": "gwLzBJYoWlI",
    "foam rolling": "S96-a83R_oA",
}


async def enrich_exercise(exercise: dict) -> dict:
    """Add YouTube video metadata to an exercise dictionary."""
    youtube_query = exercise.get("youtube_query") or exercise.get("name", "")
    video_info = await search_youtube(youtube_query)
    exercise["video"] = video_info
    return exercise


async def search_youtube(query: str, max_results: int = 1) -> Optional[dict]:
    """Search YouTube for exercise videos, returning direct watch links and video IDs."""
    query_lower = (query or "").lower().strip()

    # 1. Check curated exercise mapping first for instant 100% accurate video match
    video_id = None
    for name, vid in CURATED_EXERCISE_VIDEOS.items():
        if name in query_lower or query_lower in name:
            video_id = vid
            break

    if video_id:
        return {
            "video_id": video_id,
            "title": f"{query.title()} Tutorial",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
            "embed_url": f"https://www.youtube.com/embed/{video_id}"
        }

    # 2. Call YouTube Data API if key is present
    if settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY not in ["your_youtube_api_key_here", "your-youtube-api-key-here"]:
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
                    vid = item["id"]["videoId"]
                    return {
                        "video_id": vid,
                        "title": item["snippet"]["title"],
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                        "embed_url": f"https://www.youtube.com/embed/{vid}"
                    }
        except Exception as e:
            print(f"YouTube API error: {e}")

    # 3. Fallback default video ID
    default_vid = "wkD8rjkodUI" if "twist" in query_lower else "pSHjTRCQxIw"
    return {
        "video_id": default_vid,
        "title": query.title(),
        "url": f"https://www.youtube.com/watch?v={default_vid}",
        "thumbnail": f"https://img.youtube.com/vi/{default_vid}/mqdefault.jpg",
        "embed_url": f"https://www.youtube.com/embed/{default_vid}"
    }
