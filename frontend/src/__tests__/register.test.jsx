import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import RegisterPage from '../pages/RegisterPage'
import { AuthProvider } from '../context/AuthContext'

test('renders register form', () => {
  render(<BrowserRouter><AuthProvider><RegisterPage /></AuthProvider></BrowserRouter>)
  expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
})
