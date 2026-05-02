"""
Provider 模块
提供统一的 LLM 提供商接口和多种实现

支持的 Provider:
- siliconflow: 硅基流动
- openai: 官方 OpenAI
- claude: Claude (Anthropic)
- deepseek: Deepseek
- kimi: Kimi (Moonshot)
- qwen: 阿里千问
- bigmodel: 智谱AI
- openrouter: Openrouter (聚合平台)
"""

from provider.base import (
    Message,
    Usage,
    ChatCompletionChoice,
    ChatCompletionResponse,
    ChatCompletionRequest,
    APIError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    LLMProvider,
)
from provider.openai_compatible import OpenAICompatibleProvider
from provider.siliconflow import SiliconFlowProvider
from provider.openai_provider import OpenAIProvider
from provider.claude import ClaudeProvider
from provider.deepseek import DeepseekProvider
from provider.kimi import KimiProvider
from provider.qwen import QwenProvider
from provider.bigmodel import BigModelProvider
from provider.openrouter import OpenrouterProvider
from provider.registry import (
    ProviderRegistry,
    get_provider,
    list_providers,
    register_provider,
    create_provider,
)

__all__ = [
    "Message",
    "Usage",
    "ChatCompletionChoice",
    "ChatCompletionResponse",
    "ChatCompletionRequest",
    "APIError",
    "NetworkError",
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",
    "LLMProvider",
    "OpenAICompatibleProvider",
    "SiliconFlowProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "DeepseekProvider",
    "KimiProvider",
    "QwenProvider",
    "BigModelProvider",
    "OpenrouterProvider",
    "ProviderRegistry",
    "get_provider",
    "list_providers",
    "register_provider",
    "create_provider",
]
