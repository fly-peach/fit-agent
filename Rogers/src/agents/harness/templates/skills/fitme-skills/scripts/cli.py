"""Fitme CLI - API Version

通过 HTTP 调用 localhost:8000 的 API 来管理用户数据。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from typing import Any

import httpx

# API 配置
API_BASE_URL = "http://localhost:8000"


def _output(data: dict, exit_code: int = 0) -> None:
    """输出 JSON 并退出"""
    print(json.dumps(data, ensure_ascii=False, indent=2))
    sys.exit(exit_code)


def _get_headers(token: str) -> dict:
    """获取请求头，包含认证"""
    if token.startswith("Bearer "):
        auth_token = token
    else:
        auth_token = f"Bearer {token}"
    return {
        "Authorization": auth_token,
        "Content-Type": "application/json",
    }


def _api_request(
    method: str,
    endpoint: str,
    token: str,
    params: dict | None = None,
    json_data: dict | None = None,
) -> dict:
    """发送 API 请求"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = _get_headers(token)

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
            return {
                "success": False,
                "error": error_data.get("detail", str(e)),
                "status_code": e.response.status_code,
            }
        except Exception:
            return {"success": False, "error": str(e), "status_code": e.response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============= 用户相关 =============
def cmd_get_user_profile(args: argparse.Namespace) -> None:
    result = _api_request("GET", "/api/user/profile", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_user_settings(args: argparse.Namespace) -> None:
    result = _api_request("GET", "/api/user/settings", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# ============= 健康指标相关 =============
def cmd_get_health_metrics(args: argparse.Namespace) -> None:
    """获取健康指标（别名）"""
    result = _api_request("GET", "/api/health/metrics", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_health_summary(args: argparse.Namespace) -> None:
    """获取健康指标"""
    result = _api_request("GET", "/api/health/metrics", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_health_history(args: argparse.Namespace) -> None:
    """获取历史健康记录"""
    params = {"limit": args.limit} if hasattr(args, "limit") and args.limit else None
    result = _api_request("GET", "/api/health/measurements", args.token, params=params)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_create_health_metric(args: argparse.Namespace) -> None:
    """创建健康指标记录"""
    data = {}
    if args.weight is not None:
        data["weight"] = args.weight
    if args.height is not None:
        data["height"] = args.height
    if args.body_fat is not None:
        data["bodyFat"] = args.body_fat
    if args.weight_goal is not None:
        data["weightGoal"] = args.weight_goal
    # 必填字段：measureDate，默认今天
    if hasattr(args, "measure_date") and args.measure_date:
        data["measureDate"] = args.measure_date
    else:
        data["measureDate"] = date.today().isoformat()

    result = _api_request("POST", "/api/health/metrics", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# ============= 训练相关 =============
def cmd_get_training_today(args: argparse.Namespace) -> None:
    result = _api_request("GET", "/api/training/schedule/weekly", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_training_weekly(args: argparse.Namespace) -> None:
    """获取本周训练计划"""
    result = _api_request("GET", "/api/training/schedule/weekly", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_training_stats(args: argparse.Namespace) -> None:
    """获取训练统计"""
    result = _api_request("GET", "/api/training/stats/weekly", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_training_recommendations(args: argparse.Namespace) -> None:
    """获取推荐训练"""
    result = _api_request("GET", "/api/training/recommendations", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_create_training_plan(args: argparse.Namespace) -> None:
    """创建训练计划"""
    data = {
        "planName": args.plan_name,
        "planType": args.plan_type,
        "scheduledDate": args.scheduled_date,
    }
    if args.estimated_duration:
        data["estimatedDuration"] = args.estimated_duration
    if args.target_intensity:
        data["targetIntensity"] = args.target_intensity
    if args.note:
        data["note"] = args.note

    result = _api_request("POST", "/api/training/plans", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# ============= 饮食相关 =============
def cmd_get_diet_today(args: argparse.Namespace) -> None:
    """获取今日饮食（可指定日期）"""
    params = {}
    if hasattr(args, "date") and args.date:
        params["targetDate"] = args.date
    result = _api_request("GET", "/api/diet/meals/today", args.token, params=params)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_diet_stats(args: argparse.Namespace) -> None:
    """获取今日饮食统计"""
    result = _api_request("GET", "/api/diet/stats/today", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_get_diet_recommendations(args: argparse.Namespace) -> None:
    """获取推荐食物"""
    result = _api_request("GET", "/api/diet/recommendations", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_search_foods(args: argparse.Namespace) -> None:
    """搜索食物"""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["category"] = args.category
    result = _api_request("GET", "/api/diet/foods", args.token, params=params)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_create_diet_meal(args: argparse.Namespace) -> None:
    """创建饮食记录"""
    data = {
        "mealType": args.meal_type,
        "mealName": args.meal_name,
        "calories": args.calories,
    }
    if args.protein is not None:
        data["protein"] = args.protein
    if args.carbs is not None:
        data["carbs"] = args.carbs
    if args.fat is not None:
        data["fat"] = args.fat
    if args.water is not None:
        data["water"] = args.water
    if args.note:
        data["note"] = args.note
    if args.meal_date:
        data["mealDate"] = args.meal_date
    # 必填字段：time，默认当前时间
    if hasattr(args, "time") and args.time:
        data["time"] = args.time
    else:
        data["time"] = datetime.now().strftime("%H:%M:%S")

    result = _api_request("POST", "/api/diet/meals", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# ============= 自定义食物 =============
def cmd_create_custom_food(args: argparse.Namespace) -> None:
    """添加自定义食物"""
    data = {
        "name": args.name,
        "category": args.category,
        "portionCalories": args.portion_calories,
        "caloriesPer100g": args.calories_per_100g,
    }
    if args.portion_unit:
        data["portionUnit"] = args.portion_unit
    if args.portion_grams:
        data["portionGrams"] = args.portion_grams
    if args.calorie_level:
        data["calorieLevel"] = args.calorie_level
    if args.protein is not None:
        data["protein"] = args.protein
    if args.carbs is not None:
        data["carbs"] = args.carbs
    if args.fat is not None:
        data["fat"] = args.fat

    result = _api_request("POST", "/api/diet/foods", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_delete_custom_food(args: argparse.Namespace) -> None:
    """删除自定义食物"""
    result = _api_request("DELETE", f"/api/diet/foods/{args.food_id}", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# ============= 自定义动作 =============
def cmd_create_custom_exercise(args: argparse.Namespace) -> None:
    """创建自定义动作"""
    data = {
        "nameCn": args.name_cn,
        "targetMuscle": args.target_muscle,
        "instructions": [args.instructions] if args.instructions else ["请参考标准动作要领"],
    }
    if args.name_en:
        data["nameEn"] = args.name_en
    if args.difficulty:
        data["difficulty"] = args.difficulty
    if args.force_type:
        data["forceType"] = args.force_type
    if args.mechanics:
        data["mechanics"] = args.mechanics
    if args.equipment:
        data["equipment"] = args.equipment
    if args.exercise_type:
        data["exerciseType"] = args.exercise_type
    if args.helper_muscles:
        data["helperMuscles"] = args.helper_muscles

    result = _api_request("POST", "/api/exercises/custom", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_update_custom_exercise(args: argparse.Namespace) -> None:
    """更新自定义动作"""
    data = {}
    for field, api_field in [
        ("name_cn", "nameCn"), ("name_en", "nameEn"),
        ("difficulty", "difficulty"), ("force_type", "forceType"),
        ("mechanics", "mechanics"), ("equipment", "equipment"),
        ("exercise_type", "exerciseType"),
        ("target_muscle", "targetMuscle"), ("helper_muscles", "helperMuscles"),
    ]:
        val = getattr(args, field, None)
        if val is not None:
            data[api_field] = val
    if getattr(args, "instructions", None):
        data["instructions"] = [args.instructions]

    result = _api_request("PUT", f"/api/exercises/custom/{args.exercise_id}", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_delete_custom_exercise(args: argparse.Namespace) -> None:
    """删除自定义动作"""
    result = _api_request("DELETE", f"/api/exercises/custom/{args.exercise_id}", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# ============= 综合概览 =============
def cmd_get_full_overview(args: argparse.Namespace) -> None:
    # 综合概览
    profile = _api_request("GET", "/api/user/profile", args.token)
    health = _api_request("GET", "/api/health/metrics", args.token)
    training = _api_request("GET", "/api/training/schedule/weekly", args.token)
    diet = _api_request("GET", "/api/diet/meals/today", args.token)

    overview = {
        "profile": profile.get("data", profile) if profile.get("success", profile.get("code") == 200) else None,
        "health": health.get("data", health) if health.get("success", health.get("code") == 200) else None,
        "training": training.get("data", training) if training.get("success", training.get("code") == 200) else None,
        "diet": diet.get("data", diet) if diet.get("success", diet.get("code") == 200) else None,
    }
    _output({"success": True, "data": overview}, exit_code=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fitme-cli",
        description="Fitme 健康管理 CLI（API 版本）- 调用 localhost:8000 的 API",
    )
    parser.add_argument(
        "--token", required=True, help="登录 token，支持原始 JWT 或 \"Bearer <token>\" 格式"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help=f"API 地址，默认 {API_BASE_URL}，可通过环境变量 FITME_API_URL 设置",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, title="子命令")

    # ========== 用户相关 ==========
    sub_get_user_profile = subparsers.add_parser("get-user-profile", help="获取用户基本信息")
    sub_get_user_profile.set_defaults(func=cmd_get_user_profile)

    sub_get_user_settings = subparsers.add_parser("get-user-settings", help="获取用户设置")
    sub_get_user_settings.set_defaults(func=cmd_get_user_settings)

    # ========== 健康指标相关 ==========
    sub_get_health_metrics = subparsers.add_parser("get-health-metrics", help="获取健康指标")
    sub_get_health_metrics.set_defaults(func=cmd_get_health_metrics)

    sub_get_health_summary = subparsers.add_parser("get-health-summary", help="获取健康指标（别名）")
    sub_get_health_summary.set_defaults(func=cmd_get_health_summary)

    sub_get_health_history = subparsers.add_parser("get-health-history", help="获取历史健康记录")
    sub_get_health_history.add_argument("--limit", type=int, default=10, help="返回记录数（默认10）")
    sub_get_health_history.set_defaults(func=cmd_get_health_history)

    sub_create_health_metric = subparsers.add_parser("create-health-metric", help="创建健康指标记录")
    sub_create_health_metric.add_argument("--weight", type=float, help="体重 (kg)")
    sub_create_health_metric.add_argument("--height", type=float, help="身高 (cm)")
    sub_create_health_metric.add_argument("--body-fat", type=float, dest="body_fat", help="体脂率 (%)")
    sub_create_health_metric.add_argument("--weight-goal", type=float, dest="weight_goal", help="目标体重 (kg)")
    sub_create_health_metric.add_argument("--measure-date", dest="measure_date", help="测量日期 (YYYY-MM-DD)，默认今天")
    sub_create_health_metric.set_defaults(func=cmd_create_health_metric)

    # ========== 训练相关 ==========
    sub_get_training_today = subparsers.add_parser("get-training-today", help="获取今日训练计划")
    sub_get_training_today.set_defaults(func=cmd_get_training_today)

    sub_get_training_weekly = subparsers.add_parser("get-training-weekly", help="获取本周训练计划")
    sub_get_training_weekly.set_defaults(func=cmd_get_training_weekly)

    sub_get_training_stats = subparsers.add_parser("get-training-stats", help="获取训练统计")
    sub_get_training_stats.set_defaults(func=cmd_get_training_stats)

    sub_get_training_recommendations = subparsers.add_parser("get-training-recommendations", help="获取推荐训练")
    sub_get_training_recommendations.set_defaults(func=cmd_get_training_recommendations)

    sub_create_training_plan = subparsers.add_parser("create-training-plan", help="创建训练计划")
    sub_create_training_plan.add_argument("--plan-name", required=True, dest="plan_name", help="计划名称")
    sub_create_training_plan.add_argument("--plan-type", required=True, dest="plan_type", help="计划类型")
    sub_create_training_plan.add_argument("--scheduled-date", required=True, dest="scheduled_date", help="计划日期 (YYYY-MM-DD)")
    sub_create_training_plan.add_argument("--estimated-duration", type=int, dest="estimated_duration", help="预计时长（分钟）")
    sub_create_training_plan.add_argument("--target-intensity", dest="target_intensity", help="目标强度")
    sub_create_training_plan.add_argument("--note", help="备注")
    sub_create_training_plan.set_defaults(func=cmd_create_training_plan)

    # ========== 饮食相关 ==========
    sub_get_diet_today = subparsers.add_parser("get-diet-today", help="获取今日饮食记录")
    sub_get_diet_today.add_argument("--date", help="指定日期 (YYYY-MM-DD)，默认今日")
    sub_get_diet_today.set_defaults(func=cmd_get_diet_today)

    sub_get_diet_stats = subparsers.add_parser("get-diet-stats", help="获取今日饮食统计")
    sub_get_diet_stats.set_defaults(func=cmd_get_diet_stats)

    sub_get_diet_recommendations = subparsers.add_parser("get-diet-recommendations", help="获取推荐食物")
    sub_get_diet_recommendations.set_defaults(func=cmd_get_diet_recommendations)

    sub_search_foods = subparsers.add_parser("search-foods", help="搜索食物")
    sub_search_foods.add_argument("--keyword", default="", help="搜索关键词")
    sub_search_foods.add_argument("--category", default="", help="分类筛选")
    sub_search_foods.set_defaults(func=cmd_search_foods)

    sub_create_diet_meal = subparsers.add_parser("create-diet-meal", help="创建饮食记录")
    sub_create_diet_meal.add_argument("--meal-type", required=True, dest="meal_type", help="餐次类型 (breakfast/lunch/dinner/snack)")
    sub_create_diet_meal.add_argument("--meal-name", required=True, dest="meal_name", help="餐名")
    sub_create_diet_meal.add_argument("--calories", type=int, required=True, help="卡路里 (kcal)")
    sub_create_diet_meal.add_argument("--protein", type=float, help="蛋白质 (g)")
    sub_create_diet_meal.add_argument("--carbs", type=float, help="碳水化合物 (g)")
    sub_create_diet_meal.add_argument("--fat", type=float, help="脂肪 (g)")
    sub_create_diet_meal.add_argument("--water", type=int, help="水分 (ml)")
    sub_create_diet_meal.add_argument("--note", help="备注")
    sub_create_diet_meal.add_argument("--meal-date", dest="meal_date", help="用餐日期 (YYYY-MM-DD)，默认今日")
    sub_create_diet_meal.add_argument("--time", help="用餐时间 (HH:MM:SS)，默认当前时间")
    sub_create_diet_meal.set_defaults(func=cmd_create_diet_meal)

    # ========== 自定义食物 ==========
    sub_create_custom_food = subparsers.add_parser("create-custom-food", help="添加自定义食物")
    sub_create_custom_food.add_argument("--name", required=True, help="食物名称")
    sub_create_custom_food.add_argument("--category", required=True, help="分类")
    sub_create_custom_food.add_argument("--portion-calories", type=int, required=True, dest="portion_calories", help="每份热量 (kcal)")
    sub_create_custom_food.add_argument("--calories-per-100g", type=int, required=True, dest="calories_per_100g", help="每100g热量 (kcal)")
    sub_create_custom_food.add_argument("--portion-unit", dest="portion_unit", help="一份单位（如：1 块）")
    sub_create_custom_food.add_argument("--portion-grams", type=int, dest="portion_grams", help="一份克数")
    sub_create_custom_food.add_argument("--calorie-level", dest="calorie_level", help="热量等级（低/中/高/超高）")
    sub_create_custom_food.add_argument("--protein", type=float, default=0, help="蛋白质 (g)")
    sub_create_custom_food.add_argument("--carbs", type=float, default=0, help="碳水化合物 (g)")
    sub_create_custom_food.add_argument("--fat", type=float, default=0, help="脂肪 (g)")
    sub_create_custom_food.set_defaults(func=cmd_create_custom_food)

    sub_delete_custom_food = subparsers.add_parser("delete-custom-food", help="删除自定义食物")
    sub_delete_custom_food.add_argument("--food-id", type=int, required=True, dest="food_id", help="食物 ID")
    sub_delete_custom_food.set_defaults(func=cmd_delete_custom_food)

    # ========== 自定义动作 ==========
    sub_create_custom_exercise = subparsers.add_parser("create-custom-exercise", help="创建自定义动作")
    sub_create_custom_exercise.add_argument("--name-cn", required=True, dest="name_cn", help="动作中文名称")
    sub_create_custom_exercise.add_argument("--target-muscle", required=True, dest="target_muscle", help="目标肌肉")
    sub_create_custom_exercise.add_argument("--name-en", dest="name_en", help="动作英文名称")
    sub_create_custom_exercise.add_argument("--difficulty", help="难度（初级/中级/专家级）")
    sub_create_custom_exercise.add_argument("--force-type", dest="force_type", help="发力类型")
    sub_create_custom_exercise.add_argument("--mechanics", help="力学类型")
    sub_create_custom_exercise.add_argument("--equipment", help="器械")
    sub_create_custom_exercise.add_argument("--exercise-type", dest="exercise_type", help="动作类型")
    sub_create_custom_exercise.add_argument("--helper-muscles", dest="helper_muscles", help="辅助肌群（逗号分隔）")
    sub_create_custom_exercise.add_argument("--instructions", help="动作要领")
    sub_create_custom_exercise.set_defaults(func=cmd_create_custom_exercise)

    sub_update_custom_exercise = subparsers.add_parser("update-custom-exercise", help="更新自定义动作")
    sub_update_custom_exercise.add_argument("--exercise-id", type=int, required=True, dest="exercise_id", help="动作 ID")
    sub_update_custom_exercise.add_argument("--name-cn", dest="name_cn", help="动作中文名称")
    sub_update_custom_exercise.add_argument("--name-en", dest="name_en", help="动作英文名称")
    sub_update_custom_exercise.add_argument("--difficulty", help="难度")
    sub_update_custom_exercise.add_argument("--force-type", dest="force_type", help="发力类型")
    sub_update_custom_exercise.add_argument("--mechanics", help="力学类型")
    sub_update_custom_exercise.add_argument("--equipment", help="器械")
    sub_update_custom_exercise.add_argument("--exercise-type", dest="exercise_type", help="动作类型")
    sub_update_custom_exercise.add_argument("--target-muscle", dest="target_muscle", help="目标肌肉")
    sub_update_custom_exercise.add_argument("--helper-muscles", dest="helper_muscles", help="辅助肌群")
    sub_update_custom_exercise.add_argument("--instructions", help="动作要领")
    sub_update_custom_exercise.set_defaults(func=cmd_update_custom_exercise)

    sub_delete_custom_exercise = subparsers.add_parser("delete-custom-exercise", help="删除自定义动作")
    sub_delete_custom_exercise.add_argument("--exercise-id", type=int, required=True, dest="exercise_id", help="动作 ID")
    sub_delete_custom_exercise.set_defaults(func=cmd_delete_custom_exercise)

    # ========== 综合概览 ==========
    sub_get_full_overview = subparsers.add_parser("get-full-overview", help="获取用户综合概览")
    sub_get_full_overview.set_defaults(func=cmd_get_full_overview)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 更新 API 地址
    global API_BASE_URL
    if args.api_url:
        API_BASE_URL = args.api_url

    try:
        args.func(args)
    except Exception as e:
        _output({"success": False, "error": str(e)}, exit_code=1)


if __name__ == "__main__":
    main()
