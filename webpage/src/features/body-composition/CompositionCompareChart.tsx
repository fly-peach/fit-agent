import { useRef, useEffect } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";

interface CompositionCompareChartProps {
  a: Record<string, number>;
  b: Record<string, number>;
  labels: string[];
  height?: number;
}

export function CompositionCompareChart({ a, b, labels, height = 350 }: CompositionCompareChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }

    const option: EChartsOption = {
      tooltip: {
        backgroundColor: "rgba(30,30,40,0.95)",
        borderColor: "#444",
        textStyle: { color: "#fff" },
      },
      legend: {
        data: ["记录A", "记录B"],
        textStyle: { color: "#aaa" },
        top: 0,
      },
      radar: {
        indicator: labels.map((l) => ({ name: l, max: 100 })),
        shape: "polygon",
        splitNumber: 4,
        axisName: { color: "#aaa" },
        splitLine: { lineStyle: { color: "#333" } },
        splitArea: { areaStyle: { color: ["rgba(40,40,60,0.3)", "rgba(30,30,50,0.2)"] } },
        axisLine: { lineStyle: { color: "#444" } },
      },
      series: [
        {
          type: "radar",
          data: [
            { value: labels.map((l) => a[l] ?? 0), name: "记录A", areaStyle: { opacity: 0.3 }, lineStyle: { color: "#4f8df8" } },
            { value: labels.map((l) => b[l] ?? 0), name: "记录B", areaStyle: { opacity: 0.3 }, lineStyle: { color: "#52c41a" } },
          ],
        },
      ],
    };

    instanceRef.current.setOption(option);

    return () => {
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, [a, b, labels]);

  useEffect(() => {
    const handleResize = () => instanceRef.current?.resize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <div ref={chartRef} style={{ width: "100%", height }} />;
}
