import { useMemo, useState } from "react";
import { createVisitedRestaurant } from "../api";
import { topRestaurants } from "../data/restaurantsData";

function DiscoverPage({ onRestaurantAdded, visitedRestaurants }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("All");
  const [selectedCuisine, setSelectedCuisine] = useState("All");
  const [message, setMessage] = useState("");
  const [messageIsError, setMessageIsError] = useState(false);

  const countries = useMemo(() => {
    const uniqueCountries = [
      ...new Set(topRestaurants.map((restaurant) => restaurant.country)),
    ];
    return ["All", ...uniqueCountries];
  }, []);

  const cuisines = useMemo(() => {
    const uniqueCuisines = [
      ...new Set(topRestaurants.map((restaurant) => restaurant.cuisine)),
    ];
    return ["All", ...uniqueCuisines];
  }, []);

  const filteredRestaurants = useMemo(() => {
    return topRestaurants.filter((restaurant) => {
      const matchesSearch = restaurant.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());

      const matchesCountry =
        selectedCountry === "All" || restaurant.country === selectedCountry;

      const matchesCuisine =
        selectedCuisine === "All" || restaurant.cuisine === selectedCuisine;

      return matchesSearch && matchesCountry && matchesCuisine;
    });
  }, [searchTerm, selectedCountry, selectedCuisine]);

  function isAlreadyVisited(restaurant) {
    return visitedRestaurants.some(
      (visitedRestaurant) =>
        visitedRestaurant.name.trim().toLowerCase() ===
          restaurant.name.trim().toLowerCase() &&
        visitedRestaurant.city.trim().toLowerCase() ===
          restaurant.city.trim().toLowerCase() &&
        visitedRestaurant.country.trim().toLowerCase() ===
          restaurant.country.trim().toLowerCase()
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
        price_level: 3,
        rating: 4.5,
        is_open: true,
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

  return (
    <section className="section-card">
      <h2>Discover Restaurants</h2>
      <p className="section-subtitle">
        Explore recommended restaurants and save the ones you already visited.
      </p>

      {message && (
        <div className={`message-box${messageIsError ? " error" : ""}`}>
          {message}
        </div>
      )}

      <div className="filters">
        <div className="filter-group search">
          <label htmlFor="search-input">Search</label>
          <input
            id="search-input"
            type="text"
            placeholder="Restaurant name..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>

        <div className="filter-group dropdown">
          <label htmlFor="country-select">Country</label>
          <select
            id="country-select"
            value={selectedCountry}
            onChange={(event) => setSelectedCountry(event.target.value)}
          >
            {countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group dropdown">
          <label htmlFor="cuisine-select">Cuisine</label>
          <select
            id="cuisine-select"
            value={selectedCuisine}
            onChange={(event) => setSelectedCuisine(event.target.value)}
          >
            {cuisines.map((cuisine) => (
              <option key={cuisine} value={cuisine}>
                {cuisine}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-row">
        <div className="results-pill">{filteredRestaurants.length} results</div>
      </div>

      {filteredRestaurants.length === 0 ? (
        <div className="empty-state">
          <p>No restaurants match your current filters.</p>
          <p>Try adjusting the search term or clearing a filter.</p>
        </div>
      ) : (
        <div className="cards-grid">
          {filteredRestaurants.map((restaurant) => {
            const alreadyVisited = isAlreadyVisited(restaurant);

            return (
              <div key={restaurant.id} className="restaurant-card">
                <h3>{restaurant.name}</h3>

                <p className="card-location">
                  {restaurant.city}, {restaurant.country}
                </p>

                <div className="card-meta">
                  <span className="meta-badge">{restaurant.cuisine}</span>
                  {restaurant.worldRank && (
                    <span className="meta-badge">
                      #{restaurant.worldRank} World
                    </span>
                  )}
                </div>

                <button
                  className={
                    alreadyVisited
                      ? "secondary-button card-button"
                      : "primary-button card-button"
                  }
                  onClick={() => handleAddToVisited(restaurant)}
                  disabled={alreadyVisited}
                >
                  {alreadyVisited ? "Already Visited" : "Add to My Visited"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default DiscoverPage;
