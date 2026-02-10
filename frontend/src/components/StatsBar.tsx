import { useState, useEffect } from 'react'
import { Flame, Star, Trophy, Zap } from 'lucide-react'
import { gamificationApi } from '../services/api'
import type { UserStats } from '../types'

interface StatsBarProps {
  projectId: number
  onOpenBadges: () => void
}

export default function StatsBar({ projectId, onOpenBadges }: StatsBarProps) {
  const [stats, setStats] = useState<UserStats | null>(null)

  useEffect(() => {
    loadStats()
  }, [projectId])

  const loadStats = async () => {
    try {
      const res = await gamificationApi.getStats(projectId)
      setStats(res.data)
    } catch {
      // no stats yet
    }
  }

  if (!stats) return null

  const progressPct = stats.xp_needed > 0
    ? Math.min((stats.xp_progress / stats.xp_needed) * 100, 100)
    : 0

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-xl border border-indigo-100 px-4 py-3">
      <div className="flex items-center gap-4 flex-wrap">
        {/* Level */}
        <div className="flex items-center gap-1.5">
          <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center">
            <span className="text-xs font-bold text-white">{stats.level}</span>
          </div>
          <div className="min-w-0">
            <p className="text-[10px] text-gray-500 leading-none">Level</p>
            <p className="text-xs font-semibold text-gray-800 truncate">{stats.user_name}</p>
          </div>
        </div>

        {/* XP Bar */}
        <div className="flex-1 min-w-[120px]">
          <div className="flex items-center justify-between mb-0.5">
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-amber-500" />
              <span className="text-[10px] font-medium text-gray-600">{stats.xp} XP</span>
            </div>
            <span className="text-[10px] text-gray-400">
              {stats.xp_progress}/{stats.xp_needed} to next
            </span>
          </div>
          <div className="h-2 bg-white/80 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* Streak */}
        <div className="flex items-center gap-1.5">
          <Flame className={`w-4 h-4 ${stats.current_streak > 0 ? 'text-orange-500' : 'text-gray-300'}`} />
          <div>
            <p className="text-sm font-bold text-gray-800 leading-none">{stats.current_streak}</p>
            <p className="text-[10px] text-gray-500">day streak</p>
          </div>
        </div>

        {/* Tasks Done */}
        <div className="flex items-center gap-1.5">
          <Star className="w-4 h-4 text-amber-400" />
          <div>
            <p className="text-sm font-bold text-gray-800 leading-none">{stats.tasks_completed}</p>
            <p className="text-[10px] text-gray-500">shipped</p>
          </div>
        </div>

        {/* Badges button */}
        <button
          onClick={onOpenBadges}
          className="flex items-center gap-1 px-2.5 py-1.5 bg-white/80 border border-indigo-200 rounded-lg hover:bg-white transition-colors"
        >
          <Trophy className="w-3.5 h-3.5 text-indigo-500" />
          <span className="text-xs font-medium text-indigo-700">
            {stats.badges.length} Badge{stats.badges.length !== 1 ? 's' : ''}
          </span>
        </button>
      </div>
    </div>
  )
}
