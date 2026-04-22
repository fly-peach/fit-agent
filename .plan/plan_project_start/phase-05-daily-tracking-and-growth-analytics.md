# Phase 05 开发计划：每日三记录与成长分析

## 1. 阶段目标

- 将产品主流程切换为“个人用户每日数据管理”。
- 提供三类按天记录能力：身体数据、运动计划、热量摄入。
- 在个人看板提供成长趋势可视化，帮助用户进行周/月复盘。

## 2. 范围（In Scope）

### 2.1 后端

- 每日身体数据接口：`PUT/GET /api/v1/daily-metrics`
- 每日运动计划接口：`PUT/GET /api/v1/daily-workout`
- 每日热量摄入接口：`PUT/GET /api/v1/daily-nutrition`
- 统一响应：`code/message/data`
- 看板聚合扩展成长分析字段：`growth_analytics`

### 2.2 前端

- 页面结构：侧边栏 + 主栏（浅蓝 + 白色）
- 新增页面：
  - `/daily-metrics`
  - `/daily-workout`
  - `/daily-nutrition`
  - `/growth-analytics`
- 仪表盘页面改成个人成长概览入口

## 3. 关键设计决策

- 每日身体数据首版字段：体重、体脂率、BMI（极简 3 项）。
- 每日热量记录粒度：总热量 + 蛋白质/碳水/脂肪。
- 每日记录策略：按天唯一 Upsert（同用户同日覆盖更新）。
- 每日运动计划：结构化动作清单（动作名/组数/次数/时长）。

## 4. 数据模型

- `daily_metrics(user_id, record_date, weight, body_fat_rate, bmi)`
- `daily_workout_plans(user_id, record_date, plan_title, items, duration_minutes, is_completed, notes)`
- `daily_nutritions(user_id, record_date, calories_kcal, protein_g, carb_g, fat_g, notes)`
- 三张表均添加唯一约束：`(user_id, record_date)`

## 5. 验收标准（Definition of Done）

- 用户可在三个页面按日期保存每日记录，重复提交会覆盖更新。
- 可在列表查看最近记录，且数据归属隔离（只能看自己）。
- `/dashboard/me` 返回成长分析数据，前端可展示趋势图例。
- 后端新增接口具备集成测试覆盖，前端构建通过。

## 6. 风险与注意项

- SQLite 与 PostgreSQL 在日期/JSON 行为可能有细微差异，需通过测试兜底。
- 前端图例首版先保证可读与可用，复杂图形效果放后续迭代。
- 旧模块（评估中心、体成分）继续保留，避免对既有流程回归影响。
