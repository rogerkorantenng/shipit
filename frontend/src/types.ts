export interface User {
  id: number
  name: string
}

export interface Project {
  id: number
  name: string
  description: string
  member_count: number
  task_counts: TaskCounts
  created_at: string
}

export interface TaskCounts {
  todo: number
  in_progress: number
  done: number
  blocked: number
}

export interface Member {
  id: number
  name: string
  role: string
  workload: number
}

export interface Task {
  id: number
  project_id: number
  parent_task_id: number | null
  title: string
  description: string
  status: string
  priority: string
  assignee_id: number | null
  assignee_name: string | null
  due_date: string | null
  estimated_hours: number | null
  ai_generated: boolean
  jira_issue_key: string | null
  sprint_id: number | null
  position: number
  subtask_count: number
  subtasks_done: number
  created_at: string
  updated_at: string
}

export interface TaskDetail extends Task {
  subtasks: Task[]
}

export interface Board {
  todo: Task[]
  in_progress: Task[]
  done: Task[]
  blocked: Task[]
}

export interface Activity {
  id: number
  project_id: number
  task_id: number | null
  user_id: number
  user_name: string
  action: string
  details: Record<string, unknown> | null
  created_at: string
}

export interface BreakdownResult {
  title: string
  subtasks: {
    title: string
    description: string
    priority: string
    estimated_hours: number | null
    suggested_assignee: string | null
  }[]
  suggested_priority: string
  detected_blockers: string[]
}

export interface TaskUpdate {
  task_id: number
  task_title: string
  new_status: string
  new_priority: string | null
  new_assignee: string | null
  reason: string
}

export interface MeetingNotesResult {
  tasks: {
    title: string
    description: string
    priority: string
    estimated_hours: number | null
    suggested_assignee: string | null
  }[]
  updates: TaskUpdate[]
}

export interface BlockerResult {
  blockers: {
    task_id: number
    task_title: string
    issue: string
    severity: string
    suggestion: string
  }[]
}

export interface DigestResult {
  summary: string
  moved: string[]
  stuck: string[]
  at_risk: string[]
}

export interface SprintPlanResult {
  sprint_name: string
  goal: string
  start_date: string | null
  end_date: string | null
  total_hours: number
  assignments: {
    task_id: number
    task_title: string
    assignee: string
    estimated_hours: number
    priority: string
    reason: string
  }[]
  deferred: {
    task_id: number
    task_title: string
    reason: string
  }[]
}

export interface PriorityScoreResult {
  recommendations: {
    task_id: number
    task_title: string
    current_priority: string
    suggested_priority: string
    score: number
    reason: string
  }[]
}

export interface StandupResult {
  date: string
  standups: {
    member: string
    did: string[]
    doing: string[]
    blocked: string[]
  }[]
  team_summary: string
}

export interface AnalyticsResult {
  status_counts: Record<string, number>
  priority_counts: Record<string, number>
  workload: {
    name: string
    assigned: number
    completed: number
    estimated_hours: number
  }[]
  total_tasks: number
  completion_rate: number
}

export interface Sprint {
  id: number
  project_id: number
  name: string
  goal: string
  status: string
  start_date: string | null
  end_date: string | null
  capacity_hours: number | null
  jira_sprint_id: number | null
  task_counts: Record<string, number>
  created_at: string
  updated_at: string
}

export interface JiraConnection {
  connected: boolean
  jira_site?: string
  jira_email?: string
  jira_project_key?: string
  enabled?: boolean
  last_sync_at?: string | null
  jira_board_id?: number | null
  sprints_available?: boolean
}

export interface JiraProject {
  key: string
  name: string
}

// --- Pulse ---

export interface Pulse {
  id: number
  user_id: number
  user_name: string
  energy: number
  mood: number
  note: string | null
  date: string
  created_at: string
}

export interface TeamPulse {
  date: string
  logged_count: number
  member_count: number
  avg_energy: number
  avg_mood: number
  entries: Pulse[]
}

export interface PulseInsights {
  insights: string
  patterns: { observation: string; advice: string }[]
  energy_trend: string
  mood_trend: string
  best_day: string
  burnout_risk: string
}

// --- Gamification ---

export interface UserStats {
  user_id: number
  user_name: string
  xp: number
  level: number
  xp_progress: number
  xp_needed: number
  current_streak: number
  longest_streak: number
  tasks_completed: number
  badges: string[]
  last_active_date: string | null
  rank?: number
}

export interface Badge {
  id: string
  name: string
  description: string
  icon: string
  unlocked: boolean
}

export interface GamificationResult {
  xp_gained: number
  total_xp: number
  level: number
  current_streak: number
  new_badges: string[]
}

// --- Agents ---

export interface AgentStatus {
  name: string
  description: string
  status: 'idle' | 'running' | 'error' | 'disabled'
  enabled: boolean
  subscribed_events: string[]
  metrics: {
    events_processed: number
    errors: number
    last_run: string | null
    avg_processing_ms: number
  }
  project_config?: {
    enabled: boolean
    config: Record<string, unknown>
    last_run_at: string | null
    total_events_processed: number
  }
}

export interface AgentEvent {
  event_id: string
  type: string
  source_agent: string
  project_id: number | null
  data: Record<string, unknown>
  timestamp: string
  correlation_id: string | null
}

export interface ServiceConnection {
  id: number
  service_type: string
  base_url: string | null
  enabled: boolean
  config: Record<string, unknown> | null
  last_sync_at: string | null
  has_token: boolean
}
