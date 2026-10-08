// ==========================================
// MediFind - Interactive Customer Order Modal
// ==========================================

let activeOrderModal = null;

async function openOrderModal(medicineId) {
    const user = getCurrentUser();
    if (!user || !getToken()) {
        showToast('Please sign in as a customer to place an order.', 'warning');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1200);
        return;
    }

    if (user.role !== 'CUSTOMER') {
        showToast('Only customer accounts can place orders.', 'error');
        return;
    }

    // Fetch medicine details
    showToast('Loading medicine details...', 'info');
    const medRes = await apiFetch(`/api/medicines/${medicineId}`);
    if (!medRes.ok || !medRes.data) {
        showToast('Could not load medicine details.', 'error');
        return;
    }
    const medicine = medRes.data;

    // Remove any existing modal
    closeOrderModal();

    // Create modal DOM container
    const backdrop = document.createElement('div');
    backdrop.id = 'medifind-order-modal';
    backdrop.style.cssText = `
        position: fixed;
        inset: 0;
        z-index: 100000;
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        overflow-y: auto;
    `;

    backdrop.innerHTML = `
        <div style="background:#ffffff;border-radius:18px;max-width:620px;width:100%;max-height:92vh;display:flex;flex-direction:column;box-shadow:0 25px 50px -12px rgba(0,0,0,0.25);overflow:hidden;animation:mfFadeIn 0.2s ease;">
            <!-- Modal Header -->
            <div style="padding:22px 26px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;background:#f8fafc;">
                <div>
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <span style="font-size:0.75rem;padding:3px 9px;border-radius:999px;font-weight:700;${medicine.requires_prescription ? 'background:#fee2e2;color:#991b1b;' : 'background:#dcfce7;color:#166534;'}">
                            ${medicine.requires_prescription ? '⚠️ Doctor Prescription Required' : '✓ OTC - No Prescription Required'}
                        </span>
                        <span style="font-size:0.75rem;background:#e0f2fe;color:#0369a1;padding:3px 9px;border-radius:999px;font-weight:600;">
                            ${escapeHtml(medicine.dosage_form || 'Form')} &bull; ${escapeHtml(medicine.strength || '')}
                        </span>
                    </div>
                    <h2 style="margin:0;font-family:'Space Grotesk',sans-serif;font-size:1.45rem;color:#0f172a;">
                        ${escapeHtml(medicine.name)}
                    </h2>
                    <p style="margin:4px 0 0 0;font-size:0.85rem;color:#64748b;font-family:'Plus Jakarta Sans',sans-serif;">
                        Generic: ${escapeHtml(medicine.generic_name || medicine.name)}
                    </p>
                </div>
                <button id="mf-close-modal-btn" style="background:transparent;border:none;font-size:1.6rem;cursor:pointer;color:#64748b;line-height:1;">&times;</button>
            </div>

            <!-- Modal Body -->
            <div style="padding:22px 26px;overflow-y:auto;flex:1;font-family:'Plus Jakarta Sans',sans-serif;">
                
                <!-- Prescription Upload (if required) -->
                ${medicine.requires_prescription ? `
                    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:16px;margin-bottom:20px;">
                        <label style="display:block;font-weight:700;color:#92400e;margin-bottom:6px;font-size:0.9rem;">
                            📑 Upload Doctor Prescription *
                        </label>
                        <p style="margin:0 0 10px 0;font-size:0.82rem;color:#78350f;">
                            This is a prescription-controlled medicine. An uploaded file (PDF, JPG, PNG up to 5MB) is mandatory. The pharmacy owner will review this prescription before fulfilling your order.
                        </p>
                        <input type="file" id="mf-prescription-file" accept=".pdf,image/png,image/jpeg,image/jpg" style="font-size:0.85rem;width:100%;">
                    </div>
                ` : ''}

                <!-- Fulfillment Method Choice -->
                <div style="margin-bottom:20px;">
                    <label style="display:block;font-weight:700;color:#0f172a;margin-bottom:10px;font-size:0.92rem;">
                        Select Fulfillment Method:
                    </label>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <label id="mf-method-pickup-label" style="border:2px solid #0284c7;background:#f0f9ff;border-radius:12px;padding:14px;cursor:pointer;display:flex;align-items:center;gap:10px;transition:all 0.2s;">
                            <input type="radio" name="mf-fulfillment" value="PICKUP" checked style="accent-color:#0284c7;">
                            <div>
                                <div style="font-weight:700;font-size:0.95rem;color:#0f172a;">🏪 Store Pickup</div>
                                <div style="font-size:0.8rem;color:#64748b;">Pay Cash on Pickup</div>
                            </div>
                        </label>
                        <label id="mf-method-delivery-label" style="border:2px solid #e2e8f0;background:#ffffff;border-radius:12px;padding:14px;cursor:pointer;display:flex;align-items:center;gap:10px;transition:all 0.2s;">
                            <input type="radio" name="mf-fulfillment" value="DELIVERY" style="accent-color:#0284c7;">
                            <div>
                                <div style="font-weight:700;font-size:0.95rem;color:#0f172a;">🚚 Home Delivery</div>
                                <div style="font-size:0.8rem;color:#64748b;">Pay Cash on Delivery</div>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- Available Pharmacies -->
                <div style="margin-bottom:20px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <label style="font-weight:700;color:#0f172a;font-size:0.92rem;">
                            Choose Verified Pharmacy:
                        </label>
                        <span id="mf-pharmacy-status" style="font-size:0.8rem;color:#64748b;">Loading stock...</span>
                    </div>
                    <div id="mf-pharmacies-list" style="display:flex;flex-direction:column;gap:10px;max-height:210px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:12px;padding:10px;background:#fafafa;">
                        <!-- Injected dynamically -->
                    </div>
                </div>

                <!-- Quantity and Subtotal -->
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;">
                        <div>
                            <label style="display:block;font-weight:700;color:#0f172a;font-size:0.88rem;margin-bottom:4px;">
                                Order Quantity:
                            </label>
                            <div style="display:flex;align-items:center;gap:6px;">
                                <button type="button" id="mf-qty-dec" style="width:34px;height:34px;border:1px solid #cbd5e1;background:#fff;border-radius:8px;font-weight:700;cursor:pointer;">-</button>
                                <input type="number" id="mf-qty-input" value="1" min="1" max="99" style="width:65px;height:34px;text-align:center;border:1px solid #cbd5e1;border-radius:8px;font-weight:700;font-size:0.95rem;">
                                <button type="button" id="mf-qty-inc" style="width:34px;height:34px;border:1px solid #cbd5e1;background:#fff;border-radius:8px;font-weight:700;cursor:pointer;">+</button>
                            </div>
                        </div>

                        <div style="text-align:right;">
                            <div style="font-size:0.82rem;color:#64748b;">Unit Price: <span id="mf-unit-price-display">₹0.00</span></div>
                            <div style="font-size:1.2rem;font-weight:800;color:#0284c7;font-family:'Space Grotesk',sans-serif;margin-top:2px;">
                                Total: <span id="mf-total-price-display">₹0.00</span>
                            </div>
                            <div style="font-size:0.75rem;color:#16a34a;font-weight:600;">(Payment: CASH only)</div>
                        </div>
                    </div>
                </div>

                <!-- Delivery Address (if Delivery selected) -->
                <div id="mf-delivery-address-container" style="display:none;margin-bottom:16px;">
                    <label style="display:block;font-weight:700;color:#0f172a;margin-bottom:6px;font-size:0.88rem;">
                        Delivery Address *
                    </label>
                    <textarea id="mf-delivery-address" rows="2" placeholder="House/Flat No., Street, Area, City, Pincode" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.88rem;"></textarea>
                </div>

                <!-- Optional Order Notes -->
                <div style="margin-bottom:8px;">
                    <label style="display:block;font-weight:600;color:#64748b;margin-bottom:4px;font-size:0.8rem;">
                        Order Notes (Optional):
                    </label>
                    <input type="text" id="mf-order-notes" placeholder="e.g. Call before delivery, urgent requirement" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:0.85rem;">
                </div>

            </div>

            <!-- Modal Footer -->
            <div style="padding:16px 26px;border-top:1px solid #e2e8f0;background:#f8fafc;display:flex;justify-content:flex-end;gap:12px;">
                <button type="button" id="mf-cancel-btn" style="background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:10px 18px;border-radius:10px;font-weight:600;cursor:pointer;font-size:0.9rem;">
                    Cancel
                </button>
                <button type="button" id="mf-submit-order-btn" style="background:#0284c7;color:#ffffff;border:none;padding:10px 24px;border-radius:10px;font-weight:700;cursor:pointer;font-size:0.92rem;box-shadow:0 4px 12px rgba(2,132,199,0.25);">
                    Place Cash Order
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(backdrop);
    activeOrderModal = backdrop;

    // State
    let currentMethod = 'PICKUP';
    let availablePharmacies = [];
    let selectedPharmacy = null;

    // Element bindings
    const closeBtn = document.getElementById('mf-close-modal-btn');
    const cancelBtn = document.getElementById('mf-cancel-btn');
    const submitBtn = document.getElementById('mf-submit-order-btn');
    const qtyInput = document.getElementById('mf-qty-input');
    const qtyInc = document.getElementById('mf-qty-inc');
    const qtyDec = document.getElementById('mf-qty-dec');
    const unitPriceEl = document.getElementById('mf-unit-price-display');
    const totalPriceEl = document.getElementById('mf-total-price-display');
    const addressContainer = document.getElementById('mf-delivery-address-container');
    const addressInput = document.getElementById('mf-delivery-address');
    const notesInput = document.getElementById('mf-order-notes');
    const prescriptionInput = document.getElementById('mf-prescription-file');
    const pickupRadio = document.querySelector('input[name="mf-fulfillment"][value="PICKUP"]');
    const deliveryRadio = document.querySelector('input[name="mf-fulfillment"][value="DELIVERY"]');
    const pickupLabel = document.getElementById('mf-method-pickup-label');
    const deliveryLabel = document.getElementById('mf-method-delivery-label');

    closeBtn.onclick = closeOrderModal;
    cancelBtn.onclick = closeOrderModal;

    // Fulfillment toggle listeners
    pickupRadio.addEventListener('change', () => {
        currentMethod = 'PICKUP';
        pickupLabel.style.borderColor = '#0284c7';
        pickupLabel.style.background = '#f0f9ff';
        deliveryLabel.style.borderColor = '#e2e8f0';
        deliveryLabel.style.background = '#ffffff';
        addressContainer.style.display = 'none';
        loadPharmacies();
    });

    deliveryRadio.addEventListener('change', () => {
        currentMethod = 'DELIVERY';
        deliveryLabel.style.borderColor = '#0284c7';
        deliveryLabel.style.background = '#f0f9ff';
        pickupLabel.style.borderColor = '#e2e8f0';
        pickupLabel.style.background = '#ffffff';
        addressContainer.style.display = 'block';
        loadPharmacies();
    });

    // Quantity controls
    qtyInc.onclick = () => {
        let max = selectedPharmacy ? selectedPharmacy.quantity : 99;
        let v = parseInt(qtyInput.value, 10) || 1;
        if (v < max) {
            qtyInput.value = v + 1;
            updateTotals();
        } else {
            showToast(`Maximum available stock is ${max} units.`, 'warning');
        }
    };

    qtyDec.onclick = () => {
        let v = parseInt(qtyInput.value, 10) || 1;
        if (v > 1) {
            qtyInput.value = v - 1;
            updateTotals();
        }
    };

    qtyInput.oninput = () => {
        let v = parseInt(qtyInput.value, 10);
        if (isNaN(v) || v < 1) qtyInput.value = 1;
        if (selectedPharmacy && v > selectedPharmacy.quantity) {
            qtyInput.value = selectedPharmacy.quantity;
            showToast(`Maximum available stock is ${selectedPharmacy.quantity} units.`, 'warning');
        }
        updateTotals();
    };

    function updateTotals() {
        if (!selectedPharmacy) {
            unitPriceEl.textContent = '₹0.00';
            totalPriceEl.textContent = '₹0.00';
            return;
        }
        const qty = parseInt(qtyInput.value, 10) || 1;
        const unit = selectedPharmacy.price;
        const total = qty * unit;
        unitPriceEl.textContent = `₹${unit.toFixed(2)}`;
        totalPriceEl.textContent = `₹${total.toFixed(2)}`;
    }

    async function loadPharmacies() {
        const listEl = document.getElementById('mf-pharmacies-list');
        const statusEl = document.getElementById('mf-pharmacy-status');
        listEl.innerHTML = '<div style="padding:12px;text-align:center;color:#64748b;font-size:0.85rem;">Searching stock in verified pharmacies...</div>';
        statusEl.textContent = 'Checking...';

        const res = await apiFetch(`/api/medicines/${medicine.id}/pharmacies?method=${currentMethod.toLowerCase()}`);
        if (res.ok && res.data && res.data.pharmacies && res.data.pharmacies.length > 0) {
            availablePharmacies = res.data.pharmacies;
            statusEl.textContent = `${availablePharmacies.length} verified store(s) available`;

            // Default select the first pharmacy
            selectedPharmacy = availablePharmacies[0];

            listEl.innerHTML = availablePharmacies.map((p, idx) => `
                <div class="mf-pharma-item" data-id="${p.id}" style="padding:10px 14px;border:1px solid ${idx === 0 ? '#0284c7' : '#e2e8f0'};background:${idx === 0 ? '#f0f9ff' : '#ffffff'};border-radius:10px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;transition:all 0.15s ease;">
                    <div>
                        <div style="font-weight:700;font-size:0.92rem;color:#0f172a;display:flex;align-items:center;gap:6px;">
                            🏥 ${escapeHtml(p.name)}
                            <span style="font-size:0.7rem;background:#dcfce7;color:#166534;padding:2px 6px;border-radius:999px;">Verified</span>
                        </div>
                        <div style="font-size:0.8rem;color:#64748b;margin-top:2px;">
                            📍 ${escapeHtml(p.address)}, ${escapeHtml(p.city)} (${p.pincode})
                        </div>
                        <div style="font-size:0.78rem;color:#0284c7;font-weight:600;margin-top:2px;">
                            ${p.distance_km !== null ? `🚗 ${p.distance_km.toFixed(1)} km away &bull; ` : ''}${p.quantity} units available
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-weight:800;font-size:1.05rem;color:#0f172a;font-family:'Space Grotesk',sans-serif;">
                            ₹${p.price.toFixed(2)}
                        </div>
                        <div style="font-size:0.75rem;color:#64748b;">per unit</div>
                    </div>
                </div>
            `).join('');

            // Click listener for items
            listEl.querySelectorAll('.mf-pharma-item').forEach(item => {
                item.onclick = () => {
                    const id = parseInt(item.getAttribute('data-id'), 10);
                    selectedPharmacy = availablePharmacies.find(p => p.id === id);
                    listEl.querySelectorAll('.mf-pharma-item').forEach(i => {
                        i.style.borderColor = '#e2e8f0';
                        i.style.background = '#ffffff';
                    });
                    item.style.borderColor = '#0284c7';
                    item.style.background = '#f0f9ff';
                    updateTotals();
                };
            });

            updateTotals();
        } else {
            availablePharmacies = [];
            selectedPharmacy = null;
            statusEl.textContent = '0 stores';
            listEl.innerHTML = `
                <div style="padding:16px;text-align:center;color:#b91c1c;font-size:0.85rem;background:#fef2f2;border-radius:8px;">
                    No verified pharmacies currently have stock for <strong>${currentMethod}</strong>. Try switching between Pickup and Delivery.
                </div>
            `;
            updateTotals();
        }
    }

    // Submit Order handler
    submitBtn.onclick = async () => {
        if (!selectedPharmacy) {
            showToast('Please select a pharmacy with available stock.', 'warning');
            return;
        }

        const qty = parseInt(qtyInput.value, 10);
        if (!qty || qty <= 0) {
            showToast('Please enter a valid quantity.', 'warning');
            return;
        }

        if (qty > selectedPharmacy.quantity) {
            showToast(`Selected quantity exceeds available stock (${selectedPharmacy.quantity} units).`, 'error');
            return;
        }

        if (currentMethod === 'DELIVERY' && (!addressInput || !addressInput.value.trim())) {
            showToast('Please enter your complete delivery address.', 'warning');
            addressInput?.focus();
            return;
        }

        if (medicine.requires_prescription) {
            if (!prescriptionInput || !prescriptionInput.files || prescriptionInput.files.length === 0) {
                showToast('Doctor prescription file is mandatory for this medicine.', 'error');
                prescriptionInput?.focus();
                return;
            }
        }

        // Prepare multipart form data
        const formData = new FormData();
        formData.append('pharmacy_id', selectedPharmacy.id);
        formData.append('fulfillment_type', currentMethod);
        formData.append('payment_method', 'CASH');
        formData.append('delivery_address', currentMethod === 'DELIVERY' ? addressInput.value.trim() : '');
        formData.append('notes', notesInput ? notesInput.value.trim() : '');
        formData.append('items', JSON.stringify([
            { medicine_id: medicine.id, quantity: qty }
        ]));

        if (medicine.requires_prescription && prescriptionInput.files.length > 0) {
            formData.append('prescription', prescriptionInput.files[0]);
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting Order...';

        try {
            const res = await apiFetch('/api/orders', {
                method: 'POST',
                body: formData
            });

            if (res.ok && res.data) {
                closeOrderModal();
                showOrderSuccessModal(res.data);
            } else {
                showToast(res.message || 'Failed to place order.', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Place Cash Order';
            }
        } catch (err) {
            console.error('Order submit error:', err);
            showToast('An unexpected error occurred.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Place Cash Order';
        }
    };

    // Load pharmacies for default method
    loadPharmacies();
}

function closeOrderModal() {
    if (activeOrderModal) {
        activeOrderModal.remove();
        activeOrderModal = null;
    }
}

function showOrderSuccessModal(order) {
    const backdrop = document.createElement('div');
    backdrop.style.cssText = `
        position: fixed;
        inset: 0;
        z-index: 100000;
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    `;

    backdrop.innerHTML = `
        <div style="background:#ffffff;border-radius:20px;max-width:500px;width:100%;padding:32px 28px;text-align:center;box-shadow:0 25px 50px rgba(0,0,0,0.25);font-family:'Plus Jakarta Sans',sans-serif;">
            <div style="width:68px;height:68px;border-radius:50%;background:#dcfce7;color:#16a34a;font-size:32px;display:flex;align-items:center;justify-content:center;margin:0 auto 18px auto;">
                ✓
            </div>
            <h2 style="font-family:'Space Grotesk',sans-serif;font-size:1.6rem;color:#0f172a;margin:0 0 8px 0;">
                Order Placed Successfully!
            </h2>
            <div style="display:inline-block;background:#f1f5f9;color:#0f172a;padding:5px 14px;border-radius:999px;font-weight:700;font-size:0.9rem;margin-bottom:14px;">
                Order #${order.id}
            </div>
            <p style="color:#047857;font-weight:700;font-size:1.05rem;margin:0 0 16px 0;">
                "Your order has been placed."
            </p>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;text-align:left;font-size:0.88rem;color:#475569;margin-bottom:24px;">
                <div><strong>Pharmacy:</strong> ${escapeHtml(order.pharmacy?.name || 'Selected Pharmacy')}</div>
                <div style="margin-top:4px;"><strong>Type:</strong> ${order.fulfillment_type === 'DELIVERY' ? '🚚 Home Delivery' : '🏪 Store Pickup'}</div>
                <div style="margin-top:4px;"><strong>Payment:</strong> Cash (${order.payment_status || 'PENDING'})</div>
                <div style="margin-top:4px;font-weight:700;color:#0f172a;"><strong>Total Amount:</strong> ₹${parseFloat(order.total_amount).toFixed(2)}</div>
            </div>
            <div style="display:flex;gap:12px;justify-content:center;">
                <button id="mf-done-btn" style="background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:12px 20px;border-radius:10px;font-weight:600;cursor:pointer;">
                    Close
                </button>
                <a href="orders.html?id=${order.id}" style="background:#0284c7;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:10px;font-weight:700;display:inline-block;">
                    Track Live Status →
                </a>
            </div>
        </div>
    `;

    document.body.appendChild(backdrop);
    document.getElementById('mf-done-btn').onclick = () => backdrop.remove();
}
