import { useEffect, useMemo, useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function BoardPage() {
  const { user } = useAuth()
  const roleNames = useMemo(
    () => (user?.roles || []).map((r) => (r || '').toLowerCase().trim().replace(/\s+/g, ' ')),
    [user]
  )
  const isSergeant = user?.is_superuser || roleNames.includes('sergeant') || roleNames.includes('sergent') || roleNames.includes('sargent')
  const isDetective = user?.is_superuser || roleNames.includes('detective')
  const isCaptain = user?.is_superuser || roleNames.includes('captain')
  const isChief = user?.is_superuser || roleNames.includes('chief')
  const isSergeantOnly = isSergeant && !isDetective
  const canReviewCases = isSergeant || isCaptain || isChief || user?.is_superuser
  const [openCases, setOpenCases] = useState([])
  const [assignedCases, setAssignedCases] = useState([])
  const [reviewCases, setReviewCases] = useState([])
  const [context, setContext] = useState(null)
  const [message, setMessage] = useState('')

  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [selectedNodeIds, setSelectedNodeIds] = useState([])
  const [edgeReason, setEdgeReason] = useState('')
  const [newNote, setNewNote] = useState('')
  const [suspectForm, setSuspectForm] = useState({
    user_id: '',
    full_name: '',
    national_id: '',
    photo_url: '',
  })
  const [userOptions, setUserOptions] = useState([])
  const [selectedSuspectIds, setSelectedSuspectIds] = useState([])
  const [submissionReason, setSubmissionReason] = useState('')
  const [submissions, setSubmissions] = useState([])
  const [sergeantSubmissions, setSergeantSubmissions] = useState([])
  const [sergeantNote, setSergeantNote] = useState('')
  const [interrogations, setInterrogations] = useState([])
  const [interrogationForm, setInterrogationForm] = useState({
    suspect_id: '',
    detective_score: 5,
    detective_note: '',
    sergeant_score: 5,
    sergeant_note: '',
  })
  const [captainForm, setCaptainForm] = useState({})
  const [chiefForm, setChiefForm] = useState({})

  const boardRef = useRef(null)
  const dragState = useRef({ nodeId: null, offsetX: 0, offsetY: 0 })

  const nodeMap = useMemo(() => {
    const map = new Map()
    for (const n of nodes) map.set(n.id, n)
    return map
  }, [nodes])
  const evidenceLookup = useMemo(() => {
    const rows = {}
    const evidence = context?.evidence || {}
    const addRows = (items, type) => {
      ;(items || []).forEach((item) => {
        rows[`${type}:${item.id}`] = { type, item }
      })
    }
    addRows(evidence.witness, 'witness')
    addRows(evidence.biological, 'biological')
    addRows(evidence.vehicle, 'vehicle')
    addRows(evidence.identification, 'identification')
    addRows(evidence.other, 'other')
    return rows
  }, [context?.evidence])
  const suspectLookup = useMemo(() => {
    const rows = {}
    ;(context?.suspects || []).forEach((s) => {
      rows[s.id] = s
    })
    return rows
  }, [context?.suspects])
  const selectedNode = useMemo(
    () => (selectedNodeIds.length === 1 ? nodes.find((n) => n.id === selectedNodeIds[0]) || null : null),
    [selectedNodeIds, nodes],
  )
  const selectedNodeEvidence = useMemo(() => {
    if (!selectedNode || selectedNode.kind !== 'evidence' || !selectedNode.reference_id) return null
    return Object.values(evidenceLookup).find((x) => Number(x.item.id) === Number(selectedNode.reference_id)) || null
  }, [selectedNode, evidenceLookup])
  const selectedNodeSuspect = useMemo(() => {
    if (!selectedNode || selectedNode.kind !== 'suspect' || !selectedNode.reference_id) return null
    return suspectLookup[selectedNode.reference_id] || null
  }, [selectedNode, suspectLookup])
  const arrestedSuspects = useMemo(
    () => (context?.suspects || []).filter((s) => s.status === 'arrested'),
    [context?.suspects]
  )
  const pendingHigherDecisionForAnyInterrogation = useMemo(
    () =>
      (interrogations || []).some(
        (it) =>
          (it.captain_decision === 'pending' && it.detective_submitted && it.sergeant_submitted) ||
          (it.captain_decision === 'submitted' && it.captain_outcome === 'approved' && it.chief_decision === 'pending')
      ),
    [interrogations]
  )
  const selectedInterrogation = useMemo(
    () => (interrogations || []).find((it) => Number(it.suspect) === Number(interrogationForm.suspect_id)),
    [interrogations, interrogationForm.suspect_id]
  )
  const selectedInterrogationLocked = useMemo(
    () =>
      !!selectedInterrogation &&
      (
        (selectedInterrogation.captain_decision === 'pending'
          && selectedInterrogation.detective_submitted
          && selectedInterrogation.sergeant_submitted) ||
        (selectedInterrogation.captain_decision === 'submitted'
          && selectedInterrogation.captain_outcome === 'approved'
          && selectedInterrogation.chief_decision === 'pending')
      ),
    [selectedInterrogation]
  )
  const shouldShowScoringSection = (!isDetective && !isSergeant) || arrestedSuspects.length > 0 || interrogations.length > 0
  const hasPendingSuspectSubmission = useMemo(
    () => (submissions || []).some((s) => s.status === 'pending'),
    [submissions]
  )
  const caseLockedForInvestigation = ['sent_to_court', 'closed'].includes((context?.case?.status || '').toLowerCase())

  const loadCases = () => {
    api.get('/cases/cases/').then((res) => {
      const rows = res.data.results || []
      setOpenCases(rows.filter((c) => c.status === 'open' && !c.assigned_detective))
      setAssignedCases(rows.filter((c) => c.assigned_detective === user?.id))
      setReviewCases(rows.filter((c) => ['investigating', 'sent_to_court', 'open'].includes(c.status)))
    })
  }

  useEffect(() => {
    if (isDetective || canReviewCases) {
      loadCases()
    } else {
      setOpenCases([])
      setAssignedCases([])
      setReviewCases([])
    }
  }, [user?.id, isDetective, canReviewCases])

  useEffect(() => {
    if (!isSergeant) {
      setSergeantSubmissions([])
      return
    }
    loadSergeantSubmissions()
  }, [user?.id, isSergeant])

  useEffect(() => {
    if (isDetective || user?.is_superuser) {
      loadUserOptions()
    } else {
      setUserOptions([])
    }
  }, [isDetective, user?.is_superuser])

  const openBoard = async (caseId) => {
    setMessage('')
    try {
      const res = await api.post('/investigation/boards/open_case_board/', { case_id: caseId })
      setContext(res.data)
      setNodes(res.data.board.nodes || [])
      setEdges(res.data.board.edges || [])
      setSelectedNodeIds([])
      setSelectedSuspectIds([])
      setSubmissionReason('')
      loadSubmissions(caseId)
      loadInterrogations(caseId)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to open board')
    }
  }

  const loadSubmissions = async (caseId) => {
    try {
      const res = await api.get(`/investigation/suspect-submissions/?case_id=${caseId}`)
      setSubmissions(res.data.results || [])
    } catch {
      setSubmissions([])
    }
  }

  const loadSergeantSubmissions = async () => {
    try {
      const res = await api.get('/investigation/suspect-submissions/')
      setSergeantSubmissions((res.data.results || []).filter((x) => x.status === 'pending'))
    } catch {
      setSergeantSubmissions([])
    }
  }

  const loadInterrogations = async (caseId) => {
    try {
      const res = await api.get(`/investigation/interrogations/?case_id=${caseId}`)
      setInterrogations(res.data.results || [])
    } catch {
      setInterrogations([])
    }
  }

  const loadUserOptions = async () => {
    try {
      const res = await api.get('/investigation/suspects/selectable_users/')
      setUserOptions(Array.isArray(res.data) ? res.data : [])
    } catch {
      setUserOptions([])
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
    if (!context) return
    if (!suspectForm.user_id && !suspectForm.full_name.trim()) {
      setMessage('Select a user or enter suspect full name.')
      return
    }
    const selectedUser = userOptions.find((u) => Number(u.id) === Number(suspectForm.user_id))
    const resolvedName = selectedUser?.full_name || suspectForm.full_name
    try {
      const created = await api.post('/investigation/suspects/', {
        case: context.case.id,
        person: selectedUser ? Number(selectedUser.id) : null,
        full_name: resolvedName,
        national_id: selectedUser?.national_id || suspectForm.national_id,
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
      setContext((prev) => ({
        ...prev,
        suspects: [...(prev?.suspects || []), created.data],
      }))
      setSuspectForm({ user_id: '', full_name: '', national_id: '', photo_url: '' })
      setMessage(`Suspect "${created.data.full_name}" added to case and board.`)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to add suspect')
    }
  }

  const toggleSuspect = (id) => {
    setSelectedSuspectIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const submitMainSuspects = async () => {
    if (!context) return
    if (hasPendingSuspectSubmission) {
      setMessage('A submission is already pending sergeant review for this case.')
      return
    }
    if (selectedSuspectIds.length === 0 || !submissionReason.trim()) {
      setMessage('Select main suspects and provide detective reason.')
      return
    }
    try {
      await api.post('/investigation/suspect-submissions/submit_main_suspects/', {
        case_id: context.case.id,
        suspect_ids: selectedSuspectIds,
        detective_reason: submissionReason,
      })
      setMessage('Main suspects submitted to sergeant for review.')
      setSelectedSuspectIds([])
      setSubmissionReason('')
      loadSubmissions(context.case.id)
      loadSergeantSubmissions()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to submit main suspects')
    }
  }

  const reviewSubmission = async (submissionId, approved, caseId = null) => {
    try {
      await api.post(`/investigation/suspect-submissions/${submissionId}/sergeant_review/`, {
        approved,
        message: sergeantNote,
      })
      setMessage(approved ? 'Sergeant approved submission; arrest process started.' : 'Sergeant rejected submission and notified detective.')
      setSergeantNote('')
      if (caseId) {
        loadSubmissions(caseId)
      }
      loadSergeantSubmissions()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to review submission')
    }
  }

  const recordInterrogation = async () => {
    if (!context || !interrogationForm.suspect_id) {
      setMessage('Select suspect to record interrogation.')
      return
    }
    if (pendingHigherDecisionForAnyInterrogation || selectedInterrogationLocked) {
      setMessage('Assessment is locked while pending captain/chief decision.')
      return
    }

    const payload = {
      case_id: context.case.id,
      suspect_id: Number(interrogationForm.suspect_id),
    }
    if (isDetective) {
      payload.detective_score = Number(interrogationForm.detective_score)
      payload.detective_note = interrogationForm.detective_note
    }
    if (isSergeant && !isDetective) {
      payload.sergeant_score = Number(interrogationForm.sergeant_score)
      payload.sergeant_note = interrogationForm.sergeant_note
    }

    try {
      await api.post('/investigation/interrogations/record_assessment/', payload)
      setMessage('Interrogation assessment saved.')
      loadInterrogations(context.case.id)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to save interrogation assessment')
    }
  }

  const captainDecision = async (interrogationId, approved) => {
    const note = captainForm[interrogationId]?.note || ''
    try {
      await api.post(`/investigation/interrogations/${interrogationId}/captain_decision/`, {
        approved,
        captain_note: note,
      })
      setMessage(approved ? 'Captain approved to trial.' : 'Captain rejected and returned to investigation.')
      loadInterrogations(context.case.id)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to save captain decision')
    }
  }

  const chiefReview = async (interrogationId, approved) => {
    const note = chiefForm[interrogationId]?.note || ''
    try {
      await api.post(`/investigation/interrogations/${interrogationId}/chief_review/`, {
        approved,
        chief_note: note,
      })
      setMessage(approved ? 'Chief approved and case sent to court.' : 'Chief rejected captain decision.')
      loadInterrogations(context.case.id)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Failed to submit chief review')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {isDetective && (
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
      )}

      {!isDetective && canReviewCases && !isSergeant && (
      <div className="panel">
        <h3>Case Boards For Review</h3>
        <ul className="list">
          {reviewCases.map((c) => (
            <li key={c.id}>
              Case #{c.id} - {c.title} - {c.status}
              <button type="button" style={{ marginLeft: 8 }} onClick={() => openBoard(c.id)}>Open Board</button>
            </li>
          ))}
          {reviewCases.length === 0 && <li>No cases available for review.</li>}
        </ul>
      </div>
      )}

      {isSergeantOnly && (
      <div className="panel">
        <h3>Sergeant Cases (Open For Scoring / Review)</h3>
        <ul className="list">
          {reviewCases.map((c) => (
            <li key={c.id}>
              Case #{c.id} - {c.title} - {c.status}
              <button type="button" style={{ marginLeft: 8 }} onClick={() => openBoard(c.id)}>Open Case Review</button>
            </li>
          ))}
          {reviewCases.length === 0 && <li>No cases available for sergeant review.</li>}
        </ul>
      </div>
      )}

      {isDetective && (
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
      )}

      {!context && isSergeant && (
        <div className="panel">
          <h3>Sergeant Review Queue</h3>
          <ul className="list">
            {sergeantSubmissions.map((s) => (
              <li key={s.id}>
                Submission #{s.id} | case #{s.case} | suspects: {(s.suspect_brief || []).map((x) => x.full_name).join(', ')}
                <div>Reason: {s.detective_reason}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                  <input
                    placeholder="Sergeant review message"
                    value={sergeantNote}
                    onChange={(e) => setSergeantNote(e.target.value)}
                    style={{ maxWidth: 320 }}
                  />
                  <button type="button" onClick={() => openBoard(s.case)}>Open Case Board</button>
                  <button type="button" onClick={() => reviewSubmission(s.id, true, s.case)}>Approve</button>
                  <button type="button" onClick={() => reviewSubmission(s.id, false, s.case)}>Reject</button>
                </div>
              </li>
            ))}
            {sergeantSubmissions.length === 0 && <li>No pending submissions right now.</li>}
          </ul>
        </div>
      )}

      {message && <p className="error">{message}</p>}

      {context && (
        <div className="panel">
          <h3>{isDetective ? 'Interactive Detective Board' : 'Case Review'} - Case #{context.case.id}</h3>
          <p><strong>{context.case.title}</strong> | suspects: {context.suspects.length} | evidence items: {Object.values(context.evidence).reduce((a, b) => a + b.length, 0)}</p>

          {isDetective && (
            <>
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

          <div
            ref={boardRef}
            style={{
              position: 'relative',
              height: 560,
              border: '1px solid #d8deea',
              borderRadius: 10,
              overflow: 'hidden',
              background: 'linear-gradient(180deg, #fbfcff, #f0f4fb)',
              marginBottom: 10,
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
          <ul className="list" style={{ marginBottom: 10 }}>
            {edges.map((e) => (
              <li key={e.id}>
                {e.from_node} → {e.to_node} {e.reason ? `| ${e.reason}` : ''}
                <button type="button" style={{ marginLeft: 8 }} onClick={() => deleteEdge(e.id)}>Delete Line</button>
              </li>
            ))}
            {edges.length === 0 && <li>No connections yet.</li>}
          </ul>

          <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginBottom: 10 }}>
            <h4>Card Details</h4>
            {!selectedNode && <p style={{ margin: 0 }}>Select one card on board to view full details.</p>}
            {selectedNode && (
              <div style={{ display: 'grid', gap: 6 }}>
                <div><strong>Card ID:</strong> {selectedNode.id}</div>
                <div><strong>Kind:</strong> {selectedNode.kind}</div>
                <div><strong>Label:</strong> {selectedNode.label}</div>
                <div><strong>Position:</strong> x={Math.round(selectedNode.x)}, y={Math.round(selectedNode.y)}</div>
                {selectedNode.kind === 'note' && (
                  <div><strong>Note Text:</strong> {selectedNode.label}</div>
                )}
                {selectedNode.kind === 'suspect' && selectedNodeSuspect && (
                  <>
                    <div><strong>Suspect ID:</strong> {selectedNodeSuspect.id}</div>
                    <div><strong>Full Name:</strong> {selectedNodeSuspect.full_name}</div>
                    <div><strong>Status:</strong> {selectedNodeSuspect.status}</div>
                    <div><strong>National ID:</strong> {selectedNodeSuspect.national_id || '-'}</div>
                    <div><strong>Photo URL:</strong> {selectedNodeSuspect.photo_url || '-'}</div>
                  </>
                )}
                {selectedNode.kind === 'evidence' && selectedNodeEvidence && (
                  <>
                    <div><strong>Evidence Type:</strong> {selectedNodeEvidence.type}</div>
                    <div><strong>Evidence ID:</strong> {selectedNodeEvidence.item.id}</div>
                    <div><strong>Title:</strong> {selectedNodeEvidence.item.title}</div>
                    <div><strong>Description:</strong> {selectedNodeEvidence.item.description}</div>
                    <div><strong>Case:</strong> {selectedNodeEvidence.item.case}</div>
                    <div><strong>Recorded By:</strong> {selectedNodeEvidence.item.recorded_by}</div>
                    <div><strong>Recorded At:</strong> {selectedNodeEvidence.item.recorded_at}</div>
                    {selectedNodeEvidence.type === 'witness' && (
                      <>
                        <div><strong>Transcript:</strong> {selectedNodeEvidence.item.transcript || '-'}</div>
                        <div><strong>Media URL:</strong> {selectedNodeEvidence.item.media_url || '-'}</div>
                        <div><strong>Media Items:</strong> {JSON.stringify(selectedNodeEvidence.item.media_items || [])}</div>
                      </>
                    )}
                    {selectedNodeEvidence.type === 'biological' && (
                      <>
                        <div><strong>Image URLs:</strong> {JSON.stringify(selectedNodeEvidence.item.image_urls || [])}</div>
                        <div><strong>Forensic Result:</strong> {selectedNodeEvidence.item.forensic_result || '-'}</div>
                        <div><strong>Identity DB Result:</strong> {selectedNodeEvidence.item.identity_db_result || '-'}</div>
                      </>
                    )}
                    {selectedNodeEvidence.type === 'vehicle' && (
                      <>
                        <div><strong>Model:</strong> {selectedNodeEvidence.item.model_name}</div>
                        <div><strong>Color:</strong> {selectedNodeEvidence.item.color}</div>
                        <div><strong>Plate:</strong> {selectedNodeEvidence.item.plate_number || '-'}</div>
                        <div><strong>Serial:</strong> {selectedNodeEvidence.item.serial_number || '-'}</div>
                      </>
                    )}
                    {selectedNodeEvidence.type === 'identification' && (
                      <>
                        <div><strong>Owner Full Name:</strong> {selectedNodeEvidence.item.owner_full_name}</div>
                        <div><strong>Metadata:</strong> {JSON.stringify(selectedNodeEvidence.item.metadata || {})}</div>
                      </>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginBottom: 10 }}>
            <h4>All Board Cards</h4>
            <ul className="list">
              {nodes.map((n) => {
                const ev = n.kind === 'evidence'
                  ? Object.values(evidenceLookup).find((x) => Number(x.item.id) === Number(n.reference_id))
                  : null
                const sp = n.kind === 'suspect' ? suspectLookup[n.reference_id] : null
                return (
                  <li key={`detail-${n.id}`}>
                    <strong>#{n.id}</strong> [{n.kind}] {n.label}
                    {ev && <div>Evidence: {ev.type} #{ev.item.id} | {ev.item.title}</div>}
                    {sp && <div>Suspect: #{sp.id} {sp.full_name} | status: {sp.status}</div>}
                    <button type="button" style={{ marginTop: 6 }} onClick={() => setSelectedNodeIds([n.id])}>Show Details</button>
                  </li>
                )
              })}
              {nodes.length === 0 && <li>No cards on board.</li>}
            </ul>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1fr auto', gap: 8, marginBottom: 10 }}>
            <select
              value={suspectForm.user_id}
              onChange={(e) => {
                const selectedId = e.target.value
                const selected = userOptions.find((u) => Number(u.id) === Number(selectedId))
                setSuspectForm((prev) => ({
                  ...prev,
                  user_id: selectedId,
                  full_name: selected ? selected.full_name : prev.full_name,
                  national_id: selected ? selected.national_id : prev.national_id,
                }))
              }}
            >
              <option value="">Select user as suspect</option>
              {userOptions.map((u) => (
                <option key={u.id} value={u.id}>
                  #{u.id} {u.full_name} ({u.username}) - {u.national_id}
                </option>
              ))}
            </select>
            <input
              placeholder="Suspect full name (manual fallback)"
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

          <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginBottom: 10 }}>
            <h4>Main Suspects Declaration (Detective → Sergeant)</h4>
            <div style={{ display: 'grid', gap: 8 }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {(context.suspects || []).map((s) => (
                  <label key={s.id} style={{ border: '1px solid #d8deea', borderRadius: 8, padding: '4px 8px' }}>
                    <input
                      type="checkbox"
                      checked={selectedSuspectIds.includes(s.id)}
                      onChange={() => toggleSuspect(s.id)}
                    />{' '}
                    #{s.id} {s.full_name}
                  </label>
                ))}
              </div>
              <textarea
                placeholder="Detective reasons and rationale for selected main suspects"
                value={submissionReason}
                onChange={(e) => setSubmissionReason(e.target.value)}
              />
              {isDetective && (
                <>
                  <button type="button" onClick={submitMainSuspects} disabled={hasPendingSuspectSubmission}>
                    Submit Main Suspects To Sergeant
                  </button>
                  {hasPendingSuspectSubmission && (
                    <p style={{ margin: 0, color: '#8a1b1b' }}>
                      A submission is already pending sergeant review. You cannot submit this case again yet.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
            </>
          )}

          {isSergeantOnly && (
            <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginBottom: 10 }}>
              <h4>Sergeant Review Details (No Board Access)</h4>
              <div><strong>Case ID:</strong> {context.case.id}</div>
              <div><strong>Case Status:</strong> {context.case.status}</div>
              <div><strong>Case Severity:</strong> {context.case.severity}</div>
              <div><strong>Description:</strong> {context.case.description}</div>

              <h4 style={{ marginTop: 10 }}>Selected Suspects Sent By Detective</h4>
              <ul className="list">
                {submissions.map((sub) => (
                  <li key={`sub-suspects-${sub.id}`}>
                    Submission #{sub.id} | status: {sub.status}
                    <div><strong>Detective reason:</strong> {sub.detective_reason}</div>
                    <div style={{ marginTop: 4 }}>
                      {(sub.suspect_brief || []).map((brief) => {
                        const full = (context.suspects || []).find((s) => s.id === brief.id)
                        return (
                          <div key={`sus-${sub.id}-${brief.id}`}>
                            #{brief.id} | {brief.full_name} | status: {brief.status}
                            {full?.national_id ? ` | national_id: ${full.national_id}` : ''}
                          </div>
                        )
                      })}
                      {(sub.suspect_brief || []).length === 0 && <div>No suspects in this submission.</div>}
                    </div>
                  </li>
                ))}
                {submissions.length === 0 && <li>No suspect submissions yet.</li>}
              </ul>

              <h4 style={{ marginTop: 10 }}>All Evidence In This Case</h4>
              <ul className="list">
                {(context.evidence?.witness || []).map((e) => (
                  <li key={`w-${e.id}`}>[Witness] #{e.id} {e.title} | {e.description}</li>
                ))}
                {(context.evidence?.biological || []).map((e) => (
                  <li key={`b-${e.id}`}>[Biological] #{e.id} {e.title} | {e.description}</li>
                ))}
                {(context.evidence?.vehicle || []).map((e) => (
                  <li key={`v-${e.id}`}>[Vehicle] #{e.id} {e.title} | {e.description}</li>
                ))}
                {(context.evidence?.identification || []).map((e) => (
                  <li key={`i-${e.id}`}>[Identification] #{e.id} {e.title} | {e.description}</li>
                ))}
                {(context.evidence?.other || []).map((e) => (
                  <li key={`o-${e.id}`}>[Other] #{e.id} {e.title} | {e.description}</li>
                ))}
                {Object.values(context.evidence || {}).every((arr) => (arr || []).length === 0) && (
                  <li>No evidence recorded for this case.</li>
                )}
              </ul>
              {arrestedSuspects.length === 0 && (
                <p style={{ marginTop: 8, color: '#546176' }}>
                  No arrested suspect in this case yet, so scoring section is hidden.
                </p>
              )}
            </div>
          )}

          <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginBottom: 10 }}>
            <h4>Sergeant Review Queue</h4>
            <ul className="list">
              {submissions.map((s) => (
                <li key={s.id}>
                  Submission #{s.id} | status: {s.status} | suspects: {(s.suspect_brief || []).map((x) => x.full_name).join(', ')}
                  <div>Reason: {s.detective_reason}</div>
                  {s.status === 'pending' && isSergeant && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                      <input
                        placeholder="Sergeant review message"
                        value={sergeantNote}
                        onChange={(e) => setSergeantNote(e.target.value)}
                        style={{ maxWidth: 320 }}
                      />
                      <button type="button" onClick={() => reviewSubmission(s.id, true, context.case.id)}>Approve</button>
                      <button type="button" onClick={() => reviewSubmission(s.id, false, context.case.id)}>Reject</button>
                    </div>
                  )}
                  {s.status !== 'pending' && (
                    <div>Sergeant message: {s.sergeant_message || '-'}</div>
                  )}
                </li>
              ))}
              {submissions.length === 0 && <li>No suspect submissions yet.</li>}
            </ul>
          </div>

          {shouldShowScoringSection && (
          <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginBottom: 10 }}>
            <h4>Post-Arrest Suspect Scoring (1-10)</h4>
            {pendingHigherDecisionForAnyInterrogation && (
              <p style={{ margin: 0, color: '#8a1b1b' }}>
                Changes are locked only for interrogations pending captain/chief decision.
              </p>
            )}
            {caseLockedForInvestigation && (
              <p style={{ margin: 0, color: '#8a1b1b' }}>
                Case is in court/closed status. Detective and sergeant cannot change interrogation scores.
              </p>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8, marginBottom: 8 }}>
              <select
                value={interrogationForm.suspect_id}
                onChange={(e) => setInterrogationForm({ ...interrogationForm, suspect_id: e.target.value })}
                disabled={caseLockedForInvestigation}
              >
                <option value="">Select arrested suspect</option>
                {arrestedSuspects.map((s) => (
                  <option key={s.id} value={s.id}>#{s.id} {s.full_name}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 8, marginTop: 8 }}>
              <input
                type="number"
                min="1"
                max="10"
                value={interrogationForm.detective_score}
                onChange={(e) => setInterrogationForm({ ...interrogationForm, detective_score: e.target.value })}
                disabled={!isDetective || selectedInterrogationLocked || caseLockedForInvestigation}
                placeholder="Detective score (1-10)"
              />
              <input
                value={interrogationForm.detective_note}
                onChange={(e) => setInterrogationForm({ ...interrogationForm, detective_note: e.target.value })}
                disabled={!isDetective || selectedInterrogationLocked || caseLockedForInvestigation}
                placeholder="Detective statement"
              />
              <input
                type="number"
                min="1"
                max="10"
                value={interrogationForm.sergeant_score}
                onChange={(e) => setInterrogationForm({ ...interrogationForm, sergeant_score: e.target.value })}
                disabled={!isSergeant || selectedInterrogationLocked || caseLockedForInvestigation}
                placeholder="Sergeant score (1-10)"
              />
              <input
                value={interrogationForm.sergeant_note}
                onChange={(e) => setInterrogationForm({ ...interrogationForm, sergeant_note: e.target.value })}
                disabled={!isSergeant || selectedInterrogationLocked || caseLockedForInvestigation}
                placeholder="Sergeant statement"
              />
            </div>
            {(isDetective || isSergeant) && !selectedInterrogationLocked && !caseLockedForInvestigation && (
              <button type="button" style={{ marginTop: 8 }} onClick={recordInterrogation}>
                Save Interrogation Assessment
              </button>
            )}

            <ul className="list" style={{ marginTop: 10 }}>
              {interrogations.map((it) => (
                <li key={it.id}>
                  Interrogation #{it.id} | suspect #{it.suspect} | D:{it.detective_score}/10 S:{it.sergeant_score}/10
                  <div>Detective statement: {it.detective_note || '-'}</div>
                  <div>Sergeant statement: {it.sergeant_note || '-'}</div>
                  <div>
                    Submitted: detective={it.detective_submitted ? 'yes' : 'no'} | sergeant={it.sergeant_submitted ? 'yes' : 'no'}
                  </div>
                  <div>Captain decision: {it.captain_decision} / outcome: {it.captain_outcome} {it.captain_score ? `(${it.captain_score}/10)` : ''}</div>
                  <div>Chief decision: {it.chief_decision}</div>
                  {isCaptain && it.captain_outcome === 'rejected' && !(it.detective_submitted && it.sergeant_submitted) && (
                    <div style={{ color: '#8a1b1b' }}>
                      Waiting for both detective and sergeant to submit new scores after rejection.
                    </div>
                  )}

                  {isCaptain && it.detective_submitted && it.sergeant_submitted && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                      <span style={{ fontSize: 12, color: '#546176' }}>Captain decision required</span>
                      <input
                        placeholder="Captain final note"
                        value={captainForm[it.id]?.note || ''}
                        onChange={(e) => setCaptainForm((prev) => ({ ...prev, [it.id]: { ...(prev[it.id] || {}), note: e.target.value } }))}
                        style={{ maxWidth: 320 }}
                      />
                      <button type="button" onClick={() => captainDecision(it.id, true)}>Approve To Trial</button>
                      <button type="button" onClick={() => captainDecision(it.id, false)}>Reject (Back To Investigation)</button>
                    </div>
                  )}

                  {isChief && it.chief_decision === 'pending' && it.captain_decision === 'submitted' && it.captain_outcome === 'approved' && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                      <input
                        placeholder="Chief review note"
                        value={chiefForm[it.id]?.note || ''}
                        onChange={(e) => setChiefForm((prev) => ({ ...prev, [it.id]: { ...(prev[it.id] || {}), note: e.target.value } }))}
                        style={{ maxWidth: 320 }}
                      />
                      <button type="button" onClick={() => chiefReview(it.id, true)}>Approve Captain</button>
                      <button type="button" onClick={() => chiefReview(it.id, false)}>Reject Captain</button>
                    </div>
                  )}
                  {isChief && it.chief_decision === 'pending' && !(it.captain_decision === 'submitted' && it.captain_outcome === 'approved') && (
                    <div style={{ color: '#546176', marginTop: 6 }}>
                      Chief review will be available after captain approval.
                    </div>
                  )}
                </li>
              ))}
              {interrogations.length === 0 && <li>No interrogations recorded for this case.</li>}
            </ul>
          </div>
          )}

        </div>
      )}
    </div>
  )
}
