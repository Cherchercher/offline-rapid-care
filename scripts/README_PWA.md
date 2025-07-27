# RapidCare - AI-Powered Mass Casualty Incident Response System

A Progressive Web App (PWA) that leverages on-device AI models via direct model inference for emergency response coordination during mass casualty incidents.

## 🚀 Features

### Core Functionality
- **Offline-First Design**: Works without internet connection
- **AI-Powered Chat**: Real-time communication with Gemma 3n model
- **Role-Based Interface**: Different views for various emergency roles
- **Voice Input**: Speech-to-text capabilities for hands-free operation
- **Patient Management**: Triage categorization and tracking
- **Real-time Status**: Live connection monitoring with AI models

### Emergency Response Roles
- **PARAMEDIC/EMT**: Field triage and patient assessment
- **NURSE**: Patient monitoring and vital updates
- **PHYSICIAN**: Medical decision making and treatment approval
- **REUNIFICATION_COORDINATOR**: Family member location and matching
- **LOGISTICS**: Supply management and resource tracking
- **TRANSFER_AGENT**: Patient transport coordination
- **MEDICAL_ASSISTANT**: Clinical support and documentation
- **ADMIN**: System oversight and role management

### PWA Features
- **Installable**: Add to home screen on mobile/desktop
- **Offline Caching**: Service worker for offline functionality
- **Push Notifications**: Real-time alerts and updates
- **Background Sync**: Queue actions when offline
- **Responsive Design**: Works on all device sizes

## 🛠 Technology Stack

### Frontend
- **HTML5/CSS3**: Modern, responsive interface
- **JavaScript (ES6+)**: Progressive Web App functionality
- **Service Workers**: Offline caching and background sync
- **IndexedDB**: Local data storage
- **Web Speech API**: Voice input capabilities

### Backend
- **Flask**: Python web framework
- **Direct Model Inference**: Local AI model hosting
- **Gemma 3n**: On-device language model
- **RESTful APIs**: JSON-based communication

### AI/ML
- **Gemma 3n (E4B)**: Google's latest multimodal model
- **Role-specific Prompts**: Context-aware AI responses
- **Fine-tuning Ready**: Compatible with Unsloth for customization

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- Node.js 16+ (for development tools)
- 8GB+ RAM (for AI model)
- Modern web browser with PWA support

### Required Software
1. **Python Dependencies**: See `requirements.txt`
2. **Gemma 3n Model**: Download via `scripts/download_gemma_models.py`

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Download AI Model
```bash
# Download the Gemma 3n model
python3 scripts/download_gemma_models.py --model 2b

# Verify installation
python3 scripts/dynamic_model_manager.py
```

### 3. Generate Icons
```bash
# Install Pillow if not already installed
pip install Pillow

# Generate PWA icons
python generate_icons.py
```

### 4. Start the Application
```bash
# Start the Flask application
python app.py
```

### 5. Access the Application
- Open your browser to: `http://localhost:5000`
- The app will be available as a PWA
- Install to home screen for offline access

## 🎯 Demo Scenarios

### Scenario 1: Paramedic Field Assessment
1. Select "PARAMEDIC" role
2. Use voice input: "Unconscious male, visible bleeding from head, rapid pulse"
3. AI responds with triage classification and next steps
4. Add patient to system with Red triage level

### Scenario 2: Nurse Vital Updates
1. Select "NURSE" role
2. Click "Update Vitals" quick action
3. Input: "Patient 204: BP 120/80, HR 95, temp 98.6"
4. AI processes and logs the information

### Scenario 3: Family Reunification
1. Select "REUNIFICATION_COORDINATOR" role
2. Input: "Search for Maya Thompson, age 10"
3. AI searches patient database and provides location

### Scenario 4: Supply Management
1. Select "LOGISTICS" role
2. Click "Check Supplies" quick action
3. Input: "Request 5 IV kits at triage tent A"
4. AI logs request and provides availability status

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Customize model endpoint
export MODEL_BASE_URL="http://localhost:5001"

# Optional: Customize model name
export GEMMA_MODEL="gemma3n:e4b"
```

### Customization Options
- **Model Fine-tuning**: Use Unsloth with your training data
- **Role Permissions**: Modify role capabilities in `app.py`
- **UI Themes**: Customize colors in `static/css/style.css`
- **Offline Behavior**: Configure service worker caching strategies

## 📱 PWA Installation

### Mobile Devices
1. Open the app in Chrome/Safari
2. Tap the "Add to Home Screen" prompt
3. Or use browser menu → "Add to Home Screen"

### Desktop
1. Open the app in Chrome/Edge
2. Click the install icon in the address bar
3. Or use browser menu → "Install RapidCare"

### Offline Usage
- App works offline after first load
- Patient data cached locally
- Actions queued for sync when online

## 🔒 Security Considerations

### Data Privacy
- All data processed locally via direct model inference
- No cloud dependencies for core functionality
- Patient data stored in browser IndexedDB
- Optional encryption for sensitive data

### Access Control
- Role-based permissions
- Audit logging of all interactions
- Session management for sensitive operations

## 🧪 Testing

### Manual Testing
```bash
# Test model connection
curl http://localhost:5001/chat

# Test Flask API
curl http://localhost:5000/api/status

# Test chat endpoint
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message", "role": "PARAMEDIC"}'
```

### Automated Testing
```bash
# Run Python tests (when implemented)
python -m pytest tests/

# Run JavaScript tests (when implemented)
npm test
```

## 🚀 Deployment

### Local Development
```bash
# Development mode with auto-reload
export FLASK_ENV=development
python app.py
```

### Production Deployment
```bash
# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Python: Follow PEP 8
- JavaScript: Use ESLint configuration
- CSS: Follow BEM methodology
- Commit messages: Use conventional commits

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google**: For the Gemma 3n model
- **Direct Model Inference**: For local model hosting
- **Flask**: For the web framework
- **Emergency Responders**: For domain expertise and feedback

## 📞 Support

### Issues and Bugs
- Report issues on GitHub
- Include system information and error logs
- Provide steps to reproduce

### Feature Requests
- Use GitHub discussions
- Describe use case and expected behavior
- Consider implementation complexity

### Emergency Support
- For critical issues during deployment
- Contact: [Your Contact Information]
- Response time: Within 4 hours

---

**Note**: This is a demonstration system. For production use in emergency situations, additional testing, validation, and compliance with local regulations is required. 