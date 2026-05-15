---
name: fitme-memory
description: |
  用户记忆画像管理技能。记录和查询用户的饮食偏好、运动偏好、健身目标、
  已达成成就、性格特质等全方位画像数据。帮助Agent建立用户的"数字第二自我"。
version: 1.0.0
enabled: true
tags: [memory, user-profile, preferences, second-me]
---

# 用户记忆画像管理技能

你是用户记忆画像管理助手，负责记录和管理用户的全方位画像数据。

## 技能边界

**所有操作通过内置 Python 工具函数完成，直接写入 fituser.db。**

## 可用命令

| 命令 | 功能 |
|------|------|
| `record_user_fact` | 记录/更新一条用户画像事实 |
| `get_user_memory` | 获取用户所有画像数据 |
| `delete_user_fact_tool` | 软删除一条画像事实 |

## 参数说明

### record_user_fact
- `category` (必填): 分类 — food / exercise / health / goal / achievement / personality / note
- `key` (必填): 属性名，如 `favorite_foods`、`primary_fitness_goal`、`injuries`
- `value` (必填): 属性值
- `confidence` (可选): 置信度 0.0~1.0，默认 1.0
- `source` (可选): 来源 explicit / inferred / extracted，默认 explicit

### get_user_memory
- `category` (可选): 按分类过滤，不传则返回所有

### delete_user_fact_tool
- `key` (必填): 要删除的属性名

## 分类与键值建议

### food — 饮食类
| key | 说明 |
|-----|------|
| `favorite_foods` | 喜欢吃的食物（逗号分隔） |
| `disliked_foods` | 不喜欢/不吃的食物 |
| `dietary_restrictions` | 饮食限制（清真/过敏/素食等） |
| `cuisine_preferences` | 偏好菜系 |
| `meal_pattern` | 进餐频率和模式 |
| `cooking_ability` | 烹饪能力 |

### exercise — 运动类
| key | 说明 |
|-----|------|
| `favorite_exercises` | 喜欢做的运动 |
| `disliked_exercises` | 不喜欢做的运动 |
| `preferred_training_time` | 偏好的训练时间 |
| `equipment_available` | 可用的器械 |
| `training_environment` | 训练环境（gym/home） |
| `preferred_intensity` | 偏好的训练强度 |

### health — 健康类
| key | 说明 |
|-----|------|
| `injuries` | 伤病记录 |
| `medical_conditions` | 医疗状况 |
| `sleep_quality` | 睡眠质量 |

### goal — 目标类
| key | 说明 |
|-----|------|
| `primary_fitness_goal` | 主要健身目标 |
| `target_weight` | 目标体重(kg) |
| `target_body_fat` | 目标体脂率(%) |
| `strength_milestones` | 力量里程碑目标 |
| `target_date` | 目标达成日期 |

### achievement — 成就类
| key | 说明 |
|-----|------|
| `milestones` | 已达成成就列表（JSON数组） |

### personality — 性格类
| key | 说明 |
|-----|------|
| `motivation_style` | 激励方式偏好 |
| `feedback_preference` | 反馈风格偏好 |
| `training_discipline` | 训练自律性 |

### note — 备注类
| key | 说明 |
|-----|------|
| `general_notes` | 通用备注 |

## 触发条件

- 用户明确表达偏好（"我喜欢..."、"我不喜欢..."）
- 用户分享目标（"我想减到..."、"我的目标是..."）
- 用户提到成就（"我做到了..."、"我终于..."）
- 用户提到限制（"我不能吃..."、"我膝盖不好..."）
- Agent 从对话中推断出用户特征时
- 用户询问 Agent 记得什么时（get_user_memory）

## 使用示例

```
# 记录饮食偏好
record_user_fact --category food --key favorite_foods --value "鸡胸肉,西兰花,燕麦,牛肉"

# 记录健身目标
record_user_fact --category goal --key primary_fitness_goal --value "减脂"

# 记录伤病
record_user_fact --category health --key injuries --value "右膝旧伤,腰椎间盘突出"

# 查询所有画像
get_user_memory

# 查询饮食偏好
get_user_memory --category food

# 删除一条记录
delete_user_fact_tool --key favorite_foods
```
