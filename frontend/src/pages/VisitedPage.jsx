import { useState } from "react";
import {
  createVisitedRestaurant,
  deleteVisitedRestaurant,
  updateVisitedRestaurant,
} from "../api";

function VisitedPage({ visitedRestaurants, onRefresh }) {
  const [manualForm, setManualForm] = useState({
    name: "",
    city: "",
    country: "",
    cuisine: "",
    price_level: 3,
    rating: 4.0,
    is_open: true,
  });
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState("");
  const [message, setMessage] = useState("");
  const [messageIsError, setMessageIsError] = useState(false);

  function handleManualFormChange(event) {
    const { name, value, type, checked } = event.target;

    setManualForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function resetForm() {
    setManualForm({
      name: "",
      city: "",
      country: "",
      cuisine: "",
      price_level: 3,
      rating: 4.0,
      is_open: true,
    });
    setEditingId(null);
    setEditingName("");
  }

  function handleEditVisited(restaurant) {
    setMessage("");
    setEditingId(restaurant.id);
    setEditingName(restaurant.name);
    setManualForm({
      name: restaurant.name,
      city: restaurant.city,
      country: restaurant.country,
      cuisine: restaurant.cuisine,
      price_level: restaurant.price_level,
      rating: restaurant.rating,
      is_open: restaurant.is_open,
    });
  }

  async function handleManualSubmit(event) {
    event.preventDefault();

    try {
      setMessage("");

      const payload = {
        ...manualForm,
        price_level: Number(manualForm.price_level),
        rating: Number(manualForm.rating),
      };

      if (editingId !== null) {
        await updateVisitedRestaurant(editingId, payload);
        setMessage("Restaurant updated successfully.");
        setMessageIsError(false);
      } else {
        await createVisitedRestaurant(payload);
        setMessage("Restaurant added to your visited list.");
        setMessageIsError(false);
      }

      resetForm();
      onRefresh();
    } catch (error) {
      console.error(error);
      setMessage(
        editingId !== null
          ? "Failed to update restaurant."
          : error.message || "Failed to add restaurant."
      );
      setMessageIsError(true);
    }
  }

  async function handleDeleteVisited(id) {
    try {
      setMessage("");
      await deleteVisitedRestaurant(id);
      onRefresh();

      if (editingId === id) {
        resetForm();
      }

      setMessage("Restaurant removed from your visited list.");
      setMessageIsError(false);
    } catch (error) {
      console.error(error);
      setMessage("Failed to delete restaurant.");
      setMessageIsError(true);
    }
  }

  return (
    <section className="section-card">
      <h2>My Visited Restaurants</h2>
      <p className="section-subtitle">
        Manage the restaurants you have already visited.
      </p>

      {message && (
        <div className={`message-box${messageIsError ? " error" : ""}`}>
          {message}
        </div>
      )}

      <p className={`form-heading${editingId !== null ? " editing" : ""}`}>
        {editingId !== null ? `Editing: ${editingName}` : "Add a restaurant"}
      </p>

      <form className="visited-form" onSubmit={handleManualSubmit}>
        <div className="field-with-label">
          <label htmlFor="field-name">Name</label>
          <input
            id="field-name"
            type="text"
            name="name"
            placeholder="e.g. Osteria Francescana"
            value={manualForm.name}
            onChange={handleManualFormChange}
            required
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="field-city">City</label>
          <input
            id="field-city"
            type="text"
            name="city"
            placeholder="e.g. Rome"
            value={manualForm.city}
            onChange={handleManualFormChange}
            required
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="field-country">Country</label>
          <input
            id="field-country"
            type="text"
            name="country"
            placeholder="e.g. Italy"
            value={manualForm.country}
            onChange={handleManualFormChange}
            required
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="field-cuisine">Cuisine</label>
          <input
            id="field-cuisine"
            type="text"
            name="cuisine"
            placeholder="e.g. Italian"
            value={manualForm.cuisine}
            onChange={handleManualFormChange}
            required
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="field-price">Price Level (1–5)</label>
          <input
            id="field-price"
            type="number"
            name="price_level"
            min="1"
            max="5"
            value={manualForm.price_level}
            onChange={handleManualFormChange}
            required
          />
        </div>

        <div className="field-with-label">
          <label htmlFor="field-rating">Rating (1–5)</label>
          <input
            id="field-rating"
            type="number"
            name="rating"
            min="1"
            max="5"
            step="0.1"
            value={manualForm.rating}
            onChange={handleManualFormChange}
            required
          />
        </div>

        <div className="field-with-label">
          <label>Status</label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="is_open"
              checked={manualForm.is_open}
              onChange={handleManualFormChange}
            />
            Currently open
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" className="primary-button">
            {editingId !== null ? "Save Changes" : "Add Restaurant"}
          </button>

          {editingId !== null && (
            <button
              type="button"
              className="secondary-button"
              onClick={resetForm}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {visitedRestaurants.length === 0 ? (
        <div className="empty-state">
          <p>You have not added any visited restaurants yet.</p>
          <p>Use the form above or add one from the Discover page.</p>
        </div>
      ) : (
        <>
          <p className="visited-list-heading">
            Your list ({visitedRestaurants.length})
          </p>

          <div className="visited-list">
            {visitedRestaurants.map((restaurant) => (
              <div
                key={restaurant.id}
                className={`visited-item${editingId === restaurant.id ? " is-editing" : ""}`}
              >
                <div>
                  <strong>{restaurant.name}</strong>
                  <p>
                    {restaurant.city}, {restaurant.country}
                  </p>
                  <div className="card-meta">
                    <span className="meta-badge">{restaurant.cuisine}</span>
                    <span className="meta-badge">
                      Price {restaurant.price_level}/5
                    </span>
                    <span className="meta-badge">
                      Rating {restaurant.rating}/5
                    </span>
                    <span
                      className={`meta-badge ${restaurant.is_open ? "badge-open" : "badge-closed"}`}
                    >
                      {restaurant.is_open ? "Open" : "Closed"}
                    </span>
                  </div>
                </div>

                <div className="item-actions">
                  <button
                    className="primary-button sm-button"
                    onClick={() => handleEditVisited(restaurant)}
                  >
                    Edit
                  </button>

                  <button
                    className="danger-button sm-button"
                    onClick={() => handleDeleteVisited(restaurant.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

export default VisitedPage;
