import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'

export default function JudiciaryPage() {
  const [sessions, setSessions] = useState([])
  const [cases, setCases] = useState([])
  const [selectedCaseId, setSelectedCaseId] = useState('')
  const [summary, setSummary] = useState(null)
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({
    case: '',
    verdict: 'guilty',
    punishment_title: '',
    punishment_description: '',
  })

  const loadSessions = () => {
    api.get('/judiciary/court-sessions/')
      .then((res) => setSessions(res.data.results || []))
      .catch(() => setSessions([]))
  }

  const loadCases = () => {
    api.get('/cases/cases/')
      .then((res) => {
        const rows = res.data.results || []
        setCases(rows.filter((c) => ['sent_to_court', 'closed'].includes(c.status)))
      })
      .catch(() => setCases([]))
  }

  useEffect(() => {
    loadSessions()
    loadCases()
  }, [])

  const selectedCase = useMemo(
    () => cases.find((c) => String(c.id) === String(selectedCaseId)) || null,
    [cases, selectedCaseId]
  )

  const loadSummary = async () => {
    if (!selectedCaseId) {
      setMessage('Select a case first.')
      return
    }
    try {
      const res = await api.get(`/judiciary/court-sessions/case_summary/?case_id=${selectedCaseId}`)
      setSummary(res.data)
      setMessage('Case summary loaded for judge review.')
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to load case summary')
      setSummary(null)
    }
  }

  const submitVerdict = async () => {
    if (!form.case) {
      setMessage('Select case for verdict.')
      return
    }
    if (form.verdict === 'guilty' && !form.punishment_title.trim()) {
      setMessage('Punishment title is required for guilty verdict.')
      return
    }
    try {
      await api.post('/judiciary/court-sessions/', {
        case: Number(form.case),
        verdict: form.verdict,
        punishment_title: form.punishment_title,
        punishment_description: form.punishment_description,
      })
      setMessage('Final court verdict registered.')
      setForm({ case: '', verdict: 'guilty', punishment_title: '', punishment_description: '' })
      loadSessions()
      loadCases()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to register verdict')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {message && <p className="error">{message}</p>}

      <div className="panel">
        <h3>Judge Case Summary</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <select value={selectedCaseId} onChange={(e) => setSelectedCaseId(e.target.value)}>
            <option value="">Select case</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>Case #{c.id} - {c.title} ({c.status})</option>
            ))}
          </select>
          <button type="button" onClick={loadSummary}>Load Full Summary</button>
        </div>

        {summary && (
          <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
            <div><strong>Case:</strong> #{summary.case.id} {summary.case.title} | severity: {summary.case.severity} | status: {summary.case.status}</div>
            <div><strong>Description:</strong> {summary.case.description}</div>
            <div><strong>Involved Police/Actors:</strong> {summary.involved_members.length}</div>
            <ul className="list">
              {summary.involved_members.map((m) => (
                <li key={m.id}>#{m.id} {m.username} ({(m.roles || []).join(', ') || 'no-role'})</li>
              ))}
            </ul>

            <div><strong>Suspects:</strong> {(summary.suspects || []).length}</div>
            <ul className="list">
              {(summary.suspects || []).map((s) => (
                <li key={s.id}>#{s.id} {s.full_name} | status: {s.status} | national_id: {s.national_id || '-'}</li>
              ))}
            </ul>

            <div><strong>Interrogations:</strong> {(summary.interrogations || []).length}</div>
            <ul className="list">
              {(summary.interrogations || []).map((i) => (
                <li key={i.id}>
                  Interrogation #{i.id} | suspect #{i.suspect} | D:{i.detective_score}/10 S:{i.sergeant_score}/10 | captain: {i.captain_decision} | chief: {i.chief_decision}
                </li>
              ))}
            </ul>

            <div><strong>Evidence:</strong> witness {(summary.evidence?.witness || []).length}, biological {(summary.evidence?.biological || []).length}, vehicle {(summary.evidence?.vehicle || []).length}, identification {(summary.evidence?.identification || []).length}, other {(summary.evidence?.other || []).length}</div>

            <div><strong>Case Logs:</strong> {(summary.logs || []).length}</div>
            <ul className="list">
              {(summary.logs || []).slice(0, 20).map((log) => (
                <li key={log.id}>{log.action} | {log.details || '-'} | {new Date(log.created_at).toLocaleString()}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="panel">
        <h3>Register Final Verdict</h3>
        <div style={{ display: 'grid', gap: 8 }}>
          <select value={form.case} onChange={(e) => setForm({ ...form, case: e.target.value })}>
            <option value="">Select sent-to-court case</option>
            {cases.filter((c) => c.status === 'sent_to_court').map((c) => (
              <option key={c.id} value={c.id}>Case #{c.id} - {c.title}</option>
            ))}
          </select>
          <select value={form.verdict} onChange={(e) => setForm({ ...form, verdict: e.target.value })}>
            <option value="guilty">Guilty</option>
            <option value="not_guilty">Not Guilty</option>
          </select>
          <input
            placeholder="Punishment title"
            value={form.punishment_title}
            onChange={(e) => setForm({ ...form, punishment_title: e.target.value })}
          />
          <textarea
            placeholder="Punishment description"
            value={form.punishment_description}
            onChange={(e) => setForm({ ...form, punishment_description: e.target.value })}
          />
          <button type="button" onClick={submitVerdict}>Submit Court Verdict</button>
        </div>
      </div>

      <div className="panel">
        <h3>Court Sessions</h3>
        <table className="table">
          <thead>
            <tr><th>ID</th><th>Case</th><th>Verdict</th><th>Punishment</th><th>Created</th></tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.case}</td>
                <td>{s.verdict}</td>
                <td>{s.punishment_title || '-'}</td>
                <td>{new Date(s.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {sessions.length === 0 && (
              <tr><td colSpan="5">No court sessions yet.</td></tr>
            )}
          </tbody>
        </table>
        {selectedCase && <p style={{ marginTop: 8 }}>Selected case: #{selectedCase.id} {selectedCase.title}</p>}
      </div>
    </div>
  )
}
