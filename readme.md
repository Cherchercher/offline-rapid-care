# RapidCare: AI-Powered Mass Casualty Incident Response System

## 🚨 The Challenge

In mass casualty events like concerts, wildfires, or emergency situations, the ability to respond swiftly and effectively can make all the difference in saving lives. Each year, countless individuals suffer injuries in these environments, highlighting the urgent need for fast, reliable, and coordinated care. Not to mention that during MCI, internet access might be interrupted. From rapidly assessing injuries to locating missing loved ones, the challenge is immense, and the demand for a seamless, real-time, offline-first response system has never been greater.

## 🚑 The Solution

Enter **RapidCare** — a groundbreaking solution designed to transform emergency response during mass casualty events. Powered by the advanced Gemma 3n AI engine, RapidCare is a voice-activated, multi-role, on-device AI assistant tailored for field triage, coordination, and communication. Whether you're a paramedic, nurse, field agent, or a family member searching for a loved one, RapidCare equips you with the tools needed to act quickly and efficiently.

This cutting-edge app is designed to operate fully offline on mobile devices, including Google Edge AI, Jetson devices, and web browsers, ensuring optimal performance regardless of connectivity. With intelligent medical triage features like video-based assessments, real-time vitals transcription, and patient reunification capabilities, RapidCare serves as a vital assistant to those working on the frontlines and those desperately seeking information.

## 🏗️ Architecture Overview

### **Key Technologies:**

#### **Progressive Web App (PWA)**
By leveraging the power of PWA, we ensure that RapidCare is accessible across Web, Android, and iOS platforms, with code written once for broad deployment.

#### **Offline Capabilities**
Through an HTTP Bridge, RapidCare can communicate with on-device AI for tasks like image analysis, enabling the app to function seamlessly without cloud dependence.

#### **On-Device AI Processing**
With Google Edge AI and Jetson devices, all critical tasks are processed locally, ensuring rapid and reliable responses even in the most chaotic environments. When there's no internet connectivity, data is first stored in Jetson device. When internet comes back, Jetson syncs the data in storage to the cloud.

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

## 🏆 Prize Alignment

RapidCare is designed to compete for multiple prizes by showcasing different aspects of our architecture:

### **The Jetson Prize**
For the best demonstration of on-device power by deploying a Gemma 3n product on an NVIDIA Jetson device.

**Our Approach**: RapidCare runs fully offline on Jetson devices, processing all critical tasks locally including video analysis, voice transcription, and patient triage. When internet connectivity is lost, data is stored locally and synced when connectivity returns.

### **The Google AI Edge Prize**
For the most compelling and effective use case built using the Google AI Edge implementation of Gemma 3n.

**Our Approach**: We leverage Google Edge AI for optimized inference and device interoperability, ensuring seamless operation across different edge devices while maintaining performance.

### **The Ollama Prize**
For the best project that utilizes and showcases the capabilities of Gemma 3n running locally via Ollama.

**Our Approach**: Our local-first architecture uses Ollama to run Gemma 3n models locally, ensuring zero-latency responses even without internet connectivity.

### **The Unsloth Prize**
For the best fine-tuned Gemma 3n model created using Unsloth, optimized for a specific, impactful task.

**Our Approach**: We fine-tune Gemma 3n specifically for mass casualty incident response, optimizing for medical triage, patient reunification, and emergency coordination tasks.

## 🧠 Technical Architecture

### **Core Tech Stack**

| Technology | Role in RapidCare |
|------------|-------------------|
| **Gemma 3n** | Foundation model fine-tuned for MCI-specific workflows |
| **Google Edge AI** | Edge-optimized model inference and device interoperability |
| **Jetson Device** | On-device processing and local data storage |
| **Progressive Web App** | Cross-platform deployment (Web, Android, iOS) |
| **Voice-to-Text** | Local speech recognition for hands-free operation |
| **HTTP Bridge** | Communication between PWA and on-device AI |

### **Offline-First Design**

RapidCare operates in three connectivity modes:

1. **Online Mode**: Full cloud sync and real-time collaboration
2. **Offline Mode**: Local processing with data caching
3. **Hybrid Mode**: Selective sync when connectivity is intermittent

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

