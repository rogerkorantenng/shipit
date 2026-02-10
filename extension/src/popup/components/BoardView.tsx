import { useState, useEffect } from 'react'
import { tasksApi } from '../../api'
import type { Board, Task } from '../../types'

interface BoardViewProps {
  projectId: number
}

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  todo:        { label: 'To Do',       color: '#6b7280', bg: '#f3f4f6' },
  in_progress: { label: 'In Progress', color: '#3b82f6', bg: '#eff6ff' },
  done:        { label: 'Done',        color: '#22c55e', bg: '#f0fdf4' },
  blocked:     { label: 'Blocked',     color: '#ef4444', bg: '#fef2f2' },
}

const priorityDots: Record<string, string> = {
  urgent: '#dc2626',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
}

export default function BoardView({ projectId }: BoardViewProps) {
  const [board, setBoard] = useState<Board | null>(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    loadBoard()
  }, [projectId])

  const loadBoard = async () => {
    setLoading(true)
    try {
      const res = await tasksApi.getBoard(projectId)
      setBoard(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (task: Task, newStatus: string) => {
    try {
      await tasksApi.updateStatus(projectId, task.id, newStatus)
      await loadBoard()
    } catch {
      // ignore
    }
  }

  if (loading) {
    return <p className="hint" style={{ textAlign: 'center', padding: '24px 0' }}>Loading board...</p>
  }

  if (!board) {
    return <p className="hint" style={{ textAlign: 'center', padding: '24px 0' }}>Could not load board.</p>
  }

  const statuses = ['todo', 'in_progress', 'done', 'blocked'] as const
  const total = statuses.reduce((sum, s) => sum + board[s].length, 0)

  return (
    <div className="board-view">
      {/* Progress bar */}
      {total > 0 && (
        <div className="board-progress">
          <div className="board-progress-bar">
            {statuses.map((s) => {
              const pct = (board[s].length / total) * 100
              if (pct === 0) return null
              return (
                <div
                  key={s}
                  className="board-progress-segment"
                  style={{ width: `${pct}%`, backgroundColor: statusConfig[s].color }}
                  title={`${statusConfig[s].label}: ${board[s].length}`}
                />
              )
            })}
          </div>
          <span className="board-progress-label">{board.done.length}/{total} done</span>
        </div>
      )}

      {/* Status columns */}
      <div className="board-columns">
        {statuses.map((status) => {
          const cfg = statusConfig[status]
          const tasks = board[status]
          const isExpanded = expanded === status

          return (
            <div key={status} className="board-column">
              <button
                className="board-column-header"
                onClick={() => setExpanded(isExpanded ? null : status)}
                style={{ backgroundColor: cfg.bg }}
              >
                <span className="board-column-dot" style={{ backgroundColor: cfg.color }} />
                <span className="board-column-label">{cfg.label}</span>
                <span className="board-column-count">{tasks.length}</span>
                <span className="board-column-arrow">{isExpanded ? '▾' : '▸'}</span>
              </button>

              {isExpanded && (
                <div className="board-tasks">
                  {tasks.length === 0 ? (
                    <p className="board-empty">No tasks</p>
                  ) : (
                    tasks.slice(0, 10).map((task) => (
                      <div key={task.id} className="board-task">
                        <div className="board-task-header">
                          <span
                            className="board-task-priority"
                            style={{ backgroundColor: priorityDots[task.priority] || '#9ca3af' }}
                          />
                          <span className="board-task-title">{task.title}</span>
                        </div>
                        <div className="board-task-actions">
                          {task.assignee_name && (
                            <span className="board-task-assignee">{task.assignee_name}</span>
                          )}
                          <select
                            className="board-task-status-select"
                            value={task.status}
                            onChange={(e) => handleStatusChange(task, e.target.value)}
                          >
                            {statuses.map((s) => (
                              <option key={s} value={s}>{statusConfig[s].label}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    ))
                  )}
                  {tasks.length > 10 && (
                    <p className="board-more">+{tasks.length - 10} more</p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <button className="btn btn-secondary" onClick={loadBoard} style={{ marginTop: '8px' }}>
        Refresh
      </button>
    </div>
  )
}
