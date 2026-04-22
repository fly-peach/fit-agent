| # Phase 09: AI 教练优化与多模态数据导入（Qwen 对齐版）
| > 阶段目标：在现有 `Rogers/app/agent` 基础上升级为 `LangChain 1.x + qwen3.5-plus` 的多模态 Agent，前端对齐 qwenpaw 的对话体验（附件上传、工具调用过程、图片渲染、审批确认）。
| ## 1. 现状基线（必须先对齐）
| ### 1.1 后端现状（`Rogers/app/agent`）
| 当前代码已经具备审批闭环，但仍是规则驱动，尚未接入真实 LLM 多模态链路：
| - `service/agent_service.py`
| - 通过关键词分支处理问答与趋势分析。
| - 可创建 `PendingAction` 并在 `approve` 时调用写工具落库。
| - 输入仅 `message + session_id`，无附件字段。
| - `tools/read_tools.py`
| - 已有健康、训练、营养、仪表盘读取能力。
| - `tools/write_tools.py`
| - 已有三类写库工具（metrics/workout/nutrition），适合继续作为审批执行端。
| - `schemas/agent.py`
| - 仅定义文本聊天与审批 DTO，暂不支持 `attachments`。
| - 当前结论
| - 审批机制可复用。
| - LLM 编排层、多模态工具层、附件协议层需要补齐。
| ### 1.2 前端对齐目标（参考 `CoPaw/console/src/pages/Chat`）
| qwenpaw 这套 Chat 页面有三类关键能力需要对齐：
| - 多模态能力感知：根据模型能力决定上传提示与可用性。
| - 附件上传链路：上传、URL 归一化、消息内渲染（图片预览）。
| - 工具过程可视化：用户可看到识别中 -> 结构化结果 -> 待审批 -> 执行结果。
| ## 2. 模型与配置约束
| 统一使用你已配置的 `.env` 参数：
| ```dotenv
| DashScope_coding_URL=https://coding.dashscope.aliyuncs.com/v1
| DashScope_coding_API_KEY=***
| model=qwen3.5-plus
| ```
| 约束：
| - 不引入 OpenAI 官方 SDK，不依赖 `gpt-*` / `whisper-*`。
| - 使用 OpenAI 兼容协议方式连接 DashScope（`langchain-openai` 客户端）。
| - 代码中禁止硬编码密钥、URL、模型名。
| ## 3. 后端设计（围绕 `Rogers/app/agent` 演进）
| ### 3.1 目标分层
| 在不破坏现有审批逻辑前提下，拆分为 4 层：
| 1. `Agent Orchestrator`（会话编排）
| - 接收文本/图片输入，组织消息上下文，调度 LangChain Agent。
| 2. `Tool Layer`（读写与多模态工具）
| - `read_tools.py`：继续保留。
| - `write_tools.py`：继续保留，仅在审批后调用。
| - `multimodal_tools.py`：新增 `analyze_food_image`、`analyze_scale_image`。
| 3. `Approval Layer`（审批执行器）
| - 保留现有 `PendingAction` 执行方式，写库仍由 repository 完成。
| 4. `LLM Client Layer`（模型适配）
| - 统一从 `.env` 创建 `ChatOpenAI`（DashScope 兼容协议）。
| ### 3.2 推荐目录（在现有基础上新增）
| ```text
| Rogers/app/agent/
| service/
| agent_service.py               # 编排入口（升级）
| llm_client.py                  # 新增：读取 env 构造 qwen client
| tools/
| read_tools.py                  # 复用
| write_tools.py                 # 复用
| multimodal_tools.py            # 新增：图片识别工具
| prompts/
| fitness_coach_prompt.py        # 新增：系统提示词
| schemas/
| agent.py                       # 升级：加入 attachments
| multimodal.py                  # 新增：Attachment/ToolResult DTO
| __init__.py
| ```
| ### 3.3 `agent_service.py` 升级要点
| - 保留现有接口：`chat/list_history/list_pending/approve`。
| - `chat` 输入升级：支持 `attachments`。
| - 新增输入构造：将图片附件转成 `image_url` content part。
| - 调用 `create_tool_calling_agent`，读写工具和多模态工具统一注册。
| - 输出升级：
| - `response`（文本）
| - `tool_events`（可选，供前端展示工具调用过程）
| - `pending_actions`（继续沿用）
| ### 3.4 API/Schema 约定（向后兼容）
| `AgentChatRequest` 建议升级为：
| ```python
| class Attachment(BaseModel):
| type: Literal["image"]
| base64: str
| filename: str | None = None
| mime_type: str | None = None
| class AgentChatRequest(BaseModel):
| message: str = Field(min_length=0, max_length=2000)
| session_id: str | None = Field(default=None, max_length=64)
| attachments: list[Attachment] = Field(default_factory=list)
| ```
| 兼容策略：
| - 旧请求仅传 `message` 仍可工作。
| - 新请求可仅图片无文本，后端自动补全默认提示语。
| ### 3.5 审批链路保持不变
| 继续沿用当前强约束：
| - 模型不能直接写库。
| - `update_*` 工具只产生待执行意图或标准化 payload。
| - 仅 `approve` 路由最终调用 repository `upsert`。
| ### 3.6 Agent 与业务数据交互设计（核心）
| 参考 Hermes-Agent 常见的“编排层 + 仓储层 + 审批网关”思路，Rogers 中建议明确 3 条数据通道：
| 1. 查询通道（只读）
| - `chat` -> Agent 选择 `read_tools` -> `Daily*Repository/UserRepository` -> 返回结构化数据。
| - 只读查询不经过审批，返回结果用于回答和趋势分析。
| 2. 变更意图通道（待审批）
| - Agent 判断用户意图后调用 `update_*` 工具，生成标准化 payload。
| - 写入 `PendingAction`（`status=pending`），并返回给前端审批卡。
| 3. 执行通道（落库）
| - 前端调用 `/api/v1/agent/approve`（approve/edit/reject）。
| - `approve` 分支执行 repository `upsert`；`reject` 仅更新状态。
| - 执行后写回 `PendingAction.result_message/executed_at`，形成可追踪审计链。
| 建议在 `AgentService` 中新增统一的 Tool IO 适配结构，避免工具返回风格不一致：
| ```python
| class ToolEvent(TypedDict):
| event_id: str
| tool_name: str
| phase: Literal["started", "completed", "failed"]
| summary: str
| payload_preview: dict | None
| created_at: str
| ```
| ### 3.7 记忆系统设计（参考 Hermes-Agent 设计）
| 目标：让 Agent 既有“会话内记忆”，也有“跨会话可召回记忆”，且严格受 `user_id` 隔离。
| 记忆分层：
| 层级 | 作用 | 存储位置 | 读写方式 |
| |------|------|----------|----------|
| 短期记忆（Session Memory） | 当前会话上下文与最近轮次 | `AgentSession` + `AgentMessage` | 每轮对话直接读写 |
| 工作记忆（Working Memory） | 本次任务中的工具结果、待审批草稿 | 运行时内存 + `PendingAction` | 会话内临时缓存，审批后落状态 |
| 长期记忆（Long-term Memory） | 用户偏好、目标、稳定事实、关键结论 | `agent_memory` 表（建议新增）+ 可选 `memory/*.md` | 由记忆管理器摘要写入 |
| 长期记忆建议结构（数据库优先，文件可选）：
| ```text
| agent_memory
| - id
| - user_id
| - memory_type      # preference|goal|fact|summary
| - content          # 自然语言记忆片段
| - tags             # ["nutrition","low-carb"] 之类
| - source           # chat|tool|approval
| - source_ref       # message_id/action_id
| - importance       # 1~5
| - created_at
| - updated_at
| ```
| 记忆写入策略（何时写）：
| - 用户明确指令：“记住/以后按这个来/我的偏好是…”
| - 审批成功后的结构化事实：如“每周训练 4 次”“目标体重 68kg”
| - 会话收尾摘要：长对话结束后抽取 1~3 条高价值事实写入长期记忆
| 记忆召回策略（何时读）：
| - 每次 `chat` 前，按 `user_id` 检索 Top-K 记忆注入系统上下文（默认 3~5 条）
| - 检索采用混合策略：关键词 BM25 + 向量语义检索（可先 BM25 起步）
| - 当用户问题与历史偏好强相关时提高长期记忆权重（如饮食偏好、受伤禁忌）
| ### 3.8 记忆管理器（MemoryManager）职责
| 建议新增 `app/agent/service/memory_manager.py`，负责：
| - `extract_memories(messages, tool_events, approvals)`：从对话和工具结果抽取候选记忆。
| - `upsert_memory(user_id, memory_item)`：写入或合并长期记忆（避免重复）。
| - `search_memories(user_id, query, top_k)`：检索相关记忆供 prompt 注入。
| - `build_memory_context(...)`：输出给 LLM 的精简记忆片段（控制 token）。
| 最小可用版本（MVP）建议：
| - V1：仅用 SQLite/PostgreSQL 文本检索（`ILIKE`/FTS）+ importance 排序。
| - V2：引入向量检索（pgvector 或本地向量库）做混合召回。
| ## 4. 前端设计（对齐 qwenpaw Chat 体验）
| ### 4.1 页面结构建议
| 参考 `CoPaw/console/src/pages/Chat`，在 Rogers 前端保持三段布局：
| - 顶部：会话标题 + 新建会话 + 搜索 + 历史。
| - 中部：消息流（文本、图片、工具过程卡、审批卡）。
| - 底部：输入区（文本框 + 上传按钮 + 发送）。
| ### 4.2 关键交互（必须具备）
| - 图片上传后，立即在用户气泡显示缩略图。
| - 同图连续追问：后续消息沿用当前会话上下文，不丢图像语义。
| - 工具调用可视化：
| - `analyze_food_image` 调用中
| - 识别完成并产出结构化结果
| - 用户确认写入 -> 进入审批卡
| - 审批通过 -> 成功反馈
| - 审批卡支持三操作：确认、编辑后确认、拒绝。
| ### 4.3 前端组件规划（Rogers）
| ```text
| webpage/src/features/ai-coach/
| AISidebar.tsx
| ChatHeader.tsx
| ChatMessageList.tsx
| ChatInput.tsx
| ChatAttachmentPreview.tsx          # 新增
| ToolCallTimeline.tsx               # 新增
| FoodRecognitionResult.tsx
| PendingActionCard.tsx
| hooks/
| useAgentChat.ts
| usePendingActions.ts
| useMultimodalUpload.ts         # 新增
| api/
| agent.ts
| ```
| ### 4.4 UI 对齐点（qwenpaw 风格）
| - 输入区使用附件按钮触发上传（而不是独立大块上传区）。
| - 消息区域优先高信息密度，工具过程卡片简洁分层。
| - 图片支持点击放大与错误兜底占位。
| - 会话级操作（新会话、历史、搜索）放在 Header 右侧工具组。
| ### 4.5 与 qwenpaw 文件映射（落地参考）
| qwenpaw 参考文件 | Rogers 对应设计 |
| |------|------|
| `CoPaw/console/src/pages/Chat/index.tsx` | `AISidebar.tsx` 作为总装页面，负责会话、请求发送、附件能力检测 |
| `components/ChatActionGroup/index.tsx` | `ChatHeader.tsx` 中实现新会话/历史/搜索动作组 |
| `components/ChatHeaderTitle/index.tsx` | `ChatHeader.tsx` 显示当前会话标题 |
| `Chat/utils.ts` | 在 `features/ai-coach/utils.ts` 增加消息提取、附件 URL 规范化、复制文本能力 |
| `sender.attachments`（上传触发与 customRequest） | `useMultimodalUpload.ts` + `ChatInput.tsx` 组合实现上传、大小校验、预览回填 |
| ## 5. 端到端链路定义
| ```text
| 用户输入文本/上传图片
| -> 前端转 Attachment(base64, mime_type)
| -> POST /api/v1/agent/chat
| -> AgentService.build_multimodal_input()
| -> qwen3.5-plus + tools
| -> 返回 response + tool_events + pending_actions
| -> 前端渲染消息/工具卡/审批卡
| -> 用户 approve/edit/reject
| -> POST /api/v1/agent/approve
| -> repository.upsert
| ```
| ## 6. 分步实施计划（结合当前代码）
| ### 6.1 后端
| 序号 | 任务 | 目标文件 |
| |------|------|----------|------|
| B1 | 新增 LLM client（读取 `.env`） | `app/agent/service/llm_client.py` |
| B2 | 扩展 schema 支持附件 | `app/agent/schemas/agent.py` |
| B3 | 新增图片多模态工具 | `app/agent/tools/multimodal_tools.py` |
| B4 | 升级 `AgentService.chat` 为 LangChain 编排 | `app/agent/service/agent_service.py` |
| B5 | 输出工具事件供前端展示 | `app/agent/service/agent_service.py` |
| B6 | 回归审批流程（approve） | `app/agent/service/agent_service.py` |
| B7 | 新增长期记忆管理器（抽取/写入/检索） | `app/agent/service/memory_manager.py` |
| B8 | 新增记忆仓储与数据模型 | `app/repositories/agent_memory_repository.py` |
| B9 | 在 chat 前注入 Top-K 记忆上下文 | `app/agent/service/agent_service.py` |
| ### 6.2 前端
| 序号 | 任务 | 目标文件 |
| |------|------|----------|------|
| F1 | 图片上传与附件预览 | `ChatInput.tsx`, `ChatAttachmentPreview.tsx` |
| F2 | 消息流图片渲染与放大 | `ChatMessageList.tsx` |
| F3 | 工具调用时间线卡片 | `ToolCallTimeline.tsx` |
| F4 | 审批卡与写入反馈串联 | `PendingActionCard.tsx` |
| F5 | 会话头部动作组（新建/历史/搜索） | `ChatHeader.tsx` |
| ## 7. 验收标准
| ### 7.1 功能验收
| - [ ] `AgentChatRequest` 支持图片附件。
| - [ ] 食物图片可返回结构化营养估算。
| - [ ] 体重秤图片可返回体重识别值。
| - [ ] 写库依然必须经过 `PendingAction` 审批。
| - [ ] 历史会话可回放图片与工具过程。
| - [ ] 记忆写入仅限当前 `user_id`，不同用户完全隔离。
| - [ ] 用户说“记住这个”后，下次会话可被正确召回。
| ### 7.2 UI 验收（对齐 qwenpaw）
| - [ ] 输入区上传入口、附件预览、发送交互流畅。
| - [ ] 消息流支持文本+图片混合渲染。
| - [ ] 工具调用过程有明确阶段状态。
| - [ ] 审批卡片在视觉与交互上与消息流一致，不突兀。
| ## 8. 风险与缓解
| 风险 | 影响 | 缓解措施 |
| |------|------|----------|
| 图片识别结果不稳定 | 数据偏差 | 返回置信提示 + 用户可编辑后确认 |
| 大图上传慢 | 对话阻塞 | 前端压缩和尺寸限制（如最长边 1280） |
| 模型输出非 JSON | 解析失败 | 增加 schema 校验和兜底提取逻辑 |
| 工具过程无统一协议 | 前端难展示 | 约定 `tool_events` 标准字段 |
| 记忆写入噪声过高 | 上下文污染 | 加 importance 阈值与去重合并策略 |
| ## 9. 本期不做
| - 不引入语音识别链路（后续 Phase 扩展）。
| - 不做视频输入能力。
| - 不改动现有审批数据模型（只扩展输入输出协议）。
