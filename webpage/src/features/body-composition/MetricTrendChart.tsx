import { useRef, useEffect } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";

interface TrendPoint {
  measured_at: string;
  value: number;
}

interface MetricTrendChartProps {
  datasets: Array<{ name: string; data: TrendPoint[]; color?: string; yAxisIndex?: number }>;
  height?: number;
}

export function MetricTrendChart({ datasets, height = 300 }: MetricTrendChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || datasets.length === 0) return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }

    const allDates = [...new Set(datasets.flatMap((d) => d.data.map((p) => p.measured_at)))].sort();

    const series = datasets.map((d) => ({
      name: d.name,
      type: "line" as const,
      data: allDates.map((date) => {
        const point = d.data.find((p) => p.measured_at === date);
        return point?.value ?? null;
      }),
      smooth: true,
      symbol: "circle",
      symbolSize: 6,
      lineStyle: { width: 2 },
      yAxisIndex: d.yAxisIndex || 0,
    }));

    const option: EChartsOption = {
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(30,30,40,0.95)",
        borderColor: "#444",
        textStyle: { color: "#fff" },
      },
      legend: {
        textStyle: { color: "#aaa" },
        top: 0,
      },
      grid: { left: 50, right: 20, top: 40, bottom: 30 },
      xAxis: {
        type: "category",
        data: allDates.map((d) => d.slice(5, 10)),
        axisLabel: { color: "#888", fontSize: 11 },
        axisLine: { lineStyle: { color: "#333" } },
      },
      yAxis: datasets.length > 1
        ? [
            { type: "value", axisLabel: { color: "#888" }, splitLine: { lineStyle: { color: "#222" } } },
            { type: "value", axisLabel: { color: "#888" }, splitLine: { show: false } },
          ]
        : { type: "value", axisLabel: { color: "#888" }, splitLine: { lineStyle: { color: "#222" } } },
      series,
    };

    instanceRef.current.setOption(option);

    return () => {
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, [datasets]);

  useEffect(() => {
    const handleResize = () => instanceRef.current?.resize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <div ref={chartRef} style={{ width: "100%", height }} />;
}
