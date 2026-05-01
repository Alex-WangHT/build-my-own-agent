"""
AlexClaw TUI 应用入口
使用主题系统和 IO 接口架构

设计理念：
- Agent 只依赖 IO 接口 (AgentIO)
- TUI/Gateway 分别实现 IO 接口
- 运行时可动态切换实现
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from runtime.simple_agent import ReActAgent
from runtime.io.base import (
    ThoughtEvent,
    ActionEvent,
    ObservationEvent,
    FinalAnswerEvent,
    TokenStatsEvent,
    SystemEvent,
    ErrorEvent,
)
from config.settings import get_settings, Settings
from tui.themes.base import Theme, Color
from tui.themes.registry import list_themes, get_theme, ThemeRegistry
from tui.components.splash import SplashScreen
from tui.io.tui_adapter import TUIIO


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TUIApplication:
    """
    TUI 应用主类
    整合 Agent、IO 和主题系统
    """

    def __init__(
        self,
        theme: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        self._settings = settings or get_settings()
        self._theme = get_theme(theme)
        self._tui_io = TUIIO(self._theme)
        self._agent = None
        self._running = False

    @property
    def theme(self) -> Theme:
        return self._theme

    @property
    def agent(self) -> ReActAgent:
        return self._agent

    def _init_agent(self):
        """初始化 Agent"""
        if self._agent is None:
            self._agent = ReActAgent(
                settings=self._settings,
                io=self._tui_io,
            )

    def _switch_theme(self, theme_name: str) -> bool:
        """切换主题"""
        new_theme = get_theme(theme_name)
        if new_theme.name == theme_name or (theme_name and new_theme.name == "default"):
            self._theme = new_theme
            self._tui_io.theme = new_theme
            if self._agent:
                self._agent.io = self._tui_io
            return True
        return False

    def _print_header(self):
        """打印欢迎信息"""
        colors = self._theme.colors
        symbols = self._theme.symbols

        print("=" * 60)
        print(self._theme.style_primary("🤖 AlexClaw AI Agent - ReAct模式", bold=True))
        print("=" * 60)
        print()
        print(f"📦 模型: {self._agent.model if self._agent else self._settings.siliconflow_model}")
        print(f"⏱️  请求超时: {self._settings.request_timeout}秒")
        print(f"🎨 主题: {self._theme.name}")
        print(f"💡 输入消息进行对话，或输入以下命令：")
        print("   /help      - 显示帮助")
        print("   /clear     - 清空对话历史")
        print("   /stats     - 查看对话统计")
        print("   /tools     - 查看可用工具")
        print("   /themes    - 查看可用主题")
        print("   /theme     - 切换主题")
        print("   /models    - 查看可用模型")
        print("   /model     - 切换模型")
        print("   /quit      - 退出程序")
        print()
        print("✨ 提示: 支持实时工具调用和Token统计显示！")
        print("-" * 60)
        print()

    def _print_help(self):
        """打印帮助信息"""
        symbols = self._theme.symbols

        print()
        print(self._theme.style_info("📖 帮助信息："))
        print(self._theme.style_muted("-" * 40))
        print("直接输入消息即可与AI助手对话。")
        print("AI会根据需要自动调用工具来回答问题。")
        print()
        print("可用命令：")
        print("  /help          显示此帮助信息")
        print("  /clear         清空对话历史")
        print("  /stats         查看对话统计信息")
        print("  /tools         查看可用工具列表")
        print("  /themes        查看可用主题列表")
        print("  /theme <名称>  切换到指定主题")
        print("  /models        列出可用的模型")
        print("  /model <名称>  切换到指定模型")
        print("  /quit, /exit   退出程序")
        print()
        print("ReAct模式说明：")
        print(f"  - {self._theme.style_thought('Thought')}: AI的思考过程")
        print(f"  - {self._theme.style_action('Action')}: AI决定调用的工具")
        print(f"  - {self._theme.style_observation('Observation')}: 工具执行结果")
        print(f"  - {self._theme.style_final_answer('Final Answer')}: 最终答案")
        print()

    def _print_tools(self):
        """打印可用工具列表"""
        if not self._agent:
            print(self._theme.style_error("❌ Agent未初始化"))
            return

        tools = self._agent.list_tools()
        import json
        print()
        print(self._theme.style_info("🔧 可用工具："))
        print(self._theme.style_muted("-" * 40))
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {self._theme.style_action(tool['name'])}")
            print(f"     {tool['description']}")
            params = tool.get('parameters', {}).get('properties', {})
            if params:
                print(f"     参数:")
                for param_name, param_info in params.items():
                    required = tool.get('parameters', {}).get('required', [])
                    req_mark = " *" if param_name in required else ""
                    print(f"       - {param_name}{req_mark}: {param_info.get('description', '无描述')}")
            print()

    def _print_themes(self):
        """打印可用主题列表"""
        themes = list_themes()
        print()
        print(self._theme.style_info("🎨 可用主题："))
        print(self._theme.style_muted("-" * 40))
        for i, theme_info in enumerate(themes, 1):
            is_current = theme_info['name'] == self._theme.name
            current_mark = " ← 当前" if is_current else ""
            print(f"  {i}. {self._theme.style_primary(theme_info['name'])}{current_mark}")
            print(f"     {theme_info['description']}")
            print()

    def _print_stats(self):
        """打印统计信息"""
        if not self._agent:
            print(self._theme.style_error("❌ Agent未初始化"))
            return

        summary = self._agent.get_history_summary()
        token_stats = self._agent.get_token_stats()

        print()
        print(self._theme.style_info("📊 对话统计："))
        print(self._theme.style_muted("-" * 40))
        print(f"  消息数量: {summary['message_count']}")
        print(f"  Prompt Tokens: {self._theme.style_token_prompt(str(token_stats.prompt_tokens))}")
        print(f"  Completion Tokens: {self._theme.style_token_completion(str(token_stats.completion_tokens))}")
        print(f"  {self._theme.style_token_total(f'总Token数: {token_stats.total_tokens}')}")
        print(f"  创建时间: {summary['created_at']}")
        print(f"  最后更新: {summary['updated_at']}")
        print(f"  当前模型: {self._agent.model}")
        print()

    def _list_models(self):
        """列出可用模型"""
        if not self._agent:
            print(self._theme.style_error("❌ Agent未初始化"))
            return

        print()
        print(self._theme.style_info("🔍 正在获取模型列表..."))
        try:
            models = self._agent.list_models()
            if models:
                print()
                print(self._theme.style_info("📋 可用模型（前20个）："))
                print(self._theme.style_muted("-" * 40))
                for i, model in enumerate(models[:20], 1):
                    model_id = model.get("id", "未知")
                    print(f"  {i:2d}. {model_id}")
                if len(models) > 20:
                    print(f"  ... 还有 {len(models) - 20} 个模型")
                print()
            else:
                print(self._theme.style_error("❌ 暂无可用模型"))
        except Exception as e:
            print(self._theme.style_error(f"❌ 获取模型列表失败: {e}"))
        print()

    def _switch_model(self, model_name: str):
        """切换模型"""
        if not self._agent:
            print(self._theme.style_error("❌ Agent未初始化"))
            return

        if not model_name:
            print(self._theme.style_error("❌ 请指定模型名称"))
            print("   用法: /model <模型名称>")
            print()
            print("   提示: 输入 /models 查看可用模型列表")
            return

        self._agent.model = model_name
        print(self._theme.style_success(f"✅ 已切换到模型: {model_name}"))
        print()

    def _clear_history(self):
        """清空对话历史"""
        if not self._agent:
            print(self._theme.style_error("❌ Agent未初始化"))
            return

        self._agent.clear_history()
        print(self._theme.style_success("✅ 对话历史已清空"))
        print()

    def _handle_command(self, command: str) -> bool:
        """
        处理命令

        Args:
            command: 命令字符串

        Returns:
            是否应该继续运行（返回False表示退出）
        """
        cmd = command.strip().lower()

        if cmd in ["/quit", "/exit", "/q"]:
            self._running = False
            return False

        elif cmd == "/help" or cmd == "/?":
            self._print_help()

        elif cmd == "/clear":
            self._clear_history()

        elif cmd == "/stats":
            self._print_stats()

        elif cmd == "/tools":
            self._print_tools()

        elif cmd == "/themes":
            self._print_themes()

        elif cmd.startswith("/theme "):
            theme_name = command[len("/theme ") :].strip()
            if self._switch_theme(theme_name):
                print(self._theme.style_success(f"✅ 已切换到主题: {self._theme.name}"))
                print()
            else:
                print(self._theme.style_error(f"❌ 未找到主题: {theme_name}"))
                print("   输入 /themes 查看可用主题列表")
                print()

        elif cmd == "/models":
            self._list_models()

        elif cmd.startswith("/model "):
            model_name = command[len("/model ") :].strip()
            self._switch_model(model_name)

        else:
            print(self._theme.style_error(f"❌ 未知命令: {command}"))
            print("   输入 /help 查看帮助")
            print()

        return True

    def _get_user_input(self) -> str:
        """获取用户输入"""
        symbols = self._theme.symbols
        try:
            input_prompt = self._theme.style_user(f"{symbols.user} 你: ", bold=True)
            user_input = input(input_prompt).strip()
            return user_input
        except KeyboardInterrupt:
            print()
            print(f"\n{self._theme.style_warning('👋 检测到中断，正在退出...')}")
            self._running = False
            return ""
        except EOFError:
            print()
            self._running = False
            return ""

    def _chat(self, user_message: str):
        """
        进行对话（ReAct模式）

        Args:
            user_message: 用户消息
        """
        if not self._agent:
            print(self._theme.style_error("❌ Agent未初始化"))
            return

        start_time = time.time()

        print(f"\n{self._theme.style_warning('🤔 思考中...')}")

        try:
            response = self._agent.chat(user_message)

            elapsed = time.time() - start_time

            # Token 统计由 IO 适配器处理，但我们也可以在这里补充显示耗时
            # 实际的 Token 事件已经在 chat 方法中由 IO 适配器处理了

        except KeyboardInterrupt:
            print()
            print(f"\n{self._theme.style_warning('⚠️ 已中断请求')}")
            print()

        except Exception as e:
            print()
            print(f"\n{self._theme.style_error(f'❌ 错误: {e}')}")
            if self._settings.debug:
                import traceback
                traceback.print_exc()
            print()

    def run(self):
        """运行 TUI 应用"""
        self._init_agent()
        self._running = True
        self._print_header()

        while self._running:
            try:
                user_input = self._get_user_input()

                if not self._running:
                    break

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    self._handle_command(user_input)
                else:
                    self._chat(user_input)

            except KeyboardInterrupt:
                print()
                print(f"\n{self._theme.style_warning('👋 再见！')}")
                self._running = False
            except Exception as e:
                print(f"\n{self._theme.style_error(f'❌ 发生错误: {e}')}")
                if self._settings.debug:
                    import traceback
                    traceback.print_exc()

        if self._agent:
            self._agent.close()

        print()
        print("=" * 60)
        print(self._theme.style_primary("👋 感谢使用 AlexClaw，再见！", bold=True))
        print("=" * 60)
        print()


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

    app = TUIApplication(
        theme=theme,
        settings=settings,
    )

    if agent:
        app._agent = agent
        if IO_AVAILABLE:
            agent.io = app._tui_io

    app.run()


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


try:
    from runtime.io.base import IO_AVAILABLE
except ImportError:
    IO_AVAILABLE = False
