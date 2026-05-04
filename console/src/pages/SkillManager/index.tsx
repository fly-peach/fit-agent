import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Button, Switch, Modal, message, Upload, Tag, Tooltip, Spin } from 'antd'
import { UploadOutlined, DeleteOutlined, InfoCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import { skillApi, Skill } from '../../services/skills'
import type { UploadFile } from 'antd/es/upload/interface'

const SkillCard: React.FC<{
  skill: Skill
  onToggle: (skill: Skill) => void
  onDelete: (name: string) => void
  onView: (skill: Skill) => void
}> = ({ skill, onToggle, onDelete, onView }) => {
  return (
    <Card
      hoverable
      actions={[
        <Switch
          checked={skill.enabled}
          onChange={() => onToggle(skill)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />,
        <Tooltip title="查看详情">
          <Button type="text" icon={<InfoCircleOutlined />} onClick={() => onView(skill)} />
        </Tooltip>,
        <Tooltip title="删除技能">
          <Button type="text" danger icon={<DeleteOutlined />} onClick={() => onDelete(skill.name)} />
        </Tooltip>,
      ]}
    >
      <Card.Meta
        title={
          <span>
            {skill.name}
            <Tag color="blue" style={{ marginLeft: 8 }}>v{skill.version}</Tag>
          </span>
        }
        description={skill.description}
      />
      {skill.tags && skill.tags.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {skill.tags.map((tag) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </div>
      )}
    </Card>
  )
}

const SkillManager: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)

  const fetchSkills = async () => {
    setLoading(true)
    try {
      const data = await skillApi.list()
      setSkills(data)
    } catch (error) {
      message.error('获取技能列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSkills()
  }, [])

  const handleToggle = async (skill: Skill) => {
    try {
      if (skill.enabled) {
        await skillApi.disable(skill.name)
      } else {
        await skillApi.enable(skill.name)
      }
      message.success(`技能 ${skill.enabled ? '已禁用' : '已启用'}`)
      fetchSkills()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleDelete = (name: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除技能 "${name}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await skillApi.delete(name)
          message.success('技能已删除')
          fetchSkills()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const handleView = async (skill: Skill) => {
    setLoading(true)
    try {
      const detail = await skillApi.get(skill.name)
      setSelectedSkill(detail)
      setModalVisible(true)
    } catch {
      message.error('获取技能详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: UploadFile) => {
    const rawFile = file.originFileObj
    if (!rawFile) return false

    if (rawFile.size > 200 * 1024 * 1024) {
      message.error('技能包不能超过 200MB')
      return false
    }

    setLoading(true)
    try {
      const result = await skillApi.upload(rawFile)
      message.success(`技能 "${result.name}" 安装成功`)
      fetchSkills()
    } catch (error) {
      message.error('上传失败')
    } finally {
      setLoading(false)
    }
    return false
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>技能管理</h2>
        <div>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchSkills}
            style={{ marginRight: 8 }}
          >
            刷新
          </Button>
          <Upload
            beforeUpload={handleUpload}
            accept=".zip"
            showUploadList={false}
          >
            <Button type="primary" icon={<UploadOutlined />}>上传技能</Button>
          </Upload>
        </div>
      </div>

      <Spin spinning={loading}>
        {skills.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>
            暂无技能，点击上方"上传技能"按钮安装新技能
          </div>
        ) : (
          <Row gutter={[16, 16]}>
            {skills.map((skill) => (
              <Col xs={24} sm={12} md={8} lg={8} key={skill.name}>
                <SkillCard
                  skill={skill}
                  onToggle={handleToggle}
                  onDelete={handleDelete}
                  onView={handleView}
                />
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      <Modal
        title={selectedSkill?.name}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
        style={{ maxHeight: '80vh', overflow: 'auto' }}
      >
        {selectedSkill && (
          <div>
            <p><strong>版本:</strong> {selectedSkill.version}</p>
            <p><strong>描述:</strong> {selectedSkill.description}</p>
            <div style={{ marginTop: 16 }}>
              <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                {selectedSkill.content}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default SkillManager
