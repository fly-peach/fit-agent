import { Collapse } from "antd";
import { IndicatorCard } from "./IndicatorCard";

const { Panel } = Collapse;

interface IndicatorGroupProps {
  label: string;
  icon: React.ReactNode;
  items: Array<{
    key: string;
    label: string;
    value: number | string | null;
    unit: string;
    level: string;
    reference?: string;
    delta?: number;
    icon?: React.ReactNode;
  }>;
}

export function IndicatorGroup({ label, icon, items }: IndicatorGroupProps) {
  const count = items.filter((i) => i.level === "标准" || i.level === "优" || i.level === "正常" || i.level === "良").length;
  const low = items.filter((i) => i.level === "不足" || i.level === "偏低" || i.level === "偏轻").length;
  const high = items.filter((i) => i.level === "偏高" || i.level === "过重" || i.level === "偏胖" || i.level === "警戒型" || i.level === "轻度肥胖" || i.level === "肥胖").length;

  const header = (
    <span>
      <span style={{ marginRight: 8 }}>{icon}</span>
      {label}
      <span style={{ marginLeft: 12, fontSize: 12, color: "#888" }}>
        {count}项达标 ✓{low > 0 && ` | ${low}项偏低 ↓`}{high > 0 && ` | ${high}项偏高 ↑`}
      </span>
    </span>
  );

  return (
    <Collapse defaultActiveKey={[]} ghost>
      <Panel header={header} key="group">
        {items.map((item) => (
          <IndicatorCard
            key={item.key}
            label={item.label}
            value={item.value}
            unit={item.unit}
            level={item.level}
            reference={item.reference}
            delta={item.delta}
            icon={item.icon}
          />
        ))}
      </Panel>
    </Collapse>
  );
}
