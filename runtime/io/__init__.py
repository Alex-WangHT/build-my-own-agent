"""
Runtime IO 模块
定义 Agent Runtime 与外部交互的接口和事件类型
"""

from runtime.io.base import (
    AgentIO,
    EventType,
    Event,
    ThoughtEvent,
    ActionEvent,
    ObservationEvent,
    FinalAnswerEvent,
    UserInputEvent,
    TokenStatsEvent,
    SystemEvent,
    ErrorEvent,
)
from runtime.io.adapter import LoggingIO, NoopIO, MultiIO

__all__ = [
    "AgentIO",
    "EventType",
    "Event",
    "ThoughtEvent",
    "ActionEvent",
    "ObservationEvent",
    "FinalAnswerEvent",
    "UserInputEvent",
    "TokenStatsEvent",
    "SystemEvent",
    "ErrorEvent",
    "LoggingIO",
    "NoopIO",
    "MultiIO",
]
