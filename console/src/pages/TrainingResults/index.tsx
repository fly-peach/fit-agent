import React, { useEffect, useState } from "react";
import {
  Typography,
  Button,
  DatePicker,
  Space,
  message,
  Tabs,
} from "antd";
import { PlusOutlined, TrophyOutlined } from "@ant-design/icons";
import { BarChart4 } from "lucide-react";
import dayjs from "dayjs";
import api from "../../utils/request";
import { trainingResultsApi, type TrainingResultSnapshot } from "../../services/training";
import { useIsMobile } from "../../hooks";
import CardList from "./CardList";
import CardViewer from "./CardViewer";
import "./index.css";

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

const PERIOD_OPTIONS = [
  { label: "本周", type: "week", getRange: () => [dayjs().startOf("week"), dayjs().endOf("week")] },
  { label: "本月", type: "month", getRange: () => [dayjs().startOf("month"), dayjs().endOf("month")] },
  { label: "上月", type: "month", getRange: () => [dayjs().subtract(1, "month").startOf("month"), dayjs().subtract(1, "month").endOf("month")] },
  { label: "近7天", type: "custom", getRange: () => [dayjs().subtract(6, "day"), dayjs()] },
  { label: "近30天", type: "custom", getRange: () => [dayjs().subtract(29, "day"), dayjs()] },
];

const TrainingResults: React.FC = () => {
  const [snapshots, setSnapshots] = useState<TrainingResultSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("history");

  // 卡片生成相关
  const [generating, setGenerating] = useState(false);
  const [customRange, setCustomRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  // 查看器相关
  const [viewerOpen, setViewerOpen] = useState(false);
  const [currentSnapshotIndex, setCurrentSnapshotIndex] = useState(0);

  const isMobile = useIsMobile();

  useEffect(() => {
    fetchSnapshots();
  }, []);

  const fetchSnapshots = async () => {
    setLoading(true);
    try {
      const list = await trainingResultsApi.listResults();
      setSnapshots(list);
    } catch {
      message.error("加载失败");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (periodType: string, start?: dayjs.Dayjs, end?: dayjs.Dayjs) => {
    let periodLabel = periodType;
    let periodStart = start;
    let periodEnd = end;

    if (!start || !end) {
      const opt = PERIOD_OPTIONS.find((p) => p.label === periodType);
      if (opt) {
        [periodStart, periodEnd] = opt.getRange();
        periodType = opt.type;
      }
    }

    if (!periodStart || !periodEnd) {
      message.error("请选择时间范围");
      return;
    }

    // 生成标题
    let title = "";
    if (periodType === "week") {
      title = `${periodStart.format("YYYY年M月D日")} - ${periodEnd.format("M月D日")} 训练成果`;
    } else if (periodType === "month") {
      title = `${periodStart.format("YYYY年M月")} 训练成果`;
    } else {
      title = `${periodStart.format("YYYY年M月D日")} - ${periodEnd.format("M月D日")} 训练成果`;
    }

    setGenerating(true);

    try {
      // 调用 Agent API 生成卡片
      let htmlContent = "";
      let statsJson = "";
      let buffer = "";

      const token = localStorage.getItem('token');
      const sessionId = `training-results-${Date.now()}`;

      // 使用 fetch + ReadableStream 替代 EventSource（支持 Authorization header）
      const baseUrl = api.defaults.baseURL || '';
      const url = `${baseUrl}/agent/chat?session_id=${sessionId}&q=${encodeURIComponent(`请生成 ${title} 的训练成果卡片`)}`;

      let done = false;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body');
        }

        const decoder = new TextDecoder();

        while (!done) {
          const { value, done: streamDone } = await reader.read();
          if (streamDone) {
            done = true;
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (dataStr === '[DONE]') {
                done = true;
                break;
              }

              try {
                const data = JSON.parse(dataStr);
                if (data?.choices?.[0]?.delta?.content) {
                  buffer += data.choices[0].delta.content;
                }
              } catch {
                // 忽略解析错误
              }
            }
          }
        }
      } finally {
        clearTimeout(timeoutId);
      }

      // 从 buffer 中提取标记内容
      const htmlMatch = buffer.match(/<!--CARD_HTML_START-->([\s\S]*?)<!--CARD_HTML_END-->/);
      const statsMatch = buffer.match(/<!--STATS_JSON_START-->([\s\S]*?)<!--STATS_JSON_END-->/);

      htmlContent = htmlMatch ? htmlMatch[1] : `<div class="fallback-card">${buffer}</div>`;
      statsJson = statsMatch ? statsMatch[1] : "";

      // 保存卡片
      const saved = await trainingResultsApi.saveResult({
        cardHtml: htmlContent,
        title,
        periodType: periodType as any,
        periodStart: periodStart.format("YYYY-MM-DD"),
        periodEnd: periodEnd.format("YYYY-MM-DD"),
        statsJson,
      });

      message.success("生成成功！");
      setActiveTab("history");
      fetchSnapshots();

      // 打开查看器
      const newList = await trainingResultsApi.listResults();
      const newIndex = newList.findIndex((s) => s.id === saved.snapshotId);
      if (newIndex !== -1) {
        setCurrentSnapshotIndex(newIndex);
        setViewerOpen(true);
      }
    } catch {
      message.error("生成失败");
    } finally {
      setGenerating(false);
    }
  };

  const handleViewSnapshot = (snapshot: TrainingResultSnapshot, index: number) => {
    setCurrentSnapshotIndex(index);
    setViewerOpen(true);
  };

  const handleDeleteSnapshot = async (snapshotId: number) => {
    try {
      await trainingResultsApi.deleteResult(snapshotId);
      message.success("删除成功");
      fetchSnapshots();
    } catch {
      message.error("删除失败");
    }
  };

  const handleViewerNavigate = (delta: number) => {
    const newIndex = currentSnapshotIndex + delta;
    if (newIndex >= 0 && newIndex < snapshots.length) {
      setCurrentSnapshotIndex(newIndex);
    }
  };

  const currentSnapshot = snapshots[currentSnapshotIndex];

  return (
    <div className="training-results-page fitagent-page-enter" style={{ padding: isMobile ? 12 : 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: "#FFF7ED", color: "#F59E0B" }}>
          <BarChart4 size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>训练成果</Typography.Title>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
        <TabPane
          tab={
            <span>
              <TrophyOutlined /> 历史成果
            </span>
          }
          key="history"
        >
          <CardList
            snapshots={snapshots}
            loading={loading}
            onView={handleViewSnapshot}
            onDelete={handleDeleteSnapshot}
          />
        </TabPane>

        <TabPane
          tab={
            <span>
              <PlusOutlined /> 生成新报告
            </span>
          }
          key="generate"
        >
          <div style={{ padding: isMobile ? 12 : 24, background: "#F5F5F5", borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: "100%" }} size={16}>
              <div>
                <Typography.Text strong style={{ display: "block", marginBottom: 12 }}>
                  快速选择
                </Typography.Text>
                <Space wrap size={8}>
                  {PERIOD_OPTIONS.map((opt) => (
                    <Button
                      key={opt.label}
                      type="primary"
                      ghost
                      onClick={() => handleGenerate(opt.label)}
                      loading={generating}
                    >
                      {opt.label}
                    </Button>
                  ))}
                </Space>
              </div>

              <div>
                <Typography.Text strong style={{ display: "block", marginBottom: 12 }}>
                  自定义范围
                </Typography.Text>
                <Space direction="vertical">
                  <RangePicker
                    value={customRange}
                    onChange={(dates) => setCustomRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
                    style={{ width: isMobile ? "100%" : 400 }}
                  />
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => customRange && handleGenerate("custom", customRange[0], customRange[1])}
                    disabled={!customRange}
                    loading={generating}
                  >
                    生成自定义报告
                  </Button>
                </Space>
              </div>
            </Space>
          </div>
        </TabPane>
      </Tabs>

      <CardViewer
        open={viewerOpen}
        onClose={() => setViewerOpen(false)}
        snapshot={currentSnapshot}
        onNavigate={handleViewerNavigate}
        hasPrev={currentSnapshotIndex > 0}
        hasNext={currentSnapshotIndex < snapshots.length - 1}
      />
    </div>
  );
};

export default TrainingResults;
