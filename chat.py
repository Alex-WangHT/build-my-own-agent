#!/usr/bin/env python3
"""
AI Agent 入口脚本
使用Python基本的input()和print()实现简单的命令行交互
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


def run_single_message(message: str, debug: bool = False) -> None:
    """
    运行单条消息模式

    Args:
        message: 用户消息
        debug: 是否开启调试模式
    """
    from agent.simple_agent import ReActAgent
    from config.settings import get_settings

    settings = get_settings()

    print(f"🤖 AI Agent (模型: {settings.siliconflow_model})")
    print(f"👤 你: {message}")
    print("🤔 正在思考...\n")

    try:
        with ReActAgent(settings=settings) as agent:
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


def run_interactive(
    debug: bool = False,
    theme: str = None,
    no_splash: bool = False,
    splash_duration: float = 2.0,
) -> None:
    """
    运行交互式命令行模式

    Args:
        debug: 是否开启调试模式
        theme: 主题名称
        no_splash: 是否跳过启动界面
        splash_duration: 启动动画持续时间（秒）
    """
    from tui.app import run_cli

    if no_splash:
        print("🚀 启动AI Agent 命令行界面...")
        print("按 Ctrl+C 或输入 /quit 退出\n")

    run_cli(
        theme=theme,
        show_splash=not no_splash,
        splash_animate=True,
        splash_duration=splash_duration,
    )


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="AlexClaw AI Agent - 基于硅基流动API的智能对话系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动交互式对话模式（带启动动画）
  python chat.py

  # 跳过启动动画
  python chat.py --no-splash

  # 使用指定主题
  python chat.py --theme dark

  # 发送单条消息
  python chat.py "你好，请介绍一下你自己"

  # 调试模式
  python chat.py --debug "你好"

  # 查看可用主题
  python chat.py --themes

  # 查看帮助
  python chat.py --help
        """,
    )

    parser.add_argument(
        "message",
        nargs="?",
        help="要发送的消息（如果不提供则进入交互式模式）",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="开启调试模式",
    )

    parser.add_argument(
        "-t",
        "--theme",
        type=str,
        default=None,
        help="指定主题名称 (default, dark, light)",
    )

    parser.add_argument(
        "--themes",
        action="store_true",
        help="列出所有可用主题",
    )

    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="跳过启动动画",
    )

    parser.add_argument(
        "--splash-duration",
        type=float,
        default=2.0,
        help="启动动画持续时间（秒），默认2.0秒",
    )

    args = parser.parse_args()

    # 列出可用主题
    if args.themes:
        from tui.themes.registry import list_themes

        themes = list_themes()
        print("\n🎨 可用主题：")
        print("-" * 40)
        for i, theme_info in enumerate(themes, 1):
            print(f"  {i}. {theme_info['name']}")
            print(f"     {theme_info['description']}")
            print()
        sys.exit(0)

    # 设置日志
    setup_logging(debug=args.debug)

    # 检查API密钥
    if not check_api_key():
        sys.exit(1)

    # 根据参数决定运行模式
    if args.message:
        # 单条消息模式
        run_single_message(args.message, debug=args.debug)
    else:
        # 交互式模式
        try:
            run_interactive(
                debug=args.debug,
                theme=args.theme,
                no_splash=args.no_splash,
                splash_duration=args.splash_duration,
            )
        except KeyboardInterrupt:
            print("\n👋 再见！")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            if args.debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
