# Agent 协作导航（Rogers）

本文件给后续协作者快速说明"文档在哪里、代码怎么做、哪些事不能踩坑"。

## 1. 文档入口（先看这里）

| 文档 | 路径 | 说明 |
|------|------|------|
| 项目大纲 | `.plan/00-project-outline-and-metrics-baseline.md` | 项目定位、业务闭环、技术约束、体测字段口径 |
| 项目规范 | `Specification.md` | 后端/前端分层、UI 风格、接口约定、智能体规范 |
| 阶段计划 | `.plan/plan_app_design/phase-*.md` | 应用设计阶段计划 |
| 阶段计划 | `.plan/plan_agent_optim/phase-*.md` | Agent 优化阶段计划 |
| 阶段计划 | `.plan/plan_project_start/phase-*.md` | 历史阶段记录 |
| 项目说明 | `README.md` | 启动方式、构建方式、技术栈概览 |

## 2. 当前工程结构

### 2.1 后端目录（Rogers）

```
Rogers/app/
├── api/v1/          # API 路由（auth, assessments, dashboard, daily-*）
├── services/        # 业务编排层
├── repositories/    # 数据访问层
├── models/          # ORM 模型（user, assessment, daily_*）
├── schemas/         # Pydantic DTO
├── core/            # 配置、安全、日志
├── db/              # 数据库会话
└── agent/           # AI 教练智能体（AgentScope Runtime）
    ├── runtime/             # ReActAgent、模型工厂、流式解析
    ├── tools/               # 工具定义（view_media + multimodal_tools 已合并）
    │   ├── definitions.py   # 工具 JSON Schema
    │   ├── read_tools.py    # 数据读取工具（含 analyze_body_composition）
    │   ├── write_tools.py   # 数据编辑工具（需审批）
    │   ├── analysis_tools.py # 分析工具
    │   └── multimodal.py    # 多模态工具（图片加载+分析）
    ├── guard/               # Tool Guard + 审批服务
    ├── memory/              # 记忆管理器
    ├── schemas/             # Agent DTO
    └── service/             # Agent 服务层
        ├── agent_service.py  # 对话服务
        └── session_service.py # 会话管理
```

### 2.2 前端目录（webpage）

```
webpage/src/
├── app/             # App 入口与 Shell
├── pages/           # 路由页面（dashboard, daily-*）
│   ├── dashboard/DashboardPage.tsx        # 仪表盘（含体成分摘要/对比卡片）
│   └── body-composition/                   # 体成分管理
│       ├── List.tsx       # 记录列表（卡片网格+日期/体型筛选）
│       ├── Detail.tsx     # 记录详情（6大指标分组+评估结果）
│       ├── Create.tsx     # 录入新记录（分组表单+自动计算）
│       ├── Trend.tsx      # 趋势分析（多指标 ECharts 折线图）
│       └── Compare.tsx    # 对比分析（雷达图+差异表格）
├── router/          # 路由配置与保护
├── shared/api/      # API 客户端封装（含 bodyComposition.ts）
├── store/           # Zustand 状态管理
└── features/        # 业务域组件
    ├── ai-coach/    # AI 教练组件
    │   ├── AISidebar.tsx         # AI 侧边栏主组件
    │   ├── ChatMessageList.tsx   # 对话消息列表（多模态渲染）
    │   ├── ChatInput.tsx         # 输入框（支持多模态上传）
    │   ├── MultimodalUpload.tsx  # 多模态上传组件
    │   ├── FoodRecognitionResult.tsx # 食物识别结果展示
    │   ├── PendingActionCard.tsx # 待审批操作卡片
    │   └── hooks/                # Agent hooks
    └── body-composition/         # 体成分通用组件
        ├── StatusTag.tsx          # 状态标签（优/标准/偏高/警戒等）
        ├── IndicatorCard.tsx      # 单指标卡片（值+状态+参考范围）
        ├── IndicatorGroup.tsx     # 指标分组（Collapse 面板）
        ├── MetricTrendChart.tsx   # 趋势折线图（支持双Y轴）
        └── CompositionCompareChart.tsx # 雷达对比图
```

## 3. 协作流程（强约束）

1. **开发前先读规范**：遵守 `Specification.md` 分层和接口规范
2. **任务执行以阶段文档为准**：不跳步，按 `.plan/phase-*.md` 执行
3. **接口变更先更新文档**：先改规范，再改代码
4. **提交前检查清单**：
   - 后端最小测试（关键路径验证）
   - 前端构建检查（`npm run build`）
   - 文档同步（README/plan/specification）

## 4. 前端构建与产物复制

### 4.1 Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-and-copy-web.ps1
```

### 4.2 Linux/macOS

```bash
bash scripts/build-and-copy-web.sh
```

## 5. 智能体开发规范（AgentScope + DashScope）

### 5.1 框架选型

| 场景 | 实现方式 |
|------|----------|
| 健身问答助手 | AgentScope `ReActAgent` |
| 多模态输入（图片/音频） | AgentScope + DashScope `qwen3.5-plus` |
| 工具调用（数据读取/编辑） | AgentScope `Toolkit` + 函数工具 |
| 敏感操作审批 | Tool Guard + `pending_actions` 审批流程 |

### 5.2 AgentScope 运行配置

```env
# Rogers/.env
DashScope_coding_URL=https://coding.dashscope.aliyuncs.com/v1
DashScope_coding_API_KEY=your-api-key
model=qwen3.5-plus
AGENT_FRAMEWORK=agentscope
AGENT_MAX_ITERS=8
```

### 5.3 多模态消息格式

```python
# 图片消息（AgentScope content block）
content = [
    {"type": "text", "text": "请分析这张食物图片并估算热量"},
    {"type": "image", "image": "data:image/jpeg;base64,{base64}"},
]
```

### 5.4 AgentScope 工具注册

```python
from agentscope.tool import Toolkit

toolkit = Toolkit()
# 读取工具：get_health_metrics, get_user_profile, get_workout_history,
#            get_nutrition_history, get_dashboard_summary, analyze_body_composition
toolkit.register_tool_function(get_health_metrics)
# 写入工具（需审批）：update_daily_metrics, update_workout_plan, update_nutrition
toolkit.register_tool_function(update_daily_metrics)
# 多模态：view_image, view_image_base64, analyze_food_image, analyze_scale_image
```

当前已注册工具清单（共 15 个）：

| 类别 | 工具名 | 说明 |
|------|--------|------|
| 读取 | `get_user_profile` | 用户信息 |
| 读取 | `get_health_metrics` | 健康指标历史（含 visceral_fat_level, bmr） |
| 读取 | `get_workout_history` | 训练计划历史 |
| 读取 | `get_nutrition_history` | 营养摄入历史 |
| 读取 | `get_dashboard_summary` | 仪表盘摘要 |
| 读取 | `analyze_body_composition` | 体成分综合评估（体型/评分/控制目标/指标等级） |
| 写入 | `update_daily_metrics` | 更新身体指标（需审批） |
| 写入 | `update_workout_plan` | 更新训练计划（需审批） |
| 写入 | `update_nutrition` | 更新营养摄入（需审批） |
| 多模态 | `view_image` | 加载本地图片到上下文 |
| 多模态 | `view_image_base64` | 加载 base64 图片到上下文 |
| 多模态 | `analyze_food_image` | 食物图片营养识别 |
| 多模态 | `analyze_scale_image` | 体重秤读数识别 |
| 分析 | `summarize_text` | 文本摘要 |
| 内置 | `get_weather` | 天气查询（示例） |

### 5.5 安全要求

- 敏感操作（修改用户数据）需用户审批
- 用户健康数据传入 Agent 前需脱敏
- Agent 对话历史持久化，支持审计
- 禁止 Agent 直接写数据库，必须通过 Tool Guard + 审批流程
- 每次对话携带用户身份，确保数据隔离

### 5.6 目录约定

```text
Rogers/app/agent/
├── runtime/
│   ├── react_agent.py      # AgentScope ReActAgent 封装
│   ├── model_factory.py    # DashScope 模型工厂
│   └── stream_parser.py    # SSE 流式解析器
├── tools/
│   ├── definitions.py      # 工具 JSON Schema 定义
│   ├── read_tools.py       # 数据读取工具（含 analyze_body_composition）
│   ├── write_tools.py      # 数据编辑工具实现
│   ├── analysis_tools.py   # 分析工具实现
│   └── multimodal.py       # 多模态工具（view_media + multimodal_tools 已合并）
├── guard/
│   ├── tool_guard.py       # 工具风险判定
│   └── approval_service.py # 审批服务
├── memory/
│   ├── manager.py          # 记忆管理器
│   └── retriever.py        # 长短期记忆检索
├── schemas/                # Agent DTO
└── service/                # Agent 服务层
```

## 6. Plan 编写模板

新建 plan 文档时，复制到 `.plan/plan_app_design/` 或 `.plan/plan_agent_optim/` 目录下，文件名格式 `phase-XX-<主题>.md`。

```markdown
# Phase XX: <标题>

> **目标**：一句话说明本阶段要达成什么。

> **规范引用**：本阶段实现需遵循 `Specification.md` 第 X 节「XXX」。

---

## 1. 背景与动机

### 1.1 现状

| 文件/模块 | 当前状态 | 问题 |
|-----------|----------|------|
| ... | ... | ... |

### 1.2 目标对标

描述要达到什么状态，对标什么参考（截图/竞品/规范）。

---

## 2. 数据模型设计

### 2.1 ORM 模型变更

列出新增/修改的字段，说明类型和含义。

### 2.2 Schema 层

列出 Pydantic Schema 变更、枚举定义、分组定义等。

### 2.3 API 变更

列出新增或修改的 API 端点及变更内容。

---

## 3. 前端完整重构需求

### 3.1 设计目标

对比当前和目标的差异（UI 框架、布局、功能）。

### 3.2 页面 N: <页面名称>（重构/新增）

**文件**：`webpage/src/pages/.../Xxx.tsx`

**布局**：（用 ASCII 画出页面布局）

**具体需求**：
- 条目 1
- 条目 2
- ...

### 3.3 组件设计

列出需要新建的组件，给出 interface 定义。

### 3.4 API 层更新

列出前端 API 文件的变更。

---

## 4. 核心计算逻辑（后端 Service）

给出关键算法的代码片段（Python），如体型判定、评分计算等。

---

## 5. 实施步骤

### Step 1: <步骤名>

| # | 任务 | 文件 |
|---|------|------|
| 1.1 | ... | `path/to/file` |
| 1.2 | ... | `path/to/file` |

### Step 2: <步骤名>

| # | 任务 | 文件 |
|---|------|------|
| 2.1 | ... | `path/to/file` |

（按需增加 Step 3、4...）

---

## 6. 验收标准

### 6.1 后端

| 验收项 | 标准 | 验证方式 |
|--------|------|----------|
| ... | ... | ... |

### 6.2 前端

| 验收项 | 标准 | 验证方式 |
|--------|------|----------|
| ... | ... | ... |

### 6.3 Agent

| 验收项 | 标准 | 验证方式 |
|--------|------|----------|
| ... | ... | ... |

---

## 7. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| ... | ... | ... |

---

## 8. 里程碑

| 里程碑 | 交付物 |
|--------|--------|
| M1: ... | ... |
| M2: ... | ... |

---

**文档版本**: v1.0
**创建日期**: YYYY-MM-DD
**维护者**: Rogers 项目团队
```

**注意事项**：
- 表格**不写工时**，工时在任务执行时根据实际情况评估
- 每个页面需求必须包含 ASCII 布局图 + 具体需求条目
- 前端组件必须给出 TypeScript interface 定义
- 后端计算逻辑必须给出具体算法代码
- 验收标准必须可量化、可验证

---

## 7. 其他注意项

- 禁止把密码明文写入日志、埋点或示例数据
- 在开发过程中禁止使用npm install 命令，先改前端代码，若有重新install的需求在改完代码通知用户需要使用 npm install
- 认证接口与前端 token 字段命名必须保持一致
- 未经确认不要重置或覆盖他人已修改文件
- 若发现需求和规范冲突，以 `Specification.md` 为准并先更新文档
- AgentScope / DashScope API Key 禁止提交到代码仓库，必须使用 `.env` 配置
