import { Play, Power, PowerOff, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react'
import type { AgentStatus } from '../types'

interface AgentCardProps {
  agent: AgentStatus
  onToggle: (name: string, enabled: boolean) => void
  onTrigger: (name: string) => void
}

const STATUS_STYLES: Record<string, { bg: string; dot: string; label: string }> = {
  idle: { bg: 'bg-green-50', dot: 'bg-green-500', label: 'Idle' },
  running: { bg: 'bg-blue-50', dot: 'bg-blue-500', label: 'Running' },
  error: { bg: 'bg-red-50', dot: 'bg-red-500', label: 'Error' },
  disabled: { bg: 'bg-gray-50', dot: 'bg-gray-400', label: 'Disabled' },
}

const AGENT_ICONS: Record<string, string> = {
  product_intelligence: '🧠',
  design_sync: '🎨',
  code_orchestration: '⚙️',
  security_compliance: '🔒',
  test_intelligence: '🧪',
  review_coordination: '👀',
  deployment_orchestrator: '🚀',
  analytics_insights: '📊',
}

export default function AgentCard({ agent, onToggle, onTrigger }: AgentCardProps) {
  const style = STATUS_STYLES[agent.status] || STATUS_STYLES.idle
  const icon = AGENT_ICONS[agent.name] || '🤖'
  const displayName = agent.name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')

  return (
    <div className={`rounded-xl border border-gray-200 p-5 ${style.bg} transition-all hover:shadow-md`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">{displayName}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${style.dot}`} />
              <span className="text-xs text-gray-500">{style.label}</span>
            </div>
          </div>
        </div>
        <button
          onClick={() => onToggle(agent.name, !agent.enabled)}
          className={`p-1.5 rounded-lg transition-colors ${
            agent.enabled
              ? 'text-green-600 hover:bg-green-100'
              : 'text-gray-400 hover:bg-gray-200'
          }`}
          title={agent.enabled ? 'Disable' : 'Enable'}
        >
          {agent.enabled ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
        </button>
      </div>

      <p className="text-xs text-gray-500 mb-4 line-clamp-2">{agent.description}</p>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="text-center">
          <div className="flex items-center justify-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-green-500" />
            <span className="text-sm font-semibold text-gray-900">{agent.metrics.events_processed}</span>
          </div>
          <span className="text-[10px] text-gray-400">Processed</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-1">
            <AlertCircle className="w-3 h-3 text-red-400" />
            <span className="text-sm font-semibold text-gray-900">{agent.metrics.errors}</span>
          </div>
          <span className="text-[10px] text-gray-400">Errors</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-1">
            <Loader2 className="w-3 h-3 text-blue-400" />
            <span className="text-sm font-semibold text-gray-900">{agent.metrics.avg_processing_ms}ms</span>
          </div>
          <span className="text-[10px] text-gray-400">Avg Time</span>
        </div>
      </div>

      {agent.metrics.last_run && (
        <p className="text-[10px] text-gray-400 mb-3">
          Last run: {new Date(agent.metrics.last_run).toLocaleString()}
        </p>
      )}

      <button
        onClick={() => onTrigger(agent.name)}
        disabled={!agent.enabled}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <Play className="w-3.5 h-3.5" />
        Trigger Manually
      </button>
    </div>
  )
}
