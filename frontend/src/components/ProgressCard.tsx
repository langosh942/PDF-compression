'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { getTaskStatus } from '@/lib/api'

interface ProgressCardProps {
  taskId: string
}

export default function ProgressCard({ taskId }: ProgressCardProps) {
  const router = useRouter()
  const { data, error, isLoading } = useSWR(
    taskId,
    () => getTaskStatus(taskId),
    {
      refreshInterval: (data) => {
        if (data?.status === 'completed' || data?.status === 'failed') {
          return 0
        }
        return 2000
      },
    }
  )

  useEffect(() => {
    if (data?.status === 'completed') {
      setTimeout(() => {
        router.push(`/result/${taskId}`)
      }, 1000)
    }
  }, [data?.status, taskId, router])

  if (isLoading) {
    return (
      <div className="animate-pulse rounded-3xl border border-slate-800 bg-slate-900/60 p-8">
        <div className="h-6 w-32 rounded bg-slate-800"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="rounded-3xl border border-red-900 bg-red-950/40 p-8 text-center">
        <p className="font-medium text-red-400">无法加载任务信息</p>
        <p className="mt-2 text-sm text-red-300/70">请检查任务 ID 是否正确</p>
      </div>
    )
  }

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl shadow-blue-500/10">
      <div className="space-y-6">
        <div>
          <h2 className="mb-2 text-2xl font-bold text-blue-400">
            {data.status === 'queued' && '任务排队中'}
            {data.status === 'running' && '正在压缩...'}
            {data.status === 'completed' && '✅ 压缩完成！'}
            {data.status === 'failed' && '❌ 压缩失败'}
          </h2>
          <p className="text-sm text-slate-400">{data.original_filename}</p>
        </div>

        {(data.status === 'running' || data.status === 'queued') && (
          <div className="w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300"
              style={{
                width: data.status === 'running' ? '60%' : '20%',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
              }}
            />
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 rounded-2xl border border-slate-800 bg-slate-950 p-4">
          <div>
            <div className="text-xs font-medium uppercase text-slate-500">原始大小</div>
            <div className="mt-1 text-lg font-semibold text-slate-200">
              {data.original_size_mb.toFixed(2)} MB
            </div>
          </div>
          <div>
            <div className="text-xs font-medium uppercase text-slate-500">目标大小</div>
            <div className="mt-1 text-lg font-semibold text-slate-200">
              {data.target_size_mb.toFixed(2)} MB
            </div>
          </div>
        </div>

        {data.status === 'failed' && data.error_message && (
          <div className="rounded-xl border border-red-900 bg-red-950/30 p-4">
            <p className="text-sm text-red-300">{data.error_message}</p>
          </div>
        )}
      </div>
    </div>
  )
}
