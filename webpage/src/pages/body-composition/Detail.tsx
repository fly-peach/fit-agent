import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button, Card, Collapse, Empty, Spin, Space, Tag, message } from "antd";
import {
  ArrowLeftOutlined,
  LineChartOutlined,
  SwapOutlined,
  FireOutlined,
  ThunderboltOutlined,
  HeartOutlined,
  CheckCircleOutlined,
  AimOutlined,
  CloudOutlined,
} from "@ant-design/icons";
import {
  BodyCompositionRecord,
  BodyCompositionEvaluateResult,
  getBodyComposition,
  evaluateBodyComposition,
  getIndicatorConfig,
} from "../../shared/api/bodyComposition";
import { IndicatorGroup } from "../../features/body-composition/IndicatorGroup";
import { StatusTag } from "../../features/body-composition/StatusTag";

const { Panel } = Collapse;

const ICON_MAP: Record<string, React.ReactNode> = {
  body_composition: <CloudOutlined />,
  muscle_bone: <FireOutlined />,
  water_metabolism: <CloudOutlined />,
  metabolism: <ThunderboltOutlined />,
  control_goals: <AimOutlined />,
  health_assessment: <HeartOutlined />,
};

const UNIT_MAP: Record<string, string> = {
  weight: "kg", bmi: "", body_fat_rate: "%", visceral_fat_level: "",
  fat_mass: "kg", muscle_mass: "kg", skeletal_muscle_mass: "kg",
  skeletal_muscle_rate: "%", water_rate: "%", water_mass: "kg",
  bmr: "kcal", muscle_rate: "%", bone_mass: "kg", protein_mass: "kg",
  ideal_weight: "kg", weight_control: "kg", fat_control: "kg",
  muscle_control: "kg", body_age: "岁", subcutaneous_fat: "%",
  fat_free_mass: "kg", fat_burn_hr_low: "bpm", fat_burn_hr_high: "bpm",
  protein_rate: "%",
};

const LABEL_MAP: Record<string, string> = {
  weight: "体重", bmi: "BMI", body_fat_rate: "体脂率", visceral_fat_level: "内脏脂肪等级",
  fat_mass: "脂肪量", muscle_mass: "肌肉量", skeletal_muscle_mass: "骨骼肌重量",
  skeletal_muscle_rate: "骨骼肌率", water_rate: "水分率", water_mass: "水分量",
  bmr: "基础代谢", muscle_rate: "肌肉率", bone_mass: "骨量", protein_mass: "蛋白质重量",
  ideal_weight: "理想体重", weight_control: "体重控制量", fat_control: "脂肪控制量",
  muscle_control: "肌肉控制量", body_age: "体年龄", subcutaneous_fat: "皮下脂肪",
  fat_free_mass: "去脂体重", fat_burn_hr_low: "燃脂心率下限", fat_burn_hr_high: "燃脂心率上限",
  protein_rate: "蛋白质率",
};

export function BodyCompositionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState<BodyCompositionRecord | null>(null);
  const [evalResult, setEvalResult] = useState<BodyCompositionEvaluateResult | null>(null);
  const [levelColors, setLevelColors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    (async () => {
      setLoading(true);
      try {
        const [data, cfg] = await Promise.all([
          getBodyComposition(Number(id)),
          getIndicatorConfig(),
        ]);
        setRecord(data);
        setLevelColors(cfg.level_colors);

        try {
          const evalRes = await evaluateBodyComposition(Number(id));
          setEvalResult(evalRes);
        } catch {
          // eval may fail for old records
        }
      } catch {
        message.error("加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <div style={{ padding: 40, textAlign: "center" }}><Spin size="large" /></div>;
  if (!record) return <div style={{ padding: 40 }}><Empty description="记录不存在或无权访问" /></div>;

  const groups = searchParams.get("groups")
    ? JSON.parse(decodeURIComponent(searchParams.get("groups")!))
    : null;

  const allLevels = evalResult?.indicator_levels ?? {};
  const levels = { ...allLevels, ...Object.fromEntries(
    Object.entries(record).filter(([k]) => Object.keys(LABEL_MAP).includes(k)).map(([k, v]) => [k, (v !== null && evalResult?.indicator_levels[k]) || "标准"])
  )};

  function buildGroupItems(indicators: string[]) {
    return indicators.map((key) => ({
      key,
      label: LABEL_MAP[key] || key,
      value: (record as Record<string, any>)[key] ?? null,
      unit: UNIT_MAP[key] || "",
      level: levels[key] || "标准",
    }));
  }

  const defaultGroups = {
    body_composition: { label: "身体成分", icon: <CloudOutlined />, indicators: ["weight", "bmi", "body_fat_rate", "visceral_fat_level", "fat_mass"] },
    muscle_bone: { label: "肌肉骨骼", icon: <FireOutlined />, indicators: ["muscle_mass", "skeletal_muscle_mass", "skeletal_muscle_rate", "muscle_rate", "bone_mass"] },
    water_metabolism: { label: "水分代谢", icon: <CloudOutlined />, indicators: ["water_rate", "water_mass", "protein_mass", "protein_rate"] },
    metabolism: { label: "代谢能力", icon: <ThunderboltOutlined />, indicators: ["bmr", "fat_free_mass", "fat_burn_hr_low", "fat_burn_hr_high"] },
    control_goals: { label: "控制目标", icon: <AimOutlined />, indicators: ["ideal_weight", "weight_control", "fat_control", "muscle_control"] },
    health_assessment: { label: "健康评估", icon: <HeartOutlined />, indicators: ["body_type", "nutrition_status", "body_age", "subcutaneous_fat"] },
  };

  const groupsToRender = groups || defaultGroups;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/body-composition")} style={{ color: "#fff" }}>
          返回列表
        </Button>
        <Space>
          <Button icon={<SwapOutlined />} onClick={() => navigate("/body-composition/compare")}>对比</Button>
          <Button icon={<LineChartOutlined />} onClick={() => navigate("/body-composition/trend")}>趋势</Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16, background: "#1a1a2e", borderColor: "#333" }}>
        <div style={{ fontSize: 13, color: "#888", marginBottom: 8 }}>
          体测时间：{new Date(record.measured_at).toLocaleString()}
        </div>
        <Space size="large" wrap>
          {evalResult && (
            <>
              <div>
                <div style={{ fontSize: 12, color: "#888" }}>体型</div>
                {record.body_type ? <StatusTag level={record.body_type} /> : <span style={{ color: "#fff" }}>{evalResult.body_type || "-"}</span>}
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#888" }}>健康评分</div>
                <span style={{ fontSize: 24, fontWeight: 700, color: evalResult.health_score >= 80 ? "#52c41a" : evalResult.health_score >= 60 ? "#faad14" : "#ff4d4f" }}>
                  {evalResult.health_score}
                </span>
                <span style={{ fontSize: 13, color: "#888" }}> 分</span>
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#888" }}>营养状态</div>
                <StatusTag level={evalResult.nutrition_status || "标准"} />
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#888" }}>体年龄</div>
                <span style={{ color: "#fff", fontSize: 18 }}>{evalResult.body_age ?? "-"}</span>
                <span style={{ fontSize: 13, color: "#888" }}> 岁</span>
              </div>
            </>
          )}
        </Space>
      </Card>

      {Object.entries(groupsToRender).map(([key, g]: [string, any]) => (
        <IndicatorGroup
          key={key}
          label={g.label}
          icon={ICON_MAP[key] || <CheckCircleOutlined />}
          items={buildGroupItems(g.indicators)}
        />
      ))}
    </div>
  );
}
