import { useState, useEffect } from 'react'
import { X, Loader2, Trophy, Crown } from 'lucide-react'
import { gamificationApi } from '../services/api'
import type { Badge, UserStats } from '../types'

interface BadgePanelProps {
  projectId: number
  onClose: () => void
}

const badgeIcons: Record<string, string> = {
  first_blood: '🩸',
  streak_3: '🔥',
  streak_7: '💫',
  streak_14: '⚡',
  xp_100: '💎',
  xp_500: '🏆',
  xp_1000: '👑',
  tasks_5: '✅',
  tasks_25: '🚀',
  tasks_50: '🌟',
  sprint_shipper: '📦',
}

export default function BadgePanel({ projectId, onClose }: BadgePanelProps) {
  const [badges, setBadges] = useState<Badge[]>([])
  const [leaderboard, setLeaderboard] = useState<UserStats[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'badges' | 'leaderboard'>('badges')

  useEffect(() => {
    loadData()
  }, [projectId])

  const loadData = async () => {
    try {
      const [badgesRes, lbRes] = await Promise.all([
        gamificationApi.getBadges(projectId),
        gamificationApi.getLeaderboard(projectId),
      ])
      setBadges(badgesRes.data)
      setLeaderboard(lbRes.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const unlockedCount = badges.filter((b) => b.unlocked).length

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-semibold text-gray-900">Achievements</h3>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-4">
          <button
            onClick={() => setTab('badges')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
              tab === 'badges' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Badges ({unlockedCount}/{badges.length})
          </button>
          <button
            onClick={() => setTab('leaderboard')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
              tab === 'leaderboard' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Leaderboard
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
          </div>
        ) : tab === 'badges' ? (
          <div className="grid grid-cols-3 gap-3">
            {badges.map((badge) => (
              <div
                key={badge.id}
                className={`text-center p-3 rounded-xl border transition-all ${
                  badge.unlocked
                    ? 'bg-amber-50 border-amber-200 shadow-sm'
                    : 'bg-gray-50 border-gray-200 opacity-50'
                }`}
              >
                <div className="text-2xl mb-1">
                  {badge.unlocked
                    ? (badgeIcons[badge.id] || badge.icon)
                    : '🔒'}
                </div>
                <p className="text-xs font-medium text-gray-800 truncate">{badge.name}</p>
                <p className="text-[10px] text-gray-500 mt-0.5 line-clamp-2">{badge.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {leaderboard.map((user, i) => (
              <div
                key={user.user_id}
                className={`flex items-center gap-3 p-3 rounded-xl ${
                  i === 0 ? 'bg-amber-50 border border-amber-200' :
                  i === 1 ? 'bg-gray-50 border border-gray-200' :
                  i === 2 ? 'bg-orange-50 border border-orange-200' :
                  'bg-white border border-gray-100'
                }`}
              >
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold bg-gray-200 text-gray-700">
                  {i === 0 ? <Crown className="w-4 h-4 text-amber-500" /> : `#${i + 1}`}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{user.user_name}</p>
                  <div className="flex items-center gap-2 text-[10px] text-gray-500">
                    <span>Lv.{user.level}</span>
                    <span>{user.xp} XP</span>
                    <span>{user.tasks_completed} shipped</span>
                    {user.current_streak > 0 && (
                      <span className="text-orange-500">🔥 {user.current_streak}d</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-indigo-600">{user.xp}</p>
                  <p className="text-[10px] text-gray-400">XP</p>
                </div>
              </div>
            ))}
            {leaderboard.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-8">No data yet. Ship some tasks!</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
