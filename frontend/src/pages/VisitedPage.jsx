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
  const [message, setMessage] = useState("");

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
  }

  function handleEditVisited(restaurant) {
    setMessage("");
    setEditingId(restaurant.id);
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
        setMessage("Visited restaurant updated successfully.");
      } else {
        await createVisitedRestaurant(payload);
        setMessage("Restaurant added to your visited list.");
      }

      resetForm();
      onRefresh();
    } catch (error) {
      console.error(error);
      setMessage(
        editingId !== null
          ? "Failed to update visited restaurant."
          : error.message || "Failed to create visited restaurant."
      );
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
    } catch (error) {
      console.error(error);
      setMessage("Failed to delete restaurant.");
    }
  }

  return (
    <section className="section-card">
      <h2>My Visited Restaurants</h2>
      <p className="section-subtitle">
        Manage the restaurants you already visited.
      </p>

      {message && <div className="message-box">{message}</div>}

      <form className="visited-form" onSubmit={handleManualSubmit}>
        <input
          type="text"
          name="name"
          placeholder="Restaurant name"
          value={manualForm.name}
          onChange={handleManualFormChange}
          required
        />
        <input
          type="text"
          name="city"
          placeholder="City"
          value={manualForm.city}
          onChange={handleManualFormChange}
          required
        />
        <input
          type="text"
          name="country"
          placeholder="Country"
          value={manualForm.country}
          onChange={handleManualFormChange}
          required
        />
        <input
          type="text"
          name="cuisine"
          placeholder="Cuisine"
          value={manualForm.cuisine}
          onChange={handleManualFormChange}
          required
        />

        <div className="field-with-label">
          <label htmlFor="price_level">Price Level (1-5)</label>
          <input
            id="price_level"
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
          <label htmlFor="rating">Rating (1-5)</label>
          <input
            id="rating"
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

        <label className="checkbox-label">
          <input
            type="checkbox"
            name="is_open"
            checked={manualForm.is_open}
            onChange={handleManualFormChange}
          />
          Is Open
        </label>

        <div className="form-actions">
          <button type="submit" className="primary-button">
            {editingId !== null ? "Update Visited Restaurant" : "Add Visited Restaurant"}
          </button>

          {editingId !== null && (
            <button
              type="button"
              className="secondary-button"
              onClick={resetForm}
            >
              Cancel Edit
            </button>
          )}
        </div>
      </form>

      {visitedRestaurants.length === 0 ? (
        <div className="empty-state">
          You have not added any visited restaurants yet.
        </div>
      ) : (
        <div className="visited-list">
          {visitedRestaurants.map((restaurant) => (
            <div key={restaurant.id} className="visited-item">
              <div>
                <strong>{restaurant.name}</strong>
                <p>
                  {restaurant.city}, {restaurant.country}
                </p>
                <div className="card-meta">
                  <span className="meta-badge">{restaurant.cuisine}</span>
                  <span className="meta-badge">Price {restaurant.price_level}/5</span>
                  <span className="meta-badge">Rating {restaurant.rating}/5</span>
                </div>
              </div>

              <div className="item-actions">
                <button
                  className="primary-button"
                  onClick={() => handleEditVisited(restaurant)}
                >
                  Edit
                </button>

                <button
                  className="danger-button"
                  onClick={() => handleDeleteVisited(restaurant.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default VisitedPage;