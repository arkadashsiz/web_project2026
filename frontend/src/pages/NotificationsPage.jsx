import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'

function toText(err, fallback) {
  const data = err?.response?.data
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (typeof data.detail === 'string') return data.detail
  return fallback
}

export default function NotificationsPage() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  const unreadCount = useMemo(() => rows.filter((n) => !n.is_read).length, [rows])

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get('/investigation/notifications/')
      setRows(res.data.results || [])
      setMessage('')
    } catch (err) {
      setMessage(toText(err, 'Failed to load notifications'))
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const markRead = async (id) => {
    setMessage('')
    try {
      await api.post(`/investigation/notifications/${id}/mark_read/`, {})
      setRows((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)))
    } catch (err) {
      setMessage(toText(err, 'Failed to mark notification as read'))
    }
  }

  const markAllRead = async () => {
    const unread = rows.filter((n) => !n.is_read)
    if (unread.length === 0) return
    setMessage('')
    try {
      await Promise.all(unread.map((n) => api.post(`/investigation/notifications/${n.id}/mark_read/`, {})))
      setRows((prev) => prev.map((n) => ({ ...n, is_read: true })))
    } catch (err) {
      setMessage(toText(err, 'Failed to mark all notifications as read'))
    }
  }

  return (
    <div className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <h3 style={{ margin: 0 }}>Notifications</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ color: '#546176' }}>Unread: {unreadCount}</span>
          <button type="button" onClick={load}>Refresh</button>
          <button type="button" onClick={markAllRead} disabled={unreadCount === 0}>Mark All Read</button>
        </div>
      </div>

      {message && <p className="error">{message}</p>}
      {loading && <div className="loading">Loading notifications...</div>}

      {!loading && (
        <ul className="list">
          {rows.map((n) => (
            <li key={n.id} style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, background: n.is_read ? '#fff' : '#eef4ff' }}>
              <div><strong>{n.message}</strong></div>
              <div style={{ color: '#546176', marginTop: 4 }}>
                Case: {n.case || '-'} | Time: {new Date(n.created_at).toLocaleString()}
              </div>
              {!n.is_read && (
                <button type="button" style={{ marginTop: 8 }} onClick={() => markRead(n.id)}>
                  Mark As Read
                </button>
              )}
            </li>
          ))}
          {rows.length === 0 && <li>No notifications.</li>}
        </ul>
      )}
    </div>
  )
}
