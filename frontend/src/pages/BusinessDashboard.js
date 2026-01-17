import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { PlusCircle, CheckCircle, Shield, User } from 'lucide-react';
import { Elements } from "@stripe/react-stripe-js";
import { stripePromise } from "../stripe";
import StripePayment from "../components/StripePayment";
import API_BASE from '../config/api';

// const API_BASE = 'https://microtasks-api.onrender.com/api';

export default function BusinessDashboard() {
  const { user, logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(
    'posted'
  );

  const [clientSecret, setClientSecret] = useState(null);
  const [showPayment, setShowPayment] = useState(false);

  /* 🔹 Fetch tasks */
  useEffect(() => {
    if (!user) return;
    fetchTasks(activeTab);
  }, [activeTab, user]);

  const fetchTasks = async (tab) => {
    setLoading(true);
    try {
      let endpoint = '';
      
      if (tab === 'posted') endpoint = `${API_BASE}/business-posted-tasks/`;
      else if (tab === 'claimed') endpoint = `${API_BASE}/business-claimed-tasks/`;
      
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

  const handleApprove = async (taskId) => {
    try {
      const token = localStorage.getItem("token");

      await axios.post(
        `${API_BASE}/tasks/${taskId}/approve/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      fetchTasks(activeTab);
    } catch (err) {
      console.error(err.response?.data || err.message);
      alert("Failed to approve task");
    }
  };

  const handlePayNow = async (taskId) => {
    try {
      const token = localStorage.getItem("token");

      const res = await axios.post(
        `${API_BASE}/tasks/${taskId}/pay/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setClientSecret(res.data.client_secret);
      setShowPayment(true);
    } catch (err) {
      console.error(err.response?.data || err.message);
      alert("Failed to initiate payment");
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
            <h4 className="mb-0 fw-bold">Microtasks - Business Dashboard</h4>
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
          'bg-primary'
        }`}>
          {'🏢 Business'}
        </span>

        {/* 🔹 Tabs */}
        <ul className="nav nav-tabs bg-white shadow-sm rounded mb-4">

          {
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

                  {task.status === 'completed' && (
                    <button
                      className="btn btn-primary w-100 mb-2"
                      onClick={() => handleApprove(task.id)}
                    >
                      Approve Task
                    </button>
                  )}

                  {/* 🔹 Actions */}
                  {task.status === 'approved' && (
                    <button
                      className="btn btn-success w-100"
                      disabled={showPayment}
                      onClick={() => handlePayNow(task.id)}
                    >
                      Pay Now
                    </button>
                  )}

                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 🔹 Stripe Modal (SINGLE INSTANCE) */}
      {showPayment && clientSecret && (
        <div className="modal show d-block bg-dark bg-opacity-50">
          <div className="modal-dialog">
            <div className="modal-content p-4">
              <h5 className="mb-3">Complete Payment</h5>

              <Elements stripe={stripePromise}>
                <StripePayment
                  clientSecret={clientSecret}
                  onSuccess={() => {
                    setShowPayment(false);
                    fetchTasks(activeTab);
                  }}
                />
              </Elements>

              <button
                className="btn btn-secondary mt-3 w-100"
                onClick={() => setShowPayment(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
