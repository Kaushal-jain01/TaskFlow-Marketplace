import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import API_BASE from '../config/api';
import { PlusCircle, CheckCircle, Shield, User } from 'lucide-react';

// const API_BASE = 'https://microtasks-api.onrender.com/api';

export default function WorkerDashboard() {
  const { user, logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(
    'open'
  );


  /* 🔹 Fetch tasks */
  useEffect(() => {
    if (!user) return;
    fetchTasks(activeTab);
  }, [activeTab, user]);

  const fetchTasks = async (tab) => {
    setLoading(true);
    try {
      let endpoint = '';
     
      if (tab === 'open') endpoint = `${API_BASE}/worker-open-tasks/`;
      else if (tab === 'my') endpoint = `${API_BASE}/worker-my-tasks/`;

      if (!endpoint) {
        setTasks([]);
        return;
      }

      const { data } = await axios.get(endpoint);
      setTasks(data);
    } catch (err) {
      console.error("Fetch tasks failed", err);
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
      paid: 'bg-success text-white',
    };
    return badges[status] || 'bg-secondary';
  };

  /* 🔹 Loading screen */
  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  return (
    <div className="min-vh-100 bg-light">

      {/* 🔹 Navbar */}
      <nav className="navbar navbar-dark bg-primary shadow-sm">
        <div className="container">
          <div className="d-flex align-items-center">
            <Shield className="me-2" size={26} />
            <h4 className="mb-0 fw-bold">Microtasks - Worker Dashboard</h4>
          </div>
          <div className="d-flex align-items-center">
            <span className="me-3 text-white">
              <User size={18} className="me-1" />
              {user.username}
            </span>
            <button onClick={logout} className="btn btn-outline-light btn-sm">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="container-fluid py-4">

        {/* 🔹 Role Badge */}
        <span className={`badge fs-6 mb-4 ${
          'bg-success'
        }`}>
          {'👷 Worker '}
        </span>

        {/* 🔹 Tabs */}
        <ul className="nav nav-tabs bg-white shadow-sm rounded mb-4">
          {<>
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
          }
        </ul>

        {/* 🔹 Tasks */}
        <div className="row g-4">
          {tasks.length === 0 && (
            <div className="text-center text-muted py-5">
              <Shield size={60} className="mb-3 opacity-50" />
              <h5>No tasks found</h5>
            </div>
          )}

          {tasks.map(task => (
            <div key={task.id} className="col-lg-4 col-md-6">
              <div className="card h-100 shadow-sm">
                <div className="card-body">

                  <div className="d-flex justify-content-between mb-2">
                    <span className={`badge ${getStatusBadge(task.status)}`}>
                      {task.status.toUpperCase()}
                    </span>
                    <strong className="text-primary">₹{task.price}</strong>
                  </div>

                  <h5>{task.title}</h5>
                  <p className="text-muted small">
                    {task.description}
                  </p>                  

                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      

    </div>
  );
}
