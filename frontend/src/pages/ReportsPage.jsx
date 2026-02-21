import { useEffect, useState } from 'react'
import api from '../api/client'

export default function ReportsPage() {
  const [cases, setCases] = useState([])

  useEffect(() => {
    api.get('/cases/cases/').then((res) => setCases(res.data.results || []))
  }, [])

  return (
    <div className="panel">
      <h3>Case Reports</h3>
      <table className="table">
        <thead>
          <tr><th>ID</th><th>Title</th><th>Status</th><th>Severity</th><th>Created At</th></tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>{c.title}</td>
              <td>{c.status}</td>
              <td>{c.severity}</td>
              <td>{new Date(c.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
