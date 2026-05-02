"""
Provider 基类和数据模型
定义统一的 LLM 提供商接口和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Iterator


@dataclass
class Message:
    """消息对象"""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            data["name"] = self.name
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
        )


@dataclass
class FunctionCall:
    """函数调用对象"""

    name: str
    arguments: str
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {"name": self.name, "arguments": self.arguments}
        if self.id:
            data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunctionCall":
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            arguments=data.get("arguments", "{}"),
            id=data.get("id"),
        )


@dataclass
class Usage:
    """Token使用情况"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Usage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class ChatCompletionChoice:
    """对话完成选项"""

    index: int = 0
    message: Message = field(
        default_factory=lambda: Message(role="assistant", content="")
    )
    finish_reason: Optional[str] = None
    delta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "index": self.index,
            "message": self.message.to_dict(),
            "finish_reason": self.finish_reason,
        }
        if self.delta:
            data["delta"] = self.delta
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatCompletionChoice":
        if "message" in data and data["message"] is not None:
            message = Message.from_dict(data["message"])
        else:
            message = Message(role="assistant", content="")
        return cls(
            index=data.get("index", 0),
            message=message,
            finish_reason=data.get("finish_reason"),
            delta=data.get("delta"),
        )


@dataclass
class ChatCompletionResponse:
    """对话完成响应"""

    id: str = ""
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: List[ChatCompletionChoice] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    system_fingerprint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [c.to_dict() for c in self.choices],
            "usage": self.usage.to_dict(),
        }
        if self.system_fingerprint:
            data["system_fingerprint"] = self.system_fingerprint
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatCompletionResponse":
        choices_data = data.get("choices", [])
        choices = [ChatCompletionChoice.from_dict(c) for c in choices_data]
        usage_data = data.get("usage", {})

        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices,
            usage=Usage.from_dict(usage_data),
            system_fingerprint=data.get("system_fingerprint"),
        )

    @property
    def content(self) -> str:
        """获取第一个选择的消息内容"""
        if self.choices:
            return self.choices[0].message.content
        return ""

    @property
    def tool_calls(self) -> Optional[List[Dict[str, Any]]]:
        """获取工具调用"""
        if self.choices and self.choices[0].message.tool_calls:
            return self.choices[0].message.tool_calls
        return None


@dataclass
class ChatCompletionRequest:
    """对话完成请求"""

    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    stop: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为API请求格式"""
        data: Dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
        }
        if self.stop:
            data["stop"] = self.stop
        if self.tools:
            data["tools"] = self.tools
        if self.tool_choice:
            data["tool_choice"] = self.tool_choice
        if self.response_format:
            data["response_format"] = self.response_format
        return data


class APIError(Exception):
    """API错误"""

    def __init__(
        self,
        message: str,
        status_code: int = None,
        response: Dict = None,
        provider: str = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.provider = provider


class NetworkError(APIError):
    """网络错误"""

    pass


class AuthenticationError(APIError):
    """认证错误"""

    pass


class RateLimitError(APIError):
    """速率限制错误"""

    pass


class ModelNotFoundError(APIError):
    """模型不存在错误"""

    pass


class LLMProvider(ABC):
    """
    LLM 提供商接口
    所有 LLM 提供商都必须实现此接口

    设计理念：
    - Provider 只负责与 LLM API 交互
    - 不依赖 agent 状态、内存或通道
    - 纯文本/数据转换
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """默认模型名称"""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """API 基础 URL"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        流式对话

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
        pass

    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表

        Returns:
            模型列表
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭资源"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


if __name__ == "__main__":
    import unittest
    from unittest.mock import Mock, patch, MagicMock
    from typing import List, Dict, Any

    class TestMessage(unittest.TestCase):
        """Message 数据类单元测试"""

        def test_init_defaults(self):
            """测试默认初始化"""
            msg = Message(role="user", content="Hello")
            self.assertEqual(msg.role, "user")
            self.assertEqual(msg.content, "Hello")
            self.assertIsNone(msg.name)
            self.assertIsNone(msg.tool_calls)
            self.assertIsNone(msg.tool_call_id)

        def test_init_full(self):
            """测试完整初始化"""
            tool_calls = [{"id": "1", "type": "function"}]
            msg = Message(
                role="assistant",
                content="Hi",
                name="test_bot",
                tool_calls=tool_calls,
                tool_call_id="call_123",
            )
            self.assertEqual(msg.role, "assistant")
            self.assertEqual(msg.content, "Hi")
            self.assertEqual(msg.name, "test_bot")
            self.assertEqual(msg.tool_calls, tool_calls)
            self.assertEqual(msg.tool_call_id, "call_123")

        def test_to_dict_basic(self):
            """测试基本的 to_dict"""
            msg = Message(role="user", content="Hello")
            result = msg.to_dict()
            self.assertEqual(result, {"role": "user", "content": "Hello"})

        def test_to_dict_full(self):
            """测试完整的 to_dict"""
            tool_calls = [{"id": "1", "type": "function"}]
            msg = Message(
                role="assistant",
                content="Hi",
                name="test_bot",
                tool_calls=tool_calls,
                tool_call_id="call_123",
            )
            result = msg.to_dict()
            self.assertEqual(result["role"], "assistant")
            self.assertEqual(result["content"], "Hi")
            self.assertEqual(result["name"], "test_bot")
            self.assertEqual(result["tool_calls"], tool_calls)
            self.assertEqual(result["tool_call_id"], "call_123")

        def test_from_dict_basic(self):
            """测试基本的 from_dict"""
            data = {"role": "user", "content": "Hello"}
            msg = Message.from_dict(data)
            self.assertEqual(msg.role, "user")
            self.assertEqual(msg.content, "Hello")
            self.assertIsNone(msg.name)
            self.assertIsNone(msg.tool_calls)
            self.assertIsNone(msg.tool_call_id)

        def test_from_dict_full(self):
            """测试完整的 from_dict"""
            tool_calls = [{"id": "1", "type": "function"}]
            data = {
                "role": "assistant",
                "content": "Hi",
                "name": "test_bot",
                "tool_calls": tool_calls,
                "tool_call_id": "call_123",
            }
            msg = Message.from_dict(data)
            self.assertEqual(msg.role, "assistant")
            self.assertEqual(msg.content, "Hi")
            self.assertEqual(msg.name, "test_bot")
            self.assertEqual(msg.tool_calls, tool_calls)
            self.assertEqual(msg.tool_call_id, "call_123")

        def test_from_dict_defaults(self):
            """测试 from_dict 的默认值"""
            data = {}
            msg = Message.from_dict(data)
            self.assertEqual(msg.role, "user")
            self.assertEqual(msg.content, "")


    class TestFunctionCall(unittest.TestCase):
        """FunctionCall 数据类单元测试"""

        def test_init_defaults(self):
            """测试默认初始化"""
            func = FunctionCall(name="get_weather", arguments='{"city": "Beijing"}')
            self.assertEqual(func.name, "get_weather")
            self.assertEqual(func.arguments, '{"city": "Beijing"}')
            self.assertIsNone(func.id)

        def test_init_full(self):
            """测试完整初始化"""
            func = FunctionCall(
                name="get_weather",
                arguments='{"city": "Beijing"}',
                id="call_123",
            )
            self.assertEqual(func.name, "get_weather")
            self.assertEqual(func.arguments, '{"city": "Beijing"}')
            self.assertEqual(func.id, "call_123")

        def test_to_dict_basic(self):
            """测试基本的 to_dict"""
            func = FunctionCall(name="get_weather", arguments='{"city": "Beijing"}')
            result = func.to_dict()
            self.assertEqual(
                result,
                {"name": "get_weather", "arguments": '{"city": "Beijing"}'},
            )

        def test_to_dict_full(self):
            """测试完整的 to_dict"""
            func = FunctionCall(
                name="get_weather",
                arguments='{"city": "Beijing"}',
                id="call_123",
            )
            result = func.to_dict()
            self.assertEqual(result["name"], "get_weather")
            self.assertEqual(result["arguments"], '{"city": "Beijing"}')
            self.assertEqual(result["id"], "call_123")

        def test_from_dict_basic(self):
            """测试基本的 from_dict"""
            data = {"name": "get_weather", "arguments": '{"city": "Beijing"}'}
            func = FunctionCall.from_dict(data)
            self.assertEqual(func.name, "get_weather")
            self.assertEqual(func.arguments, '{"city": "Beijing"}')
            self.assertIsNone(func.id)

        def test_from_dict_full(self):
            """测试完整的 from_dict"""
            data = {
                "name": "get_weather",
                "arguments": '{"city": "Beijing"}',
                "id": "call_123",
            }
            func = FunctionCall.from_dict(data)
            self.assertEqual(func.name, "get_weather")
            self.assertEqual(func.arguments, '{"city": "Beijing"}')
            self.assertEqual(func.id, "call_123")

        def test_from_dict_defaults(self):
            """测试 from_dict 的默认值"""
            data = {}
            func = FunctionCall.from_dict(data)
            self.assertEqual(func.name, "")
            self.assertEqual(func.arguments, "{}")


    class TestUsage(unittest.TestCase):
        """Usage 数据类单元测试"""

        def test_init_defaults(self):
            """测试默认初始化"""
            usage = Usage()
            self.assertEqual(usage.prompt_tokens, 0)
            self.assertEqual(usage.completion_tokens, 0)
            self.assertEqual(usage.total_tokens, 0)

        def test_init_full(self):
            """测试完整初始化"""
            usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
            self.assertEqual(usage.prompt_tokens, 10)
            self.assertEqual(usage.completion_tokens, 20)
            self.assertEqual(usage.total_tokens, 30)

        def test_to_dict(self):
            """测试 to_dict"""
            usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
            result = usage.to_dict()
            self.assertEqual(
                result,
                {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            )

        def test_from_dict_basic(self):
            """测试基本的 from_dict"""
            data = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            usage = Usage.from_dict(data)
            self.assertEqual(usage.prompt_tokens, 10)
            self.assertEqual(usage.completion_tokens, 20)
            self.assertEqual(usage.total_tokens, 30)

        def test_from_dict_defaults(self):
            """测试 from_dict 的默认值"""
            data = {}
            usage = Usage.from_dict(data)
            self.assertEqual(usage.prompt_tokens, 0)
            self.assertEqual(usage.completion_tokens, 0)
            self.assertEqual(usage.total_tokens, 0)

        def test_from_dict_partial(self):
            """测试部分字段的 from_dict"""
            data = {"prompt_tokens": 10}
            usage = Usage.from_dict(data)
            self.assertEqual(usage.prompt_tokens, 10)
            self.assertEqual(usage.completion_tokens, 0)
            self.assertEqual(usage.total_tokens, 0)


    class TestChatCompletionChoice(unittest.TestCase):
        """ChatCompletionChoice 数据类单元测试"""

        def test_init_defaults(self):
            """测试默认初始化"""
            choice = ChatCompletionChoice()
            self.assertEqual(choice.index, 0)
            self.assertEqual(choice.message.role, "assistant")
            self.assertEqual(choice.message.content, "")
            self.assertIsNone(choice.finish_reason)
            self.assertIsNone(choice.delta)

        def test_init_full(self):
            """测试完整初始化"""
            msg = Message(role="assistant", content="Hello")
            delta = {"content": "H"}
            choice = ChatCompletionChoice(
                index=1,
                message=msg,
                finish_reason="stop",
                delta=delta,
            )
            self.assertEqual(choice.index, 1)
            self.assertEqual(choice.message, msg)
            self.assertEqual(choice.finish_reason, "stop")
            self.assertEqual(choice.delta, delta)

        def test_to_dict_basic(self):
            """测试基本的 to_dict"""
            msg = Message(role="assistant", content="Hello")
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="stop")
            result = choice.to_dict()
            self.assertEqual(result["index"], 0)
            self.assertEqual(result["message"], {"role": "assistant", "content": "Hello"})
            self.assertEqual(result["finish_reason"], "stop")
            self.assertNotIn("delta", result)

        def test_to_dict_with_delta(self):
            """测试带 delta 的 to_dict"""
            msg = Message(role="assistant", content="Hello")
            delta = {"content": "H"}
            choice = ChatCompletionChoice(
                index=0,
                message=msg,
                finish_reason="stop",
                delta=delta,
            )
            result = choice.to_dict()
            self.assertEqual(result["delta"], delta)

        def test_from_dict_basic(self):
            """测试基本的 from_dict"""
            data = {
                "index": 1,
                "message": {"role": "assistant", "content": "Hi"},
                "finish_reason": "length",
            }
            choice = ChatCompletionChoice.from_dict(data)
            self.assertEqual(choice.index, 1)
            self.assertEqual(choice.message.role, "assistant")
            self.assertEqual(choice.message.content, "Hi")
            self.assertEqual(choice.finish_reason, "length")
            self.assertIsNone(choice.delta)

        def test_from_dict_with_delta(self):
            """测试带 delta 的 from_dict"""
            data = {
                "index": 0,
                "message": {"role": "assistant", "content": "Hi"},
                "finish_reason": "stop",
                "delta": {"content": "H"},
            }
            choice = ChatCompletionChoice.from_dict(data)
            self.assertEqual(choice.delta, {"content": "H"})

        def test_from_dict_defaults(self):
            """测试 from_dict 的默认值"""
            data = {}
            choice = ChatCompletionChoice.from_dict(data)
            self.assertEqual(choice.index, 0)
            self.assertEqual(choice.message.role, "assistant")
            self.assertEqual(choice.message.content, "")
            self.assertIsNone(choice.finish_reason)
            self.assertIsNone(choice.delta)


    class TestChatCompletionResponse(unittest.TestCase):
        """ChatCompletionResponse 数据类单元测试"""

        def test_init_defaults(self):
            """测试默认初始化"""
            resp = ChatCompletionResponse()
            self.assertEqual(resp.id, "")
            self.assertEqual(resp.object, "chat.completion")
            self.assertEqual(resp.created, 0)
            self.assertEqual(resp.model, "")
            self.assertEqual(resp.choices, [])
            self.assertEqual(resp.usage.prompt_tokens, 0)
            self.assertIsNone(resp.system_fingerprint)

        def test_init_full(self):
            """测试完整初始化"""
            msg = Message(role="assistant", content="Hello")
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="stop")
            usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

            resp = ChatCompletionResponse(
                id="chat_123",
                object="chat.completion",
                created=1700000000,
                model="gpt-4",
                choices=[choice],
                usage=usage,
                system_fingerprint="fp_123",
            )

            self.assertEqual(resp.id, "chat_123")
            self.assertEqual(resp.object, "chat.completion")
            self.assertEqual(resp.created, 1700000000)
            self.assertEqual(resp.model, "gpt-4")
            self.assertEqual(len(resp.choices), 1)
            self.assertEqual(resp.usage.prompt_tokens, 10)
            self.assertEqual(resp.system_fingerprint, "fp_123")

        def test_content_property(self):
            """测试 content 属性"""
            msg = Message(role="assistant", content="Hello World")
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="stop")
            resp = ChatCompletionResponse(choices=[choice])
            self.assertEqual(resp.content, "Hello World")

        def test_content_property_empty_choices(self):
            """测试空 choices 的 content 属性"""
            resp = ChatCompletionResponse(choices=[])
            self.assertEqual(resp.content, "")

        def test_tool_calls_property(self):
            """测试 tool_calls 属性"""
            tool_calls = [{"id": "1", "type": "function"}]
            msg = Message(role="assistant", content="", tool_calls=tool_calls)
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="tool_calls")
            resp = ChatCompletionResponse(choices=[choice])
            self.assertEqual(resp.tool_calls, tool_calls)

        def test_tool_calls_property_none(self):
            """测试无 tool_calls 的 tool_calls 属性"""
            msg = Message(role="assistant", content="Hello")
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="stop")
            resp = ChatCompletionResponse(choices=[choice])
            self.assertIsNone(resp.tool_calls)

        def test_to_dict_basic(self):
            """测试基本的 to_dict"""
            msg = Message(role="assistant", content="Hello")
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="stop")
            usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

            resp = ChatCompletionResponse(
                id="chat_123",
                created=1700000000,
                model="gpt-4",
                choices=[choice],
                usage=usage,
            )

            result = resp.to_dict()
            self.assertEqual(result["id"], "chat_123")
            self.assertEqual(result["object"], "chat.completion")
            self.assertEqual(result["created"], 1700000000)
            self.assertEqual(result["model"], "gpt-4")
            self.assertEqual(len(result["choices"]), 1)
            self.assertEqual(result["usage"]["prompt_tokens"], 10)
            self.assertNotIn("system_fingerprint", result)

        def test_to_dict_with_system_fingerprint(self):
            """测试带 system_fingerprint 的 to_dict"""
            msg = Message(role="assistant", content="Hello")
            choice = ChatCompletionChoice(index=0, message=msg, finish_reason="stop")
            usage = Usage()

            resp = ChatCompletionResponse(
                id="chat_123",
                choices=[choice],
                usage=usage,
                system_fingerprint="fp_123",
            )

            result = resp.to_dict()
            self.assertEqual(result["system_fingerprint"], "fp_123")

        def test_from_dict_basic(self):
            """测试基本的 from_dict"""
            data = {
                "id": "chat_123",
                "object": "chat.completion",
                "created": 1700000000,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            }

            resp = ChatCompletionResponse.from_dict(data)
            self.assertEqual(resp.id, "chat_123")
            self.assertEqual(resp.model, "gpt-4")
            self.assertEqual(len(resp.choices), 1)
            self.assertEqual(resp.choices[0].message.content, "Hello")
            self.assertEqual(resp.usage.prompt_tokens, 10)

        def test_from_dict_with_system_fingerprint(self):
            """测试带 system_fingerprint 的 from_dict"""
            data = {
                "id": "chat_123",
                "object": "chat.completion",
                "created": 1700000000,
                "model": "gpt-4",
                "choices": [],
                "usage": {},
                "system_fingerprint": "fp_123",
            }

            resp = ChatCompletionResponse.from_dict(data)
            self.assertEqual(resp.system_fingerprint, "fp_123")


    class TestChatCompletionRequest(unittest.TestCase):
        """ChatCompletionRequest 数据类单元测试"""

        def test_init_minimal(self):
            """测试最小化初始化"""
            messages = [Message(role="user", content="Hello")]
            req = ChatCompletionRequest(model="gpt-4", messages=messages)

            self.assertEqual(req.model, "gpt-4")
            self.assertEqual(len(req.messages), 1)
            self.assertEqual(req.temperature, 0.7)
            self.assertEqual(req.max_tokens, 4096)
            self.assertEqual(req.top_p, 1.0)
            self.assertEqual(req.frequency_penalty, 0.0)
            self.assertEqual(req.presence_penalty, 0.0)
            self.assertEqual(req.stream, False)
            self.assertIsNone(req.stop)
            self.assertIsNone(req.tools)
            self.assertIsNone(req.tool_choice)
            self.assertIsNone(req.response_format)

        def test_init_full(self):
            """测试完整初始化"""
            messages = [Message(role="user", content="Hello")]
            tools = [{"type": "function", "function": {"name": "test"}}]
            stop = ["stop_word"]
            response_format = {"type": "json_object"}

            req = ChatCompletionRequest(
                model="gpt-4",
                messages=messages,
                temperature=0.5,
                max_tokens=2048,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stream=True,
                stop=stop,
                tools=tools,
                tool_choice="auto",
                response_format=response_format,
            )

            self.assertEqual(req.model, "gpt-4")
            self.assertEqual(req.temperature, 0.5)
            self.assertEqual(req.max_tokens, 2048)
            self.assertEqual(req.top_p, 0.9)
            self.assertEqual(req.frequency_penalty, 0.1)
            self.assertEqual(req.presence_penalty, 0.1)
            self.assertEqual(req.stream, True)
            self.assertEqual(req.stop, stop)
            self.assertEqual(req.tools, tools)
            self.assertEqual(req.tool_choice, "auto")
            self.assertEqual(req.response_format, response_format)

        def test_to_dict_basic(self):
            """测试基本的 to_dict"""
            messages = [Message(role="user", content="Hello")]
            req = ChatCompletionRequest(model="gpt-4", messages=messages)

            result = req.to_dict()
            self.assertEqual(result["model"], "gpt-4")
            self.assertEqual(len(result["messages"]), 1)
            self.assertEqual(result["messages"][0]["role"], "user")
            self.assertEqual(result["temperature"], 0.7)
            self.assertEqual(result["max_tokens"], 4096)
            self.assertEqual(result["stream"], False)
            self.assertNotIn("stop", result)
            self.assertNotIn("tools", result)
            self.assertNotIn("tool_choice", result)
            self.assertNotIn("response_format", result)

        def test_to_dict_with_optional_fields(self):
            """测试带可选字段的 to_dict"""
            messages = [Message(role="user", content="Hello")]
            tools = [{"type": "function", "function": {"name": "test"}}]
            stop = ["stop_word"]
            response_format = {"type": "json_object"}

            req = ChatCompletionRequest(
                model="gpt-4",
                messages=messages,
                stop=stop,
                tools=tools,
                tool_choice="auto",
                response_format=response_format,
            )

            result = req.to_dict()
            self.assertEqual(result["stop"], stop)
            self.assertEqual(result["tools"], tools)
            self.assertEqual(result["tool_choice"], "auto")
            self.assertEqual(result["response_format"], response_format)


    class TestAPIError(unittest.TestCase):
        """APIError 异常类单元测试"""

        def test_init_basic(self):
            """测试基本初始化"""
            err = APIError("Test error message")
            self.assertEqual(str(err), "Test error message")
            self.assertIsNone(err.status_code)
            self.assertIsNone(err.response)
            self.assertIsNone(err.provider)

        def test_init_full(self):
            """测试完整初始化"""
            response = {"error": {"message": "Something went wrong"}}
            err = APIError(
                "Test error message",
                status_code=500,
                response=response,
                provider="test_provider",
            )
            self.assertEqual(str(err), "Test error message")
            self.assertEqual(err.status_code, 500)
            self.assertEqual(err.response, response)
            self.assertEqual(err.provider, "test_provider")

    class TestNetworkError(unittest.TestCase):
        """NetworkError 异常类单元测试"""

        def test_is_subclass_of_api_error(self):
            """测试 NetworkError 是 APIError 的子类"""
            self.assertTrue(issubclass(NetworkError, APIError))

        def test_init(self):
            """测试初始化"""
            err = NetworkError("Connection failed")
            self.assertEqual(str(err), "Connection failed")

    class TestAuthenticationError(unittest.TestCase):
        """AuthenticationError 异常类单元测试"""

        def test_is_subclass_of_api_error(self):
            """测试 AuthenticationError 是 APIError 的子类"""
            self.assertTrue(issubclass(AuthenticationError, APIError))

        def test_init(self):
            """测试初始化"""
            err = AuthenticationError("Invalid API key")
            self.assertEqual(str(err), "Invalid API key")

    class TestRateLimitError(unittest.TestCase):
        """RateLimitError 异常类单元测试"""

        def test_is_subclass_of_api_error(self):
            """测试 RateLimitError 是 APIError 的子类"""
            self.assertTrue(issubclass(RateLimitError, APIError))

        def test_init(self):
            """测试初始化"""
            err = RateLimitError("Rate limit exceeded")
            self.assertEqual(str(err), "Rate limit exceeded")

    class TestModelNotFoundError(unittest.TestCase):
        """ModelNotFoundError 异常类单元测试"""

        def test_is_subclass_of_api_error(self):
            """测试 ModelNotFoundError 是 APIError 的子类"""
            self.assertTrue(issubclass(ModelNotFoundError, APIError))

        def test_init(self):
            """测试初始化"""
            err = ModelNotFoundError("Model not found")
            self.assertEqual(str(err), "Model not found")

    class TestLLMProvider(unittest.TestCase):
        """LLMProvider 抽象基类单元测试"""

        def test_cannot_instantiate_abstract_class(self):
            """测试不能直接实例化抽象基类"""
            with self.assertRaises(TypeError):
                LLMProvider()

        def test_subclass_must_implement_abstract_methods(self):
            """测试子类必须实现抽象方法"""
            with self.assertRaises(TypeError):
                class IncompleteProvider(LLMProvider):
                    pass

                IncompleteProvider()

    unittest.main(verbosity=2)
