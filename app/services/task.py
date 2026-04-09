import math
import os.path
import re
from os import path

from loguru import logger

from app.config import config
from app.models import const
from app.models.schema import VideoConcatMode, VideoParams
from app.services import llm, material, subtitle, video, voice
from app.services import state as sm
from app.utils import utils


def generate_script(task_id, params):
    logger.info("\n\n## generating video script")
    video_script = params.video_script.strip()
    if not video_script:
        video_script = llm.generate_script(
            video_subject=params.video_subject,
            language=params.video_language,
            paragraph_number=params.paragraph_number,
        )
    else:
        logger.debug(f"video script: \n{video_script}")

    if not video_script:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error("failed to generate video script.")
        return None

    return video_script


def generate_terms(task_id, params, video_script):
    logger.info("\n\n## generating video terms")
    video_terms = params.video_terms
    if not video_terms:
        video_terms = llm.generate_terms(
            video_subject=params.video_subject, video_script=video_script, amount=5
        )
    else:
        if isinstance(video_terms, str):
            video_terms = [term.strip() for term in re.split(r"[,，]", video_terms)]
        elif isinstance(video_terms, list):
            video_terms = [term.strip() for term in video_terms]
        else:
            raise ValueError("video_terms must be a string or a list of strings.")

        logger.debug(f"video terms: {utils.to_json(video_terms)}")

    if not video_terms:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error("failed to generate video terms.")
        return None

    return video_terms


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[\.!?。！？])\s+|\n+", text.strip())
    out = []
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        out.append(p)
    return out


def generate_sentence_terms(task_id, params, video_script):
    logger.info("\n\n## generating sentence-level video terms")
    sentences = _split_sentences(video_script)
    max_sentences = int(config.ui.get("max_sentence_terms", 30) or 30)
    if max_sentences > 0:
        sentences = sentences[:max_sentences]
    terms = []
    for s in sentences:
        try:
            generated = llm.generate_terms(
                video_subject=params.video_subject, video_script=s, amount=1
            )
            if isinstance(generated, list) and generated and isinstance(generated[0], str):
                t = generated[0].strip()
                if t:
                    terms.append(t)
        except Exception as e:
            logger.warning(f"failed to generate term for sentence: {str(e)}")
            continue

    if not terms:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error("failed to generate sentence-level video terms.")
        return None
    return terms


def save_script_data(task_id, video_script, video_terms, params):
    script_file = path.join(utils.task_dir(task_id), "script.json")
    script_data = {
        "script": video_script,
        "search_terms": video_terms,
        "params": params,
    }

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(utils.to_json(script_data))


def save_materials_data(task_id: str, downloaded_videos):
    materials_file = path.join(utils.task_dir(task_id), "materials.json")
    items = []
    for p in downloaded_videos or []:
        try:
            items.append({"path": str(p), "filename": path.basename(str(p))})
        except Exception:
            continue
    with open(materials_file, "w", encoding="utf-8") as f:
        f.write(utils.to_json({"materials": items}))


def generate_audio(task_id, params, video_script):
    '''
    Generate audio for the video script.
    If a custom audio file is provided, it will be used directly.
    There will be no subtitle maker object returned in this case.
    Otherwise, TTS will be used to generate the audio.
    Returns:
        - audio_file: path to the generated or provided audio file
        - audio_duration: duration of the audio in seconds
        - sub_maker: subtitle maker object if TTS is used, None otherwise
    '''
    logger.info("\n\n## generating audio")
    custom_audio_file = params.custom_audio_file
    if not custom_audio_file or not os.path.exists(custom_audio_file):
        if custom_audio_file:
            logger.warning(
                f"custom audio file not found: {custom_audio_file}, using TTS to generate audio."
            )
        else:
            logger.info("no custom audio file provided, using TTS to generate audio.")
        audio_file = path.join(utils.task_dir(task_id), "audio.mp3")
        sub_maker = voice.tts(
            text=video_script,
            voice_name=voice.parse_voice_name(params.voice_name),
            voice_rate=params.voice_rate,
            voice_file=audio_file,
        )
        if sub_maker is None:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                """failed to generate audio:
1. check if the language of the voice matches the language of the video script.
2. check if the network is available. If you are in China, it is recommended to use a VPN and enable the global traffic mode.
            """.strip()
            )
            return None, None, None
        audio_duration = math.ceil(voice.get_audio_duration(sub_maker))
        if audio_duration == 0:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error("failed to get audio duration.")
            return None, None, None
        return audio_file, audio_duration, sub_maker
    else:
        logger.info(f"using custom audio file: {custom_audio_file}")
        audio_duration = voice.get_audio_duration(custom_audio_file)
        if audio_duration == 0:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error("failed to get audio duration from custom audio file.")
            return None, None, None
        return custom_audio_file, audio_duration, None

def generate_subtitle(task_id, params, video_script, sub_maker, audio_file):
    '''
    Generate subtitle for the video script.
    If subtitle generation is disabled or no subtitle maker is provided, it will return an empty string.
    Otherwise, it will generate the subtitle using the specified provider.
    Returns:
        - subtitle_path: path to the generated subtitle file
    '''
    logger.info("\n\n## generating subtitle")
    if not params.subtitle_enabled or sub_maker is None:
        return ""

    subtitle_path = path.join(utils.task_dir(task_id), "subtitle.srt")
    subtitle_provider = config.app.get("subtitle_provider", "edge").strip().lower()
    logger.info(f"\n\n## generating subtitle, provider: {subtitle_provider}")

    subtitle_fallback = False
    if subtitle_provider == "edge":
        voice.create_subtitle(
            text=video_script, sub_maker=sub_maker, subtitle_file=subtitle_path
        )
        if not os.path.exists(subtitle_path):
            subtitle_fallback = True
            logger.warning("subtitle file not found, fallback to whisper")

    if subtitle_provider == "whisper" or subtitle_fallback:
        subtitle.create(audio_file=audio_file, subtitle_file=subtitle_path)
        logger.info("\n\n## correcting subtitle")
        subtitle.correct(subtitle_file=subtitle_path, video_script=video_script)

    subtitle_lines = subtitle.file_to_subtitles(subtitle_path)
    if not subtitle_lines:
        logger.warning(f"subtitle file is invalid: {subtitle_path}")
        return ""

    return subtitle_path


def get_video_materials(task_id, params, video_terms, audio_duration, video_script):
    if params.video_source == "local":
        logger.info("\n\n## preprocess local materials")
        materials = video.preprocess_video(
            materials=params.video_materials, clip_duration=params.video_clip_duration
        )
        if not materials:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                "no valid materials found, please check the materials and try again."
            )
            return None
        downloaded = [material_info.url for material_info in materials]
        save_materials_data(task_id, downloaded)
        return downloaded
    else:
        if params.video_materials:
            logger.info("\n\n## downloading selected videos")
            selected_urls = []
            for m in params.video_materials:
                if not m or not getattr(m, "url", ""):
                    continue
                selected_urls.append(m.url)
            downloaded_videos = material.download_video_urls(
                task_id=task_id,
                video_urls=selected_urls,
                audio_duration=audio_duration * params.video_count,
                max_clip_duration=params.video_clip_duration,
            )
            if not downloaded_videos:
                sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
                logger.error("failed to download videos")
                return None
            save_materials_data(task_id, downloaded_videos)
            return downloaded_videos

        if bool(getattr(params, "sentence_level_clips", False)):
            logger.info(f"\n\n## downloading videos per term from {params.video_source}")
            sentences = _split_sentences(video_script)
            downloaded_videos = material.download_videos_per_term(
                task_id=task_id,
                search_terms=video_terms,
                source=params.video_source,
                video_aspect=params.video_aspect,
                audio_duration=0.0,
                max_clip_duration=params.video_clip_duration,
                main_keyword=params.video_subject or "",
                sentences=sentences,
                use_semantic_scoring=True,
            )
            if not downloaded_videos:
                sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
                logger.error("failed to download videos per term")
                return None
            save_materials_data(task_id, downloaded_videos)
            return downloaded_videos
        logger.info(f"\n\n## downloading videos from {params.video_source}")
        downloaded_videos = material.download_videos(
            task_id=task_id,
            search_terms=video_terms,
            source=params.video_source,
            video_aspect=params.video_aspect,
            video_contact_mode=params.video_concat_mode,
            audio_duration=audio_duration * params.video_count,
            max_clip_duration=params.video_clip_duration,
        )
        if not downloaded_videos:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                "failed to download videos, maybe the network is not available. if you are in China, please use a VPN."
            )
            return None
        save_materials_data(task_id, downloaded_videos)
        return downloaded_videos


def generate_final_videos(
    task_id, params, downloaded_videos, audio_file, subtitle_path
):
    final_video_paths = []
    combined_video_paths = []
    video_concat_mode = (
        params.video_concat_mode if params.video_count == 1 else VideoConcatMode.random
    )
    video_transition_mode = params.video_transition_mode

    _progress = 50
    for i in range(params.video_count):
        index = i + 1
        combined_video_path = path.join(
            utils.task_dir(task_id), f"combined-{index}.mp4"
        )
        logger.info(f"\n\n## combining video: {index} => {combined_video_path}")
        video.combine_videos(
            combined_video_path=combined_video_path,
            video_paths=downloaded_videos,
            audio_file=audio_file,
            video_aspect=params.video_aspect,
            video_concat_mode=video_concat_mode,
            video_transition_mode=video_transition_mode,
            max_clip_duration=params.video_clip_duration,
            threads=params.n_threads,
        )

        _progress += 50 / params.video_count / 2
        sm.state.update_task(task_id, progress=_progress)

        final_video_path = path.join(utils.task_dir(task_id), f"final-{index}.mp4")

        logger.info(f"\n\n## generating video: {index} => {final_video_path}")
        video.generate_video(
            video_path=combined_video_path,
            audio_path=audio_file,
            subtitle_path=subtitle_path,
            output_file=final_video_path,
            params=params,
        )

        _progress += 50 / params.video_count / 2
        sm.state.update_task(task_id, progress=_progress)

        final_video_paths.append(final_video_path)
        combined_video_paths.append(combined_video_path)

    return final_video_paths, combined_video_paths


def start(task_id, params: VideoParams, stop_at: str = "video"):
    # Add file logging for this task
    task_log_path = path.join(utils.task_dir(task_id), "generation.log")
    log_handler_id = logger.add(
        task_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation=None,
        retention=None,
    )
    
    task_failed = False
    
    try:
        logger.info(f"start task: {task_id}, stop_at: {stop_at}")
        logger.info(f"task log file: {task_log_path}")
        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=5)

        if type(params.video_concat_mode) is str:
            params.video_concat_mode = VideoConcatMode(params.video_concat_mode)

        # 1. Generate script
        video_script = generate_script(task_id, params)
        if not video_script or "Error: " in video_script:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            return

        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=10)

        if stop_at == "script":
            sm.state.update_task(
                task_id, state=const.TASK_STATE_COMPLETE, progress=100, script=video_script
            )
            return {"script": video_script}

        # 2. Generate terms
        video_terms = ""
        if params.video_source != "local":
            if bool(getattr(params, "sentence_level_clips", False)):
                # For sentence-level clips, we use the main subject as the keyword
                # Semantic scoring will use actual sentence text for searches
                logger.info("\n\n## sentence-level clips enabled, using subject as main keyword")
                video_terms = [params.video_subject or ""]
            else:
                video_terms = generate_terms(task_id, params, video_script)
            if not video_terms:
                sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
                return

        save_script_data(task_id, video_script, video_terms, params)

        if stop_at == "terms":
            sm.state.update_task(
                task_id, state=const.TASK_STATE_COMPLETE, progress=100, terms=video_terms
            )
            return {"script": video_script, "terms": video_terms}

        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=20)

        # 3. Generate audio
        audio_file, audio_duration, sub_maker = generate_audio(
            task_id, params, video_script
        )
        if not audio_file:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            return

        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=30)

        if stop_at == "audio":
            sm.state.update_task(
                task_id,
                state=const.TASK_STATE_COMPLETE,
                progress=100,
                audio_file=audio_file,
            )
            return {"audio_file": audio_file, "audio_duration": audio_duration}

        # 4. Generate subtitle
        subtitle_path = generate_subtitle(
            task_id, params, video_script, sub_maker, audio_file
        )

        if stop_at == "subtitle":
            sm.state.update_task(
                task_id,
                state=const.TASK_STATE_COMPLETE,
                progress=100,
                subtitle_path=subtitle_path,
            )
            return {"subtitle_path": subtitle_path}

        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=40)

        # 5. Get video materials
        downloaded_videos = get_video_materials(
            task_id, params, video_terms, audio_duration, video_script
        )
        if not downloaded_videos:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            return

        if stop_at == "materials":
            sm.state.update_task(
                task_id,
                state=const.TASK_STATE_COMPLETE,
                progress=100,
                materials=downloaded_videos,
            )
            return {"materials": downloaded_videos}

        sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=50)

        # 6. Generate final videos
        final_video_paths, combined_video_paths = generate_final_videos(
            task_id, params, downloaded_videos, audio_file, subtitle_path
        )

        if not final_video_paths:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            return

        logger.success(
            f"task {task_id} finished, generated {len(final_video_paths)} videos."
        )

        kwargs = {
            "videos": final_video_paths,
            "combined_videos": combined_video_paths,
            "script": video_script,
            "terms": video_terms,
            "audio_file": audio_file,
            "audio_duration": audio_duration,
            "subtitle_path": subtitle_path,
            "materials": downloaded_videos,
        }
        sm.state.update_task(
            task_id, state=const.TASK_STATE_COMPLETE, progress=100, **kwargs
        )
        return kwargs
    except Exception as e:
        task_failed = True
        logger.error(f"Task {task_id} failed with exception: {str(e)}")
        logger.exception(e)
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        raise
    finally:
        # Remove the file handler to prevent memory leaks
        logger.remove(log_handler_id)
        
        # Force garbage collection to clean up any unreferenced resources
        import gc
        gc.collect()
        
        if task_failed:
            logger.warning(f"Task {task_id} cleanup completed after failure")


if __name__ == "__main__":
    task_id = "task_id"
    params = VideoParams(
        video_subject="金钱的作用",
        voice_name="zh-CN-XiaoyiNeural-Female",
        voice_rate=1.0,
    )
    start(task_id, params, stop_at="video")
