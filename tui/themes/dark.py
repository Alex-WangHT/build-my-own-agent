"""
暗色主题
高对比度的深色主题
"""

from tui.themes.base import Theme, ThemeColors, ThemeSymbols, Color


class DarkTheme(Theme):
    """暗色主题 - 高对比度深色主题"""

    _name: str = "dark"
    _description: str = "高对比度暗色主题，适合低光环境"

    def __init__(self):
        self._colors = ThemeColors(
            primary=Color.BRIGHT_WHITE,
            secondary=Color.BRIGHT_BLUE,
            success=Color.BRIGHT_GREEN,
            warning=Color.BRIGHT_YELLOW,
            error=Color.BRIGHT_RED,
            info=Color.BRIGHT_MAGENTA,
            muted=Color.BRIGHT_BLACK,
            text=Color.WHITE,
            border=Color.BRIGHT_BLACK,
            highlight=Color.BRIGHT_WHITE,
            user=Color.BRIGHT_BLUE,
            assistant=Color.BRIGHT_GREEN,
            thought=Color.BRIGHT_BLACK,
            action=Color.BRIGHT_CYAN,
            observation=Color.BRIGHT_GREEN,
            final_answer=Color.BRIGHT_YELLOW,
            token_estimate=Color.BRIGHT_BLACK,
            token_prompt=Color.BRIGHT_BLUE,
            token_completion=Color.BRIGHT_MAGENTA,
            token_total=Color.BRIGHT_WHITE,
            logo_primary=Color.BRIGHT_WHITE,
            logo_secondary=Color.BRIGHT_BLUE,
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
