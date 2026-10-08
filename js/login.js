// ==========================================
// MediFind - Login Logic
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.login-form-container form');
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    const submitBtn = document.querySelector('.sign-in-button');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = emailInput ? emailInput.value.trim() : '';
        const password = passwordInput ? passwordInput.value : '';

        if (!email || !password) {
            showToast('Please enter both email and password.', 'warning');
            return;
        }

        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Signing in...';

        try {
            const res = await apiFetch('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });

            if (res.ok && res.data) {
                setToken(res.data.token);
                setCurrentUser(res.data.user);

                showToast(`Welcome back, ${res.data.user.full_name || 'User'}!`, 'success');

                setTimeout(() => {
                    if (res.data.user.role === 'PHARMACY_OWNER') {
                        window.location.href = 'pharmacy-dashboard.html';
                    } else if (res.data.user.role === 'ADMIN') {
                        window.location.href = 'admin-dashboard.html';
                    } else {
                        window.location.href = 'HomePage.html';
                    }
                }, 800);
            } else {
                showToast(res.message || 'Login failed. Please check your credentials.', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        } catch (err) {
            console.error('Login error:', err);
            showToast('An unexpected error occurred during login.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
});
