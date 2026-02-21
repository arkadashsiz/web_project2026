import { useEffect, useState } from 'react'
import api from '../api/client'

export default function RewardsPage() {
  const [tips, setTips] = useState([])
  const [content, setContent] = useState('')

  const load = () => api.get('/rewards/tips/').then((res) => setTips(res.data.results || []))

  useEffect(() => { load() }, [])

  const submit = async (e) => {
    e.preventDefault()
    await api.post('/rewards/tips/', { content })
    setContent('')
    load()
  }

  return (
    <div className="two-col">
      <form className="panel" onSubmit={submit}>
        <h3>Submit Public Tip</h3>
        <textarea placeholder="Describe your information" value={content} onChange={(e) => setContent(e.target.value)} />
        <button type="submit">Send Tip</button>
      </form>
      <div className="panel">
        <h3>Tips Status</h3>
        <ul className="list">
          {tips.map((t) => <li key={t.id}>Tip #{t.id} - {t.status}</li>)}
        </ul>
      </div>
    </div>
  )
}
