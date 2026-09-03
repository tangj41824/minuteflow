import { exportUrl } from '../api'
import { formatDate, useI18n } from '../i18n'
import type { RunSummary } from '../types'

interface Props {
  runs: RunSummary[]
  currentId: string | null
  onSelect: (runId: string) => void
  onDelete: (runId: string) => void
  onRefresh: () => void
}

export function HistorySidebar({ runs, currentId, onSelect, onDelete, onRefresh }: Props) {
  const { lang, t } = useI18n()
  return (
    <aside className="history">
      <div className="history-header">
        <h3>{t('sidebar.title')}</h3>
        <button className="secondary" onClick={onRefresh}>
          {t('sidebar.refresh')}
        </button>
      </div>
      {runs.length === 0 ? (
        <p className="hint">{t('sidebar.empty')}</p>
      ) : (
        <ul className="history-list">
          {runs.map((run) => (
            <li key={run.run_id} className={run.run_id === currentId ? 'selected' : ''}>
              <button className="run-item" onClick={() => onSelect(run.run_id)}>
                <span className={`status-dot ${run.status}`} title={t(`status.${run.status}`)} />
                <span className="run-title">{run.summary ?? run.error ?? '…'}</span>
                <span className="run-date">{formatDate(run.created_at, lang)}</span>
              </button>
              {run.status !== 'running' && (
                <div className="run-actions">
                  <a href={exportUrl(run.run_id, 'markdown')} download>
                    md
                  </a>
                  <a href={exportUrl(run.run_id, 'json')} download>
                    json
                  </a>
                  <button className="danger" onClick={() => onDelete(run.run_id)}>
                    {t('sidebar.delete')}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}
