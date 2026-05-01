"""
ReAct对话Agent模块
实现ReAct方式的工具调用和推理
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Iterator, Callable

from config.settings import Settings, get_settings
from llm.client import (
    SiliconFlowClient,
    Message,
    APIError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
)
from tools.tool import Tool, ToolRegistry, default_registry

logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """对话历史管理"""

    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_tokens: int = 0

    def add_message(self, role: str, content: str, name: str = None):
        """添加消息"""
        message = Message(role=role, content=content, name=name)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("assistant", content)

    def add_system_message(self, content: str):
        """添加系统消息"""
        self.add_message("system", content)

    def clear(self):
        """清空对话历史"""
        self.messages = []
        self.total_tokens = 0

    def get_recent_messages(self, max_count: int = None) -> List[Message]:
        """获取最近的消息"""
        if max_count is None or len(self.messages) <= max_count:
            return self.messages.copy()
        return self.messages[-max_count:].copy()

    def truncate_by_tokens(self, max_tokens: int, approx_tokens_per_char: float = 0.5) -> List[Message]:
        """
        按Token数截断消息历史（近似估计）
        """
        if not self.messages:
            return []

        result = []
        total_chars = 0

        system_messages = [m for m in self.messages if m.role == "system"]
        non_system_messages = [m for m in self.messages if m.role != "system"]

        result.extend(system_messages)
        for msg in system_messages:
            total_chars += len(msg.content)

        for msg in reversed(non_system_messages):
            msg_chars = len(msg.content)
            estimated_tokens = (total_chars + msg_chars) * approx_tokens_per_char

            if estimated_tokens > max_tokens and result:
                break

            result.insert(len(system_messages), msg)
            total_chars += msg_chars

        return result

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """从字典创建"""
        messages_data = data.get("messages", [])
        messages = [Message.from_dict(m) for m in messages_data]

        created_at = data.get("created_at")
        if created_at:
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()

        updated_at = data.get("updated_at")
        if updated_at:
            updated_at = datetime.fromisoformat(updated_at)
        else:
            updated_at = datetime.now()

        return cls(
            messages=messages,
            created_at=created_at,
            updated_at=updated_at,
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class ReActStep:
    """
    ReAct思考步骤
    记录每一步的思考、行动和观察
    """

    thought: str
    action: str = None
    action_input: Dict[str, Any] = field(default_factory=dict)
    observation: str = None


REACT_SYSTEM_PROMPT = """你是一个有用的AI助手，能够通过思考和行动来解决问题。

你可以使用以下工具来帮助回答问题：
{tools_description}

请按照以下格式进行思考和行动：

1. 首先思考当前需要做什么（Thought）
2. 如果需要使用工具，指定要使用的工具名称（Action）和参数（Action Input）
   - Action Input必须是一个有效的JSON对象
3. 等待工具执行结果（Observation）
4. 重复上述步骤直到你能够回答用户的问题
5. 最后给出最终答案（Final Answer）

格式示例：
Thought: 用户想知道2+3等于多少，我需要使用计算器工具。
Action: calculator
Action Input: {{\"expression\": \"2 + 3\"}}

（系统执行工具后会返回Observation）

Thought: 计算器返回了结果5，现在我可以给出最终答案了。
Final Answer: 2 + 3 = 5

重要规则：
- 如果你不确定答案，或者需要更多信息，请使用工具
- 每个Action之后必须等待Observation才能继续
- 当你有足够信息时，直接使用Final Answer结束
- Action Input必须是合法的JSON格式，不要有多余的文本

现在请回答用户的问题。"""


class ReActAgent:
    """
    ReAct方式的对话Agent
    实现"思考-行动-观察"的循环推理
    """

    def __init__(
        self,
        system_prompt: str = None,
        model: str = None,
        settings: Settings = None,
        tool_registry: ToolRegistry = None,
        max_iterations: int = 10,
    ):
        """
        初始化ReAct Agent

        Args:
            system_prompt: 系统提示词（可选）
            model: 使用的模型
            settings: 配置实例
            tool_registry: 工具注册表（如果不提供则使用默认注册表）
            max_iterations: 最大迭代次数，防止无限循环
        """
        self._settings = settings or get_settings()
        self._model = model or self._settings.siliconflow_model
        self._tool_registry = tool_registry or default_registry
        self._max_iterations = max_iterations

        self._client = SiliconFlowClient(settings=self._settings)
        self._conversation = Conversation()

        tools_description = self._tool_registry.get_tools_description()
        base_system_prompt = REACT_SYSTEM_PROMPT.format(tools_description=tools_description)

        if system_prompt:
            full_system_prompt = f"{system_prompt}\n\n{base_system_prompt}"
        else:
            full_system_prompt = base_system_prompt

        self._conversation.add_system_message(full_system_prompt)

        logger.info(f"ReActAgent initialized with model: {self._model}")
        logger.info(f"Registered tools: {[t.name for t in self._tool_registry.list_tools()]}")

    @property
    def conversation(self) -> Conversation:
        """获取对话历史"""
        return self._conversation

    @property
    def model(self) -> str:
        """获取当前模型"""
        return self._model

    @model.setter
    def model(self, value: str):
        """设置模型"""
        self._model = value
        logger.info(f"Model changed to: {value}")

    def _parse_action(self, text: str) -> Dict[str, Any]:
        """
        解析LLM输出中的Action和Action Input

        Args:
            text: LLM的输出文本

        Returns:
            包含action和action_input的字典，如果没有Action则返回None
        """
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text)
        action_input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text, re.DOTALL)

        if action_match:
            action = action_match.group(1).strip()

            action_input = {}
            if action_input_match:
                try:
                    action_input_str = action_input_match.group(1).strip()
                    action_input = json.loads(action_input_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse Action Input as JSON: {action_input_match.group(1)}")
                    action_input = {"raw_input": action_input_match.group(1).strip()}

            return {
                "action": action,
                "action_input": action_input,
            }

        return None

    def _parse_final_answer(self, text: str) -> Optional[str]:
        """
        解析LLM输出中的Final Answer

        Args:
            text: LLM的输出文本

        Returns:
            Final Answer的内容，如果没有则返回None
        """
        final_answer_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
        if final_answer_match:
            return final_answer_match.group(1).strip()
        return None

    def _execute_tool(self, action: str, action_input: Dict[str, Any]) -> str:
        """
        执行工具

        Args:
            action: 工具名称
            action_input: 工具参数

        Returns:
            工具执行结果
        """
        tool = self._tool_registry.get(action)
        if tool is None:
            return f"Error: Tool '{action}' not found. Available tools: {[t.name for t in self._tool_registry.list_tools()]}"

        logger.info(f"Executing tool: {action} with input: {action_input}")

        try:
            result = tool.execute(**action_input)
            logger.info(f"Tool result: {result[:100] if len(result) > 100 else result}")
            return result
        except Exception as e:
            error_msg = f"Error executing tool '{action}': {str(e)}"
            logger.error(error_msg)
            return error_msg

    def chat(
        self,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None,
        on_thought: Callable[[str], None] = None,
        on_action: Callable[[str, Dict[str, Any]], None] = None,
        on_observation: Callable[[str, str], None] = None,
        on_final_answer: Callable[[str], None] = None,
        **kwargs,
    ) -> str:
        """
        使用ReAct方式进行对话

        Args:
            user_message: 用户消息
            temperature: 生成温度
            max_tokens: 最大生成Token数
            on_thought: 回调函数，当LLM输出思考内容时调用，参数为思考内容
            on_action: 回调函数，当检测到Action时调用，参数为(action_name, action_input)
            on_observation: 回调函数，当工具执行完成时调用，参数为(action_name, observation)
            on_final_answer: 回调函数，当找到Final Answer时调用，参数为最终答案
            **kwargs: 其他参数

        Returns:
            最终答案
        """
        logger.debug(f"User message: {user_message[:100]}...")

        self._conversation.add_user_message(user_message)

        iterations = 0

        while iterations < self._max_iterations:
            iterations += 1
            logger.info(f"ReAct iteration {iterations}/{self._max_iterations}")

            try:
                messages = self._conversation.truncate_by_tokens(
                    max_tokens=self._settings.max_history_tokens
                )

                response = self._client.chat(
                    messages=messages,
                    model=self._model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                assistant_message = response.content

                self._conversation.add_assistant_message(assistant_message)
                logger.debug(f"LLM response: {assistant_message[:200] if len(assistant_message) > 200 else assistant_message}")

                if on_thought:
                    on_thought(assistant_message)

                final_answer = self._parse_final_answer(assistant_message)
                if final_answer:
                    logger.info(f"Final answer found after {iterations} iterations")
                    if on_final_answer:
                        on_final_answer(final_answer)
                    return final_answer

                action_info = self._parse_action(assistant_message)
                if action_info:
                    action = action_info["action"]
                    action_input = action_info["action_input"]

                    if on_action:
                        on_action(action, action_input)

                    observation = self._execute_tool(action, action_input)

                    if on_observation:
                        on_observation(action, observation)

                    observation_message = f"Observation: {observation}"
                    self._conversation.add_user_message(observation_message)

                    logger.debug(f"Observation: {observation[:200] if len(observation) > 200 else observation}")
                else:
                    logger.warning("No Action or Final Answer found in response, continuing...")
                    if "Final Answer" in assistant_message:
                        final_answer = assistant_message.split("Final Answer:")[-1].strip()
                        if on_final_answer:
                            on_final_answer(final_answer)
                        return final_answer

            except Exception as e:
                logger.exception(f"Error in ReAct iteration: {e}")
                raise

        max_iter_msg = f"已达到最大迭代次数 ({self._max_iterations})，无法完成推理。请尝试简化问题或增加max_iterations。"
        logger.warning(max_iter_msg)
        return max_iter_msg

    def chat_stream(
        self,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None,
        on_thought: Callable[[str], None] = None,
        on_action: Callable[[str, Dict[str, Any]], None] = None,
        on_observation: Callable[[str, str], None] = None,
        on_final_answer: Callable[[str], None] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        ReAct方式的流式对话

        Args:
            user_message: 用户消息
            temperature: 生成温度
            max_tokens: 最大生成Token数
            on_thought: 回调函数，当LLM输出思考内容时调用，参数为思考内容
            on_action: 回调函数，当检测到Action时调用，参数为(action_name, action_input)
            on_observation: 回调函数，当工具执行完成时调用，参数为(action_name, observation)
            on_final_answer: 回调函数，当找到Final Answer时调用，参数为最终答案
            **kwargs: 其他参数

        Yields:
            每次返回的内容片段
        """
        logger.debug(f"User message (stream): {user_message[:100]}...")

        final_answer = self.chat(
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
            on_thought=on_thought,
            on_action=on_action,
            on_observation=on_observation,
            on_final_answer=on_final_answer,
            **kwargs,
        )

        for char in final_answer:
            yield char

    def clear_history(self):
        """清空对话历史（保留系统提示词）"""
        system_messages = [m for m in self._conversation.messages if m.role == "system"]
        self._conversation.clear()
        for msg in system_messages:
            self._conversation.add_message(msg.role, msg.content, msg.name)
        logger.info("Conversation history cleared (system prompt preserved)")

    def get_history_summary(self) -> Dict[str, Any]:
        """获取对话历史摘要"""
        return {
            "message_count": len(self._conversation.messages),
            "total_tokens": self._conversation.total_tokens,
            "created_at": self._conversation.created_at.isoformat(),
            "updated_at": self._conversation.updated_at.isoformat(),
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表

        Returns:
            工具列表
        """
        return [tool.to_dict() for tool in self._tool_registry.list_tools()]

    def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表

        Returns:
            模型列表
        """
        return self._client.list_models()

    def close(self):
        """关闭资源"""
        self._client.close()
        logger.info("ReActAgent closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
