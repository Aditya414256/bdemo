// ==========================================
// MediFind - Admin Verification Dashboard Logic
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireRole(['ADMIN'])) return;

    const listContainer = document.getElementById('pending-pharmacies-list');
    const countEl = document.getElementById('pending-count');
    const refreshBtn = document.getElementById('admin-refresh-btn');

    refreshBtn.onclick = () => loadPendingPharmacies();

    await loadPendingPharmacies();

    async function loadPendingPharmacies() {
        listContainer.innerHTML = '<div style="text-align:center;padding:40px;color:#64748b;">Fetching pending applications...</div>';

        const res = await apiFetch('/api/admin/pharmacies/pending');
        if (res.ok && res.data && Array.isArray(res.data.pending_pharmacies)) {
            const list = res.data.pending_pharmacies;
            countEl.textContent = list.length;

            if (list.length === 0) {
                listContainer.innerHTML = `
                    <div style="background:#ffffff;border:1px dashed #cbd5e1;border-radius:16px;padding:60px 20px;text-align:center;">
                        <div style="font-size:36px;margin-bottom:10px;">🎉</div>
                        <h3 style="margin:0 0 6px 0;color:#0f172a;font-family:'Space Grotesk',sans-serif;">No Pending Registrations</h3>
                        <p style="margin:0;color:#64748b;font-size:0.9rem;">All registered pharmacy accounts have been verified and processed.</p>
                    </div>
                `;
                return;
            }

            listContainer.innerHTML = list.map(p => `
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;box-shadow:0 4px 12px rgba(15,23,42,0.04);display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center;">
                    <div>
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;">
                            <span style="background:#fef3c7;color:#92400e;font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:999px;">
                                ⏳ PENDING APPROVAL
                            </span>
                            <span style="background:#f1f5f9;color:#0f172a;font-size:0.8rem;font-weight:700;padding:3px 10px;border-radius:999px;border:1px solid #cbd5e1;">
                                Drug License No: ${escapeHtml(p.license_number || 'DL-PENDING-SUBMISSION')}
                            </span>
                        </div>

                        <h3 style="margin:0 0 8px 0;font-family:'Space Grotesk',sans-serif;font-size:1.35rem;color:#0f172a;">
                            ${escapeHtml(p.name)}
                        </h3>

                        <div style="font-size:0.9rem;color:#475569;margin-bottom:6px;">
                            📍 <strong>Store Address:</strong> ${escapeHtml(p.address)}, ${escapeHtml(p.city)}, ${escapeHtml(p.state)} - ${escapeHtml(p.pincode)}
                        </div>

                        <div style="display:flex;gap:18px;font-size:0.85rem;color:#64748b;flex-wrap:wrap;margin-top:6px;">
                            <span>👤 <strong>Owner:</strong> ${escapeHtml(p.owner?.name || 'Registered Owner')}</span>
                            <span>✉️ ${escapeHtml(p.owner?.email || p.email || 'N/A')}</span>
                            <span>📞 ${escapeHtml(p.phone || p.owner?.phone || 'N/A')}</span>
                        </div>

                        <div style="display:flex;gap:8px;margin-top:10px;">
                            ${p.supports_pickup ? '<span style="font-size:0.75rem;background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:6px;font-weight:600;">Pickup Supported</span>' : ''}
                            ${p.supports_delivery ? '<span style="font-size:0.75rem;background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:6px;font-weight:600;">Delivery Supported</span>' : ''}
                        </div>
                    </div>

                    <div style="display:flex;flex-direction:column;gap:8px;min-width:140px;">
                        <button type="button" class="btn-admin-approve" data-id="${p.id}" style="background:#10b981;color:#ffffff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:0.88rem;cursor:pointer;transition:all 0.2s;">
                            ✓ Approve
                        </button>
                        <button type="button" class="btn-admin-reject" data-id="${p.id}" style="background:#ef4444;color:#ffffff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:0.88rem;cursor:pointer;transition:all 0.2s;">
                            ✕ Reject
                        </button>
                    </div>
                </div>
            `).join('');

            // Wire action buttons
            listContainer.querySelectorAll('.btn-admin-approve').forEach(btn => {
                btn.onclick = async () => {
                    const id = btn.getAttribute('data-id');
                    btn.disabled = true;
                    btn.textContent = 'Approving...';

                    const actionRes = await apiFetch(`/api/admin/pharmacies/${id}/verification`, {
                        method: 'PATCH',
                        body: JSON.stringify({ status: 'APPROVED' })
                    });

                    if (actionRes.ok) {
                        showToast(`Pharmacy #${id} approved! It is now active and visible to customers.`, 'success');
                        await loadPendingPharmacies();
                    } else {
                        showToast(actionRes.message || 'Approval failed.', 'error');
                        btn.disabled = false;
                        btn.textContent = '✓ Approve';
                    }
                };
            });

            listContainer.querySelectorAll('.btn-admin-reject').forEach(btn => {
                btn.onclick = async () => {
                    const id = btn.getAttribute('data-id');
                    if (!confirm(`Are you sure you want to reject registration for pharmacy #${id}?`)) return;

                    btn.disabled = true;
                    btn.textContent = 'Rejecting...';

                    const actionRes = await apiFetch(`/api/admin/pharmacies/${id}/verification`, {
                        method: 'PATCH',
                        body: JSON.stringify({ status: 'REJECTED' })
                    });

                    if (actionRes.ok) {
                        showToast(`Pharmacy #${id} registration rejected.`, 'info');
                        await loadPendingPharmacies();
                    } else {
                        showToast(actionRes.message || 'Rejection failed.', 'error');
                        btn.disabled = false;
                        btn.textContent = '✕ Reject';
                    }
                };
            });
        } else {
            listContainer.innerHTML = '<div style="padding:30px;text-align:center;color:#ef4444;">Failed to load pending pharmacies.</div>';
        }
    }
});
