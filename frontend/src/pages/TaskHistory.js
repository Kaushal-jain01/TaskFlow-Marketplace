import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../config/api';

// const API_BASE = 'https://microtasks-api.onrender.com/api';

export default function ClaimedTasks({ userId }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClaimedTasks();
  }, []);

  const fetchClaimedTasks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tasks/?type=history`);
      setTasks(res.data);
    } catch (err) {
      console.error('Error fetching history tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-3">
      <h4>Previous Tasks</h4>
      {loading ? (
        <div className="d-flex justify-content-center mt-5">
          <div className="spinner-border" role="status" />
        </div>
      ) : tasks.length === 0 ? (
        <p>No tasks found in History.</p>
      ) : (
        tasks.map(task => (
          <div key={task.id} className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">{task.title}</h5>
              <p className="card-text">{task.description}</p>
              <p className="card-text">
                <small className="text-muted">
                  Price: ₹{task.price} | Duration: {task.duration_minutes} mins
                </small>
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
