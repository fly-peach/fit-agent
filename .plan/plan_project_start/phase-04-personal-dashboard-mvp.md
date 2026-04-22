# Phase 04 开发计划：个人用户看板 MVP（Personal Dashboard）

## 1. 阶段目标

- 交付个人用户可见价值的最小闭环看板：
  - 登录后进入 `/dashboard` 即可看到个人概览、最新评估、体成分摘要、趋势与对比。
- 对齐现有数据链路：
  - 评估（Phase 02）+ 体成分（Phase 03）→ 看板聚合展示（Phase 04）。
- 保持“个人用户自助”口径：
  - 所有数据默认仅与当前登录用户绑定，不引入教练/管理端视角。

## 2. 范围（In Scope）

### 2.1 后端 API 与功能

- `GET /api/v1/dashboard/me`
  - 聚合返回个人看板所需数据（减少前端多次请求与状态拼装成本）。
- `GET /api/v1/analytics/me`（可选）
  - 返回趋势与对比所需的结构化数据（若 dashboard 接口过重可拆分）。

### 2.2 前端页面与功能

- `/dashboard` 个人看板页面
  - 顶部概览卡：昵称/联系方式、最近更新时间
  - 最新评估卡：状态、风险等级、建议摘要、跳转评估中心
  - 体成分摘要卡：体重、BMI、体脂率、骨骼肌率（优先从最新体成分记录取）
  - 趋势图：体重（`weight`）与体脂率（`body_fat_rate`）折线图
  - 最近两次对比：展示变化值与变化率（体重/体脂率至少覆盖）

## 3. 不在本阶段（Out of Scope）

- 训练计划生成与训练执行记录（留给后续阶段）。
- 体态/动作筛查的完整采集与评分引擎（留给后续阶段）。
- 多角色权限矩阵与团队协作功能（教练/管理员端）。

## 4. 后端设计

### 4.1 `GET /api/v1/dashboard/me` 响应结构（建议）

- `me`
  - `id`、`name`、`email`、`phone`
- `latest_assessment`（可空）
  - `id`、`status`、`risk_level`、`report_summary`、`created_at`、`completed_at`
- `body_composition_summary`（可空）
  - `latest`（可空）：最新体成分记录核心字段（`measured_at` + 常用指标）
  - `trend`：至少返回 `weight` 与 `body_fat_rate` 的序列数据
  - `compare`（可空）：最近两次记录对比（差值、变化率、tags）

### 4.2 权限规则

- 仅允许当前登录用户获取自己的看板数据。
- 所有聚合数据查询都必须以 `current_user.id` 作为硬过滤条件。

## 5. 前端设计

### 5.1 目录落位

- Pages：`webpage/src/pages/dashboard/DashboardPage.tsx`
- API：`webpage/src/shared/api/dashboard.ts`
- 图表（Phase 04 引入）：ECharts（沿用项目基线）

### 5.2 UI 交互

- 深色卡片布局与现有主题保持一致。
- 看板首屏避免空白：
  - 没有评估时给出“新建评估”按钮入口。
  - 没有体成分记录时给出“录入体成分”入口（Phase 03 页面）。

## 6. 任务拆解

### 6.1 后端任务

1. 新增 dashboard/analytics 聚合接口（只读）。
2. 复用现有 assessments 与 body-composition 的查询逻辑，封装到 service 层。
3. 增加测试覆盖：
   - 未登录访问失败
   - 无数据时返回空结构
   - 有数据时返回完整结构

### 6.2 前端任务

1. 新增 `shared/api/dashboard.ts` 封装接口与类型。
2. 重做 `/dashboard` 页面为个人看板布局：
   - 最新评估卡 + 快捷入口
   - 体成分摘要卡 + 趋势图 + 对比卡
3. 空状态与错误态处理（可读文案、可操作入口）。

## 7. 验收标准（Definition of Done）

- 登录后进入 `/dashboard` 可看到个人看板页面，不出现空白与报错。
- 无评估/无体成分记录时展示空状态引导入口。
- 有数据时：
  - 展示最新评估摘要
  - 展示体重/体脂率趋势图
  - 展示最近两次体成分对比（至少体重与体脂率）
- 接口与前端字段命名一致，测试覆盖通过。

