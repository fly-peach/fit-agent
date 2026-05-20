# FitAgent — AI 健身管理平台

AI 驱动的全栈健身管理平台，帮你制定训练计划、记录饮食、追踪健康数据，并通过智能 Agent 对话获取个性化建议与训练成果卡片。

## 功能

### 📊 健康追踪
记录体重、体脂、BMI 等身体指标，自动生成趋势变化图表，直观掌握身体变化。

### 🏋️ 训练管理
- 创建/编辑训练计划，设定训练类型、强度、时长
- 日历视图查看每月训练安排，点击日期查看详情
- 打卡完成记录，追踪训练进度
- AI 智能推荐训练方案

### 🥗 饮食记录
- 日历式饮食日志，按日期查看每餐记录
- 记录每餐热量及蛋白质/碳水/脂肪等宏量营养素
- 内置 295 种常见食物库，支持自定义食物
- 自动汇总每日营养摄入统计

### 🤖 AI 智能助手
多 Agent 对话系统，基于 AgentScope 架构：

| Agent | 职责 |
|-------|------|
| **Master Agent** | 主对话 Agent，理解用户意图，调度专项 Agent |
| **Diet Analyst** | 饮食分析 Agent，解读营养数据与饮食习惯 |
| **Training Analyst** | 训练分析 Agent，评估训练效果与进展 |
| **Card Generator** | 训练成果卡片生成，支持视觉化呈现 |

**Agent 可用工具：**
- `analyze_image` — 图片识别与分析（支持本地/网络图片输入）
- `execute_fitme_command` — 执行健身相关 CLI 命令，直接查询/创建/更新用户数据
- 技能树系统 — 动态加载的领域特定能力

### 🃏 AI 训练卡片
- 自动生成视觉化的训练成果卡片
- 支持杂志风、简约、现代等多种模板
- 一键归档至个人成果墙，随时回顾历史

### 📱 多端支持
- Web 端（React + Ant Design）
- 移动端（React Native + Expo）

## Skill 技能树系统

FitAgent 内置灵活的技能树架构，Agent 可动态加载领域特定能力：

| 技能 | 说明 |
|------|------|
| `fitme-training-results` | 训练成果卡片生成，包含多模板（杂志/简约/现代/经典） |
| （更多技能开发中） | |

技能树位于 `Rogers/src/agents/harness/templates/skills/`，每个技能独立目录，包含 `SKILL.md` 定义元数据与提示词，Agent 按需加载。

## 快速开始

### 后端
```bash
cd Rogers
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env，填入 JWT_SECRET_KEY 和 CORS_ORIGINS
python run.py          # 首次启动自动初始化数据库
```

### 前端开发模式
```bash
cd console
npm install
npm run dev            # → http://localhost:3000
```

### 前端生产构建（嵌入后端）
```bash
cd Rogers
python scripts/build_console.py
# 访问 http://localhost:8000 即可使用
```

### 移动端
```bash
cd mobile
npm install
npx expo start
```


## 测试账户

首次启动自动创建：
```
邮箱: user@test.com
密码: password123
```

## Tech Stack

- **后端**: Python 3.10+, FastAPI, SQLAlchemy 2.0, PyJWT
- **AI Agent**: AgentScope Runtime, DashScope LLM
- **前端**: React 18, TypeScript, Vite 5, Ant Design 5, Recharts
- **移动端**: React Native 0.81, Expo 54
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
