"""
简单命令行界面
使用Python基本的input()和print()实现，方便测试
支持ReAct工具调用和Token统计
"""

import json
import sys
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any

from agent.simple_agent import ReActAgent, estimate_messages_tokens
from config.settings import get_settings, Settings


class Color:
    """终端颜色常量"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


class LoadingAnimation:
    """加载动画类"""

    def __init__(self, message: str = "正在思考", interval: float = 0.2):
        self.message = message
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._frame_index = 0

    def _animate(self):
        """动画循环"""
        while self._running:
            frame = self._frames[self._frame_index % len(self._frames)]
            print(f"\r{frame} {self.message}...", end="", flush=True)
            self._frame_index += 1
            time.sleep(self.interval)

    def start(self):
        """启动动画"""
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self, clear: bool = True):
        """
        停止动画

        Args:
            clear: 是否清除动画显示
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if clear:
            print("\r" + " " * (len(self.message) + 10), end="\r", flush=True)


class TokenTracker:
    """Token追踪器，用于跟踪每轮对话的Token使用情况"""

    def __init__(self):
        self.initial_prompt_tokens = 0
        self.initial_completion_tokens = 0
        self.initial_total_tokens = 0
        self.round_prompt_tokens = 0
        self.round_completion_tokens = 0
        self.round_total_tokens = 0
        self.estimated_context_tokens = 0

    def reset(self, agent: ReActAgent):
        """重置并记录初始状态"""
        stats = agent.get_token_stats()
        self.initial_prompt_tokens = stats.prompt_tokens
        self.initial_completion_tokens = stats.completion_tokens
        self.initial_total_tokens = stats.total_tokens
        self.estimated_context_tokens = agent.estimate_context_tokens()
        self.round_prompt_tokens = 0
        self.round_completion_tokens = 0
        self.round_total_tokens = 0

    def update(self, agent: ReActAgent):
        """更新本轮统计"""
        stats = agent.get_token_stats()
        self.round_prompt_tokens = stats.prompt_tokens - self.initial_prompt_tokens
        self.round_completion_tokens = stats.completion_tokens - self.initial_completion_tokens
        self.round_total_tokens = stats.total_tokens - self.initial_total_tokens

    def get_summary(self) -> Dict[str, Any]:
        """获取本轮统计摘要"""
        return {
            "estimated_context": self.estimated_context_tokens,
            "round_prompt": self.round_prompt_tokens,
            "round_completion": self.round_completion_tokens,
            "round_total": self.round_total_tokens,
        }


class SimpleCLI:
    """简单命令行界面"""

    def __init__(
        self,
        agent: Optional[ReActAgent] = None,
        settings: Optional[Settings] = None,
    ):
        self._settings = settings or get_settings()
        self._agent = agent
        self._running = False
        self._token_tracker = TokenTracker()

    def _print_thought(self, text: str):
        """显示思考内容"""
        print(f"\n{Color.DIM}💭 Thought:{Color.RESET}")
        for line in text.split('\n'):
            if line.strip():
                print(f"   {Color.DIM}{line}{Color.RESET}")

    def _print_action(self, action: str, action_input: Dict[str, Any]):
        """显示Action（工具调用）"""
        print(f"\n{Color.CYAN}🔧 Action: {Color.BOLD}{action}{Color.RESET}")
        print(f"   {Color.CYAN}Input: {json.dumps(action_input, ensure_ascii=False, indent=2)}{Color.RESET}")
        print(f"   {Color.YELLOW}正在执行工具...{Color.RESET}")

    def _print_observation(self, action: str, observation: str):
        """显示Observation（工具执行结果）"""
        print(f"\n{Color.GREEN}👁️ Observation ({action}):{Color.RESET}")
        for line in observation.split('\n'):
            if line.strip():
                print(f"   {Color.GREEN}{line}{Color.RESET}")

    def _print_final_answer(self, answer: str):
        """显示最终答案"""
        print(f"\n{Color.BOLD}{Color.YELLOW}✨ Final Answer:{Color.RESET}")
        lines = answer.split("\n")
        for line in lines:
            print(f"   {Color.BOLD}{line}{Color.RESET}")

    def _print_token_stats(self, elapsed: float):
        """打印Token统计信息"""
        token_summary = self._token_tracker.get_summary()
        total_stats = self._agent.get_token_stats()
        
        print()
        print(f"{Color.DIM}{'='*60}{Color.RESET}")
        print(f"{Color.BLUE}📊 Token统计（本轮对话）:{Color.RESET}")
        print(f"{Color.DIM}{'-'*40}{Color.RESET}")
        print(f"   {Color.CYAN}上下文估计: {token_summary['estimated_context']} tokens{Color.RESET}")
        print(f"   {Color.MAGENTA}本轮消耗:{Color.RESET}")
        print(f"      Prompt: {token_summary['round_prompt']} tokens")
        print(f"      Completion: {token_summary['round_completion']} tokens")
        print(f"      {Color.BOLD}Total: {token_summary['round_total']} tokens{Color.RESET}")
        print()
        print(f"{Color.BLUE}📊 累计统计:{Color.RESET}")
        print(f"{Color.DIM}{'-'*40}{Color.RESET}")
        print(f"   累计 Prompt: {total_stats.prompt_tokens} tokens")
        print(f"   累计 Completion: {total_stats.completion_tokens} tokens")
        print(f"   {Color.BOLD}累计 Total: {total_stats.total_tokens} tokens{Color.RESET}")
        print()
        print(f"⏱️  本轮耗时: {elapsed:.2f}秒")
        print(f"{Color.DIM}{'='*60}{Color.RESET}")
        print()

    def _print_header(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("🤖 AI Agent - 基于硅基流动API (ReAct模式)")
        print("=" * 60)
        print()
        print(f"📦 模型: {self._agent.model if self._agent else self._settings.siliconflow_model}")
        print(f"⏱️  请求超时: {self._settings.request_timeout}秒")
        print(f"💡 输入消息进行对话，或输入以下命令：")
        print("   /help    - 显示帮助")
        print("   /clear   - 清空对话历史")
        print("   /stats   - 查看对话统计")
        print("   /tools   - 查看可用工具")
        print("   /models  - 查看可用模型")
        print("   /model   - 切换模型")
        print("   /quit    - 退出程序")
        print()
        print("✨ 提示: 支持实时工具调用和Token统计显示！")
        print("-" * 60)
        print()

    def _print_help(self):
        """打印帮助信息"""
        print()
        print("📖 帮助信息：")
        print("-" * 40)
        print("直接输入消息即可与AI助手对话。")
        print("AI会根据需要自动调用工具来回答问题。")
        print()
        print("可用命令：")
        print("  /help          显示此帮助信息")
        print("  /clear         清空对话历史")
        print("  /stats         查看对话统计信息")
        print("  /tools         查看可用工具列表")
        print("  /models        列出可用的模型")
        print("  /model <名称>  切换到指定模型")
        print("  /quit, /exit   退出程序")
        print()
        print("ReAct模式说明：")
        print("  - AI会先思考（Thought）需要做什么")
        print("  - 如果需要工具，会调用工具（Action）")
        print("  - 工具执行后返回结果（Observation）")
        print("  - 重复上述步骤直到得到最终答案（Final Answer）")
        print()

    def _print_tools(self):
        """打印可用工具列表"""
        if not self._agent:
            print("❌ Agent未初始化")
            return

        tools = self._agent.list_tools()
        print()
        print("🔧 可用工具：")
        print("-" * 40)
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {Color.CYAN}{tool['name']}{Color.RESET}")
            print(f"     {tool['description']}")
            params = tool.get('parameters', {}).get('properties', {})
            if params:
                print(f"     参数:")
                for param_name, param_info in params.items():
                    required = tool.get('parameters', {}).get('required', [])
                    req_mark = " *" if param_name in required else ""
                    print(f"       - {param_name}{req_mark}: {param_info.get('description', '无描述')}")
            print()

    def _print_stats(self):
        """打印统计信息"""
        if not self._agent:
            print("❌ Agent未初始化")
            return

        summary = self._agent.get_history_summary()
        token_stats = self._agent.get_token_stats()
        
        print()
        print("📊 对话统计：")
        print("-" * 40)
        print(f"  消息数量: {summary['message_count']}")
        print(f"  Prompt Tokens: {token_stats.prompt_tokens}")
        print(f"  Completion Tokens: {token_stats.completion_tokens}")
        print(f"  {Color.BOLD}总Token数: {token_stats.total_tokens}{Color.RESET}")
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
            print()
            print("   提示: 输入 /models 查看可用模型列表")
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

        elif cmd == "/tools":
            self._print_tools()

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

    def _chat(self, user_message: str):
        """
        进行对话（ReAct模式）

        Args:
            user_message: 用户消息
        """
        if not self._agent:
            print("❌ Agent未初始化")
            return

        start_time = time.time()
        
        self._token_tracker.reset(self._agent)
        
        estimated = self._token_tracker.estimated_context_tokens
        print(f"\n{Color.DIM}📊 上下文Token估计: {estimated} tokens{Color.RESET}")
        print(f"{Color.YELLOW}🤔 思考中...{Color.RESET}")

        try:
            response = self._agent.chat(
                user_message,
                on_thought=self._print_thought,
                on_action=self._print_action,
                on_observation=self._print_observation,
                on_final_answer=self._print_final_answer,
            )
            
            self._token_tracker.update(self._agent)
            
            elapsed = time.time() - start_time
            self._print_token_stats(elapsed)

        except KeyboardInterrupt:
            print()
            print("\n⚠️  已中断请求")
            print()

        except Exception as e:
            print()
            print(f"\n{Color.RED}❌ 错误: {e}{Color.RESET}")
            if self._settings.debug:
                import traceback
                traceback.print_exc()
            print()

    def run(self):
        """运行命令行界面"""
        if self._agent is None:
            self._agent = ReActAgent(settings=self._settings)

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
                print("\n👋 再见！")
                self._running = False
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                if self._settings.debug:
                    import traceback
                    traceback.print_exc()

        if self._agent:
            self._agent.close()

        print()
        print("=" * 60)
        print("👋 感谢使用，再见！")
        print("=" * 60)
        print()


def run_cli(
    agent: Optional[ReActAgent] = None,
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
