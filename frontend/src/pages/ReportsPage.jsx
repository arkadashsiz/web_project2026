import { useEffect, useState } from 'react'
import api from '../api/client'

export default function ReportsPage() {
  const [cases, setCases] = useState([])
  const [selectedCaseId, setSelectedCaseId] = useState('')
  const [report, setReport] = useState(null)
  const [message, setMessage] = useState('')

  const loadCases = async () => {
    const res = await api.get('/cases/cases/')
    setCases(res.data.results || [])
  }

  useEffect(() => {
    loadCases().catch(() => setMessage('Failed to load cases'))
  }, [])

  const loadReport = async () => {
    setMessage('')
    setReport(null)
    if (!selectedCaseId) {
      setMessage('Select a case first.')
      return
    }
    try {
      const res = await api.get(`/cases/cases/${selectedCaseId}/global_report/`)
      setReport(res.data)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to load global report')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {message && <p className="error">{message}</p>}

      <div className="panel">
        <h3>Global Case Report</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <select value={selectedCaseId} onChange={(e) => setSelectedCaseId(e.target.value)}>
            <option value="">Select case</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>#{c.id} {c.title} ({c.status})</option>
            ))}
          </select>
          <button type="button" onClick={loadReport}>Load Report</button>
        </div>
      </div>

      {report && (
        <div className="panel" style={{ display: 'grid', gap: 10 }}>
          <h3>Case #{report.case.id}: {report.case.title}</h3>
          <div>Formed at: {new Date(report.formed_at || report.case.created_at).toLocaleString()}</div>
          <div>Status: {report.case.status} | Severity: {report.case.severity} | Source: {report.case.source}</div>

          <div>
            <h4>Complainants</h4>
            <ul className="list">
              {(report.complainants || []).map((c) => (
                <li key={c.id}>
                  {c.user?.first_name} {c.user?.last_name} ({c.user?.username}) | roles: {(c.user?.roles || []).join(', ') || '-'} | status: {c.status}
                </li>
              ))}
              {(report.complainants || []).length === 0 && <li>No complainants.</li>}
            </ul>
          </div>

          <div>
            <h4>Witness Statements</h4>
            <ul className="list">
              {(report.witness_statements || []).map((w) => (
                <li key={w.id}>#{w.id} {w.full_name} | {w.national_id} | {w.phone} {w.statement ? `| ${w.statement}` : ''}</li>
              ))}
              {(report.witness_statements || []).length === 0 && <li>No witness statements.</li>}
            </ul>
          </div>

          <div>
            <h4>Evidence</h4>
            <div>
              witness: {(report.evidence?.witness || []).length}, biological: {(report.evidence?.biological || []).length}, vehicle: {(report.evidence?.vehicle || []).length}, identification: {(report.evidence?.identification || []).length}, other: {(report.evidence?.other || []).length}
            </div>
          </div>

          <div>
            <h4>Suspects</h4>
            <ul className="list">
              {(report.suspects || []).map((s) => (
                <li key={s.id}>#{s.id} {s.full_name} | status: {s.status} | national_id: {s.national_id || '-'}</li>
              ))}
              {(report.suspects || []).length === 0 && <li>No suspects.</li>}
            </ul>
          </div>

          <div>
            <h4>Criminals</h4>
            <ul className="list">
              {(report.criminals || []).map((s) => (
                <li key={s.id}>#{s.id} {s.full_name} | national_id: {s.national_id || '-'}</li>
              ))}
              {(report.criminals || []).length === 0 && <li>No criminal marked yet.</li>}
            </ul>
          </div>

          <div>
            <h4>Involved Members (Name + Rank/Role)</h4>
            <ul className="list">
              {(report.involved_members || []).map((m) => (
                <li key={m.id}>#{m.id} {m.first_name} {m.last_name} ({m.username}) | roles: {(m.roles || []).join(', ') || '-'}</li>
              ))}
            </ul>
          </div>

          <div>
            <h4>Approval/Rejection Logs</h4>
            <ul className="list">
              {(report.logs || []).map((l) => (
                <li key={l.id}>{l.action} | {l.details || '-'} | {new Date(l.created_at).toLocaleString()}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
