"""
工具定义模块
实现ReAct Agent可以调用的各种工具
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    """
    工具定义
    封装一个工具函数的元信息和实现
    """

    name: str
    description: str
    func: Callable
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于LLM提示词"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
            },
        }

    def execute(self, **kwargs) -> str:
        """
        执行工具函数

        Args:
            **kwargs: 传递给工具函数的参数

        Returns:
            工具执行结果的字符串表示
        """
        try:
            result = self.func(**kwargs)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


class ToolRegistry:
    """
    工具注册表
    管理所有可用的工具
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """根据名称获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """获取所有已注册的工具"""
        return list(self._tools.values())

    def get_tools_description(self) -> str:
        """
        获取所有工具的描述，用于构建提示词

        Returns:
            格式化的工具描述字符串
        """
        descriptions = []
        for tool in self._tools.values():
            desc = f"Tool: {tool.name}\n"
            desc += f"Description: {tool.description}\n"
            if tool.parameters:
                desc += "Parameters:\n"
                for param_name, param_info in tool.parameters.items():
                    desc += f"  - {param_name}: {param_info.get('description', '')} (type: {param_info.get('type', 'string')})\n"
            descriptions.append(desc)
        return "\n".join(descriptions)


def calculator(expression: str) -> str:
    """
    计算器工具
    计算简单的数学表达式

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4"

    Returns:
        计算结果
    """
    try:
        safe_pattern = r'^[\d\s+\-*/().]+$'
        if not re.match(safe_pattern, expression):
            return "Error: Invalid expression. Only numbers and basic operators (+, -, *, /, (, )) are allowed."

        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


def get_current_time(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间

    Args:
        format: 时间格式，默认为 "%Y-%m-%d %H:%M:%S"

    Returns:
        当前时间字符串
    """
    try:
        now = datetime.now()
        return now.strftime(format)
    except Exception as e:
        return f"Error: {str(e)}"


def web_search(query: str) -> str:
    """
    模拟网页搜索工具

    Args:
        query: 搜索查询

    Returns:
        模拟的搜索结果
    """
    mock_results = {
        "Python": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。它以其简洁的语法和强大的功能而闻名，广泛用于Web开发、数据科学、人工智能等领域。",
        "人工智能": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。这包括学习、推理、问题解决、语言理解和视觉感知等能力。",
        "天气": "要获取当前天气，请使用get_weather工具。",
        "时间": "要获取当前时间，请使用get_current_time工具。",
    }

    for key, value in mock_results.items():
        if key.lower() in query.lower():
            return f"Search results for '{query}':\n{value}"

    return f"Search results for '{query}':\n未找到相关信息。这是一个模拟的搜索工具，实际应用中需要接入真实的搜索引擎API。"


def get_weather(city: str) -> str:
    """
    模拟获取天气信息

    Args:
        city: 城市名称

    Returns:
        模拟的天气信息
    """
    mock_weather = {
        "北京": "北京今日天气：晴，温度 15-25°C，微风，空气质量良好。",
        "上海": "上海今日天气：多云，温度 18-28°C，东南风 3-4级，湿度 65%。",
        "广州": "广州今日天气：阵雨，温度 22-30°C，南风 2级，湿度 80%。",
        "深圳": "深圳今日天气：雷阵雨，温度 24-31°C，西南风 3级，湿度 85%。",
    }

    weather = mock_weather.get(city)
    if weather:
        return f"Weather in {city}:\n{weather}"
    return f"Weather in {city}:\n未找到该城市的天气信息。这是一个模拟的天气工具，实际应用中需要接入真实的天气API。"


def create_default_registry() -> ToolRegistry:
    """
    创建默认的工具注册表

    Returns:
        包含所有默认工具的注册表
    """
    registry = ToolRegistry()

    calculator_tool = Tool(
        name="calculator",
        description="计算数学表达式。支持基本的加减乘除运算，例如 '2 + 3 * 4' 或 '(10 - 5) / 2'。",
        func=calculator,
        parameters={
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式",
            }
        },
        required=["expression"],
    )
    registry.register(calculator_tool)

    time_tool = Tool(
        name="get_current_time",
        description="获取当前时间和日期。可以指定时间格式，默认为 'YYYY-MM-DD HH:MM:SS' 格式。",
        func=get_current_time,
        parameters={
            "format": {
                "type": "string",
                "description": "时间格式字符串，例如 '%Y-%m-%d %H:%M:%S'",
            }
        },
        required=[],
    )
    registry.register(time_tool)

    search_tool = Tool(
        name="web_search",
        description="搜索网络信息。用于查找关于特定主题的信息、事实、定义等。",
        func=web_search,
        parameters={
            "query": {
                "type": "string",
                "description": "搜索查询",
            }
        },
        required=["query"],
    )
    registry.register(search_tool)

    weather_tool = Tool(
        name="get_weather",
        description="获取指定城市的天气信息。包括温度、天气状况、风力等。",
        func=get_weather,
        parameters={
            "city": {
                "type": "string",
                "description": "城市名称",
            }
        },
        required=["city"],
    )
    registry.register(weather_tool)

    return registry


default_registry = create_default_registry()
