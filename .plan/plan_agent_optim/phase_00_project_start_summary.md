# Rogers 项目现状总结

> 本文档汇总项目整体进展、Agent 功能现状、前端设计现状，为后续 Agent 专项优化提供基线参考。

---

## 1. 项目定位与核心价值

### 1.1 项目定位

Rogers 定位为"个人用户数据管理与成长可视化应用"，核心价值链路：

```
数据记录 → 成长可视化 → 系统支持 → 可解释建议
```

### 1.2 业务目标

- 建立标准化评估流程：问卷筛查 → 静态体态 → 动态动作 → 体成分 → 训练与恢复
- 支持体测仪关键指标接入（体重、BMI、体脂率、内脏脂肪等级、骨骼肌率等）
- 通过分层架构保证可扩展性，支持后续接入更多设备与算法

### 1.3 个人成长闭环（落地版本）

按"记录 → 聚合 → 展示 → 复盘"闭环落地：

| 记录类型 | 核心字段 | 频次 |
|---------|---------|------|
| 每日身体数据 | 体重、体脂率、BMI | 每日 |
| 每日运动计划 | 结构化动作清单、时长、完成状态 | 每日 |
| 每日热量摄入 | 总热量 + 蛋白质/碳水/脂肪 | 每日 |
| 成长可视化 | 趋势图展示体重体脂、运动时长、热量摄入变化 | 实时 |
| 周期复盘 | 按周/月观察成长曲线并形成自我反馈 | 周/月 |

---

## 2. 已完成功能模块（Phase 01-13）

### 2.1 Phase 完成状态总览

| Phase | 功能模块 | 状态 | 核心能力 |
|-------|----------|------|----------|
| Phase 01 | 用户登录与注册 | ✅ 已完成 | JWT 认证、Token 管理、路由守卫 |
| Phase 02 | 评估中心基础能力 | ✅ 已完成 | 评估创建/查询/完成/报告 |
| Phase 03 | 体成分接入 MVP | ✅ 已完成 | 体成分录入、趋势、对比 |
| Phase 04 | 个人用户看板 MVP | ✅ 已完成 | 个人概览、评估摘要、体成分趋势 |
| Phase 05 | 每日三记录与成长分析 | ✅ 已完成 | 每日身体/运动/营养记录 |
| Phase 06 | 专业化仪表盘 | ✅ 已完成 | 健康画像、目标进度、预警标识 |
| Phase 07 | 热量摄入与运动计划一体化页面 | ✅ 已完成 | 统一工作台、差值提示、7天微趋势 |
| Phase 08 | AI 教练智能体 | ✅ 已完成 | 基础对话、审批机制、工具调用 |
| Phase 09 | AI 教练优化与多模态导入 | ✅ 已完成 | 多模态支持、记忆系统设计 |
| Phase 10 | 布局解耦与 Agent 对话体验升级 | ✅ 已完成 | 三栏布局、流式输出、过程可视化 |
| Phase 11 | AgentScope AI 后端系统重构 | ✅ 已完成 | ReActAgent、Tool Guard、记忆管理 |
| Phase 12 | Runtime 流式 UI 对齐 | ✅ 已完成 | 统一消息模型、重连补偿、审批按钮化 |
| Phase 13 | AutoContextMemory 记忆压缩 | ✅ 已完成 | 四层存储、6级压缩策略、智能摘要 |

### 2.2 技术栈基线

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI + SQLAlchemy + Alembic | 分层架构：API → Service → Repository → Model |
| 前端框架 | React + TypeScript + Vite | Feature-based 目录结构 |
| 图表库 | ECharts | 趋势图、对比图、进度图 |
| 数据库 | PostgreSQL（生产）/ SQLite（开发） | 统一 ORM，迁移脚本管理 |
| Agent 运行时 | AgentScope ReActAgent | 工具调用、审批机制、记忆管理 |
| LLM 模型 | qwen3.5-plus（DashScope） | OpenAI 兼容协议，流式输出 |

---

## 3. Agent 功能现状详解

### 3.1 Agent 核心能力矩阵

| 能力 | 实现状态 | 技术方案 | 优先级 |
|------|----------|----------|--------|
| 健身问答 | ✅ 已实现 | AgentScope ReActAgent + Toolkit | P0 |
| 健康数据分析 | ✅ 已实现 | read_tools + analysis_tools | P0 |
| 训练建议生成 | ✅ 已实现 | 基于健康数据生成个性化建议 | P1 |
| 数据编辑（需审批） | ✅ 已实现 | write_tools + PendingAction + approve | P1 |
| 多模态图片识别 | ✅ 已实现 | multimodal_tools（食物/体重秤图片） | P1 |
| 流式对话 | ✅ 已实现 | SSE + Runtime 消息模型 | P0 |
| 记忆管理 | ✅ 已实现 | AutoContextMemory 四层存储 | P0 |
| 工具调用可视化 | ✅ 已实现 | ToolCallTimeline + 状态展示 | P1 |

### 3.2 Agent 工具定义

#### 数据读取工具（无需审批）

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `get_user_profile` | 获取用户基本信息 | `user_id` | 用户信息字典 |
| `get_health_metrics` | 获取健康指标趋势 | `user_id, days, metric_type` | 指标记录列表 |
| `get_workout_history` | 获取训练历史 | `user_id, days` | 训练记录列表 |
| `get_nutrition_history` | 获取营养摄入历史 | `user_id, days` | 营养记录列表 |
| `get_dashboard_summary` | 获取仪表盘摘要 | `user_id` | 仪表盘数据聚合 |

#### 数据编辑工具（需人工审批）

| 工具名 | 功能 | 输入 | 审批流程 |
|--------|------|------|----------|
| `update_daily_metrics` | 更新每日身体数据 | `user_id, record_date, data` | PendingAction → approve/edit/reject |
| `update_workout_plan` | 更新训练计划 | `user_id, record_date, plan` | PendingAction → approve/edit/reject |
| `update_nutrition` | 更新营养摄入 | `user_id, record_date, data` | PendingAction → approve/edit/reject |

#### 多模态工具

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `analyze_food_image` | 食物图片识别 | `image_base64` | 营养估算（热量、蛋白、碳水、脂肪） |
| `analyze_scale_image` | 体重秤图片识别 | `image_base64` | 体重数值识别 |

### 3.3 Agent 安全机制

| 安全要求 | 实现状态 | 技术方案 |
|----------|----------|----------|
| 敏感操作需人工审批 | ✅ 已实现 | Tool Guard + PendingAction + approve API |
| 用户健康数据脱敏 | ✅ 已实现 | PII 中间件 + 数据隔离 |
| Agent 对话历史持久化 | ✅ 已实现 | agent_sessions + agent_messages 表 |
| Agent 不直接写数据库 | ✅ 已实现 | 所有写操作通过 Tools + Repository |
| 工具调用风险扫描 | ✅ 已实现 | Tool Guard 规则引擎（deny/guard/allow） |

### 3.4 Agent 记忆系统架构

#### 四层存储架构（Phase 13 实现）

```
┌─────────────────────────────────────────────┐
│  1. Working Memory Storage（工作存储）        │
│     - 存储压缩后的消息                         │
│     - 用于实际 LLM 对话                       │
│     - Token 数量受控                          │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  2. Original Memory Storage（原始存储）       │
│     - 存储完整的未压缩历史                     │
│     - append-only 模式（只追加）              │
│     - 支持完整历史追溯                         │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  3. Offload Context Storage（卸载存储）       │
│     - Map<UUID, List<Msg>>                   │
│     - 存储卸载的大内容（工具输入/输出）        │
│     - 按需重新加载                            │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  4. Compression Events Storage（压缩事件）    │
│     - 记录所有压缩操作详细信息                 │
│     - 包括事件类型、时间戳、消息数、token消耗   │
└─────────────────────────────────────────────┘
```

#### 6 级渐进式压缩策略

| 策略级别 | 策略名称 | 压缩方式 | 适用场景 |
|----------|----------|----------|----------|
| 策略 1 | 压缩历史工具调用 | LLM 智能压缩工具调用历史 | 连续工具调用超过阈值 |
| 策略 2 | 卸载大消息 | 将大内容卸载到外部存储，用 UUID 替代 | 工具输入/输出超过阈值 |
| 策略 3 | 压缩历史对话轮次 | LLM 生成对话摘要 | 历史对话轮次超过阈值 |
| 策略 4 | 压缩 Plan 相关消息 | 最小压缩（仅保留简要描述） | Plan 执行相关消息 |
| 策略 5 | 全局摘要压缩 | LLM 生成全局对话摘要 | 前面策略无法满足 token 限制 |
| 策略 6 | 强制截断 | 强制截断最旧的消息 | 所有策略都无法满足 |

#### 压缩效果目标

- Token 成本降低：68.4%（实测目标）
- 原始历史完整保留：append-only 模式
- 压缩事件可审计：完整记录策略级别、前后对比、压缩比例

### 3.5 Agent 流式协议（Phase 12 实现）

#### SSE 事件类型

| 事件类型 | 说明 | 数据结构 |
|----------|------|----------|
| `message_start` | 开始一轮回复 | `{session_id}` |
| `thinking_delta` | 模型思考过程增量 | `{delta, sequence_number}` |
| `tool_event` | 工具调用事件 | `{tool_name, phase, input_preview, output_preview}` |
| `content_delta` | 最终回复正文增量 | `{delta, sequence_number}` |
| `pending_action` | 需审批操作 | `{action_id, tool_name, summary, payload}` |
| `message_end` | 本轮结束 | `{response_id, usage, memory_hits}` |
| `error` | 错误事件 | `{message}` |

#### 重连补偿机制

- run 级 buffer：StreamTracker 维护事件缓冲
- reconnect 参数：`run_id + last_seq` 支持断线重连
- 去重机制：按 `sequence_number` 去重与补偿

---

## 4. 前端设计现状详解

### 4.1 页面结构总览

| 页面路由 | 功能 | 核心组件 |
|----------|------|----------|
| `/login` | 用户登录 | LoginForm、Token 管理 |
| `/register` | 用户注册 | RegisterForm、校验规则 |
| `/dashboard` | 个人看板 | HealthProfileCards、GoalProgressBoard、RiskAlertList |
| `/assessment-center` | 评估中心 | AssessmentList、AssessmentDetail、ReportSummary |
| `/body-composition` | 体成分管理 | BodyCompositionList、TrendChart、CompareView |
| `/daily-metrics` | 每日身体数据 | DailyMetricsForm、TrendChart |
| `/daily-energy-workout` | 热量与运动统一工作台 | WorkoutPlanEditor、NutritionEditor、EnergyGapCard |
| `/growth-analytics` | 成长分析 | GrowthTrendChart、WeekSummary |

### 4.2 AI 侧边栏设计（AISidebar）

#### 三栏布局架构

```
AppShell
├── LeftNavPanel（可收缩）
├── MainViewport（独立滚动容器）
└── AgentDock（可手势收展，独立滚动容器）
```

#### Agent UI 架构

```
AISidebar
├── AgentHeaderTabs
│   ├── 会话 Tab
│   └── 历史对话 Tab
├── SessionPane
│   ├── MessageList
│   ├── ThinkingBlock（可折叠）
│   ├── ToolCallTimeline
│   └── PendingActionCard
├── HistoryPane
│   ├── SessionList
│   └── SessionPreview
└── ChatInput（文本 + 图片）
```

#### 关键交互特性

| 特性 | 实现状态 | 说明 |
|------|----------|------|
| 图片上传与预览 | ✅ 已实现 | ChatAttachmentPreview、base64 转换 |
| 流式消息渲染 | ✅ 已实现 | RuntimeBubbleList、delta 拼接 |
| Thinking 区块折叠 | ✅ 已实现 | RuntimeThinkingCard、可折叠展示 |
| 工具调用时间线 | ✅ 已实现 | ToolCallTimeline、started/completed/failed 状态 |
| 审批卡片交互 | ✅ 已实现 | PendingActionCard、approve/edit/reject 按钮 |
| 会话切换与历史回放 | ✅ 已实现 | SessionHistoryPanel、历史消息同构渲染 |
| 边缘滑动收展 | ✅ 已实现 | 手势交互、无显式按钮 |
| 独立滚动容器 | ✅ 已实现 | 三栏滚动隔离、无穿透 |

### 4.3 Runtime 消息模型（Phase 12 实现）

#### 统一消息类型

| 消息类型 | 说明 | 渲染组件 |
|----------|------|----------|
| `REASONING` | 模型思考过程 | RuntimeThinkingCard |
| `PLUGIN_CALL` | 工具调用 | RuntimeToolCard |
| `PLUGIN_CALL_OUTPUT` | 工具输出 | RuntimeToolCard |
| `MESSAGE` | 最终正文 | RuntimeOutputCard |
| `APPROVAL` | 待审批操作 | PendingActionCard |

#### 前端消息映射层

```
SSE Event (new + legacy)
   → normalize / mapper
      → RuntimeMessage[] / RuntimeMessagePatch
         → RuntimeBubbleList
            → ThinkingCard / ToolCard / OutputCard
```

#### 历史/实时同构

- 历史 API 返回后，先转换为 `RuntimeMessage[]` 再渲染
- 流式增量转换为同类型 `RuntimeMessagePatch` 再 merge
- 消除历史与实时展示差异

### 4.4 前端组件拆分（Phase 12 实现）

| 组件 | 功能 | 文件路径 |
|------|------|----------|
| `AISidebar` | Agent 聊天总装容器 | `webpage/src/features/ai-coach/AISidebar.tsx` |
| `ChatHeader` | 会话标题 + 动作组 | `webpage/src/features/ai-coach/ChatHeader.tsx` |
| `ChatMessageList` | 消息列表（模块化渲染） | `webpage/src/features/ai-coach/ChatMessageList.tsx` |
| `ToolCallTimeline` | 工具调用时间线 | `webpage/src/features/ai-coach/ToolCallTimeline.tsx` |
| `PendingActionCard` | 审批卡片 | `webpage/src/features/ai-coach/PendingActionCard.tsx` |
| `SessionHistoryPanel` | 历史会话抽屉 | `webpage/src/features/ai-coach/SessionHistoryPanel.tsx` |
| `RuntimeBubbleList` | 统一气泡列表 | `webpage/src/features/ai-coach/components/RuntimeBubbleList.tsx` |
| `RuntimeThinkingCard` | Thinking 卡片 | `webpage/src/features/ai-coach/components/RuntimeThinkingCard.tsx` |
| `RuntimeToolCard` | 工具卡片 | `webpage/src/features/ai-coach/components/RuntimeToolCard.tsx` |
| `RuntimeOutputCard` | 输出卡片 | `webpage/src/features/ai-coach/components/RuntimeOutputCard.tsx` |

### 4.5 前端压缩状态可视化（Phase 13 实现）

| 组件 | 功能 | 展示内容 |
|------|------|----------|
| `CompressionStatus` | 压缩状态可视化 | 当前 Token、已节省 Token、压缩比例、已执行策略 |
| `OriginalHistoryPanel` | 历史追溯面板 | 查看完整原始历史（未压缩） |
| `OffloadLoader` | 卸载内容加载按钮 | 按需加载卸载的大内容 |
| `CompressionTimeline` | 压缩事件时间线 | 压缩策略执行顺序、前后对比 |

---

## 5. Agent 待优化问题清单

### 5.1 性能与稳定性问题

| 问题 | 影响 | 优先级 | 建议优化方向 |
|------|------|--------|--------------|
| LLM API 调用延迟 | 用户等待时间长 | P0 | 流式响应优化、预加载缓存 |
| Token 消耗过大 | 成本增加 | P0 | 记忆压缩策略调优、摘要质量提升 |
| 弱网场景重连不稳定 | 流式输出中断 | P1 | StreamTracker 增强、自动重连优化 |
| 图片识别结果不稳定 | 数据偏差 | P1 | 置信提示、用户可编辑后确认 |

### 5.2 交互体验问题

| 问题 | 影响 | 优先级 | 建议优化方向 |
|------|------|--------|--------------|
| 工具调用过程展示复杂 | 用户认知负担 | P1 | 简化展示、默认折叠详情 |
| 审批入口认知负担 | 用户不知道该点哪里 | P1 | 输入区按钮为主入口、命令提示降级 |
| 压缩状态展示复杂 | 用户认知负担 | P2 | 简化展示、默认折叠详情 |
| 多轮对话上下文丢失 | 对话质量下降 | P1 | 记忆召回策略优化、Top-K 调整 |

### 5.3 技术架构问题

| 问题 | 影响 | 优先级 | 建议优化方向 |
|------|------|--------|--------------|
| 记忆召回噪声高 | 回答质量下降 | P1 | Top-K + score 阈值 + 去重策略 |
| 压缩策略误删关键信息 | 对话质量下降 | P1 | lastKeep 保护增强、摘要 Prompt 优化 |
| 工具护栏误拦截 | 用户操作阻塞 | P2 | 规则分级 + 审批兜底 + 审计日志 |
| Token 计数不准确 | 压缩触发时机错误 | P2 | 多种计数方法交叉验证 |

### 5.4 可扩展性问题

| 问题 | 影响 | 优先级 | 建议优化方向 |
|------|------|--------|--------------|
| 单 Agent 架构限制 | 复杂场景支持不足 | P2 | 多 Agent 协作编排（LangGraph） |
| 技能动态注册缺失 | 扩展性不足 | P2 | 技能（skills）动态注册与开关管理 |
| 多 workspace 隔离缺失 | 多用户场景支持不足 | P2 | 多 Agent workspace 隔离能力 |

---

## 6. 后续 Agent 优化建议

### 6.1 短期优化（P0）

| 优化项 | 目标 |
|--------|------|
| 流式响应延迟优化 | 用户等待时间降低 30% |
| 记忆压缩策略调优 | Token 成本降低至 70% |
| 弱网重连稳定性增强 | 断线重连成功率 95% |
| 多轮对话上下文保持 | 对话质量提升 20% |

### 6.2 中期优化（P1）

| 优化项 | 目标 |
|--------|------|
| 工具调用过程展示简化 | 用户认知负担降低 40% |
| 审批交互体验优化 | 审批成功率提升 30% |
| 记忆召回策略优化 | 回答质量提升 25% |
| 图片识别稳定性增强 | 识别准确率提升 20% |

### 6.3 长期优化（P2）

| 优化项 | 目标 |
|--------|------|
| 多 Agent 协作编排 | 支持复杂场景（训练计划生成、营养方案定制） |
| 技能动态注册系统 | 支持第三方技能接入 |
| 多 workspace 隔离 | 支持多用户并发场景 |
| ReMe 知识图谱集成 | 检索准确率提升 30% |

---

## 7. 技术债务与风险

### 7.1 技术债务清单

| 债务项 | 来源 | 影响 | 建议清理时机 |
|--------|------|------|--------------|
| 双轨协议并存（legacy + modern） | Phase 12 兼容策略 | 维护成本增加 | Phase 14 统一协议 |
| 手写 DOM 渲染残留 | Phase 08-10 遗留 | 性能瓶颈 | Phase 14 组件化重构 |
| 记忆管理器多版本并存 | Phase 09-13 演进 | 代码冗余 | Phase 14 统一记忆系统 |
| 审批流程多入口并存 | Phase 08-12 演进 | 用户认知负担 | Phase 14 统一审批入口 |

### 7.2 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM API 成本失控 | 预算超支 | Token 监控 + 压缩策略 + 成本预警 |
| Agent 误操作导致数据丢失 | 用户信任下降 | 审批机制 + 操作日志 + 数据备份 |
| 记忆压缩导致关键信息丢失 | 对话质量下降 | 原始存储完整保留 + lastKeep 保护 |
| 多模态识别隐私泄露 | 合规风险 | 图片脱敏 + 本地处理 + 用户授权 |

---

## 8. 参考资源

### 8.1 内部文档

- 项目大纲与体测数据基线：`.plan/plan_project_start/00-project-outline-and-metrics-baseline.md`
- 技术规范：`f:\fitagent\Specification.md`
- Phase 详细计划：`.plan/plan_project_start/phase-*.md`

### 8.2 外部参考

- AgentScope 文档：https://doc.agentscope.io/tutorial/task_memory.html
- AgentScope AutoContextMemory：https://java.agentscope.io/en/task/memory.html
- LangChain ConversationSummaryMemory：https://python.langchain.com.cn/docs/modules/memory/types/summary
- CoPaw Chat 页面参考：`f:\copaw\CoPaw\src\qwenpaw`

---

## 9. 总结

### 9.1 项目整体进展

- **已完成模块**：13 个 Phase，覆盖认证、评估、体成分、每日记录、仪表盘、AI 教练全链路
- **技术栈成熟度**：后端分层架构稳定，前端 Feature-based 结构清晰，Agent 运行时已落地
- **核心能力完备性**：健身问答、健康数据分析、训练建议、数据编辑（审批）、多模态、流式对话、记忆管理均已实现

### 9.2 Agent 功能成熟度

- **基础能力**：对话、工具调用、审批机制已稳定运行
- **进阶能力**：多模态、流式输出、记忆压缩已落地，但仍有优化空间
- **安全机制**：审批、脱敏、审计、隔离均已实现，符合安全要求

### 9.3 前端设计成熟度

- **布局架构**：三栏布局稳定，滚动隔离良好
- **交互体验**：流式渲染、工具可视化、审批交互已实现，但仍有简化空间
- **组件化程度**：Runtime 消息模型已落地，组件拆分清晰，但仍有手写 DOM 残留

### 9.4 后续优化重点

1. **短期**：性能优化（延迟、Token 成本、重连稳定性）
2. **中期**：交互优化（工具展示简化、审批体验、记忆召回）
3. **长期**：架构扩展（多 Agent 协作、技能动态注册、workspace 隔离）

---

**文档版本**：v1.0  
**更新日期**：2026-04-17  
**维护者**：Rogers 项目团队