import { useEffect, useState } from 'react'
import api from '../api/client'

export default function PaymentsPage() {
  const [rows, setRows] = useState([])

  useEffect(() => {
    api.get('/payments/bail/').then((res) => setRows(res.data.results || []))
  }, [])

  return (
    <div className="panel">
      <h3>Bail & Fine Payments</h3>
      <ul className="list">
        {rows.map((r) => (
          <li key={r.id}>Payment #{r.id} | Case {r.case} | Amount {r.amount} | {r.status}</li>
        ))}
      </ul>
    </div>
  )
}
