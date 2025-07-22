from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import requests
import json
import os
from datetime import datetime
import uuid
from typing import Dict
from model_manager_api import get_api_model_manager
from database_setup import get_db_manager
from vector_search import get_vector_search_manager
import re
from prompts import CHARACTERISTIC_EXTRACTION_PROMPT, VITALS_EXTRACTION_PROMPT, MEDICAL_TRIAGE_PROMPT, REUNIFICATION_SEARCH_PROMPT, DESCRIPTION_PARSING_PROMPT, AUDIO_TRANSCRIPTION_PROMPT, MEDICAL_TRANSCRIPTION_PROMPT, SOAP_SUBJECTIVE_PROMPT, SOAP_OBJECTIVE_PROMPT, SOAP_ASSESSMENT_PROMPT, SOAP_PLAN_PROMPT, GENERAL_MEDICAL_ANALYSIS_PROMPT, FALLBACK_CHARACTERISTIC_PROMPT, AI_QUERY_SYSTEM_PROMPT_TEMPLATE, TRANSCRIBE_TEXT_SYSTEM_PROMPT_TEMPLATE, AUDIO_ENHANCEMENT_PROMPT_TEMPLATE

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
vector_search = get_vector_search_manager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/offline.html')
def offline_page():
    from flask import send_from_directory
    import os
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    return send_from_directory(templates_dir, 'offline.html')

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

@app.route('/chat/text', methods=['POST'])
def chat_text():
    try:
        data = request.json
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'success': False, 'error': 'No messages provided'}), 400

        result = model_manager.chat_text(messages)
        if result['success']:
            return jsonify({
                'success': True,
                'response': result['response'],
                'timestamp': datetime.now().isoformat(),
                'mode': result.get('mode', 'unknown')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    

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
                    {"type": "video", "path": video_path}
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
        import traceback
        traceback.print_exc()
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
                    {"type": "video", "path": video_path}
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
        import traceback
        traceback.print_exc()
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
                    {"type": "text", "text": MEDICAL_TRIAGE_PROMPT}
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/similar-cases', methods=['POST'])
def search_similar_cases():
    """Search for similar medical cases using AI-powered vector search"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        filters = data.get('filters', {})
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        # Search using vector database
        results = vector_search.search_similar_cases(query, limit, filters)
        
        # Convert results to JSON-serializable format
        search_results = []
        for result in results:
            search_results.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'results': search_results,
            'query': query,
            'total_found': len(search_results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/medical-notes', methods=['POST'])
def search_medical_notes():
    """Search across medical notes using AI"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        # Search medical notes
        results = vector_search.search_medical_notes(query, limit)
        
        # Convert results to JSON-serializable format
        search_results = []
        for result in results:
            search_results.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'results': search_results,
            'query': query,
            'total_found': len(search_results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/recommendations', methods=['POST'])
def get_treatment_recommendations():
    """Get AI-powered treatment recommendations based on triage and symptoms"""
    try:
        data = request.json
        triage_level = data.get('triage_level', '')
        symptoms = data.get('symptoms', '')
        
        if not triage_level or not symptoms:
            return jsonify({'error': 'Triage level and symptoms required'}), 400
        
        # Get recommendations
        results = vector_search.get_case_recommendations(triage_level, symptoms)
        
        # Convert results to JSON-serializable format
        recommendations = []
        for result in results:
            recommendations.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'triage_level': triage_level,
            'symptoms': symptoms,
            'total_found': len(recommendations)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/missing-persons', methods=['POST'])
def search_missing_persons():
    """Search for missing persons using AI"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        # Search missing persons
        results = vector_search.search_missing_persons(query, limit)
        
        # Convert results to JSON-serializable format
        search_results = []
        for result in results:
            search_results.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'results': search_results,
            'query': query,
            'total_found': len(search_results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def is_all_unknown(characteristics):
    if not characteristics:
        return True
    for v in characteristics.get('physical_features', {}).values():
        if v and v.lower() != 'unknown':
            return False
    for v in characteristics.get('clothing', {}).values():
        if v and v.lower() != 'unknown':
            return False
    if characteristics.get('distinctive_features'):
        if any(x.lower() != 'unknown' for x in characteristics['distinctive_features']):
            return False
    if characteristics.get('age_range', '').lower() != 'unknown':
        return False
    return True

@app.route('/api/search/missing-persons-by-description', methods=['POST'])
def search_missing_persons_by_description():
    """Search for missing persons using family member descriptions"""
    try:
        data = request.json
        description = data.get('description', '')
        limit = data.get('limit', 10)
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        # Parse description to extract characteristics
        parsed_characteristics = parse_characteristics_from_text(description)
        
        # Debug logging
        print(f"🔍 Search query: '{description}'")
        print(f"🔍 Parsed characteristics: {parsed_characteristics}")
        
        # Create enhanced search query with specific characteristics
        physical = parsed_characteristics.get('physical_features', {})
        clothing = parsed_characteristics.get('clothing', {})
        distinctive = parsed_characteristics.get('distinctive_features', [])
        age_range = parsed_characteristics.get('age_range', 'Unknown')
        
        # Build specific search terms
        search_terms = []
        if physical.get('gender'):
            search_terms.append(f"gender: {physical['gender']}")
        if physical.get('skin_tone'):
            search_terms.append(f"skin tone: {physical['skin_tone']}")
        if physical.get('hair_color'):
            search_terms.append(f"hair color: {physical['hair_color']}")
        if physical.get('eye_color'):
            search_terms.append(f"eye color: {physical['eye_color']}")
        if age_range != 'Unknown':
            search_terms.append(f"age: {age_range}")
        
        search_query = f"""
        Missing person search criteria:
        {', '.join(search_terms)}
        Original description: {description}
        """
        
        # Use vector search to find similar missing persons
        if db_manager.vector_search and db_manager.vector_search.is_available():
            results = vector_search.search_missing_persons(search_query, limit)
            
            # Enhance results with hybrid weighted scoring and filter out all-unknowns
            enhanced_results = []
            for result in results:
                person_characteristics = result.metadata.get('characteristics', {})
                # Parse characteristics from string if needed
                if isinstance(person_characteristics, str):
                    try:
                        person_characteristics = json.loads(person_characteristics)
                    except:
                        person_characteristics = {}
                # Calculate characteristic similarity
                char_sim = calculate_characteristic_similarity(parsed_characteristics, person_characteristics)
                # Weighted hybrid score: 30% vector, 70% characteristic
                combined_score = 0.3 * result.similarity_score + 0.7 * char_sim
                # Filter out results where all features are unknown
                if not is_all_unknown(person_characteristics):
                    enhanced_results.append({
                        'id': result.id,
                        'content': result.content,
                        'metadata': result.metadata,
                        'similarity_score': combined_score,
                        'source_type': result.source_type,
                        'characteristic_match': char_sim,
                        'vector_score': result.similarity_score
                    })
            # Sort by combined score
            enhanced_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return jsonify({
                'success': True,
                'results': enhanced_results,
                'total_found': len(enhanced_results),
                'parsed_characteristics': parsed_characteristics
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Vector search not available'
            }), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_characteristic_similarity(desc_characteristics: Dict, person_characteristics: Dict) -> float:
    """Calculate similarity between description and person characteristics"""
    try:
        if not person_characteristics:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        # Physical features comparison
        desc_physical = desc_characteristics.get('physical_features', {})
        person_physical = person_characteristics.get('physical_features', {})
        
        physical_weights = {
            'gender': 0.30,  # Increased weight for gender
            'skin_tone': 0.25,  # Increased weight for skin tone
            'hair_color': 0.15,
            'eye_color': 0.12,
            'height': 0.08,
            'build': 0.08
        }
        
        for feature, weight in physical_weights.items():
            if feature in desc_physical and feature in person_physical:
                if desc_physical[feature].lower() == person_physical[feature].lower():
                    total_score += weight
                total_weight += weight
        
        # Clothing comparison
        desc_clothing = desc_characteristics.get('clothing', {})
        person_clothing = person_characteristics.get('clothing', {})
        
        clothing_weights = {
            'top': 0.08,
            'bottom': 0.08,
            'accessories': 0.05
        }
        
        for item, weight in clothing_weights.items():
            if item in desc_clothing and item in person_clothing:
                if desc_clothing[item].lower() in person_clothing[item].lower() or person_clothing[item].lower() in desc_clothing[item].lower():
                    total_score += weight
                total_weight += weight
        
        # Distinctive features comparison
        desc_distinctive = set(desc_characteristics.get('distinctive_features', []))
        person_distinctive = set(person_characteristics.get('distinctive_features', []))
        
        if desc_distinctive and person_distinctive:
            intersection = desc_distinctive.intersection(person_distinctive)
            union = desc_distinctive.union(person_distinctive)
            distinctive_score = len(intersection) / len(union) if union else 0.0
            total_score += distinctive_score * 0.12
            total_weight += 0.12
        
        # Age range comparison
        desc_age = desc_characteristics.get('age_range', '')
        person_age = person_characteristics.get('age_range', '')
        
        if desc_age and person_age and desc_age != 'Unknown' and person_age != 'Unknown':
            # Simple age range overlap calculation
            try:
                desc_range = [int(x) for x in desc_age.replace('+', '').split('-')]
                person_range = [int(x) for x in person_age.replace('+', '').split('-')]
                
                if len(desc_range) == 2 and len(person_range) == 2:
                    overlap = min(desc_range[1], person_range[1]) - max(desc_range[0], person_range[0])
                    if overlap > 0:
                        age_score = overlap / max(desc_range[1] - desc_range[0], person_range[1] - person_range[0])
                        total_score += age_score * 0.10
                        total_weight += 0.10
            except:
                pass
        
        return total_score / total_weight if total_weight > 0 else 0.0
        
    except Exception as e:
        print(f"❌ Error calculating characteristic similarity: {e}")
        return 0.0

@app.route('/api/search/reunification-matches', methods=['POST'])
def find_reunification_matches():
    """Find potential matches for reunification"""
    try:
        data = request.json
        person_data = data.get('person_data', {})
        limit = data.get('limit', 5)
        
        if not person_data:
            return jsonify({'error': 'Person data required'}), 400
        
        # Find potential matches
        results = vector_search.find_potential_matches(person_data, limit)
        
        # Convert results to JSON-serializable format
        matches = []
        for result in results:
            matches.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'matches': matches,
            'total_found': len(matches)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/patients-reunification', methods=['POST'])
def search_patients_for_reunification():
    """Search patients for reunification purposes"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        # Search patients for reunification
        results = vector_search.search_patients_for_reunification(query, limit)
        
        # Convert results to JSON-serializable format
        search_results = []
        for result in results:
            search_results.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'results': search_results,
            'query': query,
            'total_found': len(search_results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/reunification-recommendations', methods=['POST'])
def get_reunification_recommendations():
    """Get AI-powered reunification recommendations"""
    try:
        data = request.json
        person_type = data.get('person_type', '')
        description = data.get('description', '')
        
        if not person_type or not description:
            return jsonify({'error': 'Person type and description required'}), 400
        
        # Get reunification recommendations
        results = vector_search.get_reunification_recommendations(person_type, description)
        
        # Convert results to JSON-serializable format
        recommendations = []
        for result in results:
            recommendations.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'person_type': person_type,
            'description': description,
            'total_found': len(recommendations)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/similar-patients', methods=['POST'])
def find_similar_patients():
    """Find patients with similar conditions"""
    try:
        data = request.json
        patient_data = data.get('patient_data', {})
        limit = data.get('limit', 5)
        
        if not patient_data:
            return jsonify({'error': 'Patient data required'}), 400
        
        # Find similar patients
        results = vector_search.find_similar_patients(patient_data, limit)
        
        # Convert results to JSON-serializable format
        similar_patients = []
        for result in results:
            similar_patients.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'similar_patients': similar_patients,
            'total_found': len(similar_patients)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/search/ai-query', methods=['POST'])
def ai_powered_query():
    """AI-powered natural language query interface"""
    try:
        data = request.json
        query = data.get('query', '')
        user_role = data.get('role', 'PARAMEDIC')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Use AI to understand the query and generate search strategy
        system_prompt = AI_QUERY_SYSTEM_PROMPT_TEMPLATE.format(role=user_role.lower(), query=query)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Get AI analysis
        result = model_manager.chat(messages)
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to analyze query'
            }), 500
        
        # Parse AI response
        try:
            ai_analysis = json.loads(result['response'])
        except:
            # Fallback to simple search
            ai_analysis = {
                "search_type": "similar_cases",
                "search_query": query,
                "filters": {},
                "explanation": "Fallback search"
            }
        
        # Execute the recommended search
        search_results = []
        if ai_analysis['search_type'] == 'missing_persons':
            search_results = vector_search.search_missing_persons(
                ai_analysis['search_query'], 
                10
            )
        elif ai_analysis['search_type'] == 'patients':
            search_results = vector_search.search_patients_for_reunification(
                ai_analysis['search_query'], 
                10
            )
        elif ai_analysis['search_type'] == 'matches':
            # Create person data from query
            person_data = {
                'name': 'Unknown',
                'description': ai_analysis['search_query'],
                'status': 'missing'
            }
            search_results = vector_search.find_potential_matches(
                person_data, 
                5
            )
        elif ai_analysis['search_type'] == 'reunification_protocols':
            # Extract person type and description from query
            search_results = vector_search.get_reunification_recommendations(
                ai_analysis.get('filters', {}).get('person_type', 'adult'),
                ai_analysis['search_query']
            )
        elif ai_analysis['search_type'] == 'medical_notes':
            search_results = vector_search.search_medical_notes(
                ai_analysis['search_query'], 
                10
            )
        
        # Convert results
        results_data = []
        for result in search_results:
            results_data.append({
                'id': result.id,
                'content': result.content,
                'metadata': result.metadata,
                'similarity_score': result.similarity_score,
                'source_type': result.source_type
            })
        
        return jsonify({
            'success': True,
            'ai_analysis': ai_analysis,
            'results': results_data,
            'total_found': len(results_data)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        system_prompt = TRANSCRIBE_TEXT_SYSTEM_PROMPT_TEMPLATE.format(role=user_role.lower())
        
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
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
                    {"type": "video", "path": tmp_path}
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
        import traceback
        traceback.print_exc()
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
        system_prompt = AUDIO_ENHANCEMENT_PROMPT_TEMPLATE.format(role=user_role.lower())
        
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def extract_person_characteristics(image_path: str) -> Dict:
    """Extract structured characteristics from a person's image"""
    try:
        # Create image URL for model analysis - use uploads server
        image_url = f"http://127.0.0.1:11435/{os.path.basename(image_path)}"
        
        # Detailed prompt for characteristic extraction
        prompt = CHARACTERISTIC_EXTRACTION_PROMPT
        
        # Prepare messages for chat_image method
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "url": image_url
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        # Use model manager to analyze image
        result = model_manager.chat_image(messages)
        
        if result['success']:
            try:
                # Parse JSON response - handle markdown code blocks
                import json
                import re
                
                response_text = result['response']
                
                # Try to extract JSON from markdown code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    characteristics = json.loads(json_match.group(1))
                    print(f"📸 Successfully parsed JSON from markdown: {characteristics}")
                    return characteristics
                
                # Try direct JSON parsing
                characteristics = json.loads(response_text)
                print(f"📸 Successfully parsed direct JSON: {characteristics}")
                return characteristics
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing failed: {e}")
                print(f"📸 Raw response: {result['response']}")
                # Fallback: try to extract from text
                return parse_characteristics_from_text(result['response'])
        else:
            print(f"❌ Image analysis failed: {result.get('error', 'Unknown error')}")
            return {}
            
    except Exception as e:
        print(f"❌ Error extracting characteristics: {e}")
        return {}

def parse_characteristics_from_text(text: str) -> Dict:
    """Parse characteristics from unstructured text as fallback"""
    characteristics = {
        'physical_features': {},
        'clothing': {},
        'distinctive_features': [],
        'age_range': 'Unknown'
    }
    
    try:
        # Simple parsing logic for common patterns
        text_lower = text.lower()
        
        # Extract age patterns
        import re
        age_match = re.search(r'(\d+)[-\s]*(\d+)?\s*(?:years?|y\.?o\.?)', text_lower)
        if age_match:
            if age_match.group(2):
                characteristics['age_range'] = f"{age_match.group(1)}-{age_match.group(2)}"
            else:
                age = int(age_match.group(1))
                characteristics['age_range'] = f"{age-5}-{age+5}"
        
        # Extract gender
        if 'male' in text_lower or 'man' in text_lower or 'boy' in text_lower or 'father' in text_lower or 'husband' in text_lower or 'son' in text_lower:
            characteristics['physical_features']['gender'] = 'male'
        elif 'female' in text_lower or 'woman' in text_lower or 'girl' in text_lower or 'mother' in text_lower or 'wife' in text_lower or 'daughter' in text_lower:
            characteristics['physical_features']['gender'] = 'female'
        
        # Extract hair color
        hair_colors = ['black', 'brown', 'blonde', 'red', 'gray', 'white']
        for color in hair_colors:
            if color in text_lower:
                characteristics['physical_features']['hair_color'] = color
                break
        
        # Extract eye color
        eye_colors = ['brown', 'blue', 'green', 'hazel', 'gray']
        for color in eye_colors:
            if color in text_lower:
                characteristics['physical_features']['eye_color'] = color
                break
        
        # Extract skin tone
        skin_tones = ['white', 'black', 'brown', 'tan', 'olive', 'pale', 'dark', 'light']
        for tone in skin_tones:
            if tone in text_lower:
                characteristics['physical_features']['skin_tone'] = tone
                break
        
        # Extract clothing
        if 'shirt' in text_lower or 't-shirt' in text_lower:
            characteristics['clothing']['top'] = 'shirt'
        if 'pants' in text_lower or 'jeans' in text_lower:
            characteristics['clothing']['bottom'] = 'pants'
        
        # Extract distinctive features
        distinctive_keywords = ['scar', 'birthmark', 'tattoo', 'piercing', 'glasses']
        for keyword in distinctive_keywords:
            if keyword in text_lower:
                characteristics['distinctive_features'].append(keyword)
        
        return characteristics
        
    except Exception as e:
        print(f"❌ Error parsing characteristics from text: {e}")
        return characteristics

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
            print("--- Incoming missing person data ---")
            
            # Handle both JSON and FormData
            if request.content_type and 'multipart/form-data' in request.content_type:
                # Handle file upload
                data = {
                    'name': request.form.get('name', ''),
                    'age': request.form.get('age'),
                    'description': request.form.get('description', ''),
                    'contact_info': request.form.get('contact_info', ''),
                    'reported_by': request.form.get('reported_by', 'REUNIFICATION_COORDINATOR')
                }
                
                # Handle photo upload
                image_path = None
                if 'photo' in request.files:
                    file = request.files['photo']
                    if file and file.filename != '':
                        filename = f"missing_person_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
                        image_path = os.path.join('uploads', filename)
                        file.save(image_path)
                        print(f"📸 Photo saved: {image_path}")
                    else:
                        print("📸 No photo file provided")
                else:
                    print("📸 No photo field in request")
            else:
                # Handle JSON data (legacy)
                data = request.json
                print(data)
                
                # Save image if provided as base64
                image_path = None
                if 'image_data' in data and data['image_data']:
                    import base64
                    image_data = base64.b64decode(data['image_data'].split(',')[1])
                    filename = f"missing_person_{uuid.uuid4()}.jpg"
                    image_path = os.path.join('uploads', filename)
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
            
            # Extract characteristics from image if provided
            characteristics = {}
            if image_path:
                try:
                    characteristics = extract_person_characteristics(image_path)
                    print(f"📸 Extracted characteristics: {characteristics}")
                except Exception as e:
                    print(f"⚠️  Failed to extract characteristics: {e}")
                    characteristics = {}
            
            # Prepare person data
            person_data = {
                'name': data.get('name', ''),
                'age': data.get('age'),
                'description': data.get('description', ''),
                'image_path': image_path,
                'contact_info': data.get('contact_info', ''),
                'reported_by': data.get('reported_by', 'REUNIFICATION_COORDINATOR'),
                'status': 'missing',
                'characteristics': characteristics
            }
            
            person_id = db_manager.add_missing_person(person_data)
            
            return jsonify({
                'success': True,
                'person_id': person_id,
                'message': 'Missing person added successfully'
            })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"--- Exception in missing_persons_api ---")
        print(f"Traceback (most recent call last):")
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
        prompt = request.form.get('prompt', AUDIO_TRANSCRIPTION_PROMPT)
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
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vitals', methods=['GET', 'POST'])
def vitals_api():
    """Handle vitals operations"""
    try:
        if request.method == 'GET':
            patient_id = request.args.get('patient_id')
            if not patient_id:
                return jsonify({'success': False, 'error': 'patient_id required'}), 400
            vitals = db_manager.get_vitals(patient_id)
            return jsonify({'success': True, 'vitals': vitals})
        elif request.method == 'POST':
            data = request.json
            try:
                vitals_id = db_manager.add_vitals(data)
            except Exception as e:
                import traceback
                print('--- Exception in add_vitals ---')
                traceback.print_exc()
                return jsonify({'success': False, 'error': str(e)}), 500
            return jsonify({'success': True, 'vitals_id': vitals_id, 'message': 'Vitals added successfully'})
    except Exception as e:
        import traceback
        print('--- Exception in /api/vitals ---')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/edgeai', methods=['POST'])
def edgeai_text():
    """Compatible with Android EdgeAIHTTPServer: Accepts JSON {"prompt": ..., "model": ...} and returns {"text": ...}"""
    try:
        data = request.get_json(force=True)
        prompt = data.get('prompt', '')
        model_name = data.get('model', None)
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        # Use model_manager to generate text (customize as needed)
        if hasattr(model_manager, 'chat_text'):
            # If chat_text expects messages, wrap prompt
            result = model_manager.chat_text([{"role": "user", "content": prompt}], model_name) if model_name else model_manager.chat_text([{"role": "user", "content": prompt}])
            text = result.get('response', '') if isinstance(result, dict) else result
        elif hasattr(model_manager, '_chat_edge_ai'):
            text = model_manager._chat_edge_ai(prompt)
        else:
            text = 'No compatible model_manager method found.'
        return jsonify({"text": text})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/edgeai_image', methods=['POST'])
def edgeai_image():
    """Compatible with Android EdgeAIHTTPServer: Accepts JSON {"prompt": ..., "image": base64, "model": ...} and returns {"text": ...}"""
    try:
        import base64, io
        from PIL import Image
        data = request.get_json(force=True)
        prompt = data.get('prompt', '')
        image_base64 = data.get('image', None)
        model_name = data.get('model', None)
        if not prompt or not image_base64:
            return jsonify({'error': 'Prompt and image (base64) required'}), 400
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        # If your model_manager expects a file path, save temp file
        # If it expects a PIL image or bytes, pass directly
        if hasattr(model_manager, 'chat_image'):
            # Example: chat_image expects messages
            import numpy as np
            frame = np.array(image)
            # Convert image to base64 for message
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            frame_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            messages = [
                {"role": "user", "content": [
                    {"type": "image", "path": f"data:image/jpeg;base64,{frame_base64}"},
                    {"type": "text", "text": prompt}
                ]}
            ]
            result = model_manager.chat_image(messages, model_name) if model_name else model_manager.chat_image(messages)
            text = result.get('response', '') if isinstance(result, dict) else result
        elif hasattr(model_manager, '_chat_edge_ai'):
            text = model_manager._chat_edge_ai(prompt)
        else:
            text = 'No compatible model_manager method found.'
        return jsonify({"text": text})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5050) 