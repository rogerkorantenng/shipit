import { useState } from 'react'
import { aiApi } from '../../api'
import type { ExtractedTask, TaskUpdateItem } from '../../types'

interface TaskPreviewProps {
  tasks: ExtractedTask[]
  updates: TaskUpdateItem[]
  projectId: number
  onApplied: () => void
  onBack: () => void
}

const priorityColors: Record<string, string> = {
  urgent: '#dc2626',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
}

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
  blocked: 'Blocked',
}

export default function TaskPreview({ tasks, updates, projectId, onApplied, onBack }: TaskPreviewProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleApply = async () => {
    setLoading(true)
    setError('')
    try {
      await aiApi.applyMeetingNotes(projectId, { tasks, updates })
      onApplied()
    } catch {
      setError('Failed to apply. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const totalChanges = tasks.length + updates.length

  return (
    <div className="task-preview">
      <div className="preview-header">
        <button className="btn-link" onClick={onBack}>&larr; Back</button>
        <span className="task-count">
          {totalChanges} change{totalChanges !== 1 ? 's' : ''} found
        </span>
      </div>

      {/* Status Updates */}
      {updates.length > 0 && (
        <div className="preview-section">
          <div className="preview-section-header update-header">
            Status Updates ({updates.length})
          </div>
          <div className="task-list">
            {updates.map((u, i) => (
              <div key={i} className="task-card update-card">
                <div className="task-card-header">
                  <span className="task-title">{u.task_title}</span>
                  <span className="status-badge" data-status={u.new_status}>
                    {statusLabels[u.new_status] || u.new_status}
                  </span>
                </div>
                {u.reason && <p className="task-desc">{u.reason}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* New Tasks */}
      {tasks.length > 0 && (
        <div className="preview-section">
          <div className="preview-section-header new-header">
            New Tasks ({tasks.length})
          </div>
          <div className="task-list">
            {tasks.map((task, i) => (
              <div key={i} className="task-card">
                <div className="task-card-header">
                  <span className="task-title">{task.title}</span>
                  <span
                    className="priority-badge"
                    style={{ backgroundColor: priorityColors[task.priority] || '#9ca3af' }}
                  >
                    {task.priority}
                  </span>
                </div>
                {task.description && <p className="task-desc">{task.description}</p>}
                <div className="task-meta">
                  {task.estimated_hours && <span>{task.estimated_hours}h</span>}
                  {task.suggested_assignee && <span>{task.suggested_assignee}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {totalChanges === 0 && (
        <p className="hint" style={{ textAlign: 'center', padding: '16px 0' }}>
          No tasks or updates found in the text.
        </p>
      )}

      {error && <p className="error">{error}</p>}

      <button
        className="btn btn-primary"
        onClick={handleApply}
        disabled={loading || totalChanges === 0}
      >
        {loading ? 'Applying...' : `Apply ${tasks.length} New + ${updates.length} Updates`}
      </button>
    </div>
  )
}
