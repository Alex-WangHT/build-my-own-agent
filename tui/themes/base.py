"""
主题基类
定义主题接口和颜色类型
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class Color:
    """终端颜色常量"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"


@dataclass
class ThemeColors:
    """主题颜色配置"""

    primary: str = field(default=Color.CYAN)
    secondary: str = field(default=Color.BLUE)
    success: str = field(default=Color.GREEN)
    warning: str = field(default=Color.YELLOW)
    error: str = field(default=Color.RED)
    info: str = field(default=Color.MAGENTA)
    muted: str = field(default=Color.DIM)
    text: str = field(default=Color.WHITE)
    border: str = field(default=Color.DIM)
    highlight: str = field(default=Color.BRIGHT_CYAN)

    user: str = field(default=Color.BRIGHT_BLUE)
    assistant: str = field(default=Color.BRIGHT_GREEN)
    thought: str = field(default=Color.DIM)
    action: str = field(default=Color.BRIGHT_CYAN)
    observation: str = field(default=Color.BRIGHT_GREEN)
    final_answer: str = field(default=Color.BRIGHT_YELLOW)

    token_estimate: str = field(default=Color.DIM)
    token_prompt: str = field(default=Color.BLUE)
    token_completion: str = field(default=Color.MAGENTA)
    token_total: str = field(default=Color.BRIGHT_CYAN)

    logo_primary: str = field(default=Color.BRIGHT_CYAN)
    logo_secondary: str = field(default=Color.BLUE)
    logo_accent: str = field(default=Color.BRIGHT_YELLOW)


@dataclass
class ThemeSymbols:
    """主题符号配置"""

    user: str = "👤"
    assistant: str = "🤖"
    thought: str = "💭"
    action: str = "🔧"
    observation: str = "👁️"
    final_answer: str = "✨"
    success: str = "✅"
    warning: str = "⚠️"
    error: str = "❌"
    info: str = "ℹ️"
    stats: str = "📊"
    clock: str = "⏱️"
    tools: str = "🔧"


class Theme(ABC):
    """
    主题接口
    所有主题都必须实现这些方法
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """主题名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """主题描述"""
        pass

    @property
    @abstractmethod
    def colors(self) -> ThemeColors:
        """主题颜色配置"""
        pass

    @property
    @abstractmethod
    def symbols(self) -> ThemeSymbols:
        """主题符号配置"""
        pass

    def style(self, text: str, color: str, bold: bool = False) -> str:
        """
        给文本应用样式

        Args:
            text: 要格式化的文本
            color: 颜色代码
            bold: 是否加粗

        Returns:
            格式化后的文本
        """
        result = color
        if bold:
            result += Color.BOLD
        return f"{result}{text}{Color.RESET}"

    def style_primary(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.primary, bold)

    def style_secondary(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.secondary, bold)

    def style_success(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.success, bold)

    def style_warning(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.warning, bold)

    def style_error(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.error, bold)

    def style_info(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.info, bold)

    def style_muted(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.muted, bold)

    def style_user(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.user, bold)

    def style_assistant(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.assistant, bold)

    def style_thought(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.thought, bold)

    def style_action(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.action, bold)

    def style_observation(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.observation, bold)

    def style_final_answer(self, text: str, bold: bool = True) -> str:
        return self.style(text, self.colors.final_answer, bold)

    def style_token_estimate(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.token_estimate, bold)

    def style_token_prompt(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.token_prompt, bold)

    def style_token_completion(self, text: str, bold: bool = False) -> str:
        return self.style(text, self.colors.token_completion, bold)

    def style_token_total(self, text: str, bold: bool = True) -> str:
        return self.style(text, self.colors.token_total, bold)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
        }
