"""
Claude (Anthropic) Provider 实现

Claude API 与 OpenAI API 不兼容，需要单独实现
文档: https://platform.claude.com/docs/en/api/overview
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

import json
import time
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


class ClaudeProvider(LLMProvider):
    """
    Claude (Anthropic) LLM Provider 实现

    注意: Claude API 与 OpenAI API 不兼容，需要单独实现
    """

    _provider_name: str = "claude"
    _default_base_url: str = "https://api.anthropic.com"
    _default_model: str = "claude-3-5-sonnet-20241022"
    _api_version: str = "2023-06-01"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = None,
        settings: Settings = None,
    ):
        """
        初始化 Claude Provider

        Args:
            api_key: API 密钥，如果不提供则从配置读取
            base_url: API 基础 URL，如果不提供则从配置读取
            default_model: 默认模型，如果不提供则从配置读取
            settings: 配置实例，如果不提供则使用全局配置
        """
        self._settings = settings or get_settings()

        self.api_key = api_key or self._get_api_key_from_settings()
        self.base_url = base_url or self._settings.claude_base_url
        self._default_model = default_model or self._settings.claude_model

        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        self._session = requests.Session()
        self._session.headers.update(
            {
                "x-api-key": self.api_key,
                "anthropic-version": self._api_version,
                "Content-Type": "application/json",
            }
        )

    def _get_api_key_from_settings(self) -> str:
        """从配置中获取 API 密钥"""
        return self._settings.claude_api_key or self._settings.anthropic_api_key or ""

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

    def _convert_messages_to_claude_format(
        self, messages: List[Message]
    ) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """
        将消息转换为 Claude API 格式

        Claude API 要求:
        - system message 作为单独的参数
        - user/assistant 消息交替出现
        - 不支持 tool 角色（需要特殊处理）

        Returns:
            tuple: (system_prompt, claude_messages)
        """
        system_prompt = None
        claude_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role in ["user", "assistant"]:
                claude_msg = {
                    "role": msg.role,
                    "content": msg.content,
                }
                claude_messages.append(claude_msg)
            elif msg.role == "tool":
                if claude_messages:
                    last_msg = claude_messages[-1]
                    if last_msg["role"] == "assistant":
                        tool_content = {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id or "unknown",
                            "content": msg.content,
                        }
                        if isinstance(last_msg["content"], list):
                            last_msg["content"].append(tool_content)
                        else:
                            last_msg["content"] = [
                                {"type": "text", "text": last_msg["content"]},
                                tool_content,
                            ]
            elif msg.role == "assistant" and msg.tool_calls:
                tool_content = []
                for tool_call in msg.tool_calls:
                    function = tool_call.get("function", {})
                    tool_content.append(
                        {
                            "type": "tool_use",
                            "id": tool_call.get("id", "unknown"),
                            "name": function.get("name", ""),
                            "input": json.loads(function.get("arguments", "{}")),
                        }
                    )
                if msg.content:
                    tool_content.insert(
                        0, {"type": "text", "text": msg.content}
                    )
                claude_messages.append(
                    {"role": "assistant", "content": tool_content}
                )

        return system_prompt, claude_messages

    def _convert_tools_to_claude_format(
        self, tools: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        将工具定义转换为 Claude API 格式

        OpenAI 格式:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "description",
                "parameters": {...}
            }
        }

        Claude 格式:
        {
            "name": "tool_name",
            "description": "description",
            "input_schema": {...}
        }
        """
        if not tools:
            return None

        claude_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                claude_tool = {
                    "name": function.get("name", ""),
                    "description": function.get("description", ""),
                    "input_schema": function.get("parameters", {}),
                }
                claude_tools.append(claude_tool)

        return claude_tools if claude_tools else None

    def _parse_claude_response(
        self, response_data: Dict[str, Any], model: str
    ) -> ChatCompletionResponse:
        """
        解析 Claude API 响应为 ChatCompletionResponse
        """
        content_blocks = response_data.get("content", [])
        text_content = ""
        tool_calls = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_call = {
                    "id": block.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": block.get("name", ""),
                        "arguments": json.dumps(block.get("input", {})),
                    },
                }
                tool_calls.append(tool_call)

        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0)
            + usage_data.get("output_tokens", 0),
        )

        message = Message(
            role="assistant",
            content=text_content,
            tool_calls=tool_calls if tool_calls else None,
        )

        choice = ChatCompletionChoice(
            index=0,
            message=message,
            finish_reason=response_data.get("stop_reason", "stop"),
        )

        return ChatCompletionResponse(
            id=response_data.get("id", ""),
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[choice],
            usage=usage,
        )

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

        system_prompt, claude_messages = self._convert_messages_to_claude_format(
            messages
        )
        claude_tools = self._convert_tools_to_claude_format(tools)

        request_data: Dict[str, Any] = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            request_data["system"] = system_prompt

        if claude_tools:
            request_data["tools"] = claude_tools

        response_data = self._request(
            method="POST",
            endpoint="/v1/messages",
            data=request_data,
        )

        return self._parse_claude_response(response_data, model)

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

        system_prompt, claude_messages = self._convert_messages_to_claude_format(
            messages
        )
        claude_tools = self._convert_tools_to_claude_format(tools)

        request_data: Dict[str, Any] = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if system_prompt:
            request_data["system"] = system_prompt

        if claude_tools:
            request_data["tools"] = claude_tools

        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self._api_version,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        stream_timeout = getattr(self._settings, "stream_timeout", 120)

        try:
            response = self._session.post(
                url,
                json=request_data,
                headers=headers,
                stream=True,
                timeout=stream_timeout,
            )

            if response.status_code >= 400:
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
                    event_type = chunk.get("type")

                    if event_type == "content_block_delta":
                        delta = chunk.get("delta", {})
                        if delta.get("type") == "text_delta":
                            content = delta.get("text", "")
                            if content:
                                yield content

                    elif event_type == "message_stop":
                        break

                except json.JSONDecodeError:
                    continue

        except requests.exceptions.Timeout:
            raise APIError(
                "请求超时。请尝试增加 STREAM_TIMEOUT 环境变量的值。",
                provider=self._provider_name,
            )
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"网络错误: {str(e)}", provider=self._provider_name) from e

    def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表

        Claude API 目前没有公开的列出模型的端点
        返回一些常用的 Claude 模型

        Returns:
            模型列表
        """
        return [
            {
                "id": "claude-3-5-sonnet-20241022",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
            {
                "id": "claude-3-5-haiku-20241022",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
            {
                "id": "claude-3-opus-20240229",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
            {
                "id": "claude-3-sonnet-20240229",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
            {
                "id": "claude-3-haiku-20240307",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
        ]

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
    from provider.base import Message

    class TestClaudeProvider(unittest.TestCase):
        """ClaudeProvider 单元测试"""

        def setUp(self):
            """测试前准备"""
            self.mock_settings = Mock()
            self.mock_settings.claude_api_key = "test-key"
            self.mock_settings.anthropic_api_key = None
            self.mock_settings.claude_base_url = "https://api.anthropic.com"
            self.mock_settings.claude_model = "claude-3-5-sonnet-20241022"
            self.mock_settings.request_timeout = 60
            self.mock_settings.max_retries = 3
            self.mock_settings.retry_delay = 1.0
            self.mock_settings.temperature = 0.7
            self.mock_settings.max_tokens = 4096
            self.mock_settings.stream_timeout = 120
            self.mock_settings.first_token_timeout = 30

        @patch("provider.claude.requests.Session")
        def test_init(self, mock_session_class):
            """测试初始化"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            provider = ClaudeProvider(settings=self.mock_settings)

            self.assertEqual(provider.provider_name, "claude")
            self.assertEqual(provider.base_url, "https://api.anthropic.com")
            self.assertEqual(provider.default_model, "claude-3-5-sonnet-20241022")

        @patch("provider.claude.requests.Session")
        def test_anthropic_api_key_alias(self, mock_session_class):
            """测试 anthropic_api_key 别名"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            self.mock_settings.claude_api_key = None
            self.mock_settings.anthropic_api_key = "anthropic-key"

            provider = ClaudeProvider.__new__(ClaudeProvider)
            provider._settings = self.mock_settings

            api_key = provider._get_api_key_from_settings()
            self.assertEqual(api_key, "anthropic-key")

        @patch("provider.claude.requests.Session")
        def test_custom_params(self, mock_session_class):
            """测试自定义参数"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            provider = ClaudeProvider(
                api_key="custom-key",
                base_url="https://custom.api/",
                default_model="claude-3-opus-20240229",
                settings=self.mock_settings,
            )

            self.assertEqual(provider.base_url, "https://custom.api")
            self.assertEqual(provider.default_model, "claude-3-opus-20240229")

        @patch("provider.claude.requests.Session")
        def test_provider_name(self, mock_session_class):
            """测试 provider_name"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            provider = ClaudeProvider(settings=self.mock_settings)
            self.assertEqual(provider.provider_name, "claude")

        def test_convert_messages_to_claude_format(self):
            """测试消息格式转换"""
            provider = ClaudeProvider.__new__(ClaudeProvider)

            messages = [
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content="Hello!"),
                Message(role="assistant", content="Hi there!"),
            ]

            system_prompt, claude_messages = provider._convert_messages_to_claude_format(
                messages
            )

            self.assertEqual(system_prompt, "You are a helpful assistant.")
            self.assertEqual(len(claude_messages), 2)
            self.assertEqual(claude_messages[0]["role"], "user")
            self.assertEqual(claude_messages[0]["content"], "Hello!")
            self.assertEqual(claude_messages[1]["role"], "assistant")
            self.assertEqual(claude_messages[1]["content"], "Hi there!")

        def test_convert_messages_to_claude_format_no_system(self):
            """测试没有系统消息的转换"""
            provider = ClaudeProvider.__new__(ClaudeProvider)

            messages = [
                Message(role="user", content="Hello!"),
            ]

            system_prompt, claude_messages = provider._convert_messages_to_claude_format(
                messages
            )

            self.assertIsNone(system_prompt)
            self.assertEqual(len(claude_messages), 1)
            self.assertEqual(claude_messages[0]["role"], "user")

        def test_convert_tools_to_claude_format(self):
            """测试工具格式转换"""
            provider = ClaudeProvider.__new__(ClaudeProvider)

            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather",
                        "parameters": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}},
                            "required": ["city"],
                        },
                    },
                }
            ]

            claude_tools = provider._convert_tools_to_claude_format(openai_tools)

            self.assertEqual(len(claude_tools), 1)
            self.assertEqual(claude_tools[0]["name"], "get_weather")
            self.assertEqual(claude_tools[0]["description"], "Get the weather")
            self.assertIn("input_schema", claude_tools[0])

        def test_convert_tools_to_claude_format_none(self):
            """测试 None 工具转换"""
            provider = ClaudeProvider.__new__(ClaudeProvider)

            result = provider._convert_tools_to_claude_format(None)
            self.assertIsNone(result)

            result = provider._convert_tools_to_claude_format([])
            self.assertIsNone(result)

        def test_parse_claude_response(self):
            """测试 Claude 响应解析"""
            provider = ClaudeProvider.__new__(ClaudeProvider)

            response_data = {
                "id": "msg_123",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Hello, how can I help?"}],
                "model": "claude-3-5-sonnet-20241022",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 20},
            }

            result = provider._parse_claude_response(
                response_data, "claude-3-5-sonnet-20241022"
            )

            self.assertEqual(result.id, "msg_123")
            self.assertEqual(result.content, "Hello, how can I help?")
            self.assertEqual(result.usage.prompt_tokens, 10)
            self.assertEqual(result.usage.completion_tokens, 20)
            self.assertEqual(result.usage.total_tokens, 30)

        @patch("provider.claude.requests.Session")
        def test_list_models(self, mock_session_class):
            """测试 list_models"""
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            provider = ClaudeProvider(settings=self.mock_settings)
            models = provider.list_models()

            self.assertGreater(len(models), 0)
            self.assertIn("id", models[0])
            self.assertIn("object", models[0])

    unittest.main(verbosity=2)
