"""
Tool Call Parser 注册表
管理和使用各种工具调用解析器
"""

from typing import Dict, List, Optional, Type, Any

from tool_call_parser.base import (
    ToolCallParser,
    ToolCall,
    ParsedToolCalls,
    ParseResult,
    ToolCallFormat,
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


class ParserRegistry:
    """
    解析器注册表
    管理所有已注册的工具调用解析器

    设计理念：
    - 运行时可动态注册新的解析器
    - 支持尝试所有解析器或指定格式解析
    """

    _instance: Optional["ParserRegistry"] = None
    _parsers: Dict[str, ToolCallParser] = {}
    _parser_classes: Dict[str, Type[ToolCallParser]] = {}

    PARSER_ORDER = [
        "openai_native",
        "json",
        "xml_tool_call",
        "markdown_fence",
        "perl_style",
        "minimax_invoke",
        "glm_style",
        "react_style",
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance

    def _initialize_defaults(self):
        """初始化默认解析器"""
        self._parsers = {}
        self._parser_classes = {}

        default_parsers = [
            ("json", JSONParser),
            ("xml_tool_call", XMLToolCallParser),
            ("glm_style", GLMStyleParser),
            ("minimax_invoke", MiniMaxInvokeParser),
            ("perl_style", PerlStyleParser),
            ("markdown_fence", MarkdownFenceParser),
            ("openai_native", OpenAINativeParser),
            ("react_style", ReActStyleParser),
        ]

        for name, parser_class in default_parsers:
            self.register(name, parser_class)

    def register(self, name: str, parser_class: Type[ToolCallParser]) -> None:
        """
        注册一个解析器类

        Args:
            name: 解析器名称
            parser_class: 解析器类
        """
        self._parser_classes[name] = parser_class
        if name in self._parsers:
            del self._parsers[name]

    def get(self, name: str) -> Optional[ToolCallParser]:
        """
        获取解析器实例

        Args:
            name: 解析器名称

        Returns:
            解析器实例，如果不存在则返回 None
        """
        if name in self._parsers:
            return self._parsers[name]

        if name in self._parser_classes:
            parser = self._parser_classes[name]()
            self._parsers[name] = parser
            return parser

        return None

    def list_parsers(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的解析器

        Returns:
            解析器信息列表
        """
        return [
            {
                "name": name,
                "format": parser_class().format.value,
                "description": parser_class().description,
            }
            for name, parser_class in self._parser_classes.items()
        ]

    def parse(
        self,
        text: str,
        format_name: Optional[str] = None,
    ) -> ParsedToolCalls:
        """
        解析文本中的工具调用

        Args:
            text: 要解析的文本
            format_name: 指定格式（可选，不指定则尝试所有格式）

        Returns:
            ParsedToolCalls 解析结果
        """
        if format_name:
            parser = self.get(format_name)
            if parser:
                result = parser.try_parse(text)
                return ParsedToolCalls(
                    tool_calls=result.tool_calls,
                    raw_response=text,
                    has_tool_calls=len(result.tool_calls) > 0,
                )
            return ParsedToolCalls(raw_response=text, has_tool_calls=False)

        for name in self.PARSER_ORDER:
            parser = self.get(name)
            if parser and parser.can_parse(text):
                result = parser.try_parse(text)
                if result.success and result.tool_calls:
                    return ParsedToolCalls(
                        tool_calls=result.tool_calls,
                        raw_response=text,
                        has_tool_calls=True,
                    )

        for name, parser_class in self._parser_classes.items():
            if name not in self.PARSER_ORDER:
                parser = self.get(name)
                if parser:
                    result = parser.try_parse(text)
                    if result.success and result.tool_calls:
                        return ParsedToolCalls(
                            tool_calls=result.tool_calls,
                            raw_response=text,
                            has_tool_calls=True,
                        )

        return ParsedToolCalls(raw_response=text, has_tool_calls=False)

    def parse_all(self, text: str) -> ParsedToolCalls:
        """
        解析文本中的所有工具调用（不局限于第一个匹配的格式）

        Args:
            text: 要解析的文本

        Returns:
            ParsedToolCalls 解析结果
        """
        all_tool_calls: List[ToolCall] = []

        for name, parser_class in self._parser_classes.items():
            parser = self.get(name)
            if parser:
                result = parser.try_parse(text)
                if result.success and result.tool_calls:
                    all_tool_calls.extend(result.tool_calls)

        return ParsedToolCalls(
            tool_calls=all_tool_calls,
            raw_response=text,
            has_tool_calls=len(all_tool_calls) > 0,
        )

    def clear_cache(self) -> None:
        """清除缓存的解析器实例"""
        self._parsers = {}


_registry: Optional[ParserRegistry] = None


def _get_registry() -> ParserRegistry:
    """获取全局注册表实例"""
    global _registry
    if _registry is None:
        _registry = ParserRegistry()
    return _registry


def parse_tool_calls(
    text: str,
    format_name: Optional[str] = None,
) -> ParsedToolCalls:
    """
    解析文本中的工具调用的便捷函数

    Args:
        text: 要解析的文本
        format_name: 指定格式（可选）

    Returns:
        ParsedToolCalls 解析结果
    """
    registry = _get_registry()
    return registry.parse(text, format_name)


def parse_first_tool_call(
    text: str,
    format_name: Optional[str] = None,
) -> Optional[ToolCall]:
    """
    解析文本并返回第一个工具调用的便捷函数

    Args:
        text: 要解析的文本
        format_name: 指定格式（可选）

    Returns:
        第一个 ToolCall，如果没有则返回 None
    """
    result = parse_tool_calls(text, format_name)
    return result.first()


def get_parser(name: str) -> Optional[ToolCallParser]:
    """
    获取指定解析器的便捷函数

    Args:
        name: 解析器名称

    Returns:
        解析器实例
    """
    registry = _get_registry()
    return registry.get(name)


def list_parsers() -> List[Dict[str, Any]]:
    """
    列出所有可用解析器的便捷函数

    Returns:
        解析器信息列表
    """
    registry = _get_registry()
    return registry.list_parsers()


def register_parser(name: str, parser_class: Type[ToolCallParser]) -> None:
    """
    注册自定义解析器的便捷函数

    Args:
        name: 解析器名称
        parser_class: 解析器类
    """
    registry = _get_registry()
    registry.register(name, parser_class)
