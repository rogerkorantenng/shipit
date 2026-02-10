import { Sparkles, Clock, CalendarDays } from 'lucide-react'
import PriorityBadge from './PriorityBadge'
import MemberBadge from './MemberBadge'
import type { Task } from '../types'

interface TaskCardProps {
  task: Task
  jiraSite?: string
  onClick: () => void
  onDragStart?: (e: React.DragEvent, task: Task) => void
}

export default function TaskCard({ task, jiraSite, onClick, onDragStart }: TaskCardProps) {
  return (
    <button
      onClick={onClick}
      draggable={!!onDragStart}
      onDragStart={(e) => onDragStart?.(e, task)}
      className="w-full text-left bg-white rounded-lg border border-gray-200 p-3 hover:shadow-sm hover:border-gray-300 transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <h4 className="text-sm font-medium text-gray-900 line-clamp-2">{task.title}</h4>
        <div className="flex items-center gap-1 shrink-0 mt-0.5">
          {task.jira_issue_key && (
            <a
              href={jiraSite ? `https://${jiraSite}/browse/${task.jira_issue_key}` : '#'}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-[10px] font-medium bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded hover:bg-blue-200 transition-colors"
            >
              {task.jira_issue_key}
            </a>
          )}
          {task.ai_generated && (
            <Sparkles className="w-3.5 h-3.5 text-purple-500" />
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <PriorityBadge priority={task.priority} />

        {task.assignee_name && <MemberBadge name={task.assignee_name} />}

        {task.subtask_count > 0 && (
          <span className="text-xs text-gray-400">
            {task.subtasks_done}/{task.subtask_count}
          </span>
        )}

        {task.estimated_hours && (
          <span className="flex items-center gap-0.5 text-xs text-gray-400">
            <Clock className="w-3 h-3" />
            {task.estimated_hours}h
          </span>
        )}

        {task.due_date && (
          <span className="flex items-center gap-0.5 text-xs text-gray-400">
            <CalendarDays className="w-3 h-3" />
            {task.due_date}
          </span>
        )}
      </div>
    </button>
  )
}
