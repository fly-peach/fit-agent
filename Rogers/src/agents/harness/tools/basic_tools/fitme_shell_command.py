"""Fitme API Command Tool

直接通过 HTTP (curl 风格) 调用 localhost API，不需要 subprocess 或 cli.py 中间层。
"""
import json
import shlex
from dataclasses import dataclass, field
from typing import Dict, Optional, Union

import httpx

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

# ── API 地址（可通过环境变量覆盖） ─────────────────────────────────────────
import os
API_BASE_URL = os.getenv("FITME_API_URL", "http://localhost:8000")

# ── 命令 → (HTTP 方法, API 路径, 请求体构建器) 映射 ──────────────────────────

@dataclass
class ApiRoute:
    method: str                      # "GET" | "POST"
    path: str                        # API endpoint
    body_builder: Optional[str] = None  # 可选：构建请求体的参数名列表


# 完整的命令路由表
COMMAND_ROUTES: dict[str, ApiRoute] = {
    # ── 用户 ──
    "get-user-profile":    ApiRoute("GET",  "/api/user/profile"),
    "get-user-settings":   ApiRoute("GET",  "/api/user/settings"),

    # ── 健康 ──
    "get-health-metrics":  ApiRoute("GET",  "/api/health/metrics"),
    "get-health-summary":  ApiRoute("GET",  "/api/health/metrics"),
    "get-health-history":  ApiRoute("GET",  "/api/health/measurements"),
    "create-health-metric": ApiRoute("POST", "/api/health/metrics",
        "weight,height,body_fat,weight_goal,measure_date"),

    # ── 训练 ──
    "get-training-today":          ApiRoute("GET", "/api/training/schedule/weekly"),
    "get-training-weekly":         ApiRoute("GET", "/api/training/schedule/weekly"),
    "get-training-stats":          ApiRoute("GET", "/api/training/stats/weekly"),
    "get-training-recommendations": ApiRoute("GET", "/api/training/recommendations"),
    "get-training-card-templates": ApiRoute("GET", "/api/training/result-templates"),
    "get-training-card-template": ApiRoute("GET", "/api/training/result-templates/{template_key}"),
    "save-training-result":       ApiRoute("POST", "/api/training/results/archive",
        "title,session_id,stats_json,card_html,template_key,period_type,period_start,period_end,thumbnail"),
    "create-training-plan":        ApiRoute("POST", "/api/training/plans",
        "plan_name,plan_type,scheduled_date,estimated_duration,target_intensity,note"),

    # ── 饮食 ──
    "get-diet-today":          ApiRoute("GET", "/api/diet/meals/today"),
    "get-diet-stats":          ApiRoute("GET", "/api/diet/stats/today"),
    "get-diet-recommendations": ApiRoute("GET", "/api/diet/recommendations"),
    "search-foods":            ApiRoute("GET", "/api/diet/foods"),
    "create-diet-meal":        ApiRoute("POST", "/api/diet/meals",
        "meal_type,meal_name,calories,protein,carbs,fat,water,note,meal_date,time"),

    # ── 自定义食物 ──
    "create-custom-food":   ApiRoute("POST", "/api/diet/foods",
        "name,category,portion_calories,calories_per_100g,portion_unit,portion_grams,calorie_level,protein,carbs,fat"),
    "delete-custom-food":   ApiRoute("DELETE", "/api/diet/foods/{food_id}"),

    # ── 自定义动作 ──
    "create-custom-exercise":   ApiRoute("POST", "/api/exercises/custom",
        "name_cn,target_muscle,name_en,difficulty,force_type,mechanics,equipment,exercise_type,helper_muscles,instructions"),
    "update-custom-exercise":   ApiRoute("PUT", "/api/exercises/custom/{exercise_id}",
        "name_cn,name_en,difficulty,force_type,mechanics,equipment,exercise_type,target_muscle,helper_muscles,instructions"),
    "delete-custom-exercise":   ApiRoute("DELETE", "/api/exercises/custom/{exercise_id}"),

    # ── 综合 ──
    "get-full-overview": ApiRoute("GET", "__OVERVIEW__"),
}

# 向后兼容的别名
ALLOWED_COMMAND_PREFIXES = sorted(COMMAND_ROUTES.keys())


def _resolve_token(token: Optional[str]) -> Optional[str]:
    """规范化 token：去除 Bearer 前缀空白，返回纯净 token 或 None"""
    if not token:
        return None
    t = token.strip()
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t or None


def _make_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _parse_args(raw_args: list[str]) -> dict[str, str]:
    """将 ['--weight', '70.5', '--height', '175'] 解析为 {'weight': '70.5', 'height': '175'}"""
    parsed: dict[str, str] = {}
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            if i + 1 < len(raw_args) and not raw_args[i + 1].startswith("--"):
                parsed[key] = raw_args[i + 1]
                i += 2
            else:
                parsed[key] = "true"  # 布尔标志
                i += 1
        else:
            i += 1
    return parsed


def _cast_value(key: str, value: str) -> str | int | float:
    """根据 key 名智能转换参数类型"""
    int_keys = {"calories", "water", "estimated_duration"}
    float_keys = {"weight", "height", "body_fat", "weight_goal", "protein", "carbs", "fat"}

    if key in int_keys:
        try:
            return int(value)
        except ValueError:
            return value
    if key in float_keys:
        try:
            return float(value)
        except ValueError:
            return value
    return value


# ── 单个 API 请求 ──────────────────────────────────────────────────────────

async def _api_call(
    method: str,
    path: str,
    token: str,
    params: Optional[Dict] = None,
    body: Optional[Dict] = None,
) -> Dict:
    """通用 HTTP 调用，支持 GET/POST/PUT/DELETE"""
    url = f"{API_BASE_URL}{path}"
    headers = _make_headers(token)

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            resp = await client.post(url, headers=headers, json=body)
        elif method == "PUT":
            resp = await client.put(url, headers=headers, json=body)
        elif method == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            return {"success": False, "error": f"不支持的 HTTP 方法: {method}"}

    try:
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError:
        try:
            error_data = resp.json()
            return {"success": False, "error": error_data.get("detail", str(resp)), "status_code": resp.status_code}
        except Exception:
            return {"success": False, "error": str(resp), "status_code": resp.status_code}


def _substitute_path(path: str, args: dict) -> str:
    """替换路径中的 {food_id} / {exercise_id} 等占位符为实际值"""
    import re
    def _replacer(m: re.Match) -> str:
        key = m.group(1)
        val = args.pop(key, None)
        if val is None:
            raise ValueError(f"路径参数 {key} 缺失")
        return str(val)
    return re.sub(r"\{(\w+)\}", _replacer, path)


# ── 综合概览（并行请求） ─────────────────────────────────────────────────────

async def _handle_overview(token: str) -> dict:
    """并行获取所有模块数据"""
    routes = [
        ("profile",  "GET", "/api/user/profile"),
        ("health",   "GET", "/api/health/metrics"),
        ("training", "GET", "/api/training/schedule/weekly"),
        ("diet",     "GET", "/api/diet/meals/today"),
    ]
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = _make_headers(token)

        async def _fetch(key: str, method: str, path: str):
            url = f"{API_BASE_URL}{path}"
            resp = await client.get(url, headers=headers)
            return key, resp

        results = {}
        import asyncio
        tasks = [_fetch(k, m, p) for k, m, p in routes]
        responses = await asyncio.gather(*tasks)

        for key, resp in responses:
            try:
                resp.raise_for_status()
                data = resp.json()
                results[key] = data.get("data", data) if data.get("success") or data.get("code") == 200 else None
            except Exception:
                results[key] = None

    return {"success": True, "data": results}


# ── 主入口 ─────────────────────────────────────────────────────────────────

async def execute_fitme_command(
    command: str,
    auth_token: Optional[str] = None,
) -> ToolResponse:
    """执行 fitme 数据命令（直接 HTTP 调用 API）

    支持的调用方式：
    1. 简单命令: "get-user-profile"
    2. 带参数:   "create-health-metric --weight 70.5 --height 175"
    3. 完整命令: "python cli.py --token xxx get-user-profile"  （兼容旧写法）
    """
    # ── 验证 token ──
    token = _resolve_token(auth_token)
    if not token:
        return ToolResponse(content=[TextBlock(type="text", text="错误: 缺少认证 token，请先登录")])

    # ── 解析命令 ──
    cmd_clean = command.strip()
    try:
        parts = shlex.split(cmd_clean)
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"错误: 命令解析失败: {e}")])

    # 识别子命令（兼容完整命令格式）
    is_full = "python" in cmd_clean.lower() or "cli.py" in cmd_clean
    subcommand = None
    raw_args: list[str] = []

    if is_full:
        # 完整命令：跳过 python/cli.py/--token，找到子命令
        skip_next = False
        found_cmd = False
        for part in parts:
            if skip_next:
                skip_next = False
                continue
            if part in ("python", "python3", "py") or part.endswith(".py"):
                found_cmd = True
                continue
            if part == "--token":
                skip_next = True
                continue
            if found_cmd or part in COMMAND_ROUTES:
                if subcommand is None and part in COMMAND_ROUTES:
                    subcommand = part
                else:
                    raw_args.append(part)
                found_cmd = True
    else:
        subcommand = parts[0] if parts and parts[0] in COMMAND_ROUTES else None
        raw_args = parts[1:] if subcommand else []

    if not subcommand:
        guidance = ""
        if "agent-card-results" in command or "training-card" in command:
            guidance = (
                "\n提示: `agent-card-results` / `training-card` 是技能名称，不是可直接调用的工具函数。"
                "\n请改为先参考技能说明，再通过 execute_fitme_command 调用真实存在的子命令，"
                "例如 `get-training-stats`、`get-training-weekly`、`save-training-result`。"
            )
        elif "generate-training-report" in command:
            guidance = (
                "\n提示: `generate-training-report` 不是可用命令。"
                "\n请改用真实存在的子命令，如 `get-training-stats`、`get-training-weekly` 获取数据，"
                "并在生成 HTML 后使用 `save-training-result` 归档。"
            )
        return ToolResponse(content=[TextBlock(
            type="text",
            text=f"错误: 无法识别命令\n可用命令: {', '.join(sorted(COMMAND_ROUTES.keys()))}\n你输入的: {command}{guidance}"
        )])

    # ── 查找路由 ──
    route = COMMAND_ROUTES.get(subcommand)
    if not route:
        return ToolResponse(content=[TextBlock(type="text", text=f"错误: 未知子命令 '{subcommand}'")])

    # ── 综合概览特殊处理 ──
    if route.path == "__OVERVIEW__":
        try:
            result = await _handle_overview(token)
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"综合概览请求失败: {e}")])

    # ── 解析参数 ──
    parsed_args = _parse_args(raw_args) if raw_args else {}

    # 路径参数替换（如 {food_id} → 实际值）
    resolved_path = _substitute_path(route.path, parsed_args)

    try:
        if route.method == "GET":
            params = _build_query_params(subcommand, parsed_args)
            result = await _api_call("GET", resolved_path, token, params=params)
        elif route.method == "POST":
            body = _build_request_body(subcommand, parsed_args)
            result = await _api_call("POST", resolved_path, token, body=body)
        elif route.method == "PUT":
            body = _build_request_body(subcommand, parsed_args)
            result = await _api_call("PUT", resolved_path, token, body=body)
        elif route.method == "DELETE":
            result = await _api_call("DELETE", resolved_path, token)
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"不支持的 HTTP 方法: {route.method}")])

        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])
    except Exception as e:
        import traceback
        return ToolResponse(content=[TextBlock(
            type="text",
            text=f"API 请求异常: {str(e)}\n\n{traceback.format_exc()}"
        )])


# ── 参数映射 ───────────────────────────────────────────────────────────────

def _build_query_params(subcommand: str, args: dict) -> dict:
    """将 CLI 参数映射为 API 的 query params"""
    mapping = {
        "get-health-history": {"limit": "limit"},
        "get-diet-today":    {"date": "targetDate"},
        "search-foods":      {"keyword": "keyword", "category": "category"},
        "get-training-card-templates": {"template_group": "template_group"},
    }
    mapped = mapping.get(subcommand, {})
    params = {}
    for cli_key, api_key in mapped.items():
        if cli_key in args:
            params[api_key] = _cast_value(cli_key, args[cli_key])
    return params


def _build_request_body(subcommand: str, args: dict) -> dict:
    """将 CLI 参数映射为 API 的 JSON body"""
    from datetime import date, datetime

    body_mappings = {
        "create-health-metric": {
            "weight": "weight",
            "height": "height",
            "body_fat": "bodyFat",
            "weight_goal": "weightGoal",
            "measure_date": "measureDate",
        },
        "create-training-plan": {
            "plan_name": "planName",
            "plan_type": "planType",
            "scheduled_date": "scheduledDate",
            "estimated_duration": "estimatedDuration",
            "target_intensity": "targetIntensity",
            "note": "note",
        },
        "save-training-result": {
            "title": "title",
            "session_id": "session_id",
            "stats_json": "stats_json",
            "card_html": "card_html",
            "template_key": "template_key",
            "period_type": "period_type",
            "period_start": "period_start",
            "period_end": "period_end",
            "thumbnail": "thumbnail",
        },
        "create-diet-meal": {
            "meal_type": "mealType",
            "meal_name": "mealName",
            "calories": "calories",
            "protein": "protein",
            "carbs": "carbs",
            "fat": "fat",
            "water": "water",
            "note": "note",
            "meal_date": "mealDate",
            "time": "time",
        },
        "create-custom-food": {
            "name": "name",
            "category": "category",
            "portion_calories": "portionCalories",
            "calories_per_100g": "caloriesPer100g",
            "portion_unit": "portionUnit",
            "portion_grams": "portionGrams",
            "calorie_level": "calorieLevel",
            "protein": "protein",
            "carbs": "carbs",
            "fat": "fat",
        },
        "create-custom-exercise": {
            "name_cn": "nameCn",
            "name_en": "nameEn",
            "difficulty": "difficulty",
            "force_type": "forceType",
            "mechanics": "mechanics",
            "equipment": "equipment",
            "exercise_type": "exerciseType",
            "target_muscle": "targetMuscle",
            "helper_muscles": "helperMuscles",
            "instructions": "instructions",
        },
        "update-custom-exercise": {
            "name_cn": "nameCn",
            "name_en": "nameEn",
            "difficulty": "difficulty",
            "force_type": "forceType",
            "mechanics": "mechanics",
            "equipment": "equipment",
            "exercise_type": "exerciseType",
            "target_muscle": "targetMuscle",
            "helper_muscles": "helperMuscles",
            "instructions": "instructions",
        },
    }

    auto_defaults = {
        "create-health-metric": {"measureDate": lambda: date.today().isoformat()},
        "create-diet-meal":     {"time": lambda: datetime.now().strftime("%H:%M:%S")},
        "create-custom-food":   {"calorieLevel": lambda: "中"},
        "create-custom-exercise": {"instructions": lambda: "请参考标准动作要领"},
    }

    mapping = body_mappings.get(subcommand, {})
    body = {}
    for cli_key, api_key in mapping.items():
        if cli_key in args:
            body[api_key] = _cast_value(cli_key, args[cli_key])

    # 填充自动默认值（仅当用户未提供时）
    defaults = auto_defaults.get(subcommand, {})
    for api_key, fn in defaults.items():
        if api_key not in body:
            body[api_key] = fn()

    return body
