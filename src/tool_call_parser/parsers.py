"""
Tool Call Parser 实现
各种格式的工具调用解析器
"""

import json
import re
from typing import List, Optional, Dict, Any

from tool_call_parser.base import (
    ToolCallParser,
    ToolCall,
    FunctionCall,
    ParseResult,
    ToolCallFormat,
)


class JSONParser(ToolCallParser):
    """
    JSON 格式解析器
    解析直接的 JSON 对象或数组

    支持的格式示例：
    {"name": "get_weather", "arguments": {"city": "北京"}}
    [{"name": "get_weather", "arguments": {"city": "北京"}}]
    """

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.JSON

    @property
    def name(self) -> str:
        return "json"

    @property
    def description(self) -> str:
        return "解析直接的 JSON 对象或数组格式的工具调用"

    def can_parse(self, text: str) -> bool:
        text = text.strip()
        if not text:
            return False
        if text.startswith("{") and text.endswith("}"):
            return True
        if text.startswith("[") and text.endswith("]"):
            return True
        return False

    def parse(self, text: str) -> ParseResult:
        text = text.strip()

        if not self.can_parse(text):
            return ParseResult(
                success=False,
                format=self.format,
                error_message="Not a valid JSON format",
            )

        parsed = self._try_parse_json(text)
        if parsed is None:
            return ParseResult(
                success=False,
                format=self.format,
                error_message="Invalid JSON",
            )

        tool_calls: List[ToolCall] = []

        if isinstance(parsed, dict):
            tc = self._dict_to_tool_call(parsed)
            if tc:
                tool_calls.append(tc)
        elif isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    tc = self._dict_to_tool_call(item)
                    if tc:
                        tool_calls.append(tc)

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=text if tool_calls else None,
        )

    def _dict_to_tool_call(self, data: Dict[str, Any]) -> Optional[ToolCall]:
        """将字典转换为 ToolCall 对象"""
        if "name" in data:
            name = str(data["name"])
            arguments = data.get("arguments", {})
            if isinstance(arguments, dict):
                arguments_str = json.dumps(arguments, ensure_ascii=False)
            else:
                arguments_str = str(arguments)
                if not (arguments_str.startswith("{") and arguments_str.endswith("}")):
                    arguments_str = json.dumps({"input": arguments_str}, ensure_ascii=False)

            parsed_args = self._try_parse_json(arguments_str)

            return ToolCall(
                id=data.get("id"),
                type=data.get("type", "function"),
                function=FunctionCall(
                    name=name,
                    arguments=arguments_str,
                    parsed_arguments=parsed_args,
                ),
                format=self.format,
            )
        elif "function" in data:
            func_data = data.get("function", {})
            if isinstance(func_data, dict) and "name" in func_data:
                name = str(func_data["name"])
                arguments = func_data.get("arguments", {})
                if isinstance(arguments, dict):
                    arguments_str = json.dumps(arguments, ensure_ascii=False)
                else:
                    arguments_str = str(arguments)

                parsed_args = self._try_parse_json(arguments_str)

                return ToolCall(
                    id=data.get("id"),
                    type=data.get("type", "function"),
                    function=FunctionCall(
                        name=name,
                        arguments=arguments_str,
                        parsed_arguments=parsed_args,
                    ),
                    format=self.format,
                )

        return None


class XMLToolCallParser(ToolCallParser):
    """
    XML <tool_call> 标签解析器

    支持的格式示例：
    <tool_call>
    {"name": "get_weather", "arguments": {"city": "北京"}}
    </tool_call>

    <|FunctionCallBegin|>
    {"name": "get_weather", "arguments": {"city": "北京"}}
    <|FunctionCallEnd|>
    """

    TOOL_CALL_PATTERN = re.compile(
        r"<tool_call>(.*?)</tool_call>",
        re.DOTALL | re.IGNORECASE,
    )

    FUNCTION_CALL_PATTERN = re.compile(
        r"<\|FunctionCallBegin\|>(.*?)<\|FunctionCallEnd\|>",
        re.DOTALL,
    )

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.XML_TOOL_CALL

    @property
    def name(self) -> str:
        return "xml_tool_call"

    @property
    def description(self) -> str:
        return "解析 XML <tool_call> 标签格式的工具调用"

    def can_parse(self, text: str) -> bool:
        if "<tool_call>" in text.lower() and "</tool_call>" in text.lower():
            return True
        if "<|FunctionCallBegin|>" in text and "<|FunctionCallEnd|>" in text:
            return True
        return False

    def parse(self, text: str) -> ParseResult:
        tool_calls: List[ToolCall] = []
        raw_matches: List[str] = []

        for match in self.TOOL_CALL_PATTERN.finditer(text):
            content = match.group(1).strip()
            parsed = self._try_parse_json(content)
            if parsed is not None:
                tc = self._json_to_tool_call(parsed)
                if tc:
                    tool_calls.append(tc)
                    raw_matches.append(match.group(0))

        for match in self.FUNCTION_CALL_PATTERN.finditer(text):
            content = match.group(1).strip()
            parsed = self._try_parse_json(content)
            if parsed is not None:
                tc = self._json_to_tool_call(parsed)
                if tc:
                    tool_calls.append(tc)
                    raw_matches.append(match.group(0))

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=raw_matches[0] if raw_matches else None,
        )

    def _json_to_tool_call(self, data: Dict[str, Any]) -> Optional[ToolCall]:
        if isinstance(data, dict):
            if "name" in data:
                name = str(data["name"])
                arguments = data.get("arguments", {})
                if isinstance(arguments, dict):
                    arguments_str = json.dumps(arguments, ensure_ascii=False)
                else:
                    arguments_str = json.dumps(arguments, ensure_ascii=False)

                parsed_args = self._try_parse_json(arguments_str)

                return ToolCall(
                    id=data.get("id"),
                    type=data.get("type", "function"),
                    function=FunctionCall(
                        name=name,
                        arguments=arguments_str,
                        parsed_arguments=parsed_args,
                    ),
                    format=self.format,
                )

        return None


class GLMStyleParser(ToolCallParser):
    """
    GLM 风格简化语法解析器

    支持的格式示例：
    get_weather
    北京

    get_weather
    {"city": "北京"}
    """

    GLM_PATTERN = re.compile(
        r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*$\s*(\{.*?\}|[^}]+?)(?=\n\n|$)",
        re.DOTALL | re.MULTILINE,
    )

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.GLM_STYLE

    @property
    def name(self) -> str:
        return "glm_style"

    @property
    def description(self) -> str:
        return "解析 GLM 风格简化语法的工具调用（函数名换行参数）"

    def can_parse(self, text: str) -> bool:
        lines = text.strip().split("\n")
        if len(lines) >= 2:
            first_line = lines[0].strip()
            if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", first_line):
                if first_line.lower() not in ["thought", "action", "observation", "final"]:
                    return True
        return False

    def parse(self, text: str) -> ParseResult:
        tool_calls: List[ToolCall] = []
        lines = text.strip().split("\n")

        if len(lines) < 2:
            return ParseResult(
                success=False,
                format=self.format,
                error_message="Not enough lines for GLM style",
            )

        name = lines[0].strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            return ParseResult(
                success=False,
                format=self.format,
                error_message=f"Invalid function name: {name}",
            )

        arguments_str = "\n".join(lines[1:]).strip()
        parsed_args = self._try_parse_json(arguments_str)

        if parsed_args is None:
            parsed_args = {"input": arguments_str}
            arguments_str = json.dumps(parsed_args, ensure_ascii=False)

        tool_calls.append(
            ToolCall(
                type="function",
                function=FunctionCall(
                    name=name,
                    arguments=arguments_str,
                    parsed_arguments=parsed_args,
                ),
                format=self.format,
                raw_match=text.strip(),
            )
        )

        return ParseResult(
            success=True,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=text.strip(),
        )


class MiniMaxInvokeParser(ToolCallParser):
    """
    MiniMax <invoke> 块解析器

    支持的格式示例：
    <invoke>get_weather</invoke>
    <invoke_params>{"city": "北京"}</invoke_params>
    """

    INVOKE_PATTERN = re.compile(
        r"<invoke>([^<]+)</invoke>\s*<invoke_params>(\{.*?\})</invoke_params>",
        re.DOTALL | re.IGNORECASE,
    )

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.MINIMAX_INVOKE

    @property
    def name(self) -> str:
        return "minimax_invoke"

    @property
    def description(self) -> str:
        return "解析 MiniMax <invoke> 块格式的工具调用"

    def can_parse(self, text: str) -> bool:
        return "<invoke>" in text.lower() and "<invoke_params>" in text.lower()

    def parse(self, text: str) -> ParseResult:
        tool_calls: List[ToolCall] = []
        raw_matches: List[str] = []

        for match in self.INVOKE_PATTERN.finditer(text):
            name = match.group(1).strip()
            params_str = match.group(2).strip()

            parsed_args = self._try_parse_json(params_str)
            if parsed_args is None:
                parsed_args = {"params": params_str}
                params_str = json.dumps(parsed_args, ensure_ascii=False)

            tool_calls.append(
                ToolCall(
                    type="function",
                    function=FunctionCall(
                        name=name,
                        arguments=params_str,
                        parsed_arguments=parsed_args,
                    ),
                    format=self.format,
                )
            )
            raw_matches.append(match.group(0))

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=raw_matches[0] if raw_matches else None,
        )


class PerlStyleParser(ToolCallParser):
    """
    Perl 风格 [TOOL_CALL] 块解析器

    支持的格式示例：
    [TOOL_CALL]
    Function: get_weather
    Parameters: {"city": "北京"}
    [/TOOL_CALL]
    """

    TOOL_CALL_BLOCK_PATTERN = re.compile(
        r"\[TOOL_CALL\](.*?)\[/TOOL_CALL\]",
        re.DOTALL | re.IGNORECASE,
    )

    FUNCTION_PATTERN = re.compile(r"Function:\s*(\w+)", re.IGNORECASE)
    PARAMETERS_PATTERN = re.compile(r"Parameters:\s*(\{.*?\})", re.DOTALL | re.IGNORECASE)

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.PERL_STYLE

    @property
    def name(self) -> str:
        return "perl_style"

    @property
    def description(self) -> str:
        return "解析 Perl 风格 [TOOL_CALL] 块格式的工具调用"

    def can_parse(self, text: str) -> bool:
        return "[TOOL_CALL]" in text.upper() and "[/TOOL_CALL]" in text.upper()

    def parse(self, text: str) -> ParseResult:
        tool_calls: List[ToolCall] = []
        raw_matches: List[str] = []

        for match in self.TOOL_CALL_BLOCK_PATTERN.finditer(text):
            block_content = match.group(1)

            func_match = self.FUNCTION_PATTERN.search(block_content)
            if func_match:
                name = func_match.group(1)

                params_match = self.PARAMETERS_PATTERN.search(block_content)
                if params_match:
                    params_str = params_match.group(1).strip()
                else:
                    params_str = "{}"

                parsed_args = self._try_parse_json(params_str)
                if parsed_args is None:
                    parsed_args = {"input": params_str}
                    params_str = json.dumps(parsed_args, ensure_ascii=False)

                tool_calls.append(
                    ToolCall(
                        type="function",
                        function=FunctionCall(
                            name=name,
                            arguments=params_str,
                            parsed_arguments=parsed_args,
                        ),
                        format=self.format,
                    )
                )
                raw_matches.append(match.group(0))

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=raw_matches[0] if raw_matches else None,
        )


class MarkdownFenceParser(ToolCallParser):
    """
    Markdown 代码块解析器

    支持的格式示例：
    ```json
    {"name": "get_weather", "arguments": {"city": "北京"}}
    ```

    ```tool_call
    {"name": "get_weather", "arguments": {"city": "北京"}}
    ```
    """

    CODE_BLOCK_PATTERN = re.compile(
        r"```(?:json|tool_call|function)?\s*$\s*(\{.*?\})\s*$```",
        re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.MARKDOWN_FENCE

    @property
    def name(self) -> str:
        return "markdown_fence"

    @property
    def description(self) -> str:
        return "解析 Markdown 代码块格式的工具调用"

    def can_parse(self, text: str) -> bool:
        return "```" in text

    def parse(self, text: str) -> ParseResult:
        tool_calls: List[ToolCall] = []
        raw_matches: List[str] = []

        for match in self.CODE_BLOCK_PATTERN.finditer(text):
            json_content = match.group(1).strip()
            parsed = self._try_parse_json(json_content)

            if parsed is not None:
                if isinstance(parsed, dict) and "name" in parsed:
                    name = str(parsed["name"])
                    arguments = parsed.get("arguments", {})
                    if isinstance(arguments, dict):
                        arguments_str = json.dumps(arguments, ensure_ascii=False)
                    else:
                        arguments_str = json.dumps(arguments, ensure_ascii=False)

                    parsed_args = self._try_parse_json(arguments_str)

                    tool_calls.append(
                        ToolCall(
                            id=parsed.get("id"),
                            type=parsed.get("type", "function"),
                            function=FunctionCall(
                                name=name,
                                arguments=arguments_str,
                                parsed_arguments=parsed_args,
                            ),
                            format=self.format,
                        )
                    )
                    raw_matches.append(match.group(0))

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=raw_matches[0] if raw_matches else None,
        )


class OpenAINativeParser(ToolCallParser):
    """
    OpenAI 原生格式解析器

    支持的格式示例：
    {
      "tool_calls": [
        {
          "id": "call_xxx",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"city\": \"北京\"}"
          }
        }
      ]
    }
    """

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.OPENAI_NATIVE

    @property
    def name(self) -> str:
        return "openai_native"

    @property
    def description(self) -> str:
        return "解析 OpenAI 原生格式的工具调用"

    def can_parse(self, text: str) -> bool:
        text = text.strip()
        if text.startswith("{") and "tool_calls" in text:
            return True
        return False

    def parse(self, text: str) -> ParseResult:
        text = text.strip()

        if not self.can_parse(text):
            return ParseResult(
                success=False,
                format=self.format,
                error_message="Not OpenAI native format",
            )

        parsed = self._try_parse_json(text)
        if parsed is None:
            return ParseResult(
                success=False,
                format=self.format,
                error_message="Invalid JSON",
            )

        tool_calls: List[ToolCall] = []

        tool_calls_data = parsed.get("tool_calls", [])
        if isinstance(tool_calls_data, list):
            for tc_data in tool_calls_data:
                if isinstance(tc_data, dict):
                    func_data = tc_data.get("function", {})
                    if isinstance(func_data, dict) and "name" in func_data:
                        name = str(func_data["name"])
                        arguments_str = func_data.get("arguments", "{}")
                        if not isinstance(arguments_str, str):
                            arguments_str = json.dumps(arguments_str, ensure_ascii=False)

                        parsed_args = self._try_parse_json(arguments_str)

                        tool_calls.append(
                            ToolCall(
                                id=tc_data.get("id"),
                                type=tc_data.get("type", "function"),
                                function=FunctionCall(
                                    name=name,
                                    arguments=arguments_str,
                                    parsed_arguments=parsed_args,
                                ),
                                format=self.format,
                            )
                        )

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=text if tool_calls else None,
        )


class ReActStyleParser(ToolCallParser):
    """
    ReAct 风格解析器

    支持的格式示例：
    Action: get_weather
    Action Input: {"city": "北京"}
    """

    ACTION_PATTERN = re.compile(
        r"Action:\s*(.+?)(?:\n|$)(?:Action Input:\s*(.+?))?(?=\n(?:Action|Thought|Observation|Final Answer):|$)",
        re.DOTALL | re.IGNORECASE,
    )

    @property
    def format(self) -> ToolCallFormat:
        return ToolCallFormat.REACT_STYLE

    @property
    def name(self) -> str:
        return "react_style"

    @property
    def description(self) -> str:
        return "解析 ReAct 风格的工具调用（Action/Action Input）"

    def can_parse(self, text: str) -> bool:
        return "Action:" in text

    def parse(self, text: str) -> ParseResult:
        tool_calls: List[ToolCall] = []
        raw_matches: List[str] = []

        for match in self.ACTION_PATTERN.finditer(text):
            name = match.group(1).strip()
            action_input = match.group(2).strip() if match.group(2) else "{}"

            parsed_args = self._try_parse_json(action_input)
            if parsed_args is None:
                parsed_args = {"input": action_input}
                action_input = json.dumps(parsed_args, ensure_ascii=False)

            tool_calls.append(
                ToolCall(
                    type="function",
                    function=FunctionCall(
                        name=name,
                        arguments=action_input,
                        parsed_arguments=parsed_args,
                    ),
                    format=self.format,
                )
            )
            raw_matches.append(match.group(0))

        return ParseResult(
            success=len(tool_calls) > 0,
            tool_calls=tool_calls,
            format=self.format,
            raw_match=raw_matches[0] if raw_matches else None,
        )
