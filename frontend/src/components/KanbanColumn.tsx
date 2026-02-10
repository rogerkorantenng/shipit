import { useState } from 'react'
import TaskCard from './TaskCard'
import type { Task } from '../types'

const statusColors: Record<string, string> = {
  todo: 'bg-gray-400',
  in_progress: 'bg-blue-500',
  done: 'bg-green-500',
  blocked: 'bg-red-500',
}

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
  blocked: 'Blocked',
}

interface KanbanColumnProps {
  status: string
  tasks: Task[]
  jiraSite?: string
  onTaskClick: (task: Task) => void
  onDragStart?: (e: React.DragEvent, task: Task) => void
  onDrop?: (status: string) => void
}

export default function KanbanColumn({ status, tasks, jiraSite, onTaskClick, onDragStart, onDrop }: KanbanColumnProps) {
  const [dragOver, setDragOver] = useState(false)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    onDrop?.(status)
  }

  return (
    <div
      className={`kanban-column flex flex-col bg-gray-50 rounded-xl p-3 min-w-[280px] transition-colors ${dragOver ? 'bg-indigo-50 ring-2 ring-indigo-300' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex items-center gap-2 mb-3 px-1">
        <div className={`w-2.5 h-2.5 rounded-full ${statusColors[status] || 'bg-gray-400'}`} />
        <h3 className="text-sm font-semibold text-gray-700">
          {statusLabels[status] || status}
        </h3>
        <span className="text-xs text-gray-400 ml-auto">{tasks.length}</span>
      </div>

      <div className="flex flex-col gap-2 flex-1 overflow-y-auto max-h-[calc(100vh-280px)]">
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-xs text-gray-400">
            {dragOver ? 'Drop here' : 'No tasks'}
          </div>
        ) : (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              jiraSite={jiraSite}
              onClick={() => onTaskClick(task)}
              onDragStart={onDragStart}
            />
          ))
        )}
      </div>
    </div>
  )
}
