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

export interface Task {
  id: number
  title: string
  status: string
  priority: string
  assignee_name: string | null
  due_date: string | null
  estimated_hours: number | null
  ai_generated: boolean
  jira_issue_key: string | null
  subtask_count: number
  subtasks_done: number
}

export interface Board {
  todo: Task[]
  in_progress: Task[]
  done: Task[]
  blocked: Task[]
}

export interface ExtractedTask {
  title: string
  description: string
  priority: string
  estimated_hours: number | null
  suggested_assignee: string | null
}

export interface TaskUpdateItem {
  task_id: number
  task_title: string
  new_status: string
  new_priority: string | null
  new_assignee: string | null
  reason: string
}

export interface ExtractTasksResult {
  tasks: ExtractedTask[]
  updates: TaskUpdateItem[]
}
