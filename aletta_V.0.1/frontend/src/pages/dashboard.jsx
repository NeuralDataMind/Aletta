import { useEffect, useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await api.get('/projects/');
        setProjects(response.data);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          navigate('/auth');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [navigate]);

  return (
    // Apple-style ultra-light gray background
    <div className="flex h-screen bg-[#F5F5F7] font-sans text-[#1D1D1F] overflow-hidden selection:bg-black selection:text-white">
      
      {/* --- SIDEBAR (Perplexity/Apple Minimalist) --- */}
      <aside className="w-65 flex flex-col pt-6 pb-4 px-4">
        {/* Logo Area */}
        <div className="flex items-center px-2 mb-8">
          <div className="h-8 w-8 bg-black rounded-lg flex items-center justify-center mr-3">
            <span className="text-white font-bold text-lg leading-none tracking-tighter">A</span>
          </div>
          <span className="text-xl font-semibold tracking-tight">Aletta</span>
        </div>

        {/* The Big "New" Button - High Contrast */}
        <div className="mb-6">
          <button 
            onClick={() => navigate('/projects/new')}
            className="w-full flex items-center justify-center space-x-2 bg-white hover:bg-gray-50 text-black border border-[#E5E5EA] shadow-sm rounded-xl px-4 py-3 transition-all cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
            <span className="font-semibold text-sm">New Project</span>
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 space-y-1.5">
          {/* Active Item - Black Pill */}
          <button className="w-full flex items-center space-x-3 px-3 py-2 bg-black text-white rounded-lg font-medium transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
            <span className="text-sm">All Projects</span>
          </button>
          
          {/* Local Workspace */}
          <button className="w-full flex items-center space-x-3 px-3 py-2 text-gray-600 hover:bg-[#E5E5EA] hover:text-black rounded-lg font-medium transition-colors cursor-pointer">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
            <span className="text-sm">Local Workspace</span>
          </button>

          {/* Cloud Sync */}
          <button className="w-full flex items-center space-x-3 px-3 py-2 text-gray-600 hover:bg-[#E5E5EA] hover:text-black rounded-lg font-medium transition-colors cursor-pointer">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path></svg>
            <span className="text-sm">Cloud Sync</span>
          </button>

          {/* Trash */}
          <button className="w-full flex items-center space-x-3 px-3 py-2 text-gray-600 hover:bg-[#E5E5EA] hover:text-black rounded-lg font-medium transition-colors cursor-pointer mt-4">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            <span className="text-sm">Trash</span>
          </button>
        </nav>
      </aside>

      {/* --- MAIN CONTENT WINDOW --- */}
      <div className="flex-1 flex flex-col min-w-0 pr-4 pb-4 pt-4">
        
        {/* TOP SEARCH BAR & PROFILE */}
        <header className="flex justify-between items-center mb-6 px-2">
          {/* Search Bar - Perplexity Style */}
          <div className="flex-1 max-w-150 bg-white border border-[#E5E5EA] focus-within:border-black focus-within:ring-1 focus-within:ring-black transition-all rounded-full flex items-center px-4 py-2.5 shadow-sm">
            <svg className="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            <input 
              type="text" 
              placeholder="Search datasets, models, or projects..." 
              className="bg-transparent border-none outline-none w-full text-sm text-[#1D1D1F] placeholder-gray-400"
            />
          </div>

          {/* Profile Dropdown */}
          <div className="flex items-center ml-6 relative">
            <div 
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="h-9 w-9 bg-black rounded-full flex items-center justify-center text-white text-xs font-bold cursor-pointer hover:bg-gray-800 transition-colors shadow-sm"
            >
              MR
            </div>

            {/* Popup Panel */}
            {isProfileOpen && (
              <div className="absolute top-12 right-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-[#E5E5EA] py-6 px-6 z-50 flex flex-col items-center">
                <div className="h-16 w-16 bg-black rounded-full flex items-center justify-center text-white text-xl font-bold mb-3">
                  MR
                </div>
                <h3 className="text-lg font-semibold text-[#1D1D1F]">Mallikarjun Reddy</h3>
                <span className="text-xs text-gray-500 font-medium mb-6">Data Scientist</span>
                
                <button 
                  onClick={() => { localStorage.removeItem('token'); navigate('/auth'); }}
                  className="w-full py-2.5 bg-[#F5F5F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-semibold text-sm rounded-xl transition-colors"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </header>

        {/* --- WHITE CONTENT CANVAS --- */}
        <main className="flex-1 bg-white rounded-2xl shadow-sm flex flex-col overflow-hidden border border-[#E5E5EA] relative">
          
          {/* Canvas Header */}
          <div className="px-8 py-5 border-b border-[#E5E5EA] flex justify-between items-center">
            <h2 className="text-xl font-semibold text-[#1D1D1F]">All Projects</h2>
            
            {/* View Toggle - Apple Segmented Control Style */}
            <div className="flex bg-[#F5F5F7] p-1 rounded-lg border border-[#E5E5EA]">
              <button 
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-black'}`}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M4 4h4v4H4V4zm6 0h4v4h-4V4zM4 10h4v4H4v-4zm6 0h4v4h-4v-4zM4 16h4v4H4v-4zm6 0h4v4h-4v-4zm6-12h4v4h-4V4zm0 6h4v4h-4v-4zm0 6h4v4h-4v-4z"></path></svg>
              </button>
              <button 
                onClick={() => setViewMode('table')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'table' ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-black'}`}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M3 4h18v2H3V4zm0 7h18v2H3v-2zm0 7h18v2H3v-2z"></path></svg>
              </button>
            </div>
          </div>

          {/* Canvas Scrollable Content */}
          <div className="flex-1 overflow-auto p-8">
            {isProfileOpen && (
              <div className="absolute inset-0 z-40" onClick={() => setIsProfileOpen(false)}></div>
            )}

            {loading ? (
              <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              </div>
            ) : projects.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center max-w-sm mx-auto z-10 relative">
                <div className="mb-4 h-16 w-16 bg-[#F5F5F7] rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
                </div>
                <h3 className="text-lg font-semibold text-[#1D1D1F] mb-2">No Active Projects</h3>
                <p className="text-gray-500 text-sm">Initialize a new project to upload data and begin training models.</p>
              </div>
            ) : viewMode === 'grid' ? (
              // GRID VIEW
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 relative z-10">
                {projects.map((project) => (
                  <div 
                    key={project.id}
                    onClick={() => navigate(`/projects/${project.id}`)}
                    className="flex flex-col bg-white rounded-xl p-5 cursor-pointer transition-all border border-[#E5E5EA] hover:border-black hover:shadow-md group"
                  >
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="p-2 bg-[#F5F5F7] rounded-lg group-hover:bg-black group-hover:text-white transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                      </div>
                      <span className="font-semibold text-[#1D1D1F] truncate">{project.name}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-auto flex justify-between items-center border-t border-[#F5F5F7] pt-3">
                      <span className="font-medium px-2 py-1 bg-[#F5F5F7] rounded-md">Dataset</span>
                      <span className="truncate ml-2 text-gray-400">Target: {project.target_variable || 'None'}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // TABLE VIEW
              <table className="w-full text-left text-sm text-[#1D1D1F] relative z-10">
                <thead className="border-b border-[#E5E5EA] text-gray-500 font-medium">
                  <tr>
                    <th className="pb-3 font-semibold">Project Name</th>
                    <th className="pb-3 font-semibold">Owner</th>
                    <th className="pb-3 font-semibold">Target Variable</th>
                    <th className="pb-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((project) => (
                    <tr 
                      key={project.id}
                      onClick={() => navigate(`/projects/${project.id}`)}
                      className="border-b border-[#F5F5F7] hover:bg-[#F5F5F7] cursor-pointer transition-colors"
                    >
                      <td className="py-4 flex items-center space-x-3">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                        <span className="font-semibold">{project.name}</span>
                      </td>
                      <td className="py-4">
                        <div className="flex items-center space-x-2">
                          <div className="h-5 w-5 rounded-full bg-black text-white text-[9px] font-bold flex items-center justify-center">MR</div>
                          <span className="text-gray-600">You</span>
                        </div>
                      </td>
                      <td className="py-4 text-gray-600">{project.target_variable || 'Not set'}</td>
                      <td className="py-4">
                        <span className="px-2 py-1 bg-[#E5E5EA] text-xs font-semibold rounded-md">Active</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;