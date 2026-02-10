import { useState, useEffect } from 'react'
import { Heart, Battery, Loader2, ChevronDown, ChevronUp, Brain } from 'lucide-react'
import { pulseApi } from '../services/api'
import type { Pulse, TeamPulse, PulseInsights } from '../types'

interface PulseWidgetProps {
  projectId: number
}

const moodEmojis = ['', '😫', '😕', '😐', '😊', '🔥']
const energyLabels = ['', 'Exhausted', 'Low', 'Okay', 'Good', 'Pumped']

export default function PulseWidget({ projectId }: PulseWidgetProps) {
  const [todayPulse, setTodayPulse] = useState<Pulse | null>(null)
  const [energy, setEnergy] = useState(3)
  const [mood, setMood] = useState(3)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)
  const [team, setTeam] = useState<TeamPulse | null>(null)
  const [insights, setInsights] = useState<PulseInsights | null>(null)
  const [insightsLoading, setInsightsLoading] = useState(false)

  useEffect(() => {
    loadToday()
  }, [projectId])

  const loadToday = async () => {
    try {
      const res = await pulseApi.getToday(projectId)
      if (res.data) {
        setTodayPulse(res.data)
        setEnergy(res.data.energy)
        setMood(res.data.mood)
        setNote(res.data.note || '')
      }
    } catch {
      // no pulse yet today
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    setSaving(true)
    try {
      const res = await pulseApi.log(projectId, { energy, mood, note: note || undefined })
      setTodayPulse(res.data)
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  const loadTeam = async () => {
    if (team) return
    try {
      const res = await pulseApi.getTeam(projectId)
      setTeam(res.data)
    } catch {
      // ignore
    }
  }

  const loadInsights = async () => {
    if (insights) return
    setInsightsLoading(true)
    try {
      const res = await pulseApi.getInsights(projectId)
      setInsights(res.data)
    } catch {
      // ignore
    } finally {
      setInsightsLoading(false)
    }
  }

  const handleExpand = () => {
    const next = !expanded
    setExpanded(next)
    if (next) {
      loadTeam()
      loadInsights()
    }
  }

  if (loading) return null

  return (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-100 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Heart className="w-4 h-4 text-pink-500" />
          <span className="text-sm font-semibold text-gray-800">Vibe Check</span>
        </div>
        <button
          onClick={handleExpand}
          className="p-1 text-gray-400 hover:text-gray-600"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {todayPulse ? (
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Battery className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-sm text-gray-700">{energyLabels[todayPulse.energy]}</span>
          </div>
          <div className="text-lg">{moodEmojis[todayPulse.mood]}</div>
          {todayPulse.note && (
            <span className="text-xs text-gray-500 truncate">{todayPulse.note}</span>
          )}
          <span className="text-[10px] text-gray-400 ml-auto">Logged</span>
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">Energy</span>
              <span className="text-xs text-gray-600">{energyLabels[energy]}</span>
            </div>
            <div className="flex gap-1.5">
              {[1, 2, 3, 4, 5].map((v) => (
                <button
                  key={v}
                  onClick={() => setEnergy(v)}
                  className={`flex-1 h-7 rounded-md text-xs font-medium transition-all ${
                    v <= energy
                      ? 'bg-amber-400 text-white'
                      : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">Mood</span>
              <span className="text-sm">{moodEmojis[mood]}</span>
            </div>
            <div className="flex gap-1.5">
              {[1, 2, 3, 4, 5].map((v) => (
                <button
                  key={v}
                  onClick={() => setMood(v)}
                  className={`flex-1 h-7 rounded-md text-sm transition-all ${
                    v <= mood
                      ? 'bg-pink-400 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {moodEmojis[v]}
                </button>
              ))}
            </div>
          </div>

          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="How are you feeling? (optional)"
            className="w-full px-2.5 py-1.5 text-xs border border-purple-200 rounded-lg bg-white/70 focus:ring-1 focus:ring-purple-400 outline-none"
          />

          <button
            onClick={handleSubmit}
            disabled={saving}
            className="w-full py-1.5 bg-purple-600 text-white text-xs font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {saving ? 'Logging...' : 'Log Vibe'}
          </button>
        </div>
      )}

      {/* Expanded: Team + Insights */}
      {expanded && (
        <div className="mt-4 pt-3 border-t border-purple-200 space-y-3">
          {team && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Team Today</p>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <Battery className="w-3 h-3 text-amber-500" />
                  <span className="text-xs text-gray-700">Avg Energy: {team.avg_energy.toFixed(1)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Heart className="w-3 h-3 text-pink-500" />
                  <span className="text-xs text-gray-700">Avg Mood: {team.avg_mood.toFixed(1)}</span>
                </div>
                <span className="text-[10px] text-gray-400 ml-auto">
                  {team.logged_count}/{team.member_count} logged
                </span>
              </div>
              {team.entries.length > 0 && (
                <div className="mt-2 space-y-1">
                  {team.entries.map((e) => (
                    <div key={e.id} className="flex items-center gap-2 text-xs">
                      <span className="text-gray-700 font-medium w-20 truncate">{e.user_name}</span>
                      <span>{moodEmojis[e.mood]}</span>
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-400 rounded-full"
                          style={{ width: `${(e.energy / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {insightsLoading ? (
            <div className="flex items-center gap-2 py-2">
              <Loader2 className="w-3 h-3 animate-spin text-purple-500" />
              <span className="text-xs text-gray-500">Generating insights...</span>
            </div>
          ) : insights ? (
            <div>
              <div className="flex items-center gap-1 mb-2">
                <Brain className="w-3 h-3 text-purple-500" />
                <p className="text-xs font-medium text-gray-500">AI Insights</p>
              </div>
              <p className="text-xs text-gray-700 mb-2">{insights.insights}</p>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="bg-white/60 rounded-lg p-2">
                  <span className="text-gray-500">Energy Trend:</span>{' '}
                  <span className="font-medium text-gray-700">{insights.energy_trend}</span>
                </div>
                <div className="bg-white/60 rounded-lg p-2">
                  <span className="text-gray-500">Mood Trend:</span>{' '}
                  <span className="font-medium text-gray-700">{insights.mood_trend}</span>
                </div>
                <div className="bg-white/60 rounded-lg p-2">
                  <span className="text-gray-500">Best Day:</span>{' '}
                  <span className="font-medium text-gray-700">{insights.best_day}</span>
                </div>
                <div className="bg-white/60 rounded-lg p-2">
                  <span className="text-gray-500">Burnout Risk:</span>{' '}
                  <span className={`font-medium ${
                    insights.burnout_risk === 'low' ? 'text-green-600'
                    : insights.burnout_risk === 'medium' ? 'text-amber-600'
                    : 'text-red-600'
                  }`}>{insights.burnout_risk}</span>
                </div>
              </div>
              {insights.patterns.length > 0 && (
                <div className="mt-2 space-y-1">
                  {insights.patterns.map((p, i) => (
                    <div key={i} className="text-[10px] bg-white/60 rounded-lg p-1.5">
                      <span className="text-gray-600">{p.observation}</span>
                      <span className="text-purple-600 ml-1">{p.advice}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
