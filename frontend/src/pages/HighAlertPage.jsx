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
      <div style={{ display: 'grid', gap: 10 }}>
        {list.map((x) => (
          <div key={x.group_key} style={{ border: '1px solid #d8deea', borderRadius: 10, padding: 10, background: '#fff' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '84px 1fr', gap: 10 }}>
              <div>
                {x.photo_url ? (
                  <img
                    src={x.photo_url}
                    alt={x.full_name}
                    style={{ width: 84, height: 84, objectFit: 'cover', borderRadius: 8, border: '1px solid #ced7e8' }}
                  />
                ) : (
                  <div style={{ width: 84, height: 84, borderRadius: 8, border: '1px dashed #ced7e8', display: 'grid', placeItems: 'center', fontSize: 12, color: '#667' }}>
                    No Photo
                  </div>
                )}
              </div>
              <div style={{ display: 'grid', gap: 4 }}>
                <strong>{x.full_name}</strong>
                <div>National ID: {x.national_id || '-'}</div>
                <div>Max Wanted Days (Lj): {x.max_lj_days}</div>
                <div>Max Severity (Di): {x.max_di}</div>
                <div>Rank Score (Lj × Di): {x.rank_score}</div>
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
  )
}
