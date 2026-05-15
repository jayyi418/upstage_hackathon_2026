'use client'

import { useCallback, useRef, useState } from 'react'
import type { AnalysisResult } from './types'
import ResultView from './components/ResultView'
import ChatBot from './components/ChatBot'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const SAMPLES = [
  { key: 'internal', label: '🫀 내과 진단서', desc: '당뇨·고혈압·고지혈증' },
  { key: 'ortho',    label: '🦴 정형외과 소견서', desc: '허리디스크·골다공증' },
  { key: 'eye',      label: '👁️ 안과 검진 결과', desc: '녹내장·근시' },
]

type Page = 'landing' | 'analyzing' | 'result'

// ── 진행 화면 ──────────────────────────────────────────────────────────────────
function AnalyzingScreen({ progress, message, isDemoMode }: { progress: number; message: string; isDemoMode: boolean }) {
  const steps = isDemoMode
    ? [{ p: 20, label: '위험도 평가' }, { p: 60, label: '번역' }, { p: 100, label: '완료' }]
    : [{ p: 10, label: '문서 파싱' }, { p: 32, label: '정보 추출' }, { p: 55, label: '위험도 평가' }, { p: 75, label: '번역' }, { p: 100, label: '완료' }]

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-10 w-full max-w-md text-center">
        <div className="text-5xl mb-6 animate-bounce">🏥</div>
        <h2 className="text-xl font-bold text-slate-800 mb-2">진단서를 분석하고 있습니다</h2>
        <p className="text-slate-500 text-sm mb-8">{message || '잠시만 기다려 주세요...'}</p>

        {/* 진행 바 */}
        <div className="w-full bg-slate-100 rounded-full h-3 mb-6 overflow-hidden">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-sky-400 transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* 단계 표시 */}
        <div className="flex justify-between gap-1">
          {steps.map((s) => (
            <div key={s.label} className="flex-1 text-center">
              <div className={`w-2.5 h-2.5 rounded-full mx-auto mb-1 transition-colors duration-500 ${
                progress >= s.p ? 'bg-blue-500' : 'bg-slate-200'
              }`} />
              <span className={`text-xs ${progress >= s.p ? 'text-blue-600 font-medium' : 'text-slate-400'}`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>

        <p className="mt-6 text-xs text-slate-400">
          {isDemoMode ? 'Upstage Solar Pro 3로 분석 중' : 'Upstage Document Parse + Solar Pro 3로 분석 중'}
        </p>
      </div>
    </div>
  )
}

// ── 업로드 존 ──────────────────────────────────────────────────────────────────
function UploadZone({ onFile }: { onFile: (f: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-200 p-10 text-center
        ${dragging ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/30'}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f) }}
      />
      <div className="text-4xl mb-3">📂</div>
      <p className="font-semibold text-slate-700 mb-1">진단서 / 소견서 업로드</p>
      <p className="text-slate-400 text-sm">PDF, JPG, PNG 파일을 드래그하거나 클릭하세요</p>
      <div className="mt-5 inline-flex items-center gap-2 bg-blue-600 text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-blue-700 transition-colors">
        파일 선택
      </div>
    </div>
  )
}

// ── 랜딩 페이지 ──────────────────────────────────────────────────────────────
function LandingPage({
  onFile, onSample, error,
}: {
  onFile: (f: File) => void
  onSample: (k: string) => void
  error: string | null
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* 헤더 */}
      <header className="bg-white border-b border-slate-100 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <span className="text-2xl">🏥</span>
          <span className="text-xl font-bold text-slate-900">MediRead</span>
          <span className="text-slate-400 text-sm hidden sm:inline">진단서 번역기</span>
          <span className="ml-auto text-xs text-slate-400 hidden sm:inline">Powered by Upstage</span>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-12">
        {/* 히어로 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 mb-4 leading-tight">
            진단서, 이제<br />
            <span className="text-blue-600">진짜로 이해하세요</span>
          </h1>
          <p className="text-lg text-slate-500 max-w-lg mx-auto">
            의학 용어가 가득한 진단서를<br className="sm:hidden" /> 누구나 이해할 수 있는 쉬운 한국어로 번역해드립니다.
          </p>
        </div>

        {/* 에러 */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm flex gap-2">
            <span>⚠️</span> {error}
          </div>
        )}

        <div className="grid md:grid-cols-5 gap-6 items-start">
          {/* 업로드 */}
          <div className="md:col-span-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">직접 업로드</p>
            <UploadZone onFile={onFile} />
          </div>

          {/* 샘플 */}
          <div className="md:col-span-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">샘플로 바로 체험</p>
            <div className="space-y-3">
              {SAMPLES.map((s) => (
                <button
                  key={s.key}
                  onClick={() => onSample(s.key)}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3.5 text-left hover:border-blue-300 hover:bg-blue-50/40 transition-all card-hover group"
                >
                  <div className="font-semibold text-slate-800 group-hover:text-blue-700 text-sm">{s.label}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{s.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 기능 설명 */}
        <div className="mt-14 grid sm:grid-cols-3 gap-4">
          {[
            { icon: '📄', title: 'Document Parse', desc: 'PDF·사진에서 의학 텍스트를 정확하게 추출' },
            { icon: '🔍', title: 'Information Extract', desc: '진단명·수치·약물을 구조화된 데이터로 변환' },
            { icon: '💬', title: 'Solar Pro 3', desc: '의학 용어를 쉬운 한국어로 번역 + Q&A 답변' },
          ].map((f) => (
            <div key={f.title} className="bg-white border border-slate-100 rounded-xl p-5 text-center">
              <div className="text-3xl mb-2">{f.icon}</div>
              <div className="font-semibold text-slate-800 text-sm mb-1">{f.title}</div>
              <div className="text-xs text-slate-500">{f.desc}</div>
            </div>
          ))}
        </div>
      </main>

      <footer className="max-w-5xl mx-auto w-full px-6 pb-8">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800 text-sm">
          ⚠️ 이 서비스는 의료 진단을 대체하지 않습니다. 건강에 관한 중요한 결정은 반드시 의사와 상담하세요.
        </div>
      </footer>
    </div>
  )
}

// ── 메인 앱 ──────────────────────────────────────────────────────────────────
export default function Home() {
  const [page, setPage] = useState<Page>('landing')
  const [progress, setProgress] = useState(0)
  const [progressMsg, setProgressMsg] = useState('')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const consumeStream = async (url: string, options: RequestInit) => {
    setPage('analyzing')
    setProgress(0)
    setProgressMsg('')
    setError(null)

    try {
      const res = await fetch(url, options)
      if (!res.ok || !res.body) throw new Error(`서버 오류 (${res.status})`)

      const reader = res.body.getReader()
      const dec = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })

        const parts = buf.split('\n\n')
        buf = parts.pop() ?? ''

        for (const part of parts) {
          if (!part.startsWith('data: ')) continue
          const data = JSON.parse(part.slice(6))

          if (data.error) {
            setError(data.error)
            setPage('landing')
            return
          }

          if (typeof data.progress === 'number') setProgress(data.progress)
          if (data.message) setProgressMsg(data.message)

          if (data.done && data.data) {
            setResult(data.data)
            setPage('result')
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.')
      setPage('landing')
    }
  }

  const handleFile = useCallback((file: File) => {
    setIsDemoMode(false)
    const fd = new FormData()
    fd.append('file', file)
    consumeStream(`${API}/api/analyze`, { method: 'POST', body: fd })
  }, [])

  const handleSample = useCallback((key: string) => {
    setIsDemoMode(true)
    consumeStream(`${API}/api/analyze-sample/${key}`, { method: 'POST' })
  }, [])

  const handleReset = () => { setPage('landing'); setResult(null); setProgress(0) }

  if (page === 'analyzing') {
    return <AnalyzingScreen progress={progress} message={progressMsg} isDemoMode={isDemoMode} />
  }

  if (page === 'result' && result) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <ResultView result={result} isDemoMode={isDemoMode} onReset={handleReset} />
        <ChatBot
          apiBase={API}
          parsedText={result.parsed_text}
          richSummary={result.rich_translation.summary}
        />
        <footer className="max-w-6xl mx-auto w-full px-6 pb-8">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800 text-sm">
            ⚠️ 이 서비스는 의료 진단을 대체하지 않습니다. 건강에 관한 중요한 결정은 반드시 의사와 상담하세요.
          </div>
        </footer>
      </div>
    )
  }

  return <LandingPage onFile={handleFile} onSample={handleSample} error={error} />
}
