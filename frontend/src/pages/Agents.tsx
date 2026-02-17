import { useEffect, useState, useCallback } from 'react'
import { Bot, RefreshCw, Settings } from 'lucide-react'
import Layout from '../components/Layout'
import AgentCard from '../components/AgentCard'
import AgentEventLog from '../components/AgentEventLog'
import AgentConfigModal from '../components/AgentConfigModal'
import AgentConnectionPanel from '../components/AgentConnectionPanel'
import { agentsApi, projectsApi } from '../services/api'
import type { AgentStatus, AgentEvent, ServiceConnection } from '../types'

interface ProjectOption {
  id: number
  name: string
}

export default function Agents() {
  const [agents, setAgents] = useState<AgentStatus[]>([])
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [connections, setConnections] = useState<ServiceConnection[]>([])
  const [busRunning, setBusRunning] = useState(false)
  const [loading, setLoading] = useState(true)
  const [configAgent, setConfigAgent] = useState<AgentStatus | null>(null)
  const [testResults, setTestResults] = useState<Record<string, 'ok' | 'error' | 'testing'>>({})
  const [selectedProject, setSelectedProject] = useState<number | null>(null)
  const [projects, setProjects] = useState<ProjectOption[]>([])

  // Load available projects and try to restore last selection
  useEffect(() => {
    projectsApi.list().then(({ data }) => {
      const list = (data.projects || data || []).map((p: { id: number; name: string }) => ({ id: p.id, name: p.name }))
      setProjects(list)

      const stored = localStorage.getItem('lastProjectId')
      if (stored && list.some((p: ProjectOption) => p.id === Number(stored))) {
        setSelectedProject(Number(stored))
      } else if (list.length > 0) {
        setSelectedProject(list[0].id)
        localStorage.setItem('lastProjectId', String(list[0].id))
      }
    }).catch(() => {
      const stored = localStorage.getItem('lastProjectId')
      if (stored) setSelectedProject(Number(stored))
    })
  }, [])

  const fetchFleetStatus = useCallback(async () => {
    try {
      const { data } = await agentsApi.fleetStatus()
      setAgents(data.agents)
      setBusRunning(data.bus_running)
    } catch {
      // Fleet status not available
    }
  }, [])

  const fetchProjectData = useCallback(async () => {
    if (!selectedProject) return
    try {
      const [agentsRes, eventsRes, connsRes] = await Promise.all([
        agentsApi.listProjectAgents(selectedProject),
        agentsApi.listEvents(selectedProject, 100),
        agentsApi.listConnections(selectedProject),
      ])
      setAgents(agentsRes.data.agents)
      setEvents(eventsRes.data.events)
      setConnections(connsRes.data.connections)
    } catch {
      // Fallback to fleet status only
      await fetchFleetStatus()
    }
  }, [selectedProject, fetchFleetStatus])

  useEffect(() => {
    setLoading(true)
    if (selectedProject) {
      fetchProjectData().finally(() => setLoading(false))
    } else {
      fetchFleetStatus().finally(() => setLoading(false))
    }

    const interval = setInterval(() => {
      if (selectedProject) fetchProjectData()
      else fetchFleetStatus()
    }, 10000)

    return () => clearInterval(interval)
  }, [selectedProject, fetchProjectData, fetchFleetStatus])

  const handleToggle = async (name: string, enabled: boolean) => {
    if (!selectedProject) return
    try {
      await agentsApi.updateAgentConfig(selectedProject, name, { enabled })
      await fetchProjectData()
    } catch (e) {
      console.error('Failed to toggle agent:', e)
    }
  }

  const handleTrigger = async (name: string) => {
    if (!selectedProject) return
    try {
      await agentsApi.triggerAgent(selectedProject, name)
      setTimeout(fetchProjectData, 1000)
    } catch (e) {
      console.error('Failed to trigger agent:', e)
    }
  }

  const handleSaveConfig = async (agentName: string, config: Record<string, unknown>) => {
    if (!selectedProject) return
    try {
      await agentsApi.updateAgentConfig(selectedProject, agentName, { config })
      setConfigAgent(null)
      await fetchProjectData()
    } catch (e) {
      console.error('Failed to save config:', e)
    }
  }

  const handleConnect = async (data: { service_type: string; base_url?: string; api_token: string; config?: Record<string, unknown> }) => {
    if (!selectedProject) return
    try {
      await agentsApi.createConnection(selectedProject, data)
      await fetchProjectData()
    } catch (e) {
      console.error('Failed to connect service:', e)
    }
  }

  const handleDisconnect = async (serviceType: string) => {
    if (!selectedProject) return
    try {
      await agentsApi.deleteConnection(selectedProject, serviceType)
      await fetchProjectData()
    } catch (e) {
      console.error('Failed to disconnect:', e)
    }
  }

  const handleTest = async (serviceType: string) => {
    if (!selectedProject) return
    setTestResults((r) => ({ ...r, [serviceType]: 'testing' }))
    try {
      const { data } = await agentsApi.testConnection(selectedProject, serviceType)
      setTestResults((r) => ({ ...r, [serviceType]: data.status === 'ok' ? 'ok' : 'error' }))
    } catch {
      setTestResults((r) => ({ ...r, [serviceType]: 'error' }))
    }
  }

  const handleReveal = async (serviceType: string) => {
    if (!selectedProject) return null
    try {
      const { data } = await agentsApi.revealConnection(selectedProject, serviceType)
      return data
    } catch {
      return null
    }
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Bot className="w-7 h-7 text-indigo-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Agent Fleet</h1>
              <p className="text-sm text-gray-500">
                {agents.length} agents {busRunning ? '(bus active)' : '(bus inactive)'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {projects.length > 0 && (
              <select
                value={selectedProject || ''}
                onChange={(e) => {
                  const pid = Number(e.target.value)
                  setSelectedProject(pid)
                  localStorage.setItem('lastProjectId', String(pid))
                }}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            )}
            <button
              onClick={() => (selectedProject ? fetchProjectData() : fetchFleetStatus())}
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {!selectedProject && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
            <p className="text-sm text-amber-700">
              No project selected. Visit a project board first, then return here to manage agents for that project.
              Showing global fleet status.
            </p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Agent grid - 2/3 width */}
            <div className="lg:col-span-2 space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {agents.map((agent) => (
                  <div key={agent.name} className="relative group">
                    <AgentCard
                      agent={agent}
                      onToggle={handleToggle}
                      onTrigger={handleTrigger}
                    />
                    <button
                      onClick={() => setConfigAgent(agent)}
                      className="absolute top-3 right-12 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-white/80 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Configure"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Event Log */}
              <AgentEventLog events={events} />
            </div>

            {/* Sidebar - 1/3 width */}
            <div className="space-y-6">
              <AgentConnectionPanel
                connections={connections}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
                onTest={handleTest}
                onReveal={handleReveal}
                testResults={testResults}
              />

              {/* Fleet Summary */}
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Fleet Summary</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Active</span>
                    <span className="font-medium text-green-600">
                      {agents.filter((a) => a.enabled && a.status !== 'disabled').length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Disabled</span>
                    <span className="font-medium text-gray-400">
                      {agents.filter((a) => !a.enabled || a.status === 'disabled').length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Errors</span>
                    <span className="font-medium text-red-500">
                      {agents.filter((a) => a.status === 'error').length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Total Events</span>
                    <span className="font-medium text-gray-900">
                      {agents.reduce((sum, a) => sum + a.metrics.events_processed, 0)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Connections</span>
                    <span className="font-medium text-indigo-600">{connections.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Config Modal */}
        {configAgent && (
          <AgentConfigModal
            agent={configAgent}
            onSave={handleSaveConfig}
            onClose={() => setConfigAgent(null)}
          />
        )}
      </div>
    </Layout>
  )
}
