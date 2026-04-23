import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Modal,
  Form,
  InputNumber,
  DatePicker,
  message,
  Typography,
  Tag,
} from 'antd'
import {
  HeartOutlined,
  LineChartOutlined,
  PlusOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { healthApi, type HealthMetrics, HealthMeasurement, HealthReport } from '../../services/health'
import styles from './Health.module.css'

const { Title } = Typography

const Health: React.FC = () => {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null)
  const [measurements, setMeasurements] = useState<HealthMeasurement[]>([])
  const [report, setReport] = useState<HealthReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
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

  const handleAddRecord = async (values: { weight: number; bodyFat: number; measureDate: dayjs.Dayjs }) => {
    try {
      await healthApi.createMetric({
        weight: values.weight,
        bodyFat: values.bodyFat,
        measureDate: values.measureDate.format('YYYY-MM-DD'),
      })
      message.success('记录成功')
      setModalVisible(false)
      form.resetFields()
      fetchData()
    } catch {
      message.error('记录失败')
    }
  }

  const handleExport = async () => {
    try {
      const blob = await healthApi.exportData('week', 'csv')
      const url = window.URL.createObjectURL(blob as Blob)
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
    switch (status) {
      case 'normal':
        return <Tag color="green">正常</Tag>
      case 'under':
        return <Tag color="blue">偏瘦</Tag>
      case 'over':
        return <Tag color="orange">偏胖</Tag>
      default:
        return <Tag>{status}</Tag>
    }
  }

  const columns: ColumnsType<HealthMeasurement> = [
    {
      title: '日期',
      dataIndex: 'measureDate',
      key: 'measureDate',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '体重',
      dataIndex: 'weight',
      key: 'weight',
      render: (val: number) => `${val} kg`,
    },
    {
      title: '体脂率',
      dataIndex: 'bodyFat',
      key: 'bodyFat',
      render: (val: number) => `${val}%`,
    },
    {
      title: 'BMI',
      dataIndex: 'bmi',
      key: 'bmi',
      render: (val: number) => val.toFixed(1),
    },
    {
      title: '状态',
      dataIndex: 'bmiStatus',
      key: 'bmiStatus',
      render: getBmiStatusTag,
    },
  ]

  return (
    <div className={styles.container}>
      <Title level={3}>
        <HeartOutlined /> 健康数据
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="当前体重" value={metrics?.weight || 0} suffix="kg" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="身高" value={metrics?.height || 175} suffix="cm" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="体脂率" value={metrics?.bodyFat || 0} suffix="%" precision={1} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="BMI"
              value={metrics?.bmi || 0}
              suffix={
                metrics?.bmiStatus ? getBmiStatusTag(metrics.bmiStatus) : null
              }
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="历史记录"
        loading={loading}
        style={{ marginTop: 16 }}
        extra={
          <>
            <Button icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
              添加记录
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport} style={{ marginLeft: 8 }}>
              导出
            </Button>
          </>
        }
      >
        <Table
          columns={columns}
          dataSource={measurements}
          rowKey="recordId"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Card
        title={<><LineChartOutlined /> 健康趋势</>}
        loading={loading}
        style={{ marginTop: 16 }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Title level={5}>体重变化</Title>
            {report?.weightTrend && (
              <div className={styles.trendData}>
                {report.weightTrend.map((item, idx) => (
                  <div key={idx} className={styles.trendItem}>
                    <span>{dayjs(item.date).format('MM-DD')}</span>
                    <span>{item.value} kg</span>
                  </div>
                ))}
              </div>
            )}
            {report?.summary && (
              <div className={styles.summary}>
                <span>平均: {report.summary.avgWeight} kg</span>
                <span>变化: {report.summary.weightChange > 0 ? '+' : ''}{report.summary.weightChange} kg</span>
              </div>
            )}
          </Col>
          <Col span={12}>
            <Title level={5}>BMI变化</Title>
            {report?.bmiTrend && (
              <div className={styles.trendData}>
                {report.bmiTrend.map((item, idx) => (
                  <div key={idx} className={styles.trendItem}>
                    <span>{dayjs(item.date).format('MM-DD')}</span>
                    <span>{item.value.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            )}
          </Col>
        </Row>
      </Card>

      <Modal
        title="添加健康记录"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleAddRecord} layout="vertical">
          <Form.Item name="weight" label="体重" rules={[{ required: true }]}>
            <InputNumber min={30} max={200} step={0.1} addonAfter="kg" />
          </Form.Item>
          <Form.Item name="bodyFat" label="体脂率" rules={[{ required: true }]}>
            <InputNumber min={3} max={50} step={0.1} addonAfter="%" />
          </Form.Item>
          <Form.Item name="measureDate" label="测量日期" rules={[{ required: true }]}>
            <DatePicker defaultValue={dayjs()} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Health