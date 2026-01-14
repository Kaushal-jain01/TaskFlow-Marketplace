import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { PlusCircle, CheckCircle, Shield, User } from 'lucide-react';

const API_BASE = 'https://microtasks-api.onrender.com/api';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(
    user?.role === 'business' ? 'posted' : 'open'
  );

  // 🔹 Fetch tasks whenever the tab changes or user loads
  useEffect(() => {
    if (!user) return;
    fetchTasks(activeTab);
  }, [activeTab, user]);

  const fetchTasks = async (tab) => {
    setLoading(true);
    try {
      let endpoint = '';

      if (user.role === 'worker') {
        if (tab === 'open') endpoint = `${API_BASE}/worker-open-tasks/`;
        else if (tab === 'my') endpoint = `${API_BASE}/worker-my-tasks/`;
      } else if (user.role === 'business') {
        if (tab === 'posted') endpoint = `${API_BASE}/business-posted-tasks/`;
        else if (tab === 'claimed') endpoint = `${API_BASE}/business-claimed-tasks/`;
      }

      if (!endpoint) {
        setTasks([]);
        setLoading(false);
        return;
      }

      const { data } = await axios.get(endpoint);
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      open: 'bg-success text-white',
      claimed: 'bg-warning text-dark',
      completed: 'bg-info text-dark', 
      approved: 'bg-primary text-white',
      paid: 'bg-success text-white'
    };
    return badges[status] || 'bg-secondary';
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-vh-100 bg-light">
      {/* Header */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div className="container">
          <div className="d-flex align-items-center">
            <Shield className="me-2" size={28} />
            <h2 className="navbar-brand mb-0 h4 fw-bold">Microtasks</h2>
          </div>
          <div className="d-flex align-items-center">
            <span className="navbar-text me-3">
              <User size={20} className="me-1" /> {user.username}
            </span>
            <button onClick={logout} className="btn btn-outline-light btn-sm">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="container-fluid py-4">
        {/* Role Badge */}
        <div className="row mb-4">
          <div className="col-12">
            <span className={`badge fs-6 px-3 py-2 ${user.role === 'business' ? 'bg-primary' : 'bg-success'}`}>
              {user.role === 'business' ? '🏢 Business' : '👷 Worker'}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="row mb-4">
          <div className="col-12">
            <ul className="nav nav-tabs border-0 bg-white shadow-sm rounded-top">
              {user.role === 'worker' && (
                <>
                  <li className="nav-item">
                    <button 
                      className={`nav-link ${activeTab === 'open' ? 'active' : ''}`}
                      onClick={() => setActiveTab('open')}
                    >
                      Open Tasks
                    </button>
                  </li>
                  <li className="nav-item">
                    <button 
                      className={`nav-link ${activeTab === 'my' ? 'active' : ''}`}
                      onClick={() => setActiveTab('my')}
                    >
                      My Tasks
                    </button>
                  </li>
                </>
              )}
              {user.role === 'business' && (
                <>
                  <li className="nav-item">
                    <button 
                      className={`nav-link ${activeTab === 'posted' ? 'active' : ''}`}
                      onClick={() => setActiveTab('posted')}
                    >
                      Posted Tasks
                    </button>
                  </li>
                  <li className="nav-item">
                    <button 
                      className={`nav-link ${activeTab === 'claimed' ? 'active' : ''}`}
                      onClick={() => setActiveTab('claimed')}
                    >
                      Claimed Tasks
                    </button>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>

        {/* Tasks Grid */}
        <div className="row g-4">
          {tasks.length === 0 && (
            <div className="col-12 text-center py-5">
              <Shield size={64} className="text-muted mb-4 opacity-50" />
              <h3 className="fw-bold text-muted mb-3">No tasks found</h3>
              <p className="text-muted mb-4">Check back later for new opportunities</p>
            </div>
          )}

          {tasks.map((task) => (
            <div key={task.id} className="col-lg-4 col-md-6">
              <div className="card h-100 shadow-sm border-0 hover-shadow">
                <div className="card-body p-4">
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <span className={`badge ${getStatusBadge(task.status)} px-3 py-2 fs-6 fw-semibold`}>
                      {task.status.toUpperCase()}
                    </span>
                    <div className="text-end">
                      <div className="h5 fw-bold text-primary mb-0">₹{task.price}</div>
                      <small className="text-muted">Reward</small>
                    </div>
                  </div>

                  <h5 className="card-title fw-bold text-dark mb-3">{task.title}</h5>
                  <p className="card-text text-muted mb-4" style={{ height: '60px', overflow: 'hidden' }}>
                    {task.description}
                  </p>

                  <div className="d-flex gap-2">
                    {/* Worker buttons */}
                    {user.role === 'worker' && task.status === 'open' && (
                      <button className="btn btn-success w-100">
                        <PlusCircle size={18} className="me-1" />
                        Claim Task
                      </button>
                    )}
                    {user.role === 'worker' && task.status === 'claimed' && (
                      <button className="btn btn-primary w-100">
                        <CheckCircle size={18} className="me-1" />
                        Upload Proof
                      </button>
                    )}

                    {/* Business buttons */}
                    {user.role === 'business' && task.status === 'completed' && (
                      <button className="btn btn-outline-primary w-100">
                        Review & Approve
                      </button>
                    )}
                    {user.role === 'business' && task.status === 'approved' && (
                      <button className="btn btn-success w-100">
                        Pay Now
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Post New Task Button */}
          {user.role === 'business' && activeTab === 'posted' && (
            <div className="col-12 text-center py-5">
              <button className="btn btn-primary btn-lg">
                <PlusCircle size={20} className="me-2" />
                Post New Task
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
