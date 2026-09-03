import { createContext, useContext, useState, type ReactNode } from 'react'

export type Language = 'en' | 'zh'

export const STORAGE_KEY = 'minuteflow.lang'

export const LOCALES: Record<Language, string> = { en: 'en-US', zh: 'zh-CN' }

const en = {
  app: {
    keyWarning: 'No API key configured — live runs will fail',
    offlinePrefix: 'Cannot reach the MinuteFlow server. Start it with',
    offlineSuffix: '.',
    retry: 'Retry',
    deleteConfirm: 'Delete this run from local history?',
    langLabel: 'Language',
  },
  tabs: {
    label: 'Main view',
    report: 'Report',
    source: 'Source',
  },
  sidebar: {
    title: 'History',
    refresh: 'Refresh',
    empty: 'No runs yet.',
    delete: 'Delete',
  },
  status: {
    running: 'running',
    delivered: 'delivered',
    failed: 'failed',
  },
  input: {
    title: 'Meeting notes',
    placeholder: 'Paste Markdown or plain-text meeting notes here, or drop a file…',
    chooseFile: 'Choose file',
    fileChosen: 'File: {name}',
    meetingDate: 'Meeting date',
    submit: 'Run pipeline',
    tooLong: 'Input exceeds the {max}-character limit.',
  },
  progress: {
    running: 'Running pipeline',
    finished: 'Finished',
    retryOne: '{count} retry',
    retryMany: '{count} retries',
    waitHint: 'The pipeline is calling the configured model. This can take a minute.',
  },
  stage: {
    started: 'Started',
    extracting: 'Extracting',
    verifying: 'Verifying',
    retrying: 'Retrying',
    delivered: 'Delivered',
    failed: 'Failed',
  },
  report: {
    runFailed: 'Run failed',
    unknownError: 'Unknown error.',
    errors: 'Errors',
    summary: 'Summary',
    decisions: 'Decisions',
    actions: 'Actions',
    questions: 'Clarification questions',
    warnings: 'Warnings',
    metadata: 'Run metadata',
    none: 'None.',
    owner: 'Owner',
    due: 'Due',
    statusLabel: 'Status',
    statusConfirmed: 'confirmed',
    statusNeedsClarification: 'needs clarification',
    notSpecified: 'not specified',
    meetingDate: 'Meeting date',
    notProvided: 'not provided',
    sourceLines: 'Source lines',
    retries: 'Extraction retries',
  },
  source: {
    title: 'Source ({count} lines)',
  },
  api: {
    requestFailed: 'Request failed ({status})',
  },
}

// `zh` is checked against this shape: a missing or extra key is a compile error.
type Messages = typeof en

const zh: Messages = {
  app: {
    keyWarning: '未配置 API 密钥 — 实时运行将失败',
    offlinePrefix: '无法连接 MinuteFlow 服务。请使用',
    offlineSuffix: '启动。',
    retry: '重试',
    deleteConfirm: '从本地历史记录中删除这条运行？',
    langLabel: '语言',
  },
  tabs: {
    label: '主视图',
    report: '报告',
    source: '原文',
  },
  sidebar: {
    title: '历史记录',
    refresh: '刷新',
    empty: '暂无运行记录。',
    delete: '删除',
  },
  status: {
    running: '运行中',
    delivered: '已交付',
    failed: '失败',
  },
  input: {
    title: '会议记录',
    placeholder: '在此粘贴 Markdown 或纯文本会议记录，或将文件拖入…',
    chooseFile: '选择文件',
    fileChosen: '文件：{name}',
    meetingDate: '会议日期',
    submit: '运行流水线',
    tooLong: '输入超过 {max} 字符上限。',
  },
  progress: {
    running: '流水线运行中',
    finished: '已完成',
    retryOne: '{count} 次重试',
    retryMany: '{count} 次重试',
    waitHint: '流水线正在调用已配置的模型，可能需要一分钟。',
  },
  stage: {
    started: '已开始',
    extracting: '提取中',
    verifying: '验证中',
    retrying: '重试中',
    delivered: '已交付',
    failed: '失败',
  },
  report: {
    runFailed: '运行失败',
    unknownError: '未知错误。',
    errors: '错误',
    summary: '摘要',
    decisions: '决议',
    actions: '行动项',
    questions: '待澄清问题',
    warnings: '警告',
    metadata: '运行元数据',
    none: '无。',
    owner: '负责人',
    due: '截止',
    statusLabel: '状态',
    statusConfirmed: '已确认',
    statusNeedsClarification: '待澄清',
    notSpecified: '未指定',
    meetingDate: '会议日期',
    notProvided: '未提供',
    sourceLines: '原文行数',
    retries: '提取重试次数',
  },
  source: {
    title: '原文（{count} 行）',
  },
  api: {
    requestFailed: '请求失败（{status}）',
  },
}

// The catalog is intentionally two levels deep, so key paths can be a simple
// non-recursive mapped type (a recursive Leaves type trips TS2589 here).
export type MessageKey = {
  [S in keyof Messages]: `${string & S}.${string & keyof Messages[S]}`
}[keyof Messages]

const CATALOGS: Record<Language, Messages> = { en, zh }

function readInitial(): Language {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'zh') return stored
  } catch {
    // localStorage can be unavailable (private mode, tests).
  }
  return 'zh'
}

// Module-level language so non-React code (api.ts) can translate too.
let currentLang: Language = readInitial()

if (typeof document !== 'undefined') {
  document.documentElement.lang = LOCALES[currentLang]
}

function lookup(key: MessageKey, lang: Language): string {
  let node: unknown = CATALOGS[lang]
  for (const part of key.split('.')) {
    node = (node as Record<string, unknown>)[part]
  }
  return String(node)
}

function interpolate(message: string, params?: Record<string, string | number>): string {
  if (!params) return message
  return message.replace(/\{(\w+)\}/g, (match, name: string) =>
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match,
  )
}

/** Translate a catalog key in the current language. */
export function t(key: MessageKey, params?: Record<string, string | number>): string {
  return interpolate(lookup(key, currentLang), params)
}

export function formatDate(iso: string, lang: Language): string {
  return new Date(iso).toLocaleString(LOCALES[lang], { dateStyle: 'medium', timeStyle: 'short' })
}

export function formatNumber(value: number, lang: Language): string {
  return value.toLocaleString(LOCALES[lang])
}

interface I18nContextValue {
  lang: Language
  setLang: (lang: Language) => void
  t: (key: MessageKey, params?: Record<string, string | number>) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(currentLang)

  const setLang = (next: Language) => {
    currentLang = next
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Persistence is best-effort.
    }
    document.documentElement.lang = LOCALES[next]
  }

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  const value = useContext(I18nContext)
  if (!value) throw new Error('useI18n must be used within I18nProvider')
  return value
}
