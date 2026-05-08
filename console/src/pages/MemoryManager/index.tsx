import React, { useState, useEffect, useMemo } from 'react'
import { Row, Col, Button, message, Input, List, Spin, Collapse, Popconfirm, Card, Space, Typography, Empty, Switch, Tag } from 'antd'
import { SaveOutlined, ReloadOutlined, DeleteOutlined, CalendarOutlined, UndoOutlined, SearchOutlined, CopyOutlined, FileTextOutlined } from '@ant-design/icons'
import { memoryApi, MemoryContent, DailyLog, MemoryConfig } from '../../services/memory'

const { TextArea } = Input
const { Text } = Typography

const MemoryManager: React.FC = () => {
  const [memory, setMemory] = useState<MemoryContent | null>(null)
  const [editingContent, setEditingContent] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const [logSearch, setLogSearch] = useState('')
  const [selectedLog, setSelectedLog] = useState<DailyLog | null>(null)
  const [logLoading, setLogLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [activeLogDate, setActiveLogDate] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // Memory config state (heartbeat only)
  const [memoryConfig, setMemoryConfig] = useState<MemoryConfig>({
    heartbeat: { enabled: false, every: '6h', target: 'main', active_hours: null },
  })
  const [savingConfig, setSavingConfig] = useState(false)

  // HEARTBEAT.md 编辑
  const [heartbeatDoc, setHeartbeatDoc] = useState('')
  const [heartbeatDocLoading, setHeartbeatDocLoading] = useState(false)
  const [heartbeatDocSaving, setHeartbeatDocSaving] = useState(false)

  const fetchMemory = async () => {
    setLoading(true)
    try {
      const data = await memoryApi.get()
      setMemory(data)
      setEditingContent(data.content)
    } catch (error) {
      message.error('获取记忆失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchLogs = async () => {
    try {
      const data = await memoryApi.listLogs()
      const sorted = [...data].sort((a, b) => b.localeCompare(a))
      setLogs(sorted)
    } catch (error) {
      message.error('获取日志列表失败')
    }
  }

  const fetchConfig = async () => {
    try {
      const cfg = await memoryApi.getConfig()
      setMemoryConfig(cfg)
    } catch (error) {
      // 配置不存在时使用默认值
    }
  }

  const fetchHeartbeatDoc = async () => {
    setHeartbeatDocLoading(true)
    try {
      const data = await memoryApi.getHeartbeatDoc()
      setHeartbeatDoc(data.content)
    } catch (error) {
      // 文件不存在时使用空内容
    } finally {
      setHeartbeatDocLoading(false)
    }
  }

  useEffect(() => {
    fetchMemory()
    fetchLogs()
    fetchConfig()
    fetchHeartbeatDoc()
  }, [])

  const hasChanges = editingContent !== (memory?.content || '')
  const lineCount = editingContent ? editingContent.split('\n').length : 0
  const charCount = editingContent.length
  const filteredLogs = useMemo(
    () => logs.filter((date) => date.toLowerCase().includes(logSearch.toLowerCase())),
    [logs, logSearch],
  )

  useEffect(() => {
    if (!hasChanges) return
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', onBeforeUnload)
    }
  }, [hasChanges])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isSave = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's'
      if (!isSave) return
      event.preventDefault()
      if (!saving && !loading && hasChanges) {
        void handleSave()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [saving, loading, hasChanges, editingContent, memory])

  const handleSave = async () => {
    if (!hasChanges) return
    setSaving(true)
    try {
      await memoryApi.update(editingContent)
      message.success('记忆已保存')
      await fetchMemory()
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleViewLog = async (date: string) => {
    setLogLoading(true)
    setActiveLogDate(date)
    try {
      const data = await memoryApi.getLog(date)
      setSelectedLog(data)
    } catch (error) {
      message.error('获取日志失败')
    } finally {
      setLogLoading(false)
    }
  }

  const handleDeleteLog = async (date: string) => {
    try {
      await memoryApi.deleteLog(date)
      message.success('日志已删除')
      fetchLogs()
      if (activeLogDate === date) {
        setSelectedLog(null)
        setActiveLogDate(null)
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleReset = () => {
    setEditingContent(memory?.content || '')
    message.info('已恢复到最近一次保存内容')
  }

  const handleCopyLog = async () => {
    if (!selectedLog?.content) return
    try {
      await navigator.clipboard.writeText(selectedLog.content)
      message.success('日志内容已复制')
    } catch (error) {
      message.error('复制失败')
    }
  }

  const handleSaveConfig = async () => {
    setSavingConfig(true)
    try {
      await memoryApi.updateConfig(memoryConfig)
      message.success('设置已保存')
    } catch (error) {
      message.error('保存设置失败')
    } finally {
      setSavingConfig(false)
    }
  }

  const handleSaveHeartbeatDoc = async () => {
    setHeartbeatDocSaving(true)
    try {
      await memoryApi.updateHeartbeatDoc(heartbeatDoc)
      message.success('HEARTBEAT.md 已保存')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setHeartbeatDocSaving(false)
    }
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <Row gutter={24}>
        <Col xs={24} lg={14}>
          <Card
            title={(
              <Space>
                <span>长期记忆</span>
                {hasChanges ? <Tag color="warning">未保存</Tag> : <Tag color="success">已保存</Tag>}
              </Space>
            )}
            extra={(
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
            )}
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
                style={{ fontFamily: 'monospace', fontSize: 14 }}
              />
            </Spin>
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card
            title={(
              <Space>
                <CalendarOutlined />
                <span>日志历史</span>
                <Tag>{filteredLogs.length}/{logs.length}</Tag>
              </Space>
            )}
            extra={(
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchLogs}
              >
                刷新
              </Button>
            )}
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
              style={{ maxHeight: '60vh', overflow: 'auto' }}
              locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无日志" /> }}
              renderItem={(date) => (
                <List.Item
                  actions={[
                    <Popconfirm
                      title="确认删除"
                      description={`确定要删除 ${date} 的日志吗？`}
                      onConfirm={() => handleDeleteLog(date)}
                    >
                      <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <a
                        onClick={() => handleViewLog(date)}
                        style={{ cursor: 'pointer', color: activeLogDate === date ? '#1677ff' : undefined }}
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
              <Collapse.Panel header={`日志: ${selectedLog.date}`} key="1" extra={
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
                    <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              }>
                <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 13 }}>
                  {selectedLog.content}
                </pre>
              </Collapse.Panel>
            </Collapse>
          )}

          {/* 心跳配置 */}
          <Card
            title={
              <Space>
                <ReloadOutlined />
                <span>心跳配置</span>
              </Space>
            }
            style={{ marginTop: 16 }}
          >
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              Agent 会按固定间隔自动执行 HEARTBEAT.md 中的任务（如记忆维护、状态检查）。
            </Text>

            <div style={{ marginBottom: 16 }}>
              <Space>
                <Switch
                  checked={memoryConfig.heartbeat?.enabled ?? false}
                  onChange={(checked) =>
                    setMemoryConfig({
                      ...memoryConfig,
                      heartbeat: { ...memoryConfig.heartbeat, enabled: checked },
                    })
                  }
                />
                <Text>启用心跳</Text>
              </Space>
            </div>

            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                执行间隔
              </Text>
              <Input
                value={memoryConfig.heartbeat?.every ?? '6h'}
                onChange={(e) =>
                  setMemoryConfig({
                    ...memoryConfig,
                    heartbeat: { ...memoryConfig.heartbeat, every: e.target.value },
                  })
                }
                disabled={!memoryConfig.heartbeat?.enabled}
                placeholder="如 30m、1h、6h、0 */6 * * *"
                style={{ width: '100%' }}
              />
              <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                支持区间格式（30m / 1h / 6h）或 cron 表达式（0 */6 * * *）
              </Text>
            </div>

            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                活跃时段（可选）
              </Text>
              <Space>
                <Input
                  value={memoryConfig.heartbeat?.active_hours?.start ?? '08:00'}
                  onChange={(e) =>
                    setMemoryConfig({
                      ...memoryConfig,
                      heartbeat: {
                        ...memoryConfig.heartbeat,
                        active_hours: {
                          start: e.target.value,
                          end: memoryConfig.heartbeat?.active_hours?.end ?? '22:00',
                        },
                      },
                    })
                  }
                  disabled={!memoryConfig.heartbeat?.enabled}
                  placeholder="08:00"
                  style={{ width: 100 }}
                />
                <Text>至</Text>
                <Input
                  value={memoryConfig.heartbeat?.active_hours?.end ?? '22:00'}
                  onChange={(e) =>
                    setMemoryConfig({
                      ...memoryConfig,
                      heartbeat: {
                        ...memoryConfig.heartbeat,
                        active_hours: {
                          start: memoryConfig.heartbeat?.active_hours?.start ?? '08:00',
                          end: e.target.value,
                        },
                      },
                    })
                  }
                  disabled={!memoryConfig.heartbeat?.enabled}
                  placeholder="22:00"
                  style={{ width: 100 }}
                />
              </Space>
            </div>

            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSaveConfig}
              loading={savingConfig}
            >
              保存心跳配置
            </Button>
          </Card>

          {/* HEARTBEAT.md 编辑 */}
          <Card
            title={
              <Space>
                <FileTextOutlined />
                <span>心跳文档 (HEARTBEAT.md)</span>
              </Space>
            }
            style={{ marginTop: 16 }}
          >
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              编辑 HEARTBEAT.md 来指定 agent 每次心跳时需要执行的任务清单。
              内容为 Markdown 格式，以 <Text code>#</Text> 开头的行是注释，会被 agent 忽略。
            </Text>

            <TextArea
              value={heartbeatDoc}
              onChange={(e) => setHeartbeatDoc(e.target.value)}
              placeholder="# HEARTBEAT.md&#10;&#10;# 在此添加心跳任务清单&#10;# 1. 检查最近日志并更新 MEMORY.md&#10;# 2. 检查未完成的训练计划"
              autoSize={{ minRows: 10, maxRows: 20 }}
              disabled={heartbeatDocLoading}
              style={{ fontFamily: 'monospace', fontSize: 13 }}
            />

            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSaveHeartbeatDoc}
                loading={heartbeatDocSaving}
              >
                保存 HEARTBEAT.md
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchHeartbeatDoc}
                loading={heartbeatDocLoading}
              >
                刷新
              </Button>
            </div>
          </Card>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default MemoryManager
