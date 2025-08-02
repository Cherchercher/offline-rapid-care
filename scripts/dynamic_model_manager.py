#!/usr/bin/env python3
"""
Dynamic Model Manager for Jetson
Automatically selects between 2B and 4B models based on system load
"""

import os
import torch
import psutil
import subprocess
from typing import Dict, Optional
from pathlib import Path

class DynamicModelManager:
    """Manages dynamic model selection based on system capabilities and load"""
    
    def __init__(self):
        self.model_2b_path = "./models/gemma3n-2b"
        self.model_4b_path = "./models/gemma3n-4b"
        self.current_model_path = None
        self.current_model = None
        self.current_processor = None
        
        # Load thresholds
        self.high_load_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'memory_available_gb': 2.0,
            'gpu_memory_percent': 90.0,
            'temperature': 75.0,
            'concurrent_requests': 3
        }
    
    def get_system_load(self) -> Dict:
        """Get current system load metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Get GPU metrics if available
        gpu_memory_used_mb = 0
        gpu_memory_total_mb = 0
        gpu_utilization = 0
        temperature = None
        
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 4:
                            gpu_memory_used_mb = float(parts[0])
                            gpu_memory_total_mb = float(parts[1])
                            gpu_utilization = float(parts[2])
                            temperature = float(parts[3])
        except:
            pass
        
        # Count concurrent requests
        concurrent_requests = len([p for p in psutil.process_iter(['pid', 'name']) 
                                 if 'python' in p.info['name'].lower() and 'app.py' in ' '.join(p.cmdline())])
        
        # Determine if system is under high load
        is_high_load = (
            cpu_percent > self.high_load_thresholds['cpu_percent'] or
            memory_percent > self.high_load_thresholds['memory_percent'] or
            memory_available_gb < self.high_load_thresholds['memory_available_gb'] or
            (gpu_memory_total_mb > 0 and (gpu_memory_used_mb / gpu_memory_total_mb * 100) > self.high_load_thresholds['gpu_memory_percent']) or
            (temperature and temperature > self.high_load_thresholds['temperature']) or
            concurrent_requests > self.high_load_thresholds['concurrent_requests']
        )
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': memory_available_gb,
            'gpu_memory_used_mb': gpu_memory_used_mb,
            'gpu_memory_total_mb': gpu_memory_total_mb,
            'gpu_utilization': gpu_utilization,
            'temperature': temperature,
            'concurrent_requests': concurrent_requests,
            'is_high_load': is_high_load
        }
    
    def get_device_capabilities(self) -> Dict:
        """Get device capabilities"""
        capabilities = {
            "is_jetson": self._is_jetson_device(),
            "has_cuda": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "memory_available": None,
            "offline_processing_supported": False
        }
        
        try:
            capabilities["memory_available"] = psutil.virtual_memory().available / (1024**3)
        except:
            pass
        
        if capabilities["is_jetson"]:
            capabilities["offline_processing_supported"] = True
        elif capabilities["has_cuda"] and capabilities["memory_available"] and capabilities["memory_available"] > 4:
            capabilities["offline_processing_supported"] = True
        else:
            capabilities["offline_processing_supported"] = False
        
        return capabilities
    
    def _is_jetson_device(self) -> bool:
        """Check if running on a Jetson device"""
        try:
            jetson_indicators = [
                "/etc/nv_tegra_release",
                "/proc/device-tree/model",
                "/sys/module/tegra_fuse/parameters/tegra_chip_id"
            ]
            
            for indicator in jetson_indicators:
                if os.path.exists(indicator):
                    return True
            
            if torch.cuda.is_available():
                try:
                    device_name = torch.cuda.get_device_name(0).lower()
                    if 'tegra' in device_name or 'jetson' in device_name or 'xavier' in device_name:
                        return True
                except:
                    pass
            
            return False
        except:
            return False
    
    def select_optimal_model(self, task_type: str = 'general') -> str:
        """Select the optimal model based on system load and task type"""
        
        system_load = self.get_system_load()
        device_capabilities = self.get_device_capabilities()
        
        print(f"📊 System Load Analysis:")
        print(f"   CPU: {system_load['cpu_percent']:.1f}%")
        print(f"   Memory: {system_load['memory_percent']:.1f}% ({system_load['memory_available_gb']:.1f}GB available)")
        print(f"   GPU Memory: {system_load['gpu_memory_used_mb']:.1f}MB / {system_load['gpu_memory_total_mb']:.1f}MB")
        print(f"   High Load: {'⚠️ YES' if system_load['is_high_load'] else '✅ NO'}")
        print(f"   Device: {'🚀 Jetson' if device_capabilities['is_jetson'] else '💻 Desktop'}")
        
        # Model selection logic
        if system_load['is_high_load']:
            print("⚠️ High load detected - selecting 2B model")
            return '2b'
        
        # Task-specific recommendations
        if task_type in ['quick_triage', 'voice_transcription', 'simple_query']:
            print("⚡ Quick task - selecting 2B model for speed")
            return '2b'
        elif task_type in ['complex_analysis', 'video_analysis', 'detailed_assessment']:
            if system_load['memory_available_gb'] > 3.0:
                print("🎯 Complex task with good resources - selecting 4B model")
                return '4b'
            else:
                print("⚠️ Complex task but limited memory - selecting 2B model")
                return '2b'
        else:
            # Default selection based on device capabilities
            if device_capabilities['is_jetson'] and system_load['memory_available_gb'] > 4.0:
                print("✅ Jetson with good resources - selecting 4B model")
                return '4b'
            else:
                print("⚡ Standard environment - selecting 2B model")
                return '2b'
    
    def get_model_path(self, model_size: str = None) -> str:
        """Get the path for the specified model size"""
        if model_size is None:
            model_size = self.select_optimal_model()
        
        if model_size.lower() == '2b':
            return self.model_2b_path
        elif model_size.lower() == '4b':
            return self.model_4b_path
        else:
            raise ValueError(f"Unknown model size: {model_size}")
    
    def check_model_availability(self) -> Dict:
        """Check which models are available"""
        availability = {
            '2b': os.path.exists(self.model_2b_path),
            '4b': os.path.exists(self.model_4b_path)
        }
        
        print(f"📁 Model Availability:")
        print(f"   2B Model: {'✅ Available' if availability['2b'] else '❌ Not found'}")
        print(f"   4B Model: {'✅ Available' if availability['4b'] else '❌ Not found'}")
        
        return availability
    
    def load_model(self, model_size: str = None):
        """Load the specified model"""
        from transformers import AutoProcessor, AutoModelForImageTextToText
        
        model_size = model_size or self.select_optimal_model()
        model_path = self.get_model_path(model_size)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        print(f"🔄 Loading {model_size.upper()} model from {model_path}...")
        
        # Load processor and model
        self.current_processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        self.current_model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        self.current_model_path = model_path
        print(f"✅ {model_size.upper()} model loaded successfully!")
        
        return self.current_model, self.current_processor

def test_dynamic_model_manager():
    """Test the dynamic model manager"""
    print("🧪 Testing Dynamic Model Manager...")
    
    manager = DynamicModelManager()
    
    # Check model availability
    availability = manager.check_model_availability()
    
    # Test model selection
    print(f"\n🤖 Model Selection Tests:")
    for task_type in ['quick_triage', 'complex_analysis', 'voice_transcription']:
        selected_model = manager.select_optimal_model(task_type)
        print(f"   {task_type}: {selected_model.upper()}")
    
    # Test model loading (if available)
    if availability['2b'] or availability['4b']:
        print(f"\n🔄 Testing model loading...")
        try:
            model, processor = manager.load_model()
            print(f"✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
    else:
        print(f"\n⚠️ No models available. Please download models first:")
        print(f"   python3 scripts/download_gemma_models.py --model both")

if __name__ == "__main__":
    test_dynamic_model_manager() 