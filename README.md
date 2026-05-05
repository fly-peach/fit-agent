# FitAgent - AI 健身管理平台

AI 驱动的健身管理平台，帮你制定训练计划、记录饮食、追踪健康数据，并提供智能对话助手。

## 功能

- **健康追踪** — 记录体重、体脂、BMI，查看趋势变化
- **训练管理** — 创建训练计划，追踪完成进度，获取 AI 推荐
- **饮食记录** — 记录每餐营养，自动计算热量与宏量营养素
- **AI 助手** — 智能对话，回答健身问题，提供个性化建议
- **小红书运营** — AI 辅助发布内容、互动管理（Skill 扩展）

## 项目结构

```
fitagent/
├── rogers/          # 后端 (FastAPI + SQLAlchemy)
│   ├── app/         #   FastAPI 应用、路由、启动逻辑
│   ├── src/
│   │   ├── fitme/   #   核心业务：模型、服务、数据库
│   │   └── agents/  #   AI Agent 框架：技能、记忆、会话
│   ├── scripts/     #   数据库初始化脚本 & 种子数据 (JSON)
│   ├── data/        #   SQLite 数据库 (gitignore)
│   └── run.py       #   启动入口
├── console/         # 前端 (React + Vite + TypeScript)
└── mobile/          # 移动端 (React Native + Expo)
```

## 快速开始

### 1. 后端

```bash
cd rogers
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入必填项（见下方配置说明）
python run.py
```

首次启动自动初始化数据库（建表 + 导入动作库和食物库种子数据）。

### 2. 前端

```bash
cd console
npm install
npm run dev
```

访问 http://localhost:3000

### 3. 移动端

```bash
cd mobile
npm install
npx expo start
```

## 配置

复制 `.env.example` 为 `.env` 并填入实际值。未配置必填项时应用拒绝启动。

| 变量 | 说明 | 必填 |
|------|------|------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | 是 |
| `CORS_ORIGINS` | 允许的跨域域名（逗号分隔） | 是 |
| `DASHSCOPE_MODEL` | 默认模型 | 否（默认 qwen-turbo） |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 | 否 |
| `OPENAI_MODEL` | OpenAI 兼容模型名 | 否 |

生成 JWT 密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 模型选择

在「Agent 配置」页面选择模型并填入 API Key：

| 模型 | 速度 | 精度 | 适用场景 |
|------|------|------|----------|
| qwen-turbo | 快 | 中 | 日常对话 |
| qwen-plus | 中 | 高 | 复杂问题 |
| qwen-max | 慢 | 高 | 专业分析 |

开启「思考模式」后 AI 会先分析再回答，结果更准确但响应稍慢。

**API Key 通过「Agent 配置」页面填入**，每个用户使用自己的 Key，不再从 `.env` 读取。

## 测试账户

首次启动自动创建：

```
邮箱: user@test.com
密码: password123
```

## 数据库

采用双库分离架构，首次启动自动初始化：

| 数据库 | 用途 | 位置 |
|--------|------|------|
| `fitbase.db` | 系统预置数据（动作库、食物库） | `rogers/data/` |
| `fituser.db` | 用户数据（账户、健康、训练、饮食） | `rogers/data/` |

手动初始化（通常不需要）：

```bash
cd rogers
python scripts/init_all.py        # 一键初始化
python scripts/init_base_db.py    # 仅基础库
python scripts/init_user_db.py --seed  # 仅用户库 + 测试账户
```

## API 文档

启动后访问 Swagger UI：http://localhost:8000/docs

## Tech Stack

- **后端**: FastAPI, SQLAlchemy, PyJWT, Pydantic Settings
- **AI Agent**: AgentScope Runtime, ReMe Memory
- **前端**: React, TypeScript, Vite, RainbowKit
- **移动端**: React Native, Expo
