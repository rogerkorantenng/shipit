import axios from 'axios'
import type { Project, Board, ExtractTasksResult } from './types'

const API_BASE = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach X-User-Id header from chrome.storage
api.interceptors.request.use(async (config) => {
  const result = await chrome.storage.local.get('user')
  if (result.user?.id) {
    config.headers['X-User-Id'] = result.user.id
  }
  return config
})

export const authApi = {
  enter: (name: string) => api.post('/auth/enter', { name }),
}

export const projectsApi = {
  list: () => api.get<Project[]>('/projects/'),
}

export const tasksApi = {
  getBoard: (projectId: number) =>
    api.get<Board>(`/projects/${projectId}/tasks`),
  create: (projectId: number, data: { title: string; priority?: string; description?: string }) =>
    api.post(`/projects/${projectId}/tasks`, data),
  updateStatus: (projectId: number, taskId: number, status: string) =>
    api.put(`/projects/${projectId}/tasks/${taskId}`, { status }),
}

export const aiApi = {
  extractTasks: (projectId: number, text: string) =>
    api.post<ExtractTasksResult>(`/projects/${projectId}/ai/extract-tasks`, { text }),
  applyMeetingNotes: (projectId: number, data: { tasks: object[]; updates?: object[] }) =>
    api.post(`/projects/${projectId}/ai/meeting-notes/apply`, data),
}

export default api
