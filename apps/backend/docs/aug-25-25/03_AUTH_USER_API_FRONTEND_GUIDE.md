# Authentication & User Management API - Frontend Integration Guide
**Date**: 2025-08-25  
**Time**: 13:15:00  
**Component**: Authentication System & User Management

## Overview

This comprehensive guide covers the authentication system and user management APIs built with Supabase Auth integration. The system provides secure JWT-based authentication with hybrid cookie + Bearer token support, role-based access control, and complete user profile management.

## Authentication Architecture

### Token Management System
- **Supabase Auth**: Primary authentication provider
- **Hybrid Auth**: Supports both Bearer tokens and httpOnly cookies
- **JWT Tokens**: Access and refresh token pair
- **Session Management**: Server-side session tracking
- **Role-Based Access**: Student/Instructor/Admin roles

### Security Features
- JWT signature validation
- Token expiration handling
- Automatic token refresh
- Session revocation
- CORS and CSRF protection

## Base Configuration

### API Base URLs
```
Production: https://your-api-domain.com/api/v1
Development: http://localhost:3001/api/v1
```

### Authentication Paths
- **Primary**: `/api/v1/auth/`
- **Alias**: `/api/v1/user/` (for frontend compatibility)

## Authentication Endpoints

### 1. User Registration

**Endpoint**: `POST /auth/signup`

**Purpose**: Create a new user account with email and password

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "role": "student"
}
```

**Success Response (201)**:
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "user": {
      "supabase_user_id": "uuid-string",
      "email": "user@example.com",
      "full_name": "John Doe",
      "display_name": "John",
      "status": "active",
      "email_verified": false,
      "created_at": "2025-08-25T10:30:00Z"
    },
    "session": {
      "access_token": "jwt-access-token",
      "refresh_token": "jwt-refresh-token",
      "expires_at": "2025-08-25T11:30:00Z",
      "expires_in": 3600,
      "token_type": "bearer"
    }
  }
}
```

**Error Responses**:
```json
// 400 - Validation Error
{
  "email": ["Email already registered"],
  "password": ["Password must be at least 6 characters"]
}

// 400 - Supabase Error
{
  "error": "Unable to validate email address: invalid format"
}
```

### 2. User Sign In

**Endpoint**: `POST /auth/signin`

**Purpose**: Authenticate existing user and return session tokens

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Sign in successful",
  "data": {
    "user": {
      "supabase_user_id": "uuid-string",
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe",
      "display_name": "John",
      "avatar_url": "https://example.com/avatar.jpg",
      "bio": "Learning enthusiast",
      "status": "active",
      "email_verified": true,
      "last_login": "2025-08-25T10:30:00Z",
      "created_at": "2025-08-20T10:00:00Z"
    },
    "session": {
      "access_token": "jwt-access-token",
      "refresh_token": "jwt-refresh-token",
      "expires_at": "2025-08-25T11:30:00Z",
      "expires_in": 3600,
      "token_type": "bearer"
    }
  }
}
```

**Error Responses**:
```json
// 400 - Invalid credentials
{
  "error": "Invalid email or password"
}

// 400 - Account issues
{
  "error": "Email not confirmed"
}
```

### 3. Token Refresh

**Endpoint**: `POST /auth/refresh`

**Purpose**: Get new access token using refresh token

**Request Body**:
```json
{
  "refresh_token": "jwt-refresh-token"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "access_token": "new-jwt-access-token",
    "refresh_token": "new-jwt-refresh-token",
    "expires_at": "2025-08-25T12:30:00Z",
    "expires_in": 3600,
    "token_type": "bearer"
  }
}
```

### 4. Password Reset

**Endpoint**: `POST /auth/reset-password`

**Purpose**: Send password reset email to user

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

### 5. Sign Out

**Endpoint**: `POST /auth/signout`

**Headers**: `Authorization: Bearer <access_token>`

**Purpose**: Invalidate current session and tokens

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Signed out successfully"
}
```

## User Profile Endpoints

### 1. Get Profile

**Endpoint**: `GET /auth/profile`

**Headers**: `Authorization: Bearer <access_token>`

**Purpose**: Get current user's profile information

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "supabase_user_id": "uuid-string",
    "email": "user@example.com",
    "username": "john_doe",
    "full_name": "John Doe",
    "display_name": "John",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "Learning enthusiast and developer",
    "status": "active",
    "phone_number": "+1234567890",
    "timezone": "UTC",
    "language": "en",
    "email_verified": true,
    "last_login": "2025-08-25T10:30:00Z",
    "created_at": "2025-08-20T10:00:00Z",
    "updated_at": "2025-08-25T09:00:00Z"
  }
}
```

### 2. Update Profile

**Endpoint**: `PUT /auth/profile/update` or `PATCH /auth/profile/update`

**Headers**: `Authorization: Bearer <access_token>`

**Purpose**: Update current user's profile information

**Request Body** (all fields optional for PATCH):
```json
{
  "username": "new_username",
  "full_name": "John Smith",
  "display_name": "Johnny",
  "bio": "Updated bio text",
  "phone_number": "+1234567890",
  "timezone": "America/New_York",
  "language": "en"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "supabase_user_id": "uuid-string",
    "email": "user@example.com",
    "username": "new_username",
    "full_name": "John Smith",
    "display_name": "Johnny",
    "bio": "Updated bio text",
    // ... rest of profile data
    "updated_at": "2025-08-25T10:35:00Z"
  }
}
```

## Session Management Endpoints

### 1. Get User Sessions

**Endpoint**: `GET /auth/sessions`

**Headers**: `Authorization: Bearer <access_token>`

**Purpose**: List all active sessions for current user

**Success Response (200)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "session-uuid",
      "session_id": "session-string",
      "device_info": "Chrome 118 on MacOS",
      "ip_address": "192.168.1.100",
      "location": "New York, US",
      "is_active": true,
      "last_activity": "2025-08-25T10:30:00Z",
      "expires_at": "2025-08-26T10:30:00Z",
      "created_at": "2025-08-25T09:00:00Z"
    }
  ]
}
```

### 2. Revoke Session

**Endpoint**: `DELETE /auth/sessions/{sessionId}`

**Headers**: `Authorization: Bearer <access_token>`

**Purpose**: Revoke a specific session

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Session revoked successfully"
}
```

### 3. Revoke All Sessions

**Endpoint**: `POST /auth/sessions/revoke-all`

**Headers**: `Authorization: Bearer <access_token>`

**Purpose**: Revoke all sessions except current one

**Success Response (200)**:
```json
{
  "success": true,
  "message": "All other sessions revoked successfully"
}
```

## Role-Based Access Control

### 1. Get User Roles

**Endpoint**: `GET /auth/roles`

**Headers**: `Authorization: Bearer <access_token>`

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "roles": ["student", "instructor"],
    "primary_role": "instructor",
    "permissions": [
      "course.create",
      "course.update",
      "course.delete",
      "enrollment.view"
    ]
  }
}
```

### 2. Check Permission

**Endpoint**: `POST /auth/permissions/check`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "permission": "course.create"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "has_permission": true,
    "permission": "course.create"
  }
}
```

## Frontend Integration Examples

### React Authentication Context

```javascript
import React, { createContext, useContext, useReducer, useEffect } from 'react';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, loading: true, error: null };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        loading: false,
        user: action.payload.user,
        token: action.payload.session.access_token,
        refreshToken: action.payload.session.refresh_token,
        isAuthenticated: true
      };
    case 'LOGIN_FAILURE':
      return { ...state, loading: false, error: action.payload };
    case 'LOGOUT':
      return { ...initialState };
    case 'UPDATE_PROFILE':
      return { ...state, user: { ...state.user, ...action.payload } };
    default:
      return state;
  }
};

const initialState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: false,
  error: null
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    // Check for stored tokens on app start
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const userData = localStorage.getItem('user_data');

    if (token && refreshToken && userData) {
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          session: { access_token: token, refresh_token: refreshToken },
          user: JSON.parse(userData)
        }
      });
    }
  }, []);

  const signup = async (userData) => {
    dispatch({ type: 'LOGIN_START' });
    try {
      const response = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Signup failed');
      }

      const data = await response.json();
      
      // Store tokens
      localStorage.setItem('access_token', data.data.session.access_token);
      localStorage.setItem('refresh_token', data.data.session.refresh_token);
      localStorage.setItem('user_data', JSON.stringify(data.data.user));

      dispatch({ type: 'LOGIN_SUCCESS', payload: data.data });
      return data.data;
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE', payload: error.message });
      throw error;
    }
  };

  const signin = async (credentials) => {
    dispatch({ type: 'LOGIN_START' });
    try {
      const response = await fetch('/api/v1/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Sign in failed');
      }

      const data = await response.json();
      
      // Store tokens
      localStorage.setItem('access_token', data.data.session.access_token);
      localStorage.setItem('refresh_token', data.data.session.refresh_token);
      localStorage.setItem('user_data', JSON.stringify(data.data.user));

      dispatch({ type: 'LOGIN_SUCCESS', payload: data.data });
      return data.data;
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE', payload: error.message });
      throw error;
    }
  };

  const signout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch('/api/v1/auth/signout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      }
    } catch (error) {
      console.error('Signout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) throw new Error('No refresh token');

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh })
      });

      if (!response.ok) throw new Error('Token refresh failed');

      const data = await response.json();
      
      // Update stored tokens
      localStorage.setItem('access_token', data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);

      return data.data.access_token;
    } catch (error) {
      console.error('Token refresh error:', error);
      signout();
      throw error;
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/auth/profile/update', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      });

      if (!response.ok) throw new Error('Profile update failed');

      const data = await response.json();
      
      // Update stored user data
      localStorage.setItem('user_data', JSON.stringify(data.data));
      dispatch({ type: 'UPDATE_PROFILE', payload: data.data });
      
      return data.data;
    } catch (error) {
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{
      ...state,
      signup,
      signin,
      signout,
      refreshToken,
      updateProfile
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Protected Route Component

```javascript
import React from 'react';
import { useAuth } from './AuthContext';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    // Redirect to login with return URL
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.primary_role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

// Usage examples
const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      
      {/* Protected routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      
      {/* Instructor-only route */}
      <Route path="/instructor" element={
        <ProtectedRoute requiredRole="instructor">
          <InstructorDashboard />
        </ProtectedRoute>
      } />
    </Routes>
  );
};
```

### API Service with Auto Token Refresh

```javascript
class APIService {
  constructor(baseURL = '/api/v1') {
    this.baseURL = baseURL;
    this.refreshPromise = null;
  }

  async getToken() {
    return localStorage.getItem('access_token');
  }

  async refreshToken() {
    // Prevent multiple refresh calls
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._doRefresh();
    try {
      const result = await this.refreshPromise;
      this.refreshPromise = null;
      return result;
    } catch (error) {
      this.refreshPromise = null;
      throw error;
    }
  }

  async _doRefresh() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token');
    }

    const response = await fetch(`${this.baseURL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
      // Refresh failed, redirect to login
      localStorage.clear();
      window.location.href = '/login';
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('refresh_token', data.data.refresh_token);
    
    return data.data.access_token;
  }

  async apiCall(endpoint, options = {}) {
    const token = await this.getToken();
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      }
    };

    let response = await fetch(`${this.baseURL}${endpoint}`, config);

    // Handle token expiration
    if (response.status === 401 && token) {
      try {
        const newToken = await this.refreshToken();
        
        // Retry with new token
        config.headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(`${this.baseURL}${endpoint}`, config);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.clear();
        window.location.href = '/login';
        throw refreshError;
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth methods
  async signup(userData) {
    return this.apiCall('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async signin(credentials) {
    return this.apiCall('/auth/signin', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  async getProfile() {
    return this.apiCall('/auth/profile');
  }

  async updateProfile(profileData) {
    return this.apiCall('/auth/profile/update', {
      method: 'PATCH',
      body: JSON.stringify(profileData)
    });
  }

  async getUserSessions() {
    return this.apiCall('/auth/sessions');
  }

  async revokeSession(sessionId) {
    return this.apiCall(`/auth/sessions/${sessionId}`, {
      method: 'DELETE'
    });
  }
}

export default new APIService();
```

### Login/Signup Components

```javascript
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const LoginPage = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [isSignup, setIsSignup] = useState(false);
  const { signin, signup, loading, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isSignup) {
        await signup({
          ...formData,
          full_name: formData.fullName,
          role: formData.role || 'student'
        });
      } else {
        await signin(formData);
      }
      navigate(from, { replace: true });
    } catch (error) {
      console.error('Auth error:', error);
    }
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit}>
        <h2>{isSignup ? 'Create Account' : 'Sign In'}</h2>
        
        {error && <div className="error">{error}</div>}
        
        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
        
        <input
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
          minLength={6}
        />
        
        {isSignup && (
          <>
            <input
              type="text"
              placeholder="Full Name"
              value={formData.fullName || ''}
              onChange={(e) => setFormData({...formData, fullName: e.target.value})}
            />
            
            <select
              value={formData.role || 'student'}
              onChange={(e) => setFormData({...formData, role: e.target.value})}
            >
              <option value="student">Student</option>
              <option value="instructor">Instructor</option>
            </select>
          </>
        )}
        
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : (isSignup ? 'Sign Up' : 'Sign In')}
        </button>
        
        <button
          type="button"
          onClick={() => setIsSignup(!isSignup)}
        >
          {isSignup ? 'Already have an account?' : 'Need an account?'}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
```

## Error Handling Best Practices

### Common Error Patterns

```javascript
const handleAuthError = (error) => {
  const errorPatterns = {
    'No authorization token': () => {
      // Clear tokens and redirect to login
      localStorage.clear();
      window.location.href = '/login';
    },
    'Token has expired': () => {
      // Try to refresh token
      return refreshToken();
    },
    'Invalid email or password': () => {
      // Show user-friendly login error
      setError('Please check your email and password');
    },
    'Email already registered': () => {
      // Suggest sign in instead
      setError('Email already registered. Try signing in instead.');
    }
  };

  for (const [pattern, handler] of Object.entries(errorPatterns)) {
    if (error.message.includes(pattern)) {
      return handler();
    }
  }
  
  // Default error handling
  console.error('Auth error:', error);
  setError(error.message);
};
```

### Global Error Interceptor

```javascript
// Axios interceptor example
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const newToken = await refreshToken();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

## Security Best Practices

### Token Storage
```javascript
// Secure token storage options
const tokenStorage = {
  // Option 1: Memory only (most secure, lost on refresh)
  memoryStorage: {
    token: null,
    set: (token) => { this.token = token; },
    get: () => this.token,
    clear: () => { this.token = null; }
  },

  // Option 2: localStorage (persistent, less secure)
  localStorageSecure: {
    set: (token) => {
      // Add basic obfuscation
      const encoded = btoa(JSON.stringify({ token, timestamp: Date.now() }));
      localStorage.setItem('auth_data', encoded);
    },
    get: () => {
      try {
        const encoded = localStorage.getItem('auth_data');
        if (!encoded) return null;
        
        const { token, timestamp } = JSON.parse(atob(encoded));
        
        // Check if token is too old (additional security)
        if (Date.now() - timestamp > 24 * 60 * 60 * 1000) {
          localStorage.removeItem('auth_data');
          return null;
        }
        
        return token;
      } catch {
        return null;
      }
    },
    clear: () => localStorage.removeItem('auth_data')
  },

  // Option 3: httpOnly cookies (recommended for production)
  // Set by backend, automatically included in requests
};
```

### Content Security Policy
```html
<!-- Add to HTML head -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  connect-src 'self' https://your-api-domain.com https://*.supabase.co;
  img-src 'self' data: https:;
  style-src 'self' 'unsafe-inline';
  script-src 'self';
">
```

## Testing Examples

### Unit Tests
```javascript
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { AuthProvider } from '../contexts/AuthContext';
import LoginPage from '../pages/LoginPage';

const server = setupServer(
  rest.post('/api/v1/auth/signin', (req, res, ctx) => {
    const { email, password } = req.body;
    
    if (email === 'test@example.com' && password === 'password123') {
      return res(ctx.json({
        success: true,
        data: {
          user: { email: 'test@example.com', full_name: 'Test User' },
          session: { access_token: 'fake-token', refresh_token: 'fake-refresh' }
        }
      }));
    }
    
    return res(
      ctx.status(400),
      ctx.json({ error: 'Invalid email or password' })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('successful login flow', async () => {
  render(
    <AuthProvider>
      <LoginPage />
    </AuthProvider>
  );
  
  // Test login form interaction
  // ... test implementation
});
```

## Troubleshooting Guide

### Common Issues

**1. Token Expiration**
- Symptoms: 401 errors on authenticated requests
- Solution: Implement automatic token refresh
- Prevention: Monitor token expiration times

**2. CORS Errors**
- Symptoms: Network errors in browser console
- Solution: Configure CORS settings on backend
- Check: Ensure credentials are included in requests

**3. Session Management**
- Symptoms: Users logged out unexpectedly
- Solution: Implement proper session storage
- Monitor: Session duration and refresh logic

**4. Role-Based Access**
- Symptoms: Users accessing restricted areas
- Solution: Implement proper permission checks
- Verify: User roles on both frontend and backend

## Conclusion

This authentication system provides a robust foundation for user management with Supabase integration, JWT tokens, and comprehensive session handling. The hybrid authentication approach supports both modern and legacy frontend requirements while maintaining security best practices.

For production deployment, ensure proper token storage, implement CSP headers, and monitor authentication metrics for optimal user experience.

---

**Related Documentation**:
- [Student Learning API Guide](./02_STUDENT_LEARNING_API_FRONTEND_GUIDE.md)
- [Course Management API Guide](./04_COURSE_MANAGEMENT_API_GUIDE.md)
- [Security Best Practices](./05_SECURITY_BEST_PRACTICES.md)