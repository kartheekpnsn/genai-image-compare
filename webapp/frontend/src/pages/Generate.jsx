import { useState } from "react";

export default function Generate() {
  const [prompt, setPrompt] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function generate() {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!r.ok) throw new Error(`Request failed (${r.status})`);
      const data = await r.json();
      setResults(data.results);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Generate with all 4 models</h1>
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <input
          className="input"
          placeholder="Enter a prompt…"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && generate()}
        />
        <button className="btn" onClick={generate} disabled={loading || !prompt.trim()}>
          {loading ? "Generating…" : "Generate"}
        </button>
      </div>

      {error && <p style={{ color: "var(--ms-orange)" }}>{error}</p>}
      {loading && <p className="muted">Running 4 models in parallel — this can take ~30s.</p>}

      <div className="grid-4">
        {results.map((res) => (
          <div className="card" key={res.model}>
            <p style={{ fontWeight: 600, marginTop: 0 }}>{res.model}</p>
            {res.image_b64 ? (
              <>
                <img
                  src={`data:image/png;base64,${res.image_b64}`}
                  alt={res.model}
                  style={{ width: "100%", borderRadius: 6 }}
                />
                <p className="muted">{res.seconds}s</p>
              </>
            ) : (
              <p style={{ color: "var(--ms-orange)" }}>{res.error}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
