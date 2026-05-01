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
        message_data = data.get("message", {})
        return cls(
            index=data.get("index", 0),
            message=Message.from_dict(message_data),
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
