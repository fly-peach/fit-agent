import React, { useEffect, useState } from "react";
import {
  Typography,
  Row,
  Col,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  Calendar,
  Tag,
  Space,
  message,
  Radio,
  Checkbox,
  List,
  Avatar,
  Popconfirm,
  Divider,
  Card,
} from "antd";
import {
  PlusOutlined,
  CheckOutlined,
  EditOutlined,
  SyncOutlined,
  LeftOutlined,
  RightOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { Dumbbell } from "lucide-react";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";
import api from "../../utils/request";
import {
  trainingApi,
  type WeeklyStats,
  type PlanDetail,
  PlanExerciseItemOutput,
} from "../../services/training";
import { exerciseApi, PlanExerciseInput } from "../../services/exercise";
import ExercisePicker from "../../components/ExercisePicker";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useIsMobile } from "../../hooks";
import "dayjs/locale/zh-cn";

const planTypes = [
  { value: "strength", label: "力量训练" },
  { value: "cardio", label: "有氧运动" },
  { value: "flexibility", label: "柔韧训练" },
];

const intensities = [
  { value: "low", label: "低强度" },
  { value: "medium", label: "中等强度" },
  { value: "high", label: "高强度" },
];

const Training: React.FC = () => {
  const sharedTrendLineMotion = {
    isAnimationActive: true,
    animationBegin: 0,
    animationDuration: 420,
    animationEasing: "ease-out" as const,
  };
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null);
  const [monthSchedule, setMonthSchedule] = useState<
    {
      planId?: number;
      date: string;
      planName: string;
      planType: string;
      duration: number;
      intensity: string;
      status: string;
      isRecurring?: boolean;
      isLastInGroup?: boolean;
    }[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState<Dayjs>(dayjs());
  const [createOpen, setCreateOpen] = useState(false);
  const [completeOpen, setCompleteOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [editingPlanId, setEditingPlanId] = useState<number | null>(null);
  const [createForm] = Form.useForm();
  const [completeForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [selectedCalendarDate, setSelectedCalendarDate] = useState<string>(dayjs().format('YYYY-MM-DD'));

  const [trendDays, setTrendDays] = useState(7);
  const [trendLoading, setTrendLoading] = useState(false);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [activeMetrics, setActiveMetrics] = useState<string[]>([
    "duration",
    "caloriesBurned",
  ]);

  const [exercisePickerOpen, setExercisePickerOpen] = useState(false);
  const [selectedExercises, setSelectedExercises] = useState<
    PlanExerciseInput[]
  >([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState<PlanDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [editingExerciseId, setEditingExerciseId] = useState<number | null>(
    null,
  );
  const [editingDraft, setEditingDraft] = useState<{
    sets: number;
    reps: number;
    weight: number | null;
  } | null>(null);
  const [detailPlanInfo, setDetailPlanInfo] = useState<{
    isRecurring?: boolean;
    isLastInGroup?: boolean;
  } | null>(null);
  const [detailExercisePickerOpen, setDetailExercisePickerOpen] =
    useState(false);
  const [detailCustomName, setDetailCustomName] = useState("");
  const [detailCustomSets, setDetailCustomSets] = useState(3);
  const [detailCustomReps, setDetailCustomReps] = useState(10);

  // 自定义动作 Modal
  const [customExerciseOpen, setCustomExerciseOpen] = useState(false);
  const [customExerciseForm] = Form.useForm();
  const [catMuscles, setCatMuscles] = useState<string[]>([]);
  const [catTypes, setCatTypes] = useState<string[]>([]);
  const [catEquipment, setCatEquipment] = useState<string[]>([]);
  const [catForceTypes, setCatForceTypes] = useState<string[]>([]);
  const [catMechanics, setCatMechanics] = useState<string[]>([]);
  const [instructionsInput, setInstructionsInput] = useState<string[]>([""]);

  const isMobile = useIsMobile();

  const handleRenewPlan = async (planId: number) => {
    try {
      await api.post(`/api/training/plans/${planId}/renew`);
      message.success("续期成功");
      fetchData();
    } catch {
      message.error("续期失败");
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentMonth]);

  useEffect(() => {
    fetchTrendData();
  }, [trendDays]);

  const fetchTrendData = async () => {
    setTrendLoading(true);
    try {
      const end = dayjs();
      const start = end.subtract(trendDays - 1, "day");
      const result = await trainingApi.getDateRangeTrend(
        start.format("YYYY-MM-DD"),
        end.format("YYYY-MM-DD"),
      );
      const formatted = result.dailyStats.map((d) => ({
        ...d,
        date: dayjs(d.date).format("MM/DD"),
      }));
      setTrendData(formatted);
    } catch {
      /* ignore */
    } finally {
      setTrendLoading(false);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [stats, sched] = await Promise.all([
        trainingApi.getWeeklyStats(),
        trainingApi.getMonthlySchedule(
          currentMonth.year(),
          currentMonth.month() + 1,
        ),
      ]);
      setWeeklyStats(stats);
      setMonthSchedule(sched);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async () => {
    try {
      const values = await createForm.validateFields();
      await trainingApi.createPlan({
        ...values,
        estimatedDuration: values.estimatedDuration,
        scheduledDate: values.scheduledDate.format("YYYY-MM-DD"),
        isRecurring: values.isRecurring || false,
        exercises: selectedExercises.length > 0 ? selectedExercises : undefined,
      });
      message.success("创建成功");
      setCreateOpen(false);
      createForm.resetFields();
      setSelectedExercises([]);
      fetchData();
    } catch {
      message.error("创建失败");
    }
  };

  const handleOpenEditPlan = async (planId: number) => {
    try {
      const detail = await trainingApi.getPlanDetail(planId);
      editForm.setFieldsValue({
        planName: detail.planName,
        planType: detail.planType,
        targetIntensity: detail.targetIntensity,
        estimatedDuration: detail.estimatedDuration,
        scheduledDate: detail.scheduledDate ? dayjs(detail.scheduledDate) : null,
        note: detail.note,
      });
      setEditingPlanId(planId);
      setEditOpen(true);
    } catch {
      message.error("获取计划详情失败");
    }
  };

  const handleEditPlan = async () => {
    if (!editingPlanId) return;
    try {
      const values = await editForm.validateFields();
      await trainingApi.updatePlan(editingPlanId, {
        ...values,
        scheduledDate: values.scheduledDate ? values.scheduledDate.format("YYYY-MM-DD") : undefined,
      });
      message.success("修改成功");
      setEditOpen(false);
      fetchData();
      if (detailOpen && detailData?.planId === editingPlanId) {
        handleViewDetail(editingPlanId);
      }
    } catch {
      message.error("修改失败");
    }
  };

  const handleLoadCategoryData = async () => {
    try {
      const [muscles, types, equipment, forceTypes, mechanics] =
        await Promise.all([
          exerciseApi.getMuscleCategories(),
          exerciseApi.getTypeCategories(),
          exerciseApi.getEquipmentCategories(),
          exerciseApi.getForceTypeCategories(),
          exerciseApi.getMechanicsCategories(),
        ]);
      setCatMuscles(muscles);
      setCatTypes(types);
      setCatEquipment(equipment);
      setCatForceTypes(forceTypes);
      setCatMechanics(mechanics);
    } catch {
      /* ignore */
    }
  };

  const handleOpenCustomExercise = () => {
    handleLoadCategoryData();
    customExerciseForm.resetFields();
    setInstructionsInput([""]);
    setCustomExerciseOpen(true);
  };

  const handleAddCustomInstruction = () => {
    setInstructionsInput((prev) => [...prev, ""]);
  };

  const handleRemoveCustomInstruction = (idx: number) => {
    setInstructionsInput((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleChangeCustomInstruction = (idx: number, value: string) => {
    setInstructionsInput((prev) => {
      const next = [...prev];
      next[idx] = value;
      return next;
    });
  };

  const handleSaveCustomExercise = async () => {
    try {
      const values = await customExerciseForm.validateFields();
      const filteredInstructions = instructionsInput
        .map((s) => s.trim())
        .filter(Boolean);
      if (filteredInstructions.length === 0) {
        message.warning("请至少输入一个动作要领步骤");
        return;
      }
      const result = await exerciseApi.createCustomExercise({
        nameCn: values.nameCn,
        nameEn: values.nameEn || undefined,
        targetMuscle: values.targetMuscle,
        exerciseType: values.exerciseType || undefined,
        difficulty: values.difficulty || undefined,
        equipment: values.equipment || undefined,
        forceType: values.forceType || undefined,
        mechanics: values.mechanics || undefined,
        helperMuscles: values.helperMuscles || undefined,
        instructions: filteredInstructions,
      });
      // 自动添加到当前计划
      setSelectedExercises((prev) => [
        ...prev,
        {
          exerciseId: result.exerciseId,
          sets: values.sets ?? 3,
          reps: values.reps ?? 10,
          weight: values.weight || undefined,
        },
      ]);
      message.success("自定义动作已保存并添加到计划");
      setCustomExerciseOpen(false);
      customExerciseForm.resetFields();
      setInstructionsInput([""]);
    } catch (e: any) {
      if (e?.errorFields) return; // form validation
      message.error("保存失败");
    }
  };

  const handleCompletePlan = async () => {
    if (!selectedPlanId) {
      message.error("请先选择计划");
      return;
    }
    try {
      const values = await completeForm.validateFields();
      await trainingApi.completePlan(selectedPlanId, {
        ...values,
        completedDate: values.completedDate?.format("YYYY-MM-DD"),
      });
      message.success("完成记录成功");
      setCompleteOpen(false);
      completeForm.resetFields();
      fetchData();
    } catch (e: any) {
      message.error(e.message || "记录失败");
    }
  };

  const handleDeletePlan = async (planId: number) => {
    Modal.confirm({
      title: "确认删除",
      content: "确定要删除该训练计划吗？相关训练记录也会被一并删除。",
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await trainingApi.deletePlan(planId);
          message.success("删除成功");
          fetchData();
        } catch {
          message.error("删除失败");
        }
      },
    });
  };

  const handleViewDetail = async (planId: number) => {
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const detail = await trainingApi.getPlanDetail(planId);
      setDetailData(detail);
      const schedItem = monthSchedule.find((s) => s.planId === planId);
      setDetailPlanInfo(
        schedItem
          ? {
              isRecurring: schedItem.isRecurring,
              isLastInGroup: schedItem.isLastInGroup,
            }
          : null,
      );
    } catch {
      message.error("获取详情失败");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleAddExercisesToDetail = async (exercises: PlanExerciseInput[]) => {
    if (!detailData) return;
    try {
      for (const ex of exercises) {
        await trainingApi.addPlanExercise(detailData.planId, ex);
      }
      message.success("添加成功");
      setDetailExercisePickerOpen(false);
      // 重新加载详情
      handleViewDetail(detailData.planId);
    } catch {
      message.error("添加失败");
    }
  };

  const handleAddCustomExerciseToDetail = async () => {
    if (!detailData) return;
    if (!detailCustomName.trim()) {
      message.warning("请输入动作名称");
      return;
    }
    try {
      await trainingApi.addPlanExercise(detailData.planId, {
        customName: detailCustomName.trim(),
        sets: detailCustomSets,
        reps: detailCustomReps,
      });
      message.success("添加成功");
      setDetailCustomName("");
      handleViewDetail(detailData.planId);
    } catch {
      message.error("添加失败");
    }
  };

  const handleDeleteExerciseFromDetail = async (exerciseId: number) => {
    try {
      await trainingApi.deletePlanExercise(exerciseId);
      message.success("删除成功");
      if (detailData) {
        setDetailData((prev) =>
          prev
            ? {
                ...prev,
                exercises: prev.exercises.filter((e) => e.id !== exerciseId),
              }
            : prev,
        );
      }
    } catch {
      message.error("删除失败");
    }
  };

  const getTypeTag = (type: string) => {
    const colors: Record<string, string> = {
      strength: "#F59E0B",
      cardio: "#10B981",
      flexibility: "#0EA5E9",
    };
    const labels: Record<string, string> = {
      strength: "力量",
      cardio: "有氧",
      flexibility: "柔韧",
    };
    return <Tag color={colors[type] || "default"}>{labels[type] || type}</Tag>;
  };

  const getIntensityTag = (intensity: string) => {
    const colors: Record<string, string> = {
      low: "#06B6D4",
      medium: "#F59E0B",
      high: "#EF4444",
    };
    return <Tag color={colors[intensity] || "default"}>{intensity}</Tag>;
  };

  return (
    <div
      className="fitagent-page-enter"
      style={{ padding: isMobile ? 12 : 24 }}
    >
      <style>{`
        .training-calendar .ant-picker-cell-inner { overflow: hidden; max-width: 100%; }
        .training-calendar .ant-picker-cell { overflow: hidden; }
        .training-calendar .ant-picker-calendar-date-content { height: auto !important; min-height: 100px; }
        @media (max-width: 767px) {
          .training-calendar .ant-picker-calendar-header { flex-wrap: wrap; }
          .training-calendar .ant-picker-cell-content { height: auto; }
          .training-calendar .ant-picker-date-panel .ant-picker-body th { font-size: 12px; padding: 6px 0; }
          .training-calendar .ant-picker-cell-inner { padding: 0; }
          .training-calendar .ant-picker-content { font-size: 13px; }
          .fitagent-page-enter .ant-modal { padding-bottom: 0; }
          .fitagent-page-enter .ant-modal-body { padding: 16px; max-height: 80vh; overflow-y: auto; }
        }
      `}</style>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <span
          className="fitagent-icon-badge"
          style={{ background: "#FFF7ED", color: "#F59E0B" }}
        >
          <Dumbbell size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>
          训练计划
        </Typography.Title>
      </div>

      <Row gutter={[isMobile ? 8 : 12, isMobile ? 8 : 12]}>
        <Col xs={12} sm={6} md={6}>
          <div
            className="fitagent-card-hover"
            style={{
              padding: isMobile ? 12 : 16,
              borderRadius: 6,
              background: "#F0FDF4",
              border: "1px solid #86EFAC",
              height: "100%",
            }}
          >
            <Typography.Text
              type="secondary"
              style={{ fontSize: isMobile ? 12 : 13 }}
            >
              本周训练
            </Typography.Text>
            <div
              style={{
                fontSize: isMobile ? 22 : 28,
                fontWeight: 700,
                color: "#10B981",
                marginTop: 8,
              }}
            >
              {loading ? "-" : `${weeklyStats?.weeklyCount || 0}`}
              <span
                style={{
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 500,
                  marginLeft: 4,
                }}
              >
                次
              </span>
            </div>
          </div>
        </Col>
        <Col xs={12} sm={6} md={6}>
          <div
            className="fitagent-card-hover"
            style={{
              padding: isMobile ? 12 : 16,
              borderRadius: 6,
              background: "#F5F5F5",
              border: "1px solid #e8e8e8",
              height: "100%",
            }}
          >
            <Typography.Text
              type="secondary"
              style={{ fontSize: isMobile ? 12 : 13 }}
            >
              本周时长
            </Typography.Text>
            <div
              style={{
                fontSize: isMobile ? 22 : 28,
                fontWeight: 700,
                marginTop: 8,
              }}
            >
              {loading ? "-" : `${weeklyStats?.weeklyHours || 0}`}
              <span
                style={{
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 500,
                  marginLeft: 4,
                }}
              >
                小时
              </span>
            </div>
          </div>
        </Col>
        <Col xs={12} sm={6} md={6}>
          <div
            className="fitagent-card-hover"
            style={{
              padding: isMobile ? 12 : 16,
              borderRadius: 6,
              background: "#FFF7ED",
              border: "1px solid #FED7AA",
              height: "100%",
            }}
          >
            <Typography.Text
              type="secondary"
              style={{ fontSize: isMobile ? 12 : 13 }}
            >
              消耗热量
            </Typography.Text>
            <div
              style={{
                fontSize: isMobile ? 22 : 28,
                fontWeight: 700,
                color: "#F59E0B",
                marginTop: 8,
              }}
            >
              {loading ? "-" : `${weeklyStats?.weeklyCalories || 0}`}
              <span
                style={{
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 500,
                  marginLeft: 4,
                }}
              >
                kcal
              </span>
            </div>
          </div>
        </Col>
        <Col xs={12} sm={6} md={6}>
          <div
            className="fitagent-card-hover"
            style={{
              padding: isMobile ? 12 : 16,
              borderRadius: 6,
              background: "#F5F3FF",
              border: "1px solid #DDD6FE",
              height: "100%",
            }}
          >
            <Typography.Text
              type="secondary"
              style={{ fontSize: isMobile ? 12 : 13 }}
            >
              连续训练
            </Typography.Text>
            <div
              style={{
                fontSize: isMobile ? 22 : 28,
                fontWeight: 700,
                color: "#8B5CF6",
                marginTop: 8,
              }}
            >
              {loading ? "-" : `${weeklyStats?.streakDays || 0}`}
              <span
                style={{
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 500,
                  marginLeft: 4,
                }}
              >
                天
              </span>
            </div>
          </div>
        </Col>
      </Row>

      <div
        className="fitagent-trend-panel"
        style={{
          marginTop: isMobile ? 16 : 24,
          padding: isMobile ? 12 : 16,
        }}
      >
        <div className="fitagent-trend-toolbar">
          <div>
            <Typography.Text strong className="fitagent-trend-title" style={{ fontSize: isMobile ? 14 : 16 }}>
              训练趋势
            </Typography.Text>
            <div>
              <Typography.Text className="fitagent-trend-subtitle">
                聚焦训练时长与热量消耗，快速判断最近执行状态
              </Typography.Text>
            </div>
          </div>
          <Radio.Group
            className="fitagent-trend-radio"
            value={trendDays}
            onChange={(e) => setTrendDays(e.target.value)}
            size="small"
          >
            <Radio.Button value={7}>近7天</Radio.Button>
            <Radio.Button value={14}>近14天</Radio.Button>
            <Radio.Button value={30}>近30天</Radio.Button>
          </Radio.Group>
        </div>

        <Checkbox.Group
          className="fitagent-trend-metrics"
          value={activeMetrics}
          onChange={(vals: any[]) => setActiveMetrics(vals)}
        >
          <Space wrap size={8}>
            <Checkbox value="duration">时长</Checkbox>
            <Checkbox value="caloriesBurned">消耗热量</Checkbox>
          </Space>
        </Checkbox.Group>

        <div className="fitagent-chart-shell">
        <ResponsiveContainer width="100%" height={isMobile ? 200 : 260}>
          <LineChart data={trendLoading ? [] : trendData}>
            <CartesianGrid strokeDasharray="4 4" stroke="#dbeafe" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: isMobile ? 11 : 12, fill: "#64748b" }}
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: isMobile ? 11 : 12, fill: "#64748b" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: isMobile ? 11 : 12, fill: "#64748b" }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 16,
                border: "1px solid #dbeafe",
                boxShadow: "0 14px 32px rgba(14, 165, 233, 0.12)",
                background: "rgba(255,255,255,0.96)",
              }}
              labelStyle={{ color: "#0f172a", fontWeight: 600, marginBottom: 6 }}
              itemStyle={{ color: "#334155" }}
              formatter={(value: any, name: any) => {
                const labels: Record<string, string> = {
                  duration: "时长",
                  caloriesBurned: "消耗热量",
                  planCount: "计划数",
                };
                const units: Record<string, string> = {
                  duration: " 分钟",
                  caloriesBurned: " kcal",
                };
                return [`${value}${units[name] || ""}`, labels[name] || name];
              }}
            />
            {activeMetrics.includes("duration") && (
              <Line
                type="monotone"
                yAxisId="left"
                dataKey="duration"
                name="duration"
                stroke="#10B981"
                strokeWidth={3}
                dot={{ r: 0 }}
                activeDot={{ r: 5, strokeWidth: 0, fill: "#10B981" }}
                {...sharedTrendLineMotion}
              />
            )}
            {activeMetrics.includes("caloriesBurned") && (
              <Line
                type="monotone"
                yAxisId="right"
                dataKey="caloriesBurned"
                name="caloriesBurned"
                stroke="#F59E0B"
                strokeWidth={3}
                dot={{ r: 0 }}
                activeDot={{ r: 5, strokeWidth: 0, fill: "#F59E0B" }}
                {...sharedTrendLineMotion}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
        </div>
      </div>

      <div
        style={{
          marginTop: isMobile ? 16 : 24,
          padding: isMobile ? 12 : 16,
          borderRadius: 6,
          background: "#F5F5F5",
          border: "1px solid #e8e8e8",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 12,
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              size="small"
              icon={<LeftOutlined />}
              onClick={() => setCurrentMonth((m) => m.subtract(1, "month"))}
            />
            <Typography.Text strong style={{ fontSize: isMobile ? 14 : 16 }}>
              {currentMonth.format("YYYY年M月")}
            </Typography.Text>
            <Button
              size="small"
              icon={<RightOutlined />}
              onClick={() => setCurrentMonth((m) => m.add(1, "month"))}
            />
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateOpen(true)}
            size={isMobile ? "small" : "middle"}
          >
            新建计划
          </Button>
        </div>

        <Calendar
          className="training-calendar"
          fullscreen={!isMobile}
          mode="month"
          value={currentMonth}
          onSelect={(date) => {
            if (isMobile) {
              setSelectedCalendarDate(date.format("YYYY-MM-DD"));
            }
          }}
          onPanelChange={(_, mode) => {
            if (mode === "month") setCurrentMonth(_);
          }}
          cellRender={(date) => {
            const dateStr = date.format("YYYY-MM-DD");
            const dayPlans = monthSchedule.filter((s) => s.date === dateStr);
            const isToday = date.isSame(dayjs(), "day");
            const isCurrentMonth = date.month() === currentMonth.month();
            const hasCompleted = dayPlans.some((p) => p.status === "completed");
            const isFuture = date.isAfter(dayjs(), "day");
            const isSelected = isMobile && selectedCalendarDate === dateStr;

            if (isMobile) {
              return (
                <div
                  style={{
                    minHeight: 82,
                    height: "100%",
                    padding: "6px 8px",
                    position: "relative",
                    borderRadius: 12,
                    cursor: "pointer",
                    border: isSelected
                      ? "1px solid #38bdf8"
                      : dayPlans.length > 0
                        ? "1px solid #dbeafe"
                        : "1px solid transparent",
                    background: isSelected
                      ? "linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%)"
                      : dayPlans.length > 0
                        ? "linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)"
                        : isCurrentMonth
                          ? "#fafcff"
                          : "#f8fafc",
                    boxShadow: isSelected ? "0 10px 24px rgba(14, 165, 233, 0.12)" : "none",
                    opacity: isCurrentMonth ? 1 : 0.58,
                    display: "flex",
                    flexDirection: "column",
                    gap: 6,
                  }}
                >
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: isToday || isSelected ? 700 : 500,
                      color: isToday ? "#0284c7" : "#0f172a",
                    }}
                  >
                    {date.date()}
                  </div>
                  {dayPlans.length > 0 ? (
                    <>
                      <div
                        style={{
                          display: "inline-flex",
                          alignSelf: "flex-start",
                          padding: "2px 8px",
                          borderRadius: 999,
                          background: hasCompleted ? "#dcfce7" : "#e0f2fe",
                          color: hasCompleted ? "#166534" : "#0369a1",
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        {dayPlans.length} 项计划
                      </div>
                    </>
                  ) : (
                    <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 4 }}>
                      暂无计划
                    </div>
                  )}
                </div>
              );
            }

            if (dayPlans.length === 0) {
              return (
                <div
                  style={{
                    minHeight: isMobile ? 80 : 120,
                    height: "100%",
                    borderLeft: isToday ? "3px solid #10B981" : "none",
                    padding: "4px 6px",
                    background:
                      isCurrentMonth && !isToday ? "#FAFFFE" : undefined,
                    width: "100%",
                  }}
                >
                  <div
                    style={{
                      fontWeight: isToday ? 700 : 400,
                      color: isToday
                        ? "#10B981"
                        : !isCurrentMonth
                          ? "#ccc"
                          : undefined,
                      fontSize: isMobile ? 14 : 16,
                    }}
                  >
                    {date.date()}
                  </div>
                </div>
              );
            }

            return (
              <div
                style={{
                  minHeight: isMobile ? 80 : 120,
                  height: "100%",
                  borderLeft: isToday
                    ? "3px solid #10B981"
                    : hasCompleted
                      ? "3px solid #10B981"
                      : "none",
                  padding: "4px 6px",
                  overflow: "hidden",
                  background:
                    isCurrentMonth && !isToday ? "#FAFFFE" : undefined,
                  width: "100%",
                }}
              >
                <div
                  style={{
                    fontWeight: isToday ? 700 : 400,
                    color: isToday ? "#10B981" : undefined,
                    fontSize: isMobile ? 14 : 16,
                    marginBottom: 4,
                  }}
                >
                  {date.date()}
                </div>
                {dayPlans.slice(0, 3).map((item) => (
                  <div
                    key={item.planId}
                    style={{
                      marginTop: 0,
                      marginBottom: 4,
                      padding: "6px 8px",
                      borderRadius: 6,
                      fontSize: isMobile ? 12 : 13,
                      background:
                        item.status === "completed" ? "#F0FDF4" : "#F5F5F5",
                      border:
                        item.status === "completed"
                          ? "1px solid #86EFAC"
                          : "1px solid #e8e8e8",
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    <div
                      style={{ display: "flex", alignItems: "center", gap: 6 }}
                    >
                      {item.status === "completed" && (
                        <CheckOutlined
                          style={{
                            color: "#10B981",
                            fontSize: isMobile ? 12 : 14,
                            flexShrink: 0,
                          }}
                        />
                      )}
                      <span
                        style={{
                          display: "inline-block",
                          padding: "2px 8px",
                          borderRadius: 4,
                          fontSize: isMobile ? 11 : 12,
                          lineHeight: "18px",
                          background: (() => {
                            const colors: Record<string, string> = {
                              strength: "#F59E0B20",
                              cardio: "#10B98120",
                              flexibility: "#0EA5E920",
                            };
                            return colors[item.planType] || "#eee";
                          })(),
                          color: (() => {
                            const colors: Record<string, string> = {
                              strength: "#F59E0B",
                              cardio: "#10B981",
                              flexibility: "#0EA5E9",
                            };
                            return colors[item.planType] || "#666";
                          })(),
                          flexShrink: 0,
                          fontWeight: 600,
                        }}
                      >
                        {(() => {
                          const labels: Record<string, string> = {
                            strength: "力量",
                            cardio: "有氧",
                            flexibility: "柔韧",
                          };
                          return labels[item.planType] || item.planType;
                        })()}
                      </span>
                      <span
                        style={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          cursor: "pointer",
                          flex: 1,
                          minWidth: 0,
                          fontWeight: 500,
                        }}
                        onClick={() =>
                          item.planId &&
                          item.planId > 0 &&
                          handleViewDetail(item.planId)
                        }
                      >
                        {item.planName}
                      </span>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: 12,
                        justifyContent: "flex-start",
                        flexWrap: "wrap",
                      }}
                    >
                      <span
                        style={{
                          color: "#1677ff",
                          cursor: "pointer",
                          fontSize: isMobile ? 12 : 13,
                          lineHeight: "18px",
                          fontWeight: 500,
                        }}
                        onClick={() => item.planId && handleViewDetail(item.planId)}
                      >
                        详情
                      </span>
                      <span
                        style={{
                          color: "#1677ff",
                          cursor: "pointer",
                          fontSize: isMobile ? 12 : 13,
                          lineHeight: "18px",
                          fontWeight: 500,
                        }}
                        onClick={() => item.planId && handleOpenEditPlan(item.planId)}
                      >
                        编辑
                      </span>
                      {item.status !== "completed" && (
                        <span
                          style={{
                            color: isFuture ? "#ccc" : "#1677ff",
                            cursor: isFuture ? "not-allowed" : "pointer",
                            fontSize: isMobile ? 12 : 13,
                            lineHeight: "18px",
                            fontWeight: 500,
                          }}
                          onClick={
                            isFuture
                              ? undefined
                              : () => {
                                  setSelectedPlanId(item.planId!);
                                  setCompleteOpen(true);
                                }
                          }
                        >
                          {isFuture ? "未到" : "打卡"}
                        </span>
                      )}
                      <span
                        style={{
                          color: "#ff4d4f",
                          cursor: "pointer",
                          fontSize: isMobile ? 12 : 13,
                          lineHeight: "18px",
                          fontWeight: 500,
                        }}
                        onClick={() =>
                          item.planId && handleDeletePlan(item.planId)
                        }
                      >
                        删除
                      </span>
                      {item.isRecurring && item.isLastInGroup && (
                        <span
                          style={{
                            color: "#1677ff",
                            cursor: "pointer",
                            fontSize: isMobile ? 12 : 13,
                            lineHeight: "18px",
                            fontWeight: 500,
                          }}
                          onClick={() =>
                            item.planId && handleRenewPlan(item.planId)
                          }
                        >
                          续期
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {dayPlans.length > 3 && (
                  <div
                    style={{
                      fontSize: 12,
                      color: "#999",
                      marginTop: 2,
                      fontWeight: 500,
                    }}
                  >
                    +{dayPlans.length - 3} 更多
                  </div>
                )}
              </div>
            );
          }}
        />

        {isMobile && (
          <div style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
              <div>
                <Typography.Text strong style={{ fontSize: 15 }}>
                  {dayjs(selectedCalendarDate).format('YYYY-MM-DD')} 训练详情
                </Typography.Text>
                <div style={{ marginTop: 6 }}>
                  <Typography.Text type="secondary">
                    {monthSchedule.filter(s => s.date === selectedCalendarDate).length} 项计划
                  </Typography.Text>
                </div>
              </div>
            </div>

            {(() => {
              const selectedPlans = monthSchedule.filter(s => s.date === selectedCalendarDate);
              if (selectedPlans.length === 0) {
                return (
                  <Card
                    size="small"
                    style={{
                      borderRadius: 20,
                      border: '1px dashed #cbd5e1',
                      background: '#f8fafc',
                    }}
                    styles={{ body: { padding: 20, textAlign: 'center' } }}
                  >
                    <Typography.Text type="secondary">
                      这一天还没有训练计划，可以直接点击该日期右上角的加号快速补充。
                    </Typography.Text>
                    <div style={{ marginTop: 12 }}>
                      <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                        createForm.setFieldsValue({ scheduledDate: dayjs(selectedCalendarDate) });
                        setCreateOpen(true);
                      }}>
                        为这一天添加计划
                      </Button>
                    </div>
                  </Card>
                );
              }

              return (
                <Row gutter={[12, 12]}>
                  {selectedPlans.map((item) => {
                    const isFuture = dayjs(selectedCalendarDate).isAfter(dayjs(), 'day');
                    const hasCompleted = item.status === "completed";
                    return (
                      <Col xs={24} key={item.planId}>
                        <Card
                          className="fitagent-card-hover"
                          size="small"
                          style={{
                            borderRadius: 20,
                            border: hasCompleted ? '1px solid #86EFAC' : '1px solid #dbeafe',
                            background: hasCompleted ? '#F0FDF4' : 'linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)',
                          }}
                          styles={{ body: { padding: 16 } }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                            <div style={{ minWidth: 0 }}>
                              <Space size={8} wrap>
                                {getTypeTag(item.planType)}
                                {getIntensityTag(item.intensity)}
                                <Typography.Text type="secondary">{item.duration} 分钟</Typography.Text>
                              </Space>
                              <Typography.Title level={5} style={{ margin: '10px 0 0', fontSize: 18 }}>
                                {item.planName}
                              </Typography.Title>
                            </div>
                            <Avatar style={{ backgroundColor: hasCompleted ? '#10B981' : '#F59E0B', flexShrink: 0 }}>
                              <Dumbbell size={16} />
                            </Avatar>
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
                            <Button size="small" onClick={() => item.planId && handleViewDetail(item.planId)}>
                              详情
                            </Button>
                            <Button size="small" icon={<EditOutlined />} onClick={() => item.planId && handleOpenEditPlan(item.planId)}>
                              编辑
                            </Button>
                            {!hasCompleted && (
                              <Button
                                size="small"
                                type="primary"
                                disabled={isFuture}
                                onClick={
                                  isFuture
                                    ? undefined
                                    : () => {
                                        setSelectedPlanId(item.planId!);
                                        setCompleteOpen(true);
                                      }
                                }
                              >
                                {isFuture ? "未到" : "打卡"}
                              </Button>
                            )}
                            {item.isRecurring && item.isLastInGroup && (
                              <Button
                                size="small"
                                icon={<SyncOutlined />}
                                onClick={() => item.planId && handleRenewPlan(item.planId)}
                              >
                                续期
                              </Button>
                            )}
                            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => item.planId && handleDeletePlan(item.planId)}>
                              删除
                            </Button>
                          </div>
                        </Card>
                      </Col>
                    );
                  })}
                </Row>
              );
            })()}
          </div>
        )}
      </div>

      <Modal
        title="创建训练计划"
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false);
          setSelectedExercises([]);
        }}
        onOk={handleCreatePlan}
        okText="创建"
        cancelText="取消"
        width={isMobile ? "100%" : undefined}
        style={isMobile ? { top: 0, margin: 0, maxWidth: "100%" } : undefined}
      >
        <Form form={createForm} layout="vertical" style={{ marginTop: 16 }} initialValues={{ estimatedDuration: 60, scheduledDate: dayjs() }}>
          <Form.Item
            name="planName"
            label="计划名称"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="planType"
            label="训练类型"
            rules={[{ required: true }]}
          >
            <Select options={planTypes} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={12}>
              <Form.Item
                name="targetIntensity"
                label="目标强度"
                rules={[{ required: true }]}
              >
                <Select options={intensities} />
              </Form.Item>
            </Col>
            <Col xs={12}>
              <Form.Item
                name="estimatedDuration"
                label="预计时长"
                rules={[{ required: true }]}
              >
                <Space.Compact style={{ width: "100%" }}>
                  <InputNumber style={{ flex: 1 }} />
                  <Button disabled>分钟</Button>
                </Space.Compact>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="scheduledDate"
            label="计划日期"
            rules={[{ required: true }]}
          >
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="isRecurring"
            valuePropName="checked"
            initialValue={false}
          >
            <Checkbox>
              <SyncOutlined /> 每周循环（按周几自动复用）
            </Checkbox>
          </Form.Item>
          <Form.Item label="训练动作">
            <Space direction="vertical" style={{ width: "100%" }} size={8}>
              <Space wrap>
                <Button
                  icon={<PlusOutlined />}
                  onClick={() => setExercisePickerOpen(true)}
                >
                  从动作库选择
                </Button>
                <Button
                  type="dashed"
                  icon={<PlusOutlined />}
                  onClick={handleOpenCustomExercise}
                >
                  添加自定义
                </Button>
              </Space>
              {selectedExercises.length > 0 && (
                <Space wrap>
                  {selectedExercises.map((sel, idx) => {
                    const exName = sel.customName || `#${sel.exerciseId}`;
                    return (
                      <Tag
                        key={`${sel.exerciseId || sel.customName}-${idx}`}
                        closable
                        onClose={() =>
                          setSelectedExercises((prev) =>
                            prev.filter((_, i) => i !== idx),
                          )
                        }
                      >
                        {exName} · {sel.sets ?? 3}组×{sel.reps ?? 10}次
                        {sel.weight ? ` · ${sel.weight}kg` : ""}
                        {sel.customName && (
                          <Tag color="default" style={{ marginLeft: 4 }}>
                            自定义
                          </Tag>
                        )}
                      </Tag>
                    );
                  })}
                </Space>
              )}
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑训练计划"
        open={editOpen}
        onCancel={() => {
          setEditOpen(false);
          setEditingPlanId(null);
          editForm.resetFields();
        }}
        onOk={handleEditPlan}
        okText="保存"
        cancelText="取消"
        width={isMobile ? "100%" : undefined}
        style={isMobile ? { top: 0, margin: 0, maxWidth: "100%" } : undefined}
      >
        <Form form={editForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="planName"
            label="计划名称"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="planType"
            label="训练类型"
            rules={[{ required: true }]}
          >
            <Select options={planTypes} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={12}>
              <Form.Item
                name="targetIntensity"
                label="目标强度"
                rules={[{ required: true }]}
              >
                <Select options={intensities} />
              </Form.Item>
            </Col>
            <Col xs={12}>
              <Form.Item
                name="estimatedDuration"
                label="预计时长"
                rules={[{ required: true }]}
              >
                <Space.Compact style={{ width: "100%" }}>
                  <InputNumber style={{ flex: 1 }} />
                  <Button disabled>分钟</Button>
                </Space.Compact>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="scheduledDate"
            label="计划日期"
            rules={[{ required: true }]}
          >
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="完成训练"
        open={completeOpen}
        onCancel={() => {
          setCompleteOpen(false);
          completeForm.resetFields();
        }}
        onOk={handleCompletePlan}
        okText="提交"
        cancelText="取消"
        width={isMobile ? "100%" : undefined}
        style={isMobile ? { top: 0, margin: 0, maxWidth: "100%" } : undefined}
      >
        <Form
          form={completeForm}
          layout="vertical"
          style={{ marginTop: 16 }}
          initialValues={{
            completedDate: dayjs(),
            actualDuration: 60,
            caloriesBurned: 0,
          }}
        >
          <Form.Item
            name="actualDuration"
            label="实际时长"
            rules={[{ required: true }]}
          >
            <Space.Compact style={{ width: "100%" }}>
              <InputNumber style={{ flex: 1 }} />
              <Button disabled>分钟</Button>
            </Space.Compact>
          </Form.Item>
          <Form.Item name="caloriesBurned" label="消耗热量">
            <Space.Compact style={{ width: "100%" }}>
              <InputNumber style={{ flex: 1 }} />
              <Button disabled>kcal</Button>
            </Space.Compact>
          </Form.Item>
          <Form.Item name="completedDate" label="完成日期">
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>

      <ExercisePicker
        open={exercisePickerOpen}
        onClose={() => setExercisePickerOpen(false)}
        onConfirm={(exercises) => {
          setSelectedExercises(exercises);
          setExercisePickerOpen(false);
        }}
        initialExercises={selectedExercises}
      />

      {/* 自定义动作创建 Modal */}
      <Modal
        title="创建自定义动作"
        open={customExerciseOpen}
        onCancel={() => {
          setCustomExerciseOpen(false);
          customExerciseForm.resetFields();
          setInstructionsInput([""]);
        }}
        onOk={handleSaveCustomExercise}
        okText="保存并添加到计划"
        cancelText="取消"
        width={isMobile ? "100%" : 640}
        style={isMobile ? { top: 0, margin: 0, maxWidth: "100%" } : undefined}
      >
        <Form
          form={customExerciseForm}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Row gutter={16}>
            <Col xs={12}>
              <Form.Item
                name="nameCn"
                label="动作名称"
                rules={[{ required: true }]}
              >
                <Input placeholder="如：俯卧撑" />
              </Form.Item>
            </Col>
            <Col xs={12}>
              <Form.Item name="nameEn" label="英文名称">
                <Input placeholder="如：Push-up" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={12}>
              <Form.Item
                name="targetMuscle"
                label="目标肌肉"
                rules={[{ required: true }]}
              >
                <Select placeholder="选择目标肌肉" showSearch>
                  {catMuscles.map((m) => (
                    <Select.Option key={m} value={m}>
                      {m}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={12}>
              <Form.Item name="helperMuscles" label="辅助肌群">
                <Input placeholder="逗号分隔" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={8}>
              <Form.Item name="difficulty" label="难度">
                <Select placeholder="选择难度" allowClear>
                  {["初级", "中级", "专家级"].map((d) => (
                    <Select.Option key={d} value={d}>
                      {d}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={8}>
              <Form.Item name="exerciseType" label="动作类型">
                <Select placeholder="选择类型" allowClear>
                  {catTypes.map((t) => (
                    <Select.Option key={t} value={t}>
                      {t}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={8}>
              <Form.Item name="equipment" label="器械">
                <Select placeholder="选择器械" allowClear>
                  {catEquipment.map((e) => (
                    <Select.Option key={e} value={e}>
                      {e}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={12}>
              <Form.Item name="forceType" label="发力类型">
                <Select placeholder="选择发力类型" allowClear>
                  {catForceTypes.map((f) => (
                    <Select.Option key={f} value={f}>
                      {f}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={12}>
              <Form.Item name="mechanics" label="力学类型">
                <Select placeholder="选择力学类型" allowClear>
                  {catMechanics.map((m) => (
                    <Select.Option key={m} value={m}>
                      {m}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Divider>训练参数</Divider>
          <Row gutter={16}>
            <Col xs={8}>
              <Form.Item
                name="sets"
                label="组数"
                initialValue={3}
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={20} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col xs={8}>
              <Form.Item
                name="reps"
                label="次数"
                initialValue={10}
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={100} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col xs={8}>
              <Form.Item name="weight" label="重量(kg)">
                <InputNumber min={0} step={0.5} style={{ width: "100%" }} />
              </Form.Item>
            </Col>
          </Row>
          <Divider>动作要领</Divider>
          {instructionsInput.map((step, idx) => (
            <Space key={idx} style={{ width: "100%", marginBottom: 8 }}>
              <Input.TextArea
                placeholder={`步骤 ${idx + 1}`}
                value={step}
                onChange={(e) =>
                  handleChangeCustomInstruction(idx, e.target.value)
                }
                rows={2}
                style={{ flex: 1 }}
              />
              {instructionsInput.length > 1 && (
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleRemoveCustomInstruction(idx)}
                />
              )}
            </Space>
          ))}
          <Button
            type="dashed"
            onClick={handleAddCustomInstruction}
            icon={<PlusOutlined />}
            style={{ width: "100%" }}
          >
            添加步骤
          </Button>
        </Form>
      </Modal>

      <ExercisePicker
        open={detailExercisePickerOpen}
        onClose={() => setDetailExercisePickerOpen(false)}
        onConfirm={(exercises) => handleAddExercisesToDetail(exercises)}
        initialExercises={[]}
      />

      <Modal
        title="计划详情"
        open={detailOpen}
        onCancel={() => {
          setDetailOpen(false);
          setDetailData(null);
          setEditingExerciseId(null);
          setEditingDraft(null);
        }}
        footer={null}
        width={isMobile ? "100%" : 600}
        style={isMobile ? { top: 0, margin: 0, maxWidth: "100%" } : undefined}
      >
        {detailLoading ? (
          <div style={{ textAlign: "center", padding: 40 }}>加载中...</div>
        ) : detailData ? (
          <Space direction="vertical" style={{ width: "100%" }} size={16}>
            <div>
              <Typography.Title level={5} style={{ margin: "0 0 8px" }}>
                {detailData.planName}
              </Typography.Title>
              <Space wrap>
                {getTypeTag(detailData.planType)}
                {detailData.targetIntensity &&
                  getIntensityTag(detailData.targetIntensity)}
                <Tag>{detailData.estimatedDuration} 分钟</Tag>
                <Tag
                  color={
                    detailData.status === "completed" ? "#10B981" : "#06B6D4"
                  }
                >
                  {detailData.status === "completed" ? "已完成" : "待完成"}
                </Tag>
              </Space>
            </div>
            {detailData.note && (
              <Typography.Text type="secondary">
                {detailData.note}
              </Typography.Text>
            )}
            {detailData.exercises.length > 0 ? (
              <List
                dataSource={detailData.exercises}
                renderItem={(ex: PlanExerciseItemOutput) => {
                  const isEditing = editingExerciseId === ex.id;
                  return (
                    <>
                      <List.Item>
                        <List.Item.Meta
                          avatar={
                            <Avatar style={{ backgroundColor: "#F59E0B" }}>
                              <Dumbbell size={16} />
                            </Avatar>
                          }
                          title={ex.customName || ex.nameCn || "自定义动作"}
                          description={
                            ex.exerciseId ? (
                              <div>
                                <Space wrap size={4}>
                                  <Tag color="blue">{ex.targetMuscle}</Tag>
                                  {ex.difficulty && <Tag>{ex.difficulty}</Tag>}
                                  {ex.forceType && (
                                    <Tag color="green">{ex.forceType}</Tag>
                                  )}
                                  {ex.mechanics && (
                                    <Tag color="purple">{ex.mechanics}</Tag>
                                  )}
                                  {ex.equipment && (
                                    <Tag color="orange">{ex.equipment}</Tag>
                                  )}
                                </Space>
                                {ex.helperMuscles && (
                                  <div
                                    style={{
                                      fontSize: 12,
                                      color: "#999",
                                      marginTop: 4,
                                    }}
                                  >
                                    辅助肌肉：{ex.helperMuscles}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <Tag color="default">自定义</Tag>
                            )
                          }
                        />
                        <div style={{ textAlign: "right", flexShrink: 0 }}>
                          {!isEditing && (
                            <>
                              <Typography.Text strong>
                                {ex.sets} 组 × {ex.reps} 次
                              </Typography.Text>
                              {ex.weight && (
                                <Typography.Text
                                  type="secondary"
                                  style={{ display: "block", fontSize: 12 }}
                                >
                                  {ex.weight} kg
                                </Typography.Text>
                              )}
                              <div>
                                <Button
                                  size="small"
                                  type="link"
                                  onClick={() => {
                                    setEditingExerciseId(ex.id);
                                    setEditingDraft({
                                      sets: ex.sets,
                                      reps: ex.reps,
                                      weight: ex.weight ?? null,
                                    });
                                  }}
                                >
                                  编辑
                                </Button>
                                <Popconfirm
                                  title="确认删除"
                                  description="确定要删除该动作吗？"
                                  onConfirm={() =>
                                    handleDeleteExerciseFromDetail(ex.id)
                                  }
                                  okText="删除"
                                  cancelText="取消"
                                  okButtonProps={{ danger: true }}
                                >
                                  <Button size="small" type="link" danger>
                                    删除
                                  </Button>
                                </Popconfirm>
                              </div>
                            </>
                          )}
                        </div>
                      </List.Item>
                      {isEditing && (
                        <List.Item
                          style={{
                            display: "block",
                            padding: "12px 16px",
                            background: "#FAFAFA",
                            borderRadius: 8,
                            marginBottom: 8,
                            border: "1px solid #e8e8e8",
                          }}
                        >
                          <Row gutter={16} style={{ marginBottom: 12 }}>
                            <Col xs={8}>
                              <Space.Compact style={{ width: "100%" }}>
                                <Button disabled size="small">组</Button>
                                <InputNumber
                                  size="middle"
                                  min={1}
                                  max={20}
                                  value={editingDraft?.sets ?? ex.sets}
                                  onChange={(v) =>
                                    setEditingDraft((prev) =>
                                      prev
                                        ? { ...prev, sets: v ?? prev.sets }
                                        : {
                                            sets: v ?? ex.sets,
                                            reps: ex.reps,
                                            weight: ex.weight ?? null,
                                          },
                                    )
                                  }
                                  style={{
                                    flex: 1,
                                    fontSize: 16,
                                    height: 40,
                                  }}
                                />
                              </Space.Compact>
                            </Col>
                            <Col xs={8}>
                              <Space.Compact style={{ width: "100%" }}>
                                <Button disabled size="small">次</Button>
                                <InputNumber
                                  size="middle"
                                  min={1}
                                  max={100}
                                  value={editingDraft?.reps ?? ex.reps}
                                  onChange={(v) =>
                                    setEditingDraft((prev) =>
                                      prev
                                        ? { ...prev, reps: v ?? prev.reps }
                                        : {
                                            sets: ex.sets,
                                            reps: v ?? ex.reps,
                                            weight: ex.weight ?? null,
                                          },
                                    )
                                  }
                                  style={{
                                    flex: 1,
                                    fontSize: 16,
                                    height: 40,
                                  }}
                                />
                              </Space.Compact>
                            </Col>
                            <Col xs={8}>
                              <Space.Compact style={{ width: "100%" }}>
                                <Button disabled size="small">kg</Button>
                                <InputNumber
                                  size="middle"
                                  min={0}
                                  max={500}
                                  step={0.5}
                                  value={
                                    editingDraft?.weight ?? ex.weight ?? undefined
                                  }
                                  onChange={(v) =>
                                    setEditingDraft((prev) =>
                                      prev
                                        ? { ...prev, weight: v }
                                        : {
                                            sets: ex.sets,
                                            reps: ex.reps,
                                            weight: v,
                                          },
                                    )
                                  }
                                  style={{
                                    flex: 1,
                                    fontSize: 16,
                                    height: 40,
                                  }}
                                  placeholder="-"
                                />
                              </Space.Compact>
                            </Col>
                          </Row>
                          <Space>
                            <Button
                              type="primary"
                              onClick={async () => {
                                const draft = editingDraft ?? {
                                  sets: ex.sets,
                                  reps: ex.reps,
                                  weight: ex.weight ?? null,
                                };
                                try {
                                  await trainingApi.updatePlanExercise(ex.id, {
                                    sets: draft.sets,
                                    reps: draft.reps,
                                    weight: draft.weight ?? undefined,
                                  });
                                  // 保存成功后写回 detailData
                                  setDetailData((prev) => {
                                    if (!prev) return prev;
                                    return {
                                      ...prev,
                                      exercises: prev.exercises.map((e) =>
                                        e.id === ex.id
                                          ? {
                                              ...e,
                                              sets: draft.sets,
                                              reps: draft.reps,
                                              weight: draft.weight,
                                            }
                                          : e,
                                      ),
                                    };
                                  });
                                  message.success("更新成功");
                                  setEditingExerciseId(null);
                                  setEditingDraft(null);
                                } catch {
                                  message.error("更新失败");
                                }
                              }}
                            >
                              保存
                            </Button>
                            <Button
                              onClick={() => {
                                setEditingExerciseId(null);
                                setEditingDraft(null);
                              }}
                            >
                              取消
                            </Button>
                          </Space>
                        </List.Item>
                      )}
                    </>
                  );
                }}
              />
            ) : (
              <Typography.Text type="secondary">暂无训练动作</Typography.Text>
            )}
            {detailData.status !== "completed" && (
              <div
                style={{ padding: "12px 0", borderTop: "1px dashed #e8e8e8" }}
              >
                <Typography.Text
                  type="secondary"
                  style={{ display: "block", marginBottom: 8 }}
                >
                  添加动作
                </Typography.Text>
                <Space direction="vertical" style={{ width: "100%" }} size={8}>
                  <Space wrap>
                    <Button
                      icon={<PlusOutlined />}
                      onClick={() => setDetailExercisePickerOpen(true)}
                    >
                      从动作库选择
                    </Button>
                    <Button
                      type="dashed"
                      icon={<PlusOutlined />}
                      onClick={handleAddCustomExerciseToDetail}
                    >
                      添加自定义
                    </Button>
                  </Space>
                  <Space wrap>
                    <Input
                      placeholder="自定义动作名称"
                      value={detailCustomName}
                      onChange={(e) => setDetailCustomName(e.target.value)}
                      style={{ width: 180 }}
                    />
                    <Space.Compact style={{ width: 70 }}>
                      <Button disabled size="small">组</Button>
                      <InputNumber
                        size="small"
                        min={1}
                        max={20}
                        value={detailCustomSets}
                        onChange={(v) => setDetailCustomSets(v ?? 3)}
                        style={{ flex: 1 }}
                      />
                    </Space.Compact>
                    <Space.Compact style={{ width: 70 }}>
                      <Button disabled size="small">次</Button>
                      <InputNumber
                        size="small"
                        min={1}
                        max={100}
                        value={detailCustomReps}
                        onChange={(v) => setDetailCustomReps(v ?? 10)}
                        style={{ flex: 1 }}
                      />
                    </Space.Compact>
                  </Space>
                </Space>
              </div>
            )}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                paddingTop: 8,
                marginTop: 8,
                borderTop: "1px solid #f0f0f0",
              }}
            >
              <Button
                onClick={() => {
                  setDetailOpen(false);
                  setDetailData(null);
                  setEditingExerciseId(null);
                  setEditingDraft(null);
                }}
              >
                关闭
              </Button>
              <Space>
                {detailPlanInfo?.isRecurring &&
                  detailPlanInfo?.isLastInGroup && (
                    <Button
                      type="primary"
                      icon={<SyncOutlined />}
                      onClick={() => {
                        handleRenewPlan(detailData!.planId);
                        setDetailOpen(false);
                      }}
                    >
                      续期
                    </Button>
                  )}
                <Button
                  danger
                  onClick={() => {
                    if (detailData) handleDeletePlan(detailData.planId);
                    setDetailOpen(false);
                  }}
                >
                  删除
                </Button>
              </Space>
            </div>
          </Space>
        ) : null}
      </Modal>
    </div>
  );
};

export default Training;
