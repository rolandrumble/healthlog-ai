// HealthLog AI - Dashboard Application
// Completely rewritten with proper modal handling

const API_URL = window.location.origin;
let currentUser = JSON.parse(localStorage.getItem('healthlog_user') || 'null');
const userId = currentUser?.user_id || 'demo-user';

console.log('Dashboard.js loading...');
console.log('API URL:', API_URL);
console.log('Current User:', currentUser);

// ============================================
// MODAL FUNCTIONS - CRITICAL FOR UI
// ============================================

// Show Meal Log Modal
window.showMealLogModal = function() {
    console.log('showMealLogModal called');
    const modal = document.getElementById('meal-log-modal');
    if (modal) {
        modal.classList.add('active');
        console.log('Modal opened successfully');
        
        // Reset form
        const form = document.getElementById('meal-form');
        if (form) form.reset();
        
        // Reset upload area
        const uploadArea = document.getElementById('meal-upload-area');
        const mealPreview = document.getElementById('meal-preview');
        const mealPhoto = document.getElementById('meal-photo');
        const nutritionResults = document.getElementById('nutrition-results');
        
        if (uploadArea) uploadArea.style.display = 'block';
        if (mealPreview) mealPreview.style.display = 'none';
        if (mealPhoto) mealPhoto.value = '';
        if (nutritionResults) nutritionResults.style.display = 'none';
        
        // Setup upload handlers
        setTimeout(() => setupMealUpload(), 100);
    } else {
        console.error('meal-log-modal element not found');
    }
};

// Show Symptom Log Modal
window.showSymptomLogModal = function() {
    console.log('showSymptomLogModal called');
    const modal = document.getElementById('symptom-log-modal');
    if (modal) {
        modal.classList.add('active');
        console.log('Symptom modal opened');
        const form = document.getElementById('symptom-form');
        if (form) form.reset();
    } else {
        console.error('symptom-log-modal not found');
    }
};

// Show Medication Modal
window.showMedicationModal = function() {
    console.log('showMedicationModal called');
    const modal = document.getElementById('med-modal');
    if (modal) {
        modal.classList.add('active');
        console.log('Medication modal opened');
        const form = document.getElementById('med-form');
        if (form) form.reset();
    } else {
        console.error('med-modal not found');
    }
};

// Close Modal
window.closeModal = function(modalId) {
    console.log('Closing modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        console.log('Modal closed');
    }
};

// Handle Modal Backdrop Click
window.handleModalBackdropClick = function(event, modalId) {
    if (event.target.id === modalId) {
        closeModal(modalId);
    }
};

// ============================================
// FORM SUBMISSION HANDLERS
// ============================================

// Handle Meal Form Submission
window.handleMealSubmit = async function(event) {
    event.preventDefault();
    console.log('Meal form submitted');
    
    const mealName = document.getElementById('meal-name').value;
    const mealType = document.getElementById('meal-type').value;
    const mealDescription = document.getElementById('meal-description').value;
    const mealPhoto = document.getElementById('meal-photo').files[0];
    
    if (!mealName) {
        alert('Please enter a meal name');
        return;
    }
    
    if (!mealPhoto) {
        alert('Please upload a meal photo');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('meal_name', mealName);
        formData.append('meal_type', mealType);
        formData.append('description', mealDescription);
        formData.append('photo', mealPhoto);
        
        const response = await fetch(`${API_URL}/api/meals`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentUser?.token || ''}`
            },
            body: formData
        });
        
        if (response.ok) {
            alert('✅ Meal logged successfully!');
            closeModal('meal-log-modal');
            loadDashboardData();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.detail || 'Failed to log meal'));
        }
    } catch (error) {
        console.error('Meal submission error:', error);
        alert('Error logging meal: ' + error.message);
    }
};

// Handle Symptom Form Submission
window.handleSymptomSubmit = async function(event) {
    event.preventDefault();
    console.log('Symptom form submitted');
    
    const symptomName = document.getElementById('symptom-name').value;
    const symptomSeverity = document.getElementById('symptom-severity').value;
    const symptomNotes = document.getElementById('symptom-notes').value;
    
    if (!symptomName) {
        alert('Please enter a symptom name');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/symptoms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser?.token || ''}`
            },
            body: JSON.stringify({
                symptom_name: symptomName,
                severity: parseInt(symptomSeverity),
                notes: symptomNotes
            })
        });
        
        if (response.ok) {
            alert('✅ Symptom logged successfully!');
            closeModal('symptom-log-modal');
            loadDashboardData();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.detail || 'Failed to log symptom'));
        }
    } catch (error) {
        console.error('Symptom submission error:', error);
        alert('Error logging symptom: ' + error.message);
    }
};

// Handle Medication Form Submission
window.handleMedSubmit = async function(event) {
    event.preventDefault();
    console.log('Medication form submitted');
    
    const medName = document.getElementById('med-name').value;
    const medDosage = document.getElementById('med-dosage').value;
    const medFrequency = document.getElementById('med-frequency').value;
    
    if (!medName || !medDosage) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/medications`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser?.token || ''}`
            },
            body: JSON.stringify({
                med_name: medName,
                dosage: medDosage,
                frequency: medFrequency
            })
        });
        
        if (response.ok) {
            alert('✅ Medication added successfully!');
            closeModal('med-modal');
            loadDashboardData();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.detail || 'Failed to add medication'));
        }
    } catch (error) {
        console.error('Medication submission error:', error);
        alert('Error adding medication: ' + error.message);
    }
};

// ============================================
// UPLOAD HANDLERS
// ============================================

window.setupMealUpload = function() {
    const uploadArea = document.getElementById('meal-upload-area');
    const mealPhoto = document.getElementById('meal-photo');
    
    if (!uploadArea || !mealPhoto) return;
    
    // Click to upload
    uploadArea.addEventListener('click', () => mealPhoto.click());
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#00ff00';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#00d4ff';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#00d4ff';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            mealPhoto.files = files;
            handlePhotoUpload();
        }
    });
    
    // File input change
    mealPhoto.addEventListener('change', handlePhotoUpload);
};

window.handlePhotoUpload = function() {
    const mealPhoto = document.getElementById('meal-photo');
    const mealPreview = document.getElementById('meal-preview');
    const uploadArea = document.getElementById('meal-upload-area');
    
    if (mealPhoto.files.length > 0) {
        const file = mealPhoto.files[0];
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.maxWidth = '100%';
            img.style.borderRadius = '8px';
            
            if (mealPreview) {
                mealPreview.innerHTML = '';
                mealPreview.appendChild(img);
                mealPreview.style.display = 'block';
            }
            
            if (uploadArea) {
                uploadArea.style.display = 'none';
            }
        };
        
        reader.readAsDataURL(file);
    }
};

// ============================================
// INITIALIZATION
// ============================================

window.initDashboard = function() {
    console.log('Initializing dashboard...');
    
    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
    const greetingEl = document.getElementById('greeting');
    if (greetingEl) {
        greetingEl.textContent = `${greeting}! Here's your health summary.`;
    }
    
    if (currentUser) {
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) {
            userNameEl.textContent = currentUser.name || 'User';
        }
    }
};

window.loadDashboardData = function() {
    console.log('Loading dashboard data...');
    // Load meals, symptoms, medications, etc.
};

window.handleLogout = function() {
    localStorage.removeItem('healthlog_user');
    window.location.href = '/';
};

// ============================================
// PAGE LOAD
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    initDashboard();
    loadDashboardData();
});

console.log('Dashboard.js loaded successfully');
console.log('showMealLogModal function available:', typeof window.showMealLogModal);
