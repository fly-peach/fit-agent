import React, { useState, useEffect } from 'react'
import {
  Card, Row, Col, Button, Switch, Modal, message, Tag, Tooltip, Spin,
  Descriptions, Alert, Space, Typography, Divider,
  Tree, Empty
} from 'antd'
import {
  InfoCircleOutlined, ReloadOutlined, DownloadOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import {
  skillApi, Skill, SkillDetail,
} from '../../services/skills'
import type { DataNode } from 'antd/es/tree'
import request from '../../utils/request'

const { Title, Text } = Typography

const buildFileTreeData = (paths: string[]): DataNode[] => {
  const root: DataNode[] = []

  paths.forEach((fullPath) => {
    const parts = fullPath.split('/').filter(Boolean)
    let current = root
    let currentPath = ''

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      let node = current.find((item) => item.key === currentPath)
      if (!node) {
        node = {
          key: currentPath,
          title: part,
          children: [],
          isLeaf: index === parts.length - 1,
        }
        current.push(node)
      }
      if (!node.children) {
        node.children = []
      }
      current = node.children
    })
  })

  return root
}

const SkillCard: React.FC<{
  skill: Skill
  onToggle: (skill: Skill) => void
  onView: (skill: Skill) => void
  onExport: (skill: Skill) => void
}> = ({ skill, onToggle, onView, onExport }) => {
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
        <Tooltip title="导出技能">
          <Button type="text" icon={<DownloadOutlined />} onClick={() => onExport(skill)} />
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
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null)
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null)
  const [selectedFileContent, setSelectedFileContent] = useState('')
  const [fileLoading, setFileLoading] = useState(false)
  const [subSkills, setSubSkills] = useState<Skill[]>([])

  const fetchSkills = async () => {
    setLoading(true)
    try {
      const data = await skillApi.list()
      setSkills(data)
    } catch {
      message.error('获取技能列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchSkills() }, [])

  const handleToggle = async (skill: Skill) => {
    try {
      if (skill.enabled) {
        await skillApi.disable(skill.name)
      } else {
        await skillApi.enable(skill.name)
      }
      message.success(`技能 ${skill.enabled ? '已禁用' : '已启用'}`)
      fetchSkills()
    } catch {
      message.error('操作失败')
    }
  }

  const handleExport = async (skill: Skill) => {
    try {
      message.loading({ content: '正在导出...', key: 'export' })
      const response = await request.get(`/agent/skills/${skill.name}/export`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${skill.name}.zip`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success({ content: '导出成功', key: 'export' })
    } catch {
      message.error({ content: '导出失败', key: 'export' })
    }
  }

  const handleView = async (skill: Skill) => {
    setLoading(true)
    try {
      const detail = await skillApi.get(skill.name)
      setSelectedSkill(detail)
      setSelectedFilePath(null)
      setSelectedFileContent('')
      setSubSkills([])
      try {
        const subs = await skillApi.getSubSkills(skill.name)
        setSubSkills(subs)
      } catch { setSubSkills([]) }
      setModalVisible(true)
    } catch {
      message.error('获取技能详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectSkillFile = async (filePath: string) => {
    if (!selectedSkill) return
    setSelectedFilePath(filePath)
    setFileLoading(true)
    try {
      const result = await skillApi.getFile(selectedSkill.name, filePath)
      setSelectedFileContent(result.content)
    } catch (error) {
      setSelectedFileContent('')
      message.error((error as Error).message || '读取技能文件失败')
    } finally {
      setFileLoading(false)
    }
  }

  const closeModal = () => {
    setModalVisible(false)
    setSelectedFilePath(null)
    setSelectedFileContent('')
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <ThunderboltOutlined style={{ marginRight: 8 }} />
          技能管理
        </Title>
        <Button icon={<ReloadOutlined />} onClick={fetchSkills}>刷新</Button>
      </div>

      <Spin spinning={loading}>
        {skills.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>暂无技能</div>
        ) : (
          <Row gutter={[16, 16]}>
            {skills.map((skill) => (
              <Col xs={24} sm={12} md={8} lg={8} key={skill.name}>
                <SkillCard
                  skill={skill}
                  onToggle={handleToggle}
                  onView={handleView}
                  onExport={handleExport}
                />
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      <Modal
        title={selectedSkill?.name}
        open={modalVisible}
        onCancel={closeModal}
        footer={[<Button key="close" onClick={closeModal}>关闭</Button>]}
        width={800}
        style={{ maxHeight: '80vh', overflow: 'auto' }}
      >
        {selectedSkill && (
          <div>
            <Descriptions bordered size="small">
              <Descriptions.Item label="版本">{selectedSkill.version}</Descriptions.Item>
              <Descriptions.Item label="状态">
                {selectedSkill.enabled ? <Tag color="green">已启用</Tag> : <Tag color="default">已禁用</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="来源">{selectedSkill.source}</Descriptions.Item>
              <Descriptions.Item label="渠道" span={2}>
                {selectedSkill.channels?.length > 0
                  ? selectedSkill.channels.map((c) => <Tag key={c}>{c}</Tag>)
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="标签" span={2}>
                {selectedSkill.tags?.length > 0
                  ? selectedSkill.tags.map((t) => <Tag key={t}>{t}</Tag>)
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{selectedSkill.description}</Descriptions.Item>
            </Descriptions>

            {subSkills.length > 0 && (
              <>
                <Divider />
                <Title level={5}>子技能 ({subSkills.length})</Title>
                <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                  {subSkills.map((sub) => (
                    <Col xs={24} sm={12} key={sub.name}>
                      <Card size="small" style={{ background: sub.enabled ? '#f6ffed' : '#fafafa' }}>
                        <div>
                          <Text strong>{sub.name}</Text>
                          <Tag style={{ marginLeft: 8 }} color={sub.enabled ? 'green' : 'default'}>
                            {sub.enabled ? '启用' : '禁用'}
                          </Tag>
                        </div>
                        {sub.description && (
                          <div style={{ marginTop: 4 }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>{sub.description}</Text>
                          </div>
                        )}
                      </Card>
                    </Col>
                  ))}
                </Row>
              </>
            )}

            <Divider />
            <Row gutter={16}>
              <Col span={12}>
                <Title level={5}>SKILL.md 正文</Title>
                <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, borderRadius: 4, maxHeight: 420, overflow: 'auto' }}>
                  {selectedSkill.body || selectedSkill.content}
                </pre>
              </Col>
              <Col span={12}>
                <Title level={5}>技能文件树</Title>
                {(selectedSkill.references?.length || 0) === 0 && (selectedSkill.scripts?.length || 0) === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有 references 或 scripts 文件" />
                ) : (
                  <Tree
                    defaultExpandAll
                    treeData={[
                      {
                        key: 'references-root',
                        title: `references (${selectedSkill.references?.length || 0})`,
                        children: buildFileTreeData(selectedSkill.references || []),
                      },
                      {
                        key: 'scripts-root',
                        title: `scripts (${selectedSkill.scripts?.length || 0})`,
                        children: buildFileTreeData(selectedSkill.scripts || []),
                      },
                    ]}
                    onSelect={(keys, info) => {
                      if (!info.node.isLeaf) return
                      const filePath = String(keys[0] || '')
                      if (filePath) handleSelectSkillFile(filePath)
                    }}
                  />
                )}
                <Divider />
                <Title level={5}>
                  文件预览
                  {selectedFilePath ? <Text type="secondary" style={{ marginLeft: 8 }}>{selectedFilePath}</Text> : null}
                </Title>
                <Spin spinning={fileLoading}>
                  {selectedFilePath ? (
                    <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, borderRadius: 4, maxHeight: 260, overflow: 'auto' }}>
                      {selectedFileContent || '文件为空'}
                    </pre>
                  ) : (
                    <Alert type="info" message="点击文件树中的文件后按需加载内容" />
                  )}
                </Spin>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default SkillManager
