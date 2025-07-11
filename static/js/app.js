// RapidCare - Mass Casualty Incident Response System
class RapidCareApp {
    constructor() {
        this.currentRole = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.stream = null;
        this.recognition = null;
        this.isOnline = navigator.onLine;
        this.currentVoiceMethod = null;
        this.currentVoiceField = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkOnlineStatus();
        this.updateStatusIndicators();
        this.loadPatients();
        
        // Initialize system messages as collapsed
        const systemMessages = document.getElementById('system-messages');
        systemMessages.classList.add('collapsed');
        this.updateSystemMessagesCount();
        
        // Check if user is already logged in
        const storedRole = localStorage.getItem('rapidcare_role');
        if (storedRole) {
            this.currentRole = storedRole;
            document.getElementById('welcome-text').textContent = `Welcome, ${this.getRoleDisplayName(storedRole)}`;
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('main-app').classList.remove('hidden');
            this.updateActionCardsForRole(storedRole);
            this.addSystemMessage(`Welcome back, ${this.getRoleDisplayName(storedRole)}. System ready for emergency response.`);
        }
        
        // Start status polling
        setInterval(() => this.updateStatusIndicators(), 30000);
    }

    setupEventListeners() {
        // Login system
        document.querySelectorAll('.role-card').forEach(card => {
            card.addEventListener('click', (e) => this.handleRoleSelection(e));
        });

        document.getElementById('logout-btn').addEventListener('click', () => this.logout());

        // Voice input dropdown
        const voiceInputBtn = document.getElementById('voice-input-btn');
        const voiceDropdownMenu = document.getElementById('voice-dropdown-menu');
        
        voiceInputBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            voiceDropdownMenu.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.voice-input-dropdown')) {
                voiceDropdownMenu.classList.remove('show');
            }
        });

        // Voice option selection
        document.querySelectorAll('.voice-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const method = option.dataset.method;
                this.selectVoiceMethod(method);
                voiceDropdownMenu.classList.remove('show');
            });
        });

        // Action cards
        document.querySelectorAll('.action-card').forEach(card => {
            const action = card.dataset.action;
            const btn = card.querySelector('.action-btn');
            btn.addEventListener('click', (e) => this.handleActionClick(action, e));
        });

        // Modal events
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.closeModal(e.target.closest('.modal')));
        });

        // Patient form
        document.getElementById('patient-form').addEventListener('submit', (e) => this.handlePatientSubmit(e));

        // SOAP form
        document.getElementById('soap-form').addEventListener('submit', (e) => this.handleSoapSubmit(e));

        // Media modal events
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        document.getElementById('capture-btn').addEventListener('click', () => this.captureImage());
        document.getElementById('record-btn').addEventListener('click', () => this.startRecording());
        document.getElementById('stop-record-btn').addEventListener('click', () => this.stopRecording());
        document.getElementById('analyze-media-btn').addEventListener('click', () => this.analyzeMedia());
        document.getElementById('close-media-btn').addEventListener('click', () => this.closeModal(document.getElementById('media-modal')));

        // AI Search events
        document.getElementById('description-search-btn').addEventListener('click', () => this.searchByDescription());
        document.getElementById('close-ai-search-btn').addEventListener('click', () => this.closeModal(document.getElementById('ai-search-modal')));

        // Photo upload for missing person form
        const photoUploadArea = document.getElementById('photo-upload-area');
        const photoInput = document.getElementById('missing-person-photo-input');
        const photoPreview = document.getElementById('photo-preview');
        const photoPreviewImg = document.getElementById('photo-preview-img');
        const removePhotoBtn = document.getElementById('remove-photo-btn');

        if (photoUploadArea && photoInput) {
            photoUploadArea.addEventListener('click', () => photoInput.click());
            photoInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        photoPreviewImg.src = e.target.result;
                        photoPreview.style.display = 'block';
                        photoUploadArea.style.display = 'none';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        if (removePhotoBtn) {
            removePhotoBtn.addEventListener('click', () => {
                photoInput.value = '';
                photoPreview.style.display = 'none';
                photoUploadArea.style.display = 'block';
            });
        }

        // Photo upload for search form
        const searchPhotoUploadArea = document.getElementById('search-photo-upload-area');
        const searchPhotoInput = document.getElementById('search-photo-input');
        const searchPhotoPreview = document.getElementById('search-photo-preview');
        const searchPhotoPreviewImg = document.getElementById('search-photo-preview-img');
        const removeSearchPhotoBtn = document.getElementById('remove-search-photo-btn');
        const searchMatchBtn = document.getElementById('search-match-btn');

        if (searchPhotoUploadArea && searchPhotoInput) {
            searchPhotoUploadArea.addEventListener('click', () => searchPhotoInput.click());
            searchPhotoInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        searchPhotoPreviewImg.src = e.target.result;
                        searchPhotoPreview.style.display = 'block';
                        searchPhotoUploadArea.style.display = 'none';
                        if (searchMatchBtn) searchMatchBtn.disabled = false;
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        if (removeSearchPhotoBtn) {
            removeSearchPhotoBtn.addEventListener('click', () => {
                searchPhotoInput.value = '';
                searchPhotoPreview.style.display = 'none';
                searchPhotoUploadArea.style.display = 'block';
                if (searchMatchBtn) searchMatchBtn.disabled = true;
            });
        }

        // File upload
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
        uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Voice input for notes
        document.getElementById('notes-voice-btn').addEventListener('click', (e) => {
            e.preventDefault();
            this.startVoiceInput('patient-notes');
        });

        // Patient section click
        document.getElementById('patient-section').addEventListener('click', (e) => {
            // Don't trigger if clicking on a patient card (for doctors)
            if (e.target.closest('.patient-card')) {
                return;
            }
            this.showPatientsList();
        });

        // System messages toggle
        document.getElementById('system-messages-header').addEventListener('click', (e) => {
            if (!e.target.closest('.clear-messages-btn')) {
                this.toggleSystemMessages();
            }
        });

        // Clear messages button
        document.getElementById('clear-messages-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.clearSystemMessages();
        });

        // Stop recording button
        document.getElementById('stop-recording-btn').addEventListener('click', () => {
            this.stopRecording();
        });

        // SOAP notes voice input buttons
        document.getElementById('soap-subjective-voice-btn').addEventListener('click', (e) => {
            e.preventDefault();
            this.startVoiceInput('soap-subjective');
        });
        document.getElementById('soap-objective-voice-btn').addEventListener('click', (e) => {
            e.preventDefault();
            this.startVoiceInput('soap-objective');
        });
        document.getElementById('soap-assessment-voice-btn').addEventListener('click', (e) => {
            e.preventDefault();
            this.startVoiceInput('soap-assessment');
        });
        document.getElementById('soap-plan-voice-btn').addEventListener('click', (e) => {
            e.preventDefault();
            this.startVoiceInput('soap-plan');
        });

        // Vitals form submit
        document.getElementById('vitals-form').addEventListener('submit', (e) => this.handleVitalsSubmit(e));

        // Vitals dictation buttons
        const overallBtn = document.getElementById('vitals-overall-dictation-btn');
        if (overallBtn) {
            overallBtn.addEventListener('click', () => {
                this.stopVoiceInput();
                // Show stop button
                const stopBtn = document.getElementById('vitals-stop-dictation-btn');
                if (stopBtn) stopBtn.style.display = 'inline-block';
                if (!('webkitSpeechRecognition' in window)) {
                    alert('Speech recognition not supported in this browser.');
                    return;
                }
                this.recognition = new webkitSpeechRecognition();
                this.recognition.lang = 'en-US';
                this.recognition.interimResults = false;
                this.recognition.maxAlternatives = 1;
                this.recognition.onresult = (event) => {
                    let transcript = event.results[0][0].transcript.trim().toLowerCase();
                    // Parse all vitals from transcript
                    const fields = {
                        'vitals-heart-rate': /heart rate(?: is|:)?\s*(\d+)/,
                        'vitals-bp-sys': /blood pressure(?: is|:)?\s*(\d+)[^\d]+(\d+)/,
                        'vitals-bp-dia': /blood pressure(?: is|:)?\s*(\d+)[^\d]+(\d+)/,
                        'vitals-resp-rate': /respiratory rate(?: is|:)?\s*(\d+)/,
                        'vitals-o2-sat': /o2|oxygen saturation(?: is|:)?\s*(\d+)/,
                        'vitals-temperature': /temperature(?: is|:)?\s*(\d+(?:\.\d+)?)/,
                        'vitals-pain-score': /pain score(?: is|:)?\s*(\d+)/
                    };
                    // Heart rate
                    const hr = transcript.match(fields['vitals-heart-rate']);
                    if (hr) document.getElementById('vitals-heart-rate').value = hr[1];
                    // Blood pressure
                    const bp = transcript.match(fields['vitals-bp-sys']);
                    if (bp) {
                        document.getElementById('vitals-bp-sys').value = bp[1];
                        document.getElementById('vitals-bp-dia').value = bp[2];
                    }
                    // Respiratory rate
                    const rr = transcript.match(fields['vitals-resp-rate']);
                    if (rr) document.getElementById('vitals-resp-rate').value = rr[1];
                    // O2 saturation
                    const o2 = transcript.match(fields['vitals-o2-sat']);
                    if (o2) document.getElementById('vitals-o2-sat').value = o2[1];
                    // Temperature
                    const temp = transcript.match(fields['vitals-temperature']);
                    if (temp) document.getElementById('vitals-temperature').value = temp[1];
                    // Pain score
                    const pain = transcript.match(fields['vitals-pain-score']);
                    if (pain) document.getElementById('vitals-pain-score').value = pain[1];
                    this.addSystemMessage('Overall dictation parsed and fields filled.');
                    if (stopBtn) stopBtn.style.display = 'none';
                };
                this.recognition.onend = () => {
                    const stopBtn = document.getElementById('vitals-stop-dictation-btn');
                    if (stopBtn) stopBtn.style.display = 'none';
                };
                this.recognition.start();
            });
        }

        // Missing person form submit
        const missingPersonForm = document.getElementById('missing-person-form');
        if (missingPersonForm) {
            missingPersonForm.addEventListener('submit', (e) => this.handleMissingPersonSubmit(e));
        }

        // Find match form submit
        const findMatchForm = document.getElementById('find-match-form');
        if (findMatchForm) {
            findMatchForm.addEventListener('submit', (e) => this.handleFindMatchSubmit(e));
        }
        // Voice input for each vitals field
        const vitalsVoiceFields = [
            { btn: 'vitals-heart-rate-voice-btn', field: 'vitals-heart-rate' },
            { btn: 'vitals-bp-voice-btn', field: 'vitals-bp-sys' },
            { btn: 'vitals-resp-rate-voice-btn', field: 'vitals-resp-rate' },
            { btn: 'vitals-o2-sat-voice-btn', field: 'vitals-o2-sat' },
            { btn: 'vitals-temperature-voice-btn', field: 'vitals-temperature' },
            { btn: 'vitals-pain-score-voice-btn', field: 'vitals-pain-score' }
        ];
        vitalsVoiceFields.forEach(({btn, field}) => {
            const button = document.getElementById(btn);
            if (button) {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.startVoiceInput(field);
                });
            }
        });

        // Online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Delegated event listener for create patient button (handles dynamically created buttons)
        document.addEventListener('click', (e) => {
            if (e.target.closest('#create-patient-btn')) {
                const button = e.target.closest('#create-patient-btn');
                const triageLevel = button.dataset.triageLevel;
                const reasoning = decodeURIComponent(button.dataset.reasoning);
                console.log('Create patient button clicked:', { triageLevel, reasoning });
                try {
                    this.createPatientFromTriage(triageLevel, reasoning);
                } catch (error) {
                    console.error('Error in createPatientFromTriage:', error);
                    this.addSystemMessage(`Error creating patient: ${error.message}`);
                }
            }
        });

        // Delegated event listener for paramedic patient card click in recent patients
        document.getElementById('patients-list').addEventListener('click', (e) => {
            if (this.currentRole === 'PARAMEDIC') {
                const card = e.target.closest('.patient-card');
                if (card && card.hasAttribute('data-patient-id')) {
                    const patientId = card.getAttribute('data-patient-id');
                    this.openVitalsModal(patientId);
                }
            }
        });
        // Delegated event listener for paramedic patient card click in all patients modal
        const allPatientsList = document.getElementById('all-patients-list');
        if (allPatientsList) {
            allPatientsList.addEventListener('click', (e) => {
                if (this.currentRole === 'PARAMEDIC') {
                    const card = e.target.closest('.patient-card');
                    if (card && card.hasAttribute('data-patient-id')) {
                        const patientId = card.getAttribute('data-patient-id');
                        this.openVitalsModal(patientId);
                    }
                }
            });
        }

        // Vitals audio upload/record
        const recordBtn = document.getElementById('vitals-record-btn');
        const progressDiv = document.getElementById('vitals-record-progress');
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        
        if (recordBtn) recordBtn.addEventListener('click', async () => {
            if (!isRecording) {
                // Start recording
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    alert('Audio recording not supported in this browser.');
                    return;
                }
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    mediaRecorder.ondataavailable = (e) => {
                        if (e.data.size > 0) audioChunks.push(e.data);
                    };
                    mediaRecorder.onstop = async () => {
                        progressDiv.style.display = 'block';
                        progressDiv.textContent = 'Transcribing audio...';
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const formData = new FormData();
                        formData.append('file', audioBlob, 'vitals.webm');
                        try {
                            const resp = await fetch('/api/transcribe-audio', { method: 'POST', body: formData });
                            const data = await resp.json();
                            if (!data.success || !data.transcription) {
                                progressDiv.textContent = 'Transcription failed.';
                                isRecording = false;
                                recordBtn.textContent = 'Record Vitals';
                                return;
                            }
                            progressDiv.textContent = 'Extracting vitals from transcription (AI)...';

                            const extractResp = await fetch('/chat/text', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    messages: [
                                        { role: 'system', content: [ {"type": "text", "text": PROMPTS.VITALS_EXTRACTION }] },
                                        { role: 'user', content: [ {"type": "text", "text": `Text: ${data.transcription}`}] }
                                    ]
                                })
                            });
                            const extractData = await extractResp.json();
                            let vitals = null;
                            if (extractData.success && extractData.response) {
                                try {
                                    const match = extractData.response.match(/\{[\s\S]*\}/);
                                    if (match) {
                                        vitals = JSON.parse(match[0]);
                                    }
                                } catch (err) {}
                            }
                            if (vitals) {
                                if (vitals.heart_rate) document.getElementById('vitals-heart-rate').value = vitals.heart_rate;
                                if (vitals.bp_sys) document.getElementById('vitals-bp-sys').value = vitals.bp_sys;
                                if (vitals.bp_dia) document.getElementById('vitals-bp-dia').value = vitals.bp_dia;
                                if (vitals.resp_rate) document.getElementById('vitals-resp-rate').value = vitals.resp_rate;
                                if (vitals.o2_sat) document.getElementById('vitals-o2-sat').value = vitals.o2_sat;
                                if (vitals.temperature) document.getElementById('vitals-temperature').value = vitals.temperature;
                                if (vitals.pain_score) document.getElementById('vitals-pain-score').value = vitals.pain_score;
                                progressDiv.textContent = 'Vitals extracted and fields filled.';
                            } else {
                                progressDiv.textContent = 'Could not extract vitals from transcription.';
                            }
                        } catch (err) {
                            progressDiv.textContent = 'Error during audio transcription or extraction.';
                        }
                        setTimeout(() => { progressDiv.style.display = 'none'; }, 4000);
                        isRecording = false;
                        recordBtn.textContent = 'Record Vitals';
                    };
                    mediaRecorder.start();
                    isRecording = true;
                    recordBtn.textContent = 'Stop Recording';
                    progressDiv.style.display = 'block';
                    progressDiv.textContent = 'Recording...';
                } catch (err) {
                    alert('Could not start audio recording: ' + err.message);
                }
            } else {
                // Stop recording
                if (mediaRecorder && isRecording) {
                    mediaRecorder.stop();
                }
            }
        });
    }

    handleRoleSelection(event) {
        const roleCard = event.currentTarget;
        const role = roleCard.dataset.role;

        // Remove previous selection
        document.querySelectorAll('.role-card').forEach(card => card.classList.remove('selected'));

        // Select current role
        roleCard.classList.add('selected');

        // Store role and show main app
        this.currentRole = role;
        localStorage.setItem('rapidcare_role', role);

        // Update welcome message
        document.getElementById('welcome-text').textContent = `Welcome, ${this.getRoleDisplayName(role)}`;

        // Show main app
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('main-app').classList.remove('hidden');

        // Update action cards based on role
        this.updateActionCardsForRole(role);

        // Add system message
        this.addSystemMessage(`Logged in as ${this.getRoleDisplayName(role)}. System ready for emergency response.`);
    }

    updateActionCardsForRole(role) {
        const actionGrid = document.querySelector('.action-grid');
        
        if (role === 'REUNIFICATION_COORDINATOR') {
            // Show reunification-specific actions
            actionGrid.innerHTML = `
                <div class="action-card" data-action="submit-missing-person">
                    <div class="action-icon">
                        <i class="fas fa-user-plus"></i>
                    </div>
                    <h3>Submit Missing Person</h3>
                    <p>Report a missing person with photo and details</p>
                    <button class="action-btn">
                        <i class="fas fa-upload"></i>
                        Submit Report
                    </button>
                </div>

                <div class="action-card" data-action="find-match">
                    <div class="action-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h3>Find Match</h3>
                    <p>Search for matching missing persons using photo</p>
                    <button class="action-btn">
                        <i class="fas fa-camera"></i>
                        Search Database
                    </button>
                </div>

                <div class="action-card" data-action="view-missing-persons">
                    <div class="action-icon">
                        <i class="fas fa-list"></i>
                    </div>
                    <h3>View Missing Persons</h3>
                    <p>View all reported missing persons</p>
                    <button class="action-btn">
                        <i class="fas fa-eye"></i>
                        View All
                    </button>
                </div>

                <div class="action-card" data-action="view-patients">
                    <div class="action-icon">
                        <i class="fas fa-hospital-user"></i>
                    </div>
                    <h3>View Patients</h3>
                    <p>View all patient records for matching</p>
                    <button class="action-btn">
                        <i class="fas fa-users"></i>
                        View Patients
                    </button>
                </div>
            `;
        } else if (role === 'DOCTOR') {
            // Show doctor-specific actions
            actionGrid.innerHTML = `
                <div class="action-card" data-action="view-patients">
                    <div class="action-icon">
                        <i class="fas fa-stethoscope"></i>
                    </div>
                    <h3>Patient List</h3>
                    <p>View and manage all patient records with SOAP notes</p>
                    <button class="action-btn">
                        <i class="fas fa-users"></i>
                        View Patients
                    </button>
                </div>

                <div class="action-card" data-action="create-patient">
                    <div class="action-icon">
                        <i class="fas fa-user-plus"></i>
                    </div>
                    <h3>Create Patient</h3>
                    <p>Add a new patient to the system</p>
                    <button class="action-btn">
                        <i class="fas fa-plus"></i>
                        Add Patient
                    </button>
                </div>
            `;
        } else {
            // Show paramedic/nurse actions
            actionGrid.innerHTML = `
                <div class="action-card" data-action="video-analysis">
                    <div class="action-icon">
                        <i class="fas fa-video"></i>
                    </div>
                    <h3>Video Analysis</h3>
                    <p>Analyze video for triage assessment</p>
                    <button class="action-btn">
                        <i class="fas fa-play"></i>
                        Analyze Video
                    </button>
                </div>

                <div class="action-card" data-action="image-analysis">
                    <div class="action-icon">
                        <i class="fas fa-camera"></i>
                    </div>
                    <h3>Image Analysis</h3>
                    <p>Analyze images for triage assessment</p>
                    <button class="action-btn">
                        <i class="fas fa-search"></i>
                        Analyze Image
                    </button>
                </div>

                <div class="action-card" data-action="create-patient">
                    <div class="action-icon">
                        <i class="fas fa-user-plus"></i>
                    </div>
                    <h3>Create Patient</h3>
                    <p>Add a new patient to the system</p>
                    <button class="action-btn">
                        <i class="fas fa-plus"></i>
                        Add Patient
                    </button>
                </div>

                <div class="action-card" data-action="view-patients">
                    <div class="action-icon">
                        <i class="fas fa-hospital-user"></i>
                    </div>
                    <h3>View Patients</h3>
                    <p>View all patient records</p>
                    <button class="action-btn">
                        <i class="fas fa-users"></i>
                        View Patients
                    </button>
                </div>
            `;
        }

        // Add event listeners to the new action cards
        document.querySelectorAll('.action-card').forEach(card => {
            const action = card.dataset.action;
            const btn = card.querySelector('.action-btn');
            if (btn) {
                btn.addEventListener('click', (e) => this.handleActionClick(action, e));
            }
        });
    }

    getRoleDisplayName(role) {
        const roleNames = {
            'PARAMEDIC': 'Paramedic',
            'NURSE': 'Nurse',
            'DOCTOR': 'Doctor',
            'REUNIFICATION_COORDINATOR': 'Reunification Coordinator'
        };
        return roleNames[role] || role;
    }

    logout() {
        this.currentRole = null;
        localStorage.removeItem('rapidcare_role');
        
        // Clear system messages
        document.getElementById('system-messages').innerHTML = `
            <div class="message system">
                <div class="message-content">
                    <i class="fas fa-info-circle"></i>
                    <span>System ready. Select an action to begin.</span>
                </div>
            </div>
        `;

        // Show login screen
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('login-screen').style.display = 'flex';
    }

    handleActionClick(action, event) {
        event.preventDefault();
        console.log('Action clicked:', action);

        switch (action) {
            case 'video-analysis':
                this.openMediaModal('Video Analysis', 'video');
                break;
            case 'image-analysis':
                this.openMediaModal('Image Analysis', 'image');
                break;
            case 'voice-input':
                console.log('Voice input action triggered');
                this.openVoiceInputModal();
                break;
            case 'ai-search':
                this.showModal(document.getElementById('ai-search-modal'));
                break;
            case 'create-patient':
                this.openPatientModal();
                break;
            case 'view-patients':
                this.showPatientsList();
                break;
            case 'submit-missing-person':
                this.openMissingPersonModal();
                break;
            case 'find-match':
                this.openFindMatchModal();
                break;
            case 'view-missing-persons':
                this.showMissingPersonsList();
                break;
        }
    }

    openMediaModal(title, type) {
        const modal = document.getElementById('media-modal');
        document.getElementById('media-modal-title').textContent = title;
        
        // Set active tab based on type
        const tab = type === 'video' ? 'camera' : 'upload';
        this.switchTab(tab);
        
        this.showModal(modal);
        
        if (type === 'video') {
            this.startCamera();
        }
    }

    openPatientModal() {
        const modal = document.getElementById('patient-modal');
        
        // Generate RFID
        const rfid = 'RFID_' + Date.now().toString(36).toUpperCase();
        document.getElementById('patient-rfid').value = rfid;
        
        // Clear form
        document.getElementById('patient-form').reset();
        document.getElementById('patient-rfid').value = rfid;
        
        this.showModal(modal);
    }

    openMissingPersonModal() {
        const modal = document.getElementById('missing-person-modal');
        
        // Clear form
        document.getElementById('missing-person-form').reset();
        
        this.showModal(modal);
    }

    openFindMatchModal() {
        const modal = document.getElementById('find-match-modal');
        
        // Clear form
        document.getElementById('find-match-form').reset();
        
        this.showModal(modal);
    }

    showMissingPersonsList() {
        // For now, just show the AI search modal with missing persons tab
        const modal = document.getElementById('ai-search-modal');
        this.showModal(modal);
        
        // Switch to missing persons tab
        this.switchTab('missing-persons');
    }

    showModal(modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modal) {
        if (!modal) return;
        
        modal.classList.remove('show');
        document.body.style.overflow = '';
        
        // Stop camera/recording if active
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.isRecording) {
            this.stopRecording();
        }
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `${tabName}-tab`);
        });
    }

    async startCamera() {
        try {
            // Check if MediaDevices API is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('MediaDevices API not supported in this browser');
            }

            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: true, 
                audio: false 
            });
            
            const video = document.getElementById('camera-preview');
            video.srcObject = this.stream;
            
            this.addSystemMessage('Camera started. Ready to capture or record.');
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.addSystemMessage('Error: Could not access camera - ' + error.message);
        }
    }

    captureImage() {
        const video = document.getElementById('camera-preview');
        const canvas = document.getElementById('capture-canvas');
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        canvas.toBlob((blob) => {
            this.analyzeImage(blob);
        }, 'image/jpeg', 0.8);
    }

    startRecording() {
        if (!this.stream) {
            this.addSystemMessage('Error: Camera not available');
            return;
        }

        // Clear any existing recorded video preview
        this.clearRecordedVideoPreview();

        this.recordedChunks = [];
        this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: 'video/webm' });

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = () => {
            const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
            this.showRecordedVideoPreview(blob);
            this.analyzeVideo(blob);
        };

        this.mediaRecorder.start();
        this.isRecording = true;

        document.getElementById('record-btn').style.display = 'none';
        document.getElementById('stop-record-btn').style.display = 'inline-block';

        this.addSystemMessage('Recording started...');
    }

    showRecordedVideoPreview(blob) {
        const cameraContainer = document.querySelector('.camera-container');
        const videoPreview = document.getElementById('camera-preview');
        
        // Remove any existing recorded video preview
        const existingPreview = cameraContainer.querySelector('.recorded-video-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        // Remove any existing label
        const existingLabel = cameraContainer.querySelector('.recorded-video-label');
        if (existingLabel) {
            existingLabel.remove();
        }
        
        // Create video preview element
        const recordedVideo = document.createElement('video');
        recordedVideo.className = 'recorded-video-preview';
        recordedVideo.controls = true;
        recordedVideo.muted = true;
        recordedVideo.style.width = '100%';
        recordedVideo.style.maxWidth = '400px';
        recordedVideo.style.height = '225px';
        recordedVideo.style.borderRadius = '0.375rem';
        recordedVideo.style.marginBottom = '1rem';
        recordedVideo.style.background = 'var(--bg-primary)';
        
        // Set video source
        const videoUrl = URL.createObjectURL(blob);
        recordedVideo.src = videoUrl;
        
        // Create label
        const label = document.createElement('p');
        label.className = 'recorded-video-label';
        label.textContent = 'Recorded Video Preview:';
        label.style.fontWeight = 'bold';
        label.style.marginBottom = '0.5rem';
        label.style.color = 'var(--text-primary)';
        
        // Insert after the camera preview
        videoPreview.parentNode.insertBefore(label, videoPreview.nextSibling);
        label.parentNode.insertBefore(recordedVideo, label.nextSibling);
        
        // Auto-play the preview
        recordedVideo.play();
    }

    clearRecordedVideoPreview() {
        const cameraContainer = document.querySelector('.camera-container');
        if (!cameraContainer) return;
        
        const existingPreview = cameraContainer.querySelector('.recorded-video-preview');
        const existingLabel = cameraContainer.querySelector('.recorded-video-label');
        
        if (existingPreview) {
            existingPreview.remove();
        }
        if (existingLabel) {
            existingLabel.remove();
        }
    }

    // AI Search Methods
    async searchByDescription() {
        const description = document.getElementById('description-search-input').value.trim();
        
        if (!description) {
            this.addSystemMessage('Please describe the missing person');
            return;
        }

        try {
            this.addSystemMessage('Searching by description...');
            
            const response = await fetch('/api/search/missing-persons-by-description', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: description,
                    limit: 10
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.displaySearchResults(data.results, { 
                    search_type: 'description_search',
                    parsed_characteristics: data.parsed_characteristics
                });
                this.addSystemMessage(`Found ${data.total_found} potential matches`);
            } else {
                this.addSystemMessage(`Search failed: ${data.error}`);
            }
        } catch (error) {
            console.error('Error searching by description:', error);
            this.addSystemMessage(`Error: ${error.message}`);
        }
    }



    displaySearchResults(results, analysis = {}) {
        const resultsContainer = document.getElementById('search-results');
        
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <h4>No results found</h4>
                    <p>Try adjusting your search terms or filters</p>
                </div>
            `;
            return;
        }

        let resultsHTML = '';
        
        if (analysis.explanation) {
            resultsHTML += `
                <div class="search-analysis">
                    <h4>AI Analysis</h4>
                    <p>${analysis.explanation}</p>
                </div>
            `;
        }

        resultsHTML += '<h4>Search Results</h4>';
        
        results.forEach(result => {
            const sourceType = this.getSourceTypeDisplay(result.source_type);
            const metadata = this.formatMetadata(result.metadata);
            
            // Add image display for missing person results
            let imageHTML = '';
            if (result.source_type === 'missing_person' && result.metadata && result.metadata.image_path) {
                const imageFilename = result.metadata.image_path.split('/').pop();
                // Use the same server to serve images (relative URL)
                const imageUrl = `/uploads/${imageFilename}`;
                console.log('🔍 Debug - Image path:', result.metadata.image_path);
                console.log('🔍 Debug - Image filename:', imageFilename);
                console.log('🔍 Debug - Image URL:', imageUrl);
                imageHTML = `
                    <div class="search-result-image">
                        <img src="${imageUrl}" alt="Photo of ${result.metadata.name || 'missing person'}" 
                             onerror="this.style.display='none'; this.onerror=null; console.log('❌ Image failed to load:', this.src);"
                             onload="console.log('✅ Image loaded successfully:', this.src);">
                    </div>
                `;
            }
            
            resultsHTML += `
                <div class="search-result-item">
                    <div class="search-result-header">
                        <span class="search-result-type">${sourceType}</span>
                        <span class="search-result-score">Similarity: ${(result.similarity_score * 100).toFixed(1)}%</span>
                    </div>
                    ${imageHTML}
                    <div class="search-result-content">
                        ${this.formatContent(result.content)}
                    </div>
                    <div class="search-result-metadata">
                        ${metadata}
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = resultsHTML;
    }

    getSourceTypeDisplay(sourceType) {
        const typeMap = {
            'patient': 'Patient Record',
            'missing_person': 'Missing Person',
            'soap_note': 'SOAP Note',
            'video_analysis': 'Video Analysis',
            'vitals': 'Vitals Record'
        };
        return typeMap[sourceType] || sourceType;
    }

    formatContent(content) {
        // Format content for display
        return content.replace(/\n/g, '<br>').substring(0, 300) + (content.length > 300 ? '...' : '');
    }

    formatMetadata(metadata) {
        if (!metadata) return '';
        
        let metadataHTML = '';
        if (metadata.name) metadataHTML += `<span><strong>Name:</strong> ${metadata.name}</span>`;
        if (metadata.triage_level) metadataHTML += `<span><strong>Triage:</strong> ${metadata.triage_level}</span>`;
        if (metadata.location) metadataHTML += `<span><strong>Location:</strong> ${metadata.location}</span>`;
        if (metadata.created_at) metadataHTML += `<span><strong>Date:</strong> ${new Date(metadata.created_at).toLocaleString()}</span>`;
        
        return metadataHTML;
    }

    stopRecording() {
        if (this.recognition) {
            this.recognition.stop();
        }
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        this.isRecording = false;
        document.getElementById('recording-status-text').textContent = 'Recording stopped';
        
        // Reset voice input button state
        const voiceInputBtn = document.getElementById('voice-input-btn');
        voiceInputBtn.classList.remove('recording');
        voiceInputBtn.innerHTML = `
            <i class="fas fa-microphone"></i>
            <span>Voice Input</span>
            <i class="fas fa-chevron-down"></i>
        `;
    }

    handleFileDrop(event) {
        event.preventDefault();
        document.getElementById('upload-area').classList.remove('drag-over');
        
        const files = event.dataTransfer.files;
        this.processFiles(files);
    }

    handleFileSelect(event) {
        const files = event.target.files;
        this.processFiles(files);
    }

    processFiles(files) {
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';

        Array.from(files).forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            if (file.type.startsWith('video/')) {
                // Create video preview for video files
                const videoUrl = URL.createObjectURL(file);
            fileItem.innerHTML = `
                    <div class="file-preview">
                        <video class="video-preview" controls muted>
                            <source src="${videoUrl}" type="${file.type}">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    <div class="file-info">
                        <i class="fas fa-video"></i>
                        <span>${file.name}</span>
                        <button class="analyze-file-btn" data-file="${file.name}">Analyze</button>
                    </div>
                `;
            } else if (file.type.startsWith('image/')) {
                // Create image preview for image files
                const imageUrl = URL.createObjectURL(file);
                fileItem.innerHTML = `
                    <div class="file-preview">
                        <img class="image-preview" src="${imageUrl}" alt="${file.name}">
                    </div>
                    <div class="file-info">
                        <i class="fas fa-image"></i>
                        <span>${file.name}</span>
                        <button class="analyze-file-btn" data-file="${file.name}">Analyze</button>
                    </div>
                `;
            } else {
                // Default file display for other types
                fileItem.innerHTML = `
                    <div class="file-info">
                <i class="fas fa-file"></i>
                <span>${file.name}</span>
                <button class="analyze-file-btn" data-file="${file.name}">Analyze</button>
                    </div>
            `;
            }
            
            fileList.appendChild(fileItem);

            // Add analyze button event
            fileItem.querySelector('.analyze-file-btn').addEventListener('click', () => {
                this.analyzeFile(file);
            });
        });
    }

    analyzeFile(file) {
        this.addSystemMessage(`Analyzing ${file.name}...`);
        
        if (file.type.startsWith('image/')) {
            this.analyzeImage(file);
        } else if (file.type.startsWith('video/')) {
            this.analyzeVideo(file);
        } else {
            this.addSystemMessage('Error: Unsupported file type');
        }
    }

    async analyzeImage(file) {
        try {
            this.addSystemMessage('Analyzing image...');
            
            const formData = new FormData();
            formData.append('files', file);
            formData.append('role', this.currentRole);

            const response = await fetch('/api/analyze-media', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.addSystemMessage('Analysis complete!');
                this.showTriageResult(data.analysis);
                this.closeModal(document.getElementById('media-modal'));
            } else {
                this.addSystemMessage(`Analysis failed: ${data.error}`);
            }
        } catch (error) {
            console.error('Error analyzing image:', error);
            this.addSystemMessage(`Error: ${error.message}`);
        }
    }

    async analyzeVideo(file) {
        try {
            this.addSystemMessage('Analyzing video...');
            
            const formData = new FormData();
            formData.append('files', file);
            formData.append('role', this.currentRole);

            const response = await fetch('/api/analyze-media', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.addSystemMessage('Analysis complete!');
                this.showTriageResult(data.analysis);
                this.closeModal(document.getElementById('media-modal'));
            } else {
                this.addSystemMessage(`Analysis failed: ${data.error}`);
            }
        } catch (error) {
            console.error('Error analyzing video:', error);
            this.addSystemMessage(`Error: ${error.message}`);
        }
    }

    analyzeMedia() {
        // This will be called from the media modal
        const fileList = document.getElementById('file-list');
        const files = fileList.querySelectorAll('.file-item');
        const analyzeBtn = document.getElementById('analyze-media-btn');
        
        if (files.length === 0) {
            this.addSystemMessage('Please select files to analyze');
            return;
        }

        // Disable button and show loading
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

        // For now, analyze the first file
        const firstFile = files[0];
        const fileName = firstFile.querySelector('.analyze-file-btn').dataset.file;
        
        // Find the actual file object
        const fileInput = document.getElementById('file-input');
        const file = Array.from(fileInput.files).find(f => f.name === fileName);
        
        if (file) {
            if (file.type.startsWith('image/')) {
                this.analyzeImage(file).finally(() => {
                    // Re-enable button
                    analyzeBtn.disabled = false;
                    analyzeBtn.innerHTML = '<i class="fas fa-brain"></i> Analyze Media';
                });
            } else if (file.type.startsWith('video/')) {
                this.analyzeVideo(file).finally(() => {
                    // Re-enable button
                    analyzeBtn.disabled = false;
                    analyzeBtn.innerHTML = '<i class="fas fa-brain"></i> Analyze Media';
                });
            } else {
                this.addSystemMessage('Error: Unsupported file type');
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="fas fa-brain"></i> Analyze Media';
            }
        } else {
            this.addSystemMessage('Error: File not found');
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-brain"></i> Analyze Media';
        }
    }

    showTriageResult(analysis) {
        const modal = document.getElementById('triage-modal');
        const body = document.getElementById('triage-modal-body');

        // Handle both old and new response formats
        let analysisText = '';
        let confidence = 0.8; // Default confidence
        let imageUrl = null;
        
        if (typeof analysis === 'string') {
            // New format: analysis is directly the string
            analysisText = analysis;
        } else if (analysis && analysis.description) {
            // Old format: analysis.description contains the text
            analysisText = analysis.description;
            confidence = analysis.confidence || 0.8;
            imageUrl = analysis.image_url;
        } else {
            console.error('Invalid analysis data:', analysis);
            body.innerHTML = `
                <div class="triage-result">
                    <div class="triage-header yellow">
                        <h4>Analysis Error</h4>
                    </div>
                    <div class="triage-reasoning">
                        <p>Unable to parse analysis results. Please try again.</p>
                    </div>
                    <div class="triage-buttons">
                        <button class="btn-secondary" onclick="app.closeModal(document.getElementById('triage-modal'))">
                            <i class="fas fa-times"></i>
                            Close
                        </button>
                    </div>
                </div>
            `;
            this.showModal(modal);
            this.addSystemMessage('Error: Could not parse analysis results');
            return;
        }

        // Extract individual analysis from combined result
        const individualAnalysis = this.extractIndividualAnalysis(analysisText);
        
        // Parse triage data
        const triageData = this.parseTriageResponse(individualAnalysis);
        
        // Create image preview if available
        const imagePreview = imageUrl ? `
            <div class="image-preview">
                <h5>Patient Image:</h5>
                <div class="image-container">
                    <img src="${imageUrl}" alt="Patient Image" class="patient-image" />
                </div>
            </div>
        ` : '';
        
        body.innerHTML = `
            <div class="triage-result">
                <div class="triage-header ${triageData.level.toLowerCase()}">
                    <h4>Triage Level: ${triageData.level}</h4>
                    <div class="confidence">Confidence: ${Math.round(confidence * 100)}%</div>
                </div>
                
                ${imagePreview}
                
                <div class="patient-info">
                    <h5>Patient Information:</h5>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Age:</strong> ${triageData.patientInfo.age}
                        </div>
                        <div class="info-item">
                            <strong>Gender:</strong> ${triageData.patientInfo.gender}
                        </div>
                        <div class="info-item">
                            <strong>Mechanism of Injury:</strong> ${triageData.patientInfo.mechanism}
                        </div>
                        <div class="info-item full-width">
                            <strong>Assessment Findings:</strong> ${triageData.patientInfo.assessment}
                        </div>
                    </div>
                </div>
                
                <div class="triage-reasoning">
                    <h5>Reasoning:</h5>
                    <p>${triageData.reasoning}</p>
                </div>
                
                <div class="triage-actions">
                    <h5>Immediate Actions:</h5>
                    <ul>
                        ${triageData.actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="triage-buttons">
                    <button class="btn-primary" id="create-patient-btn" data-triage-level="${triageData.level}" data-reasoning="${encodeURIComponent(triageData.reasoning)}">
                        <i class="fas fa-user-plus"></i>
                        Create Patient
                    </button>
                    <button class="btn-secondary" onclick="app.closeModal(document.getElementById('triage-modal'))">
                        <i class="fas fa-times"></i>
                        Close
                    </button>
                </div>
            </div>
        `;

        this.showModal(modal);
        this.addSystemMessage(`Triage assessment complete: ${triageData.level} level patient`);
    }

    extractIndividualAnalysis(combinedAnalysis) {
        console.log('Extracting individual analysis from:', combinedAnalysis);
        
        // First, check if this is already in the individual format (like the logs show)
        const individualFormatMatch = combinedAnalysis.match(/^\*\*Triage: ([^*]+)\*\*\n\*\*Reasoning:\*\* ([\s\S]*?)(?=\*\*Action:\*\*|$)/);
        if (individualFormatMatch) {
            const triageLevel = individualFormatMatch[1].trim();
            const reasoning = individualFormatMatch[2].trim();
            console.log('Found individual format:', { triageLevel, reasoning });
            
            // Extract the full text including actions
            const fullMatch = combinedAnalysis.match(/^\*\*Triage: ([^*]+)\*\*\n\*\*Reasoning:\*\* ([\s\S]*?)\*\*Action:\*\* ([\s\S]*?)(?=\n\n|$)/);
            if (fullMatch) {
                const triageLevel = fullMatch[1].trim();
                const reasoning = fullMatch[2].trim();
                const actions = fullMatch[3].trim();
                console.log('Found individual format with actions:', { triageLevel, reasoning, actions });
                return `**Triage: ${triageLevel}**\n**Reasoning:** ${reasoning}\n**Action:** ${actions}`;
            }
            
            return `**Triage: ${triageLevel}**\n**Reasoning:** ${reasoning}`;
        }
        
        // Check for the combined format with "Analysis:" prefix
        const combinedFormatMatch = combinedAnalysis.match(/Analysis: \*\*Triage: ([^*]+)\*\* \*\*Reasoning:\*\* ([\s\S]*?)(?=\*\*Action:\*\*|$)/);
        if (combinedFormatMatch) {
            const triageLevel = combinedFormatMatch[1].trim();
            const reasoning = combinedFormatMatch[2].trim();
            console.log('Found combined format:', { triageLevel, reasoning });
            return `**Triage: ${triageLevel}**\n**Reasoning:** ${reasoning}`;
        }
        
        // Fallback: try to extract just the triage and reasoning from the combined text
        const triageMatch = combinedAnalysis.match(/\*\*Triage: ([^*]+)\*\*/);
        if (triageMatch) {
            const triageLevel = triageMatch[1].trim();
            // Extract the reasoning part (everything after "Analysis:" until the next section)
            const reasoningMatch = combinedAnalysis.match(/Analysis: ([\s\S]*?)(?=\*\*OVERALL|$)/);
            const reasoning = reasoningMatch ? reasoningMatch[1].trim() : 'Analysis completed';
            
            console.log('Fallback extraction:', { triageLevel, reasoning });
            return `**Triage: ${triageLevel}**\n**Reasoning:** ${reasoning}`;
        }
        
        // If all else fails, return the original text
        console.log('Using original analysis text');
        return combinedAnalysis;
    }

    parseTriageResponse(response) {
        console.log('Parsing triage response:', response);
        
        // Handle undefined or null response
        if (!response || typeof response !== 'string') {
            console.error('Invalid response type:', typeof response, response);
            return {
                level: 'Yellow',
                reasoning: 'Unable to parse analysis. Please review manually.',
                actions: ['Assess patient condition manually', 'Follow standard protocols'],
                patientInfo: {
                    age: 'Unknown',
                    gender: 'Unknown',
                    mechanism: 'Unknown',
                    assessment: 'Unable to parse assessment findings'
                }
            };
        }

        // Initialize structured data
        let level = 'Yellow'; // Default fallback
        let reasoning = 'Assessment completed based on visual analysis';
        let actions = ['Follow standard protocols'];
        let patientInfo = {
            age: 'Unknown',
            gender: 'Unknown',
            mechanism: 'Unknown',
            assessment: 'Unable to parse assessment findings'
        };

        // Extract triage level - enhanced pattern matching for new format
        const triagePatterns = [
            /\*\*TRIAGE LEVEL:\*\*\s*(RED|YELLOW|GREEN|BLACK)/i,
            /\*\*Triage:\s*(RED|YELLOW|GREEN|BLACK)\*\*/i,
            /Triage:\s*(RED|YELLOW|GREEN|BLACK)/i,
            /Triage Level:\s*(RED|YELLOW|GREEN|BLACK)/i,
            /Category:\s*(RED|YELLOW|GREEN|BLACK)/i,
            /Priority:\s*(RED|YELLOW|GREEN|BLACK)/i
        ];
        
        for (const pattern of triagePatterns) {
            const match = response.match(pattern);
            if (match) {
                level = match[1];
                break;
            }
        }
        
        // If no explicit triage level found, infer from content
        if (level === 'Yellow') {
            const text = response.toLowerCase();
            
            // Red indicators - enhanced for medical assessment language
            if (text.includes('red') || text.includes('immediate') || text.includes('critical') || 
                text.includes('life-threatening') || text.includes('severe trauma') || 
                text.includes('highest priority') || text.includes('emergency') ||
                text.includes('immediate life-threatening') || text.includes('airway') ||
                text.includes('breathing') || text.includes('circulation') ||
                text.includes('facial injuries') || text.includes('smoke inhalation') ||
                text.includes('burns') || text.includes('significant') ||
                text.includes('dangerous environment') || text.includes('fire')) {
                level = 'Red';
            }
            // Black indicators
            else if (text.includes('black') || text.includes('deceased') || text.includes('dead') ||
                     text.includes('incompatible with life') || text.includes('expectant')) {
                level = 'Black';
            }
            // Green indicators
            else if (text.includes('green') || text.includes('minor') || text.includes('stable') ||
                     text.includes('non-urgent') || text.includes('walking wounded')) {
                level = 'Green';
            }
            // Yellow indicators (default)
            else if (text.includes('yellow') || text.includes('urgent') || text.includes('serious') ||
                     text.includes('delayed') || text.includes('moderate')) {
                level = 'Yellow';
            }
        }

        // Extract reasoning - enhanced for new format and natural language
        const reasoningPatterns = [
            /\*\*REASONING:\*\*\s*([\s\S]*?)(?=\*\*PATIENT INFORMATION:\*\*|\*\*Action:\*\*|\*\*Actions:\*\*|\*\*Recommendations:\*\*|$)/i,
            /\*\*Reasoning:\*\*\s*([\s\S]*?)(?=\*\*Action:\*\*|\*\*Actions:\*\*|\*\*Recommendations:\*\*|$)/i,
            /Reasoning:\s*([\s\S]*?)(?=Action:|Actions:|Recommendations:|$)/i,
            /Assessment:\s*([\s\S]*?)(?=Action:|Actions:|Recommendations:|$)/i,
            /Analysis:\s*([\s\S]*?)(?=Action:|Actions:|Recommendations:|$)/i
        ];
        
        for (const pattern of reasoningPatterns) {
            const match = response.match(pattern);
            if (match) {
                reasoning = match[1].trim();
                break;
            }
        }
        
        // If no structured reasoning found, extract the first descriptive paragraph
        if (reasoning === 'Assessment completed based on visual analysis') {
            const paragraphs = response.split('\n\n').filter(p => p.trim() && p.length > 50);
            if (paragraphs.length > 0) {
                // Find the paragraph that describes the situation
                const descriptiveParagraphs = paragraphs.filter(p => 
                    p.toLowerCase().includes('video') || 
                    p.toLowerCase().includes('frames') || 
                    p.toLowerCase().includes('patient') ||
                    p.toLowerCase().includes('man') ||
                    p.toLowerCase().includes('woman') ||
                    p.toLowerCase().includes('person')
                );
                
                if (descriptiveParagraphs.length > 0) {
                    reasoning = descriptiveParagraphs[0].trim();
                } else {
                    reasoning = paragraphs[0].trim();
                }
            }
        }

        // Extract patient information - new structured format
        const patientInfoSection = response.match(/\*\*PATIENT INFORMATION:\*\*([\s\S]*?)(?=\*\*TRIAGE CATEGORY DETAILS:\*\*|\*\*IMMEDIATE ACTIONS:\*\*|$)/i);
        if (patientInfoSection) {
            const patientText = patientInfoSection[1];
            
            // Extract age
            const ageMatch = patientText.match(/\*\*Approximate Age:\*\*\s*([^\n]+)/i) || 
                           patientText.match(/Approximate Age:\s*([^\n]+)/i);
            if (ageMatch) {
                patientInfo.age = ageMatch[1].trim();
            }
            
            // Extract gender
            const genderMatch = patientText.match(/\*\*Gender:\*\*\s*([^\n]+)/i) || 
                              patientText.match(/Gender:\s*([^\n]+)/i);
            if (genderMatch) {
                patientInfo.gender = genderMatch[1].trim();
            }
            
            // Extract mechanism of injury
            const mechanismMatch = patientText.match(/\*\*Mechanism of Injury:\*\*\s*([^\n]+)/i) || 
                                 patientText.match(/Mechanism of Injury:\s*([^\n]+)/i);
            if (mechanismMatch) {
                patientInfo.mechanism = mechanismMatch[1].trim();
            }
            
            // Extract assessment findings
            const assessmentMatch = patientText.match(/\*\*Brief Assessment Findings:\*\*\s*([^\n]+)/i) || 
                                  patientText.match(/Brief Assessment Findings:\s*([^\n]+)/i);
            if (assessmentMatch) {
                patientInfo.assessment = assessmentMatch[1].trim();
            }
        }
        
        // If no structured patient info found, try to extract from general text
        if (patientInfo.age === 'Unknown') {
            const agePatterns = [
                /(\d+)\s*(?:years?\s*old|y\.?o\.?)/i,
                /age[:\s]*(\d+)/i,
                /(\d+)\s*(?:year|yr)/i
            ];
            for (const pattern of agePatterns) {
                const match = response.match(pattern);
                if (match) {
                    patientInfo.age = `${match[1]} years`;
                    break;
                }
            }
        }
        
        if (patientInfo.gender === 'Unknown') {
            const genderPatterns = [
                /(male|female|man|woman|boy|girl)/i
            ];
            for (const pattern of genderPatterns) {
                const match = response.match(pattern);
                if (match) {
                    patientInfo.gender = match[1].toLowerCase();
                    break;
                }
            }
        }
        
        // Extract mechanism of injury from natural language
        if (patientInfo.mechanism === 'Unknown') {
            const mechanismPatterns = [
                /(motor vehicle accident|car crash|car accident)/i,
                /(fall|fell|falling)/i,
                /(fire|burn|smoke)/i,
                /(trauma|injury|injured)/i,
                /(medical emergency|medical condition)/i
            ];
            for (const pattern of mechanismPatterns) {
                const match = response.match(pattern);
                if (match) {
                    patientInfo.mechanism = match[1].toLowerCase();
                    break;
                }
            }
        }
        
        // Extract assessment findings from natural language
        if (patientInfo.assessment === 'Unable to parse assessment findings') {
            const assessmentKeywords = [
                'facial injuries', 'bleeding', 'conscious', 'unconscious', 
                'breathing', 'airway', 'smoke inhalation', 'burns', 'fractures'
            ];
            
            const sentences = response.split(/[.!?]+/).filter(s => s.trim().length > 20);
            const assessmentSentences = sentences.filter(sentence => 
                assessmentKeywords.some(keyword => sentence.toLowerCase().includes(keyword))
            );
            
            if (assessmentSentences.length > 0) {
                patientInfo.assessment = assessmentSentences[0].trim();
            } else if (sentences.length > 0) {
                // Use the first descriptive sentence
                patientInfo.assessment = sentences[0].trim();
            }
        }

        // Extract actions - enhanced for new format
        const actionPatterns = [
            /\*\*IMMEDIATE ACTIONS:\*\*\s*([\s\S]*?)(?=\n\n|$)/i,
            /\*\*Action:\*\*\s*([\s\S]*?)(?=\n\n|$)/i,
            /\*\*Actions:\*\*\s*([\s\S]*?)(?=\n\n|$)/i,
            /\*\*Recommendations:\*\*\s*([\s\S]*?)(?=\n\n|$)/i,
            /Action:\s*([\s\S]*?)(?=\n\n|$)/i,
            /Actions:\s*([\s\S]*?)(?=\n\n|$)/i,
            /Recommendations:\s*([\s\S]*?)(?=\n\n|$)/i
        ];
        
        for (const pattern of actionPatterns) {
            const match = response.match(pattern);
            if (match) {
                const actionText = match[1];
                // Split by various list formats
                const listItems = actionText.split(/(?:\d+\.|\*|\-)\s*/).filter(item => item.trim());
                if (listItems.length > 0) {
                    actions = listItems.slice(0, 5); // Limit to 5 actions
                    break;
                }
            }
        }
        
        // If no actions section found, extract key points
        if (actions.length === 1 && actions[0] === 'Follow standard protocols') {
            // Look for numbered or bulleted lists
            const listPatterns = [
                /\d+\.\s*\*\*([^*]+)\*\*:?\s*([^*]+)/g,
                /\d+\.\s*([^*]+):\s*([^*]+)/g,
                /\*\s*\*\*([^*]+)\*\*:?\s*([^*]+)/g,
                /\*\s*([^*]+):\s*([^*]+)/g
            ];
            
            for (const pattern of listPatterns) {
                const matches = response.match(pattern);
                if (matches && matches.length > 0) {
                    actions = matches.slice(0, 5).map(item => 
                        item.replace(/(?:\d+\.|\*)\s*\*\*([^*]+)\*\*:?\s*/, '$1: ')
                           .replace(/(?:\d+\.|\*)\s*([^*]+):\s*/, '$1: ')
                    );
                    break;
                }
            }
            
            // If still no actions, extract sentences that look like recommendations
            if (actions.length === 1 && actions[0] === 'Follow standard protocols') {
                const sentences = response.split(/[.!?]+/).filter(s => s.trim().length > 20);
                const recommendationKeywords = ['assess', 'check', 'monitor', 'provide', 'ensure', 'prepare', 'administer', 'evaluate'];
                
                const recommendations = sentences.filter(sentence => 
                    recommendationKeywords.some(keyword => sentence.toLowerCase().includes(keyword))
                );
                
                if (recommendations.length > 0) {
                    actions = recommendations.slice(0, 4).map(s => s.trim());
                }
            }
            
            // Enhanced extraction for medical assessment format
            if (actions.length === 1 && actions[0] === 'Follow standard protocols') {
                // Look for medical assessment sections
                const medicalSections = response.split(/\*\*[^*]+\*\*/);
                for (const section of medicalSections) {
                    if (section.toLowerCase().includes('immediate') || 
                        section.toLowerCase().includes('medical') ||
                        section.toLowerCase().includes('needs')) {
                        
                        const lines = section.split('\n').filter(line => line.trim() && line.includes(':'));
                        if (lines.length > 0) {
                            actions = lines.slice(0, 5).map(line => line.trim());
                            break;
                        }
                    }
                }
            }
        }

        console.log('Parsed triage data:', { level, reasoning, actions, patientInfo });
        return { level, reasoning, actions, patientInfo };
    }

    createPatientFromTriage(triageLevel, reasoning) {
        console.log('createPatientFromTriage called with:', { triageLevel, reasoning });
        
        try {
        this.closeModal(document.getElementById('triage-modal'));
            console.log('Triage modal closed');
            
        this.openPatientModal();
            console.log('Patient modal opened');
        
        // Pre-fill form with triage data
        const triageField = document.getElementById('triage-level');
        const notesField = document.getElementById('patient-notes');
        
        console.log('Setting triage level:', triageLevel, 'Field found:', !!triageField);
        console.log('Setting notes:', reasoning, 'Field found:', !!notesField);
        
        if (triageField && triageLevel) {
            // Normalize to "Red", "Yellow", etc.
            const normalized = triageLevel.charAt(0).toUpperCase() + triageLevel.slice(1).toLowerCase();
            triageField.value = normalized;
            console.log('Triage level set to:', triageField.value);
        }
        
        if (notesField) {
            notesField.value = `Triage Assessment: ${reasoning}`;
            console.log('Notes set to:', notesField.value);
        }
        
        this.addSystemMessage('Patient form opened with triage data');
            console.log('createPatientFromTriage completed successfully');
        } catch (error) {
            console.error('Error in createPatientFromTriage:', error);
            this.addSystemMessage(`Error opening patient form: ${error.message}`);
            throw error;
        }
    }

    async handlePatientSubmit(event) {
        event.preventDefault();
        console.log('handlePatientSubmit called');
        
        const formData = {
            rfid: document.getElementById('patient-rfid').value,
            name: document.getElementById('patient-name').value || 'Unknown',
            age: document.getElementById('patient-age').value || null,
            triage_level: document.getElementById('triage-level').value,
            location: document.getElementById('patient-location').value || 'Triage Area',
            notes: document.getElementById('patient-notes').value || '',
            role: this.currentRole
        };

        console.log('Form data to submit:', formData);

        try {
            console.log('Sending request to /api/patients');
            const response = await fetch('/api/patients', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            console.log('Response received:', response.status, response.statusText);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                this.addSystemMessage(`Patient ${formData.name} added successfully`);
                this.closeModal(document.getElementById('patient-modal'));
                this.loadPatients();
            } else {
                this.addSystemMessage(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error adding patient:', error);
            this.addSystemMessage('Error: Failed to add patient');
        }
    }

    async loadPatients() {
        try {
            const response = await fetch('/api/patients');
            const data = await response.json();
            
            if (data.success) {
                this.displayPatients(data.patients);
            }
        } catch (error) {
            console.error('Error loading patients:', error);
        }
    }

    displayPatients(patients) {
        const container = document.getElementById('patients-list');
        
        if (patients.length === 0) {
            container.innerHTML = '<p class="no-patients">No patients recorded yet</p>';
            return;
        }

        // Sort patients by triage priority: Red > Yellow > Green > Black
        const triagePriority = { 'Red': 1, 'Yellow': 2, 'Green': 3, 'Black': 4 };
        const sortedPatients = patients.sort((a, b) => {
            const priorityA = triagePriority[a.triage_level] || 5;
            const priorityB = triagePriority[b.triage_level] || 5;
            return priorityA - priorityB;
        });

        // Show more patients for doctors, fewer for others
        const maxPatients = this.currentRole === 'DOCTOR' ? 10 : 5;
        const displayPatients = sortedPatients.slice(0, maxPatients);

        container.innerHTML = displayPatients.map(patient => `
            <div class="patient-card ${patient.triage_level.toLowerCase()}" 
                 ${this.currentRole === 'DOCTOR' ? `onclick="app.openSoapNotes('${patient.id}', '${patient.name || 'Unknown'}')" style="cursor: pointer;"` : `data-patient-id="${patient.id}" style="cursor: pointer;"`}>
                <div class="patient-header">
                    <h4>${patient.name || 'Unknown'}</h4>
                    <span class="triage-badge ${patient.triage_level.toLowerCase()}">${patient.triage_level}</span>
                </div>
                <div class="patient-details">
                    <p><strong>RFID:</strong> ${patient.rfid || 'N/A'}</p>
                    <p><strong>Location:</strong> ${patient.location || 'Unknown'}</p>
                    <p><strong>Added:</strong> ${new Date(patient.created_at).toLocaleString()}</p>
                    ${patient.age ? `<p><strong>Age:</strong> ${patient.age}</p>` : ''}
                </div>
                <div class="patient-actions">
                    ${this.currentRole === 'DOCTOR' ? `
                        <button class="btn-secondary" onclick="event.stopPropagation(); app.openSoapNotes('${patient.id}', '${patient.name || 'Unknown'}')">
                            <i class="fas fa-stethoscope"></i>
                            SOAP Notes
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');

        // Add "View All" button if there are more patients
        if (patients.length > maxPatients) {
            container.innerHTML += `
                <div class="view-all-patients">
                    <button class="btn-primary" onclick="app.showPatientsList()">
                        <i class="fas fa-list"></i>
                        View All ${patients.length} Patients
                    </button>
                </div>
            `;
        }
    }

    async openSoapNotes(patientId, patientName) {
        // Set patient ID in form
        document.getElementById('soap-patient-id').value = patientId;
        
        // Load existing SOAP notes
        await this.loadSoapNotes(patientId);
        
        // Update modal title
        document.querySelector('#soap-modal .modal-header h3').textContent = `SOAP Notes - ${patientName}`;
        
        // Show modal
        this.showModal(document.getElementById('soap-modal'));
        
        this.addSystemMessage(`Opening SOAP notes for ${patientName}`);
    }

    async loadSoapNotes(patientId) {
        try {
            const response = await fetch(`/api/soap-notes?patient_id=${patientId}`);
            const data = await response.json();
            
            if (data.success) {
                this.displaySoapNotes(data.soap_notes);
            } else {
                this.addSystemMessage(`Error loading SOAP notes: ${data.error}`);
            }
        } catch (error) {
            console.error('Error loading SOAP notes:', error);
            this.addSystemMessage('Error loading SOAP notes');
        }
    }

    displaySoapNotes(soapNotes) {
        const container = document.getElementById('soap-notes-list');
        
        if (soapNotes.length === 0) {
            container.innerHTML = '<p class="no-soap-notes">No SOAP notes yet</p>';
            return;
        }

        container.innerHTML = soapNotes.map(note => `
            <div class="soap-note">
                <div class="soap-note-header">
                    <h4>SOAP Note - ${new Date(note.created_at).toLocaleString()}</h4>
                    <span class="doctor-id">Dr. ${note.doctor_id}</span>
                </div>
                <div class="soap-note-content">
                    <div class="soap-section">
                        <strong>Subjective:</strong>
                        <p>${note.subjective || 'Not recorded'}</p>
                    </div>
                    <div class="soap-section">
                        <strong>Objective:</strong>
                        <p>${note.objective || 'Not recorded'}</p>
                    </div>
                    <div class="soap-section">
                        <strong>Assessment:</strong>
                        <p>${note.assessment || 'Not recorded'}</p>
                    </div>
                    <div class="soap-section">
                        <strong>Plan:</strong>
                        <p>${note.plan || 'Not recorded'}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async handleSoapSubmit(event) {
        event.preventDefault();
        
        const formData = {
            patient_id: document.getElementById('soap-patient-id').value,
            doctor_id: this.currentRole === 'DOCTOR' ? 'Dr. ' + this.getRoleDisplayName(this.currentRole) : 'Unknown',
            subjective: document.getElementById('soap-subjective').value,
            objective: document.getElementById('soap-objective').value,
            assessment: document.getElementById('soap-assessment').value,
            plan: document.getElementById('soap-plan').value
        };

        try {
            const response = await fetch('/api/soap-notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (data.success) {
                this.addSystemMessage('SOAP note saved successfully');
                document.getElementById('soap-form').reset();
                
                // Reload SOAP notes
                await this.loadSoapNotes(formData.patient_id);
            } else {
                this.addSystemMessage(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error saving SOAP note:', error);
            this.addSystemMessage('Error: Failed to save SOAP note');
        }
    }

    startVoiceInput(field = 'patient-notes') {
        // Stop any previous dictation
            this.stopVoiceInput();
        this.currentVoiceField = field;
        const input = document.getElementById(field);
        if (input) {
            input.classList.add('voice-active');
        }
        // Show stop button if in vitals modal
        const stopBtn = document.getElementById('vitals-stop-dictation-btn');
        if (stopBtn) stopBtn.style.display = 'inline-block';
        // Start recognition
        if (!('webkitSpeechRecognition' in window)) {
            alert('Speech recognition not supported in this browser.');
            return;
        }
        this.recognition = new webkitSpeechRecognition();
        this.recognition.lang = 'en-US';
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;
        this.recognition.onresult = (event) => {
            let transcript = event.results[0][0].transcript.trim();
            // If numeric field, extract number
            if (input && input.type === 'number') {
                const numMatch = transcript.match(/(-?\d+(?:\.\d+)?)/);
                if (numMatch) {
                    input.value = numMatch[1];
                } else {
                    input.value = '';
                    this.addSystemMessage('No number detected in dictation.');
                }
            } else {
                input.value = transcript;
            }
            input.classList.remove('voice-active');
            this.currentVoiceField = null;
            if (stopBtn) stopBtn.style.display = 'none';
        };
        this.recognition.onend = () => {
            if (input) input.classList.remove('voice-active');
            this.currentVoiceField = null;
            if (stopBtn) stopBtn.style.display = 'none';
        };
        this.recognition.start();
    }

    stopVoiceInput() {
        if (this.recognition) {
            this.recognition.stop();
            this.recognition = null;
        }
        if (this.currentVoiceField) {
            const input = document.getElementById(this.currentVoiceField);
            if (input) input.classList.remove('voice-active');
            this.currentVoiceField = null;
        }
        const stopBtn = document.getElementById('vitals-stop-dictation-btn');
        if (stopBtn) stopBtn.style.display = 'none';
    }

    showPatientsList() {
        this.loadAllPatients();
        this.showModal(document.getElementById('patients-list-modal'));
    }

    async loadAllPatients() {
        try {
            const response = await fetch('/api/patients');
            const data = await response.json();
            
            if (data.success) {
                this.displayAllPatients(data.patients);
            }
        } catch (error) {
            console.error('Error loading all patients:', error);
        }
    }

    displayAllPatients(patients) {
        const container = document.getElementById('all-patients-list');
        const countSpan = document.getElementById('patients-count');
        
        if (patients.length === 0) {
            container.innerHTML = '<p class="no-patients">No patients recorded yet</p>';
            countSpan.textContent = '0 patients';
            return;
        }

        // Sort patients by triage priority: Red > Yellow > Green > Black
        const triagePriority = { 'Red': 1, 'Yellow': 2, 'Green': 3, 'Black': 4 };
        const sortedPatients = patients.sort((a, b) => {
            const priorityA = triagePriority[a.triage_level] || 5;
            const priorityB = triagePriority[b.triage_level] || 5;
            return priorityA - priorityB;
        });

        countSpan.textContent = `${patients.length} patient${patients.length !== 1 ? 's' : ''}`;

        container.innerHTML = sortedPatients.map(patient => `
            <div class="patient-card ${patient.triage_level.toLowerCase()}" data-triage="${patient.triage_level}"
                 ${this.currentRole === 'DOCTOR' ? `onclick="app.openSoapNotes('${patient.id}', '${patient.name || 'Unknown'}')" style="cursor: pointer;"` : `data-patient-id="${patient.id}" style="cursor: pointer;"`}>
                <div class="patient-header">
                    <h4>${patient.name || 'Unknown'}</h4>
                    <span class="triage-badge ${patient.triage_level.toLowerCase()}">${patient.triage_level}</span>
                </div>
                <div class="patient-details">
                    <p><strong>RFID:</strong> ${patient.rfid || 'N/A'}</p>
                    <p><strong>Location:</strong> ${patient.location || 'Unknown'}</p>
                    <p><strong>Added:</strong> ${new Date(patient.created_at).toLocaleString()}</p>
                    ${patient.age ? `<p><strong>Age:</strong> ${patient.age}</p>` : ''}
                    ${patient.notes ? `<p><strong>Notes:</strong> ${patient.notes.substring(0, 100)}${patient.notes.length > 100 ? '...' : ''}</p>` : ''}
                </div>
                <div class="patient-actions">
                    ${this.currentRole === 'DOCTOR' ? `
                        <button class="btn-secondary" onclick="event.stopPropagation(); app.openSoapNotes('${patient.id}', '${patient.name || 'Unknown'}')">
                            <i class="fas fa-stethoscope"></i>
                            SOAP Notes
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');

        // Add filter functionality
        this.setupPatientFilter();
    }

    setupPatientFilter() {
        const filterSelect = document.getElementById('triage-filter');
        const patientCards = document.querySelectorAll('#all-patients-list .patient-card');
        
        filterSelect.addEventListener('change', (e) => {
            const selectedTriage = e.target.value;
            
            patientCards.forEach(card => {
                const cardTriage = card.dataset.triage;
                if (!selectedTriage || cardTriage === selectedTriage) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    toggleSystemMessages() {
        const systemMessages = document.getElementById('system-messages');
        systemMessages.classList.toggle('collapsed');
    }

    clearSystemMessages() {
        const content = document.getElementById('system-messages-content');
        content.innerHTML = '';
        this.updateSystemMessagesCount();
    }

    addSystemMessage(message) {
        const content = document.getElementById('system-messages-content');
        if (!content) {
            console.warn('System messages content element not found');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-info-circle"></i>
                <span>${message}</span>
            </div>
        `;
        content.appendChild(messageDiv);
        this.updateSystemMessagesCount();
        
        // Auto-collapse after 5 seconds if it's a welcome message
        if (message.includes('Welcome') || message.includes('System ready')) {
            setTimeout(() => {
                const systemMessages = document.getElementById('system-messages');
                if (systemMessages && !systemMessages.classList.contains('collapsed')) {
                    systemMessages.classList.add('collapsed');
                }
            }, 5000);
        }
    }

    updateSystemMessagesCount() {
        const content = document.getElementById('system-messages-content');
        const countSpan = document.getElementById('system-messages-count');
        
        if (!content || !countSpan) {
            return;
        }
        
        const count = content.children.length;
        countSpan.textContent = `${count} message${count !== 1 ? 's' : ''}`;
    }

    async updateStatusIndicators() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            const ollamaStatus = data.ollama_connected ? 'connected' : 'disconnected';
            const modelStatus = data.model_loaded ? 'connected' : 'disconnected';
            
            // Update all status indicators
            document.querySelectorAll('#ollama-status, #ollama-status-main').forEach(el => {
                el.className = `status-item ${ollamaStatus}`;
            });
            
            document.querySelectorAll('#model-status, #model-status-main').forEach(el => {
                el.className = `status-item ${modelStatus}`;
            });
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    checkOnlineStatus() {
        this.isOnline = navigator.onLine;
        this.updateOfflineIndicator();
    }

    handleOnline() {
        this.isOnline = true;
        this.updateOfflineIndicator();
        this.addSystemMessage('Connection restored');
    }

    handleOffline() {
        this.isOnline = false;
        this.updateOfflineIndicator();
        this.addSystemMessage('Working offline - some features may be limited');
    }

    updateOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (!this.isOnline) {
            indicator.classList.remove('hidden');
        } else {
            indicator.classList.add('hidden');
        }
    }

    openVoiceInputModal() {
        console.log('Opening voice input modal...');
        const modal = document.getElementById('voice-input-modal');
        if (modal) {
            console.log('Modal found, showing...');
            this.showModal(modal);
            // Reset the modal state
            document.querySelector('.voice-options').style.display = 'grid';
            document.getElementById('voice-recording-section').style.display = 'none';
            document.getElementById('transcription-text').textContent = '';
        } else {
            console.error('Voice input modal not found!');
            this.addSystemMessage('Error: Voice input modal not found');
        }
    }

    selectVoiceMethod(method) {
        console.log('Selecting voice input method:', method);
        
        // Store the selected method
        this.currentVoiceMethod = method;
        
        // Update the voice input button to show the selected method
        const voiceInputBtn = document.getElementById('voice-input-btn');
        const methodNames = {
            'webkit': 'Browser Speech',
            'gemma': 'Gemma 3n AI',
            'gemma-finetuned': 'Gemma Fine-tuned'
        };
        
        voiceInputBtn.innerHTML = `
            <i class="fas fa-microphone"></i>
            <span>${methodNames[method] || 'Voice Input'}</span>
            <i class="fas fa-chevron-down"></i>
        `;
        
        this.addSystemMessage(`Voice input method set to: ${methodNames[method]}`);
    }

    openVitalsModal(patientId) {
        const modal = document.getElementById('vitals-modal');
        document.getElementById('vitals-patient-id').value = patientId;
        // Set timestamp to now
        const now = new Date();
        document.getElementById('vitals-timestamp').value = now.toISOString().slice(0,16);
        // Clear form
        document.getElementById('vitals-form').reset();
        document.getElementById('vitals-patient-id').value = patientId;
        document.getElementById('vitals-timestamp').value = now.toISOString().slice(0,16);
        this.loadVitalsHistory(patientId);
        this.showModal(modal);
        this.addSystemMessage('Vitals entry form opened');
    }
    async loadVitalsHistory(patientId) {
        const historyList = document.getElementById('vitals-history-list');
        historyList.innerHTML = '<p>Loading...</p>';
        try {
            const response = await fetch(`/api/vitals?patient_id=${patientId}`);
            const data = await response.json();
            if (data.success && data.vitals.length > 0) {
                historyList.innerHTML = '<ul>' + data.vitals.map(v => `
                    <li>
                        <strong>${new Date(v.timestamp).toLocaleString()}</strong>: 
                        HR: ${v.heart_rate}, BP: ${v.bp_sys}/${v.bp_dia}, RR: ${v.resp_rate}, O₂: ${v.o2_sat}%, Temp: ${v.temperature}°F, Pain: ${v.pain_score}
                    </li>
                `).join('') + '</ul>';
            } else {
                historyList.innerHTML = '<p>No vitals recorded yet.</p>';
            }
        } catch (error) {
            historyList.innerHTML = '<p>Error loading vitals history.</p>';
        }
    }
    async handleVitalsSubmit(event) {
        event.preventDefault();
        const formData = {
            patient_id: document.getElementById('vitals-patient-id').value,
            heart_rate: document.getElementById('vitals-heart-rate').value,
            bp_sys: document.getElementById('vitals-bp-sys').value,
            bp_dia: document.getElementById('vitals-bp-dia').value,
            resp_rate: document.getElementById('vitals-resp-rate').value,
            o2_sat: document.getElementById('vitals-o2-sat').value,
            temperature: document.getElementById('vitals-temperature').value,
            timestamp: new Date(document.getElementById('vitals-timestamp').value).toISOString(),
            created_by: this.currentRole
        };
        const painScoreValue = document.getElementById('vitals-pain-score').value;
        if (painScoreValue) {
            formData.pain_score = painScoreValue;
        }
        try {
            const response = await fetch('/api/vitals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await response.json();
            if (data.success) {
                this.addSystemMessage('Vitals saved successfully');
                this.loadVitalsHistory(formData.patient_id);
                document.getElementById('vitals-form').reset();
            } else {
                this.addSystemMessage('Error saving vitals: ' + data.error);
            }
        } catch (error) {
            this.addSystemMessage('Error saving vitals');
        }
    }

    async handleMissingPersonSubmit(event) {
        event.preventDefault();
        
        console.log('🔍 Missing person form submitted');
        
        const form = event.target;
        const photoInput = document.getElementById('missing-person-photo-input');
        const file = photoInput.files[0];
        
        // Validate that a photo is provided (this is the main requirement)
        if (!file) {
            this.addSystemMessage('Please upload a photo of the missing person. The photo is required for AI-powered matching.');
            return;
        }
        
        // Show progress indicator and disable form
        const progressIndicator = document.getElementById('missing-person-progress');
        const progressText = document.getElementById('progress-text');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        progressIndicator.style.display = 'block';
        form.classList.add('form-processing');
        submitBtn.disabled = true;
        
        // Helper function to update progress
        const updateProgress = (step, text) => {
            // Update progress text
            progressText.textContent = text;
            
            // Update step indicators
            const steps = progressIndicator.querySelectorAll('.progress-step');
            steps.forEach((stepEl, index) => {
                stepEl.classList.remove('active', 'completed');
                if (index < step) {
                    stepEl.classList.add('completed');
                } else if (index === step) {
                    stepEl.classList.add('active');
                }
            });
        };
        
        try {
            // Step 1: Uploading image
            updateProgress(0, 'Uploading image...');
            console.log('📸 Photo included in submission:', file.name);
            
            // Create FormData for multipart upload
            const formData = new FormData();
            
            // Add optional fields only if they have values
            const name = form.querySelector('#missing-person-name').value.trim();
            const age = form.querySelector('#missing-person-age').value.trim();
            const description = form.querySelector('#missing-person-description').value.trim();
            const contactInfo = form.querySelector('#missing-person-contact').value.trim();
            
            if (name) formData.append('name', name);
            if (age) formData.append('age', age);
            if (description) formData.append('description', description);
            if (contactInfo) formData.append('contact_info', contactInfo);
            
            formData.append('reported_by', this.currentRole || 'REUNIFICATION_COORDINATOR');
            formData.append('photo', file);
            
            console.log('📋 Form data entries:');
            for (let [key, value] of formData.entries()) {
                if (key === 'photo') {
                    console.log(`  ${key}: [File] ${value.name} (${value.size} bytes)`);
                } else {
                    console.log(`  ${key}: ${value}`);
                }
            }
            
            // Step 2: Extracting characteristics from image
            updateProgress(1, 'Extracting characteristics from image...');
            // Small delay to show the step
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Step 3: Saving to database
            updateProgress(2, 'Saving to database...');
            
            const response = await fetch('/api/missing-persons', {
                method: 'POST',
                body: formData // Send as FormData, not JSON
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Step 4: Indexing for search
            updateProgress(3, 'Indexing for search...');
            // Small delay to show the indexing step
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (data.success) {
                // Show completion
                progressText.textContent = 'Report submitted successfully!';
                progressText.style.color = '#4caf50';
                
                this.addSystemMessage('Missing person report submitted successfully. AI characteristics extracted for future matching.');
                
                // Reset form after a short delay
                setTimeout(() => {
                    this.closeModal(document.getElementById('missing-person-modal'));
                    form.reset();
                    
                    // Reset photo preview
                    const photoPreview = document.getElementById('photo-preview');
                    const photoUploadArea = document.getElementById('photo-upload-area');
                    if (photoPreview && photoUploadArea) {
                        photoPreview.style.display = 'none';
                        photoUploadArea.style.display = 'block';
                    }
                    
                    // Hide progress indicator
                    progressIndicator.style.display = 'none';
                    form.classList.remove('form-processing');
                    submitBtn.disabled = false;
                    progressText.style.color = '';
                }, 1500);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error submitting missing person report:', error);
            
            // Show error in progress
            progressText.textContent = `Error: ${error.message}`;
            progressText.style.color = '#f44336';
            
            this.addSystemMessage(`Error: ${error.message}`);
            
            // Reset form after error
            setTimeout(() => {
                progressIndicator.style.display = 'none';
                form.classList.remove('form-processing');
                submitBtn.disabled = false;
                progressText.style.color = '';
            }, 3000);
        }
    }

    async handleFindMatchSubmit(event) {
        event.preventDefault();
        
        const photoInput = document.getElementById('search-photo-input');
        const file = photoInput.files[0];
        
        if (!file) {
            this.addSystemMessage('Please select a photo to search');
            return;
        }
        
        // Show progress indicator and disable form
        const progressIndicator = document.getElementById('find-match-progress');
        const progressText = document.getElementById('find-match-progress-text');
        const submitBtn = document.getElementById('search-match-btn');
        
        progressIndicator.style.display = 'block';
        submitBtn.disabled = true;
        
        // Helper function to update progress
        const updateProgress = (step, text) => {
            // Update progress text
            progressText.textContent = text;
            
            // Update step indicators
            const steps = progressIndicator.querySelectorAll('.progress-step');
            steps.forEach((stepEl, index) => {
                stepEl.classList.remove('active', 'completed');
                if (index < step) {
                    stepEl.classList.add('completed');
                } else if (index === step) {
                    stepEl.classList.add('active');
                }
            });
        };
        
        try {
            // Step 1: Uploading search image
            updateProgress(0, 'Uploading search image...');
            
            // Step 2: Analyzing image characteristics
            updateProgress(1, 'Analyzing image characteristics...');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Step 3: Searching database
            updateProgress(2, 'Searching database...');
            
            this.addSystemMessage('Searching for matches...');
            
            const formData = new FormData();
            formData.append('photo', file);
            
            const response = await fetch('/api/missing-persons/match', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Step 4: Finding potential matches
            updateProgress(3, 'Finding potential matches...');
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (data.success) {
                // Show completion
                progressText.textContent = `Found ${data.matches.length} potential matches!`;
                progressText.style.color = '#4caf50';
                
                this.displayMatchResults(data.matches);
                this.addSystemMessage(`Found ${data.matches.length} potential matches`);
                
                // Hide progress indicator after a delay
                setTimeout(() => {
                    progressIndicator.style.display = 'none';
                    submitBtn.disabled = false;
                    progressText.style.color = '';
                }, 2000);
            } else {
                throw new Error(data.error || 'Search failed');
            }
        } catch (error) {
            console.error('Error finding matches:', error);
            
            // Show error in progress
            progressText.textContent = `Error: ${error.message}`;
            progressText.style.color = '#f44336';
            
            this.addSystemMessage(`Error: ${error.message}`);
            
            // Reset form after error
            setTimeout(() => {
                progressIndicator.style.display = 'none';
                submitBtn.disabled = false;
                progressText.style.color = '';
            }, 3000);
        }
    }

    displayMatchResults(matches) {
        const matchResults = document.getElementById('match-results');
        const matchList = document.getElementById('match-list');
        
        if (matches.length === 0) {
            matchList.innerHTML = '<p>No potential matches found.</p>';
        } else {
            matchList.innerHTML = matches.map(match => `
                <div class="match-item">
                    <div class="match-photo">
                        <img src="${match.image_url ? `/uploads/${match.image_url.split('/').pop()}` : '/static/images/icon-128x128.png'}" alt="Match photo">
                    </div>
                    <div class="match-info">
                        <h5>${match.name}</h5>
                        <p><strong>Age:</strong> ${match.age || 'Unknown'}</p>
                        <p><strong>Description:</strong> ${match.description}</p>
                        <p><strong>Similarity:</strong> ${Math.round(match.similarity_score * 100)}%</p>
                        <p><strong>Status:</strong> ${match.status}</p>
                    </div>
                </div>
            `).join('');
        }
        
        matchResults.style.display = 'block';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RapidCareApp();
    
    // Check if user is already logged in
    const savedRole = localStorage.getItem('rapidcare_role');
    if (savedRole) {
        window.app.currentRole = savedRole;
        document.getElementById('welcome-text').textContent = `Welcome, ${window.app.getRoleDisplayName(savedRole)}`;
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('main-app').classList.remove('hidden');
        window.app.addSystemMessage(`Welcome back, ${window.app.getRoleDisplayName(savedRole)}`);
    }
}); 