# Generate Page SSE Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the batch `/api/generate` response with a Server-Sent Events stream so each model's result card appears on screen the moment that model finishes, with all 6 still running in parallel on the backend.

**Architecture:** `generation.py` gains a `generate_stream` generator that uses `concurrent.futures.as_completed` to yield results in completion order. `main.py` wraps it in a FastAPI `StreamingResponse` emitting one `data: <json>\n\n` SSE frame per result plus a `data: [DONE]\n\n` sentinel. `Generate.jsx` reads the stream with `fetch` + `ReadableStream` reader, appending a result card to state as each frame arrives.

**Tech Stack:** Python `concurrent.futures.as_completed`, FastAPI `StreamingResponse`, React `useState` + `fetch` streaming with `ReadableStream` reader

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `webapp/backend/generation.py` | Modify | Add `generate_stream`; remove `generate_all` |
| `webapp/backend/main.py` | Modify | Change `post_generate` to return `StreamingResponse` |
| `webapp/backend/tests/test_generation.py` | Modify | Replace `generate_all` tests with `generate_stream` tests |
| `webapp/backend/tests/test_api.py` | Modify | Replace `test_generate_endpoint_uses_clients` with SSE test |
| `webapp/frontend/src/pages/Generate.jsx` | Modify | Streaming fetch + `pending` state + progressive card render |

---

## Task 1: Replace `generate_all` with `generate_stream` in `generation.py`

**Files:**
- Modify: `webapp/backend/generation.py`
- Modify: `webapp/backend/tests/test_generation.py`

- [ ] **Step 1: Write failing tests for `generate_stream`**

Replace the contents of `webapp/backend/tests/test_generation.py` with:

```python
from webapp.backend import generation


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    def generate(self, prompt):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_generate_stream_returns_one_result_per_client():
    clients = {
        "GPT-Image": _FakeClient(b"\x89PNG-gpt"),
        "MAI-Image-2e": _FakeClient(b"\x89PNG-mai"),
    }
    results = list(generation.generate_stream("a cat", clients))
    by_model = {r["model"]: r for r in results}
    assert set(by_model) == {"GPT-Image", "MAI-Image-2e"}
    assert by_model["GPT-Image"]["error"] is None
    assert by_model["GPT-Image"]["image_b64"]
    assert by_model["GPT-Image"]["seconds"] >= 0


def test_generate_stream_isolates_failures():
    clients = {
        "GPT-Image": _FakeClient(b"\x89PNG"),
        "MAI-Image-2e": _FakeClient(RuntimeError("boom")),
    }
    by_model = {r["model"]: r for r in generation.generate_stream("x", clients)}
    assert by_model["GPT-Image"]["error"] is None
    assert by_model["MAI-Image-2e"]["image_b64"] is None
    assert "boom" in by_model["MAI-Image-2e"]["error"]


def test_generate_stream_is_a_generator():
    clients = {"M1": _FakeClient(b"\x89PNG")}
    result = generation.generate_stream("x", clients)
    # Must be a generator, not a list
    import types
    assert isinstance(result, types.GeneratorType)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/kartheek/Documents/kartheek/Work/Engagements/Personal/genai-image-compare
python -m pytest webapp/backend/tests/test_generation.py -v
```

Expected: `FAILED` — `AttributeError: module 'generation' has no attribute 'generate_stream'`

- [ ] **Step 3: Implement `generate_stream` and remove `generate_all`**

In `webapp/backend/generation.py`:

1. Change the import line from:
```python
from concurrent.futures import ThreadPoolExecutor
```
to:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

2. Replace the `generate_all` function (lines 66-73) with:
```python
def generate_stream(prompt: str, clients: dict[str, object]):
    """Yield one result dict per model in completion order; never raises."""
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        future_to_model = {
            executor.submit(_run_one, model, client, prompt): model
            for model, client in clients.items()
        }
        for future in as_completed(future_to_model):
            yield future.result()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest webapp/backend/tests/test_generation.py -v
```

Expected: 3 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add webapp/backend/generation.py webapp/backend/tests/test_generation.py
git commit -m "feat: replace generate_all with generate_stream using as_completed"
```

---

## Task 2: Change `/api/generate` to SSE `StreamingResponse`

**Files:**
- Modify: `webapp/backend/main.py`
- Modify: `webapp/backend/tests/test_api.py`

- [ ] **Step 1: Write failing test for the SSE endpoint**

In `webapp/backend/tests/test_api.py`:

Replace the `test_generate_endpoint_uses_clients` test (lines 66–77) with:

```python
import json as _json


def test_generate_streams_sse_events(client, monkeypatch):
    from webapp.backend import main

    fake_results = [
        {"model": "M1", "image_b64": "abc", "seconds": 1.0, "error": None},
        {"model": "M2", "image_b64": "xyz", "seconds": 2.0, "error": None},
    ]

    monkeypatch.setattr(main, "_get_clients", lambda: {"M1": object(), "M2": object()})
    monkeypatch.setattr(
        main.generation, "generate_stream", lambda p, c: iter(fake_results)
    )

    r = client.post("/api/generate", json={"prompt": "a fox"})
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]

    payloads = [
        line[6:]
        for line in r.text.splitlines()
        if line.startswith("data: ")
    ]
    assert payloads[-1] == "[DONE]"
    events = [_json.loads(p) for p in payloads[:-1]]
    assert {e["model"] for e in events} == {"M1", "M2"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest webapp/backend/tests/test_api.py::test_generate_streams_sse_events -v
```

Expected: `FAILED` — `AssertionError` on `text/event-stream` check (endpoint still returns JSON)

- [ ] **Step 3: Update `main.py` to return `StreamingResponse`**

In `webapp/backend/main.py`:

1. Change the imports:
```python
# Before:
from fastapi.responses import FileResponse

# After:
import json
from fastapi.responses import FileResponse, StreamingResponse
```

2. Replace the `post_generate` function:
```python
@app.post("/api/generate")
def post_generate(req: GenerateRequest) -> StreamingResponse:
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be empty")

    def event_stream():
        for result in generation.generate_stream(prompt, _get_clients()):
            yield f"data: {json.dumps(result)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 4: Run the full backend test suite**

```bash
python -m pytest webapp/backend/tests/ -v
```

Expected: All tests `PASSED` including `test_generate_streams_sse_events` and `test_generate_requires_prompt`

- [ ] **Step 5: Commit**

```bash
git add webapp/backend/main.py webapp/backend/tests/test_api.py
git commit -m "feat: stream generate results via SSE (text/event-stream)"
```

---

## Task 3: Update `Generate.jsx` to consume the SSE stream

**Files:**
- Modify: `webapp/frontend/src/pages/Generate.jsx`

- [ ] **Step 1: Rewrite `Generate.jsx` with streaming fetch**

Replace the entire contents of `webapp/frontend/src/pages/Generate.jsx` with:

```jsx
import { useState } from "react";

export default function Generate() {
  const [prompt, setPrompt] = useState("");
  const [results, setResults] = useState([]);
  const [pending, setPending] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function generate() {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResults([]);
    setPending(6);

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
            setLoading(false);
            return;
          }
          const result = JSON.parse(payload);
          setResults((prev) => [...prev, result]);
          setPending((p) => p - 1);
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
              {res.seconds && <span className="muted" style={{ fontSize: 13 }}>{res.seconds}s</span>}
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
```

- [ ] **Step 2: Start the dev server and manually verify**

In two terminals:

```bash
# Terminal 1 — backend
cd /Users/kartheek/Documents/kartheek/Work/Engagements/Personal/genai-image-compare
make backend   # or: uvicorn webapp.backend.main:app --port 8175 --reload
```

```bash
# Terminal 2 — frontend
cd /Users/kartheek/Documents/kartheek/Work/Engagements/Personal/genai-image-compare
make frontend  # or: cd webapp/frontend && npm run dev -- --port 5175
```

Open http://localhost:5175, go to Generate, enter a prompt, click Generate.

Expected behaviour:
- Counter shows "Waiting for results… (0 of 6 done)" immediately
- Cards appear one by one as each model finishes (fastest first)
- Counter increments: "1 of 6 done", "2 of 6 done", …
- Loading indicator disappears after all 6 arrive (or after `[DONE]` event)

- [ ] **Step 3: Commit**

```bash
git add webapp/frontend/src/pages/Generate.jsx
git commit -m "feat: stream model results one by one as they finish (SSE)"
```

---

## Self-Review Notes

- `generate_stream` is tested as a generator, for completeness, and for failure isolation — matches spec section "Backend".
- `[DONE]` sentinel is emitted by `event_stream()` and asserted in `test_generate_streams_sse_events` — matches spec "Error Handling".
- Frontend `pending` state starts at 6 (hardcoded) because there are always exactly 6 clients — simple and correct for this codebase.
- `test_generate_requires_prompt` in `test_api.py` is unchanged — the 422 guard is still in `post_generate` before the stream starts, so it still works.
- The old `test_generate_endpoint_uses_clients` is fully replaced by `test_generate_streams_sse_events` — no orphaned test.
