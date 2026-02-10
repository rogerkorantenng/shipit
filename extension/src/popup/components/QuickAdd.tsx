import { useState } from 'react'
import { tasksApi } from '../../api'

interface QuickAddProps {
  projectId: number
}

export default function QuickAdd({ projectId }: QuickAddProps) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState('medium')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true)
    setError('')
    setSuccess(false)
    try {
      await tasksApi.create(projectId, {
        title: title.trim(),
        priority,
        description: description.trim() || undefined,
      })
      setTitle('')
      setDescription('')
      setPriority('medium')
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch {
      setError('Failed to create task.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="quick-add">
      <div className="quick-add-field">
        <input
          type="text"
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title"
          required
          autoFocus
        />
      </div>

      <div className="quick-add-field">
        <textarea
          className="textarea"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          rows={3}
        />
      </div>

      <div className="quick-add-field">
        <label className="label">Priority</label>
        <div className="quick-add-priorities">
          {(['low', 'medium', 'high', 'urgent'] as const).map((p) => (
            <button
              key={p}
              type="button"
              className={`quick-add-priority ${priority === p ? 'active' : ''}`}
              data-priority={p}
              onClick={() => setPriority(p)}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {success && <p className="quick-add-success">Task created!</p>}

      <button type="submit" className="btn btn-primary" disabled={loading || !title.trim()}>
        {loading ? 'Creating...' : 'Create Task'}
      </button>
    </form>
  )
}
