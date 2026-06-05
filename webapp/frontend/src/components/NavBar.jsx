import { NavLink } from "react-router-dom";

export default function NavBar() {
  return (
    <nav className="nav">
      <span className="brand">GenAI Image Compare</span>
      <NavLink to="/" end>Rank</NavLink>
      <NavLink to="/generate">Generate</NavLink>
      <NavLink to="/insights">Insights</NavLink>
      <NavLink to="/leaderboard">Leaderboard</NavLink>
    </nav>
  );
}
