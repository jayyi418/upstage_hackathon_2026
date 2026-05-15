import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MediRead — 진단서 번역기',
  description: '의학 용어가 가득한 진단서를 누구나 이해할 수 있는 쉬운 한국어로 번역해드립니다.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  )
}
