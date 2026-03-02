import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // <-- ADD THIS LINE
import api from '../api';

const ProjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [eda, setEda] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // NEW: Split state so each tab remembers its own data
  const [analysisData, setAnalysisData] = useState({ insight: null, tools: null });
  const [modelData, setModelData] = useState({ insight: null, tools: null });

  useEffect(() => {
    const fetchProjectData = async () => {
      try {
        const projRes = await api.get('/projects/');
        const currentProj = projRes.data.find(p => p.id === parseInt(id));
        if (!currentProj) throw new Error("Project not found or unauthorized.");
        setProject(currentProj);

        const edaRes = await api.get(`/projects/${id}/eda/`);
        setEda(edaRes.data);
      } catch (err) {
        console.error(err);
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchProjectData();
  }, [id]);

  const runEngine = async (mode) => {
    setIsProcessing(true);
    setError(null);

    // Clear only the specific mode's previous data before running
    if (mode === 'analysis') setAnalysisData({ insight: null, tools: null });
    if (mode === 'model') setModelData({ insight: null, tools: null });

    try {
      const response = await api.post(`/projects/${id}/analyze`, { mode: mode });
      
      // Save data to the correct state bucket
      if (mode === 'analysis') {
        setAnalysisData({ insight: response.data.ai_insight, tools: response.data.tool_results });
      } else if (mode === 'model') {
        setModelData({ insight: response.data.ai_insight, tools: response.data.tool_results });
      }
      
      setActiveTab(mode);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || `Failed to execute ${mode} pipeline.`);
      setActiveTab(mode);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async (fileType) => {
    try {
      const response = await api.get(`/projects/${id}/download/${fileType}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${project.name.replace(/\s+/g, '_')}_${fileType}.${fileType === 'model' ? 'pkl' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("File not found. Ensure you have run the required pipeline first.");
    }
  };

  const handleDelete = async () => {
    const isConfirmed = window.confirm("Are you sure you want to permanently delete this project? This will destroy the database record, the raw CSV, and any trained models.");
    if (!isConfirmed) return;

    try {
      await api.delete(`/projects/${id}`);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      alert("Failed to delete project. Check the console for details.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-black"></div>
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex flex-col items-center justify-center p-6">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-red-200 max-w-md w-full text-center">
          <div className="h-12 w-12 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Error Loading Project</h2>
          <p className="text-sm text-gray-500 mb-6">{error}</p>
          <button onClick={() => navigate('/dashboard')} className="w-full bg-black text-white font-bold py-3 rounded-xl cursor-pointer">Return to Workspace</button>
        </div>
      </div>
    );
  }

  // Determine which data to show based on the active tab
  const currentDisplayData = activeTab === 'analysis' ? analysisData : modelData;

  return (
    <div className="min-h-screen bg-[#F5F5F7] font-sans text-[#1D1D1F] flex flex-col">
      
      {/* TOP HEADER */}
      <header className="bg-white border-b border-[#E5E5EA] px-8 py-5 flex justify-between items-center sticky top-0 z-20">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
          </button>
          <div>
            <h1 className="text-xl font-bold tracking-tight">{project.name}</h1>
            <p className="text-xs text-gray-500 font-medium">Target: <span className="text-indigo-600 font-bold">{project.target_variable || 'Unsupervised'}</span></p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className="px-3 py-1 bg-[#F5F5F7] border border-[#E5E5EA] text-xs font-bold rounded-lg text-gray-600">
            {eda?.summary?.total_rows?.toLocaleString() || 0} Rows
          </span>
          <span className="px-3 py-1 bg-[#F5F5F7] border border-[#E5E5EA] text-xs font-bold rounded-lg text-gray-600">
            {eda?.summary?.columns?.length || 0} Features
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN: Controls & Context */}
        <div className="lg:col-span-4 space-y-6">
          
          <div className="bg-white rounded-2xl p-6 border border-[#E5E5EA] shadow-sm">
            <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Autonomous Pipeline</h2>
            
            <button 
              onClick={() => runEngine('analysis')}
              disabled={isProcessing}
              className="w-full mb-3 flex items-center justify-between bg-[#F5F5F7] hover:bg-[#E5E5EA] border border-transparent hover:border-black text-[#1D1D1F] font-semibold py-3 px-4 rounded-xl transition-all disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
            >
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                <span>Run Data Engineering</span>
              </div>
              {isProcessing && activeTab === 'analysis' && <span className="animate-ping h-2 w-2 rounded-full bg-black"></span>}
            </button>

            <button 
              onClick={() => runEngine('model')}
              disabled={isProcessing || !project.target_variable}
              className="w-full flex items-center justify-between bg-black hover:bg-gray-800 text-white font-semibold py-3 px-4 rounded-xl transition-all disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed shadow-sm"
              title={!project.target_variable ? "Requires target variable" : ""}
            >
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                <span>Train ML Models</span>
              </div>
              {isProcessing && activeTab === 'model' && <span className="animate-ping h-2 w-2 rounded-full bg-white"></span>}
            </button>
            {!project.target_variable && (
              <p className="text-xs text-red-500 mt-2 font-medium text-center">Set a target variable to enable modeling.</p>
            )}
          </div>

          <div className="bg-white rounded-2xl p-6 border border-[#E5E5EA] shadow-sm">
            <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Context</h2>
            <div className="mb-4">
              <span className="text-xs text-gray-400 font-bold uppercase">Problem Statement</span>
              <p className="text-sm font-medium mt-1">{project.problem_statement}</p>
            </div>
            <div>
              <span className="text-xs text-gray-400 font-bold uppercase">Dataset Description</span>
              <p className="text-sm font-medium mt-1">{project.dataset_context}</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-[#E5E5EA] shadow-sm">
            <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Export Assets</h2>
            <div className="space-y-2">
              <button onClick={() => handleDownload('engineered')} className="w-full text-left text-sm font-semibold text-gray-700 hover:text-black py-2 px-3 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer">
                ↓ Download Cleaned Dataset (.csv)
              </button>
              <button onClick={() => handleDownload('model')} className="w-full text-left text-sm font-semibold text-gray-700 hover:text-black py-2 px-3 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer">
                ↓ Download Best Model (.pkl)
              </button>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-white rounded-2xl p-6 border border-red-200 shadow-sm mt-6">
            <h2 className="text-sm font-bold text-red-600 uppercase tracking-wider mb-4">Danger Zone</h2>
            <button 
              onClick={handleDelete} 
              className="w-full flex items-center space-x-2 text-sm font-semibold text-red-600 hover:text-white py-2.5 px-3 hover:bg-red-600 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-red-700"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
              <span>Permanently Delete Project</span>
            </button>
          </div>

        </div>

        {/* RIGHT COLUMN: Output Terminal */}
        <div className="lg:col-span-8 flex flex-col min-h-125">
          
          <div className="flex space-x-1 bg-[#E5E5EA] p-1 rounded-t-2xl w-fit">
            <button onClick={() => setActiveTab('overview')} className={`px-4 py-1.5 text-sm font-bold rounded-lg transition-all cursor-pointer ${activeTab === 'overview' ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-black'}`}>Data Overview</button>
            <button onClick={() => setActiveTab('analysis')} className={`px-4 py-1.5 text-sm font-bold rounded-lg transition-all cursor-pointer ${activeTab === 'analysis' ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-black'}`}>Engineering Log</button>
            <button onClick={() => setActiveTab('model')} className={`px-4 py-1.5 text-sm font-bold rounded-lg transition-all cursor-pointer ${activeTab === 'model' ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-black'}`}>Model Insights</button>
          </div>

          <div className="flex-1 bg-white border border-[#E5E5EA] rounded-tr-2xl rounded-b-2xl p-6 md:p-8 shadow-sm overflow-auto">
            
            {error && (
              <div className="mb-6 p-4 bg-red-50 text-red-700 text-sm font-medium rounded-xl border border-red-100">
                {error}
              </div>
            )}

            {isProcessing ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4 py-20">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
                <p className="font-semibold text-sm animate-pulse">Aletta is executing pipeline operations...</p>
              </div>
            ) : (
              <>
                {/* TAB 1: OVERVIEW */}
                {activeTab === 'overview' && eda && (
                  <div>
                    <h3 className="text-lg font-bold mb-4">Raw Data Snapshot</h3>
                    <div className="overflow-x-auto border border-[#E5E5EA] rounded-xl mb-6">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-[#F5F5F7] border-b border-[#E5E5EA]">
                          <tr>
                            {eda.summary.columns.slice(0, 8).map(col => (
                              <th key={col} className="p-3 font-semibold text-gray-600 truncate max-w-37.5">{col}</th>
                            ))}
                            {eda.summary.columns.length > 8 && <th className="p-3 font-semibold text-gray-600">...</th>}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#F5F5F7]">
                          {eda.sample.map((row, i) => (
                            <tr key={i} className="hover:bg-gray-50">
                              {eda.summary.columns.slice(0, 8).map(col => (
                                <td key={col} className="p-3 truncate max-w-37.5 text-gray-800">{String(row[col])}</td>
                              ))}
                              {eda.summary.columns.length > 8 && <td className="p-3 text-gray-400">...</td>}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    <h3 className="text-lg font-bold mb-4">Missing Values</h3>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(eda.summary.missing_values).map(([col, count]) => (
                        count > 0 && (
                          <span key={col} className="px-3 py-1.5 bg-red-50 border border-red-100 text-red-700 text-xs font-bold rounded-lg">
                            {col}: {count} missing
                          </span>
                        )
                      ))}
                      {Object.values(eda.summary.missing_values).every(v => v === 0) && (
                        <span className="text-sm font-medium text-green-600">Dataset is perfectly clean. No missing values detected.</span>
                      )}
                    </div>
                  </div>
                )}

                {/* TAB 2 & 3: AI INSIGHTS & TOOL LOGS */}
                {(activeTab === 'analysis' || activeTab === 'model') && (
                  <div className="space-y-8">
                    <div>
                      <div className="flex items-center space-x-2 mb-3">
                        <div className="h-6 w-6 bg-black rounded-md flex items-center justify-center">
                            <span className="text-white text-[8px] font-extrabold tracking-tighter">ADS</span>
                        </div>
                        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Aletta Intelligence</h3>
                      </div>
                      
                      {currentDisplayData.insight ? (
                        <div className="text-sm text-[#1D1D1F] leading-relaxed markdown-body space-y-3">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              p: ({node, ...props}) => <p className="mb-3" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-bold text-black" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                              li: ({node, ...props}) => <li className="pl-1" {...props} />,
                              // NEW: Table Parsing and Styling
                              table: ({node, ...props}) => (
                                <div className="overflow-x-auto mb-4 border border-[#E5E5EA] rounded-xl shadow-sm">
                                  <table className="min-w-full text-sm text-left divide-y divide-[#E5E5EA]" {...props} />
                                </div>
                              ),
                              thead: ({node, ...props}) => <thead className="bg-[#F5F5F7] text-gray-600 font-semibold" {...props} />,
                              tbody: ({node, ...props}) => <tbody className="divide-y divide-[#F5F5F7] text-gray-800" {...props} />,
                              th: ({node, ...props}) => <th className="px-4 py-3" {...props} />,
                              td: ({node, ...props}) => <td className="px-4 py-3" {...props} />,
                            }}
                          >
                            {currentDisplayData.insight}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400 italic font-medium">Pipeline has not been executed yet. Click a Run button on the left to begin.</p>
                      )}
                    </div>

                    {currentDisplayData.tools && (
                      <div className="pt-6 border-t border-[#E5E5EA] space-y-8">
                        
                        {/* NEW: Engineered Data Snapshot */}
                        {currentDisplayData.tools.engineered_sample && currentDisplayData.tools.engineered_sample.length > 0 && (
                          <div>
                            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Engineered Data Snapshot</h3>
                            <div className="overflow-x-auto border border-[#E5E5EA] rounded-xl shadow-sm">
                              <table className="w-full text-left text-sm">
                                <thead className="bg-[#F5F5F7] border-b border-[#E5E5EA]">
                                  <tr>
                                    {Object.keys(currentDisplayData.tools.engineered_sample[0]).slice(0, 8).map(col => (
                                      <th key={col} className="p-3 font-semibold text-gray-600 truncate max-w-37.5">{col}</th>
                                    ))}
                                    {Object.keys(currentDisplayData.tools.engineered_sample[0]).length > 8 && <th className="p-3 font-semibold text-gray-600">...</th>}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-[#F5F5F7]">
                                  {currentDisplayData.tools.engineered_sample.map((row, i) => (
                                    <tr key={i} className="hover:bg-gray-50">
                                      {Object.keys(row).slice(0, 8).map(col => (
                                        <td key={col} className="p-3 truncate max-w-37.5 text-gray-800">
                                          {typeof row[col] === 'number' ? Number(row[col]).toFixed(4).replace(/\.?0+$/, '') : String(row[col])}
                                        </td>
                                      ))}
                                      {Object.keys(row).length > 8 && <td className="p-3 text-gray-400">...</td>}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Raw JSON System Log */}
                        <div>
                          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">System Execution Log</h3>
                          <div className="bg-[#1D1D1F] rounded-xl p-4 overflow-x-auto shadow-sm">
                            <pre className="text-xs text-green-400 font-mono">
                              {JSON.stringify(currentDisplayData.tools, null, 2)}
                            </pre>
                          </div>
                        </div>

                      </div>
                    )}
                  </div>
                )}
              </>
            )}

          </div>
        </div>
      </main>
    </div>
  );
};

export default ProjectDetail;