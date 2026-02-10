import { Link } from 'react-router-dom'
import { Users, CheckCircle2, ListTodo } from 'lucide-react'
import type { Project } from '../types'

export default function ProjectCard({ project }: { project: Project }) {
  const { task_counts: tc } = project
  const total = tc.todo + tc.in_progress + tc.done + tc.blocked
  const progress = total > 0 ? Math.round((tc.done / total) * 100) : 0

  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
    >
      <h3 className="font-semibold text-gray-900 mb-1 truncate">{project.name}</h3>
      {project.description && (
        <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.description}</p>
      )}

      <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
        <span className="flex items-center gap-1">
          <Users className="w-3.5 h-3.5" />
          {project.member_count}
        </span>
        <span className="flex items-center gap-1">
          <ListTodo className="w-3.5 h-3.5" />
          {total} tasks
        </span>
        <span className="flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
          {tc.done} done
        </span>
      </div>

      {total > 0 && (
        <div className="w-full bg-gray-100 rounded-full h-1.5">
          <div
            className="bg-green-500 h-1.5 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </Link>
  )
}
