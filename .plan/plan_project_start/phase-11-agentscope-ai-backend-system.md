| # Phase 11: AgentScope AI 系统重构（后端 + 前端）
| > 阶段目标：将 Rogers AI 后端从 LangChain 体系整体迁移到 AgentScope 运行时，并参考 `f:\copaw\CoPaw\src\qwenpaw` 的成熟实践，同时升级 Agent 前端交互体验，落地可扩展、可审计、可流式的 AI 系统底座。
| ## 1. 改造范围
| ### 1.1 本期必须完成（P0）
| - 统一 Agent 运行时为 AgentScope `ReActAgent`。
| - 建立 `toolkit + tool guard + approval` 的敏感操作闭环。
| - 建立可用的记忆管理器（短期/工作/长期记忆三层）。
| - 完成流式对话后端（SSE）稳定输出能力。
| - 保持现有 API 契约兼容（`/api/v1/agent/chat`、`/approve`、`/history`、`/pending`）。
| - 参考 CoPaw Chat 页面，完成 Agent 前端会话、消息流、工具过程与审批体验优化。
| ### 1.2 本期可选完成（P1）
| - 增加多 Agent workspace 隔离能力（单进程多工作区）。
| - 增加技能（skills）动态注册与开关管理。
| ## 2. 参考映射（CoPaw -> Rogers）
| CoPaw 参考 | Rogers 落地 |
| |------|------|
| `src/qwenpaw/agents/react_agent.py` | `Rogers/app/agent/runtime/react_agent.py`（核心 ReAct 封装） |
| `src/qwenpaw/agents/tool_guard_mixin.py` | `Rogers/app/agent/guard/tool_guard.py`（工具护栏拦截） |
| `src/qwenpaw/app/approvals/service.py` | `Rogers/app/agent/guard/approval_service.py`（审批生命周期） |
| `src/qwenpaw/agents/memory/base_memory_manager.py` | `Rogers/app/agent/memory/base_memory_manager.py`（记忆抽象） |
| `src/qwenpaw/agents/memory/reme_light_memory_manager.py` | `Rogers/app/agent/memory/memory_manager.py`（记忆实现） |
| `src/qwenpaw/app/routers/agent_scoped.py` | `Rogers/app/api/v1/agent.py` + agent 上下文隔离 |
| `src/qwenpaw/app/multi_agent_manager.py` | `Rogers/app/agent/runtime/multi_agent_manager.py`（可选） |
| `console/src/pages/Chat/index.tsx` | `webpage/src/features/ai-coach/AISidebar.tsx`（聊天总装） |
| `console/src/pages/Chat/components/ChatActionGroup` | `webpage/src/features/ai-coach/ChatHeader.tsx`（会话动作组） |
| `console/src/pages/Chat/components/ChatSessionDrawer` | `webpage/src/features/ai-coach/SessionHistoryPanel.tsx`（历史会话） |
| `console/src/pages/Chat/utils.ts` | `webpage/src/features/ai-coach/utils.ts`（消息与流式工具） |
| ## 3. 目标架构
| ### 3.1 后端分层
| ```text
| api/v1/agent.py
| -> service/agent_service.py
| -> runtime/react_agent.py
| -> tools/* (read/write/analysis)
| -> guard/tool_guard.py + approval_service.py
| -> memory/memory_manager.py
| -> repositories/*
| ```
| ### 3.2 核心约束
| - 读写工具统一走 `Toolkit`，禁止在路由层直接写库。
| - 写工具必须被 Tool Guard 拦截并进入审批队列。
| - Agent 回复必须支持 token 级流式，不允许“伪流式”。
| - 所有会话数据按 `user_id` + `session_id` 隔离。
| ### 3.3 前端体验约束（参考 CoPaw）
| - 会话区与历史区分离，支持会话切换与历史回放。
| - 消息支持模块化展示：`thinking` -> `tool_use` -> `content`。
| - 工具调用需可视化状态：`started/completed/failed`，并显示摘要。
| - 侧边栏支持可折叠与独立滚动，不影响主内容区滚动。
| ## 4. 目录落位（目标）
| ```text
| Rogers/app/agent/
| ├── runtime/
| │   ├── react_agent.py
| │   ├── model_factory.py
| │   ├── stream_parser.py
| │   └── multi_agent_manager.py
| ├── tools/
| │   ├── definitions.py
| │   ├── read_tools.py
| │   ├── write_tools.py
| │   └── analysis_tools.py
| ├── guard/
| │   ├── tool_guard.py
| │   ├── approval_service.py
| │   └── rules/
| ├── memory/
| │   ├── base_memory_manager.py
| │   ├── memory_manager.py
| │   └── retriever.py
| ├── schemas/
| │   ├── request.py
| │   └── response.py
| └── service/
| ├── agent_service.py
| └── session_service.py
| ```
| ### 4.2 前端目录落位（目标）
| ```text
| webpage/src/features/ai-coach/
| ├── AISidebar.tsx             # Agent 聊天总装容器
| ├── ChatHeader.tsx            # 会话标题 + 动作组
| ├── ChatMessageList.tsx       # 消息列表（模块化渲染）
| ├── ToolCallTimeline.tsx      # 工具调用时间线
| ├── PendingActionCard.tsx     # 审批卡片
| ├── SessionHistoryPanel.tsx   # 历史会话抽屉/面板
| ├── hooks/
| │   ├── useAgentChat.ts
| │   ├── useAgentStream.ts
| │   └── useSessionHistory.ts
| └── utils.ts
| ```
| ## 5. 实施任务拆解
| ### 5.1 Runtime 层（R 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| R1 | 接入 AgentScope `ReActAgent` 主体封装 | `runtime/react_agent.py` |
| R2 | 构建 DashScope 模型工厂与 formatter | `runtime/model_factory.py` |
| R3 | 实现稳健 SSE 输出解析（多字节安全） | `runtime/stream_parser.py` |
| R4 | 预留多 workspace 管理器（可选） | `runtime/multi_agent_manager.py` |
| ### 5.2 Guard + 审批层（G 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| G1 | 落地工具护栏引擎（deny/guard/allow） | `guard/tool_guard.py` |
| G2 | 实现待审批队列与决策消费 | `guard/approval_service.py` |
| G3 | 统一与 `pending_actions` 表对接 | `service/agent_service.py` |
| ### 5.3 Memory 层（M 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| M1 | 抽象 BaseMemoryManager 接口 | `memory/base_memory_manager.py` |
| M2 | 实现记忆管理（短期/工作/长期） | `memory/memory_manager.py` |
| M3 | 实现记忆检索注入（Top-K） | `memory/retriever.py` |
| ### 5.4 Service + API 层（S 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| S1 | 重构 AgentService（AgentScope 编排） | `service/agent_service.py` |
| S2 | 保持非流式接口兼容 | `api/v1/agent.py` |
| S3 | 增强流式接口稳定性与错误透传 | `api/v1/agent.py` |
| S4 | 对话历史/待审批接口兼容回归 | `api/v1/agent.py` |
| ### 5.5 Agent 前端优化（F 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| F1 | 重构 Agent 聊天主容器与布局分区 | `AISidebar.tsx` |
| F2 | 增加会话动作组（新建/搜索/历史） | `ChatHeader.tsx` |
| F3 | 接入历史会话面板与切换回放 | `SessionHistoryPanel.tsx`, `useSessionHistory.ts` |
| F4 | 增强流式消息渲染（thinking/tool/content 分块） | `ChatMessageList.tsx`, `useAgentStream.ts` |
| F5 | 增加工具调用时间线与状态可视化 | `ToolCallTimeline.tsx` |
| F6 | 优化审批卡交互（approve/edit/reject）与反馈 | `PendingActionCard.tsx` |
| ## 6. 接口契约（兼容策略）
| ### 6.1 保持不变
| - `POST /api/v1/agent/chat`
| - `POST /api/v1/agent/chat/stream`
| - `POST /api/v1/agent/approve`
| - `GET /api/v1/agent/history`
| - `GET /api/v1/agent/pending`
| ### 6.2 可新增字段（向后兼容）
| - `tool_events`: 工具调用阶段事件（started/completed/failed）。
| - `memory_hits`: 命中记忆摘要（用于前端可视化）。
| ### 6.3 SSE 事件协议（推荐）
| 建议统一采用以下事件流，前后端按事件类型解耦：
| - `message_start`：开始一轮回复，返回 `session_id`。
| - `thinking_delta`：模型思考过程增量文本。
| - `tool_event`：工具调用事件（`started/completed/failed`）。
| - `content_delta`：最终回复正文增量文本。
| - `pending_action`：需要用户审批的操作卡片数据。
| - `message_end`：本轮结束，附带收尾元数据（如 `memory_hits`）。
| - `error`：错误事件，不中断 UI 已有内容渲染。
| 事件示例：
| ```text
| event: thinking_delta
| data: {"delta":"正在分析最近7天体重与体脂趋势..."}
| event: tool_event
| data: {"event_id":"evt_001","tool_name":"get_health_metrics","phase":"started","summary":"开始读取近7天指标"}
| event: content_delta
| data: {"delta":"你的体重近7天下降了0.8kg，"}
| ```
| ### 6.4 后端流式输出示例（FastAPI）
| ```python
| import json
| from fastapi.responses import StreamingResponse
| def _sse(event: str, data: dict) -> str:
| return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
| def chat_stream(...):
| yield _sse("message_start", {"session_id": session_id})
| yield _sse("thinking_delta", {"delta": "正在分析用户输入与历史记忆...\n"})
| yield _sse("tool_event", {
| "event_id": "evt_001",
| "tool_name": "get_health_metrics",
| "phase": "started",
| "summary": "开始读取健康指标",
| })
| # ...调用工具
| yield _sse("tool_event", {
| "event_id": "evt_002",
| "tool_name": "get_health_metrics",
| "phase": "completed",
| "summary": "指标读取完成",
| "payload_preview": {"days": 7, "records": 7},
| })
| for chunk in llm_stream():
| yield _sse("content_delta", {"delta": chunk})
| yield _sse("message_end", {
| "session_id": session_id,
| "memory_hits": memory_hits,
| })
| @router.post("/agent/chat/stream")
| def chat_with_agent_stream(...):
| return StreamingResponse(chat_stream(...), media_type="text/event-stream")
| ```
| ### 6.5 前端流式消费示例（TypeScript）
| ```ts
| type StreamEvent =
| { event: "message_start"; data: { session_id: string } }
| { event: "thinking_delta"; data: { delta: string } }
| { event: "tool_event"; data: ToolEventItem }
| { event: "content_delta"; data: { delta: string } }
| { event: "pending_action"; data: PendingActionItem }
| { event: "message_end"; data: { session_id?: string; memory_hits?: string[] } }
| { event: "error"; data: { message: string } };
| function handleStreamEvent(evt: StreamEvent) {
| switch (evt.event) {
| case "message_start":
| createAssistantMessage(evt.data.session_id);
| break;
| case "thinking_delta":
| appendThinking(evt.data.delta);
| break;
| case "tool_event":
| appendToolEvent(evt.data);
| break;
| case "content_delta":
| appendContent(evt.data.delta);
| break;
| case "pending_action":
| pushPendingAction(evt.data);
| break;
| case "message_end":
| finalizeAssistantMessage(evt.data.memory_hits ?? []);
| break;
| case "error":
| showStreamError(evt.data.message);
| break;
| }
| }
| ```
| ### 6.6 前端渲染结构示例（Thinking / Tools / Output）
| ```tsx
| <div className="ai-assistant-modules">
| {thinking ? (
| <details open>
| <summary>Thinking</summary>
| <pre>{thinking}</pre>
| </details>
| ) : null}
| {toolEvents.length ? (
| <details open>
| <summary>Tool Use ({toolEvents.length})</summary>
| {toolEvents.map((evt) => (
| <div key={evt.event_id}>
| <strong>{evt.tool_name}</strong> <span>{evt.phase}</span>
| <p>{evt.summary}</p>
| </div>
| ))}
| </details>
| ) : null}
| {content ? (
| <div>
| <div>Output</div>
| <div>{content}</div>
| </div>
| ) : null}
| </div>
| ```
| ### 6.7 实施注意事项
| - 增量文本必须做 UTF-8 安全解码，避免中文拆包乱码。
| - `tool_event` 建议包含 `event_id` 与 `created_at`，便于前端排序与去重。
| - 同一轮消息只维护一个 assistant 容器，`thinking/tools/content` 逐步填充。
| - 发生 `error` 时不要清空已渲染内容，只提示本轮中断原因。
| ## 7. 测试与验收
| ### 7.1 验收清单
| - [ ] Agent 对话可正常调用读工具并返回分析结果。
| - [ ] 写工具必须触发审批，未审批不得落库。
| - [ ] `/chat/stream` 支持连续 token 流，中文不乱码、不截断。
| - [ ] 审批后能正确回放工具调用并完成结果输出。
| - [ ] 会话历史与待审批列表接口返回结构不破坏前端。
| - [ ] 记忆检索仅命中当前用户数据，不串用户。
| - [ ] Agent 前端支持“会话/历史”切换与回放。
| - [ ] 消息区可展示 thinking、工具调用与正文分层块。
| - [ ] 工具调用时间线状态准确且与后端事件一致。
| - [ ] 侧边栏收展与滚动行为稳定，无布局穿透。
| ### 7.2 建议测试用例
| - 成功路径：读取趋势 -> 生成建议。
| - 风险路径：更新体重 -> 触发审批 -> approve/edit/reject 三分支。
| - 异常路径：模型超时、工具异常、SSE 中断重连。
| ## 8. 风险与缓解
| 风险 | 影响 | 缓解措施 |
| |------|------|----------|
| AgentScope 与现有 DTO 不一致 | 前后端联调失败 | 保持 schema 兼容，新增字段仅追加 |
| 工具护栏误拦截 | 用户操作阻塞 | 规则分级 + 审批兜底 + 审计日志 |
| 记忆召回噪声高 | 回答质量下降 | Top-K + score 阈值 + 去重策略 |
| 流式输出碎片化 | 前端渲染异常 | 采用游标缓冲与事件重组 |
| 前端事件渲染顺序错乱 | 过程展示不可信 | 统一 event_id + phase，前后端按时间序排序 |
| 会话切换状态污染 | 用户看到错会话消息 | 会话切换时重置本地 stream 状态与临时缓存 |
| ## 9. 里程碑
| - M1：Runtime 基座完成（R1-R3）
| - M2：Guard + 审批完成（G1-G3）
| - M3：Memory 完成（M1-M3）
| - M4：Service/API 联调完成（S1-S4）
| - M5：Agent 前端优化完成（F1-F6）
| - M6：回归验收与文档归档
| ## 10. 本期不做
| - 不引入复杂多 Agent 编排图（先保证单 Agent 稳定）。
| - 不扩展新业务接口（先保证现有接口兼容）。
| - 不重做整站视觉主题，仅优化 Agent 区域交互与信息结构。
