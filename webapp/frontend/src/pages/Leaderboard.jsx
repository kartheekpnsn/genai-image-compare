import { useEffect, useState } from "react";

const MEDAL = ["🥇", "🥈", "🥉"];

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [totalVotes, setTotalVotes] = useState(0);
  const [target, setTarget] = useState(36);

  async function load() {
    const r = await fetch("/api/leaderboard");
    const data = await r.json();
    setLeaderboard(data.leaderboard);
    setTotalVotes(data.total_votes);
    setTarget(data.target);
  }

  useEffect(() => { load(); }, []);

  const maxRating = leaderboard.length ? Math.max(...leaderboard.map((r) => r.rating)) : 1200;
  const minRating = leaderboard.length ? Math.min(...leaderboard.map((r) => r.rating)) : 800;
  const ratingSpan = maxRating - minRating || 1;

  return (
    <div className="page">
      <h1>Model Leaderboard</h1>
      <p className="muted" style={{ marginBottom: 24 }}>
        Based on {totalVotes} vote{totalVotes !== 1 ? "s" : ""} out of {target} target
        {totalVotes >= target && (
          <span style={{ color: "var(--ms-green)", fontWeight: 600, marginLeft: 8 }}>
            ✓ Round complete
          </span>
        )}
      </p>

      {/* Rating bar chart */}
      <div style={{ marginBottom: 32, display: "flex", flexDirection: "column", gap: 12 }}>
        {leaderboard.map((row) => {
          const barPct = Math.round(((row.rating - minRating) / ratingSpan) * 100);
          const totalGames = row.games + row.skips;
          const winRate = totalGames > 0 ? Math.round((row.wins / (row.games || 1)) * 100) : 0;
          return (
            <div key={row.model} className="card" style={{ padding: "14px 18px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                <span style={{ fontSize: 22, width: 30, textAlign: "center" }}>
                  {MEDAL[row.rank - 1] ?? row.rank}
                </span>
                <span style={{ fontWeight: 600, flex: 1 }}>{row.model}</span>
                <span style={{ fontWeight: 700, fontSize: 20, color: "var(--ms-blue)" }}>
                  {Math.round(row.rating)}
                </span>
              </div>
              <div className="progress" style={{ marginBottom: 6 }}>
                <div style={{ width: `${Math.max(barPct, 4)}%`, background: row.rank === 1 ? "var(--ms-green)" : "var(--ms-blue)" }} />
              </div>
              <div style={{ display: "flex", gap: 20, fontSize: 13, color: "var(--text-muted)" }}>
                <span>Games: <strong>{row.games}</strong></span>
                <span>Wins: <strong>{row.wins}</strong></span>
                <span>Losses: <strong>{row.losses}</strong></span>
                <span>Skips: <strong>{row.skips}</strong></span>
                <span>Win rate: <strong>{winRate}%</strong></span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Full stats table */}
      <h2 style={{ fontWeight: 600 }}>Full Stats</h2>
      <table className="table">
        <thead>
          <tr>
            <th>#</th><th>Model</th><th>ELO</th><th>Games</th>
            <th>W</th><th>L</th><th>Skips</th><th>Win %</th>
          </tr>
        </thead>
        <tbody>
          {leaderboard.map((row) => {
            const winRate = row.games > 0 ? Math.round((row.wins / row.games) * 100) : "—";
            return (
              <tr key={row.model}>
                <td>{MEDAL[row.rank - 1] ?? row.rank}</td>
                <td style={{ fontWeight: 600 }}>{row.model}</td>
                <td style={{ color: "var(--ms-blue)", fontWeight: 600 }}>{Math.round(row.rating)}</td>
                <td>{row.games}</td>
                <td style={{ color: "var(--ms-green)" }}>{row.wins}</td>
                <td style={{ color: "var(--ms-orange)" }}>{row.losses}</td>
                <td className="muted">{row.skips}</td>
                <td>{typeof winRate === "number" ? `${winRate}%` : winRate}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div style={{ marginTop: 16, textAlign: "right" }}>
        <button className="btn secondary" style={{ fontSize: 13 }} onClick={load}>
          Refresh
        </button>
      </div>
    </div>
  );
}
