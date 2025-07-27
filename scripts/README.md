# RapidCare Scripts

This folder contains utility scripts, test files, and development tools that are not part of the core RapidCare application.

## 📁 Script Categories

### 🧪 Test Scripts
- `test_*.py` - Various test files for different components
- `test_setup.py` - Comprehensive setup testing
- `test_endpoints.py` - API endpoint testing
- `test_model_api.py` - Model API testing
- `test_video_analysis.py` - Video analysis testing
- `test_video_frames.py` - Video frame processing testing
- `test_ocr.py` - OCR functionality testing
- `test_vector_search.py` - Vector search testing

### 🤖 Model Management
- `model_manager_pipeline.py` - Pipeline-based model manager
- `model_server.py` - Standalone model API server
- `direct_gemma_server.py` - Direct Gemma model server
- `run_gemma_local.py` - Local Gemma model runner
- `run_gemma_offload.py` - Offloaded Gemma model runner

### 🔧 Model Optimization
- `aggressive_reduction.py` - Aggressive model size reduction
- `reduce_model_size.py` - Model size optimization
- `check_model_dtype.py` - Model data type checking
- `download_gemma_local.py` - Local model downloader

### 🗄️ Database Utilities
- `list_vector_db.py` - Vector database listing utility
- `flush_vector_db.py` - Vector database cleanup utility

### 🔍 Analysis Tools
- `jetson_size_check.py` - Jetson device size checking
- `license_scanner.py` - License scanning utility
- `convert_audio.py` - Audio format conversion

### 📚 Documentation & Examples
- `curl_examples.md` - cURL API examples
- `EdgeAIHTTPServer.kt` - Android Edge AI server example
- `Modelfile.*` - Various model configuration files
- `README_PWA.md` - PWA documentation

### 🎯 Development
- `demo.py` - Demo script (empty)
- `index.py` - Index script (not main app)

## 🚀 Usage

Most of these scripts are standalone utilities. To use them:

```bash
# Example: Run a test
python3 scripts/test_setup.py

# Example: Download local model
python3 scripts/download_gemma_local.py

# Example: Check vector database
python3 scripts/list_vector_db.py
```

## 📝 Notes

- These scripts are **NOT** used by the main RapidCare application
- They are kept for development, testing, and utility purposes
- The main application files remain in the root directory
- Startup scripts (`tmux_start.sh`, `start.sh`) only reference files in the root directory

## 🔗 Related Files

The following files remain in the root directory as they are used by the main application:
- `app.py` - Main Flask application
- `model_manager_api.py` - API model manager
- `database_setup.py` - Database setup
- `vector_search.py` - Vector search functionality
- `prompts.py` - AI prompts
- `serve_uploads.py` - Upload server (used by startup scripts)
- `generate_icons.py` - Icon generation (used by startup scripts) 