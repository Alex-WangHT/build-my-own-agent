# AlexClaw AI Agent 开发任务清单

## 项目概述

AlexClaw 是一个基于 Python 构建的智能 AI Agent，支持多种 LLM Provider，实现对话、工具调用、记忆管理等功能。

***

## 已完成阶段

### 阶段1: 项目结构重构 ✅ 已完成

**目标**：建立规范的项目结构，便于后续开发和维护

**完成内容**：
- [x] 创建 `src/` 目录，存放所有代码相关文件
- [x] 保留 `doc/` 目录在根目录
- [x] 将 `chat.py` 移动到 `main.py`
- [x] 创建 `start.sh` 和 `start.bat` 启动脚本

**当前项目结构**：
```
build-my-own-agent/
├── doc/
│   └── TODOList.md          # 本文档
├── src/
│   ├── config/              # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── provider/            # LLM Provider 模块
│   │   ├── __init__.py
│   │   ├── base.py          # 抽象基类
│   │   ├── openai_compatible.py  # OpenAI 兼容基类
│   │   ├── siliconflow.py   # 硅基流动
│   │   ├── openai_provider.py  # OpenAI
│   │   ├── claude.py        # Claude (Anthropic)
│   │   ├── bigmodel.py      # 智谱AI
│   │   ├── deepseek.py      # Deepseek
│   │   ├── kimi.py          # Kimi (Moonshot)
│   │   ├── qwen.py          # 阿里千问
│   │   ├── openrouter.py    # Openrouter
│   │   └── registry.py      # Provider 注册表
│   ├── runtime/             # 运行时模块
│   │   ├── __init__.py
│   │   ├── simple_agent.py  # 简单 Agent
│   │   └── io/
│   │       ├── __init__.py
│   │       ├── adapter.py
│   │       └── base.py
│   ├── tool_call_parser/    # 工具调用解析器
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── parsers.py
│   │   └── registry.py
│   ├── tools/               # 工具模块
│   │   ├── __init__.py
│   │   └── tool.py
│   └── tui/                 # 终端界面
│       ├── __init__.py
│       ├── app.py
│       ├── components/
│       ├── io/
│       └── themes/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── start.sh
└── start.bat
```

### 阶段2: Provider 模块开发 ✅ 已完成

**目标**：为多个 AI 厂商创建统一的 Provider 类，实现灵活的 LLM 接口

**完成内容**：
- [x] 设计 `LLMProvider` 抽象基类
  - [x] 定义统一的 `chat()` 接口
  - [x] 定义数据类：`Message`, `FunctionCall`, `Usage`, `ChatCompletionChoice`, `ChatCompletionResponse`
  - [x] 定义异常类：`APIError`, `NetworkError`, `AuthenticationError`, `RateLimitError`, `ModelNotFoundError`
- [x] 实现 `OpenAICompatibleProvider` 基类
  - [x] 封装 HTTP 请求和重试机制
  - [x] 支持流式响应处理
  - [x] 实现工具调用解析
- [x] 实现各厂商 Provider：
  - [x] 硅基流动 (`SiliconFlowProvider`)
  - [x] OpenAI (`OpenAIProvider`)
  - [x] Deepseek (`DeepseekProvider`)
  - [x] Kimi (`KimiProvider`)
  - [x] 阿里千问 (`QwenProvider`)
  - [x] 智谱AI (`BigModelProvider`)
  - [x] Openrouter (`OpenrouterProvider`)
  - [x] Claude (`ClaudeProvider`) - 原生 API 实现
- [x] 实现 `ProviderRegistry` 单例注册表
  - [x] 自动注册所有 Provider
  - [x] 支持通过名称获取 Provider
- [x] 完善配置管理
  - [x] 为每个 Provider 添加配置项
  - [x] 支持多环境变量别名（如 `CLAUDE_API_KEY` / `ANTHROPIC_API_KEY`）
- [x] 单元测试
  - [x] 每个 Provider 文件包含完整测试套件
  - [x] 使用 `unittest.mock` 模拟外部依赖
  - [x] 修复导入路径问题

***

## 待完成阶段

### 阶段3: Provider 模块测试 ⏳ 待开始

**目标**：确保 Provider 模块的正确性和稳定性

**任务清单**：
- [ ] 运行所有 Provider 单元测试
  - [ ] 修复 `base.py` 中的 `test_from_dict_defaults` 测试
  - [ ] 验证各厂商 API 调用模拟
  - [ ] 检查异常处理逻辑
- [ ] 集成测试
  - [ ] 测试 Provider 注册表功能
  - [ ] 测试配置加载和多别名支持
  - [ ] 测试流式响应处理
- [ ] 边界条件测试
  - [ ] 空消息列表测试
  - [ ] 无效模型名称测试
  - [ ] 网络错误重试测试

### 阶段4: Runtime 模块重构与测试 ⏳ 待开始

**目标**：重构并完善运行时模块，实现 Agent 核心逻辑

**任务清单**：
- [ ] 分析现有 `runtime/` 结构
  - [ ] 审查 `simple_agent.py` 实现
  - [ ] 审查 `io/adapter.py` 和 `io/base.py`
- [ ] 重构 Runtime 架构
  - [ ] 定义 `BaseAgent` 抽象基类
  - [ ] 实现 `Agent` 核心类
  - [ ] 设计 Agent 生命周期管理
- [ ] 完善 IO 适配器
  - [ ] 统一输入输出接口
  - [ ] 支持多种 IO 后端（TUI、CLI、API）
- [ ] 单元测试
  - [ ] 测试 Agent 基本对话流程
  - [ ] 测试 IO 适配器
  - [ ] 测试异常处理

### 阶段5: Runtime 上下文管理 ⏳ 待开始

**目标**：实现对话上下文管理，支持多轮对话

**任务清单**：
- [ ] 设计上下文管理接口
  - [ ] 定义 `ContextManager` 抽象基类
  - [ ] 实现 `SimpleContextManager` 基础实现
- [ ] 上下文存储
  - [ ] 实现内存存储
  - [ ] 实现文件持久化存储（可选）
- [ ] 上下文策略
  - [ ] 实现 Token 计数和截断策略
  - [ ] 实现消息摘要和压缩策略
  - [ ] 实现重要消息保留策略
- [ ] 单元测试
  - [ ] 测试上下文添加和获取
  - [ ] 测试 Token 计数准确性
  - [ ] 测试截断策略边界条件

### 阶段6: Memory 模块 ⏳ 待开始

**目标**：实现记忆系统，支持短期和长期记忆

**任务清单**：
- [ ] 设计记忆系统架构
  - [ ] 区分短期记忆（对话上下文）和长期记忆（知识存储）
  - [ ] 定义 `Memory` 数据结构
- [ ] 实现短期记忆
  - [ ] 基于上下文管理扩展
  - [ ] 支持记忆摘要
- [ ] 实现长期记忆（可选）
  - [ ] 设计向量存储接口
  - [ ] 实现简单的文件存储后端
  - [ ] 实现记忆检索机制
- [ ] 记忆操作
  - [ ] 实现记忆添加、查询、删除
  - [ ] 实现记忆重要性评分
  - [ ] 实现记忆遗忘策略
- [ ] 单元测试
  - [ ] 测试记忆 CRUD 操作
  - [ ] 测试记忆检索准确性
  - [ ] 测试记忆遗忘策略

### 阶段7: Tool Call Parser 模块 ⏳ 待开始

**目标**：完善工具调用解析器，支持多种 LLM 的工具调用格式

**任务清单**：
- [ ] 分析现有实现
  - [ ] 审查 `base.py` 抽象基类
  - [ ] 审查 `parsers.py` 具体实现
  - [ ] 审查 `registry.py` 注册表
- [ ] 完善解析器实现
  - [ ] 实现 OpenAI 格式工具调用解析
  - [ ] 实现 Claude 格式工具调用解析
  - [ ] 实现通用格式解析（处理不同厂商差异）
- [ ] 实现工具调用执行器
  - [ ] 定义工具执行接口
  - [ ] 实现参数验证
  - [ ] 实现错误处理和重试
- [ ] 单元测试
  - [ ] 测试各种格式的工具调用解析
  - [ ] 测试参数验证逻辑
  - [ ] 测试执行器错误处理

### 阶段8: Tools 基类 ⏳ 待开始

**目标**：设计并实现工具基类，构建可扩展的工具系统

**任务清单**：
- [ ] 分析现有 `tools/tool.py`
- [ ] 设计工具系统架构
  - [ ] 定义 `BaseTool` 抽象基类
  - [ ] 定义工具元数据（名称、描述、参数、返回值）
  - [ ] 定义工具执行接口
- [ ] 实现工具基类功能
  - [ ] 参数验证（基于 schema）
  - [ ] 执行前/后钩子
  - [ ] 错误处理和日志
  - [ ] 执行超时控制
- [ ] 实现示例工具
  - [ ] 实现 `EchoTool`（回显工具）
  - [ ] 实现 `CalculatorTool`（计算工具）
  - [ ] 实现 `FileReadTool`（文件读取工具）
- [ ] 实现工具注册表
  - [ ] 支持工具自动发现
  - [ ] 支持工具动态加载
- [ ] 单元测试
  - [ ] 测试工具基类功能
  - [ ] 测试参数验证
  - [ ] 测试示例工具执行

### 阶段9: TUI 模块重构与测试 ⏳ 待开始

**目标**：重构并完善终端用户界面，提升用户体验

**任务清单**：
- [ ] 分析现有 TUI 结构
  - [ ] 审查 `app.py` 主应用
  - [ ] 审查 `components/` 组件
  - [ ] 审查 `io/tui_adapter.py` IO 适配器
  - [ ] 审查 `themes/` 主题系统
- [ ] 重构 TUI 架构
  - [ ] 优化组件通信
  - [ ] 完善消息渲染
  - [ ] 实现流式输出显示
- [ ] 增强功能
  - [ ] 支持 Markdown 渲染
  - [ ] 支持代码高亮
  - [ ] 实现命令历史
  - [ ] 实现快捷键支持
- [ ] 完善主题系统
  - [ ] 确保主题切换功能正常
  - [ ] 添加主题预览
- [ ] 单元测试
  - [ ] 测试组件渲染
  - [ ] 测试 IO 适配器
  - [ ] 测试主题切换

### 阶段10: AlexClaw MVP 集成 ⏳ 待开始

**目标**：完成 AlexClaw 的最小可行产品，实现完整的 Agent 功能

**任务清单**：
- [ ] 整合所有模块
  - [ ] 连接 Provider → Runtime → TUI
  - [ ] 集成 Memory 模块到 Runtime
  - [ ] 集成 Tool Call Parser 和 Tools 模块
- [ ] 实现核心 Agent 流程
  - [ ] 接收用户输入
  - [ ] 构建上下文（包含历史对话和记忆）
  - [ ] 调用 LLM Provider
  - [ ] 解析工具调用（如果有）
  - [ ] 执行工具
  - [ ] 将工具结果反馈给 LLM
  - [ ] 输出响应给用户
  - [ ] 更新上下文和记忆
- [ ] 实现配置集成
  - [ ] 支持从环境变量和 .env 文件加载配置
  - [ ] 支持命令行参数覆盖配置
  - [ ] 实现默认配置
- [ ] 端到端测试
  - [ ] 测试简单对话流程
  - [ ] 测试多轮对话上下文保持
  - [ ] 测试工具调用流程
  - [ ] 测试错误恢复能力
- [ ] 文档完善
  - [ ] 更新 README.md
  - [ ] 添加使用示例
  - [ ] 记录配置项说明

***

## 开发进度追踪

| 阶段             | 状态    | 开始日期       | 完成日期       | 备注                       |
| -------------- | ----- | ---------- | ---------- | ------------------------ |
| 阶段1: 项目结构重构    | ✅ 已完成 | 2026-04-29 | 2026-04-29 | 建立规范的 src/ 目录结构 |
| 阶段2: Provider 模块开发 | ✅ 已完成 | 2026-04-30 | 2026-05-01 | 8个厂商 Provider + 注册表 |
| 阶段3: Provider 模块测试 | ⏳ 待开始 | -          | -          | 单元测试和集成测试 |
| 阶段4: Runtime 重构与测试 | ⏳ 待开始 | -          | -          | Agent 核心逻辑 |
| 阶段5: Runtime 上下文管理 | ⏳ 待开始 | -          | -          | 多轮对话支持 |
| 阶段6: Memory 模块 | ⏳ 待开始 | -          | -          | 短期/长期记忆 |
| 阶段7: Tool Call Parser | ⏳ 待开始 | -          | -          | 工具调用解析 |
| 阶段8: Tools 基类 | ⏳ 待开始 | -          | -          | 可扩展工具系统 |
| 阶段9: TUI 重构与测试 | ⏳ 待开始 | -          | -          | 终端界面优化 |
| 阶段10: AlexClaw MVP | ⏳ 待开始 | -          | -          | 完整集成和端到端测试 |

***

## 技术栈

### 核心依赖

- **语言**: Python 3.10+
- **HTTP请求**: requests
- **TUI界面**: textual
- **配置管理**: python-dotenv, pydantic
- **数据类**: dataclasses (标准库)

### 开发工具

- **代码格式化**: black, ruff
- **类型检查**: mypy
- **测试**: unittest (标准库)
- **环境管理**: venv, conda

***

## 注意事项

1. **API Key安全**: 永远不要将API Key提交到版本控制，使用 .env 文件
2. **成本控制**: 注意API调用成本，设置合理的预算和模型选择
3. **错误处理**: 每个模块都要考虑完善的错误处理和异常捕获
4. **日志记录**: 完善的日志便于调试和问题定位
5. **代码质量**: 保持代码整洁，遵循类型提示，添加必要的文档字符串
6. **测试覆盖**: 每个新功能都要编写对应的单元测试
7. **安全意识**: 在处理Shell执行、文件操作、网络请求时要特别注意安全

***

## 参考资源

- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API 文档](https://docs.anthropic.com/)
- [硅基流动 API 文档](https://docs.siliconflow.cn/)
- [智谱AI 文档](https://docs.bigmodel.cn/)
- [Textual 文档](https://textual.textualize.io/)
- [Pydantic 文档](https://docs.pydantic.dev/)
