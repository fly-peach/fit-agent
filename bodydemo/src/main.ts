import './styles/body-visualizer.css';
import './styles/label-overlay.css';
import './styles/animations.css';
import './styles/muscle-custom.css';
import './styles/dialog.css';
import { BodyVisualizer } from './visualizer/BodyVisualizer';
import { BodyModel, type Gender } from './models/BodyModel';
import { ALL_PART_CONFIGS, CIRCUMFERENCE_PARTS, COMPOSITION_PARTS, BASIC_PARTS } from './models/BodyPartConfig';
import type { BodyMeasurements } from './models/BodyMeasurements';
import { ALL_DEMO_DATA, DEMO_PREVIOUS } from './demo/demo-data';

const app = document.getElementById('app')!;

let currentModel: BodyModel;
let previousModel: BodyModel | null = null;
let visualizer: BodyVisualizer;
let activeTab: 'circumference' | 'composition' | 'basic' = 'circumference';
let currentGender: Gender = 'male';

function init() {
  app.innerHTML = buildHTML();
  const vizContainer = document.getElementById('body-visualizer')!;
  visualizer = new BodyVisualizer(vizContainer, {
    showLabels: true,
    showValues: true,
    highlightAbnormal: true,
    animationEnabled: true,
    bodyScaleEnabled: true,
  });

  const initialData = ALL_DEMO_DATA['current'].data;
  currentModel = new BodyModel(initialData, 'male');
  previousModel = new BodyModel(DEMO_PREVIOUS, 'male');
  visualizer.render(currentModel);

  visualizer.on('partClick', (data) => openEditDialog(data.key));
  visualizer.on('partHover', (data) => {
    showPartDetail(data.key, data.value, data.label);
    const config = ALL_PART_CONFIGS.find(c => c.key === data.key);
    if (config) {
      visualizer.labelOverlayPublic.highlight(data.key);
    }
  });

  renderSummaryCards();
  renderMetricCards('circumference');
  renderComparisonPanel();
  bindEvents();
}

function buildHTML(): string {
  return `
    <div class="app-header">
      <h1>🧍 人体数据展示</h1>
      <p>点击人体部位编辑数据</p>
    </div>

    <div class="app-layout">
      <div class="body-panel">
        <div class="body-panel__controls">
          <button class="body-panel__btn body-panel__btn--active" data-view="front">正面</button>
          <button class="body-panel__btn" data-view="back">背面</button>
          <button class="body-panel__btn body-panel__btn--active" id="toggle-labels">标注</button>
          <button class="body-panel__btn body-panel__btn--active" id="toggle-values">数值</button>
          <button class="body-panel__btn body-panel__btn--active" id="toggle-scale">缩放</button>
        </div>
        <div class="body-panel__controls" style="margin-bottom: 8px; justify-content: center;">
          <span style="font-size: 14px; color: #94a3b8;">性别：</span>
          <button class="body-panel__btn body-panel__btn--active" id="gender-male">男</button>
          <button class="body-panel__btn" id="gender-female">女</button>
        </div>
        <div class="body-visualizer" id="body-visualizer"></div>
        <div class="body-panel__controls" style="margin-top: 12px; flex-wrap: wrap;">
          <span style="font-size: 12px; color: var(--color-text-secondary); margin-right: 8px;">预设体型：</span>
          ${Object.entries(ALL_DEMO_DATA).map(([key, value]) => `
            <button class="body-panel__btn ${key === 'current' ? 'body-panel__btn--active' : ''}" data-dataset="${key}">${value.label}</button>
          `).join('')}
        </div>
      </div>

      <div class="data-panel">
        <div class="data-panel__section" id="summary-section">
          <div class="data-panel__title"><span class="icon">📊</span> 综合指标</div>
          <div class="summary-row" id="summary-row"></div>
        </div>

        <div class="data-panel__section">
          <div class="data-panel__title" style="justify-content: space-between;">
            <span><span class="icon">📏</span> 数据展示</span>
            <div style="display: flex; gap: 6px;">
              <button class="body-panel__btn body-panel__btn--active" data-tab="circumference">围度</button>
              <button class="body-panel__btn" data-tab="composition">体成分</button>
              <button class="body-panel__btn" data-tab="basic">基础</button>
            </div>
          </div>
          <div class="metric-grid" id="metric-grid"></div>
        </div>

        <div class="comparison-panel" id="comparison-panel">
          <div class="comparison-panel__title">📈 与上次对比（两周前）</div>
          <div class="comparison-list" id="comparison-list"></div>
        </div>
      </div>
    </div>

    <div class="part-detail" id="part-detail"></div>
    <div id="modal-root"></div>
  `;
}

function openEditDialog(key: string): void {
  const config = ALL_PART_CONFIGS.find(c => c.key === key);
  if (!config) return;
  const value = currentModel.raw[config.key as keyof BodyMeasurements];
  if (typeof value !== 'number') return;

  const modalRoot = document.getElementById('modal-root')!;
  modalRoot.innerHTML = `
    <div class="modal-overlay" id="edit-modal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">编辑 ${config.label}</div>
          <button class="modal-close-btn" id="close-modal-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="modal-input-group">
            <label class="modal-label">${config.label} (正常范围：${config.normalRange[0]} ~ ${config.normalRange[1]})</label>
            <div class="modal-input-row">
              <input type="number" id="edit-input" value="${value}" step="0.1" min="0" class="modal-input">
              <span class="modal-unit">${config.unit}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn modal-btn--cancel" id="cancel-edit-btn">取消</button>
          <button class="modal-btn modal-btn--save" id="save-edit-btn">保存</button>
        </div>
      </div>
    </div>
  `;

  const modal = document.getElementById('edit-modal')!;
  const input = document.getElementById('edit-input') as HTMLInputElement;

  // 关闭事件
  document.getElementById('close-modal-btn')?.addEventListener('click', closeEditDialog);
  document.getElementById('cancel-edit-btn')?.addEventListener('click', closeEditDialog);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeEditDialog();
  });

  // 保存事件
  document.getElementById('save-edit-btn')?.addEventListener('click', () => {
    const newValue = parseFloat(input.value);
    if (!isNaN(newValue) && newValue >= 0) {
      const updatedData = { ...currentModel.raw } as unknown as Record<string, number>;
      updatedData[config.key] = newValue;
      currentModel = new BodyModel(updatedData as unknown as BodyMeasurements, currentGender);
      visualizer.update(currentModel);
      renderSummaryCards();
      renderMetricCards(activeTab);
      renderComparisonPanel();
    }
    closeEditDialog();
  });

  input.focus();
  input.select();
}

function closeEditDialog(): void {
  const modalRoot = document.getElementById('modal-root')!;
  modalRoot.innerHTML = '';
  visualizer.labelOverlayPublic.clearHighlight();
}

function renderSummaryCards(): void {
  const row = document.getElementById('summary-row')!;
  const bmi = currentModel.getBMI();
  const bmiStatus = currentModel.getBMIStatus();
  const whr = currentModel.getWaistToHipRatio();
  const ffmi = currentModel.getFFMI();

  const bmiLabel: Record<string, string> = {
    underweight: '偏瘦',
    normal: '正常',
    overweight: '偏胖',
    obese: '肥胖',
  };

  row.innerHTML = `
    <div class="summary-card">
      <div class="summary-card__label">BMI</div>
      <div class="summary-card__value">${bmi.toFixed(1)}</div>
      <div class="summary-card__sub">${bmiLabel[bmiStatus] || bmiStatus}</div>
    </div>
    <div class="summary-card">
      <div class="summary-card__label">腰臀比</div>
      <div class="summary-card__value">${whr.toFixed(2)}</div>
      <div class="summary-card__sub">${whr < 0.9 ? '正常' : '偏高'}</div>
    </div>
    <div class="summary-card">
      <div class="summary-card__label">FFMI</div>
      <div class="summary-card__value">${ffmi.toFixed(1)}</div>
      <div class="summary-card__sub">${ffmi < 18 ? '一般' : ffmi < 20 ? '良好' : '优秀'}</div>
    </div>
    <div class="summary-card">
      <div class="summary-card__label">测量日期</div>
      <div class="summary-card__value" style="font-size:16px;">${currentModel.raw.measureDate}</div>
      <div class="summary-card__sub">ID: ${currentModel.raw.id.slice(0, 8)}</div>
    </div>
  `;
}

function renderMetricCards(tab: 'circumference' | 'composition' | 'basic'): void {
  activeTab = tab;
  const grid = document.getElementById('metric-grid')!;
  const parts = tab === 'circumference'
    ? CIRCUMFERENCE_PARTS
    : tab === 'composition'
    ? COMPOSITION_PARTS
    : BASIC_PARTS;

  const comparison = previousModel ? currentModel.compare(previousModel.raw) : null;

  grid.innerHTML = parts.map(config => {
    const mk = config.key as keyof BodyMeasurements;
    const value = currentModel.raw[mk];
    if (typeof value !== 'number') return '';
    const status = currentModel.getBodyPartStatus(mk);
    const change = comparison?.changes[mk];

    const gender = currentModel.currentGender;
    const range = gender === 'female' ? config.normalRangeFemale : config.normalRange;

    const statusClass = status !== 'normal' ? `metric-card--${status}` : '';
    const statusColor = status === 'danger' ? 'var(--color-accent)' : 'var(--color-warning)';

    let changeHTML = '';
    if (change !== undefined && change !== 0) {
      const dir = change > 0 ? '↑' : '↓';
      changeHTML = `<span style="color: ${status === 'normal' ? 'var(--color-text-secondary)' : statusColor}">${dir} ${Math.abs(change).toFixed(1)}</span>`;
    }

    return `
      <div class="metric-card ${statusClass}" data-key="${config.key}">
        <div class="metric-card__icon">${config.icon}</div>
        <div class="metric-card__info">
          <div class="metric-card__label">${config.label}</div>
          <div class="metric-card__value">${value} <span class="metric-card__unit">${config.unit}</span></div>
          <div class="metric-card__change">${changeHTML}</div>
          <div class="metric-card__normal-range">正常范围：${range[0]} ~ ${range[1]} ${config.unit}</div>
        </div>
      </div>
    `;
  }).join('');

  grid.querySelectorAll<HTMLElement>('.metric-card[data-key]').forEach(card => {
    card.addEventListener('click', () => {
      const key = card.dataset.key!;
      openEditDialog(key);
    });
  });
}

function renderComparisonPanel(): void {
  if (!previousModel) {
    document.getElementById('comparison-panel')!.style.display = 'none';
    return;
  }

  const list = document.getElementById('comparison-list')!;
  const comparison = currentModel.compare(previousModel.raw);
  const changes = Object.entries(comparison.changes)
    .filter(([, v]) => v !== 0)
    .slice(0, 6);

  list.innerHTML = changes.map(([key, change]) => {
    const config = ALL_PART_CONFIGS.find(c => c.key === key);
    if (!config) return '';
    const sign = change > 0 ? '+' : '';
    const color = change > 0 ? 'var(--color-accent)' : 'var(--color-success)';
    return `
      <div class="comparison-item">
        <span class="comparison-item__label">${config.icon} ${config.label}</span>
        <span class="comparison-item__value" style="color: ${color};">${sign}${change.toFixed(1)}${config.unit}</span>
      </div>
    `;
  }).join('');
}

function showPartDetail(key: string, value: number, label: string): void {
  const config = ALL_PART_CONFIGS.find(c => c.key === key);
  if (!config) return;

  const detail = document.getElementById('part-detail')!;
  const status = currentModel.getBodyPartStatus(key as keyof BodyMeasurements);
  const range = config.normalRange;
  const position = status === 'danger' ? '偏高' : status === 'warning' ? '临界' : '正常';

  detail.innerHTML = `
    <div class="part-detail__card">
      <div class="part-detail__header">
        <span class="part-detail__icon">${config.icon}</span>
        <span class="part-detail__title">${label}</span>
      </div>
      <div class="part-detail__value">${value} ${config.unit}</div>
      <div class="part-detail__status part-detail__status--${status}">${position}</div>
      <div class="part-detail__range">正常范围：${range[0]} ~ ${range[1]} ${config.unit}</div>
    </div>
  `;
}

function bindEvents(): void {
  // 正面/背面切换
  document.querySelectorAll('[data-view]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-view]').forEach(b => b.classList.remove('body-panel__btn--active'));
      (btn as HTMLElement).classList.add('body-panel__btn--active');
      const view = (btn as HTMLElement).getAttribute('data-view')!;
      visualizer.setView(view as 'front' | 'back');
    });
  });

  // 标注/数值/缩放切换
  document.getElementById('toggle-labels')?.addEventListener('click', (e) => {
    visualizer.setShowLabels(!visualizer.options.showLabels);
    (e.target as HTMLElement).classList.toggle('body-panel__btn--active');
  });

  document.getElementById('toggle-values')?.addEventListener('click', (e) => {
    visualizer.setShowValues(!visualizer.options.showValues);
    (e.target as HTMLElement).classList.toggle('body-panel__btn--active');
  });

  document.getElementById('toggle-scale')?.addEventListener('click', (e) => {
    visualizer.setBodyScaleEnabled(!visualizer.options.bodyScaleEnabled);
    (e.target as HTMLElement).classList.toggle('body-panel__btn--active');
  });

  // Tab切换
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-tab]').forEach(b => b.classList.remove('body-panel__btn--active'));
      (btn as HTMLElement).classList.add('body-panel__btn--active');
      const tab = (btn as HTMLElement).getAttribute('data-tab') as 'circumference' | 'composition' | 'basic';
      renderMetricCards(tab);
    });
  });

  // 性别切换
  document.getElementById('gender-male')?.addEventListener('click', () => {
    currentGender = 'male';
    currentModel.setGender('male');
    previousModel?.setGender('male');
    document.getElementById('gender-male')!.classList.add('body-panel__btn--active');
    document.getElementById('gender-female')!.classList.remove('body-panel__btn--active');
    visualizer.update(currentModel);
    renderSummaryCards();
    renderMetricCards(activeTab);
    renderComparisonPanel();
  });

  document.getElementById('gender-female')?.addEventListener('click', () => {
    currentGender = 'female';
    currentModel.setGender('female');
    previousModel?.setGender('female');
    document.getElementById('gender-female')!.classList.add('body-panel__btn--active');
    document.getElementById('gender-male')!.classList.remove('body-panel__btn--active');
    visualizer.update(currentModel);
    renderSummaryCards();
    renderMetricCards(activeTab);
    renderComparisonPanel();
  });

  // 预设数据集
  document.querySelectorAll('[data-dataset]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-dataset]').forEach(b => b.classList.remove('body-panel__btn--active'));
      (btn as HTMLElement).classList.add('body-panel__btn--active');
      const datasetKey = (btn as HTMLElement).getAttribute('data-dataset')!;
      const dataset = ALL_DEMO_DATA[datasetKey];
      if (!dataset) return;

      const data = dataset.data;
      currentModel = new BodyModel(data, currentGender);
      visualizer.update(currentModel);
      renderSummaryCards();
      renderMetricCards(activeTab);
      renderComparisonPanel();
    });
  });
}

init();
