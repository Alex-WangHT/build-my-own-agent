"""
Tool Call Parser 模块
从自由文本 LLM 输出中提取结构化的工具调用

支持多种格式：
- JSON 格式
- XML `<tool_call>` 标签
- GLM 风格简化语法
- MiniMax `<invoke>` 块
- Perl 风格 `[TOOL_CALL]` 块
- Markdown 代码块
- OpenAI 原生格式
- 更多...

设计理念：
- 不依赖 agent 状态、内存、provider 或通道
- 纯文本转换
- 可扩展的解析器架构
"""

from tool_call_parser.base import (
    ToolCall,
    FunctionCall,
    ParsedToolCalls,
    ToolCallParser,
    ParseResult,
)
from tool_call_parser.parsers import (
    JSONParser,
    XMLToolCallParser,
    GLMStyleParser,
    MiniMaxInvokeParser,
    PerlStyleParser,
    MarkdownFenceParser,
    OpenAINativeParser,
    ReActStyleParser,
)
from tool_call_parser.registry import (
    ParserRegistry,
    get_parser,
    list_parsers,
    register_parser,
    parse_tool_calls,
    parse_first_tool_call,
)

__all__ = [
    "ToolCall",
    "FunctionCall",
    "ParsedToolCalls",
    "ToolCallParser",
    "ParseResult",
    "JSONParser",
    "XMLToolCallParser",
    "GLMStyleParser",
    "MiniMaxInvokeParser",
    "PerlStyleParser",
    "MarkdownFenceParser",
    "OpenAINativeParser",
    "ReActStyleParser",
    "ParserRegistry",
    "get_parser",
    "list_parsers",
    "register_parser",
    "parse_tool_calls",
    "parse_first_tool_call",
]
