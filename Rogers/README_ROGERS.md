# Rogers Agent v2.0 - 健身助手

简化版的多智能体健身助手，基于 AgentScope 框架。

## 主要变化

- ✅ 删除了复杂的 harness 模块依赖
- ✅ 使用 fakeredis 存储会话状态
- ✅ 保持 PipelineController 多智能体架构
- ✅ 简化的配置方案

## 快速开始

### 1. 安装依赖

```bash
cd Rogers
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.rogers.example .env

# 编辑 .env，填入你的 DashScope API Key
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 启动服务

```bash
python rogers_main.py
```

服务将在 `http://127.0.0.1:8000` 启动。

## 架构说明

### Pipeline 工作流

```
用户消息
    ↓
[Vision Agent] (仅当有图片时)
    ↓
[Master Agent] ──判断复杂度──→ 简单回复?
    ↓ 否
[Fanout] ──→ [Diet Analyst] (流式)
    │       └─→ [Training Analyst] (流式)
    ↓
[Master Agent] 汇总回复
```

### 智能体角色

1. **Vision Agent**: 分析图片内容
2. **Master Agent**: 路由 + 汇总
3. **Diet Analyst**: 饮食分析专家
4. **Training Analyst**: 训练分析专家

## API 文档

启动服务后访问 `http://127.0.0.1:8000/docs` 查看完整的 OpenAPI 文档。

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 信息 |
| `/health` | GET | 健康检查 |
| `/api/agent/health` | GET | Agent 健康检查 |
| `/api/agent/config` | GET | 配置状态 |
| `/api/agent/chat` | POST | 简单聊天 (非流式) |
| `/api/agent/sessions/{session_id}` | GET/DELETE | 会话管理 |
| `/process` | POST | AgentScope 流式对话 (WebSocket/SSE) |
| `/v1/chat/completions` | POST | OpenAI 兼容接口 |

### 简单聊天示例

```bash
curl -X POST http://127.0.0.1:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想制定一个健身计划",
    "session_id": "test-session-001"
  }'
```

### 使用 AgentScope 流式接口

AgentScope 提供的 `/process` 端点支持 WebSocket 和 SSE 流式输出。

```python
import httpx
import json

async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        "http://127.0.0.1:8000/process",
        json={
            "session_id": "my-session",
            "user_id": "user1",
            "messages": [
                {"role": "user", "content": "帮我分析一下我的饮食情况"}
            ]
        }
    ) as response:
        async for line in response.aiter_lines():
            if line:
                print(line)
```

## 项目结构

```
Rogers/
├── rogers_main.py              # 简化版主入口
├── .env.rogers.example         # 环境变量示例
├── README_ROGERS.md            # 本文档
├── app/
│   └── routers/
│       └── agent.py            # Agent API 路由 (已简化)
└── src/
    └── agents/
        ├── rogers_agent.py     # PipelineController (已重构)
        └── config.py           # 简化配置
```

## 配置说明

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DASHSCOPE_API_KEY` | 是 | - | 阿里云 DashScope API Key |
| `VISION_MODEL` | 否 | `qwen-vl-max` | 视觉模型名称 |
| `REASONING_MODEL` | 否 | `qwen-max` | 推理模型名称 |
| `HOST` | 否 | `127.0.0.1` | 服务监听地址 |
| `PORT` | 否 | `8000` | 服务监听端口 |
| `FANOUT_ENABLED` | 否 | `true` | 是否启用子Agent分析 |

## 从 v1.0 迁移

### 不再需要的模块

以下模块已被移除，不再依赖：
- `src/agents/harness/` (整个目录)
- `src/fitme/` (数据库相关)
- 复杂的用户认证系统

### 代码迁移示例

**旧版:**
```python
from src.agents.rogers_agent import create_user_agent, PipelineController
from src.agents.config import load_agent_config

agent_cfg = load_agent_config(user_id)
agent = await create_user_agent(user_id, api_key, db_memory=...)
```

**新版:**
```python
from src.agents.rogers_agent import create_rogers_agent, PipelineController

agent = await create_rogers_agent(api_key)
controller = PipelineController(api_key)
```

## 开发说明

### 运行测试

```bash
# 查看 agentdemo 中的测试示例
python ../agentdemo/agent_test.py
```

### 代码规范

- 使用类型提示
- 保持函数简洁
- 添加必要的文档字符串

## License

MIT
