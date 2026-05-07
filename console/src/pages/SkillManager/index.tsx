import React, { useState, useEffect } from 'react'
import {
  Card, Row, Col, Button, Switch, Modal, message, Tag, Tooltip, Spin,
  Tabs, Descriptions, Alert, Space, Typography, Input, Divider,
  Tree, Empty, Popconfirm
} from 'antd'
import {
  InfoCircleOutlined, ReloadOutlined, DownloadOutlined,
  SettingOutlined, DatabaseOutlined, SyncOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import {
  skillApi, Skill, SkillDetail, SkillSystemConfig, SkillPackageConfig,
  SkillSyncStatus, InitializeConfigRequest, SyncConfigRequest,
  UpdateSkillPackageRequest
} from '../../services/skills'
import type { DataNode } from 'antd/es/tree'
import request from '../../utils/request'

const { Title, Text } = Typography
const { TabPane } = Tabs
const { TextArea } = Input

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

const SkillPackageConfigEditor: React.FC<{
  pkg: SkillPackageConfig
  onUpdate: (name: string, data: UpdateSkillPackageRequest) => void
}> = ({ pkg, onUpdate }) => {
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState<UpdateSkillPackageRequest>({ ...pkg })

  const handleSave = () => {
    onUpdate(pkg.name, formData)
    setEditing(false)
  }

  return (
    <Card size="small" style={{ marginBottom: 8 }}>
      <Descriptions column={2} size="small">
        <Descriptions.Item label="名称">{pkg.name}</Descriptions.Item>
        <Descriptions.Item label="优先级">{pkg.priority}</Descriptions.Item>
        <Descriptions.Item label="启用">
          {editing ? (
            <Switch
              checked={formData.enabled}
              onChange={(v) => setFormData({ ...formData, enabled: v })}
            />
          ) : pkg.enabled ? '是' : '否'}
        </Descriptions.Item>
        <Descriptions.Item label="自动更新">
          {editing ? (
            <Switch
              checked={formData.auto_update}
              onChange={(v) => setFormData({ ...formData, auto_update: v })}
            />
          ) : pkg.auto_update ? '是' : '否'}
        </Descriptions.Item>
      </Descriptions>

      {editing && (
        <div style={{ marginTop: 8 }}>
          <Text strong>配置 (JSON)</Text>
          <TextArea
            rows={3}
            value={JSON.stringify(formData.config, null, 2)}
            onChange={(e) => {
              try {
                setFormData({ ...formData, config: JSON.parse(e.target.value) })
              } catch {
                // 允许未完成的输入
              }
            }}
            style={{ marginTop: 4 }}
          />
        </div>
      )}

      <div style={{ marginTop: 8, textAlign: 'right' }}>
        {editing ? (
          <Space>
            <Button size="small" onClick={() => setEditing(false)}>取消</Button>
            <Button size="small" type="primary" onClick={handleSave}>保存</Button>
          </Space>
        ) : (
          <Button size="small" icon={<SettingOutlined />} onClick={() => setEditing(true)}>编辑</Button>
        )}
      </div>
    </Card>
  )
}

const SkillManager: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([])
  const [config, setConfig] = useState<SkillSystemConfig | null>(null)
  const [syncStatus, setSyncStatus] = useState<SkillSyncStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null)
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null)
  const [selectedFileContent, setSelectedFileContent] = useState('')
  const [fileLoading, setFileLoading] = useState(false)
  const [subSkills, setSubSkills] = useState<Skill[]>([])
  const [subSkillsLoading, setSubSkillsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('skills')

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

  const fetchConfig = async () => {
    try {
      const data = await skillApi.getConfig()
      setConfig(data)
    } catch {
      // 配置可能未初始化，忽略错误
    }
  }

  const fetchSyncStatus = async () => {
    try {
      const data = await skillApi.getSyncStatus()
      setSyncStatus(data)
    } catch {
      // 忽略错误
    }
  }

  const fetchAll = async () => {
    await Promise.all([fetchSkills(), fetchConfig(), fetchSyncStatus()])
  }

  useEffect(() => {
    fetchAll()
  }, [])

  const handleToggle = async (skill: Skill) => {
    try {
      if (skill.enabled) {
        await skillApi.disable(skill.name)
      } else {
        await skillApi.enable(skill.name)
      }
      message.success(`技能 ${skill.enabled ? '已禁用' : '已启用'}`)
      fetchAll()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleExport = async (skill: Skill) => {
    try {
      message.loading({ content: '正在导出...', key: 'export' })

      const response = await request.get(`/agent/skills/${skill.name}/export`, {
        responseType: 'blob',
      })

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${skill.name}.zip`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      message.success({ content: '导出成功', key: 'export' })
    } catch (error) {
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
      // 获取子技能
      await fetchSubSkills(skill.name)
      setModalVisible(true)
    } catch {
      message.error('获取技能详情失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchSubSkills = async (skillName: string) => {
    setSubSkillsLoading(true)
    try {
      const subs = await skillApi.getSubSkills(skillName)
      setSubSkills(subs)
    } catch {
      setSubSkills([])
    } finally {
      setSubSkillsLoading(false)
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

  const handleInitialize = async () => {
    setLoading(true)
    try {
      const request: InitializeConfigRequest = {
        default_skill_names: skills.filter(s => s.enabled).map(s => s.name)
      }
      await skillApi.initializeConfig(request)
      message.success('配置初始化成功')
      fetchAll()
    } catch {
      message.error('初始化失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async (direction: 'two-way' | 'to-config' | 'from-config') => {
    setLoading(true)
    try {
      const request: SyncConfigRequest = { direction }
      await skillApi.syncConfig(request)
      const directions: Record<string, string> = {
        'two-way': '双向同步',
        'to-config': '同步到配置',
        'from-config': '从配置同步'
      }
      message.success(`${directions[direction]}成功`)
      fetchAll()
    } catch {
      message.error('同步失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateSkillPackage = async (name: string, data: UpdateSkillPackageRequest) => {
    setLoading(true)
    try {
      await skillApi.updateSkillPackage(name, data)
      message.success('配置更新成功')
      fetchAll()
    } catch {
      message.error('更新失败')
    } finally {
      setLoading(false)
    }
  }

  const handleResetConfig = () => {
    Modal.confirm({
      title: '确认重置',
      content: '确定要重置技能配置吗？所有自定义配置将丢失。',
      okText: '重置',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true)
        try {
          await skillApi.resetConfig()
          message.success('配置已重置')
          fetchAll()
        } catch {
          message.error('重置失败')
        } finally {
          setLoading(false)
        }
      },
    })
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <SettingOutlined style={{ marginRight: 8 }} />
          技能管理
        </Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchAll}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <ThunderboltOutlined /> 技能列表
              </span>
            }
            key="skills"
          >
            {skills.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>
                暂无技能
              </div>
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
          </TabPane>

          <TabPane
            tab={
              <span>
                <DatabaseOutlined /> 配置管理
              </span>
            }
            key="config"
          >
            <Row gutter={24}>
              <Col xs={24} md={16}>
                {/* 状态面板 */}
                <Card title="系统状态" style={{ marginBottom: 16 }}>
                  {syncStatus ? (
                    <Descriptions column={2} bordered size="small">
                      <Descriptions.Item label="初始化状态">
                        {syncStatus.initialized ? (
                          <Tag color="success">已初始化</Tag>
                        ) : (
                          <Tag color="warning">未初始化</Tag>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="最后同步时间">
                        {syncStatus.last_synced_at ? (
                          new Date(syncStatus.last_synced_at).toLocaleString()
                        ) : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="技能包总数">
                        {syncStatus.total_skill_packages}
                      </Descriptions.Item>
                      <Descriptions.Item label="已扫描技能数">
                        {syncStatus.total_scanned_skills}
                      </Descriptions.Item>
                      <Descriptions.Item label="已启用技能" span={2}>
                        {syncStatus.enabled_skills.length > 0 ? (
                          syncStatus.enabled_skills.map((s) => <Tag key={s}>{s}</Tag>)
                        ) : '-'}
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Alert type="info" message="暂无状态信息" />
                  )}
                </Card>

                {/* 操作面板 */}
                <Card title="配置操作" style={{ marginBottom: 16 }}>
                  <Space wrap>
                    {!config?.initialized ? (
                      <Button
                        type="primary"
                        icon={<SettingOutlined />}
                        onClick={handleInitialize}
                      >
                        初始化配置
                      </Button>
                    ) : (
                      <>
                        <Button
                          icon={<SyncOutlined />}
                          onClick={() => handleSync('two-way')}
                        >
                          双向同步
                        </Button>
                        <Button onClick={() => handleSync('to-config')}>
                          → 同步到配置
                        </Button>
                        <Button onClick={() => handleSync('from-config')}>
                          ← 从配置同步
                        </Button>
                        <Popconfirm
                          title="确认重置"
                          description="确定要重置配置吗？"
                          onConfirm={handleResetConfig}
                          okText="是"
                          cancelText="否"
                        >
                          <Button danger>重置配置</Button>
                        </Popconfirm>
                      </>
                    )}
                  </Space>
                </Card>

                {/* 技能包配置 */}
                {config && Object.keys(config.skill_packages).length > 0 && (
                  <Card title="技能包配置">
                    {Object.entries(config.skill_packages).map(([name, pkg]) => (
                      <SkillPackageConfigEditor
                        key={name}
                        pkg={pkg}
                        onUpdate={handleUpdateSkillPackage}
                      />
                    ))}
                  </Card>
                )}
              </Col>

              <Col xs={24} md={8}>
                {/* 系统配置信息 */}
                <Card title="配置信息">
                  {config ? (
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="配置版本">
                        {config.version}
                      </Descriptions.Item>
                      <Descriptions.Item label="初始化时间">
                        {config.initialized_at ? (
                          new Date(config.initialized_at).toLocaleString()
                        ) : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="最后同步时间">
                        {config.last_synced_at ? (
                          new Date(config.last_synced_at).toLocaleString()
                        ) : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="默认启用技能">
                        {config.default_skills_enabled.length > 0 ? (
                          config.default_skills_enabled.map((s) => <Tag key={s}>{s}</Tag>)
                        ) : '-'}
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Alert
                      type="info"
                      message="配置未初始化"
                      description="点击左侧的初始化配置按钮来初始化系统"
                    />
                  )}
                </Card>

                <Card title="使用说明" style={{ marginTop: 16 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>
                      <strong>初始化配置：</strong>首次使用时需要初始化配置系统，将当前启用的技能保存为默认配置。
                    </Text>
                    <Divider style={{ margin: '8px 0' }} />
                    <Text>
                      <strong>同步配置：</strong>
                      <br />- 双向同步：技能状态与配置互相同步
                      <br />- 同步到配置：将当前技能状态保存到配置文件
                      <br />- 从配置同步：用配置文件恢复技能状态
                    </Text>
                    <Divider style={{ margin: '8px 0' }} />
                    <Text>
                      <strong>技能包配置：</strong>可以单独编辑每个技能包的启用状态、自动更新设置和自定义配置。
                    </Text>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Spin>

      <Modal
        title={selectedSkill?.name}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setSelectedFilePath(null)
          setSelectedFileContent('')
        }}
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
            <Descriptions bordered size="small">
              <Descriptions.Item label="版本">{selectedSkill.version}</Descriptions.Item>
              <Descriptions.Item label="状态">
                {selectedSkill.enabled ? <Tag color="green">已启用</Tag> : <Tag color="default">已禁用</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="来源">{selectedSkill.source}</Descriptions.Item>
              <Descriptions.Item label="渠道" span={2}>
                {selectedSkill.channels.length > 0 ? (
                  selectedSkill.channels.map((channel) => <Tag key={channel}>{channel}</Tag>)
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="标签" span={2}>
                {selectedSkill.tags.length > 0 ? (
                  selectedSkill.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{selectedSkill.description}</Descriptions.Item>
            </Descriptions>
            {/* 子技能区域 */}
            {subSkills.length > 0 && (
              <>
                <Divider />
                <Title level={5}>子技能 ({subSkills.length})</Title>
                <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                  {subSkills.map((sub) => (
                    <Col xs={24} sm={12} key={sub.name}>
                      <Card size="small" style={{ background: sub.enabled ? '#f6ffed' : '#fafafa' }}>
                        <Space>
                          <div>
                            <Text strong>{sub.name}</Text>
                            <Tag style={{ marginLeft: 8 }} color={sub.enabled ? 'green' : 'default'}>
                              {sub.enabled ? '启用' : '禁用'}
                            </Tag>
                          </div>
                        </Space>
                        {sub.description && (
                          <div style={{ marginTop: 4 }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {sub.description}
                            </Text>
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
                {selectedSkill.references.length === 0 && selectedSkill.scripts.length === 0 ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有 references 或 scripts 文件" />
                ) : (
                  <Tree
                    defaultExpandAll
                    treeData={[
                      {
                        key: 'references-root',
                        title: `references (${selectedSkill.references.length})`,
                        children: buildFileTreeData(selectedSkill.references),
                      },
                      {
                        key: 'scripts-root',
                        title: `scripts (${selectedSkill.scripts.length})`,
                        children: buildFileTreeData(selectedSkill.scripts),
                      },
                    ]}
                    onSelect={(keys, info) => {
                      if (!info.node.isLeaf) return
                      const filePath = String(keys[0] || '')
                      if (filePath) {
                        handleSelectSkillFile(filePath)
                      }
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
