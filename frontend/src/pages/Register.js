import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '', email: '', password: '', profile: { role: 'worker' }
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('https://microtasks-api.onrender.com/api/register/', formData);
      navigate('/login');
    } catch {
      setError('Registration failed');
    }
  };

  return (
    <div className="vh-100 d-flex align-items-center justify-content-center bg-light">
      <div className="card shadow-lg border-0" style={{ maxWidth: '450px', width: '100%' }}>
        <div className="card-body p-5">
          <div className="text-center mb-4">
            <h1 className="h3 fw-bold text-dark mb-2">Join Microtasks</h1>
            <p className="text-muted">Create your account</p>
          </div>

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="row">
              <div className="col-md-6 mb-4">
                <label className="form-label fw-semibold">Username</label>
                <input
                  type="text"
                  className="form-control form-control-lg"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div className="col-md-6 mb-4">
                <label className="form-label fw-semibold">Email</label>
                <input
                  type="email"
                  className="form-control form-control-lg"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="form-label fw-semibold">Password</label>
              <input
                type="password"
                className="form-control form-control-lg"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>

            <div className="mb-4">
              <label className="form-label fw-semibold">Role</label>
              <select
                className="form-select form-select-lg"
                value={formData.profile.role}
                onChange={(e) => setFormData({ ...formData, profile: { role: e.target.value } })}
              >
                <option value="worker">Worker</option>
                <option value="business">Business</option>
              </select>
            </div>

            <button type="submit" className="btn btn-success btn-lg w-100 mb-3">
              Create Account
            </button>
          </form>

          <div className="text-center">
            <small className="text-muted">
              Already have an account?{' '}
              <Link to="/login" className="text-decoration-none fw-semibold text-primary">
                Sign in
              </Link>
            </small>
          </div>
        </div>
      </div>
    </div>
  );
}
