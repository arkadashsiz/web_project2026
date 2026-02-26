import { render, screen } from '@testing-library/react'
import DashboardPage from '../pages/DashboardPage'

test('shows loading before stats', () => {
  render(<DashboardPage />)
  expect(screen.getByText(/Loading dashboard/i)).toBeInTheDocument()
})
