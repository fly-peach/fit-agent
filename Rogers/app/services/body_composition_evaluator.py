"""体成分评估服务：体型判定、控制量计算、营养状态、健康评分、指标状态判定。"""

from app.models.body_composition import BodyCompositionRecord


def evaluate_body_type(bmi: float | None, body_fat_rate: float | None) -> str | None:
    """体型判定：6 种体型分类"""
    if bmi is None or body_fat_rate is None:
        return None
    if bmi >= 28 and body_fat_rate < 20:
        return "肌肉型"
    if bmi >= 28 and body_fat_rate >= 20:
        return "肥胖"
    if bmi >= 24 and body_fat_rate >= 20:
        return "运动型偏胖"
    if bmi >= 24 and body_fat_rate < 20:
        return "隐藏型肥胖"
    if bmi < 18.5:
        return "偏瘦"
    return "标准"


def calculate_controls(
    weight: float | None,
    body_fat_rate: float | None,
    height_cm: float | None,
    target_fat_rate: float = 18.0,
    target_muscle_rate: float = 40.0,
) -> dict:
    """控制量计算：理想体重、体重/脂肪/肌肉控制量"""
    defaults = {
        "ideal_weight": None,
        "weight_control": None,
        "fat_control": None,
        "muscle_control": None,
    }
    if not weight or not height_cm:
        return defaults
    height_m = height_cm / 100
    ideal_weight = round(22.0 * height_m**2, 1)
    weight_control = round(ideal_weight - weight, 2)
    fat_control = None
    muscle_control = None
    if body_fat_rate is not None:
        fat_control = round((body_fat_rate / 100 - target_fat_rate / 100) * weight, 2)
        muscle_control = round((target_muscle_rate / 100 - (100 - body_fat_rate) / 100) * weight, 2)
    return {
        "ideal_weight": ideal_weight,
        "weight_control": weight_control,
        "fat_control": fat_control,
        "muscle_control": muscle_control,
    }


def evaluate_nutrition(
    protein_mass: float | None,
    weight: float | None,
    calories_intake: float | None = None,
    bmr: float | None = None,
) -> str:
    """营养状态判定"""
    if protein_mass and weight and protein_mass < 0.8 * weight / 1000:
        return "营养不足"
    if calories_intake and bmr and calories_intake > bmr * 1.5:
        return "营养过剩"
    return "营养均衡"


def calc_fat_burn_hr(body_age: float | None, actual_age: int) -> tuple[float | None, float | None]:
    """燃脂心率区间"""
    age = body_age or actual_age
    if age is None:
        return None, None
    max_hr = 220 - age
    return round(max_hr * 0.6), round(max_hr * 0.75)


def calc_health_score(record: BodyCompositionRecord) -> int:
    """健康评分 0-100，基于各项指标达标情况加权计算"""
    score = 100
    if record.bmi:
        score -= abs(record.bmi - 22) * 2
    if record.body_fat_rate:
        score -= max(0, (record.body_fat_rate - 20) * 1.5)
    if record.visceral_fat_level and record.visceral_fat_level > 9:
        score -= (record.visceral_fat_level - 9) * 3
    return max(0, min(100, int(score)))


def evaluate_indicator_level(metric: str, value: float | None, ctx: dict) -> str | None:
    """单指标状态判定"""
    if value is None:
        return None
    rules: dict[str, callable] = {
        "weight": lambda v, c: ("过重" if c.get("bmi", 0) >= 24 else "偏轻" if c.get("bmi", 100) < 18.5 else "标准"),
        "bmi": lambda v, _: "偏胖" if v >= 24 else "偏瘦" if v < 18.5 else "标准",
        "body_fat_rate": lambda v, _: ("轻度肥胖" if v >= 25 else "标准" if v < 20 else "偏高"),
        "visceral_fat_level": lambda v, _: ("警戒型" if v >= 10 else "偏高" if v >= 7 else "正常"),
        "fat_mass": lambda v, _: ("偏高" if v > 20 else "标准"),
        "muscle_mass": lambda v, _: "优" if v > 60 else "良" if v > 40 else "不足",
        "skeletal_muscle_mass": lambda v, _: "优" if v > 40 else "标准" if v > 25 else "不足",
        "skeletal_muscle_rate": lambda v, _: "优" if v > 50 else "标准" if v > 35 else "偏低",
        "muscle_rate": lambda v, _: "优" if v >= 70 else "良" if v >= 55 else "不足",
        "bone_mass": lambda v, _: "正常" if v >= 3.5 else "偏低",
        "water_rate": lambda v, _: "偏高" if v > 65 else "标准" if v >= 50 else "不足",
        "water_mass": lambda v, _: "标准",
        "protein_mass": lambda v, _: "标准",
        "protein_rate": lambda v, _: "偏高" if v > 20 else "标准" if v >= 12 else "不足",
        "bmr": lambda v, _: "正常",
        "body_age": lambda v, _: "正常",
        "subcutaneous_fat": lambda v, _: "偏高" if v > 25 else "标准" if v > 10 else "偏低",
        "ideal_weight": lambda v, _: "标准",
        "weight_control": lambda v, _: "减重" if v < 0 else "增重" if v > 0 else "标准",
        "fat_control": lambda v, _: "减脂" if v > 0 else "增脂" if v < 0 else "标准",
        "muscle_control": lambda v, _: "增肌" if v > 0 else "减肌" if v < 0 else "标准",
        "fat_free_mass": lambda v, _: "正常",
        "fat_burn_hr_low": lambda v, _: "正常",
        "fat_burn_hr_high": lambda v, _: "正常",
    }
    fn = rules.get(metric)
    if fn:
        return fn(value, ctx)
    return "标准"


def evaluate_all(
    record: BodyCompositionRecord,
    *,
    height_cm: float | None = None,
    actual_age: int | None = None,
) -> dict:
    """综合评估：返回所有评估结果"""
    ctx = {
        "bmi": record.bmi,
        "body_fat_rate": record.body_fat_rate,
    }

    body_type = evaluate_body_type(record.bmi, record.body_fat_rate)
    nutrition = evaluate_nutrition(record.protein_mass, record.weight, None, record.bmr)
    health_score = calc_health_score(record)
    controls = calculate_controls(record.weight, record.body_fat_rate, height_cm)
    fat_burn_low, fat_burn_high = calc_fat_burn_hr(record.body_age, actual_age or 25)
    fat_free_mass = round(record.weight - record.fat_mass, 2) if record.weight and record.fat_mass else None
    protein_rate = round(record.protein_mass / fat_free_mass * 100, 2) if record.protein_mass and fat_free_mass else None

    indicator_levels: dict[str, str] = {}
    all_metrics = [
        "weight", "bmi", "body_fat_rate", "visceral_fat_level", "fat_mass",
        "muscle_mass", "skeletal_muscle_mass", "skeletal_muscle_rate",
        "muscle_rate", "bone_mass", "water_rate", "water_mass",
        "protein_mass", "protein_rate", "bmr", "subcutaneous_fat",
    ]
    for metric in all_metrics:
        value = getattr(record, metric, None)
        level = evaluate_indicator_level(metric, value, ctx)
        if level:
            indicator_levels[metric] = level

    return {
        "body_type": body_type,
        "nutrition_status": nutrition,
        "body_age": record.body_age,
        "health_score": health_score,
        "subcutaneous_fat": record.subcutaneous_fat,
        "ideal_weight": controls["ideal_weight"],
        "weight_control": controls["weight_control"],
        "fat_control": controls["fat_control"],
        "muscle_control": controls["muscle_control"],
        "fat_free_mass": fat_free_mass,
        "protein_rate": protein_rate,
        "fat_burn_hr_low": fat_burn_low,
        "fat_burn_hr_high": fat_burn_high,
        "indicator_levels": indicator_levels,
    }
