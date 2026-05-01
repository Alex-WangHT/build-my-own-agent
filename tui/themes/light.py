"""
亮色主题
适用于亮色终端背景
"""

from tui.themes.base import Theme, ThemeColors, ThemeSymbols, Color


class LightTheme(Theme):
    """亮色主题 - 适用于亮色终端背景"""

    _name: str = "light"
    _description: str = "亮色主题，适用于浅色终端背景"

    def __init__(self):
        self._colors = ThemeColors(
            primary=Color.BLUE,
            secondary=Color.CYAN,
            success=Color.GREEN,
            warning=Color.YELLOW,
            error=Color.RED,
            info=Color.MAGENTA,
            muted=Color.DIM,
            text=Color.BLACK,
            border=Color.DIM,
            highlight=Color.BLUE,
            user=Color.BLUE,
            assistant=Color.GREEN,
            thought=Color.DIM,
            action=Color.CYAN,
            observation=Color.GREEN,
            final_answer=Color.YELLOW,
            token_estimate=Color.DIM,
            token_prompt=Color.BLUE,
            token_completion=Color.MAGENTA,
            token_total=Color.CYAN,
            logo_primary=Color.BLUE,
            logo_secondary=Color.CYAN,
            logo_accent=Color.YELLOW,
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
