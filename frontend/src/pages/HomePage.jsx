import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <div className="home-hero">
      <h2>Modern Case Management for Police Operations</h2>
      <p>
        This system digitizes complaint handling, crime scene reporting, evidence tracking,
        suspect investigation, court workflow, and reward processing.
      </p>
      <div className="home-actions">
        <Link className="btn-link" to="/login">Login</Link>
        <Link className="btn-link secondary" to="/register">Register</Link>
      </div>
      <div className="hero-grid">
        <article>
          <h3>Role-Based Access</h3>
          <p>Dynamic roles are managed by the superuser without code changes.</p>
        </article>
        <article>
          <h3>End-to-End Case Flow</h3>
          <p>From complaint intake to verdict and payment workflows.</p>
        </article>
        <article>
          <h3>Detective Board</h3>
          <p>Link evidence and suspects visually with notes and graph edges.</p>
        </article>
      </div>
    </div>
  )
}
