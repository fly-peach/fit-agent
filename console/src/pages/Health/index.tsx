import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Table, Button, Modal, Form, InputNumber, DatePicker, Tag, message } from 'antd'
import { DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { healthApi, type HealthMetrics, HealthMeasurement, HealthReport } from '../../services/health'
import type { ColumnsType } from 'antd/es/table'

const Health: React.FC = () => {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null)
  const [measurements, setMeasurements] = useState<HealthMeasurement[]>([])
  const [report, setReport] = useState<HealthReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

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
    } finally {
      setLoading(false)
    }
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
    } catch {
      message.error('记录失败')
    }
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
    } catch {
      message.error('导出失败')
    }
  }

  const getBmiStatusTag = (status: string) => {
    const colors: Record<string, string> = { normal: 'success', under: 'processing', over: 'warning' }
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
    <div style={{ padding: 24 }}>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>❤️ 健康数据</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">当前体重</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0' }}>{metrics?.weight || 0} kg</Typography.Title>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">身高</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0' }}>{metrics?.height || 175} cm</Typography.Title>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">体脂率</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0' }}>{metrics?.bodyFat || 0}%</Typography.Title>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            {loading ? (
              <Typography.Text type="secondary">加载中...</Typography.Text>
            ) : (
              <>
                <Typography.Text type="secondary">BMI</Typography.Text>
                <Typography.Title level={3} style={{ margin: '8px 0 0' }}>{metrics?.bmi?.toFixed(1) || 0}</Typography.Title>
                {metrics?.bmiStatus && getBmiStatusTag(metrics.bmiStatus)}
              </>
            )}
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>历史记录</Typography.Title>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加记录</Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出</Button>
          </div>
        </div>
        <Table
          columns={columns}
          dataSource={measurements}
          rowKey="recordId"
          size="small"
          pagination={false}
          loading={loading}
        />
      </Card>

      <Card style={{ marginTop: 24 }}>
        <Typography.Title level={5}>📈 健康趋势</Typography.Title>
        <Row gutter={16}>
          <Col span={12}>
            <Typography.Text strong>体重变化</Typography.Text>
            {report?.weightTrend?.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
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
          <Col span={12}>
            <Typography.Text strong>BMI变化</Typography.Text>
            {report?.bmiTrend?.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
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
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="weight" label="体重 (kg)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} defaultValue={70} />
          </Form.Item>
          <Form.Item name="height" label="身高 (cm)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} defaultValue={175} />
          </Form.Item>
          <Form.Item name="bodyFat" label="体脂率 (%)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} defaultValue={15} />
          </Form.Item>
          <Form.Item name="measureDate" label="测量日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} defaultValue={dayjs()} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Health
