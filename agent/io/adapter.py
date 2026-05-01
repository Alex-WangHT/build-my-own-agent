"""
内置 IO 适配器
提供默认的 IO 实现
"""

import logging
from typing import Optional

from agent.io.base import (
    AgentIO,
    ThoughtEvent,
    ActionEvent,
    ObservationEvent,
    FinalAnswerEvent,
    TokenStatsEvent,
    SystemEvent,
    ErrorEvent,
)


class NoopIO(AgentIO):
    """
    空操作 IO 适配器
    所有方法都不执行任何操作，用于不需要交互的场景
    """

    def on_thought(self, event: ThoughtEvent) -> None:
        pass

    def on_action(self, event: ActionEvent) -> None:
        pass

    def on_observation(self, event: ObservationEvent) -> None:
        pass

    def on_final_answer(self, event: FinalAnswerEvent) -> None:
        pass

    def on_token_stats(self, event: TokenStatsEvent) -> None:
        pass

    def on_system(self, event: SystemEvent) -> None:
        pass

    def on_error(self, event: ErrorEvent) -> None:
        pass

    def get_user_input(self, prompt: str = "") -> str:
        return ""


class LoggingIO(AgentIO):
    """
    日志 IO 适配器
    将所有事件记录到日志，不进行实际交互
    """

    def __init__(self, logger_name: str = "agent.io"):
        self._logger = logging.getLogger(logger_name)

    def on_thought(self, event: ThoughtEvent) -> None:
        self._logger.debug(f"[Thought] {event.content[:100] if len(event.content) > 100 else event.content}")

    def on_action(self, event: ActionEvent) -> None:
        self._logger.info(f"[Action] {event.action}")
        self._logger.debug(f"[Action Input] {event.action_input}")

    def on_observation(self, event: ObservationEvent) -> None:
        self._logger.info(f"[Observation] {event.action}")
        self._logger.debug(f"[Observation Content] {event.observation[:200] if len(event.observation) > 200 else event.observation}")

    def on_final_answer(self, event: FinalAnswerEvent) -> None:
        self._logger.info(f"[Final Answer] {event.answer[:100] if len(event.answer) > 100 else event.answer}")

    def on_token_stats(self, event: TokenStatsEvent) -> None:
        self._logger.info(
            f"[Token Stats] Round: {event.round_total} (P:{event.round_prompt}/C:{event.round_completion}), "
            f"Total: {event.total_tokens}, Elapsed: {event.elapsed_seconds:.2f}s"
        )

    def on_system(self, event: SystemEvent) -> None:
        level_map = {
            "debug": self._logger.debug,
            "info": self._logger.info,
            "warning": self._logger.warning,
            "error": self._logger.error,
        }
        log_func = level_map.get(event.level, self._logger.info)
        log_func(f"[System] {event.message}")

    def on_error(self, event: ErrorEvent) -> None:
        self._logger.error(f"[Error] [{event.error_type}] {event.error_message}")
        if event.details:
            self._logger.debug(f"[Error Details] {event.details}")

    def get_user_input(self, prompt: str = "") -> str:
        self._logger.warning(f"[User Input] LoggingIO cannot get user input, prompt: {prompt}")
        return ""


class MultiIO(AgentIO):
    """
    多 IO 适配器
    同时将事件分发给多个 IO 适配器

    示例:
        io = MultiIO([
            TUIIO(theme),
            LoggingIO(),
        ])
    """

    def __init__(self, io_handlers: list[AgentIO]):
        self._handlers = io_handlers

    def on_thought(self, event: ThoughtEvent) -> None:
        for handler in self._handlers:
            handler.on_thought(event)

    def on_action(self, event: ActionEvent) -> None:
        for handler in self._handlers:
            handler.on_action(event)

    def on_observation(self, event: ObservationEvent) -> None:
        for handler in self._handlers:
            handler.on_observation(event)

    def on_final_answer(self, event: FinalAnswerEvent) -> None:
        for handler in self._handlers:
            handler.on_final_answer(event)

    def on_token_stats(self, event: TokenStatsEvent) -> None:
        for handler in self._handlers:
            handler.on_token_stats(event)

    def on_system(self, event: SystemEvent) -> None:
        for handler in self._handlers:
            handler.on_system(event)

    def on_error(self, event: ErrorEvent) -> None:
        for handler in self._handlers:
            handler.on_error(event)

    def get_user_input(self, prompt: str = "") -> str:
        for handler in self._handlers:
            result = handler.get_user_input(prompt)
            if result:
                return result
        return ""

    def add_handler(self, handler: AgentIO) -> None:
        """添加 IO 处理器"""
        self._handlers.append(handler)

    def remove_handler(self, handler: AgentIO) -> None:
        """移除 IO 处理器"""
        if handler in self._handlers:
            self._handlers.remove(handler)
