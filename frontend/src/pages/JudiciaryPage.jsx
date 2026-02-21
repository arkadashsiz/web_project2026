import { useEffect, useState } from 'react'
import api from '../api/client'

export default function JudiciaryPage() {
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    api.get('/judiciary/court-sessions/').then((res) => setSessions(res.data.results || []))
  }, [])

  return (
    <div className="panel">
      <h3>Court Sessions</h3>
      <table className="table">
        <thead>
          <tr><th>ID</th><th>Case</th><th>Verdict</th><th>Punishment</th></tr>
        </thead>
        <tbody>
          {sessions.map((s) => (
            <tr key={s.id}>
              <td>{s.id}</td>
              <td>{s.case}</td>
              <td>{s.verdict}</td>
              <td>{s.punishment_title || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
