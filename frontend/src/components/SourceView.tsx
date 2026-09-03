import { useEffect, useRef } from 'react'
import { useI18n } from '../i18n'
import type { MeetingActionReport } from '../types'

interface Props {
  source: string
  report: MeetingActionReport | null
  focusLine: number | null
}

export function SourceView({ source, report, focusLine }: Props) {
  const { t } = useI18n()
  const lineRefs = useRef<Map<number, HTMLDivElement>>(new Map())

  const cited = new Set<number>()
  for (const record of [...(report?.decisions ?? []), ...(report?.actions ?? [])]) {
    for (const reference of record.evidence) {
      for (let line = reference.start_line; line <= reference.end_line; line++) {
        cited.add(line)
      }
    }
  }

  // The highlight persists until the next evidence click or view change.
  useEffect(() => {
    if (focusLine === null) return
    const behavior = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
    lineRefs.current.get(focusLine)?.scrollIntoView({ behavior, block: 'center' })
  }, [focusLine])

  const lines = source.split('\n')
  return (
    <aside className="source-view card">
      <h3>{t('source.title', { count: lines.length })}</h3>
      <pre className="source-lines">
        {lines.map((line, index) => {
          const number = index + 1
          const isCited = cited.has(number)
          const isFocused = focusLine === number
          return (
            <div
              key={number}
              ref={(element) => {
                if (element) lineRefs.current.set(number, element)
                else lineRefs.current.delete(number)
              }}
              className={isFocused ? 'source-line cited focus' : isCited ? 'source-line cited' : 'source-line'}
            >
              <span className="line-number">{number}</span>
              <span className="line-text">{line || ' '}</span>
            </div>
          )
        })}
      </pre>
    </aside>
  )
}
