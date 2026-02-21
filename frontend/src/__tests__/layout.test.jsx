import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Layout from '../components/Layout'
import { AuthProvider } from '../context/AuthContext'

test('renders app shell brand', () => {
  render(<BrowserRouter><AuthProvider><Layout><div>Child</div></Layout></AuthProvider></BrowserRouter>)
  expect(screen.getByText(/City Police/i)).toBeInTheDocument()
})
