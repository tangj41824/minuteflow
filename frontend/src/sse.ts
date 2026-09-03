import type { PipelineEvent } from './types'

export interface SSEFrame {
  index: number
  data: PipelineEvent
}

/** Parse one complete SSE frame block (a blank-line-separated chunk). */
export function parseSSEFrame(block: string): SSEFrame | null {
  let index: number | null = null
  let data: string | null = null
  for (const line of block.split('\n')) {
    if (line.startsWith('id: ')) {
      const parsed = Number(line.slice(4).trim())
      if (Number.isInteger(parsed)) index = parsed
    } else if (line.startsWith('data: ')) {
      data = data === null ? line.slice(6) : `${data}\n${line.slice(6)}`
    }
  }
  if (index === null || data === null) return null
  try {
    return { index, data: JSON.parse(data) as PipelineEvent }
  } catch {
    return null
  }
}

/** Stream SSE frames from a fetch response body, splitting on blank lines. */
export async function* readSSE(response: Response): AsyncGenerator<SSEFrame> {
  if (!response.body) return
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let split: number
      while ((split = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, split)
        buffer = buffer.slice(split + 2)
        if (block.trim() === '' || block.trimStart().startsWith(':')) continue
        const frame = parseSSEFrame(block)
        if (frame) yield frame
      }
    }
    buffer += decoder.decode()
    const block = buffer.trim()
    if (block && !block.startsWith(':')) {
      const frame = parseSSEFrame(block)
      if (frame) yield frame
    }
  } finally {
    reader.releaseLock()
  }
}
