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
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkOnlineStatus();
        this.updateStatusIndicators();
        this.loadPatients();
        
        // Start status polling
        setInterval(() => this.updateStatusIndicators(), 30000);
    }

    setupEventListeners() {
        // Login system
        document.querySelectorAll('.role-card').forEach(card => {
            card.addEventListener('click', (e) => this.handleRoleSelection(e));
        });

        document.getElementById('logout-btn').addEventListener('click', () => this.logout());

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
            this.startVoiceInput();
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

        // Online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
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
                        <i class="fas fa-list"></i>
                    </div>
                    <h3>View Patients</h3>
                    <p>View and manage all patient records</p>
                    <button class="action-btn">
                        <i class="fas fa-eye"></i>
                        View All
                    </button>
                </div>
            `;
        } else {
            // Show standard actions for other roles
            actionGrid.innerHTML = `
                <div class="action-card" data-action="video-analysis">
                    <div class="action-icon">
                        <i class="fas fa-video"></i>
                    </div>
                    <h3>Video Analysis</h3>
                    <p>Analyze video footage for patient assessment and triage</p>
                    <button class="action-btn">
                        <i class="fas fa-play"></i>
                        Start Analysis
                    </button>
                </div>

                <div class="action-card" data-action="image-analysis">
                    <div class="action-icon">
                        <i class="fas fa-camera"></i>
                    </div>
                    <h3>Image Analysis</h3>
                    <p>Analyze photos for patient condition assessment</p>
                    <button class="action-btn">
                        <i class="fas fa-upload"></i>
                        Upload Image
                    </button>
                </div>

                <div class="action-card" data-action="voice-input">
                    <div class="action-icon">
                        <i class="fas fa-microphone"></i>
                    </div>
                    <h3>Voice Input</h3>
                    <p>Record voice notes for patient assessment</p>
                    <button class="action-btn">
                        <i class="fas fa-record-vinyl"></i>
                        Start Recording
                    </button>
                </div>

                <div class="action-card" data-action="create-patient">
                    <div class="action-icon">
                        <i class="fas fa-user-plus"></i>
                    </div>
                    <h3>Create Patient</h3>
                    <p>Manually create a new patient record</p>
                    <button class="action-btn">
                        <i class="fas fa-plus"></i>
                        Add Patient
                    </button>
                </div>

                <div class="action-card" data-action="view-patients">
                    <div class="action-icon">
                        <i class="fas fa-list"></i>
                    </div>
                    <h3>View Patients</h3>
                    <p>View and manage all patient records</p>
                    <button class="action-btn">
                        <i class="fas fa-eye"></i>
                        View All
                    </button>
                </div>
            `;
        }

        // Re-attach event listeners to new action cards
        document.querySelectorAll('.action-card').forEach(card => {
            const action = card.dataset.action;
            const btn = card.querySelector('.action-btn');
            btn.addEventListener('click', (e) => this.handleActionClick(action, e));
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

        switch (action) {
            case 'video-analysis':
                this.openMediaModal('Video Analysis', 'video');
                break;
            case 'image-analysis':
                this.openMediaModal('Image Analysis', 'image');
                break;
            case 'voice-input':
                this.startVoiceInput();
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
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: true, 
                audio: false 
            });
            
            const video = document.getElementById('camera-preview');
            video.srcObject = this.stream;
            
            this.addSystemMessage('Camera started. Ready to capture or record.');
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.addSystemMessage('Error: Could not access camera. Please check permissions.');
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

        this.recordedChunks = [];
        this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: 'video/webm' });

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = () => {
            const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
            this.analyzeVideo(blob);
        };

        this.mediaRecorder.start();
        this.isRecording = true;

        document.getElementById('record-btn').style.display = 'none';
        document.getElementById('stop-record-btn').style.display = 'inline-block';

        this.addSystemMessage('Recording started...');
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;

            document.getElementById('record-btn').style.display = 'inline-block';
            document.getElementById('stop-record-btn').style.display = 'none';

            this.addSystemMessage('Recording stopped. Analyzing video...');
        }
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
            fileItem.innerHTML = `
                <i class="fas fa-file"></i>
                <span>${file.name}</span>
                <button class="analyze-file-btn" data-file="${file.name}">Analyze</button>
            `;
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

        // Check if analysis exists and has description
        if (!analysis || !analysis.description) {
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
        const individualAnalysis = this.extractIndividualAnalysis(analysis.description);
        
        // Parse triage data
        const triageData = this.parseTriageResponse(individualAnalysis);
        
        // Create image preview if available
        const imagePreview = analysis.image_url ? `
            <div class="image-preview">
                <h5>Patient Image:</h5>
                <div class="image-container">
                    <img src="${analysis.image_url}" alt="Patient Image" class="patient-image" />
                </div>
            </div>
        ` : '';
        
        body.innerHTML = `
            <div class="triage-result">
                <div class="triage-header ${triageData.level.toLowerCase()}">
                    <h4>Triage Level: ${triageData.level}</h4>
                    <div class="confidence">Confidence: ${Math.round(analysis.confidence * 100)}%</div>
                </div>
                
                ${imagePreview}
                
                <div class="triage-reasoning">
                    <h5>Assessment:</h5>
                    <p>${triageData.reasoning}</p>
                </div>
                
                <div class="triage-actions">
                    <h5>Recommended Actions:</h5>
                    <ul>
                        ${triageData.actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="triage-buttons">
                    <button class="btn-primary" onclick="app.createPatientFromTriage('${triageData.level}', '${triageData.reasoning.replace(/'/g, "\\'")}')">
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
                actions: ['Assess patient condition manually', 'Follow standard protocols']
            };
        }

        // Extract triage level
        const triageMatch = response.match(/\*\*Triage:\s*(RED|YELLOW|GREEN|BLACK)\*\*/i);
        const level = triageMatch ? triageMatch[1] : 'Yellow';

        // Extract reasoning
        const reasoningMatch = response.match(/\*\*Reasoning:\*\*\s*([^*]+?)(?=\*\*Action:\*\*)/s);
        const reasoning = reasoningMatch ? reasoningMatch[1].trim() : 'Assessment completed based on visual analysis';

        // Extract actions
        const actionMatch = response.match(/\*\*Action:\*\*\s*([\s\S]*?)(?=\n\n|$)/);
        let actions = ['Follow standard protocols'];
        
        if (actionMatch) {
            const actionText = actionMatch[1];
            // Split by numbered items
            actions = actionText.split(/\d+\.\s*/).filter(item => item.trim()).map(item => item.trim());
        }

        console.log('Parsed triage data:', { level, reasoning, actions });
        return { level, reasoning, actions };
    }

    createPatientFromTriage(triageLevel, reasoning) {
        this.closeModal(document.getElementById('triage-modal'));
        this.openPatientModal();
        
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
    }

    async handlePatientSubmit(event) {
        event.preventDefault();
        
        const formData = {
            rfid: document.getElementById('patient-rfid').value,
            name: document.getElementById('patient-name').value || 'Unknown',
            age: document.getElementById('patient-age').value || null,
            triage_level: document.getElementById('triage-level').value,
            location: document.getElementById('patient-location').value || 'Triage Area',
            notes: document.getElementById('patient-notes').value || '',
            role: this.currentRole
        };

        try {
            const response = await fetch('/api/patients', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
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

        container.innerHTML = sortedPatients.slice(0, 5).map(patient => `
            <div class="patient-card ${patient.triage_level.toLowerCase()}">
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
                        <button class="btn-secondary" onclick="app.openSoapNotes('${patient.id}', '${patient.name || 'Unknown'}')">
                            <i class="fas fa-stethoscope"></i>
                            SOAP Notes
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
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
        if (!('webkitSpeechRecognition' in window)) {
            this.addSystemMessage('Error: Speech recognition not supported');
            return;
        }

        if (this.isRecording) {
            this.stopVoiceInput();
            return;
        }

        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        let finalTranscript = '';
        const textarea = document.getElementById(field);
        const voiceBtn = document.getElementById(field === 'patient-notes' ? 'notes-voice-btn' : `${field}-voice-btn`);

        this.recognition.onstart = () => {
            this.isRecording = true;
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            this.addSystemMessage('Voice recording started. Speak now...');
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            // Update textarea with current transcription
            const currentText = textarea.value;
            textarea.value = currentText + finalTranscript + interimTranscript;
            textarea.focus();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.addSystemMessage(`Voice recognition error: ${event.error}`);
            this.stopVoiceInput();
        };

        this.recognition.onend = () => {
            this.stopVoiceInput();
            this.addSystemMessage('Voice recording completed');
        };

        this.recognition.start();
    }

    stopVoiceInput() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.isRecording = false;
        
        // Reset all voice buttons
        const voiceButtons = [
            'notes-voice-btn',
            'soap-subjective-voice-btn',
            'soap-objective-voice-btn',
            'soap-assessment-voice-btn',
            'soap-plan-voice-btn'
        ];
        
        voiceButtons.forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) {
                btn.classList.remove('recording');
                btn.innerHTML = '<i class="fas fa-microphone"></i>';
            }
        });
    }

    showPatientsList() {
        this.loadPatients();
    }

    addSystemMessage(message) {
        const container = document.getElementById('system-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-info-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        container.appendChild(messageDiv);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
        
        // Auto-remove old messages (keep last 10)
        const messages = container.querySelectorAll('.message');
        if (messages.length > 10) {
            messages[0].remove();
        }
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