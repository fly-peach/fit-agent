import { useEffect, useMemo, useState } from "react";
import { getGrowthAnalytics } from "../../shared/api/growth";

function miniBarWidth(value: number, max: number) {
  if (max <= 0) return "0%";
  return `${Math.max(3, Math.round((value / max) * 100))}%`;
}

export function GrowthAnalyticsPage() {
  const [growth, setGrowth] = useState<Awaited<ReturnType<typeof getGrowthAnalytics>> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getGrowthAnalytics()
      .then(setGrowth)
      .catch((e: Error) => setError(e.message));
  }, []);

  const trends = growth?.trends ?? {};
  const maxWeight = useMemo(
    () => Math.max(1, ...(trends.weight ?? []).map((p) => p.value)),
    [trends.weight]
  );
  const maxCalories = useMemo(
    () => Math.max(1, ...(trends.calories_kcal ?? []).map((p) => p.value)),
    [trends.calories_kcal]
  );

  if (error) {
    return <p className="error-text">{error}</p>;
  }

  return (
    <section>
      <h1>成长分析</h1>
      <div className="card list-card">
        <h2>关键趋势（近30天）</h2>
        <div className="analytics-grid">
          <div>
            <h3>体重趋势</h3>
            {(trends.weight ?? []).map((p) => (
              <div key={p.record_date} className="bar-row">
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
              <div key={p.record_date} className="bar-row">
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
    </section>
  );
}
