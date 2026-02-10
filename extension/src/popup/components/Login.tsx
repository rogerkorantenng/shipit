import { useState } from 'react'
import { authApi } from '../../api'
import type { User } from '../../types'

interface LoginProps {
  onLogin: (user: User) => void
}

export default function Login({ onLogin }: LoginProps) {
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const username = name.trim()
    if (!username) return
    if (username.length < 2) {
      setError('Username must be at least 2 characters')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await authApi.enter(username)
      onLogin(res.data as User)
    } catch {
      setError('Could not connect. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      <div className="login-brand">
        <div className="login-logo">S</div>
        <h1 className="login-title">ShipIt</h1>
        <p className="login-subtitle">AI-powered task board</p>
      </div>

      <div className="login-card">
        <h2 className="login-heading">Enter your username</h2>
        <p className="login-desc">Your unique username — no passwords needed.</p>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. alex_dev"
            autoFocus
            required
            minLength={2}
            className="input"
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Connecting...' : 'Get Started'}
          </button>
        </form>
      </div>
    </div>
  )
}
