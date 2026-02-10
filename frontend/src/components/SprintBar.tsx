import { Play, CheckCircle, Layers } from 'lucide-react'
import type { Sprint } from '../types'

interface SprintBarProps {
  sprints: Sprint[]
  selectedSprintId: number | null
  viewMode: 'sprint' | 'backlog'
  onSelectSprint: (sprintId: number) => void
  onSelectBacklog: () => void
  onStartSprint: (sprintId: number) => void
  onCompleteSprint: (sprintId: number) => void
}

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800 border-green-300',
  planned: 'bg-blue-100 text-blue-800 border-blue-300',
  completed: 'bg-gray-100 text-gray-600 border-gray-300',
  cancelled: 'bg-red-100 text-red-600 border-red-300',
}

export default function SprintBar({
  sprints,
  selectedSprintId,
  viewMode,
  onSelectSprint,
  onSelectBacklog,
  onStartSprint,
  onCompleteSprint,
}: SprintBarProps) {
  const backlogCount = 0 // Will be passed or computed externally if needed

  return (
    <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1">
      {/* Backlog tab */}
      <button
        onClick={onSelectBacklog}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors whitespace-nowrap ${
          viewMode === 'backlog'
            ? 'bg-gray-900 text-white border-gray-900'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
        }`}
      >
        <Layers className="w-3.5 h-3.5" />
        Backlog
      </button>

      {/* Sprint tabs */}
      {sprints
        .filter((s) => s.status !== 'completed' && s.status !== 'cancelled')
        .map((sprint) => {
          const isSelected = viewMode === 'sprint' && selectedSprintId === sprint.id
          const totalTasks = Object.values(sprint.task_counts || {}).reduce((a, b) => a + b, 0)

          return (
            <div key={sprint.id} className="flex items-center gap-1">
              <button
                onClick={() => onSelectSprint(sprint.id)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors whitespace-nowrap ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : statusColors[sprint.status] || 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                {sprint.name}
                {sprint.status === 'active' && (
                  <span className={`text-[10px] px-1 py-0.5 rounded ${isSelected ? 'bg-indigo-500' : 'bg-green-200 text-green-800'}`}>
                    Active
                  </span>
                )}
                {totalTasks > 0 && (
                  <span className={`text-[10px] px-1 py-0.5 rounded ${isSelected ? 'bg-indigo-500' : 'bg-gray-200 text-gray-600'}`}>
                    {totalTasks}
                  </span>
                )}
              </button>

              {/* Inline actions */}
              {sprint.status === 'planned' && (
                <button
                  onClick={(e) => { e.stopPropagation(); onStartSprint(sprint.id) }}
                  className="p-1 text-green-600 hover:bg-green-50 rounded"
                  title="Start Sprint"
                >
                  <Play className="w-3.5 h-3.5" />
                </button>
              )}
              {sprint.status === 'active' && (
                <button
                  onClick={(e) => { e.stopPropagation(); onCompleteSprint(sprint.id) }}
                  className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                  title="Complete Sprint"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )
        })}

      {/* Completed sprints (collapsed) */}
      {sprints.filter((s) => s.status === 'completed').length > 0 && (
        <details className="inline-block">
          <summary className="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-400 cursor-pointer hover:text-gray-600">
            +{sprints.filter((s) => s.status === 'completed').length} completed
          </summary>
          <div className="absolute mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-1 z-10">
            {sprints
              .filter((s) => s.status === 'completed')
              .map((sprint) => (
                <button
                  key={sprint.id}
                  onClick={() => onSelectSprint(sprint.id)}
                  className="block w-full text-left px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 rounded"
                >
                  {sprint.name}
                </button>
              ))}
          </div>
        </details>
      )}
    </div>
  )
}
