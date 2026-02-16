import { useEffect, useState } from 'react'
import { Activity, ChevronDown, ChevronRight } from 'lucide-react'
import type { AgentEvent } from '../types'

interface AgentEventLogProps {
  events: AgentEvent[]
  loading?: boolean
}

const TYPE_COLORS: Record<string, string> = {
  'jira.': 'bg-blue-100 text-blue-700',
  'gitlab.': 'bg-orange-100 text-orange-700',
  'figma.': 'bg-purple-100 text-purple-700',
  'agent.product.': 'bg-emerald-100 text-emerald-700',
  'agent.design.': 'bg-pink-100 text-pink-700',
  'agent.code.': 'bg-yellow-100 text-yellow-700',
  'agent.security.': 'bg-red-100 text-red-700',
  'agent.test.': 'bg-cyan-100 text-cyan-700',
  'agent.review.': 'bg-indigo-100 text-indigo-700',
  'agent.deploy.': 'bg-teal-100 text-teal-700',
  'agent.analytics.': 'bg-violet-100 text-violet-700',
  'notification.': 'bg-gray-100 text-gray-700',
  'agent.error': 'bg-red-200 text-red-800',
}

function getTypeColor(type: string): string {
  for (const [prefix, color] of Object.entries(TYPE_COLORS)) {
    if (type.startsWith(prefix)) return color
  }
  return 'bg-gray-100 text-gray-600'
}

function EventRow({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false)
  const color = getTypeColor(event.type)
  const time = new Date(event.timestamp).toLocaleTimeString()

  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 text-left transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
        )}
        <span className="text-xs text-gray-400 w-20 flex-shrink-0">{time}</span>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${color} flex-shrink-0`}>
          {event.type}
        </span>
        <span className="text-xs text-gray-500 truncate">{event.source_agent}</span>
      </button>
      {expanded && (
        <div className="px-4 pb-3 pl-12">
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto max-h-48">
            {JSON.stringify(event.data, null, 2)}
          </pre>
          {event.correlation_id && (
            <p className="text-[10px] text-gray-400 mt-1">
              Correlation: {event.correlation_id}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function AgentEventLog({ events, loading }: AgentEventLogProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 bg-gray-50">
        <Activity className="w-4 h-4 text-indigo-500" />
        <h3 className="text-sm font-semibold text-gray-900">Event Log</h3>
        <span className="text-xs text-gray-400 ml-auto">{events.length} events</span>
      </div>
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500" />
          </div>
        ) : events.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-8">No events yet</p>
        ) : (
          events.map((event) => <EventRow key={event.event_id} event={event} />)
        )}
      </div>
    </div>
  )
}
