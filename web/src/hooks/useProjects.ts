import { useState, useEffect } from 'react'
import { apiFetch } from '../lib/api'

export interface Project {
  id: number | null
  name: string
  goal: string
  status: string
  where_i_left_off: string
  next_step: string
  notes: string
  updated_at: string
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([])

  useEffect(() => {
    apiFetch<Project[]>('/api/projects').then(setProjects).catch(() => {})
  }, [])

  return projects
}
