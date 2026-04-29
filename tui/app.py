"""
简单命令行界面
使用Python基本的input()和print()实现，方便测试
"""

import sys
from datetime import datetime
from typing import Optional

from agent.simple_agent import SimpleAgent
from config.settings import get_settings, Settings


class SimpleCLI:
    """简单命令行界面"""

    def __init__(
        self,
        agent: Optional[SimpleAgent] = None,
        settings: Optional[Settings] = None,
    ):
        self._settings = settings or get_settings()
        self._agent = agent
        self._running = False

    def _print_header(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("🤖 AI Agent - 基于硅基流动API")
        print("=" * 60)
        print()
        print(f"📦 模型: {self._agent.model if self._agent else self._settings.siliconflow_model}")
        print(f"💡 输入消息进行对话，或输入以下命令：")
        print("   /help    - 显示帮助")
        print("   /clear   - 清空对话历史")
        print("   /stats   - 查看对话统计")
        print("   /models  - 查看可用模型")
        print("   /model   - 切换模型")
        print("   /quit    - 退出程序")
        print()
        print("-" * 60)
        print()

    def _print_help(self):
        """打印帮助信息"""
        print()
        print("📖 帮助信息：")
        print("-" * 40)
        print("直接输入消息即可与AI助手对话。")
        print()
        print("可用命令：")
        print("  /help          显示此帮助信息")
        print("  /clear         清空对话历史")
        print("  /stats         查看对话统计信息")
        print("  /models        列出可用的模型")
        print("  /model <名称>  切换到指定模型")
        print("  /quit, /exit   退出程序")
        print()
        print("示例：")
        print("  你好，请介绍一下你自己")
        print("  /model deepseek-ai/DeepSeek-V3")
        print("  /stats")
        print()

    def _print_stats(self):
        """打印统计信息"""
        if not self._agent:
            print("❌ Agent未初始化")
            return

        summary = self._agent.get_history_summary()
        print()
        print("📊 对话统计：")
        print("-" * 40)
        print(f"  消息数量: {summary['message_count']}")
        print(f"  总Token数: {summary['total_tokens']}")
        print(f"  创建时间: {summary['created_at']}")
        print(f"  最后更新: {summary['updated_at']}")
        print(f"  当前模型: {self._agent.model}")
        print()

    def _list_models(self):
        """列出可用模型"""
        if not self._agent:
            print("❌ Agent未初始化")
            return

        print()
        print("🔍 正在获取模型列表...")
        try:
            models = self._agent.list_models()
            if models:
                print()
                print("📋 可用模型（前20个）：")
                print("-" * 40)
                for i, model in enumerate(models[:20], 1):
                    model_id = model.get("id", "未知")
                    print(f"  {i:2d}. {model_id}")
                if len(models) > 20:
                    print(f"  ... 还有 {len(models) - 20} 个模型")
                print()
            else:
                print("❌ 暂无可用模型")
        except Exception as e:
            print(f"❌ 获取模型列表失败: {e}")
        print()

    def _switch_model(self, model_name: str):
        """切换模型"""
        if not self._agent:
            print("❌ Agent未初始化")
            return

        if not model_name:
            print("❌ 请指定模型名称")
            print("   用法: /model <模型名称>")
            return

        self._agent.model = model_name
        print(f"✅ 已切换到模型: {model_name}")
        print()

    def _clear_history(self):
        """清空对话历史"""
        if not self._agent:
            print("❌ Agent未初始化")
            return

        self._agent.clear_history()
        print("✅ 对话历史已清空")
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

        elif cmd == "/models":
            self._list_models()

        elif cmd.startswith("/model "):
            model_name = command[len("/model ") :].strip()
            self._switch_model(model_name)

        else:
            print(f"❌ 未知命令: {command}")
            print("   输入 /help 查看帮助")
            print()

        return True

    def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            user_input = input("👤 你: ").strip()
            return user_input
        except KeyboardInterrupt:
            print()
            print("\n👋 检测到中断，正在退出...")
            self._running = False
            return ""
        except EOFError:
            print()
            self._running = False
            return ""

    def _print_assistant_response(self, response: str):
        """打印助手回复"""
        print()
        print("🤖 AI助手:")
        # 逐行打印，保持格式
        lines = response.split("\n")
        for line in lines:
            print(f"   {line}")
        print()

    def _chat(self, user_message: str):
        """
        进行对话

        Args:
            user_message: 用户消息
        """
        if not self._agent:
            print("❌ Agent未初始化")
            return

        print("🤔 正在思考...", end="\r")

        try:
            # 调用Agent获取回复
            if self._settings.debug:
                # 调试模式：流式输出
                print("🤖 AI助手: ")
                full_response = ""
                for chunk in self._agent.chat_stream(user_message):
                    full_response += chunk
                    print(chunk, end="", flush=True)
                print()  # 换行
                print()
            else:
                # 普通模式
                response = self._agent.chat(user_message)
                self._print_assistant_response(response)

            # 显示Token使用情况（调试模式）
            if self._settings.debug:
                summary = self._agent.get_history_summary()
                print(f"[调试] 已使用 {summary['total_tokens']} tokens")
                print()

        except Exception as e:
            print()
            print(f"❌ 错误: {e}")
            if self._settings.debug:
                import traceback

                traceback.print_exc()
            print()

    def run(self):
        """运行命令行界面"""
        # 初始化Agent
        if self._agent is None:
            self._agent = SimpleAgent(settings=self._settings)

        self._running = True
        self._print_header()

        while self._running:
            try:
                user_input = self._get_user_input()

                if not self._running:
                    break

                if not user_input:
                    continue

                # 检查是否是命令
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                else:
                    # 普通对话
                    self._chat(user_input)

            except KeyboardInterrupt:
                print()
                print("\n👋 再见！")
                self._running = False
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                if self._settings.debug:
                    import traceback

                    traceback.print_exc()

        # 清理资源
        if self._agent:
            self._agent.close()

        print()
        print("=" * 60)
        print("👋 感谢使用，再见！")
        print("=" * 60)
        print()


def run_cli(
    agent: Optional[SimpleAgent] = None,
    settings: Optional[Settings] = None,
) -> None:
    """
    运行简单命令行界面

    Args:
        agent: 可选的Agent实例
        settings: 可选的配置实例
    """
    cli = SimpleCLI(agent=agent, settings=settings)
    cli.run()
