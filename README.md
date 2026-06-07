---
title: GenAI Image Compare
description: Side-by-side benchmark of Azure GPT-Image and MAI image-generation models, with a class-based Python client, dotenv configuration, and UV package management.
---

## Overview

This project benchmarks Azure image-generation models side by side on a shared set
of prompts. Two thin clients wrap the Azure endpoints:

* `AzureGPTImageGenerator` — [src/genai_image_compare/gpt_image_generator.py](src/genai_image_compare/gpt_image_generator.py)
* `AzureMAIGenerator` — [src/genai_image_compare/mai_generator.py](src/genai_image_compare/mai_generator.py)

Both expose a `generate(prompt)` method that returns image bytes. The notebook
[notebooks/compare_generators.ipynb](notebooks/compare_generators.ipynb) runs every
model over the benchmark prompts in parallel, caches the rendered images, and records
generation timings.

## Project Structure

```
.
├── src/genai_image_compare/   # Importable package: the two generator clients
│   ├── gpt_image_generator.py
│   └── mai_generator.py
├── notebooks/
│   └── compare_generators.ipynb   # Side-by-side comparison + timing chart
├── data/
│   ├── prompts/prompts.csv        # Benchmark prompts consumed by the notebook
│   ├── images/<model>/<id>.png    # Cached generated images, one folder per model
│   └── results/timing_results.csv # Per-model generation timings
└── docs/
    ├── INSIGHTS.md                # Model comparison summary
    ├── prompts.md                 # Benchmark methodology + final prompt set
    └── sources/                   # Raw per-source prompt suggestions
        ├── claude.md
        ├── gemini.md
        └── gpt.md
```

## Prerequisites

* Python 3.11+
* [uv](https://docs.astral.sh/uv/)
* An Azure AI resource with GPT-Image and/or MAI deployments

## Configuration

Set values in `.env`:

* `GPT_IMAGE_ENDPOINT` — GPT-Image generation endpoint
* `MAI_ENDPOINT` — MAI generation endpoint
* `MAI_MODEL` — MAI model name (default `MAI-Image-2.5`)
* `AZURE_AUTH_SCOPE` — token scope (default `https://cognitiveservices.azure.com/.default`)
* `AZURE_IMAGE_WIDTH`, `AZURE_IMAGE_HEIGHT` — image size (default `1024` x `1024`)
* `AZURE_IMAGE_N` — number of images per prompt (default `1`)

Authentication uses `DefaultAzureCredential`, so make sure you are logged in
(e.g. `az login`) or have the appropriate environment credentials available.

## Install Dependencies

```bash
uv sync
```

This also installs the `genai_image_compare` package from `src/` into the
environment, so the generators can be imported as
`from genai_image_compare import AzureGPTImageGenerator, AzureMAIGenerator`.

## Run

Run the full comparison from the notebook:

```bash
uv run jupyter lab notebooks/compare_generators.ipynb
```

Or smoke-test a single generator from the command line (writes a sample
`*_generated_image.png` to the current directory, which is git-ignored):

```bash
uv run python src/genai_image_compare/gpt_image_generator.py
uv run python src/genai_image_compare/mai_generator.py
```

## Output

* Generated images are cached under `data/images/<model>/<prompt-id>.png`. The
  notebook skips regenerating an image if it already exists.
* Per-model generation timings are written to `data/results/timing_results.csv`
  and summarized in a bar chart at the end of the notebook.
* See [docs/INSIGHTS.md](docs/INSIGHTS.md) for a qualitative model comparison.
