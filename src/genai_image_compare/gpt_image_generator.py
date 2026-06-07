#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import base64
import os
import sys
import time
from pathlib import Path

import requests
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_ERROR = 2


class AzureGPTImageGenerator:
    """Azure GPT Image generation client."""

    def __init__(
        self,
        *,
        endpoint: str,
        scope: str,
        model: str,
        size: str,
        quality: str,
        output_compression: int,
        output_format: str,
        n: int,
    ) -> None:
        self.endpoint = endpoint
        self.scope = scope
        self.model = model
        self.endpoint = self.endpoint.replace("{model_name}", self.model)
        self.size = size
        self.quality = quality
        self.output_compression = output_compression
        self.output_format = output_format
        self.n = n
        self.credential = DefaultAzureCredential()

    def generate(self, prompt: str) -> bytes:
        """Generate an image. Input is prompt, output is image bytes."""
        payload = {
            "prompt": prompt,
            "size": self.size,
            "quality": self.quality,
            "output_compression": self.output_compression,
            "output_format": self.output_format,
            "n": self.n,
        }

        access_token = self.credential.get_token(self.scope)
        remaining = access_token.expires_on - time.time()
        print(f"[{self.model}] Token expires in {remaining / 60:.1f} min")
        token = access_token.token

        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.HTTPError as error:
            raise RuntimeError(
                f"HTTP error {response.status_code}: {response.text}"
            ) from error
        except requests.RequestException as error:
            raise RuntimeError(f"Network error: {error}") from error

        try:
            b64_image = response_data["data"][0]["b64_json"]
            return base64.b64decode(b64_image)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise RuntimeError(f"Unexpected response format: {error}") from error


if __name__ == "__main__":
    load_dotenv()

    PROMPT = "Create a brown fox standing in snow"
    OUTPUT_PATH = Path("gpt_generated_image.png")

    endpoint = os.getenv("GPT_IMAGE_ENDPOINT")
    scope = os.getenv("AZURE_AUTH_SCOPE", "https://cognitiveservices.azure.com/.default")
    width = os.getenv("AZURE_IMAGE_WIDTH", "1024")
    height = os.getenv("AZURE_IMAGE_HEIGHT", "1024")
    size = f"{width}x{height}"
    quality = "low"
    output_compression = 100
    output_format = "png"
    n = int(os.getenv("AZURE_IMAGE_N", "1"))

    if not endpoint:
        print("Error: endpoint missing. Set GPT_IMAGE_ENDPOINT in .env.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    model = os.getenv("GPT_IMAGE_MODEL")
    if not model:
        print("Error: model missing. Set GPT_IMAGE_MODEL in .env.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    client = AzureGPTImageGenerator(
        endpoint=endpoint,
        scope=scope,
        model=model,
        size=size,
        quality=quality,
        output_compression=output_compression,
        output_format=output_format,
        n=n,
    )

    try:
        image_bytes = client.generate(PROMPT)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(EXIT_FAILURE)
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        sys.exit(130)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(image_bytes)
    print(f"Saved image to {OUTPUT_PATH}")
    sys.exit(EXIT_SUCCESS)
