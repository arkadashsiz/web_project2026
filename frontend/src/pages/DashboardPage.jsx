import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [modules, setModules] = useState([])

  useEffect(() => {
    api.get('/dashboard/stats/').then((res) => setStats(res.data)).catch(() => setStats({}))
    api.get('/dashboard/modules/').then((res) => setModules(res.data.modules || [])).catch(() => setModules([]))
  }, [])

  if (!stats) return <div className="loading">Loading dashboard...</div>

  return (
    <div className="cards-grid">
      <article className="card"><h3>Resolved Cases</h3><p>{stats.resolved_cases ?? 0}</p></article>
      <article className="card"><h3>Employees</h3><p>{stats.employees ?? 0}</p></article>
      <article className="card"><h3>Active Cases</h3><p>{stats.active_cases ?? 0}</p></article>
      <article className="card"><h3>Total Cases</h3><p>{stats.total_cases ?? 0}</p></article>
      <article className="card" style={{ gridColumn: '1 / -1' }}>
        <h3>Modules For Your Role</h3>
        {modules.length === 0 ? (
          <p style={{ fontSize: 16, fontWeight: 500 }}>No modules</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {modules.map((m) => (
              <Link key={m.key} className="btn-link" to={m.path || '/dashboard'}>
                {m.title}
              </Link>
            ))}
          </div>
        )}
      </article>
    </div>
  )
}
