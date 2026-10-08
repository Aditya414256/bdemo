// ==========================================
// MediFind - Homepage Search & Autocomplete
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('home-search-input');
    const searchBtn = document.querySelector('.search-button');
    const suggestionsBox = document.getElementById('search-suggestions');
    const resultsContainer = document.getElementById('medicine-results');

    let debounceTimer = null;

    if (!searchInput) return;

    // Autocomplete Suggestions on Input
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);

        if (!query || query.length < 2) {
            if (suggestionsBox) {
                suggestionsBox.innerHTML = '';
                suggestionsBox.style.display = 'none';
            }
            return;
        }

        debounceTimer = setTimeout(async () => {
            const res = await apiFetch(`/api/medicines/suggestions?q=${encodeURIComponent(query)}`);
            if (res.ok && res.data && res.data.suggestions && res.data.suggestions.length > 0) {
                renderSuggestions(res.data.suggestions);
            } else {
                if (suggestionsBox) {
                    suggestionsBox.innerHTML = '';
                    suggestionsBox.style.display = 'none';
                }
            }
        }, 250);
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (suggestionsBox && !suggestionsBox.contains(e.target) && e.target !== searchInput) {
            suggestionsBox.style.display = 'none';
        }
    });

    // Perform Search on Button click or Enter
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            performSearch(searchInput.value.trim());
        });
    }

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch(searchInput.value.trim());
        }
    });

    function renderSuggestions(suggestions) {
        if (!suggestionsBox) return;

        suggestionsBox.innerHTML = suggestions.map(s => `
            <div class="suggestion-item" data-id="${s.id}" data-name="${escapeHtml(s.name)}" style="padding:10px 14px;cursor:pointer;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <strong style="color:#0f172a;font-size:0.95rem;">${escapeHtml(s.name)}</strong>
                    <span style="color:#64748b;font-size:0.85rem;margin-left:8px;">${escapeHtml(s.generic_name || '')} (${escapeHtml(s.strength || '')})</span>
                </div>
                <span style="font-size:0.75rem;padding:3px 8px;border-radius:999px;background:${s.requires_prescription ? '#fee2e2;color:#b91c1c' : '#dcfce7;color:#15803d'}">
                    ${s.requires_prescription ? 'Rx Required' : 'OTC'}
                </span>
            </div>
        `).join('');

        suggestionsBox.style.display = 'block';

        // Add click events to suggestion items
        suggestionsBox.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const name = item.getAttribute('data-name');
                searchInput.value = name;
                suggestionsBox.style.display = 'none';
                performSearch(name);
            });
        });
    }

    async function performSearch(query) {
        if (suggestionsBox) suggestionsBox.style.display = 'none';

        if (!query) {
            showToast('Please enter a medicine name to search.', 'warning');
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
                            <p style="color:#64748b;">We couldn't find any medicines matching "<strong>${escapeHtml(query)}</strong>". Try searching "Paracetamol", "Amoxicillin", or "Cetirizine".</p>
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error('Search error:', err);
            showToast('Error fetching medicine results.', 'error');
        }
    }

    function renderMedicines(medicines) {
        if (!resultsContainer) return;

        resultsContainer.innerHTML = medicines.map(m => `
            <div class="medicine-card" id="medicine-card-${m.id}">
                <div class="medicine-details">
                    <div class="medicine-badges">
                        <span class="badge">${escapeHtml(m.dosage_form || 'Form')}</span>
                        <span class="badge badge-primary">${escapeHtml(m.strength || 'Standard')}</span>
                        <span class="badge ${m.requires_prescription ? 'badge-primary' : 'badge-success'}">
                            ${m.requires_prescription ? 'Rx Prescription' : '✓ OTC'}
                        </span>
                    </div>

                    <h3>${escapeHtml(m.name)}</h3>

                    <div class="medicine-generic">
                        <strong>Generic:</strong> ${escapeHtml(m.generic_name || m.name)}
                    </div>

                    <div class="medicine-description">
                        ${escapeHtml(m.description || 'Verified pharmaceutical formulation.')}
                    </div>

                    <div class="pharmacy-count">
                        ✓ In-stock at verified local pharmacies
                    </div>

                    <!-- Expandable Pharmacy Availability Panel -->
                    <div class="pharmacies-panel" id="pharmacies-for-${m.id}" style="display:none;margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0;">
                    </div>
                </div>

                <div class="medicine-action">
                    <button class="view-stores-button" type="button" data-medicine-id="${m.id}" data-medicine-name="${escapeHtml(m.name)}">
                        View Stores
                    </button>
                </div>
            </div>
        `).join('');

        // Wire View Stores buttons
        resultsContainer.querySelectorAll('.view-stores-button').forEach(btn => {
            btn.addEventListener('click', () => {
                const medId = btn.getAttribute('data-medicine-id');
                const medName = btn.getAttribute('data-medicine-name');
                togglePharmacyStores(medId, medName, btn);
            });
        });
    }

    async function togglePharmacyStores(medicineId, medicineName, btn) {
        const panel = document.getElementById(`pharmacies-for-${medicineId}`);
        if (!panel) return;

        if (panel.style.display === 'block') {
            panel.style.display = 'none';
            btn.textContent = 'View Stores';
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Checking stock...';

        try {
            const res = await apiFetch(`/api/medicines/${medicineId}/pharmacies?method=pickup`);
            btn.disabled = false;
            btn.textContent = 'Hide Stores';

            if (res.ok && res.data && res.data.pharmacies && res.data.pharmacies.length > 0) {
                const list = res.data.pharmacies;
                panel.innerHTML = `
                    <h4 style="font-family:'Space Grotesk',sans-serif;margin:0 0 12px 0;color:#0f172a;font-size:1.05rem;">
                        Available Stores for ${escapeHtml(medicineName)} (${list.length} nearby)
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
                                        💰 ₹${p.price.toFixed(2)} &bull; ${p.quantity} units in stock
                                        ${p.distance_km !== null ? ` &bull; 🚗 ${p.distance_km.toFixed(1)} km away` : ''}
                                    </div>
                                </div>
                                <div>
                                    <button class="order-btn" data-pharmacy-id="${p.id}" data-medicine-id="${medicineId}" data-price="${p.price}" style="background:#0284c7;color:#fff;border:none;padding:8px 16px;border-radius:8px;font-weight:600;font-size:0.85rem;cursor:pointer;">
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
                        handleOrderClick(
                            orderBtn.getAttribute('data-pharmacy-id'),
                            orderBtn.getAttribute('data-medicine-id'),
                            orderBtn.getAttribute('data-price')
                        );
                    });
                });
            } else {
                panel.innerHTML = `
                    <div style="padding:12px;background:#fef2f2;border-radius:8px;color:#991b1b;font-size:0.9rem;">
                        No verified pharmacies currently have stock for this medicine.
                    </div>
                `;
                panel.style.display = 'block';
            }
        } catch (err) {
            console.error('Fetch pharmacies error:', err);
            btn.disabled = false;
            btn.textContent = 'View Stores';
            showToast('Unable to load stores at this time.', 'error');
        }
    }

    async function handleOrderClick(pharmacyId, medicineId, price) {
        const user = getCurrentUser();
        if (!user || !getToken()) {
            showToast('Please log in as a customer to place an order.', 'warning');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1200);
            return;
        }

        const qtyStr = prompt('Enter quantity to order:', '1');
        if (!qtyStr) return;
        const qty = parseInt(qtyStr, 10);
        if (isNaN(qty) || qty <= 0) {
            showToast('Invalid quantity entered.', 'error');
            return;
        }

        const fulfillmentMethod = confirm('Click OK for Store Pickup, or Cancel for Home Delivery') ? 'PICKUP' : 'DELIVERY';

        let deliveryAddress = '';
        if (fulfillmentMethod === 'DELIVERY') {
            deliveryAddress = prompt('Enter your delivery address:');
            if (!deliveryAddress) {
                showToast('Delivery address is required for home delivery.', 'warning');
                return;
            }
        }

        const formData = new FormData();
        formData.append('pharmacy_id', pharmacyId);
        formData.append('fulfillment_method', fulfillmentMethod);
        if (deliveryAddress) {
            formData.append('delivery_address', deliveryAddress);
        }
        formData.append('items', JSON.stringify([
            { medicine_id: parseInt(medicineId, 10), quantity: qty }
        ]));

        showToast('Submitting your order...', 'info');

        const res = await apiFetch('/api/orders', {
            method: 'POST',
            body: formData
        });

        if (res.ok && res.data) {
            showToast(`Order #${res.data.id} placed successfully! Total: ₹${res.data.total_amount}`, 'success');
        } else {
            showToast(res.message || 'Failed to place order.', 'error');
        }
    }

    // Default search on load: populate Paracetamol so page looks lively!
    performSearch('Paracetamol');
});
