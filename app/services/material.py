import os
import random
from typing import List
from urllib.parse import urlencode

import requests
from loguru import logger
from moviepy.video.io.VideoFileClip import VideoFileClip

from app.config import config
from app.models.schema import MaterialInfo, VideoAspect, VideoConcatMode
from app.utils import utils

requested_count = 0


def get_api_key(cfg_key: str):
    api_keys = config.app.get(cfg_key)
    if not api_keys:
        raise ValueError(
            f"\n\n##### {cfg_key} is not set #####\n\nPlease set it in the config.toml file: {config.config_file}\n\n"
            f"{utils.to_json(config.app)}"
        )

    # if only one key is provided, return it
    if isinstance(api_keys, str):
        return api_keys

    global requested_count
    requested_count += 1
    return api_keys[requested_count % len(api_keys)]


def search_videos_pexels(
    search_term: str,
    minimum_duration: int,
    video_aspect: VideoAspect = VideoAspect.portrait,
) -> List[MaterialInfo]:
    aspect = VideoAspect(video_aspect)
    video_orientation = aspect.name
    video_width, video_height = aspect.to_resolution()
    api_key = get_api_key("pexels_api_keys")
    headers = {
        "Authorization": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    }
    # Build URL
    params = {"query": search_term, "per_page": 20, "orientation": video_orientation}
    query_url = f"https://api.pexels.com/videos/search?{urlencode(params)}"
    logger.info(f"[PEXELS API] Searching: {query_url}")
    logger.info(f"[PEXELS API] Search term: '{search_term}' | orientation: {video_orientation} | min_duration: {minimum_duration}s")

    try:
        r = requests.get(
            query_url,
            headers=headers,
            proxies=config.proxy,
            verify=False,
            timeout=(30, 60),
        )
        response = r.json()
        video_items = []
        if "videos" not in response:
            logger.error(f"[PEXELS API] Search failed: {response}")
            return video_items
        videos = response["videos"]
        logger.info(f"[PEXELS API] Returned {len(videos)} total videos")
        # loop through each video in the result
        for v in videos:
            duration = v["duration"]
            thumb = (v.get("image") or "").strip() if isinstance(v, dict) else ""
            video_id = str(v.get("id") or "")
            tags_list = v.get("tags", [])
            tags = " ".join(tags_list) if isinstance(tags_list, list) else ""
            # check if video has desired minimum duration
            if duration < minimum_duration:
                continue
            video_files = v["video_files"]
            # loop through each url to determine the best quality
            for video in video_files:
                w = int(video["width"])
                h = int(video["height"])
                if w == video_width and h == video_height:
                    item = MaterialInfo()
                    item.provider = "pexels"
                    item.url = video["link"]
                    item.thumbnail = thumb
                    item.duration = duration
                    item.video_id = video_id
                    item.tags = tags
                    video_items.append(item)
                    logger.debug(f"[PEXELS API] Match: id={video_id} duration={duration}s tags='{tags[:60]}...'")
                    break
        logger.info(f"[PEXELS API] Filtered to {len(video_items)} videos matching criteria")
        return video_items
    except Exception as e:
        logger.error(f"[PEXELS API] Error: {str(e)}")

    return []


def search_videos_pixabay(
    search_term: str,
    minimum_duration: int,
    video_aspect: VideoAspect = VideoAspect.portrait,
) -> List[MaterialInfo]:
    aspect = VideoAspect(video_aspect)

    video_width, video_height = aspect.to_resolution()

    api_key = get_api_key("pixabay_api_keys")
    # Build URL
    params = {
        "key": api_key,
        "q": search_term,
        "video_type": "all",  # Accepted values: "all", "film", "animation"
        "per_page": 20,
    }
    query_url = f"https://pixabay.com/api/videos/?{urlencode(params)}"
    logger.info(f"[PIXABAY API] Searching: {query_url.replace(api_key, 'XXX')}")
    logger.info(f"[PIXABAY API] Search term: '{search_term}' | aspect: {video_aspect.value} | min_duration: {minimum_duration}s")

    try:
        r = requests.get(
            query_url, proxies=config.proxy, verify=False, timeout=(30, 60)
        )
        response = r.json()
        video_items = []
        if "hits" not in response:
            logger.error(f"[PIXABAY API] Search failed: {response}")
            return video_items
        videos = response["hits"]
        logger.info(f"[PIXABAY API] Returned {len(videos)} total videos")
        # loop through each video in the result
        for v in videos:
            duration = v["duration"]
            picture_id = ""
            try:
                picture_id = str(v.get("picture_id") or "").strip()
            except Exception:
                picture_id = ""
            thumb = f"https://i.vimeocdn.com/video/{picture_id}_640x360.jpg" if picture_id else ""
            video_id = str(v.get("id") or "")
            tags = str(v.get("tags") or "")
            # check if video has desired minimum duration
            if duration < minimum_duration:
                continue
            video_files = v["videos"]
            # loop through each url to determine the best quality
            for video_type in video_files:
                video = video_files[video_type]
                w = int(video["width"])
                # h = int(video["height"])
                if w >= video_width:
                    item = MaterialInfo()
                    item.provider = "pixabay"
                    item.url = video["url"]
                    item.thumbnail = thumb
                    item.duration = duration
                    item.video_id = video_id
                    item.tags = tags
                    video_items.append(item)
                    logger.debug(f"[PIXABAY API] Match: id={video_id} duration={duration}s tags='{tags[:60]}...'")
                    break
        logger.info(f"[PIXABAY API] Filtered to {len(video_items)} videos matching criteria")
        return video_items
    except Exception as e:
        logger.error(f"[PIXABAY API] Error: {str(e)}")

    return []


def save_video(video_url: str, save_dir: str = "") -> str:
    if not save_dir:
        save_dir = utils.storage_dir("cache_videos")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    url_without_query = video_url.split("?")[0]
    url_hash = utils.md5(url_without_query)
    video_id = f"vid-{url_hash}"
    video_path = f"{save_dir}/{video_id}.mp4"

    # if video already exists, return the path
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        logger.info(f"video already exists: {video_path}")
        return video_path

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    # if video does not exist, download it
    with open(video_path, "wb") as f:
        f.write(
            requests.get(
                video_url,
                headers=headers,
                proxies=config.proxy,
                verify=False,
                timeout=(60, 240),
            ).content
        )

    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            fps = clip.fps
            clip.close()
            if duration > 0 and fps > 0:
                return video_path
        except Exception as e:
            try:
                os.remove(video_path)
            except Exception:
                pass
            logger.warning(f"invalid video file: {video_path} => {str(e)}")
    return ""


def download_videos(
    task_id: str,
    search_terms: List[str],
    source: str = "pexels",
    video_aspect: VideoAspect = VideoAspect.portrait,
    video_contact_mode: VideoConcatMode = VideoConcatMode.random,
    audio_duration: float = 0.0,
    max_clip_duration: int = 5,
) -> List[str]:
    valid_video_items = []
    valid_video_urls = []
    found_duration = 0.0
    search_videos = search_videos_pexels
    if source == "pixabay":
        search_videos = search_videos_pixabay

    for search_term in search_terms:
        video_items = search_videos(
            search_term=search_term,
            minimum_duration=max_clip_duration,
            video_aspect=video_aspect,
        )
        logger.info(f"found {len(video_items)} videos for '{search_term}'")

        for item in video_items:
            if item.url not in valid_video_urls:
                valid_video_items.append(item)
                valid_video_urls.append(item.url)
                found_duration += item.duration

    logger.info(
        f"found total videos: {len(valid_video_items)}, required duration: {audio_duration} seconds, found duration: {found_duration} seconds"
    )
    video_paths = []

    material_directory = config.app.get("material_directory", "").strip()
    if material_directory == "task":
        material_directory = utils.task_dir(task_id)
    elif material_directory and not os.path.isdir(material_directory):
        material_directory = ""

    if video_contact_mode.value == VideoConcatMode.random.value:
        random.shuffle(valid_video_items)

    total_duration = 0.0
    for item in valid_video_items:
        try:
            logger.info(f"downloading video: {item.url}")
            saved_video_path = save_video(
                video_url=item.url, save_dir=material_directory
            )
            if saved_video_path:
                logger.info(f"video saved: {saved_video_path}")
                video_paths.append(saved_video_path)
                seconds = min(max_clip_duration, item.duration)
                total_duration += seconds
                if total_duration > audio_duration:
                    logger.info(
                        f"total duration of downloaded videos: {total_duration} seconds, skip downloading more"
                    )
                    break
        except Exception as e:
            logger.error(f"failed to download video: {utils.to_json(item)} => {str(e)}")
    logger.success(f"downloaded {len(video_paths)} videos")
    return video_paths


def download_video_urls(
    task_id: str,
    video_urls: List[str],
    audio_duration: float = 0.0,
    max_clip_duration: int = 5,
) -> List[str]:
    if not video_urls:
        return []

    material_directory = config.app.get("material_directory", "").strip()
    if material_directory == "task":
        material_directory = utils.task_dir(task_id)
    elif material_directory and not os.path.isdir(material_directory):
        material_directory = ""

    video_paths = []
    total_duration = 0.0
    for url in video_urls:
        if not url:
            continue
        try:
            logger.info(f"downloading selected video: {url}")
            saved_video_path = save_video(video_url=url, save_dir=material_directory)
            if not saved_video_path:
                continue
            video_paths.append(saved_video_path)

            seconds = float(max_clip_duration)
            try:
                clip = VideoFileClip(saved_video_path)
                duration = float(clip.duration or 0)
                clip.close()
                if duration > 0:
                    seconds = min(float(max_clip_duration), duration)
            except Exception:
                pass

            total_duration += seconds
            if audio_duration and total_duration > audio_duration:
                logger.info(
                    f"total duration of selected videos: {total_duration} seconds, skip downloading more"
                )
                break
        except Exception as e:
            logger.error(f"failed to download selected video: {url} => {str(e)}")
    logger.success(f"downloaded {len(video_paths)} selected videos")
    return video_paths


def download_videos_per_term(
    task_id: str,
    search_terms: List[str],
    source: str = "pexels",
    video_aspect: VideoAspect = VideoAspect.portrait,
    audio_duration: float = 0.0,
    max_clip_duration: int = 5,
    main_keyword: str = "",
    sentences: List[str] = None,
    use_semantic_scoring: bool = True,
) -> List[str]:
    """
    Download videos per term with optional semantic relevance scoring.
    
    Args:
        task_id: Task ID
        search_terms: List of search terms (one per sentence)
        source: "pexels" or "pixabay"
        video_aspect: Video aspect ratio
        audio_duration: Total audio duration (for early stopping)
        max_clip_duration: Minimum clip duration
        main_keyword: Main video subject/topic for relevance scoring
        sentences: Actual subtitle sentences for semantic matching
        use_semantic_scoring: Whether to use semantic relevance (default True)
    """
    if not search_terms:
        return []

    video_paths = []
    used_urls = set()
    total_duration = 0.0

    material_directory = config.app.get("material_directory", "").strip()
    if material_directory == "task":
        material_directory = utils.task_dir(task_id)
    elif material_directory and not os.path.isdir(material_directory):
        material_directory = ""

    # Import here to avoid circular dependency
    if use_semantic_scoring:
        try:
            from app.services.relevance import select_relevant_clip
            semantic_available = True
        except Exception as e:
            logger.warning(f"Semantic scoring unavailable, falling back to basic: {str(e)}")
            semantic_available = False
    else:
        semantic_available = False

    # When using semantic scoring, iterate over sentences; otherwise use search_terms
    items_to_process = sentences if (semantic_available and sentences) else search_terms
    
    for idx, item in enumerate(items_to_process):
        if not item:
            continue
        
        # For semantic scoring, item is the sentence; for basic search, item is the term
        sentence = item if (semantic_available and sentences) else item
        term = main_keyword or (search_terms[0] if search_terms else item)
        
        if semantic_available:
            # Use semantic relevance scoring
            try:
                result = select_relevant_clip(
                    main_keyword=main_keyword or term,
                    subtitle_sentence=sentence,
                    required_duration=float(max_clip_duration),
                    video_aspect=video_aspect,
                    sources=[source] if source in ("pexels", "pixabay") else ["pexels", "pixabay"],
                )
                
                picked_url = result.get("picked_url", "")
                if not picked_url or picked_url in used_urls:
                    logger.warning(f"No unique clip found for term '{term}'")
                    continue
                
                # Log top candidates with scores
                candidates = result.get("candidates", [])
                logger.info(f"Section {idx+1}: '{sentence[:60]}...'")
                logger.info(f"  Search queries: {result.get('search_queries', [])}")
                logger.info(f"  Top 3 candidates:")
                for i, cand in enumerate(candidates[:3]):
                    logger.info(f"    {i+1}. score={cand['score']:.3f} duration={cand['duration']}s provider={cand['provider']}")
                    logger.info(f"       url={cand['url'][:80]}...")
                logger.info(f"  Picked: score={result.get('relevance_score', 0):.3f} (cached={result.get('cached', False)})")
                
                # Download the picked clip
                saved_video_path = save_video(video_url=picked_url, save_dir=material_directory)
                if not saved_video_path:
                    continue
                
                used_urls.add(picked_url)
                video_paths.append(saved_video_path)
                seconds = min(float(max_clip_duration), float(result.get("picked_duration", max_clip_duration)))
                total_duration += seconds
                
                if audio_duration and total_duration > audio_duration:
                    break
                    
            except Exception as e:
                logger.error(f"Semantic scoring failed for term '{term}': {str(e)}")
                logger.exception(e)
                # Fall back to basic search
                semantic_available = False
        
        if not semantic_available:
            # Fallback: basic first-match search (original behavior)
            try:
                search_videos = search_videos_pexels
                if source == "pixabay":
                    search_videos = search_videos_pixabay
                
                items = search_videos(
                    search_term=term,
                    minimum_duration=max_clip_duration,
                    video_aspect=video_aspect,
                )
            except Exception as e:
                logger.warning(f"search videos failed for term '{term}': {str(e)}")
                continue

            picked = None
            for item in items:
                if not item.url:
                    continue
                if item.url in used_urls:
                    continue
                picked = item
                break
            if not picked:
                continue

            try:
                saved_video_path = save_video(video_url=picked.url, save_dir=material_directory)
                if not saved_video_path:
                    continue
                used_urls.add(picked.url)
                video_paths.append(saved_video_path)
                seconds = min(float(max_clip_duration), float(picked.duration or max_clip_duration))
                total_duration += seconds
                if audio_duration and total_duration > audio_duration:
                    break
            except Exception as e:
                logger.warning(f"failed to download picked video for term '{term}': {str(e)}")
                continue

    logger.success(f"downloaded {len(video_paths)} videos (per-term, semantic={semantic_available})")
    return video_paths


if __name__ == "__main__":
    download_videos(
        "test123", ["Money Exchange Medium"], audio_duration=100, source="pixabay"
    )
