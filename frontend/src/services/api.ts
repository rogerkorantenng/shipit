import axios from 'axios'
import type {
  Board,
  TaskDetail,
  Task,
  Sprint,
  BreakdownResult,
  MeetingNotesResult,
  BlockerResult,
  DigestResult,
  SprintPlanResult,
  PriorityScoreResult,
  StandupResult,
  AnalyticsResult,
  JiraConnection,
  JiraProject,
  Pulse,
  TeamPulse,
  PulseInsights,
  UserStats,
  Badge,
  AgentStatus,
  AgentEvent,
  ServiceConnection,
} from '../types'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach X-User-Id header to requests
api.interceptors.request.use((config) => {
  const raw = localStorage.getItem('user')
  if (raw) {
    try {
      const user = JSON.parse(raw)
      if (user.id) {
        config.headers['X-User-Id'] = user.id
      }
    } catch {
      // ignore bad JSON
    }
  }
  return config
})

// --- Auth ---

export const authApi = {
  enter: (name: string) => api.post('/auth/enter', { name }),
}

// --- Projects ---

export const projectsApi = {
  list: () => api.get('/projects/'),
  create: (data: { name: string; description: string }) =>
    api.post('/projects/', data),
  get: (id: number) => api.get(`/projects/${id}`),
  delete: (id: number) => api.delete(`/projects/${id}`),
  listMembers: (projectId: number) =>
    api.get(`/projects/${projectId}/members`),
  addMember: (projectId: number, name: string) =>
    api.post(`/projects/${projectId}/members`, { name }),
  removeMember: (projectId: number, userId: number) =>
    api.delete(`/projects/${projectId}/members/${userId}`),
  joinByCode: (joinCode: string) =>
    api.post('/projects/join', { join_code: joinCode }),
}

// --- Tasks ---

export interface TaskCreateData {
  title: string
  description?: string
  status?: string
  priority?: string
  assignee_id?: number | null
  due_date?: string | null
  estimated_hours?: number | null
  parent_task_id?: number | null
  ai_generated?: boolean
  sprint_id?: number | null
}

export const tasksApi = {
  getBoard: (projectId: number, params?: { sprint_id?: number; backlog?: boolean }) =>
    api.get<Board>(`/projects/${projectId}/tasks`, { params }),
  create: (projectId: number, data: TaskCreateData) =>
    api.post<Task>(`/projects/${projectId}/tasks`, data),
  get: (projectId: number, taskId: number) =>
    api.get<TaskDetail>(`/projects/${projectId}/tasks/${taskId}`),
  update: (projectId: number, taskId: number, data: Partial<TaskCreateData>) =>
    api.put<Task>(`/projects/${projectId}/tasks/${taskId}`, data),
  delete: (projectId: number, taskId: number) =>
    api.delete(`/projects/${projectId}/tasks/${taskId}`),
}

// --- AI ---

export const aiApi = {
  breakdown: (projectId: number, description: string) =>
    api.post<BreakdownResult>(`/projects/${projectId}/ai/breakdown`, { description }),
  applyBreakdown: (projectId: number, data: { title: string; priority: string; subtasks: object[] }) =>
    api.post(`/projects/${projectId}/ai/breakdown/apply`, data),
  meetingNotes: (projectId: number, notes: string) =>
    api.post<MeetingNotesResult>(`/projects/${projectId}/ai/meeting-notes`, { notes }),
  applyMeetingNotes: (projectId: number, data: { tasks: object[]; updates?: object[] }) =>
    api.post(`/projects/${projectId}/ai/meeting-notes/apply`, data),
  detectBlockers: (projectId: number) =>
    api.post<BlockerResult>(`/projects/${projectId}/ai/blockers`),
  digest: (projectId: number) =>
    api.post<DigestResult>(`/projects/${projectId}/ai/digest`),
  sprintPlan: (projectId: number, capacityHours: number) =>
    api.post<SprintPlanResult>(`/projects/${projectId}/ai/sprint-plan`, { capacity_hours: capacityHours }),
  applySprintPlan: (projectId: number, data: {
    sprint_name: string; goal?: string; start_date?: string | null;
    end_date?: string | null; capacity_hours?: number | null;
    assignments: { task_id: number; assignee: string }[];
  }) =>
    api.post(`/projects/${projectId}/ai/sprint-plan/apply`, data),
  priorityScore: (projectId: number) =>
    api.post<PriorityScoreResult>(`/projects/${projectId}/ai/priority-score`),
  applyPriorityScore: (projectId: number, updates: { task_id: number; priority: string }[]) =>
    api.post(`/projects/${projectId}/ai/priority-score/apply`, { updates }),
  standup: (projectId: number) =>
    api.post<StandupResult>(`/projects/${projectId}/ai/standup`),
  analytics: (projectId: number) =>
    api.get<AnalyticsResult>(`/projects/${projectId}/ai/analytics`),
}

// --- Jira ---

export const jiraApi = {
  connect: (projectId: number, data: { jira_site: string; jira_email: string; jira_api_token: string; jira_project_key: string }) =>
    api.post(`/projects/${projectId}/jira/connect`, data),
  getConnection: (projectId: number) =>
    api.get<JiraConnection>(`/projects/${projectId}/jira/connection`),
  disconnect: (projectId: number) =>
    api.delete(`/projects/${projectId}/jira/connection`),
  revealCredentials: (projectId: number) =>
    api.get<{ jira_site: string; jira_email: string; jira_api_token: string; jira_project_key: string; jira_board_id: number | null }>(`/projects/${projectId}/jira/connection/reveal`),
  listProjects: (projectId: number) =>
    api.get<JiraProject[]>(`/projects/${projectId}/jira/projects`),
  export: (projectId: number) =>
    api.post(`/projects/${projectId}/jira/export`),
  import: (projectId: number) =>
    api.post(`/projects/${projectId}/jira/import`),
  sync: (projectId: number) =>
    api.post(`/projects/${projectId}/jira/sync`),
  importSprints: (projectId: number) =>
    api.post(`/projects/${projectId}/jira/import-sprints`),
  exportSprint: (projectId: number, sprintId: number) =>
    api.post(`/projects/${projectId}/jira/export-sprint/${sprintId}`),
}

// --- Sprints ---

export const sprintsApi = {
  list: (projectId: number) =>
    api.get<Sprint[]>(`/projects/${projectId}/sprints`),
  getActive: (projectId: number) =>
    api.get<Sprint | null>(`/projects/${projectId}/sprints/active`),
  create: (projectId: number, data: { name: string; goal?: string; start_date?: string | null; end_date?: string | null; capacity_hours?: number | null }) =>
    api.post<Sprint>(`/projects/${projectId}/sprints`, data),
  update: (projectId: number, sprintId: number, data: Partial<{ name: string; goal: string; status: string; start_date: string; end_date: string; capacity_hours: number }>) =>
    api.put<Sprint>(`/projects/${projectId}/sprints/${sprintId}`, data),
  delete: (projectId: number, sprintId: number) =>
    api.delete(`/projects/${projectId}/sprints/${sprintId}`),
  start: (projectId: number, sprintId: number) =>
    api.post<Sprint>(`/projects/${projectId}/sprints/${sprintId}/start`),
  complete: (projectId: number, sprintId: number) =>
    api.post<Sprint>(`/projects/${projectId}/sprints/${sprintId}/complete`),
  moveTasks: (projectId: number, sprintId: number, taskIds: number[], action: 'add' | 'remove') =>
    api.post(`/projects/${projectId}/sprints/${sprintId}/tasks`, { task_ids: taskIds, action }),
  getBacklog: (projectId: number) =>
    api.get(`/projects/${projectId}/backlog`),
}

// --- Pulse ---

export const pulseApi = {
  log: (projectId: number, data: { energy: number; mood: number; note?: string }) =>
    api.post<Pulse>(`/projects/${projectId}/pulse`, data),
  getToday: (projectId: number) =>
    api.get<Pulse | null>(`/projects/${projectId}/pulse/today`),
  getHistory: (projectId: number, days?: number) =>
    api.get<Pulse[]>(`/projects/${projectId}/pulse/history`, { params: days ? { days } : {} }),
  getTeam: (projectId: number) =>
    api.get<TeamPulse>(`/projects/${projectId}/pulse/team`),
  getInsights: (projectId: number) =>
    api.get<PulseInsights>(`/projects/${projectId}/pulse/insights`),
}

// --- Gamification ---

export const gamificationApi = {
  getStats: (projectId: number) =>
    api.get<UserStats>(`/projects/${projectId}/stats`),
  getBadges: (projectId: number) =>
    api.get<Badge[]>(`/projects/${projectId}/stats/badges`),
  getLeaderboard: (projectId: number) =>
    api.get<UserStats[]>(`/projects/${projectId}/leaderboard`),
}

// --- Activity ---

export const activityApi = {
  list: (projectId: number, since?: string) =>
    api.get(`/projects/${projectId}/activity`, { params: since ? { since } : {} }),
  forTask: (projectId: number, taskId: number) =>
    api.get(`/projects/${projectId}/activity/task/${taskId}`),
}

// --- Agents ---

export const agentsApi = {
  fleetStatus: () =>
    api.get<{ agents: AgentStatus[]; bus_running: boolean }>('/agents/status'),
  listProjectAgents: (projectId: number) =>
    api.get<{ agents: AgentStatus[] }>(`/projects/${projectId}/agents`),
  updateAgentConfig: (projectId: number, agentName: string, data: { enabled?: boolean; config?: Record<string, unknown> }) =>
    api.put(`/projects/${projectId}/agents/${agentName}`, data),
  triggerAgent: (projectId: number, agentName: string, eventData?: Record<string, unknown>) =>
    api.post(`/projects/${projectId}/agents/${agentName}/trigger`, { event_data: eventData || {} }),
  listEvents: (projectId: number, limit?: number) =>
    api.get<{ events: AgentEvent[] }>(`/projects/${projectId}/agents/events`, { params: limit ? { limit } : {} }),
  createConnection: (projectId: number, data: { service_type: string; base_url?: string; api_token: string; config?: Record<string, unknown> }) =>
    api.post(`/projects/${projectId}/connections`, data),
  listConnections: (projectId: number) =>
    api.get<{ connections: ServiceConnection[] }>(`/projects/${projectId}/connections`),
  revealConnection: (projectId: number, serviceType: string) =>
    api.get<{ service_type: string; base_url: string | null; api_token: string; config: Record<string, unknown> }>(`/projects/${projectId}/connections/${serviceType}/reveal`),
  deleteConnection: (projectId: number, serviceType: string) =>
    api.delete(`/projects/${projectId}/connections/${serviceType}`),
  testConnection: (projectId: number, serviceType: string) =>
    api.post<{ status: string; error?: string }>(`/projects/${projectId}/connections/${serviceType}/test`),
}

export default api
