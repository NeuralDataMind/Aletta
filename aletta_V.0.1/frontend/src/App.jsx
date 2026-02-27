import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './pages/Auth';

const PlaceholderDashboard = () => <div className="p-10 text-2xl font-bold text-green-600">Aletta Dashboard</div>;

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
        <Routes>
          <Route path="/auth" element={<Auth />} />
          <Route path="/dashboard" element={<PlaceholderDashboard />} />
          <Route path="*" element={<Navigate to="/auth" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;