"""
Qwen (阿里千问) Provider 实现
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

from config.settings import Settings, get_settings
from provider.openai_compatible import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    """
    Qwen (阿里千问) LLM Provider 实现

    兼容 OpenAI API 格式（使用 Dashscope 兼容模式）
    """

    _provider_name: str = "qwen"
    _default_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    _default_model: str = "qwen-turbo"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = None,
        settings: Settings = None,
    ):
        """
        初始化 Qwen Provider

        Args:
            api_key: API 密钥，如果不提供则从配置读取
            base_url: API 基础 URL，如果不提供则从配置读取
            default_model: 默认模型，如果不提供则从配置读取
            settings: 配置实例，如果不提供则使用全局配置
        """
        self._settings = settings or get_settings()

        self.api_key = api_key or self._get_api_key_from_settings()
        self.base_url = base_url or self._settings.qwen_base_url
        self._default_model = default_model or self._settings.qwen_model

        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        import requests

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _get_api_key_from_settings(self) -> str:
        """从配置中获取 API 密钥"""
        return self._settings.qwen_api_key or self._settings.dashscope_api_key or ""


if __name__ == "__main__":
    import unittest
    from unittest.mock import Mock, patch, MagicMock

    class TestQwenProvider(unittest.TestCase):
        """QwenProvider 单元测试"""

        def setUp(self):
            """测试前准备"""
            self.mock_settings = Mock()
            self.mock_settings.qwen_api_key = "test-key"
            self.mock_settings.dashscope_api_key = None
            self.mock_settings.qwen_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.mock_settings.qwen_model = "qwen-turbo"
            self.mock_settings.request_timeout = 60
            self.mock_settings.max_retries = 3
            self.mock_settings.retry_delay = 1.0
            self.mock_settings.temperature = 0.7
            self.mock_settings.max_tokens = 4096
            self.mock_settings.stream_timeout = 120
            self.mock_settings.first_token_timeout = 30

        @patch("provider.qwen.requests.Session")
        def test_init(self, mock_session_class):
            """测试初始化"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            provider = QwenProvider(settings=self.mock_settings)

            self.assertEqual(provider.provider_name, "qwen")
            self.assertEqual(
                provider.base_url,
                "https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            self.assertEqual(provider.default_model, "qwen-turbo")

        @patch("provider.qwen.requests.Session")
        def test_dashscope_api_key_alias(self, mock_session_class):
            """测试 dashscope_api_key 别名"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            self.mock_settings.qwen_api_key = None
            self.mock_settings.dashscope_api_key = "dashscope-key"

            provider = QwenProvider.__new__(QwenProvider)
            provider._settings = self.mock_settings

            api_key = provider._get_api_key_from_settings()
            self.assertEqual(api_key, "dashscope-key")

        @patch("provider.qwen.requests.Session")
        def test_custom_params(self, mock_session_class):
            """测试自定义参数"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            provider = QwenProvider(
                api_key="custom-key",
                base_url="https://custom.api/v1/",
                default_model="qwen-plus",
                settings=self.mock_settings,
            )

            self.assertEqual(provider.base_url, "https://custom.api/v1")
            self.assertEqual(provider.default_model, "qwen-plus")

    unittest.main(verbosity=2)
