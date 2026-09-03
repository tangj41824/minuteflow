import { useI18n } from '../i18n'
import type { PipelineEvent, PipelineStage } from '../types'

function elapsed(from: string, to: string): string {
  const ms = new Date(to).getTime() - new Date(from).getTime()
  return ms >= 0 ? `${(ms / 1000).toFixed(1)}s` : ''
}

export function ProgressView({ events }: { events: PipelineEvent[] }) {
  const { t } = useI18n()
  const stageLabels: Record<PipelineStage, string> = {
    started: t('stage.started'),
    extracting: t('stage.extracting'),
    verifying: t('stage.verifying'),
    retrying: t('stage.retrying'),
    delivered: t('stage.delivered'),
    failed: t('stage.failed'),
  }
  const started = events.find((event) => event.stage === 'started')?.timestamp
  const failed = events.find((event) => event.stage === 'failed')
  const retries = events.filter((event) => event.stage === 'retrying').length
  const done = failed !== undefined || events.some((event) => event.stage === 'delivered')

  return (
    <section className="progress card">
      <h2>{done ? t('progress.finished') : t('progress.running')}</h2>
      {retries > 0 && (
        <span className="retry-badge">
          {t(retries === 1 ? 'progress.retryOne' : 'progress.retryMany', { count: retries })}
        </span>
      )}
      <ol className="timeline">
        {events.map((event, index) => (
          <li key={index} className={event.stage}>
            <span className="dot" />
            <span className="stage-name">{stageLabels[event.stage]}</span>
            {started && index > 0 && (
              <span className="stage-time">{elapsed(started, event.timestamp)}</span>
            )}
            {event.message && <span className="stage-message">{event.message}</span>}
          </li>
        ))}
      </ol>
      {failed && <p className="error-message">{failed.message}</p>}
      {!done && <p className="hint">{t('progress.waitHint')}</p>}
    </section>
  )
}
