import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Assessment, getAssessment, completeAssessment, getAssessmentReport, AssessmentReport } from "../../shared/api/assessment";

export function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [report, setReport] = useState<AssessmentReport | null>(null);
  const [loading, setLoading] = useState(true);
  
  // 报告表单状态
  const [riskLevel, setRiskLevel] = useState<"low" | "medium" | "high">("low");
  const [reportNote, setReportNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    async function fetchDetail() {
      try {
        const data = await getAssessment(Number(id));
        setAssessment(data);
        if (data.status === "completed") {
          const rep = await getAssessmentReport(Number(id));
          setReport(rep);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [id]);

  if (loading) return <div className="shell"><p>加载中...</p></div>;
  if (!assessment) return <div className="shell"><p>评估不存在或无权访问</p></div>;

  const isCompleted = assessment.status === "completed";

  async function handleComplete(e: React.FormEvent) {
    e.preventDefault();
    if (!id) return;
    setSubmitting(true);
    try {
      const updated = await completeAssessment(Number(id), {
        risk_level: riskLevel,
        report_summary: { notes: reportNote }
      });
      setAssessment(updated);
      const rep = await getAssessmentReport(Number(id));
      setReport(rep);
    } catch (err) {
      alert("完成评估失败: " + (err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="shell">
      <div className="card" style={{ maxWidth: 800, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h1>评估详情 #{assessment.id}</h1>
          <button 
            onClick={() => navigate("/assessment-center")} 
            style={{ padding: "8px 16px", borderRadius: 8, background: "#333", color: "#fff", border: "none", cursor: "pointer" }}
          >
            返回列表
          </button>
        </div>

        <div style={{ background: "#222", padding: 15, borderRadius: 8, marginBottom: 20 }}>
          <p><strong>目标:</strong> {assessment.goal || "无"}</p>
          <p><strong>当前状态:</strong> {isCompleted ? "已完成" : "进行中"}</p>
          <p><strong>创建时间:</strong> {new Date(assessment.created_at).toLocaleString()}</p>
        </div>

        {isCompleted && report ? (
          <div>
            <h2>评估报告</h2>
            <div style={{ background: "#2c3e50", padding: 15, borderRadius: 8, borderLeft: "4px solid #8a2be2" }}>
              <p><strong>风险等级:</strong> {report.risk_level}</p>
              <p><strong>评估建议:</strong> {report.report_summary?.notes || "暂无建议"}</p>
              <p><strong>完成时间:</strong> {report.completed_at ? new Date(report.completed_at).toLocaleString() : "-"}</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleComplete} style={{ marginTop: 20 }}>
            <h2>出具报告并完成评估</h2>
            <label>风险等级</label>
            <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value as any)} style={{ marginBottom: 15 }}>
              <option value="low">低风险 (Low)</option>
              <option value="medium">中等风险 (Medium)</option>
              <option value="high">高风险 (High)</option>
            </select>

            <label>评估建议</label>
            <textarea
              value={reportNote}
              onChange={(e) => setReportNote(e.target.value)}
              placeholder="请输入针对该会员的训练建议..."
              style={{ width: "100%", padding: 10, minHeight: 100, marginBottom: 15, borderRadius: 8, border: "1px solid #444", background: "#222", color: "#fff" }}
              required
            />
            
            <button type="submit" className="primary-btn" disabled={submitting}>
              {submitting ? "提交中..." : "确认完成评估"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
