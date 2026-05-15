import { NavLink } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">🍽 Restaurant Finder</div>

      <div className="navbar-links">
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
      </div>
    </nav>
  );
}

export default Navbar;
