'use client'

import { useState } from 'react'
import type { AnalysisResult, RiskAssessment, TestResult, Medication } from '../types'

// ── 위험도 배지 ───────────────────────────────────────────────────────────────
const RISK_META = {
  low:    { label: '🟢 경증',   bg: 'bg-green-50',  border: 'border-green-200', text: 'text-green-700',  badge: 'bg-green-100 text-green-700' },
  medium: { label: '🟡 중등증', bg: 'bg-amber-50',  border: 'border-amber-200', text: 'text-amber-700',  badge: 'bg-amber-100 text-amber-700' },
  high:   { label: '🔴 중증',   bg: 'bg-red-50',    border: 'border-red-200',   text: 'text-red-700',    badge: 'bg-red-100 text-red-700' },
}

function RiskBadges({ risks }: { risks: RiskAssessment[] }) {
  if (!risks.length) return null
  return (
    <section className="mb-6">
      <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">진단명 위험도</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {risks.map((r) => {
          const m = RISK_META[r.level] ?? RISK_META.low
          return (
            <div key={r.diagnosis} className={`rounded-xl border p-4 ${m.bg} ${m.border}`}>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${m.badge}`}>{m.label}</span>
              <p className={`font-semibold mt-2 ${m.text}`}>{r.diagnosis}</p>
              <p className="text-xs text-slate-500 mt-1">{r.reason}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}

// ── 검사 결과 테이블 ──────────────────────────────────────────────────────────
const STATUS_META = {
  high:   { label: '🔴 높음', row: 'bg-red-50/60',   text: 'text-red-600 font-bold' },
  low:    { label: '🔵 낮음', row: 'bg-blue-50/60',  text: 'text-blue-600 font-bold' },
  normal: { label: '🟢 정상', row: 'bg-green-50/40', text: 'text-green-600 font-bold' },
}

function TestResultsTable({ results }: { results: TestResult[] }) {
  if (!results.length) return null
  return (
    <section className="mb-6">
      <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">🧪 검사 결과</h2>
      <div className="overflow-x-auto rounded-xl border border-slate-100">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100">
              <th className="text-left px-4 py-3 font-semibold text-slate-500 text-xs">검사명</th>
              <th className="text-right px-4 py-3 font-semibold text-slate-500 text-xs">수치</th>
              <th className="text-center px-4 py-3 font-semibold text-slate-500 text-xs hidden sm:table-cell">정상 범위</th>
              <th className="text-center px-4 py-3 font-semibold text-slate-500 text-xs">상태</th>
              <th className="text-left px-4 py-3 font-semibold text-slate-500 text-xs hidden md:table-cell">설명</th>
            </tr>
          </thead>
          <tbody>
            {results.map((tr, i) => {
              const s = STATUS_META[tr.status] ?? STATUS_META.normal
              return (
                <tr key={i} className={`border-b border-slate-50 last:border-0 ${s.row}`}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-800">{tr.name}</div>
                    {tr.original_term && <div className="text-xs text-slate-400">{tr.original_term}</div>}
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-semibold text-slate-800">
                    {tr.value} <span className="font-normal text-slate-400 text-xs">{tr.unit}</span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-slate-400 hidden sm:table-cell">
                    {tr.normal_range ?? '—'}
                  </td>
                  <td className={`px-4 py-3 text-center text-xs whitespace-nowrap ${s.text}`}>{s.label}</td>
                  <td className="px-4 py-3 text-xs text-slate-600 hidden md:table-cell max-w-xs">{tr.plain_explanation}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// ── 약물 카드 ─────────────────────────────────────────────────────────────────
function MedicationCards({ meds }: { meds: Medication[] }) {
  if (!meds.length) return null
  return (
    <section className="mb-6">
      <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">💊 처방 약물</h2>
      <div className="grid sm:grid-cols-2 gap-3">
        {meds.map((m, i) => (
          <div key={i} className="bg-white border border-slate-100 rounded-xl p-4 card-hover">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center text-base flex-shrink-0">💊</div>
              <div className="min-w-0">
                <p className="font-semibold text-slate-800 text-sm">{m.name}</p>
                {m.dosage_instruction && (
                  <p className="text-xs text-slate-400 mt-0.5">{m.dosage_instruction}</p>
                )}
                <p className="text-xs text-slate-600 mt-2 bg-slate-50 rounded-lg px-3 py-2">{m.purpose}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── 할 일 목록 ────────────────────────────────────────────────────────────────
function ActionItems({ items }: { items: string[] }) {
  if (!items.length) return null
  return (
    <section className="mb-6">
      <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">✅ 지금 해야 할 일</h2>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-3 bg-white border border-slate-100 rounded-xl px-4 py-3 card-hover">
            <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
            </div>
            <p className="text-sm text-slate-700">{item}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── 전체 결과 뷰 ──────────────────────────────────────────────────────────────
export default function ResultView({
  result, isDemoMode, onReset,
}: {
  result: AnalysisResult
  isDemoMode: boolean
  onReset: () => void
}) {
  const [activeTab, setActiveTab] = useState<'translation' | 'original'>('translation')
  const { rich_translation: r, risk_assessments, parsed_text } = result

  return (
    <div className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-6">
      {/* 헤더 */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onReset}
          className="text-sm text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition-colors"
        >
          ← 새 문서
        </button>
        <h1 className="text-lg font-bold text-slate-900">🏥 분석 결과</h1>
        {isDemoMode && (
          <span className="text-xs bg-blue-100 text-blue-600 px-2.5 py-1 rounded-full font-medium">샘플 체험</span>
        )}
      </div>

      {/* 탭 */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl mb-6 w-fit">
        {(['translation', 'original'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`text-sm px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab === 'translation' ? '✅ 번역 결과' : '📋 원문 보기'}
          </button>
        ))}
      </div>

      {activeTab === 'translation' && (
        <div>
          {/* 요약 배너 */}
          {r.summary && (
            <div className="bg-gradient-to-r from-blue-600 to-sky-500 rounded-2xl p-6 mb-6 text-white shadow-md">
              <p className="text-xs font-semibold uppercase tracking-widest opacity-80 mb-2">💬 요약</p>
              <p className="text-base leading-relaxed">{r.summary}</p>
            </div>
          )}

          <RiskBadges risks={risk_assessments} />
          <TestResultsTable results={r.test_results} />
          <MedicationCards meds={r.medications} />
          <ActionItems items={r.action_items} />

          {/* 상세 번역 접기 */}
          {r.full_explanation && (
            <details className="group bg-white border border-slate-100 rounded-xl">
              <summary className="px-5 py-4 cursor-pointer text-sm font-medium text-slate-600 hover:text-slate-900 flex items-center justify-between select-none">
                <span>📄 전체 번역 자세히 보기</span>
                <span className="group-open:rotate-180 transition-transform text-slate-400">▼</span>
              </summary>
              <div className="px-5 pb-5 prose prose-sm prose-slate max-w-none border-t border-slate-50 pt-4">
                {r.full_explanation.split('\n').map((line, i) => (
                  <p key={i} className={line.startsWith('#') ? 'font-bold text-slate-800' : 'text-slate-600'}>
                    {line}
                  </p>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {activeTab === 'original' && (
        <div className="bg-white border border-slate-100 rounded-2xl p-6">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">원문 (Document Parse 결과)</p>
          <div className="text-sm text-slate-700 leading-relaxed font-mono whitespace-pre-wrap scrollbar-thin overflow-y-auto max-h-[600px]">
            {parsed_text}
          </div>
        </div>
      )}
    </div>
  )
}
