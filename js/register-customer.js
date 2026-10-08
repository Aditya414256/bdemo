// ==========================================
// MediFind - Customer Registration Logic
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.customer-card-body form');
    const fullNameInput = document.getElementById('full_name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const submitBtn = document.querySelector('.customer-register-button');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const full_name = fullNameInput ? fullNameInput.value.trim() : '';
        const email = emailInput ? emailInput.value.trim() : '';
        const phone = phoneInput ? phoneInput.value.trim() : '';
        const password = passwordInput ? passwordInput.value : '';
        const confirm_password = confirmPasswordInput ? confirmPasswordInput.value : '';

        if (!full_name || !email || !password) {
            showToast('Please fill in all required fields (*).', 'warning');
            return;
        }

        if (password !== confirm_password) {
            showToast('Passwords do not match.', 'error');
            return;
        }

        if (password.length < 6) {
            showToast('Password must be at least 6 characters long.', 'warning');
            return;
        }

        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';

        try {
            const res = await apiFetch('/api/auth/register/customer', {
                method: 'POST',
                body: JSON.stringify({
                    full_name,
                    email,
                    phone,
                    password
                })
            });

            if (res.ok && res.data) {
                setToken(res.data.token);
                setCurrentUser(res.data.user);

                showToast('Registration successful! Welcome to MediFind.', 'success');

                setTimeout(() => {
                    window.location.href = 'HomePage.html';
                }, 1000);
            } else {
                showToast(res.message || 'Registration failed.', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }
        } catch (err) {
            console.error('Registration error:', err);
            showToast('An error occurred during registration.', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    });
});
