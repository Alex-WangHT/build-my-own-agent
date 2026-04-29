"""
简单对话Agent
实现基本的对话功能，包括上下文管理和错误处理
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Iterator

from config.settings import Settings, get_settings
from llm.client import (
    SiliconFlowClient,
    Message,
    ChatCompletionResponse,
    APIError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """对话历史管理"""

    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_tokens: int = 0

    def add_message(self, role: str, content: str, name: str = None):
        """添加消息"""
        message = Message(role=role, content=content, name=name)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("assistant", content)

    def add_system_message(self, content: str):
        """添加系统消息"""
        self.add_message("system", content)

    def clear(self):
        """清空对话历史"""
        self.messages = []
        self.total_tokens = 0

    def get_recent_messages(self, max_count: int = None) -> List[Message]:
        """获取最近的消息"""
        if max_count is None or len(self.messages) <= max_count:
            return self.messages.copy()
        return self.messages[-max_count:].copy()

    def truncate_by_tokens(self, max_tokens: int, approx_tokens_per_char: float = 0.5) -> List[Message]:
        """
        按Token数截断消息历史（近似估计）

        Args:
            max_tokens: 最大Token数
            approx_tokens_per_char: 每个字符大约的Token数

        Returns:
            截断后的消息列表
        """
        if not self.messages:
            return []

        # 从最新消息开始累加
        result = []
        total_chars = 0

        # 总是保留系统消息（如果有）
        system_messages = [m for m in self.messages if m.role == "system"]
        non_system_messages = [m for m in self.messages if m.role != "system"]

        # 先添加系统消息
        result.extend(system_messages)
        for msg in system_messages:
            total_chars += len(msg.content)

        # 从后往前添加非系统消息
        for msg in reversed(non_system_messages):
            msg_chars = len(msg.content)
            estimated_tokens = (total_chars + msg_chars) * approx_tokens_per_char

            if estimated_tokens > max_tokens and result:
                break

            result.insert(len(system_messages), msg)
            total_chars += msg_chars

        return result

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """从字典创建"""
        messages_data = data.get("messages", [])
        messages = [Message.from_dict(m) for m in messages_data]

        created_at = data.get("created_at")
        if created_at:
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()

        updated_at = data.get("updated_at")
        if updated_at:
            updated_at = datetime.fromisoformat(updated_at)
        else:
            updated_at = datetime.now()

        return cls(
            messages=messages,
            created_at=created_at,
            updated_at=updated_at,
            total_tokens=data.get("total_tokens", 0),
        )


class SimpleAgent:
    """简单对话Agent"""

    def __init__(
        self,
        system_prompt: str = None,
        model: str = None,
        settings: Settings = None,
    ):
        """
        初始化Agent

        Args:
            system_prompt: 系统提示词
            model: 使用的模型
            settings: 配置实例
        """
        self._settings = settings or get_settings()
        self._model = model or self._settings.siliconflow_model
        self._system_prompt = system_prompt

        # 初始化LLM客户端
        self._client = SiliconFlowClient(settings=self._settings)

        # 初始化对话历史
        self._conversation = Conversation()

        # 如果有系统提示词，添加到对话历史
        if self._system_prompt:
            self._conversation.add_system_message(self._system_prompt)

        logger.info(f"SimpleAgent initialized with model: {self._model}")

    @property
    def conversation(self) -> Conversation:
        """获取对话历史"""
        return self._conversation

    @property
    def model(self) -> str:
        """获取当前模型"""
        return self._model

    @model.setter
    def model(self, value: str):
        """设置模型"""
        self._model = value
        logger.info(f"Model changed to: {value}")

    def _prepare_messages(self, user_message: str) -> List[Message]:
        """
        准备发送给LLM的消息

        Args:
            user_message: 用户输入的消息

        Returns:
            消息列表
        """
        # 添加用户消息到对话历史
        self._conversation.add_user_message(user_message)

        # 获取截断后的消息（防止上下文过长）
        messages = self._conversation.truncate_by_tokens(
            max_tokens=self._settings.max_history_tokens
        )

        return messages

    def chat(
        self,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> str:
        """
        发送消息并获取回复

        Args:
            user_message: 用户消息
            temperature: 生成温度
            max_tokens: 最大生成Token数
            **kwargs: 其他参数

        Returns:
            助手的回复内容

        Raises:
            APIError: API调用错误
            NetworkError: 网络错误
            AuthenticationError: 认证错误
            RateLimitError: 速率限制错误
        """
        logger.debug(f"User message: {user_message[:100]}...")

        try:
            # 准备消息
            messages = self._prepare_messages(user_message)

            # 调用LLM
            response = self._client.chat(
                messages=messages,
                model=self._model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # 获取回复内容
            assistant_message = response.content

            # 添加到对话历史
            self._conversation.add_assistant_message(assistant_message)

            # 更新Token计数
            self._conversation.total_tokens += response.usage.total_tokens

            logger.debug(f"Assistant response: {assistant_message[:100]}...")
            logger.info(f"Tokens used: {response.usage.total_tokens}")

            return assistant_message

        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            raise
        except RateLimitError as e:
            logger.warning(f"Rate limit error: {e}")
            raise
        except NetworkError as e:
            logger.error(f"Network error: {e}")
            raise
        except APIError as e:
            logger.error(f"API error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in chat: {e}")
            raise

    def chat_stream(
        self,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        流式对话（逐字返回）

        Args:
            user_message: 用户消息
            temperature: 生成温度
            max_tokens: 最大生成Token数
            **kwargs: 其他参数

        Yields:
            每次返回的内容片段
        """
        logger.debug(f"User message (stream): {user_message[:100]}...")

        try:
            # 准备消息
            messages = self._prepare_messages(user_message)

            # 流式调用
            full_content = ""
            for chunk in self._client.chat_stream(
                messages=messages,
                model=self._model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                full_content += chunk
                yield chunk

            # 添加完整内容到对话历史
            self._conversation.add_assistant_message(full_content)

            logger.debug(f"Assistant response (stream): {full_content[:100]}...")

        except Exception as e:
            logger.exception(f"Error in chat_stream: {e}")
            raise

    def chat_single(
        self,
        user_message: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> str:
        """
        单次对话（不影响对话历史）

        Args:
            user_message: 用户消息
            system_prompt: 系统提示词（可选）
            temperature: 生成温度
            max_tokens: 最大生成Token数
            **kwargs: 其他参数

        Returns:
            助手的回复内容
        """
        logger.debug(f"Single chat message: {user_message[:100]}...")

        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=user_message))

        response = self._client.chat(
            messages=messages,
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        logger.debug(f"Single chat response: {response.content[:100]}...")

        return response.content

    def clear_history(self):
        """清空对话历史"""
        self._conversation.clear()
        logger.info("Conversation history cleared")

        # 重新添加系统提示词
        if self._system_prompt:
            self._conversation.add_system_message(self._system_prompt)

    def get_history_summary(self) -> Dict[str, Any]:
        """获取对话历史摘要"""
        return {
            "message_count": len(self._conversation.messages),
            "total_tokens": self._conversation.total_tokens,
            "created_at": self._conversation.created_at.isoformat(),
            "updated_at": self._conversation.updated_at.isoformat(),
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表

        Returns:
            模型列表
        """
        return self._client.list_models()

    def close(self):
        """关闭资源"""
        self._client.close()
        logger.info("Agent closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
