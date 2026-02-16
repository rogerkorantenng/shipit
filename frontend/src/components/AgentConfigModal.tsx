import { useState } from 'react'
import { X, Save } from 'lucide-react'
import type { AgentStatus } from '../types'

interface AgentConfigModalProps {
  agent: AgentStatus
  onSave: (agentName: string, config: Record<string, unknown>) => void
  onClose: () => void
}

const AGENT_CONFIG_FIELDS: Record<string, { key: string; label: string; type: string; default: unknown }[]> = {
  review_coordination: [
    { key: 'sla_hours', label: 'Review SLA (hours)', type: 'number', default: 24 },
    { key: 'auto_merge', label: 'Auto-merge when approved', type: 'boolean', default: false },
    { key: 'min_reviewers', label: 'Minimum reviewers', type: 'number', default: 1 },
  ],
  security_compliance: [
    { key: 'block_on_critical', label: 'Block merge on critical', type: 'boolean', default: true },
    { key: 'scan_dependencies', label: 'Scan dependencies', type: 'boolean', default: true },
  ],
  analytics_insights: [
    { key: 'schedule_hours', label: 'Report interval (hours)', type: 'number', default: 24 },
    { key: 'include_predictions', label: 'Include AI predictions', type: 'boolean', default: true },
  ],
  deployment_orchestrator: [
    { key: 'auto_deploy', label: 'Auto-deploy on merge', type: 'boolean', default: false },
    { key: 'health_check_minutes', label: 'Post-deploy check (min)', type: 'number', default: 5 },
    { key: 'auto_rollback', label: 'Auto-rollback on errors', type: 'boolean', default: true },
  ],
  product_intelligence: [
    { key: 'create_gitlab_issues', label: 'Create GitLab issues', type: 'boolean', default: true },
    { key: 'max_stories', label: 'Max stories per ticket', type: 'number', default: 5 },
  ],
  design_sync: [
    { key: 'auto_create_issues', label: 'Auto-create GitLab issues', type: 'boolean', default: true },
  ],
  code_orchestration: [
    { key: 'auto_assign_reviewers', label: 'Auto-assign reviewers', type: 'boolean', default: true },
    { key: 'branch_prefix', label: 'Branch prefix', type: 'text', default: 'feature/' },
  ],
  test_intelligence: [
    { key: 'max_suggestions', label: 'Max test suggestions', type: 'number', default: 10 },
    { key: 'include_edge_cases', label: 'Include edge cases', type: 'boolean', default: true },
  ],
}

export default function AgentConfigModal({ agent, onSave, onClose }: AgentConfigModalProps) {
  const fields = AGENT_CONFIG_FIELDS[agent.name] || []
  const existingConfig = agent.project_config?.config || {}
  const [config, setConfig] = useState<Record<string, unknown>>(() => {
    const initial: Record<string, unknown> = {}
    for (const f of fields) {
      initial[f.key] = existingConfig[f.key] ?? f.default
    }
    return initial
  })

  const displayName = agent.name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Configure {displayName}</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-4 max-h-80 overflow-y-auto">
          {fields.length === 0 ? (
            <p className="text-sm text-gray-500">No configuration options for this agent.</p>
          ) : (
            fields.map((field) => (
              <div key={field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                {field.type === 'boolean' ? (
                  <button
                    onClick={() => setConfig((c) => ({ ...c, [field.key]: !c[field.key] }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      config[field.key] ? 'bg-indigo-600' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        config[field.key] ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                ) : field.type === 'number' ? (
                  <input
                    type="number"
                    value={config[field.key] as number}
                    onChange={(e) => setConfig((c) => ({ ...c, [field.key]: Number(e.target.value) }))}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                ) : (
                  <input
                    type="text"
                    value={config[field.key] as string}
                    onChange={(e) => setConfig((c) => ({ ...c, [field.key]: e.target.value }))}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                )}
              </div>
            ))
          )}
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(agent.name, config)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
