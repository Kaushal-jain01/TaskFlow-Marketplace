import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import API_BASE from '../config/api';
import { Elements } from "@stripe/react-stripe-js";
import { stripePromise } from "../stripe";
import StripePayment from "../components/StripePayment";



export default function TaskDetail() {
  const { id } = useParams(); // task id from URL
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  // Completion states (worker)
  const [completionDetails, setCompletionDetails] = useState('');
  const [proofImage, setProofImage] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Comments
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');

  // Payments
  const [clientSecret, setClientSecret] = useState(null);
  const [showPayment, setShowPayment] = useState(false);
  const [billingDetails, setBillingDetails] = useState(null);

  const fetchTask = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tasks/${id}/`);
      setTask(res.data);
    } catch (err) {
      console.error('Failed to load task', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tasks/${id}/comments/`);
      setComments(res.data);
    } catch (err) {
      console.error('Failed to load comments');
    }
  };

  useEffect(() => {
    fetchTask();
    fetchComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // -------------------------
  // Worker: Complete Task
  // -------------------------
  const handleCompleteTask = async () => {
    if (!proofImage || !completionDetails.trim()) {
      alert('Please provide proof image and completion details');
      return;
    }

    const formData = new FormData();
    formData.append('proof_image', proofImage);
    formData.append('completion_details', completionDetails);

    try {
      setSubmitting(true);
      await axios.patch(
        `${API_BASE}/tasks/${id}/complete/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      alert('✅ Task completed successfully');
      setCompletionDetails('');
      setProofImage(null);
      fetchTask();
      fetchComments();
    } catch (err) {
      alert('❌ Failed to complete task');
    } finally {
      setSubmitting(false);
    }
  };

  // -------------------------
  // Business: Approve Task
  // -------------------------
  const handleApproveTask = async () => {
    try {
      await axios.patch(`${API_BASE}/tasks/${id}/approve/`);
      alert('✅ Task approved');
      fetchTask();
    } catch (err) {
      alert('❌ Failed to approve task');
    }
  };

  // -------------------------
  // Business: Pay for a Task
  // -------------------------
  const handlePayTask = async () => {
    // try {
    //     await axios.patch(`${API_BASE}/tasks/${id}/pay/`);
    //     alert('✅ Task marked as paid');
    //     fetchTask(); // refresh task details
    // } catch (err) {
    //     alert('❌ Failed to pay task');
    // }

    try {
      const token = localStorage.getItem("token");

      const res = await axios.patch(
        `${API_BASE}/tasks/${id}/pay/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      console.log(res)

      setClientSecret(res.data.client_secret);
      setBillingDetails(res.data.billing_details)
      setShowPayment(true);
    //   fetchTask(); // refresh task details
    } catch (err) {
      console.error(err.response?.data || err.message);
      alert("Failed to initiate payment");
    }
    };


  // -------------------------
  // Add Comment
  // -------------------------
  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    try {
      await axios.post(`${API_BASE}/tasks/${id}/comments/`, {
        message: newComment
      });
      setNewComment('');
      fetchComments();
    } catch (err) {
      alert('Failed to add comment');
    }
  };

  // -------------------------
  // UI
  // -------------------------
  if (loading) {
    return (
      <div className="d-flex justify-content-center vh-100 align-items-center">
        <div className="spinner-border" role="status" />
      </div>
    );
  }

  if (!task) return <p>Task not found.</p>;

  return (
    <div className="p-3">
      <h3>{task.title}</h3>
      <p>{task.description}</p>
      <p>
        <small className="text-muted">
          Price: ₹{task.price} | Duration: {task.duration_minutes} mins
        </small>
      </p>
      <p>Status: <strong>{task.status}</strong></p>
      <p>Created by: {task.created_by?.username}</p>
      {task.claimed_by && <p>Claimed by: {task.claimed_by.username}</p>}

      {/* Proof + completion (if completed) */}
      {task.status === 'completed' && task.completion && (
        <div className="mt-3 border p-2">
          <h5>Completion Details:</h5>
          <p>{task.completion.completion_details}</p>
          {task.completion.proof_image && (
           <img
            src={`${API_BASE.replace(/\/api\/$/, '')}${task.completion.proof_image}`}
            alt="Proof"
            className="img-fluid"
          />
          )}
        </div>
      )}

      {/* Worker: Complete Task Form */}
      {task.status === 'claimed' && !task.completion && (
        <div className="mt-3 border p-2">
          <h5>Complete Task</h5>
          <div className="mb-2">
            <label className="form-label">Completion Details</label>
            <textarea
              className="form-control"
              rows="3"
              value={completionDetails}
              onChange={(e) => setCompletionDetails(e.target.value)}
            />
          </div>
          <div className="mb-2">
            <label className="form-label">Proof Image</label>
            <input
              type="file"
              className="form-control"
              onChange={(e) => setProofImage(e.target.files[0])}
            />
          </div>
          <button
            className="btn btn-success"
            disabled={submitting}
            onClick={handleCompleteTask}
          >
            {submitting ? 'Submitting...' : 'Submit Completion'}
          </button>
        </div>
      )}

      {/* Business: Approve Task */}
      {task.status === 'completed' && task.created_by && (
        <div className="mt-3">
          <button className="btn btn-primary" onClick={handleApproveTask}>
            Approve Task
          </button>
        </div>
      )}

      {/* Business: Pay Task */}
    {task.status === 'approved' && task.created_by && (
    <div className="mt-3">
        <button className="btn btn-success" onClick={handlePayTask}>
        Pay Task
        </button>
    </div>
    )}

      {/* Comments */}
      <div className="mt-4">
        <h5>Comments</h5>
        {comments.map(c => (
          <div key={c.id} className="border rounded p-2 mb-1">
            <small className="fw-bold">{c.user.username}</small>
            <div>{c.message}</div>
          </div>
        ))}

        <div className="d-flex mt-2">
          <input
            className="form-control me-2"
            placeholder="Add a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <button className="btn btn-secondary" onClick={handleAddComment}>
            Send
          </button>
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
                  billing_details={billingDetails}
                  onSuccess={() => {
                    setShowPayment(false);
                    fetchTask();
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
