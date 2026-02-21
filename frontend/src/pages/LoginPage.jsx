import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ identifier: '', password: '' })
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await login(form.identifier, form.password)
      navigate('/dashboard')
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Login failed. Check your credentials or server connection.')
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h2>Login</h2>
        <input placeholder="Username / Email / Phone / National ID" value={form.identifier} onChange={(e) => setForm({ ...form, identifier: e.target.value })} />
        <input type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  )
}
