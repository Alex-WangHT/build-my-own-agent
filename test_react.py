#!/usr/bin/env python3
"""
ReAct Agent 测试脚本
演示如何使用ReAct方式的对话Agent
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


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
        print("测试 5: 复杂问题 - 多步计算")
        print("=" * 60)

        agent.clear_history()
        try:
            response = agent.chat("如果一个人有100元，买了3个苹果，每个苹果5元，然后又买了2个橙子，每个橙子8元，最后还剩多少钱？请一步步计算。")
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
    print("输入 /quit 或 /exit 退出")
    print("输入 /clear 清空对话历史")
    print("输入 /tools 查看可用工具")
    print("=" * 60)

    with ReActAgent(settings=settings) as agent:
        while True:
            try:
                user_input = input("\n你: ")

                if user_input.lower() in ["/quit", "/exit"]:
                    print("再见！")
                    break

                if user_input.lower() == "/clear":
                    agent.clear_history()
                    print("对话历史已清空。")
                    continue

                if user_input.lower() == "/tools":
                    print("\n可用工具:")
                    for tool in agent.list_tools():
                        print(f"  - {tool['name']}: {tool['description']}")
                    continue

                if not user_input.strip():
                    continue

                print("🤔 思考中...")

                response = agent.chat(user_input)
                print(f"\nAI: {response}")

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n错误: {e}")
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
