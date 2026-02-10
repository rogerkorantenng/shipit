import { useState, useEffect } from 'react'
import { Loader2, X, CheckCircle, Clock, AlertTriangle } from 'lucide-react'
import { aiApi } from '../services/api'
import type { StandupResult } from '../types'

interface StandupPanelProps {
  projectId: number
  onClose: () => void
}

export default function StandupPanel({ projectId, onClose }: StandupPanelProps) {
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState<StandupResult | null>(null)

  useEffect(() => {
    loadStandup()
  }, [])

  const loadStandup = async () => {
    try {
      const res = await aiApi.standup(projectId)
      setResult(res.data)
    } catch {
      setResult({ date: '', standups: [], team_summary: 'Failed to generate standup' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Daily Standup</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
            <span className="ml-2 text-sm text-gray-500">Generating standup...</span>
          </div>
        ) : result ? (
          <div className="space-y-4">
            {result.team_summary && (
              <div className="bg-indigo-50 rounded-lg p-3">
                <p className="text-sm text-indigo-800">{result.team_summary}</p>
              </div>
            )}

            {result.standups.map((s, i) => (
              <div key={i} className="border border-gray-200 rounded-xl p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-700">
                    {s.member.charAt(0).toUpperCase()}
                  </div>
                  <span className="font-medium text-sm text-gray-900">{s.member}</span>
                </div>

                {s.did.length > 0 && (
                  <div className="mb-2">
                    <div className="flex items-center gap-1 mb-1">
                      <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                      <span className="text-xs font-medium text-green-700">Did</span>
                    </div>
                    <ul className="ml-5 space-y-0.5">
                      {s.did.map((item, j) => (
                        <li key={j} className="text-xs text-gray-600">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {s.doing.length > 0 && (
                  <div className="mb-2">
                    <div className="flex items-center gap-1 mb-1">
                      <Clock className="w-3.5 h-3.5 text-blue-500" />
                      <span className="text-xs font-medium text-blue-700">Doing</span>
                    </div>
                    <ul className="ml-5 space-y-0.5">
                      {s.doing.map((item, j) => (
                        <li key={j} className="text-xs text-gray-600">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {s.blocked.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                      <span className="text-xs font-medium text-red-700">Blocked</span>
                    </div>
                    <ul className="ml-5 space-y-0.5">
                      {s.blocked.map((item, j) => (
                        <li key={j} className="text-xs text-gray-600">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )
}
