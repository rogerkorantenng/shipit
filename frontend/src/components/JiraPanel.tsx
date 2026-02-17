import { useState, useEffect } from 'react'
import { X, Loader2, Check, Upload, Download, RefreshCw, Layers, Eye, EyeOff, Key } from 'lucide-react'
import { jiraApi } from '../services/api'
import type { JiraConnection } from '../types'

interface JiraPanelProps {
  projectId: number
  onClose: () => void
  onRefresh: () => void
}

interface RevealedJira {
  jira_site: string
  jira_email: string
  jira_api_token: string
  jira_project_key: string
  jira_board_id: number | null
}

export default function JiraPanel({ projectId, onClose, onRefresh }: JiraPanelProps) {
  const [connection, setConnection] = useState<JiraConnection | null>(null)
  const [loading, setLoading] = useState(true)

  // Connect form
  const [site, setSite] = useState('')
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [projectKey, setProjectKey] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [connectError, setConnectError] = useState('')

  // Sync state
  const [syncing, setSyncing] = useState<'export' | 'import' | 'sync' | 'import-sprints' | null>(null)
  const [syncResult, setSyncResult] = useState('')

  // Reveal state
  const [revealed, setRevealed] = useState<RevealedJira | null>(null)
  const [revealing, setRevealing] = useState(false)

  useEffect(() => {
    loadConnection()
  }, [])

  const loadConnection = async () => {
    try {
      const res = await jiraApi.getConnection(projectId)
      setConnection(res.data)
    } catch {
      setConnection({ connected: false })
    } finally {
      setLoading(false)
    }
  }

  const handleRevealToggle = async () => {
    if (revealed) {
      setRevealed(null)
      return
    }
    setRevealing(true)
    try {
      const res = await jiraApi.revealCredentials(projectId)
      setRevealed(res.data)
    } catch {
      // ignore
    } finally {
      setRevealing(false)
    }
  }

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault()
    setConnecting(true)
    setConnectError('')
    try {
      await jiraApi.connect(projectId, {
        jira_site: site,
        jira_email: email,
        jira_api_token: token,
        jira_project_key: projectKey,
      })
      setRevealed(null)
      await loadConnection()
    } catch {
      setConnectError('Failed to connect. Check your credentials and site URL.')
    } finally {
      setConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await jiraApi.disconnect(projectId)
      setConnection({ connected: false })
      setRevealed(null)
      setSite('')
      setEmail('')
      setToken('')
      setProjectKey('')
    } catch {
      // ignore
    }
  }

  const handleExport = async () => {
    setSyncing('export')
    setSyncResult('')
    try {
      const res = await jiraApi.export(projectId)
      setSyncResult(`Exported ${res.data.exported} tasks to Jira`)
      onRefresh()
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Export failed'
      setSyncResult(detail)
    } finally {
      setSyncing(null)
    }
  }

  const handleImport = async () => {
    setSyncing('import')
    setSyncResult('')
    try {
      const res = await jiraApi.import(projectId)
      setSyncResult(`Imported ${res.data.imported} issues from Jira`)
      onRefresh()
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Import failed'
      setSyncResult(detail)
    } finally {
      setSyncing(null)
    }
  }

  const handleImportSprints = async () => {
    setSyncing('import-sprints')
    setSyncResult('')
    try {
      const res = await jiraApi.importSprints(projectId)
      const parts = []
      if (res.data.sprints_created > 0) parts.push(`${res.data.sprints_created} sprints created`)
      if (res.data.tasks_assigned > 0) parts.push(`${res.data.tasks_assigned} tasks assigned`)
      setSyncResult(parts.length > 0 ? parts.join(', ') : 'Sprints already in sync')
      onRefresh()
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Import sprints failed'
      setSyncResult(detail)
    } finally {
      setSyncing(null)
    }
  }

  const handleSync = async () => {
    setSyncing('sync')
    setSyncResult('')
    try {
      const res = await jiraApi.sync(projectId)
      const parts = []
      if (res.data.updated_local > 0) parts.push(`${res.data.updated_local} updated locally`)
      if (res.data.updated_remote > 0) parts.push(`${res.data.updated_remote} exported`)
      if (res.data.imported > 0) parts.push(`${res.data.imported} imported`)
      setSyncResult(parts.length > 0 ? parts.join(', ') : 'Everything in sync')
      onRefresh()
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Sync failed'
      setSyncResult(detail)
    } finally {
      setSyncing(null)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Jira Sync</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          </div>
        ) : connection?.connected ? (
          /* Connected State */
          <div className="space-y-4">
            <div className="bg-green-50 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800 font-medium">Connected to Jira</span>
              </div>
              <button
                onClick={handleRevealToggle}
                className="p-1.5 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-green-100"
                title={revealed ? 'Hide credentials' : 'Show credentials'}
              >
                {revealing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : revealed ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>

            <div className="text-sm text-gray-600 space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium min-w-[5rem]">Site:</span>
                <span className="font-mono text-gray-700">{connection.jira_site}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium min-w-[5rem]">Email:</span>
                <span className="font-mono text-gray-700">
                  {revealed ? revealed.jira_email : connection.jira_email}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium min-w-[5rem]">Project:</span>
                <span className="font-mono text-gray-700">{connection.jira_project_key}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium min-w-[5rem]">API Token:</span>
                <div className="flex items-center gap-1">
                  <Key className="w-3 h-3 text-gray-400" />
                  <span className="font-mono text-gray-700 break-all">
                    {revealed ? revealed.jira_api_token : (connection.masked_token || '••••••••')}
                  </span>
                </div>
              </div>
              {connection.jira_board_id && (
                <div className="flex items-center gap-2">
                  <span className="font-medium min-w-[5rem]">Board ID:</span>
                  <span className="font-mono text-gray-700">{connection.jira_board_id}</span>
                </div>
              )}
              {connection.last_sync_at && (
                <div className="flex items-center gap-2">
                  <span className="font-medium min-w-[5rem]">Last Sync:</span>
                  <span className="text-gray-700">{new Date(connection.last_sync_at).toLocaleString()}</span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleExport}
                disabled={syncing !== null}
                className="flex flex-col items-center gap-1 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 text-sm"
              >
                {syncing === 'export' ? <Loader2 className="w-5 h-5 animate-spin text-blue-500" /> : <Upload className="w-5 h-5 text-blue-600" />}
                Export
              </button>
              <button
                onClick={handleImport}
                disabled={syncing !== null}
                className="flex flex-col items-center gap-1 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 text-sm"
              >
                {syncing === 'import' ? <Loader2 className="w-5 h-5 animate-spin text-blue-500" /> : <Download className="w-5 h-5 text-blue-600" />}
                Import
              </button>
              <button
                onClick={handleSync}
                disabled={syncing !== null}
                className="flex flex-col items-center gap-1 p-3 rounded-lg border border-gray-200 hover:bg-blue-50 disabled:opacity-50 text-sm font-medium"
              >
                {syncing === 'sync' ? <Loader2 className="w-5 h-5 animate-spin text-blue-500" /> : <RefreshCw className="w-5 h-5 text-blue-600" />}
                Sync
              </button>
              <button
                onClick={handleImportSprints}
                disabled={syncing !== null || !connection?.sprints_available}
                className="flex flex-col items-center gap-1 p-3 rounded-lg border border-gray-200 hover:bg-purple-50 disabled:opacity-50 text-sm"
                title={!connection?.sprints_available ? 'No Jira board found — sprints not available' : 'Import sprints from Jira'}
              >
                {syncing === 'import-sprints' ? <Loader2 className="w-5 h-5 animate-spin text-purple-500" /> : <Layers className="w-5 h-5 text-purple-600" />}
                Sprints
              </button>
            </div>

            {syncResult && (
              <p className="text-sm text-center text-gray-600 bg-gray-50 rounded-lg p-2">{syncResult}</p>
            )}

            <button
              onClick={handleDisconnect}
              className="w-full text-sm text-red-600 hover:text-red-700 mt-2"
            >
              Disconnect Jira
            </button>
          </div>
        ) : (
          /* Connect Form */
          <form onSubmit={handleConnect} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Jira Site</label>
              <input
                type="text"
                value={site}
                onChange={(e) => setSite(e.target.value)}
                placeholder="yourcompany.atlassian.net"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">API Token</label>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Your Jira API token"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Project Key</label>
              <input
                type="text"
                value={projectKey}
                onChange={(e) => setProjectKey(e.target.value.toUpperCase())}
                placeholder="e.g. SHIP"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            {connectError && <p className="text-xs text-red-600">{connectError}</p>}
            <button
              type="submit"
              disabled={connecting}
              className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {connecting ? 'Connecting...' : 'Connect to Jira'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
