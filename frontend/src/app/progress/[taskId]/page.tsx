'use client'

import ProgressCard from '@/components/ProgressCard'

interface ProgressPageProps {
  params: {
    taskId: string
  }
}

export default function ProgressPage({ params }: ProgressPageProps) {
  const { taskId } = params

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
        <ProgressCard taskId={taskId} />
      </div>
    </section>
  )
}
