// HealthLog AI - Dashboard JavaScript (Fixed Version)
const API_URL = '';
let currentUser = JSON.parse(localStorage.getItem('healthlog_user') || 'null');
const userId = currentUser?.user_id || 'demo-user';

// Debug: Log user info on load
console.log('HealthLog AI Dashboard Loaded');
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
    document.getElementById('greeting').textContent = `${greeting}! Here's your health summary.`;
    if (currentUser) {
        document.getElementById('user-name').textContent = currentUser.name || 'User';
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
            document.getElementById(`${section}-section`).classList.add('active');
            document.getElementById('page-title').textContent = section.charAt(0).toUpperCase() + section.slice(1);
        });
    });
}

function initSliders() {
    ['energy', 'mood'].forEach(id => {
        const slider = document.getElementById(`${id}-slider`);
        const display = document.getElementById(`${id}-value`);
        if (slider && display) {
            slider.addEventListener('input', () => display.textContent = slider.value);
        }
    });
    const sevSlider = document.getElementById('symptom-severity');
    const sevDisplay = document.getElementById('severity-display');
    if (sevSlider && sevDisplay) {
        sevSlider.addEventListener('input', () => sevDisplay.textContent = sevSlider.value);
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
                    alert('Daily check-in saved!');
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
            document.getElementById('today-calories').textContent = insights.avg_daily_calories || 0;
            document.getElementById('meals-logged').textContent = insights.meals_logged || 0;
            document.getElementById('avg-energy').textContent = insights.avg_energy ? `${insights.avg_energy}/10` : '-';
            document.getElementById('med-adherence').textContent = '-';
        }
    } catch (e) {
        console.log('Error loading dashboard data:', e);
    }
}

// Modal functions
function showQuickLogModal() {
    console.log('Opening Quick Log modal');
    const modal = document.getElementById('quick-log-modal');
    if (modal) {
        modal.classList.add('active');
    } else {
        console.error('quick-log-modal not found!');
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
    
    // Add change listener to file input (label handles the click automatically)
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
        const closeBtn = document.getElementById('close-meal-modal-btn');
        
        if (uploadArea) uploadArea.style.display = 'block';
        if (mealPreview) mealPreview.style.display = 'none';
        if (mealPhoto) mealPhoto.value = '';
        if (nutritionResults) nutritionResults.style.display = 'none';
        if (submitBtn) submitBtn.style.display = 'block';
        if (closeBtn) closeBtn.remove();
        
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
        frequency: document.getElementById('med-frequency').value,
        reminder_times: []
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
        } else {
            const err = await res.json();
            alert('Error: ' + (err.detail || 'Could not add medication'));
        }
    } catch (e) {
        console.error('Medication submit error:', e);
        alert('Error adding medication');
    }
}

// Chat
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    const container = document.getElementById('chat-messages');
    container.innerHTML += `<div class="chat-message user"><div class="message-content">${msg}</div></div>`;
    input.value = '';
    container.scrollTop = container.scrollHeight;
    
    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, user_id: userId })
        });
        
        const data = await res.json();
        container.innerHTML += `<div class="chat-message bot"><div class="message-content">${data.response}</div></div>`;
        container.scrollTop = container.scrollHeight;
    } catch (e) {
        container.innerHTML += `<div class="chat-message bot"><div class="message-content">Sorry, I couldn't respond. Please try again.</div></div>`;
    }
}

// Chat enter key
const chatInput = document.getElementById('chat-input');
if (chatInput) {
    chatInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// Generate report
async function generateReport() {
    const container = document.getElementById('report-content');
    container.innerHTML = '<p>Generating report...</p>';
    
    try {
        const res = await fetch(`${API_URL}/api/report/${userId}`);
        const data = await res.json();
        
        container.innerHTML = `
            <h3>📊 Weekly Health Report</h3>
            <p><strong>Period:</strong> ${data.period}</p>
            <p><strong>Meals Logged:</strong> ${data.summary?.meals_logged || 0}</p>
            <p><strong>Avg Calories:</strong> ${data.summary?.avg_daily_calories || 0}</p>
            <p><strong>Avg Energy:</strong> ${data.summary?.avg_energy || '-'}/10</p>
            <p><strong>Avg Mood:</strong> ${data.summary?.avg_mood || '-'}/10</p>
            <h4>Recommendations:</h4>
            <ul>${(data.recommendations || []).map(r => `<li>${r}</li>`).join('')}</ul>
        `;
    } catch (e) {
        container.innerHTML = '<p>Error generating report</p>';
    }
}

function navigateTo(section) {
    const navItem = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (navItem) navItem.click();
}

function handleLogout() {
    localStorage.removeItem('healthlog_user');
    window.location.href = '/';
}

// Display nutritional analysis results
function displayNutritionResults(data) {
    const nutritionResults = document.getElementById('nutrition-results');
    const nutritionContent = document.getElementById('nutrition-content');
    
    if (!nutritionResults || !nutritionContent) return;
    
    const analysis = data.analysis || {};
    const calories = analysis.calories || 0;
    const protein = analysis.protein || 0;
    const carbs = analysis.carbs || 0;
    const fat = analysis.fat || 0;
    const description = analysis.description || analysis.meal_description || 'Meal analyzed';
    const details = analysis.details || analysis.nutritional_info || '';
    
    // Build HTML for nutrition display
    let html = `
        <div class="nutrition-description">
            <strong>🍽️ ${description}</strong>
        </div>
        <div class="nutrition-grid">
            <div class="nutrition-item">
                <div class="nutrition-label">Calories</div>
                <div class="nutrition-value">${calories}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">kcal</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-label">Protein</div>
                <div class="nutrition-value">${protein}g</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-label">Carbs</div>
                <div class="nutrition-value">${carbs}g</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-label">Fat</div>
                <div class="nutrition-value">${fat}g</div>
            </div>
        </div>
    `;
    
    if (details) {
        html += `<div class="nutrition-description" style="margin-top: 16px;">${details}</div>`;
    }
    
    nutritionContent.innerHTML = html;
    nutritionResults.style.display = 'block';
    
    // Scroll to nutrition results
    nutritionResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Hide submit button, show close button option
    const submitBtn = document.getElementById('meal-submit-btn');
    if (submitBtn) {
        submitBtn.style.display = 'none';
    }
    
    // Add a close button after results
    if (!document.getElementById('close-meal-modal-btn')) {
        const closeBtn = document.createElement('button');
        closeBtn.id = 'close-meal-modal-btn';
        closeBtn.className = 'btn btn-primary btn-block';
        closeBtn.style.marginTop = '16px';
        closeBtn.textContent = 'Close';
        closeBtn.onclick = () => {
            closeModal('meal-log-modal');
            loadDashboardData();
        };
        nutritionResults.appendChild(closeBtn);
    }
}
