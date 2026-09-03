import { describe, expect, it } from 'vitest'
import { parseSSEFrame, readSSE } from './sse'

const FRAME = (
  index: number,
  stage: string,
): string => `id: ${index}\nevent: pipeline\ndata: {"stage":"${stage}","timestamp":"2026-09-02T10:00:00+00:00","retry_count":0,"message":null}\n\n`

function chunkedResponse(chunks: string[]): Response {
  const encoder = new TextEncoder()
  let position = 0
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (position < chunks.length) {
        controller.enqueue(encoder.encode(chunks[position]))
        position += 1
      } else {
        controller.close()
      }
    },
  })
  return new Response(stream)
}

describe('parseSSEFrame', () => {
  it('parses a well-formed frame', () => {
    const frame = parseSSEFrame(FRAME(3, 'verifying').trim())
    expect(frame?.index).toBe(3)
    expect(frame?.data.stage).toBe('verifying')
    expect(frame?.data.retry_count).toBe(0)
  })

  it('joins multi-line data fields', () => {
    const frame = parseSSEFrame('id: 0\ndata: {"stage":"failed",\ndata: "message":"boom"}')
    expect(frame?.data.message).toBe('boom')
  })

  it('rejects frames missing id, data, or valid JSON', () => {
    expect(parseSSEFrame('data: {"stage":"started"}')).toBeNull()
    expect(parseSSEFrame('id: 1')).toBeNull()
    expect(parseSSEFrame('id: 1\ndata: not-json')).toBeNull()
  })

  it('ignores heartbeat comments', () => {
    expect(parseSSEFrame(': ping')).toBeNull()
  })
})

describe('readSSE', () => {
  it('streams frames split across decoder chunks', async () => {
    const response = chunkedResponse([
      FRAME(0, 'started'),
      FRAME(1, 'extracting').slice(0, 40),
      FRAME(1, 'extracting').slice(40),
      FRAME(2, 'verifying'),
      ': ping\n\n',
    ])
    const frames = []
    for await (const frame of readSSE(response)) frames.push(frame)
    expect(frames.map((frame) => frame.index)).toEqual([0, 1, 2])
    expect(frames.map((frame) => frame.data.stage)).toEqual(['started', 'extracting', 'verifying'])
  })
})
