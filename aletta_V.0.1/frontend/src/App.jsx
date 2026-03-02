import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './pages/Auth'; // Adjust path if your Auth is located elsewhere
import Dashboard from './pages/dashboard'; // The actual Dashboard file I gave you
import NewProject from './pages/NewProject';
import ProjectDetail from './pages/ProjectDetail';    

// --- The Guard Checkpoint ---
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  
  // If no token exists, immediately kick them to the login screen
  if (!token) {
    return <Navigate to="/auth" replace />;
  }
  
  // If token exists, let them pass
  return children;
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
        <Routes>
          {/* Public Route */}
          <Route path="/auth" element={<Auth />} />

          {/* Protected Dashboard Route */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />

          {/* NewProject Route */}
          <Route
            path="/projects/new"
            element={
              <ProtectedRoute>
                <NewProject />
              </ProtectedRoute>
            }
          />

          {/* Project Details */}
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />

          {/* Catch-all: If they type a random URL, send them to login */}
          <Route path="*" element={<Navigate to="/auth" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;