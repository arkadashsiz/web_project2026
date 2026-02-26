import { render, screen } from '@testing-library/react'
import HomePage from '../pages/HomePage'

test('renders home intro', () => {
  render(<HomePage />)
  expect(screen.getByText(/Modern Case Management/i)).toBeInTheDocument()
})
