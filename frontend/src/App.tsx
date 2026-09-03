import { useCallback, useEffect, useRef, useState } from 'react'
import { createRun, deleteRun, getHealth, getRun, listRuns, streamRunEvents } from './api'
import type { HealthResponse, PipelineEvent, RunDetail, RunSummary } from './types'
import { useI18n } from './i18n'
import { HistorySidebar } from './components/HistorySidebar'
import { InputPanel } from './components/InputPanel'
import { ProgressView } from './components/ProgressView'
import { ReportView } from './components/ReportView'
import { SourceView } from './components/SourceView'

export default function App() {
  const { lang, setLang, t } = useI18n()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [offline, setOffline] = useState(false)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [current, setCurrent] = useState<RunDetail | null>(null)
  const [events, setEvents] = useState<PipelineEvent[]>([])
  const [runningId, setRunningId] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [focusLine, setFocusLine] = useState<number | null>(null)
  const [activeView, setActiveView] = useState<'report' | 'source'>('report')
  const abortRef = useRef<AbortController | null>(null)

  const refreshHistory = useCallback(async () => {
    try {
      setRuns(await listRuns())
      setOffline(false)
    } catch {
      setOffline(true)
    }
  }, [])

  const loadHealth = useCallback(async () => {
    try {
      setHealth(await getHealth())
      setOffline(false)
    } catch {
      setOffline(true)
    }
  }, [])

  useEffect(() => {
    void loadHealth()
    void refreshHistory()
  }, [loadHealth, refreshHistory])

  useEffect(() => () => abortRef.current?.abort(), [])

  const watchRun = useCallback(
    async (runId: string) => {
      setRunningId(runId)
      setCurrent(null)
      setEvents([])
      setSubmitError(null)
      setFocusLine(null)
      setActiveView('report')
      let lastIndex = -1
      let finished = false
      while (!finished) {
        const controller = new AbortController()
        abortRef.current = controller
        try {
          for await (const frame of streamRunEvents(runId, lastIndex + 1, controller.signal)) {
            lastIndex = frame.index
            setEvents((previous) => [...previous, frame.data])
            if (frame.data.stage === 'delivered' || frame.data.stage === 'failed') {
              finished = true
              break
            }
          }
        } catch {
          if (controller.signal.aborted) return
        }
        if (!finished) {
          // Stream ended without a terminal event: reconcile via the run endpoint.
          try {
            const detail = await getRun(runId)
            if (detail.status === 'delivered' || detail.status === 'failed') {
              setCurrent(detail)
              finished = true
            }
          } catch {
            setOffline(true)
            break
          }
        }
      }
      if (finished) {
        try {
          setCurrent(await getRun(runId))
        } catch {
          setOffline(true)
        }
        setRunningId(null)
        void refreshHistory()
      }
    },
    [refreshHistory],
  )

  const handleSubmit = useCallback(
    async (text: string, meetingDate: string | null) => {
      try {
        const { run_id } = await createRun(text, meetingDate)
        await watchRun(run_id)
      } catch (error) {
        setSubmitError(error instanceof Error ? error.message : String(error))
      }
    },
    [watchRun],
  )

  const handleSelect = useCallback(async (runId: string) => {
    abortRef.current?.abort()
    setRunningId(null)
    setEvents([])
    setFocusLine(null)
    setActiveView('report')
    try {
      setCurrent(await getRun(runId))
    } catch {
      setOffline(true)
    }
  }, [])

  const handleDelete = useCallback(
    async (runId: string) => {
      if (!window.confirm(t('app.deleteConfirm'))) return
      try {
        await deleteRun(runId)
        if (current?.run_id === runId) setCurrent(null)
        await refreshHistory()
      } catch {
        setOffline(true)
      }
    },
    [current, refreshHistory, t],
  )

  const handleFocusLine = useCallback((line: number) => {
    setActiveView('source')
    setFocusLine(line)
  }, [])

  const retryConnection = useCallback(() => {
    void loadHealth()
    void refreshHistory()
  }, [loadHealth, refreshHistory])

  const noKey = health !== null && !health.api_key_configured

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="brand">
          <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
            <defs>
              <linearGradient id="mf-logo" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#0a84ff" />
                <stop offset="1" stopColor="#0060df" />
              </linearGradient>
            </defs>
            <rect width="24" height="24" rx="6.5" fill="url(#mf-logo)" />
            <g stroke="#ffffff" strokeWidth="1.7" strokeLinecap="round">
              <path d="M7 8.2h10" />
              <path d="M7 12h10" />
              <path d="M7 15.8h6" />
            </g>
          </svg>
          MinuteFlow
        </h1>
        <div className="header-controls">
          <div className="segmented" role="group" aria-label={t('app.langLabel')}>
            <button aria-selected={lang === 'zh'} onClick={() => setLang('zh')}>
              中文
            </button>
            <button aria-selected={lang === 'en'} onClick={() => setLang('en')}>
              EN
            </button>
          </div>
          {health && <span className="model-badge">{health.model}</span>}
          {noKey && (
            <span className="key-warning" title={t('app.keyWarning')}>
              {t('app.keyWarning')}
            </span>
          )}
        </div>
      </header>
      {offline && (
        <div className="offline-banner">
          <span>
            {t('app.offlinePrefix')} <code>minuteflow web</code> {t('app.offlineSuffix')}
          </span>
          <button className="secondary" onClick={retryConnection}>
            {t('app.retry')}
          </button>
        </div>
      )}
      <div className="layout">
        <HistorySidebar
          runs={runs}
          currentId={current?.run_id ?? runningId}
          onSelect={(runId) => void handleSelect(runId)}
          onDelete={(runId) => void handleDelete(runId)}
          onRefresh={() => void refreshHistory()}
        />
        <main className="main">
          <div className="content-column">
            {runningId ? (
              <ProgressView events={events} />
            ) : current ? (
              <>
                {current.source_text && current.report && (
                  <div className="segmented view-switcher" role="tablist" aria-label={t('tabs.label')}>
                    <button
                      role="tab"
                      aria-selected={activeView === 'report'}
                      onClick={() => setActiveView('report')}
                    >
                      {t('tabs.report')}
                    </button>
                    <button
                      role="tab"
                      aria-selected={activeView === 'source'}
                      onClick={() => setActiveView('source')}
                    >
                      {t('tabs.source')}
                    </button>
                  </div>
                )}
                <div hidden={activeView !== 'report'}>
                  <ReportView run={current} onFocusLine={handleFocusLine} />
                </div>
                {current.source_text && (
                  <div hidden={activeView !== 'source'}>
                    <SourceView source={current.source_text} report={current.report} focusLine={focusLine} />
                  </div>
                )}
              </>
            ) : (
              <InputPanel
                maxChars={health?.max_input_chars ?? 100000}
                submitError={submitError}
                onSubmit={(text, meetingDate) => void handleSubmit(text, meetingDate)}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
