import { useState } from "react";
import { StatusTag } from "./StatusTag";

interface IndicatorCardProps {
  label: string;
  value: number | string | null;
  unit: string;
  level: string;
  reference?: string;
  delta?: number;
  icon?: React.ReactNode;
}

export function IndicatorCard({
  label,
  value,
  unit,
  level,
  reference,
  delta,
  icon,
}: IndicatorCardProps) {
  const [expanded, setExpanded] = useState(false);

  const deltaColor =
    delta !== undefined
      ? delta < 0
        ? "#52c41a"
        : delta > 0
          ? "#ff4d4f"
          : "#999"
      : undefined;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        padding: "12px 16px",
        borderBottom: "1px solid #222",
        cursor: "pointer",
        userSelect: "none",
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <div style={{ width: 32, marginRight: 12, color: "#888", fontSize: 18 }}>
        {icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, color: "#aaa", marginBottom: 2 }}>{label}</div>
        <div style={{ fontSize: 20, fontWeight: 600, color: "#fff" }}>
          {value ?? "-"}
          <span style={{ fontSize: 13, color: "#888", marginLeft: 4 }}>{unit}</span>
          {delta !== undefined && (
            <span
              style={{
                fontSize: 12,
                color: deltaColor,
                marginLeft: 10,
              }}
            >
              {delta > 0 ? "↑" : delta < 0 ? "↓" : "—"}
              {Math.abs(delta).toFixed(1)}
            </span>
          )}
        </div>
        {expanded && reference && (
          <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>参考范围：{reference}</div>
        )}
      </div>
      <div style={{ marginLeft: 12 }}>
        <StatusTag level={level} />
      </div>
    </div>
  );
}
