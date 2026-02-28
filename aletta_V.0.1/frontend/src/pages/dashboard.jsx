import { useEffect, useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await api.get('/projects/');
        setProjects(response.data);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
        // If the token is invalid or expired, kick them back to login
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          navigate('/');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Aletta Workspace</h1>
          <p className="text-gray-500 italic">Welcome back, Data Scientist.</p>
        </div>
        <button 
          onClick={() => { localStorage.removeItem('token'); navigate('/'); }}
          className="px-4 py-2 text-sm font-semibold text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
        >
          Logout
        </button>
      </header>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* New Project Card */}
          <div 
            onClick={() => navigate('/projects/new')}
            className="border-2 border-dashed border-gray-300 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer hover:border-gray-900 transition-colors group"
          >
            <span className="text-4xl mb-4 group-hover:scale-110 transition-transform">+</span>
            <p className="font-bold text-gray-600 group-hover:text-gray-900">Initialize New Project</p>
          </div>

          {/* Project List */}
          {projects.map((project) => (
            <div 
              key={project.id} 
              className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/projects/${project.id}`)}
            >
              <h3 className="text-xl font-bold mb-2">{project.name}</h3>
              <p className="text-sm text-gray-500 line-clamp-2 mb-4">{project.problem_statement}</p>
              <div className="flex items-center text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded w-fit">
                Target: {project.target_variable || 'Not Defined'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;