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


if __name__ == "__main__":
    import unittest
    from unittest.mock import Mock, patch, MagicMock
    from typing import List, Dict, Any, Iterator

    from provider.base import LLMProvider, Message, ChatCompletionResponse

    class MockProvider(LLMProvider):
        """测试用的 Mock Provider"""

        def __init__(self, api_key: str = None, base_url: str = None, settings=None, **kwargs):
            self._provider_name = "mock"
            self._default_model = "mock-model"
            self._base_url = base_url or "https://mock.api"
            self._api_key = api_key
            self._settings = settings
            self._closed = False

        @property
        def provider_name(self) -> str:
            return self._provider_name

        @property
        def default_model(self) -> str:
            return self._default_model

        @property
        def base_url(self) -> str:
            return self._base_url

        def chat(
            self,
            messages: List[Message],
            model: str = None,
            temperature: float = None,
            max_tokens: int = None,
            tools: Optional[List[Dict[str, Any]]] = None,
            **kwargs,
        ) -> ChatCompletionResponse:
            return ChatCompletionResponse(
                id="mock_123",
                model=model or self._default_model,
                choices=[],
            )

        def chat_stream(
            self,
            messages: List[Message],
            model: str = None,
            temperature: float = None,
            max_tokens: int = None,
            tools: Optional[List[Dict[str, Any]]] = None,
            **kwargs,
        ) -> Iterator[str]:
            yield "Hello"

        def list_models(self) -> List[Dict[str, Any]]:
            return [{"id": "mock-model", "object": "model"}]

        def close(self) -> None:
            self._closed = True

    class TestProviderRegistry(unittest.TestCase):
        """ProviderRegistry 单元测试"""

        def setUp(self):
            """测试前准备 - 重置单例"""
            ProviderRegistry._instance = None
            ProviderRegistry._providers = {}
            ProviderRegistry._instances = {}
            ProviderRegistry._default_provider = "siliconflow"

        def test_singleton_pattern(self):
            """测试单例模式"""
            reg1 = ProviderRegistry()
            reg2 = ProviderRegistry()
            self.assertIs(reg1, reg2)

        def test_initialize_defaults(self):
            """测试初始化默认 Provider"""
            reg = ProviderRegistry()
            providers = reg.list_providers()
            provider_names = [p["name"] for p in providers]

            self.assertIn("siliconflow", provider_names)
            self.assertIn("openai", provider_names)
            self.assertIn("claude", provider_names)
            self.assertIn("deepseek", provider_names)
            self.assertIn("kimi", provider_names)
            self.assertIn("qwen", provider_names)
            self.assertIn("bigmodel", provider_names)
            self.assertIn("openrouter", provider_names)

        def test_register_new_provider(self):
            """测试注册新 Provider"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            providers = reg.list_providers()
            provider_names = [p["name"] for p in providers]
            self.assertIn("mock", provider_names)

        def test_register_existing_provider_clears_instance(self):
            """测试注册已存在的 Provider 会清除实例"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            with patch.object(reg, "_providers", {"mock": MockProvider}):
                with patch.object(reg, "_instances", {"mock": MockProvider()}):
                    old_instance = reg._instances.get("mock")

                    class NewMockProvider(MockProvider):
                        pass

                    reg.register("mock", NewMockProvider)

                    self.assertNotIn("mock", reg._instances)

        def test_get_existing_provider(self):
            """测试获取已注册的 Provider"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider = reg.get("mock")
                self.assertIsInstance(provider, MockProvider)

        def test_get_unknown_provider_raises_error(self):
            """测试获取未知 Provider 会抛出异常"""
            reg = ProviderRegistry()

            with self.assertRaises(ValueError) as context:
                reg.get("unknown_provider")

            self.assertIn("Unknown provider", str(context.exception))
            self.assertIn("unknown_provider", str(context.exception))

        def test_get_returns_same_instance(self):
            """测试 get 方法返回相同实例（单例模式）"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider1 = reg.get("mock")
                provider2 = reg.get("mock")
                self.assertIs(provider1, provider2)

        def test_create_always_returns_new_instance(self):
            """测试 create 方法总是返回新实例"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider1 = reg.create("mock")
                provider2 = reg.create("mock")
                self.assertIsNot(provider1, provider2)

        def test_create_unknown_provider_raises_error(self):
            """测试创建未知 Provider 会抛出异常"""
            reg = ProviderRegistry()

            with self.assertRaises(ValueError) as context:
                reg.create("unknown_provider")

            self.assertIn("Unknown provider", str(context.exception))

        def test_list_providers(self):
            """测试列出所有 Provider"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            providers = reg.list_providers()
            self.assertGreater(len(providers), 0)

            mock_info = next((p for p in providers if p["name"] == "mock"), None)
            self.assertIsNotNone(mock_info)
            self.assertEqual(mock_info["class"], "MockProvider")
            self.assertEqual(mock_info["has_instance"], False)

        def test_set_default_success(self):
            """测试成功设置默认 Provider"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            result = reg.set_default("mock")
            self.assertTrue(result)
            self.assertEqual(reg.default_provider_name, "mock")

        def test_set_default_failure(self):
            """测试设置未知 Provider 为默认失败"""
            reg = ProviderRegistry()

            result = reg.set_default("unknown")
            self.assertFalse(result)
            self.assertEqual(reg.default_provider_name, "siliconflow")

        def test_default_property(self):
            """测试 default 属性"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)
            reg.set_default("mock")

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                default_provider = reg.default
                self.assertIsInstance(default_provider, MockProvider)

        def test_default_provider_name_property(self):
            """测试 default_provider_name 属性"""
            reg = ProviderRegistry()
            self.assertEqual(reg.default_provider_name, "siliconflow")

            reg.register("mock", MockProvider)
            reg.set_default("mock")
            self.assertEqual(reg.default_provider_name, "mock")

        def test_clear_instance(self):
            """测试清除单个实例"""
            reg = ProviderRegistry()
            reg.register("mock", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider = reg.get("mock")
                self.assertIn("mock", reg._instances)

                reg.clear_instance("mock")
                self.assertNotIn("mock", reg._instances)
                self.assertTrue(provider._closed)

        def test_clear_instance_nonexistent(self):
            """测试清除不存在的实例不报错"""
            reg = ProviderRegistry()

            reg.clear_instance("nonexistent")

        def test_clear_all_instances(self):
            """测试清除所有实例"""
            reg = ProviderRegistry()
            reg.register("mock1", MockProvider)
            reg.register("mock2", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider1 = reg.get("mock1")
                provider2 = reg.get("mock2")

                self.assertIn("mock1", reg._instances)
                self.assertIn("mock2", reg._instances)

                reg.clear_all_instances()

                self.assertNotIn("mock1", reg._instances)
                self.assertNotIn("mock2", reg._instances)
                self.assertTrue(provider1._closed)
                self.assertTrue(provider2._closed)

    class TestRegistryHelpers(unittest.TestCase):
        """注册表便捷函数单元测试"""

        def setUp(self):
            """测试前准备 - 重置单例"""
            global _registry
            _registry = None
            ProviderRegistry._instance = None
            ProviderRegistry._providers = {}
            ProviderRegistry._instances = {}
            ProviderRegistry._default_provider = "siliconflow"

        def test_get_registry_returns_singleton(self):
            """测试 _get_registry 返回单例"""
            reg1 = _get_registry()
            reg2 = _get_registry()
            self.assertIs(reg1, reg2)

        def test_get_provider_with_name(self):
            """测试带名称的 get_provider"""
            reg = _get_registry()
            reg.register("mock", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider = get_provider("mock")
                self.assertIsInstance(provider, MockProvider)

        def test_get_provider_without_name(self):
            """测试不带名称的 get_provider 返回默认"""
            reg = _get_registry()
            reg.register("mock", MockProvider)
            reg.set_default("mock")

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider = get_provider()
                self.assertIsInstance(provider, MockProvider)

        def test_create_provider(self):
            """测试 create_provider 函数"""
            reg = _get_registry()
            reg.register("mock", MockProvider)

            with patch("provider.siliconflow.SiliconFlowProvider", MockProvider):
                provider1 = create_provider("mock")
                provider2 = create_provider("mock")
                self.assertIsNot(provider1, provider2)

        def test_list_providers(self):
            """测试 list_providers 函数"""
            reg = _get_registry()
            reg.register("mock", MockProvider)

            providers = list_providers()
            provider_names = [p["name"] for p in providers]
            self.assertIn("mock", provider_names)

        def test_register_provider(self):
            """测试 register_provider 函数"""
            class NewMock(MockProvider):
                pass

            register_provider("new_mock", NewMock)

            reg = _get_registry()
            providers = reg.list_providers()
            provider_names = [p["name"] for p in providers]
            self.assertIn("new_mock", provider_names)

    unittest.main(verbosity=2)
