#!/usr/bin/env python3
"""
AI Agent 入口脚本
提供TUI交互模式和命令行模式
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging(debug: bool = False) -> None:
    """
    设置日志

    Args:
        debug: 是否开启调试模式
    """
    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )

    # 降低第三方库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("textual").setLevel(logging.WARNING)


def check_api_key() -> bool:
    """
    检查API密钥是否配置

    Returns:
        是否配置了API密钥
    """
    import os

    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n❌ 错误: 未配置硅基流动API密钥")
        print("\n请按以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("   cp .env.example .env")
        print("2. 编辑 .env 文件，填入你的API密钥")
        print("   SILICONFLOW_API_KEY=你的实际密钥")
        print("\n获取API密钥: https://cloud.siliconflow.cn/")
        return False
    return True


def run_interactive() -> None:
    """运行交互式TUI模式"""
    from tui.app import run_tui

    print("🚀 启动AI Agent TUI界面...")
    print("按 Ctrl+C 退出\n")

    run_tui()


def run_single_message(message: str, debug: bool = False) -> None:
    """
    运行单条消息模式

    Args:
        message: 用户消息
        debug: 是否开启调试模式
    """
    from agent.simple_agent import SimpleAgent
    from config.settings import get_settings

    settings = get_settings()

    print(f"🤖 AI Agent (模型: {settings.siliconflow_model})")
    print(f"👤 你: {message}")
    print("🤔 正在思考...\n")

    try:
        with SimpleAgent(settings=settings) as agent:
            if debug:
                # 调试模式：流式输出
                print("🤖 AI助手: ", end="", flush=True)
                for chunk in agent.chat_stream(message):
                    print(chunk, end="", flush=True)
                print()  # 换行
            else:
                # 普通模式
                response = agent.chat(message)
                print(f"🤖 AI助手: {response}")

            # 显示统计
            summary = agent.get_history_summary()
            print(f"\n📊 统计: {summary['total_tokens']} tokens")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="AI Agent - 基于硅基流动API的智能对话系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动TUI交互模式
  python chat.py

  # 发送单条消息
  python chat.py "你好，请介绍一下你自己"

  # 调试模式
  python chat.py --debug "你好"

  # 查看帮助
  python chat.py --help
        """,
    )

    parser.add_argument(
        "message",
        nargs="?",
        help="要发送的消息（如果不提供则进入TUI交互模式）",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="开启调试模式",
    )

    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="强制使用简单命令行模式而非TUI",
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(debug=args.debug)

    # 检查API密钥
    if not check_api_key():
        sys.exit(1)

    # 根据参数决定运行模式
    if args.message:
        # 单条消息模式
        run_single_message(args.message, debug=args.debug)
    elif args.no_tui:
        # 简单命令行交互模式
        print("🚀 启动AI Agent 命令行模式...")
        print("输入 /quit 或 /exit 退出\n")

        from agent.simple_agent import SimpleAgent
        from config.settings import get_settings

        settings = get_settings()

        with SimpleAgent(settings=settings) as agent:
            print(f"🤖 AI助手已就绪 (模型: {settings.siliconflow_model})")
            print("-" * 50)

            while True:
                try:
                    user_input = input("\n👤 你: ").strip()

                    if not user_input:
                        continue

                    if user_input.lower() in ["/quit", "/exit", "/q"]:
                        print("👋 再见！")
                        break

                    if user_input.lower() == "/clear":
                        agent.clear_history()
                        print("🗑️  对话历史已清空")
                        continue

                    print("🤔 正在思考...", end="\r")

                    if args.debug:
                        # 调试模式：流式输出
                        print("🤖 AI助手: ", end="", flush=True)
                        for chunk in agent.chat_stream(user_input):
                            print(chunk, end="", flush=True)
                        print()
                    else:
                        response = agent.chat(user_input)
                        print(f"🤖 AI助手: {response}")

                except KeyboardInterrupt:
                    print("\n\n👋 再见！")
                    break
                except Exception as e:
                    print(f"❌ 错误: {e}")
                    if args.debug:
                        import traceback

                        traceback.print_exc()
    else:
        # TUI交互模式
        try:
            run_interactive()
        except KeyboardInterrupt:
            print("\n👋 再见！")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            if args.debug:
                import traceback

                traceback.print_exc()

            # 如果TUI失败，回退到简单命令行模式
            print("\n⚠️  TUI启动失败，回退到简单命令行模式...")
            print("提示: 可以使用 --no-tui 参数强制使用简单模式\n")

            from agent.simple_agent import SimpleAgent
            from config.settings import get_settings

            settings = get_settings()

            with SimpleAgent(settings=settings) as agent:
                print(f"🤖 AI助手已就绪 (模型: {settings.siliconflow_model})")
                print("输入 /quit 退出")

                while True:
                    try:
                        user_input = input("\n👤 你: ").strip()

                        if not user_input:
                            continue

                        if user_input.lower() in ["/quit", "/exit", "/q"]:
                            print("👋 再见！")
                            break

                        response = agent.chat(user_input)
                        print(f"🤖 AI助手: {response}")

                    except KeyboardInterrupt:
                        print("\n\n👋 再见！")
                        break
                    except Exception as e:
                        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
