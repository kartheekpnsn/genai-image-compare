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


class AzureMAIGenerator:
    """Azure MAI models image generation client."""

    def __init__(
        self,
        *,
        endpoint: str,
        scope: str,
        model: str,
        width: int,
        height: int,
        n: int,
    ) -> None:
        self.endpoint = endpoint
        self.scope = scope
        self.model = model
        self.width = width
        self.height = height
        self.n = n
        self.credential = DefaultAzureCredential()

    def generate(self, prompt: str) -> bytes:
        """Generate an image. Input is prompt, output is image bytes."""
        payload = {
            "prompt": prompt,
            "width": self.width,
            "height": self.height,
            "n": self.n,
            "model": self.model,
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
    OUTPUT_PATH = Path("mai_generated_image.png")

    endpoint = os.getenv("MAI_ENDPOINT")
    scope = os.getenv("AZURE_AUTH_SCOPE", "https://cognitiveservices.azure.com/.default")
    model = os.getenv("MAI_MODEL", "MAI-Image-2.5")
    width = int(os.getenv("AZURE_IMAGE_WIDTH", "1024"))
    height = int(os.getenv("AZURE_IMAGE_HEIGHT", "1024"))
    n = int(os.getenv("AZURE_IMAGE_N", "1"))

    if not endpoint:
        print("Error: endpoint missing. Set MAI_ENDPOINT in .env.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    client = AzureMAIGenerator(
        endpoint=endpoint,
        scope=scope,
        model=model,
        width=width,
        height=height,
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
