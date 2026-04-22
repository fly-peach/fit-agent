import { FormEvent, useEffect, useState } from "react";
import { listDailyWorkout, upsertDailyWorkout } from "../../shared/api/daily";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export function DailyWorkoutPage() {
  const [recordDate, setRecordDate] = useState(todayStr());
  const [title, setTitle] = useState("今日训练");
  const [duration, setDuration] = useState("45");
  const [itemsText, setItemsText] = useState("深蹲,4,10,15\n硬拉,4,8,15");
  const [completed, setCompleted] = useState(false);
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<Awaited<ReturnType<typeof listDailyWorkout>>>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function reload() {
    setRows(await listDailyWorkout());
  }

  useEffect(() => {
    reload().catch((e) => setError(e.message));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const items = itemsText
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [name, sets, reps, mins] = line.split(",");
          return {
            name: (name || "").trim(),
            sets: Number(sets || 0),
            reps: Number(reps || 0),
            duration_minutes: Number(mins || 0),
          };
        });
      await upsertDailyWorkout(recordDate, {
        plan_title: title,
        items,
        duration_minutes: Number(duration || 0),
        is_completed: completed,
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
      <h1>每日运动计划</h1>
      <form className="card form-card" onSubmit={onSubmit}>
        <label>日期</label>
        <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)} />
        <label>计划标题</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
        <label>总时长 (分钟)</label>
        <input value={duration} onChange={(e) => setDuration(e.target.value)} />
        <label>动作清单（每行：动作名,组数,次数,分钟）</label>
        <textarea rows={5} value={itemsText} onChange={(e) => setItemsText(e.target.value)} />
        <label>备注</label>
        <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="可选" />
        <label className="checkbox-label">
          <input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} />
          已完成
        </label>
        {message && <p className="success-text">{message}</p>}
        {error && <p className="error-text">{error}</p>}
        <button className="primary-btn" type="submit">
          保存运动计划
        </button>
      </form>

      <div className="card list-card">
        <h2>最近计划</h2>
        <table className="simple-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>标题</th>
              <th>时长</th>
              <th>完成</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.record_date}</td>
                <td>{r.plan_title}</td>
                <td>{r.duration_minutes}</td>
                <td>{r.is_completed ? "是" : "否"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
