import { useState } from 'react';
import { authAPI } from '../api';
import { useNavigate } from 'react-router-dom';

const Auth = () => {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (isLogin) {
        // Attempt Login
        const response = await authAPI.login({
          email: formData.email,
          password: formData.password
        });
        
        console.log("Login successful!", response.data);
        
        // Save the token to local storage
        if (response.data.access_token) {
          localStorage.setItem('token', response.data.access_token);
        }
        
        // Push the user to the dashboard
        navigate('/dashboard');
        
      } else {
        // Attempt Registration
        const response = await authAPI.register({
          name: formData.name, // Ensure your FastAPI schema expects 'name' if you kept it in the form
          email: formData.email,
          password: formData.password
        });
        
        console.log("Registration successful!", response.data);
        alert("Account created successfully! Please sign in.");
        
        // Switch the UI back to the login screen
        setIsLogin(true);
      }
    } catch (error) {
      // Brutal error handling
      console.error("Auth Failed:", error);
      const errorMsg = error.response?.data?.detail || "An error occurred connecting to the server.";
      alert(`Error: ${errorMsg}`);
    }
  };

  return (
    <div className="h-screen flex font-sans bg-white overflow-hidden relative">
      
      {/* SVG Displacement Map */}
      <svg className="w-0 h-0 absolute pointer-events-none hidden">
        <filter id="liquid-refraction" x="-20%" y="-20%" width="140%" height="140%">
          <feTurbulence type="fractalNoise" baseFrequency="0.004" numOctaves="2" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="30" xChannelSelector="R" yChannelSelector="G" result="displaced" />
          <feGaussianBlur in="displaced" stdDeviation="25" result="blurred" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1.8 0" in="blurred" />
        </filter>
      </svg>

      {/* Left Side */}
      <div className="hidden lg:block lg:w-1/2 relative h-full">
        <img
          src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
          alt="Data Science Network"
          className="absolute inset-0 w-full h-full object-cover"
        />
        
        {/* The Glass Card - TEXT COLOR UPDATED TO GRAY-900 */}
        <div 
          className="absolute bottom-12 left-12 right-12 p-8 rounded-4xl bg-white/30 border border-white/50 shadow-[inset_0_2px_4px_rgba(255,255,255,0.9),0_12px_40px_rgba(0,0,0,0.4)] transition-all duration-500"
          style={{ backdropFilter: 'url(#liquid-refraction) saturate(180%)' }}
        >
          <p className="text-xl font-bold leading-relaxed mb-6 text-gray-900">
            "Aletta makes it easy to analyze vast datasets and build machine learning pipelines. Whether I'm running EDA or predicting outcomes, the speed and clarity are unmatched."
          </p>
          <div className="flex justify-between items-end">
            <div>
              <p className="font-extrabold text-lg text-black">Mallikarjun Reddy Bardipuram</p>
              <p className="text-sm font-bold text-gray-800">Data Science Student</p>
              <p className="text-xs font-bold text-gray-700 uppercase tracking-wider mt-1">ACE Engineering College</p>
            </div>
            <div className="flex space-x-3">
              <button className="cursor-pointer p-2 hover:bg-white/50 bg-white/30 rounded-full transition text-black border border-gray-400 shadow-sm">&larr;</button>
              <button className="cursor-pointer p-2 hover:bg-white/50 bg-white/30 rounded-full transition text-black border border-gray-400 shadow-sm">&rarr;</button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side */}
      <div className="w-full lg:w-1/2 h-full flex flex-col justify-center items-center px-8 sm:px-16 md:px-24 bg-[#FAFAFA]">
        <div className="max-w-md w-full">
          
          <div className="flex justify-center space-x-8 mb-8">
            <button onClick={() => setIsLogin(true)} className={`cursor-pointer flex items-center space-x-2 pb-2 transition-all ${isLogin ? 'text-gray-900 font-bold border-b-2 border-gray-900' : 'text-gray-400 hover:text-gray-900'}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg>
              <span>Login</span>
            </button>
            <button onClick={() => setIsLogin(false)} className={`cursor-pointer flex items-center space-x-2 pb-2 transition-all ${!isLogin ? 'text-gray-900 font-bold border-b-2 border-gray-900' : 'text-gray-400 hover:text-gray-900'}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
              <span>Sign Up</span>
            </button>
          </div>

          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-gray-900 mb-1">{isLogin ? 'Welcome back' : 'Create an account'}</h2>
            <p className="text-gray-500 text-sm">{isLogin ? 'Please enter your details to sign in.' : 'Please enter your details to create an account.'}</p>
          </div>

          {/* SVGs ADDED FOR UNIVERSAL RENDERING */}
          <div className="space-y-3 mb-6">
            <button type="button" className="cursor-pointer w-full flex items-center justify-center space-x-3 py-2.5 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-sm">
              <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              <span>Continue with Google</span>
            </button>
            <button type="button" className="cursor-pointer w-full flex items-center justify-center space-x-3 py-2.5 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-sm">
              <svg className="w-5 h-5" viewBox="0 0 384 512" fill="currentColor"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>
              <span>Continue with Apple</span>
            </button>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200"></div></div>
            <div className="relative flex justify-center text-sm"><span className="px-4 bg-[#FAFAFA] text-gray-400 text-xs uppercase font-bold tracking-wider">OR</span></div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
              <input type="email" name="email" value={formData.email} onChange={handleChange} required placeholder="Enter your email address" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-gray-900 focus:border-gray-900 sm:text-sm transition-all outline-none bg-white shadow-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" name="password" value={formData.password} onChange={handleChange} required placeholder="Enter your password" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-gray-900 focus:border-gray-900 sm:text-sm transition-all outline-none bg-white shadow-sm" />
            </div>

            {!isLogin && (
              <div className="flex items-start mt-2">
                <input id="terms" type="checkbox" className="cursor-pointer mt-1 h-4 w-4 text-gray-900 border-gray-300 rounded focus:ring-gray-900" />
                <label htmlFor="terms" className="cursor-pointer ml-3 text-xs text-gray-500 leading-relaxed">
                  Please keep me updated by email with the latest news, research findings, and event updates.
                </label>
              </div>
            )}

            <button type="submit" className="cursor-pointer w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-bold text-white bg-[#111111] hover:bg-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 mt-4 transition-colors">
              {isLogin ? 'Sign in' : 'Create an account'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button onClick={() => setIsLogin(!isLogin)} className="cursor-pointer font-bold text-gray-900 underline hover:text-black transition-colors">
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;