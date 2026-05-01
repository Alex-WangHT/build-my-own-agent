"""
启动界面
显示AlexClaw Logo和启动动画
"""

import sys
import time
from typing import Optional

from tui.themes.base import Theme, Color


class SplashScreen:
    """
    启动界面
    显示AlexClaw ASCII艺术Logo和启动动画
    """

    ALEXCLAW_LOGO = [
        "         _    _           _____ _                    ",
        "        / \\  | | _____  _| ____| | _____      __    ",
        "       / _ \\ | |/ _ \\ \\/ /  _| | |/ _ \\\\ \\ /\\ / /    ",
        "      / ___ \\| |  __/>  <| |___| | (_) \\\\ V  V /     ",
        "     /_/   \\_\\_|\\___/_/\\_\\_____|_|\\___/ \\_/\\_/      ",
        "                                                     ",
        "     ─────────────────────────────────────────────   ",
        "              AI Agent Powered by ReAct             ",
        "     ─────────────────────────────────────────────   ",
    ]

    def __init__(self, theme: Theme):
        self._theme = theme

    def _get_terminal_width(self) -> int:
        """获取终端宽度"""
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except Exception:
            return 80

    def _center_text(self, text: str, width: Optional[int] = None) -> str:
        """居中文本"""
        if width is None:
            width = self._get_terminal_width()
        return text.center(width)

    def _clear_screen(self):
        """清屏"""
        print("\033[H\033[J", end="", flush=True)

    def _print_logo_line_by_line(self, delay: float = 0.03):
        """逐行显示Logo动画"""
        colors = self._theme.colors
        width = self._get_terminal_width()

        for i, line in enumerate(self.ALEXCLAW_LOGO):
            if i < 5:
                colored_line = f"{colors.logo_primary}{line}{Color.RESET}"
            elif i == 5:
                colored_line = line
            elif i in [6, 8]:
                colored_line = f"{colors.logo_secondary}{line}{Color.RESET}"
            else:
                colored_line = f"{colors.logo_accent}{line}{Color.RESET}"

            centered = self._center_text(colored_line, width)
            print(centered)
            sys.stdout.flush()
            time.sleep(delay)

    def _print_loading_animation(self, duration: float = 2.0):
        """显示加载动画"""
        colors = self._theme.colors
        width = self._get_terminal_width()
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        messages = [
            "初始化AI引擎...",
            "加载工具系统...",
            "准备对话系统...",
            "启动完成!",
        ]

        frame_index = 0
        message_index = 0
        start_time = time.time()
        frame_duration = 0.1
        message_change_interval = duration / len(messages)
        last_message_change = start_time

        while time.time() - start_time < duration:
            current_time = time.time()

            if current_time - last_message_change > message_change_interval:
                message_index = min(message_index + 1, len(messages) - 1)
                last_message_change = current_time

            frame = frames[frame_index % len(frames)]
            message = messages[message_index]

            loading_text = f"{frame} {message}"
            colored_text = f"{colors.primary}{loading_text}{Color.RESET}"
            centered = self._center_text(colored_text, width)

            print(f"\r{centered}", end="", flush=True)

            frame_index += 1
            time.sleep(frame_duration)

        print()

    def _print_version_info(self):
        """显示版本信息"""
        import platform

        colors = self._theme.colors
        width = self._get_terminal_width()

        python_version = platform.python_version()

        info_lines = [
            f"Python {python_version} | ReAct Agent System",
            "",
            f"{Color.BOLD}输入 /help 查看可用命令{Color.RESET}",
            f"{Color.DIM}按 Ctrl+C 或输入 /quit 退出{Color.RESET}",
        ]

        for line in info_lines:
            centered = self._center_text(line, width)
            print(centered)

    def show(
        self,
        animate: bool = True,
        clear_screen: bool = True,
        show_loading: bool = True,
        loading_duration: float = 2.0,
    ):
        """
        显示启动界面

        Args:
            animate: 是否使用动画效果
            clear_screen: 是否清屏
            show_loading: 是否显示加载动画
            loading_duration: 加载动画持续时间（秒）
        """
        if clear_screen:
            self._clear_screen()

        print()
        print()

        if animate:
            self._print_logo_line_by_line(delay=0.03)
        else:
            width = self._get_terminal_width()
            colors = self._theme.colors
            for i, line in enumerate(self.ALEXCLAW_LOGO):
                if i < 5:
                    colored_line = f"{colors.logo_primary}{line}{Color.RESET}"
                elif i == 5:
                    colored_line = line
                elif i in [6, 8]:
                    colored_line = f"{colors.logo_secondary}{line}{Color.RESET}"
                else:
                    colored_line = f"{colors.logo_accent}{line}{Color.RESET}"
                print(self._center_text(colored_line, width))

        print()

        if show_loading and animate:
            self._print_loading_animation(duration=loading_duration)
            print()

        self._print_version_info()

        print()
        print()
        print("=" * self._get_terminal_width())
        print()
