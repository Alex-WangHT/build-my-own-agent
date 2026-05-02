"""
配置管理模块
使用pydantic-settings管理环境变量和配置
"""

import os
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


def _load_env_file():
    """加载.env文件"""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        env_example = Path(".env.example")
        if env_example.exists():
            load_dotenv(env_example)


_load_env_file()


class Settings(BaseSettings):
    """应用配置"""

    # 硅基流动API配置
    siliconflow_api_key: Optional[str] = Field(
        default=None,
        alias="SILICONFLOW_API_KEY",
        description="硅基流动API密钥",
    )

    siliconflow_base_url: str = Field(
        default="https://api.siliconflow.cn/v1",
        alias="SILICONFLOW_BASE_URL",
        description="硅基流动API基础URL",
    )

    siliconflow_model: str = Field(
        default="deepseek-ai/DeepSeek-V3",
        alias="SILICONFLOW_MODEL",
        description="默认使用的模型",
    )

    # OpenAI API配置
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API密钥",
    )

    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL",
        description="OpenAI API基础URL",
    )

    openai_model: str = Field(
        default="gpt-4o",
        alias="OPENAI_MODEL",
        description="OpenAI默认模型",
    )

    # Claude (Anthropic) API配置
    claude_api_key: Optional[str] = Field(
        default=None,
        alias="CLAUDE_API_KEY",
        alias_priority=1,
        description="Claude API密钥",
    )

    anthropic_api_key: Optional[str] = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
        alias_priority=2,
        description="Anthropic API密钥（别名）",
    )

    claude_base_url: str = Field(
        default="https://api.anthropic.com",
        alias="CLAUDE_BASE_URL",
        description="Claude API基础URL",
    )

    claude_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        alias="CLAUDE_MODEL",
        description="Claude默认模型",
    )

    # 智谱AI (BigModel) API配置
    bigmodel_api_key: Optional[str] = Field(
        default=None,
        alias="BIGMODEL_API_KEY",
        alias_priority=1,
        description="智谱AI API密钥",
    )

    zhipu_api_key: Optional[str] = Field(
        default=None,
        alias="ZHIPU_API_KEY",
        alias_priority=2,
        description="智谱AI API密钥（别名）",
    )

    bigmodel_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        alias="BIGMODEL_BASE_URL",
        description="智谱AI API基础URL",
    )

    bigmodel_model: str = Field(
        default="glm-4",
        alias="BIGMODEL_MODEL",
        description="智谱AI默认模型",
    )

    # Deepseek API配置
    deepseek_api_key: Optional[str] = Field(
        default=None,
        alias="DEEPSEEK_API_KEY",
        description="Deepseek API密钥",
    )

    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        alias="DEEPSEEK_BASE_URL",
        description="Deepseek API基础URL",
    )

    deepseek_model: str = Field(
        default="deepseek-chat",
        alias="DEEPSEEK_MODEL",
        description="Deepseek默认模型",
    )

    # Kimi (Moonshot) API配置
    kimi_api_key: Optional[str] = Field(
        default=None,
        alias="KIMI_API_KEY",
        alias_priority=1,
        description="Kimi API密钥",
    )

    moonshot_api_key: Optional[str] = Field(
        default=None,
        alias="MOONSHOT_API_KEY",
        alias_priority=2,
        description="Moonshot API密钥（别名）",
    )

    kimi_base_url: str = Field(
        default="https://api.moonshot.cn/v1",
        alias="KIMI_BASE_URL",
        description="Kimi API基础URL",
    )

    kimi_model: str = Field(
        default="moonshot-v1-8k",
        alias="KIMI_MODEL",
        description="Kimi默认模型",
    )

    # Qwen (阿里千问) API配置
    qwen_api_key: Optional[str] = Field(
        default=None,
        alias="QWEN_API_KEY",
        alias_priority=1,
        description="Qwen API密钥",
    )

    dashscope_api_key: Optional[str] = Field(
        default=None,
        alias="DASHSCOPE_API_KEY",
        alias_priority=2,
        description="Dashscope API密钥（别名）",
    )

    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
        description="Qwen API基础URL",
    )

    qwen_model: str = Field(
        default="qwen-turbo",
        alias="QWEN_MODEL",
        description="Qwen默认模型",
    )

    # Openrouter API配置
    openrouter_api_key: Optional[str] = Field(
        default=None,
        alias="OPENROUTER_API_KEY",
        description="Openrouter API密钥",
    )

    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
        description="Openrouter API基础URL",
    )

    openrouter_model: str = Field(
        default="openai/gpt-4o",
        alias="OPENROUTER_MODEL",
        description="Openrouter默认模型",
    )

    # API调用配置
    request_timeout: int = Field(
        default=60,
        description="普通API请求超时时间（秒）",
    )

    stream_timeout: int = Field(
        default=120,
        alias="STREAM_TIMEOUT",
        description="流式输出超时时间（秒），对于响应较慢的模型可以调大",
    )

    first_token_timeout: int = Field(
        default=30,
        alias="FIRST_TOKEN_TIMEOUT",
        description="等待第一个token的超时时间（秒）",
    )

    max_retries: int = Field(
        default=3,
        description="最大重试次数",
    )

    retry_delay: float = Field(
        default=1.0,
        description="重试延迟（秒）",
    )

    # 对话配置
    max_history_tokens: int = Field(
        default=8000,
        description="对话历史最大Token数",
    )

    temperature: float = Field(
        default=0.7,
        description="生成温度",
    )

    max_tokens: int = Field(
        default=4096,
        description="最大生成Token数",
    )

    # 调试配置
    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="调试模式",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="日志级别",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _load_env_file()
    _settings = Settings()
    return _settings
