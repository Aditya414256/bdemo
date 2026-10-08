// ==========================================
// MediFind - Pharmacies Page Logic
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
    const container = document.querySelector('.Pharmacies');
    if (!container) return;

    container.innerHTML = `
        <div style="margin-bottom:30px;">
            <h1 style="font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:700;color:#0f172a;margin:0 0 8px 0;">
                Verified Pharmacies
            </h1>
            <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1rem;color:#64748b;margin:0;">
                Browse licensed and verified partner pharmacies in your area.
            </p>
        </div>
        <div id="pharmacies-list" style="display:flex;flex-direction:column;gap:18px;">
            <div style="text-align:center;padding:40px;color:#64748b;font-family:'Plus Jakarta Sans',sans-serif;">
                Loading verified pharmacies...
            </div>
        </div>
    `;

    const listElement = document.getElementById('pharmacies-list');

    try {
        const res = await apiFetch('/api/pharmacy/list');

        if (res.ok && res.data && res.data.pharmacies && res.data.pharmacies.length > 0) {
            const pharmacies = res.data.pharmacies;
            listElement.innerHTML = pharmacies.map(p => `
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:25px;box-shadow:0 4px 12px rgba(15,23,42,0.05);display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center;">
                    <div>
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;">
                            <span style="background:#d1fae5;color:#047857;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.75rem;font-weight:700;padding:4px 10px;border-radius:999px;">
                                ✓ VERIFIED PHARMACY
                            </span>
                            <span style="background:#f1f5f9;color:#475569;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.75rem;font-weight:600;padding:4px 10px;border-radius:999px;">
                                License: ${escapeHtml(p.license_number || 'Verified')}
                            </span>
                        </div>

                        <h3 style="font-family:'Space Grotesk',sans-serif;font-size:1.35rem;font-weight:700;color:#0f172a;margin:0 0 8px 0;">
                            ${escapeHtml(p.name)}
                        </h3>

                        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.9rem;color:#475569;margin-bottom:6px;">
                            📍 <strong>Address:</strong> ${escapeHtml(p.address)}, ${escapeHtml(p.city)}, ${escapeHtml(p.state)} - ${escapeHtml(p.pincode)}
                        </div>

                        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.85rem;color:#64748b;display:flex;gap:18px;flex-wrap:wrap;margin-top:8px;">
                            ${p.phone ? `<span>📞 ${escapeHtml(p.phone)}</span>` : ''}
                            ${p.email ? `<span>✉️ ${escapeHtml(p.email)}</span>` : ''}
                        </div>

                        <div style="display:flex;gap:8px;margin-top:12px;">
                            ${p.supports_pickup ? '<span style="font-size:0.78rem;background:#e0f2fe;color:#0369a1;padding:3px 8px;border-radius:6px;font-weight:600;">🏪 Store Pickup</span>' : ''}
                            ${p.supports_delivery ? '<span style="font-size:0.78rem;background:#fef3c7;color:#92400e;padding:3px 8px;border-radius:6px;font-weight:600;">🚚 Home Delivery</span>' : ''}
                        </div>
                    </div>

                    <div>
                        <a href="FindMedi.html" style="display:inline-flex;align-items:center;justify-content:center;background:#0284c7;color:#ffffff;padding:0.65rem 1.25rem;border-radius:10px;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.9rem;font-weight:600;text-decoration:none;transition:all 0.2s ease;">
                            Search Medicines
                        </a>
                    </div>
                </div>
            `).join('');
        } else {
            listElement.innerHTML = `
                <div style="text-align:center;padding:50px 20px;background:#ffffff;border-radius:16px;border:1px dashed #cbd5e1;font-family:'Plus Jakarta Sans',sans-serif;">
                    <h3 style="color:#0f172a;margin-bottom:8px;">No pharmacies found</h3>
                    <p style="color:#64748b;">No verified pharmacies are currently active.</p>
                </div>
            `;
        }
    } catch (err) {
        console.error('Pharmacies list error:', err);
        listElement.innerHTML = `
            <div style="text-align:center;padding:30px;color:#ef4444;font-family:'Plus Jakarta Sans',sans-serif;">
                Failed to load pharmacies. Please ensure the backend server is running.
            </div>
        `;
    }
});
