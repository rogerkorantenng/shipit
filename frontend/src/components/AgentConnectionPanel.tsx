import { useState } from 'react'
import { Link2, Unlink, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import type { ServiceConnection } from '../types'

interface AgentConnectionPanelProps {
  connections: ServiceConnection[]
  onConnect: (data: { service_type: string; base_url?: string; api_token: string; config?: Record<string, unknown> }) => void
  onDisconnect: (serviceType: string) => void
  onTest: (serviceType: string) => void
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
  testResults,
}: AgentConnectionPanelProps) {
  const [expandedService, setExpandedService] = useState<string | null>(null)
  const [formData, setFormData] = useState<Record<string, string>>({})

  const connMap = new Map(connections.map((c) => [c.service_type, c]))

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

              {isExpanded && (
                <div className="mt-3 space-y-2 pl-9">
                  {service.needsUrl && (
                    <input
                      type="text"
                      placeholder={service.urlPlaceholder}
                      value={formData[`${service.type}_url`] || ''}
                      onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_url`]: e.target.value }))}
                      className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                    />
                  )}
                  <input
                    type="password"
                    placeholder="API Token"
                    value={formData[`${service.type}_token`] || ''}
                    onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_token`]: e.target.value }))}
                    className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                  />
                  {service.type === 'gitlab' && (
                    <input
                      type="text"
                      placeholder="GitLab Project ID (numeric)"
                      value={formData[`${service.type}_project_id`] || ''}
                      onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_project_id`]: e.target.value }))}
                      className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                    />
                  )}
                  {service.extraFields?.map((field) => (
                    <input
                      key={field}
                      type="password"
                      placeholder={field.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      value={formData[`${service.type}_${field}`] || ''}
                      onChange={(e) => setFormData((d) => ({ ...d, [`${service.type}_${field}`]: e.target.value }))}
                      className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                    />
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
