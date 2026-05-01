#!/usr/bin/env python3
"""
ReAct Agent 测试脚本
演示如何使用ReAct方式的对话Agent
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


class Color:
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
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def print_thought(text: str):
    """显示思考内容"""
    print(f"\n{Color.DIM}💭 Thought:{Color.RESET}")
    for line in text.split('\n'):
        if line.strip():
            print(f"   {Color.DIM}{line}{Color.RESET}")


def print_action(action: str, action_input: dict):
    """显示Action（工具调用）"""
    print(f"\n{Color.CYAN}🔧 Action: {Color.BOLD}{action}{Color.RESET}")
    print(f"   {Color.CYAN}Input: {json.dumps(action_input, ensure_ascii=False, indent=2)}{Color.RESET}")
    print(f"   {Color.YELLOW}正在执行工具...{Color.RESET}")


def print_observation(action: str, observation: str):
    """显示Observation（工具执行结果）"""
    print(f"\n{Color.GREEN}👁️ Observation ({action}):{Color.RESET}")
    for line in observation.split('\n'):
        if line.strip():
            print(f"   {Color.GREEN}{line}{Color.RESET}")


def print_final_answer(answer: str):
    """显示最终答案"""
    print(f"\n{Color.BOLD}{Color.YELLOW}✨ Final Answer:{Color.RESET}")
    print(f"   {Color.BOLD}{answer}{Color.RESET}")


def test_react_agent():
    """
    测试ReAct Agent的基本功能
    """
    from agent.simple_agent import ReActAgent
    from config.settings import get_settings

    settings = get_settings()

    print("=" * 60)
    print("ReAct Agent 测试")
    print(f"模型: {settings.siliconflow_model}")
    print("=" * 60)

    with ReActAgent(settings=settings) as agent:
        print("\n可用工具:")
        for tool in agent.list_tools():
            print(f"  - {tool['name']}: {tool['description']}")

        print("\n" + "=" * 60)
        print("测试 1: 计算器工具 - 计算 2 + 3 * 4")
        print("=" * 60)

        try:
            response = agent.chat("计算 2 + 3 * 4 等于多少？")
            print(f"\n答案: {response}")
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 60)
        print("测试 2: 获取当前时间")
        print("=" * 60)

        agent.clear_history()
        try:
            response = agent.chat("现在是什么时间？")
            print(f"\n答案: {response}")
        except Exception as e:
            print(f"\n错误: {e}")

        print("\n" + "=" * 60)
        print("测试 3: 天气查询 - 北京的天气")
        print("=" * 60)

        agent.clear_history()
        try:
            response = agent.chat("北京今天的天气怎么样？")
            print(f"\n答案: {response}")
        except Exception as e:
            print(f"\n错误: {e}")

        print("\n" + "=" * 60)
        print("测试 4: 网络搜索 - 关于Python")
        print("=" * 60)

        agent.clear_history()
        try:
            response = agent.chat("什么是Python编程语言？请搜索相关信息。")
            print(f"\n答案: {response}")
        except Exception as e:
            print(f"\n错误: {e}")

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)


def test_custom_tool():
    """
    测试自定义工具
    """
    from tools.tool import Tool, ToolRegistry

    def greet(name: str, greeting: str = "Hello") -> str:
        """
        问候函数
        """
        return f"{greeting}, {name}!"

    greet_tool = Tool(
        name="greet",
        description="向用户发送问候。可以自定义问候语。",
        func=greet,
        parameters={
            "name": {
                "type": "string",
                "description": "要问候的人的名字",
            },
            "greeting": {
                "type": "string",
                "description": "问候语，默认为'Hello'",
            },
        },
        required=["name"],
    )

    registry = ToolRegistry()
    registry.register(greet_tool)

    print("\n" + "=" * 60)
    print("测试自定义工具: greet")
    print("=" * 60)

    result = greet_tool.execute(name="张三", greeting="你好")
    print(f"执行结果: {result}")

    print("\n自定义工具测试完成！")


def interactive_mode():
    """
    交互式模式
    """
    from agent.simple_agent import ReActAgent
    from config.settings import get_settings

    settings = get_settings()

    print("\n" + "=" * 60)
    print("ReAct Agent 交互式模式")
    print(f"模型: {settings.siliconflow_model}")
    print("输入 /quit 或 /exit 退出")
    print("输入 /clear 清空对话历史")
    print("输入 /tools 查看可用工具")
    print("=" * 60)

    with ReActAgent(settings=settings) as agent:
        while True:
            try:
                user_input = input(f"\n{Color.BOLD}👤 你: {Color.RESET}")

                if user_input.lower() in ["/quit", "/exit"]:
                    print("再见！")
                    break

                if user_input.lower() == "/clear":
                    agent.clear_history()
                    print("对话历史已清空。")
                    continue

                if user_input.lower() == "/tools":
                    print(f"\n{Color.BOLD}🔧 可用工具:{Color.RESET}")
                    for tool in agent.list_tools():
                        print(f"  - {Color.CYAN}{tool['name']}{Color.RESET}: {tool['description']}")
                    continue

                if not user_input.strip():
                    continue

                print(f"\n{Color.YELLOW}🤔 思考中...{Color.RESET}")

                response = agent.chat(
                    user_input,
                    on_thought=print_thought,
                    on_action=print_action,
                    on_observation=print_observation,
                    on_final_answer=print_final_answer,
                )

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n{Color.RED}❌ 错误: {e}{Color.RESET}")
                import traceback
                traceback.print_exc()


def main():
    """
    主函数
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="ReAct Agent 测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  python test_react.py

  # 运行交互式模式
  python test_react.py --interactive

  # 测试自定义工具
  python test_react.py --custom-tool
        """,
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="启动交互式模式",
    )

    parser.add_argument(
        "-c",
        "--custom-tool",
        action="store_true",
        help="测试自定义工具",
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.custom_tool:
        test_custom_tool()
    else:
        test_react_agent()
        test_custom_tool()


if __name__ == "__main__":
    main()
