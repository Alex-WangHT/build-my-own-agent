"""
Provider 注册表
管理 LLM Provider 的注册和获取
"""

from typing import Dict, Optional, List, Any, Type

from config.settings import Settings, get_settings
from provider.base import LLMProvider
from provider.siliconflow import SiliconFlowProvider
from provider.openai_provider import OpenAIProvider
from provider.claude import ClaudeProvider
from provider.deepseek import DeepseekProvider
from provider.kimi import KimiProvider
from provider.qwen import QwenProvider
from provider.bigmodel import BigModelProvider
from provider.openrouter import OpenrouterProvider


class ProviderRegistry:
    """
    Provider 注册表
    管理所有可用的 LLM Provider

    设计理念：
    - 运行时可动态注册新的 Provider
    - 支持创建和获取 Provider 实例
    """

    _instance: Optional["ProviderRegistry"] = None
    _providers: Dict[str, Type[LLMProvider]] = {}
    _instances: Dict[str, LLMProvider] = {}
    _default_provider: str = "siliconflow"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance

    def _initialize_defaults(self):
        """初始化默认 Provider"""
        self._providers = {}
        self._instances = {}
        self.register("siliconflow", SiliconFlowProvider)
        self.register("openai", OpenAIProvider)
        self.register("claude", ClaudeProvider)
        self.register("deepseek", DeepseekProvider)
        self.register("kimi", KimiProvider)
        self.register("qwen", QwenProvider)
        self.register("bigmodel", BigModelProvider)
        self.register("openrouter", OpenrouterProvider)

    def register(
        self, name: str, provider_class: Type[LLMProvider]
    ) -> None:
        """
        注册一个 Provider 类

        Args:
            name: Provider 名称
            provider_class: Provider 类
        """
        self._providers[name] = provider_class
        if name in self._instances:
            del self._instances[name]

    def get(
        self,
        name: str,
        settings: Optional[Settings] = None,
        **kwargs,
    ) -> LLMProvider:
        """
        获取或创建 Provider 实例

        Args:
            name: Provider 名称
            settings: 配置实例（可选）
            **kwargs: 其他参数传递给 Provider 构造函数

        Returns:
            Provider 实例

        Raises:
            ValueError: 如果 Provider 名称不存在
        """
        if name not in self._providers:
            raise ValueError(
                f"Unknown provider: {name}. Available providers: {list(self._providers.keys())}"
            )

        if name not in self._instances:
            provider_class = self._providers[name]
            self._instances[name] = provider_class(settings=settings, **kwargs)

        return self._instances[name]

    def create(
        self,
        name: str,
        settings: Optional[Settings] = None,
        **kwargs,
    ) -> LLMProvider:
        """
        总是创建新的 Provider 实例

        Args:
            name: Provider 名称
            settings: 配置实例（可选）
            **kwargs: 其他参数传递给 Provider 构造函数

        Returns:
            新的 Provider 实例
        """
        if name not in self._providers:
            raise ValueError(
                f"Unknown provider: {name}. Available providers: {list(self._providers.keys())}"
            )

        provider_class = self._providers[name]
        return provider_class(settings=settings, **kwargs)

    def list_providers(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的 Provider

        Returns:
            Provider 信息列表
        """
        return [
            {
                "name": name,
                "class": provider_class.__name__,
                "has_instance": name in self._instances,
            }
            for name, provider_class in self._providers.items()
        ]

    def set_default(self, name: str) -> bool:
        """
        设置默认 Provider

        Args:
            name: Provider 名称

        Returns:
            是否成功设置
        """
        if name in self._providers:
            self._default_provider = name
            return True
        return False

    @property
    def default(self) -> LLMProvider:
        """获取默认 Provider 实例"""
        return self.get(self._default_provider)

    @property
    def default_provider_name(self) -> str:
        """获取默认 Provider 名称"""
        return self._default_provider

    def clear_instance(self, name: str) -> None:
        """
        清除缓存的 Provider 实例

        Args:
            name: Provider 名称
        """
        if name in self._instances:
            self._instances[name].close()
            del self._instances[name]

    def clear_all_instances(self) -> None:
        """清除所有缓存的 Provider 实例"""
        for name in list(self._instances.keys()):
            self.clear_instance(name)


_registry: Optional[ProviderRegistry] = None


def _get_registry() -> ProviderRegistry:
    """获取全局注册表实例"""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def get_provider(
    name: Optional[str] = None,
    settings: Optional[Settings] = None,
    **kwargs,
) -> LLMProvider:
    """
    获取 Provider 实例的便捷函数

    Args:
        name: Provider 名称（可选，默认使用硅基流动）
        settings: 配置实例（可选）
        **kwargs: 其他参数

    Returns:
        Provider 实例
    """
    registry = _get_registry()
    if name is None:
        return registry.default
    return registry.get(name, settings=settings, **kwargs)


def create_provider(
    name: str,
    settings: Optional[Settings] = None,
    **kwargs,
) -> LLMProvider:
    """
    创建新 Provider 实例的便捷函数

    Args:
        name: Provider 名称
        settings: 配置实例（可选）
        **kwargs: 其他参数

    Returns:
        新的 Provider 实例
    """
    registry = _get_registry()
    return registry.create(name, settings=settings, **kwargs)


def list_providers() -> List[Dict[str, Any]]:
    """
    列出所有可用 Provider 的便捷函数

    Returns:
        Provider 信息列表
    """
    registry = _get_registry()
    return registry.list_providers()


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """
    注册 Provider 的便捷函数

    Args:
        name: Provider 名称
        provider_class: Provider 类
    """
    registry = _get_registry()
    registry.register(name, provider_class)
