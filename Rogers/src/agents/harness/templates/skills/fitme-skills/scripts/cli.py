"""Fitme CLI - API Version

通过 HTTP 调用 localhost:8000 的 API 来管理用户数据。
"""
from __future__ import annotations

import argparse
import json
import sys
import os
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


# =============================================================================
# 读取命令
# =============================================================================


def cmd_get_user_profile(args: argparse.Namespace) -> None:
    """获取用户基本信息"""
    result = _api_request("GET", "/api/user/profile", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_health_summary(args: argparse.Namespace) -> None:
    """获取用户最新健康指标"""
    result = _api_request("GET", "/api/health/metrics", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_health_history(args: argparse.Namespace) -> None:
    """获取近期健康指标变化趋势"""
    result = _api_request(
        "GET", "/api/health/measurements", args.token, params={"limit": args.limit}
    )
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_training_today(args: argparse.Namespace) -> None:
    """获取今日训练安排"""
    result = _api_request("GET", "/api/training/schedule/weekly", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_training_weekly(args: argparse.Namespace) -> None:
    """获取本周训练统计和安排"""
    result = _api_request("GET", "/api/training/stats/weekly", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_training_monthly(args: argparse.Namespace) -> None:
    """获取指定月份训练安排"""
    result = _api_request(
        "GET", "/api/training/schedule/monthly", args.token, params={"year": args.year, "month": args.month}
    )
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_training_weekly_progress(args: argparse.Namespace) -> None:
    """获取本周训练进度"""
    result = _api_request("GET", "/api/training/progress/weekly", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_training_recommendations(args: argparse.Namespace) -> None:
    """获取推荐的训练计划"""
    result = _api_request("GET", "/api/training/recommendations", args.token, params={"limit": args.limit})
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_training_plan_detail(args: argparse.Namespace) -> None:
    """获取训练计划详情"""
    result = _api_request("GET", f"/api/training/plans/{args.plan_id}/detail", args.token)
    _output(result, exit_code=0 if result.get("code") == 200 or result.get("success") is True else 1)


def cmd_get_diet_today(args: argparse.Namespace) -> None:
    """获取今日饮食记录和统计"""
    result = _api_request("GET", "/api/diet/meals/today", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_diet_weekly_trend(args: argparse.Namespace) -> None:
    """获取本周饮食趋势"""
    result = _api_request("GET", "/api/diet/trend/weekly", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_nutrition_progress(args: argparse.Namespace) -> None:
    """获取今日营养摄入进度"""
    result = _api_request("GET", "/api/diet/nutrition/progress", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_food_recommendations(args: argparse.Namespace) -> None:
    """获取推荐的食物"""
    result = _api_request("GET", "/api/diet/recommendations", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_user_settings(args: argparse.Namespace) -> None:
    """获取用户设置"""
    result = _api_request("GET", "/api/user/settings", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_search_foods(args: argparse.Namespace) -> None:
    """搜索食物数据库"""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["category"] = args.category
    if args.meal_type:
        params["meal_type"] = args.meal_type
    if args.limit:
        params["limit"] = args.limit

    result = _api_request("GET", "/api/diet/foods", args.token, params=params)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_food_categories(args: argparse.Namespace) -> None:
    """获取食物分类列表"""
    result = _api_request("GET", "/api/diet/foods/categories", args.token)
    _output(result, exit_code=0 if result.get("code") == 200 or result.get("success") is True else 1)


def cmd_search_exercises(args: argparse.Namespace) -> None:
    """搜索动作库"""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.target_muscle:
        params["target_muscle"] = args.target_muscle
    if args.exercise_type:
        params["exercise_type"] = args.exercise_type
    if args.difficulty:
        params["difficulty"] = args.difficulty
    if args.equipment:
        params["equipment"] = args.equipment
    if args.force_type:
        params["force_type"] = args.force_type
    if args.mechanics:
        params["mechanics"] = args.mechanics
    if args.limit:
        params["limit"] = args.limit

    result = _api_request("GET", "/api/exercises", args.token, params=params)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_exercise_detail(args: argparse.Namespace) -> None:
    """获取动作详情"""
    result = _api_request("GET", f"/api/exercises/{args.exercise_id}", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_get_exercise_categories(args: argparse.Namespace) -> None:
    """获取动作分类选项"""
    result = _api_request("GET", "/api/exercises/categories/muscles", args.token)
    _output(result, exit_code=0 if result.get("code") == 200 or result.get("success") is True else 1)


def cmd_pin_exercise(args: argparse.Namespace) -> None:
    """收藏动作"""
    result = _api_request(
        "POST", "/api/exercises/pin", args.token, json_data={"exerciseId": args.exercise_id}
    )
    _output(result, exit_code=0 if result.get("code") == 200 or result.get("success") is True else 1)


def cmd_unpin_exercise(args: argparse.Namespace) -> None:
    """取消收藏动作"""
    result = _api_request("DELETE", f"/api/exercises/pin/{args.exercise_id}", args.token)
    _output(result, exit_code=0 if result.get("code") == 200 or result.get("success") is True else 1)


def cmd_get_pinned_exercises(args: argparse.Namespace) -> None:
    """获取已收藏动作列表"""
    result = _api_request("GET", "/api/exercises/pinned", args.token)
    if result.get("success") is False:
        _output(result, exit_code=1)
    _output({"success": True, "data": result.get("data", result)}, exit_code=0)


def cmd_reorder_pinned_exercises(args: argparse.Namespace) -> None:
    """按顺序重排收藏动作"""
    exercise_ids = [int(x.strip()) for x in args.exercise_ids.split(",") if x.strip()]
    result = _api_request(
        "POST", "/api/exercises/pin/reorder", args.token, json_data={"exerciseIds": exercise_ids}
    )
    _output(result, exit_code=0 if result.get("code") == 200 or result.get("success") is True else 1)


def cmd_get_full_overview(args: argparse.Namespace) -> None:
    """获取用户综合概览"""
    profile = _api_request("GET", "/api/user/profile", args.token)
    health = _api_request("GET", "/api/health/metrics", args.token)
    training = _api_request("GET", "/api/training/stats/weekly", args.token)
    diet = _api_request("GET", "/api/diet/stats/today", args.token)

    overview = {
        "profile": profile.get("data", profile) if profile.get("success", profile.get("code") == 200) else None,
        "health": health.get("data", health) if health.get("success", health.get("code") == 200) else None,
        "training": training.get("data", training) if training.get("success", training.get("code") == 200) else None,
        "diet": diet.get("data", diet) if diet.get("success", diet.get("code") == 200) else None,
    }

    _output({"success": True, "data": overview}, exit_code=0)


# =============================================================================
# 写入命令
# =============================================================================


def cmd_update_profile(args: argparse.Namespace) -> None:
    """更新用户基本信息"""
    data = {}
    if args.name:
        data["name"] = args.name
    if args.avatar:
        data["avatar"] = args.avatar

    result = _api_request("PUT", "/api/user/profile", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_add_health_metric(args: argparse.Namespace) -> None:
    """添加一条新的健康指标记录"""
    data = {}
    if args.weight is not None:
        data["weight"] = args.weight
    if args.height is not None:
        data["height"] = args.height
    if args.body_fat is not None:
        data["bodyFat"] = args.body_fat
    if args.measure_date:
        data["measureDate"] = args.measure_date

    result = _api_request("POST", "/api/health/metrics", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_add_training_plan(args: argparse.Namespace) -> None:
    """创建训练计划"""
    data = {
        "planName": args.plan_name,
        "planType": args.plan_type,
    }
    if args.scheduled_date:
        data["scheduledDate"] = args.scheduled_date
    if args.estimated_duration:
        data["estimatedDuration"] = args.estimated_duration
    if args.target_intensity:
        data["targetIntensity"] = args.target_intensity
    if args.note:
        data["note"] = args.note
    if args.exercises_json:
        data["exercises"] = json.loads(args.exercises_json)

    result = _api_request("POST", "/api/training/plans", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_update_training_plan(args: argparse.Namespace) -> None:
    """更新训练计划"""
    data = {}
    if args.plan_name:
        data["planName"] = args.plan_name
    if args.scheduled_date:
        data["scheduledDate"] = args.scheduled_date
    if args.estimated_duration:
        data["estimatedDuration"] = args.estimated_duration
    if args.target_intensity:
        data["targetIntensity"] = args.target_intensity
    if args.note:
        data["note"] = args.note

    result = _api_request("PUT", f"/api/training/plans/{args.plan_id}", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_complete_training(args: argparse.Namespace) -> None:
    """完成一个训练计划"""
    data = {}
    if args.actual_duration:
        data["actualDuration"] = args.actual_duration
    if args.actual_intensity:
        data["actualIntensity"] = args.actual_intensity
    if args.calories_burned:
        data["caloriesBurned"] = args.calories_burned
    if args.completed_date:
        data["completedDate"] = args.completed_date
    if args.note:
        data["note"] = args.note

    result = _api_request("POST", f"/api/training/complete/{args.plan_id}", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_delete_training_plan(args: argparse.Namespace) -> None:
    """删除训练计划"""
    result = _api_request("DELETE", f"/api/training/plans/{args.plan_id}", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_update_plan_exercise(args: argparse.Namespace) -> None:
    """更新计划中的动作"""
    data = {}
    if args.sets is not None:
        data["sets"] = args.sets
    if args.reps is not None:
        data["reps"] = args.reps
    if args.weight is not None:
        data["weight"] = args.weight
    if args.duration is not None:
        data["duration"] = args.duration

    result = _api_request("PUT", f"/api/training/plans/exercise/{args.exercise_item_id}", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_add_meal(args: argparse.Namespace) -> None:
    """添加饮食记录"""
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
    if args.meal_date:
        data["mealDate"] = args.meal_date
    if args.meal_time:
        data["mealTime"] = args.meal_time
    if args.note:
        data["note"] = args.note

    result = _api_request("POST", "/api/diet/meals", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_update_meal(args: argparse.Namespace) -> None:
    """更新饮食记录"""
    data = {}
    if args.meal_name:
        data["mealName"] = args.meal_name
    if args.calories is not None:
        data["calories"] = args.calories
    if args.protein is not None:
        data["protein"] = args.protein
    if args.carbs is not None:
        data["carbs"] = args.carbs
    if args.fat is not None:
        data["fat"] = args.fat
    if args.water is not None:
        data["water"] = args.water

    result = _api_request("PUT", f"/api/diet/meals/{args.meal_id}", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_delete_meal(args: argparse.Namespace) -> None:
    """删除饮食记录"""
    result = _api_request("DELETE", f"/api/diet/meals/{args.meal_id}", args.token)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_add_custom_food(args: argparse.Namespace) -> None:
    """添加自定义食物"""
    data = {
        "name": args.name,
        "category": args.category,
        "portionCalories": args.portion_calories,
        "caloriesPer100g": args.calories_per_100g,
    }
    if args.portion_unit:
        data["portionUnit"] = args.portion_unit
    if args.portion_grams is not None:
        data["portionGrams"] = args.portion_grams
    if args.calorie_level:
        data["calorieLevel"] = args.calorie_level
    if args.protein is not None:
        data["protein"] = args.protein
    if args.carbs is not None:
        data["carbs"] = args.carbs
    if args.fat is not None:
        data["fat"] = args.fat
    if args.suitable_meals:
        data["suitableMeals"] = args.suitable_meals

    result = _api_request("POST", "/api/diet/foods", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


def cmd_update_settings(args: argparse.Namespace) -> None:
    """更新用户设置"""
    data = {}
    if args.calorie_goal is not None:
        data["calorieGoal"] = args.calorie_goal
    if args.protein_goal is not None:
        data["proteinGoal"] = args.protein_goal
    if args.carbs_goal is not None:
        data["carbsGoal"] = args.carbs_goal
    if args.fat_goal is not None:
        data["fatGoal"] = args.fat_goal
    if args.water_goal is not None:
        data["waterGoal"] = args.water_goal
    if args.weight_goal is not None:
        data["weightGoal"] = args.weight_goal
    if args.weekly_training_goal is not None:
        data["weeklyTrainingGoal"] = args.weekly_training_goal

    result = _api_request("PUT", "/api/user/settings", args.token, json_data=data)
    _output(result, exit_code=0 if result.get("success", result.get("code") == 200) else 1)


# =============================================================================
# 参数解析
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fitme-cli",
        description="Fitme 健康管理 CLI (API 版本) - 调用 localhost:8000 的 API",
    )
    parser.add_argument(
        "--token", required=True, help="登录 token，支持原始 JWT 或 `Bearer <token>` 格式"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help=f"API 地址，默认 {API_BASE_URL}，可通过环境变量 FITME_API_URL 设置",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, title="子命令")

    # -------------------------------------------------------------------------
    # 读取命令
    # -------------------------------------------------------------------------
    sub_get_user_profile = subparsers.add_parser("get-user-profile", help="获取用户基本信息")
    sub_get_user_profile.set_defaults(func=cmd_get_user_profile)

    sub_get_health_summary = subparsers.add_parser("get-health-summary", help="获取用户最新健康指标")
    sub_get_health_summary.set_defaults(func=cmd_get_health_summary)

    sub_get_health_history = subparsers.add_parser("get-health-history", help="获取近期健康指标变化趋势")
    sub_get_health_history.add_argument("--limit", type=int, default=10, help="历史记录数量，默认 10")
    sub_get_health_history.set_defaults(func=cmd_get_health_history)

    sub_get_training_today = subparsers.add_parser("get-training-today", help="获取今日训练安排")
    sub_get_training_today.set_defaults(func=cmd_get_training_today)

    sub_get_training_weekly = subparsers.add_parser("get-training-weekly", help="获取本周训练统计")
    sub_get_training_weekly.set_defaults(func=cmd_get_training_weekly)

    sub_get_training_monthly = subparsers.add_parser("get-training-monthly", help="获取指定月份训练安排")
    sub_get_training_monthly.add_argument("--year", type=int, required=True, help="年份，例如 2026")
    sub_get_training_monthly.add_argument("--month", type=int, required=True, help="月份，1-12")
    sub_get_training_monthly.set_defaults(func=cmd_get_training_monthly)

    sub_get_training_weekly_progress = subparsers.add_parser("get-training-weekly-progress", help="获取本周训练进度")
    sub_get_training_weekly_progress.set_defaults(func=cmd_get_training_weekly_progress)

    sub_get_training_recommendations = subparsers.add_parser("get-training-recommendations", help="获取推荐的训练计划")
    sub_get_training_recommendations.add_argument("--limit", type=int, default=5, help="推荐数量，默认 5")
    sub_get_training_recommendations.set_defaults(func=cmd_get_training_recommendations)

    sub_get_training_plan_detail = subparsers.add_parser("get-training-plan-detail", help="获取训练计划详情")
    sub_get_training_plan_detail.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_get_training_plan_detail.set_defaults(func=cmd_get_training_plan_detail)

    sub_get_diet_today = subparsers.add_parser("get-diet-today", help="获取今日饮食记录和统计")
    sub_get_diet_today.set_defaults(func=cmd_get_diet_today)

    sub_get_diet_weekly_trend = subparsers.add_parser("get-diet-weekly-trend", help="获取本周饮食趋势")
    sub_get_diet_weekly_trend.set_defaults(func=cmd_get_diet_weekly_trend)

    sub_get_nutrition_progress = subparsers.add_parser("get-nutrition-progress", help="获取今日营养摄入进度")
    sub_get_nutrition_progress.set_defaults(func=cmd_get_nutrition_progress)

    sub_get_food_recommendations = subparsers.add_parser("get-food-recommendations", help="获取推荐的食物")
    sub_get_food_recommendations.set_defaults(func=cmd_get_food_recommendations)

    sub_get_user_settings = subparsers.add_parser("get-user-settings", help="获取用户设置")
    sub_get_user_settings.set_defaults(func=cmd_get_user_settings)

    sub_search_foods = subparsers.add_parser("search-foods", help="搜索食物数据库")
    sub_search_foods.add_argument("--keyword", help="搜索关键词")
    sub_search_foods.add_argument("--category", help="食物分类")
    sub_search_foods.add_argument("--meal-type", help="适合餐次：breakfast/lunch/dinner")
    sub_search_foods.add_argument("--limit", type=int, default=50, help="结果数量，默认 50")
    sub_search_foods.set_defaults(func=cmd_search_foods)

    sub_get_food_categories = subparsers.add_parser("get-food-categories", help="获取食物分类列表")
    sub_get_food_categories.set_defaults(func=cmd_get_food_categories)

    sub_search_exercises = subparsers.add_parser("search-exercises", help="搜索动作库")
    sub_search_exercises.add_argument("--keyword", help="动作名称关键词")
    sub_search_exercises.add_argument("--target-muscle", help="目标肌肉")
    sub_search_exercises.add_argument("--exercise-type", help="动作类型")
    sub_search_exercises.add_argument("--difficulty", help="难度")
    sub_search_exercises.add_argument("--equipment", help="器械")
    sub_search_exercises.add_argument("--force-type", help="发力类型")
    sub_search_exercises.add_argument("--mechanics", help="力学类型")
    sub_search_exercises.add_argument("--limit", type=int, default=200, help="结果数量，默认 200")
    sub_search_exercises.set_defaults(func=cmd_search_exercises)

    sub_get_exercise_detail = subparsers.add_parser("get-exercise-detail", help="获取动作详情")
    sub_get_exercise_detail.add_argument("--exercise-id", type=int, required=True, help="动作 ID")
    sub_get_exercise_detail.set_defaults(func=cmd_get_exercise_detail)

    sub_get_exercise_categories = subparsers.add_parser("get-exercise-categories", help="获取动作分类选项")
    sub_get_exercise_categories.set_defaults(func=cmd_get_exercise_categories)

    sub_pin_exercise = subparsers.add_parser("pin-exercise", help="收藏动作")
    sub_pin_exercise.add_argument("--exercise-id", type=int, required=True, help="动作 ID")
    sub_pin_exercise.set_defaults(func=cmd_pin_exercise)

    sub_unpin_exercise = subparsers.add_parser("unpin-exercise", help="取消收藏动作")
    sub_unpin_exercise.add_argument("--exercise-id", type=int, required=True, help="动作 ID")
    sub_unpin_exercise.set_defaults(func=cmd_unpin_exercise)

    sub_get_pinned_exercises = subparsers.add_parser("get-pinned-exercises", help="获取已收藏动作列表")
    sub_get_pinned_exercises.set_defaults(func=cmd_get_pinned_exercises)

    sub_reorder_pinned_exercises = subparsers.add_parser("reorder-pinned-exercises", help="重排收藏动作")
    sub_reorder_pinned_exercises.add_argument("--exercise-ids", required=True, help="动作 ID，用英文逗号分隔")
    sub_reorder_pinned_exercises.set_defaults(func=cmd_reorder_pinned_exercises)

    sub_get_full_overview = subparsers.add_parser("get-full-overview", help="获取用户综合概览")
    sub_get_full_overview.set_defaults(func=cmd_get_full_overview)

    # -------------------------------------------------------------------------
    # 写入命令
    # -------------------------------------------------------------------------
    sub_update_profile = subparsers.add_parser("update-profile", help="更新用户基本信息")
    sub_update_profile.add_argument("--name", help="姓名")
    sub_update_profile.add_argument("--avatar", help="头像 URL")
    sub_update_profile.set_defaults(func=cmd_update_profile)

    sub_add_health_metric = subparsers.add_parser("add-health-metric", help="添加健康指标记录")
    sub_add_health_metric.add_argument("--weight", type=float, help="体重 (kg)")
    sub_add_health_metric.add_argument("--height", type=float, help="身高 (cm)")
    sub_add_health_metric.add_argument("--body-fat", type=float, help="体脂率 (%)")
    sub_add_health_metric.add_argument("--measure-date", help="测量日期，YYYY-MM-DD")
    sub_add_health_metric.set_defaults(func=cmd_add_health_metric)

    sub_add_training_plan = subparsers.add_parser("add-training-plan", help="创建训练计划")
    sub_add_training_plan.add_argument("--plan-name", required=True, help="训练计划名称")
    sub_add_training_plan.add_argument("--plan-type", required=True, choices=["strength", "cardio", "flexibility"], help="训练类型")
    sub_add_training_plan.add_argument("--scheduled-date", help="计划日期，YYYY-MM-DD")
    sub_add_training_plan.add_argument("--estimated-duration", type=int, default=60, help="预计时长（分钟）")
    sub_add_training_plan.add_argument("--target-intensity", default="medium", choices=["low", "medium", "high"], help="目标强度")
    sub_add_training_plan.add_argument("--note", help="备注")
    sub_add_training_plan.add_argument("--exercises-json", help="训练动作 JSON 数组")
    sub_add_training_plan.set_defaults(func=cmd_add_training_plan)

    sub_update_training_plan = subparsers.add_parser("update-training-plan", help="更新训练计划")
    sub_update_training_plan.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_update_training_plan.add_argument("--plan-name", help="训练计划名称")
    sub_update_training_plan.add_argument("--scheduled-date", help="计划日期")
    sub_update_training_plan.add_argument("--estimated-duration", type=int, help="预计时长（分钟）")
    sub_update_training_plan.add_argument("--target-intensity", choices=["low", "medium", "high"], help="目标强度")
    sub_update_training_plan.add_argument("--note", help="备注")
    sub_update_training_plan.set_defaults(func=cmd_update_training_plan)

    sub_complete_training = subparsers.add_parser("complete-training", help="完成一个训练计划")
    sub_complete_training.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_complete_training.add_argument("--actual-duration", type=int, help="实际时长（分钟）")
    sub_complete_training.add_argument("--actual-intensity", choices=["low", "medium", "high"], help="实际强度")
    sub_complete_training.add_argument("--calories-burned", type=int, help="消耗热量（kcal）")
    sub_complete_training.add_argument("--completed-date", help="完成日期，YYYY-MM-DD")
    sub_complete_training.add_argument("--note", help="备注")
    sub_complete_training.set_defaults(func=cmd_complete_training)

    sub_delete_training_plan = subparsers.add_parser("delete-training-plan", help="删除训练计划")
    sub_delete_training_plan.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_delete_training_plan.set_defaults(func=cmd_delete_training_plan)

    sub_update_plan_exercise = subparsers.add_parser("update-plan-exercise", help="更新计划中的动作")
    sub_update_plan_exercise.add_argument("--exercise-item-id", type=int, required=True, help="动作项 ID")
    sub_update_plan_exercise.add_argument("--sets", type=int, help="组数")
    sub_update_plan_exercise.add_argument("--reps", type=int, help="次数")
    sub_update_plan_exercise.add_argument("--weight", type=float, help="重量")
    sub_update_plan_exercise.add_argument("--duration", type=int, help="时长")
    sub_update_plan_exercise.set_defaults(func=cmd_update_plan_exercise)

    sub_add_meal = subparsers.add_parser("add-meal", help="添加饮食记录")
    sub_add_meal.add_argument("--meal-type", required=True, choices=["breakfast", "lunch", "dinner", "snack"], help="餐次类型")
    sub_add_meal.add_argument("--meal-name", required=True, help="食物名称")
    sub_add_meal.add_argument("--calories", type=int, required=True, help="热量（kcal）")
    sub_add_meal.add_argument("--protein", type=float, default=0, help="蛋白质（g）")
    sub_add_meal.add_argument("--carbs", type=float, default=0, help="碳水（g）")
    sub_add_meal.add_argument("--fat", type=float, default=0, help="脂肪（g）")
    sub_add_meal.add_argument("--water", type=int, default=0, help="水（ml）")
    sub_add_meal.add_argument("--meal-date", help="日期，YYYY-MM-DD")
    sub_add_meal.add_argument("--meal-time", help="时间，HH:MM:SS")
    sub_add_meal.add_argument("--note", help="备注")
    sub_add_meal.set_defaults(func=cmd_add_meal)

    sub_update_meal = subparsers.add_parser("update-meal", help="更新饮食记录")
    sub_update_meal.add_argument("--meal-id", type=int, required=True, help="饮食记录 ID")
    sub_update_meal.add_argument("--meal-name", help="食物名称")
    sub_update_meal.add_argument("--calories", type=int, help="热量（kcal）")
    sub_update_meal.add_argument("--protein", type=float, help="蛋白质（g）")
    sub_update_meal.add_argument("--carbs", type=float, help="碳水（g）")
    sub_update_meal.add_argument("--fat", type=float, help="脂肪（g）")
    sub_update_meal.add_argument("--water", type=int, help="水（ml）")
    sub_update_meal.set_defaults(func=cmd_update_meal)

    sub_delete_meal = subparsers.add_parser("delete-meal", help="删除饮食记录")
    sub_delete_meal.add_argument("--meal-id", type=int, required=True, help="饮食记录 ID")
    sub_delete_meal.set_defaults(func=cmd_delete_meal)

    sub_add_custom_food = subparsers.add_parser("add-custom-food", help="添加自定义食物")
    sub_add_custom_food.add_argument("--name", required=True, help="食物名称")
    sub_add_custom_food.add_argument("--category", required=True, help="分类")
    sub_add_custom_food.add_argument("--portion-calories", type=int, required=True, help="单份热量（kcal）")
    sub_add_custom_food.add_argument("--calories-per-100g", type=int, required=True, help="每 100g 热量（kcal）")
    sub_add_custom_food.add_argument("--portion-unit", help="单份单位")
    sub_add_custom_food.add_argument("--portion-grams", type=float, help="单份克数")
    sub_add_custom_food.add_argument("--calorie-level", help="热量等级")
    sub_add_custom_food.add_argument("--protein", type=float, default=0, help="蛋白质（g）")
    sub_add_custom_food.add_argument("--carbs", type=float, default=0, help="碳水（g）")
    sub_add_custom_food.add_argument("--fat", type=float, default=0, help="脂肪（g）")
    sub_add_custom_food.add_argument("--suitable-meals", default="breakfast,lunch,dinner", help="适合餐次")
    sub_add_custom_food.set_defaults(func=cmd_add_custom_food)

    sub_update_settings = subparsers.add_parser("update-settings", help="更新用户设置")
    sub_update_settings.add_argument("--calorie-goal", type=int, help="每日热量目标（kcal）")
    sub_update_settings.add_argument("--protein-goal", type=int, help="蛋白质目标（g）")
    sub_update_settings.add_argument("--carbs-goal", type=int, help="碳水目标（g）")
    sub_update_settings.add_argument("--fat-goal", type=int, help="脂肪目标（g）")
    sub_update_settings.add_argument("--water-goal", type=int, help="饮水目标（ml）")
    sub_update_settings.add_argument("--weight-goal", type=float, help="目标体重（kg）")
    sub_update_settings.add_argument("--weekly-training-goal", type=int, help="每周训练目标（次数）")
    sub_update_settings.set_defaults(func=cmd_update_settings)

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
