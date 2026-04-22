import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Empty, Select, Space, Spin, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import {
  BodyCompositionTrendPoint,
  listBodyComposition,
  getBodyCompositionTrend,
} from "../../shared/api/bodyComposition";
import { MetricTrendChart } from "../../features/body-composition/MetricTrendChart";

const METRIC_OPTIONS = [
  { value: "weight", label: "体重", unit: "kg" },
  { value: "body_fat_rate", label: "体脂率", unit: "%" },
  { value: "bmi", label: "BMI", unit: "" },
  { value: "muscle_mass", label: "肌肉量", unit: "kg" },
  { value: "fat_mass", label: "脂肪量", unit: "kg" },
  { value: "skeletal_muscle_rate", label: "骨骼肌率", unit: "%" },
  { value: "water_rate", label: "水分率", unit: "%" },
  { value: "bmr", label: "基础代谢", unit: "kcal" },
];

export function BodyCompositionTrendPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [selectedMetrics, setSelectedMetrics] = useState(["weight"]);
  const [datasets, setDatasets] = useState<
    Array<{ name: string; data: BodyCompositionTrendPoint[]; color?: string; yAxisIndex?: number }>
  >([]);
  const [records, setRecords] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const allRecords = await listBodyComposition({ limit: 200 });
        setRecords(allRecords);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (records.length === 0) return;

    const newDatasets = selectedMetrics.map((metric, idx) => {
      const data = records
        .filter((r) => r[metric] !== null)
        .map((r) => ({
          measured_at: r.measured_at,
          value: r[metric],
        }))
        .reverse();
      const opt = METRIC_OPTIONS.find((o) => o.value === metric);
      return {
        name: opt?.label || metric,
        data,
        color: idx === 0 ? "#4f8df8" : "#52c41a",
        yAxisIndex: idx > 0 ? 1 : 0,
      };
    });
    setDatasets(newDatasets);
  }, [selectedMetrics, records]);

  const summary = (() => {
    if (datasets.length === 0 || datasets[0].data.length < 2) return null;
    const data = datasets[0].data;
    const start = data[0].value;
    const end = data[data.length - 1].value;
    const values = data.map((d) => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const opt = METRIC_OPTIONS.find((o) => o.value === selectedMetrics[0]);
    return {
      start: start.toFixed(1),
      end: end.toFixed(1),
      delta: (end - start).toFixed(2),
      min: min.toFixed(1),
      max: max.toFixed(1),
      unit: opt?.unit || "",
      down: end < start,
    };
  })();

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 20 }}>
      <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/body-composition")} style={{ color: "#fff", marginBottom: 16 }}>
        返回
      </Button>

      <Card title="体成分趋势" style={{ background: "#1a1a2e", borderColor: "#333" }}>
        <Space wrap style={{ marginBottom: 16 }}>
          <Select
            mode="multiple"
            maxTagCount="responsive"
            value={selectedMetrics}
            onChange={setSelectedMetrics}
            style={{ width: 300 }}
            options={METRIC_OPTIONS}
            placeholder="选择要展示的指标"
          />
        </Space>

        {loading ? (
          <Spin size="large" style={{ display: "block", textAlign: "center", padding: 40 }} />
        ) : datasets.length === 0 || datasets.every((d) => d.data.length === 0) ? (
          <Empty description="暂无趋势数据" />
        ) : (
          <>
            <MetricTrendChart datasets={datasets} height={350} />

            {summary && (
              <div style={{ marginTop: 16, padding: 16, background: "#222", borderRadius: 8 }}>
                <Typography.Text style={{ color: "#aaa" }}>统计摘要</Typography.Text>
                <div style={{ marginTop: 8, display: "flex", gap: 24, fontSize: 14 }}>
                  <span>
                    起始: <span style={{ color: "#fff" }}>{summary.start}{summary.unit}</span> → 当前:{" "}
                    <span style={{ color: summary.down ? "#52c41a" : "#ff4d4f" }}>
                      {summary.end}{summary.unit} ({summary.down ? "↓" : "↑"}{summary.delta}{summary.unit})
                    </span>
                  </span>
                  <span>
                    最高: <span style={{ color: "#ff4d4f" }}>{summary.max}{summary.unit}</span>
                    {" "}最低: <span style={{ color: "#52c41a" }}>{summary.min}{summary.unit}</span>
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
