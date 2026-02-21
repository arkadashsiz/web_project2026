import { useEffect, useState } from 'react'
import api from '../api/client'

export default function BoardPage() {
  const [boards, setBoards] = useState([])

  useEffect(() => {
    api.get('/investigation/boards/').then((res) => setBoards(res.data.results || []))
  }, [])

  return (
    <div className="panel">
      <h3>Detective Boards</h3>
      <p>Nodes and edges are managed through API endpoints for drag-and-drop UIs.</p>
      <ul className="list">
        {boards.map((b) => <li key={b.id}>Board #{b.id} - Case #{b.case} - Nodes: {b.nodes.length}</li>)}
      </ul>
    </div>
  )
}
