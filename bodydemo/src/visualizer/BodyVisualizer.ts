import { BodyChart, ViewSide, type BodyState, type MuscleId, FRONT_MUSCLES, BACK_MUSCLES } from 'body-muscles';
import type { MuscleDef } from 'body-muscles';
import { BodyModel } from '../models/BodyModel';
import { ALL_PART_CONFIGS, getMuscleIdToPartKeyMap } from '../models/BodyPartConfig';
import { LabelOverlay } from './LabelOverlay';

export interface BodyVisualizationConfig {
  showLabels: boolean;
  showValues: boolean;
  showNormalRange: boolean;
  highlightAbnormal: boolean;
  animationEnabled: boolean;
  bodyScaleEnabled: boolean;
}

const DEFAULT_CONFIG: BodyVisualizationConfig = {
  showLabels: true,
  showValues: true,
  showNormalRange: true,
  highlightAbnormal: true,
  animationEnabled: true,
  bodyScaleEnabled: true,
};

type VisualizerEvent = 'partClick' | 'partHover';
type EventCallback = (data: { key: string; value: number; label: string }) => void;

export class BodyVisualizer {
  private container: HTMLElement;
  private chartContainer: HTMLElement;
  private chart: BodyChart | null = null;
  private labelOverlay: LabelOverlay;
  private model: BodyModel | null = null;
  private config: BodyVisualizationConfig;
  private currentView: 'front' | 'back' = 'front';
  private listeners: Map<VisualizerEvent, EventCallback[]> = new Map();
  private muscleToPartKey: Record<string, string>;
  private muscleNameToId: Map<string, MuscleId> = new Map();

  constructor(container: HTMLElement, config?: Partial<BodyVisualizationConfig>) {
    this.container = container;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.muscleToPartKey = getMuscleIdToPartKeyMap();
    this.buildNameToIdMap();

    this.chartContainer = document.createElement('div');
    this.chartContainer.className = 'body-chart-container';
    this.container.appendChild(this.chartContainer);

    this.labelOverlay = new LabelOverlay(this.container);
  }

  private buildNameToIdMap(): void {
    const allMuscles: MuscleDef[] = [...FRONT_MUSCLES, ...BACK_MUSCLES];
    for (const m of allMuscles) {
      this.muscleNameToId.set(m.name, m.id);
    }
  }

  render(model: BodyModel): void {
    this.model = model;
    this.destroyChart();

    const bodyState = this.buildBodyState(model);

    this.chart = new BodyChart(this.chartContainer, {
      view: this.currentView === 'front' ? ViewSide.FRONT : ViewSide.BACK,
      bodyState,
      onMuscleClick: (id: MuscleId, _name: string) => {
        this.handleMuscleClick(id);
      },
      onMuscleHover: (id: MuscleId | null) => {
        if (id) this.handleMuscleHover(id);
      },
      enableTransitions: this.config.animationEnabled,
    });

    this.tagMusclePaths();

    requestAnimationFrame(() => {
      this.applyMuscleScale(model);
    });

    this.labelOverlay.setValuesVisible(this.config.showValues);
    this.labelOverlay.render(model);
  }

  update(model: BodyModel): void {
    this.model = model;
    if (!this.chart) {
      this.render(model);
      return;
    }
    const bodyState = this.buildBodyState(model);
    this.chart.update({ bodyState });

    requestAnimationFrame(() => {
      if (this.config.bodyScaleEnabled) {
        this.applyMuscleScale(model);
      }
    });

    this.labelOverlay.update(model);
  }

  highlight(parts: string[]): void {
    if (!this.chart || !this.model) return;
    const svg = this.chartContainer.querySelector('svg');
    if (!svg) return;

    svg.querySelectorAll<SVGPathElement>('.body-chart-muscle').forEach(path => {
      const mId = (path as SVGElement & { _muscleId?: string })._muscleId;
      const isHighlighted = mId && parts.some(p => {
        const config = ALL_PART_CONFIGS.find(c => c.key === p);
        return config && config.muscleIds.includes(mId);
      });
      path.setAttribute('stroke', isHighlighted ? '#ffffff' : '#1e293b');
      path.setAttribute('stroke-width', isHighlighted ? '0.3' : '0.1');
    });
  }

  setView(side: 'front' | 'back'): void {
    this.currentView = side;
    if (this.model) {
      this.render(this.model);
    }
  }

  setConfig(config: Partial<BodyVisualizationConfig>): void {
    this.config = { ...this.config, ...config };
    this.labelOverlay.setLabelsVisible(this.config.showLabels);
    this.labelOverlay.setValuesVisible(this.config.showValues);
    if (this.model) {
      this.update(this.model);
    }
  }

  setShowLabels(value: boolean): void {
    this.config.showLabels = value;
    this.labelOverlay.setLabelsVisible(value);
  }

  setShowValues(value: boolean): void {
    this.config.showValues = value;
    this.labelOverlay.setValuesVisible(value);
  }

  setBodyScaleEnabled(value: boolean): void {
    this.config.bodyScaleEnabled = value;
    if (this.model) {
      this.update(this.model);
    }
  }

  get options(): BodyVisualizationConfig {
    return this.config;
  }

  get labelOverlayPublic(): LabelOverlay {
    return this.labelOverlay;
  }

  on(event: VisualizerEvent, callback: EventCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: VisualizerEvent, callback: EventCallback): void {
    const list = this.listeners.get(event);
    if (list) {
      const idx = list.indexOf(callback);
      if (idx >= 0) list.splice(idx, 1);
    }
  }

  destroy(): void {
    this.destroyChart();
    this.labelOverlay.destroy();
    this.listeners.clear();
    if (this.chartContainer.parentNode) {
      this.chartContainer.parentNode.removeChild(this.chartContainer);
    }
  }

  private tagMusclePaths(): void {
    const svg = this.chartContainer.querySelector('svg');
    if (!svg) return;

    svg.querySelectorAll<SVGPathElement>('.body-chart-muscle').forEach(path => {
      const titleEl = path.querySelector('title');
      if (titleEl) {
        const name = titleEl.textContent || '';
        const mId = this.muscleNameToId.get(name);
        if (mId) {
          (path as SVGElement & { _muscleId?: string })._muscleId = mId;
        }
      }
    });
  }

  private buildBodyState(_model: BodyModel): BodyState {
    const state: BodyState = {};
    for (const config of ALL_PART_CONFIGS) {
      if (config.muscleIds.length === 0) continue;
      for (const mId of config.muscleIds) {
        state[mId] = { intensity: 0, selected: false };
      }
    }
    return state;
  }

  private applyMuscleScale(model: BodyModel): void {
    const svg = this.chartContainer.querySelector('svg');
    if (!svg) return;
    const gender = model.currentGender;

    const chartContainer = this.chartContainer;
    chartContainer.classList.remove('female-body-shape');
    if (gender === 'female') {
      chartContainer.classList.add('female-body-shape');
    }

    svg.querySelectorAll<SVGPathElement>('.body-chart-muscle').forEach(path => {
      const mId = (path as SVGElement & { _muscleId?: string })._muscleId;
      if (!mId) return;

      const partKey = this.muscleToPartKey[mId];
      if (!partKey) return;

      const config = ALL_PART_CONFIGS.find(c => c.key === partKey);
      if (!config) return;

      const mk = config.key as keyof typeof model.raw;
      const currentVal = model.raw[mk];
      const range = gender === 'female' ? config.normalRangeFemale : config.normalRange;
      const baseVal = (range[0] + range[1]) / 2;
      if (typeof currentVal !== 'number' || baseVal <= 0) return;

      const ratio = currentVal / baseVal;
      const scale = Math.max(0.5, Math.min(1.8, 1 + (ratio - 1) * 1.4));

      let totalScale = scale;
      if (gender === 'female') {
        if (mId.includes('shoulder') || mId.includes('neck')) {
          totalScale = scale * 0.82;
        } else if (mId.includes('chest') || mId.includes('pectoralis')) {
          totalScale = scale * 1.1;
        } else if (mId.includes('obliques') || mId.includes('abs') || mId.includes('waist')) {
          totalScale = scale * 0.85;
        } else if (mId.includes('hip') || mId.includes('glutes') || mId.includes('hip-flexor')) {
          totalScale = scale * 1.2;
        }
      }

      try {
        const bbox = path.getBBox();
        if (bbox.width === 0 || bbox.height === 0) return;
        const cx = bbox.x + bbox.width / 2;
        const cy = bbox.y + bbox.height / 2;

        path.style.transformOrigin = `${cx}px ${cy}px`;
        path.style.transform = `scale(${totalScale})`;
        path.style.transition = this.config.animationEnabled ? 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none';
      } catch {
        // getBBox may fail if element not rendered yet
      }
    });
  }

  private handleMuscleClick(muscleId: MuscleId): void {
    const partKey = this.muscleToPartKey[muscleId];
    if (!partKey || !this.model) return;
    const config = ALL_PART_CONFIGS.find(c => c.key === partKey);
    if (!config) return;
    const value = this.model.raw[partKey as keyof typeof this.model.raw];
    if (typeof value !== 'number') return;
    const callbacks = this.listeners.get('partClick') || [];
    for (const cb of callbacks) {
      cb({ key: partKey, value, label: config.label });
    }
  }

  private handleMuscleHover(muscleId: MuscleId): void {
    const partKey = this.muscleToPartKey[muscleId];
    if (!partKey || !this.model) return;
    const config = ALL_PART_CONFIGS.find(c => c.key === partKey);
    if (!config) return;
    const value = this.model.raw[partKey as keyof typeof this.model.raw];
    if (typeof value !== 'number') return;
    const callbacks = this.listeners.get('partHover') || [];
    for (const cb of callbacks) {
      cb({ key: partKey, value, label: config.label });
    }
  }

  private destroyChart(): void {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
    this.chartContainer.innerHTML = '';
  }
}
