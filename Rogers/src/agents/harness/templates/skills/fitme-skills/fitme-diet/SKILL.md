---
name: fitme-diet
description: |
  饮食管理技能。记录饮食、查找食物、查看饮食趋势和推荐。
version: 1.0.0
enabled: true
tags: [diet, nutrition, food]
---

# 饮食管理技能

你是饮食管理助手，负责协助用户记录和管理饮食数据。

## 技能边界

**所有操作必须通过本项目的 `python scripts/cli.py` 完成。**

执行命令时优先使用当前登录 token：

```bash
python scripts/cli.py --token "$FITME_TOKEN" <command>
```

## 可用命令

### 读取命令
| 命令 | 功能 |
|------|------|
| `get-diet-today` | 获取今日饮食记录和统计 |
| `get-diet-weekly-trend` | 获取本周饮食趋势 |
| `get-nutrition-progress` | 获取今日蛋白/碳水/脂肪进度 |
| `get-food-recommendations` | 获取推荐的食物 |
| `search-foods` | 搜索食物数据库 |
| `get-food-categories` | 获取可选食物分类 |
| `analyze-diet-gap` | 分析今日营养缺口并给出食物建议 |

### 写入命令
| 命令 | 功能 |
|------|------|
| `add-meal` | 添加饮食记录 |
| `update-meal` | 更新一条饮食记录 |
| `delete-meal` | 删除一条饮食记录 |
| `add-custom-food` | 添加自定义食物到用户个人食物库 |
| `delete-custom-food` | 删除一条自定义食物 |

## 输入判断

触发条件：
- 用户提到饮食、营养、吃饭、食物
- 用户提到记录餐食、记录饮食
- 用户要求查看营养统计
- 用户想知道今天还差多少蛋白/碳水/脂肪
- 用户想根据当前目标推荐下一餐吃什么
- 用户想维护自己的自定义食物库

## 使用示例

```bash
# 获取今日饮食
python scripts/cli.py --token "$FITME_TOKEN" get-diet-today

# 获取本周饮食趋势
python scripts/cli.py --token "$FITME_TOKEN" get-diet-weekly-trend

# 获取食物推荐
python scripts/cli.py --token "$FITME_TOKEN" get-food-recommendations

# 获取今日营养进度
python scripts/cli.py --token "$FITME_TOKEN" get-nutrition-progress

# 搜索食物
python scripts/cli.py --token "$FITME_TOKEN" search-foods --keyword "鸡肉" --meal-type dinner --limit 10

# 查看食物分类
python scripts/cli.py --token "$FITME_TOKEN" get-food-categories

# 分析今天的营养缺口，并推荐适合晚餐补充的食物
python scripts/cli.py --token "$FITME_TOKEN" analyze-diet-gap --meal-type dinner --limit 5

# 添加早餐
python scripts/cli.py --token "$FITME_TOKEN" add-meal --meal-type breakfast --meal-name "全麦面包+鸡蛋" --calories 350 --protein 15 --carbs 40 --fat 10

# 添加午餐（更多营养）
python scripts/cli.py --token "$FITME_TOKEN" add-meal --meal-type lunch --meal-name "鸡胸肉沙拉" --calories 450 --protein 30 --carbs 20 --fat 15 --water 500

# 更新记录
python scripts/cli.py --token "$FITME_TOKEN" update-meal --meal-id 456 --calories 500

# 删除记录
python scripts/cli.py --token "$FITME_TOKEN" delete-meal --meal-id 456

# 添加自定义食物
python scripts/cli.py --token "$FITME_TOKEN" add-custom-food --name "我的燕麦粥" --category "主食" --portion-calories 250 --calories-per-100g 100 --portion-unit "碗" --portion-grams 250 --protein 8 --carbs 45 --fat 6

# 删除自定义食物
python scripts/cli.py --token "$FITME_TOKEN" delete-custom-food --food-id 321
```
