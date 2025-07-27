import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import onnx
from onnx_tf.backend import prepare
import tensorflow as tf
import os

# Model and paths
MODEL_ID = "models/gemma3n-local”
EXPORT_DIR = "./gemma3n_onnx"
TFLITE_PATH = "./gemma3n.tflite"

os.makedirs(EXPORT_DIR, exist_ok=True)

# Load model with unfused kernels (force standard attention)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    torch_dtype=torch.float32,  # Use fp32 for export clarity
    max_seq_length=128,         # Unsloth disables fused kernels if set low
)

tokenizer = AutoTokenizer.frogitm_pretrained(MODEL_ID)

# Dummy input for export
inputs = tokenizer("Hello, how are you?", return_tensors="pt")

# Export to ONNX
onnx_path = os.path.join(EXPORT_DIR, "gemma3n.onnx")

print("[INFO] Exporting model to ONNX...")

torch.onnx.export(
    model,
    (inputs["input_ids"], inputs["attention_mask"]),
    onnx_path,
    input_names=["input_ids", "attention_mask"],
    output_names=["logits"],
    dynamic_axes={
        "input_ids": {0: "batch", 1: "sequence"},
        "attention_mask": {0: "batch", 1: "sequence"},
        "logits": {0: "batch", 1: "sequence"},
    },
    opset_version=17,
)

print(f"[INFO] Exported ONNX model to {onnx_path}")

# Load ONNX and convert to TFLite via TensorFlow
print("[INFO] Converting ONNX to TFLite...")

onnx_model = onnx.load(onnx_path)
tf_rep = prepare(onnx_model)  # Converts ONNX to TensorFlow

# Export to SavedModel temporarily
saved_model_dir = os.path.join(EXPORT_DIR, "saved_model")
tf_rep.export_graph(saved_model_dir)

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open(TFLITE_PATH, "wb") as f:
    f.write(tflite_model)

print(f"[SUCCESS] TFLite model saved at {TFLITE_PATH}")
