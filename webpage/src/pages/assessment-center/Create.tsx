import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAssessment } from "../../shared/api/assessment";

export function AssessmentCreate() {
  const navigate = useNavigate();
  const [goal, setGoal] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    
    try {
      const assessment = await createAssessment({
        goal,
        questionnaire_summary: { notes: "初始风险筛查" }
      });
      navigate(`/assessment-center/${assessment.id}`);
    } catch (err: any) {
      setError(err.message || "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="shell">
      <div className="card" style={{ maxWidth: 600, margin: "0 auto" }}>
        <h1>新建评估</h1>
        <form onSubmit={onSubmit}>
          <label>评估目标（选填）</label>
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="例如：减脂、增肌、康复"
            style={{ marginBottom: 15 }}
          />

          {error && <p className="error-text">{error}</p>}
          
          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            <button type="submit" className="primary-btn" disabled={submitting}>
              {submitting ? "创建中..." : "创建并继续"}
            </button>
            <button 
              type="button" 
              onClick={() => navigate("/assessment-center")} 
              style={{ padding: "10px 20px", borderRadius: 8, background: "#333", color: "#fff", border: "none", cursor: "pointer" }}
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
