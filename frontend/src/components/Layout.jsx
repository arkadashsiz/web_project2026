import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [modules, setModules] = useState([])

  const onLogout = () => {
    logout()
    navigate('/login')
  }

  useEffect(() => {
    if (!user) {
      setModules([])
      return
    }
    api.get('/dashboard/modules/')
      .then((res) => setModules(res.data.modules || []))
      .catch(() => setModules([]))
  }, [user])

  const navLinks = useMemo(() => {
    if (!user) return []
    const links = [
      { key: 'dashboard', title: 'Dashboard', path: '/dashboard' },
      { key: 'notifications', title: 'Notifications', path: '/notifications' },
    ]
    for (const m of modules) {
      if (!m?.path || !m?.title) continue
      if (!links.find((x) => x.path === m.path)) links.push({ key: m.key || m.path, title: m.title, path: m.path })
    }
    if (!links.find((x) => x.path === '/high-alert')) {
      links.push({ key: 'high-alert', title: 'High Alert', path: '/high-alert' })
    }
    return links
  }, [user, modules])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand">City Police</Link>
        <nav>
          {navLinks.map((item) => (
            <NavLink key={item.key} to={item.path}>{item.title}</NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <header className="topbar">
          <div>
            <h1>Police Automation System</h1>
            <p>Los Angeles Central Operations</p>
          </div>
          <div className="topbar-actions">
            <span>{user ? user.username : 'Guest'}</span>
            {!user && <Link className="btn-link" to="/login">Login</Link>}
            {!user && <Link className="btn-link secondary" to="/register">Register</Link>}
            {user && <button onClick={onLogout}>Logout</button>}
          </div>
        </header>
        <section>{children}</section>
      </main>
    </div>
  )
}
