import React, { useState, useEffect } from 'react'
import { Row, Col, Button, message, Input, List, Modal, Spin, Collapse, Popconfirm } from 'antd'
import { SaveOutlined, ReloadOutlined, ExperimentOutlined, DeleteOutlined, CalendarOutlined } from '@ant-design/icons'
import { memoryApi, MemoryContent, DailyLog } from '../../services/memory'

const { TextArea } = Input

const MemoryManager: React.FC = () => {
  const [memory, setMemory] = useState<MemoryContent | null>(null)
  const [editingContent, setEditingContent] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const [selectedLog, setSelectedLog] = useState<DailyLog | null>(null)
  const [logLoading, setLogLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [activeLogDate, setActiveLogDate] = useState<string | null>(null)

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
      setLogs(data)
    } catch (error) {
      message.error('获取日志列表失败')
    }
  }

  useEffect(() => {
    fetchMemory()
    fetchLogs()
  }, [])

  const handleSave = async () => {
    try {
      await memoryApi.update(editingContent)
      message.success('记忆已保存')
      fetchMemory()
    } catch (error) {
      message.error('保存失败')
    }
  }

  const handleOptimize = async () => {
    setOptimizing(true)
    try {
      const result = await memoryApi.optimize()
      if (result.success) {
        message.success('记忆优化完成')
        fetchMemory()
      } else {
        message.error(`优化失败: ${result.reason}`)
      }
    } catch (error) {
      message.error('优化失败')
    } finally {
      setOptimizing(false)
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

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <Row gutter={24}>
        <Col xs={24} lg={14}>
          <div style={{ marginBottom: 16 }}>
            <h2 style={{ margin: 0, display: 'inline-block' }}>长期记忆</h2>
            <div style={{ float: 'right' }}>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchMemory}
                style={{ marginRight: 8 }}
              >
                刷新
              </Button>
              <Button
                icon={<ExperimentOutlined />}
                onClick={handleOptimize}
                loading={optimizing}
                style={{ marginRight: 8 }}
              >
                优化记忆
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
              >
                保存
              </Button>
            </div>
          </div>
          <Spin spinning={loading}>
            <TextArea
              value={editingContent}
              onChange={(e) => setEditingContent(e.target.value)}
              autoSize={{ minRows: 20, maxRows: 30 }}
              style={{ fontFamily: 'monospace', fontSize: 14 }}
            />
            {memory && memory.last_updated && (
              <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                最后更新: {memory.last_updated}
              </div>
            )}
          </Spin>
        </Col>

        <Col xs={24} lg={10}>
          <h2 style={{ marginTop: 0 }}>
            <CalendarOutlined /> 日志历史
          </h2>
          <Spin spinning={logLoading}>
            <List
              dataSource={logs}
              style={{ maxHeight: '60vh', overflow: 'auto' }}
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
                <Popconfirm
                  title="确认删除"
                  description={`确定要删除 ${selectedLog.date} 的日志吗？`}
                  onConfirm={() => handleDeleteLog(selectedLog.date)}
                >
                  <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                </Popconfirm>
              }>
                <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 13 }}>
                  {selectedLog.content}
                </pre>
              </Collapse.Panel>
            </Collapse>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default MemoryManager
