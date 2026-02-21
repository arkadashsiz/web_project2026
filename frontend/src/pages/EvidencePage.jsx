import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function EvidencePage() {
  const { user } = useAuth()
  const roles = (user?.roles || []).map((r) => r.toLowerCase())
  const isForensic = user?.is_superuser || roles.includes('coroner') || roles.includes('forensic')

  const [mode, setMode] = useState('witness')
  const [message, setMessage] = useState('')
  const [bioList, setBioList] = useState([])
  const [evidenceList, setEvidenceList] = useState([])

  const [witness, setWitness] = useState({
    case: '', title: '', description: '', transcript: '', media_items: '[{"type":"image","url":""}]', media_url: '',
  })
  const [biological, setBiological] = useState({
    case: '', title: '', description: '', image_urls: '["https://example.com/image1.jpg"]',
  })
  const [vehicle, setVehicle] = useState({
    case: '', title: '', description: '', model_name: '', color: '', plate_number: '', serial_number: '',
  })
  const [identification, setIdentification] = useState({
    case: '', title: '', description: '', owner_full_name: '', metadata: '{"id_number":""}',
  })
  const [other, setOther] = useState({ case: '', title: '', description: '' })
  const [bioResult, setBioResult] = useState({
    evidence_id: '',
    forensic_result: '',
    identity_db_result: '',
  })

  const parseJson = (value, fallback) => {
    try {
      return JSON.parse(value)
    } catch {
      return fallback
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      if (mode === 'witness') {
        await api.post('/evidence/witness/', {
          ...witness,
          case: Number(witness.case),
          media_items: parseJson(witness.media_items, []),
        })
        await loadEvidenceByMode('witness')
      }
      if (mode === 'biological') {
        await api.post('/evidence/biological/', {
          ...biological,
          case: Number(biological.case),
          image_urls: parseJson(biological.image_urls, []),
        })
        await loadBiological()
        await loadEvidenceByMode('biological')
      }
      if (mode === 'vehicle') {
        await api.post('/evidence/vehicle/', {
          ...vehicle,
          case: Number(vehicle.case),
        })
        await loadEvidenceByMode('vehicle')
      }
      if (mode === 'identification') {
        await api.post('/evidence/identification/', {
          ...identification,
          case: Number(identification.case),
          metadata: parseJson(identification.metadata, {}),
        })
        await loadEvidenceByMode('identification')
      }
      if (mode === 'other') {
        await api.post('/evidence/other/', {
          ...other,
          case: Number(other.case),
        })
        await loadEvidenceByMode('other')
      }
      setMessage('Evidence saved successfully.')
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (detail) {
        setMessage(`Error: ${detail}`)
      } else {
        setMessage(`Error: ${JSON.stringify(err?.response?.data || 'invalid input')}`)
      }
    }
  }

  const updateBioResults = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      await api.post(`/evidence/biological/${bioResult.evidence_id}/update_results/`, {
        forensic_result: bioResult.forensic_result,
        identity_db_result: bioResult.identity_db_result,
      })
      await loadBiological()
      setMessage('Biological evidence results updated successfully.')
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (detail) {
        setMessage(`Error: ${detail}`)
      } else {
        setMessage(`Error: ${JSON.stringify(err?.response?.data || 'invalid input')}`)
      }
    }
  }

  const loadBiological = async () => {
    try {
      const res = await api.get('/evidence/biological/')
      setBioList(res.data.results || [])
    } catch {
      setBioList([])
    }
  }

  const loadEvidenceByMode = async (targetMode = mode) => {
    const endpointMap = {
      witness: '/evidence/witness/',
      biological: '/evidence/biological/',
      vehicle: '/evidence/vehicle/',
      identification: '/evidence/identification/',
      other: '/evidence/other/',
    }
    try {
      const res = await api.get(endpointMap[targetMode])
      setEvidenceList(res.data.results || [])
    } catch {
      setEvidenceList([])
    }
  }

  useEffect(() => {
    loadEvidenceByMode(mode)
    if (mode === 'biological') {
      loadBiological()
    }
  }, [mode])

  return (
    <div className="panel">
      <h3>Register & Review Evidence</h3>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button type="button" className={mode === 'witness' ? '' : 'btn-link secondary'} onClick={() => setMode('witness')}>Witness / Local</button>
        <button type="button" className={mode === 'biological' ? '' : 'btn-link secondary'} onClick={() => setMode('biological')}>Biological / Medical</button>
        <button type="button" className={mode === 'vehicle' ? '' : 'btn-link secondary'} onClick={() => setMode('vehicle')}>Vehicle</button>
        <button type="button" className={mode === 'identification' ? '' : 'btn-link secondary'} onClick={() => setMode('identification')}>Identification</button>
        <button type="button" className={mode === 'other' ? '' : 'btn-link secondary'} onClick={() => setMode('other')}>Other</button>
      </div>

      <form onSubmit={submit} style={{ display: 'grid', gap: 10 }}>
        {mode === 'witness' && (
          <>
            <input placeholder="Case ID" value={witness.case} onChange={(e) => setWitness({ ...witness, case: e.target.value })} />
            <input placeholder="Title" value={witness.title} onChange={(e) => setWitness({ ...witness, title: e.target.value })} />
            <textarea placeholder="Description" value={witness.description} onChange={(e) => setWitness({ ...witness, description: e.target.value })} />
            <textarea placeholder="Transcript" value={witness.transcript} onChange={(e) => setWitness({ ...witness, transcript: e.target.value })} />
            <input placeholder="Single media URL (optional)" value={witness.media_url} onChange={(e) => setWitness({ ...witness, media_url: e.target.value })} />
            <textarea placeholder='media_items JSON (e.g. [{"type":"image","url":"https://..."}])' value={witness.media_items} onChange={(e) => setWitness({ ...witness, media_items: e.target.value })} />
          </>
        )}

        {mode === 'biological' && (
          <>
            <input placeholder="Case ID" value={biological.case} onChange={(e) => setBiological({ ...biological, case: e.target.value })} />
            <input placeholder="Title" value={biological.title} onChange={(e) => setBiological({ ...biological, title: e.target.value })} />
            <textarea placeholder="Description" value={biological.description} onChange={(e) => setBiological({ ...biological, description: e.target.value })} />
            <textarea placeholder='image_urls JSON (required, e.g. ["https://..."])' value={biological.image_urls} onChange={(e) => setBiological({ ...biological, image_urls: e.target.value })} />
          </>
        )}

        {mode === 'vehicle' && (
          <>
            <input placeholder="Case ID" value={vehicle.case} onChange={(e) => setVehicle({ ...vehicle, case: e.target.value })} />
            <input placeholder="Title" value={vehicle.title} onChange={(e) => setVehicle({ ...vehicle, title: e.target.value })} />
            <textarea placeholder="Description" value={vehicle.description} onChange={(e) => setVehicle({ ...vehicle, description: e.target.value })} />
            <input placeholder="Model" value={vehicle.model_name} onChange={(e) => setVehicle({ ...vehicle, model_name: e.target.value })} />
            <input placeholder="Color" value={vehicle.color} onChange={(e) => setVehicle({ ...vehicle, color: e.target.value })} />
            <input placeholder="Plate number (or leave empty)" value={vehicle.plate_number} onChange={(e) => setVehicle({ ...vehicle, plate_number: e.target.value })} />
            <input placeholder="Serial number (or leave empty)" value={vehicle.serial_number} onChange={(e) => setVehicle({ ...vehicle, serial_number: e.target.value })} />
          </>
        )}

        {mode === 'identification' && (
          <>
            <input placeholder="Case ID" value={identification.case} onChange={(e) => setIdentification({ ...identification, case: e.target.value })} />
            <input placeholder="Title" value={identification.title} onChange={(e) => setIdentification({ ...identification, title: e.target.value })} />
            <textarea placeholder="Description" value={identification.description} onChange={(e) => setIdentification({ ...identification, description: e.target.value })} />
            <input placeholder="Owner full name" value={identification.owner_full_name} onChange={(e) => setIdentification({ ...identification, owner_full_name: e.target.value })} />
            <textarea placeholder='metadata JSON (key-value, can be {})' value={identification.metadata} onChange={(e) => setIdentification({ ...identification, metadata: e.target.value })} />
          </>
        )}

        {mode === 'other' && (
          <>
            <input placeholder="Case ID" value={other.case} onChange={(e) => setOther({ ...other, case: e.target.value })} />
            <input placeholder="Title" value={other.title} onChange={(e) => setOther({ ...other, title: e.target.value })} />
            <textarea placeholder="Description" value={other.description} onChange={(e) => setOther({ ...other, description: e.target.value })} />
          </>
        )}

        <button type="submit">Save Evidence</button>
      </form>

      {mode === 'biological' && (
        <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginTop: 12 }}>
          <h4>Biological Evidence IDs</h4>
          {bioList.length === 0 && <p>No items loaded. Click refresh.</p>}
          <ul className="list">
            {bioList.map((b) => (
              <li key={b.id}>
                ID:{b.id} | Case:{b.case} | {b.title}
                {b.forensic_result ? ' | forensic result: filled' : ' | forensic result: empty'}
                {b.identity_db_result ? ' | identity DB: filled' : ' | identity DB: empty'}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ border: '1px solid #d8deea', borderRadius: 8, padding: 10, marginTop: 12 }}>
        <h4>Evidence Review List ({mode})</h4>
        <ul className="list">
          {evidenceList.map((row) => (
            <li key={row.id}>
              ID:{row.id} | Case:{row.case} | Title:{row.title}
              <div>description: {row.description}</div>
              <div>recorded_at: {row.recorded_at}</div>
              <div>recorded_by: {row.recorded_by}</div>
              {mode === 'biological' && (
                <div>
                  forensic_result: {row.forensic_result || '-'} | identity_db_result: {row.identity_db_result || '-'}
                </div>
              )}
            </li>
          ))}
          {evidenceList.length === 0 && <li>No evidence records in this category.</li>}
        </ul>
      </div>

      {mode === 'biological' && isForensic && (
        <form onSubmit={updateBioResults} style={{ display: 'grid', gap: 10, marginTop: 12 }}>
          <h4>Update Biological Results Later (Forensic / Coroner)</h4>
          <input
            placeholder="Biological Evidence ID"
            value={bioResult.evidence_id}
            onChange={(e) => setBioResult({ ...bioResult, evidence_id: e.target.value })}
          />
          <textarea
            placeholder="Forensic result"
            value={bioResult.forensic_result}
            onChange={(e) => setBioResult({ ...bioResult, forensic_result: e.target.value })}
          />
          <textarea
            placeholder="Identity DB result"
            value={bioResult.identity_db_result}
            onChange={(e) => setBioResult({ ...bioResult, identity_db_result: e.target.value })}
          />
          <button type="submit">Update Results</button>
        </form>
      )}

      {message && <p className={message.startsWith('Error:') ? 'error' : ''}>{message}</p>}
    </div>
  )
}
