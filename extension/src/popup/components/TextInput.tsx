import { useState } from 'react'
import { aiApi } from '../../api'
import type { ExtractedTask, TaskUpdateItem } from '../../types'

interface TextInputProps {
  text: string
  setText: (text: string) => void
  projectId: number
  onExtracted: (tasks: ExtractedTask[], updates: TaskUpdateItem[]) => void
}

export default function TextInput({ text, setText, projectId, onExtracted }: TextInputProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleExtract = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await aiApi.extractTasks(projectId, text.trim())
      const tasks = res.data.tasks
      const updates = res.data.updates || []
      if (tasks.length === 0 && updates.length === 0) {
        setError('No actionable tasks or updates found in the text.')
      } else {
        onExtracted(tasks, updates)
      }
    } catch {
      setError('Failed to extract tasks. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="text-input">
      <label className="label">Paste text or use right-click &quot;Send to ShipIt&quot;</label>
      <textarea
        className="textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste meeting notes, emails, Slack messages..."
        rows={6}
      />
      {error && <p className="error">{error}</p>}
      <button
        className="btn btn-primary"
        onClick={handleExtract}
        disabled={loading || !text.trim()}
      >
        {loading ? 'Extracting...' : 'Extract Tasks'}
      </button>
    </div>
  )
}
