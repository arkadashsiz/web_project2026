import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../pages/LoginPage'
import { AuthProvider } from '../context/AuthContext'

test('renders login form', () => {
  render(<BrowserRouter><AuthProvider><LoginPage /></AuthProvider></BrowserRouter>)
  expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
})
