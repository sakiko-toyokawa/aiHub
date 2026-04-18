import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import SummaryDetail from './pages/SummaryDetail'
import Settings from './pages/Settings'
import Favorites from './pages/Favorites'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="favorites" element={<Favorites />} />
        <Route path="summary/:id" element={<SummaryDetail />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
