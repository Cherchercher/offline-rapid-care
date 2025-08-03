# RapidCare: AI-Powered Mass Casualty Incident Response System

## 🚨 The Challenge

In mass casualty events like concerts, wildfires, or emergency situations, the ability to respond swiftly and effectively can make all the difference in saving lives. Each year, countless individuals suffer injuries in these environments, highlighting the urgent need for fast, reliable, and coordinated care. Not to mention that during MCI, internet access might be interrupted. From rapidly assessing injuries to locating missing loved ones, the challenge is immense, and the demand for a seamless, real-time, offline-first response system has never been greater.

## 🚑 The Solution

Enter **RapidCare** — a groundbreaking solution designed to transform emergency response during mass casualty events. Powered by the advanced Gemma 3n AI engine, RapidCare is a voice-activated, multi-role, on-device AI assistant tailored for field triage, coordination, and communication. Whether you're a paramedic, nurse, field agent, or a family member searching for a loved one, RapidCare equips you with the tools needed to act quickly and efficiently.

This cutting-edge app is designed to operate fully offline on mobile devices, including Google Edge AI, Jetson devices, and web browsers, ensuring optimal performance regardless of connectivity. With intelligent medical triage features like video-based assessments, real-time vitals transcription, and patient reunification capabilities, RapidCare serves as a vital assistant to those working on the frontlines and those desperately seeking information.

## 🐳 Quick Start (Docker)

### **For Jetson Devices:**
```bash
# Clone the repository
git clone <your-repo>
cd offline-gemma

# Build and run with Docker (5-minute setup)
./build_and_run.sh

# Access the application
# Web Interface: http://localhost:5050
# Model API: http://localhost:5001
# Upload Server: http://localhost:11435
```

### **For Other Platforms:**
```bash
# Install dependencies
pip install -r requirements.txt

# Download models
python scripts/download_gemma_models.py --model 4b

# Run the application
python app.py
```

## 🏗️ Architecture Overview

### **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    RapidCare System Architecture               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Web Browser   │    │   Mobile PWA    │    │  Desktop    │ │
│  │   (Chrome)      │    │   (Android/iOS) │    │  (Windows)  │ │
│  └─────────┬───────┘    └─────────┬───────┘    └─────┬───────┘ │
│            │                      │                  │         │
│            └──────────────────────┼──────────────────┘         │
│                                   │                            │
│  ┌─────────────────────────────────┼────────────────────────────┐ │
│  │         HTTP Bridge Layer       │                            │ │
│  │  (Progressive Web App)          │                            │ │
│  └─────────────────┬───────────────┘                            │
│                    │                                            │
│  ┌─────────────────┼────────────────────────────────────────────┐ │
│  │              Backend Services                                │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Flask     │ │   Model     │ │     File Upload         │ │ │
│  │  │   App       │ │   Server    │ │     Server              │ │ │
│  │  │  (Port 5050)│ │ (Port 5001) │ │    (Port 11435)         │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                   │                            │
│  ┌─────────────────────────────────┼────────────────────────────┐ │
│  │            AI Models                                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │  Gemma 3n   │ │  Gemma 3n   │ │    Dynamic Model        │ │ │
│  │  │    2B       │ │    4B       │ │    Selection            │ │ │
│  │  │  (CPU)      │ │  (GPU)      │ │    (Load-based)         │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                   │                            │
│  ┌─────────────────────────────────┼────────────────────────────┐ │
│  │            Storage Layer                                      │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   SQLite    │ │   Local     │ │     Offline Sync        │ │ │
│  │  │  Database   │ │   Storage   │ │     Manager             │ │ │
│  │  │ (Patients)  │ │ (Files)     │ │    (Jetson)            │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Docker Deployment Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container Architecture               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Docker Container (offline-gemma-jetson)      │ │
│  │                                                             │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │ │
│  │  │   Flask     │ │   Model     │ │   Upload Server     │   │ │
│  │  │   App       │ │   Server    │ │                     │   │ │
│  │  │ (Port 5050) │ │ (Port 5001) │ │   (Port 11435)      │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              AI Models (Gemma 3n)                      │ │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │ │ │
│  │  │  │   4B Model  │ │   2B Model  │ │   Dynamic       │ │ │ │
│  │  │  │  (Primary)  │ │  (Fallback) │ │   Selection     │ │ │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              Storage Layer                              │ │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │ │ │
│  │  │  │   SQLite    │ │   Uploads   │ │   Offload       │ │ │ │
│  │  │  │  Database   │ │   Directory │ │   Directory     │ │ │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Volume Mounts                                 │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │ │
│  │  │   Models    │ │   Uploads   │ │   Database          │   │ │
│  │  │   (Host)    │ │   (Host)    │ │   (Host)            │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Deployment Options**

| Platform | Setup Time | Model | Performance | Offline Cap. |
|----------|------------|-------|-------------|--------------|
| **Jetson (Docker)** | 5 minutes | 4B | High | ✅ Full |
| **Google Edge AI** | 10 minutes | 4B | Medium | ✅ Full |
| **AWS EC2** | 15 minutes | 2B | Medium | ❌ Limited |
| **Local Desktop** | 20 minutes | 4B | High | ✅ Full |

### **Data Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Flow Diagram                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input ──┐                                                │
│               │                                                │
│  ┌────────────┴────────────┐                                   │
│  │      Media Upload       │                                   │
│  │  (Image/Video/Audio)    │                                   │
│  └────────────┬────────────┘                                   │
│               │                                                │
│  ┌────────────┴────────────┐                                   │
│  │    File Processing      │                                   │
│  │  (Upload Server)        │                                   │
│  └────────────┬────────────┘                                   │
│               │                                                │
│  ┌────────────┴────────────┐                                   │
│  │   Model Selection       │                                   │
│  │  (Load-based Logic)     │                                   │
│  │  • High Load → 2B       │                                   │
│  │  • Low Load → 4B        │                                   │
│  └────────────┬────────────┘                                   │
│               │                                                │
│  ┌────────────┴────────────┐                                   │
│  │    AI Analysis          │                                   │
│  │  (Gemma 3n Model)       │                                   │
│  │  • Medical Triage       │                                   │
│  │  • Patient Assessment   │                                   │
│  └────────────┬────────────┘                                   │
│               │                                                │
│  ┌────────────┴────────────┐                                   │
│  │   Result Processing     │                                   │
│  │  • Triage Level         │                                   │
│  │  • Patient Creation     │                                   │
│  │  • Database Storage     │                                   │
│  └────────────┬────────────┘                                   │
│               │                                                │
│  ┌────────────┴────────────┐                                   │
│  │   Offline Sync          │                                   │
│  │  (When Online)          │                                   │
│  │  • Cloud Storage        │                                   │
│  │  • Data Backup          │                                   │
│  └─────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Technologies:**

#### **Progressive Web App (PWA)**
By leveraging the power of PWA, we ensure that RapidCare is accessible across Web, Android, and iOS platforms, with code written once for broad deployment.

#### **Offline Capabilities**
Through an HTTP Bridge, RapidCare can communicate with on-device AI for tasks like image analysis, enabling the app to function seamlessly without cloud dependence.

#### **Medical Image Triage Fine-tuning**
Our medical image triage system is fine-tuned using Unsloth with comprehensive injury image datasets, extracting precise triage information including:

- **Triage Level Classification**: Red (Immediate), Yellow (Delayed), Green (Minor), Black (Deceased)
- **Detailed Reasoning**: AI-generated explanations for triage decisions based on visual assessment
- **Patient Information Extraction**: Age estimation, gender identification, and brief assessment findings
- **Injury Pattern Recognition**: Automated detection of trauma patterns, bleeding, fractures, and burns
- **Vital Sign Indicators**: Visual assessment of consciousness, breathing patterns, and circulation

The fine-tuned model processes medical images in real-time, providing structured output that integrates seamlessly with our patient management system for immediate triage decisions in mass casualty scenarios. (See training here: https://colab.research.google.com/drive/1lAwg-rEmwbxqGlrPTpMuPVV78T2wz6dV?usp=sharing)

#### **On-Device AI Processing**
With Google Edge AI and Jetson devices, all critical tasks are processed locally, ensuring rapid and reliable responses even in the most chaotic environments. When there's no internet connectivity, data is first stored in Jetson device. When internet comes back, Jetson syncs the data in storage to the cloud.

#### **Multi-Service Architecture**
RapidCare runs as three coordinated services:
- **Flask App** (port 5050): Main web interface and API
- **Model Server** (port 5001): AI model inference and processing
- **Upload Server** (port 11435): File upload and storage management

## 🎯 Impact

With RapidCare, emergency responders and families can navigate the chaos of mass casualty events with increased efficiency, improved coordination, and ultimately, better outcomes for those in need of urgent medical care.

## 👥 Multi-Role Support

RapidCare supports multiple roles to ensure comprehensive emergency response:

- **ADMIN**: System oversight and role management
- **PHYSICIAN**: Medical assessment and treatment decisions
- **NURSE**: Patient monitoring and vital signs
- **PARAMEDIC/EMT**: Field triage and emergency care
- **REUNIFICATION_COORDINATOR**: Family location and patient matching
- **FIELD_AGENT**: Field operations and coordination
- **TRANSFER_AGENT**: Patient transfer management
- **LOGISTICS**: Supply and resource management
- **MEDICAL_ASSISTANT**: Clinical support and documentation

## 🐳 Docker Management

### **Essential Commands**
```bash
# Build and run
./build_and_run.sh

# View logs
docker logs -f offline-gemma-jetson

# Stop container
docker stop offline-gemma-jetson

# Restart container
docker restart offline-gemma-jetson

# Enter container shell
docker exec -it offline-gemma-jetson bash

# Check container status
docker ps
```

### **Service-Specific Logs**
```bash
# Model server logs
./scripts/view_model_logs.sh

# Flask app logs
./scripts/view_flask_logs.sh

# Upload server logs
./scripts/view_upload_logs.sh

# All logs with color coding
./scripts/view_all_logs.sh
```

### **Troubleshooting**
```bash
# Check if all services are running
docker exec offline-gemma-jetson ps aux | grep python

# Test model server health
curl http://localhost:5001/health

# Check GPU access
docker exec offline-gemma-jetson nvidia-smi

# Monitor resource usage
docker stats offline-gemma-jetson
```

## 🏆 Prize Alignment

RapidCare is designed to compete for multiple prizes by showcasing different aspects of our architecture:

### **The Jetson Prize**
For the best demonstration of on-device power by deploying a Gemma 3n product on an NVIDIA Jetson device.

**Our Approach**: RapidCare runs fully offline on Jetson devices with intelligent dual-model support (2B and 4B), automatically selecting the optimal model based on system load. This ensures maximum performance while maintaining reliability during critical emergency response scenarios. When internet connectivity is lost, data is stored locally and synced when connectivity returns.

### **The Google AI Edge Prize**
For the most compelling and effective use case built using the Google AI Edge implementation of Gemma 3n.

**Our Approach**: We leverage Google Edge AI with dynamic model selection, automatically choosing between 2B and 4B models based on system load and task complexity. This ensures optimal performance across different edge devices while maintaining reliability during critical emergency response scenarios.

### **The Local AI Prize**
For the best project that utilizes and showcases the capabilities of Gemma 3n running locally via direct model inference.

**Our Approach**: Our local-first architecture uses intelligent model selection to run both Gemma 3n 2B and 4B models locally, automatically choosing the optimal model based on system load and task requirements. This demonstrates real-world production scenarios where organizations must balance performance with resource constraints, ensuring reliable operation across diverse hardware environments.

### **The Unsloth Prize**
For the best fine-tuned Gemma 3n model created using Unsloth, optimized for a specific, impactful task.

**Our Approach**: We fine-tune both Gemma 3n 2B and 4B models specifically for mass casualty incident response, optimizing for medical triage, patient reunification, and emergency coordination tasks across different deployment scenarios.

## 🧠 Technical Architecture

### **Core Tech Stack**

| Technology | Role in RapidCare |
|------------|-------------------|
| **Gemma 3n 2B** | CPU-optimized model for local hosting (AWS, etc.) |
| **Gemma 3n 4B** | GPU-optimized model for Google Edge AI and Jetson devices |
| **Google Edge AI** | Edge-optimized model inference and device interoperability |
| **Jetson Device** | On-device processing and local data storage |
| **Progressive Web App** | Cross-platform deployment (Web, Android, iOS) |
| **Voice-to-Text** | Local speech recognition for hands-free operation |
| **HTTP Bridge** | Communication between PWA and on-device AI |

### **Dynamic Model Deployment Strategy**

Our architecture supports intelligent model selection based on system load and available hardware:

#### **Smart Model Selection**
- **High Load Detection**: Automatically switches to 2B model when system resources are constrained
- **Load Monitoring**: Real-time CPU, memory, GPU, and temperature monitoring
- **Task-Aware Selection**: Quick tasks (voice transcription) use 2B, complex tasks (video analysis) use 4B when resources allow

#### **Hardware-Based Deployment**
- **CPU-Only Environments** (AWS EC2, local servers): Gemma 3n 2B model for efficient CPU inference
- **GPU-Enabled Edge Devices** (Google Edge AI, Jetson): Gemma 3n 4B model for enhanced performance
- **Mixed Environments**: Dynamic switching between 2B and 4B based on current system load

#### **Load-Based Optimization**
- **High Load Conditions** (>80% CPU, >85% memory, >90% GPU): Automatically selects 2B model
- **Moderate Load** (60-80% CPU, 70-85% memory): Uses 2B for quick tasks, 4B for complex tasks
- **Low Load** (<60% CPU, <70% memory): Leverages 4B model for maximum performance

## 🚀 Future Enhancements

### **Multi-Language Support**
- **International Deployment**: Support for Spanish, French, Arabic, Mandarin, and other languages common in emergency scenarios
- **Voice Recognition**: Multi-language speech-to-text for hands-free operation in diverse environments
- **Cultural Adaptation**: Region-specific triage protocols and medical terminology
- **Translation Services**: Real-time translation for international emergency response teams

### **Hospital Integration & Resource Management**
- **Bed Availability**: Real-time sync with local hospital databases to locate available beds and resources
- **Transfer Coordination**: Automated patient transfer scheduling and routing
- **Resource Tracking**: Monitor medical supplies, equipment, and personnel availability
- **Capacity Planning**: Predictive analytics for resource allocation during mass casualty events

### **Advanced AI Model Fine-tuning**
- **Specialized Training**: Fine-tune models for specific medical specialties (trauma, pediatrics, geriatrics)
- **Regional Adaptation**: Train models on local medical protocols and regional health guidelines
- **Continuous Learning**: Implement feedback loops to improve model accuracy based on real-world outcomes
- **Specialized Tasks**: Custom training for wound assessment, medication interaction checking, and vital sign interpretation

### **Enhanced Offline Capabilities**
- **Distributed Processing**: Multi-device coordination for large-scale incidents
- **Mesh Networking**: Device-to-device communication without internet infrastructure
- **Data Synchronization**: Intelligent conflict resolution for offline data merging
- **Battery Optimization**: Power management for extended field operations

### **Advanced Analytics & Reporting**
- **Predictive Triage**: Machine learning models to predict patient deterioration
- **Epidemiological Tracking**: Pattern recognition for disease outbreaks and injury trends
- **Performance Metrics**: Real-time analytics on response times and outcomes
- **Quality Assurance**: Automated auditing of triage decisions and patient outcomes

### **IoT & Wearable Integration**
- **Vital Sign Monitoring**: Real-time integration with wearable devices and medical sensors
- **Environmental Sensors**: Air quality, radiation, and chemical exposure monitoring
- **Location Services**: GPS tracking for patient and responder safety
- **Smart Alerts**: Automated notifications for critical patient conditions

### **Security & Compliance**
- **HIPAA Compliance**: Enhanced data encryption and privacy protection
- **Audit Trails**: Comprehensive logging for regulatory compliance
- **Access Control**: Role-based permissions and multi-factor authentication
- **Data Governance**: Automated data retention and disposal policies

### **Mobile & Edge Computing**
- **5G Integration**: Ultra-low latency communication for real-time collaboration
- **Edge AI**: Distributed AI processing across multiple edge devices
- **Augmented Reality**: AR overlays for medical procedures and training
- **Voice Commands**: Advanced natural language processing for hands-free operation

### **Collaboration & Communication**
- **Team Coordination**: Real-time communication between emergency response teams
- **Family Reunification**: Enhanced missing person tracking and family notification
- **Inter-agency Integration**: Seamless coordination between police, fire, and medical services
- **Public Communication**: Automated public announcements and emergency broadcasts

### **Scalability & Performance**
- **Microservices Architecture**: Modular deployment for better scalability
- **Load Balancing**: Intelligent distribution of processing load across multiple servers
- **Auto-scaling**: Dynamic resource allocation based on incident scale
- **Disaster Recovery**: Robust backup and recovery systems for critical operations

### **Research & Development**
- **Clinical Trials**: Integration with research protocols for evidence-based improvements
- **Data Sharing**: Secure sharing of anonymized data for medical research
- **A/B Testing**: Continuous improvement through controlled experimentation
- **Academic Partnerships**: Collaboration with medical schools and research institutions

## 📚 Documentation

For detailed setup instructions, system configuration files, and deployment guides, see:
- **[Setup Guide](setup_guide.md)** - Complete deployment and configuration instructions
- **[TODO.md](TODO.md)** - Jetson device setup and advanced features

This approach demonstrates real-world production scenarios where organizations must balance performance with resource constraints, automatically optimizing for the best possible response quality given current system conditions.

### **Offline-First Design**

RapidCare operates in three connectivity modes:

1. **Online Mode**: Full cloud sync and real-time collaboration
2. **Offline Mode**: Local processing with data caching
3. **Hybrid Mode**: Selective sync when connectivity is intermittent

### **Real-Time System Monitoring**

#### **Load Status Indicators**
- **Low Load** (🟢): System operating optimally, using 4B model for maximum performance
- **Moderate Load** (🟡): System under moderate stress, task-aware model selection
- **High Load** (🔴): System under high stress, automatically switched to 2B model

#### **UI Monitoring Features**
- **Live Load Display**: Real-time CPU, memory, and GPU utilization
- **Model Status**: Shows which model is currently active (2B or 4B)
- **System Messages**: Automatic notifications when load changes significantly
- **Performance Metrics**: Temperature, concurrent requests, and memory availability

#### **Smart Alerts**
- **Load Transitions**: Notifies users when switching between models
- **Resource Warnings**: Alerts when system resources are constrained
- **Performance Optimization**: Suggests actions to improve system performance

## 🚀 Jetson-Specific Features

### **Dual Model Support on Jetson Xavier NX**
- **8GB RAM Capacity**: Can store both 2B (~4GB) and 4B (~8GB) models
- **Smart Model Selection**: Automatically chooses optimal model based on current load
- **Memory Management**: Only loads one model at a time to maximize available memory
- **Performance Optimization**: 4B model for complex tasks, 2B for quick responses under load

### **Offline Processing Capabilities**
- **Local Data Storage**: Audio, image, and video files stored locally when offline
- **Background Processing**: Processes stored data when system resources allow
- **Cloud Synchronization**: Syncs processed results when connectivity returns
- **Device Capability Detection**: Automatically determines if offline processing is supported

### **System Load Intelligence**
- **Multi-Metric Monitoring**: CPU, memory, GPU, temperature, and concurrent requests
- **Predictive Switching**: Anticipates load changes and switches models proactively
- **Resource Optimization**: Ensures critical tasks always have sufficient resources
- **Performance Tracking**: Historical load data for system optimization

## 🎯 Benefits of Dynamic Model Selection

### **Production-Ready Flexibility**
- **Resource Optimization**: Automatically adapts to available system resources
- **Performance Guarantees**: Ensures critical tasks always complete, even under load
- **Cost Efficiency**: Uses smaller models when possible, larger models when beneficial
- **Scalability**: Works across different hardware configurations without manual tuning

### **Real-World Deployment Scenarios**
- **Emergency Response**: Critical situations where response time is paramount
- **Resource-Constrained Environments**: Rural areas or temporary setups with limited hardware
- **High-Traffic Situations**: Mass casualty events with multiple concurrent users
- **Variable Load Conditions**: Systems that experience fluctuating resource demands

### **Technical Advantages**
- **Zero Downtime**: Model switching happens seamlessly without service interruption
- **Predictive Intelligence**: Anticipates load changes before they impact performance
- **Task Optimization**: Matches model complexity to task requirements
- **Memory Efficiency**: Only loads the model currently needed

## 🎥 Demo Scenarios

### **Scene 1: Paramedic Field Assessment**
- **Voice Input**: "Unconscious male, no visible trauma, shallow breathing"
- **AI Response**: "Classify as Yellow. Pulse irregular. Advise oxygen support. Logging patient."
- **Action**: Automatically creates patient record, geotags location, syncs when online

### **Scene 2: Nurse Vital Signs Update**
- **Voice Input**: "Patient 237: BP 90/60, pulse 130, unresponsive"
- **AI Response**: "Updating triage to Red. Flagging for physician review. Alerting transfer team."
- **Action**: Updates patient status, notifies relevant personnel

### **Scene 3: Family Reunification**
- **Voice Input**: "Looking for Maya Thompson, 10 years old"
- **AI Response**: "Match found in triage area 3. Assigned green tag. Vital signs stable."
- **Action**: Connects family with patient location and status

## 🚀 Getting Started

### **Quick Start**
```bash
# Clone the repository
git clone <repository-url>
cd offline-gemma

# Install dependencies
pip install -r requirements.txt

# Start the application
./start.sh
```

### **Development Setup**
```bash
# Start with TMUX for development
./tmux_start.sh

# Stop all services
./tmux_stop.sh
```

## 📱 Features

- **Voice-Activated Interface**: Hands-free operation for field responders
- **Multi-Role Support**: Different capabilities for each emergency role
- **Offline Operation**: Works without internet connectivity
- **Real-Time Triage**: AI-powered injury assessment and classification
- **Patient Tracking**: RFID/wristband integration for patient identification
- **Family Reunification**: AI-powered matching of patients with families
- **Video Analysis**: On-device video processing for injury assessment
- **Vital Signs Monitoring**: Real-time vital signs tracking and alerts

## 🔧 Technical Implementation

### **Internet Detection**
The application includes robust internet connectivity detection with:
- Backend connectivity testing via `/api/connectivity` endpoint
- Frontend browser-based connectivity monitoring
- Real-time status indicators in the UI
- Graceful degradation when offline

### **AI Model Integration**
- **Gemma 3n 2B**: CPU-optimized model for AWS/local hosting scenarios
- **Gemma 3n 4B**: GPU-optimized model for Google Edge AI and Jetson devices
- **Google Edge AI**: Optimized inference for edge devices
- **Jetson AI**: Local processing and data storage
- **Voice Recognition**: Browser-based speech-to-text
- **Image/Video Analysis**: On-device media processing

### **Data Management**
- **Local Storage**: SQLite database for offline operation
- **Vector Search**: Patient and document search capabilities
- **File Upload**: Media processing and analysis
- **Sync Mechanism**: Cloud synchronization when online

## 📊 Performance Optimizations

- **10-minute timeouts** for long-running analysis operations
- **Progressive loading** for patient lists and data
- **Caching strategies** for frequently accessed data
- **Background processing** for non-critical operations

## 🛠️ Development Tools

The project includes various development and utility scripts in the `scripts/` folder:
- Model management and optimization tools
- Testing and validation scripts
- Database utilities
- Documentation and examples

For detailed information about available scripts, see `scripts/README.md`.

