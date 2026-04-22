import { FormEvent, useEffect, useState } from "react";
import { listDailyMetrics, upsertDailyMetrics } from "../../shared/api/daily";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export function DailyMetricsPage() {
  const [recordDate, setRecordDate] = useState(todayStr());
  const [weight, setWeight] = useState<string>("");
  const [bodyFatRate, setBodyFatRate] = useState<string>("");
  const [bmi, setBmi] = useState<string>("");
  const [rows, setRows] = useState<Awaited<ReturnType<typeof listDailyMetrics>>>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function reload() {
    const data = await listDailyMetrics();
    setRows(data);
  }

  useEffect(() => {
    reload().catch((e) => setError(e.message));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await upsertDailyMetrics(recordDate, {
        weight: weight ? Number(weight) : null,
        body_fat_rate: bodyFatRate ? Number(bodyFatRate) : null,
        bmi: bmi ? Number(bmi) : null,
      });
      setMessage("保存成功");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    }
  }

  return (
    <section>
      <h1>每日数据记录</h1>
      <form className="card form-card" onSubmit={onSubmit}>
        <label>日期</label>
        <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)} />
        <label>体重 (kg)</label>
        <input value={weight} onChange={(e) => setWeight(e.target.value)} placeholder="例如 70.5" />
        <label>体脂率 (%)</label>
        <input value={bodyFatRate} onChange={(e) => setBodyFatRate(e.target.value)} placeholder="例如 18.2" />
        <label>BMI</label>
        <input value={bmi} onChange={(e) => setBmi(e.target.value)} placeholder="例如 24.3" />
        {message && <p className="success-text">{message}</p>}
        {error && <p className="error-text">{error}</p>}
        <button className="primary-btn" type="submit">
          保存当日数据
        </button>
      </form>

      <div className="card list-card">
        <h2>最近记录</h2>
        <table className="simple-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>体重</th>
              <th>体脂率</th>
              <th>BMI</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.record_date}</td>
                <td>{r.weight ?? "-"}</td>
                <td>{r.body_fat_rate ?? "-"}</td>
                <td>{r.bmi ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
