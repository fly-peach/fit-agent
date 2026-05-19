import React, { useState } from "react";
import { Modal, Button, Typography } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import { useIsMobile } from "../../hooks";
import type { TrainingResultSnapshot } from "../../services/training";

interface CardViewerProps {
  open: boolean;
  onClose: () => void;
  snapshot?: TrainingResultSnapshot;
  onNavigate: (delta: number) => void;
  hasPrev: boolean;
  hasNext: boolean;
}

const CardViewer: React.FC<CardViewerProps> = ({
  open,
  onClose,
  snapshot,
  onNavigate,
  hasPrev,
  hasNext,
}) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const isMobile = useIsMobile();

  if (!snapshot) return null;

  return (
    <Modal
      title={
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span>{snapshot.title}</span>
          <div style={{ display: "flex", gap: 8 }}>
            <Button
              icon={<LeftOutlined />}
              disabled={!hasPrev}
              onClick={() => onNavigate(-1)}
            />
            <Button
              icon={<RightOutlined />}
              disabled={!hasNext}
              onClick={() => onNavigate(1)}
            />
          </div>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={isMobile ? "100%" : 800}
      style={isMobile ? { top: 0, margin: 0, maxWidth: "100%" } : undefined}
    >
      <div className="card-viewer-container">
        <div
          className={`card-flip-container ${isFlipped ? "flipped" : ""}`}
          onClick={() => setIsFlipped(!isFlipped)}
        >
          <div className="card-face card-front">
            <div
              className="card-content"
              dangerouslySetInnerHTML={{ __html: snapshot.cardHtml }}
            />
            <div className="flip-hint">点击查看 AI 评价</div>
          </div>
          <div className="card-face card-back">
            <div className="ai-evaluation">
              <Typography.Title level={4} style={{ textAlign: "center", marginBottom: 24 }}>
                AI 评价与建议
              </Typography.Title>
              <Typography.Paragraph>
                保持良好的训练习惯，继续坚持！
              </Typography.Paragraph>
              <Typography.Paragraph>
                建议增加力量训练的比重，搭配合理的营养摄入，可以获得更好的效果。
              </Typography.Paragraph>
              <div className="flip-hint">点击返回</div>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default CardViewer;
