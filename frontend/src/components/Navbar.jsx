import { NavLink } from "react-router-dom";

function Navbar({ currentUser, onLogout, theme, onToggleTheme }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        🍽️
        Restaurant Finder
      </div>

      <div className="navbar-links">
        {currentUser ? (
          <>
            <NavLink
              to="/"
              className={({ isActive }) =>
                isActive ? "nav-link active-link" : "nav-link"
              }
            >
              Discover
            </NavLink>

            <NavLink
              to="/visited"
              className={({ isActive }) =>
                isActive ? "nav-link active-link" : "nav-link"
              }
            >
              My Visited
            </NavLink>

            <NavLink
              to="/profile"
              className={({ isActive }) =>
                isActive ? "nav-link active-link" : "nav-link"
              }
            >
              Profile
            </NavLink>

            <span className="nav-divider"></span>

            <span className="nav-user">Welcome, {currentUser.username}</span>

            <button
              className="theme-toggle-btn"
              onClick={onToggleTheme}
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? "☀" : "🌙"}
            </button>

            <button className="nav-logout-btn" onClick={onLogout}>
              Sign out
            </button>
          </>
        ) : (
          <>
            <NavLink
              to="/login"
              className={({ isActive }) =>
                isActive ? "nav-link active-link" : "nav-link"
              }
            >
              Sign in
            </NavLink>

            <NavLink
              to="/register"
              className={({ isActive }) =>
                isActive ? "nav-link active-link" : "nav-link"
              }
            >
              Register
            </NavLink>

            <button
              className="theme-toggle-btn"
              onClick={onToggleTheme}
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? "☀" : "🌙"}
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
