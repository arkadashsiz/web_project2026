import { useEffect, useState } from 'react'
import api from '../api/client'

export default function HighAlertPage() {
  const [list, setList] = useState([])

  useEffect(() => {
    api.get('/investigation/high-alert/').then((res) => setList(res.data))
  }, [])

  return (
    <div className="panel">
      <h3>High Alert Suspects</h3>
      <ul className="list">
        {list.map((x) => (
          <li key={x.suspect_id}>
            {x.full_name} | Score: {x.rank_score} | Reward: {x.reward_irr.toLocaleString()} IRR
          </li>
        ))}
      </ul>
    </div>
  )
}
