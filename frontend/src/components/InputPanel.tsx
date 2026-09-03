import { useRef, useState } from 'react'
import { formatNumber, useI18n } from '../i18n'

interface Props {
  maxChars: number
  submitError: string | null
  onSubmit: (text: string, meetingDate: string | null) => void
}

export function InputPanel({ maxChars, submitError, onSubmit }: Props) {
  const { lang, t } = useI18n()
  const [text, setText] = useState('')
  const [meetingDate, setMeetingDate] = useState('')
  const [filename, setFilename] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const over = text.length > maxChars

  const handleFiles = async (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    setText(await file.text())
    setFilename(file.name)
  }

  return (
    <section className="input-panel card">
      <h2>{t('input.title')}</h2>
      <div
        className={dragging ? 'dropzone dragging' : 'dropzone'}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          void handleFiles(event.dataTransfer.files)
        }}
      >
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={t('input.placeholder')}
          rows={14}
        />
      </div>
      <div className="input-meta">
        <span className={over ? 'char-count over' : 'char-count'}>
          {formatNumber(text.length, lang)} / {formatNumber(maxChars, lang)}
        </span>
        <input
          ref={fileInput}
          type="file"
          accept=".md,.txt,.markdown,text/*"
          hidden
          onChange={(event) => {
            void handleFiles(event.target.files)
            event.target.value = ''
          }}
        />
        <button className="secondary" onClick={() => fileInput.current?.click()}>
          {filename ? t('input.fileChosen', { name: filename }) : t('input.chooseFile')}
        </button>
        <input
          type="date"
          value={meetingDate}
          onChange={(event) => setMeetingDate(event.target.value)}
          aria-label={t('input.meetingDate')}
        />
      </div>
      <button
        className="primary"
        disabled={!text.trim() || over}
        onClick={() => onSubmit(text, meetingDate || null)}
      >
        {t('input.submit')}
      </button>
      {over && <p className="hint">{t('input.tooLong', { max: formatNumber(maxChars, lang) })}</p>}
      {submitError && <p className="error-message">{submitError}</p>}
    </section>
  )
}
