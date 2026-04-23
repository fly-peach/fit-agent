# FitAgent - 健身管理平台

基于 FastAPI + React + Ant Design 的健身管理平台。

## 项目结构

```
fitagent/
├── rogers/                 # 后端 (FastAPI)
│   ├── app/                # API 应用入口
│   │   ├── app/
│   │   │   ├── routers/    # API 路由
│   │   │   └── core/       # 配置
│   │   ├── api_doc.md      # API 文档
│   │   ├── database_schema.md
│   │   ├── requirements.txt
│   │   └── run.py
│   └── src/
│       ├── fitme/          # 核心业务
│       │   ├── core/       # 配置
│       │   ├── models/     # SQLAlchemy 模型
│       │   ├── schemas/    # Pydantic 模型
│       │   ├── services/   # 业务服务
│       │   └── utils/      # 工具函数
│       └── agent/          # AI Agent 模块
│   └── README.md
│
├── console/                # 前端 (React + Ant Design)
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   ├── Dashboard/  # 仪表盘
│   │   │   ├── Health/     # 健康数据
│   │   │   ├── Training/   # 训练计划
│   │   │   ├── Diet/       # 饮食管理
│   │   │   ├── User/       # 个人中心
│   │   │   └── Login/      # 登录页
│   │   ├── services/       # API 服务
│   │   ├── components/     # 公共组件
│   │   ├── hooks/          # React Hooks
│   │   ├── styles/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
│
├── mobile/                 # 移动端 (待开发)
├── design/                 # 设计文件
└── webpage/                # 网页设计
```

## 功能模块

| 模块 | 功能 |
|------|------|
| Dashboard | 今日概览、本周训练统计、营养摄入进度 |
| Health | 体重/体脂/BMI 记录、历史数据、数据导出 |
| Training | 训练计划管理、本周进度、推荐训练 |
| Diet | 饮食记录管理、营养摄入统计、推荐食物 |
| User | 个人信息编辑、健身目标设置 |

## 技术栈

**后端:** FastAPI, SQLAlchemy, PyMySQL, PyJWT, Passlib

**前端:** React 18, Ant Design 5, TypeScript, Vite, Axios

**数据库:** MySQL 8.0+

---

## 后端启动

```bash
# 1. 安装依赖
cd rogers/app
pip install -r requirements.txt

# 2. 配置数据库
# 修改 src/fitme/core/config.py 中的 DATABASE_URL
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/fitagent

# 3. 创建数据库
mysql -u root -p -e "CREATE DATABASE fitagent CHARACTER SET utf8mb4;"

# 4. 初始化表结构
cd rogers/app
python -c "
import sys
sys.path.insert(0, '../src')
from fitme.models import Base
from fitme.utils.database import engine
Base.metadata.create_all(engine)
"

# 5. 启动服务
python run.py
```

**后端地址:**
- API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 前端启动

```bash
# 1. 安装依赖
cd console
npm install

# 2. 启动开发服务器
npm run dev
```

**前端地址:** http://localhost:3000

前端通过 Vite proxy 自动转发 `/api` 请求到后端 `http://localhost:8000`。

---

## API 端点

### 认证
- `POST /api/auth/login` - 登录
- `POST /api/auth/logout` - 登出

### 用户
- `GET /api/user/profile` - 获取用户信息
- `PUT /api/user/profile` - 更新用户信息
- `GET /api/user/settings` - 获取设置
- `PUT /api/user/settings` - 更新设置

### 健康数据
- `GET /api/health/metrics` - 获取健康指标
- `POST /api/health/metrics` - 创建记录
- `GET /api/health/measurements` - 历史记录
- `GET /api/health/report` - 健康报表
- `GET /api/health/export` - 导出数据

### 训练计划
- `GET /api/training/stats/weekly` - 本周统计
- `GET /api/training/schedule/weekly` - 本周安排
- `GET /api/training/progress/weekly` - 本周进度
- `GET /api/training/recommendations` - 推荐训练
- `POST /api/training/plans` - 创建计划
- `PUT /api/training/plans/{id}` - 更新计划
- `POST /api/training/complete/{id}` - 完成训练
- `DELETE /api/training/plans/{id}` - 删除计划

### 饮食管理
- `GET /api/diet/stats/today` - 今日统计
- `GET /api/diet/meals/today` - 今日记录
- `POST /api/diet/meals` - 添加记录
- `PUT /api/diet/meals/{id}` - 更新记录
- `DELETE /api/diet/meals/{id}` - 删除记录
- `GET /api/diet/nutrition/progress` - 营养进度
- `GET /api/diet/recommendations` - 推荐食物
- `GET /api/diet/trend/weekly` - 本周趋势

---

## 数据库表

| 表名 | 说明 |
|------|------|
| users | 用户表 |
| user_settings | 用户设置表 |
| health_metrics | 健康指标记录表 |
| training_plans | 训练计划表 |
| training_records | 训练完成记录表 |
| diet_meals | 饮食记录表 |
| streak_stats | 连续记录统计表 |
| daily_diet_summary | 每日饮食汇总表 |
| recommended_trainings | 推荐训练表 |
| recommended_foods | 推荐食物表 |

---

## 开发

### 后端开发

添加新模块:
1. `src/fitme/schemas/` - 创建 Pydantic 模型
2. `src/fitme/services/` - 创建服务函数
3. `app/app/routers/` - 创建 API 路由
4. `app/app/main.py` - 注册路由

### 前端开发

添加新页面:
1. `console/src/pages/` - 创建页面组件
2. `console/src/services/` - 创建 API 服务
3. `console/src/App.tsx` - 添加路由

---

## License

MIT