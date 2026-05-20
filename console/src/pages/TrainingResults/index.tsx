import React, { useEffect, useMemo, useState } from "react";
import { Typography, Button, DatePicker, Tabs, Alert, App } from "antd";
import { PlusOutlined, HistoryOutlined } from "@ant-design/icons";
import { BarChart4 } from "lucide-react";
import dayjs from "dayjs";
import {
  trainingResultsApi,
  type TrainingResultSnapshot,
  type TrainingResultTemplateSample,
} from "../../services/training";
import {
  CARD_RESULT_FAILED_EVENT,
  CARD_RESULT_SAVED_EVENT,
  requestCardGeneration,
  type CardResultFailedDetail,
  type CardResultSavedDetail,
} from "../../components/AIAssistant/bridge";
import { useIsMobile } from "../../hooks";
import CardList from "./CardList";
import CardViewer from "./CardViewer";
import "./index.css";

const { RangePicker } = DatePicker;

const PERIOD_OPTIONS = [
  { label: "本周", type: "week", getRange: () => [dayjs().startOf("week"), dayjs().endOf("week")] },
  { label: "本月", type: "month", getRange: () => [dayjs().startOf("month"), dayjs().endOf("month")] },
  { label: "上月", type: "month", getRange: () => [dayjs().subtract(1, "month").startOf("month"), dayjs().subtract(1, "month").endOf("month")] },
  { label: "近7天", type: "custom", getRange: () => [dayjs().subtract(6, "day"), dayjs()] },
  { label: "近30天", type: "custom", getRange: () => [dayjs().subtract(29, "day"), dayjs()] },
] as const;

type PeriodType = "week" | "month" | "custom";

function buildResultTitle(periodType: PeriodType, start: dayjs.Dayjs, end: dayjs.Dayjs) {
  if (periodType === "month") {
    return `${start.format("YYYY年M月")} 训练成果`;
  }
  return `${start.format("YYYY年M月D日")} - ${end.format("M月D日")} 训练成果`;
}

function buildPresetPrompt(
  title: string,
  periodType: PeriodType,
  start: dayjs.Dayjs,
  end: dayjs.Dayjs,
  template?: TrainingResultTemplateSample
) {
  return [
    `请为我生成一张“${title}”的训练成果卡片。`,
    "",
    "【卡片要求】",
    "- 使用 training-card 模板生成结果。",
    template ? `- 使用样式模板：${template.templateKey}（${template.templateName}）` : "",
    `- 统计周期类型：${periodType}`,
    `- 统计区间：${start.format("YYYY-MM-DD")} 至 ${end.format("YYYY-MM-DD")}`,
    "- 结果要突出训练次数、训练总时长、消耗热量、阶段总结。",
    "- 卡片应适合直接在训练成果页展示。",
    template?.description ? `- 模板说明：${template.description}` : "",
    template?.promptHint ? `- 模板提示：${template.promptHint}` : "",
    template?.highlights?.length ? `- 风格重点：${template.highlights.join(" / ")}` : "",
    "",
    "【输出要求】",
    "- 请严格遵循 agent-card-results / training-card skill 的输出规范。",
  ].join("\n");
}

const TrainingResults: React.FC = () => {
  const { message } = App.useApp();
  const [snapshots, setSnapshots] = useState<TrainingResultSnapshot[]>([]);
  const [templates, setTemplates] = useState<TrainingResultTemplateSample[]>([]);
  const [loading, setLoading] = useState(true);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("history");

  const initialRange = PERIOD_OPTIONS[0].getRange() as [dayjs.Dayjs, dayjs.Dayjs];
  const [selectedPeriodLabel, setSelectedPeriodLabel] = useState<string>(PERIOD_OPTIONS[0].label);
  const [selectedPeriodType, setSelectedPeriodType] = useState<PeriodType>("week");
  const [selectedRange, setSelectedRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>(initialRange);
  const [customRange, setCustomRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [submittingToAgent, setSubmittingToAgent] = useState(false);
  const [pendingTitle, setPendingTitle] = useState("");
  const [selectedStyleTemplateKey, setSelectedStyleTemplateKey] = useState("");

  const [viewerOpen, setViewerOpen] = useState(false);
  const [currentSnapshotIndex, setCurrentSnapshotIndex] = useState(0);
  const [currentSnapshotDetail, setCurrentSnapshotDetail] = useState<TrainingResultSnapshot | undefined>(undefined);

  const isMobile = useIsMobile();

  useEffect(() => {
    fetchSnapshots();
    fetchTemplates();
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

  const fetchTemplates = async () => {
    setTemplatesLoading(true);
    try {
      const list = await trainingResultsApi.listTemplates();
      setTemplates(list);
      setSelectedStyleTemplateKey((prev) => prev || list[0]?.templateKey || "");
    } catch {
      message.error("加载模板失败");
    } finally {
      setTemplatesLoading(false);
    }
  };

  const currentTemplate = useMemo(
    () => templates.find((item) => item.templateKey === selectedStyleTemplateKey) || templates[0],
    [templates, selectedStyleTemplateKey]
  );

  const currentTitle = useMemo(
    () => buildResultTitle(selectedPeriodType, selectedRange[0], selectedRange[1]),
    [selectedPeriodType, selectedRange]
  );

  const presetPrompt = useMemo(
    () => buildPresetPrompt(currentTitle, selectedPeriodType, selectedRange[0], selectedRange[1], currentTemplate),
    [currentTitle, selectedPeriodType, selectedRange, currentTemplate]
  );

  const applySelection = (label: string, nextType: PeriodType, range: [dayjs.Dayjs, dayjs.Dayjs]) => {
    setSelectedPeriodLabel(label);
    setSelectedPeriodType(nextType);
    setSelectedRange(range);
  };

  const applyPreset = (label: string) => {
    const option = PERIOD_OPTIONS.find((item) => item.label === label);
    if (!option) return;
    const range = option.getRange() as [dayjs.Dayjs, dayjs.Dayjs];
    applySelection(option.label, option.type as PeriodType, range);
    if (option.type === "custom") {
      setCustomRange(range);
    }
  };

  const handleCustomRangeChange = (dates: [dayjs.Dayjs, dayjs.Dayjs] | null) => {
    setCustomRange(dates);
    if (!dates) return;
    applySelection("自定义", "custom", dates);
  };

  const openSnapshotFromList = async (snapshotId: number) => {
    const list = await trainingResultsApi.listResults();
    setSnapshots(list);
    const newIndex = list.findIndex((item) => item.id === snapshotId);
    if (newIndex !== -1) {
      const detail = await trainingResultsApi.getResult(snapshotId);
      setCurrentSnapshotDetail(detail);
      setCurrentSnapshotIndex(newIndex);
      setViewerOpen(true);
    }
  };

  const openSnapshotDetail = async (snapshotId: number, index: number) => {
    const detail = await trainingResultsApi.getResult(snapshotId);
    setCurrentSnapshotDetail(detail);
    setCurrentSnapshotIndex(index);
    setViewerOpen(true);
  };

  useEffect(() => {
    const handleSaved = async (event: Event) => {
      const detail = (event as CustomEvent<CardResultSavedDetail>).detail;
      if (!detail || detail.source !== "training-results-card") return;

      setSubmittingToAgent(false);
      setPendingTitle("");
      setActiveTab("history");
      message.success("卡片已归档，正在刷新展示");
      await openSnapshotFromList(detail.snapshotId);
    };

    const handleFailed = (event: Event) => {
      const detail = (event as CustomEvent<CardResultFailedDetail>).detail;
      if (!detail || detail.source !== "training-results-card") return;

      setSubmittingToAgent(false);
      setPendingTitle("");
      message.error(detail.message || "AI 生成或归档失败");
    };

    window.addEventListener(CARD_RESULT_SAVED_EVENT, handleSaved as EventListener);
    window.addEventListener(CARD_RESULT_FAILED_EVENT, handleFailed as EventListener);
    return () => {
      window.removeEventListener(CARD_RESULT_SAVED_EVENT, handleSaved as EventListener);
      window.removeEventListener(CARD_RESULT_FAILED_EVENT, handleFailed as EventListener);
    };
  }, []);

  const handleGenerate = () => {
    if (submittingToAgent) return;
    if (!currentTemplate) {
      message.error("请先选择一个卡片模板");
      return;
    }

    requestCardGeneration({
      source: "training-results-card",
      templateKey: "training-card",
      styleTemplateKey: currentTemplate.templateKey,
      styleTemplateSummary: currentTemplate.description,
      styleTemplatePreviewHtml: currentTemplate.previewHtml,
      styleTemplatePromptHint: currentTemplate.promptHint,
      styleTemplateHighlights: currentTemplate.highlights,
      title: currentTitle,
      promptText: presetPrompt,
      periodType: selectedPeriodType,
      periodStart: selectedRange[0].format("YYYY-MM-DD"),
      periodEnd: selectedRange[1].format("YYYY-MM-DD"),
    });

    setSubmittingToAgent(true);
    setPendingTitle(currentTitle);
    message.info("已发送到 AI 侧边栏，新会话将开始生成");
  };

  const handleViewSnapshot = async (snapshot: TrainingResultSnapshot, index: number) => {
    try {
      await openSnapshotDetail(snapshot.id, index);
    } catch {
      message.error("加载卡片详情失败");
    }
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

  const handleViewerNavigate = async (delta: number) => {
    const newIndex = currentSnapshotIndex + delta;
    if (newIndex >= 0 && newIndex < snapshots.length) {
      try {
        await openSnapshotDetail(snapshots[newIndex].id, newIndex);
      } catch {
        message.error("加载卡片详情失败");
      }
    }
  };

  const currentSnapshot = currentSnapshotDetail ?? snapshots[currentSnapshotIndex];

  return (
    <div className="training-results-page fitagent-page-enter" style={{ padding: isMobile ? 12 : 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: "#FFF7ED", color: "#F59E0B" }}>
          <BarChart4 size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>训练成果</Typography.Title>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        items={[
          {
            key: "history",
            label: <span><HistoryOutlined /> 历史成果</span>,
            children: (
              <CardList
                snapshots={snapshots}
                loading={loading}
                onView={handleViewSnapshot}
                onDelete={handleDeleteSnapshot}
              />
            ),
          },
          {
            key: "generate",
            label: <span><PlusOutlined /> 生成新报告</span>,
            children: (
              <div className="training-results-generator">
                <div className="generator-shell">
                  {submittingToAgent && (
                    <Alert
                      className="generator-alert"
                      type="info"
                      showIcon
                      message="已提交到 AI 侧边栏处理"
                      description={`AI 正在新会话中生成并归档：${pendingTitle}`}
                    />
                  )}

                  <div className="generator-grid">
                    <section className="generator-panel generator-panel-controls">
                      <div className="generator-panel-head">
                        <Typography.Text className="generator-eyebrow">STEP 01</Typography.Text>
                        <Typography.Title level={5} style={{ margin: 0 }}>
                          选择统计区间
                        </Typography.Title>
                        <Typography.Paragraph type="secondary" style={{ margin: 0 }}>
                          选择一个预设范围，或直接指定自定义日期区间。
                        </Typography.Paragraph>
                      </div>

                      <div className="generator-section">
                        <Typography.Text strong className="generator-label">
                          卡片模板
                        </Typography.Text>
                        <div className="generator-chip-group generator-template-group">
                          {templates.map((template) => (
                            <Button
                              key={template.templateKey}
                              type={currentTemplate?.templateKey === template.templateKey ? "primary" : "default"}
                              ghost={currentTemplate?.templateKey !== template.templateKey}
                              className="generator-chip generator-template-chip"
                              onClick={() => setSelectedStyleTemplateKey(template.templateKey)}
                              disabled={submittingToAgent || templatesLoading}
                            >
                              {template.templateName}
                            </Button>
                          ))}
                        </div>
                        {currentTemplate && (
                          <Typography.Paragraph type="secondary" className="generator-template-desc">
                            {currentTemplate.description}
                          </Typography.Paragraph>
                        )}
                      </div>

                      <div className="generator-section">
                        <Typography.Text strong className="generator-label">
                          快速范围
                        </Typography.Text>
                        <div className="generator-chip-group">
                          {PERIOD_OPTIONS.map((opt) => (
                            <Button
                              key={opt.label}
                              type={selectedPeriodLabel === opt.label ? "primary" : "default"}
                              ghost={selectedPeriodLabel !== opt.label}
                              className="generator-chip"
                              onClick={() => applyPreset(opt.label)}
                              disabled={submittingToAgent}
                            >
                              {opt.label}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <div className="generator-section">
                        <Typography.Text strong className="generator-label">
                          自定义日期
                        </Typography.Text>
                        <RangePicker
                          value={customRange ?? undefined}
                          onChange={(dates) => handleCustomRangeChange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
                          allowEmpty={[true, true]}
                          className="generator-range-picker"
                          style={{ width: isMobile ? "100%" : undefined }}
                          disabled={submittingToAgent}
                        />
                      </div>
                    </section>

                    <section className="generator-panel generator-panel-preview">
                      <div className="generator-panel-head">
                        <Typography.Text className="generator-eyebrow">STEP 02</Typography.Text>
                        <Typography.Title level={5} style={{ margin: 0 }}>
                          生成卡片
                        </Typography.Title>
                        <Typography.Paragraph type="secondary" style={{ margin: 0 }}>
                          系统会按当前区间自动生成提示词，并发送到 AI 侧边栏的新会话中处理。
                        </Typography.Paragraph>
                      </div>

                      <div className="generator-preview-card">
                        <div className="generator-preview-badge">
                          {currentTemplate?.templateKey || "training-card"}
                        </div>
                        <Typography.Text className="generator-preview-title">
                          {currentTitle}
                        </Typography.Text>
                        {currentTemplate?.highlights?.length ? (
                          <div className="generator-preview-highlights">
                            {currentTemplate.highlights.map((highlight) => (
                              <span key={highlight} className="generator-preview-highlight-tag">
                                {highlight}
                              </span>
                            ))}
                          </div>
                        ) : null}
                        <div className="generator-preview-meta">
                          <div className="generator-preview-stat">
                            <span className="generator-preview-stat-label">周期类型</span>
                            <span className="generator-preview-stat-value">
                              {selectedPeriodType === "week" ? "周报告" : selectedPeriodType === "month" ? "月报告" : "自定义"}
                            </span>
                          </div>
                          <div className="generator-preview-stat">
                            <span className="generator-preview-stat-label">开始时间</span>
                            <span className="generator-preview-stat-value">{selectedRange[0].format("YYYY-MM-DD")}</span>
                          </div>
                          <div className="generator-preview-stat">
                            <span className="generator-preview-stat-label">结束时间</span>
                            <span className="generator-preview-stat-value">{selectedRange[1].format("YYYY-MM-DD")}</span>
                          </div>
                        </div>
                        {currentTemplate?.previewHtml ? (
                          <div
                            className="generator-template-preview-html"
                            dangerouslySetInnerHTML={{ __html: currentTemplate.previewHtml }}
                          />
                        ) : null}
                      </div>

                      <div className="generator-action-row">
                        <Button
                          type="primary"
                          size="large"
                          icon={<PlusOutlined />}
                          onClick={handleGenerate}
                          loading={submittingToAgent}
                          className="generator-submit-btn"
                        >
                          发送到 AI 侧边栏生成
                        </Button>
                        <Typography.Text type="secondary" className="generator-footnote">
                          生成完成后会自动归档，并回到这里展示数据库中的卡片。
                        </Typography.Text>
                      </div>
                    </section>
                  </div>
                </div>
              </div>
            ),
          },
        ]}
      />

      <CardViewer
        open={viewerOpen}
        onClose={() => {
          setViewerOpen(false);
          setCurrentSnapshotDetail(undefined);
        }}
        snapshot={currentSnapshot}
        onNavigate={handleViewerNavigate}
        hasPrev={currentSnapshotIndex > 0}
        hasNext={currentSnapshotIndex < snapshots.length - 1}
      />
    </div>
  );
};

export default TrainingResults;
