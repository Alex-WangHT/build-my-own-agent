"""
主题注册表
管理主题的注册和获取
"""

from typing import Dict, Optional, List, Any

from tui.themes.base import Theme
from tui.themes.default import DefaultTheme
from tui.themes.dark import DarkTheme
from tui.themes.light import LightTheme


class ThemeRegistry:
    """
    主题注册表
    管理所有可用的主题，支持动态注册和切换
    """

    _instance: Optional["ThemeRegistry"] = None
    _themes: Dict[str, Theme] = {}
    _default_theme: str = "default"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance

    def _initialize_defaults(self):
        """初始化默认主题"""
        self._themes = {}
        self.register(DefaultTheme())
        self.register(DarkTheme())
        self.register(LightTheme())

    def register(self, theme: Theme) -> None:
        """
        注册一个主题

        Args:
            theme: 主题实例
        """
        self._themes[theme.name] = theme

    def get(self, name: str) -> Optional[Theme]:
        """
        获取指定名称的主题

        Args:
            name: 主题名称

        Returns:
            主题实例，如果不存在则返回None
        """
        return self._themes.get(name)

    def get_or_default(self, name: Optional[str] = None) -> Theme:
        """
        获取指定主题，如果不存在则返回默认主题

        Args:
            name: 主题名称

        Returns:
            主题实例
        """
        if name and name in self._themes:
            return self._themes[name]
        return self._themes[self._default_theme]

    def list_themes(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的主题

        Returns:
            主题信息列表
        """
        return [theme.to_dict() for theme in self._themes.values()]

    def set_default(self, name: str) -> bool:
        """
        设置默认主题

        Args:
            name: 主题名称

        Returns:
            是否成功设置
        """
        if name in self._themes:
            self._default_theme = name
            return True
        return False

    @property
    def default_theme(self) -> Theme:
        """获取默认主题"""
        return self._themes[self._default_theme]


_registry: Optional[ThemeRegistry] = None


def _get_registry() -> ThemeRegistry:
    """获取全局注册表实例"""
    global _registry
    if _registry is None:
        _registry = ThemeRegistry()
    return _registry


def get_theme(name: Optional[str] = None) -> Theme:
    """
    获取主题的便捷函数

    Args:
        name: 主题名称（可选）

    Returns:
        主题实例
    """
    return _get_registry().get_or_default(name)


def list_themes() -> List[Dict[str, Any]]:
    """
    列出所有可用主题的便捷函数

    Returns:
        主题信息列表
    """
    return _get_registry().list_themes()


def register_theme(theme: Theme) -> None:
    """
    注册主题的便捷函数

    Args:
        theme: 主题实例
    """
    _get_registry().register(theme)
