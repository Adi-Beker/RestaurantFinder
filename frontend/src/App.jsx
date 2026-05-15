import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { getVisitedRestaurants } from "./api";
import Navbar from "./components/Navbar";
import DiscoverPage from "./pages/DiscoverPage";
import VisitedPage from "./pages/VisitedPage";

function App() {
  const [visitedRestaurants, setVisitedRestaurants] = useState([]);

  async function loadVisitedRestaurants() {
    const restaurants = await getVisitedRestaurants();
    setVisitedRestaurants(restaurants);
  }

  useEffect(() => {
    async function loadData() {
      try {
        await loadVisitedRestaurants();
      } catch (error) {
        console.error(error);
      }
    }

    loadData();
  }, []);

  return (
    <div className="app">
      <Navbar />

      <header className="app-header">
        <h1>Restaurant Finder</h1>
        <p>Explore acclaimed restaurants from around the world. Save the ones you've been to.</p>
      </header>

      <main className="app-main">
        <Routes>
          <Route
            path="/"
            element={
              <DiscoverPage
                onRestaurantAdded={loadVisitedRestaurants}
                visitedRestaurants={visitedRestaurants}
              />
            }
          />
          <Route
            path="/visited"
            element={
              <VisitedPage
                visitedRestaurants={visitedRestaurants}
                onRefresh={loadVisitedRestaurants}
              />
            }
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;