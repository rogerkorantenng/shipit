import { useState, useEffect } from 'react'
import type { User, Project, ExtractedTask, TaskUpdateItem } from '../types'
import Login from './components/Login'
import ProjectPicker from './components/ProjectPicker'
import TextInput from './components/TextInput'
import TaskPreview from './components/TaskPreview'
import BoardView from './components/BoardView'
import QuickAdd from './components/QuickAdd'

type View = 'login' | 'main' | 'preview' | 'success'
type Tab = 'extract' | 'board' | 'add'

export default function App() {
  const [view, setView] = useState<View>('login')
  const [tab, setTab] = useState<Tab>('extract')
  const [user, setUser] = useState<User | null>(null)
  const [project, setProject] = useState<Project | null>(null)
  const [text, setText] = useState('')
  const [tasks, setTasks] = useState<ExtractedTask[]>([])
  const [updates, setUpdates] = useState<TaskUpdateItem[]>([])

  useEffect(() => {
    chrome.storage.local.get(['user', 'selectedProject', 'selectedText'], (result) => {
      if (result.user) {
        setUser(result.user)
        if (result.selectedProject) {
          setProject(result.selectedProject)
        }
        setView('main')
      }
      if (result.selectedText) {
        setText(result.selectedText)
        chrome.storage.local.remove('selectedText')
        chrome.action.setBadgeText({ text: '' })
      }
    })
  }, [])

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser)
    chrome.storage.local.set({ user: loggedInUser })
    setView('main')
  }

  const handleLogout = () => {
    setUser(null)
    setProject(null)
    chrome.storage.local.remove(['user', 'selectedProject'])
    setView('login')
  }

  const handleProjectSelect = (p: Project) => {
    setProject(p)
    chrome.storage.local.set({ selectedProject: p })
  }

  const handleExtracted = (extractedTasks: ExtractedTask[], extractedUpdates: TaskUpdateItem[]) => {
    setTasks(extractedTasks)
    setUpdates(extractedUpdates)
    setView('preview')
  }

  const handleApplied = () => {
    setView('success')
    setText('')
    setTasks([])
    setUpdates([])
  }

  const handleBack = () => {
    setView('main')
    setTasks([])
    setUpdates([])
  }

  if (view === 'login') {
    return (
      <div className="popup">
        <Login onLogin={handleLogin} />
      </div>
    )
  }

  if (view === 'success') {
    return (
      <div className="popup">
        <header className="popup-header">
          <h1>ShipIt</h1>
        </header>
        <div className="success-view">
          <div className="success-icon">&#10003;</div>
          <h2>Applied!</h2>
          <p>Changes have been applied to your board.</p>
          <button className="btn btn-primary" onClick={() => setView('main')}>
            Continue
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="popup">
      <header className="popup-header">
        <h1>ShipIt</h1>
        <div className="header-actions">
          {user && <span className="user-name">{user.name}</span>}
          <button className="btn-link" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {/* Project picker — always visible */}
      <div className="main-view" style={{ paddingBottom: 0 }}>
        <ProjectPicker selected={project} onSelect={handleProjectSelect} />
      </div>

      {project && view === 'main' && (
        <>
          {/* Tab bar */}
          <div className="tab-bar">
            <button
              className={`tab-btn ${tab === 'extract' ? 'active' : ''}`}
              onClick={() => setTab('extract')}
            >
              Extract
            </button>
            <button
              className={`tab-btn ${tab === 'board' ? 'active' : ''}`}
              onClick={() => setTab('board')}
            >
              Board
            </button>
            <button
              className={`tab-btn ${tab === 'add' ? 'active' : ''}`}
              onClick={() => setTab('add')}
            >
              Quick Add
            </button>
          </div>

          <div className="tab-content">
            {tab === 'extract' && (
              <TextInput
                text={text}
                setText={setText}
                projectId={project.id}
                onExtracted={handleExtracted}
              />
            )}
            {tab === 'board' && (
              <BoardView projectId={project.id} />
            )}
            {tab === 'add' && (
              <QuickAdd projectId={project.id} />
            )}
          </div>
        </>
      )}

      {view === 'preview' && project && (
        <TaskPreview
          tasks={tasks}
          updates={updates}
          projectId={project.id}
          onApplied={handleApplied}
          onBack={handleBack}
        />
      )}
    </div>
  )
}
