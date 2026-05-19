import React from "react";
import { Row, Col, Card, Typography, Tag, Space, Button, Popconfirm, Empty } from "antd";
import { EyeOutlined, DeleteOutlined, CalendarOutlined } from "@ant-design/icons";
import { Trophy } from "lucide-react";
import dayjs from "dayjs";
import { useIsMobile } from "../../hooks";
import type { TrainingResultSnapshot } from "../../services/training";

interface CardListProps {
  snapshots: TrainingResultSnapshot[];
  loading: boolean;
  onView: (snapshot: TrainingResultSnapshot, index: number) => void;
  onDelete: (snapshotId: number) => void;
}

const CardList: React.FC<CardListProps> = ({ snapshots, loading, onView, onDelete }) => {
  const isMobile = useIsMobile();

  const parseStats = (snapshot: TrainingResultSnapshot) => {
    if (!snapshot.statsJson) return null;
    try {
      return JSON.parse(snapshot.statsJson);
    } catch {
      return null;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px 0" }}>
        加载中...
      </div>
    );
  }

  if (snapshots.length === 0) {
    return (
      <div style={{ padding: "60px 0" }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="还没有训练成果报告，快去生成一个吧！"
        />
      </div>
    );
  }

  return (
    <Row gutter={[16, 16]}>
      {snapshots.map((snapshot, index) => {
        const stats = parseStats(snapshot);
        return (
          <Col xs={24} sm={12} md={8} key={snapshot.id}>
            <Card
              hoverable
              className="snapshot-card"
              cover={
                <div className="card-cover">
                  <Trophy size={32} color="#F59E0B" />
                </div>
              }
              actions={[
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => onView(snapshot, index)}
                >
                  查看
                </Button>,
                <Popconfirm
                  title="确认删除"
                  description="确定要删除这个训练成果报告吗？"
                  onConfirm={() => onDelete(snapshot.id)}
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>,
              ]}
            >
              <Card.Meta
                title={
                  <div style={{ marginBottom: 8 }}>
                    <Typography.Text strong ellipsis={{ rows: 2 }}>
                      {snapshot.title}
                    </Typography.Text>
                  </div>
                }
                description={
                  <Space direction="vertical" style={{ width: "100%" }} size={8}>
                    <Space wrap>
                      {snapshot.periodType && (
                        <Tag color="blue">
                          {snapshot.periodType === "week" ? "周报告" : snapshot.periodType === "month" ? "月报告" : "自定义"}
                        </Tag>
                      )}
                      {snapshot.periodStart && snapshot.periodEnd && (
                        <Tag icon={<CalendarOutlined />}>
                          {dayjs(snapshot.periodStart).format("M/D")} - {dayjs(snapshot.periodEnd).format("M/D")}
                        </Tag>
                      )}
                    </Space>

                    {stats && (
                      <div className="stats-preview">
                        {stats.totalSessions !== undefined && (
                          <div className="stat-item">
                            <span className="stat-value">{stats.totalSessions}</span>
                            <span className="stat-label">次训练</span>
                          </div>
                        )}
                        {stats.totalDuration !== undefined && (
                          <div className="stat-item">
                            <span className="stat-value">{stats.totalDuration}</span>
                            <span className="stat-label">分钟</span>
                          </div>
                        )}
                        {stats.totalCalories !== undefined && (
                          <div className="stat-item">
                            <span className="stat-value">{stats.totalCalories}</span>
                            <span className="stat-label">kcal</span>
                          </div>
                        )}
                      </div>
                    )}

                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      生成于 {dayjs(snapshot.createdAt).format("YYYY-MM-DD HH:mm")}
                    </Typography.Text>
                  </Space>
                }
              />
            </Card>
          </Col>
        );
      })}
    </Row>
  );
};

export default CardList;
