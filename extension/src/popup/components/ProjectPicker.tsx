import { useState, useEffect } from 'react'
import { projectsApi } from '../../api'
import type { Project } from '../../types'

interface ProjectPickerProps {
  selected: Project | null
  onSelect: (project: Project) => void
}

export default function ProjectPicker({ selected, onSelect }: ProjectPickerProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const res = await projectsApi.list()
      setProjects(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <p className="hint">Loading projects...</p>
  }

  if (projects.length === 0) {
    return <p className="hint">No projects found. Create one in the dashboard first.</p>
  }

  return (
    <div className="project-picker">
      <label className="label">Project</label>
      <select
        className="input"
        value={selected?.id ?? ''}
        onChange={(e) => {
          const p = projects.find((p) => p.id === Number(e.target.value))
          if (p) onSelect(p)
        }}
      >
        <option value="" disabled>Select a project...</option>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
    </div>
  )
}
