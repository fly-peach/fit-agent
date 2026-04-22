# Phase 01: 多模态图片上传与聊天框自适应高度

> 阶段目标：引入模型的多模态识别图片能力，实现图片上传功能；聊天框自适应用户输入内容高度。

## 1. 功能需求

### 1.1 图片上传功能

- 用户可在聊天框上传图片（食物图片、体重秤图片等）
- 图片预览展示在输入框上方
- 发送时将图片转为 base64 格式传递给后端
- 后端使用 AgentScope 多模态能力识别图片内容

### 1.2 聊天框自适应高度

- 输入框根据用户输入内容自动调整高度
- 最小高度 1 行，最大高度 6 行
- 平滑过渡动画

## 2. 技术方案

### 2.1 前端实现

#### 图片上传组件

- 使用原生 `<input type="file" accept="image/*">` 触发图片选择
- 图片转 base64 使用 `FileReader.readAsDataURL`
- 预览使用 `<img>` 标签展示缩略图
- 支持删除已选图片

#### 自适应高度输入框

- 监听 textarea 的 input 事件
- 使用 `scrollHeight` 计算实际高度
- 设置 `rows` 属性动态调整

### 2.2 后端集成

- 流式 API `chatWithAgentStream` 扩展支持 `attachments` 参数
- 后端 `agent_service.py` 已支持多模态消息处理
- `multimodal_tools.py` 已实现图片识别工具

## 3. 文件修改清单

### 3.1 前端文件

| 文件 | 修改内容 |
|------|----------|
| `AISidebar.tsx` | 添加图片上传 UI、预览、发送逻辑 |
| `agent.ts` | 扩展 `chatWithAgentStream` 支持 attachments |
| `styles.css` | 添加图片上传相关样式、自适应高度样式 |

### 3.2 后端文件

| 文件 | 修改内容 |
|------|----------|
| `agent_service.py` | 确认多模态消息处理逻辑 |
| `multimodal_tools.py` | 已完成 AgentScope 多模态适配 |

## 4. 实现细节

### 4.1 图片上传 UI 结构

```tsx
<div className="ai-composer-wrapper">
  {/* 图片预览区 */}
  {attachments.length > 0 && (
    <div className="ai-attachments-preview">
      {attachments.map((att, idx) => (
        <div className="ai-attachment-item">
          <img src={att.preview} alt="预览" />
          <button onClick={() => removeAttachment(idx)}>×</button>
        </div>
      ))}
    </div>
  )}
  
  {/* 输入框 */}
  <div className="ai-inline-composer-main">
    <textarea ... />
    <div className="ai-composer-actions">
      <button className="ai-upload-btn" onClick={triggerUpload}>
        📷
      </button>
      <button className="ai-send-btn">↑</button>
    </div>
  </div>
  
  {/* 隐藏的文件输入 */}
  <input
    ref={fileInputRef}
    type="file"
    accept="image/*"
    multiple
    style={{ display: 'none' }}
    onChange={handleFileSelect}
  />
</div>
```

### 4.2 自适应高度逻辑

```tsx
const textareaRef = useRef<HTMLTextAreaElement>(null);

const adjustHeight = () => {
  const textarea = textareaRef.current;
  if (!textarea) return;
  
  textarea.style.height = 'auto';
  const lineHeight = 24; // 根据实际样式调整
  const maxHeight = lineHeight * 6;
  const newHeight = Math.min(textarea.scrollHeight, maxHeight);
  textarea.style.height = `${newHeight}px`;
};

// 在 onChange 中调用
<textarea
  ref={textareaRef}
  onChange={(e) => {
    setText(e.target.value);
    adjustHeight();
  }}
/>
```

### 4.3 API 扩展

```typescript
export async function chatWithAgentStream(
  payload: {
    messages: AgentMessageInput[];
    thinking: boolean;
    session_id?: string | null;
    attachments?: AgentAttachment[];  // 新增
  },
  onEvent: (event: StreamEventPayload) => void,
): Promise<void>
```

## 5. 验收标准

### 5.1 图片上传验收

- [ ] 用户可点击按钮选择图片
- [ ] 图片预览正确显示在输入框上方
- [ ] 可删除已选图片
- [ ] 发送时图片正确传递给后端
- [ ] 后端正确识别图片内容并返回结果
- [ ] 消息列表中显示用户发送的图片

### 5.2 自适应高度验收

- [ ] 输入框默认 1 行高度
- [ ] 输入内容增加时高度自动扩展
- [ ] 最大高度限制为 6 行
- [ ] 删除内容时高度自动收缩
- [ ] 过渡动画平滑

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大图片上传慢 | 用户等待时间长 | 前端压缩图片、限制文件大小 |
| 图片识别结果不稳定 | 数据偏差 | 显示置信度、用户可编辑后确认 |
| 自适应高度计算不准确 | UI 显示异常 | 使用 scrollHeight + lineHeight 精确计算 |

## 7. 里程碑

- M1：图片上传 UI 完成
- M2：API 扩展完成
- M3：自适应高度完成
- M4：联调验收通过