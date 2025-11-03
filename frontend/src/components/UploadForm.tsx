'use client'

import { FormEvent, useState } from 'react'
import { useRouter } from 'next/navigation'
import { uploadPDF } from '@/lib/api'

export default function UploadForm() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [targetSize, setTargetSize] = useState<number>(2)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!file) {
      setError('请先选择一个 PDF 文件')
      return
    }

    if (targetSize <= 0) {
      setError('目标大小必须大于 0')
      return
    }

    setIsSubmitting(true)
    try {
      const response = await uploadPDF(file, targetSize)
      router.push(`/progress/${response.task_id}`)
    } catch (err) {
      setError('上传失败，请稍后再试')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-200">选择 PDF 文件</label>
        <label className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-700 bg-slate-900/80 p-8 transition hover:border-blue-500">
          <span className="text-slate-400">
            {file ? file.name : '点击或拖拽 PDF 文件到此处'}
          </span>
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(event) => {
              const selected = event.target.files?.[0]
              if (selected) {
                setFile(selected)
              }
            }}
          />
        </label>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-200" htmlFor="targetSize">
          目标大小 (MB)
        </label>
        <input
          id="targetSize"
          type="number"
          min={0.1}
          step={0.1}
          value={targetSize}
          onChange={(event) => setTargetSize(Number(event.target.value))}
          className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
        />
      </div>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-lg shadow-blue-500/20 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-900"
      >
        {isSubmitting ? '上传中...' : '开始压缩'}
      </button>
    </form>
  )
}
