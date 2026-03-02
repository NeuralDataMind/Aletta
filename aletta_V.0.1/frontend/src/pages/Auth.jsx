import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', username: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Step 1: If signing up, create the account first
      if (!isLogin) {
        await api.post('/api/auth/register', {
          email: formData.email,
          password: formData.password,
          username: formData.username
        });
      }

      // Step 2: Proceed directly to Login (runs for both returning users AND newly registered users)
      const response = await api.post('/api/auth/login', {
        email: formData.email,
        password: formData.password
      });
      
      // Save token and blast them to the dashboard
      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Authentication failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex font-sans text-[#1D1D1F]">
      
      {/* --- LEFT SIDE: Branding & Color --- */}
      <div className="hidden lg:flex lg:w-1/2 bg-linear-to-br from-indigo-900 via-blue-900 to-black text-white p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-[100px] opacity-40"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-[100px] opacity-40"></div>
        
        <div className="relative z-10">
          <div className="h-12 w-12 bg-white text-black rounded-xl flex items-center justify-center mb-6 shadow-sm">
            <span className="font-extrabold text-lg leading-none tracking-tighter">ADS</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">Aletta Data Engine.</h1>
          <p className="text-lg text-indigo-200 font-medium max-w-md">
            The autonomous workspace for modern data scientists. Upload datasets, engineer features, and train models in seconds.
          </p>
        </div>

        <div className="relative z-10">
          <p className="text-sm font-medium text-indigo-300">© 2026 Aletta Systems. All rights reserved.</p>
        </div>
      </div>

      {/* --- RIGHT SIDE: The Form --- */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center bg-[#F5F5F7] p-8 sm:p-12">
        <div className="w-full max-w-md">
          
          <h2 className="text-3xl font-bold mb-2">
            {isLogin ? 'Sign in to Aletta' : 'Create your account'}
          </h2>
          <p className="text-sm text-gray-500 mb-8 font-medium">
            {isLogin ? 'Welcome back. Enter your details below.' : 'Start analyzing data today.'}
          </p>

          {/* Dummy SSO Buttons */}
          <div className="space-y-3 mb-8">
            <button 
              type="button"
              className="w-full flex items-center justify-center space-x-2 bg-white border border-[#E5E5EA] text-[#1D1D1F] font-semibold py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors shadow-sm cursor-not-allowed opacity-70"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 15.02 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
              <span>Continue with Google</span>
            </button>
            <button 
              type="button"
              className="w-full flex items-center justify-center space-x-2 bg-black text-white font-semibold py-3 px-4 rounded-xl hover:bg-gray-800 transition-colors shadow-sm cursor-not-allowed opacity-70"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.78 1.18-.19 2.24-.86 3.43-.88 1.52-.03 2.69.59 3.44 1.67-3.07 1.76-2.58 5.76.29 6.84-1.14 2.1-2.29 3.63-2.24 4.56zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"></path></svg>
              <span>Continue with Apple</span>
            </button>
          </div>

          <div className="flex items-center mb-8">
            <div className="flex-1 border-t border-gray-300"></div>
            <span className="px-3 text-xs text-gray-500 font-bold uppercase tracking-wide">Or continue with email</span>
            <div className="flex-1 border-t border-gray-300"></div>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-50 text-red-700 text-sm font-medium rounded-lg border border-red-100 text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Full Name</label>
                <input 
                  type="text" 
                  name="username" 
                  required={!isLogin}
                  value={formData.username} 
                  onChange={handleChange} 
                  className="w-full px-4 py-3 bg-white border border-[#E5E5EA] focus:border-black rounded-xl outline-none transition-all text-sm font-medium shadow-sm"
                  placeholder="Mallikarjun Reddy"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email</label>
              <input 
                type="email" 
                name="email" 
                required
                value={formData.email} 
                onChange={handleChange} 
                className="w-full px-4 py-3 bg-white border border-[#E5E5EA] focus:border-black rounded-xl outline-none transition-all text-sm font-medium shadow-sm"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Password</label>
              <input 
                type="password" 
                name="password" 
                required
                value={formData.password} 
                onChange={handleChange} 
                className="w-full px-4 py-3 bg-white border border-[#E5E5EA] focus:border-black rounded-xl outline-none transition-all text-sm font-medium shadow-sm"
                placeholder="••••••••"
              />
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full mt-2 bg-black hover:bg-gray-800 text-white font-bold py-3.5 px-4 rounded-xl transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 shadow-sm"
            >
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          <div className="mt-8 text-center text-sm">
            <span className="text-gray-500 font-medium">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
            </span>
            <button 
              type="button"
              onClick={() => { setIsLogin(!isLogin); setError(''); }}
              className="font-bold text-black hover:text-gray-600 hover:underline cursor-pointer transition-colors focus:outline-none ml-1.5"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default Auth;