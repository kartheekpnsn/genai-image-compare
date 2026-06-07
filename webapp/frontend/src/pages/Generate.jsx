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

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") {
            reader.cancel();
            break;
          }
          const result = JSON.parse(payload);
          setResults((prev) => [...prev, result]);
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const done = results.length;

  return (
    <div className="page">
      <h1>Generate with all 6 models</h1>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
        <textarea
          className="input"
          placeholder="Enter a prompt…"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => (e.key === "Enter" && (e.ctrlKey || e.metaKey)) && generate()}
          style={{ height: "50vh", minHeight: 120, resize: "vertical" }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button className="btn" onClick={generate} disabled={loading || !prompt.trim()}>
            {loading ? "Generating…" : "Generate"}
          </button>
          <span className="muted" style={{ fontSize: 12 }}>Ctrl+Enter to generate</span>
        </div>
      </div>

      {error && <p style={{ color: "var(--ms-orange)" }}>{error}</p>}
      {loading && (
        <p className="muted">
          Waiting for results… ({done} of 6 done)
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {results.map((res) => (
          <div className="card" key={res.model}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
              <p style={{ fontWeight: 600, margin: 0, fontSize: 16 }}>{res.model}</p>
              {res.seconds != null && <span className="muted" style={{ fontSize: 13 }}>{res.seconds}s</span>}
            </div>
            {res.image_b64 ? (
              <img
                src={`data:image/png;base64,${res.image_b64}`}
                alt={res.model}
                style={{ width: "100%", borderRadius: 6, display: "block" }}
              />
            ) : (
              <p style={{ color: "var(--ms-orange)", margin: 0 }}>{res.error}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
