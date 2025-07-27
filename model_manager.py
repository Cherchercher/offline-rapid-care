import os
import requests
import json
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch

class ModelManager:
    """Unified Manager for Direct and Edge AI Modes"""

    def __init__(self, mode="auto", android_webview_url="http://localhost:12345"):
        """
        Args:
            mode: "direct", "edge_ai", or "auto"
            android_webview_url: HTTP bridge to Android WebView (for Edge AI)
        """
        self.mode = mode
        self.android_webview_url = android_webview_url
        
        self.direct_model = None
        self.direct_processor = None
        
        if mode == "auto":
            self.mode = self._detect_best_mode()

        print(f"🚀 ModelManager initialized in {self.mode} mode")

    def _detect_best_mode(self):
        """Auto-detect mode: try Edge AI first, fallback to direct"""
        # 1. Try Edge AI (Android WebView bridge)
        try:
            response = requests.get(f"{self.android_webview_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Detected Edge AI (Android WebView bridge), using edge_ai mode.")
                return "edge_ai"
        except Exception as e:
            print(f"Edge AI detection failed: {e}")
            pass

        print("🔄 No Edge AI detected, defaulting to direct mode.")
        return "direct"

    def chat(self, prompt: str):
        """Unified chat interface"""
        if self.mode == "edge_ai":
            return self._chat_edge_ai(prompt)
        else:
            return self._chat_direct(prompt)

    def _chat_edge_ai(self, prompt: str):
        """Call Android MediaPipe Edge AI via HTTP bridge"""
        try:
            print(f"📡 Sending prompt to Edge AI (Android bridge): {self.android_webview_url}/edgeai")
            payload = {"prompt": prompt}
            response = requests.post(f"{self.android_webview_url}/edgeai", json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            return {
                "success": True,
                "response": result.get("text", ""),
                "mode": "edge_ai"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Edge AI error: {str(e)}",
                "mode": "edge_ai"
            }



    def _chat_direct(self, prompt: str):
        """Chat using local model with transformers"""
        try:
            if self.direct_model is None:
                self._load_direct_model()

            messages = [
                {"role": "user", "content": prompt}
            ]

            inputs = self.direct_processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )

            inputs = inputs.to("cpu", dtype=next(self.direct_model.parameters()).dtype)

            outputs = self.direct_model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7
            )

            response_text = self.direct_processor.batch_decode(outputs, skip_special_tokens=True)[0]
            return {
                "success": True,
                "response": response_text.strip(),
                "mode": "direct"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Direct mode error: {str(e)}",
                "mode": "direct"
            }

    def _load_direct_model(self):
        """Load the local Gemma model into CPU"""
        model_path = "./models/gemma3n-local-e2b"

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Local model not found at {model_path}")

        print("📥 Loading Gemma 3n model locally...")

        self.direct_processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

        try:
            self.direct_model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="cpu",
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            print("✅ Model loaded with float16 on CPU")
        except Exception as e:
            print(f"⚠️ float16 load failed: {e}")
            print("🔄 Trying float32...")
            self.direct_model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            print("✅ Model loaded with float32 on CPU")

    def switch_mode(self, new_mode):
        """Switch between modes at runtime"""
        print(f"🔄 Switching from {self.mode} to {new_mode}")
        self.mode = new_mode

    def get_status(self):
        """Return current mode and model status"""
        return {
            "mode": self.mode,
            "direct_loaded": self.direct_model is not None,
            "android_webview_url": self.android_webview_url
        }
