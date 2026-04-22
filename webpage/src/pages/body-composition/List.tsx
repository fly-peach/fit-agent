import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Card, DatePicker, Empty, Select, Space, Spin, Tag } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import {
  BodyCompositionRecord,
  listBodyComposition,
  getIndicatorConfig,
} from "../../shared/api/bodyComposition";

const { RangePicker } = DatePicker;

export function BodyCompositionListPage() {
  const navigate = useNavigate();
  const [records, setRecords] = useState<BodyCompositionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [configLoading, setConfigLoading] = useState(true);
  const [levelColors, setLevelColors] = useState<Record<string, string>>({});
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [bodyTypeFilter, setBodyTypeFilter] = useState<string | undefined>();

  async function load() {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: "100" };
      if (dateRange) {
        params.from = dateRange[0];
        params.to = dateRange[1];
      }
      const data = await listBodyComposition(params);
      setRecords(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const cfg = await getIndicatorConfig();
        setLevelColors(cfg.level_colors);
      } finally {
        setConfigLoading(false);
      }
    })();
  }, []);

  const filtered = bodyTypeFilter
    ? records.filter((r) => r.body_type === bodyTypeFilter)
    : records;

  const bodyTypes = [...new Set(records.map((r) => r.body_type).filter(Boolean))];

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1 style={{ color: "#fff", margin: 0 }}>体成分记录</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/body-composition/new")}>
          录入新记录
        </Button>
      </div>

      <Space wrap style={{ marginBottom: 16 }}>
        <RangePicker
          onChange={(dates) =>
            setDateRange(dates && dates[0] && dates[1] ? [dates[0].format("YYYY-MM-DD"), dates[1].format("YYYY-MM-DD")] : null)
          }
          onOk={load}
          style={{ background: "#222", borderColor: "#444", color: "#fff" }}
        />
        <Select
          placeholder="按体型筛选"
          allowClear
          value={bodyTypeFilter}
          onChange={(v) => setBodyTypeFilter(v)}
          style={{ width: 160 }}
          options={bodyTypes.map((t) => ({ label: t, value: t! }))}
          popupMatchSelectWidth={false}
        />
      </Space>

      {loading ? (
        <Spin size="large" style={{ display: "block", textAlign: "center", padding: 40 }} />
      ) : filtered.length === 0 ? (
        <Empty description="暂无体成分记录" />
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
          {filtered.map((r) => (
            <Card
              key={r.id}
              hoverable
              onClick={() => navigate(`/body-composition/${r.id}`)}
              style={{ cursor: "pointer", background: "#1a1a2e" }}
              styles={{ body: { padding: "16px" } }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: "#fff" }}>
                    {new Date(r.measured_at).toLocaleDateString()}
                  </div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: "#4f8df8", marginTop: 4 }}>
                    {r.weight?.toFixed(1) ?? "-"} <span style={{ fontSize: 13, color: "#888" }}>kg</span>
                  </div>
                </div>
                {r.body_type && (
                  <Tag color={levelColors[r.body_type] || "default"}>{r.body_type}</Tag>
                )}
              </div>
              <div style={{ marginTop: 12, display: "flex", gap: 16, fontSize: 13, color: "#aaa" }}>
                <span>BMI: {r.bmi ?? "-"}</span>
                <span>体脂率: {r.body_fat_rate?.toFixed(1) ?? "-"}%</span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
