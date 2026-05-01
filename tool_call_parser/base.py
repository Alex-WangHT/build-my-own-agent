"""
Tool Call Parser 基础模块
定义数据模型和解析器接口
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Iterator


class ToolCallFormat(Enum):
    """工具调用格式枚举"""

    JSON = "json"
    XML_TOOL_CALL = "xml_tool_call"
    GLM_STYLE = "glm_style"
    MINIMAX_INVOKE = "minimax_invoke"
    PERL_STYLE = "perl_style"
    MARKDOWN_FENCE = "markdown_fence"
    OPENAI_NATIVE = "openai_native"
    REACT_STYLE = "react_style"
    UNKNOWN = "unknown"


@dataclass
class FunctionCall:
    """函数调用对象"""

    name: str
    arguments: str
    parsed_arguments: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "name": self.name,
            "arguments": self.arguments,
        }
        if self.parsed_arguments is not None:
            data["parsed_arguments"] = self.parsed_arguments
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunctionCall":
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            arguments=data.get("arguments", "{}"),
            parsed_arguments=data.get("parsed_arguments"),
        )

    @property
    def args(self) -> Dict[str, Any]:
        """获取解析后的参数（如果是有效的 JSON）"""
        if self.parsed_arguments is not None:
            return self.parsed_arguments
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return {}


@dataclass
class ToolCall:
    """工具调用对象"""

    id: Optional[str] = None
    type: str = "function"
    function: Optional[FunctionCall] = None
    format: ToolCallFormat = ToolCallFormat.UNKNOWN
    raw_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data: Dict[str, Any] = {
            "type": self.type,
            "format": self.format.value,
        }
        if self.id:
            data["id"] = self.id
        if self.function:
            data["function"] = self.function.to_dict()
        if self.raw_text:
            data["raw_text"] = self.raw_text
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """从字典创建"""
        function_data = data.get("function")
        function = FunctionCall.from_dict(function_data) if function_data else None

        format_str = data.get("format", "unknown")
        try:
            format_enum = ToolCallFormat(format_str)
        except ValueError:
            format_enum = ToolCallFormat.UNKNOWN

        return cls(
            id=data.get("id"),
            type=data.get("type", "function"),
            function=function,
            format=format_enum,
            raw_text=data.get("raw_text"),
        )

    @property
    def name(self) -> str:
        """获取函数名"""
        return self.function.name if self.function else ""

    @property
    def arguments(self) -> str:
        """获取参数字符串"""
        return self.function.arguments if self.function else "{}"

    @property
    def args(self) -> Dict[str, Any]:
        """获取解析后的参数"""
        return self.function.args if self.function else {}


@dataclass
class ParsedToolCalls:
    """解析结果集合"""

    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_response: str = ""
    has_tool_calls: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "raw_response": self.raw_response,
            "has_tool_calls": self.has_tool_calls,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParsedToolCalls":
        """从字典创建"""
        tool_calls_data = data.get("tool_calls", [])
        tool_calls = [ToolCall.from_dict(tc) for tc in tool_calls_data]

        return cls(
            tool_calls=tool_calls,
            raw_response=data.get("raw_response", ""),
            has_tool_calls=data.get("has_tool_calls", False),
        )

    def __iter__(self) -> Iterator[ToolCall]:
        """迭代工具调用"""
        return iter(self.tool_calls)

    def __len__(self) -> int:
        """工具调用数量"""
        return len(self.tool_calls)

    def __getitem__(self, index: int) -> ToolCall:
        """获取指定索引的工具调用"""
        return self.tool_calls[index]

    def first(self) -> Optional[ToolCall]:
        """获取第一个工具调用"""
        return self.tool_calls[0] if self.tool_calls else None


@dataclass
class ParseResult:
    """单次解析的结果"""

    success: bool
    tool_calls: List[ToolCall] = field(default_factory=list)
    format: ToolCallFormat = ToolCallFormat.UNKNOWN
    error_message: Optional[str] = None
    raw_match: Optional[str] = None


class ToolCallParser(ABC):
    """
    工具调用解析器接口
    所有解析器都必须实现此接口

    设计理念：
    - 不依赖任何外部状态
    - 纯文本转换
    - 可组合、可扩展
    """

    @property
    @abstractmethod
    def format(self) -> ToolCallFormat:
        """此解析器支持的格式"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """解析器名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """解析器描述"""
        pass

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """
        检查是否可以解析此文本

        Args:
            text: 要检查的文本

        Returns:
            是否可以解析
        """
        pass

    @abstractmethod
    def parse(self, text: str) -> ParseResult:
        """
        解析文本中的工具调用

        Args:
            text: 要解析的文本

        Returns:
            ParseResult 解析结果
        """
        pass

    def try_parse(self, text: str) -> ParseResult:
        """
        尝试解析，不抛出异常

        Args:
            text: 要解析的文本

        Returns:
            ParseResult 解析结果
        """
        try:
            return self.parse(text)
        except Exception as e:
            return ParseResult(
                success=False,
                format=self.format,
                error_message=str(e),
            )

    def _try_parse_json(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        尝试解析 JSON，失败时返回 None

        Args:
            json_str: JSON 字符串

        Returns:
            解析后的字典或 None
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
