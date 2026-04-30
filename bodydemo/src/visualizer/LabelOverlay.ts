import type { BodyModel } from '../models/BodyModel';
import { CIRCUMFERENCE_PARTS } from '../models/BodyPartConfig';
import type { BodyPartConfig } from '../models/BodyPartConfig';

interface LabelPoint {
  x: number;
  y: number;
  config: BodyPartConfig;
  value: number;
  status: 'normal' | 'warning' | 'danger';
  anchorX: number;
  anchorY: number;
}

const STATUS_COLORS: Record<string, string> = {
  normal: '#52c41a',
  warning: '#faad14',
  danger: '#ff4d4f',
};

const LABEL_POSITIONS: Record<string, { x: number; y: number; anchorX: number; anchorY: number }> = {
  neck: { x: 62, y: 8, anchorX: 50, anchorY: 10 },
  shoulderWidth: { x: 90, y: 18, anchorX: 50, anchorY: 20 },
  chest: { x: 5, y: 30, anchorX: 50, anchorY: 30 },
  waist: { x: 5, y: 48, anchorX: 50, anchorY: 46 },
  hip: { x: 5, y: 60, anchorX: 50, anchorY: 58 },
  leftUpperArm: { x: 5, y: 28, anchorX: 25, anchorY: 30 },
  rightUpperArm: { x: 90, y: 28, anchorX: 75, anchorY: 30 },
  leftForearm: { x: 0, y: 38, anchorX: 18, anchorY: 38 },
  rightForearm: { x: 95, y: 38, anchorX: 82, anchorY: 38 },
  leftThigh: { x: 5, y: 72, anchorX: 40, anchorY: 68 },
  rightThigh: { x: 90, y: 72, anchorX: 60, anchorY: 68 },
  leftCalf: { x: 5, y: 88, anchorX: 40, anchorY: 85 },
  rightCalf: { x: 90, y: 88, anchorX: 60, anchorY: 85 },
};

export class LabelOverlay {
  private container: HTMLElement;
  private svgEl: SVGElement | null = null;
  private labelsVisible = true;
  private valuesVisible = true;
  private highlightedKey: string | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  render(model: BodyModel): void {
    this.remove();
    const points = this.computeLabelPoints(model);
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('class', 'body-label-overlay');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';

    for (const pt of points) {
      const g = document.createElementNS(svgNS, 'g');
      g.setAttribute('class', `body-label body-label--${pt.status}`);
      g.setAttribute('data-key', pt.config.key);
      if (this.highlightedKey === pt.config.key) {
        g.classList.add('body-label--highlight');
      }

      const line = document.createElementNS(svgNS, 'line');
      line.setAttribute('x1', String(pt.anchorX));
      line.setAttribute('y1', String(pt.anchorY));
      line.setAttribute('x2', String(pt.x));
      line.setAttribute('y2', String(pt.y));
      line.setAttribute('stroke', STATUS_COLORS[pt.status]);
      line.setAttribute('stroke-width', '0.3');
      line.setAttribute('opacity', '0.6');

      const dot = document.createElementNS(svgNS, 'circle');
      dot.setAttribute('cx', String(pt.anchorX));
      dot.setAttribute('cy', String(pt.anchorY));
      dot.setAttribute('r', '0.8');
      dot.setAttribute('fill', STATUS_COLORS[pt.status]);

      const labelBg = document.createElementNS(svgNS, 'rect');
      const labelText = `${pt.config.label}`;
      const bgWidth = labelText.length * 1.8 + 3;
      const bgX = pt.x > 50 ? pt.x : pt.x - bgWidth;
      labelBg.setAttribute('x', String(bgX));
      labelBg.setAttribute('y', String(pt.y - 1.5));
      labelBg.setAttribute('width', String(bgWidth));
      labelBg.setAttribute('height', '3');
      labelBg.setAttribute('rx', '0.8');
      labelBg.setAttribute('fill', STATUS_COLORS[pt.status]);
      labelBg.setAttribute('opacity', '0.15');

      const text = document.createElementNS(svgNS, 'text');
      const textX = pt.x > 50 ? pt.x + 0.5 : pt.x - 0.5;
      text.setAttribute('x', String(textX));
      text.setAttribute('y', String(pt.y + 0.5));
      text.setAttribute('font-size', '1.6');
      text.setAttribute('fill', STATUS_COLORS[pt.status]);
      text.setAttribute('text-anchor', pt.x > 50 ? 'start' : 'end');
      text.setAttribute('font-weight', '600');
      text.textContent = this.valuesVisible
        ? `${pt.config.label} ${pt.value}${pt.config.unit}`
        : pt.config.label;

      g.appendChild(line);
      g.appendChild(dot);
      g.appendChild(labelBg);
      g.appendChild(text);
      svg.appendChild(g);
    }

    this.container.appendChild(svg);
    this.svgEl = svg;
    if (!this.labelsVisible) {
      svg.style.display = 'none';
    }
  }

  update(model: BodyModel): void {
    this.render(model);
  }

  highlight(key: string): void {
    this.highlightedKey = key;
    if (!this.svgEl) return;
    // 先清除所有高亮
    this.svgEl.querySelectorAll('.body-label--highlight').forEach(el => el.classList.remove('body-label--highlight'));
    // 高亮新的
    const el = this.svgEl.querySelector(`[data-key="${key}"]`);
    if (el) {
      el.classList.add('body-label--highlight');
    }
  }

  clearHighlight(): void {
    this.highlightedKey = null;
    if (!this.svgEl) return;
    this.svgEl.querySelectorAll('.body-label--highlight').forEach(el => el.classList.remove('body-label--highlight'));
  }

  setLabelsVisible(visible: boolean): void {
    this.labelsVisible = visible;
    if (this.svgEl) {
      this.svgEl.style.display = visible ? '' : 'none';
    }
  }

  setValuesVisible(visible: boolean): void {
    this.valuesVisible = visible;
  }

  remove(): void {
    if (this.svgEl && this.svgEl.parentNode) {
      this.svgEl.parentNode.removeChild(this.svgEl);
    }
    this.svgEl = null;
  }

  destroy(): void {
    this.remove();
  }

  private computeLabelPoints(model: BodyModel): LabelPoint[] {
    const points: LabelPoint[] = [];
    const allParts = [...CIRCUMFERENCE_PARTS];

    for (const config of allParts) {
      const pos = LABEL_POSITIONS[config.key];
      if (!pos) continue;
      const value = model.raw[config.key as keyof typeof model.raw];
      if (typeof value !== 'number' || value <= 0) continue;
      const status = model.getBodyPartStatus(config.key as keyof typeof model.raw);
      points.push({
        x: pos.x,
        y: pos.y,
        anchorX: pos.anchorX,
        anchorY: pos.anchorY,
        config,
        value,
        status,
      });
    }
    return points;
  }
}
