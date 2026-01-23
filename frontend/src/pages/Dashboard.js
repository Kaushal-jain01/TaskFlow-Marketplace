import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import API_BASE from '../config/api';
import { PlusCircle, CheckCircle, Shield, User } from 'lucide-react';
import 'bootstrap/dist/css/bootstrap.min.css';

// const API_BASE = 'https://microtasks-api.onrender.com/api';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});

  useEffect(() => {
    if (!user) return;
    if (user.role === 'worker') {
      fetchOpenTasks();
      fetchWorkerStats();
    } else if (user.role === 'business') {
      fetchBusinessStats();
    }
  }, [user]);

  // --------------------
  // Worker Functions
  // --------------------
  const fetchOpenTasks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tasks/?status=open`);
      setTasks(res.data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkerStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/worker/`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching business stats:', err);
    }
  };

  const handleClaim = async (taskId) => {
    try {
      await axios.patch(`${API_BASE}/tasks/${taskId}/claim/`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      alert('Task claimed successfully!');
      fetchOpenTasks();
      fetchWorkerStats();
    } catch (err) {
      console.error('Error claiming task:', err);
      alert('Failed to claim task.');
    }
  };

  // --------------------
  // Business Functions
  // --------------------
  const fetchBusinessStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/business/`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching business stats:', err);
    }
  };

  const handleCreateTask = () => {
    navigate('/tasks/create'); // Navigate to a create task page/modal
  };


  return (
    <div className="container-fluid vh-100">
      <div className="row h-100">

        {/* Main Content */}
        <div className="col-8 p-3 overflow-auto" style={{ maxHeight: '100vh' }}>
          {user?.role === 'worker' ? (
            <>
              <h4>Open Tasks</h4>
              {loading ? (
                <div className="d-flex justify-content-center mt-5">
                  <div className="spinner-border" role="status" />
                </div>
              ) : (
                tasks.map(task => (
                  <div key={task.id} className="card mb-3">
                    <div className="card-body">
                      <h5 className="card-title">{task.title}</h5>
                      <p className="card-text">{task.description}</p>
                      <p className="card-text">
                        <small className="text-muted">Price: ₹{task.price} | Duration: {task.duration_minutes} mins</small>
                      </p>
                      <button className="btn btn-primary" onClick={() => handleClaim(task.id)}>Claim Task</button>
                    </div>
                  </div>
                ))
              )}
              {tasks.length === 0 && !loading && <p>No open tasks available.</p>}
            </>
          ) : (
            <>
              <h4>Business Dashboard</h4>
              <button className="btn btn-success mb-3" onClick={handleCreateTask}>
                <PlusCircle className="me-2" /> Create Task
              </button>
            </>
          )}
        </div>

        {/* Stats Panel */}
        <div className="col-4 bg-light p-3">
          <h5>Stats</h5>
          {user?.role === 'worker' ? (
            <>
              <div className="card mb-2">
                <div className="card-body d-flex align-items-center">
                  <User className="me-2" />
                  <div>
                    <p className="mb-0">Tasks Claimed</p>
                    <h6>{stats.claimed}</h6>
                  </div>
                </div>
              </div>

              <div className="card mb-2">
                <div className="card-body d-flex align-items-center">
                  <CheckCircle className="me-2" />
                  <div>
                    <p className="mb-0">Tasks Completed</p>
                    <h6>{stats.completed}</h6>
                  </div>
                </div>
              </div>

              <div className="card mb-2">
                <div className="card-body d-flex align-items-center">
                  <Shield className="me-2" />
                  <div>
                    <p className="mb-0">Total Earnings</p>
                    <h6>₹{stats.total_earnings}</h6>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="card mb-2">
                <div className="card-body d-flex align-items-center">
                  <User className="me-2" />
                  <div>
                    <p className="mb-0">Tasks Posted</p>
                    <h6>{stats.posted}</h6>
                  </div>
                </div>
              </div>

              <div className="card mb-2">
                <div className="card-body d-flex align-items-center">
                  <CheckCircle className="me-2" />
                  <div>
                    <p className="mb-0">Tasks Pending</p>
                    <h6>{stats.pending}</h6>
                  </div>
                </div>
              </div>

              <div className="card mb-2">
                <div className="card-body d-flex align-items-center">
                  <Shield className="me-2" />
                  <div>
                    <p className="mb-0">Total Amount Paid</p>
                    <h6>₹{stats.total_paid_amount}</h6>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
