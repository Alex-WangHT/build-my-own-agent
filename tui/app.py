"""
终端用户界面（TUI）
使用Textual库构建交互式对话界面
"""

import logging
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Static,
    Input,
    Button,
    Label,
    RichLog,
)
from textual.containers import (
    Container,
    Vertical,
    Horizontal,
    VerticalScroll,
)
from textual.reactive import reactive

from agent.simple_agent import SimpleAgent
from config.settings import get_settings, Settings

logger = logging.getLogger(__name__)


class MessageBubble(Static):
    """消息气泡组件"""

    def __init__(
        self,
        content: str,
        is_user: bool,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()

    def compose(self) -> ComposeResult:
        time_str = self.timestamp.strftime("%H:%M:%S")
        role_label = "你" if self.is_user else "AI助手"

        # 根据角色设置不同的样式
        bubble_class = "user-bubble" if self.is_user else "assistant-bubble"
        container_class = "user-container" if self.is_user else "assistant-container"

        with Container(classes=container_class):
            yield Label(f"[{role_label}] {time_str}", classes="message-header")
            yield Static(self.content, classes=f"message-content {bubble_class}")


class StatusBar(Static):
    """状态栏组件"""

    status = reactive("就绪")
    tokens = reactive(0)
    model = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="status-container"):
            yield Label(f"状态: {self.status}", id="status-text")
            yield Label(f"模型: {self.model}", id="model-text")
            yield Label(f"Token: {self.tokens}", id="token-text")

    def watch_status(self, status: str):
        """状态变化时更新显示"""
        status_widget = self.query_one("#status-text", Label)
        status_widget.update(f"状态: {status}")

    def watch_tokens(self, tokens: int):
        """Token数变化时更新显示"""
        token_widget = self.query_one("#token-text", Label)
        token_widget.update(f"Token: {tokens}")

    def watch_model(self, model: str):
        """模型变化时更新显示"""
        model_widget = self.query_one("#model-text", Label)
        model_widget.update(f"模型: {model}")


class ChatApp(App):
    """聊天应用主类"""

    CSS_PATH = "style.tcss"
    CSS = """
    Screen {
        background: #1a1a2e;
    }

    Header {
        background: #16213e;
        color: #e94560;
        height: 3;
    }

    Footer {
        background: #16213e;
        color: #0f3460;
        height: 1;
    }

    .chat-container {
        width: 100%;
        height: 100%;
        background: #1a1a2e;
    }

    .messages-container {
        height: 1fr;
        overflow-y: scroll;
        padding: 1 2;
        background: #1a1a2e;
    }

    .input-container {
        height: auto;
        padding: 1 2;
        background: #16213e;
        border-top: solid #0f3460;
    }

    .user-container {
        width: 100%;
        margin-bottom: 1;
    }

    .assistant-container {
        width: 100%;
        margin-bottom: 1;
    }

    .message-header {
        color: #e94560;
        margin-bottom: 0.5;
    }

    .message-content {
        padding: 1 2;
        border-radius: 4;
    }

    .user-bubble {
        background: #0f3460;
        color: #ffffff;
        margin-left: 4;
    }

    .assistant-bubble {
        background: #16213e;
        color: #e0e0e0;
        margin-right: 4;
        border: solid #0f3460;
    }

    .status-container {
        height: 1;
        background: #16213e;
        padding: 0 1;
        color: #0f3460;
    }

    .status-container Label {
        width: 1fr;
    }

    Input {
        background: #0f3460;
        color: #ffffff;
        border: none;
    }

    Input:focus {
        background: #16213e;
        border: solid #e94560;
    }

    Button {
        background: #e94560;
        color: #ffffff;
        border: none;
    }

    Button:hover {
        background: #ff6b6b;
    }

    Button:focus {
        border: solid #ffffff;
    }

    .loading {
        color: #e94560;
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    """

    def __init__(
        self,
        agent: Optional[SimpleAgent] = None,
        settings: Optional[Settings] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._settings = settings or get_settings()
        self._agent = agent
        self._is_generating = False

    def compose(self) -> ComposeResult:
        """构建界面"""
        yield Header()

        with Container(classes="chat-container"):
            # 消息区域
            yield VerticalScroll(
                id="messages-scroll",
                classes="messages-container",
            )

            # 状态条
            yield StatusBar(id="status-bar")

            # 输入区域
            with Horizontal(classes="input-container"):
                yield Input(
                    placeholder="输入消息... (按Enter发送, /clear清空历史, /help查看帮助)",
                    id="chat-input",
                )
                yield Button("发送", id="send-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """应用启动时"""
        # 初始化Agent
        if self._agent is None:
            self._agent = SimpleAgent(settings=self._settings)

        # 更新状态栏
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.model = self._agent.model

        # 添加欢迎消息
        self._add_welcome_message()

        # 聚焦输入框
        input_widget = self.query_one("#chat-input", Input)
        input_widget.focus()

    def _add_welcome_message(self) -> None:
        """添加欢迎消息"""
        welcome_content = (
            "你好！我是AI助手，基于硅基流动API。\n\n"
            "你可以：\n"
            "• 直接输入消息进行对话\n"
            "• 输入 /clear 清空对话历史\n"
            "• 输入 /help 查看帮助\n"
            "• 输入 /stats 查看对话统计\n"
            "• 输入 /models 查看可用模型\n"
        )
        self._add_message(welcome_content, is_user=False)

    def _add_message(
        self,
        content: str,
        is_user: bool,
        scroll: bool = True,
    ) -> None:
        """
        添加消息到界面

        Args:
            content: 消息内容
            is_user: 是否是用户消息
            scroll: 是否滚动到底部
        """
        messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
        bubble = MessageBubble(content, is_user=is_user)
        messages_scroll.mount(bubble)

        if scroll:
            messages_scroll.scroll_end(animate=False)

    def _update_status(self, status: str) -> None:
        """更新状态栏"""
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.status = status

    def _update_tokens(self) -> None:
        """更新Token计数"""
        if self._agent:
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.tokens = self._agent.conversation.total_tokens

    async def _send_message(self, user_input: str) -> None:
        """
        发送消息

        Args:
            user_input: 用户输入
        """
        if self._is_generating or not user_input.strip():
            return

        # 检查是否是特殊命令
        if user_input.startswith("/"):
            await self._handle_command(user_input)
            return

        self._is_generating = True
        self._update_status("正在思考...")

        try:
            # 添加用户消息
            self._add_message(user_input, is_user=True)

            # 清空输入框
            input_widget = self.query_one("#chat-input", Input)
            input_widget.value = ""

            # 调用Agent获取回复
            if self._settings.debug:
                # 调试模式：流式输出
                full_response = ""
                messages_scroll = self.query_one("#messages-scroll", VerticalScroll)

                # 创建一个临时的消息气泡用于显示流式输出
                temp_bubble = MessageBubble("正在生成...", is_user=False)
                messages_scroll.mount(temp_bubble)
                messages_scroll.scroll_end(animate=False)

                for chunk in self._agent.chat_stream(user_input):
                    full_response += chunk
                    # 更新临时气泡的内容（简化实现）
                    # 实际项目中可能需要更复杂的更新机制

                # 移除临时气泡，添加完整消息
                temp_bubble.remove()
                self._add_message(full_response, is_user=False)
            else:
                # 普通模式
                response = self._agent.chat(user_input)
                self._add_message(response, is_user=False)

            # 更新Token计数
            self._update_tokens()
            self._update_status("就绪")

        except Exception as e:
            error_msg = f"发生错误: {str(e)}"
            self._add_message(error_msg, is_user=False)
            self._update_status("错误")
            logger.error(f"Error in chat: {e}", exc_info=True)

        finally:
            self._is_generating = False
            # 重新聚焦输入框
            input_widget = self.query_one("#chat-input", Input)
            input_widget.focus()

    async def _handle_command(self, command: str) -> None:
        """
        处理特殊命令

        Args:
            command: 命令字符串
        """
        cmd = command.lower().strip()

        if cmd == "/clear" or cmd == "/清空":
            # 清空对话历史
            self._agent.clear_history()

            # 清空消息区域
            messages_scroll = self.query_one("#messages-scroll", VerticalScroll)
            messages_scroll.remove_children()

            # 重新添加欢迎消息
            self._add_welcome_message()

            # 更新状态
            self._update_tokens()
            self._update_status("已清空对话历史")

        elif cmd == "/help" or cmd == "/帮助":
            help_text = (
                "可用命令：\n"
                "/clear 或 /清空 - 清空对话历史\n"
                "/help 或 /帮助 - 显示此帮助\n"
                "/stats 或 /统计 - 查看对话统计\n"
                "/models 或 /模型 - 查看可用模型\n"
                "/model <模型名> - 切换模型\n"
                "/debug - 切换调试模式\n"
            )
            self._add_message(help_text, is_user=False)

        elif cmd == "/stats" or cmd == "/统计":
            if self._agent:
                summary = self._agent.get_history_summary()
                stats_text = (
                    "对话统计：\n"
                    f"• 消息数量: {summary['message_count']}\n"
                    f"• 总Token数: {summary['total_tokens']}\n"
                    f"• 创建时间: {summary['created_at']}\n"
                    f"• 最后更新: {summary['updated_at']}\n"
                    f"• 当前模型: {self._agent.model}"
                )
                self._add_message(stats_text, is_user=False)

        elif cmd == "/models" or cmd == "/模型":
            try:
                self._update_status("正在获取模型列表...")
                models = self._agent.list_models()

                if models:
                    model_list = "可用模型：\n"
                    for i, model in enumerate(models[:20], 1):  # 最多显示20个
                        model_id = model.get("id", "未知")
                        model_list += f"{i}. {model_id}\n"
                    if len(models) > 20:
                        model_list += f"... 还有 {len(models) - 20} 个模型"
                    self._add_message(model_list, is_user=False)
                else:
                    self._add_message("暂无可用模型", is_user=False)

                self._update_status("就绪")
            except Exception as e:
                self._add_message(f"获取模型列表失败: {e}", is_user=False)
                self._update_status("错误")

        elif cmd.startswith("/model "):
            # 切换模型
            model_name = command[len("/model ") :].strip()
            if model_name:
                self._agent.model = model_name
                status_bar = self.query_one("#status-bar", StatusBar)
                status_bar.model = model_name
                self._add_message(f"已切换到模型: {model_name}", is_user=False)
            else:
                self._add_message("用法: /model <模型名>", is_user=False)

        elif cmd == "/debug":
            # 切换调试模式
            self._settings.debug = not self._settings.debug
            status = "开启" if self._settings.debug else "关闭"
            self._add_message(f"调试模式已{status}", is_user=False)

        else:
            self._add_message(
                f"未知命令: {command}\n输入 /help 查看帮助", is_user=False
            )

        # 清空输入框
        input_widget = self.query_one("#chat-input", Input)
        input_widget.value = ""
        input_widget.focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮点击事件"""
        if event.button.id == "send-button":
            input_widget = self.query_one("#chat-input", Input)
            await self._send_message(input_widget.value)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """输入框提交事件"""
        if event.input.id == "chat-input":
            await self._send_message(event.value)

    def on_unmount(self) -> None:
        """应用关闭时"""
        if self._agent:
            self._agent.close()
            logger.info("Agent closed on unmount")


def run_tui(
    agent: Optional[SimpleAgent] = None,
    settings: Optional[Settings] = None,
) -> None:
    """
    运行TUI界面

    Args:
        agent: 可选的Agent实例
        settings: 可选的配置实例
    """
    app = ChatApp(agent=agent, settings=settings)
    app.run()
