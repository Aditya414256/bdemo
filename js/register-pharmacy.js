// ==========================================
// MediFind - Pharmacy Registration Logic
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.pharmacy-card-body form');
    const submitBtn = document.querySelector('.pharmacy-register-button');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const full_name = document.getElementById('full_name')?.value.trim();
        const email = document.getElementById('email')?.value.trim();
        const password = document.getElementById('password')?.value;
        const confirm_password = document.getElementById('confirm_password')?.value;
        const pharmacy_name = document.getElementById('pharmacy_name')?.value.trim();
        const license_number = document.getElementById('license_number')?.value.trim();
        const pharmacy_phone = document.getElementById('pharmacy_phone')?.value.trim();
        const pharmacy_email = document.getElementById('pharmacy_email')?.value.trim();
        const address = document.getElementById('address')?.value.trim();
        const city = document.getElementById('city')?.value.trim();
        const state = document.getElementById('state')?.value.trim();
        const pincode = document.getElementById('pincode')?.value.trim();
        const supports_pickup = document.getElementById('supports_pickup')?.checked ?? true;
        const supports_delivery = document.getElementById('supports_delivery')?.checked ?? false;

        if (!full_name || !email || !password || !pharmacy_name || !license_number || !address || !city || !state || !pincode) {
            showToast('Please fill in all mandatory fields (*).', 'warning');
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
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting Application...';

        try {
            const payload = {
                full_name,
                email,
                password,
                pharmacy_name,
                license_number,
                phone: pharmacy_phone,
                pharmacy_email: pharmacy_email || email,
                address,
                city,
                state,
                pincode,
                supports_pickup,
                supports_delivery
            };

            const res = await apiFetch('/api/auth/register/pharmacy', {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                showToast('Pharmacy registered successfully! Pending admin verification.', 'success');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 1500);
            } else {
                showToast(res.message || 'Registration failed.', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }
        } catch (err) {
            console.error('Pharmacy registration error:', err);
            showToast('An error occurred during submission.', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    });
});
