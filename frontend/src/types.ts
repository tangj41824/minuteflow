// TypeScript mirrors of the Pydantic API contracts in src/minuteflow/web/models.py
// and src/minuteflow/schemas.py.

export type PipelineStage =
  | 'started'
  | 'extracting'
  | 'verifying'
  | 'retrying'
  | 'delivered'
  | 'failed'

export interface PipelineEvent {
  stage: PipelineStage
  timestamp: string // ISO-8601 with offset
  retry_count: number
  message: string | null
}

export interface EvidenceReference {
  start_line: number
  end_line: number
  line_range: string
  text: string
}

export interface DecisionRecord {
  id: string
  statement: string
  evidence: EvidenceReference[]
}

export interface ActionRecord {
  id: string
  task: string
  owner: string | null
  due_date: string | null
  status: 'confirmed' | 'needs_clarification'
  evidence: EvidenceReference[]
}

export interface MeetingActionReport {
  summary: string
  decisions: DecisionRecord[]
  actions: ActionRecord[]
  clarification_questions: string[]
  warnings: string[]
  errors: string[]
  retry_count: number
  source_line_count: number
  meeting_date: string | null
}

export type RunStatus = 'running' | 'delivered' | 'failed'

export interface RunSummary {
  run_id: string
  created_at: string
  status: RunStatus
  meeting_date: string | null
  summary: string | null
  retry_count: number | null
  error: string | null
}

export interface RunDetail {
  run_id: string
  created_at: string
  status: RunStatus
  meeting_date: string | null
  source_text: string | null
  events: PipelineEvent[]
  report: MeetingActionReport | null
  error: string | null
}

export interface HealthResponse {
  status: 'ok'
  version: string
  model: string
  api_key_configured: boolean
  max_input_chars: number
  max_concurrent_runs: number
  history_dir: string
}
