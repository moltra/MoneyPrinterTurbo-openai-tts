"""
LLM Configuration Component
Secure LLM provider configuration with proper API key handling
"""
import streamlit as st
from typing import Dict, Optional

from app.config import config
from webui.i18n import tr
from webui.utils.security import render_secure_api_key_input, MASKED_VALUE


# LLM Provider configurations
LLM_PROVIDER_CONFIGS = {
    "openai": {
        "display_name": "OpenAI",
        "default_model": "gpt-3.5-turbo",
        "default_base_url": "",
        "help_text_zh": """
            ##### OpenAI 配置说明
            > 需要VPN开启全局流量模式
            - **API Key**: [点击到官网申请](https://platform.openai.com/api-keys)
            - **Base Url**: 可以留空
            - **Model Name**: 填写**有权限**的模型，[点击查看模型列表](https://platform.openai.com/settings/organization/limits)
        """,
        "help_text_en": """
            ##### OpenAI Configuration
            > VPN required for global access
            - **API Key**: [Get it here](https://platform.openai.com/api-keys)
            - **Base Url**: Leave empty for default
            - **Model Name**: Enter a model you have access to
        """
    },
    "moonshot": {
        "display_name": "Moonshot",
        "default_model": "moonshot-v1-8k",
        "default_base_url": "https://api.moonshot.cn/v1",
        "help_text_zh": """
            ##### Moonshot 配置说明
            - **API Key**: [点击到官网申请](https://platform.moonshot.cn/console/api-keys)
            - **Base Url**: 固定为 https://api.moonshot.cn/v1
            - **Model Name**: 比如 moonshot-v1-8k，[点击查看模型列表](https://platform.moonshot.cn/docs/intro#%E6%A8%A1%E5%9E%8B%E5%88%97%E8%A1%A8)
        """,
        "help_text_en": "##### Moonshot Configuration\n- Get API key from platform.moonshot.cn"
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "default_model": "deepseek-chat",
        "default_base_url": "https://api.deepseek.com",
        "help_text_zh": """
            ##### DeepSeek 配置说明
            - **API Key**: [点击到官网申请](https://platform.deepseek.com/api_keys)
            - **Base Url**: 固定为 https://api.deepseek.com
            - **Model Name**: 固定为 deepseek-chat
        """,
        "help_text_en": "##### DeepSeek Configuration\n- Get API key from platform.deepseek.com"
    },
    "qwen": {
        "display_name": "Qwen",
        "default_model": "qwen-max",
        "default_base_url": "",
        "help_text_zh": """
            ##### 通义千问Qwen 配置说明
            - **API Key**: [点击到官网申请](https://dashscope.console.aliyun.com/apiKey)
            - **Base Url**: 留空
            - **Model Name**: 比如 qwen-max，[点击查看模型列表](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction#3ef6d0bcf91wy)
        """,
        "help_text_en": "##### Qwen Configuration\n- Get API key from Aliyun DashScope"
    },
    "gemini": {
        "display_name": "Gemini",
        "default_model": "gemini-1.0-pro",
        "default_base_url": "",
        "help_text_zh": """
            ##### Gemini 配置说明
            > 需要VPN开启全局流量模式
            - **API Key**: [点击到官网申请](https://ai.google.dev/)
            - **Base Url**: 留空
            - **Model Name**: 比如 gemini-1.0-pro
        """,
        "help_text_en": "##### Gemini Configuration\n- Get API key from ai.google.dev"
    },
    "azure": {
        "display_name": "Azure",
        "default_model": "",
        "default_base_url": "",
        "help_text_zh": """
            ##### Azure 配置说明
            > [点击查看如何部署模型](https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/create-resource)
            - **API Key**: [点击到Azure后台创建](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/OpenAI)
            - **Base Url**: 留空
            - **Model Name**: 填写你实际的部署名
        """,
        "help_text_en": "##### Azure Configuration\n- Create deployment in Azure Portal"
    },
    "ollama": {
        "display_name": "Ollama",
        "default_model": "qwen:7b",
        "default_base_url": "http://localhost:11434/v1",
        "help_text_zh": """
            ##### Ollama配置说明
            - **API Key**: 随便填写，比如 123
            - **Base Url**: 一般为 http://localhost:11434/v1
                - 如果 `MoneyPrinterTurbo` 和 `Ollama` **不在同一台机器上**，需要填写 `Ollama` 机器的IP地址
                - 如果 `MoneyPrinterTurbo` 是 `Docker` 部署，建议填写 `http://host.docker.internal:11434/v1`
            - **Model Name**: 使用 `ollama list` 查看，比如 `qwen:7b`
        """,
        "help_text_en": "##### Ollama Configuration\n- Local LLM server"
    },
    "g4f": {
        "display_name": "G4f",
        "default_model": "gpt-3.5-turbo",
        "default_base_url": "",
        "help_text_zh": """
            ##### gpt4free 配置说明
            > [GitHub开源项目](https://github.com/xtekky/gpt4free)，可以免费使用GPT模型，但是**稳定性较差**
            - **API Key**: 随便填写，比如 123
            - **Base Url**: 留空
            - **Model Name**: 比如 gpt-3.5-turbo，[点击查看模型列表](https://github.com/xtekky/gpt4free/blob/main/g4f/models.py#L308)
        """,
        "help_text_en": "##### GPT4Free Configuration\n- Free GPT models (unstable)"
    },
    "oneapi": {
        "display_name": "OneAPI",
        "default_model": "claude-3-5-sonnet-20240620",
        "default_base_url": "",
        "help_text_zh": """
            ##### OneAPI 配置说明
            - **API Key**: 填写您的 OneAPI 密钥
            - **Base Url**: 填写 OneAPI 的基础 URL
            - **Model Name**: 填写您要使用的模型名称，例如 claude-3-5-sonnet-20240620
        """,
        "help_text_en": "##### OneAPI Configuration\n- Unified API interface"
    },
    "cloudflare": {
        "display_name": "Cloudflare",
        "default_model": "",
        "default_base_url": "",
        "help_text_zh": "##### Cloudflare Workers AI 配置说明",
        "help_text_en": "##### Cloudflare Workers AI Configuration"
    },
    "ernie": {
        "display_name": "ERNIE",
        "default_model": "",
        "default_base_url": "",
        "has_secret_key": True,
        "help_text_zh": """
            ##### 百度文心一言 配置说明
            - **API Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
            - **Secret Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
            - **Base Url**: 填写 **请求地址** [点击查看文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11#%E8%AF%B7%E6%B1%82%E8%AF%B4%E6%98%8E)
        """,
        "help_text_en": "##### Baidu ERNIE Configuration\n- Requires API Key and Secret Key"
    },
    "modelscope": {
        "display_name": "ModelScope",
        "default_model": "Qwen/Qwen3-32B",
        "default_base_url": "https://api-inference.modelscope.cn/v1/",
        "help_text_zh": """
            ##### ModelScope 配置说明
            - **API Key**: [点击到官网申请](https://modelscope.cn/docs/model-service/API-Inference/intro)
            - **Base Url**: 固定为 https://api-inference.modelscope.cn/v1/
            - **Model Name**: 比如 Qwen/Qwen3-32B，[点击查看模型列表](https://modelscope.cn/models?filter=inference_type&page=1)
        """,
        "help_text_en": "##### ModelScope Configuration\n- Alibaba's model platform"
    },
    "pollinations": {
        "display_name": "Pollinations",
        "default_model": "default",
        "default_base_url": "",
        "help_text_zh": """
            ##### Pollinations AI Configuration
            - **API Key**: Optional - Leave empty for public access
            - **Base Url**: Default is https://text.pollinations.ai/openai
            - **Model Name**: Use 'openai-fast' or specify a model name
        """,
        "help_text_en": "##### Pollinations AI Configuration\n- Free AI service"
    },
}


def render_llm_config() -> None:
    """
    Render LLM configuration panel with secure API key handling
    """
    st.write(tr("LLM Settings"))
    
    # Provider selection
    llm_providers = list(LLM_PROVIDER_CONFIGS.keys())
    display_names = [LLM_PROVIDER_CONFIGS[p]["display_name"] for p in llm_providers]
    
    saved_llm_provider = config.app.get("llm_provider", "OpenAI").lower()
    
    # Find saved provider index
    saved_index = 0
    for i, provider_key in enumerate(llm_providers):
        if provider_key == saved_llm_provider:
            saved_index = i
            break
    
    selected_display_name = st.selectbox(
        tr("LLM Provider"),
        options=display_names,
        index=saved_index,
    )
    
    # Get provider key from display name
    llm_provider = None
    for key, cfg in LLM_PROVIDER_CONFIGS.items():
        if cfg["display_name"] == selected_display_name:
            llm_provider = key
            break
    
    if not llm_provider:
        llm_provider = saved_llm_provider
    
    config.app["llm_provider"] = llm_provider
    
    provider_config = LLM_PROVIDER_CONFIGS.get(llm_provider, {})
    
    # Show Chinese recommendation for Chinese users
    if config.ui.get("language") == "zh":
        st.warning(
            "中国用户建议使用 **DeepSeek** 或 **Moonshot** 作为大模型提供商\n- 国内可直接访问，不需要VPN \n- 注册就送额度，基本够用"
        )
    
    # Show provider-specific help text
    help_text = (
        provider_config.get("help_text_zh", "")
        if config.ui.get("language") == "zh"
        else provider_config.get("help_text_en", "")
    )
    if help_text:
        st.info(help_text)
    
    # Get current values with defaults
    llm_base_url = config.app.get(
        f"{llm_provider}_base_url",
        provider_config.get("default_base_url", "")
    )
    llm_model_name = config.app.get(
        f"{llm_provider}_model_name",
        provider_config.get("default_model", "")
    )
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label=tr("API Key"),
        config_key=f"{llm_provider}_api_key",
        help_text=tr("Required for most providers")
    )
    
    if was_updated:
        if new_api_key:
            config.app[f"{llm_provider}_api_key"] = new_api_key
        else:
            # User cleared the key
            config.app.pop(f"{llm_provider}_api_key", None)
    
    # Secret key for ERNIE (Baidu)
    if provider_config.get("has_secret_key", False):
        was_updated_secret, new_secret_key = render_secure_api_key_input(
            label=tr("Secret Key"),
            config_key=f"{llm_provider}_secret_key",
            help_text=tr("Required for Baidu ERNIE")
        )
        
        if was_updated_secret:
            if new_secret_key:
                config.app[f"{llm_provider}_secret_key"] = new_secret_key
            else:
                config.app.pop(f"{llm_provider}_secret_key", None)
    
    # Base URL
    st_llm_base_url = st.text_input(
        tr("Base Url"),
        value=llm_base_url,
        help=tr("Leave empty for default")
    )
    if st_llm_base_url:
        config.app[f"{llm_provider}_base_url"] = st_llm_base_url
    
    # Model name (not for ERNIE)
    if llm_provider != "ernie":
        st_llm_model_name = st.text_input(
            tr("Model Name"),
            value=llm_model_name,
            key=f"{llm_provider}_model_name_input",
            help=tr("Model identifier for this provider")
        )
        if st_llm_model_name:
            config.app[f"{llm_provider}_model_name"] = st_llm_model_name
    else:
        # For ERNIE, show specialized fields
        st_ernie_account_id = st.text_input(
            "Account ID",
            value=config.app.get(f"{llm_provider}_account_id", ""),
            key=f"{llm_provider}_account_id_input"
        )
        if st_ernie_account_id:
            config.app[f"{llm_provider}_account_id"] = st_ernie_account_id
    
    # Save config
    config.save_config()
