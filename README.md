# FitAgent - 健身管理平台

## 功能

| 模块 | 功能 |
|------|------|
| Dashboard | 今日概览、本周训练统计、营养摄入进度 |
| Health | 体重/体脂/BMI 记录、历史数据查看、数据导出 |
| Training | 训练计划管理、本周进度追踪、推荐训练 |
| Diet | 饮食记录管理、营养摄入统计、推荐食物 |
| User | 个人信息编辑、健身目标设置 |

## 使用方法

### 后端启动

```bash
# 安装依赖并启动（自动创建 SQLite 数据库）
cd rogers/app
pip install -r requirements.txt
python run.py
```

后端地址: http://localhost:8000  
API 文档: http://localhost:8000/docs

### 前端启动

```bash
# 安装依赖
cd console
npm install

# 启动开发服务器
npm run dev
```

前端地址: http://localhost:3000