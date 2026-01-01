// HealthLog AI - Dashboard Application
// Fixed version with proper API URL configuration

// Get API URL from environment or use current domain
const API_URL = window.location.origin;
let currentUser = JSON.parse(localStorage.getItem('healthlog_user') || 'null');
const userId = currentUser?.user_id || 'demo-user';

// Debug: Log user info on load
console.log('HealthLog AI Dashboard Loaded');
console.log('API URL:', API_URL);
console.log('Current User:', currentUser);
console.log('User ID:', userId);

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    initNavigation();
    initSliders();
    initForms();
    loadDashboardData();
});

function initDashboard() {
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
}

function initNavigation() {
    document.querySelectorAll('.nav-item[data-section]').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            const section = item.dataset.section;
            
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            
            document.querySelectorAll('.dashboard-section').forEach(s => s.classList.remove('active'));
            const targetSection = document.getElementById(`${section}-section`);
            if (targetSection) {
                targetSection.classList.add('active');
            }
            
            const pageTitle = document.getElementById('page-title');
            if (pageTitle) {
                pageTitle.textContent = section.charAt(0).toUpperCase() + section.slice(1);
            }
        });
    });
}

function initSliders() {
    ['energy', 'mood'].forEach(id => {
        const slider = document.getElementById(`${id}-slider`);
        const display = document.getElementById(`${id}-value`);
        if (slider && display) {
            slider.addEventListener('input', () => {
                display.textContent = slider.value;
            });
        }
    });
    
    const sevSlider = document.getElementById('symptom-severity');
    const sevDisplay = document.getElementById('severity-display');
    if (sevSlider && sevDisplay) {
        sevSlider.addEventListener('input', () => {
            sevDisplay.textContent = sevSlider.value;
        });
    }
}

function initForms() {
    // Daily check-in form
    const checkinForm = document.getElementById('daily-checkin-form');
    if (checkinForm) {
        checkinForm.addEventListener('submit', async e => {
            e.preventDefault();
            
            const data = {
                energy_level: parseInt(document.getElementById('energy-slider').value),
                mood_level: parseInt(document.getElementById('mood-slider').value),
                sleep_hours: parseFloat(document.getElementById('sleep-input').value) || null,
                water_intake: parseInt(document.getElementById('water-input').value) || null
            };
            
            try {
                const res = await fetch(`${API_URL}/api/daily-score?user_id=${userId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (res.ok) {
                    alert('✅ Daily check-in saved!');
                } else {
                    const err = await res.json();
                    alert('Error: ' + (err.detail || 'Could not save'));
                }
            } catch (e) {
                console.error('Check-in error:', e);
                alert('Error saving check-in');
            }
        });
    }

    // Meal upload area - setup event listeners
    setupMealUpload();
}

async function loadDashboardData() {
    try {
        const res = await fetch(`${API_URL}/api/insights/${userId}`);
        if (res.ok) {
            const insights = await res.json();
            
            const caloriesEl = document.getElementById('today-calories');
            if (caloriesEl) caloriesEl.textContent = insights.avg_daily_calories || 0;
            
            const mealsEl = document.getElementById('meals-logged');
            if (mealsEl) mealsEl.textContent = insights.meals_logged || 0;
            
            const energyEl = document.getElementById('avg-energy');
            if (energyEl) energyEl.textContent = insights.avg_energy ? `${insights.avg_energy}/10` : '-';
            
            const adherenceEl = document.getElementById('med-adherence');
            if (adherenceEl) adherenceEl.textContent = '-';
        }
    } catch (e) {
        console.error('Error loading dashboard data:', e);
    }
}

function setupMealUpload() {
    const mealPhoto = document.getElementById('meal-photo');
    const mealPreview = document.getElementById('meal-preview');
    const uploadArea = document.getElementById('meal-upload-area');
    
    if (!mealPhoto || !mealPreview || !uploadArea) {
        console.warn('Meal upload elements not found');
        return;
    }
    
    // Check if already set up to avoid duplicate listeners
    if (mealPhoto.dataset.listenersAttached === 'true') {
        console.log('Upload listeners already attached');
        return;
    }
    
    // Mark as set up
    mealPhoto.dataset.listenersAttached = 'true';
    
    // Add change listener to file input
    mealPhoto.addEventListener('change', (e) => {
        const file = e.target.files[0];
        console.log('File selected:', file?.name, file?.type, file?.size);
        
        if (!file) {
            console.warn('No file selected');
            return;
        }
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            mealPhoto.value = '';
            return;
        }
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('File size too large. Please select an image under 10MB');
            mealPhoto.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (ev) => {
            mealPreview.src = ev.target.result;
            mealPreview.style.display = 'block';
            uploadArea.style.display = 'none';
            console.log('Image preview loaded');
        };
        reader.onerror = () => {
            console.error('Error reading file');
            alert('Error reading file. Please try another image.');
            mealPhoto.value = '';
        };
        reader.readAsDataURL(file);
    });
    
    console.log('Meal upload handlers set up successfully');
}

function showMealLogModal() {
    console.log('Opening Meal Log modal');
    const modal = document.getElementById('meal-log-modal');
    if (modal) {
        modal.classList.add('active');
        
        // Reset the form
        const uploadArea = document.getElementById('meal-upload-area');
        const mealPreview = document.getElementById('meal-preview');
        const mealPhoto = document.getElementById('meal-photo');
        const nutritionResults = document.getElementById('nutrition-results');
        const submitBtn = document.getElementById('meal-submit-btn');
        
        if (uploadArea) uploadArea.style.display = 'block';
        if (mealPreview) mealPreview.style.display = 'none';
        if (mealPhoto) mealPhoto.value = '';
        if (nutritionResults) nutritionResults.style.display = 'none';
        if (submitBtn) submitBtn.style.display = 'block';
        
        // Reset form
        const form = document.getElementById('meal-form');
        if (form) form.reset();
        
        // Clear the listeners flag so we can re-attach if needed
        if (mealPhoto) mealPhoto.dataset.listenersAttached = 'false';
        
        // Setup upload handlers after modal is shown
        setTimeout(() => {
            setupMealUpload();
        }, 100);
    } else {
        console.error('meal-log-modal not found!');
    }
}

function showSymptomLogModal() {
    console.log('Opening Symptom Log modal');
    const modal = document.getElementById('symptom-log-modal');
    if (modal) {
        modal.classList.add('active');
    } else {
        console.error('symptom-log-modal not found!');
    }
}

function showMedModal() {
    console.log('Opening Medication modal');
    const modal = document.getElementById('med-modal');
    if (modal) {
        modal.classList.add('active');
    } else {
        console.error('med-modal not found!');
    }
}

function closeModal(id) {
    console.log('Closing modal:', id);
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        
        // Reset meal form if closing meal modal
        if (id === 'meal-log-modal') {
            const nutritionResults = document.getElementById('nutrition-results');
            if (nutritionResults) nutritionResults.style.display = 'none';
            
            const form = document.getElementById('meal-form');
            if (form) form.reset();
            
            const mealPreview = document.getElementById('meal-preview');
            const uploadArea = document.getElementById('meal-upload-area');
            if (mealPreview) mealPreview.style.display = 'none';
            if (uploadArea) uploadArea.style.display = 'block';
        }
    }
}

function handleModalBackdropClick(event, modalId) {
    if (event.target.id === modalId) {
        closeModal(modalId);
    }
}

// Meal submission
async function handleMealSubmit(e) {
    e.preventDefault();
    console.log('Submitting meal...');
    
    const btn = document.getElementById('meal-submit-btn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    if (btnText) btnText.style.display = 'none';
    if (btnLoader) btnLoader.style.display = 'inline';
    
    const formData = new FormData();
    const file = document.getElementById('meal-photo').files[0];
    
    if (file) {
        console.log('Adding file:', file.name);
        formData.append('file', file);
    }
    
    formData.append('meal_type', document.getElementById('meal-type').value);
    formData.append('description', document.getElementById('meal-description').value || '');
    formData.append('user_id', userId);
    
    console.log('User ID:', userId);
    console.log('Meal type:', document.getElementById('meal-type').value);
    
    try {
        const res = await fetch(`${API_URL}/api/meals/log`, {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', res.status);
        
        if (res.ok) {
            const data = await res.json();
            console.log('Meal logged:', data);
            
            // Display nutritional analysis in modal
            displayNutritionResults(data);
            loadDashboardData();
        } else {
            const err = await res.json();
            console.error('Error response:', err);
            alert('Error: ' + (err.detail || err.message || 'Could not log meal'));
        }
    } catch (e) {
        console.error('Meal submit error:', e);
        alert('Error logging meal. Please try again.');
    } finally {
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
    }
}

// Symptom submission
async function handleSymptomSubmit(e) {
    e.preventDefault();
    console.log('Submitting symptom...');
    
    const data = {
        symptom: document.getElementById('symptom-name').value,
        severity: parseInt(document.getElementById('symptom-severity').value),
        notes: document.getElementById('symptom-notes').value || null
    };
    
    try {
        const res = await fetch(`${API_URL}/api/symptoms/log?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            alert('✅ Symptom logged successfully!');
            closeModal('symptom-log-modal');
            
            // Clear form
            document.getElementById('symptom-name').value = '';
            document.getElementById('symptom-severity').value = 5;
            document.getElementById('symptom-notes').value = '';
        } else {
            const err = await res.json();
            alert('Error: ' + (err.detail || 'Could not log symptom'));
        }
    } catch (e) {
        console.error('Symptom submit error:', e);
        alert('Error logging symptom');
    }
}

// Medication submission
async function handleMedSubmit(e) {
    e.preventDefault();
    console.log('Submitting medication...');
    
    const data = {
        name: document.getElementById('med-name').value,
        dosage: document.getElementById('med-dosage').value,
        frequency: document.getElementById('med-frequency').value
    };
    
    try {
        const res = await fetch(`${API_URL}/api/medications/add?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            alert('✅ Medication added successfully!');
            closeModal('med-modal');
            
            // Clear form
            document.getElementById('med-name').value = '';
            document.getElementById('med-dosage').value = '';
            document.getElementById('med-frequency').value = '';
        } else {
            const err = await res.json();
            alert('Error: ' + (err.detail || 'Could not add medication'));
        }
    } catch (e) {
        console.error('Medication submit error:', e);
        alert('Error adding medication');
    }
}

// Display nutrition results
function displayNutritionResults(data) {
    const resultsDiv = document.getElementById('nutrition-results');
    const contentDiv = document.getElementById('nutrition-content');
    
    if (!resultsDiv || !contentDiv) return;
    
    const analysis = data.analysis || {};
    
    let html = `
        <div class="nutrition-grid">
            <div class="nutrition-item">
                <span class="nutrition-label">Calories</span>
                <span class="nutrition-value">${analysis.calories || 0} kcal</span>
            </div>
            <div class="nutrition-item">
                <span class="nutrition-label">Protein</span>
                <span class="nutrition-value">${analysis.protein || 0}g</span>
            </div>
            <div class="nutrition-item">
                <span class="nutrition-label">Carbs</span>
                <span class="nutrition-value">${analysis.carbs || 0}g</span>
            </div>
            <div class="nutrition-item">
                <span class="nutrition-label">Fat</span>
                <span class="nutrition-value">${analysis.fat || 0}g</span>
            </div>
        </div>
    `;
    
    if (analysis.description) {
        html += `<p class="nutrition-description">${analysis.description}</p>`;
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Logout handler
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('healthlog_user');
        window.location.href = '/';
    }
}

// AI Chat submission
async function handleChatSubmit(e) {
    e.preventDefault();
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, user_id: userId })
        });
        
        if (res.ok) {
            const data = await res.json();
            console.log('Chat response:', data);
            
            // Display response (implement based on your UI)
            alert('AI Response: ' + data.response);
            input.value = '';
        }
    } catch (e) {
        console.error('Chat error:', e);
        alert('Error sending message');
    }
}

console.log('Dashboard.js loaded successfully');
