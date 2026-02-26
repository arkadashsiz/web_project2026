import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

function extractApiError(err, fallback) {
  const data = err?.response?.data
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (typeof data.detail === 'string') return data.detail
  const parts = []
  Object.entries(data).forEach(([key, value]) => {
    if (Array.isArray(value)) parts.push(`${key}: ${value.join(', ')}`)
    else if (typeof value === 'string') parts.push(`${key}: ${value}`)
    else parts.push(`${key}: ${JSON.stringify(value)}`)
  })
  return parts.length ? parts.join(' | ') : fallback
}

export default function PaymentsPage() {
  const { user } = useAuth()
  const roleNames = useMemo(() => (user?.roles || []).map((r) => (r || '').toLowerCase()), [user])
  const isSergeant = user?.is_superuser || roleNames.includes('sergeant') || roleNames.includes('sergent') || roleNames.includes('sargent')
  const canStartPayment = !isSergeant
  const canSimulateSuccess = !!user?.is_superuser

  const [rows, setRows] = useState([])
  const [cases, setCases] = useState([])
  const [suspects, setSuspects] = useState([])
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({
    case: '',
    suspect: '',
    amount: '',
  })
  const selectedCaseId = Number(form.case || 0)
  const selectedCase = useMemo(
    () => cases.find((c) => Number(c.id) === selectedCaseId) || null,
    [cases, selectedCaseId],
  )
  const filteredSuspects = useMemo(() => {
    if (!selectedCaseId || !selectedCase) return []
    const severity = Number(selectedCase.severity)
    return suspects.filter((s) => {
      if (Number(s.case) !== selectedCaseId) return false
      const status = String(s.status || '').toLowerCase()
      // Project rules:
      // - arrested suspects: only level 2/3 cases (severity 2 or 1)
      // - criminals: only level 3 cases (severity 1) + sergeant approval at submit
      if (status === 'arrested') return severity === 1 || severity === 2
      if (status === 'criminal') return severity === 1
      return false
    })
  }, [suspects, selectedCaseId, selectedCase])

  const load = async () => {
    const reqs = [api.get('/payments/bail/')]
    if (isSergeant) {
      reqs.push(api.get('/payments/bail/create_options/'))
    }
    const [r1, r2] = await Promise.all(reqs)
    setRows(r1.data.results || [])
    if (isSergeant) {
      setCases(r2?.data?.cases || [])
      setSuspects(r2?.data?.suspects || [])
    }
  }

  useEffect(() => {
    load().catch((err) => setMessage(err?.response?.data?.detail || 'Failed to load payment data'))
  }, [isSergeant])

  const createPayment = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      await api.post('/payments/bail/', {
        case: Number(form.case),
        suspect: Number(form.suspect),
        amount: Number(form.amount),
        sergeant_approved: true,
      })
      setMessage('Payment record created.')
      setForm({ case: '', suspect: '', amount: '' })
      await load()
    } catch (err) {
      setMessage(extractApiError(err, 'Failed to create payment'))
    }
  }

  const startGateway = async (id) => {
    setMessage('')
    try {
      const res = await api.post(`/payments/bail/${id}/start_gateway/`, {})
      const url = res.data.start_pay_url
      setMessage(`Gateway started. Redirecting to: ${url}`)
      window.open(url, '_blank')
      await load()
    } catch (err) {
      setMessage(extractApiError(err, 'Failed to start gateway payment'))
    }
  }

  const simulateSuccess = async (id) => {
    setMessage('')
    try {
      await api.post(`/payments/bail/${id}/callback/`, { status: 'success', payment_ref: `DEV-${id}` })
      setMessage('Simulated success callback done.')
      await load()
    } catch (err) {
      setMessage(extractApiError(err, 'Simulation failed'))
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {message && <p className="error">{message}</p>}

      {isSergeant && (
        <form className="panel" onSubmit={createPayment}>
          <h3>Create Bail/Fine Payment (Sergeant)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8 }}>
            <select
              value={form.case}
              onChange={(e) => {
                const nextCase = e.target.value
                setForm((prev) => ({ ...prev, case: nextCase, suspect: '' }))
              }}
            >
              <option value="">Select case</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>#{c.id} {c.title} ({c.severity})</option>
              ))}
            </select>
            <select
              value={form.suspect}
              disabled={!form.case}
              onChange={(e) => setForm({ ...form, suspect: e.target.value })}
            >
              <option value="">{form.case ? 'Select suspect' : 'Select case first'}</option>
              {filteredSuspects.map((s) => (
                <option key={s.id} value={s.id}>#{s.id} {s.full_name} ({s.status})</option>
              ))}
            </select>
            <input
              type="number"
              min="1000"
              required
              placeholder="Amount"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
            />
            <div />
          </div>
          {form.case && filteredSuspects.length === 0 && (
            <p className="error" style={{ marginTop: 8 }}>
              No eligible suspects for this case based on payment rules.
            </p>
          )}
          <button type="submit" style={{ marginTop: 8 }}>Create Payment</button>
        </form>
      )}

      <div className="panel">
        <h3>Bail & Fine Payments</h3>
        <ul className="list">
          {rows.map((r) => (
            <li key={r.id}>
              <div>Payment #{r.id} | Case {r.case} | Suspect {r.suspect} | Amount {Number(r.amount || 0).toLocaleString()} | {r.status}</div>
              <div>Authority: {r.authority || '-'} | Ref: {r.payment_ref || '-'} | Sergeant approved: {r.sergeant_approved ? 'yes' : 'no'}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                {canStartPayment && r.status === 'initiated' && <button type="button" onClick={() => startGateway(r.id)}>Start Gateway Payment</button>}
                {canSimulateSuccess && r.status === 'initiated' && <button type="button" onClick={() => simulateSuccess(r.id)}>Simulate Success (Dev)</button>}
              </div>
            </li>
          ))}
          {rows.length === 0 && <li>No payment records.</li>}
        </ul>
      </div>
    </div>
  )
}
