import { useEffect, useState } from "react";

export default function Rank() {
  const [matchup, setMatchup] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [totalVotes, setTotalVotes] = useState(0);
  const [target, setTarget] = useState(36);
  const [reveal, setReveal] = useState(null);
  const [loading, setLoading] = useState(false);

  async function loadLeaderboard() {
    const r = await fetch("/api/leaderboard");
    const data = await r.json();
    setLeaderboard(data.leaderboard);
    setTotalVotes(data.total_votes);
    setTarget(data.target);
  }

  async function loadMatchup() {
    setReveal(null);
    setLoading(true);
    const r = await fetch("/api/matchup");
    setMatchup(await r.json());
    setLoading(false);
  }

  useEffect(() => {
    loadLeaderboard();
    loadMatchup();
  }, []);

  async function vote(choice) {
    if (!matchup) return;
    const r = await fetch("/api/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ matchup_id: matchup.matchup_id, choice }),
    });
    const data = await r.json();
    setLeaderboard(data.leaderboard);
    setTotalVotes(data.state.total_votes);
    setReveal(data.reveal);
    setTimeout(loadMatchup, 900); // brief reveal before next pair
  }

  async function reset() {
    await fetch("/api/reset", { method: "POST" });
    await loadLeaderboard();
    await loadMatchup();
  }

  const pct = Math.min(100, Math.round((totalVotes / target) * 100));
  const done = totalVotes >= target;

  return (
    <div className="page">
      <h1>Which image is better?</h1>
      <p className="muted">
        Vote {totalVotes} / {target}{" "}
        {done && (
          <span style={{ color: "var(--ms-green)", fontWeight: 600 }}>
            ✓ Round complete — keep going if you like
          </span>
        )}
      </p>
      <div className="progress" style={{ marginBottom: 24 }}>
        <div style={{ width: `${pct}%` }} />
      </div>

      {matchup && (
        <div className="card" style={{ marginBottom: 32 }}>
          <p className="muted" style={{ margin: 0 }}>{matchup.category}</p>
          <p style={{ marginTop: 4, fontWeight: 600 }}>{matchup.prompt}</p>
          <div className="versus">
            <div>
              <img
                className="choice-img"
                src={matchup.left_image}
                alt="Option A"
                onClick={() => !reveal && vote("left")}
              />
              {reveal && <p className="muted">{reveal.left_model}{!reveal.skipped && reveal.winner === reveal.left_model ? " ✓" : ""}</p>}
            </div>
            <span className="vs">VS</span>
            <div>
              <img
                className="choice-img"
                src={matchup.right_image}
                alt="Option B"
                onClick={() => !reveal && vote("right")}
              />
              {reveal && <p className="muted">{reveal.right_model}{!reveal.skipped && reveal.winner === reveal.right_model ? " ✓" : ""}</p>}
            </div>
          </div>
          <div style={{ textAlign: "center", marginTop: 16 }}>
            <button className="btn secondary" disabled={!!reveal || loading} onClick={() => vote("skip")}>
              Too close to call / Skip
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontWeight: 600 }}>Leaderboard</h2>
        <button className="btn danger" onClick={reset}>Reset ELO</button>
      </div>
      <table className="table">
        <thead>
          <tr><th>#</th><th>Model</th><th>ELO</th><th>Games</th><th>W</th><th>L</th><th>Skips</th></tr>
        </thead>
        <tbody>
          {leaderboard.map((row) => (
            <tr key={row.model}>
              <td>{row.rank}</td>
              <td>{row.model}</td>
              <td>{Math.round(row.rating)}</td>
              <td>{row.games}</td>
              <td>{row.wins}</td>
              <td>{row.losses}</td>
              <td>{row.skips}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
