'use client'

import { useRef, useState } from 'react'

interface Message { role: 'user' | 'assistant'; content: string }

const SUGGESTED = [
  '이 진단이 심각한 건가요?',
  '앞으로 어떤 치료를 받게 되나요?',
  '일상생활에서 주의할 점이 있나요?',
]

export default function ChatBot({
  apiBase, parsedText, richSummary,
}: {
  apiBase: string
  parsedText: string
  richSummary: string
}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const send = async (content: string) => {
    if (!content.trim() || loading) return
    const next: Message[] = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: next, parsed_text: parsedText, rich_summary: richSummary }),
      })
      const data = await res.json()
      setMessages([...next, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages([...next, { role: 'assistant', content: '죄송합니다. 오류가 발생했습니다. 다시 시도해 주세요.' }])
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    }
  }

  return (
    <section className="max-w-6xl mx-auto w-full px-4 sm:px-6 pb-6">
      <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
        {/* 헤더 */}
        <div className="border-b border-slate-100 px-5 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm">💬</div>
          <div>
            <p className="font-semibold text-slate-800 text-sm">궁금한 점을 물어보세요</p>
            <p className="text-xs text-slate-400">번역 결과를 바탕으로 Upstage Solar Pro 3가 답변합니다</p>
          </div>
        </div>

        {/* 추천 질문 */}
        {messages.length === 0 && (
          <div className="px-5 pt-4 pb-2 flex flex-wrap gap-2">
            {SUGGESTED.map((q) => (
              <button
                key={q}
                onClick={() => send(q)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-full px-3.5 py-2 text-slate-600 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* 메시지 목록 */}
        {messages.length > 0 && (
          <div className="px-5 py-4 space-y-4 max-h-80 overflow-y-auto scrollbar-thin">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-sm'
                    : 'bg-slate-50 text-slate-800 border border-slate-100 rounded-tl-sm'
                }`}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1 items-center">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-slate-300 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* 입력창 */}
        <div className="border-t border-slate-100 px-4 py-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
            placeholder="질문을 입력하세요..."
            disabled={loading}
            className="flex-1 text-sm bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all disabled:opacity-50"
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="bg-blue-600 text-white rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            전송
          </button>
        </div>
      </div>
    </section>
  )
}
