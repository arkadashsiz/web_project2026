import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

function WantedPhoto({ url, name }) {
  const [broken, setBroken] = useState(false)
  if (!url || broken) {
    return (
      <div style={{ width: 84, height: 84, borderRadius: 8, border: '1px dashed #ced7e8', display: 'grid', placeItems: 'center', fontSize: 12, color: '#667', textAlign: 'center', padding: 6 }}>
        {url ? 'Photo Unavailable' : 'No Photo'}
      </div>
    )
  }
  return (
    <img
      src={url}
      alt={name}
      onError={() => setBroken(true)}
      style={{ width: 84, height: 84, objectFit: 'cover', borderRadius: 8, border: '1px solid #ced7e8' }}
    />
  )
}

export default function HighAlertPage() {
  const { user } = useAuth()
  const [list, setList] = useState([])
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({
    full_name: '',
    national_id: '',
    photo_url: '',
    severity: 2,
    days_wanted: 31,
    case_title: '',
    case_description: '',
  })

  const load = () => {
    api.get('/investigation/high-alert/')
      .then((res) => setList(res.data))
      .catch(() => setList([]))
  }

  useEffect(() => {
    load()
  }, [])

  const createWanted = async () => {
    setMessage('')
    const photo = (form.photo_url || '').trim()
    if (photo && !/^https?:\/\//i.test(photo)) {
      setMessage('Photo URL must start with http:// or https://')
      return
    }
    try {
      const res = await api.post('/investigation/suspects/create_wanted_profile/', {
        ...form,
        photo_url: photo,
        severity: Number(form.severity),
        days_wanted: Number(form.days_wanted),
      })
      setMessage(`Wanted profile created. Case #${res.data.case_id}, suspect #${res.data.suspect.id}`)
      setForm({
        full_name: '',
        national_id: '',
        photo_url: '',
        severity: 2,
        days_wanted: 31,
        case_title: '',
        case_description: '',
      })
      load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to create wanted profile')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {user?.is_superuser && (
        <div className="panel">
          <h3>Superuser: Create Wanted Person</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <input
              placeholder="Full name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
            <input
              placeholder="National ID"
              value={form.national_id}
              onChange={(e) => setForm({ ...form, national_id: e.target.value })}
            />
            <input
              placeholder="Photo URL"
              value={form.photo_url}
              onChange={(e) => setForm({ ...form, photo_url: e.target.value })}
            />
            <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              <option value={1}>Level 3 (1)</option>
              <option value={2}>Level 2 (2)</option>
              <option value={3}>Level 1 (3)</option>
              <option value={4}>Critical (4)</option>
            </select>
            <input
              type="number"
              min="0"
              placeholder="Days wanted"
              value={form.days_wanted}
              onChange={(e) => setForm({ ...form, days_wanted: e.target.value })}
            />
            <input
              placeholder="Case title (optional)"
              value={form.case_title}
              onChange={(e) => setForm({ ...form, case_title: e.target.value })}
            />
          </div>
          <textarea
            style={{ marginTop: 8 }}
            placeholder="Case description (optional)"
            value={form.case_description}
            onChange={(e) => setForm({ ...form, case_description: e.target.value })}
          />
          <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
            <button type="button" onClick={createWanted}>Create Wanted</button>
            <button type="button" onClick={load}>Refresh High Alert List</button>
          </div>
          <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '84px 1fr', gap: 10, alignItems: 'center' }}>
            <WantedPhoto url={form.photo_url} name={form.full_name || 'Preview'} />
            <div style={{ color: '#546176', fontSize: 13 }}>
              Photo preview. If this shows \"Photo Unavailable\", the URL is blocked/invalid/not public.
            </div>
          </div>
          {message && <p className="error" style={{ marginTop: 8 }}>{message}</p>}
        </div>
      )}

      <div className="panel">
        <h3>High Alert Suspects</h3>
        <div style={{ display: 'grid', gap: 10 }}>
        {list.map((x) => (
          <div key={x.group_key} style={{ border: '1px solid #d8deea', borderRadius: 10, padding: 10, background: '#fff' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '84px 1fr', gap: 10 }}>
              <div>
                <WantedPhoto url={x.photo_url} name={x.full_name} />
              </div>
              <div style={{ display: 'grid', gap: 4 }}>
                <strong>{x.full_name}</strong>
                <div>National ID: {x.national_id || '-'}</div>
                <div>Max Wanted Days (Lj): {x.max_lj_days}</div>
                <div>Max Severity (Di): {x.max_di}</div>
                <div>Rank Score (Lj × Di): {x.rank_score}</div>
                {x.photo_url && (
                  <div>
                    Photo URL:{' '}
                    <a href={x.photo_url} target="_blank" rel="noreferrer" style={{ color: '#0b5ed7' }}>
                      Open Image
                    </a>
                  </div>
                )}
              </div>
            </div>
            <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #eef2f9', fontWeight: 700, color: '#b00020' }}>
              Reward For Information: {Number(x.reward_irr || 0).toLocaleString()} IRR
            </div>
          </div>
        ))}
        {list.length === 0 && <p>No suspects in high alert list.</p>}
      </div>
      </div>
    </div>
  )
}
