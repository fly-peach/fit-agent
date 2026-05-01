# FitAgent - AI 健身管理平台

FitAgent 是一个 AI 驾动的健身管理平台，帮你制定训练计划、记录饮食、追踪健康数据。

## 功能

- **健康追踪** - 记录体重、体脂、BMI，查看趋势变化
- **训练管理** - 创建训练计划，追踪完成进度，获取 AI 推荐
- **饮食记录** - 记录每餐营养，自动计算热量摄入
- **AI 助手** - 智能对话，回答健身问题，提供个性化建议

## 安装

### 后端

```bash
cd Rogers
pip install -r requirements.txt
```

### 前端

```bash
cd console
npm install
```

## 配置模型

### 1. 配置 API Key

```bash
cd Rogers
cp .env.example .env
```

编辑 `.env` 文件：

```
DASHSCOPE_API_KEY=sk-你的密钥
```

从 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 获取 API Key。

### 2. 选择模型

在「Agent 配置」页面选择模型：

| 模型 | 速度 | 精度 | 适用场景 |
|------|------|------|----------|
| qwen-turbo | 快 | 中 | 日常对话 |
| qwen-plus | 中 | 高 | 复杂问题 |
| qwen-max | 慢 | 高 | 专业分析 |
| qwen2.5-72b-instruct | 慢 | 最高 | 高质量回答 |

### 3. 思考模式

开启「思考模式」后，AI 会先分析再回答，结果更准确但响应稍慢。

### 4. 个人 API Key（可选）

在「Agent 配置」页面填入个人 API Key，可获得更稳定的服务。优先级高于系统默认。

## 启动

```bash
# 后端 (端口 8000)
cd Rogers
python run.py

# 前端 (端口 3000)
cd console
npm run dev
```

访问 http://localhost:3000

## 测试账号

```
邮箱: user@test.com
密码: password123
```