import { useI18n } from '../i18n'
import type { EvidenceReference, RunDetail } from '../types'

interface Props {
  run: RunDetail
  onFocusLine: (line: number) => void
}

function EvidenceLinks({
  evidence,
  onFocusLine,
}: {
  evidence: EvidenceReference[]
  onFocusLine: (line: number) => void
}) {
  return (
    <span className="evidence-tags">
      {evidence.map((reference) => (
        <button
          key={reference.line_range}
          className="evidence-link"
          title={reference.text}
          onClick={() => onFocusLine(reference.start_line)}
        >
          {reference.line_range}
        </button>
      ))}
    </span>
  )
}

export function ReportView({ run, onFocusLine }: Props) {
  const { t } = useI18n()
  const report = run.report
  if (!report) {
    return (
      <section className="report card">
        <div className="group">
          <h2>{t('report.runFailed')}</h2>
          <p className="error-message">{run.error ?? t('report.unknownError')}</p>
        </div>
      </section>
    )
  }
  return (
    <section className="report card">
      {report.errors.length > 0 && (
        <div className="group">
          <h3>{t('report.errors')}</h3>
          <ul>
            {report.errors.map((error, index) => (
              <li key={index} className="note-row">
                <span className="dot danger" />
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="group">
        <h3>{t('report.summary')}</h3>
        <p>{report.summary}</p>
      </div>
      <div className="group">
        <h3>{t('report.decisions')}</h3>
        {report.decisions.length === 0 ? (
          <p className="hint">{t('report.none')}</p>
        ) : (
          <ul>
            {report.decisions.map((decision) => (
              <li key={decision.id} className="record">
                <div className="record-head">
                  <span className="record-id">{decision.id}</span>
                  <span className="record-text">{decision.statement}</span>
                </div>
                <EvidenceLinks evidence={decision.evidence} onFocusLine={onFocusLine} />
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="group">
        <h3>{t('report.actions')}</h3>
        {report.actions.length === 0 ? (
          <p className="hint">{t('report.none')}</p>
        ) : (
          <ul>
            {report.actions.map((action) => (
              <li key={action.id} className="record">
                <div className="record-head">
                  <span className="record-id">{action.id}</span>
                  <span className="record-text">{action.task}</span>
                </div>
                <div className="record-meta">
                  <span className={action.status === 'confirmed' ? 'dot ok' : 'dot warn'} />
                  <span>
                    {t('report.owner')} {action.owner ?? t('report.notSpecified')} ·{' '}
                    {t('report.due')} {action.due_date ?? t('report.notSpecified')} ·{' '}
                    {action.status === 'confirmed'
                      ? t('report.statusConfirmed')
                      : t('report.statusNeedsClarification')}
                  </span>
                </div>
                <EvidenceLinks evidence={action.evidence} onFocusLine={onFocusLine} />
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="group">
        <h3>{t('report.questions')}</h3>
        {report.clarification_questions.length === 0 ? (
          <p className="hint">{t('report.none')}</p>
        ) : (
          <ul>
            {report.clarification_questions.map((question, index) => (
              <li key={index} className="note-row">
                <span className="dot info" />
                <span>{question}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="group">
        <h3>{t('report.warnings')}</h3>
        {report.warnings.length === 0 ? (
          <p className="hint">{t('report.none')}</p>
        ) : (
          <ul>
            {report.warnings.map((warning, index) => (
              <li key={index} className="note-row">
                <span className="dot warn" />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="group">
        <h3>{t('report.metadata')}</h3>
        <ul className="metadata">
          <li>
            <span className="label">{t('report.meetingDate')}</span>
            <span>{report.meeting_date ?? t('report.notProvided')}</span>
          </li>
          <li>
            <span className="label">{t('report.sourceLines')}</span>
            <span>{report.source_line_count}</span>
          </li>
          <li>
            <span className="label">{t('report.retries')}</span>
            <span>{report.retry_count}</span>
          </li>
        </ul>
      </div>
    </section>
  )
}
