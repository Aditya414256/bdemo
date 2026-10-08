// ==========================================
// MediFind - Shared API & Session Utility
// ==========================================

const API_BASE = (window.location.origin.includes(':5000'))
    ? ''
    : 'http://127.0.0.1:5000';

const STORAGE_KEY_TOKEN = 'medifind_token';
const STORAGE_KEY_USER = 'medifind_user';

function getToken() {
    return localStorage.getItem(STORAGE_KEY_TOKEN);
}

function setToken(token) {
    if (token) {
        localStorage.setItem(STORAGE_KEY_TOKEN, token);
    } else {
        localStorage.removeItem(STORAGE_KEY_TOKEN);
    }
}

function getCurrentUser() {
    const raw = localStorage.getItem(STORAGE_KEY_USER);
    try {
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function setCurrentUser(user) {
    if (user) {
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
    } else {
        localStorage.removeItem(STORAGE_KEY_USER);
    }
}

function clearSession() {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
}

async function apiFetch(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const token = getToken();

    const headers = options.headers ? { ...options.headers } : {};

    if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const errorMsg = data && data.message ? data.message : `Request failed (${response.status})`;
            return {
                ok: false,
                status: response.status,
                message: errorMsg,
                data: data ? data.data : null
            };
        }

        return {
            ok: true,
            status: response.status,
            message: data && data.message ? data.message : 'Success',
            data: data && data.data !== undefined ? data.data : data
        };
    } catch (err) {
        console.error('API Network Error:', err);
        return {
            ok: false,
            status: 0,
            message: 'Unable to connect to server. Please ensure the backend is running.',
            data: null
        };
    }
}

// Toast notification helper
function showToast(message, type = 'info') {
    let container = document.getElementById('medifind-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'medifind-toast-container';
        container.style.cssText = `
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#0284c7',
        warning: '#f59e0b'
    };

    toast.style.cssText = `
        background: ${bgColors[type] || '#0284c7'};
        color: #ffffff;
        padding: 12px 20px;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.18);
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.9rem;
        font-weight: 600;
        opacity: 0;
        transform: translateY(-10px);
        transition: all 0.25s ease;
        pointer-events: auto;
        max-width: 360px;
        line-height: 1.4;
    `;
    toast.textContent = message;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 250);
    }, 4000);
}

// Navbar dynamic authentication update
// Navbar dynamic navigation update based on role
function initNavbarAuth() {
    const user = getCurrentUser();
    const section2 = document.querySelector('.section2');
    const section3 = document.querySelector('.section3');

    if (section2) {
        if (user && user.role === 'CUSTOMER') {
            section2.innerHTML = `
                <a class="home" href="HomePage.html">Home</a>
                <a class="findmedi" href="FindMedi.html">Find Medicine</a>
                <a class="pharmacies" href="Pharmacies.html">Pharmacies</a>
                <a class="orders" href="orders.html" style="color:#0284c7;font-weight:700;">My Orders</a>
            `;
        } else if (user && user.role === 'PHARMACY_OWNER') {
            section2.innerHTML = `
                <a class="home" href="HomePage.html">Home</a>
                <a class="pharmacies" href="Pharmacies.html">Pharmacies</a>
                <a class="dashboard" href="pharmacy-dashboard.html" style="color:#0284c7;font-weight:700;">Pharmacy Dashboard</a>
            `;
        } else if (user && user.role === 'ADMIN') {
            section2.innerHTML = `
                <a class="home" href="HomePage.html">Home</a>
                <a class="pharmacies" href="Pharmacies.html">Pharmacies</a>
                <a class="admin" href="admin-dashboard.html" style="color:#0284c7;font-weight:700;">Admin Verification</a>
            `;
        } else {
            section2.innerHTML = `
                <a class="home" href="HomePage.html">Home</a>
                <a class="findmedi" href="FindMedi.html">Find Medicine</a>
                <a class="pharmacies" href="Pharmacies.html">Pharmacies</a>
            `;
        }
    }

    if (section3) {
        if (user && getToken()) {
            section3.innerHTML = `
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.85rem;color:#0f172a;font-weight:600;background:#e0f2fe;padding:6px 12px;border-radius:20px;white-space:nowrap;">
                        👤 ${escapeHtml(user.full_name || user.name || user.email)} (${user.role.replace('_', ' ')})
                    </span>
                    <button id="nav-logout-btn" style="background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:6px 14px;border-radius:8px;font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;font-size:0.85rem;cursor:pointer;transition:all 0.2s ease;">
                        Sign Out
                    </button>
                </div>
            `;

            const logoutBtn = document.getElementById('nav-logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async () => {
                    await apiFetch('/api/auth/logout', { method: 'POST' });
                    clearSession();
                    showToast('Signed out successfully.', 'info');
                    setTimeout(() => {
                        window.location.href = 'login.html';
                    }, 500);
                });
            }
        }
    }
}

function requireRole(allowedRoles = [], redirectUrl = 'login.html') {
    const user = getCurrentUser();
    const token = getToken();
    if (!user || !token || !allowedRoles.includes(user.role)) {
        showToast('Unauthorized access. Redirecting...', 'warning');
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 800);
        return false;
    }
    return true;
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', initNavbarAuth);
