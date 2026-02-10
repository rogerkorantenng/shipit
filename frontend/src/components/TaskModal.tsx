import { useState, useEffect } from 'react'
import {
  X, Loader2, Sparkles, Plus, CheckCircle2, Circle, ArrowRight,
} from 'lucide-react'
import PriorityBadge from './PriorityBadge'
import MemberBadge from './MemberBadge'
import { tasksApi, aiApi, activityApi } from '../services/api'
import type { Task, TaskDetail, Member, Activity, BreakdownResult, MeetingNotesResult, TaskUpdate } from '../types'

interface TaskModalProps {
  projectId: number
  task?: Task | null          // null = create mode
  members: Member[]
  onClose: () => void
  onRefresh: () => void
}

type CreateTab = 'manual' | 'breakdown' | 'meeting'

export default function TaskModal({ projectId, task, members, onClose, onRefresh }: TaskModalProps) {
  const isCreate = !task

  // --- Create mode state ---
  const [tab, setTab] = useState<CreateTab>('manual')

  // Manual form
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [assigneeId, setAssigneeId] = useState<number | null>(null)
  const [dueDate, setDueDate] = useState('')
  const [estHours, setEstHours] = useState('')
  const [saving, setSaving] = useState(false)

  // AI Breakdown
  const [breakdownInput, setBreakdownInput] = useState('')
  const [breakdownResult, setBreakdownResult] = useState<BreakdownResult | null>(null)
  const [breakdownLoading, setBreakdownLoading] = useState(false)

  // Meeting Notes
  const [notesInput, setNotesInput] = useState('')
  const [notesResult, setNotesResult] = useState<MeetingNotesResult | null>(null)
  const [notesLoading, setNotesLoading] = useState(false)

  // --- Detail mode state ---
  const [detail, setDetail] = useState<TaskDetail | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [editStatus, setEditStatus] = useState('')
  const [editPriority, setEditPriority] = useState('')
  const [editAssignee, setEditAssignee] = useState<number | null>(null)
  const [subtaskTitle, setSubtaskTitle] = useState('')
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    if (task) loadDetail()
  }, [task])

  const loadDetail = async () => {
    if (!task) return
    try {
      const [taskRes, actRes] = await Promise.all([
        tasksApi.get(projectId, task.id),
        activityApi.forTask(projectId, task.id),
      ])
      setDetail(taskRes.data)
      setActivities(actRes.data)
      setEditStatus(taskRes.data.status)
      setEditPriority(taskRes.data.priority)
      setEditAssignee(taskRes.data.assignee_id)
    } catch {
      // ignore
    }
  }

  // --- Create handlers ---

  const handleManualCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setSaving(true)
    try {
      await tasksApi.create(projectId, {
        title,
        description,
        priority,
        assignee_id: assigneeId,
        due_date: dueDate || null,
        estimated_hours: estHours ? parseFloat(estHours) : null,
      })
      onRefresh()
      onClose()
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  const handleBreakdown = async () => {
    if (!breakdownInput.trim()) return
    setBreakdownLoading(true)
    try {
      const res = await aiApi.breakdown(projectId, breakdownInput)
      setBreakdownResult(res.data)
    } catch {
      // ignore
    } finally {
      setBreakdownLoading(false)
    }
  }

  const handleApplyBreakdown = async () => {
    if (!breakdownResult) return
    setSaving(true)
    try {
      await aiApi.applyBreakdown(projectId, {
        title: breakdownResult.title,
        priority: breakdownResult.suggested_priority,
        subtasks: breakdownResult.subtasks,
      })
      onRefresh()
      onClose()
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  const handleExtractNotes = async () => {
    if (!notesInput.trim()) return
    setNotesLoading(true)
    try {
      const res = await aiApi.meetingNotes(projectId, notesInput)
      setNotesResult(res.data)
    } catch {
      // ignore
    } finally {
      setNotesLoading(false)
    }
  }

  const handleApplyNotes = async () => {
    if (!notesResult) return
    setSaving(true)
    try {
      await aiApi.applyMeetingNotes(projectId, {
        tasks: notesResult.tasks,
        updates: notesResult.updates || [],
      })
      onRefresh()
      onClose()
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  // --- Detail handlers ---

  const handleUpdate = async (field: string, value: unknown) => {
    if (!task) return
    setUpdating(true)
    try {
      await tasksApi.update(projectId, task.id, { [field]: value })
      await loadDetail()
      onRefresh()
    } catch {
      // ignore
    } finally {
      setUpdating(false)
    }
  }

  const handleAddSubtask = async () => {
    if (!task || !subtaskTitle.trim()) return
    try {
      await tasksApi.create(projectId, {
        title: subtaskTitle,
        parent_task_id: task.id,
      })
      setSubtaskTitle('')
      await loadDetail()
      onRefresh()
    } catch {
      // ignore
    }
  }

  const toggleSubtaskStatus = async (subtask: Task) => {
    const newStatus = subtask.status === 'done' ? 'todo' : 'done'
    try {
      await tasksApi.update(projectId, subtask.id, { status: newStatus })
      await loadDetail()
      onRefresh()
    } catch {
      // ignore
    }
  }

  const handleDelete = async () => {
    if (!task) return
    try {
      await tasksApi.delete(projectId, task.id)
      onRefresh()
      onClose()
    } catch {
      // ignore
    }
  }

  // --- Render ---

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {isCreate ? 'New Task' : detail?.title || task?.title}
          </h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4">
          {isCreate ? (
            <>
              {/* Tab switcher */}
              <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1">
                {(['manual', 'breakdown', 'meeting'] as CreateTab[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`flex-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      tab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {t === 'manual' ? 'Manual' : t === 'breakdown' ? 'AI Breakdown' : 'Meeting Notes'}
                  </button>
                ))}
              </div>

              {/* Manual tab */}
              {tab === 'manual' && (
                <form onSubmit={handleManualCreate} className="space-y-3">
                  <input
                    type="text"
                    placeholder="Task title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  />
                  <textarea
                    placeholder="Description (optional)"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="low">Low Priority</option>
                      <option value="medium">Medium Priority</option>
                      <option value="high">High Priority</option>
                      <option value="urgent">Urgent</option>
                    </select>
                    <select
                      value={assigneeId ?? ''}
                      onChange={(e) => setAssigneeId(e.target.value ? Number(e.target.value) : null)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="">Unassigned</option>
                      {members.map((m) => (
                        <option key={m.id} value={m.id}>{m.name}</option>
                      ))}
                    </select>
                    <input
                      type="date"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      placeholder="Est. hours"
                      value={estHours}
                      onChange={(e) => setEstHours(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                    <button type="submit" disabled={saving} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                      {saving ? 'Creating...' : 'Create Task'}
                    </button>
                  </div>
                </form>
              )}

              {/* AI Breakdown tab */}
              {tab === 'breakdown' && (
                <div className="space-y-3">
                  <textarea
                    placeholder="Describe what needs to happen... e.g. 'We need to launch a new pricing page by Friday with three tiers'"
                    value={breakdownInput}
                    onChange={(e) => setBreakdownInput(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
                  />
                  {!breakdownResult && (
                    <button
                      onClick={handleBreakdown}
                      disabled={breakdownLoading || !breakdownInput.trim()}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                    >
                      {breakdownLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                      {breakdownLoading ? 'Analyzing...' : 'Break it down'}
                    </button>
                  )}
                  {breakdownResult && (
                    <div className="space-y-3">
                      <div className="bg-purple-50 rounded-lg p-3">
                        <h4 className="font-medium text-sm text-purple-900 mb-2">
                          {breakdownResult.title}
                        </h4>
                        <div className="space-y-2">
                          {breakdownResult.subtasks.map((st, i) => (
                            <div key={i} className="bg-white rounded-md p-2 text-sm">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{st.title}</span>
                                <PriorityBadge priority={st.priority} />
                                {st.estimated_hours && (
                                  <span className="text-xs text-gray-400">{st.estimated_hours}h</span>
                                )}
                              </div>
                              {st.description && (
                                <p className="text-xs text-gray-500 mt-1">{st.description}</p>
                              )}
                              {st.suggested_assignee && (
                                <div className="flex items-center gap-1 mt-1">
                                  <MemberBadge name={st.suggested_assignee} />
                                  <span className="text-xs text-gray-400">{st.suggested_assignee}</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                        {breakdownResult.detected_blockers.length > 0 && (
                          <div className="mt-2 text-xs text-red-600">
                            Potential blockers: {breakdownResult.detected_blockers.join(', ')}
                          </div>
                        )}
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setBreakdownResult(null)}
                          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                        >
                          Redo
                        </button>
                        <button
                          onClick={handleApplyBreakdown}
                          disabled={saving}
                          className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                        >
                          {saving ? 'Applying...' : 'Apply to Board'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Meeting Notes tab */}
              {tab === 'meeting' && (
                <div className="space-y-3">
                  <textarea
                    placeholder="Paste meeting notes here..."
                    value={notesInput}
                    onChange={(e) => setNotesInput(e.target.value)}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
                  />
                  {!notesResult && (
                    <button
                      onClick={handleExtractNotes}
                      disabled={notesLoading || !notesInput.trim()}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                    >
                      {notesLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                      {notesLoading ? 'Extracting...' : 'Extract Tasks'}
                    </button>
                  )}
                  {notesResult && (
                    <div className="space-y-3">
                      {/* Status Updates for existing tasks */}
                      {notesResult.updates && notesResult.updates.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-blue-600 mb-1.5">Status Updates ({notesResult.updates.length})</p>
                          <div className="bg-blue-50 rounded-lg p-3 space-y-2">
                            {notesResult.updates.map((u, i) => (
                              <div key={i} className="bg-white rounded-md p-2 text-sm">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-medium text-gray-900">{u.task_title}</span>
                                  <span className="inline-flex items-center gap-1 text-xs">
                                    <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                                      {u.new_status?.replace('_', ' ')}
                                    </span>
                                  </span>
                                  {u.new_priority && (
                                    <>
                                      <ArrowRight className="w-3 h-3 text-gray-400" />
                                      <PriorityBadge priority={u.new_priority} />
                                    </>
                                  )}
                                </div>
                                {u.reason && (
                                  <p className="text-xs text-gray-500 mt-1">{u.reason}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* New tasks */}
                      {notesResult.tasks.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-purple-600 mb-1.5">New Tasks ({notesResult.tasks.length})</p>
                          <div className="bg-purple-50 rounded-lg p-3 space-y-2">
                            {notesResult.tasks.map((t, i) => (
                              <div key={i} className="bg-white rounded-md p-2 text-sm">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{t.title}</span>
                                  <PriorityBadge priority={t.priority} />
                                </div>
                                {t.description && (
                                  <p className="text-xs text-gray-500 mt-1">{t.description}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {notesResult.tasks.length === 0 && (!notesResult.updates || notesResult.updates.length === 0) && (
                        <p className="text-sm text-gray-500 text-center py-4">No tasks or updates found in the text.</p>
                      )}

                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setNotesResult(null)}
                          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                        >
                          Redo
                        </button>
                        <button
                          onClick={handleApplyNotes}
                          disabled={saving}
                          className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                        >
                          {saving ? 'Applying...' : `Apply ${notesResult.tasks.length} New + ${notesResult.updates?.length || 0} Updates`}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            /* Detail mode */
            <div className="space-y-4">
              {/* Status + Priority + Assignee */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
                  <select
                    value={editStatus}
                    onChange={(e) => { setEditStatus(e.target.value); handleUpdate('status', e.target.value) }}
                    disabled={updating}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                    <option value="blocked">Blocked</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Priority</label>
                  <select
                    value={editPriority}
                    onChange={(e) => { setEditPriority(e.target.value); handleUpdate('priority', e.target.value) }}
                    disabled={updating}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Assignee</label>
                  <select
                    value={editAssignee ?? ''}
                    onChange={(e) => { const v = e.target.value ? Number(e.target.value) : null; setEditAssignee(v); handleUpdate('assignee_id', v) }}
                    disabled={updating}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Description */}
              {detail?.description && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{detail.description}</p>
                </div>
              )}

              {/* Subtasks */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-2">
                  Subtasks {detail?.subtasks && `(${detail.subtasks.filter(s => s.status === 'done').length}/${detail.subtasks.length})`}
                </label>
                <div className="space-y-1">
                  {detail?.subtasks.map((st) => (
                    <button
                      key={st.id}
                      onClick={() => toggleSubtaskStatus(st)}
                      className="flex items-center gap-2 w-full text-left px-2 py-1.5 rounded-md hover:bg-gray-50 text-sm"
                    >
                      {st.status === 'done' ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                      ) : (
                        <Circle className="w-4 h-4 text-gray-300 shrink-0" />
                      )}
                      <span className={st.status === 'done' ? 'line-through text-gray-400' : 'text-gray-700'}>
                        {st.title}
                      </span>
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="text"
                    placeholder="Add subtask..."
                    value={subtaskTitle}
                    onChange={(e) => setSubtaskTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddSubtask()}
                    className="flex-1 px-2 py-1.5 border border-gray-300 rounded-lg text-sm"
                  />
                  <button
                    onClick={handleAddSubtask}
                    className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-md"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Activity Feed */}
              {activities.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-2">Activity</label>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {activities.map((a) => (
                      <div key={a.id} className="text-xs text-gray-500">
                        <span className="font-medium text-gray-700">{a.user_name}</span>{' '}
                        {a.action === 'status_changed' && a.details
                          ? `moved to ${(a.details as Record<string, string>).to}`
                          : a.action}
                        {' '}
                        <span className="text-gray-400">
                          {new Date(a.created_at).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Delete button */}
              <div className="flex justify-end pt-2 border-t border-gray-100">
                <button
                  onClick={handleDelete}
                  className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                >
                  Delete Task
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
