# Phase 12：Runtime 流式 UI 对齐与稳定性增强

> 阶段目标：将 Rogers 的 AI 对话链路从“事件驱动页面渲染”升级为“统一消息模型驱动渲染”，对齐 CoPaw 的 Runtime 流式架构，完成 Thinking / Tool / Output 的同构展示、弱网重连补偿与可维护性拆分。

## 1. 目标与范围

### 1.1 本期目标（P0）

- 建立统一运行时消息模型（前端）。
- 固化后端 CoPaw 风格流式事件体 schema（双轨兼容旧协议）。
- 让历史消息与实时流式共用同一消息模型与同一渲染层。
- 实现 run 级最小重连补偿（`run_id + sequence_number`）。
- 将审批交互从“命令触发（/approve /deny）”升级为“可视化按钮触发”，在有待审批项时前端直接渲染快捷审批按钮。

### 1.2 本期范围（包含）

- 前端：`AISidebar`、流式消费、消息映射层、消息渲染子组件。
- 后端：`chat/stream` 事件 schema、重连参数支持、stream tracker。
- 审批交互：输入区审批快捷按钮、待审批卡片与按钮行为一致性。
- 测试：流式稳定性、历史回放一致性、断线重连补偿。

### 1.3 本期不做（排除）

- 不引入完整 `@agentscope-ai/chat` 重构现有页面容器。
- 不重做全站视觉主题，仅聚焦 AI 侧边栏消息链路。
- 不改审批业务语义（`pending_actions` 仍沿用现有流程）。

## 2. 设计原则

1. **模型先于视图**：先统一消息类型和序列，再谈 UI 细节。  
2. **历史实时同构**：历史与实时走同一 mapper 和同一组件。  
3. **双轨兼容迁移**：新旧协议同时输出，避免一次性切断。  
4. **可追踪可重放**：所有流式片段可按 `run_id + sequence_number` 复盘。

## 3. 目标架构

```text
SSE Event (new + legacy)
   -> normalize / mapper
      -> RuntimeMessage[] / RuntimeMessagePatch
         -> RuntimeBubbleList
            -> ThinkingCard / ToolCard / OutputCard
```

```text
AgentService.chat_stream
   -> internal runtime DTO
      -> emitter (legacy + modern)
      -> StreamTracker buffer
      -> reconnect replay + live stream
```

## 4. 任务拆解

## 4.1 前端任务（F 系列）

| 编号 | 任务 | 文件 | 输出 |
|------|------|------|------|
| F1 | 新增 runtime 消息 mapper | `webpage/src/features/ai-coach/runtime_message_mapper.ts` | `RuntimeMessagePatch` 转换器 |
| F2 | `AISidebar` 接入 mapper，移除事件分支渲染 | `webpage/src/features/ai-coach/AISidebar.tsx` | orchestrator 化 |
| F3 | 拆分消息渲染组件 | `RuntimeBubbleList.tsx`, `RuntimeThinkingCard.tsx`, `RuntimeToolCard.tsx`, `RuntimeOutputCard.tsx` | 协议驱动组件 |
| F4 | 历史消息接入统一模型 | `AISidebar.tsx`（历史加载逻辑） | 历史/实时一致展示 |
| F5 | Tool 卡结构升级 | `RuntimeToolCard.tsx` | 输入/输出/错误三段模板 |
| F6 | 审批按钮化交互完善 | `AISidebar.tsx`, `styles.css` | 有待审批时渲染快捷按钮，替代命令提示 |

## 4.2 后端任务（B 系列）

| 编号 | 任务 | 文件 | 输出 |
|------|------|------|------|
| B1 | 固化新协议事件体 schema | `Rogers/app/agent/service/agent_service.py` | 结构化 `reasoning/tool_call/assistant_delta/done` |
| B2 | 双轨统一派生 | `agent_service.py` | legacy 与 modern 来源同一内部 DTO |
| B3 | 新增 stream tracker | `Rogers/app/agent/runtime/stream_tracker.py` | run buffer + replay |
| B4 | stream 接口支持 reconnect 参数 | `Rogers/app/api/v1/agent.py` | `reconnect/run_id/last_seq` 支持 |
| B5 | 事件发送统一出口 | `agent_service.py` | emitter 收敛与可观测字段 |

## 4.3 协议任务（S 系列）

| 编号 | 任务 | 内容 | 结果 |
|------|------|------|------|
| S1 | 定义 RuntimeMessage 类型 | `REASONING / PLUGIN_CALL / PLUGIN_CALL_OUTPUT / MESSAGE / APPROVAL` | 前后端统一语义 |
| S2 | 定义字段契约 | `id/sequence_number/created_at/status/meta` | 去重、排序、追踪可用 |
| S3 | 定义 done 语义 | `response_id/usage/completed_at` | 收尾一致性 |

## 5. 事件体规范（Phase-12 定稿）

### 5.1 reasoning

```json
{
  "id": "rsn_xxx",
  "type": "reasoning",
  "delta": "正在分析最近7天体重趋势...",
  "sequence_number": 12,
  "created_at": "2026-04-15T10:00:00Z"
}
```

### 5.2 tool_call

```json
{
  "id": "tool_xxx",
  "type": "tool_call",
  "tool_name": "get_health_metrics",
  "phase": "started",
  "input_preview": {"days": 7},
  "output_preview": null,
  "error_preview": null,
  "sequence_number": 18,
  "created_at": "2026-04-15T10:00:02Z"
}
```

### 5.3 assistant_delta

```json
{
  "id": "msg_xxx",
  "type": "message",
  "delta": "你的体重近7天下降了0.8kg，",
  "sequence_number": 25,
  "created_at": "2026-04-15T10:00:03Z"
}
```

### 5.4 approval_required

```json
{
  "id": "apr_xxx",
  "type": "approval",
  "action_id": "act_xxx",
  "tool_name": "update_daily_metrics",
  "summary": "更新今日体重为 78.2kg",
  "payload": {"record_date": "2026-04-15", "data": {"weight": 78.2}},
  "sequence_number": 31,
  "created_at": "2026-04-15T10:00:05Z"
}
```

### 5.5 done

```json
{
  "response_id": "resp_xxx",
  "usage": {"prompt_tokens": 123, "completion_tokens": 245},
  "completed_at": "2026-04-15T10:00:10Z",
  "sequence_number": 40
}
```

## 6. 执行里程碑

- M1：协议与 mapper 基座（S1-S3 + F1 + B1）  
- M2：双轨并行与页面接入（B2 + F2 + F4）  
- M3：组件拆分与 Tool 卡升级（F3 + F5）  
- M3.1：审批按钮化交互收敛（F6）  
- M4：重连补偿最小可用（B3 + B4 + B5）  
- M5：回归验收与文档闭环

## 7. 验收标准

### 7.1 功能验收

- Thinking / Tool / Output 在实时与历史回放一致。
- 新旧协议都可渲染，且渲染逻辑只依赖统一 mapper 输出。
- 断线重连后可续流，不重复不缺段（按 `sequence_number`）。
- Tool 结果卡支持输入摘要/输出摘要/错误摘要。
- 当存在待审批操作时，输入区显示“确认审批/拒绝审批”按钮；无需通过 `/approve` `/deny` 命令唤醒。
- 审批按钮触发结果与待审批卡片触发结果一致（状态更新、消息回显、列表刷新一致）。

### 7.2 技术验收

- 前端构建通过：`npm run build`（`webpage`）。
- 后端编译通过：`python -m compileall Rogers/app/agent Rogers/app/api/v1`。
- 接口冒烟：
  - `POST /api/v1/agent/chat/stream` 正常流式；
  - reconnect 参数可触发 replay。

## 8. 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 新旧协议字段不一致 | 前端偶发渲染缺块 | 双轨统一由内部 DTO 派生，禁止手写两套字段 |
| 重连逻辑顺序错乱 | 内容重复/缺失 | 强制 `sequence_number` 单调与去重 |
| AISidebar 改造范围大 | 回归成本高 | 先 mapper 接入，再逐步组件拆分 |
| Tool 输出结构不稳定 | 卡片展示漂移 | 固定 `input/output/error preview` 三段模板 |
| 审批入口双轨并存导致认知负担 | 用户不知道该点哪里 | 输入区以按钮为主入口，命令提示降级为文档能力说明 |

## 9. 交付物清单

- `.plan/phase-12-runtime-stream-ui-alignment.md`（本文件）
- 前端 mapper 与组件拆分代码
- 后端 stream tracker 与 reconnect 支持
- 流式协议样例与验证记录
