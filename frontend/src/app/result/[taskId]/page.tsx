'use client'

import { useParams } from 'next/navigation'
import DownloadCard from '@/components/DownloadCard'

export default function ResultPage() {
  const params = useParams()
  const taskId = params?.taskId as string

  if (!taskId) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-center">
          <p className="text-red-400">Task ID not found</p>
        </div>
      </div>
    )
  }

  return (
    <section className="flex flex-1 flex-col justify-center">
      <div className="mx-auto w-full max-w-2xl">
        <DownloadCard taskId={taskId} />
      </div>
    </section>
  )
}
