import { useState } from 'react'
import { Loader2, X, Play, Check } from 'lucide-react'
import { aiApi } from '../services/api'
import type { SprintPlanResult } from '../types'

interface SprintPlanPanelProps {
  projectId: number
  onClose: () => void
  onRefresh: () => void
}

const priorityColors: Record<string, string> = {
  urgent: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

export default function SprintPlanPanel({ projectId, onClose, onRefresh }: SprintPlanPanelProps) {
  const [capacity, setCapacity] = useState(40)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<SprintPlanResult | null>(null)
  const [applied, setApplied] = useState(false)

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const res = await aiApi.sprintPlan(projectId, capacity)
      setResult(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleApply = async () => {
    if (!result) return
    setApplying(true)
    try {
      const assignments = result.assignments.map((a) => ({
        task_id: a.task_id,
        assignee: a.assignee,
      }))
      await aiApi.applySprintPlan(projectId, {
        sprint_name: result.sprint_name,
        goal: result.goal || '',
        start_date: result.start_date,
        end_date: result.end_date,
        capacity_hours: capacity,
        assignments,
      })
      setApplied(true)
      onRefresh()
    } catch {
      // ignore
    } finally {
      setApplying(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">AI Sprint Planner</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {!result ? (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Team Capacity (hours)</label>
              <input
                type="number"
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                min={1}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Planning...</> : <><Play className="w-4 h-4" /> Generate Sprint Plan</>}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-indigo-50 rounded-lg p-3">
              <p className="font-medium text-sm text-indigo-900">{result.sprint_name}</p>
              {result.goal && <p className="text-xs text-indigo-700 mt-0.5">{result.goal}</p>}
              <div className="flex gap-3 text-xs text-indigo-600 mt-1">
                <span>{result.total_hours}h planned</span>
                {result.start_date && <span>Start: {result.start_date}</span>}
                {result.end_date && <span>End: {result.end_date}</span>}
              </div>
            </div>

            {result.assignments.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Assigned ({result.assignments.length})</p>
                <div className="space-y-2">
                  {result.assignments.map((a, i) => (
                    <div key={i} className="border border-gray-200 rounded-lg p-2.5">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900">{a.task_title}</span>
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${priorityColors[a.priority] || 'bg-gray-100 text-gray-600'}`}>
                          {a.priority}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>{a.assignee}</span>
                        <span>{a.estimated_hours}h</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{a.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.deferred.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Deferred ({result.deferred.length})</p>
                <div className="space-y-1">
                  {result.deferred.map((d, i) => (
                    <div key={i} className="bg-gray-50 rounded-lg p-2 text-xs">
                      <span className="font-medium text-gray-700">{d.task_title}</span>
                      <span className="text-gray-400 ml-2">{d.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-xs text-gray-400 bg-gray-50 rounded-lg p-2">
              Applying will create a persistent sprint and assign tasks to it.
            </div>

            <button
              onClick={applied ? onClose : handleApply}
              disabled={applying}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {applied ? <><Check className="w-4 h-4" /> Done</> : applying ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating Sprint...</> : 'Create Sprint & Apply'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
