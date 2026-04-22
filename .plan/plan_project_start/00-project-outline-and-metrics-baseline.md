# Rogers 项目大纲与体测数据基线

> 说明：本文件作为项目总览，沉淀“业务大纲 + 数据口径基线”。  
> 详细实现规范看 `f:\fitagent\Specification.md`，阶段执行看 `.plan/phase-*.md`。

## 1. 项目定位

Rogers 当前定位为“个人用户数据管理与成长可视化应用”，核心价值是帮助用户通过每日记录建立可持续的健康改进闭环：

- 数据记录：每天记录身体数据、运动计划和营养摄入。
- 成长可视化：通过趋势图和对比图直观看到阶段变化。
- 系统支持：沉淀可解释的数据分析与建议能力。

## 2. 业务目标

- 建立标准化评估流程：问卷筛查 -> 静态体态 -> 动态动作 -> 体成分 -> 训练与恢复。
- 支持体测仪关键指标接入（体重、BMI、体脂率、内脏脂肪等级、骨骼肌率等）。
- 通过分层架构保证可扩展性，支持后续接入更多设备与算法。

## 3. 个人成长闭环（落地版本）

Rogers 当前阶段以“每日三记录 + 仪表盘分析”为主，按“记录 -> 聚合 -> 展示 -> 复盘”的闭环落地：

1. 每日身体数据：体重、体脂率、BMI（首版极简 3 项）。
2. 每日运动计划：结构化动作清单、时长、完成状态。
3. 每日热量摄入：总热量 + 蛋白质/碳水/脂肪。
4. 成长可视化：趋势图展示体重体脂、运动时长、热量摄入变化。
5. 周期复盘：支持按周/月观察成长曲线并形成自我反馈。

## 4. 风险分层标准

- 红色（高风险）：存在疼痛/明显代偿/高风险体成分指标，先修复后强化。
- 黄色（中风险）：可训练，但需严格动作约束与负荷管理。
- 绿色（低风险）：按增肌/减脂/表现提升计划推进。

## 5. 技术约束与目录约定

- 后端目录固定：`Rogers`
- 前端目录固定：`webpage`
- 数据库：生产 `PostgreSQL`，本地开发可用 `SQLite`
- 后端：`FastAPI + SQLAlchemy + Alembic`
- 前端：`React + TypeScript + Vite + ECharts`

## 6. 体测数据基线（参考截图）

### 6.1 核心展示指标（首页卡片）

- 体脂率：`22.44 %`
- 体重：`88.65 kg`
- 骨骼肌率：`75`（设备展示口径）

### 6.2 体成分详情指标（字段建议）

| 分组 | 指标名 | 字段建议 | 单位 | 截图示例值 |
|---|---|---|---|---|
| 基础 | 体重 | `weight` | kg | 88.65 |
| 基础 | BMI | `bmi` | - | 27.98 |
| 脂肪 | 体脂率 | `body_fat_rate` | % | 22.44 |
| 肌肉 | 肌肉率 | `muscle_rate` | % | 72.89 |
| 脂肪 | 内脏脂肪等级 | `visceral_fat_level` | level | 8.9 |
| 水分 | 水分率 | `water_rate` | % | 57.4 |
| 骨骼 | 骨量 | `bone_mass` | kg | 4.14 |
| 代谢 | 基础代谢 | `bmr` | kcal | 1981 |
| 脂肪 | 脂肪量 | `fat_mass` | kg | 19.89 |
| 肌肉 | 肌肉量 | `muscle_mass` | kg | 64.62 |
| 肌肉 | 骨骼肌量 | `skeletal_muscle_mass` | kg | 43.94 |
| 肌肉 | 骨骼肌率 | `skeletal_muscle_rate` | % | 49.57 |
| 水分 | 水分量 | `water_mass` | kg | 50.8 |
| 蛋白 | 蛋白质量 | `protein_mass` | kg | 13.74 |
| 目标 | 理想体重 | `ideal_weight` | kg | 70 |
| 控制 | 体重控制量 | `weight_control` | kg | 18.45 |
| 控制 | 脂肪控制量 | `fat_control` | kg | 4.91 |
| 控制 | 肌肉控制量 | `muscle_control` | kg | 0 |
| 评估 | 体型 | `body_type` | text | 运动员偏胖 |
| 评估 | 营养状态 | `nutrition_status` | text | 营养过剩 |
| 评估 | 体年龄 | `body_age` | year | 30 |
| 蛋白 | 蛋白质率 | `protein_rate` | % | 15.49 |
| 脂肪 | 皮下脂肪 | `subcutaneous_fat_rate` | % | 18.89 |
| 基础 | 去脂体重 | `lean_body_mass` | kg | 68.76 |
| 心肺 | 燃脂心率 | `fat_burning_hr_range` | bpm-range | 118-157 |

> 备注：截图示例值用于字段校准与 UI 样式联调，最终以设备原始数据为准。

## 7. API 规划对齐（v1）

- 评估：`POST /api/v1/assessments`、`GET /api/v1/assessments/{id}`、`POST /api/v1/assessments/{id}/complete`、`GET /api/v1/assessments/{id}/report`
- 体成分：`POST /api/v1/body-composition`、`GET /api/v1/body-composition/trend`、`GET /api/v1/body-composition/compare`
- 体态：`POST /api/v1/posture-assessments`、`GET /api/v1/posture-assessments/{id}`、`GET /api/v1/posture-assessments/{id}/risk-tags`
- 个人看板：
  - `GET /api/v1/dashboard/me`（聚合接口：当前用户概览、最新评估、体成分摘要、趋势）
  - `GET /api/v1/analytics/me`（个人分析：趋势与对比的可视化口径接口，必要时与 dashboard 拆分）
- 每日记录（新增）：
  - `PUT /api/v1/daily-metrics/{record_date}`、`GET /api/v1/daily-metrics`
  - `PUT /api/v1/daily-workout/{record_date}`、`GET /api/v1/daily-workout`
  - `PUT /api/v1/daily-nutrition/{record_date}`、`GET /api/v1/daily-nutrition`

## 8. 智能体能力规划

### 8.1 智能体定位

Rogers 智能体定位为"健身教练助手"，核心能力：

- **训练建议生成**：基于用户健康数据自动生成个性化训练计划
- **健康数据分析**：分析体重、体脂、运动时长趋势，给出改进建议
- **行为提醒**：自动识别"3天未训练"、"体脂连续上升"等异常情况
- **问答交互**：解答用户关于健身、营养、恢复的问题

### 8.2 技术选型

| 能力 | 推荐框架 | 理由 |
|------|----------|------|
| 健身问答助手 | AgentScope `ReActAgent` | 统一推理-工具调用闭环，便于流式输出 |
| 训练建议生成 | AgentScope `Toolkit` + Tool Guard | 工具调用可审计，敏感操作可审批 |
| 多维度健康分析 | AgentScope 多工具编排 | 在单 Agent 架构下实现分步骤分析 |
| 长期记忆对话 | AgentScope Memory Manager | 支持短期/工作/长期记忆分层 |

### 8.3 智能体工具定义

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `get_user_health_data` | 获取用户健康数据 | `user_id` | 健康数据字典 |
| `get_user_workout_history` | 获取训练历史 | `user_id`, `days` | 训练记录列表 |
| `create_workout_plan` | 创建训练计划 | `goal`, `level` | 计划文本 |
| `analyze_health_trend` | 分析健康趋势 | `user_id`, `metric_type` | 分析结果 |
| `send_notification` | 发送通知 | `user_id`, `message` | 发送状态 |

### 8.4 智能体安全要求

- 敏感操作（发送通知、修改计划）需人工审批
- 用户健康数据传入 Agent 前需脱敏
- Agent 对话历史持久化，支持审计
- 禁止 Agent 直接写数据库，必须通过 Tools
- 工具调用前必须经过 Tool Guard 风险扫描与策略拦截

## 9. 与阶段计划关系

| Phase | 功能模块 | 状态 | 计划文档 |
|-------|----------|------|----------|
| Phase 01 | 用户登录与注册 | ✅ 已完成 | `phase-01-auth-login-register.md` |
| Phase 02 | 评估中心基础能力 | ✅ 已完成 | `phase-02-core-assessment-foundation.md` |
| Phase 03 | 体成分接入 MVP | ✅ 已完成 | `phase-03-body-composition-mvp.md` |
| Phase 04 | 个人用户看板 MVP | ✅ 已完成 | `phase-04-personal-dashboard-mvp.md` |
| Phase 05 | 每日三记录 + 成长分析 | ✅ 已完成 | `phase-05-daily-tracking-and-growth-analytics.md` |
| Phase 06 | 专业仪表盘与健康卡片 | ✅ 已完成 | `phase-06-dashboard-professional-insights.md` |
| Phase 07 | 每日运动与热量统一页面 | ✅ 已完成 | `phase-07-daily-energy-and-workout-unified-page.md` |
| Phase 08 | AI 教练智能体 | ✅ 已完成 | `phase-08-ai-coach-agent.md` |
| Phase 09 | AI 教练优化与多模态导入 | ✅ 已完成 | `phase-09-ai-coach-optimization.md` |
| Phase 10 | 布局解耦与 Agent 对话体验升级 | ✅ 已完成 | `phase-10-layout-and-agent-chat-experience.md` |
| Phase 11 | AgentScope AI 后端系统重构 | 🔄 规划中 | `phase-11-agentscope-ai-backend-system.md` |

### Phase 08 详细规划

Phase 08 目标：实现 AI 教练智能体，核心能力：

1. **健身问答**：解答用户关于健身、营养、恢复的问题
2. **健康数据分析**：分析体重、体脂、运动时长趋势
3. **训练建议生成**：基于健康数据生成个性化训练建议
4. **数据编辑**：帮助用户修改每日记录数据（需人工审批）

技术方案：
- 后端：AgentScope `ReActAgent` + `Toolkit` + Tool Guard
- 前端：右侧 AI 侧边栏（320px，可折叠）
- 安全：敏感操作需人工审批，数据隔离

详见：`.plan/phase-08-ai-coach-agent.md`
