"""
主题系统
提供主题接口和多个主题实现
"""

from tui.themes.base import Theme, Color, ThemeColors
from tui.themes.default import DefaultTheme
from tui.themes.dark import DarkTheme
from tui.themes.light import LightTheme
from tui.themes.registry import ThemeRegistry, get_theme, list_themes, register_theme

__all__ = [
    "Theme",
    "Color",
    "ThemeColors",
    "DefaultTheme",
    "DarkTheme",
    "LightTheme",
    "ThemeRegistry",
    "get_theme",
    "list_themes",
    "register_theme",
]
