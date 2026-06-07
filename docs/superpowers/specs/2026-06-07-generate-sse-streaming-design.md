# Generate Page — SSE Streaming Design

**Date:** 2026-06-07
**Status:** Approved

## Problem

The current Generate page waits for all 6 models to finish before rendering any results. Users stare at a spinner for up to 30s with no feedback on progress.

## Goal

Results appear on screen the moment each model finishes. All 6 models still run in parallel on the backend; the frontend renders cards in finish order.

## Approach: Server-Sent Events (SSE)

Single HTTP connection from frontend to backend. Backend yields one JSON event per model result as each future completes; frontend appends a card immediately on receipt.

---

## Backend

### `generation.py` — new `generate_stream` function

Replace `generate_all` (which collects all results before returning) with `generate_stream`, a generator that yields results in completion order using `concurrent.futures.as_completed`.

```python
def generate_stream(prompt: str, clients: dict[str, object]):
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        future_to_model = {
            executor.submit(_run_one, model, client, prompt): model
            for model, client in clients.items()
        }
        for future in as_completed(future_to_model):
            yield future.result()
```

`_run_one` is unchanged. `generate_all` is removed — `main.py` is its only caller and it is being replaced.

### `main.py` — `POST /api/generate` becomes a `StreamingResponse`

```python
import json
from fastapi.responses import StreamingResponse

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

Response format per event:
```
data: {"model": "gpt-image-1-mini", "image_b64": "...", "seconds": 8.2, "error": null}\n\n
```
Terminal event:
```
data: [DONE]\n\n
```

---

## Frontend

### `Generate.jsx` — streaming fetch + progressive render

**State:**
- `results: []` — array that grows as events arrive (same shape as today)
- `pending: number` — count of models not yet returned (starts at 6, decrements per event)
- `loading: boolean` — true while stream is open
- `error: string | null` — top-level network/stream error

**`generate()` function:**

```js
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
      buffer = lines.pop(); // keep incomplete last line
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (payload === "[DONE]") { setLoading(false); return; }
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
```

**UI changes:**

- Replace static "Running 6 models in parallel…" message with a live counter: `"Waiting for results… (X of 6 done)"`
- Cards render immediately as each result arrives (fastest first)
- Each card is identical to today's card (model name, timing, image or error)
- No skeleton placeholders — cards simply appear as they arrive

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| One model errors | Its card appears with `res.error` text, same as today |
| Network drops mid-stream | `reader.read()` rejects → top-level error message shown |
| Backend 4xx/5xx before stream starts | `r.ok` check throws → top-level error message |
| Stream ends without `[DONE]` | `done === true` exits loop cleanly; `finally` sets `loading = false` |

---

## Files Changed

| File | Change |
|---|---|
| `webapp/backend/generation.py` | Add `generate_stream`; keep or remove `generate_all` |
| `webapp/backend/main.py` | Change `post_generate` to return `StreamingResponse`; add `json` import |
| `webapp/frontend/src/pages/Generate.jsx` | Replace batch fetch with streaming reader; add `pending` state; update loading UI |

---

## Out of Scope

- Skeleton/placeholder cards while waiting (cards just appear on arrival)
- Ability to cancel an in-flight stream
- Persisting generated images to disk
