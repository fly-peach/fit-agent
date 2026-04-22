import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardMe, type DashboardMeData } from "../../shared/api/dashboard";
import { getGrowthAnalytics } from "../../shared/api/growth";
import { useAuthStore } from "../../store/auth";

function statusText(status: "normal" | "blue" | "yellow" | "red") {
  if (status === "red") return "高风险";
  if (status === "yellow") return "中风险";
  if (status === "blue") return "提示";
  return "正常";
}

function ringBackground(outer: number, inner: number) {
  return `conic-gradient(#4f8df8 ${outer}%, #dcecff ${outer}% 100%), conic-gradient(#6aa7ff ${inner}%, #ecf4ff ${inner}% 100%)`;
}

function miniBarWidth(value: number, max: number) {
  if (max <= 0) return "0%";
  return `${Math.max(3, Math.round((value / max) * 100))}%`;
}

export function DataOverviewPage() {
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardMeData | null>(null);
  const [growth, setGrowth] = useState<Awaited<ReturnType<typeof getGrowthAnalytics>> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMe().catch(() => undefined);
  }, [fetchMe]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [d, g] = await Promise.all([getDashboardMe(), getGrowthAnalytics()]);
        setData(d);
        setGrowth(g);
      } catch (e: any) {
        setError(e?.message || "加载失败");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const latestMetrics = data?.growth_analytics.metrics_latest ?? null;
  const latestWorkout = data?.growth_analytics.workout_latest ?? null;
  const latestNutrition = data?.growth_analytics.nutrition_latest ?? null;
  const latestAssessment = data?.latest_assessment;
  const healthProfile = data?.growth_analytics.health_profile ?? {};
  const goal = data?.growth_analytics.goal_progress ?? null;
  const alerts = data?.growth_analytics.alerts ?? [];
  const bcSummary = data?.body_composition_summary ?? null;
  const bcLatest = bcSummary?.latest ?? null;

  const trends = growth?.trends ?? {};
  const maxWeight = useMemo(
    () => Math.max(1, ...(trends.weight ?? []).map((p) => p.value)),
    [trends.weight]
  );
  const maxCalories = useMemo(
    () => Math.max(1, ...(trends.calories_kcal ?? []).map((p) => p.value)),
    [trends.calories_kcal]
  );

  return (
    <section>
      <h1>数据总览</h1>
      <p className="muted-text">用户：{user?.name ?? "-"} / 联系方式：{user?.email || user?.phone || "-"}</p>
      {loading && <p className="muted-text">加载中...</p>}
      {error && <p className="error-text">{error}</p>}

      {/* 核心数据概览 */}
      <div className="dashboard-core card">
        <h2>核心数据概览</h2>
        <div className="health-grid">
          {Object.entries(healthProfile).map(([key, card]) => (
            <div key={key} className={`health-card status-${card.status}`}>
              <div className="health-card-top">
                <strong>{card.label}</strong>
                <span className={`status-chip ${card.status}`}>{statusText(card.status)}</span>
              </div>
              <div className="health-value">
                {card.value ?? "-"} {card.unit}
              </div>
              <p className="metric-ref">
                参考：{card.reference_range}
                <br />
                <small>{card.reference_note}</small>
              </p>
              <p className="metric-delta">较上期：{card.delta === null ? "-" : `${card.delta > 0 ? "+" : ""}${card.delta}`}</p>
            </div>
          ))}
          <div className="health-card target-card">
            <div className="health-card-top">
              <strong>目标达成进度</strong>
            </div>
            <div className="health-value">{goal ? `${goal.inner_achieve_percent}%` : "-"}</div>
            <p className="metric-ref">基于近4周趋势动态估算</p>
          </div>
        </div>
      </div>

      {/* 训练目标进度看板 */}
      {goal && (
        <div className="dashboard-core card">
          <h2>训练目标进度看板</h2>
          <div className="goal-board">
            <div className="goal-ring-wrap">
              <div className="goal-ring-outer" style={{ background: ringBackground(goal.outer_ring_percent, goal.inner_achieve_percent) }}>
                <div className="goal-ring-inner">
                  <p>{goal.target_type}</p>
                  <strong>{goal.inner_achieve_percent}%</strong>
                  <small>达成率</small>
                </div>
              </div>
              <p className="muted-text">外环：本周变化 {goal.outer_week_change > 0 ? "+" : ""}{goal.outer_week_change}</p>
            </div>
            <div className="goal-trend">
              <h3>近4周趋势</h3>
              {goal.trend_4w.map((p) => (
                <div key={p.record_date} className="bar-row">
                  <span>{p.record_date}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.max(4, Math.min(100, p.value * 4))}%` }} />
                  </div>
                  <strong>{p.value}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 动态预警 */}
      <div className="dashboard-core card">
        <h2>动态预警标识</h2>
        {!alerts.length ? (
          <p className="muted-text">当前无异常预警</p>
        ) : (
          <div className="alerts-list">
            {alerts.map((a, idx) => (
              <div key={`${a.metric}-${idx}`} className={`alert-item ${a.level}`}>
                <div className="alert-head">
                  <strong>{a.metric}</strong>
                  <span>{statusText(a.level)}</span>
                </div>
                <p>{a.message}</p>
                <small>{a.action}</small>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 今日数据 */}
      <div className="dashboard-grid">
        <div className="card mini-card">
          <h3>今日身体数据</h3>
          <p>体重：{latestMetrics?.weight ?? bcLatest?.weight ?? "-"}</p>
          <p>体脂率：{latestMetrics?.body_fat_rate ?? bcLatest?.body_fat_rate ?? "-"}%</p>
          <p>BMI：{latestMetrics?.bmi ?? bcLatest?.bmi ?? "-"}</p>
          <p>内脏脂肪：{bcLatest?.visceral_fat_level ?? "-"}</p>
          <p>基础代谢：{bcLatest?.bmr ?? "-"} kcal</p>
          <p>肌肉量：{bcLatest?.muscle_mass ?? "-"} kg</p>
        </div>
        <div className="card mini-card">
          <h3>今日运动计划</h3>
          <p>时长：{latestWorkout?.duration_minutes ?? "-"} 分钟</p>
          <p>完成：{latestWorkout?.is_completed ? "是" : "否"}</p>
        </div>
        <div className="card mini-card">
          <h3>今日热量摄入</h3>
          <p>总热量：{latestNutrition?.calories_kcal ?? "-"} kcal</p>
          <p>蛋白/碳水/脂肪：{latestNutrition ? `${latestNutrition.protein_g}/${latestNutrition.carb_g}/${latestNutrition.fat_g}` : "-"}</p>
          {latestNutrition && (
            <div style={{ marginTop: "6px", fontSize: "12px", color: "#64748b" }}>
              <div>🌅 早餐 {latestNutrition.breakfast?.calories_kcal ?? 0} kcal</div>
              <div>☀️ 午餐 {latestNutrition.lunch?.calories_kcal ?? 0} kcal</div>
              <div>🌙 晚餐 {latestNutrition.dinner?.calories_kcal ?? 0} kcal</div>
            </div>
          )}
        </div>
        <div className="card mini-card">
          <h3>最近评估</h3>
          {!latestAssessment ? <p>-</p> : <p>{latestAssessment.status} / {latestAssessment.risk_level || "-"}</p>}
        </div>
      </div>

      {/* 趋势分析 */}
      <div className="card list-card">
        <h2>关键趋势（近30天）</h2>
        <div className="analytics-grid">
          <div>
            <h3>体重趋势</h3>
            {(trends.weight ?? []).map((p) => (
              <div key={`tw-${p.record_date}`} className="bar-row">
                <span>{p.record_date}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: miniBarWidth(p.value, maxWeight) }} />
                </div>
                <strong>{p.value.toFixed(1)}</strong>
              </div>
            ))}
          </div>
          <div>
            <h3>热量趋势</h3>
            {(trends.calories_kcal ?? []).map((p) => (
              <div key={`tc-${p.record_date}`} className="bar-row">
                <span>{p.record_date}</span>
                <div className="bar-track">
                  <div className="bar-fill secondary" style={{ width: miniBarWidth(p.value, maxCalories) }} />
                </div>
                <strong>{p.value.toFixed(0)}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 体成分 */}
      {bcLatest && (
        <div className="card">
          <h2>
            最近体成分评估
            <span style={{ float: "right", fontSize: 14 }}>
              <Link to="/body-composition" style={{ color: "#4f8df8" }}>查看全部</Link>
              {" | "}
              <Link to={`/body-composition/${bcLatest.id}`} style={{ color: "#4f8df8" }}>详情</Link>
            </span>
          </h2>
          <div className="health-grid">
            <div className="health-card status-normal">
              <div className="health-card-top"><strong>体重</strong></div>
              <div className="health-value">{bcLatest.weight?.toFixed(1) ?? "-"} kg</div>
            </div>
            <div className="health-card status-normal">
              <div className="health-card-top"><strong>体脂率</strong></div>
              <div className="health-value">{bcLatest.body_fat_rate?.toFixed(1) ?? "-"}%</div>
            </div>
            <div className="health-card status-normal">
              <div className="health-card-top"><strong>肌肉量</strong></div>
              <div className="health-value">{bcLatest.muscle_mass ?? "-"} kg</div>
            </div>
            <div className="health-card status-normal">
              <div className="health-card-top"><strong>骨骼肌率</strong></div>
              <div className="health-value">{bcLatest.skeletal_muscle_rate?.toFixed(1) ?? "-"}%</div>
            </div>
            <div className="health-card status-normal">
              <div className="health-card-top"><strong>水分率</strong></div>
              <div className="health-value">{bcLatest.water_rate?.toFixed(1) ?? "-"}%</div>
            </div>
            <div className="health-card status-normal">
              <div className="health-card-top"><strong>BMR</strong></div>
              <div className="health-value">{bcLatest.bmr ?? "-"} kcal</div>
            </div>
          </div>
        </div>
      )}

      {bcSummary?.compare && (
        <div className="card">
          <h2>
            体成分对比
            <span style={{ float: "right", fontSize: 14 }}>
              <Link to="/body-composition/compare" style={{ color: "#4f8df8" }}>详细对比</Link>
            </span>
          </h2>
          <div style={{ display: "flex", gap: 24, fontSize: 14, color: "#ccc" }}>
            <span>
              体重：{bcSummary.compare.a?.weight ?? "-"} → {bcSummary.compare.b?.weight ?? "-"} kg
              <span style={{ color: (bcSummary.compare.b?.weight ?? 0) - (bcSummary.compare.a?.weight ?? 0) < 0 ? "#52c41a" : "#ff4d4f" }}>
                ({((bcSummary.compare.b?.weight ?? 0) - (bcSummary.compare.a?.weight ?? 0)).toFixed(1)})
              </span>
            </span>
            <span>
              体脂率：{bcSummary.compare.a?.body_fat_rate ?? "-"} → {bcSummary.compare.b?.body_fat_rate ?? "-"}%
              <span style={{ color: (bcSummary.compare.b?.body_fat_rate ?? 0) - (bcSummary.compare.a?.body_fat_rate ?? 0) < 0 ? "#52c41a" : "#ff4d4f" }}>
                ({((bcSummary.compare.b?.body_fat_rate ?? 0) - (bcSummary.compare.a?.body_fat_rate ?? 0)).toFixed(1)}%)
              </span>
            </span>
            <span>
              肌肉量：{bcSummary.compare.a?.muscle_mass ?? "-"} → {bcSummary.compare.b?.muscle_mass ?? "-"} kg
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
