import axios from 'axios';

// FastAPI backend runs on port 8000. 
const API_URL = 'http://localhost:8000'; 

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Automatically attach the JWT token to every request if it exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth Endpoints
export const authAPI = {
  // Matches standard FastAPI JSON user creation
  register: (userData) => api.post('/api/auth/register', userData),
  
  // NOTE: If your FastAPI backend uses OAuth2PasswordRequestForm, 
  // it expects Form-Data (username/password), not JSON. 
  // We will send standard JSON for now. If your backend strictly requires Form-Data, 
  // we will adjust this function.
  login: (credentials) => api.post('/api/auth/login', credentials),
};

export default api;