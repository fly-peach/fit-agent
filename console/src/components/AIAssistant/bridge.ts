export const OPEN_CARD_GENERATION_EVENT = 'fitagent:open-card-generation'
export const START_CARD_GENERATION_EVENT = 'fitagent:start-card-generation'
export const CARD_RESULT_SAVED_EVENT = 'fitagent:card-result-saved'
export const CARD_RESULT_FAILED_EVENT = 'fitagent:card-result-failed'

export interface CardGenerationRequestDetail {
  source: 'training-results-card'
  templateKey: string
  styleTemplateKey?: string
  styleTemplateSummary?: string
  styleTemplatePreviewHtml?: string
  styleTemplatePromptHint?: string
  styleTemplateHighlights?: string[]
  title: string
  promptText: string
  periodType?: 'week' | 'month' | 'custom'
  periodStart?: string
  periodEnd?: string
}

export interface CardResultSavedDetail {
  source: 'training-results-card'
  sessionId: string
  snapshotId: number
  title: string
  templateKey: string
  periodType?: string
  periodStart?: string
  periodEnd?: string
}

export interface CardResultFailedDetail {
  source: 'training-results-card'
  sessionId?: string
  title: string
  templateKey: string
  message: string
}

export function requestCardGeneration(detail: CardGenerationRequestDetail) {
  window.dispatchEvent(new CustomEvent(OPEN_CARD_GENERATION_EVENT, { detail }))
}

export function startCardGeneration(detail: CardGenerationRequestDetail) {
  window.dispatchEvent(new CustomEvent(START_CARD_GENERATION_EVENT, { detail }))
}

export function emitCardResultSaved(detail: CardResultSavedDetail) {
  window.dispatchEvent(new CustomEvent(CARD_RESULT_SAVED_EVENT, { detail }))
}

export function emitCardResultFailed(detail: CardResultFailedDetail) {
  window.dispatchEvent(new CustomEvent(CARD_RESULT_FAILED_EVENT, { detail }))
}
