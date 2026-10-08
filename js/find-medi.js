// ==========================================
// MediFind - Find Medicine Page Logic
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.medicine-search input');
    const searchBtn = document.querySelector('.search-medicine-button');
    const resultsContainer = document.querySelector('main.medicine-results');

    // Parse URL param ?q=
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get('q') || 'Paracetamol';

    if (searchInput) {
        searchInput.value = initialQuery;
    }

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => {
            performSearch(searchInput.value.trim());
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(searchInput.value.trim());
            }
        });
    }

    async function performSearch(query) {
        if (!query) {
            showToast('Please type a medicine or generic name.', 'warning');
            return;
        }

        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div style="text-align:center;padding:40px;color:#64748b;font-family:'Plus Jakarta Sans',sans-serif;">
                    <p style="font-size:1.1rem;">🔍 Searching available medicines...</p>
                </div>
            `;
        }

        try {
            const res = await apiFetch(`/api/medicines/search?q=${encodeURIComponent(query)}`);
            if (res.ok && res.data && res.data.medicines && res.data.medicines.length > 0) {
                renderMedicines(res.data.medicines);
            } else {
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div style="text-align:center;padding:50px 20px;background:#ffffff;border-radius:16px;border:1px dashed #cbd5e1;font-family:'Plus Jakarta Sans',sans-serif;">
                            <h3 style="color:#0f172a;margin-bottom:8px;">No medicines found</h3>
                            <p style="color:#64748b;">No matches found for "<strong>${escapeHtml(query)}</strong>". Try searching "Paracetamol", "Amoxicillin", "Cetirizine", or "Ibuprofen".</p>
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error('Search error:', err);
            showToast('Error searching medicines.', 'error');
        }
    }

    function renderMedicines(medicines) {
        if (!resultsContainer) return;

        resultsContainer.innerHTML = medicines.map(m => `
            <div class="medicine-card" id="medicine-card-${m.id}">
                <div class="medicine-details">
                    <div class="medicine-badges">
                        <span class="badge">${escapeHtml(m.dosage_form || 'Tablet')}</span>
                        <span class="badge badge-primary">${escapeHtml(m.strength || '500mg')}</span>
                        <span class="badge ${m.requires_prescription ? 'badge-primary' : 'badge-success'}">
                            ${m.requires_prescription ? 'Rx Prescription' : '✓ OTC'}
                        </span>
                    </div>

                    <h3>${escapeHtml(m.name)}</h3>

                    <div class="medicine-generic">
                        <strong>Generic:</strong> ${escapeHtml(m.generic_name || m.name)}
                    </div>

                    <div class="medicine-description">
                        ${escapeHtml(m.description || 'Quality assured pharmaceutical product.')}
                    </div>

                    <div class="pharmacy-count">
                        ✓ Found in verified nearby pharmacies
                    </div>

                    <!-- Pharmacy availability panel -->
                    <div class="pharmacies-panel" id="stores-for-${m.id}" style="display:none;margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0;"></div>
                </div>

                <div class="medicine-action" style="display:flex;gap:10px;align-items:center;">
                    <button class="view-stores-button" type="button" data-medicine-id="${m.id}" data-medicine-name="${escapeHtml(m.name)}">
                        View Stores
                    </button>
                    <button class="direct-order-btn" type="button" data-medicine-id="${m.id}" style="background:#0284c7;color:#ffffff;border:1px solid transparent;padding:0.65rem 1.25rem;border-radius:10px;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.9rem;font-weight:600;cursor:pointer;">
                        Order Now
                    </button>
                </div>
            </div>
        `).join('');

        resultsContainer.querySelectorAll('.view-stores-button').forEach(btn => {
            btn.addEventListener('click', () => {
                const medId = btn.getAttribute('data-medicine-id');
                const medName = btn.getAttribute('data-medicine-name');
                toggleStores(medId, medName, btn);
            });
        });

        resultsContainer.querySelectorAll('.direct-order-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const medId = btn.getAttribute('data-medicine-id');
                openOrderModal(medId);
            });
        });
    }

    async function toggleStores(medicineId, medicineName, btn) {
        const panel = document.getElementById(`stores-for-${medicineId}`);
        if (!panel) return;

        if (panel.style.display === 'block') {
            panel.style.display = 'none';
            btn.textContent = 'View Stores';
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Checking...';

        try {
            const res = await apiFetch(`/api/medicines/${medicineId}/pharmacies?method=pickup`);
            btn.disabled = false;
            btn.textContent = 'Hide Stores';

            if (res.ok && res.data && res.data.pharmacies && res.data.pharmacies.length > 0) {
                const list = res.data.pharmacies;
                panel.innerHTML = `
                    <h4 style="font-family:'Space Grotesk',sans-serif;margin:0 0 12px 0;color:#0f172a;font-size:1.05rem;">
                        Verified Stores with Available Stock:
                    </h4>
                    <div style="display:flex;flex-direction:column;gap:12px;">
                        ${list.map(p => `
                            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                                <div>
                                    <div style="font-weight:700;color:#0f172a;font-size:1rem;display:flex;align-items:center;gap:6px;">
                                        🏥 ${escapeHtml(p.name)}
                                        <span style="font-size:0.75rem;background:#dcfce7;color:#166534;padding:2px 8px;border-radius:999px;">Verified</span>
                                    </div>
                                    <div style="color:#64748b;font-size:0.85rem;margin-top:4px;">
                                        📍 ${escapeHtml(p.address)}, ${escapeHtml(p.city)} (${p.pincode})
                                    </div>
                                    <div style="color:#0369a1;font-size:0.85rem;margin-top:3px;font-weight:600;">
                                        💰 ₹${p.price.toFixed(2)} &bull; ${p.quantity} units available
                                        ${p.distance_km !== null ? ` &bull; 🚗 ${p.distance_km.toFixed(1)} km away` : ''}
                                    </div>
                                </div>
                                <div>
                                    <button class="order-btn" data-pharmacy-id="${p.id}" data-medicine-id="${medicineId}" style="background:#0284c7;color:#fff;border:none;padding:8px 16px;border-radius:8px;font-weight:600;font-size:0.85rem;cursor:pointer;">
                                        Order Now
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
                panel.style.display = 'block';

                panel.querySelectorAll('.order-btn').forEach(orderBtn => {
                    orderBtn.addEventListener('click', () => {
                        const medId = orderBtn.getAttribute('data-medicine-id');
                        openOrderModal(medId);
                    });
                });
            } else {
                panel.innerHTML = `
                    <div style="padding:12px;background:#fef2f2;border-radius:8px;color:#991b1b;font-size:0.9rem;">
                        No nearby verified pharmacies currently have stock for this medicine.
                    </div>
                `;
                panel.style.display = 'block';
            }
        } catch (err) {
            console.error('Stores error:', err);
            btn.disabled = false;
            btn.textContent = 'View Stores';
            showToast('Unable to load stores.', 'error');
        }
    }

    performSearch(initialQuery);
});
