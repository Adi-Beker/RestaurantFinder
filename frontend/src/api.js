const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function buildError(response, fallbackMessage) {
  try {
    const data = await response.json();
    return new Error(data.detail || fallbackMessage);
  } catch {
    return new Error(fallbackMessage);
  }
}

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function registerUser(username, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw await buildError(response, "Registration failed");
  return response.json();
}

export async function loginUser(username, password) {
  const body = new URLSearchParams({ username, password });
  const response = await fetch(`${API_BASE_URL}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!response.ok) throw await buildError(response, "Invalid credentials");
  return response.json();
}

export async function getMe() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw await buildError(response, "Failed to fetch user");
  return response.json();
}

export async function changePassword(currentPassword, newPassword) {
  const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  if (!response.ok) throw await buildError(response, "Failed to change password");
}

// ── Refresh jobs ─────────────────────────────────────────────────────────────

export async function createRefreshJob() {
  const response = await fetch(`${API_BASE_URL}/refresh-jobs`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!response.ok) throw await buildError(response, "Failed to start refresh job");
  return response.json();
}

export async function getRefreshJob(jobId) {
  const response = await fetch(`${API_BASE_URL}/refresh-jobs/${jobId}`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw await buildError(response, "Failed to fetch job status");
  return response.json();
}

// ── AI recommendation ─────────────────────────────────────────────────────────

export async function getAiRecommendation(excludedNames = []) {
  const params = excludedNames.length > 0
    ? "?" + excludedNames.map(n => `exclude=${encodeURIComponent(n)}`).join("&")
    : "";
  const response = await fetch(`${API_BASE_URL}/ai/recommendation${params}`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw await buildError(response, "Failed to get AI recommendation");
  return response.json();
}

// ── Discover catalogue ────────────────────────────────────────────────────────

export async function getDiscoverCities() {
  const response = await fetch(`${API_BASE_URL}/discover/cities`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw await buildError(response, "Failed to fetch cities");
  return response.json();
}

export async function getDiscoverRestaurants(city) {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const response = await fetch(`${API_BASE_URL}/discover/restaurants${params}`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw await buildError(response, "Failed to fetch discover restaurants");
  return response.json();
}

// ── Restaurants ───────────────────────────────────────────────────────────────

export async function getVisitedRestaurants() {
  const response = await fetch(`${API_BASE_URL}/restaurants`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw await buildError(response, "Failed to fetch visited restaurants");
  }
  return response.json();
}

export async function createVisitedRestaurant(restaurantData) {
  const response = await fetch(`${API_BASE_URL}/restaurants`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(restaurantData),
  });

  if (!response.ok) {
    throw await buildError(response, "Failed to create restaurant");
  }

  return response.json();
}

export async function updateVisitedRestaurant(id, restaurantData) {
  const response = await fetch(`${API_BASE_URL}/restaurants/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(restaurantData),
  });

  if (!response.ok) {
    throw await buildError(response, "Failed to update restaurant");
  }

  return response.json();
}

export async function deleteVisitedRestaurant(id) {
  const response = await fetch(`${API_BASE_URL}/restaurants/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });

  if (!response.ok) {
    throw await buildError(response, "Failed to delete restaurant");
  }

  return true;
}
