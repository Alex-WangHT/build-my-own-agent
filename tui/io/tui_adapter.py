"""
TUI IO 适配器
实现 AgentIO 接口，用于与命令行界面交互
"""

import json
from typing import Optional

from tui.themes.base import Theme, Color
from tui.themes.registry import get_theme
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


class TUIIO(AgentIO):
    """
    TUI IO 适配器
    使用主题系统渲染事件到命令行界面
    """

    def __init__(self, theme: Optional[Theme] = None):
        self._theme = theme or get_theme()

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, value: Theme):
        self._theme = value

    def on_thought(self, event: ThoughtEvent) -> None:
        symbols = self._theme.symbols
        print(f"\n{self._theme.style_thought(f'{symbols.thought} Thought:')}")
        for line in event.content.split('\n'):
            if line.strip():
                print(f"   {self._theme.style_thought(line)}")

    def on_action(self, event: ActionEvent) -> None:
        symbols = self._theme.symbols
        print(f"\n{self._theme.style_action(f'{symbols.action} Action: ', bold=True)}{self._theme.style_action(event.action, bold=True)}")
        print(f"   {self._theme.style_action('Input: ')}{json.dumps(event.action_input, ensure_ascii=False, indent=2)}")
        print(f"   {self._theme.style_warning('正在执行工具...')}")

    def on_observation(self, event: ObservationEvent) -> None:
        symbols = self._theme.symbols
        print(f"\n{self._theme.style_observation(f'{symbols.observation} Observation ({event.action}):')}")
        for line in event.observation.split('\n'):
            if line.strip():
                print(f"   {self._theme.style_observation(line)}")

    def on_final_answer(self, event: FinalAnswerEvent) -> None:
        symbols = self._theme.symbols
        print(f"\n{self._theme.style_final_answer(f'{symbols.final_answer} Final Answer:')}")
        for line in event.answer.split('\n'):
            print(f"   {self._theme.style_final_answer(line)}")

    def on_token_stats(self, event: TokenStatsEvent) -> None:
        symbols = self._theme.symbols

        print()
        print(self._theme.style_muted("=" * 60))
        print(self._theme.style_info(f"{symbols.stats} Token统计（本轮对话）:"))
        print(self._theme.style_muted("-" * 40))
        print(f"   {self._theme.style_token_estimate(f'上下文估计: {event.estimated_context} tokens')}")
        print(f"   {self._theme.style_info('本轮消耗:')}")
        print(f"      {self._theme.style_token_prompt(f'Prompt: {event.round_prompt} tokens')}")
        print(f"      {self._theme.style_token_completion(f'Completion: {event.round_completion} tokens')}")
        print(f"      {self._theme.style_token_total(f'Total: {event.round_total} tokens')}")
        print()
        print(self._theme.style_info(f"{symbols.stats} 累计统计:"))
        print(self._theme.style_muted("-" * 40))
        print(f"   累计 Prompt: {event.total_prompt} tokens")
        print(f"   累计 Completion: {event.total_completion} tokens")
        print(f"   {self._theme.style_token_total(f'累计 Total: {event.total_tokens} tokens')}")
        print()
        print(f"{symbols.clock} 本轮耗时: {event.elapsed_seconds:.2f}秒")
        print(self._theme.style_muted("=" * 60))
        print()

    def on_system(self, event: SystemEvent) -> None:
        symbols = self._theme.symbols

        style_map = {
            "debug": self._theme.style_muted,
            "info": self._theme.style_info,
            "warning": self._theme.style_warning,
            "error": self._theme.style_error,
        }
        style_func = style_map.get(event.level, self._theme.style_info)

        symbol_map = {
            "debug": "🔍",
            "info": symbols.info,
            "warning": symbols.warning,
            "error": symbols.error,
        }
        symbol = symbol_map.get(event.level, symbols.info)

        print(f"\n{style_func(f'{symbol} {event.message}')}")

    def on_error(self, event: ErrorEvent) -> None:
        symbols = self._theme.symbols
        print(f"\n{self._theme.style_error(f'{symbols.error} [{event.error_type}] {event.error_message}')}")
        if event.details:
            import traceback
            if "traceback" in event.details:
                print(f"\n{self._theme.style_muted(event.details['traceback'])}")

    def get_user_input(self, prompt: str = "") -> str:
        symbols = self._theme.symbols
        try:
            if prompt:
                input_prompt = self._theme.style_user(f"{symbols.user} {prompt}", bold=True)
            else:
                input_prompt = self._theme.style_user(f"{symbols.user} 你: ", bold=True)
            user_input = input(input_prompt).strip()
            return user_input
        except KeyboardInterrupt:
            print()
            print(f"\n{self._theme.style_warning('👋 检测到中断，正在退出...')}")
            return ""
        except EOFError:
            print()
            return ""
