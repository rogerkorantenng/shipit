import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Plus, UserPlus, Sparkles, FileText,
  AlertTriangle, BarChart3, X, Loader2, RefreshCw,
  Target, TrendingUp, Users, PieChart,
} from 'lucide-react'
import Layout from '../components/Layout'
import KanbanColumn from '../components/KanbanColumn'
import TaskModal from '../components/TaskModal'
import DigestPanel from '../components/DigestPanel'
import JiraPanel from '../components/JiraPanel'
import SprintPlanPanel from '../components/SprintPlanPanel'
import SprintBar from '../components/SprintBar'
import PriorityScorePanel from '../components/PriorityScorePanel'
import StandupPanel from '../components/StandupPanel'
import AnalyticsPanel from '../components/AnalyticsPanel'
import Toast from '../components/Toast'
import MemberBadge from '../components/MemberBadge'
import PulseWidget from '../components/PulseWidget'
import StatsBar from '../components/StatsBar'
import BadgePanel from '../components/BadgePanel'
import Confetti from '../components/Confetti'
import { projectsApi, tasksApi, aiApi, jiraApi, sprintsApi } from '../services/api'
import type { Task, Board as BoardType, Member, BlockerResult, JiraConnection, Sprint } from '../types'

type Panel =
  | 'task-create' | 'task-detail' | 'blockers' | 'digest' | 'add-member'
  | 'jira' | 'sprint-plan' | 'priority-score' | 'standup' | 'analytics'
  | 'badges'
  | null

export default function Board() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = Number(id)

  const [projectName, setProjectName] = useState('')
  const [board, setBoard] = useState<BoardType>({ todo: [], in_progress: [], done: [], blocked: [] })
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)

  const [panel, setPanel] = useState<Panel>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  // Add member
  const [memberName, setMemberName] = useState('')
  const [addingMember, setAddingMember] = useState(false)

  // Blockers
  const [blockers, setBlockers] = useState<BlockerResult | null>(null)
  const [blockersLoading, setBlockersLoading] = useState(false)

  // Sprints
  const [sprints, setSprints] = useState<Sprint[]>([])
  const [selectedSprintId, setSelectedSprintId] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'sprint' | 'backlog'>('sprint')

  // Jira connection info (for badge links)
  const [jiraConn, setJiraConn] = useState<JiraConnection | null>(null)

  // Drag & drop
  const [draggedTask, setDraggedTask] = useState<Task | null>(null)

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)

  // Confetti
  const [showConfetti, setShowConfetti] = useState(false)

  useEffect(() => {
    loadAll()
  }, [projectId])

  const [error, setError] = useState<string | null>(null)

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [projectRes, boardRes, membersRes, sprintsRes] = await Promise.all([
        projectsApi.get(projectId),
        tasksApi.getBoard(projectId),
        projectsApi.listMembers(projectId),
        sprintsApi.list(projectId),
      ])
      setProjectName(projectRes.data.name)
      setBoard(boardRes.data)
      setMembers(membersRes.data)
      setSprints(sprintsRes.data)

      // Default to active sprint view
      const active = sprintsRes.data.find((s: Sprint) => s.status === 'active')
      if (active) {
        setSelectedSprintId(active.id)
        setViewMode('sprint')
      }

      // Load Jira connection + auto-sync
      try {
        const jiraRes = await jiraApi.getConnection(projectId)
        setJiraConn(jiraRes.data)
        if (jiraRes.data.connected) {
          const syncRes = await jiraApi.sync(projectId)
          const d = syncRes.data
          const total = (d.updated_local || 0) + (d.updated_remote || 0) + (d.imported || 0)
          if (total > 0) {
            const boardRes2 = await tasksApi.getBoard(projectId)
            setBoard(boardRes2.data)
            setToast({ message: `Jira synced: ${total} change${total !== 1 ? 's' : ''}`, type: 'success' })
          }
        }
      } catch {
        // Jira not connected, that's fine
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Failed to load project'
      const status = err.response?.status
      if (status === 401) {
        navigate('/')
      } else {
        setError(detail)
      }
    } finally {
      setLoading(false)
    }
  }

  const refreshBoard = useCallback(async () => {
    try {
      const params = viewMode === 'backlog'
        ? { backlog: true }
        : selectedSprintId
          ? { sprint_id: selectedSprintId }
          : undefined
      const [boardRes, sprintsRes] = await Promise.all([
        tasksApi.getBoard(projectId, params),
        sprintsApi.list(projectId),
      ])
      setBoard(boardRes.data)
      setSprints(sprintsRes.data)
    } catch {
      // ignore
    }
  }, [projectId, viewMode, selectedSprintId])

  const handleSelectSprint = async (sprintId: number) => {
    setSelectedSprintId(sprintId)
    setViewMode('sprint')
    try {
      const res = await tasksApi.getBoard(projectId, { sprint_id: sprintId })
      setBoard(res.data)
    } catch {
      // ignore
    }
  }

  const handleSelectBacklog = async () => {
    setSelectedSprintId(null)
    setViewMode('backlog')
    try {
      const res = await tasksApi.getBoard(projectId, { backlog: true })
      setBoard(res.data)
    } catch {
      // ignore
    }
  }

  const handleStartSprint = async (sprintId: number) => {
    try {
      await sprintsApi.start(projectId, sprintId)
      setToast({ message: 'Sprint started!', type: 'success' })
      setSelectedSprintId(sprintId)
      setViewMode('sprint')
      await refreshBoard()
    } catch {
      setToast({ message: 'Failed to start sprint', type: 'error' })
    }
  }

  const handleCompleteSprint = async (sprintId: number) => {
    try {
      await sprintsApi.complete(projectId, sprintId)
      setToast({ message: 'Sprint completed! Incomplete tasks moved to backlog.', type: 'success' })
      await refreshBoard()
    } catch {
      setToast({ message: 'Failed to complete sprint', type: 'error' })
    }
  }

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task)
    setPanel('task-detail')
  }

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!memberName.trim()) return
    setAddingMember(true)
    try {
      await projectsApi.addMember(projectId, memberName.trim())
      setMemberName('')
      setPanel(null)
      const res = await projectsApi.listMembers(projectId)
      setMembers(res.data)
    } catch {
      // ignore
    } finally {
      setAddingMember(false)
    }
  }

  const handleDetectBlockers = async () => {
    setPanel('blockers')
    setBlockersLoading(true)
    try {
      const res = await aiApi.detectBlockers(projectId)
      setBlockers(res.data)
    } catch {
      setBlockers({ blockers: [] })
    } finally {
      setBlockersLoading(false)
    }
  }

  // Drag & Drop handlers
  const handleDragStart = (_e: React.DragEvent, task: Task) => {
    setDraggedTask(task)
  }

  const handleDrop = async (newStatus: string) => {
    if (!draggedTask || draggedTask.status === newStatus) {
      setDraggedTask(null)
      return
    }

    // Optimistic update
    const oldBoard = { ...board }
    const updatedTask = { ...draggedTask, status: newStatus }
    setBoard((prev) => {
      const next = { ...prev }
      next[draggedTask.status as keyof BoardType] = prev[draggedTask.status as keyof BoardType].filter((t) => t.id !== draggedTask.id)
      next[newStatus as keyof BoardType] = [...prev[newStatus as keyof BoardType], updatedTask]
      return next
    })
    setDraggedTask(null)

    try {
      await tasksApi.update(projectId, draggedTask.id, { status: newStatus })
      setToast({ message: `Moved "${draggedTask.title}" to ${newStatus.replace('_', ' ')}`, type: 'success' })
      if (newStatus === 'done') {
        setShowConfetti(true)
      }
    } catch {
      setBoard(oldBoard)
      setToast({ message: 'Failed to update task', type: 'error' })
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-24">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg"
            >
              Back to Dashboard
            </button>
            <button
              onClick={loadAll}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Retry
            </button>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-full">
        {/* Toast */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => navigate('/')}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold text-gray-900">{projectName}</h1>

          {/* Member avatars */}
          <div className="flex items-center -space-x-1 ml-2">
            {members.slice(0, 5).map((m) => (
              <MemberBadge key={m.id} name={m.name} />
            ))}
            {members.length > 5 && (
              <span className="text-xs text-gray-400 ml-2">+{members.length - 5}</span>
            )}
          </div>

          <button
            onClick={() => setPanel('add-member')}
            className="p-1.5 text-gray-400 hover:text-indigo-600 rounded-md hover:bg-indigo-50"
            title="Add member"
          >
            <UserPlus className="w-4 h-4" />
          </button>
        </div>

        {/* Action bar */}
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <button
            onClick={() => { setSelectedTask(null); setPanel('task-create') }}
            className="inline-flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" /> New Task
          </button>
          <button
            onClick={() => { setSelectedTask(null); setPanel('task-create') }}
            className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-100"
          >
            <Sparkles className="w-4 h-4" /> AI Breakdown
          </button>
          <button
            onClick={() => { setSelectedTask(null); setPanel('task-create') }}
            className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-100"
          >
            <FileText className="w-4 h-4" /> Meeting Notes
          </button>
          <button
            onClick={() => setPanel('sprint-plan')}
            className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-100"
          >
            <Target className="w-4 h-4" /> Sprint Plan
          </button>
          <button
            onClick={() => setPanel('priority-score')}
            className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-100"
          >
            <TrendingUp className="w-4 h-4" /> Priority Score
          </button>
          <button
            onClick={() => setPanel('standup')}
            className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-purple-100"
          >
            <Users className="w-4 h-4" /> Standup
          </button>
          <button
            onClick={handleDetectBlockers}
            className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-red-100"
          >
            <AlertTriangle className="w-4 h-4" /> Blockers
          </button>
          <button
            onClick={() => setPanel('digest')}
            className="inline-flex items-center gap-1.5 bg-green-50 text-green-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-green-100"
          >
            <BarChart3 className="w-4 h-4" /> Digest
          </button>
          <button
            onClick={() => setPanel('analytics')}
            className="inline-flex items-center gap-1.5 bg-green-50 text-green-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-green-100"
          >
            <PieChart className="w-4 h-4" /> Analytics
          </button>
          <button
            onClick={() => setPanel('jira')}
            className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-100"
          >
            <RefreshCw className="w-4 h-4" /> Jira Sync
          </button>
        </div>

        {/* Sprint Bar */}
        {sprints.length > 0 && (
          <SprintBar
            sprints={sprints}
            selectedSprintId={selectedSprintId}
            viewMode={viewMode}
            onSelectSprint={handleSelectSprint}
            onSelectBacklog={handleSelectBacklog}
            onStartSprint={handleStartSprint}
            onCompleteSprint={handleCompleteSprint}
          />
        )}

        {/* Stats + Pulse Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-4">
          <div className="lg:col-span-2">
            <StatsBar projectId={projectId} onOpenBadges={() => setPanel('badges')} />
          </div>
          <PulseWidget projectId={projectId} />
        </div>

        {/* Confetti */}
        {showConfetti && <Confetti onDone={() => setShowConfetti(false)} />}

        {/* Kanban Board */}
        <div className="kanban-grid">
          {(['todo', 'in_progress', 'done', 'blocked'] as const).map((status) => (
            <KanbanColumn
              key={status}
              status={status}
              tasks={board[status]}
              jiraSite={jiraConn?.jira_site}
              onTaskClick={handleTaskClick}
              onDragStart={handleDragStart}
              onDrop={handleDrop}
            />
          ))}
        </div>

        {/* Task Modal */}
        {(panel === 'task-create' || panel === 'task-detail') && (
          <TaskModal
            projectId={projectId}
            task={panel === 'task-detail' ? selectedTask : null}
            members={members}
            onClose={() => setPanel(null)}
            onRefresh={refreshBoard}
          />
        )}

        {/* Add Member Modal */}
        {panel === 'add-member' && (
          <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Add Team Member</h3>
                <button onClick={() => setPanel(null)} className="p-1 text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <form onSubmit={handleAddMember} className="space-y-4">
                <input
                  type="text"
                  value={memberName}
                  onChange={(e) => setMemberName(e.target.value)}
                  placeholder="Enter name"
                  autoFocus
                  required
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                />
                <div className="flex justify-end gap-2">
                  <button type="button" onClick={() => setPanel(null)} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
                  <button type="submit" disabled={addingMember} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                    {addingMember ? 'Adding...' : 'Add Member'}
                  </button>
                </div>
              </form>

              {members.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-500 mb-2">Current Members</p>
                  <div className="space-y-1">
                    {members.map((m) => (
                      <div key={m.id} className="flex items-center gap-2 text-sm">
                        <MemberBadge name={m.name} />
                        <span className="text-gray-700">{m.name}</span>
                        <span className="text-xs text-gray-400 ml-auto">{m.workload} tasks</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Blockers Panel */}
        {panel === 'blockers' && (
          <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Blocker Analysis</h3>
                <button onClick={() => setPanel(null)} className="p-1 text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
              {blockersLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-red-500" />
                  <span className="ml-2 text-sm text-gray-500">Analyzing...</span>
                </div>
              ) : blockers && blockers.blockers.length > 0 ? (
                <div className="space-y-3">
                  {blockers.blockers.map((b, i) => (
                    <div key={i} className="bg-red-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm text-red-900">{b.task_title}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                          b.severity === 'high' ? 'bg-red-200 text-red-800'
                          : b.severity === 'medium' ? 'bg-amber-200 text-amber-800'
                          : 'bg-gray-200 text-gray-700'
                        }`}>
                          {b.severity}
                        </span>
                      </div>
                      <p className="text-sm text-red-800">{b.issue}</p>
                      <p className="text-xs text-red-600 mt-1">{b.suggestion}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">No blockers detected!</p>
              )}
            </div>
          </div>
        )}

        {/* Jira Panel */}
        {panel === 'jira' && (
          <JiraPanel
            projectId={projectId}
            onClose={() => setPanel(null)}
            onRefresh={refreshBoard}
          />
        )}

        {/* Sprint Plan Panel */}
        {panel === 'sprint-plan' && (
          <SprintPlanPanel
            projectId={projectId}
            onClose={() => setPanel(null)}
            onRefresh={refreshBoard}
          />
        )}

        {/* Priority Score Panel */}
        {panel === 'priority-score' && (
          <PriorityScorePanel
            projectId={projectId}
            onClose={() => setPanel(null)}
            onRefresh={refreshBoard}
          />
        )}

        {/* Standup Panel */}
        {panel === 'standup' && (
          <StandupPanel
            projectId={projectId}
            onClose={() => setPanel(null)}
          />
        )}

        {/* Analytics Panel */}
        {panel === 'analytics' && (
          <AnalyticsPanel
            projectId={projectId}
            onClose={() => setPanel(null)}
          />
        )}

        {/* Badge Panel */}
        {panel === 'badges' && (
          <BadgePanel
            projectId={projectId}
            onClose={() => setPanel(null)}
          />
        )}

        {/* Digest Panel */}
        {panel === 'digest' && (
          <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Daily Digest</h3>
                <button onClick={() => setPanel(null)} className="p-1 text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <DigestPanel projectId={projectId} />
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
