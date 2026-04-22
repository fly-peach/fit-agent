import { FormEvent, useEffect, useState } from "react";
import { listDailyNutrition, upsertDailyNutrition, type DailyNutrition, type MealData } from "../../shared/api/daily";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

type MealKey = "breakfast" | "lunch" | "dinner";
const MEALS: { key: MealKey; label: string; icon: string }[] = [
  { key: "breakfast", label: "早餐", icon: "🌅" },
  { key: "lunch", label: "午餐", icon: "☀️" },
  { key: "dinner", label: "晚餐", icon: "🌙" },
];

function MealInputs({
  mealKey,
  label,
  icon,
  calories,
  protein,
  carb,
  fat,
  onChange,
}: {
  mealKey: MealKey;
  label: string;
  icon: string;
  calories: string;
  protein: string;
  carb: string;
  fat: string;
  onChange: (mealKey: MealKey, field: string, value: string) => void;
}) {
  return (
    <fieldset className="meal-group">
      <legend>
        <span className="meal-icon">{icon}</span>
        {label}
      </legend>
      <div className="meal-grid">
        <label>
          热量 <small>(kcal)</small>
          <input
            type="number"
            min="0"
            step="1"
            value={calories}
            onChange={(e) => onChange(mealKey, "calories_kcal", e.target.value)}
          />
        </label>
        <label>
          蛋白 <small>(g)</small>
          <input
            type="number"
            min="0"
            step="1"
            value={protein}
            onChange={(e) => onChange(mealKey, "protein_g", e.target.value)}
          />
        </label>
        <label>
          碳水 <small>(g)</small>
          <input
            type="number"
            min="0"
            step="1"
            value={carb}
            onChange={(e) => onChange(mealKey, "carb_g", e.target.value)}
          />
        </label>
        <label>
          脂肪 <small>(g)</small>
          <input
            type="number"
            min="0"
            step="1"
            value={fat}
            onChange={(e) => onChange(mealKey, "fat_g", e.target.value)}
          />
        </label>
      </div>
    </fieldset>
  );
}

function num(v: unknown): string {
  return v != null ? String(v) : "";
}

function mealState(record?: DailyNutrition, mealKey?: MealKey) {
  if (!record) return { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" };
  const m = mealKey ? record[mealKey] : undefined;
  return {
    calories_kcal: num(m?.calories_kcal),
    protein_g: num(m?.protein_g),
    carb_g: num(m?.carb_g),
    fat_g: num(m?.fat_g),
  };
}

export function DailyNutritionPage() {
  const [recordDate, setRecordDate] = useState(todayStr());
  const [meal, setMeal] = useState<Record<MealKey, { calories_kcal: string; protein_g: string; carb_g: string; fat_g: string }>>({
    breakfast: { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" },
    lunch: { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" },
    dinner: { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" },
  });
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<DailyNutrition[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function reload() {
    setRows(await listDailyNutrition());
  }

  useEffect(() => {
    reload().catch((e) => setError(e.message));
  }, []);

  // Prefill form when switching to a date that has an existing record
  useEffect(() => {
    const existing = rows.find((r) => r.record_date === recordDate);
    if (existing) {
      setMeal({
        breakfast: mealState(existing, "breakfast"),
        lunch: mealState(existing, "lunch"),
        dinner: mealState(existing, "dinner"),
      });
      setNotes(existing.notes ?? "");
    } else {
      setMeal({
        breakfast: { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" },
        lunch: { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" },
        dinner: { calories_kcal: "", protein_g: "", carb_g: "", fat_g: "" },
      });
      setNotes("");
    }
  }, [recordDate, rows]);

  function handleMealChange(mealKey: MealKey, field: string, value: string) {
    setMeal((prev) => ({
      ...prev,
      [mealKey]: { ...prev[mealKey], [field]: value },
    }));
  }

  function dailyTotal(field: "calories_kcal" | "protein_g" | "carb_g" | "fat_g"): number {
    return MEALS.reduce((sum, { key }) => sum + (parseFloat(meal[key][field]) || 0), 0);
  }

  function toMealData(m: { calories_kcal: string; protein_g: string; carb_g: string; fat_g: string }): MealData | undefined {
    const kcal = parseFloat(m.calories_kcal) || 0;
    const pro = parseFloat(m.protein_g) || 0;
    const carb = parseFloat(m.carb_g) || 0;
    const fat = parseFloat(m.fat_g) || 0;
    if (kcal === 0 && pro === 0 && carb === 0 && fat === 0) return undefined;
    return { calories_kcal: kcal, protein_g: pro, carb_g: carb, fat_g: fat };
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await upsertDailyNutrition(recordDate, {
        breakfast: toMealData(meal.breakfast),
        lunch: toMealData(meal.lunch),
        dinner: toMealData(meal.dinner),
        notes: notes || null,
      });
      setMessage("保存成功");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    }
  }

  return (
    <section>
      <h1>每日三餐摄入</h1>
      <form className="card form-card nutrition-form" onSubmit={onSubmit}>
        <label>日期</label>
        <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)} />

        {MEALS.map(({ key, label, icon }) => (
          <MealInputs
            key={key}
            mealKey={key}
            label={label}
            icon={icon}
            calories={meal[key].calories_kcal}
            protein={meal[key].protein_g}
            carb={meal[key].carb_g}
            fat={meal[key].fat_g}
            onChange={handleMealChange}
          />
        ))}

        <div className="meal-daily-total">
          <h3>每日合计</h3>
          <div className="meal-grid daily-totals">
            <div className="total-value">热量: {dailyTotal("calories_kcal").toFixed(0)} kcal</div>
            <div className="total-value">蛋白: {dailyTotal("protein_g").toFixed(1)} g</div>
            <div className="total-value">碳水: {dailyTotal("carb_g").toFixed(1)} g</div>
            <div className="total-value">脂肪: {dailyTotal("fat_g").toFixed(1)} g</div>
          </div>
        </div>

        <label>备注</label>
        <input value={notes} onChange={(e) => setNotes(e.target.value)} />
        {message && <p className="success-text">{message}</p>}
        {error && <p className="error-text">{error}</p>}
        <button className="primary-btn" type="submit">
          保存摄入记录
        </button>
      </form>

      <div className="card list-card">
        <h2>最近摄入记录</h2>
        <table className="simple-table nutrition-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>早餐</th>
              <th>午餐</th>
              <th>晚餐</th>
              <th>合计</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.record_date}</td>
                <td>
                  <span className="nutrition-meal-cell">{r.breakfast?.calories_kcal ?? 0} kcal</span>
                  <br />
                  <small>
                    蛋{r.breakfast?.protein_g ?? 0} / 碳{r.breakfast?.carb_g ?? 0} / 脂{r.breakfast?.fat_g ?? 0}
                  </small>
                </td>
                <td>
                  <span className="nutrition-meal-cell">{r.lunch?.calories_kcal ?? 0} kcal</span>
                  <br />
                  <small>
                    蛋{r.lunch?.protein_g ?? 0} / 碳{r.lunch?.carb_g ?? 0} / 脂{r.lunch?.fat_g ?? 0}
                  </small>
                </td>
                <td>
                  <span className="nutrition-meal-cell">{r.dinner?.calories_kcal ?? 0} kcal</span>
                  <br />
                  <small>
                    蛋{r.dinner?.protein_g ?? 0} / 碳{r.dinner?.carb_g ?? 0} / 脂{r.dinner?.fat_g ?? 0}
                  </small>
                </td>
                <td className="nutrition-total-cell">
                  <strong>{r.calories_kcal} kcal</strong>
                  <br />
                  <small>
                    蛋{r.protein_g} / 碳{r.carb_g} / 脂{r.fat_g}
                  </small>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
