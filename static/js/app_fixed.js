// HealthLog AI - Frontend Application
// Fixed version with proper API URL configuration and error handling

// Get API URL from environment or use current domain
const API_URL = window.location.origin;
let currentUser = JSON.parse(localStorage.getItem('healthlog_user') || 'null');

console.log('HealthLog AI App Initialized');
console.log('API URL:', API_URL);
console.log('Current User:', currentUser);

function showAuthModal(type) {
    const modal = document.getElementById('auth-modal');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    
    if (modal) {
        modal.classList.add('active');
    }
    
    if (loginForm && signupForm) {
        loginForm.style.display = type === 'login' ? 'block' : 'none';
        signupForm.style.display = type === 'signup' ? 'block' : 'none';
    }
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        console.log('Attempting login with email:', email);
        
        const res = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        console.log('Login response status:', res.status);
        
        if (res.ok) {
            const data = await res.json();
            console.log('Login successful:', data);
            
            currentUser = data;
            localStorage.setItem('healthlog_user', JSON.stringify(data));
            closeAuthModal();
            
            // Redirect to dashboard
            window.location.href = '/dashboard';
        } else {
            const err = await res.json();
            console.error('Login error:', err);
            alert(err.detail || 'Invalid email or password');
        }
    } catch (e) {
        console.error('Login error:', e);
        alert('Error logging in. Please check your connection and try again.');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    
    if (!name || !email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    if (password.length < 6) {
        alert('Password must be at least 6 characters');
        return;
    }
    
    try {
        console.log('Attempting signup with email:', email);
        
        const res = await fetch(`${API_URL}/api/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        console.log('Signup response status:', res.status);
        
        if (res.ok) {
            const data = await res.json();
            console.log('Signup successful:', data);
            
            alert('✅ Account created successfully! Please log in.');
            
            // Clear form
            document.getElementById('signup-name').value = '';
            document.getElementById('signup-email').value = '';
            document.getElementById('signup-password').value = '';
            
            // Switch to login form
            showAuthModal('login');
        } else {
            const err = await res.json();
            console.error('Signup error:', err);
            alert(err.detail || 'Signup failed. Please try again.');
        }
    } catch (e) {
        console.error('Signup error:', e);
        alert('Error creating account. Please check your connection and try again.');
    }
}

function toggleMobileMenu() {
    const nav = document.querySelector('.nav-links');
    if (nav) {
        nav.style.display = nav.style.display === 'flex' ? 'none' : 'flex';
    }
}

// Modal backdrop click to close
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeAuthModal();
    }
});

// Escape key to close modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAuthModal();
    }
});

console.log('App.js loaded successfully');
