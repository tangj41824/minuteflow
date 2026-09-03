import { readSSE, type SSEFrame } from './sse'
import { t } from './i18n'
import type { HealthResponse, RunDetail, RunSummary } from './types'

async function detailOf(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown }
    return typeof payload.detail === 'string' ? payload.detail : t('api.requestFailed', { status: response.status })
  } catch {
    return t('api.requestFailed', { status: response.status })
  }
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health')
  if (!response.ok) throw new Error(await detailOf(response))
  return (await response.json()) as HealthResponse
}

export async function createRun(
  text: string,
  meetingDate: string | null,
): Promise<{ run_id: string; status: string; created_at: string }> {
  const response = await fetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, meeting_date: meetingDate || null }),
  })
  if (!response.ok) throw new Error(await detailOf(response))
  return (await response.json()) as { run_id: string; status: string; created_at: string }
}

export async function getRun(runId: string): Promise<RunDetail> {
  const response = await fetch(`/api/runs/${runId}`)
  if (!response.ok) throw new Error(await detailOf(response))
  return (await response.json()) as RunDetail
}

export async function listRuns(): Promise<RunSummary[]> {
  const response = await fetch('/api/runs')
  if (!response.ok) throw new Error(await detailOf(response))
  const payload = (await response.json()) as { runs: RunSummary[] }
  return payload.runs
}

export async function deleteRun(runId: string): Promise<void> {
  const response = await fetch(`/api/runs/${runId}`, { method: 'DELETE' })
  if (!response.ok && response.status !== 404) throw new Error(await detailOf(response))
}

export function exportUrl(runId: string, format: 'markdown' | 'json'): string {
  return `/api/runs/${runId}/export?format=${format}`
}

/** Stream run events starting after the given frame index. */
export async function* streamRunEvents(
  runId: string,
  after: number,
  signal: AbortSignal,
): AsyncGenerator<SSEFrame> {
  const response = await fetch(`/api/runs/${runId}/events?after=${after}`, { signal })
  if (!response.ok) throw new Error(await detailOf(response))
  yield* readSSE(response)
}
