import { useEffect, useState } from 'react'
import api from '../api/client'

export default function AdminRBACPage() {
  const [roles, setRoles] = useState([])
  const [users, setUsers] = useState([])
  const [userRoles, setUserRoles] = useState([])
  const [name, setName] = useState('')
  const [assignment, setAssignment] = useState({ user: '', role: '' })
  const [msg, setMsg] = useState('')

  const load = async () => {
    const [rolesRes, usersRes, userRolesRes] = await Promise.all([
      api.get('/rbac/roles/'),
      api.get('/auth/users/'),
      api.get('/rbac/user-roles/'),
    ])
    setRoles(rolesRes.data.results || [])
    setUsers(usersRes.data.results || [])
    setUserRoles(userRolesRes.data.results || [])
  }
  useEffect(() => { load() }, [])

  const add = async (e) => {
    e.preventDefault()
    await api.post('/rbac/roles/', { name, description: 'Custom role', permissions: [] })
    setName('')
    load()
  }

  const assignRole = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      await api.post('/rbac/user-roles/', { user: Number(assignment.user), role: Number(assignment.role) })
      setAssignment({ user: '', role: '' })
      setMsg('Role assigned successfully.')
      load()
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Failed to assign role.')
    }
  }

  const deleteRole = async (roleId, roleName) => {
    setMsg('')
    const ok = window.confirm(`Delete role "${roleName}" for all users?`)
    if (!ok) return
    try {
      const res = await api.delete(`/rbac/roles/${roleId}/`)
      const removed = res?.data?.removed_user_roles ?? 0
      setMsg(`Role "${roleName}" deleted. Removed from ${removed} user assignment(s).`)
      await load()
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Failed to delete role.')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <div className="two-col">
        <form className="panel" onSubmit={add}>
          <h3>Create Role</h3>
          <input placeholder="Role name" value={name} onChange={(e) => setName(e.target.value)} />
          <button type="submit">Add Role</button>
        </form>
        <form className="panel" onSubmit={assignRole}>
          <h3>Assign Role To User</h3>
          <select value={assignment.user} onChange={(e) => setAssignment({ ...assignment, user: e.target.value })}>
            <option value="">Select user</option>
            {users.map((u) => <option key={u.id} value={u.id}>{u.username} ({u.national_id})</option>)}
          </select>
          <select value={assignment.role} onChange={(e) => setAssignment({ ...assignment, role: e.target.value })}>
            <option value="">Select role</option>
            {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
          <button type="submit">Assign</button>
          {msg && <p>{msg}</p>}
        </form>
      </div>
      <div className="two-col">
        <div className="panel">
          <h3>Role List</h3>
          <ul className="list">
            {roles.map((r) => (
              <li key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <span>{r.name}</span>
                <button type="button" onClick={() => deleteRole(r.id, r.name)}>Delete Role</button>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3>User Role Assignments</h3>
          <ul className="list">
            {userRoles.map((ur) => <li key={ur.id}>{ur.username} → {ur.role_name}</li>)}
          </ul>
        </div>
      </div>
    </div>
  )
}
