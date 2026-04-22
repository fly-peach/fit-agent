import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button, Card, Collapse, DatePicker, Form, InputNumber, message, Row, Col, Space, Spin, Upload,
} from "antd";
import { ArrowLeftOutlined, CameraOutlined, SaveOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd/es/upload/interface";
import {
  BodyCompositionRecord,
  createBodyComposition,
  listBodyComposition,
} from "../../shared/api/bodyComposition";

const { Panel } = Collapse;

interface FormData {
  weight?: number;
  bmi?: number;
  body_fat_rate?: number;
  visceral_fat_level?: number;
  fat_mass?: number;
  fat_free_mass?: number;
  muscle_mass?: number;
  skeletal_muscle_mass?: number;
  skeletal_muscle_rate?: number;
  water_rate?: number;
  water_mass?: number;
  bmr?: number;
  muscle_rate?: number;
  bone_mass?: number;
  protein_mass?: number;
  subcutaneous_fat?: number;
  body_age?: number;
}

export function BodyCompositionCreatePage() {
  const navigate = useNavigate();
  const [form] = Form.useForm<FormData>();
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [lastRecord, setLastRecord] = useState<BodyCompositionRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [measuredAt, setMeasuredAt] = useState(() => dayjs());

  useEffect(() => {
    (async () => {
      try {
        const records = await listBodyComposition({ limit: 1 });
        if (records.length > 0) {
          setLastRecord(records[0]);
          form.setFieldsValue({
            weight: records[0].weight || undefined,
            body_fat_rate: records[0].body_fat_rate || undefined,
            bmi: records[0].bmi || undefined,
            visceral_fat_level: records[0].visceral_fat_level || undefined,
            fat_mass: records[0].fat_mass || undefined,
            muscle_mass: records[0].muscle_mass || undefined,
            skeletal_muscle_mass: records[0].skeletal_muscle_mass || undefined,
            skeletal_muscle_rate: records[0].skeletal_muscle_rate || undefined,
            water_rate: records[0].water_rate || undefined,
            water_mass: records[0].water_mass || undefined,
            bmr: records[0].bmr || undefined,
            muscle_rate: records[0].muscle_rate || undefined,
            bone_mass: records[0].bone_mass || undefined,
            protein_mass: records[0].protein_mass || undefined,
            subcutaneous_fat: records[0].subcutaneous_fat || undefined,
            body_age: records[0].body_age || undefined,
          });
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [form]);

  const handleWeightChange = (val: number | null) => {
    const bfr = form.getFieldValue("body_fat_rate");
    if (val && bfr) {
      form.setFieldValue("fat_mass", Math.round(val * bfr / 100 * 100) / 100);
      form.setFieldValue("fat_free_mass", Math.round(val * (100 - bfr) / 100 * 100) / 100);
    }
  };

  async function onSubmit(values: FormData) {
    setSubmitting(true);
    try {
      const payload: any = {
        measured_at: measuredAt.toISOString(),
      };
      Object.entries(values).forEach(([k, v]) => {
        if (v !== null && v !== undefined) payload[k] = v;
      });
      const record = await createBodyComposition(payload);
      message.success("保存成功");
      navigate(`/body-composition/${record.id}`);
    } catch (err: any) {
      message.error(err.message || "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleScaleUpload(_file: UploadFile) {
    setUploading(true);
    // TODO: integrate with analyze_scale_image tool
    setTimeout(() => {
      setUploading(false);
      message.info("体重秤识别功能即将上线");
    }, 1000);
    return false;
  }

  if (loading) return <div style={{ padding: 40, textAlign: "center" }}><Spin size="large" /></div>;

  const inputProps = { style: { width: "100%", background: "#222", borderColor: "#444", color: "#fff" } };

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: 20 }}>
      <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/body-composition")} style={{ color: "#fff", marginBottom: 16 }}>
        返回
      </Button>

      <Card title="录入体成分" style={{ background: "#1a1a2e", borderColor: "#333" }}>
        <Form form={form} layout="vertical" onFinish={onSubmit}>
          <Form.Item label="体测时间" required>
            <DatePicker
              showTime
              value={measuredAt}
              onChange={(d) => d && setMeasuredAt(d)}
              style={{ width: "100%", background: "#222", borderColor: "#444", color: "#fff" }}
            />
          </Form.Item>

          <Form.Item label="从体脂秤照片导入">
            <Upload beforeUpload={handleScaleUpload} maxCount={1} listType="picture-card">
              <div>
                <CameraOutlined style={{ fontSize: 24 }} />
                <div style={{ marginTop: 8 }}>上传照片</div>
              </div>
            </Upload>
          </Form.Item>

          <Collapse defaultActiveKey={["basic"]} ghost>
            <Panel header="身体成分（必填）" key="basic">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="weight" label="体重(kg)" rules={[{ required: true, message: "请输入体重" }]}>
                    <InputNumber {...inputProps} placeholder="例如：88.65" min={0} onChange={handleWeightChange} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="body_fat_rate" label="体脂率(%)">
                    <InputNumber {...inputProps} placeholder="例如：22.44" min={0} max={60} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="bmi" label="BMI（自动计算）">
                    <InputNumber {...inputProps} disabled />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="visceral_fat_level" label="内脏脂肪等级">
                    <InputNumber {...inputProps} placeholder="例如：8.9" min={0} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="fat_mass" label="脂肪量(kg)">
                    <InputNumber {...inputProps} placeholder="例如：19.89" min={0} />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>

            <Panel header="肌肉骨骼" key="muscle">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="muscle_mass" label="肌肉量(kg)">
                    <InputNumber {...inputProps} placeholder="例如：64.62" min={0} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="skeletal_muscle_mass" label="骨骼肌重量(kg)">
                    <InputNumber {...inputProps} placeholder="例如：43.94" min={0} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="skeletal_muscle_rate" label="骨骼肌率(%)">
                    <InputNumber {...inputProps} placeholder="例如：49.57" min={0} max={100} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="muscle_rate" label="肌肉率(%)">
                    <InputNumber {...inputProps} placeholder="例如：72.89" min={0} max={100} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="bone_mass" label="骨量(kg)">
                    <InputNumber {...inputProps} placeholder="例如：4.14" min={0} />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>

            <Panel header="水分代谢" key="water">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="water_rate" label="水分率(%)">
                    <InputNumber {...inputProps} placeholder="例如：57.4" min={0} max={100} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="water_mass" label="水分量(kg)">
                    <InputNumber {...inputProps} placeholder="例如：50.88" min={0} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="protein_mass" label="蛋白质重量(kg)">
                    <InputNumber {...inputProps} placeholder="例如：13.74" min={0} />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>

            <Panel header="代谢与评估" key="metabolism">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="bmr" label="基础代谢(kcal)">
                    <InputNumber {...inputProps} placeholder="例如：1981" min={0} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="subcutaneous_fat" label="皮下脂肪(%)">
                    <InputNumber {...inputProps} placeholder="例如：18.89" min={0} max={60} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="body_age" label="体年龄">
                    <InputNumber {...inputProps} placeholder="例如：30" min={0} max={100} />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>
          </Collapse>

          <div style={{ marginTop: 20 }}>
            <Space>
              <Button type="primary" icon={<SaveOutlined />} htmlType="submit" loading={submitting}>
                保存
              </Button>
              <Button onClick={() => form.resetFields()}>重置</Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  );
}
