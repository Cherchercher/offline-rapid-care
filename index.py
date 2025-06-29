import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

GEMMA_MODEL_ID = "google/gemma-3n-E4B-it"

processor = AutoProcessor.from_pretrained(GEMMA_MODEL_ID, device_map="auto")
model = AutoModelForImageTextToText.from_pretrained(
            GEMMA_MODEL_ID, torch_dtype="auto", device_map="auto")