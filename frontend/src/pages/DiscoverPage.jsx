import { useEffect, useMemo, useRef, useState } from "react";
import {
  createRefreshJob,
  createVisitedRestaurant,
  getAiRecommendation,
  getDiscoverCities,
  getDiscoverRestaurants,
  getRefreshJob,
} from "../api";

function DiscoverPage({ onRestaurantAdded, visitedRestaurants }) {
  // ── Discover catalogue state ────────────────────────────────────────────────
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState(null);
  const [restaurants, setRestaurants] = useState([]);
  const [catalogueLoading, setCatalogueLoading] = useState(true);
  const [catalogueError, setCatalogueError] = useState(null);

  // ── Client-side filters ─────────────────────────────────────────────────────
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCuisine, setSelectedCuisine] = useState("All");

  // ── Add-to-visited message ──────────────────────────────────────────────────
  const [message, setMessage] = useState("");
  const [messageIsError, setMessageIsError] = useState(false);

  // ── Refresh state ───────────────────────────────────────────────────────────
  const [refreshStatus, setRefreshStatus] = useState(null); // null | 'loading' | 'polling' | 'done' | 'failed'
  const [refreshResult, setRefreshResult] = useState(null);
  const [refreshError, setRefreshError] = useState(null);
  const pollRef = useRef(null);

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => () => stopPolling(), []);

  function startPolling(jobId) {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const data = await getRefreshJob(jobId);
        if (data.status === "done") {
          stopPolling();
          setRefreshResult(data.result);
          setRefreshStatus("done");
        } else if (data.status === "failed") {
          stopPolling();
          setRefreshError(data.error || "The refresh job failed.");
          setRefreshStatus("failed");
        }
      } catch (err) {
        stopPolling();
        setRefreshError(err.message);
        setRefreshStatus("failed");
      }
    }, 2000);
  }

  async function handleRefresh() {
    setRefreshStatus("loading");
    setRefreshResult(null);
    setRefreshError(null);
    try {
      const { job_id } = await createRefreshJob();
      setRefreshStatus("polling");
      startPolling(job_id);
    } catch (err) {
      setRefreshError(err.message);
      setRefreshStatus("failed");
    }
  }

  function handleRetry() {
    setRefreshStatus(null);
    setRefreshError(null);
  }

  // ── AI recommendation state ─────────────────────────────────────────────────
  const [aiStatus, setAiStatus] = useState(null); // null | 'loading' | 'done' | 'failed'
  const [aiResult, setAiResult] = useState(null);
  const [aiError, setAiError] = useState(null);
  const [aiExcludedNames, setAiExcludedNames] = useState([]);

  async function handleAiRecommendation(excludedNames = []) {
    setAiStatus("loading");
    setAiResult(null);
    setAiError(null);
    try {
      const data = await getAiRecommendation(excludedNames);
      setAiResult(data);
      setAiStatus("done");
    } catch (err) {
      setAiError(err.message);
      setAiStatus("failed");
    }
  }

  function handleAskAgain() {
    const newExcluded = [...aiExcludedNames, aiResult.restaurant_name];
    setAiExcludedNames(newExcluded);
    handleAiRecommendation(newExcluded);
  }

  // ── Load city list on mount ─────────────────────────────────────────────────
  useEffect(() => {
    async function loadCities() {
      try {
        const data = await getDiscoverCities();
        setCities(data);
        const defaultCity = data.includes("Tel Aviv") ? "Tel Aviv" : (data[0] ?? null);
        setSelectedCity(defaultCity);
        // catalogueLoading stays true until the restaurant effect completes
      } catch (err) {
        setCatalogueError(err.message);
        setCatalogueLoading(false);
      }
    }
    loadCities();
  }, []);

  // ── Load restaurants whenever selected city changes ─────────────────────────
  useEffect(() => {
    if (!selectedCity) return;
    async function loadRestaurants() {
      setCatalogueLoading(true);
      setCatalogueError(null);
      try {
        const data = await getDiscoverRestaurants(selectedCity === "All" ? null : selectedCity);
        setRestaurants(data);
        setSelectedCuisine("All");
      } catch (err) {
        setCatalogueError(err.message);
      } finally {
        setCatalogueLoading(false);
      }
    }
    loadRestaurants();
  }, [selectedCity]);

  // ── Derived: unique cuisines from current city's restaurants ────────────────
  const cuisines = useMemo(() => {
    const unique = [...new Set(restaurants.map((r) => r.cuisine))].sort();
    return ["All", ...unique];
  }, [restaurants]);

  // ── Derived: client-side filter on fetched list ─────────────────────────────
  const filteredRestaurants = useMemo(() => {
    return restaurants.filter((r) => {
      const matchesSearch = r.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCuisine = selectedCuisine === "All" || r.cuisine === selectedCuisine;
      return matchesSearch && matchesCuisine;
    });
  }, [restaurants, searchTerm, selectedCuisine]);

  function isAlreadyVisited(restaurant) {
    return visitedRestaurants.some(
      (v) =>
        v.name.trim().toLowerCase() === restaurant.name.trim().toLowerCase() &&
        v.city.trim().toLowerCase() === restaurant.city.trim().toLowerCase() &&
        v.country.trim().toLowerCase() === restaurant.country.trim().toLowerCase()
    );
  }

  async function handleAddToVisited(restaurant) {
    if (isAlreadyVisited(restaurant)) {
      setMessage(`"${restaurant.name}" is already in My Visited Restaurants.`);
      setMessageIsError(false);
      return;
    }
    try {
      setMessage("");
      await createVisitedRestaurant({
        name: restaurant.name,
        city: restaurant.city,
        country: restaurant.country,
        cuisine: restaurant.cuisine,
        price_level: restaurant.price_level,
        rating: restaurant.rating,
        is_open: Boolean(restaurant.is_open),
      });
      await onRestaurantAdded();
      setMessage(`"${restaurant.name}" was added to My Visited Restaurants.`);
      setMessageIsError(false);
    } catch (error) {
      console.error(error);
      setMessage(error.message || "Failed to add restaurant to visited list.");
      setMessageIsError(true);
    }
  }

  const isRefreshing = refreshStatus === "loading" || refreshStatus === "polling";

  return (
    <section className="section-card">
      <div className="discover-header">
        <div>
          <h2>Discover Restaurants</h2>
          <p className="section-subtitle">
            Explore recommended restaurants and save the ones you already visited.
          </p>
        </div>

        <div className="discover-actions">
          <button
            className="primary-button"
            onClick={() => { setAiExcludedNames([]); handleAiRecommendation([]); }}
            disabled={aiStatus === "loading"}
          >
            {aiStatus === "loading" ? "Asking AI…" : "Get AI Recommendation"}
          </button>

          <button
            className="primary-button refresh-btn"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing…" : "Analyze My Dining Summary"}
          </button>
        </div>
      </div>

      {/* ── Refresh result / error panel ── */}
      {refreshStatus === "failed" && (
        <div className="refresh-panel refresh-panel--error">
          <p className="refresh-panel__message">Refresh failed: {refreshError}</p>
          <button className="secondary-button sm-button" onClick={handleRetry}>
            Try again
          </button>
        </div>
      )}

      {refreshStatus === "done" && refreshResult && (
        <div className="refresh-panel refresh-panel--done">
          <div className="refresh-panel__header">
            <span className="refresh-panel__title">Your Dining Summary</span>
            <button className="secondary-button sm-button" onClick={handleRefresh}>
              Refresh again
            </button>
          </div>

          <div className="summary-grid">
            <div className="summary-stat">
              <span className="summary-stat__value">{refreshResult.total_visited}</span>
              <span className="summary-stat__label">Restaurants visited</span>
            </div>

            {refreshResult.top_cuisine && (
              <div className="summary-stat">
                <span className="summary-stat__value">{refreshResult.top_cuisine}</span>
                <span className="summary-stat__label">Top cuisine</span>
              </div>
            )}

            {refreshResult.avg_rating != null && (
              <div className="summary-stat">
                <span className="summary-stat__value">{refreshResult.avg_rating}</span>
                <span className="summary-stat__label">Avg rating</span>
              </div>
            )}

            {refreshResult.highest_rated && (
              <div className="summary-stat">
                <span className="summary-stat__value">{refreshResult.highest_rated.name}</span>
                <span className="summary-stat__label">
                  Highest rated · {refreshResult.highest_rated.rating}
                </span>
              </div>
            )}
          </div>

          {refreshResult.by_cuisine && Object.keys(refreshResult.by_cuisine).length > 0 && (
            <div className="cuisine-breakdown">
              <p className="cuisine-breakdown__label">By cuisine</p>
              <div className="cuisine-breakdown__list">
                {Object.entries(refreshResult.by_cuisine).map(([cuisine, stats]) => (
                  <span key={cuisine} className="cuisine-chip">
                    {cuisine} · {stats.count} {stats.count === 1 ? "visit" : "visits"} · avg{" "}
                    {stats.avg_rating}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── AI recommendation panel ── */}
      {aiStatus === "failed" && (
        <div className="ai-panel ai-panel--error">
          <p className="ai-panel__message">AI recommendation failed: {aiError}</p>
          <button
            className="secondary-button sm-button"
            onClick={() => setAiStatus(null)}
          >
            Try again
          </button>
        </div>
      )}

      {aiStatus === "done" && aiResult && (
        <div className="ai-panel ai-panel--done">
          <div className="ai-panel__header">
            <span className="ai-panel__label">AI Recommendation</span>
            <button
              className="secondary-button sm-button"
              onClick={handleAskAgain}
            >
              Ask again
            </button>
          </div>

          <div className="ai-rec-card">
            <p className="ai-rec-card__name">{aiResult.restaurant_name}</p>
            <p className="ai-rec-card__city">{aiResult.city}</p>
            <p className="ai-rec-card__reason">{aiResult.reason}</p>
          </div>
        </div>
      )}

      {/* ── Add-to-visited message ── */}
      {message && (
        <div className={`message-box${messageIsError ? " error" : ""}`}>{message}</div>
      )}

      {/* ── Filters ── */}
      <div className="filters">
        <div className="filter-group dropdown">
          <label htmlFor="city-select">City</label>
          <select
            id="city-select"
            value={selectedCity ?? ""}
            onChange={(e) => setSelectedCity(e.target.value)}
            disabled={cities.length === 0}
          >
            <option value="All">All</option>
            {cities.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group search">
          <label htmlFor="search-input">Search</label>
          <input
            id="search-input"
            type="text"
            placeholder="Restaurant name…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group dropdown">
          <label htmlFor="cuisine-select">Cuisine</label>
          <select
            id="cuisine-select"
            value={selectedCuisine}
            onChange={(e) => setSelectedCuisine(e.target.value)}
          >
            {cuisines.map((cuisine) => (
              <option key={cuisine} value={cuisine}>
                {cuisine}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ── Results count (hidden while loading or in error state) ── */}
      {!catalogueLoading && !catalogueError && (
        <div className="results-row">
          <div className="results-pill">{filteredRestaurants.length} results</div>
        </div>
      )}

      {/* ── Main content area ── */}
      {catalogueLoading ? (
        <div className="empty-state">
          <span className="empty-state-icon">⏳</span>
          <p>Loading restaurants…</p>
        </div>
      ) : catalogueError ? (
        <div className="message-box error">Could not load restaurants: {catalogueError}</div>
      ) : filteredRestaurants.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon">🔍</span>
          <p>No restaurants match your filters.</p>
          <p>Try adjusting the search term or clearing a filter.</p>
        </div>
      ) : (
        <div className="cards-grid">
          {filteredRestaurants.map((restaurant) => {
            const alreadyVisited = isAlreadyVisited(restaurant);
            return (
              <div key={restaurant.id} className="restaurant-card">
                <div className="card-body">
                  <h3>{restaurant.name}</h3>
                  <p className="card-location">
                    {restaurant.city}, {restaurant.country}
                  </p>
                  <div className="card-meta">
                    <span className="meta-badge">{restaurant.cuisine}</span>
                    <span className="meta-badge">★ {restaurant.rating}</span>
                  </div>
                  <button
                    className={alreadyVisited ? "secondary-button card-button" : "primary-button card-button"}
                    onClick={() => handleAddToVisited(restaurant)}
                    disabled={alreadyVisited}
                  >
                    {alreadyVisited ? "Already Visited" : "Add to My Visited"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default DiscoverPage;
