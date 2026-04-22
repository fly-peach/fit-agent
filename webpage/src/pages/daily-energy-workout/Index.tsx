import { useEffect, useMemo, useState } from "react";
import { listDailyNutrition, listDailyWorkout, upsertDailyNutrition, upsertDailyWorkout, type DailyNutrition, type MealData } from "../../shared/api/daily";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function dateOffset(base: string, offsetDays: number) {
  const d = new Date(`${base}T00:00:00`);
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

type SaveState = "idle" | "saving" | "success" | "error";
type WorkoutRow = {
  id: string;
  name: string;
  sets: number;
  reps: number;
  duration_minutes: number;
  completed: boolean;
};

type MealFields = { calories: string; protein: string; carb: string; fat: string };
type MealKey = "breakfast" | "lunch" | "dinner";

const MEAL_META: { key: MealKey; label: string; icon: string }[] = [
  { key: "breakfast", label: "早餐", icon: "🌅" },
  { key: "lunch", label: "午餐", icon: "☀️" },
  { key: "dinner", label: "晚餐", icon: "🌙" },
];

function defaultMeals(): Record<MealKey, MealFields> {
  return {
    breakfast: { calories: "", protein: "", carb: "", fat: "" },
    lunch: { calories: "", protein: "", carb: "", fat: "" },
    dinner: { calories: "", protein: "", carb: "", fat: "" },
  };
}

function mealFromApi(m?: MealData): MealFields {
  if (!m) return { calories: "", protein: "", carb: "", fat: "" };
  return {
    calories: m.calories_kcal ? String(Math.round(m.calories_kcal)) : "",
    protein: m.protein_g ? String(Math.round(m.protein_g)) : "",
    carb: m.carb_g ? String(Math.round(m.carb_g)) : "",
    fat: m.fat_g ? String(Math.round(m.fat_g)) : "",
  };
}

function mealToData(m: MealFields): MealData | undefined {
  const kcal = parseFloat(m.calories) || 0;
  const pro = parseFloat(m.protein) || 0;
  const carb = parseFloat(m.carb) || 0;
  const fat = parseFloat(m.fat) || 0;
  if (kcal === 0 && pro === 0 && carb === 0 && fat === 0) return undefined;
  return { calories_kcal: kcal, protein_g: pro, carb_g: carb, fat_g: fat };
}

export function DailyEnergyWorkoutPage() {
  const [recordDate, setRecordDate] = useState(todayStr());

  const [planTitle, setPlanTitle] = useState("今日训练");
  const [workoutRows, setWorkoutRows] = useState<WorkoutRow[]>([
    { id: "r1", name: "深蹲", sets: 4, reps: 10, duration_minutes: 15, completed: false },
    { id: "r2", name: "硬拉", sets: 4, reps: 8, duration_minutes: 15, completed: false },
  ]);
  const [workoutNotes, setWorkoutNotes] = useState("");

  const [meals, setMeals] = useState<Record<MealKey, MealFields>>(defaultMeals());
  const [nutritionNotes, setNutritionNotes] = useState("");

  const [weekWorkout, setWeekWorkout] = useState<Awaited<ReturnType<typeof listDailyWorkout>>>([]);
  const [weekNutrition, setWeekNutrition] = useState<Awaited<ReturnType<typeof listDailyNutrition>>>([]);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [error, setError] = useState("");

  const totalDuration = useMemo(
    () => workoutRows.reduce((sum, row) => sum + Math.max(0, Number(row.duration_minutes || 0)), 0),
    [workoutRows]
  );
  const completedCount = useMemo(() => workoutRows.filter((r) => r.completed).length, [workoutRows]);
  const isCompleted = workoutRows.length > 0 && completedCount === workoutRows.length;

  const totalCalories = useMemo(
    () => Object.values(meals).reduce((sum, m) => sum + (parseFloat(m.calories) || 0), 0),
    [meals]
  );
  const totalProtein = useMemo(
    () => Object.values(meals).reduce((sum, m) => sum + (parseFloat(m.protein) || 0), 0),
    [meals]
  );
  const totalCarb = useMemo(
    () => Object.values(meals).reduce((sum, m) => sum + (parseFloat(m.carb) || 0), 0),
    [meals]
  );
  const totalFat = useMemo(
    () => Object.values(meals).reduce((sum, m) => sum + (parseFloat(m.fat) || 0), 0),
    [meals]
  );

  const dayStatus = useMemo(() => {
    const hasInput = totalDuration > 0 || totalCalories > 0 || workoutRows.some((r) => r.name.trim().length > 0);
    if (isCompleted && totalCalories > 0) return "已完成";
    if (hasInput) return "进行中";
    return "未完成";
  }, [isCompleted, totalDuration, totalCalories, workoutRows]);

  const macroEnergy = useMemo(() => {
    const p = totalProtein * 4;
    const c = totalCarb * 4;
    const f = totalFat * 9;
    return { p, c, f, total: p + c + f };
  }, [totalProtein, totalCarb, totalFat]);

  const energyGap = useMemo(() => {
    const intake = totalCalories;
    const targetConsume = 1600 + totalDuration * 8;
    const gap = intake - targetConsume;
    let label = "合理";
    let hint = "摄入与计划匹配度良好";
    if (gap > 300) {
      label = "偏高";
      hint = "摄入偏高，建议控制晚餐或加餐";
    } else if (gap < -300) {
      label = "偏低";
      hint = "摄入偏低，注意恢复与训练质量";
    }
    return { intake, targetConsume, gap, label, hint };
  }, [totalCalories, totalDuration]);

  async function reloadForDate(date: string) {
    setError("");
    const workoutRows = await listDailyWorkout(date, date);
    const nutritionRows = await listDailyNutrition(date, date);
    const workout = workoutRows[0];
    const nutrition = nutritionRows[0];

    if (workout) {
      setPlanTitle(workout.plan_title);
      setWorkoutNotes(workout.notes || "");
      setWorkoutRows(
        workout.items.length
          ? workout.items.map((i, idx) => ({
              id: `${date}-${idx}`,
              name: i.name,
              sets: i.sets,
              reps: i.reps,
              duration_minutes: i.duration_minutes,
              completed: workout.is_completed,
            }))
          : [{ id: `${date}-empty`, name: "", sets: 0, reps: 0, duration_minutes: 0, completed: false }]
      );
    } else {
      setPlanTitle("今日训练");
      setWorkoutNotes("");
      setWorkoutRows([
        { id: `${date}-r1`, name: "深蹲", sets: 4, reps: 10, duration_minutes: 15, completed: false },
        { id: `${date}-r2`, name: "硬拉", sets: 4, reps: 8, duration_minutes: 15, completed: false },
      ]);
    }

    if (nutrition) {
      setMeals({
        breakfast: mealFromApi(nutrition.breakfast),
        lunch: mealFromApi(nutrition.lunch),
        dinner: mealFromApi(nutrition.dinner),
      });
      setNutritionNotes(nutrition.notes || "");
    } else {
      setMeals(defaultMeals());
      setNutritionNotes("");
    }
  }

  async function reloadWeek(date: string) {
    const from = dateOffset(date, -6);
    const [ws, ns] = await Promise.all([listDailyWorkout(from, date), listDailyNutrition(from, date)]);
    setWeekWorkout(ws);
    setWeekNutrition(ns);
  }

  useEffect(() => {
    Promise.all([reloadForDate(recordDate), reloadWeek(recordDate)]).catch((e: Error) => setError(e.message));
  }, [recordDate]);

  function updateRow(id: string, patch: Partial<WorkoutRow>) {
    setWorkoutRows((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  }

  function addRow() {
    setWorkoutRows((rows) => [
      ...rows,
      {
        id: `r-${Date.now()}-${rows.length}`,
        name: "",
        sets: 0,
        reps: 0,
        duration_minutes: 0,
        completed: false,
      },
    ]);
  }

  function removeRow(id: string) {
    setWorkoutRows((rows) => (rows.length <= 1 ? rows : rows.filter((r) => r.id !== id)));
  }

  function updateMeal(mealKey: MealKey, field: keyof MealFields, value: string) {
    setMeals((prev) => ({
      ...prev,
      [mealKey]: { ...prev[mealKey], [field]: value },
    }));
  }

  async function onSaveAll(e?: { preventDefault?: () => void }) {
    e?.preventDefault?.();
    setError("");
    setSaveState("saving");
    const items = workoutRows
      .map((r) => ({
        name: r.name.trim(),
        sets: Math.max(0, Number(r.sets || 0)),
        reps: Math.max(0, Number(r.reps || 0)),
        duration_minutes: Math.max(0, Number(r.duration_minutes || 0)),
      }))
      .filter((r) => r.name.length > 0);

    if (items.length === 0) {
      setError("请至少填写一条有效动作");
      setSaveState("error");
      return;
    }

    const [workoutResult, nutritionResult] = await Promise.allSettled([
      upsertDailyWorkout(recordDate, {
        plan_title: planTitle,
        items,
        duration_minutes: totalDuration,
        is_completed: isCompleted,
        notes: workoutNotes || null,
      }),
      upsertDailyNutrition(recordDate, {
        breakfast: mealToData(meals.breakfast),
        lunch: mealToData(meals.lunch),
        dinner: mealToData(meals.dinner),
        notes: nutritionNotes || null,
      }),
    ]);

    if (workoutResult.status === "rejected" || nutritionResult.status === "rejected") {
      const parts = [
        workoutResult.status === "rejected" ? `训练保存失败：${String(workoutResult.reason?.message || "未知错误")}` : "",
        nutritionResult.status === "rejected" ? `营养保存失败：${String(nutritionResult.reason?.message || "未知错误")}` : "",
      ].filter(Boolean);
      setError(parts.join("；"));
      setSaveState("error");
      return;
    }

    setSaveState("success");
    await reloadWeek(recordDate);
  }

  return (
    <section className="dew-page">
      <h1>每日饮食与训练一体化</h1>

      <div className="card dew-toolbar">
        <div className="dew-toolbar-left">
          <label>日期</label>
          <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)} />
        </div>
        <div className="dew-toolbar-center">
          <span className={`dew-status ${dayStatus === "已完成" ? "done" : dayStatus === "进行中" ? "doing" : "todo"}`}>
            今日状态：{dayStatus}
          </span>
        </div>
        <div className="dew-toolbar-right">
          <button className="primary-btn" onClick={onSaveAll} disabled={saveState === "saving"}>
            {saveState === "saving" ? "保存中..." : "保存全部"}
          </button>
        </div>
      </div>

      <div className="dew-editor-grid">
        <div className="card dew-editor">
          <div className="dew-section">
            <h2>每日运动计划</h2>
            <label>计划标题</label>
            <input value={planTitle} onChange={(e) => setPlanTitle(e.target.value)} />
            <label>动作清单 / 总时长 / 完成情况（表格）</label>
            <div className="dew-workout-table-wrap">
              <table className="simple-table dew-workout-table">
                <thead>
                  <tr>
                    <th>动作名</th>
                    <th>组数</th>
                    <th>次数</th>
                    <th>时长(分钟)</th>
                    <th>完成</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {workoutRows.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <input className="dew-cell-input" value={row.name} onChange={(e) => updateRow(row.id, { name: e.target.value })} placeholder="动作名" />
                      </td>
                      <td>
                        <input className="dew-cell-input" type="number" min={0} value={row.sets} onChange={(e) => updateRow(row.id, { sets: Math.max(0, Number(e.target.value || 0)) })} />
                      </td>
                      <td>
                        <input className="dew-cell-input" type="number" min={0} value={row.reps} onChange={(e) => updateRow(row.id, { reps: Math.max(0, Number(e.target.value || 0)) })} />
                      </td>
                      <td>
                        <input className="dew-cell-input" type="number" min={0} value={row.duration_minutes} onChange={(e) => updateRow(row.id, { duration_minutes: Math.max(0, Number(e.target.value || 0)) })} />
                      </td>
                      <td>
                        <input type="checkbox" checked={row.completed} onChange={(e) => updateRow(row.id, { completed: e.target.checked })} />
                      </td>
                      <td>
                        <button className="dew-row-btn danger" type="button" onClick={() => removeRow(row.id)}>
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={3}>汇总</td>
                    <td>{totalDuration} 分钟</td>
                    <td>{completedCount}/{workoutRows.length}</td>
                    <td>
                      <button className="dew-row-btn" type="button" onClick={addRow}>
                        新增动作
                      </button>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <label>备注</label>
            <input value={workoutNotes} onChange={(e) => setWorkoutNotes(e.target.value)} placeholder="可选" />
          </div>
        </div>

        <div className="card dew-editor dew-nutrition-editor">
          <div className="dew-section">
            <h2>每日三餐摄入</h2>
            {MEAL_META.map(({ key, label, icon }) => (
              <fieldset className="dew-meal-group" key={key}>
                <legend>
                  <span>{icon}</span> {label}
                </legend>
                <div className="dew-meal-grid">
                  <div>
                    <label>热量 (kcal)</label>
                    <input type="number" min={0} value={meals[key].calories} onChange={(e) => updateMeal(key, "calories", e.target.value)} />
                  </div>
                  <div>
                    <label>蛋白 (g)</label>
                    <input type="number" min={0} value={meals[key].protein} onChange={(e) => updateMeal(key, "protein", e.target.value)} />
                  </div>
                  <div>
                    <label>碳水 (g)</label>
                    <input type="number" min={0} value={meals[key].carb} onChange={(e) => updateMeal(key, "carb", e.target.value)} />
                  </div>
                  <div>
                    <label>脂肪 (g)</label>
                    <input type="number" min={0} value={meals[key].fat} onChange={(e) => updateMeal(key, "fat", e.target.value)} />
                  </div>
                </div>
              </fieldset>
            ))}

            <div className="dew-meal-totals">
              <span>每日合计：热量 {Math.round(totalCalories)} kcal</span>
              <span>蛋白 {Math.round(totalProtein)}g</span>
              <span>碳水 {Math.round(totalCarb)}g</span>
              <span>脂肪 {Math.round(totalFat)}g</span>
            </div>
            <p className="muted-text">供能估算：蛋白 {macroEnergy.p} + 碳水 {macroEnergy.c} + 脂肪 {macroEnergy.f} = {macroEnergy.total} kcal</p>
            <label>备注</label>
            <input value={nutritionNotes} onChange={(e) => setNutritionNotes(e.target.value)} placeholder="可选" />
          </div>
        </div>
      </div>

      {saveState === "success" && <p className="success-text">保存成功</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="card dew-summary-full">
        <h2>今日执行摘要</h2>
        <p>训练总时长：{totalDuration} 分钟</p>
        <p>训练完成状态：{isCompleted ? "已完成" : "未完成"}</p>
        <p>热量总摄入：{Math.round(totalCalories)} kcal</p>
        <p>三大营养素：P {Math.round(totalProtein)} / C {Math.round(totalCarb)} / F {Math.round(totalFat)}</p>

        <div className="dew-gap-card">
          <h3>摄入 vs 计划消耗（估算）</h3>
          <p>摄入：{Math.round(energyGap.intake)} kcal</p>
          <p>消耗估算：{energyGap.targetConsume} kcal</p>
          <p>差值：{energyGap.gap > 0 ? "+" : ""}{Math.round(energyGap.gap)} kcal</p>
          <p className={`dew-gap-${energyGap.label === "偏高" ? "high" : energyGap.label === "偏低" ? "low" : "ok"}`}>{energyGap.label}：{energyGap.hint}</p>
        </div>

        <div className="dew-week">
          <h3>最近7天微趋势</h3>
          {(weekNutrition.length === 0 && weekWorkout.length === 0) ? (
            <p className="muted-text">暂无数据</p>
          ) : (
            <>
              <p className="muted-text">热量折线（简版）</p>
              {weekNutrition.map((n) => (
                <div key={`n-${n.record_date}`} className="bar-row">
                  <span>{n.record_date.slice(5)}</span>
                  <div className="bar-track">
                    <div className="bar-fill secondary" style={{ width: `${Math.max(4, Math.min(100, (n.calories_kcal / 3000) * 100))}%` }} />
                  </div>
                  <strong>{Math.round(n.calories_kcal)}</strong>
                </div>
              ))}
              <p className="muted-text">训练时长柱状（简版）</p>
              {weekWorkout.map((w) => (
                <div key={`w-${w.record_date}`} className="bar-row">
                  <span>{w.record_date.slice(5)}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.max(4, Math.min(100, (w.duration_minutes / 120) * 100))}%` }} />
                  </div>
                  <strong>{w.duration_minutes}</strong>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
