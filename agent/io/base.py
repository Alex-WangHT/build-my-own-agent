"""
Agent IO 基础接口
定义 Agent 与外部交互的抽象接口
参考 ZeroClaw 的 trait 驱动架构设计
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List


class EventType(Enum):
    """事件类型枚举"""

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"
    USER_INPUT = "user_input"
    TOKEN_STATS = "token_stats"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class Event:
    """事件基类"""

    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ThoughtEvent(Event):
    """思考内容事件"""

    content: str = ""

    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            event_type=EventType.THOUGHT,
            metadata=metadata or {},
        )
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["content"] = self.content
        return data


@dataclass
class ActionEvent(Event):
    """工具调用事件"""

    action: str = ""
    action_input: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        action: str,
        action_input: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=EventType.ACTION,
            metadata=metadata or {},
        )
        self.action = action
        self.action_input = action_input

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["action"] = self.action
        data["action_input"] = self.action_input
        return data


@dataclass
class ObservationEvent(Event):
    """工具执行结果事件"""

    action: str = ""
    observation: str = ""

    def __init__(
        self,
        action: str,
        observation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=EventType.OBSERVATION,
            metadata=metadata or {},
        )
        self.action = action
        self.observation = observation

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["action"] = self.action
        data["observation"] = self.observation
        return data


@dataclass
class FinalAnswerEvent(Event):
    """最终答案事件"""

    answer: str = ""

    def __init__(self, answer: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            event_type=EventType.FINAL_ANSWER,
            metadata=metadata or {},
        )
        self.answer = answer

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["answer"] = self.answer
        return data


@dataclass
class UserInputEvent(Event):
    """用户输入事件"""

    input_text: str = ""

    def __init__(self, input_text: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            event_type=EventType.USER_INPUT,
            metadata=metadata or {},
        )
        self.input_text = input_text

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["input_text"] = self.input_text
        return data


@dataclass
class TokenStatsEvent(Event):
    """Token 统计事件"""

    estimated_context: int = 0
    round_prompt: int = 0
    round_completion: int = 0
    round_total: int = 0
    total_prompt: int = 0
    total_completion: int = 0
    total_tokens: int = 0
    elapsed_seconds: float = 0.0

    def __init__(
        self,
        estimated_context: int = 0,
        round_prompt: int = 0,
        round_completion: int = 0,
        round_total: int = 0,
        total_prompt: int = 0,
        total_completion: int = 0,
        total_tokens: int = 0,
        elapsed_seconds: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=EventType.TOKEN_STATS,
            metadata=metadata or {},
        )
        self.estimated_context = estimated_context
        self.round_prompt = round_prompt
        self.round_completion = round_completion
        self.round_total = round_total
        self.total_prompt = total_prompt
        self.total_completion = total_completion
        self.total_tokens = total_tokens
        self.elapsed_seconds = elapsed_seconds

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "estimated_context": self.estimated_context,
                "round_prompt": self.round_prompt,
                "round_completion": self.round_completion,
                "round_total": self.round_total,
                "total_prompt": self.total_prompt,
                "total_completion": self.total_completion,
                "total_tokens": self.total_tokens,
                "elapsed_seconds": self.elapsed_seconds,
            }
        )
        return data


@dataclass
class SystemEvent(Event):
    """系统消息事件"""

    message: str = ""
    level: str = "info"

    def __init__(
        self,
        message: str,
        level: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=EventType.SYSTEM,
            metadata=metadata or {},
        )
        self.message = message
        self.level = level

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["message"] = self.message
        data["level"] = self.level
        return data


@dataclass
class ErrorEvent(Event):
    """错误事件"""

    error_message: str = ""
    error_type: str = ""
    details: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        error_message: str,
        error_type: str = "general",
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=EventType.ERROR,
            metadata=metadata or {},
        )
        self.error_message = error_message
        self.error_type = error_type
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["error_message"] = self.error_message
        data["error_type"] = self.error_type
        if self.details:
            data["details"] = self.details
        return data


class AgentIO(ABC):
    """
    Agent IO 接口
    定义 Agent 与外部交互的抽象契约

    参考 ZeroClaw 的 trait 驱动架构：
    - Agent 只依赖此接口，不依赖具体实现
    - TUI、Gateway 等分别实现此接口
    - 运行时可动态切换实现
    """

    @abstractmethod
    def on_thought(self, event: ThoughtEvent) -> None:
        """
        处理思考内容

        Args:
            event: 思考事件
        """
        pass

    @abstractmethod
    def on_action(self, event: ActionEvent) -> None:
        """
        处理工具调用

        Args:
            event: 动作事件
        """
        pass

    @abstractmethod
    def on_observation(self, event: ObservationEvent) -> None:
        """
        处理工具执行结果

        Args:
            event: 观察事件
        """
        pass

    @abstractmethod
    def on_final_answer(self, event: FinalAnswerEvent) -> None:
        """
        处理最终答案

        Args:
            event: 最终答案事件
        """
        pass

    @abstractmethod
    def on_token_stats(self, event: TokenStatsEvent) -> None:
        """
        处理 Token 统计

        Args:
            event: Token 统计事件
        """
        pass

    @abstractmethod
    def on_system(self, event: SystemEvent) -> None:
        """
        处理系统消息

        Args:
            event: 系统事件
        """
        pass

    @abstractmethod
    def on_error(self, event: ErrorEvent) -> None:
        """
        处理错误

        Args:
            event: 错误事件
        """
        pass

    @abstractmethod
    def get_user_input(self, prompt: str = "") -> str:
        """
        获取用户输入

        Args:
            prompt: 提示文本

        Returns:
            用户输入的文本
        """
        pass

    def on_event(self, event: Event) -> None:
        """
        通用事件处理方法

        根据事件类型分发到对应的处理方法

        Args:
            event: 事件对象
        """
        if isinstance(event, ThoughtEvent):
            self.on_thought(event)
        elif isinstance(event, ActionEvent):
            self.on_action(event)
        elif isinstance(event, ObservationEvent):
            self.on_observation(event)
        elif isinstance(event, FinalAnswerEvent):
            self.on_final_answer(event)
        elif isinstance(event, TokenStatsEvent):
            self.on_token_stats(event)
        elif isinstance(event, SystemEvent):
            self.on_system(event)
        elif isinstance(event, ErrorEvent):
            self.on_error(event)
