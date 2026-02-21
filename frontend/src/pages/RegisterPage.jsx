import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '', password: '', email: '', phone: '', national_id: '', first_name: '', last_name: '',
  })
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await register(form)
      navigate('/login')
    } catch (err) {
      const data = err?.response?.data
      if (!data) {
        setError('Registration failed: network or CORS issue.')
        return
      }
      if (typeof data === 'string') {
        setError(data)
        return
      }
      const first = Object.entries(data)[0]
      if (!first) {
        setError('Registration failed.')
        return
      }
      const [field, messages] = first
      const msg = Array.isArray(messages) ? messages[0] : messages
      setError(`${field}: ${msg}`)
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h2>Register</h2>
        {Object.keys(form).map((k) => (
          <input
            key={k}
            type={k === 'password' ? 'password' : 'text'}
            placeholder={k.replace('_', ' ')}
            value={form[k]}
            onChange={(e) => setForm({ ...form, [k]: e.target.value })}
          />
        ))}
        {error && <p className="error">{error}</p>}
        <button type="submit">Create Account</button>
      </form>
    </div>
  )
}
