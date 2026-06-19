import { useState, useEffect } from 'react'
import { apiFetch } from '../lib/api'

export interface Status {
  ollama_ok: boolean
  model: string
  projects_count: number
  last_latency_ms: number
}

export function useStatus(pollMs = 10_000) {
  const [status, setStatus] = useState<Status | null>(null)

  useEffect(() => {
    const load = () => apiFetch<Status>('/api/status').then(setStatus).catch(() => setStatus(null))
    load()
    const id = setInterval(load, pollMs)
    return () => clearInterval(id)
  }, [pollMs])

  return status
}
