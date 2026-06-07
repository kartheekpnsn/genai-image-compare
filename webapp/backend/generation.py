"""Build the 6 model clients and run them in parallel for one prompt."""

from __future__ import annotations

import base64
import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from genai_image_compare.gpt_image_generator import AzureGPTImageGenerator
from genai_image_compare.mai_generator import AzureMAIGenerator

MAI_MODELS = ["MAI-Image-2.5", "MAI-Image-2.5-Flash", "MAI-Image-2e"]
GPT_MODELS = ["gpt-image-1-mini", "gpt-image-1.5", "gpt-image-2"]

def build_clients() -> dict[str, object]:
    """Construct one client per model from environment configuration."""
    load_dotenv()
    scope = os.getenv("AZURE_AUTH_SCOPE",
                      "https://cognitiveservices.azure.com/.default")
    width = os.getenv("AZURE_IMAGE_WIDTH", "1024")
    height = os.getenv("AZURE_IMAGE_HEIGHT", "1024")
    n = int(os.getenv("AZURE_IMAGE_N", "1"))

    clients: dict[str, object] = {}
    for gpt_model in GPT_MODELS:
        clients[gpt_model] = AzureGPTImageGenerator(
            endpoint=os.getenv("GPT_IMAGE_ENDPOINT", ""),
            scope=scope,
            model=gpt_model,
            size=f"{width}x{height}",
            quality="low",
            output_compression=100,
            output_format="png",
            n=n,
        )
    for mai_model in MAI_MODELS:
        clients[mai_model] = AzureMAIGenerator(
            endpoint=os.getenv("MAI_ENDPOINT", ""),
            scope=scope,
            model=mai_model,
            width=int(width),
            height=int(height),
            n=n,
        )
    return clients


def _run_one(model: str, client: object, prompt: str) -> dict:
    start = time.time()
    try:
        image_bytes = client.generate(prompt)
        return {
            "model": model,
            "image_b64": base64.b64encode(image_bytes).decode("ascii"),
            "seconds": round(time.time() - start, 2),
            "error": None,
        }
    except Exception as error:  # isolate per-model failure
        return {"model": model, "image_b64": None,
                "seconds": round(time.time() - start, 2), "error": str(error)}


def generate_stream(prompt: str, clients: dict[str, object]) -> Iterator[dict]:
    """Yield one result dict per model in completion order; never raises."""
    with ThreadPoolExecutor(max_workers=max(1, len(clients))) as executor:
        future_to_model = {
            executor.submit(_run_one, model, client, prompt): model
            for model, client in clients.items()
        }
        for future in as_completed(future_to_model):
            yield future.result()
