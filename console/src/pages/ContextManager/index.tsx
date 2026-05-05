import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Button, Table, message, Spin, Statistic, Popconfirm, Modal, Input, Space, Tag, Empty, Typography } from 'antd'
import { ReloadOutlined, DeleteOutlined, ExperimentOutlined, EyeOutlined, SearchOutlined, CopyOutlined } from '@ant-design/icons'
import { contextApi, ContextStats, CacheEntry } from '../../services/context'

const { Text } = Typography

const ContextManager: React.FC = () => {
  const [stats, setStats] = useState<ContextStats | null>(null)
  const [cacheList, setCacheList] = useState<CacheEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [compactLoading, setCompactLoading] = useState(false)
  const [cacheContent, setCacheContent] = useState<string | null>(null)
  const [cacheModalVisible, setCacheModalVisible] = useState(false)
  const [cacheKeyword, setCacheKeyword] = useState('')

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsData, cacheData] = await Promise.all([
        contextApi.getStats(),
        contextApi.listCache(),
      ])
      setStats(statsData)
      setCacheList(cacheData)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleClearCache = async () => {
    try {
      const result = await contextApi.clearCache()
      message.success(`已清理 ${result.cleared} 个缓存文件`)
      fetchData()
    } catch (error) {
      message.error('清理失败')
    }
  }

  const handleCompact = async () => {
    setCompactLoading(true)
    try {
      const result = await contextApi.triggerCompact()
      if (result.success) {
        message.success('上下文压缩完成')
      } else {
        message.error(`压缩失败: ${result.reason}`)
      }
      fetchData()
    } catch (error) {
      message.error('压缩失败')
    } finally {
      setCompactLoading(false)
    }
  }

  const handleViewCache = async (id: string) => {
    try {
      const data = await contextApi.getCache(id)
      setCacheContent(data.content)
      setCacheModalVisible(true)
    } catch (error) {
      message.error('获取缓存失败')
    }
  }

  const handleCopyCache = async () => {
    if (!cacheContent) return
    try {
      await navigator.clipboard.writeText(cacheContent)
      message.success('缓存内容已复制')
    } catch (error) {
      message.error('复制失败')
    }
  }

  const filteredCacheList = cacheList.filter((item) =>
    item.tool_name.toLowerCase().includes(cacheKeyword.toLowerCase()),
  )

  const columns = [
    {
      title: '工具名称',
      dataIndex: 'tool_name',
      key: 'tool_name',
    },
    {
      title: '大小',
      dataIndex: 'size_bytes',
      key: 'size_bytes',
      render: (bytes: number) => `${(bytes / 1024).toFixed(1)} KB`,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: CacheEntry) => (
        <Button
          type="text"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewCache(record.id)}
        >
          查看
        </Button>
      ),
    },
  ]

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>上下文管理</h2>
        <div>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchData}
            style={{ marginRight: 8 }}
          >
            刷新
          </Button>
          <Button
            icon={<ExperimentOutlined />}
            onClick={handleCompact}
            loading={compactLoading}
            style={{ marginRight: 8 }}
          >
            压缩上下文
          </Button>
          <Popconfirm
            title="确认清理"
            description="确定要清理所有工具结果缓存吗？"
            onConfirm={handleClearCache}
          >
            <Button danger icon={<DeleteOutlined />}>清理缓存</Button>
          </Popconfirm>
        </div>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="当前 Token 使用"
                value={stats?.current_tokens || 0}
                suffix={`/ ${stats?.max_tokens || 131072}`}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="压缩次数 (今日/总计)"
                value={stats?.compaction_count_today || 0}
                suffix={`/ ${stats?.compaction_count_total || 0}`}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="缓存文件"
                value={stats?.cache_file_count || 0}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="缓存总大小"
                value={stats?.cache_total_size_bytes || 0}
                precision={0}
                suffix={<Text type="secondary">{formatBytes(stats?.cache_total_size_bytes || 0)}</Text>}
              />
            </Card>
          </Col>
        </Row>

        <Card title="工具结果缓存">
          <Space style={{ marginBottom: 12, width: '100%', justifyContent: 'space-between' }}>
            <Input
              prefix={<SearchOutlined />}
              value={cacheKeyword}
              onChange={(e) => setCacheKeyword(e.target.value)}
              allowClear
              placeholder="按工具名称筛选缓存"
              style={{ maxWidth: 280 }}
            />
            <Tag>{filteredCacheList.length}/{cacheList.length}</Tag>
          </Space>
          <Table
            dataSource={filteredCacheList}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无缓存" /> }}
          />
        </Card>
      </Spin>

      <Modal
        title="缓存内容"
        open={cacheModalVisible}
        onCancel={() => setCacheModalVisible(false)}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyCache}>
            复制
          </Button>,
          <Button key="close" type="primary" onClick={() => setCacheModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
        style={{ maxHeight: '80vh', overflow: 'auto' }}
      >
        <pre className="cache-content">
          {cacheContent}
        </pre>
      </Modal>
    </div>
  )
}

export default ContextManager
