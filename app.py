from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import requests
import json
import os
from datetime import datetime
import uuid
from model_manager_api import get_api_model_manager
from database_setup import get_db_manager

app = Flask(__name__)

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
GEMMA_MODEL = "gemma3n:e4b"
USE_OLLAMA = True  # Set to False to use direct model loading

# Create uploads directory for temporary images
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Initialize API model manager
model_manager = get_api_model_manager()

# In-memory storage for demo (in production, use a proper database)
patients = {}
incidents = {}
roles = {
    "ADMIN": "System administrator with full access",
    "PHYSICIAN": "Medical doctor with patient care authority",
    "NURSE": "Registered nurse for patient monitoring",
    "PARAMEDIC": "Emergency medical technician",
    "EMT": "Emergency medical technician",
    "REUNIFICATION_COORDINATOR": "Family reunification specialist",
    "FIELD_AGENT": "Field operations coordinator",
    "TRANSFER_AGENT": "Patient transfer coordinator",
    "LOGISTICS": "Supply and resource management",
    "MEDICAL_ASSISTANT": "Clinical support staff"
}

db_manager = get_db_manager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files with proper MIME types"""
    import os
    from flask import send_from_directory, Response
    
    file_path = os.path.join(UPLOADS_DIR, filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Determine MIME type based on file extension
    file_ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime'
    }
    
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    # For audio files, ensure they're served with proper headers
    if mime_type.startswith('audio/'):
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        response = Response(audio_data, mimetype=mime_type)
        response.headers['Content-Length'] = len(audio_data)
        response.headers['Accept-Ranges'] = 'bytes'
        return response
    
    # For other files, use send_from_directory
    return send_from_directory(UPLOADS_DIR, filename, mimetype=mime_type)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        user_role = data.get('role', 'PARAMEDIC')
        patient_id = data.get('patient_id', None)
        
        # Create system prompt based on role with triage requirements
        system_prompt = f"""You are a {user_role.lower()} in a mass casualty incident response system. 
        
        CRITICAL REQUIREMENTS:
        1. ALWAYS provide a triage category (RED, YELLOW, GREEN, BLACK) at the beginning of your response
        2. ALWAYS provide clear reasoning for your triage decision
        3. ALWAYS provide specific actionable steps for the situation
        4. Use medical triage protocols and emergency response procedures
        
        TRIAGE CATEGORIES:
        - RED (Immediate): Life-threatening injuries requiring immediate attention
        - YELLOW (Delayed): Serious injuries that can wait for treatment
        - GREEN (Minor): Minor injuries that can wait or self-treat
        - BLACK (Deceased/Expectant): Deceased or injuries incompatible with life
        
        Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Format your response as:
        **Triage: [CATEGORY]** **Reasoning:** [Clear explanation] **Action:** [Specific steps]"""
        
        # Prepare messages for model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Use model manager to get response
        result = model_manager.chat(messages)
        
        if result['success']:
            assistant_message = result['response']
            
            # Log the interaction
            log_interaction(user_role, user_message, assistant_message, patient_id)
            
            return jsonify({
                'success': True,
                'response': assistant_message,
                'timestamp': datetime.now().isoformat(),
                'mode': result.get('mode', 'unknown')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    """Handle video upload and processing"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        user_role = request.form.get('role', 'PARAMEDIC')
        
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Save video temporarily
        video_path = f"temp_video_{uuid.uuid4()}.mp4"
        video_file.save(video_path)
        
        # Use the new API approach for video processing
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "video", "path": video_path},
                    {"type": "text", "text": f"Analyze this video for medical triage assessment as a {user_role.lower()}."}
                ]
            }
        ]
        
        # Use the model manager's video endpoint
        result = model_manager.chat_video(messages)
        analysis_results = result.get('response', 'Error analyzing video') if result['success'] else result.get('error', 'Unknown error')
        
        # Clean up temporary file
        try:
            os.remove(video_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'analysis': analysis_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/analyze', methods=['POST'])
def analyze_video():
    """Analyze video from URL or existing file using the new API approach"""
    try:
        data = request.json
        video_path = data.get('video_path', '')
        user_role = data.get('role', 'PARAMEDIC')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Use the new API approach - same as direct curl call
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "video", "path": video_path},
                    {"type": "text", "text": f"Analyze this video for medical triage assessment as a {user_role.lower()}."}
                ]
            }
        ]
        
        # Use the model manager's video endpoint
        result = model_manager.chat_video(messages)
        
        return jsonify({
            'success': result['success'],
            'analysis': result.get('response', '') if result['success'] else result.get('error', 'Unknown error'),
            'timestamp': datetime.now().isoformat(),
            'mode': result.get('mode', 'unknown'),
            'inference_time': result.get('inference_time', 0),
            'frames_analyzed': result.get('frames_analyzed', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/frame', methods=['POST'])
def analyze_frame():
    """Analyze a single frame from video"""
    try:
        data = request.json
        frame_data = data.get('frame', '')  # Base64 encoded image
        user_role = data.get('role', 'PARAMEDIC')
        
        if not frame_data:
            return jsonify({'error': 'No frame data provided'}), 400
        
        # Convert base64 to numpy array
        import base64
        import numpy as np
        from PIL import Image
        import io
        
        # Decode base64 image
        image_data = base64.b64decode(frame_data)
        image = Image.open(io.BytesIO(image_data))
        frame = np.array(image)
        
        # Convert frame to base64 for API call
        import base64
        import io
        
        # Convert PIL image to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        frame_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Use the new API approach for frame analysis
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "image", "path": f"data:image/jpeg;base64,{frame_base64}"},
                    {"type": "text", "text": f"Analyze this frame for medical triage assessment as a {user_role.lower()}."}
                ]
            }
        ]
        
        # Use the model manager's image endpoint
        result = model_manager.chat_image(messages)
        analysis = result.get('response', 'Error analyzing frame') if result['success'] else result.get('error', 'Unknown error')
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze-media', methods=['POST'])
def analyze_media():
    """Analyze uploaded media files (images and videos)"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        user_role = request.form.get('role', 'PARAMEDIC')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        analysis_results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Determine file type
            if file.content_type.startswith('image/'):
                # Handle image analysis
                analysis = analyze_image_file(file, user_role)
                analysis_results.append({
                    'type': 'image',
                    'filename': file.filename,
                    'analysis': analysis
                })
                
            elif file.content_type.startswith('video/'):
                # Handle video analysis
                analysis = analyze_video_file(file, user_role)
                analysis_results.append({
                    'type': 'video',
                    'filename': file.filename,
                    'analysis': analysis
                })
        
        # If only one file, return individual analysis directly
        if len(analysis_results) == 1:
            individual_analysis = analysis_results[0]['analysis']
            return jsonify({
                'success': True,
                'analysis': individual_analysis,
                'details': analysis_results,
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Multiple files - combine results
            combined_analysis = combine_analysis_results(analysis_results, user_role)
            return jsonify({
                'success': True,
                'analysis': combined_analysis,
                'details': analysis_results,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_voice():
    """Transcribe voice input using Ollama"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        user_role = request.form.get('role', 'PARAMEDIC')
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save audio temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
        
        try:
            # Use Ollama for transcription
            transcription = transcribe_audio_with_ollama(audio_path, user_role)
            
            return jsonify({
                'success': True,
                'transcription': transcription,
                'auto_send': True,  # Auto-send transcribed message
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
            except:
                pass
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/voice/transcribe-text', methods=['POST'])
def transcribe_text():
    """Process text transcription from frontend Web Speech API"""
    try:
        data = request.json
        transcription = data.get('transcription', '')
        user_role = data.get('role', 'PARAMEDIC')
        
        if not transcription:
            return jsonify({'error': 'No transcription provided'}), 400
        
        # Use Ollama to enhance/process the transcription with triage requirements
        system_prompt = f"""You are a {user_role.lower()} in an emergency response system. 
        
        CRITICAL REQUIREMENTS:
        1. ALWAYS provide a triage category (RED, YELLOW, GREEN, BLACK) at the beginning of your response
        2. ALWAYS provide clear reasoning for your triage decision
        3. ALWAYS provide specific actionable steps for the situation
        4. Use medical triage protocols and emergency response procedures
        
        TRIAGE CATEGORIES:
        - RED (Immediate): Life-threatening injuries requiring immediate attention
        - YELLOW (Delayed): Serious injuries that can wait for treatment
        - GREEN (Minor): Minor injuries that can wait or self-treat
        - BLACK (Deceased/Expectant): Deceased or injuries incompatible with life
        
        Process this audio transcription and provide medical insights with triage categorization.
        If the transcription is unclear, ask for clarification.
        Focus on medical terminology, patient information, and emergency details.
        
        Format your response as:
        **Triage: [CATEGORY]** **Reasoning:** [Clear explanation] **Action:** [Specific steps]"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Process this emergency audio transcription: {transcription}"}
        ]
        
        result = model_manager.chat(messages)
        
        if result['success']:
            return jsonify({
                'success': True,
                'transcription': transcription,
                'enhanced_response': result['response'],
                'auto_send': True,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'transcription': transcription,
                'enhanced_response': transcription,  # Use raw transcription if Ollama fails
                'auto_send': True,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_image_file(file, user_role):
    """Analyze an uploaded image file"""
    try:
        # Save image to uploads directory
        import os
        from PIL import Image
        import numpy as np
        from datetime import datetime
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads"
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}_{file.filename}"
        filepath = os.path.join(uploads_dir, filename)
        
        # Save the uploaded file
        file.save(filepath)
        
        # Create URL for the image (use uploads server port)
        image_url = f"http://127.0.0.1:11435/{filename}"
        
        print(f"🔍 Analyzing image with role: {user_role}")
        print(f"📏 Image saved to: {filepath}")
        print(f"🌐 Image URL: {image_url}")
        
        # Load and analyze image using URL instead of base64
        image = Image.open(filepath)
        frame = np.array(image)
        
        # Analyze using video processor with URL
        # Use the new API approach for frame analysis with URL
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "image", "path": image_url},
                    {"type": "text", "text": f"Analyze this frame for medical triage assessment as a {user_role.lower()}."}
                ]
            }
        ]
        
        # Use the model manager's image endpoint
        result = model_manager.chat_image(messages)
        analysis = result.get('response', 'Error analyzing frame') if result['success'] else result.get('error', 'Unknown error')
        
        print(f"📊 Analysis result: {analysis}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing image: {str(e)}")
        return f"Error analyzing image: {str(e)}"

def analyze_video_file(file, user_role):
    """Analyze an uploaded video file using the new API approach"""
    try:
        # Save video temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Use the new API approach - same as direct curl call
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "video", "path": tmp_path},
                    {"type": "text", "text": f"Analyze this video for medical triage assessment as a {user_role.lower()}."}
                ]
            }
        ]
        
        # Use the model manager's video endpoint
        result = model_manager.chat_video(messages)
        
        # Clean up
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if result['success']:
            return result['response']
        else:
            return f"Error analyzing video: {result.get('error', 'Unknown error')}"
        
    except Exception as e:
        return f"Error analyzing video: {str(e)}"

def combine_analysis_results(results, user_role):
    """Combine multiple analysis results into a coherent response"""
    if not results:
        return "No media files were successfully analyzed."
    
    combined = f"Media Analysis Results ({len(results)} file(s)):\n\n"
    
    # Track triage levels across all files
    triage_counts = {'Red': 0, 'Yellow': 0, 'Green': 0, 'Black': 0}
    
    for i, result in enumerate(results, 1):
        combined += f"File {i}: {result['filename']} ({result['type']})\n"
        
        # Extract triage information if available
        analysis_text = result['analysis']
        if isinstance(analysis_text, dict):
            # Handle structured analysis results
            triage_level = analysis_text.get('triage_level', 'Unknown')
            description = analysis_text.get('description', 'No description')
            combined += f"**Triage: {triage_level.upper()}**\n"
            combined += f"Analysis: {description}\n\n"
            
            if triage_level in triage_counts:
                triage_counts[triage_level] += 1
        else:
            # Handle text analysis results
            combined += f"Analysis: {analysis_text}\n\n"
            
            # Try to extract triage level from text
            if '**Triage: RED**' in analysis_text.upper():
                triage_counts['Red'] += 1
            elif '**Triage: YELLOW**' in analysis_text.upper():
                triage_counts['Yellow'] += 1
            elif '**Triage: BLACK**' in analysis_text.upper():
                triage_counts['Black'] += 1
            elif '**Triage: GREEN**' in analysis_text.upper():
                triage_counts['Green'] += 1
    
    # Add overall triage summary
    combined += "**OVERALL TRIAGE SUMMARY:**\n"
    priority_order = ['Black', 'Red', 'Yellow', 'Green']
    overall_triage = 'Green'
    
    for level in priority_order:
        if triage_counts[level] > 0:
            overall_triage = level
            break
    
    combined += f"**Overall Triage: {overall_triage.upper()}**\n"
    combined += f"Distribution: Red={triage_counts['Red']}, Yellow={triage_counts['Yellow']}, Green={triage_counts['Green']}, Black={triage_counts['Black']}\n\n"
    
    # Add role-specific recommendations with triage context
    if user_role in ['PARAMEDIC', 'NURSE', 'PHYSICIAN']:
        combined += "**Medical Recommendations:**\n"
        if overall_triage == 'Red':
            combined += "- IMMEDIATE: Life-threatening conditions detected\n"
            combined += "- Prioritize airway, breathing, circulation (ABC)\n"
            combined += "- Prepare for emergency interventions\n"
        elif overall_triage == 'Yellow':
            combined += "- URGENT: Serious injuries requiring prompt care\n"
            combined += "- Monitor vital signs closely\n"
            combined += "- Prepare for surgical intervention if needed\n"
        elif overall_triage == 'Black':
            combined += "- DECEASED: Confirm death and document\n"
            combined += "- Preserve scene for investigation\n"
            combined += "- Notify appropriate authorities\n"
        else:  # Green
            combined += "- MINOR: Non-life-threatening conditions\n"
            combined += "- Assess patient consciousness and airway\n"
            combined += "- Check for visible injuries and bleeding\n"
            combined += "- Monitor vital signs if possible\n"
    elif user_role == 'REUNIFICATION_COORDINATOR':
        combined += "**Reunification Notes:**\n"
        combined += "- Document any identifying features\n"
        combined += "- Note approximate age and gender\n"
        combined += "- Record any personal items visible\n"
    
    return combined

def transcribe_audio_with_ollama(audio_path, user_role):
    """Transcribe audio using speech recognition and enhance with Ollama"""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
        import os
        
        # Convert audio to WAV if needed
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.replace('.mp3', '.wav').replace('.m4a', '.wav')
        if not wav_path.endswith('.wav'):
            wav_path = audio_path + '.wav'
        
        audio.export(wav_path, format="wav")
        
        # Use speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            
        # Try multiple recognition services
        transcription = None
        
        # First try Google Speech Recognition (requires internet)
        try:
            transcription = recognizer.recognize_google(audio_data)
        except:
            pass
        
        # Fallback to Sphinx (offline)
        if not transcription:
            try:
                transcription = recognizer.recognize_sphinx(audio_data)
            except:
                pass
        
        # If still no transcription, use a fallback
        if not transcription:
            transcription = "Audio received but could not be transcribed clearly"
        
        # Clean up temporary WAV file
        try:
            if wav_path != audio_path:
                os.unlink(wav_path)
        except:
            pass
        
        # Use Ollama to enhance/process the transcription
        system_prompt = f"""You are a {user_role.lower()} in an emergency response system. 
        Process this audio transcription and provide medical insights. If the transcription is unclear,
        ask for clarification. Focus on medical terminology, patient information, and emergency details."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Process this emergency audio transcription: {transcription}"}
        ]
        
        result = model_manager.chat(messages)
        
        if result['success']:
            return result['response']
        else:
            return transcription  # Return raw transcription if Ollama fails
            
    except ImportError:
        # Fallback if speech recognition libraries aren't available
        return "Speech recognition not available. Please install: pip install SpeechRecognition pydub pyaudio"
    except Exception as e:
        return f"Transcription error: {str(e)}"

@app.route('/api/patients', methods=['GET', 'POST'])
def patients_api():
    """Handle patient operations"""
    try:
        if request.method == 'GET':
            # Get all patients
            patients = db_manager.get_patients()
            return jsonify({
                'success': True,
                'patients': patients
            })
        
        elif request.method == 'POST':
            # Add new patient
            data = request.json
            print('--- Incoming patient data ---')
            print(data)
            try:
                patient_id = db_manager.add_patient(data)
            except Exception as e:
                import traceback
                print('--- Exception in add_patient ---')
                traceback.print_exc()
                return jsonify({'success': False, 'error': str(e)}), 500
            
            return jsonify({
                'success': True,
                'patient_id': patient_id,
                'message': 'Patient added successfully'
            })
            
    except Exception as e:
        import traceback
        print('--- Exception in /api/patients ---')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/soap-notes', methods=['GET', 'POST', 'PUT'])
def soap_notes_api():
    """Handle SOAP notes operations"""
    try:
        if request.method == 'GET':
            # Get SOAP notes
            patient_id = request.args.get('patient_id')
            doctor_id = request.args.get('doctor_id')
            
            soap_notes = db_manager.get_soap_notes(patient_id=patient_id, doctor_id=doctor_id)
            
            return jsonify({
                'success': True,
                'soap_notes': soap_notes
            })
        
        elif request.method == 'POST':
            # Add new SOAP note
            data = request.json
            soap_id = db_manager.add_soap_note(data)
            
            return jsonify({
                'success': True,
                'soap_id': soap_id,
                'message': 'SOAP note added successfully'
            })
        
        elif request.method == 'PUT':
            # Update SOAP note
            data = request.json
            soap_id = data.get('soap_id')
            
            if not soap_id:
                return jsonify({
                    'success': False,
                    'error': 'SOAP note ID required'
                }), 400
            
            success = db_manager.update_soap_note(soap_id, data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'SOAP note updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update SOAP note'
                }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    return jsonify(roles)

@app.route('/api/status', methods=['GET'])
def status():
    # Get model manager status
    model_status = model_manager.get_status()
    
    return jsonify({
        'model_status': model_status,
        'patients_count': len(patients),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get application configuration"""
    return jsonify({
        'model_config': model_manager.get_status(),
        'roles': roles
    })

@app.route('/api/model/switch', methods=['POST'])
def switch_model_mode():
    """Switch between direct and Ollama modes"""
    try:
        data = request.json
        new_mode = data.get('mode', 'auto')
        
        if new_mode not in ['direct', 'ollama', 'auto']:
            return jsonify({'error': 'Invalid mode. Use: direct, ollama, or auto'}), 400
        
        # Switch mode
        model_manager.switch_mode(new_mode)
        
        return jsonify({
            'success': True,
            'new_mode': model_manager.mode,
            'status': model_manager.get_status()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def log_interaction(role, user_message, assistant_message, patient_id=None):
    """Log interactions for audit trail"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'role': role,
        'user_message': user_message,
        'assistant_message': assistant_message,
        'patient_id': patient_id,
        'model_mode': model_manager.mode
    }
    
    # In production, save to database
    print(f"LOG: {json.dumps(log_entry)}")

@app.route('/api/missing-persons', methods=['GET', 'POST'])
def missing_persons_api():
    """Handle missing persons operations"""
    try:
        if request.method == 'GET':
            # Get all missing persons
            missing_persons = db_manager.get_missing_persons()
            return jsonify({
                'success': True,
                'missing_persons': missing_persons
            })
        
        elif request.method == 'POST':
            # Add new missing person
            data = request.json
            print("--- Incoming missing person data ---")
            print(data)
            
            # Save image if provided
            image_path = None
            if 'image_data' in data and data['image_data']:
                import base64
                image_data = base64.b64decode(data['image_data'].split(',')[1])
                filename = f"missing_person_{uuid.uuid4()}.jpg"
                image_path = os.path.join('uploads', filename)
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
            
            # Prepare person data
            person_data = {
                'name': data.get('name', ''),
                'age': data.get('age'),
                'description': data.get('description', ''),
                'image_path': image_path,
                'contact_info': data.get('contact_info', ''),
                'reported_by': data.get('reported_by', 'REUNIFICATION_COORDINATOR'),
                'status': 'missing'
            }
            
            person_id = db_manager.add_missing_person(person_data)
            
            return jsonify({
                'success': True,
                'person_id': person_id,
                'message': 'Missing person added successfully'
            })
    
    except Exception as e:
        print(f"--- Exception in missing_persons_api ---")
        print(f"Traceback (most recent call last):")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/find-match', methods=['POST'])
def find_match():
    """Find potential matches for a missing person"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Save uploaded image
        filename = f"search_image_{uuid.uuid4()}.jpg"
        image_path = os.path.join('uploads', filename)
        file.save(image_path)
        
        # Find matches
        matches = db_manager.find_missing_person_match(image_path)
        
        return jsonify({
            'success': True,
            'matches': matches,
            'search_image_path': image_path,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transcribe-audio', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using Gemma 3n"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['file']
        prompt = request.form.get('prompt', 'Transcribe this audio accurately')
        user_role = request.form.get('role', 'PARAMEDIC')
        
        if file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save uploaded audio
        print(f"🔊 Audio upload debug:")
        print(f"   Original filename: {file.filename}")
        print(f"   File content type: {file.content_type}")
        print(f"   File size: {len(file.read())} bytes")
        file.seek(0)  # Reset file pointer after reading
        
        filename = f"audio_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        audio_path = os.path.join('uploads', filename)
        file.save(audio_path)
        print(f"   Saved as: {audio_path}")
        
        # Convert to WAV for better compatibility
        conversion_start = datetime.now()
        try:
            from convert_audio import convert_to_wav
            wav_path = convert_to_wav(audio_path)
            conversion_time = (datetime.now() - conversion_start).total_seconds()
            if wav_path:
                audio_path = wav_path
                print(f"   Converted to WAV: {audio_path}")
                print(f"   ⏱️  Conversion time: {conversion_time:.2f} seconds")
            else:
                print(f"   Conversion failed, using original: {audio_path}")
                print(f"   ⏱️  Conversion attempt time: {conversion_time:.2f} seconds")
        except Exception as e:
            conversion_time = (datetime.now() - conversion_start).total_seconds()
            print(f"   Conversion error: {e}, using original: {audio_path}")
            print(f"   ⏱️  Conversion error time: {conversion_time:.2f} seconds")
        
        # Transcribe using Gemma 3n
        transcription_start = datetime.now()
        result = model_manager.transcribe_audio_file(audio_path, prompt)
        transcription_time = (datetime.now() - transcription_start).total_seconds()
        print(f"   ⏱️  Transcription time: {transcription_time:.2f} seconds")
        
        if result['success']:
            return jsonify({
                'success': True,
                'transcription': result['response'],
                'audio_path': audio_path,
                'timestamp': datetime.now().isoformat(),
                'mode': result.get('mode', 'unknown')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Transcription failed')
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # For development, you can use a self-signed certificate
    # In production, use a proper SSL certificate
    try:
        print("Starting Flask app on HTTPS")
        print("Access via: https://54.202.229.249:5050/")
        print("Note: You may see a security warning - click 'Advanced' and 'Proceed'")
        app.run(debug=True, host='0.0.0.0', port=5050, ssl_context='adhoc')
    except ImportError as e:
        print(f"SSL not available: {e}")
        print("Note: MediaDevices API requires HTTPS in most browsers")
        print("Access via: http://54.202.229.249:5050/")
        app.run(debug=True, host='0.0.0.0', port=5050)
    except Exception as e:
        print(f"Error starting HTTPS: {e}")
        print("Falling back to HTTP")
        app.run(debug=True, host='0.0.0.0', port=5050) 