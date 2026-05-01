"""
默认主题
现代化的深色主题
"""

from tui.themes.base import Theme, ThemeColors, ThemeSymbols, Color


class DefaultTheme(Theme):
    """默认主题 - 现代化深色主题"""

    _name: str = "default"
    _description: str = "现代化深色主题，适用于大多数终端"

    def __init__(self):
        self._colors = ThemeColors(
            primary=Color.BRIGHT_CYAN,
            secondary=Color.BLUE,
            success=Color.BRIGHT_GREEN,
            warning=Color.BRIGHT_YELLOW,
            error=Color.BRIGHT_RED,
            info=Color.BRIGHT_MAGENTA,
            muted=Color.DIM,
            text=Color.WHITE,
            border=Color.DIM,
            highlight=Color.BRIGHT_CYAN,
            user=Color.BRIGHT_BLUE,
            assistant=Color.BRIGHT_GREEN,
            thought=Color.DIM,
            action=Color.BRIGHT_CYAN,
            observation=Color.BRIGHT_GREEN,
            final_answer=Color.BRIGHT_YELLOW,
            token_estimate=Color.DIM,
            token_prompt=Color.BLUE,
            token_completion=Color.MAGENTA,
            token_total=Color.BRIGHT_CYAN,
            logo_primary=Color.BRIGHT_CYAN,
            logo_secondary=Color.BLUE,
            logo_accent=Color.BRIGHT_YELLOW,
        )
        self._symbols = ThemeSymbols(
            user="👤",
            assistant="🤖",
            thought="💭",
            action="🔧",
            observation="👁️",
            final_answer="✨",
            success="✅",
            warning="⚠️",
            error="❌",
            info="ℹ️",
            stats="📊",
            clock="⏱️",
            tools="🔧",
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def colors(self) -> ThemeColors:
        return self._colors

    @property
    def symbols(self) -> ThemeSymbols:
        return self._symbols
