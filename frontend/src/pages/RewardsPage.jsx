import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function RewardsPage() {
  const { user } = useAuth()
  const roleNames = useMemo(() => (user?.roles || []).map((r) => (r || '').toLowerCase()), [user])
  const isOfficer = user?.is_superuser || roleNames.includes('police officer')
  const isDetective = user?.is_superuser || roleNames.includes('detective')
  const isPoliceRank = user?.is_superuser || roleNames.some((r) => ['chief', 'captain', 'sergeant', 'detective', 'police officer', 'patrol officer', 'cadet', 'administrator'].includes(r))

  const [tips, setTips] = useState([])
  const [cases, setCases] = useState([])
  const [suspects, setSuspects] = useState([])
  const [message, setMessage] = useState('')

  const [submitForm, setSubmitForm] = useState({
    case: '',
    suspect: '',
    content: '',
  })

  const [officerForm, setOfficerForm] = useState({})
  const [detectiveForm, setDetectiveForm] = useState({})
  const [verifyForm, setVerifyForm] = useState({ national_id: '', unique_code: '' })
  const [verifyResult, setVerifyResult] = useState(null)

  const load = async () => {
    const [tipsRes, casesRes, suspectsRes] = await Promise.all([
      api.get('/rewards/tips/'),
      api.get('/cases/cases/'),
      api.get('/investigation/suspects/'),
    ])
    setTips(tipsRes.data.results || [])
    setCases(casesRes.data.results || [])
    setSuspects(suspectsRes.data.results || [])
  }

  useEffect(() => {
    load().catch(() => setMessage('Failed to load rewards data'))
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      await api.post('/rewards/tips/', {
        case: submitForm.case ? Number(submitForm.case) : null,
        suspect: submitForm.suspect ? Number(submitForm.suspect) : null,
        content: submitForm.content,
      })
      setSubmitForm({ case: '', suspect: '', content: '' })
      setMessage('Tip submitted.')
      await load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to submit tip')
    }
  }

  const officerReview = async (tipId, valid) => {
    setMessage('')
    try {
      await api.post(`/rewards/tips/${tipId}/officer_review/`, {
        valid,
        note: officerForm[tipId]?.note || '',
        detective_id: officerForm[tipId]?.detective_id ? Number(officerForm[tipId]?.detective_id) : undefined,
      })
      setMessage(valid ? 'Tip sent to responsible detective.' : 'Tip rejected by officer.')
      await load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Officer review failed')
    }
  }

  const detectiveReview = async (tipId, useful) => {
    setMessage('')
    try {
      await api.post(`/rewards/tips/${tipId}/detective_review/`, {
        useful,
        amount: Number(detectiveForm[tipId]?.amount || 50000000),
        note: detectiveForm[tipId]?.note || '',
      })
      setMessage(useful ? 'Tip approved and reward code generated.' : 'Tip rejected by detective.')
      await load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Detective review failed')
    }
  }

  const verifyReward = async (e) => {
    e.preventDefault()
    setMessage('')
    setVerifyResult(null)
    try {
      const res = await api.post('/rewards/reward-claims/verify/', verifyForm)
      setVerifyResult(res.data)
      setMessage('Reward claim verified successfully.')
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Verification failed')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {message && <p className="error">{message}</p>}

      <form className="panel" onSubmit={submit}>
        <h3>Submit Tip (Public User)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <select value={submitForm.case} onChange={(e) => setSubmitForm({ ...submitForm, case: e.target.value })}>
            <option value="">Case (optional)</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>#{c.id} {c.title}</option>
            ))}
          </select>
          <select value={submitForm.suspect} onChange={(e) => setSubmitForm({ ...submitForm, suspect: e.target.value })}>
            <option value="">Suspect (optional)</option>
            {suspects.map((s) => (
              <option key={s.id} value={s.id}>#{s.id} {s.full_name}</option>
            ))}
          </select>
        </div>
        <textarea
          placeholder="Describe your information"
          value={submitForm.content}
          onChange={(e) => setSubmitForm({ ...submitForm, content: e.target.value })}
        />
        <button type="submit">Send Tip</button>
      </form>

      <div className="panel">
        <h3>Tips Workflow</h3>
        <ul className="list">
          {tips.map((t) => (
            <li key={t.id}>
              <div>
                Tip #{t.id} | status: {t.status} | case: {t.case || '-'} | suspect: {t.suspect || '-'}
              </div>
              <div>Content: {t.content}</div>
              <div>Officer note: {t.officer_note || '-'}</div>
              <div>Detective note: {t.detective_note || '-'}</div>
              {t.claim?.unique_code && (
                <div style={{ color: '#0a5' }}>
                  Reward Code: {t.claim.unique_code} | Amount: {Number(t.claim.amount || 0).toLocaleString()} IRR
                </div>
              )}

              {isOfficer && t.status === 'pending' && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                  <input
                    placeholder="Officer review note"
                    value={officerForm[t.id]?.note || ''}
                    onChange={(e) => setOfficerForm((prev) => ({ ...prev, [t.id]: { ...(prev[t.id] || {}), note: e.target.value } }))}
                  />
                  <input
                    type="number"
                    placeholder="Detective ID (optional)"
                    value={officerForm[t.id]?.detective_id || ''}
                    onChange={(e) => setOfficerForm((prev) => ({ ...prev, [t.id]: { ...(prev[t.id] || {}), detective_id: e.target.value } }))}
                  />
                  <button type="button" onClick={() => officerReview(t.id, true)}>Send To Detective</button>
                  <button type="button" onClick={() => officerReview(t.id, false)}>Reject</button>
                </div>
              )}

              {isDetective && t.status === 'sent_to_detective' && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                  <input
                    placeholder="Detective note"
                    value={detectiveForm[t.id]?.note || ''}
                    onChange={(e) => setDetectiveForm((prev) => ({ ...prev, [t.id]: { ...(prev[t.id] || {}), note: e.target.value } }))}
                  />
                  <input
                    type="number"
                    placeholder="Reward amount"
                    value={detectiveForm[t.id]?.amount || ''}
                    onChange={(e) => setDetectiveForm((prev) => ({ ...prev, [t.id]: { ...(prev[t.id] || {}), amount: e.target.value } }))}
                  />
                  <button type="button" onClick={() => detectiveReview(t.id, true)}>Approve Useful</button>
                  <button type="button" onClick={() => detectiveReview(t.id, false)}>Reject</button>
                </div>
              )}
            </li>
          ))}
          {tips.length === 0 && <li>No tips found.</li>}
        </ul>
      </div>

      {isPoliceRank && (
        <form className="panel" onSubmit={verifyReward}>
          <h3>Police Verification (National ID + Unique Code)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8 }}>
            <input
              placeholder="National ID"
              value={verifyForm.national_id}
              onChange={(e) => setVerifyForm({ ...verifyForm, national_id: e.target.value })}
            />
            <input
              placeholder="Unique reward code"
              value={verifyForm.unique_code}
              onChange={(e) => setVerifyForm({ ...verifyForm, unique_code: e.target.value })}
            />
            <button type="submit">Verify</button>
          </div>
          {verifyResult && (
            <div style={{ marginTop: 8 }}>
              <div>Amount: {Number(verifyResult.amount || 0).toLocaleString()} IRR</div>
              <div>Submitter: {verifyResult.submitter?.username} | national_id: {verifyResult.submitter?.national_id}</div>
              <div>Phone: {verifyResult.submitter?.phone} | Email: {verifyResult.submitter?.email}</div>
            </div>
          )}
        </form>
      )}
    </div>
  )
}
