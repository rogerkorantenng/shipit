import { useState } from 'react'
import { Link2, Unlink, CheckCircle2, XCircle, Loader2, Eye, EyeOff, Key } from 'lucide-react'
import type { ServiceConnection } from '../types'

interface RevealedData {
  api_token: string
  base_url: string | null
  config: Record<string, unknown>
}

interface AgentConnectionPanelProps {
  connections: ServiceConnection[]
  onConnect: (data: { service_type: string; base_url?: string; api_token: string; config?: Record<string, unknown> }) => void
  onDisconnect: (serviceType: string) => void
  onTest: (serviceType: string) => void
  onReveal: (serviceType: string) => Promise<RevealedData | null>
  testResults: Record<string, 'ok' | 'error' | 'testing'>
}

const SERVICES = [
  { type: 'gitlab', label: 'GitLab', icon: '🦊', needsUrl: true, urlPlaceholder: 'https://gitlab.com' },
  { type: 'figma', label: 'Figma', icon: '🎨', needsUrl: false },
  { type: 'slack', label: 'Slack', icon: '💬', needsUrl: false },
  { type: 'datadog', label: 'Datadog', icon: '🐶', needsUrl: false, extraFields: ['app_key'] },
  { type: 'sentry', label: 'Sentry', icon: '🔍', needsUrl: true, urlPlaceholder: 'https://sentry.io' },
]

export default function AgentConnectionPanel({
  connections,
  onConnect,
  onDisconnect,
  onTest,
  onReveal,
  testResults,
}: AgentConnectionPanelProps) {
  const [expandedService, setExpandedService] = useState<string | null>(null)
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [revealedServices, setRevealedServices] = useState<Record<string, RevealedData>>({})
  const [revealingService, setRevealingService] = useState<string | null>(null)

  const connMap = new Map(connections.map((c) => [c.service_type, c]))

  const handleRevealToggle = async (serviceType: string) => {
    if (revealedServices[serviceType]) {
      // Hide - just remove from state
      setRevealedServices((prev) => {
        const next = { ...prev }
        delete next[serviceType]
        return next
      })
      return
    }

    // Fetch full credentials
    setRevealingService(serviceType)
    const data = await onReveal(serviceType)
    setRevealingService(null)
    if (data) {
      setRevealedServices((prev) => ({ ...prev, [serviceType]: data }))
    }
  }

  const handleSubmit = (serviceType: string) => {
    const service = SERVICES.find((s) => s.type === serviceType)
    if (!service) return

    const data: { service_type: string; base_url?: string; api_token: string; config?: Record<string, unknown> } = {
      service_type: serviceType,
      api_token: formData[`${serviceType}_token`] || '',
    }

    if (service.needsUrl) {
      data.base_url = formData[`${serviceType}_url`] || service.urlPlaceholder
    }

    if (service.extraFields) {
      const config: Record<string, unknown> = {}
      for (const field of service.extraFields) {
        config[field] = formData[`${serviceType}_${field}`] || ''
      }
      data.config = config
    }

    if (formData[`${serviceType}_project_id`]) {
      data.config = { ...data.config, project_id: Number(formData[`${serviceType}_project_id`]) }
    }

    onConnect(data)
    setExpandedService(null)
    setFormData({})
    // Clear revealed data since it may have changed
    setRevealedServices((prev) => {
      const next = { ...prev }
      delete next[serviceType]
      return next
    })
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 bg-gray-50">
        <Link2 className="w-4 h-4 text-indigo-500" />
        <h3 className="text-sm font-semibold text-gray-900">Service Connections</h3>
      </div>

      <div className="divide-y divide-gray-100">
        {SERVICES.map((service) => {
          const conn = connMap.get(service.type)
          const isExpanded = expandedService === service.type
          const testStatus = testResults[service.type]
          const revealed = revealedServices[service.type]
          const isRevealing = revealingService === service.type

          return (
            <div key={service.type} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{service.icon}</span>
                  <div>
                    <span className="text-sm font-medium text-gray-900">{service.label}</span>
                    {conn && (
                      <span className="ml-2 inline-flex items-center gap-1 text-xs text-green-600">
                        <CheckCircle2 className="w-3 h-3" /> Connected
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {conn && (
                    <>
                      <button
                        onClick={() => handleRevealToggle(service.type)}
                        className="text-xs px-2 py-1 rounded border border-gray-200 text-gray-600 hover:bg-gray-50"
                        title={revealed ? 'Hide credentials' : 'Show credentials'}
                      >
                        {isRevealing ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : revealed ? (
                          <EyeOff className="w-3 h-3" />
                        ) : (
                          <Eye className="w-3 h-3" />
                        )}
                      </button>
                      <button
                        onClick={() => onTest(service.type)}
                        className="text-xs px-2 py-1 rounded border border-gray-200 text-gray-600 hover:bg-gray-50"
                      >
                        {testStatus === 'testing' ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : testStatus === 'ok' ? (
                          <CheckCircle2 className="w-3 h-3 text-green-500" />
                        ) : testStatus === 'error' ? (
                          <XCircle className="w-3 h-3 text-red-500" />
                        ) : (
                          'Test'
                        )}
                      </button>
                      <button
                        onClick={() => onDisconnect(service.type)}
                        className="text-xs px-2 py-1 rounded border border-red-200 text-red-600 hover:bg-red-50"
                      >
                        <Unlink className="w-3 h-3" />
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setExpandedService(isExpanded ? null : service.type)}
                    className="text-xs px-3 py-1 rounded-lg bg-indigo-50 text-indigo-600 hover:bg-indigo-100 font-medium"
                  >
                    {conn ? 'Update' : 'Connect'}
                  </button>
                </div>
              </div>

              {/* Show stored credentials when connected */}
              {conn && !isExpanded && (
                <div className="mt-2 pl-9 space-y-1">
                  {conn.base_url && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="font-medium min-w-[5rem]">URL:</span>
                      <span className="font-mono text-gray-700">{conn.base_url}</span>
                    </div>
                  )}
                  {conn.has_token && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="font-medium min-w-[5rem]">API Token:</span>
                      <div className="flex items-center gap-1">
                        <Key className="w-3 h-3 text-gray-400" />
                        <span className="font-mono text-gray-700 break-all">
                          {revealed ? revealed.api_token : (conn.masked_token || '••••••••')}
                        </span>
                      </div>
                    </div>
                  )}
                  {/* Show config values */}
                  {revealed && revealed.config && Object.keys(revealed.config).length > 0 && (
                    Object.entries(revealed.config).map(([key, value]) => (
                      <div key={key} className="flex items-center gap-2 text-xs text-gray-500">
                        <span className="font-medium min-w-[5rem]">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                        </span>
                        <span className="font-mono text-gray-700 break-all">{String(value)}</span>
                      </div>
                    ))
                  )}
                  {!revealed && conn.masked_config && Object.keys(conn.masked_config).length > 0 && (
                    Object.entries(conn.masked_config).map(([key, value]) => (
                      <div key={key} className="flex items-center gap-2 text-xs text-gray-500">
                        <span className="font-medium min-w-[5rem]">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                        </span>
                        <span className="font-mono text-gray-700">{String(value)}</span>
                      </div>
                    ))
                  )}
                  {conn.last_sync_at && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="font-medium min-w-[5rem]">Last Sync:</span>
                      <span className="text-gray-700">{new Date(conn.last_sync_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              )}

              {isExpanded && (
                <div className="mt-3 space-y-2 pl-9">
                  {service.needsUrl && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Base URL</label>
                      <input
                        type="text"
                        placeholder={service.urlPlaceholder}
                        value={formData[`${service.type}_url`] || ''}
                        onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_url`]: e.target.value }))}
                        className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                      />
                    </div>
                  )}
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      {service.type === 'datadog' ? 'API Key (32-char hex from API Keys page)' :
                       service.type === 'slack' ? 'Bot Token (starts with xoxb-)' :
                       service.type === 'gitlab' ? 'Personal Access Token (api scope)' :
                       service.type === 'figma' ? 'Personal Access Token' :
                       'API Token'}
                    </label>
                    <input
                      type="password"
                      placeholder={conn?.masked_token ? `Current: ${conn.masked_token}` : (service.type === 'datadog' ? 'e.g. 4107d89cab5e73a4f23b9de1...' : 'API Token')}
                      value={formData[`${service.type}_token`] || ''}
                      onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_token`]: e.target.value }))}
                      className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                    />
                  </div>
                  {service.type === 'gitlab' && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">GitLab Project ID</label>
                      <input
                        type="text"
                        placeholder={conn?.config?.project_id ? `Current: ${conn.config.project_id}` : 'Numeric ID from project homepage'}
                        value={formData[`${service.type}_project_id`] || ''}
                        onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_project_id`]: e.target.value }))}
                        className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                      />
                    </div>
                  )}
                  {service.extraFields?.map((field) => (
                    <div key={field}>
                      <label className="block text-xs font-medium text-gray-500 mb-1">
                        {service.type === 'datadog' && field === 'app_key'
                          ? 'Application Key (32-char hex from Application Keys page)'
                          : field.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                      </label>
                      <input
                        type="password"
                        placeholder={
                          conn?.masked_config?.[field]
                            ? `Current: ${conn.masked_config[field]}`
                            : (service.type === 'datadog' && field === 'app_key' ? 'e.g. 5a1a01d97292a119a7f6...' : field.replace('_', ' '))
                        }
                        value={formData[`${service.type}_${field}`] || ''}
                        onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_${field}`]: e.target.value }))}
                        className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                      />
                    </div>
                  ))}
                  <button
                    onClick={() => handleSubmit(service.type)}
                    className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
                  >
                    Save Connection
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
