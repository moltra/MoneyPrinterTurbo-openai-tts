import os
import platform
import pathlib
import json
import re
import shutil
import signal
import sys
import time
from uuid import uuid4

import requests
import streamlit as st
from loguru import logger

# Add the root directory of the project to the system path to allow importing modules from the project
root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    print("******** sys.path ********")
    print(sys.path)
    print("")

from app.config import config
from app.models.schema import (
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.services import llm, voice
from app.utils import utils

st.set_page_config(
    page_title="MoneyPrinterTurbo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Report a bug": "https://github.com/harry0703/MoneyPrinterTurbo/issues",
        "About": "# MoneyPrinterTurbo\nSimply provide a topic or keyword for a video, and it will "
        "automatically generate the video copy, video materials, video subtitles, "
        "and video background music before synthesizing a high-definition short "
        "video.\n\nhttps://github.com/harry0703/MoneyPrinterTurbo",
    },
)


is_dev_mode = (os.environ.get("MPT_MODE", "") or "").strip().lower() == "dev"


streamlit_style = """
<style>
h1 {
    padding-top: 0 !important;
}
</style>
"""
st.markdown(streamlit_style, unsafe_allow_html=True)

if is_dev_mode:
    st.markdown(
        """
<style>
  /* DEV mode tint */
  [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, rgba(255, 239, 213, 0.35) 0%, rgba(255, 239, 213, 0.0) 40%);
  }
  [data-testid="stHeader"] {
    background: rgba(255, 239, 213, 0.65);
  }
</style>
""",
        unsafe_allow_html=True,
    )


def _api_base_url() -> str:
    base_url = (os.environ.get("MPT_API_BASE_URL", "") or "").strip()
    if base_url:
        base_url = base_url.rstrip("/")
        try:
            if os.path.exists("/.dockerenv") and base_url.endswith(":8089"):
                return "http://moneyprinterturbo-dev-api:8080"
        except Exception:
            pass
        return base_url
    return "http://127.0.0.1:8080"


def _public_api_base_url() -> str:
    base_url = (os.environ.get("MPT_PUBLIC_API_BASE_URL", "") or "").strip()
    if base_url:
        return base_url.rstrip("/")
    return _api_base_url()


def _safe_task_dir(task_id: str) -> pathlib.Path:
    base_dir = pathlib.Path(utils.task_dir()).resolve()
    candidate = (base_dir / (task_id or "")).resolve()
    candidate.relative_to(base_dir)
    return candidate


def _list_task_ids(limit: int = 50) -> list[str]:
    tasks_dir = pathlib.Path(utils.task_dir()).resolve()
    if not tasks_dir.exists():
        return []
    items = []
    for p in tasks_dir.iterdir():
        if not p.is_dir():
            continue
        try:
            mtime = p.stat().st_mtime
        except Exception:
            mtime = 0
        items.append((mtime, p.name))
    items.sort(reverse=True)
    return [name for _, name in items[: max(0, int(limit or 0))]]


def _task_file_url(public_api_base_url: str, task_id: str, filename: str) -> str:
    base = (public_api_base_url or "").rstrip("/")
    return f"{base}/tasks/{task_id}/{filename}"


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[\.!?。！？])\s+|\n+", (text or "").strip())
    out = []
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        out.append(p)
    return out


def _search_stock_videos(
    api_base_url: str,
    provider: str,
    search_term: str,
    minimum_duration: int,
    video_aspect: str,
    limit: int,
) -> list[dict]:
    logger.info(
        utils.to_json(
            {
                "event": "stock_video_search",
                "provider": provider,
                "search_term": search_term,
                "minimum_duration": int(minimum_duration or 0),
                "video_aspect": video_aspect,
                "limit": int(limit or 20),
            }
        )
    )
    resp = requests.post(
        f"{api_base_url}/api/v1/stock_videos/search",
        headers=_api_headers(),
        json={
            "provider": provider,
            "search_term": search_term,
            "minimum_duration": int(minimum_duration or 0),
            "video_aspect": video_aspect,
            "limit": int(limit or 20),
        },
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json() if resp.content else {}
    items = (body.get("data") or {}).get("items") or []
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if isinstance(it, dict) and it.get("url"):
            out.append(it)
    return out


def _api_key() -> str:
    return (os.environ.get("MPT_API_KEY", "") or config.app.get("api_key", "") or "").strip()


def _api_headers() -> dict:
    api_key = _api_key()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    return headers

# 定义资源目录
font_dir = os.path.join(root_dir, "resource", "fonts")
song_dir = os.path.join(root_dir, "resource", "songs")
i18n_dir = os.path.join(root_dir, "webui", "i18n")
config_file = os.path.join(root_dir, "webui", ".streamlit", "webui.toml")
system_locale = utils.get_system_locale()


if "video_subject" not in st.session_state:
    st.session_state["video_subject"] = ""
if "video_script" not in st.session_state:
    st.session_state["video_script"] = ""
if "video_terms" not in st.session_state:
    st.session_state["video_terms"] = ""
if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = config.ui.get("language", system_locale)

# 加载语言文件
locales = utils.load_locales(i18n_dir)

# 创建一个顶部栏，包含标题和语言选择
title_col, lang_col = st.columns([3, 1])

with title_col:
    if is_dev_mode:
        st.title(f"MoneyPrinterTurbo DEV v{config.project_version}")
    else:
        st.title(f"MoneyPrinterTurbo v{config.project_version}")

with lang_col:
    display_languages = []
    selected_index = 0
    for i, code in enumerate(locales.keys()):
        display_languages.append(f"{code} - {locales[code].get('Language')}")
        if code == st.session_state.get("ui_language", ""):
            selected_index = i

    selected_language = st.selectbox(
        "Language / 语言",
        options=display_languages,
        index=selected_index,
        key="top_language_selector",
        label_visibility="collapsed",
    )
    if selected_language:
        code = selected_language.split(" - ")[0].strip()
        st.session_state["ui_language"] = code
        config.ui["language"] = code

support_locales = [
    "zh-CN",
    "zh-HK",
    "zh-TW",
    "de-DE",
    "en-US",
    "fr-FR",
    "vi-VN",
    "th-TH",
    "tr-TR",
]


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs


def open_task_folder(task_id):
    try:
        sys = platform.system()
        path = os.path.join(root_dir, "storage", "tasks", task_id)
        if os.path.exists(path):
            if sys == "Windows":
                os.system(f"start {path}")
            if sys == "Darwin":
                os.system(f"open {path}")
    except Exception as e:
        logger.error(e)


def scroll_to_bottom():
    js = """
    <script>
        console.log("scroll_to_bottom");
        function scroll(dummy_var_to_force_repeat_execution){
            var sections = parent.document.querySelectorAll('section.main');
            console.log(sections);
            for(let index = 0; index<sections.length; index++) {
                sections[index].scrollTop = sections[index].scrollHeight;
            }
        }
        scroll(1);
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


def init_log():
    logger.remove()
    _lvl = "DEBUG"

    def format_record(record):
        # 获取日志记录中的文件全路径
        file_path = record["file"].path
        # 将绝对路径转换为相对于项目根目录的路径
        relative_path = os.path.relpath(file_path, root_dir)
        # 更新记录中的文件路径
        record["file"].path = f"./{relative_path}"
        # 返回修改后的格式字符串
        # 您可以根据需要调整这里的格式
        record["message"] = record["message"].replace(root_dir, ".")

        _format = (
            "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
            + "<level>{level}</> | "
            + '"{file.path}:{line}":<blue> {function}</> '
            + "- <level>{message}</>"
            + "\n"
        )
        return _format

    logger.add(
        sys.stdout,
        level=_lvl,
        format=format_record,
        colorize=True,
    )


init_log()

locales = utils.load_locales(i18n_dir)


def tr(key):
    loc = locales.get(st.session_state["ui_language"], {})
    return loc.get("Translation", {}).get(key, key)


# 创建基础设置折叠框
if not config.app.get("hide_config", False):
    with st.expander(tr("Basic Settings"), expanded=False):
        config_panels = st.columns(3)
        left_config_panel = config_panels[0]
        middle_config_panel = config_panels[1]
        right_config_panel = config_panels[2]

        # 左侧面板 - 日志设置
        with left_config_panel:
            # 是否隐藏配置面板
            hide_config = st.checkbox(
                tr("Hide Basic Settings"), value=config.app.get("hide_config", False)
            )
            config.app["hide_config"] = hide_config

            # 是否禁用日志显示
            hide_log = st.checkbox(
                tr("Hide Log"), value=config.ui.get("hide_log", False)
            )
            config.ui["hide_log"] = hide_log

        # 中间面板 - LLM 设置

        with middle_config_panel:
            st.write(tr("LLM Settings"))
            llm_providers = [
                "OpenAI",
                "Moonshot",
                "Azure",
                "Qwen",
                "DeepSeek",
                "ModelScope",
                "Gemini",
                "Ollama",
                "G4f",
                "OneAPI",
                "Cloudflare",
                "ERNIE",
                "Pollinations",
            ]
            saved_llm_provider = config.app.get("llm_provider", "OpenAI").lower()
            saved_llm_provider_index = 0
            for i, provider in enumerate(llm_providers):
                if provider.lower() == saved_llm_provider:
                    saved_llm_provider_index = i
                    break

            llm_provider = st.selectbox(
                tr("LLM Provider"),
                options=llm_providers,
                index=saved_llm_provider_index,
            )
            llm_helper = st.container()
            llm_provider = llm_provider.lower()
            config.app["llm_provider"] = llm_provider

            llm_api_key = config.app.get(f"{llm_provider}_api_key", "")
            llm_secret_key = config.app.get(
                f"{llm_provider}_secret_key", ""
            )  # only for baidu ernie
            llm_base_url = config.app.get(f"{llm_provider}_base_url", "")
            llm_model_name = config.app.get(f"{llm_provider}_model_name", "")
            llm_account_id = config.app.get(f"{llm_provider}_account_id", "")

            tips = ""
            if llm_provider == "ollama":
                if not llm_model_name:
                    llm_model_name = "qwen:7b"
                if not llm_base_url:
                    llm_base_url = "http://localhost:11434/v1"

                with llm_helper:
                    tips = """
                            ##### Ollama配置说明
                            - **API Key**: 随便填写，比如 123
                            - **Base Url**: 一般为 http://localhost:11434/v1
                                - 如果 `MoneyPrinterTurbo` 和 `Ollama` **不在同一台机器上**，需要填写 `Ollama` 机器的IP地址
                                - 如果 `MoneyPrinterTurbo` 是 `Docker` 部署，建议填写 `http://host.docker.internal:11434/v1`
                            - **Model Name**: 使用 `ollama list` 查看，比如 `qwen:7b`
                            """

            if llm_provider == "openai":
                if not llm_model_name:
                    llm_model_name = "gpt-3.5-turbo"
                with llm_helper:
                    tips = """
                            ##### OpenAI 配置说明
                            > 需要VPN开启全局流量模式
                            - **API Key**: [点击到官网申请](https://platform.openai.com/api-keys)
                            - **Base Url**: 可以留空
                            - **Model Name**: 填写**有权限**的模型，[点击查看模型列表](https://platform.openai.com/settings/organization/limits)
                            """

            if llm_provider == "moonshot":
                if not llm_model_name:
                    llm_model_name = "moonshot-v1-8k"
                with llm_helper:
                    tips = """
                            ##### Moonshot 配置说明
                            - **API Key**: [点击到官网申请](https://platform.moonshot.cn/console/api-keys)
                            - **Base Url**: 固定为 https://api.moonshot.cn/v1
                            - **Model Name**: 比如 moonshot-v1-8k，[点击查看模型列表](https://platform.moonshot.cn/docs/intro#%E6%A8%A1%E5%9E%8B%E5%88%97%E8%A1%A8)
                            """
            if llm_provider == "oneapi":
                if not llm_model_name:
                    llm_model_name = (
                        "claude-3-5-sonnet-20240620"  # 默认模型，可以根据需要调整
                    )
                with llm_helper:
                    tips = """
                        ##### OneAPI 配置说明
                        - **API Key**: 填写您的 OneAPI 密钥
                        - **Base Url**: 填写 OneAPI 的基础 URL
                        - **Model Name**: 填写您要使用的模型名称，例如 claude-3-5-sonnet-20240620
                        """

            if llm_provider == "qwen":
                if not llm_model_name:
                    llm_model_name = "qwen-max"
                with llm_helper:
                    tips = """
                            ##### 通义千问Qwen 配置说明
                            - **API Key**: [点击到官网申请](https://dashscope.console.aliyun.com/apiKey)
                            - **Base Url**: 留空
                            - **Model Name**: 比如 qwen-max，[点击查看模型列表](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction#3ef6d0bcf91wy)
                            """

            if llm_provider == "g4f":
                if not llm_model_name:
                    llm_model_name = "gpt-3.5-turbo"
                with llm_helper:
                    tips = """
                            ##### gpt4free 配置说明
                            > [GitHub开源项目](https://github.com/xtekky/gpt4free)，可以免费使用GPT模型，但是**稳定性较差**
                            - **API Key**: 随便填写，比如 123
                            - **Base Url**: 留空
                            - **Model Name**: 比如 gpt-3.5-turbo，[点击查看模型列表](https://github.com/xtekky/gpt4free/blob/main/g4f/models.py#L308)
                            """
            if llm_provider == "azure":
                with llm_helper:
                    tips = """
                            ##### Azure 配置说明
                            > [点击查看如何部署模型](https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/create-resource)
                            - **API Key**: [点击到Azure后台创建](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/OpenAI)
                            - **Base Url**: 留空
                            - **Model Name**: 填写你实际的部署名
                            """

            if llm_provider == "gemini":
                if not llm_model_name:
                    llm_model_name = "gemini-1.0-pro"

                with llm_helper:
                    tips = """
                            ##### Gemini 配置说明
                            > 需要VPN开启全局流量模式
                            - **API Key**: [点击到官网申请](https://ai.google.dev/)
                            - **Base Url**: 留空
                            - **Model Name**: 比如 gemini-1.0-pro
                            """

            if llm_provider == "deepseek":
                if not llm_model_name:
                    llm_model_name = "deepseek-chat"
                if not llm_base_url:
                    llm_base_url = "https://api.deepseek.com"
                with llm_helper:
                    tips = """
                            ##### DeepSeek 配置说明
                            - **API Key**: [点击到官网申请](https://platform.deepseek.com/api_keys)
                            - **Base Url**: 固定为 https://api.deepseek.com
                            - **Model Name**: 固定为 deepseek-chat
                            """

            if llm_provider == "modelscope":
                if not llm_model_name:
                    llm_model_name = "Qwen/Qwen3-32B"
                if not llm_base_url:
                    llm_base_url = "https://api-inference.modelscope.cn/v1/"
                with llm_helper:
                    tips = """
                            ##### ModelScope 配置说明
                            - **API Key**: [点击到官网申请](https://modelscope.cn/docs/model-service/API-Inference/intro)
                            - **Base Url**: 固定为 https://api-inference.modelscope.cn/v1/
                            - **Model Name**: 比如 Qwen/Qwen3-32B，[点击查看模型列表](https://modelscope.cn/models?filter=inference_type&page=1)
                            """

            if llm_provider == "ernie":
                with llm_helper:
                    tips = """
                            ##### 百度文心一言 配置说明
                            - **API Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                            - **Secret Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                            - **Base Url**: 填写 **请求地址** [点击查看文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11#%E8%AF%B7%E6%B1%82%E8%AF%B4%E6%98%8E)
                            """

            if llm_provider == "pollinations":
                if not llm_model_name:
                    llm_model_name = "default"
                with llm_helper:
                    tips = """
                            ##### Pollinations AI Configuration
                            - **API Key**: Optional - Leave empty for public access
                            - **Base Url**: Default is https://text.pollinations.ai/openai
                            - **Model Name**: Use 'openai-fast' or specify a model name
                            """

            if tips and config.ui["language"] == "zh":
                st.warning(
                    "中国用户建议使用 **DeepSeek** 或 **Moonshot** 作为大模型提供商\n- 国内可直接访问，不需要VPN \n- 注册就送额度，基本够用"
                )
                st.info(tips)

            st_llm_api_key = st.text_input(
                tr("API Key"), value=llm_api_key, type="password"
            )
            st_llm_base_url = st.text_input(tr("Base Url"), value=llm_base_url)
            st_llm_model_name = ""
            if llm_provider != "ernie":
                st_llm_model_name = st.text_input(
                    tr("Model Name"),
                    value=llm_model_name,
                    key=f"{llm_provider}_model_name_input",
                )
                if st_llm_model_name:
                    config.app[f"{llm_provider}_model_name"] = st_llm_model_name
            else:
                st_llm_model_name = None

            if st_llm_api_key:
                config.app[f"{llm_provider}_api_key"] = st_llm_api_key
            if st_llm_base_url:
                config.app[f"{llm_provider}_base_url"] = st_llm_base_url
            if st_llm_model_name:
                config.app[f"{llm_provider}_model_name"] = st_llm_model_name
            if llm_provider == "ernie":
                st_llm_secret_key = st.text_input(
                    tr("Secret Key"), value=llm_secret_key, type="password"
                )
                config.app[f"{llm_provider}_secret_key"] = st_llm_secret_key

            if llm_provider == "cloudflare":
                st_llm_account_id = st.text_input(
                    tr("Account ID"), value=llm_account_id
                )
                if st_llm_account_id:
                    config.app[f"{llm_provider}_account_id"] = st_llm_account_id

        # 右侧面板 - API 密钥设置
        with right_config_panel:

            def get_keys_from_config(cfg_key):
                api_keys = config.app.get(cfg_key, [])
                if isinstance(api_keys, str):
                    api_keys = [api_keys]
                api_key = ", ".join(api_keys)
                return api_key

            def save_keys_to_config(cfg_key, value):
                value = value.replace(" ", "")
                if value:
                    config.app[cfg_key] = value.split(",")

            st.write(tr("Video Source Settings"))

            pexels_api_key = get_keys_from_config("pexels_api_keys")
            pexels_api_key = st.text_input(
                tr("Pexels API Key"), value=pexels_api_key, type="password"
            )
            save_keys_to_config("pexels_api_keys", pexels_api_key)

            pixabay_api_key = get_keys_from_config("pixabay_api_keys")
            pixabay_api_key = st.text_input(
                tr("Pixabay API Key"), value=pixabay_api_key, type="password"
            )
            save_keys_to_config("pixabay_api_keys", pixabay_api_key)

llm_provider = config.app.get("llm_provider", "").lower()
panel = st.columns(3)
left_panel = panel[0]
middle_panel = panel[1]
right_panel = panel[2]

params = VideoParams(video_subject="")
uploaded_files = []

with left_panel:
    with st.container(border=True):
        st.write(tr("Video Script Settings"))
        params.video_subject = st.text_input(
            tr("Video Subject"),
            value=st.session_state["video_subject"],
            key="video_subject_input",
        ).strip()

        video_languages = [
            (tr("Auto Detect"), ""),
        ]
        for code in support_locales:
            video_languages.append((code, code))

        saved_video_language = config.ui.get("video_language", "")
        saved_video_language_index = 0
        try:
            saved_video_language_index = [v[1] for v in video_languages].index(
                saved_video_language
            )
        except Exception:
            saved_video_language_index = 0

        selected_index = st.selectbox(
            tr("Script Language"),
            index=saved_video_language_index,
            options=range(
                len(video_languages)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_languages[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_language = video_languages[selected_index][1]
        config.ui["video_language"] = params.video_language

        if st.button(
            tr("Generate Video Script and Keywords"), key="auto_generate_script"
        ):
            with st.spinner(tr("Generating Video Script and Keywords")):
                script = llm.generate_script(
                    video_subject=params.video_subject, language=params.video_language
                )
                terms = llm.generate_terms(params.video_subject, script)
                if "Error: " in script:
                    st.error(tr(script))
                elif "Error: " in terms:
                    st.error(tr(terms))
                else:
                    st.session_state["video_script"] = script
                    st.session_state["video_terms"] = ", ".join(terms)
        params.video_script = st.text_area(
            tr("Video Script"), value=st.session_state["video_script"], height=280
        )
        if st.button(tr("Generate Video Keywords"), key="auto_generate_terms"):
            if not params.video_script:
                st.error(tr("Please Enter the Video Subject"))
                st.stop()

            with st.spinner(tr("Generating Video Keywords")):
                terms = llm.generate_terms(params.video_subject, params.video_script)
                if "Error: " in terms:
                    st.error(tr(terms))
                else:
                    st.session_state["video_terms"] = ", ".join(terms)

        params.video_terms = st.text_area(
            tr("Video Keywords"), value=st.session_state["video_terms"]
        )

        force_regen_terms = st.checkbox(
            tr("Force regenerate keywords when generating"),
            value=bool(st.session_state.get("force_regen_terms", False)),
            key="force_regen_terms",
        )

        _terms_preview = []
        if isinstance(params.video_terms, str) and params.video_terms.strip():
            _terms_preview = [t.strip() for t in re.split(r"[,，]", params.video_terms) if t.strip()]
        st.caption(f"{tr('Keyword count')}: {len(_terms_preview)}")

        with st.expander(tr("Preview clips (pick your own)"), expanded=False):
            if "selected_clip_urls" not in st.session_state:
                st.session_state["selected_clip_urls"] = []
            if "preview_items" not in st.session_state:
                st.session_state["preview_items"] = []

            preview_term = st.selectbox(
                tr("Keyword to preview"),
                options=_terms_preview,
                index=0,
                disabled=not bool(_terms_preview),
                key="preview_term_select",
            )
            preview_limit = st.slider(tr("Preview results"), 5, 30, 10, 1)

            cols = st.columns(2)
            with cols[0]:
                do_preview = st.button(tr("Search clips"), disabled=not bool(preview_term))
            with cols[1]:
                if st.button(tr("Clear selected clips")):
                    st.session_state["selected_clip_urls"] = []

            if do_preview:
                api_base_url = _api_base_url()
                try:
                    resp = requests.post(
                        f"{api_base_url}/api/v1/stock_videos/search",
                        headers=_api_headers(),
                        json={
                            "provider": params.video_source,
                            "search_term": preview_term,
                            "minimum_duration": int(config.ui.get("video_clip_duration", 4) or 4),
                            "video_aspect": params.video_aspect.value if hasattr(params.video_aspect, "value") else params.video_aspect,
                            "limit": int(preview_limit),
                        },
                        timeout=60,
                    )
                    resp.raise_for_status()
                    body = resp.json() if resp.content else {}
                    items = (body.get("data") or {}).get("items") or []
                    st.session_state["preview_items"] = items
                except Exception as e:
                    st.error(tr("Failed to search clips"))
                    logger.exception(e)

            items = st.session_state.get("preview_items") or []
            if items:
                urls = [i.get("url") for i in items if isinstance(i, dict) and i.get("url")]
                selected = st.multiselect(
                    tr("Select clips to use"),
                    options=urls,
                    default=st.session_state.get("selected_clip_urls") or [],
                    key="selected_clip_urls_multiselect",
                )
                st.session_state["selected_clip_urls"] = selected
                st.caption(f"{tr('Selected clips')}: {len(selected)}")

                public_api_base_url = _public_api_base_url()
                for u in urls[: int(preview_limit)]:
                    if isinstance(u, str) and u.startswith(_api_base_url()):
                        u = public_api_base_url + u[len(_api_base_url()) :]
                    st.video(u)

with middle_panel:
    with st.container(border=True):
        st.write(tr("Video Settings"))
        video_concat_modes = [
            (tr("Sequential"), "sequential"),
            (tr("Random"), "random"),
        ]
        video_sources = [
            (tr("Pexels"), "pexels"),
            (tr("Pixabay"), "pixabay"),
            (tr("Local file"), "local"),
            (tr("TikTok"), "douyin"),
            (tr("Bilibili"), "bilibili"),
            (tr("Xiaohongshu"), "xiaohongshu"),
        ]

        saved_video_source_name = config.app.get("video_source", "pexels")
        saved_video_source_index = [v[1] for v in video_sources].index(
            saved_video_source_name
        )

        selected_index = st.selectbox(
            tr("Video Source"),
            options=range(len(video_sources)),
            format_func=lambda x: video_sources[x][0],
            index=saved_video_source_index,
        )
        params.video_source = video_sources[selected_index][1]
        config.app["video_source"] = params.video_source

        if params.video_source == "local":
            uploaded_files = st.file_uploader(
                "Upload Local Files",
                type=["mp4", "mov", "avi", "flv", "mkv", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )

        selected_index = st.selectbox(
            tr("Video Concat Mode"),
            index=[m[1] for m in video_concat_modes].index(
                config.ui.get("video_concat_mode", "random")
            )
            if config.ui.get("video_concat_mode", "random") in [m[1] for m in video_concat_modes]
            else 1,
            options=range(
                len(video_concat_modes)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_concat_modes[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_concat_mode = VideoConcatMode(
            video_concat_modes[selected_index][1]
        )
        config.ui["video_concat_mode"] = params.video_concat_mode.value

        pacing_presets = [
            (tr("Custom"), "custom"),
            (tr("Fast"), "fast"),
            (tr("Normal"), "normal"),
            (tr("Slow"), "slow"),
        ]
        saved_pacing = config.ui.get("pacing_preset", "custom")
        if saved_pacing not in [p[1] for p in pacing_presets]:
            saved_pacing = "custom"
        pacing_index = [p[1] for p in pacing_presets].index(saved_pacing)
        pacing_selected_index = st.selectbox(
            tr("Pacing"),
            options=range(len(pacing_presets)),
            format_func=lambda x: pacing_presets[x][0],
            index=pacing_index,
        )
        pacing_preset = pacing_presets[pacing_selected_index][1]
        config.ui["pacing_preset"] = pacing_preset

        auto_clip_duration = st.checkbox(
            tr("Auto clip duration"),
            value=bool(config.ui.get("auto_clip_duration", False)),
            key="auto_clip_duration",
        )
        config.ui["auto_clip_duration"] = auto_clip_duration

        if pacing_preset != "custom":
            if pacing_preset == "fast":
                config.ui["video_transition_mode"] = VideoTransitionMode.none.value
                config.ui["video_clip_duration"] = 2
                config.ui["video_concat_mode"] = VideoConcatMode.random.value
            elif pacing_preset == "normal":
                config.ui["video_transition_mode"] = VideoTransitionMode.fade_in.value
                config.ui["video_clip_duration"] = 4
                config.ui["video_concat_mode"] = VideoConcatMode.random.value
            elif pacing_preset == "slow":
                config.ui["video_transition_mode"] = VideoTransitionMode.fade_in.value
                config.ui["video_clip_duration"] = 6
                config.ui["video_concat_mode"] = VideoConcatMode.sequential.value

        if auto_clip_duration and isinstance(params.video_script, str) and params.video_script.strip():
            word_count = len(re.findall(r"\w+", params.video_script))
            if word_count > 0:
                if word_count < 60:
                    config.ui["video_clip_duration"] = 3
                elif word_count < 140:
                    config.ui["video_clip_duration"] = 4
                elif word_count < 220:
                    config.ui["video_clip_duration"] = 5
                else:
                    config.ui["video_clip_duration"] = 6

        # 视频转场模式
        video_transition_modes = [
            (tr("None"), VideoTransitionMode.none.value),
            (tr("Shuffle"), VideoTransitionMode.shuffle.value),
            (tr("FadeIn"), VideoTransitionMode.fade_in.value),
            (tr("FadeOut"), VideoTransitionMode.fade_out.value),
            (tr("SlideIn"), VideoTransitionMode.slide_in.value),
            (tr("SlideOut"), VideoTransitionMode.slide_out.value),
        ]
        selected_index = st.selectbox(
            tr("Video Transition Mode"),
            options=range(len(video_transition_modes)),
            format_func=lambda x: video_transition_modes[x][0],
            index=[m[1] for m in video_transition_modes].index(
                config.ui.get("video_transition_mode", VideoTransitionMode.none.value)
            )
            if config.ui.get("video_transition_mode", VideoTransitionMode.none.value)
            in [m[1] for m in video_transition_modes]
            else 0,
        )
        params.video_transition_mode = VideoTransitionMode(
            video_transition_modes[selected_index][1]
        )
        config.ui["video_transition_mode"] = params.video_transition_mode.value

        video_aspect_ratios = [
            (tr("Portrait"), VideoAspect.portrait.value),
            (tr("Landscape"), VideoAspect.landscape.value),
        ]
        selected_index = st.selectbox(
            tr("Video Ratio"),
            options=range(
                len(video_aspect_ratios)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_aspect_ratios[x][
                0
            ],  # The label is displayed to the user
            index=[m[1] for m in video_aspect_ratios].index(
                config.ui.get("video_aspect", VideoAspect.portrait.value)
            )
            if config.ui.get("video_aspect", VideoAspect.portrait.value)
            in [m[1] for m in video_aspect_ratios]
            else 0,
        )
        params.video_aspect = VideoAspect(video_aspect_ratios[selected_index][1])
        config.ui["video_aspect"] = params.video_aspect.value

        clip_duration_options = [2, 3, 4, 5, 6, 7, 8, 9, 10]
        saved_clip_duration = int(config.ui.get("video_clip_duration", 3) or 3)
        params.video_clip_duration = st.selectbox(
            tr("Clip Duration"),
            options=clip_duration_options,
            index=clip_duration_options.index(saved_clip_duration)
            if saved_clip_duration in clip_duration_options
            else 1,
        )
        config.ui["video_clip_duration"] = params.video_clip_duration

        params.sentence_level_clips = st.checkbox(
            tr("Sentence-level clips"),
            value=bool(config.ui.get("sentence_level_clips", False)),
            key="sentence_level_clips",
        )
        config.ui["sentence_level_clips"] = bool(params.sentence_level_clips)
        logger.debug(f"[CHECKBOX DEBUG] sentence_level_clips checkbox value: {params.sentence_level_clips}")

        video_count_options = [1, 2, 3, 4, 5]
        saved_video_count = int(config.ui.get("video_count", 1) or 1)
        params.video_count = st.selectbox(
            tr("Number of Videos Generated Simultaneously"),
            options=video_count_options,
            index=video_count_options.index(saved_video_count)
            if saved_video_count in video_count_options
            else 0,
        )
        config.ui["video_count"] = params.video_count
    with st.container(border=True):
        st.write(tr("Audio Settings"))

        # 添加TTS服务器选择下拉框
        tts_servers = [
            ("azure-tts-v1", "Azure TTS V1"),
            ("azure-tts-v2", "Azure TTS V2"),
            ("siliconflow", "SiliconFlow TTS"),
            ("gemini-tts", "Google Gemini TTS"),
            ("openai-tts", "OpenAI TTS"),
        ]

        # 获取保存的TTS服务器，默认为v1
        saved_tts_server = config.ui.get("tts_server", "azure-tts-v1")
        saved_tts_server_index = 0
        for i, (server_value, _) in enumerate(tts_servers):
            if server_value == saved_tts_server:
                saved_tts_server_index = i
                break

        selected_tts_server_index = st.selectbox(
            tr("TTS Servers"),
            options=range(len(tts_servers)),
            format_func=lambda x: tts_servers[x][1],
            index=saved_tts_server_index,
        )

        selected_tts_server = tts_servers[selected_tts_server_index][0]
        config.ui["tts_server"] = selected_tts_server

        if selected_tts_server == "openai-tts":
            config.app["tts_provider"] = "openai"
        else:
            config.app["tts_provider"] = ""

        # 根据选择的TTS服务器获取声音列表
        filtered_voices = []

        if selected_tts_server == "siliconflow":
            # 获取硅基流动的声音列表
            filtered_voices = voice.get_siliconflow_voices()
        elif selected_tts_server == "gemini-tts":
            # 获取Gemini TTS的声音列表
            filtered_voices = voice.get_gemini_voices()
        elif selected_tts_server == "openai-tts":
            saved_openai_voice = (config.app.get("openai_tts_voice", "") or "").strip()
            openai_voices = [
                "alloy",
                "echo",
                "fable",
                "onyx",
                "nova",
                "shimmer",
            ]
            if saved_openai_voice and saved_openai_voice not in openai_voices:
                openai_voices.insert(0, saved_openai_voice)
            filtered_voices = [f"openai:{v}" for v in openai_voices]
        else:
            # 获取Azure的声音列表
            all_voices = voice.get_all_azure_voices(filter_locals=None)

            # 根据选择的TTS服务器筛选声音
            for v in all_voices:
                if selected_tts_server == "azure-tts-v2":
                    # V2版本的声音名称中包含"v2"
                    if "V2" in v:
                        filtered_voices.append(v)
                else:
                    # V1版本的声音名称中不包含"v2"
                    if "V2" not in v:
                        filtered_voices.append(v)

        friendly_names = {
            v: v.replace("Female", tr("Female"))
            .replace("Male", tr("Male"))
            .replace("Neural", "")
            for v in filtered_voices
        }

        saved_voice_name = config.ui.get("voice_name", "")
        saved_voice_name_index = 0

        # 检查保存的声音是否在当前筛选的声音列表中
        if saved_voice_name in friendly_names:
            saved_voice_name_index = list(friendly_names.keys()).index(saved_voice_name)
        else:
            # 如果不在，则根据当前UI语言选择一个默认声音
            for i, v in enumerate(filtered_voices):
                if v.lower().startswith(st.session_state["ui_language"].lower()):
                    saved_voice_name_index = i
                    break

        # 如果没有找到匹配的声音，使用第一个声音
        if saved_voice_name_index >= len(friendly_names) and friendly_names:
            saved_voice_name_index = 0

        # 确保有声音可选
        if friendly_names:
            selected_friendly_name = st.selectbox(
                tr("Speech Synthesis"),
                options=list(friendly_names.values()),
                index=min(saved_voice_name_index, len(friendly_names) - 1)
                if friendly_names
                else 0,
            )

            voice_name = list(friendly_names.keys())[
                list(friendly_names.values()).index(selected_friendly_name)
            ]
            params.voice_name = voice_name
            config.ui["voice_name"] = voice_name
        else:
            # 如果没有声音可选，显示提示信息
            st.warning(
                tr(
                    "No voices available for the selected TTS server. Please select another server."
                )
            )
            params.voice_name = ""
            config.ui["voice_name"] = ""

        # 只有在有声音可选时才显示试听按钮
        if friendly_names and st.button(tr("Play Voice")):
            play_content = params.video_subject
            if not play_content:
                play_content = params.video_script
            if not play_content:
                play_content = tr("Voice Example")
            with st.spinner(tr("Synthesizing Voice")):
                temp_dir = utils.storage_dir("temp", create=True)
                audio_file = os.path.join(temp_dir, f"tmp-voice-{str(uuid4())}.mp3")
                sub_maker = voice.tts(
                    text=play_content,
                    voice_name=voice_name,
                    voice_rate=params.voice_rate,
                    voice_file=audio_file,
                    voice_volume=params.voice_volume,
                )
                # if the voice file generation failed, try again with a default content.
                if not sub_maker:
                    play_content = "This is a example voice. if you hear this, the voice synthesis failed with the original content."
                    sub_maker = voice.tts(
                        text=play_content,
                        voice_name=voice_name,
                        voice_rate=params.voice_rate,
                        voice_file=audio_file,
                        voice_volume=params.voice_volume,
                    )

                if sub_maker and os.path.exists(audio_file):
                    st.audio(audio_file, format="audio/mp3")
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

        if selected_tts_server == "openai-tts":
            saved_openai_tts_base_url = config.app.get("openai_tts_base_url", "")
            saved_openai_tts_api_key = config.app.get("openai_tts_api_key", "")
            saved_openai_tts_model_name = config.app.get("openai_tts_model_name", "")
            saved_openai_tts_voice = config.app.get("openai_tts_voice", "")

            openai_tts_base_url = st.text_input(
                "OpenAI TTS Base Url",
                value=saved_openai_tts_base_url,
                key="openai_tts_base_url_input",
            )
            openai_tts_api_key = st.text_input(
                "OpenAI TTS API Key",
                value=saved_openai_tts_api_key,
                type="password",
                key="openai_tts_api_key_input",
            )
            openai_tts_model_name = st.text_input(
                "OpenAI TTS Model Name",
                value=saved_openai_tts_model_name,
                key="openai_tts_model_name_input",
            )
            openai_tts_voice = st.text_input(
                "OpenAI TTS Voice",
                value=saved_openai_tts_voice,
                key="openai_tts_voice_input",
            )

            config.app["openai_tts_base_url"] = openai_tts_base_url
            config.app["openai_tts_api_key"] = openai_tts_api_key
            config.app["openai_tts_model_name"] = openai_tts_model_name
            config.app["openai_tts_voice"] = openai_tts_voice

        # 当选择V2版本或者声音是V2声音时，显示服务区域和API key输入框
        if selected_tts_server == "azure-tts-v2" or (
            voice_name and voice.is_azure_v2_voice(voice_name)
        ):
            saved_azure_speech_region = config.azure.get("speech_region", "")
            saved_azure_speech_key = config.azure.get("speech_key", "")
            azure_speech_region = st.text_input(
                tr("Speech Region"),
                value=saved_azure_speech_region,
                key="azure_speech_region_input",
            )
            azure_speech_key = st.text_input(
                tr("Speech Key"),
                value=saved_azure_speech_key,
                type="password",
                key="azure_speech_key_input",
            )
            config.azure["speech_region"] = azure_speech_region
            config.azure["speech_key"] = azure_speech_key

        # 当选择硅基流动时，显示API key输入框和说明信息
        if selected_tts_server == "siliconflow" or (
            voice_name and voice.is_siliconflow_voice(voice_name)
        ):
            saved_siliconflow_api_key = config.siliconflow.get("api_key", "")

            siliconflow_api_key = st.text_input(
                tr("SiliconFlow API Key"),
                value=saved_siliconflow_api_key,
                type="password",
                key="siliconflow_api_key_input",
            )

            # 显示硅基流动的说明信息
            st.info(
                tr("SiliconFlow TTS Settings")
                + ":\n"
                + "- "
                + tr("Speed: Range [0.25, 4.0], default is 1.0")
                + "\n"
                + "- "
                + tr("Volume: Uses Speech Volume setting, default 1.0 maps to gain 0")
            )

            config.siliconflow["api_key"] = siliconflow_api_key

        voice_volume_options = [0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0]
        saved_voice_volume = float(config.ui.get("voice_volume", 1.0) or 1.0)
        params.voice_volume = st.selectbox(
            tr("Speech Volume"),
            options=voice_volume_options,
            index=voice_volume_options.index(saved_voice_volume)
            if saved_voice_volume in voice_volume_options
            else 2,
        )
        config.ui["voice_volume"] = params.voice_volume

        voice_rate_options = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0]
        saved_voice_rate = float(config.ui.get("voice_rate", 1.0) or 1.0)
        params.voice_rate = st.selectbox(
            tr("Speech Rate"),
            options=voice_rate_options,
            index=voice_rate_options.index(saved_voice_rate)
            if saved_voice_rate in voice_rate_options
            else 2,
        )
        config.ui["voice_rate"] = params.voice_rate

        bgm_options = [
            (tr("No Background Music"), ""),
            (tr("Random Background Music"), "random"),
            (tr("Custom Background Music"), "custom"),
        ]
        selected_index = st.selectbox(
            tr("Background Music"),
            index=[m[1] for m in bgm_options].index(
                config.ui.get("bgm_type", "random")
            )
            if config.ui.get("bgm_type", "random") in [m[1] for m in bgm_options]
            else 1,
            options=range(
                len(bgm_options)
            ),  # Use the index as the internal option value
            format_func=lambda x: bgm_options[x][
                0
            ],  # The label is displayed to the user
        )
        # Get the selected background music type
        params.bgm_type = bgm_options[selected_index][1]
        config.ui["bgm_type"] = params.bgm_type

        # Show or hide components based on the selection
        if params.bgm_type == "custom":
            custom_bgm_file = st.text_input(
                tr("Custom Background Music File"),
                value=config.ui.get("bgm_file", ""),
                key="custom_bgm_file_input",
            )
            if custom_bgm_file and os.path.exists(custom_bgm_file):
                params.bgm_file = custom_bgm_file
                config.ui["bgm_file"] = custom_bgm_file
                # st.write(f":red[已选择自定义背景音乐]：**{custom_bgm_file}**")
        params.bgm_volume = st.selectbox(
            tr("Background Music Volume"),
            options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            index=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0].index(
                float(config.ui.get("bgm_volume", 0.2) or 0.2)
            )
            if float(config.ui.get("bgm_volume", 0.2) or 0.2)
            in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            else 2,
        )
        config.ui["bgm_volume"] = params.bgm_volume

with right_panel:
    with st.container(border=True):
        st.write(tr("Subtitle Settings"))
        params.subtitle_enabled = st.checkbox(
            tr("Enable Subtitles"), value=bool(config.ui.get("subtitle_enabled", True))
        )
        config.ui["subtitle_enabled"] = params.subtitle_enabled
        font_names = get_all_fonts()
        saved_font_name = config.ui.get("font_name", "MicrosoftYaHeiBold.ttc")
        saved_font_name_index = 0
        if saved_font_name in font_names:
            saved_font_name_index = font_names.index(saved_font_name)
        params.font_name = st.selectbox(
            tr("Font"), font_names, index=saved_font_name_index
        )
        config.ui["font_name"] = params.font_name

        subtitle_positions = [
            (tr("Top"), "top"),
            (tr("Center"), "center"),
            (tr("Bottom"), "bottom"),
            (tr("Custom"), "custom"),
        ]

        saved_subtitle_position = config.ui.get("subtitle_position", "bottom")
        selected_index = st.selectbox(
            tr("Position"),
            index=[m[1] for m in subtitle_positions].index(saved_subtitle_position)
            if saved_subtitle_position in [m[1] for m in subtitle_positions]
            else 2,
            options=range(len(subtitle_positions)),
            format_func=lambda x: subtitle_positions[x][0],
        )
        params.subtitle_position = subtitle_positions[selected_index][1]
        config.ui["subtitle_position"] = params.subtitle_position

        if params.subtitle_position == "custom":
            custom_position = st.text_input(
                tr("Custom Position (% from top)"),
                value=str(config.ui.get("custom_position", "70.0")),
                key="custom_position_input",
            )
            try:
                params.custom_position = float(custom_position)
                if params.custom_position < 0 or params.custom_position > 100:
                    st.error(tr("Please enter a value between 0 and 100"))
                else:
                    config.ui["custom_position"] = params.custom_position
            except ValueError:
                st.error(tr("Please enter a valid number"))

        font_cols = st.columns([0.3, 0.7])
        if params.subtitle_enabled:
            saved_font_size = config.ui.get("font_size", 60)
            params.text_fore_color = st.color_picker(
                tr("Text Color"), config.ui.get("text_fore_color", "#FFFFFF")
            )
            config.ui["text_fore_color"] = params.text_fore_color

        with font_cols[1]:
            saved_font_size = config.ui.get("font_size", 60)
            params.font_size = st.slider(tr("Font Size"), 30, 100, saved_font_size)
            config.ui["font_size"] = params.font_size

        stroke_cols = st.columns([0.3, 0.7])
        with stroke_cols[0]:
            saved_stroke_color = config.ui.get("stroke_color", "#000000")
            params.stroke_color = st.color_picker(tr("Stroke Color"), saved_stroke_color)
            config.ui["stroke_color"] = params.stroke_color
        with stroke_cols[1]:
            saved_stroke_width = float(config.ui.get("stroke_width", 1.5) or 0)
            params.stroke_width = st.slider(
                tr("Stroke Width"), 0.0, 10.0, saved_stroke_width
            )
            config.ui["stroke_width"] = params.stroke_width
    with st.expander(tr("Click to show API Key management"), expanded=False):
        st.subheader(tr("Manage Pexels and Pixabay API Keys"))

        col1, col2 = st.tabs(["Pexels API Keys", "Pixabay API Keys"])

        with col1:
            st.subheader("Pexels API Keys")
            if config.app["pexels_api_keys"]:
                st.write(tr("Current Keys:"))
                for key in config.app["pexels_api_keys"]:
                    st.code(key)
            else:
                st.info(tr("No Pexels API Keys currently"))

            new_key = st.text_input(tr("Add Pexels API Key"), key="pexels_new_key")
            if st.button(tr("Add Pexels API Key")):
                if new_key and new_key not in config.app["pexels_api_keys"]:
                    config.app["pexels_api_keys"].append(new_key)
                    config.save_config()
                    st.success(tr("Pexels API Key added successfully"))
                elif new_key in config.app["pexels_api_keys"]:
                    st.warning(tr("This API Key already exists"))
                else:
                    st.error(tr("Please enter a valid API Key"))

            if config.app["pexels_api_keys"]:
                delete_key = st.selectbox(
                    tr("Select Pexels API Key to delete"),
                    config.app["pexels_api_keys"],
                    key="pexels_delete_key",
                )
                if st.button(tr("Delete Selected Pexels API Key")):
                    config.app["pexels_api_keys"].remove(delete_key)
                    config.save_config()
                    st.success(tr("Pexels API Key deleted successfully"))

        with col2:
            st.subheader("Pixabay API Keys")

            if config.app["pixabay_api_keys"]:
                st.write(tr("Current Keys:"))
                for key in config.app["pixabay_api_keys"]:
                    st.code(key)
            else:
                st.info(tr("No Pixabay API Keys currently"))

            new_key = st.text_input(tr("Add Pixabay API Key"), key="pixabay_new_key")
            if st.button(tr("Add Pixabay API Key")):
                if new_key and new_key not in config.app["pixabay_api_keys"]:
                    config.app["pixabay_api_keys"].append(new_key)
                    config.save_config()
                    st.success(tr("Pixabay API Key added successfully"))
                elif new_key in config.app["pixabay_api_keys"]:
                    st.warning(tr("This API Key already exists"))
                else:
                    st.error(tr("Please enter a valid API Key"))

            if config.app["pixabay_api_keys"]:
                delete_key = st.selectbox(
                    tr("Select Pixabay API Key to delete"), config.app["pixabay_api_keys"], key="pixabay_delete_key"
                )
                if st.button(tr("Delete Selected Pixabay API Key")):
                    config.app["pixabay_api_keys"].remove(delete_key)
                    config.save_config()
                    st.success(tr("Pixabay API Key deleted successfully"))

with st.expander(tr("Bulk Run (Topics)"), expanded=False):
    bulk_topics = st.text_area(
        tr("Topics (one per line)"),
        value=str(config.ui.get("bulk_topics", "")),
        height=160,
        key="bulk_topics_input",
    )
    config.ui["bulk_topics"] = bulk_topics

    bulk_wait = st.checkbox(
        tr("Wait for completion (slow)"),
        value=bool(config.ui.get("bulk_wait", False)),
        key="bulk_wait",
    )
    config.ui["bulk_wait"] = bool(bulk_wait)

    bulk_created = []
    bulk_failed = []

    if st.button(tr("Create Bulk Tasks"), use_container_width=True, key="bulk_create"):
        config.save_config()
        topics = [t.strip() for t in (bulk_topics or "").splitlines() if t.strip()]
        if not topics:
            st.error(tr("Please enter at least one topic"))
            st.stop()

        api_base_url = _api_base_url()
        public_api_base_url = _public_api_base_url()

        for topic in topics:
            try:
                p = params.model_copy(deep=True)
            except Exception:
                p = VideoParams(**params.model_dump(mode="json"))

            p.video_subject = topic
            p.video_script = ""
            p.video_materials = None
            if bool(st.session_state.get("force_regen_terms", False)):
                p.video_terms = None

            try:
                create_resp = requests.post(
                    f"{api_base_url}/api/v1/videos",
                    headers=_api_headers(),
                    json=p.model_dump(mode="json"),
                    timeout=30,
                )
                create_resp.raise_for_status()
                create_body = create_resp.json() if create_resp.content else {}
                task_id = (create_body.get("data") or {}).get("task_id")
                if not task_id:
                    bulk_failed.append({"topic": topic, "error": "no task_id"})
                    continue

                bulk_created.append({"topic": topic, "task_id": task_id})

                if bulk_wait:
                    while True:
                        task_resp = requests.get(
                            f"{api_base_url}/api/v1/tasks/{task_id}",
                            headers=_api_headers(),
                            timeout=30,
                        )
                        task_resp.raise_for_status()
                        task_body = task_resp.json() if task_resp.content else {}
                        task = task_body.get("data") or {}
                        state = int(task.get("state") or 0)
                        if state in (-1, 1):
                            break
                        time.sleep(1)
            except Exception as e:
                bulk_failed.append({"topic": topic, "error": str(e)})

        if bulk_created:
            st.success(tr("Bulk tasks created"))
            for row in bulk_created:
                url = _task_file_url(public_api_base_url, row["task_id"], "")
                st.write(f"{row['topic']} => {row['task_id']}")
                st.link_button(tr("Open Task Folder"), url.rstrip("/"))

        if bulk_failed:
            st.error(tr("Some tasks failed to create"))
            st.code("\n".join([f"{r['topic']}: {r['error']}" for r in bulk_failed]))

with st.expander(tr("Clip Review (Preflight)"), expanded=False):
    if params.video_source not in ("pexels", "pixabay"):
        st.info(tr("Clip review is available for Pexels/Pixabay sources."))
    else:
        clip_limit = st.slider(
            tr("Clips per sentence"),
            min_value=2,
            max_value=10,
            value=int(config.ui.get("preflight_clip_limit", 6) or 6),
            key="preflight_clip_limit",
        )
        config.ui["preflight_clip_limit"] = int(clip_limit)

        minimum_duration = int(params.video_clip_duration or 3)

        if "preflight_search_log" not in st.session_state:
            st.session_state["preflight_search_log"] = []

        if st.button(tr("Generate Clip Review"), use_container_width=True, key="preflight_generate"):
            script_text = (params.video_script or "").strip()
            if not script_text:
                st.error(tr("Please enter a script first"))
                st.stop()

            st.session_state["preflight_search_log"] = []

            sentences = _split_sentences(script_text)
            st.session_state["preflight_sentences"] = sentences
            terms = []
            for s in sentences:
                try:
                    generated = llm.generate_terms(
                        video_subject="",
                        video_script=s,
                        amount=1,
                    )
                    t = ""
                    if isinstance(generated, list) and generated and isinstance(generated[0], str):
                        t = generated[0].strip()
                    terms.append(t)
                except Exception:
                    terms.append("")
            st.session_state["preflight_terms"] = terms

            api_base_url = _api_base_url()
            results = []
            picks = []
            for i, t in enumerate(terms):
                if not t:
                    results.append([])
                    picks.append("")
                    continue
                try:
                    log_entry = {
                        "section": i + 1,
                        "provider": params.video_source,
                        "search_term": t,
                        "minimum_duration": minimum_duration,
                        "video_aspect": str(params.video_aspect.value),
                        "limit": int(clip_limit),
                    }
                    items = _search_stock_videos(
                        api_base_url=api_base_url,
                        provider=params.video_source,
                        search_term=t,
                        minimum_duration=minimum_duration,
                        video_aspect=str(params.video_aspect.value),
                        limit=int(clip_limit),
                    )
                    results.append(items)
                    picked_url = items[0]["url"] if items else ""
                    picks.append(picked_url)
                    log_entry["result_count"] = len(items or [])
                    log_entry["picked_url"] = picked_url
                    st.session_state["preflight_search_log"].append(log_entry)
                    logger.info(utils.to_json({"event": "preflight_pick", **log_entry}))
                except Exception:
                    results.append([])
                    picks.append("")

            st.session_state["preflight_results"] = results
            st.session_state["preflight_picks"] = picks

        sentences = st.session_state.get("preflight_sentences") or []
        terms = st.session_state.get("preflight_terms") or []
        results = st.session_state.get("preflight_results") or []
        picks = st.session_state.get("preflight_picks") or []

        if sentences:
            st.write(tr("Review each section, adjust keywords, and choose a clip."))
            api_base_url = _api_base_url()

            show_debug = st.checkbox(
                tr("Show Clip Review Debug Log"),
                value=bool(st.session_state.get("preflight_show_debug", False)),
                key="preflight_show_debug",
            )
            if show_debug:
                try:
                    lines = [
                        utils.to_json(x)
                        for x in (st.session_state.get("preflight_search_log") or [])
                    ]
                    if lines:
                        st.code("\n".join(lines))
                    else:
                        st.info(tr("No searches yet"))
                except Exception:
                    st.info(tr("No searches yet"))

            persist_debug = st.checkbox(
                tr("Persist Clip Review Debug Log to file"),
                value=bool(st.session_state.get("preflight_persist_debug", False)),
                key="preflight_persist_debug",
            )
            if persist_debug:
                try:
                    debug_lines = [
                        utils.to_json(x)
                        for x in (st.session_state.get("preflight_search_log") or [])
                    ]
                    debug_text = "\n".join(debug_lines)

                    debug_dir = os.path.join(root_dir, "debug_logs")
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_filename = f"clip-review-{time.strftime('%Y%m%d-%H%M%S')}.log"
                    debug_path = os.path.join(debug_dir, debug_filename)

                    save_cols = st.columns([0.3, 0.7])
                    with save_cols[0]:
                        if st.button(tr("Save Debug Log"), key="preflight_save_debug"):
                            with open(debug_path, "w", encoding="utf-8") as f:
                                f.write(debug_text)
                            st.success(tr("Debug log saved"))
                    with save_cols[1]:
                        st.write(debug_path)
                        if debug_text:
                            st.download_button(
                                label=tr("Download Debug Log"),
                                data=debug_text,
                                file_name=debug_filename,
                                mime="text/plain",
                                key="preflight_download_debug",
                            )
                except Exception as e:
                    st.error(tr("Failed to persist debug log"))
                    logger.exception(e)

            for i, sentence in enumerate(sentences):
                st.divider()
                st.write(f"{tr('Section')} {i+1}")
                st.write(sentence)

                term_key = f"preflight_term_{i}"
                default_term = terms[i] if i < len(terms) else ""
                term_val = st.text_input(
                    tr("Keyword"),
                    value=str(st.session_state.get(term_key, default_term) or ""),
                    key=term_key,
                ).strip()

                cols = st.columns([0.2, 0.8])
                with cols[0]:
                    if st.button(tr("Search"), key=f"preflight_search_{i}"):
                        try:
                            log_entry = {
                                "section": i + 1,
                                "provider": params.video_source,
                                "search_term": term_val,
                                "minimum_duration": minimum_duration,
                                "video_aspect": str(params.video_aspect.value),
                                "limit": int(clip_limit),
                            }
                            items = _search_stock_videos(
                                api_base_url=api_base_url,
                                provider=params.video_source,
                                search_term=term_val,
                                minimum_duration=minimum_duration,
                                video_aspect=str(params.video_aspect.value),
                                limit=int(clip_limit),
                            )
                            while len(results) <= i:
                                results.append([])
                            results[i] = items
                            while len(picks) <= i:
                                picks.append("")
                            picked_url = items[0]["url"] if items else ""
                            picks[i] = picked_url
                            st.session_state["preflight_results"] = results
                            st.session_state["preflight_picks"] = picks

                            log_entry["result_count"] = len(items or [])
                            log_entry["picked_url"] = picked_url
                            st.session_state["preflight_search_log"].append(log_entry)
                            logger.info(utils.to_json({"event": "preflight_pick", **log_entry}))
                        except Exception as e:
                            st.error(tr("Search failed"))
                            logger.exception(e)
                with cols[1]:
                    items = results[i] if i < len(results) else []
                    candidates = [it for it in items if isinstance(it, dict) and it.get("url")]
                    picked_default = picks[i] if i < len(picks) else ""

                    while len(picks) <= i:
                        picks.append("")

                    if not candidates:
                        st.info(tr("No clips found for this keyword"))
                    else:
                        limited_candidates = candidates[: int(clip_limit)]
                        clips_per_row = 3
                        num_rows = (len(limited_candidates) + clips_per_row - 1) // clips_per_row
                        
                        for row_idx in range(num_rows):
                            start_idx = row_idx * clips_per_row
                            end_idx = min(start_idx + clips_per_row, len(limited_candidates))
                            row_candidates = limited_candidates[start_idx:end_idx]
                            
                            thumb_cols = st.columns(len(row_candidates))
                            for col_idx, cand in enumerate(row_candidates):
                                k = start_idx + col_idx
                                url = str(cand.get("url") or "")
                                thumb = str(cand.get("thumbnail") or "")
                                dur = cand.get("duration")
                                with thumb_cols[col_idx]:
                                    if thumb:
                                        st.image(thumb, use_container_width=True)
                                    st.caption(f"{tr('Duration')}: {dur}" if dur else "")
                                    is_selected = bool(picks[i] == url) or (
                                        not picks[i] and picked_default == url
                                    )
                                    label = tr("Selected") if is_selected else tr("Select")
                                    if st.button(label, key=f"preflight_pick_btn_{i}_{k}"):
                                        picks[i] = url
                                        st.session_state["preflight_picks"] = picks
                                        try:
                                            st.session_state["preflight_search_log"].append(
                                                {
                                                    "section": i + 1,
                                                    "provider": params.video_source,
                                                    "picked_url": url,
                                                    "picked_thumbnail": thumb,
                                                }
                                            )
                                        except Exception:
                                            pass

                        if picks[i]:
                            st.write(f"{tr('Picked')}: {picks[i]}")

            if st.button(tr("Apply Selected Clips"), use_container_width=True, key="preflight_apply"):
                applied_terms = []
                for i in range(len(sentences)):
                    t = (st.session_state.get(f"preflight_term_{i}") or "").strip()
                    if t:
                        applied_terms.append(t)
                    else:
                        applied_terms.append("")
                st.session_state["selected_sentence_terms"] = applied_terms
                selected = [u for u in (st.session_state.get("preflight_picks") or []) if u]
                st.session_state["selected_clip_urls"] = selected
                st.success(tr("Selected clips applied. Now click Generate Video."))

start_button = st.button(tr("Generate Video"), use_container_width=True, type="primary")
if start_button:
    config.save_config()
    applied_sentence_terms = st.session_state.get("selected_sentence_terms")
    if isinstance(applied_sentence_terms, list) and applied_sentence_terms:
        params.video_terms = [str(t).strip() for t in applied_sentence_terms if str(t).strip()]
    elif bool(st.session_state.get("force_regen_terms", False)):
        params.video_terms = None
    selected_clip_urls = st.session_state.get("selected_clip_urls") or []
    if selected_clip_urls:
        params.video_materials = []
        for u in selected_clip_urls:
            m = MaterialInfo()
            m.provider = params.video_source
            m.url = u
            m.duration = 0
            params.video_materials.append(m)
    if not params.video_subject and not params.video_script:
        st.error(tr("Video Script and Subject Cannot Both Be Empty"))
        scroll_to_bottom()
        st.stop()

    if params.video_source not in ["pexels", "pixabay", "local"]:
        st.error(tr("Please Select a Valid Video Source"))
        scroll_to_bottom()
        st.stop()

    if params.video_source == "pexels" and not config.app.get("pexels_api_keys", ""):
        st.error(tr("Please Enter the Pexels API Key"))
        scroll_to_bottom()
        st.stop()

    if params.video_source == "pixabay" and not config.app.get("pixabay_api_keys", ""):
        st.error(tr("Please Enter the Pixabay API Key"))
        scroll_to_bottom()
        st.stop()

    if uploaded_files:
        local_videos_dir = utils.storage_dir("local_videos", create=True)
        for file in uploaded_files:
            file_path = os.path.join(local_videos_dir, f"{file.file_id}_{file.name}")
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
                m = MaterialInfo()
                m.provider = "local"
                m.url = file_path
                if not params.video_materials:
                    params.video_materials = []
                params.video_materials.append(m)

    log_container = st.empty()
    log_records = []

    def log_received(msg):
        if config.ui["hide_log"]:
            return
        with log_container:
            log_records.append(msg)
            st.code("\n".join(log_records))

    logger.add(log_received)

    st.toast(tr("Generating Video"))
    logger.info(tr("Start Generating Video"))
    logger.info(f"[PARAMS DEBUG] sentence_level_clips value before API call: {params.sentence_level_clips}")
    logger.info(utils.to_json(params))
    scroll_to_bottom()

    api_base_url = _api_base_url()
    try:
        create_resp = requests.post(
            f"{api_base_url}/api/v1/videos",
            headers=_api_headers(),
            json=params.model_dump(mode="json"),
            timeout=30,
        )
        create_resp.raise_for_status()
        create_body = create_resp.json() if create_resp.content else {}
        task_id = (create_body.get("data") or {}).get("task_id")
        if not task_id:
            st.error(tr("Video Generation Failed"))
            logger.error(f"task creation failed: {create_body}")
            scroll_to_bottom()
            st.stop()
    except Exception as e:
        st.error(tr("Video Generation Failed"))
        logger.exception(e)
        scroll_to_bottom()
        st.stop()

    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    video_files = []

    public_api_base_url = _public_api_base_url()

    while True:
        try:
            task_resp = requests.get(
                f"{api_base_url}/api/v1/tasks/{task_id}",
                headers=_api_headers(),
                timeout=30,
            )
            task_resp.raise_for_status()
            task_body = task_resp.json() if task_resp.content else {}
            task = task_body.get("data") or {}
        except Exception as e:
            status_placeholder.error(tr("Video Generation Failed"))
            logger.exception(e)
            scroll_to_bottom()
            st.stop()

        state = int(task.get("state") or 0)
        progress = int(task.get("progress") or 0)
        progress_bar.progress(max(0, min(progress, 100)))

        if state == -1:
            status_placeholder.error(tr("Video Generation Failed"))
            scroll_to_bottom()
            st.stop()

        if state == 1:
            video_files = task.get("videos") or []
            if public_api_base_url and api_base_url and public_api_base_url != api_base_url:
                rewritten = []
                for u in video_files:
                    if isinstance(u, str) and u.startswith(api_base_url):
                        rewritten.append(public_api_base_url + u[len(api_base_url) :])
                    else:
                        rewritten.append(u)
                video_files = rewritten
            break

        status_placeholder.info(f"{tr('Generating Video')} ({progress}%)")
        time.sleep(2)

    st.success(tr("Video Generation Completed"))
    try:
        if video_files:
            player_cols = st.columns(len(video_files) * 2 + 1)
            for i, url in enumerate(video_files):
                player_cols[i * 2 + 1].video(url)
    except Exception:
        pass

    open_task_folder(task_id)
    logger.info(tr("Video Generation Completed"))
    scroll_to_bottom()

config.save_config()

with st.expander(tr("Task Browser"), expanded=False):
    task_ids = _list_task_ids(limit=100)
    if not task_ids:
        st.info(tr("No tasks found"))
    else:
        selected_task_id = st.selectbox(tr("Task ID"), options=task_ids)
        try:
            task_path = _safe_task_dir(selected_task_id)
            files = [p for p in task_path.iterdir() if p.is_file()]
            files.sort(key=lambda p: p.name)
            if not files:
                st.info(tr("No files found in task"))
            else:
                public_api_base_url = _public_api_base_url()

                script_data = {}
                materials_data = {}
                try:
                    script_file = task_path / "script.json"
                    if script_file.exists():
                        script_data = json.loads(script_file.read_text(encoding="utf-8"))
                except Exception:
                    script_data = {}
                try:
                    materials_file = task_path / "materials.json"
                    if materials_file.exists():
                        materials_data = json.loads(
                            materials_file.read_text(encoding="utf-8")
                        )
                except Exception:
                    materials_data = {}

                script_text = (script_data.get("script") or "").strip()
                terms = script_data.get("search_terms") or []
                if isinstance(terms, str):
                    terms = [t.strip() for t in re.split(r"[,，]", terms) if t.strip()]
                if not isinstance(terms, list):
                    terms = []
                sentences = _split_sentences(script_text)

                manifest_items = []
                try:
                    manifest_items = (materials_data.get("materials") or [])
                    if not isinstance(manifest_items, list):
                        manifest_items = []
                except Exception:
                    manifest_items = []

                if manifest_items and (sentences or terms):
                    st.subheader(tr("Clip Breakdown"))
                    per_row = 3
                    for row_start in range(0, len(manifest_items), per_row):
                        row_cols = st.columns(per_row)
                        for j in range(per_row):
                            i = row_start + j
                            if i >= len(manifest_items):
                                continue
                            item = manifest_items[i]
                            filename = (item or {}).get("filename") or ""
                            sentence = sentences[i] if i < len(sentences) else ""
                            term = terms[i] if i < len(terms) else ""

                            url = ""
                            if filename and (task_path / filename).exists():
                                url = _task_file_url(
                                    public_api_base_url, selected_task_id, filename
                                )

                            with row_cols[j]:
                                with st.container(border=True):
                                    if term:
                                        st.write(f"{tr('Keyword')}: {term}")
                                    if url:
                                        st.video(url)
                                    else:
                                        st.code(str((item or {}).get("path") or ""))
                                    if sentence:
                                        st.write(sentence)

                show_inline_media_previews = not bool(
                    manifest_items and (sentences or terms)
                )

                for p in files:
                    filename = p.name
                    url = _task_file_url(public_api_base_url, selected_task_id, filename)
                    st.write(f"{filename}  ")
                    st.link_button(tr("Open"), url)
                    lower = filename.lower()
                    if show_inline_media_previews:
                        if lower.endswith((".mp4", ".mov", ".mkv", ".webm")):
                            st.video(url)
                        elif lower.endswith((".mp3", ".wav", ".m4a", ".aac", ".flac")):
                            st.audio(url)
        except Exception as e:
            st.error(tr("Failed to load task files"))
            logger.exception(e)
