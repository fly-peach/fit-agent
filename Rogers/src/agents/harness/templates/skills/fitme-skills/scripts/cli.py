"""Fitme CLI - 统一命令行入口

提供用户数据的读取和写入操作。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path so `import src...` works from any cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT))
# Add current script's directory to path to import fitme_data_tool
sys.path.insert(0, str(Path(__file__).parent))

from fitme_data_tool import (
    get_user_profile,
    get_health_summary,
    get_health_history,
    get_training_today,
    get_training_weekly,
    get_training_recommendations,
    get_diet_today,
    get_diet_weekly_trend,
    get_food_recommendations,
    get_nutrition_progress,
    get_user_settings,
    search_foods,
    get_food_categories,
    get_full_overview,
    update_profile,
    add_health_metric,
    update_health_metric,
    delete_health_metric,
    delete_training_plan,
    add_meal,
    update_meal,
    delete_meal,
    add_custom_food,
    update_custom_food,
    delete_custom_food,
    update_settings,
    analyze_diet_gap,
    search_exercises,
    get_exercise_detail,
    get_exercise_categories,
    pin_exercise,
    unpin_exercise,
    get_pinned_exercises,
    reorder_pinned_exercises,
    get_training_monthly_schedule,
    get_training_weekly_progress,
    get_training_plan_detail,
    create_training_plan,
    update_training_plan,
    complete_training_plan,
    update_plan_exercise_item,
    renew_recurring_training_plan,
)
from src.agents.harness.context import NotAuthenticatedError, get_user_id_from_token


def _output(data: dict, exit_code: int = 0) -> None:
    """输出 JSON 并退出。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))
    sys.exit(exit_code)


def _resolve_user_id(args: argparse.Namespace) -> int:
    """从登录 token 解析当前用户。"""
    token = getattr(args, "token", "")
    if not token:
        raise ValueError("必须提供 --token")

    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    try:
        return int(get_user_id_from_token(token))
    except NotAuthenticatedError as exc:
        raise ValueError("无效或已过期的登录 token") from exc


def _parse_json_arg(raw: str | None, field_name: str) -> list[dict[str, Any]] | None:
    """解析 CLI 里的 JSON 数组参数。"""
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} 必须是合法 JSON") from exc
    if not isinstance(parsed, list):
        raise ValueError(f"{field_name} 必须是 JSON 数组")
    return parsed


def _parse_exercise_items(args: argparse.Namespace) -> list[dict[str, Any]] | None:
    """解析训练动作项，支持 JSON 或重复的 exercise-item 简写。"""
    items: list[dict[str, Any]] = []

    json_items = _parse_json_arg(getattr(args, "exercises_json", None), "exercises_json")
    if json_items:
        items.extend(json_items)

    raw_items = getattr(args, "exercise_item", None) or []
    for raw in raw_items:
        item: dict[str, Any] = {}
        for part in raw.split(","):
            piece = part.strip()
            if not piece:
                continue
            if "=" not in piece:
                raise ValueError("exercise_item 必须使用 key=value 形式")
            key, value = piece.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key in {"exerciseId", "sets", "reps", "duration"}:
                item[key] = int(value)
            elif key == "weight":
                item[key] = float(value)
            else:
                item[key] = value
        if not item:
            raise ValueError("exercise_item 不能为空")
        items.append(item)

    return items or None


# =============================================================================
# 读取命令
# =============================================================================

def cmd_get_user_profile(args: argparse.Namespace) -> None:
    """获取用户基本信息。"""
    result = get_user_profile(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_training_plan_detail(args: argparse.Namespace) -> None:
    """获取训练计划详情。"""
    result = get_training_plan_detail(args.auth_user_id, plan_id=args.plan_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_health_summary(args: argparse.Namespace) -> None:
    """获取用户最新健康指标。"""
    result = get_health_summary(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_health_history(args: argparse.Namespace) -> None:
    """获取近期健康指标变化趋势。"""
    result = get_health_history(args.auth_user_id, limit=args.limit)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_training_today(args: argparse.Namespace) -> None:
    """获取今日训练计划。"""
    result = get_training_today(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_training_weekly(args: argparse.Namespace) -> None:
    """获取本周训练统计和安排。"""
    result = get_training_weekly(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_training_monthly(args: argparse.Namespace) -> None:
    """获取指定月份训练安排。"""
    result = get_training_monthly_schedule(
        args.auth_user_id,
        year=args.year,
        month=args.month,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_training_weekly_progress(args: argparse.Namespace) -> None:
    """获取本周训练进度。"""
    result = get_training_weekly_progress(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_training_recommendations(args: argparse.Namespace) -> None:
    """获取推荐的训练计划。"""
    result = get_training_recommendations(args.auth_user_id, limit=args.limit)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_diet_today(args: argparse.Namespace) -> None:
    """获取今日饮食记录和统计。"""
    result = get_diet_today(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_diet_weekly_trend(args: argparse.Namespace) -> None:
    """获取本周饮食趋势。"""
    result = get_diet_weekly_trend(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_food_recommendations(args: argparse.Namespace) -> None:
    """获取推荐的食物。"""
    result = get_food_recommendations(args.auth_user_id, limit=args.limit)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_nutrition_progress(args: argparse.Namespace) -> None:
    """获取今日营养进度。"""
    result = get_nutrition_progress(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_user_settings(args: argparse.Namespace) -> None:
    """获取用户设置。"""
    result = get_user_settings(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_search_foods(args: argparse.Namespace) -> None:
    """搜索食物数据库。"""
    result = search_foods(
        args.auth_user_id,
        keyword=args.keyword or "",
        category=args.category or "",
        meal_type=args.meal_type or "",
        limit=args.limit,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_food_categories(args: argparse.Namespace) -> None:
    """获取食物分类。"""
    result = get_food_categories(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_analyze_diet_gap(args: argparse.Namespace) -> None:
    """分析今日饮食缺口并给出建议。"""
    result = analyze_diet_gap(
        args.auth_user_id,
        meal_type=args.meal_type or "",
        limit=args.limit,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_full_overview(args: argparse.Namespace) -> None:
    """获取用户综合概览。"""
    result = get_full_overview(args.auth_user_id)


def cmd_search_exercises(args: argparse.Namespace) -> None:
    """搜索动作库。"""
    result = search_exercises(
        args.auth_user_id,
        keyword=args.keyword or "",
        target_muscle=args.target_muscle or "",
        exercise_type=args.exercise_type or "",
        difficulty=args.difficulty or "",
        equipment=args.equipment or "",
        force_type=args.force_type or "",
        mechanics=args.mechanics or "",
        limit=args.limit,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_exercise_detail(args: argparse.Namespace) -> None:
    """获取动作详情。"""
    result = get_exercise_detail(args.auth_user_id, exercise_id=args.exercise_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_exercise_categories(args: argparse.Namespace) -> None:
    """获取动作分类选项。"""
    result = get_exercise_categories()
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_pin_exercise(args: argparse.Namespace) -> None:
    """收藏动作。"""
    result = pin_exercise(args.auth_user_id, exercise_id=args.exercise_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_unpin_exercise(args: argparse.Namespace) -> None:
    """取消收藏动作。"""
    result = unpin_exercise(args.auth_user_id, exercise_id=args.exercise_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_get_pinned_exercises(args: argparse.Namespace) -> None:
    """获取收藏动作列表。"""
    result = get_pinned_exercises(args.auth_user_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_reorder_pinned_exercises(args: argparse.Namespace) -> None:
    """按顺序重排收藏动作。"""
    exercise_ids = [
        int(item.strip())
        for item in args.exercise_ids.split(",")
        if item.strip()
    ]
    result = reorder_pinned_exercises(args.auth_user_id, exercise_ids=exercise_ids)
    _output(result, exit_code=0 if result.get("success") else 1)
    _output(result, exit_code=0 if result.get("success") else 1)


# =============================================================================
# 写入命令
# =============================================================================

def cmd_update_profile(args: argparse.Namespace) -> None:
    """更新用户基本信息。"""
    kwargs = {}
    if args.name:
        kwargs["name"] = args.name
    if args.avatar:
        kwargs["avatar"] = args.avatar
    result = update_profile(args.auth_user_id, **kwargs)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_add_health_metric(args: argparse.Namespace) -> None:
    """添加一条新的健康指标记录。"""
    result = add_health_metric(
        args.auth_user_id,
        weight=args.weight,
        height=args.height,
        body_fat=args.body_fat,
        measure_date=args.measure_date,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_update_health_metric(args: argparse.Namespace) -> None:
    """更新一条健康指标记录。"""
    result = update_health_metric(
        args.auth_user_id,
        record_id=args.record_id,
        weight=args.weight,
        height=args.height,
        body_fat=args.body_fat,
        measure_date=args.measure_date,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_delete_health_metric(args: argparse.Namespace) -> None:
    """删除一条健康指标记录。"""
    result = delete_health_metric(
        args.auth_user_id,
        record_id=args.record_id,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_add_training_plan(args: argparse.Namespace) -> None:
    """创建一条训练计划。"""
    result = create_training_plan(
        args.auth_user_id,
        plan_name=args.plan_name,
        plan_type=args.plan_type,
        scheduled_date=args.scheduled_date,
        estimated_duration=args.estimated_duration,
        target_intensity=args.target_intensity,
        note=args.note,
        is_recurring=args.is_recurring,
        exercises=_parse_exercise_items(args),
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_update_training_plan(args: argparse.Namespace) -> None:
    """更新训练计划。"""
    result = update_training_plan(
        args.auth_user_id,
        plan_id=args.plan_id,
        plan_name=args.plan_name,
        scheduled_date=args.scheduled_date,
        estimated_duration=args.estimated_duration,
        target_intensity=args.target_intensity,
        note=args.note,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_complete_training(args: argparse.Namespace) -> None:
    """完成一个训练计划，标记为已完成并记录实际数据。"""
    result = complete_training_plan(
        args.auth_user_id,
        plan_id=args.plan_id,
        actual_duration=args.actual_duration,
        actual_intensity=args.actual_intensity,
        calories_burned=args.calories_burned,
        note=args.note,
        completed_date=args.completed_date,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_update_plan_exercise(args: argparse.Namespace) -> None:
    """更新计划中的动作项。"""
    result = update_plan_exercise_item(
        args.auth_user_id,
        exercise_item_id=args.exercise_item_id,
        sets=args.sets,
        reps=args.reps,
        weight=args.weight,
        duration=args.duration,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_delete_training_plan(args: argparse.Namespace) -> None:
    """删除一个训练计划。"""
    result = delete_training_plan(args.auth_user_id, plan_id=args.plan_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_renew_recurring_training_plan(args: argparse.Namespace) -> None:
    """为循环训练计划续期。"""
    result = renew_recurring_training_plan(args.auth_user_id, plan_id=args.plan_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_add_meal(args: argparse.Namespace) -> None:
    """添加饮食记录。"""
    result = add_meal(
        args.auth_user_id,
        meal_type=args.meal_type,
        meal_name=args.meal_name,
        calories=args.calories,
        protein=args.protein,
        carbs=args.carbs,
        fat=args.fat,
        water=args.water,
        meal_date_str=args.meal_date,
        meal_time_str=args.meal_time,
        note=args.note,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_update_meal(args: argparse.Namespace) -> None:
    """更新一条饮食记录。"""
    kwargs = {}
    if args.meal_name:
        kwargs["meal_name"] = args.meal_name
    if args.calories is not None:
        kwargs["calories"] = args.calories
    if args.protein is not None:
        kwargs["protein"] = args.protein
    if args.carbs is not None:
        kwargs["carbs"] = args.carbs
    if args.fat is not None:
        kwargs["fat"] = args.fat
    if args.water is not None:
        kwargs["water"] = args.water
    result = update_meal(args.auth_user_id, meal_id=args.meal_id, **kwargs)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_delete_meal(args: argparse.Namespace) -> None:
    """删除一条饮食记录。"""
    result = delete_meal(args.auth_user_id, meal_id=args.meal_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_add_custom_food(args: argparse.Namespace) -> None:
    """添加自定义食物到用户个人食物库。"""
    result = add_custom_food(
        args.auth_user_id,
        name=args.name,
        category=args.category,
        portion_calories=args.portion_calories,
        calories_per_100g=args.calories_per_100g,
        portion_unit=args.portion_unit,
        portion_grams=args.portion_grams,
        calorie_level=args.calorie_level,
        protein=args.protein,
        carbs=args.carbs,
        fat=args.fat,
        suitable_meals=args.suitable_meals,
    )
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_update_custom_food(args: argparse.Namespace) -> None:
    """更新自定义食物。"""
    kwargs = {}
    if args.name:
        kwargs["name"] = args.name
    if args.category:
        kwargs["category"] = args.category
    if args.portion_calories is not None:
        kwargs["portion_calories"] = args.portion_calories
    if args.calories_per_100g is not None:
        kwargs["calories_per_100g"] = args.calories_per_100g
    if args.portion_unit:
        kwargs["portion_unit"] = args.portion_unit
    if args.portion_grams is not None:
        kwargs["portion_grams"] = args.portion_grams
    if args.calorie_level:
        kwargs["calorie_level"] = args.calorie_level
    if args.protein is not None:
        kwargs["protein"] = args.protein
    if args.carbs is not None:
        kwargs["carbs"] = args.carbs
    if args.fat is not None:
        kwargs["fat"] = args.fat
    if args.suitable_meals:
        kwargs["suitable_meals"] = args.suitable_meals
    result = update_custom_food(args.auth_user_id, food_id=args.food_id, **kwargs)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_delete_custom_food(args: argparse.Namespace) -> None:
    """删除一条自定义食物。"""
    result = delete_custom_food(args.auth_user_id, food_id=args.food_id)
    _output(result, exit_code=0 if result.get("success") else 1)


def cmd_update_settings(args: argparse.Namespace) -> None:
    """更新用户设置（目标值等）。"""
    kwargs = {}
    if args.calorie_goal is not None:
        kwargs["calorie_goal"] = args.calorie_goal
    if args.protein_goal is not None:
        kwargs["protein_goal"] = args.protein_goal
    if args.carbs_goal is not None:
        kwargs["carbs_goal"] = args.carbs_goal
    if args.fat_goal is not None:
        kwargs["fat_goal"] = args.fat_goal
    if args.water_goal is not None:
        kwargs["water_goal"] = args.water_goal
    if args.weight_goal is not None:
        kwargs["weight_goal"] = args.weight_goal
    if args.weekly_training_goal is not None:
        kwargs["weekly_training_goal"] = args.weekly_training_goal
    result = update_settings(args.auth_user_id, **kwargs)
    _output(result, exit_code=0 if result.get("success") else 1)


# =============================================================================
# 参数解析
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fitme-cli",
        description="Fitme 健康管理 CLI",
    )
    parser.add_argument(
        "--token",
        required=True,
        help="登录 token，支持原始 JWT 或 `Bearer <token>` 格式",
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
    sub_get_health_history.add_argument("--limit", type=int, default=7, help="历史记录数量，默认 7")
    sub_get_health_history.set_defaults(func=cmd_get_health_history)

    sub_get_training_today = subparsers.add_parser("get-training-today", help="获取今日训练计划")
    sub_get_training_today.set_defaults(func=cmd_get_training_today)

    sub_get_training_weekly = subparsers.add_parser("get-training-weekly", help="获取本周训练统计和安排")
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

    sub_get_diet_today = subparsers.add_parser("get-diet-today", help="获取今日饮食记录和统计")
    sub_get_diet_today.set_defaults(func=cmd_get_diet_today)

    sub_get_diet_weekly_trend = subparsers.add_parser("get-diet-weekly-trend", help="获取本周饮食趋势")
    sub_get_diet_weekly_trend.set_defaults(func=cmd_get_diet_weekly_trend)

    sub_get_nutrition_progress = subparsers.add_parser("get-nutrition-progress", help="获取今日营养进度")
    sub_get_nutrition_progress.set_defaults(func=cmd_get_nutrition_progress)

    sub_get_food_recommendations = subparsers.add_parser("get-food-recommendations", help="获取推荐的食物")
    sub_get_food_recommendations.add_argument("--limit", type=int, default=5, help="推荐数量，默认 5")
    sub_get_food_recommendations.set_defaults(func=cmd_get_food_recommendations)

    sub_get_user_settings = subparsers.add_parser("get-user-settings", help="获取用户设置")
    sub_get_user_settings.set_defaults(func=cmd_get_user_settings)

    sub_search_foods = subparsers.add_parser("search-foods", help="搜索食物数据库")
    sub_search_foods.add_argument("--keyword", help="搜索关键词")
    sub_search_foods.add_argument("--category", help="食物分类")
    sub_search_foods.add_argument("--meal-type", help="适合餐次")
    sub_search_foods.add_argument("--limit", type=int, default=50, help="结果数量，默认 50")
    sub_search_foods.set_defaults(func=cmd_search_foods)

    sub_get_food_categories = subparsers.add_parser("get-food-categories", help="获取食物分类")
    sub_get_food_categories.set_defaults(func=cmd_get_food_categories)

    sub_analyze_diet_gap = subparsers.add_parser("analyze-diet-gap", help="分析今日饮食缺口并推荐食物")
    sub_analyze_diet_gap.add_argument("--meal-type", help="限定餐次，如 breakfast/lunch/dinner/snack")
    sub_analyze_diet_gap.add_argument("--limit", type=int, default=5, help="建议数量，默认 5")
    sub_analyze_diet_gap.set_defaults(func=cmd_analyze_diet_gap)

    sub_get_full_overview = subparsers.add_parser("get-full-overview", help="获取用户综合概览")
    sub_get_full_overview.set_defaults(func=cmd_get_full_overview)

    sub_get_training_plan_detail = subparsers.add_parser("get-training-plan-detail", help="获取训练计划详情和动作项")
    sub_get_training_plan_detail.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_get_training_plan_detail.set_defaults(func=cmd_get_training_plan_detail)

    sub_search_exercises = subparsers.add_parser("search-exercises", help="搜索动作库")
    sub_search_exercises.add_argument("--keyword", help="动作名称关键词")
    sub_search_exercises.add_argument("--target-muscle", help="目标肌群")
    sub_search_exercises.add_argument("--exercise-type", help="动作类型")
    sub_search_exercises.add_argument("--difficulty", help="难度")
    sub_search_exercises.add_argument("--equipment", help="器械")
    sub_search_exercises.add_argument("--force-type", help="发力类型")
    sub_search_exercises.add_argument("--mechanics", help="力学类型")
    sub_search_exercises.add_argument("--limit", type=int, default=20, help="结果数量，默认 20")
    sub_search_exercises.set_defaults(func=cmd_search_exercises)

    sub_get_exercise_detail = subparsers.add_parser("get-exercise-detail", help="获取动作详情")
    sub_get_exercise_detail.add_argument("--exercise-id", type=int, required=True, help="动作 ID")
    sub_get_exercise_detail.set_defaults(func=cmd_get_exercise_detail)

    sub_get_exercise_categories = subparsers.add_parser("get-exercise-categories", help="获取动作分类选项")
    sub_get_exercise_categories.set_defaults(func=cmd_get_exercise_categories)

    sub_get_pinned_exercises = subparsers.add_parser("get-pinned-exercises", help="获取已收藏动作")
    sub_get_pinned_exercises.set_defaults(func=cmd_get_pinned_exercises)

    # -------------------------------------------------------------------------
    # 写入命令
    # -------------------------------------------------------------------------
    sub_update_profile = subparsers.add_parser("update-profile", help="更新用户基本信息")
    sub_update_profile.add_argument("--name", help="姓名")
    sub_update_profile.add_argument("--avatar", help="头像")
    sub_update_profile.set_defaults(func=cmd_update_profile)

    sub_add_health_metric = subparsers.add_parser("add-health-metric", help="添加一条新的健康指标记录")
    sub_add_health_metric.add_argument("--weight", type=float, help="体重 (kg)")
    sub_add_health_metric.add_argument("--height", type=float, help="身高 (cm)")
    sub_add_health_metric.add_argument("--body-fat", type=float, help="体脂率 (%)")
    sub_add_health_metric.add_argument("--measure-date", help="测量日期，YYYY-MM-DD，默认今天")
    sub_add_health_metric.set_defaults(func=cmd_add_health_metric)

    sub_update_health_metric = subparsers.add_parser("update-health-metric", help="更新一条健康指标记录")
    sub_update_health_metric.add_argument("--record-id", type=int, required=True, help="健康指标记录 ID")
    sub_update_health_metric.add_argument("--weight", type=float, help="体重 (kg)")
    sub_update_health_metric.add_argument("--height", type=float, help="身高 (cm)")
    sub_update_health_metric.add_argument("--body-fat", type=float, help="体脂率 (%)")
    sub_update_health_metric.add_argument("--measure-date", help="测量日期，YYYY-MM-DD")
    sub_update_health_metric.set_defaults(func=cmd_update_health_metric)

    sub_delete_health_metric = subparsers.add_parser("delete-health-metric", help="删除一条健康指标记录")
    sub_delete_health_metric.add_argument("--record-id", type=int, required=True, help="健康指标记录 ID")
    sub_delete_health_metric.set_defaults(func=cmd_delete_health_metric)

    sub_add_training_plan = subparsers.add_parser("add-training-plan", help="创建一条训练计划")
    sub_add_training_plan.add_argument("--plan-name", required=True, help="训练计划名称")
    sub_add_training_plan.add_argument("--plan-type", required=True, choices=["strength", "cardio", "flexibility"], help="训练类型：strength/cardio/flexibility")
    sub_add_training_plan.add_argument("--scheduled-date", help="计划日期，YYYY-MM-DD，默认今天")
    sub_add_training_plan.add_argument("--estimated-duration", type=int, default=60, help="预计时长（分钟），默认 60")
    sub_add_training_plan.add_argument("--target-intensity", default="medium", choices=["low", "medium", "high"], help="目标强度：low/medium/high，默认 medium")
    sub_add_training_plan.add_argument("--note", help="备注")
    sub_add_training_plan.add_argument("--is-recurring", action="store_true", help="是否生成循环计划（默认生成未来 8 周）")
    sub_add_training_plan.add_argument(
        "--exercises-json",
        help='训练动作数组 JSON，例如 [{"exerciseId":12,"sets":4,"reps":10},{"customName":"平板支撑","duration":60}]',
    )
    sub_add_training_plan.add_argument(
        "--exercise-item",
        action="append",
        help='单个动作项，支持重复传入，例如 "exerciseId=12,sets=4,reps=10" 或 "customName=平板支撑,duration=60"',
    )
    sub_add_training_plan.set_defaults(func=cmd_add_training_plan)

    sub_update_training_plan = subparsers.add_parser("update-training-plan", help="更新训练计划基础信息")
    sub_update_training_plan.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_update_training_plan.add_argument("--plan-name", help="训练计划名称")
    sub_update_training_plan.add_argument("--scheduled-date", help="计划日期，YYYY-MM-DD")
    sub_update_training_plan.add_argument("--estimated-duration", type=int, help="预计时长（分钟）")
    sub_update_training_plan.add_argument("--target-intensity", choices=["low", "medium", "high"], help="目标强度")
    sub_update_training_plan.add_argument("--note", help="备注")
    sub_update_training_plan.set_defaults(func=cmd_update_training_plan)

    sub_complete_training = subparsers.add_parser("complete-training", help="完成一个训练计划")
    sub_complete_training.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_complete_training.add_argument("--actual-duration", type=int, help="实际时长（分钟）")
    sub_complete_training.add_argument("--actual-intensity", choices=["low", "medium", "high"], help="实际强度")
    sub_complete_training.add_argument("--calories-burned", type=int, help="消耗热量（kcal）")
    sub_complete_training.add_argument("--completed-date", help="完成日期，YYYY-MM-DD，默认今天")
    sub_complete_training.add_argument("--note", help="备注")
    sub_complete_training.set_defaults(func=cmd_complete_training)

    sub_update_plan_exercise = subparsers.add_parser("update-plan-exercise", help="更新计划中的动作项")
    sub_update_plan_exercise.add_argument("--exercise-item-id", type=int, required=True, help="计划动作项 ID")
    sub_update_plan_exercise.add_argument("--sets", type=int, help="组数")
    sub_update_plan_exercise.add_argument("--reps", type=int, help="次数")
    sub_update_plan_exercise.add_argument("--weight", type=float, help="重量")
    sub_update_plan_exercise.add_argument("--duration", type=int, help="时长（秒或分钟，按动作语义）")
    sub_update_plan_exercise.set_defaults(func=cmd_update_plan_exercise)

    sub_delete_training_plan = subparsers.add_parser("delete-training-plan", help="删除一个训练计划")
    sub_delete_training_plan.add_argument("--plan-id", type=int, required=True, help="训练计划 ID")
    sub_delete_training_plan.set_defaults(func=cmd_delete_training_plan)

    sub_renew_recurring_training_plan = subparsers.add_parser("renew-recurring-training-plan", help="为循环计划续期")
    sub_renew_recurring_training_plan.add_argument("--plan-id", type=int, required=True, help="循环训练计划中的任意计划 ID")
    sub_renew_recurring_training_plan.set_defaults(func=cmd_renew_recurring_training_plan)

    sub_pin_exercise = subparsers.add_parser("pin-exercise", help="收藏动作")
    sub_pin_exercise.add_argument("--exercise-id", type=int, required=True, help="动作 ID")
    sub_pin_exercise.set_defaults(func=cmd_pin_exercise)

    sub_unpin_exercise = subparsers.add_parser("unpin-exercise", help="取消收藏动作")
    sub_unpin_exercise.add_argument("--exercise-id", type=int, required=True, help="动作 ID")
    sub_unpin_exercise.set_defaults(func=cmd_unpin_exercise)

    sub_reorder_pinned_exercises = subparsers.add_parser("reorder-pinned-exercises", help="重排收藏动作")
    sub_reorder_pinned_exercises.add_argument(
        "--exercise-ids",
        required=True,
        help="按新顺序排列的动作 ID，使用英文逗号分隔，例如 12,8,35",
    )
    sub_reorder_pinned_exercises.set_defaults(func=cmd_reorder_pinned_exercises)

    sub_add_meal = subparsers.add_parser("add-meal", help="添加饮食记录")
    sub_add_meal.add_argument("--meal-type", required=True, choices=["breakfast", "lunch", "dinner", "snack"], help="餐次类型")
    sub_add_meal.add_argument("--meal-name", required=True, help="食物名称")
    sub_add_meal.add_argument("--calories", type=int, required=True, help="热量（kcal）")
    sub_add_meal.add_argument("--protein", type=float, default=0, help="蛋白质（g）")
    sub_add_meal.add_argument("--carbs", type=float, default=0, help="碳水化合物（g）")
    sub_add_meal.add_argument("--fat", type=float, default=0, help="脂肪（g）")
    sub_add_meal.add_argument("--water", type=int, default=0, help="水（ml）")
    sub_add_meal.add_argument("--meal-date", help="日期，YYYY-MM-DD，默认今天")
    sub_add_meal.add_argument("--meal-time", help="时间，HH:MM:SS，默认当前时间")
    sub_add_meal.add_argument("--note", help="备注")
    sub_add_meal.set_defaults(func=cmd_add_meal)

    sub_update_meal = subparsers.add_parser("update-meal", help="更新一条饮食记录")
    sub_update_meal.add_argument("--meal-id", type=int, required=True, help="饮食记录 ID")
    sub_update_meal.add_argument("--meal-name", help="食物名称")
    sub_update_meal.add_argument("--calories", type=int, help="热量（kcal）")
    sub_update_meal.add_argument("--protein", type=float, help="蛋白质（g）")
    sub_update_meal.add_argument("--carbs", type=float, help="碳水化合物（g）")
    sub_update_meal.add_argument("--fat", type=float, help="脂肪（g）")
    sub_update_meal.add_argument("--water", type=int, help="水（ml）")
    sub_update_meal.set_defaults(func=cmd_update_meal)

    sub_delete_meal = subparsers.add_parser("delete-meal", help="删除一条饮食记录")
    sub_delete_meal.add_argument("--meal-id", type=int, required=True, help="饮食记录 ID")
    sub_delete_meal.set_defaults(func=cmd_delete_meal)

    sub_add_custom_food = subparsers.add_parser("add-custom-food", help="添加自定义食物到用户个人食物库")
    sub_add_custom_food.add_argument("--name", required=True, help="食物名称")
    sub_add_custom_food.add_argument("--category", required=True, help="食物分类")
    sub_add_custom_food.add_argument("--portion-calories", type=int, required=True, help="单份热量（kcal）")
    sub_add_custom_food.add_argument("--calories-per-100g", type=int, required=True, help="每100克热量（kcal）")
    sub_add_custom_food.add_argument("--portion-unit", help="单份单位（个/碗/勺）")
    sub_add_custom_food.add_argument("--portion-grams", type=float, help="单份克数")
    sub_add_custom_food.add_argument("--calorie-level", help="热量等级")
    sub_add_custom_food.add_argument("--protein", type=float, default=0, help="蛋白质（g）")
    sub_add_custom_food.add_argument("--carbs", type=float, default=0, help="碳水化合物（g）")
    sub_add_custom_food.add_argument("--fat", type=float, default=0, help="脂肪（g）")
    sub_add_custom_food.add_argument("--suitable-meals", default="breakfast,lunch,dinner", help="适合餐次，逗号分隔")
    sub_add_custom_food.set_defaults(func=cmd_add_custom_food)

    sub_update_custom_food = subparsers.add_parser("update-custom-food", help="更新自定义食物")
    sub_update_custom_food.add_argument("--food-id", type=int, required=True, help="自定义食物 ID")
    sub_update_custom_food.add_argument("--name", help="食物名称")
    sub_update_custom_food.add_argument("--category", help="食物分类")
    sub_update_custom_food.add_argument("--portion-calories", type=int, help="单份热量（kcal）")
    sub_update_custom_food.add_argument("--calories-per-100g", type=int, help="每100克热量（kcal）")
    sub_update_custom_food.add_argument("--portion-unit", help="单份单位（个/碗/勺）")
    sub_update_custom_food.add_argument("--portion-grams", type=float, help="单份克数")
    sub_update_custom_food.add_argument("--calorie-level", help="热量等级")
    sub_update_custom_food.add_argument("--protein", type=float, help="蛋白质（g）")
    sub_update_custom_food.add_argument("--carbs", type=float, help="碳水化合物（g）")
    sub_update_custom_food.add_argument("--fat", type=float, help="脂肪（g）")
    sub_update_custom_food.add_argument("--suitable-meals", help="适合餐次，逗号分隔")
    sub_update_custom_food.set_defaults(func=cmd_update_custom_food)

    sub_delete_custom_food = subparsers.add_parser("delete-custom-food", help="删除自定义食物")
    sub_delete_custom_food.add_argument("--food-id", type=int, required=True, help="自定义食物 ID")
    sub_delete_custom_food.set_defaults(func=cmd_delete_custom_food)

    sub_update_settings = subparsers.add_parser("update-settings", help="更新用户设置（目标值等）")
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

    try:
        args.auth_user_id = _resolve_user_id(args)
        args.func(args)
    except Exception as e:
        _output({"success": False, "error": str(e)}, exit_code=1)


if __name__ == "__main__":
    main()
