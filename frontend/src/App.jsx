import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { getMe, getVisitedRestaurants } from "./api";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import DiscoverPage from "./pages/DiscoverPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import VisitedPage from "./pages/VisitedPage";

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [visitedRestaurants, setVisitedRestaurants] = useState([]);
  const [theme, setTheme] = useState(
    () => localStorage.getItem("theme") || "light"
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  async function loadCurrentUser() {
    const token = localStorage.getItem("token");
    if (!token) {
      setAuthLoading(false);
      return;
    }
    try {
      const user = await getMe();
      setCurrentUser(user);
    } catch {
      localStorage.removeItem("token");
    } finally {
      setAuthLoading(false);
    }
  }

  async function loadVisitedRestaurants() {
    try {
      const restaurants = await getVisitedRestaurants();
      setVisitedRestaurants(restaurants);
    } catch (error) {
      console.error(error);
    }
  }

  useEffect(() => {
    loadCurrentUser();
  }, []);

  useEffect(() => {
    if (currentUser) {
      loadVisitedRestaurants();
    }
  }, [currentUser]);

  function handleLogout() {
    localStorage.removeItem("token");
    setCurrentUser(null);
    setVisitedRestaurants([]);
  }

  if (authLoading) return null;

  return (
    <div className="app">
      <Navbar
        currentUser={currentUser}
        onLogout={handleLogout}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {currentUser && (
        <header className="app-header">
          <h1>Discover Restaurants in Israel</h1>
          <p>
            Explore top restaurants across Israel. Save the ones you've visited
            and track your dining history.
          </p>
        </header>
      )}

      <main className="app-main">
        <Routes>
          <Route
            path="/login"
            element={
              currentUser ? (
                <Navigate to="/" replace />
              ) : (
                <LoginPage onLogin={loadCurrentUser} />
              )
            }
          />
          <Route
            path="/register"
            element={
              currentUser ? <Navigate to="/" replace /> : <RegisterPage />
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute currentUser={currentUser}>
                <DiscoverPage
                  onRestaurantAdded={loadVisitedRestaurants}
                  visitedRestaurants={visitedRestaurants}
                />
              </ProtectedRoute>
            }
          />
          <Route
            path="/visited"
            element={
              <ProtectedRoute currentUser={currentUser}>
                <VisitedPage
                  visitedRestaurants={visitedRestaurants}
                  onRefresh={loadVisitedRestaurants}
                />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute currentUser={currentUser}>
                <ProfilePage currentUser={currentUser} />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;
