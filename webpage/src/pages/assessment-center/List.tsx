import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Assessment, getAssessments } from "../../shared/api/assessment";

export function AssessmentList() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>("");

  useEffect(() => {
    async function fetchAssessments() {
      setLoading(true);
      try {
        const data = await getAssessments(filterStatus || undefined);
        setAssessments(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchAssessments();
  }, [filterStatus]);

  return (
    <div className="shell">
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h1>评估中心</h1>
          <Link to="/assessment-center/new" className="primary-btn" style={{ textDecoration: "none" }}>
            新建评估
          </Link>
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ marginRight: 10 }}>状态筛选:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">全部</option>
            <option value="draft">草稿</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
          </select>
        </div>

        {loading ? (
          <p>加载中...</p>
        ) : assessments.length === 0 ? (
          <p className="muted-text">暂无评估记录</p>
        ) : (
          <table style={{ width: "100%", textAlign: "left", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #333" }}>
                <th style={{ padding: "10px 0" }}>ID</th>
                <th>目标</th>
                <th>状态</th>
                <th>风险等级</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((a) => (
                <tr key={a.id} style={{ borderBottom: "1px solid #222" }}>
                  <td style={{ padding: "10px 0" }}>#{a.id}</td>
                  <td>{a.goal || "-"}</td>
                  <td>
                    {a.status === "draft" && "草稿"}
                    {a.status === "in_progress" && "进行中"}
                    {a.status === "completed" && "已完成"}
                  </td>
                  <td>{a.risk_level || "-"}</td>
                  <td>{new Date(a.created_at).toLocaleDateString()}</td>
                  <td>
                    <Link to={`/assessment-center/${a.id}`} style={{ color: "#8a2be2" }}>查看</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
