"""Azure image-generation clients used to compare GPT-Image and MAI models."""

from genai_image_compare.gpt_image_generator import AzureGPTImageGenerator
from genai_image_compare.mai_generator import AzureMAIGenerator

__all__ = ["AzureGPTImageGenerator", "AzureMAIGenerator"]
