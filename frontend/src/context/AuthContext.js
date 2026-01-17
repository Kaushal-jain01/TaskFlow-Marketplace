import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../config/api';

// const API_BASE = 'https://microtasks-api.onrender.com/api';

const AuthContext = createContext(null);

// ✅ NAMED EXPORT
export const useAuth = () => {
  return useContext(AuthContext);
};

// ✅ NAMED EXPORT
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const loadUser = async () => {
      try {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        const { data } = await axios.get(`${API_BASE}/auth/profile/`);

        setUser({
          id: data.id,
          username: data.username,
          role: data.role,
        });
      } catch (err) {
        localStorage.removeItem('token');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [token]);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE}/auth/token/`, { username, password });
      localStorage.setItem('token', data.access);
      setToken(data.access);

      // Set Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${data.access}`;

      // Fetch user profile immediately
      const profile = await axios.get(`${API_BASE}/auth/profile/`);
      setUser({
        id: profile.data.id,
        username: profile.data.username,
        role: profile.data.role,
      });

      setLoading(false);
    } catch (err) {
      setLoading(false);
      if (err.response?.status === 401) throw new Error("Invalid credentials");
      else throw new Error("Something went wrong. Try again.");
    }
  };


  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
