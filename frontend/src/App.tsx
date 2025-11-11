import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ListPage from './pages/ListPage'
import ShoppingMode from './pages/ShoppingMode'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/list/:listId" element={<ListPage />} />
          <Route path="/list/:listId/shop" element={<ShoppingMode />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
