import { useState, useEffect } from 'react'
import { Loader2, X, Check, ArrowRight } from 'lucide-react'
import { aiApi } from '../services/api'
import type { PriorityScoreResult } from '../types'

interface PriorityScorePanelProps {
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

export default function PriorityScorePanel({ projectId, onClose, onRefresh }: PriorityScorePanelProps) {
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<PriorityScoreResult | null>(null)
  const [applied, setApplied] = useState(false)

  useEffect(() => {
    loadScores()
  }, [])

  const loadScores = async () => {
    try {
      const res = await aiApi.priorityScore(projectId)
      setResult(res.data)
    } catch {
      setResult({ recommendations: [] })
    } finally {
      setLoading(false)
    }
  }

  const changedRecs = result?.recommendations.filter(
    (r) => r.current_priority !== r.suggested_priority
  ) || []

  const handleApply = async () => {
    setApplying(true)
    try {
      const updates = changedRecs.map((r) => ({
        task_id: r.task_id,
        priority: r.suggested_priority,
      }))
      await aiApi.applyPriorityScore(projectId, updates)
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
          <h3 className="text-lg font-semibold text-gray-900">Smart Priority Scoring</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
            <span className="ml-2 text-sm text-gray-500">Analyzing priorities...</span>
          </div>
        ) : result && result.recommendations.length > 0 ? (
          <div className="space-y-4">
            {changedRecs.length > 0 && (
              <p className="text-xs text-gray-500">{changedRecs.length} priority change{changedRecs.length !== 1 ? 's' : ''} suggested</p>
            )}
            <div className="space-y-2">
              {result.recommendations.map((r, i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-2.5">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">{r.task_title}</span>
                    <div className="flex items-center gap-1">
                      <span className="w-8 text-right text-xs font-bold text-indigo-600">{r.score}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${priorityColors[r.current_priority] || 'bg-gray-100'}`}>
                      {r.current_priority}
                    </span>
                    {r.current_priority !== r.suggested_priority && (
                      <>
                        <ArrowRight className="w-3 h-3 text-gray-400" />
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${priorityColors[r.suggested_priority] || 'bg-gray-100'}`}>
                          {r.suggested_priority}
                        </span>
                      </>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">{r.reason}</p>
                </div>
              ))}
            </div>

            {changedRecs.length > 0 && (
              <button
                onClick={applied ? onClose : handleApply}
                disabled={applying}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {applied ? <><Check className="w-4 h-4" /> Done</> : applying ? <><Loader2 className="w-4 h-4 animate-spin" /> Applying...</> : `Apply ${changedRecs.length} Changes`}
              </button>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-8">No tasks to analyze</p>
        )}
      </div>
    </div>
  )
}
