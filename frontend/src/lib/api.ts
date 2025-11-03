import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface TaskStatus {
  task_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  original_filename: string
  original_size_mb: number
  compressed_size_mb?: number
  target_size_mb: number
  created_at: string
  completed_at?: string
  result_download_url?: string
  error_message?: string
}

export async function uploadPDF(file: File, targetSizeMb: number): Promise<{ task_id: string; status: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('target_size_mb', targetSizeMb.toString())

  const response = await api.post('/v1/compress', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await api.get(`/v1/tasks/${taskId}`)
  return response.data
}
