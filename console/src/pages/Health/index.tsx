import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Table, Button, Modal, Form, InputNumber, DatePicker, Tag, message, List, Avatar } from 'antd'
import { DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import { Heart } from 'lucide-react'
import dayjs from 'dayjs'
import { healthApi, type HealthMetrics, HealthMeasurement, HealthReport } from '../../services/health'
import type { ColumnsType } from 'antd/es/table'

const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  return isMobile
}

const Health: React.FC = () => {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null)
  const [measurements, setMeasurements] = useState<HealthMeasurement[]>([])
  const [report, setReport] = useState<HealthReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const isMobile = useIsMobile()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [metricsData, measurementsData, reportData] = await Promise.all([
        healthApi.getMetrics(),
        healthApi.getMeasurements(20),
        healthApi.getReport('week'),
      ])
      setMetrics(metricsData)
      setMeasurements(measurementsData)
      setReport(reportData)
    } finally { setLoading(false) }
  }

  const handleAddRecord = async () => {
    try {
      const values = await form.validateFields()
      await healthApi.createMetric({
        weight: values.weight,
        height: values.height,
        bodyFat: values.bodyFat,
        measureDate: values.measureDate.format('YYYY-MM-DD'),
      })
      message.success('记录成功')
      setModalOpen(false)
      form.resetFields()
      fetchData()
    } catch { message.error('记录失败') }
  }

  const handleExport = async () => {
    try {
      const blob = await healthApi.exportData('week', 'csv') as unknown as Blob
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'health_data.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch { message.error('导出失败') }
  }

  const getBmiStatusTag = (status: string) => {
    const colors: Record<string, string> = { normal: '#10B981', under: '#06B6D4', over: '#F59E0B' }
    const labels: Record<string, string> = { normal: '正常', under: '偏瘦', over: '偏胖' }
    return <Tag color={colors[status] || 'default'}>{labels[status] || status}</Tag>
  }

  const columns: ColumnsType<HealthMeasurement> = [
    { title: '日期', dataIndex: 'measureDate', render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
    { title: '体重', dataIndex: 'weight', render: (v: number) => `${v} kg` },
    { title: '体脂率', dataIndex: 'bodyFat', render: (v: number) => `${v}%` },
    { title: 'BMI', dataIndex: 'bmi', render: (v: number) => v.toFixed(1) },
    { title: '状态', dataIndex: 'bmiStatus', render: (v: string) => getBmiStatusTag(v) },
  ]

  return (
    <div className="fitagent-page-enter" style={{ padding: isMobile ? 12 : 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#ECFEFF', color: '#06B6D4' }}>
          <Heart size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>健康数据</Typography.Title>
      </div>

      <Row gutter={[isMobile ? 12 : 16, isMobile ? 12 : 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%)' }}>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">当前体重</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#0EA5E9', fontWeight: 700 }}>{metrics?.weight || 0} kg</Typography.Title>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%)' }}>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">身高</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#06B6D4', fontWeight: 700 }}>{metrics?.height || 175} cm</Typography.Title>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%)' }}>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">体脂率</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#EF4444', fontWeight: 700 }}>{metrics?.bodyFat || 0}%</Typography.Title>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #FFF7ED 0%, #FED7AA 100%)' }}>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">BMI</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#F59E0B', fontWeight: 700 }}>{metrics?.bmi?.toFixed(1) || 0}</Typography.Title>
                {metrics?.bmiStatus && getBmiStatusTag(metrics.bmiStatus)}
              </>
            )}
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>历史记录</Typography.Title>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加记录</Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出</Button>
          </div>
        </div>
        {isMobile ? (
          <List
            dataSource={measurements}
            loading={loading}
            locale={{ emptyText: '暂无记录' }}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar style={{ backgroundColor: '#0EA5E9' }}>
                    {dayjs(item.measureDate).format('DD')}
                  </Avatar>}
                  title={`${item.weight} kg · ${item.bodyFat}%`}
                  description={`BMI ${item.bmi?.toFixed(1) || '-'} · ${item.bmiStatus ? getBmiStatusTag(item.bmiStatus) : ''} · ${dayjs(item.measureDate).format('YYYY-MM-DD')}`}
                />
              </List.Item>
            )}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={measurements}
            rowKey="recordId"
            size="small"
            pagination={false}
            loading={loading}
          />
        )}
      </Card>

      <Card style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <Typography.Title level={5}>健康趋势</Typography.Title>
        <Row gutter={isMobile ? 12 : 16}>
          <Col xs={24} sm={12}>
            <Typography.Text strong>体重变化</Typography.Text>
            {report?.weightTrend?.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #E5E7EB' }}>
                <Typography.Text>{dayjs(item.date).format('MM-DD')}</Typography.Text>
                <Typography.Text>{item.value} kg</Typography.Text>
              </div>
            ))}
            {report?.summary && (
              <Typography.Text type="secondary" style={{ marginTop: 8, display: 'block' }}>
                平均: {report.summary.avgWeight} kg · 变化: {report.summary.weightChange > 0 ? '+' : ''}{report.summary.weightChange} kg
              </Typography.Text>
            )}
          </Col>
          <Col xs={24} sm={12}>
            <Typography.Text strong>BMI变化</Typography.Text>
            {report?.bmiTrend?.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #E5E7EB' }}>
                <Typography.Text>{dayjs(item.date).format('MM-DD')}</Typography.Text>
                <Typography.Text>{item.value.toFixed(1)}</Typography.Text>
              </div>
            ))}
          </Col>
        </Row>
      </Card>

      <Modal
        title="添加健康记录"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleAddRecord}
        okText="提交"
        cancelText="取消"
        width={isMobile ? '100%' : undefined}
        style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="weight" label="体重 (kg)" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} defaultValue={70} /></Form.Item>
          <Form.Item name="height" label="身高 (cm)" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} defaultValue={175} /></Form.Item>
          <Form.Item name="bodyFat" label="体脂率 (%)" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} defaultValue={15} /></Form.Item>
          <Form.Item name="measureDate" label="测量日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} defaultValue={dayjs()} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Health
