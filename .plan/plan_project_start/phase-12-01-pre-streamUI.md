# Phase Pre-12：AISidebar 与 CoPaw 在流式 UI 体系上的差距与改造方案

## 1. 文档目标

本文件聚焦 3 个核心问题，并给出逐项可落地方案：

1. 前端怎么做气泡和流式 UI  
2. 后端怎么做流式输出  
3. Thinking / Tool / 最终输出的数据来源与映射

结论先行：我们当前已经具备“能流式显示”的能力，但距离 CoPaw 的“运行时消息协议驱动 UI”还有体系差距，必须从“事件名兼容”升级为“消息模型兼容”。

## 2. 对照基线（CoPaw）

### 2.1 前端气泡与流式 UI 基线

- CoPaw 核心聊天 UI 不是手写 DOM，而是 `@agentscope-ai/chat` 的 `AgentScopeRuntimeWebUI` 渲染（气泡、Thinking 卡、Tool Use 卡都由组件库输出）。
- 前端请求统一发到 `/console/chat`，且 `stream: true`，把流消费交给 Runtime WebUI 内部机制。
- 历史消息会先做“后端消息 -> 卡片模型”的标准转换：
  - user -> `AgentScopeRuntimeRequestCard`
  - assistant/tool/thinking 连续输出 -> `AgentScopeRuntimeResponseCard`

### 2.2 后端流式输出基线

- `/console/chat` 返回 `StreamingResponse(text/event-stream)`，并支持 `reconnect`。
- 输出不是手工拼一堆自定义 event name，而是 runtime event 直接 `model_dump_json()` 后以 `data: ...\n\n` 推送。
- 断线重连依赖 `TaskTracker`：run 级别 buffer，先回放历史 buffer，再续接新事件。

### 2.3 Thinking / Tool / 最终输出基线

- `thinking`：消息块 `type="thinking"` -> runtime `MessageType.REASONING`
- `tool_use`：-> `MessageType.PLUGIN_CALL`（`FunctionCall`）
- `tool_result`：-> `MessageType.PLUGIN_CALL_OUTPUT`（`FunctionCallOutput`）
- 最终正文：`type="text"` -> `MessageType.MESSAGE + TextContent`
- Agent 主循环持续产出这些消息（`stream_printing_messages(...)`），由 channel 层统一转 SSE。

## 3. 我们当前 AISidebar 的差距（按你要求的 3 个点）

## 3.1 前端气泡与流式 UI：差距与方案

### 差距

- 我们当前 `AISidebar.tsx` 是手写 DOM + 本地 state 拼装，仍属于“页面自定义渲染”。
- 尽管已有 `Thinking / Tool / Output` 模块显示，但不是 Runtime Card 体系，缺少统一卡片协议。
- 历史消息与实时流式在模型层未完全同构，回放一致性依赖页面逻辑。

### 解决方案

1. 新增前端运行时消息转换层（P0）
- 新建：`webpage/src/features/ai-coach/runtime_message_mapper.ts`
- 功能：
  - 输入：SSE 新旧事件（`reasoning/tool_call/assistant_delta/done` + legacy）
  - 输出：统一 `RuntimeMessage[]`（建议结构：`id/role/type/content/sequence/status/created_at/meta`）
- 要求：`AISidebar` 不再直接读 event，改为只读 mapper 结果。

2. 历史消息与实时消息统一进入 mapper（P0）
- 历史 API 返回后，先转换为 `RuntimeMessage[]` 再渲染。
- 流式增量也转换为同类型 `RuntimeMessagePatch` 再 merge。
- 目标：历史和实时同构，消除展示差异。

3. UI 组件从“大组件”拆为“协议驱动组件”（P1）
- `AISidebar.tsx` 仅负责 orchestrator；
- 新增：
  - `RuntimeBubbleList.tsx`
  - `RuntimeThinkingCard.tsx`
  - `RuntimeToolCard.tsx`
  - `RuntimeOutputCard.tsx`
- 每个组件只消费统一 message type，不感知后端事件。

### 验收

- 同一会话中，重进页面后看到的 Thinking/Tool/Output 与实时过程一致。
- 删除所有 `if (event.event === "...")` 直连渲染分支（保留在 mapper 内）。

## 3.2 后端流式输出：差距与方案

### 差距

- 我们已做双轨事件名兼容，但事件体仍偏“业务临时字段”，未达到 CoPaw 的 runtime message 标准化程度。
- 目前缺少 run 级事件 buffer 与 reconnect 回放链路，弱网场景稳健性不足。

### 解决方案

1. 统一 SSE 事件体 schema（P0）
- 文件：`Rogers/app/agent/service/agent_service.py`
- 新协议建议：
  - `reasoning`: `{id, type:"reasoning", delta, sequence_number, created_at}`
  - `tool_call`: `{id, type:"tool_call", tool_name, phase, args, output, error, sequence_number, created_at}`
  - `assistant_delta`: `{id, type:"message", delta, sequence_number, created_at}`
  - `approval_required`: `{id, type:"approval", action_id, tool_name, summary, payload, created_at}`
  - `done`: `{response_id, usage, completed_at, sequence_number}`
- 旧协议继续输出（双轨），但由同一内部事件对象派生，避免双维护。

2. 增加 run 级 buffer + reconnect 回放（P0）
- 新增：
  - `Rogers/app/agent/runtime/stream_tracker.py`
- 能力：
  - `create_run(session_id) -> run_id`
  - `append_event(run_id, seq, payload)`
  - `replay_from(run_id, last_seq)`
- `chat/stream` 支持 `reconnect=true&run_id=...&last_seq=...`，先 replay 再接 live。

3. channel 层统一发送（P1）
- 当前 service 中分散 `yield`，建议收敛到统一 emitter（类似 CoPaw channel）。
- 目标：所有事件发送口径统一，便于审计与压测。

### 验收

- 中断后重连，前端能从 `last_seq` 继续，不重复、不缺段。
- 服务端日志可按 `run_id + sequence_number` 追踪全链路。

## 3.3 Thinking / Tool / 最终输出：数据来源差距与方案

### 差距

- 我们目前 Thinking/Tool/Output 主要是“展示层标签”，而 CoPaw 是“类型层约束”。
- Tool 事件缺少明确的“调用输入”和“调用输出”双结构，调试与审计不充分。

### 解决方案

1. 明确消息类型系统（P0）
- 后端新增统一枚举：
  - `REASONING`
  - `PLUGIN_CALL`
  - `PLUGIN_CALL_OUTPUT`
  - `MESSAGE`
  - `APPROVAL`
- 发送前全部转换为统一内部 DTO，再序列化为 SSE 事件。

2. Tool 数据结构升级（P0）
- `tool_call` 统一字段：
  - `input_preview`（工具参数摘要）
  - `output_preview`（工具输出摘要）
  - `error_preview`（失败时错误摘要）
- 前端 `RuntimeToolCard` 按这 3 块固定模板展示。

3. 最终输出与推理过程分轨（P1）
- `reasoning` 与 `assistant_delta` 分开累计；
- `done` 事件给出最终 message 元信息（token、耗时、usage）。

### 验收

- 每条 assistant 回复都能回溯其 reasoning 片段、tool call 列表、最终正文。
- Tool 失败场景下，UI 有结构化错误卡，不再仅靠一段文本描述。

## 4. 落地任务拆解（具体到文件）

### 4.1 前端

- 修改：`webpage/src/shared/api/agent.ts`
  - 保留 SSE 读取；将 `normalizeStreamEvent` 下沉到 mapper 层。
- 新增：`webpage/src/features/ai-coach/runtime_message_mapper.ts`
  - 新旧协议事件 -> `RuntimeMessagePatch`
- 修改：`webpage/src/features/ai-coach/AISidebar.tsx`
  - 删除事件分支渲染，改为消费 `RuntimeMessage[]`
- 新增：
  - `webpage/src/features/ai-coach/components/RuntimeBubbleList.tsx`
  - `webpage/src/features/ai-coach/components/RuntimeThinkingCard.tsx`
  - `webpage/src/features/ai-coach/components/RuntimeToolCard.tsx`
  - `webpage/src/features/ai-coach/components/RuntimeOutputCard.tsx`

### 4.2 后端

- 修改：`Rogers/app/agent/service/agent_service.py`
  - 统一内部事件 DTO -> 双轨 SSE 输出
- 新增：`Rogers/app/agent/runtime/stream_tracker.py`
  - run buffer + reconnect replay
- 修改：`Rogers/app/api/v1/agent.py`
  - 增加 reconnect 参数支持（run_id/last_seq）

## 5. 执行优先级

### P0（必须先做）

1. 后端 schema 固化（reasoning/tool_call/assistant_delta/done）
2. 前端 mapper 层落地并接管渲染输入
3. 历史与实时统一模型
4. run buffer + reconnect 最小可用

### P1（随后）

5. AISidebar 组件拆分
6. Tool 卡固定模板
7. done/usage 展示增强

## 6. Phase-12 验收标准（最终）

- 流式协议：新旧双轨兼容，且由统一 DTO 派生，不出现字段漂移。
- UI 输出：Thinking / Tool / Output 全部由统一消息模型驱动，历史与实时一致。
- 重连能力：断网后可续流，按 `sequence_number` 去重与补偿。
- 可维护性：`AISidebar.tsx` 由“业务+渲染混合”降为 orchestrator，主要渲染逻辑迁移到子组件。
