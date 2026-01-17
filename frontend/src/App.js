import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import PostedTasks from './pages/PostedTasks';
import ClaimedTasks from './pages/ClaimedTasks';
import TaskHistory from './pages/TaskHistory';
import CreateTask from './pages/CreateTask';
import 'bootstrap/dist/css/bootstrap.min.css';

// Spinner while loading auth state
function LoadingSpinner() {
  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="spinner-border" role="status" />
    </div>
  );
}

// Protect routes for authenticated users
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return <LoadingSpinner />;
  return user ? children : <Navigate to="/login" />;
}

// Redirect logged-in users away from login/register
function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  // if (loading) return <LoadingSpinner />;
  return user ? <Navigate to="/dashboard" /> : children;
}

function AppContent() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } 
        />

        {/* Dashboard routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard activeTab="open" />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard/posted" 
          element={
            <ProtectedRoute>
              <PostedTasks />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard/claimed" 
          element={
            <ProtectedRoute>
              <ClaimedTasks />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard/history" 
          element={
            <ProtectedRoute>
              <TaskHistory />
            </ProtectedRoute>
          } 
        />
        <Route
          path="/tasks/create"
          element={
            <ProtectedRoute>
              <CreateTask />
            </ProtectedRoute>
          }
        />

        {/* Default route */}
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/" />} /> {/* catch-all */}
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
