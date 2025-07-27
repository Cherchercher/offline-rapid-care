#!/usr/bin/env python3
"""
Jetson Load Monitor for Smart Model Selection
Monitors system resources to determine optimal model choice
"""

import psutil
import torch
import os
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class SystemLoad:
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float
    gpu_utilization: float
    temperature: Optional[float]
    concurrent_requests: int
    is_high_load: bool

class JetsonLoadMonitor:
    """Monitor Jetson system load for smart model selection"""
    
    def __init__(self):
        self.high_load_thresholds = {
            'cpu_percent': 80.0,      # CPU usage above 80%
            'memory_percent': 85.0,    # Memory usage above 85%
            'memory_available_gb': 2.0, # Less than 2GB available
            'gpu_memory_percent': 90.0, # GPU memory above 90%
            'temperature': 75.0,       # Temperature above 75°C
            'concurrent_requests': 3    # More than 3 concurrent requests
        }
        
        self.load_history = []
        self.max_history_size = 10
        
    def get_system_load(self) -> SystemLoad:
        """Get current system load metrics"""
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # GPU metrics
        gpu_memory_used_mb = 0
        gpu_memory_total_mb = 0
        gpu_utilization = 0
        temperature = None
        
        try:
            # Try to get GPU info using nvidia-smi
            import subprocess
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
            # Fallback to PyTorch CUDA info
            if torch.cuda.is_available():
                gpu_memory_used_mb = torch.cuda.memory_allocated(0) / (1024**2)
                gpu_memory_total_mb = torch.cuda.get_device_properties(0).total_memory / (1024**2)
                gpu_utilization = 0  # PyTorch doesn't provide utilization directly
        
        # Count concurrent requests (simplified - in real app, track active requests)
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
        
        load = SystemLoad(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            gpu_memory_used_mb=gpu_memory_used_mb,
            gpu_memory_total_mb=gpu_memory_total_mb,
            gpu_utilization=gpu_utilization,
            temperature=temperature,
            concurrent_requests=concurrent_requests,
            is_high_load=is_high_load
        )
        
        # Add to history
        self.load_history.append(load)
        if len(self.load_history) > self.max_history_size:
            self.load_history.pop(0)
        
        return load
    
    def get_load_trend(self) -> Dict:
        """Analyze load trends over time"""
        if len(self.load_history) < 3:
            return {'trend': 'stable', 'confidence': 'low'}
        
        recent_loads = self.load_history[-3:]
        avg_cpu = sum(l.cpu_percent for l in recent_loads) / len(recent_loads)
        avg_memory = sum(l.memory_percent for l in recent_loads) / len(recent_loads)
        
        # Determine trend
        if avg_cpu > 70 or avg_memory > 80:
            trend = 'increasing'
        elif avg_cpu < 30 and avg_memory < 50:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'confidence': 'high' if len(self.load_history) >= 5 else 'medium'
        }
    
    def recommend_model(self, task_type: str = 'general') -> str:
        """Recommend which model to use based on current load"""
        
        current_load = self.get_system_load()
        load_trend = self.get_load_trend()
        
        print(f"📊 Current System Load:")
        print(f"   CPU: {current_load.cpu_percent:.1f}%")
        print(f"   Memory: {current_load.memory_percent:.1f}% ({current_load.memory_available_gb:.1f}GB available)")
        print(f"   GPU Memory: {current_load.gpu_memory_used_mb:.1f}MB / {current_load.gpu_memory_total_mb:.1f}MB")
        if current_load.temperature:
            print(f"   Temperature: {current_load.temperature:.1f}°C")
        print(f"   Concurrent Requests: {current_load.concurrent_requests}")
        print(f"   Load Trend: {load_trend['trend']}")
        
        # Model selection logic
        if current_load.is_high_load:
            print("⚠️ High load detected - recommending 2B model")
            return '2b'
        
        # Task-specific recommendations
        if task_type in ['quick_triage', 'voice_transcription', 'simple_query']:
            print("⚡ Quick task - recommending 2B model for speed")
            return '2b'
        elif task_type in ['complex_analysis', 'video_analysis', 'detailed_assessment']:
            if current_load.memory_available_gb > 3.0:
                print("🎯 Complex task with good resources - recommending 4B model")
                return '4b'
            else:
                print("⚠️ Complex task but limited memory - recommending 2B model")
                return '2b'
        else:
            # Default to 4B for better quality if resources allow
            if current_load.memory_available_gb > 4.0 and current_load.cpu_percent < 60:
                print("✅ Good resources available - recommending 4B model")
                return '4b'
            else:
                print("⚡ Moderate resources - recommending 2B model")
                return '2b'
    
    def get_detailed_report(self) -> Dict:
        """Get detailed system load report"""
        current_load = self.get_system_load()
        load_trend = self.get_load_trend()
        
        return {
            'current_load': {
                'cpu_percent': current_load.cpu_percent,
                'memory_percent': current_load.memory_percent,
                'memory_available_gb': current_load.memory_available_gb,
                'gpu_memory_used_mb': current_load.gpu_memory_used_mb,
                'gpu_memory_total_mb': current_load.gpu_memory_total_mb,
                'gpu_utilization': current_load.gpu_utilization,
                'temperature': current_load.temperature,
                'concurrent_requests': current_load.concurrent_requests,
                'is_high_load': current_load.is_high_load
            },
            'load_trend': load_trend,
            'thresholds': self.high_load_thresholds,
            'recommendation': self.recommend_model()
        }

def test_load_monitor():
    """Test the load monitor"""
    print("🧪 Testing Jetson Load Monitor...")
    
    monitor = JetsonLoadMonitor()
    
    # Test current load
    print("\n📊 Current System Status:")
    load = monitor.get_system_load()
    print(f"   CPU Usage: {load.cpu_percent:.1f}%")
    print(f"   Memory Usage: {load.memory_percent:.1f}%")
    print(f"   Available Memory: {load.memory_available_gb:.1f}GB")
    print(f"   GPU Memory: {load.gpu_memory_used_mb:.1f}MB / {load.gpu_memory_total_mb:.1f}MB")
    print(f"   High Load: {'⚠️ YES' if load.is_high_load else '✅ NO'}")
    
    # Test model recommendation
    print("\n🤖 Model Recommendations:")
    for task_type in ['quick_triage', 'complex_analysis', 'voice_transcription']:
        recommendation = monitor.recommend_model(task_type)
        print(f"   {task_type}: {recommendation.upper()}")
    
    # Get detailed report
    print("\n📋 Detailed Report:")
    report = monitor.get_detailed_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    test_load_monitor() 