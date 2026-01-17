import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import API_BASE from '../config/api';
import axios from 'axios';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    profile: {
      role: 'worker',
      phone: '',
      address_line1: '',
      city: '',
      country: '',
      postal_code: '',
    },
  });

  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // reset previous errors
    try {
      await axios.post(`${API_BASE}/auth/register/`, formData);
      navigate('/login');
    } catch (err) {
      // Backend may return detailed validation errors
      if (err.response?.data) {
        const messages = [];
        for (const key in err.response.data) {
          messages.push(`${key}: ${err.response.data[key]}`);
        }
        setError(messages.join(' | '));
      } else {
        setError('Registration failed. Try again.');
      }
    }
  };

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center bg-light py-5">
      <div className="card shadow-lg border-0" style={{ maxWidth: '500px', width: '100%' }}>
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
            <div className="mb-3">
              <label className="form-label fw-semibold">Username</label>
              <input
                type="text"
                className="form-control form-control-lg"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold">Email</label>
              <input
                type="email"
                className="form-control form-control-lg"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold">Password</label>
              <input
                type="password"
                className="form-control form-control-lg"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold">Role</label>
              <select
                className="form-select form-select-lg"
                value={formData.profile.role}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    profile: { ...formData.profile, role: e.target.value },
                  })
                }
              >
                <option value="worker">Worker</option>
                <option value="business">Business</option>
              </select>
            </div>

            {/* Optional profile fields */}
            <div className="mb-3">
              <label className="form-label fw-semibold">Phone</label>
              <input
                type="text"
                className="form-control form-control-lg"
                value={formData.profile.phone}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    profile: { ...formData.profile, phone: e.target.value },
                  })
                }
              />
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold">Address</label>
              <input
                type="text"
                className="form-control form-control-lg"
                value={formData.profile.address_line1}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    profile: { ...formData.profile, address_line1: e.target.value },
                  })
                }
              />
            </div>

            <div className="row mb-3">
              <div className="col-md-4">
                <label className="form-label fw-semibold">City</label>
                <input
                  type="text"
                  className="form-control form-control-lg"
                  value={formData.profile.city}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      profile: { ...formData.profile, city: e.target.value },
                    })
                  }
                />
              </div>
              <div className="col-md-4">
                <label className="form-label fw-semibold">Country</label>
                <input
                  type="text"
                  className="form-control form-control-lg"
                  value={formData.profile.country}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      profile: { ...formData.profile, country: e.target.value },
                    })
                  }
                />
              </div>
              <div className="col-md-4">
                <label className="form-label fw-semibold">Postal Code</label>
                <input
                  type="text"
                  className="form-control form-control-lg"
                  value={formData.profile.postal_code}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      profile: { ...formData.profile, postal_code: e.target.value },
                    })
                  }
                />
              </div>
            </div>

            <button type="submit" className="btn btn-success btn-lg w-100">
              Create Account
            </button>
          </form>

          <div className="text-center mt-3">
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
