import { useEffect, useMemo, useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function BoardPage() {
  const { user } = useAuth()
  const [openCases, setOpenCases] = useState([])
  const [assignedCases, setAssignedCases] = useState([])
  const [context, setContext] = useState(null)
  const [message, setMessage] = useState('')

  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [selectedNodeIds, setSelectedNodeIds] = useState([])
  const [edgeReason, setEdgeReason] = useState('')
  const [newNote, setNewNote] = useState('')
  const [suspectForm, setSuspectForm] = useState({
    full_name: '',
    national_id: '',
    photo_url: '',
  })

  const boardRef = useRef(null)
  const dragState = useRef({ nodeId: null, offsetX: 0, offsetY: 0 })

  const nodeMap = useMemo(() => {
    const map = new Map()
    for (const n of nodes) map.set(n.id, n)
    return map
  }, [nodes])

  const loadCases = () => {
    api.get('/cases/cases/').then((res) => {
      const rows = res.data.results || []
      setOpenCases(rows.filter((c) => c.status === 'open' && !c.assigned_detective))
      setAssignedCases(rows.filter((c) => c.assigned_detective === user?.id))
    })
  }

  useEffect(() => {
    loadCases()
  }, [user?.id])

  const openBoard = async (caseId) => {
    setMessage('')
    try {
      const res = await api.post('/investigation/boards/open_case_board/', { case_id: caseId })
      setContext(res.data)
      setNodes(res.data.board.nodes || [])
      setEdges(res.data.board.edges || [])
      setSelectedNodeIds([])
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to open board')
    }
  }

  const takeCase = async (caseId) => {
    setMessage('')
    try {
      await api.post(`/cases/cases/${caseId}/detective_take_case/`, {})
      setMessage(`Case #${caseId} assigned to you.`)
      loadCases()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to take case')
    }
  }

  const onNodeMouseDown = (e, node) => {
    if (!boardRef.current) return
    const rect = boardRef.current.getBoundingClientRect()
    dragState.current = {
      nodeId: node.id,
      offsetX: e.clientX - rect.left - node.x,
      offsetY: e.clientY - rect.top - node.y,
    }

    const onMove = (mv) => {
      if (!dragState.current.nodeId || !boardRef.current) return
      const r = boardRef.current.getBoundingClientRect()
      const x = Math.max(0, mv.clientX - r.left - dragState.current.offsetX)
      const y = Math.max(0, mv.clientY - r.top - dragState.current.offsetY)

      setNodes((prev) => prev.map((n) => (n.id === dragState.current.nodeId ? { ...n, x, y } : n)))
    }

    const onUp = async () => {
      const moved = nodes.find((n) => n.id === dragState.current.nodeId)
      if (moved) {
        try {
          await api.patch(`/investigation/board-nodes/${moved.id}/`, { x: moved.x, y: moved.y })
        } catch {
          // keep local position even if save fails
        }
      }
      dragState.current = { nodeId: null, offsetX: 0, offsetY: 0 }
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  const toggleNodeSelection = (id) => {
    setSelectedNodeIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length === 2) return [prev[1], id]
      return [...prev, id]
    })
  }

  const createEdge = async () => {
    if (!context || selectedNodeIds.length !== 2) {
      setMessage('Select exactly two nodes to connect.')
      return
    }
    try {
      const res = await api.post('/investigation/board-edges/', {
        board: context.board.id,
        from_node: selectedNodeIds[0],
        to_node: selectedNodeIds[1],
        reason: edgeReason,
      })
      setEdges((prev) => [...prev, res.data])
      setEdgeReason('')
      setSelectedNodeIds([])
      setMessage('Red line added between selected cards.')
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to add connection')
    }
  }

  const removeSelectedEdge = async () => {
    if (selectedNodeIds.length !== 2) {
      setMessage('Select exactly two nodes to remove their connection.')
      return
    }
    const [a, b] = selectedNodeIds
    const edge = edges.find(
      (e) => (e.from_node === a && e.to_node === b) || (e.from_node === b && e.to_node === a)
    )
    if (!edge) {
      setMessage('No line exists between selected cards.')
      return
    }
    await deleteEdge(edge.id)
    setSelectedNodeIds([])
    setMessage('Connection removed.')
  }

  const deleteEdge = async (edgeId) => {
    try {
      await api.delete(`/investigation/board-edges/${edgeId}/`)
      setEdges((prev) => prev.filter((e) => e.id !== edgeId))
    } catch {
      setMessage('Failed to remove edge')
    }
  }

  const deleteSelectedNode = async () => {
    if (selectedNodeIds.length !== 1) {
      setMessage('Select exactly one card to delete.')
      return
    }
    const nodeId = selectedNodeIds[0]
    const node = nodes.find((n) => n.id === nodeId)
    if (!node) return
    try {
      await api.delete(`/investigation/board-nodes/${nodeId}/`)
      setNodes((prev) => prev.filter((n) => n.id !== nodeId))
      setEdges((prev) => prev.filter((e) => e.from_node !== nodeId && e.to_node !== nodeId))
      setSelectedNodeIds([])
      setMessage('Card deleted from board.')
    } catch {
      setMessage('Failed to delete selected card.')
    }
  }

  const addNoteNode = async () => {
    if (!context || !newNote.trim()) return
    try {
      const res = await api.post('/investigation/board-nodes/', {
        board: context.board.id,
        label: newNote,
        kind: 'note',
        x: 50,
        y: 50,
      })
      setNodes((prev) => [...prev, res.data])
      setNewNote('')
    } catch {
      setMessage('Failed to add note card')
    }
  }

  const exportBoardAsImage = async () => {
    if (!boardRef.current) return
    const canvas = await html2canvas(boardRef.current, { backgroundColor: '#f6f8fc' })
    const url = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = url
    a.download = `detective-board-case-${context?.case?.id || 'x'}.png`
    a.click()
  }

  const addSuspect = async () => {
    if (!context || !suspectForm.full_name.trim()) {
      setMessage('Suspect full name is required.')
      return
    }
    try {
      const created = await api.post('/investigation/suspects/', {
        case: context.case.id,
        full_name: suspectForm.full_name,
        national_id: suspectForm.national_id,
        photo_url: suspectForm.photo_url,
      })

      const node = await api.post('/investigation/board-nodes/', {
        board: context.board.id,
        label: `Suspect: ${created.data.full_name}`,
        kind: 'suspect',
        reference_id: created.data.id,
        x: 120,
        y: 120,
      })

      setNodes((prev) => [...prev, node.data])
      setSuspectForm({ full_name: '', national_id: '', photo_url: '' })
      setMessage(`Suspect "${created.data.full_name}" added to case and board.`)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to add suspect')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <div className="panel">
        <h3>Open Cases From Case Management</h3>
        <ul className="list">
          {openCases.map((c) => (
            <li key={c.id}>
              Case #{c.id} - {c.title} - {c.status}
              <button type="button" style={{ marginLeft: 8 }} onClick={() => takeCase(c.id)}>Take Case</button>
            </li>
          ))}
          {openCases.length === 0 && <li>No open unassigned cases.</li>}
        </ul>
      </div>

      <div className="panel">
        <h3>Assigned Cases For Detective</h3>
        <ul className="list">
          {assignedCases.map((c) => (
            <li key={c.id}>
              Case #{c.id} - {c.title} - {c.status}
              <button type="button" style={{ marginLeft: 8 }} onClick={() => openBoard(c.id)}>Open Board</button>
            </li>
          ))}
          {assignedCases.length === 0 && <li>No assigned cases.</li>}
        </ul>
      </div>

      {message && <p className="error">{message}</p>}

      {context && (
        <div className="panel">
          <h3>Interactive Detective Board - Case #{context.case.id}</h3>
          <p><strong>{context.case.title}</strong> | suspects: {context.suspects.length} | evidence items: {Object.values(context.evidence).reduce((a, b) => a + b.length, 0)}</p>

          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
            <input
              placeholder="New note card"
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              style={{ maxWidth: 320 }}
            />
            <button type="button" onClick={addNoteNode}>Add Note Card</button>
            <input
              placeholder="Connection reason"
              value={edgeReason}
              onChange={(e) => setEdgeReason(e.target.value)}
              style={{ maxWidth: 260 }}
            />
            <button type="button" onClick={createEdge}>Connect Selected Cards (Red Line)</button>
            <button type="button" onClick={removeSelectedEdge}>Remove Selected Connection</button>
            <button type="button" onClick={deleteSelectedNode}>Delete Selected Card</button>
            <button type="button" onClick={exportBoardAsImage}>Export Board as PNG</button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, marginBottom: 10 }}>
            <input
              placeholder="Suspect full name"
              value={suspectForm.full_name}
              onChange={(e) => setSuspectForm({ ...suspectForm, full_name: e.target.value })}
            />
            <input
              placeholder="National ID (optional)"
              value={suspectForm.national_id}
              onChange={(e) => setSuspectForm({ ...suspectForm, national_id: e.target.value })}
            />
            <input
              placeholder="Photo URL (optional)"
              value={suspectForm.photo_url}
              onChange={(e) => setSuspectForm({ ...suspectForm, photo_url: e.target.value })}
            />
            <button type="button" onClick={addSuspect}>Add Suspect</button>
          </div>

          <div
            ref={boardRef}
            style={{
              position: 'relative',
              height: 560,
              border: '1px solid #d8deea',
              borderRadius: 10,
              overflow: 'hidden',
              background: 'linear-gradient(180deg, #fbfcff, #f0f4fb)',
            }}
          >
            <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
              {edges.map((edge) => {
                const from = nodeMap.get(edge.from_node)
                const to = nodeMap.get(edge.to_node)
                if (!from || !to) return null
                return (
                  <line
                    key={edge.id}
                    x1={from.x + 80}
                    y1={from.y + 28}
                    x2={to.x + 80}
                    y2={to.y + 28}
                    stroke="#d11a2a"
                    strokeWidth="3"
                  />
                )
              })}
            </svg>

            {nodes.map((n) => {
              const selected = selectedNodeIds.includes(n.id)
              return (
                <div
                  key={n.id}
                  onMouseDown={(e) => onNodeMouseDown(e, n)}
                  onClick={() => toggleNodeSelection(n.id)}
                  style={{
                    position: 'absolute',
                    left: n.x,
                    top: n.y,
                    width: 160,
                    minHeight: 56,
                    border: selected ? '2px solid #d11a2a' : '1px solid #b9c5d9',
                    borderRadius: 8,
                    padding: 8,
                    background: '#ffffff',
                    cursor: 'move',
                    boxShadow: '0 2px 8px rgba(30, 52, 88, 0.12)',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ fontSize: 11, color: '#5e6c85', textTransform: 'uppercase' }}>{n.kind}</div>
                  <div style={{ fontWeight: 600 }}>{n.label}</div>
                </div>
              )
            })}
          </div>

          <h4 style={{ marginTop: 12 }}>Connections</h4>
          <ul className="list">
            {edges.map((e) => (
              <li key={e.id}>
                {e.from_node} → {e.to_node} {e.reason ? `| ${e.reason}` : ''}
                <button type="button" style={{ marginLeft: 8 }} onClick={() => deleteEdge(e.id)}>Delete Line</button>
              </li>
            ))}
            {edges.length === 0 && <li>No connections yet.</li>}
          </ul>
        </div>
      )}
    </div>
  )
}
