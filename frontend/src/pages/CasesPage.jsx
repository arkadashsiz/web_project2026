import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function CasesPage() {
  const { user } = useAuth()
  const roles = useMemo(() => (user?.roles || []).map((r) => r.toLowerCase()), [user])
  const isCadet = roles.includes('cadet') || user?.is_superuser
  const isOfficer = roles.includes('police officer') || user?.is_superuser
  const canScene = user?.is_superuser || roles.some((r) => ['patrol officer', 'police officer', 'detective', 'sergeant', 'captain', 'chief'].includes(r))

  const [cases, setCases] = useState([])
  const [mode, setMode] = useState('complaint')
  const [error, setError] = useState('')
  const [workflowMsg, setWorkflowMsg] = useState('')
  const [workflowMsgType, setWorkflowMsgType] = useState('success')
  const [complaintForm, setComplaintForm] = useState({
    title: '', description: '', severity: 1, additional_complainant_ids: '',
  })
  const [sceneForm, setSceneForm] = useState({
    title: '',
    description: '',
    severity: 2,
    scene_reported_at: '',
    witnesses: [{ full_name: '', national_id: '', phone: '', statement: '' }],
  })
  const [workflow, setWorkflow] = useState({
    caseId: '',
    complainantRecordId: '',
    cadetApproved: true,
    cadetNote: '',
    officerApproved: true,
    officerNote: '',
    resubmitTitle: '',
    resubmitDescription: '',
    resubmitSeverity: 1,
  })
  const [selectedCaseTitle, setSelectedCaseTitle] = useState('')

  const complaintQueue = useMemo(
    () =>
      cases.filter(
        (c) => c.source === 'complaint' && c.complaint_submission && c.complaint_submission.stage !== 'formed'
      ),
    [cases]
  )
  const caseList = useMemo(
    () =>
      cases.filter((c) => c.source !== 'complaint' || !c.complaint_submission || c.complaint_submission.stage === 'formed'),
    [cases]
  )

  const load = () => api.get('/cases/cases/').then((res) => setCases(res.data.results || []))
  useEffect(() => { load() }, [])

  const parseIds = (s) => s.split(',').map((x) => x.trim()).filter(Boolean).map((x) => Number(x))

  const createComplaint = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/cases/cases/submit_complaint/', {
        title: complaintForm.title,
        description: complaintForm.description,
        severity: Number(complaintForm.severity),
        additional_complainant_ids: parseIds(complaintForm.additional_complainant_ids),
      })
      setComplaintForm({ title: '', description: '', severity: 1, additional_complainant_ids: '' })
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit complaint case.')
    }
  }

  const createSceneReport = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/cases/cases/submit_scene_report/', {
        ...sceneForm,
        severity: Number(sceneForm.severity),
      })
      setSceneForm({
        title: '',
        description: '',
        severity: 2,
        scene_reported_at: '',
        witnesses: [{ full_name: '', national_id: '', phone: '', statement: '' }],
      })
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit scene report.')
    }
  }

  const updateWitness = (idx, key, value) => {
    const witnesses = [...sceneForm.witnesses]
    witnesses[idx] = { ...witnesses[idx], [key]: value }
    setSceneForm({ ...sceneForm, witnesses })
  }

  const addWitness = () => {
    setSceneForm({
      ...sceneForm,
      witnesses: [...sceneForm.witnesses, { full_name: '', national_id: '', phone: '', statement: '' }],
    })
  }

  const callWorkflow = async (fn) => {
    setWorkflowMsg('')
    try {
      await fn()
      setWorkflowMsgType('success')
      setWorkflowMsg('Action completed.')
      load()
    } catch (err) {
      setWorkflowMsgType('error')
      setWorkflowMsg(err?.response?.data?.detail || 'Action failed.')
    }
  }

  const cadetReviewComplainant = () => callWorkflow(() =>
    api.post(`/cases/cases/${workflow.caseId}/intern_review_complainant/`, {
      complainant_id: Number(workflow.complainantRecordId),
      approved: workflow.cadetApproved,
      note: workflow.cadetNote,
    })
  )

  const cadetFinalReview = () => callWorkflow(() =>
    api.post(`/cases/cases/${workflow.caseId}/intern_review/`, {
      approved: workflow.cadetApproved,
      note: workflow.cadetNote,
    })
  )

  const officerFinalReview = () => callWorkflow(() =>
    api.post(`/cases/cases/${workflow.caseId}/officer_review/`, {
      approved: workflow.officerApproved,
      note: workflow.officerNote,
    })
  )

  const complainantResubmit = () => callWorkflow(() =>
    api.post(`/cases/cases/${workflow.caseId}/resubmit_complaint/`, {
      title: workflow.resubmitTitle,
      description: workflow.resubmitDescription,
      severity: Number(workflow.resubmitSeverity),
    })
  )

  const useInDesk = (c) => {
    setWorkflow({
      ...workflow,
      caseId: String(c.id),
      resubmitTitle: c.title || '',
      resubmitDescription: c.description || '',
      resubmitSeverity: Number(c.severity || 1),
    })
    setSelectedCaseTitle(c.title || '')
    setWorkflowMsgType('error')
    setWorkflowMsg(`Selected complaint #${c.id} for workflow desk.`)
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <div className="two-col">
        <div className="panel">
          <h3>Create Case</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className={mode === 'complaint' ? '' : 'btn-link secondary'} onClick={() => setMode('complaint')}>
              From Complaint
            </button>
            {canScene && (
              <button type="button" className={mode === 'scene' ? '' : 'btn-link secondary'} onClick={() => setMode('scene')}>
                From Crime Scene
              </button>
            )}
          </div>

          {mode === 'complaint' ? (
            <form onSubmit={createComplaint} style={{ display: 'grid', gap: 10 }}>
              <input placeholder="Case title" value={complaintForm.title} onChange={(e) => setComplaintForm({ ...complaintForm, title: e.target.value })} />
              <textarea placeholder="Description" value={complaintForm.description} onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })} />
              <select value={complaintForm.severity} onChange={(e) => setComplaintForm({ ...complaintForm, severity: Number(e.target.value) })}>
                <option value={1}>Level 3</option>
                <option value={2}>Level 2</option>
                <option value={3}>Level 1</option>
                <option value={4}>Critical</option>
              </select>
              <input
                placeholder="Additional complainant user IDs (comma separated)"
                value={complaintForm.additional_complainant_ids}
                onChange={(e) => setComplaintForm({ ...complaintForm, additional_complainant_ids: e.target.value })}
              />
              <button type="submit">Submit Initial Complaint</button>
            </form>
          ) : (
            <form onSubmit={createSceneReport} style={{ display: 'grid', gap: 10 }}>
              <input placeholder="Case title" value={sceneForm.title} onChange={(e) => setSceneForm({ ...sceneForm, title: e.target.value })} />
              <textarea placeholder="Scene description" value={sceneForm.description} onChange={(e) => setSceneForm({ ...sceneForm, description: e.target.value })} />
              <input type="datetime-local" value={sceneForm.scene_reported_at} onChange={(e) => setSceneForm({ ...sceneForm, scene_reported_at: e.target.value })} />
              <select value={sceneForm.severity} onChange={(e) => setSceneForm({ ...sceneForm, severity: Number(e.target.value) })}>
                <option value={1}>Level 3</option>
                <option value={2}>Level 2</option>
                <option value={3}>Level 1</option>
                <option value={4}>Critical</option>
              </select>
              <h4>Witnesses</h4>
              {sceneForm.witnesses.map((w, idx) => (
                <div key={idx} style={{ border: '1px solid #d8deea', padding: 10, borderRadius: 8, display: 'grid', gap: 8 }}>
                  <input placeholder="Full name" value={w.full_name} onChange={(e) => updateWitness(idx, 'full_name', e.target.value)} />
                  <input placeholder="National ID" value={w.national_id} onChange={(e) => updateWitness(idx, 'national_id', e.target.value)} />
                  <input placeholder="Phone" value={w.phone} onChange={(e) => updateWitness(idx, 'phone', e.target.value)} />
                  <textarea placeholder="Statement" value={w.statement} onChange={(e) => updateWitness(idx, 'statement', e.target.value)} />
                </div>
              ))}
              <button type="button" onClick={addWitness}>Add Another Witness</button>
              <button type="submit">Submit Scene Case</button>
            </form>
          )}
          {error && <p className="error">{error}</p>}
        </div>

        <div className="panel">
          <h3>Complaints Queue (Before Officer Final Approval)</h3>
          <ul className="list">
            {complaintQueue.map((c) => (
              <li key={c.id}>
                <div>
                  <strong>Complaint #{c.id}</strong> {c.title} | status: {c.status}
                  <button type="button" style={{ marginLeft: 8 }} onClick={() => useInDesk(c)}>Use in desk</button>
                </div>
                {c.complaint_submission && (
                  <div style={{ marginTop: 6, fontSize: 13 }}>
                    stage: {c.complaint_submission.stage} | attempts: {c.complaint_submission.attempt_count}
                    {c.complaint_submission.last_error_message && (
                      <div><strong>last error:</strong> {c.complaint_submission.last_error_message}</div>
                    )}
                    {c.complaint_submission.intern_note && <div>cadet note: {c.complaint_submission.intern_note}</div>}
                    {c.complaint_submission.officer_note && <div>officer note: {c.complaint_submission.officer_note}</div>}
                    <div>
                      complainants: {c.complainants?.map((x) => `(${x.id}) user:${x.user} ${x.status}`).join(' | ') || '-'}
                    </div>
                  </div>
                )}
              </li>
            ))}
            {complaintQueue.length === 0 && <li>No pending complaints.</li>}
          </ul>
        </div>
      </div>

      <div className="panel">
        <h3>Case List (Formed Cases)</h3>
        <ul className="list">
          {caseList.map((c) => (
            <li key={c.id}>
              <strong>Case #{c.id}</strong> {c.title} | source: {c.source} | status: {c.status}
              {c.source === 'complaint' && <span> | formed by officer approval</span>}
            </li>
          ))}
          {caseList.length === 0 && <li>No formed cases yet.</li>}
          </ul>
        </div>

      <div className="panel">
        <h3>Complaint Workflow Desk</h3>
        {workflow.caseId && (
          <p style={{ margin: 0 }}>
            <strong>Selected:</strong> complaint #{workflow.caseId} {selectedCaseTitle ? `- ${selectedCaseTitle}` : ''}
          </p>
        )}
        <p style={{ margin: 0, color: '#546176' }}>
          Base users/complainants: submit and resubmit. Cadet: complainant validation + cadet review. Officer: final review.
        </p>
        <input placeholder="Case ID" value={workflow.caseId} onChange={(e) => setWorkflow({ ...workflow, caseId: e.target.value })} />

        <div className="two-col">
          <div style={{ display: 'grid', gap: 8 }}>
            {isCadet && (
              <>
                <h4>Cadet Actions</h4>
                <input
                  placeholder="Complainant Record ID"
                  value={workflow.complainantRecordId}
                  onChange={(e) => setWorkflow({ ...workflow, complainantRecordId: e.target.value })}
                />
                <select value={workflow.cadetApproved ? 'true' : 'false'} onChange={(e) => setWorkflow({ ...workflow, cadetApproved: e.target.value === 'true' })}>
                  <option value="true">Approve</option>
                  <option value="false">Reject</option>
                </select>
                <textarea placeholder="Cadet note / mandatory error message on reject" value={workflow.cadetNote} onChange={(e) => setWorkflow({ ...workflow, cadetNote: e.target.value })} />
                <button type="button" onClick={cadetReviewComplainant}>Save Complainant Review</button>
                <button type="button" onClick={cadetFinalReview}>Cadet Final Review</button>
              </>
            )}

            {!isCadet && <p style={{ margin: 0, color: '#546176' }}>Cadet actions are hidden for your role.</p>}
          </div>

          <div style={{ display: 'grid', gap: 8 }}>
            {isOfficer && (
              <>
                <h4>Officer Actions</h4>
                <select value={workflow.officerApproved ? 'true' : 'false'} onChange={(e) => setWorkflow({ ...workflow, officerApproved: e.target.value === 'true' })}>
                  <option value="true">Approve Case Formation</option>
                  <option value="false">Return To Cadet</option>
                </select>
                <textarea placeholder="Officer note" value={workflow.officerNote} onChange={(e) => setWorkflow({ ...workflow, officerNote: e.target.value })} />
                <button type="button" onClick={officerFinalReview}>Submit Officer Review</button>
              </>
            )}

            <h4>Complainant Resubmit</h4>
            <input placeholder="Updated title" value={workflow.resubmitTitle} onChange={(e) => setWorkflow({ ...workflow, resubmitTitle: e.target.value })} />
            <textarea placeholder="Updated description" value={workflow.resubmitDescription} onChange={(e) => setWorkflow({ ...workflow, resubmitDescription: e.target.value })} />
            <select value={workflow.resubmitSeverity} onChange={(e) => setWorkflow({ ...workflow, resubmitSeverity: Number(e.target.value) })}>
              <option value={1}>Level 3</option>
              <option value={2}>Level 2</option>
              <option value={3}>Level 1</option>
              <option value={4}>Critical</option>
            </select>
            <button type="button" onClick={complainantResubmit}>Submit Resubmission</button>
          </div>
        </div>

        {workflowMsg && <p className={workflowMsgType === 'error' ? 'error' : ''}>{workflowMsg}</p>}
      </div>
    </div>
  )
}
