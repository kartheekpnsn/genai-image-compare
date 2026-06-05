import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import Rank from "./pages/Rank.jsx";
import Generate from "./pages/Generate.jsx";
import Insights from "./pages/Insights.jsx";
import Leaderboard from "./pages/Leaderboard.jsx";

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Rank />} />
        <Route path="/generate" element={<Generate />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
      </Routes>
    </>
  );
}
