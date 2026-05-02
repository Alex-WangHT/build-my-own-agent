"""
OpenAI 兼容 Provider 基类
所有兼容 OpenAI API 格式的 Provider 都可以继承此类

设计理念：
- 封装 OpenAI API 兼容的通用逻辑
- 子类只需覆盖特定的配置项即可
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

import json
import time
from abc import ABC
from typing import List, Optional, Dict, Any, Iterator

import requests

from config.settings import Settings, get_settings
from provider.base import (
    LLMProvider,
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
)


class OpenAICompatibleProvider(LLMProvider, ABC):
    """
    OpenAI 兼容 Provider 基类
    
    提供 OpenAI API 兼容的通用实现
    子类只需设置 provider_name、_default_base_url、_default_model 等属性
    """

    _provider_name: str = "openai_compatible"
    _default_base_url: str = "https://api.openai.com/v1"
    _default_model: str = "gpt-4o"
    _api_key_env_var: str = "OPENAI_API_KEY"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = None,
        settings: Settings = None,
    ):
        """
        初始化 OpenAI 兼容 Provider

        Args:
            api_key: API 密钥，如果不提供则从配置读取
            base_url: API 基础 URL，如果不提供则使用默认值
            default_model: 默认模型，如果不提供则使用默认值
            settings: 配置实例，如果不提供则使用全局配置
        """
        self._settings = settings or get_settings()

        self.api_key = api_key or self._get_api_key_from_settings()
        self.base_url = base_url or self._default_base_url
        self._default_model = default_model or self._default_model

        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _get_api_key_from_settings(self) -> str:
        """
        从配置中获取 API 密钥
        
        子类可以覆盖此方法以使用不同的配置键
        """
        return ""

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def default_model(self) -> str:
        return self._default_model

    @default_model.setter
    def default_model(self, value: str):
        """设置默认模型"""
        self._default_model = value

    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        """设置基础 URL"""
        if value.endswith("/"):
            value = value[:-1]
        self._base_url = value

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        timeout: int = None,
        max_retries: int = None,
        retry_delay: float = None,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求（带重试机制）

        Args:
            method: HTTP 方法（GET, POST 等）
            endpoint: API 端点（不包含 base_url）
            data: 请求数据
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            API 响应数据

        Raises:
            APIError: API 调用错误
            NetworkError: 网络错误
            AuthenticationError: 认证错误
            RateLimitError: 速率限制错误
            ModelNotFoundError: 模型不存在错误
        """
        timeout = timeout or self._settings.request_timeout
        max_retries = max_retries or self._settings.max_retries
        retry_delay = retry_delay or self._settings.retry_delay

        url = f"{self.base_url}{endpoint}"

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = self._session.get(
                        url,
                        params=data,
                        timeout=timeout,
                    )
                else:
                    response = self._session.post(
                        url,
                        json=data,
                        timeout=timeout,
                    )

                if response.status_code == 200:
                    return response.json()

                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"error": {"message": response.text}}

                error_message = error_data.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )

                if response.status_code == 401:
                    raise AuthenticationError(
                        f"认证失败: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                        provider=self._provider_name,
                    )
                elif response.status_code == 404:
                    raise ModelNotFoundError(
                        f"模型不存在: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                        provider=self._provider_name,
                    )
                elif response.status_code == 429:
                    if attempt < max_retries:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError(
                        f"速率限制: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                        provider=self._provider_name,
                    )
                elif response.status_code >= 500:
                    if attempt < max_retries:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                    raise APIError(
                        f"服务器错误: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                        provider=self._provider_name,
                    )
                else:
                    raise APIError(
                        f"API 错误: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                        provider=self._provider_name,
                    )

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = retry_delay * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                raise NetworkError(
                    f"网络错误: {str(e)}",
                    status_code=None,
                    response=None,
                    provider=self._provider_name,
                ) from e

        if last_error:
            raise NetworkError(
                f"网络错误（重试 {max_retries} 次后失败）: {str(last_error)}",
                provider=self._provider_name,
            ) from last_error
        raise APIError("请求失败，未知错误", provider=self._provider_name)

    def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """
        发送对话请求

        Args:
            messages: 消息列表
            model: 模型名称（可选）
            temperature: 生成温度（可选）
            max_tokens: 最大生成 Token 数（可选）
            tools: 可用工具列表（可选）
            **kwargs: 其他参数

        Returns:
            ChatCompletionResponse 响应对象
        """
        model = model or self._default_model
        temperature = (
            temperature if temperature is not None else self._settings.temperature
        )
        max_tokens = (
            max_tokens if max_tokens is not None else self._settings.max_tokens
        )

        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )

        response_data = self._request(
            method="POST",
            endpoint="/chat/completions",
            data=request.to_dict(),
        )

        return ChatCompletionResponse.from_dict(response_data)

    def chat_stream(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        流式对话（SSE）

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 生成温度
            max_tokens: 最大生成 Token 数
            tools: 可用工具列表（可选）
            **kwargs: 其他参数

        Yields:
            每次返回的内容片段
        """
        model = model or self._default_model
        temperature = (
            temperature if temperature is not None else self._settings.temperature
        )
        max_tokens = (
            max_tokens if max_tokens is not None else self._settings.max_tokens
        )

        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            tools=tools,
            **kwargs,
        )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        stream_timeout = getattr(self._settings, "stream_timeout", 120)
        first_token_timeout = getattr(self._settings, "first_token_timeout", 30)

        try:
            response = self._session.post(
                url,
                json=request.to_dict(),
                headers=headers,
                stream=True,
                timeout=stream_timeout,
            )

            if response.status_code == 401:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                error_msg = error_data.get("error", {}).get("message", "认证失败")
                raise AuthenticationError(
                    f"认证失败: {error_msg}",
                    status_code=401,
                    response=error_data,
                    provider=self._provider_name,
                )
            elif response.status_code == 404:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                error_msg = error_data.get("error", {}).get("message", "模型不存在")
                raise ModelNotFoundError(
                    f"模型不存在: {error_msg}",
                    status_code=404,
                    response=error_data,
                    provider=self._provider_name,
                )
            elif response.status_code == 429:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                error_msg = error_data.get("error", {}).get("message", "请求过于频繁")
                raise RateLimitError(
                    f"速率限制: {error_msg}",
                    status_code=429,
                    response=error_data,
                    provider=self._provider_name,
                )
            elif response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                error_msg = error_data.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )
                raise APIError(
                    f"API 错误: {error_msg}",
                    status_code=response.status_code,
                    response=error_data,
                    provider=self._provider_name,
                )

            first_token = True
            start_time = time.time()

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    line = line.decode("utf-8")
                except UnicodeDecodeError:
                    continue

                if not line.startswith("data: "):
                    continue

                data = line[6:]
                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                    choices = chunk.get("choices", [])

                    if not choices:
                        continue

                    choice = choices[0]
                    finish_reason = choice.get("finish_reason")

                    if finish_reason == "stop" or finish_reason == "length":
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                        break

                    delta = choice.get("delta", {})
                    content = delta.get("content", "")

                    if content:
                        if first_token:
                            first_token = False
                        yield content

                except json.JSONDecodeError:
                    continue

            if first_token:
                elapsed = time.time() - start_time
                raise APIError(
                    f"未收到任何响应内容（等待了 {elapsed:.1f} 秒），"
                    f"模型 {model} 可能响应较慢，请尝试增加超时时间 "
                    f"或使用其他模型。",
                    provider=self._provider_name,
                )

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time if "start_time" in dir() else 0
            raise APIError(
                f"请求超时（已等待 {elapsed:.1f} 秒）。"
                f"如果使用的是响应较慢的模型（如 Qwen-4B），"
                f"请尝试增加 STREAM_TIMEOUT 环境变量的值。",
                provider=self._provider_name,
            )
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"网络错误: {str(e)}", provider=self._provider_name) from e

    def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表

        Returns:
            模型列表
        """
        response_data = self._request(
            method="GET",
            endpoint="/models",
        )
        return response_data.get("data", [])

    def close(self) -> None:
        """关闭 HTTP 会话"""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


if __name__ == "__main__":
    import unittest
    from unittest.mock import Mock, patch, MagicMock
    from provider.base import Message, ChatCompletionResponse, Usage

    class TestOpenAICompatibleProvider(unittest.TestCase):
        """OpenAICompatibleProvider 单元测试"""

        def setUp(self):
            """测试前准备"""
            self.mock_settings = Mock()
            self.mock_settings.request_timeout = 60
            self.mock_settings.max_retries = 3
            self.mock_settings.retry_delay = 1.0
            self.mock_settings.temperature = 0.7
            self.mock_settings.max_tokens = 4096
            self.mock_settings.stream_timeout = 120
            self.mock_settings.first_token_timeout = 30

        @patch("provider.openai_compatible.requests.Session")
        def test_init(self, mock_session_class):
            """测试初始化"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            class TestProvider(OpenAICompatibleProvider):
                _provider_name = "test"
                _default_base_url = "https://test.api/v1"
                _default_model = "test-model"

            provider = TestProvider(
                api_key="test-key",
                base_url="https://custom.api/v1/",
                default_model="custom-model",
                settings=self.mock_settings,
            )

            self.assertEqual(provider.provider_name, "test")
            self.assertEqual(provider.base_url, "https://custom.api/v1")
            self.assertEqual(provider.default_model, "custom-model")
            mock_session.headers.update.assert_called_once()

        @patch("provider.openai_compatible.requests.Session")
        def test_default_values(self, mock_session_class):
            """测试默认值"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            class TestProvider(OpenAICompatibleProvider):
                _provider_name = "test"
                _default_base_url = "https://test.api/v1"
                _default_model = "test-model"

            provider = TestProvider(
                api_key="test-key",
                settings=self.mock_settings,
            )

            self.assertEqual(provider.base_url, "https://test.api/v1")
            self.assertEqual(provider.default_model, "test-model")

        @patch("provider.openai_compatible.requests.Session")
        def test_provider_name_property(self, mock_session_class):
            """测试 provider_name 属性"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            class TestProvider(OpenAICompatibleProvider):
                _provider_name = "test_provider"
                _default_base_url = "https://test.api/v1"
                _default_model = "test-model"

            provider = TestProvider(
                api_key="test-key",
                settings=self.mock_settings,
            )

            self.assertEqual(provider.provider_name, "test_provider")

        @patch("provider.openai_compatible.requests.Session")
        def test_default_model_setter(self, mock_session_class):
            """测试 default_model setter"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            class TestProvider(OpenAICompatibleProvider):
                _provider_name = "test"
                _default_base_url = "https://test.api/v1"
                _default_model = "test-model"

            provider = TestProvider(
                api_key="test-key",
                settings=self.mock_settings,
            )

            provider.default_model = "new-model"
            self.assertEqual(provider.default_model, "new-model")

        @patch("provider.openai_compatible.requests.Session")
        def test_base_url_setter(self, mock_session_class):
            """测试 base_url setter"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            class TestProvider(OpenAICompatibleProvider):
                _provider_name = "test"
                _default_base_url = "https://test.api/v1"
                _default_model = "test-model"

            provider = TestProvider(
                api_key="test-key",
                settings=self.mock_settings,
            )

            provider.base_url = "https://new.api/v1/"
            self.assertEqual(provider.base_url, "https://new.api/v1")

        def test_message_to_dict(self):
            """测试 Message 转换"""
            msg = Message(role="user", content="Hello")
            msg_dict = msg.to_dict()
            self.assertEqual(msg_dict["role"], "user")
            self.assertEqual(msg_dict["content"], "Hello")

        def test_message_from_dict(self):
            """测试 Message 从字典创建"""
            data = {"role": "assistant", "content": "Hi there!"}
            msg = Message.from_dict(data)
            self.assertEqual(msg.role, "assistant")
            self.assertEqual(msg.content, "Hi there!")

        def test_usage_from_dict(self):
            """测试 Usage 从字典创建"""
            data = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            usage = Usage.from_dict(data)
            self.assertEqual(usage.prompt_tokens, 10)
            self.assertEqual(usage.completion_tokens, 20)
            self.assertEqual(usage.total_tokens, 30)

    unittest.main(verbosity=2)
