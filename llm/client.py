"""
硅基流动API客户端
使用requests库实现与硅基流动API的交互
"""

import json
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Iterator

import requests

from config.settings import Settings, get_settings


@dataclass
class Message:
    """消息对象"""

    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {"role": self.role, "content": self.content}
        if self.name:
            data["name"] = self.name
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
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
    message: Message = field(default_factory=lambda: Message(role="assistant", content=""))
    finish_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "message": self.message.to_dict(),
            "finish_reason": self.finish_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatCompletionChoice":
        message_data = data.get("message", {})
        return cls(
            index=data.get("index", 0),
            message=Message.from_dict(message_data),
            finish_reason=data.get("finish_reason"),
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [c.to_dict() for c in self.choices],
            "usage": self.usage.to_dict(),
        }

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
        )

    @property
    def content(self) -> str:
        """获取第一个选择的消息内容"""
        if self.choices:
            return self.choices[0].message.content
        return ""


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

    def to_dict(self) -> Dict[str, Any]:
        """转换为API请求格式"""
        data = {
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
        return data


class APIError(Exception):
    """API错误"""

    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NetworkError(APIError):
    """网络错误"""

    pass


class AuthenticationError(APIError):
    """认证错误"""

    pass


class RateLimitError(APIError):
    """速率限制错误"""

    pass


class SiliconFlowClient:
    """硅基流动API客户端"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = None,
        settings: Settings = None,
    ):
        """
        初始化客户端

        Args:
            api_key: API密钥，如果不提供则从配置读取
            base_url: API基础URL，如果不提供则从配置读取
            default_model: 默认模型，如果不提供则从配置读取
            settings: 配置实例，如果不提供则使用全局配置
        """
        self._settings = settings or get_settings()

        self.api_key = api_key or self._settings.siliconflow_api_key
        self.base_url = base_url or self._settings.siliconflow_base_url
        self.default_model = default_model or self._settings.siliconflow_model

        # 确保base_url不以斜杠结尾
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        # 创建HTTP会话
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
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
        发送HTTP请求（带重试机制）

        Args:
            method: HTTP方法（GET, POST等）
            endpoint: API端点（不包含base_url）
            data: 请求数据
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            API响应数据

        Raises:
            APIError: API调用错误
            NetworkError: 网络错误
            AuthenticationError: 认证错误
            RateLimitError: 速率限制错误
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

                # 检查响应状态码
                if response.status_code == 200:
                    return response.json()

                # 处理错误响应
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"error": {"message": response.text}}

                error_message = error_data.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )

                # 根据状态码分类错误
                if response.status_code == 401:
                    raise AuthenticationError(
                        f"认证失败: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                    )
                elif response.status_code == 429:
                    # 速率限制，可能需要重试
                    if attempt < max_retries:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError(
                        f"速率限制: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                    )
                elif response.status_code >= 500:
                    # 服务器错误，可以重试
                    if attempt < max_retries:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                    raise APIError(
                        f"服务器错误: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                    )
                else:
                    # 其他错误，不重试
                    raise APIError(
                        f"API错误: {error_message}",
                        status_code=response.status_code,
                        response=error_data,
                    )

            except requests.exceptions.RequestException as e:
                # 网络错误，可以重试
                last_error = e
                if attempt < max_retries:
                    wait_time = retry_delay * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                raise NetworkError(
                    f"网络错误: {str(e)}",
                    status_code=None,
                    response=None,
                ) from e

        # 如果所有重试都失败
        if last_error:
            raise NetworkError(
                f"网络错误（重试{max_retries}次后失败）: {str(last_error)}"
            ) from last_error
        raise APIError("请求失败，未知错误")

    def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """
        发送对话请求

        Args:
            messages: 消息列表
            model: 模型名称（可选，默认使用配置中的模型）
            temperature: 生成温度（可选）
            max_tokens: 最大生成Token数（可选）
            **kwargs: 其他参数

        Returns:
            ChatCompletionResponse 响应对象

        Example:
            >>> from llm import SiliconFlowClient, Message
            >>> client = SiliconFlowClient()
            >>> messages = [Message(role="user", content="你好")]
            >>> response = client.chat(messages)
            >>> print(response.content)
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self._settings.temperature
        max_tokens = max_tokens if max_tokens is not None else self._settings.max_tokens

        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        response_data = self._request(
            method="POST",
            endpoint="/chat/completions",
            data=request.to_dict(),
        )

        return ChatCompletionResponse.from_dict(response_data)

    def chat_single(
        self,
        user_message: str,
        system_prompt: str = None,
        model: str = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """
        简单的单轮对话

        Args:
            user_message: 用户消息
            system_prompt: 系统提示（可选）
            model: 模型名称（可选）
            **kwargs: 其他参数

        Returns:
            ChatCompletionResponse 响应对象

        Example:
            >>> response = client.chat_single("你好")
            >>> print(response.content)
        """
        messages = []

        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        messages.append(Message(role="user", content=user_message))

        return self.chat(messages, model=model, **kwargs)

    def chat_stream(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        流式对话（SSE）

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 生成温度
            max_tokens: 最大生成Token数
            **kwargs: 其他参数

        Yields:
            每次返回的内容片段

        Note:
            这是一个简化的流式实现，实际使用时可能需要更完善的SSE解析
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self._settings.temperature
        max_tokens = max_tokens if max_tokens is not None else self._settings.max_tokens

        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        response = self._session.post(
            url,
            json=request.to_dict(),
            headers=headers,
            stream=True,
            timeout=self._settings.request_timeout,
        )

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

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

    def close(self):
        """关闭HTTP会话"""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
