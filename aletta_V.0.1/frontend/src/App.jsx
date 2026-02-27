import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

const PlaceholderAuth = () => <div className="p-10 text-2xl font-bold text-blue-600">Aletta Auth Screen</div>;
const PlaceholderDashboard = () => <div className="p-10 text-2xl font-bold text-green-600">Aletta Dashboard</div>;

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-900">
        <Routes>
          <Route path="/auth" element={<PlaceholderAuth />} />
          <Route path="/dashboard" element={<PlaceholderDashboard />} />
          <Route path="*" element={<Navigate to="/auth" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;