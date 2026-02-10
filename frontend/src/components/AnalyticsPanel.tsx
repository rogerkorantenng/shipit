import { useState, useEffect } from 'react'
import { Loader2, X } from 'lucide-react'
import { aiApi } from '../services/api'
import type { AnalyticsResult } from '../types'

interface AnalyticsPanelProps {
  projectId: number
  onClose: () => void
}

const statusColors: Record<string, string> = {
  todo: 'bg-gray-400',
  in_progress: 'bg-blue-500',
  done: 'bg-green-500',
  blocked: 'bg-red-500',
}

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
  blocked: 'Blocked',
}

const priorityColors: Record<string, string> = {
  low: 'bg-green-400',
  medium: 'bg-yellow-400',
  high: 'bg-orange-400',
  urgent: 'bg-red-500',
}

export default function AnalyticsPanel({ projectId, onClose }: AnalyticsPanelProps) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<AnalyticsResult | null>(null)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      const res = await aiApi.analytics(projectId)
      setData(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const maxWorkload = data ? Math.max(...data.workload.map((w) => w.assigned + w.completed), 1) : 1

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-xl shadow-xl max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Team Analytics</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-indigo-50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-indigo-700">{data.total_tasks}</p>
                <p className="text-xs text-indigo-600">Total Tasks</p>
              </div>
              <div className="bg-green-50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-green-700">{data.completion_rate}%</p>
                <p className="text-xs text-green-600">Complete</p>
              </div>
              <div className="bg-amber-50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-amber-700">{data.status_counts.in_progress || 0}</p>
                <p className="text-xs text-amber-600">In Progress</p>
              </div>
            </div>

            {/* Status Distribution */}
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Task Status</p>
              <div className="flex h-6 rounded-full overflow-hidden bg-gray-100">
                {Object.entries(data.status_counts).map(([status, count]) => {
                  const pct = data.total_tasks > 0 ? (count / data.total_tasks) * 100 : 0
                  if (pct === 0) return null
                  return (
                    <div
                      key={status}
                      className={`${statusColors[status] || 'bg-gray-300'} transition-all`}
                      style={{ width: `${pct}%` }}
                      title={`${statusLabels[status] || status}: ${count}`}
                    />
                  )
                })}
              </div>
              <div className="flex gap-3 mt-2">
                {Object.entries(data.status_counts).map(([status, count]) => (
                  <div key={status} className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
                    <span className="text-xs text-gray-500">{statusLabels[status] || status} ({count})</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Priority Distribution */}
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Priority Breakdown</p>
              <div className="grid grid-cols-4 gap-2">
                {(['low', 'medium', 'high', 'urgent'] as const).map((p) => (
                  <div key={p} className="text-center">
                    <div className="relative h-20 bg-gray-50 rounded-lg flex items-end justify-center pb-1">
                      <div
                        className={`w-8 rounded-t ${priorityColors[p]} transition-all`}
                        style={{ height: `${data.total_tasks > 0 ? Math.max(((data.priority_counts[p] || 0) / data.total_tasks) * 100, 4) : 4}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-1 capitalize">{p}</p>
                    <p className="text-xs font-medium text-gray-900">{data.priority_counts[p] || 0}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Workload per Member */}
            {data.workload.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Workload by Member</p>
                <div className="space-y-2">
                  {data.workload.map((w, i) => (
                    <div key={i}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-700">{w.name}</span>
                        <span className="text-xs text-gray-400">{w.estimated_hours}h est.</span>
                      </div>
                      <div className="flex h-4 rounded-full overflow-hidden bg-gray-100">
                        <div
                          className="bg-green-400 transition-all"
                          style={{ width: `${(w.completed / maxWorkload) * 100}%` }}
                          title={`Done: ${w.completed}`}
                        />
                        <div
                          className="bg-blue-400 transition-all"
                          style={{ width: `${(w.assigned / maxWorkload) * 100}%` }}
                          title={`Active: ${w.assigned}`}
                        />
                      </div>
                      <div className="flex gap-3 mt-0.5">
                        <span className="text-[10px] text-gray-400">{w.completed} done</span>
                        <span className="text-[10px] text-gray-400">{w.assigned} active</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-8">No data available</p>
        )}
      </div>
    </div>
  )
}
