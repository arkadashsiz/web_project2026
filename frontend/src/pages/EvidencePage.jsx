import { useState } from 'react'
import api from '../api/client'

export default function EvidencePage() {
  const [form, setForm] = useState({ case: '', title: '', description: '', transcript: '' })
  const [message, setMessage] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    await api.post('/evidence/witness/', form)
    setMessage('Witness evidence saved.')
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h3>Record Witness Evidence</h3>
      <input placeholder="Case ID" value={form.case} onChange={(e) => setForm({ ...form, case: e.target.value })} />
      <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
      <textarea placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      <textarea placeholder="Transcript" value={form.transcript} onChange={(e) => setForm({ ...form, transcript: e.target.value })} />
      <button type="submit">Save Evidence</button>
      {message && <p>{message}</p>}
    </form>
  )
}
