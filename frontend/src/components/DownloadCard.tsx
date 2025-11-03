'use client'

import Link from 'next/link'
import useSWR from 'swr'
import { TaskStatus, getTaskStatus } from '@/lib/api'

interface DownloadCardProps {
  taskId: string
}

export default function DownloadCard({ taskId }: DownloadCardProps) {
  const { data, error, isLoading } = useSWR<TaskStatus>(taskId, () => getTaskStatus(taskId))

  if (isLoading) {
    return (
      <div className="animate-pulse rounded-3xl border border-slate-800 bg-slate-900/60 p-8">
        <div className="h-6 w-48 rounded bg-slate-800"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="rounded-3xl border border-red-900 bg-red-950/40 p-8 text-center">
        <p className="font-medium text-red-400">无法加载压缩结果</p>
      </div>
    )
  }

  if (data.status !== 'completed' || !data.result_download_url) {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 text-center">
        <p className="text-slate-300">压缩仍在进行中，请稍后刷新页面。</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl shadow-blue-500/10">
      <div>
        <h2 className="text-3xl font-bold text-green-400">压缩完成</h2>
        <p className="mt-2 text-sm text-slate-400">你的文件已经准备好下载。</p>
      </div>

      <div className="grid grid-cols-2 gap-4 rounded-2xl border border-slate-800 bg-slate-950 p-4">
        <div>
          <div className="text-xs font-medium uppercase text-slate-500">原始大小</div>
          <div className="mt-1 text-lg font-semibold text-slate-200">
            {data.original_size_mb.toFixed(2)} MB
          </div>
        </div>
        <div>
          <div className="text-xs font-medium uppercase text-slate-500">压缩后大小</div>
          <div className="mt-1 text-lg font-semibold text-slate-200">
            {data.compressed_size_mb?.toFixed(2)} MB
          </div>
        </div>
      </div>

      <Link
        href={data.result_download_url}
        className="inline-flex w-full items-center justify-center rounded-xl bg-green-500 px-6 py-3 text-lg font-semibold text-slate-900 transition hover:bg-green-400"
      >
        下载压缩后的 PDF
      </Link>

      <Link href="/" className="block text-center text-sm text-blue-400 hover:text-blue-300">
        返回首页重新压缩
      </Link>
    </div>
  )
}
