import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Empty, Select, Space, Spin, Table, Tag } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import {
  BodyCompositionRecord,
  BodyCompositionCompareResult,
  listBodyComposition,
  compareBodyComposition,
} from "../../shared/api/bodyComposition";
import { CompositionCompareChart } from "../../features/body-composition/CompositionCompareChart";

const COMPARE_METRICS = [
  { key: "weight", label: "体重", unit: "kg", better: "lower" },
  { key: "bmi", label: "BMI", unit: "", better: "lower" },
  { key: "body_fat_rate", label: "体脂率", unit: "%", better: "lower" },
  { key: "visceral_fat_level", label: "内脏脂肪", unit: "", better: "lower" },
  { key: "fat_mass", label: "脂肪量", unit: "kg", better: "lower" },
  { key: "muscle_mass", label: "肌肉量", unit: "kg", better: "higher" },
  { key: "skeletal_muscle_mass", label: "骨骼肌重量", unit: "kg", better: "higher" },
  { key: "skeletal_muscle_rate", label: "骨骼肌率", unit: "%", better: "higher" },
  { key: "muscle_rate", label: "肌肉率", unit: "%", better: "higher" },
  { key: "bone_mass", label: "骨量", unit: "kg", better: "higher" },
  { key: "water_rate", label: "水分率", unit: "%", better: "normal" },
  { key: "water_mass", label: "水分量", unit: "kg", better: "normal" },
  { key: "protein_mass", label: "蛋白质重量", unit: "kg", better: "higher" },
  { key: "bmr", label: "基础代谢", unit: "kcal", better: "normal" },
  { key: "subcutaneous_fat", label: "皮下脂肪", unit: "%", better: "lower" },
  { key: "fat_free_mass", label: "去脂体重", unit: "kg", better: "higher" },
  { key: "body_age", label: "体年龄", unit: "岁", better: "lower" },
];

export function BodyCompositionComparePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [records, setRecords] = useState<BodyCompositionRecord[]>([]);
  const [recordAId, setRecordAId] = useState<number | undefined>();
  const [recordBId, setRecordBId] = useState<number | undefined>();
  const [compareResult, setCompareResult] = useState<BodyCompositionCompareResult | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await listBodyComposition({ limit: 50 });
        setRecords(data);
        if (data.length >= 2) {
          setRecordAId(data[0].id);
          setRecordBId(data[1].id);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!recordAId || !recordBId) return;
    (async () => {
      try {
        const result = await compareBodyComposition(recordAId, recordBId);
        setCompareResult(result);
      } catch {
        setCompareResult(null);
      }
    })();
  }, [recordAId, recordBId]);

  const recordA = records.find((r) => r.id === recordAId);
  const recordB = records.find((r) => r.id === recordBId);

  const columns: ColumnsType<{ key: string; label: string; unit: string; a: number | null; b: number | null; diff: number }> = [
    { title: "指标", dataIndex: "label", key: "label", width: 120 },
    { title: "记录A", key: "a", render: (_, r) => r.a !== null ? `${r.a}${r.unit}` : "-" },
    { title: "记录B", key: "b", render: (_, r) => r.b !== null ? `${r.b}${r.unit}` : "-" },
    {
      title: "变化",
      key: "diff",
      render: (_, r) => {
        if (r.a === null || r.b === null) return "-";
        const d = r.b - r.a;
        const pct = r.a !== 0 ? ((d / r.a) * 100).toFixed(1) : "-";
        const color = d < 0 ? "#52c41a" : d > 0 ? "#ff4d4f" : "#999";
        return <span style={{ color }}>{d > 0 ? "↑" : d < 0 ? "↓" : "—"}{Math.abs(d).toFixed(2)}{r.unit} ({pct}%)</span>;
      },
    },
  ];

  const tableData = COMPARE_METRICS.map((m) => ({
    key: m.key,
    label: m.label,
    unit: m.unit,
    a: recordA?.[m.key as keyof BodyCompositionRecord] as number | null ?? null,
    b: recordB?.[m.key as keyof BodyCompositionRecord] as number | null ?? null,
    diff: 0,
  }));

  const radarData = COMPARE_METRICS.filter((m) =>
    ["weight", "body_fat_rate", "muscle_mass", "fat_mass", "skeletal_muscle_rate", "water_rate"].includes(m.key)
  );

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 20 }}>
      <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/body-composition")} style={{ color: "#fff", marginBottom: 16 }}>
        返回
      </Button>

      <Card title="体成分对比" style={{ background: "#1a1a2e", borderColor: "#333" }}>
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="选择记录A"
            value={recordAId}
            onChange={setRecordAId}
            style={{ width: 240 }}
            options={records.map((r) => ({
              label: `${new Date(r.measured_at).toLocaleDateString()} (${r.weight}kg)`,
              value: r.id,
            }))}
          />
          <span style={{ color: "#888", fontSize: 20, fontWeight: 700 }}>vs</span>
          <Select
            placeholder="选择记录B"
            value={recordBId}
            onChange={setRecordBId}
            style={{ width: 240 }}
            options={records.map((r) => ({
              label: `${new Date(r.measured_at).toLocaleDateString()} (${r.weight}kg)`,
              value: r.id,
            }))}
          />
        </Space>

        {!recordA || !recordB ? (
          <Empty description="请选择两条记录进行对比" />
        ) : (
          <>
            <div style={{ marginBottom: 16, color: "#888", fontSize: 13 }}>
              {new Date(recordA.measured_at).toLocaleDateString()} → {new Date(recordB.measured_at).toLocaleDateString()}
            </div>

            <Card style={{ background: "#222", marginBottom: 16 }}>
              <CompositionCompareChart
                a={Object.fromEntries(radarData.map((m) => [m.label, ((recordA as any)[m.key] || 0) * 2]))}
                b={Object.fromEntries(radarData.map((m) => [m.label, ((recordB as any)[m.key] || 0) * 2]))}
                labels={radarData.map((m) => m.label)}
                height={300}
              />
            </Card>

            <Table
              columns={columns}
              dataSource={tableData}
              pagination={false}
              size="small"
              style={{ background: "#222" }}
              rowClassName={() => ""}
              components={{
                header: {
                  cell: (props: any) => <th {...props} style={{ ...props.style, color: "#aaa", background: "#1a1a2e" }} />,
                },
              }}
            />
          </>
        )}
      </Card>
    </div>
  );
}
