import { useState } from 'react'
import { Loader2, TrendingUp, AlertTriangle, PauseCircle } from 'lucide-react'
import { aiApi } from '../services/api'
import type { DigestResult } from '../types'

export default function DigestPanel({ projectId }: { projectId: number }) {
  const [digest, setDigest] = useState<DigestResult | null>(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const res = await aiApi.digest(projectId)
      setDigest(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
        <span className="ml-2 text-sm text-gray-500">Generating digest...</span>
      </div>
    )
  }

  if (!digest) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-gray-500 mb-4">
          Get an AI-powered summary of your project progress.
        </p>
        <button
          onClick={generate}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          Generate Digest
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-700">{digest.summary}</p>

      {digest.moved.length > 0 && (
        <div>
          <h4 className="flex items-center gap-1.5 text-sm font-medium text-green-700 mb-1">
            <TrendingUp className="w-4 h-4" /> Moved Forward
          </h4>
          <ul className="text-sm text-gray-600 space-y-0.5 pl-5 list-disc">
            {digest.moved.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </div>
      )}

      {digest.stuck.length > 0 && (
        <div>
          <h4 className="flex items-center gap-1.5 text-sm font-medium text-amber-700 mb-1">
            <PauseCircle className="w-4 h-4" /> Stuck
          </h4>
          <ul className="text-sm text-gray-600 space-y-0.5 pl-5 list-disc">
            {digest.stuck.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      {digest.at_risk.length > 0 && (
        <div>
          <h4 className="flex items-center gap-1.5 text-sm font-medium text-red-700 mb-1">
            <AlertTriangle className="w-4 h-4" /> At Risk
          </h4>
          <ul className="text-sm text-gray-600 space-y-0.5 pl-5 list-disc">
            {digest.at_risk.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      <button
        onClick={generate}
        className="text-xs text-indigo-600 hover:underline"
      >
        Regenerate
      </button>
    </div>
  )
}
