"""
AlexClaw TUI 应用入口
使用主题系统和组件架构
"""

import sys
from pathlib import Path
from typing import Optional

from agent.simple_agent import ReActAgent
from config.settings import get_settings, Settings
from tui.themes.base import Theme
from tui.themes.registry import get_theme
from tui.components.splash import SplashScreen
from tui.components.chat import ChatInterface


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_cli(
    agent: Optional[ReActAgent] = None,
    settings: Optional[Settings] = None,
    theme: Optional[str] = None,
    show_splash: bool = True,
    splash_animate: bool = True,
    splash_duration: float = 2.0,
) -> None:
    """
    运行AlexClaw命令行界面

    Args:
        agent: 可选的Agent实例
        settings: 可选的配置实例
        theme: 主题名称（可选）
        show_splash: 是否显示启动界面
        splash_animate: 启动界面是否使用动画
        splash_duration: 启动动画持续时间（秒）
    """
    settings = settings or get_settings()

    current_theme = get_theme(theme)

    if show_splash:
        splash = SplashScreen(current_theme)
        splash.show(
            animate=splash_animate,
            clear_screen=True,
            show_loading=True,
            loading_duration=splash_duration,
        )

    chat_interface = ChatInterface(
        theme=current_theme,
        agent=agent,
        settings=settings,
    )

    chat_interface.run()


def run_with_splash(
    theme: Optional[str] = None,
    splash_duration: float = 2.0,
) -> None:
    """
    运行带有启动界面的CLI

    Args:
        theme: 主题名称
        splash_duration: 启动动画持续时间
    """
    run_cli(
        theme=theme,
        show_splash=True,
        splash_animate=True,
        splash_duration=splash_duration,
    )


def run_simple(
    theme: Optional[str] = None,
) -> None:
    """
    运行简化版CLI（无启动界面）

    Args:
        theme: 主题名称
    """
    run_cli(
        theme=theme,
        show_splash=False,
    )
