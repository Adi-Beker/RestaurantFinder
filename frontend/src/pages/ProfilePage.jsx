import { useState } from "react";
import { changePassword } from "../api";

function ProfilePage({ currentUser }) {
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleChangePassword(e) {
    e.preventDefault();

    if (newPw !== confirmPw) {
      setMessage("New passwords do not match.");
      setIsError(true);
      return;
    }

    setLoading(true);
    setMessage("");
    try {
      await changePassword(currentPw, newPw);
      setMessage("Password updated successfully.");
      setIsError(false);
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (err) {
      setMessage(err.message);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="section-card">
      <h2>My Profile</h2>
      <p className="section-subtitle">View your account details and manage your password.</p>

      <div className="profile-info">
        <div className="profile-field">
          <span className="profile-field__label">Username</span>
          <span className="profile-field__value">{currentUser.username}</span>
        </div>
        <div className="profile-field">
          <span className="profile-field__label">Role</span>
          <span className="profile-field__value">{currentUser.role}</span>
        </div>
      </div>

      <h3 className="profile-section-title">Change Password</h3>

      {message && (
        <div className={`message-box${isError ? " error" : ""}`}>{message}</div>
      )}

      <form className="profile-pw-form" onSubmit={handleChangePassword}>
        <div className="field-with-label">
          <label htmlFor="current-pw">Current Password</label>
          <input
            id="current-pw"
            type="password"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="new-pw">New Password</label>
          <input
            id="new-pw"
            type="password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            required
            autoComplete="new-password"
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="confirm-pw">Confirm New Password</label>
          <input
            id="confirm-pw"
            type="password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            required
            autoComplete="new-password"
          />
        </div>

        <div>
          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? "Updating…" : "Update Password"}
          </button>
        </div>
      </form>
    </section>
  );
}

export default ProfilePage;
