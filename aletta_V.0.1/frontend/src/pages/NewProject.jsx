import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const NewProject = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    problem_statement: '',
    dataset_context: '',
    target_variable: ''
  });
  
  const [file, setFile] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type !== 'text/csv' && !selectedFile.name.endsWith('.csv')) {
      setError('Strictly CSV files are allowed for Aletta ingestion.');
      setFile(null);
      return;
    }
    setError(null);
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('You must upload a CSV dataset to initialize a project.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Step 1: Create the Project Database Record
      const projectRes = await api.post('/projects/', {
        name: formData.name,
        problem_statement: formData.problem_statement,
        dataset_context: formData.dataset_context,
        target_variable: formData.target_variable || null // Optional field
      });

      const projectId = projectRes.data.id;

      // Step 2: Upload the Physical CSV File
      const uploadData = new FormData();
      uploadData.append('file', file);

      await api.post(`/projects/${projectId}/upload/`, uploadData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Redirect back to dashboard to see the new project
      navigate('/dashboard');
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'An error occurred during pipeline initialization.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] flex flex-col justify-center items-center p-6 font-sans text-[#1D1D1F]">
      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-sm border border-[#E5E5EA] overflow-hidden">
        
        <div className="px-8 pt-8 pb-4 border-b border-[#E5E5EA] flex justify-between items-center bg-[#F8F9FA]">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Initialize Pipeline</h1>
            <p className="text-sm text-gray-500 mt-1">Define your problem statement and upload the raw dataset.</p>
          </div>
          <button 
            onClick={() => navigate('/dashboard')}
            className="h-10 w-10 bg-white border border-[#E5E5EA] rounded-full flex items-center justify-center text-gray-500 hover:text-black transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 text-red-700 text-sm font-semibold rounded-xl border border-red-100">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="col-span-1 md:col-span-2">
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Project Name</label>
              <input 
                type="text" 
                name="name"
                required
                value={formData.name} 
                onChange={handleChange}
                className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-black rounded-xl outline-none transition-all text-sm font-medium"
                placeholder="e.g., Q3 Customer Churn Analysis"
              />
            </div>

            <div className="col-span-1 md:col-span-2">
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Problem Statement</label>
              <textarea 
                name="problem_statement"
                required
                value={formData.problem_statement} 
                onChange={handleChange}
                rows="2"
                className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-black rounded-xl outline-none transition-all text-sm font-medium resize-none"
                placeholder="What exactly are we trying to solve or predict?"
              ></textarea>
            </div>

            <div className="col-span-1">
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Dataset Context</label>
              <input 
                type="text" 
                name="dataset_context"
                required
                value={formData.dataset_context} 
                onChange={handleChange}
                className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-black rounded-xl outline-none transition-all text-sm font-medium"
                placeholder="e.g., 5 years of CRM data"
              />
            </div>

            <div className="col-span-1">
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Target Variable</label>
              <input 
                type="text" 
                name="target_variable"
                value={formData.target_variable} 
                onChange={handleChange}
                className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-black rounded-xl outline-none transition-all text-sm font-medium"
                placeholder="Column to predict (Optional)"
              />
            </div>
          </div>

          <div className="pt-4">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Raw Data Ingestion (CSV)</label>
            <div className="relative flex items-center justify-center w-full">
              <label className={`flex flex-col items-center justify-center w-full h-32 border-2 ${file ? 'border-black bg-gray-50' : 'border-[#E5E5EA] border-dashed hover:bg-[#F5F5F7] hover:border-black'} rounded-xl cursor-pointer transition-all`}>
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  {file ? (
                    <>
                      <svg className="w-8 h-8 text-black mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                      <p className="text-sm font-bold text-[#1D1D1F]">{file.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </>
                  ) : (
                    <>
                      <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                      <p className="mb-1 text-sm font-medium text-gray-600"><span className="font-bold text-black">Click to upload</span> or drag and drop</p>
                      <p className="text-xs text-gray-400">Strictly .CSV files allowed</p>
                    </>
                  )}
                </div>
                <input type="file" className="hidden" accept=".csv" onChange={handleFileChange} />
              </label>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full mt-6 bg-black hover:bg-gray-800 text-white font-bold py-4 px-4 rounded-xl transition-colors flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            ) : 'Upload and Initialize Pipeline'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default NewProject;