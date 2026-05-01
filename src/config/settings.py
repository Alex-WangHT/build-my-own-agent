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
    siliconflow_api_key: str = Field(
        default=...,
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
