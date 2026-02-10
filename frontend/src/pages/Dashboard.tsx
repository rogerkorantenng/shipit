import { useState, useEffect } from 'react'
import { Plus, Rocket, FolderKanban, ListChecks, CheckCircle2, LogOut } from 'lucide-react'
import Layout from '../components/Layout'
import ProjectCard from '../components/ProjectCard'
import { projectsApi, authApi } from '../services/api'
import type { Project } from '../types'

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [creating, setCreating] = useState(false)
  const [loading, setLoading] = useState(true)

  // Name entry state
  const [user, setUser] = useState<{ id: number; name: string } | null>(() => {
    try {
      const raw = localStorage.getItem('user')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })
  const [nameInput, setNameInput] = useState('')
  const [nameLoading, setNameLoading] = useState(false)
  const [nameError, setNameError] = useState('')

  const needsName = !user

  useEffect(() => {
    if (!needsName) loadData()
  }, [needsName])

  const handleNameSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nameInput.trim()) return
    setNameError('')
    setNameLoading(true)
    try {
      const res = await authApi.enter(nameInput.trim())
      localStorage.setItem('user', JSON.stringify(res.data))
      setUser(res.data)
    } catch (err: any) {
      setNameError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setNameLoading(false)
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await projectsApi.list()
      setProjects(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      await projectsApi.create({ name: newName, description: newDesc })
      setNewName('')
      setNewDesc('')
      setShowCreate(false)
      await loadData()
    } catch {
      // ignore
    } finally {
      setCreating(false)
    }
  }

  // Stats
  const totalTasks = projects.reduce(
    (sum, p) => sum + p.task_counts.todo + p.task_counts.in_progress + p.task_counts.done + p.task_counts.blocked,
    0
  )
  const activeTasks = projects.reduce(
    (sum, p) => sum + p.task_counts.todo + p.task_counts.in_progress + p.task_counts.blocked,
    0
  )
  const doneTasks = projects.reduce((sum, p) => sum + p.task_counts.done, 0)

  // Name entry modal
  if (needsName) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Rocket className="w-10 h-10 text-indigo-600" />
              <h1 className="text-3xl font-extrabold text-gray-900">ShipIt</h1>
            </div>
            <p className="text-gray-500">AI-powered team task board</p>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 text-center mb-1">
              Enter your username
            </h2>
            <p className="text-sm text-gray-500 text-center mb-6">
              Your unique username — no passwords needed.
            </p>

            <form onSubmit={handleNameSubmit} className="space-y-4">
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                required
                autoFocus
                minLength={2}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                placeholder="e.g. alex_dev"
              />

              {nameError && (
                <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  {nameError}
                </p>
              )}

              <button
                type="submit"
                disabled={nameLoading}
                className="w-full bg-indigo-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {nameLoading ? 'Please wait...' : 'Get Started'}
              </button>
            </form>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Welcome */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user.name}
            </h1>
            <p className="text-gray-500 mt-1">
              Here's an overview of your projects.
            </p>
          </div>
          <button
            onClick={() => { localStorage.removeItem('user'); setUser(null) }}
            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
            <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FolderKanban className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{projects.length}</p>
              <p className="text-sm text-gray-500">Projects</p>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
            <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
              <ListChecks className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{activeTasks}</p>
              <p className="text-sm text-gray-500">Active Tasks</p>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{doneTasks}</p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
          </div>
        </div>

        {/* Projects */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">My Projects</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </div>

        {/* Create project modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Create New Project
              </h3>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    required
                    autoFocus
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                    placeholder="e.g., Q1 Product Launch"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
                    placeholder="What is this project about?"
                  />
                </div>
                <div className="flex gap-3 justify-end">
                  <button
                    type="button"
                    onClick={() => setShowCreate(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {creating ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <FolderKanban className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No projects yet
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Create your first project and start shipping.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-1.5 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
            >
              <Plus className="w-4 h-4" />
              Create Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
