import { useEffect, useState } from 'react'
import api from '../api/client'

export default function CasesPage() {
  const [cases, setCases] = useState([])
  const [mode, setMode] = useState('complaint')
  const [error, setError] = useState('')
  const [complaintForm, setComplaintForm] = useState({ title: '', description: '', severity: 1 })
  const [sceneForm, setSceneForm] = useState({
    title: '',
    description: '',
    severity: 2,
    witnesses: [{ full_name: '', national_id: '', phone: '', statement: '' }],
  })

  const load = () => api.get('/cases/cases/').then((res) => setCases(res.data.results || []))
  useEffect(() => { load() }, [])

  const createComplaint = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/cases/cases/submit_complaint/', complaintForm)
      setComplaintForm({ title: '', description: '', severity: 1 })
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit complaint case.')
    }
  }

  const createSceneReport = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/cases/cases/submit_scene_report/', sceneForm)
      setSceneForm({
        title: '',
        description: '',
        severity: 2,
        witnesses: [{ full_name: '', national_id: '', phone: '', statement: '' }],
      })
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit scene report.')
    }
  }

  const updateWitness = (idx, key, value) => {
    const witnesses = [...sceneForm.witnesses]
    witnesses[idx] = { ...witnesses[idx], [key]: value }
    setSceneForm({ ...sceneForm, witnesses })
  }

  const addWitness = () => {
    setSceneForm({
      ...sceneForm,
      witnesses: [...sceneForm.witnesses, { full_name: '', national_id: '', phone: '', statement: '' }],
    })
  }

  return (
    <div className="two-col">
      <div className="panel">
        <h3>Create Case</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className={mode === 'complaint' ? '' : 'btn-link secondary'} onClick={() => setMode('complaint')}>
            From Complaint
          </button>
          <button type="button" className={mode === 'scene' ? '' : 'btn-link secondary'} onClick={() => setMode('scene')}>
            From Crime Scene
          </button>
        </div>
        {mode === 'complaint' ? (
          <form onSubmit={createComplaint} style={{ display: 'grid', gap: 10 }}>
            <input placeholder="Case title" value={complaintForm.title} onChange={(e) => setComplaintForm({ ...complaintForm, title: e.target.value })} />
            <textarea placeholder="Description" value={complaintForm.description} onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })} />
            <select value={complaintForm.severity} onChange={(e) => setComplaintForm({ ...complaintForm, severity: Number(e.target.value) })}>
              <option value={1}>Level 3</option>
              <option value={2}>Level 2</option>
              <option value={3}>Level 1</option>
              <option value={4}>Critical</option>
            </select>
            <button type="submit">Submit Complaint Case</button>
          </form>
        ) : (
          <form onSubmit={createSceneReport} style={{ display: 'grid', gap: 10 }}>
            <input placeholder="Case title" value={sceneForm.title} onChange={(e) => setSceneForm({ ...sceneForm, title: e.target.value })} />
            <textarea placeholder="Scene description" value={sceneForm.description} onChange={(e) => setSceneForm({ ...sceneForm, description: e.target.value })} />
            <select value={sceneForm.severity} onChange={(e) => setSceneForm({ ...sceneForm, severity: Number(e.target.value) })}>
              <option value={1}>Level 3</option>
              <option value={2}>Level 2</option>
              <option value={3}>Level 1</option>
              <option value={4}>Critical</option>
            </select>
            <h4>Witnesses</h4>
            {sceneForm.witnesses.map((w, idx) => (
              <div key={idx} style={{ border: '1px solid #d8deea', padding: 10, borderRadius: 8, display: 'grid', gap: 8 }}>
                <input placeholder="Full name" value={w.full_name} onChange={(e) => updateWitness(idx, 'full_name', e.target.value)} />
                <input placeholder="National ID" value={w.national_id} onChange={(e) => updateWitness(idx, 'national_id', e.target.value)} />
                <input placeholder="Phone" value={w.phone} onChange={(e) => updateWitness(idx, 'phone', e.target.value)} />
                <textarea placeholder="Statement" value={w.statement} onChange={(e) => updateWitness(idx, 'statement', e.target.value)} />
              </div>
            ))}
            <button type="button" onClick={addWitness}>Add Another Witness</button>
            <button type="submit">Submit Scene Case</button>
          </form>
        )}
        {error && <p className="error">{error}</p>}
      </div>
      <div className="panel">
        <h3>Case List</h3>
        <ul className="list">
          {cases.map((c) => <li key={c.id}>#{c.id} {c.title} - {c.status}</li>)}
        </ul>
      </div>
    </div>
  )
}
