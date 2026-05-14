import React, { useState, useEffect, useMemo } from "react";
import {
  Row,
  Col,
  Button,
  message,
  Input,
  List,
  Spin,
  Collapse,
  Popconfirm,
  Card,
  Space,
  Typography,
  Empty,
  Tag,
} from "antd";
import {
  SaveOutlined,
  ReloadOutlined,
  DeleteOutlined,
  CalendarOutlined,
  UndoOutlined,
  SearchOutlined,
  CopyOutlined,
} from "@ant-design/icons";
import { memoryApi, MemoryContent, DailyLog } from "../../services/memory";

const { TextArea } = Input;
const { Text } = Typography;

const MemoryManager: React.FC = () => {
  const [memory, setMemory] = useState<MemoryContent | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [logSearch, setLogSearch] = useState("");
  const [selectedLog, setSelectedLog] = useState<DailyLog | null>(null);
  const [logLoading, setLogLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeLogDate, setActiveLogDate] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchMemory = async () => {
    setLoading(true);
    try {
      const data = await memoryApi.get();
      setMemory(data);
      setEditingContent(data.content);
    } catch (error) {
      message.error("获取记忆失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await memoryApi.listLogs();
      const sorted = [...data].sort((a, b) => b.localeCompare(a));
      setLogs(sorted);
    } catch (error) {
      message.error("获取日志列表失败");
    }
  };

  const handleCopyLog = async () => {
    if (!selectedLog?.content) return;
    try {
      await navigator.clipboard.writeText(selectedLog.content);
      message.success("日志内容已复制");
    } catch (error) {
      message.error("复制失败");
    }
  };

  const handleSave = async () => {
    if (!hasChanges) return;
    setSaving(true);
    try {
      await memoryApi.update(editingContent);
      message.success("记忆已保存");
      await fetchMemory();
    } catch (error) {
      message.error("保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleViewLog = async (date: string) => {
    setLogLoading(true);
    setActiveLogDate(date);
    try {
      const data = await memoryApi.getLog(date);
      setSelectedLog(data);
    } catch (error) {
      message.error("获取日志失败");
    } finally {
      setLogLoading(false);
    }
  };

  const handleDeleteLog = async (date: string) => {
    try {
      await memoryApi.deleteLog(date);
      message.success("日志已删除");
      fetchLogs();
      if (activeLogDate === date) {
        setSelectedLog(null);
        setActiveLogDate(null);
      }
    } catch (error) {
      message.error("删除失败");
    }
  };

  const handleReset = () => {
    setEditingContent(memory?.content || "");
    message.info("已恢复到最近一次保存内容");
  };

  const hasChanges = editingContent !== (memory?.content ?? "");
  const lineCount = editingContent.split("\n").length;
  const charCount = editingContent.length;

  const filteredLogs = useMemo(
    () => logs.filter((d) => d.includes(logSearch)),
    [logs, logSearch],
  );

  return (
    <Row gutter={24}>
      <Col xs={24} lg={14}>
        <Card
          title={
            <Space>
              <span>长期记忆</span>
              {hasChanges ? (
                <Tag color="warning">未保存</Tag>
              ) : (
                <Tag color="success">已保存</Tag>
              )}
            </Space>
          }
          extra={
            <Space>
              <Button
                icon={<UndoOutlined />}
                onClick={handleReset}
                disabled={!hasChanges || loading}
              >
                放弃修改
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchMemory}
                disabled={loading}
              >
                刷新
              </Button>

                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSave}
                  loading={saving}
                  disabled={!hasChanges || loading}
                >
                  保存
                </Button>
              </Space>
            }
          >
            <Space style={{ marginBottom: 10 }} size={12}>
              <Text type="secondary">行数: {lineCount}</Text>
              <Text type="secondary">字符: {charCount}</Text>
              {memory?.last_updated && (
                <Text type="secondary">最后更新: {memory.last_updated}</Text>
              )}
              <Text type="secondary">快捷键: Ctrl/Cmd + S</Text>
            </Space>
            <Spin spinning={loading}>
              <TextArea
                value={editingContent}
                onChange={(e) => setEditingContent(e.target.value)}
                autoSize={{ minRows: 20, maxRows: 30 }}
                placeholder="这里是 MEMORY.md 的内容，支持直接编辑并保存。"
                style={{ fontFamily: "monospace", fontSize: 14 }}
              />
            </Spin>
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card
            title={
              <Space>
                <CalendarOutlined />
                <span>日志历史</span>
                <Tag>
                  {filteredLogs.length}/{logs.length}
                </Tag>
              </Space>
            }
            extra={
              <Button icon={<ReloadOutlined />} onClick={fetchLogs}>
                刷新
              </Button>
            }
          >
            <Input
              prefix={<SearchOutlined />}
              value={logSearch}
              onChange={(e) => setLogSearch(e.target.value)}
              placeholder="按日期筛选，例如 2026-05"
              allowClear
              style={{ marginBottom: 12 }}
            />
            <Spin spinning={logLoading}>
              <List
                dataSource={filteredLogs}
                style={{ maxHeight: "60vh", overflow: "auto" }}
                locale={{
                  emptyText: (
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description="暂无日志"
                    />
                  ),
                }}
                renderItem={(date) => (
                  <List.Item
                    actions={[
                      <Popconfirm
                        title="确认删除"
                        description={`确定要删除 ${date} 的日志吗？`}
                        onConfirm={() => handleDeleteLog(date)}
                      >
                        <Button
                          type="text"
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                        />
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <a
                          onClick={() => handleViewLog(date)}
                          style={{
                            cursor: "pointer",
                            color:
                              activeLogDate === date ? "#1677ff" : undefined,
                          }}
                        >
                          📅 {date}
                        </a>
                      }
                    />
                  </List.Item>
                )}
              />
            </Spin>

            {selectedLog && (
              <Collapse style={{ marginTop: 16 }}>
                <Collapse.Panel
                  header={`日志: ${selectedLog.date}`}
                  key="1"
                  extra={
                    <Space>
                      <Button
                        type="text"
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={handleCopyLog}
                      />
                      <Popconfirm
                        title="确认删除"
                        description={`确定要删除 ${selectedLog.date} 的日志吗？`}
                        onConfirm={() => handleDeleteLog(selectedLog.date)}
                      >
                        <Button
                          type="text"
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                        />
                      </Popconfirm>
                    </Space>
                  }
                >
                  <pre
                    style={{
                      whiteSpace: "pre-wrap",
                      background: "#f5f5f5",
                      padding: 12,
                      borderRadius: 4,
                      fontSize: 13,
                    }}
                  >
                    {selectedLog.content}
                  </pre>
                </Collapse.Panel>
              </Collapse>
            )}
          </Card>
        </Col>
      </Row>
  );
};

export default MemoryManager;
