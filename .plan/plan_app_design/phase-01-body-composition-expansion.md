# Phase 01: 体成分指标扩展 — 数据层 + 前端完整重构

> **目标**：将体成分模型从 10 项基础指标扩展到覆盖主流体脂秤的 21+ 项指标，
> 同时彻底重构前端体成分页面，从「简陋的表单+表格」升级为对标体脂秤 App 的「指标卡片 + 分组展示 + 趋势图 + 对比」体验。

> **规范引用**：后端遵循 `Specification.md` 第 4 节，前端遵循第 5 节「UI 组件规范」。

---

## 1. 现状分析

### 1.1 后端现状

`body_composition_records` 表只有 10 个指标：

| 字段 | 说明 |
|------|------|
| weight, bmi, body_fat_rate, visceral_fat_level | 体重/BMI/体脂率/内脏脂肪 |
| fat_mass, muscle_mass, skeletal_muscle_mass, skeletal_muscle_rate | 脂肪量/肌肉量/骨骼肌量/骨骼肌率 |
| water_rate, water_mass, bmr | 水分率/水分量/基础代谢 |

`daily_metrics` 表只有 `weight/bmi/body_fat_rate` 三项。

### 1.2 前端现状（问题）

| 页面 | 当前状态 | 问题 |
|------|----------|------|
| **体成分列表** [`List.tsx`](webpage/src/pages/body-composition/List.tsx) | 原生 HTML table，只显示 3 列（时间/体重/体脂率/BMI） | 无图表、无筛选、无状态标识 |
| **体成分创建** [`Create.tsx`](webpage/src/pages/body-composition/Create.tsx) | 4 个输入框（时间/体重/体脂率/BMI） | 仅 3 个指标可录入，大量字段缺失 |
| **体成分详情** [`Detail.tsx`](webpage/src/pages/body-composition/Detail.tsx) | 5 行 `<p>` 标签罗列 | 无分组、无状态标签、无趋势入口 |
| **仪表盘** [`DashboardPage.tsx`](webpage/src/pages/dashboard/DashboardPage.tsx) | 固定 3 个 mini-card（体重/体脂率/BMI） | 只展示 3 项，缺少健康画像卡片的数据源 |
| **每日数据** [`daily-metrics/Index.tsx`](webpage/src/pages/daily-metrics/Index.tsx) | 3 个输入框（体重/体脂率/BMI） | 同上，字段太少 |
| **前端组件库** | 未使用 Ant Design，纯手写 HTML | 与 Specification 要求不符 |

### 1.3 截图对标

截图展示的体脂秤 App 提供 25+ 项指标，分为 6 大组，每项带状态标签（优/标准/偏高/不足/警戒型）。

**扩展后后端总计：21 个指标字段**（10 个已有 + 11 个新增）。

---

## 2. 新增指标清单

| 类别 | 字段名 | 类型 | 单位 | 说明 |
|------|--------|------|------|------|
| 核心 | `muscle_rate` | float | % | 肌肉率 |
| 核心 | `bone_mass` | float | kg | 骨量 |
| 核心 | `protein_mass` | float | kg | 蛋白质重量 |
| 控制 | `ideal_weight` | float | kg | 理想体重 |
| 控制 | `weight_control` | float | kg | 体重控制量（+增/-减） |
| 控制 | `fat_control` | float | kg | 脂肪控制量 |
| 控制 | `muscle_control` | float | kg | 肌肉控制量 |
| 评估 | `body_type` | str | - | 体型（隐藏型肥胖/标准/肌肉型/肥胖/偏瘦/运动型偏胖） |
| 评估 | `nutrition_status` | str | - | 营养状态（不足/均衡/过剩） |
| 评估 | `body_age` | float | - | 体年龄 |
| 评估 | `subcutaneous_fat` | float | % | 皮下脂肪 |
| 衍生 | `fat_free_mass` | float | kg | 去脂体重 |
| 衍生 | `fat_burn_hr_low` | float | bpm | 燃脂心率下限 |
| 衍生 | `fat_burn_hr_high` | float | bpm | 燃脂心率上限 |

**daily_metrics 新增**：`visceral_fat_level`、`bmr`（用于日常趋势跟踪）。

---

## 3. 数据模型设计

### 3.1 ORM 模型变更

```python
# app/models/body_composition.py — 新增 14 个字段
muscle_rate: Mapped[float | None]          # 肌肉率 (%)
bone_mass: Mapped[float | None]             # 骨量 (kg)
protein_mass: Mapped[float | None]          # 蛋白质重量 (kg)
ideal_weight: Mapped[float | None]          # 理想体重 (kg)
weight_control: Mapped[float | None]        # 体重控制量 (kg, +增 -减)
fat_control: Mapped[float | None]           # 脂肪控制量 (kg)
muscle_control: Mapped[float | None]        # 肌肉控制量 (kg)
body_type: Mapped[str | None]               # 体型
nutrition_status: Mapped[str | None]        # 营养状态
body_age: Mapped[float | None]              # 体年龄
subcutaneous_fat: Mapped[float | None]      # 皮下脂肪 (%)
fat_free_mass: Mapped[float | None]         # 去脂体重 (kg)
fat_burn_hr_low: Mapped[float | None]       # 燃脂心率下限 (bpm)
fat_burn_hr_high: Mapped[float | None]      # 燃脂心率上限 (bpm)
```

### 3.2 Schema 层

```python
# app/schemas/body_composition.py — 新增
class BodyType(str, Enum):
    HIDDEN_OBESE = "隐藏型肥胖"
    STANDARD = "标准"
    MUSCLE = "肌肉型"
    OBESE = "肥胖"
    UNDERWEIGHT = "偏瘦"
    ATHLETIC = "运动型偏胖"

class NutritionStatus(str, Enum):
    DEFICIENT = "营养不足"
    BALANCED = "营养均衡"
    EXCESS = "营养过剩"

class IndicatorLevel(str, Enum):
    LOW = "不足"
    NORMAL = "标准"
    HIGH = "偏高"
    EXCELLENT = "优"
    WARNING = "警戒型"
    REDUCE = "减重"
    INCREASE = "增重"

# 指标分组定义（供前端动态渲染）
INDICATOR_GROUPS = {
    "body_composition": {
        "label": "身体成分",
        "icon": "BodyOutlined",
        "indicators": ["weight", "bmi", "body_fat_rate", "visceral_fat_level", "fat_mass"],
    },
    "muscle_bone": {
        "label": "肌肉骨骼",
        "icon": "FireOutlined",
        "indicators": ["muscle_mass", "skeletal_muscle_mass", "skeletal_muscle_rate", "muscle_rate", "bone_mass"],
    },
    "water_metabolism": {
        "label": "水分代谢",
        "icon": "DropletOutlined",
        "indicators": ["water_rate", "water_mass", "protein_mass"],
    },
    "metabolism": {
        "label": "代谢能力",
        "icon": "ThunderboltOutlined",
        "indicators": ["bmr", "fat_free_mass", "fat_burn_hr_low", "fat_burn_hr_high"],
    },
    "control_goals": {
        "label": "控制目标",
        "icon": "TargetOutlined",
        "indicators": ["ideal_weight", "weight_control", "fat_control", "muscle_control"],
    },
    "health_assessment": {
        "label": "健康评估",
        "icon": "HeartOutlined",
        "indicators": ["body_type", "nutrition_status", "body_age", "subcutaneous_fat"],
    },
}
```

### 3.3 API 变更

| 端点 | 变更 |
|------|------|
| `POST /body-composition` | 入参新增 14 个字段 |
| `GET /body-composition/{id}` | 出参新增 14 个字段 |
| `GET /body-composition` | 出参新增 14 个字段 |
| `GET /body-composition/trend` | 支持新 metric 类型 |
| **NEW** `GET /body-composition/evaluate/{id}` | 返回体型/营养状态/控制量等评估结果 |
| **NEW** `GET /body-composition/indicator-config` | 返回指标分组定义 + 状态标签规则 |

---

## 4. 前端完整重构需求

### 4.1 设计目标

| 维度 | 当前 | 目标 |
|------|------|------|
| UI 框架 | 手写 HTML | Ant Design 5.x 组件 |
| 体成分列表 | 3 列 table | 卡片列表 + 筛选 + 排序 |
| 体成分详情 | 5 行文字 | 6 组指标卡片 + 状态标签 + 趋势入口 |
| 体成分录入 | 4 个输入框 | 分组折叠表单 + 21 个字段 |
| 趋势图 | 无 | ECharts 折线图（支持多指标对比） |
| 对比功能 | 无 | 两次体测的雷达图对比 |
| 仪表盘 | 3 项硬编码 | 动态渲染健康画像 + 核心指标摘要 |

### 4.2 页面 1: 体成分列表页（重构）

**文件**：`webpage/src/pages/body-composition/List.tsx`

**布局**：
```
┌─────────────────────────────────────────────┐
│  体成分记录              [+ 录入新记录]       │
├─────────────────────────────────────────────┤
│  [筛选] 时间范围选择器  [指标类型下拉]        │
├─────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌─────────┐ │
│  │ 2026-03-21 │ │ 2026-03-14 │ │ ...     │ │
│  │ 88.65kg    │ │ 89.20kg    │ │         │ │
│  │ 体脂 22.4% │ │ 体脂 23.1% │ │         │ │
│  │ BMI 27.98  │ │ BMI 28.3   │ │         │ │
│  │ [查看详情]  │ │ [查看详情]  │ │         │ │
│  └────────────┘ └──────────── └─────────┘ │
└─────────────────────────────────────────────┘
```

**具体需求**：
- 使用 Ant Design `Card` 组件展示每条记录
- 每张卡片显示：日期、体重、体脂率、BMI、体型标签
- 顶部筛选栏：时间范围（DatePicker.RangePicker）、按体型筛选（Select）
- 卡片按时间倒序排列
- 点击卡片进入详情页
- 空状态：Ant Design `Empty` 组件

### 4.3 页面 2: 体成分详情页（重构）

**文件**：`webpage/src/pages/body-composition/Detail.tsx`

**布局**（对标截图）：
```
┌─────────────────────────────────────────────┐
│  ← 体成分详情              [对比] [趋势]     │
├─────────────────────────────────────────────┤
│  体测时间: 2026-03-21 12:22                  │
├─────────────────────────────────────────────┤
│  ┌─ 健康总览 ──────────────────────────────┐ │
│  │  体型: 运动型偏胖 [标签]                  │ │
│  │  健康评分: 75分                           │ │
│  │  营养状态: 营养过剩 [标签]                │ │
│  │  体年龄: 30 岁 (>实际) [标签]             │ │
│  └─────────────────────────────────────────┘ │
─────────────────────────────────────────────┤
│  ▼ 身体成分 (16项达标 ✓ | 1项偏低 ↓ | 8项偏高 ↑)
│  │                                          │ │
│  │  体重        88.65kg    [过重] v          │ │
│  │  BMI         27.98      [偏胖] v          │ │
│  │  体脂率      22.44%     [轻度肥胖] v      │ │
│  │  内脏脂肪     8.9       [警戒型] v         │ │
│  │  脂肪量      19.89kg    [轻度肥胖] v      │ │
│  └─────────────────────────────────────────┘ │
│  ▼ 肌肉骨骼                                   │
│  │  肌肉量      64.62kg    [优] v             │ │
│  │  骨骼肌重量  43.94kg    [标准] v           │ │
│  │  骨骼肌率    49.57%     [标准] v           │ │
│  │  肌肉率      72.89%     [优] v             │ │
│  │  骨量        4.14kg     [正常] v           │ │
│  └─────────────────────────────────────────┘ │
│  ▼ 水分代谢                                   │
│  │  水分率      57.4%      [标准] v           │ │
│  │  水分量      50.88kg    [标准] v           │ │
│  │  蛋白质重量  13.74kg    [标准] v           │ │
│  └─────────────────────────────────────────┘ │
│  ... 更多分组 ...                             │
└─────────────────────────────────────────────┘
```

**具体需求**：
- **顶部**：体测时间 + 两个操作按钮（对比/趋势）
- **健康总览区**：体型、健康评分、营养状态、体年龄 — 4 个关键评估结果，每个带 Ant Design `Tag` 状态标签
- **6 组指标**：使用 Ant Design `Collapse` 折叠面板，默认展开第 1 组
- **每项指标**：
  - 左侧：图标 + 指标名称
  - 中间：数值 + 单位
  - 右侧：状态标签（`Tag color` 根据 IndicatorLevel 自动着色：优=green, 标准=blue, 偏高=orange, 不足=cyan, 警戒型=red, 增重/减重=purple）
  - 点击展开：显示参考范围、趋势变化（与上次体测对比）
- **状态标签统计**：在 Collapse header 显示「16项达标 ✓ | 1项偏低 ↓ | 8项偏高 ↑」
- **底部操作**：`[保存为图片]` `[分享给好友]`（可选，Phase 2）

### 4.4 页面 3: 体成分录入页（重构）

**文件**：`webpage/src/pages/body-composition/Create.tsx`

**布局**：
```
┌─────────────────────────────────────────────┐
│  ← 录入体成分                               │
├─────────────────────────────────────────────┤
│  体测时间: [datetime picker]                 │
│  [ ] 从体脂秤导入（照片识别）                 │
├─────────────────────────────────────────────┤
│  ▼ 身体成分                                 │
│  │  体重(kg)        [_______]               │ │
│  │  体脂率(%)       [_______]               │ │
│  │  BMI             [_______] (自动计算)     │ │
│  │  内脏脂肪等级     [_______]               │ │
│  │  脂肪量(kg)      [_______]               │ │
│  └─────────────────────────────────────────┘ │
│  ▼ 肌肉骨骼                                   │
│  │  肌肉量(kg)      [_______]               │ │
│  │  ...                                     │ │
│  └─────────────────────────────────────────┘ │
│  ... 更多分组 ...                             │
├─────────────────────────────────────────────┤
│  [保存] [重置]                               │
└─────────────────────────────────────────────┘
```

**具体需求**：
- 使用 Ant Design `Form` + `Collapse` 分组表单
- BMI 自动计算（输入体重 + 用户身高自动算出，只读展示）
- 每个输入框带 placeholder 提示（如「例如：88.65」）
- 非必填字段默认折叠，用户可展开录入
- 表单验证：数值范围校验（体重 > 0，体脂率 0-60 等）
- 顶部可选「从体脂秤照片导入」— 调用 `analyze_scale_image` 工具自动填充体重
- 保存后跳转到详情页

### 4.5 页面 4: 体成分趋势页（新增）

**文件**：`webpage/src/pages/body-composition/Trend.tsx`

**布局**：
```
┌─────────────────────────────────────────────┐
│  ← 体成分趋势                               │
├─────────────────────────────────────────────┤
│  [体重 ▼] [近7天 ▼] [体重 + 体脂率]         │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐ │
│  │         ECharts 折线图                   │ │
│  │   (多指标叠加，带数据点)                  │ │
│  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│  统计摘要：                                  │
│  起始: 89.2kg → 当前: 88.65kg (↓0.55kg)     │
│  最高: 90.1kg  最低: 88.1kg                  │
└─────────────────────────────────────────────┘
```

**具体需求**：
- 指标选择器：下拉选择要展示的指标（体重/体脂率/BMI/肌肉量/脂肪量 等）
- 时间范围：近 7 天 / 近 30 天 / 近 90 天 / 自定义
- 多指标对比：可同时勾选 2-3 个指标，叠加显示在一张图上（双 Y 轴）
- ECharts 折线图：带数据点、tooltip、平滑曲线
- 底部统计摘要：起始值、当前值、变化量、最高/最低值
- 调用 `GET /body-composition/trend?metric=xxx` 获取数据

### 4.6 页面 5: 体成分对比页（新增）

**文件**：`webpage/src/pages/body-composition/Compare.tsx`

**布局**：
```
┌─────────────────────────────────────────────┐
│  ← 体成分对比                               │
├─────────────────────────────────────────────┤
│  记录A: [2026-03-21 ▼]   vs   记录B: [2026-02-21 ▼]
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐ │
│  │       ECharts 雷达图                     │ │
│  │   (A=蓝色, B=绿色, 面积重叠)              │ │
│  └─────────────────────────────────────────┘ │
─────────────────────────────────────────────┤
│  指标对比表：                                 │
│  ┌──────────┬────────┬──────────────────┐  │
│  │ 指标     │  记录A  │ 记录B   │  变化    │  │
│  ├──────────┼────────┼────────┼──────────┤  │
│  │ 体重     │ 88.65  │ 90.20  │ ↓1.55kg  │  │
│  │ 体脂率   │ 22.4%  │ 24.1%  │ ↓1.7%    │  │
│  │ 肌肉量   │ 64.62  │ 63.80  │ ↑0.82kg  │  │
│  └──────────┴────────┴────────┴──────────┘  │
└─────────────────────────────────────────────┘
```

**具体需求**：
- 两次体测记录选择器（从列表中选）
- ECharts 雷达图：A/B 两次体测的核心指标对比（体重、体脂率、肌肉量、脂肪量、骨骼肌率、水分率）
- 对比表格：所有 21 项指标的 A/B 值 + 变化量 + 变化百分比
- 变化量用颜色标识：改善=绿色，恶化=红色，持平=灰色
- 调用 `GET /body-composition/compare?a=X&b=Y`

### 4.7 页面 6: 仪表盘增强

**文件**：`webpage/src/pages/dashboard/DashboardPage.tsx`

**具体需求**：
- 健康画像卡片从后端 `health_profile` 动态渲染（已实现，但数据源需扩展）
- 新增「体成分摘要」卡片：显示最近一次体测的核心 5 项（体重/体脂率/BMI/体型/健康评分）
- 新增「指标达标情况」环形图：达标项 vs 不达标项数量
- 「今日身体数据」mini-card 从 daily_metrics 读取，扩展为内脏脂肪 + BMR
- 预警列表接入体成分评估结果（如体脂率超标、内脏脂肪过高等）

### 4.8 组件设计

#### 4.8.1 `IndicatorCard` — 指标卡片组件

**文件**：`webpage/src/features/body-composition/IndicatorCard.tsx`

```tsx
interface IndicatorCardProps {
  label: string;           // 指标名称
  value: number | string;  // 数值
  unit: string;            // 单位
  level: IndicatorLevel;   // 状态等级
  reference?: string;      // 参考范围
  delta?: number;          // 与上次对比变化
  icon: React.ReactNode;   // 图标
}
```

- 根据 `level` 自动着色 Tag
- 有 `delta` 时显示变化箭头（↑绿色/↓红色）
- 点击展开显示参考范围

#### 4.8.2 `IndicatorGroup` — 指标分组组件

**文件**：`webpage/src/features/body-composition/IndicatorGroup.tsx`

- Ant Design `Collapse.Panel` 包装
- Header 显示组名 + 图标 + 统计（达标/偏低/偏高数量）
- Body 内渲染多个 `IndicatorCard`

#### 4.8.3 `StatusTag` — 状态标签组件

**文件**：`webpage/src/features/body-composition/StatusTag.tsx`

```tsx
const levelColorMap: Record<IndicatorLevel, string> = {
  "优": "green", "标准": "blue", "偏高": "orange",
  "不足": "cyan", "警戒型": "red", "增重": "purple", "减重": "gold",
};
```

#### 4.8.4 `MetricTrendChart` — 趋势图组件

**文件**：`webpage/src/features/body-composition/MetricTrendChart.tsx`

- ECharts 折线图封装
- 支持多指标叠加（双 Y 轴）
- 支持时间范围切换
- 数据点 tooltip

#### 4.8.5 `CompositionCompareChart` — 对比雷达图

**文件**：`webpage/src/features/body-composition/CompositionCompareChart.tsx`

- ECharts 雷达图封装
- A/B 两次体测数据对比

### 4.9 API 层更新

**文件**：`webpage/src/shared/api/bodyComposition.ts`

| 变更 | 描述 |
|------|------|
| `BodyCompositionRecord` interface | 新增 14 个字段 |
| `BodyCompositionCreatePayload` interface | 新增 14 个字段 |
| `getIndicatorConfig()` | 新增 — 获取指标分组定义 |
| `evaluateBodyComposition(id)` | 新增 — 获取评估结果 |
| `compareBodyComposition()` | 已有，需更新返回类型 |

---

## 5. 核心计算逻辑（后端 Service）

### 5.1 体型判定

```python
def evaluate_body_type(bmi: float, body_fat_rate: float) -> str:
    if bmi >= 28 and body_fat_rate < 20: return "肌肉型"
    if bmi >= 28 and body_fat_rate >= 20: return "肥胖"
    if bmi >= 24 and body_fat_rate >= 20: return "运动型偏胖"
    if bmi >= 24 and body_fat_rate < 20: return "隐藏型肥胖"
    if bmi < 18.5: return "偏瘦"
    return "标准"
```

### 5.2 控制量计算

```python
def calculate_controls(weight: float, body_fat_rate: float, height_cm: float,
                       target_fat_rate: float = 18.0, target_muscle_rate: float = 40.0) -> dict:
    height_m = height_cm / 100
    ideal_weight = 22.0 * height_m ** 2
    weight_control = round(ideal_weight - weight, 2)
    fat_control = round((body_fat_rate / 100 - target_fat_rate / 100) * weight, 2)
    muscle_control = round((target_muscle_rate / 100 - (100 - body_fat_rate) / 100) * weight, 2)
    return {"ideal_weight": round(ideal_weight, 1), "weight_control": weight_control,
            "fat_control": fat_control, "muscle_control": muscle_control}
```

### 5.3 营养状态

```python
def evaluate_nutrition(protein_mass: float | None, weight: float,
                       calories_intake: float | None, bmr: float | None) -> str:
    if protein_mass and weight and protein_mass < 0.8 * weight / 1000:
        return "营养不足"
    if calories_intake and bmr and calories_intake > bmr * 1.5:
        return "营养过剩"
    return "营养均衡"
```

### 5.4 燃脂心率

```python
def calc_fat_burn_hr(body_age: float | None, actual_age: int) -> tuple[float, float]:
    age = body_age or actual_age
    max_hr = 220 - age
    return round(max_hr * 0.6), round(max_hr * 0.75)
```

### 5.5 健康评分

```python
def calc_health_score(record: BodyCompositionRecord, user_height: float) -> int:
    """综合评分 0-100，基于各项指标达标情况加权计算"""
    score = 100
    # BMI 偏离标准(22)扣分
    bmi_penalty = abs(record.bmi - 22) * 2 if record.bmi else 0
    # 体脂率偏离标准扣分
    fat_penalty = max(0, (record.body_fat_rate - 20) * 1.5) if record.body_fat_rate else 0
    # 内脏脂肪警戒扣分
    visceral_penalty = max(0, (record.visceral_fat_level - 9) * 3) if record.visceral_fat_level and record.visceral_fat_level > 9 else 0
    score -= (bmi_penalty + fat_penalty + visceral_penalty)
    return max(0, min(100, int(score)))
```

### 5.6 指标状态判定

```python
INDICATOR_RULES = {
    "weight": lambda v, ctx: "过重" if ctx["bmi"] >= 24 else "偏轻" if ctx["bmi"] < 18.5 else "标准",
    "bmi": lambda v, _: "偏胖" if v >= 24 else "偏瘦" if v < 18.5 else "标准",
    "body_fat_rate": lambda v, ctx: (
        "轻度肥胖" if v >= 25 else "标准" if v < 20 else "偏高"
    ),
    "visceral_fat_level": lambda v, _: (
        "警戒型" if v >= 10 else "偏高" if v >= 7 else "正常"
    ),
    "muscle_rate": lambda v, _: "优" if v >= 70 else "良" if v >= 55 else "不足",
    "bone_mass": lambda v, ctx: "正常" if v >= 3.5 else "偏低",
    "water_rate": lambda v, ctx: (
        "偏高" if v > 65 else "标准" if v >= 50 else "不足"
    ),
    # ... 更多指标规则
}
```

---

## 6. 实施步骤

### Step 1: 数据层（后端）

| # | 任务 | 文件 |
|---|------|------|
| 1.1 | 扩展 BodyCompositionRecord ORM | `models/body_composition.py` |
| 1.2 | 扩展 DailyMetrics ORM | `models/daily_metrics.py` |
| 1.3 | Alembic 迁移 | `alembic/versions/` |
| 1.4 | 新增枚举 + 指标分组定义 | `schemas/body_composition.py` |
| 1.5 | 更新 Schema Response/Create | `schemas/body_composition.py` |

### Step 2: 评估服务（后端）

| # | 任务 | 文件 |
|---|------|------|
| 2.1 | 新建评估服务（体型/控制量/营养/评分） | `services/body_composition_evaluator.py` |
| 2.2 | 新增 evaluate API 端点 | `api/v1/body_composition.py` |
| 2.3 | 新增 indicator-config API 端点 | `api/v1/body_composition.py` |
| 2.4 | Service 层集成评估逻辑 | `services/body_composition_service.py` |

### Step 3: 前端组件库

| # | 任务 | 文件 |
|---|------|------|
| 3.1 | StatusTag 组件 | `features/body-composition/StatusTag.tsx` |
| 3.2 | IndicatorCard 组件 | `features/body-composition/IndicatorCard.tsx` |
| 3.3 | IndicatorGroup 组件 | `features/body-composition/IndicatorGroup.tsx` |
| 3.4 | MetricTrendChart 组件（ECharts） | `features/body-composition/MetricTrendChart.tsx` |
| 3.5 | CompositionCompareChart 组件（ECharts 雷达图） | `features/body-composition/CompositionCompareChart.tsx` |

### Step 4: 前端页面重构

| # | 任务 | 文件 |
|---|------|------|
| 4.1 | 重构体成分列表页（Card 列表 + 筛选） | `pages/body-composition/List.tsx` |
| 4.2 | 重构体成分详情页（6 组折叠面板） | `pages/body-composition/Detail.tsx` |
| 4.3 | 重构体成分录入页（分组表单） | `pages/body-composition/Create.tsx` |
| 4.4 | 新建体成分趋势页 | `pages/body-composition/Trend.tsx` |
| 4.5 | 新建体成分对比页 | `pages/body-composition/Compare.tsx` |
| 4.6 | 更新 API 层 types | `shared/api/bodyComposition.ts` |

### Step 5: 仪表盘增强

| # | 任务 | 文件 |
|---|------|------|
| 5.1 | 仪表盘接入体成分评估数据 | `pages/dashboard/DashboardPage.tsx` |
| 5.2 | 新增体成分摘要卡片 | `features/dashboard/CompositionSummaryCard.tsx` |
| 5.3 | 新增指标达标环形图 | `features/dashboard/IndicatorRingChart.tsx` |
| 5.4 | 预警列表接入体成分评估 | `pages/dashboard/DashboardPage.tsx` |

### Step 6: Agent 工具扩展

| # | 任务 | 文件 |
|---|------|------|
| 6.1 | `get_health_metrics` 支持新指标类型 | `agent/tools/read_tools.py` |
| 6.2 | 新增 `analyze_body_composition` 工具 | `agent/tools/analysis_tools.py` |

---

## 7. 验收标准

### 7.1 后端

| 验收项 | 标准 | 验证方式 |
|--------|------|----------|
| 数据库字段 | 14 个新字段 + 2 个 daily 字段 | Alembic migration 执行成功 |
| API 入参出参 | 所有新字段可读写 | Postman / curl 验证 |
| 评估服务 | 体型判定 6 分类正确 | 单元测试 6 种 BMI/体脂率组合 |
| 控制量计算 | 与截图数值一致（误差 ±5%） | 手动验算（身高 178cm, 体重 88.65kg → 理想体重 70.2kg） |
| 健康评分 | 0-100 分，合理分布 | 单元测试边界值 |

### 7.2 前端

| 验收项 | 标准 | 验证方式 |
|--------|------|----------|
| 列表页 | Card 布局 + 筛选 + 空状态 | 手动浏览 |
| 详情页 | 6 组折叠面板 + 状态标签 + 展开对比 | 截图对比 |
| 录入页 | 分组表单 + BMI 自动计算 + 表单验证 | 手动录入测试 |
| 趋势页 | ECharts 折线图 + 多指标叠加 + 统计摘要 | 手动浏览 |
| 对比页 | ECharts 雷达图 + 对比表 + 变化颜色 | 手动浏览 |
| 仪表盘 | 体成分摘要卡片 + 达标环形图 | 手动浏览 |
| 响应式 | 适配 375px-1920px 宽度 | Chrome DevTools |

### 7.3 Agent

| 验收项 | 标准 | 验证方式 |
|--------|------|----------|
| 工具调用 | `get_health_metrics` 返回新指标 | Agent 对话验证 |
| 分析能力 | `analyze_body_composition` 输出综合评估 | Agent 对话验证 |

---

## 8. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 历史数据无新字段 | 旧记录新字段为 null | 前端 `?? "-"` 处理 + 后端评估服务容错 |
| 评估逻辑主观性强 | 体型/营养状态判定有争议 | 提供可配置阈值，默认用体脂秤通用标准 |
| 前端表单过长 | 用户录入负担 | 分组折叠 + 核心字段（体重/体脂率/BMI）优先展示 |
| ECharts 性能 | 多指标叠加时渲染慢 | 限制最多 3 个指标叠加 + 数据点采样 |
| Ant Design 引入 | 包体积增加 | 按需引入（babel-plugin-import） |

---

## 9. 里程碑

| 里程碑 | 交付物 | 时间 |
|--------|--------|------|
| M1: 数据层 | ORM 模型 + Alembic 迁移 + Schema | Week 1 前半 |
| M2: 评估服务 | 评估逻辑 + 2 个新 API 端点 | Week 1 后半 |
| M3: 前端组件 | 5 个组件（StatusTag/IndicatorCard/IndicatorGroup/趋势图/对比图） | Week 2 前半 |
| M4: 前端页面 | 5 个页面（列表/详情/录入/趋势/对比） | Week 2 后半 |
| M5: 仪表盘 + Agent | 仪表盘增强 + Agent 工具扩展 | Week 3 |

---

**文档版本**: v2.0
**创建日期**: 2026-04-22
**维护者**: Rogers 项目团队
