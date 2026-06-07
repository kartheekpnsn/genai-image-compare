---
title: GenAI Image Compare
description: Side-by-side benchmark of Azure GPT-Image and MAI image-generation models with a voting-based ELO leaderboard and live generation UI.
---

## Overview

A full-stack benchmarking tool for Azure image-generation models. Users vote on blind head-to-head matchups (which image looks better for a given prompt?), and an ELO rating system derives a live leaderboard from those votes. A separate **Generate** tab lets you enter any prompt and watch both models produce images side by side in real time via server-sent events.

Two thin Python clients wrap the Azure endpoints:

* `AzureGPTImageGenerator` — [src/genai_image_compare/gpt_image_generator.py](src/genai_image_compare/gpt_image_generator.py)
* `AzureMAIGenerator` — [src/genai_image_compare/mai_generator.py](src/genai_image_compare/mai_generator.py)

Both expose a `generate(prompt)` method that returns image bytes. The original comparison notebook is still available at [notebooks/compare_generators.ipynb](notebooks/compare_generators.ipynb).

## Project Structure

```
.
├── src/genai_image_compare/       # Importable package: GPT-Image and MAI clients
│   ├── gpt_image_generator.py
│   └── mai_generator.py
├── webapp/
│   ├── backend/                   # FastAPI app
│   │   ├── main.py                # API routes
│   │   ├── elo.py                 # ELO rating math + persistent state
│   │   ├── matchups.py            # In-memory matchup store
│   │   ├── generation.py          # Parallel SSE generation stream
│   │   ├── data_loader.py         # Prompt and image loading
│   │   └── tests/                 # pytest suite
│   └── frontend/                  # React + Vite app
│       └── src/pages/
│           ├── Rank.jsx           # Blind voting UI
│           ├── Leaderboard.jsx    # ELO rankings table
│           ├── Generate.jsx       # Live prompt-to-image generation
│           └── Insights.jsx       # Model comparison writeup
├── data/
│   ├── prompts/prompts.csv        # Benchmark prompt set
│   ├── images/<model>/<id>.png    # Cached generated images
│   ├── results/timing_results.csv # Per-model generation timings
│   └── elo_state.json             # Persisted ELO ratings and vote history
├── notebooks/
│   └── compare_generators.ipynb   # Original side-by-side notebook
├── docs/
│   └── INSIGHTS.md                # Qualitative model comparison
├── .env.example                   # Template for required environment variables
└── Makefile                       # install / backend / frontend / dev targets
```

## Prerequisites

* Python 3.11+
* Node.js 18+
* [uv](https://docs.astral.sh/uv/)
* An Azure AI resource with GPT-Image and/or MAI deployments

## Configuration

Copy `.env.example` to `.env` and fill in your Azure endpoints:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GPT_IMAGE_ENDPOINT` | Azure OpenAI images endpoint (includes deployment name) |
| `GPT_IMAGE_MODEL` | GPT-Image model name (default `gpt-image-2`) |
| `MAI_ENDPOINT` | MAI generation endpoint |
| `MAI_MODEL` | MAI model name (default `MAI-Image-2.5`) |
| `AZURE_AUTH_SCOPE` | Token scope (default `https://cognitiveservices.azure.com/.default`) |
| `AZURE_IMAGE_WIDTH` / `AZURE_IMAGE_HEIGHT` | Image dimensions (default `1024` × `1024`) |
| `AZURE_IMAGE_N` | Images per prompt (default `1`) |

Authentication uses `DefaultAzureCredential`. Run `az login` (or configure a managed identity / service principal) before starting the server.

## Install

```bash
make install
```

This runs `uv sync` (Python deps + the `genai_image_compare` package) and `npm install` in the frontend.

## Run

### Full dev server (recommended)

```bash
make dev
```

Starts the FastAPI backend on **:8175** and the Vite frontend on **:5175** together. Open [http://localhost:5175](http://localhost:5175).

### Backend or frontend separately

```bash
make backend    # FastAPI on :8175
make frontend   # Vite on :5175
```

### Notebook

```bash
uv run jupyter lab notebooks/compare_generators.ipynb
```

### Smoke-test a single generator

```bash
uv run python src/genai_image_compare/gpt_image_generator.py
uv run python src/genai_image_compare/mai_generator.py
```

Each writes a `*_generated_image.png` to the current directory (git-ignored).

## API Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/matchup` | Get a new blind head-to-head matchup |
| `GET` | `/api/matchup-image/{id}/{side}` | Serve a matchup image |
| `POST` | `/api/vote` | Record a vote; returns updated ELO state |
| `GET` | `/api/leaderboard` | Current ELO rankings |
| `GET` | `/api/state` | Full ELO state JSON |
| `POST` | `/api/reset` | Reset all ratings and history |
| `POST` | `/api/generate` | Stream image generation (SSE) for both models |
| `GET` | `/api/insights` | Return `docs/INSIGHTS.md` as JSON |

## Tests

```bash
uv run pytest
```

Tests live in `webapp/backend/tests/`.
