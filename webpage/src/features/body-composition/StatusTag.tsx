import { Tag } from "antd";

const levelColorMap: Record<string, string> = {
  优: "green",
  标准: "blue",
  正常: "blue",
  偏高: "orange",
  偏胖: "orange",
  轻度肥胖: "orange",
  不足: "cyan",
  偏低: "cyan",
  警戒型: "red",
  减重: "purple",
  增重: "purple",
  良: "green",
  过重: "orange",
  偏轻: "cyan",
  减脂: "purple",
  增脂: "purple",
  增肌: "purple",
  减肌: "purple",
  肥胖: "red",
  运动型偏胖: "orange",
  隐藏型肥胖: "orange",
  偏瘦: "cyan",
  肌肉型: "blue",
  营养不足: "cyan",
  营养均衡: "blue",
  营养过剩: "orange",
};

export function StatusTag({ level }: { level: string }) {
  return <Tag color={levelColorMap[level] || "default"}>{level}</Tag>;
}
