// ==========================================
// MediFind - Pharmacy Owner Dashboard Logic
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireRole(['PHARMACY_OWNER'])) return;

    let pharmacyProfile = null;
    let allOrders = [];
    let currentFilter = 'ALL';
    let inventoryData = [];

    // Elements
    const storeNameEl = document.getElementById('pharma-store-name');
    const badgeStatusEl = document.getElementById('pharma-badge-status');
    const badgeLicenseEl = document.getElementById('pharma-badge-license');
    const addressEl = document.getElementById('pharma-address');
    const phoneEl = document.getElementById('pharma-phone');
    const ownerNameEl = document.getElementById('pharma-owner-name');

    const tabOrdersBtn = document.getElementById('tab-orders-btn');
    const tabInventoryBtn = document.getElementById('tab-inventory-btn');
    const tabOrdersContent = document.getElementById('tab-orders-content');
    const tabInventoryContent = document.getElementById('tab-inventory-content');

    const ordersBadgeCount = document.getElementById('orders-badge-count');
    const inventoryBadgeCount = document.getElementById('inventory-badge-count');
    const ordersContainer = document.getElementById('orders-list-container');
    const inventoryTableBody = document.getElementById('inventory-table-body');
    const refreshBtn = document.getElementById('refresh-dashboard-btn');

    // Add stock modal elements
    const addStockModal = document.getElementById('add-stock-modal');
    const openAddStockBtn = document.getElementById('open-add-stock-modal');
    const closeAddStockBtn = document.getElementById('close-add-stock-modal');
    const cancelAddStockBtn = document.getElementById('cancel-add-stock-btn');
    const addStockForm = document.getElementById('add-stock-form');
    const medSelect = document.getElementById('modal-medicine-select');

    // Setup Tab Switching
    tabOrdersBtn.onclick = () => {
        tabOrdersBtn.classList.add('active');
        tabInventoryBtn.classList.remove('active');
        tabOrdersContent.classList.add('active');
        tabInventoryContent.classList.remove('active');
    };

    tabInventoryBtn.onclick = () => {
        tabInventoryBtn.classList.add('active');
        tabOrdersBtn.classList.remove('active');
        tabInventoryContent.classList.add('active');
        tabOrdersContent.classList.remove('active');
    };

    // Filter Buttons
    document.querySelectorAll('.filter-order-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.filter-order-btn').forEach(b => {
                b.style.borderColor = '#cbd5e1';
                b.style.background = '#ffffff';
                b.style.color = '#475569';
                b.style.fontWeight = '600';
            });
            btn.style.borderColor = '#0284c7';
            btn.style.background = '#f0f9ff';
            btn.style.color = '#0284c7';
            btn.style.fontWeight = '700';

            currentFilter = btn.getAttribute('data-filter');
            renderOrders();
        };
    });

    // Refresh Handler
    refreshBtn.onclick = async () => {
        showToast('Refreshing dashboard...', 'info');
        await loadPharmacyProfile();
        await loadOrders();
        await loadInventory();
    };

    // Modal controls
    openAddStockBtn.onclick = async () => {
        addStockModal.style.display = 'flex';
        await loadCatalogOptions();
    };
    closeAddStockBtn.onclick = () => addStockModal.style.display = 'none';
    cancelAddStockBtn.onclick = () => addStockModal.style.display = 'none';

    // Initial load
    await loadPharmacyProfile();
    await loadOrders();
    await loadInventory();

    // 1. Load Profile
    async function loadPharmacyProfile() {
        const res = await apiFetch('/api/pharmacy/profile');
        if (res.ok && res.data) {
            pharmacyProfile = res.data;
            storeNameEl.textContent = pharmacyProfile.name;
            badgeLicenseEl.textContent = `License: ${pharmacyProfile.license_number || 'Not Recorded'}`;
            addressEl.textContent = `📍 ${pharmacyProfile.address}, ${pharmacyProfile.city} (${pharmacyProfile.pincode})`;
            phoneEl.textContent = `📞 ${pharmacyProfile.phone || 'No phone'}`;
            ownerNameEl.textContent = `👤 Owner: ${pharmacyProfile.owner?.name || 'Authorized Owner'}`;

            if (pharmacyProfile.verification_status === 'APPROVED') {
                badgeStatusEl.style.background = '#dcfce7';
                badgeStatusEl.style.color = '#15803d';
                badgeStatusEl.textContent = '✓ VERIFIED & ACTIVE';
            } else if (pharmacyProfile.verification_status === 'PENDING') {
                badgeStatusEl.style.background = '#fef3c7';
                badgeStatusEl.style.color = '#92400e';
                badgeStatusEl.textContent = '⏳ PENDING ADMIN VERIFICATION';
                showToast('Your pharmacy registration is pending admin approval. It will appear to customers once approved.', 'warning');
            } else {
                badgeStatusEl.style.background = '#fee2e2';
                badgeStatusEl.style.color = '#b91c1c';
                badgeStatusEl.textContent = '❌ REJECTED';
            }
        } else {
            showToast('Unable to load pharmacy profile.', 'error');
        }
    }

    // 2. Load Orders
    async function loadOrders() {
        const res = await apiFetch('/api/pharmacy/orders');
        if (res.ok && res.data && Array.isArray(res.data.orders)) {
            allOrders = res.data.orders;
            ordersBadgeCount.textContent = allOrders.length;
            renderOrders();
        } else {
            ordersContainer.innerHTML = '<div style="padding:30px;text-align:center;color:#ef4444;">Failed to load orders.</div>';
        }
    }

    function renderOrders() {
        let filtered = allOrders;
        if (currentFilter === 'PLACED') {
            filtered = allOrders.filter(o => o.status === 'PLACED');
        } else if (currentFilter === 'ACTIVE') {
            filtered = allOrders.filter(o => ['ACCEPTED', 'PREPARING', 'READY_FOR_PICKUP', 'OUT_FOR_DELIVERY'].includes(o.status));
        } else if (currentFilter === 'COMPLETED') {
            filtered = allOrders.filter(o => o.status === 'COMPLETED');
        }

        if (filtered.length === 0) {
            ordersContainer.innerHTML = `
                <div style="text-align:center;padding:50px 20px;background:#fff;border-radius:16px;border:1px dashed #cbd5e1;color:#64748b;">
                    <h3 style="color:#0f172a;margin-bottom:6px;">No orders found</h3>
                    <p style="margin:0;">There are currently no orders in this category.</p>
                </div>
            `;
            return;
        }

        ordersContainer.innerHTML = filtered.map(order => {
            const isDelivery = order.fulfillment_type === 'DELIVERY';
            const hasPrescription = order.has_prescription;
            const rxStatus = order.prescription_status;
            const canAccept = !hasPrescription || rxStatus === 'APPROVED';

            return `
                <div class="owner-order-card" id="owner-order-${order.id}">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #f1f5f9;">
                        <div>
                            <div style="display:flex;align-items:center;gap:10px;">
                                <h3 style="margin:0;font-size:1.15rem;color:#0f172a;font-family:'Space Grotesk',sans-serif;">
                                    Order #${order.id}
                                </h3>
                                <span style="font-size:0.75rem;padding:3px 9px;border-radius:999px;font-weight:700;${getStatusStyle(order.status)}">
                                    ${order.status.replace(/_/g, ' ')}
                                </span>
                                <span style="font-size:0.75rem;background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:6px;font-weight:600;">
                                    ${isDelivery ? '🚚 Home Delivery' : '🏪 Store Pickup'}
                                </span>
                            </div>
                            <div style="font-size:0.85rem;color:#64748b;margin-top:4px;">
                                Placed by <strong>${escapeHtml(order.customer?.name || 'Customer')}</strong> &bull; 📞 ${escapeHtml(order.customer?.phone || 'No phone')} &bull; ${new Date(order.created_at).toLocaleString()}
                            </div>
                        </div>

                        <div style="text-align:right;">
                            <div style="font-size:1.3rem;font-weight:800;color:#0284c7;font-family:'Space Grotesk',sans-serif;">
                                ₹${parseFloat(order.total_amount).toFixed(2)}
                            </div>
                            <span style="font-size:0.75rem;padding:2px 8px;border-radius:999px;font-weight:600;background:${order.payment_status === 'PAID' ? '#dcfce7;color:#166534;' : '#fef3c7;color:#92400e;'}">
                                Cash (${order.payment_status || 'PENDING'})
                            </span>
                        </div>
                    </div>

                    <!-- Items Summary -->
                    <div style="margin-bottom:14px;background:#f8fafc;padding:12px 16px;border-radius:10px;font-size:0.88rem;">
                        <div style="font-weight:700;color:#0f172a;margin-bottom:6px;">Items in Order:</div>
                        <div style="display:flex;flex-direction:column;gap:6px;">
                            ${order.items.map(item => `
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <div>
                                        <strong>${escapeHtml(item.medicine_name)}</strong>
                                        <span style="color:#64748b;font-size:0.8rem;margin-left:6px;">(${item.dosage_form || ''} ${item.strength || ''})</span>
                                        ${item.requires_prescription ? '<span style="color:#b91c1c;font-size:0.75rem;font-weight:700;margin-left:4px;">[Rx Required]</span>' : ''}
                                    </div>
                                    <div>
                                        Qty: <strong>${item.quantity}</strong> &times; ₹${item.unit_price} = <strong>₹${item.subtotal}</strong>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        ${isDelivery && order.delivery_address ? `
                            <div style="margin-top:10px;padding-top:8px;border-top:1px dashed #cbd5e1;font-size:0.85rem;color:#475569;">
                                📍 <strong>Delivery Address:</strong> ${escapeHtml(order.delivery_address)}
                            </div>
                        ` : ''}
                    </div>

                    <!-- Prescription Verification Area -->
                    ${hasPrescription ? `
                        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px 16px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                            <div>
                                <div style="font-weight:700;color:#92400e;font-size:0.88rem;display:flex;align-items:center;gap:6px;">
                                    📑 Customer Prescription Uploaded
                                    <span style="font-size:0.75rem;padding:2px 8px;border-radius:999px;font-weight:700;${rxStatus === 'APPROVED' ? 'background:#dcfce7;color:#166534;' : (rxStatus === 'REJECTED' ? 'background:#fee2e2;color:#991b1b;' : 'background:#fef3c7;color:#92400e;')}">
                                        Status: ${rxStatus || 'PENDING'}
                                    </span>
                                </div>
                                <div style="font-size:0.8rem;color:#78350f;margin-top:2px;">
                                    Verify doctor stamp, signature, and dosage before approving.
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;">
                                <button type="button" class="action-btn secondary btn-view-rx" data-order-id="${order.id}">
                                    👁️ View Prescription
                                </button>
                                ${rxStatus === 'PENDING' ? `
                                    <button type="button" class="action-btn accept btn-approve-rx" data-order-id="${order.id}">
                                        ✓ Approve Rx
                                    </button>
                                    <button type="button" class="action-btn reject btn-reject-rx" data-order-id="${order.id}">
                                        ✕ Reject Rx
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Status Transition Controls -->
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;padding-top:10px;">
                        <div style="font-size:0.85rem;color:#64748b;">
                            Current Customer Message: <em>"${escapeHtml(order.status_message || '')}"</em>
                        </div>
                        <div style="display:flex;gap:10px;align-items:center;">
                            ${renderOrderActionButtons(order, canAccept)}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        wireOrderButtons();
    }

    function renderOrderActionButtons(order, canAccept) {
        const s = order.status;
        const isDelivery = order.fulfillment_type === 'DELIVERY';

        if (s === 'PLACED') {
            return `
                ${!canAccept ? '<span style="font-size:0.8rem;color:#b45309;font-weight:600;">⚠️ Review & approve Rx before accepting</span>' : ''}
                <button type="button" class="action-btn accept btn-accept-order" data-order-id="${order.id}" ${!canAccept ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>
                    ✓ Accept Order
                </button>
                <button type="button" class="action-btn reject btn-reject-order" data-order-id="${order.id}">
                    ✕ Reject Order
                </button>
            `;
        }

        if (s === 'ACCEPTED') {
            return `
                <button type="button" class="action-btn advance btn-advance-order" data-order-id="${order.id}" data-target-status="PREPARING">
                    📦 Mark Preparing
                </button>
            `;
        }

        if (s === 'PREPARING') {
            if (isDelivery) {
                return `
                    <button type="button" class="action-btn advance btn-advance-order" data-order-id="${order.id}" data-target-status="OUT_FOR_DELIVERY">
                        🚚 Mark Out for Delivery
                    </button>
                `;
            } else {
                return `
                    <button type="button" class="action-btn advance btn-advance-order" data-order-id="${order.id}" data-target-status="READY_FOR_PICKUP">
                        🏪 Mark Ready for Pickup
                    </button>
                `;
            }
        }

        if (s === 'READY_FOR_PICKUP' || s === 'OUT_FOR_DELIVERY') {
            return `
                <button type="button" class="action-btn accept btn-advance-order" data-order-id="${order.id}" data-target-status="COMPLETED">
                    ✅ Complete Order & Collect Cash
                </button>
            `;
        }

        if (s === 'COMPLETED') {
            return '<span style="font-size:0.85rem;color:#16a34a;font-weight:700;">✓ Completed & Paid</span>';
        }

        if (s === 'REJECTED') {
            return '<span style="font-size:0.85rem;color:#dc2626;font-weight:700;">✕ Order Rejected</span>';
        }

        return '';
    }

    function wireOrderButtons() {
        // View Prescription button
        ordersContainer.querySelectorAll('.btn-view-rx').forEach(btn => {
            btn.onclick = async () => {
                const id = btn.getAttribute('data-order-id');
                btn.disabled = true;
                btn.textContent = 'Opening...';
                await viewPrescriptionFile(id);
                btn.disabled = false;
                btn.textContent = '👁️ View Prescription';
            };
        });

        // Approve Prescription button
        ordersContainer.querySelectorAll('.btn-approve-rx').forEach(btn => {
            btn.onclick = async () => {
                const id = btn.getAttribute('data-order-id');
                btn.disabled = true;
                const res = await apiFetch(`/api/pharmacy/orders/${id}/prescription`, {
                    method: 'PATCH',
                    body: JSON.stringify({ status: 'APPROVED' })
                });
                if (res.ok) {
                    showToast('Prescription approved! You can now accept the order.', 'success');
                    await loadOrders();
                } else {
                    showToast(res.message || 'Failed to approve prescription.', 'error');
                    btn.disabled = false;
                }
            };
        });

        // Reject Prescription button
        ordersContainer.querySelectorAll('.btn-reject-rx').forEach(btn => {
            btn.onclick = async () => {
                if (!confirm('Rejecting the prescription will automatically reject this order. Continue?')) return;
                const id = btn.getAttribute('data-order-id');
                btn.disabled = true;
                const res = await apiFetch(`/api/pharmacy/orders/${id}/prescription`, {
                    method: 'PATCH',
                    body: JSON.stringify({ status: 'REJECTED' })
                });
                if (res.ok) {
                    showToast('Prescription rejected. Order marked as REJECTED.', 'info');
                    await loadOrders();
                } else {
                    showToast(res.message || 'Failed to reject prescription.', 'error');
                    btn.disabled = false;
                }
            };
        });

        // Accept Order button
        ordersContainer.querySelectorAll('.btn-accept-order').forEach(btn => {
            btn.onclick = async () => {
                const id = btn.getAttribute('data-order-id');
                btn.disabled = true;
                btn.textContent = 'Verifying Stock...';

                const res = await apiFetch(`/api/pharmacy/orders/${id}/status`, {
                    method: 'PATCH',
                    body: JSON.stringify({ status: 'ACCEPTED' })
                });

                if (res.ok) {
                    showToast(`Order #${id} confirmed and stock deducted.`, 'success');
                    await loadOrders();
                    await loadInventory();
                } else {
                    if (res.status === 409) {
                        showToast(`Stock Conflict: ${res.message}`, 'error');
                    } else {
                        showToast(res.message || 'Failed to accept order.', 'error');
                    }
                    btn.disabled = false;
                    btn.textContent = '✓ Accept Order';
                }
            };
        });

        // Reject Order button
        ordersContainer.querySelectorAll('.btn-reject-order').forEach(btn => {
            btn.onclick = async () => {
                if (!confirm('Are you sure you want to decline this order?')) return;
                const id = btn.getAttribute('data-order-id');
                btn.disabled = true;
                const res = await apiFetch(`/api/pharmacy/orders/${id}/status`, {
                    method: 'PATCH',
                    body: JSON.stringify({ status: 'REJECTED' })
                });
                if (res.ok) {
                    showToast(`Order #${id} rejected. Customer notified.`, 'info');
                    await loadOrders();
                } else {
                    showToast(res.message || 'Failed to reject order.', 'error');
                    btn.disabled = false;
                }
            };
        });

        // Advance Status button
        ordersContainer.querySelectorAll('.btn-advance-order').forEach(btn => {
            btn.onclick = async () => {
                const id = btn.getAttribute('data-order-id');
                const targetStatus = btn.getAttribute('data-target-status');
                btn.disabled = true;

                const res = await apiFetch(`/api/pharmacy/orders/${id}/status`, {
                    method: 'PATCH',
                    body: JSON.stringify({ status: targetStatus })
                });

                if (res.ok) {
                    showToast(`Order #${id} status updated to ${targetStatus.replace(/_/g, ' ')}.`, 'success');
                    await loadOrders();
                } else {
                    showToast(res.message || 'Status transition failed.', 'error');
                    btn.disabled = false;
                }
            };
        });
    }

    async function viewPrescriptionFile(orderId) {
        const token = getToken();
        const url = `${API_BASE}/api/pharmacy/orders/${orderId}/prescription`;

        try {
            const resp = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!resp.ok) {
                showToast('Unable to view prescription file.', 'error');
                return;
            }

            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(blob);
            window.open(blobUrl, '_blank');
        } catch (err) {
            console.error('Prescription download error:', err);
            showToast('Failed to load prescription file.', 'error');
        }
    }

    // 3. Load Inventory
    async function loadInventory() {
        const res = await apiFetch('/api/pharmacy/inventory');
        if (res.ok && res.data && Array.isArray(res.data.inventory)) {
            inventoryData = res.data.inventory;
            inventoryBadgeCount.textContent = inventoryData.length;
            renderInventoryTable();
        } else {
            inventoryTableBody.innerHTML = '<tr><td colspan="6" style="padding:30px;text-align:center;color:#ef4444;">Failed to load inventory.</td></tr>';
        }
    }

    function renderInventoryTable() {
        if (inventoryData.length === 0) {
            inventoryTableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="padding:40px;text-align:center;color:#64748b;">
                        No medicines currently stocked. Click "+ Add Medicine to Inventory" above to stock items from the catalog.
                    </td>
                </tr>
            `;
            return;
        }

        inventoryTableBody.innerHTML = inventoryData.map(item => {
            const m = item.medicine || {};
            const inStock = item.quantity > 0;

            return `
                <tr style="border-bottom:1px solid #f1f5f9;">
                    <td style="padding:14px 18px;">
                        <strong style="color:#0f172a;font-size:0.95rem;">${escapeHtml(m.name || 'Medicine')}</strong>
                        <div style="font-size:0.78rem;color:#64748b;">${escapeHtml(m.generic_name || '')} &bull; ${escapeHtml(m.dosage_form || '')} ${escapeHtml(m.strength || '')}</div>
                    </td>
                    <td style="padding:14px 18px;">
                        <span style="font-size:0.75rem;padding:3px 8px;border-radius:999px;font-weight:700;${m.requires_prescription ? 'background:#fee2e2;color:#991b1b;' : 'background:#dcfce7;color:#166534;'}">
                            ${m.requires_prescription ? 'Rx Required' : 'OTC'}
                        </span>
                    </td>
                    <td style="padding:14px 18px;font-weight:700;font-size:0.95rem;color:${inStock ? '#0f172a' : '#dc2626'};">
                        ${item.quantity} units
                    </td>
                    <td style="padding:14px 18px;font-weight:700;font-family:'Space Grotesk',sans-serif;font-size:1rem;color:#0284c7;">
                        ₹${parseFloat(item.price).toFixed(2)}
                    </td>
                    <td style="padding:14px 18px;">
                        <span style="font-size:0.75rem;padding:3px 8px;border-radius:999px;font-weight:600;background:${inStock ? '#dcfce7;color:#15803d;' : '#fee2e2;color:#b91c1c;'}">
                            ${inStock ? 'IN STOCK' : 'OUT OF STOCK'}
                        </span>
                    </td>
                    <td style="padding:14px 18px;text-align:right;">
                        <button type="button" class="action-btn secondary btn-edit-stock" data-id="${item.id}" data-qty="${item.quantity}" data-price="${item.price}" data-name="${escapeHtml(m.name)}">
                            ✏️ Update Stock / Price
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        // Wire edit inventory buttons
        inventoryTableBody.querySelectorAll('.btn-edit-stock').forEach(btn => {
            btn.onclick = async () => {
                const id = btn.getAttribute('data-id');
                const oldQty = btn.getAttribute('data-qty');
                const oldPrice = btn.getAttribute('data-price');
                const name = btn.getAttribute('data-name');

                const newQtyStr = prompt(`Update stock quantity for "${name}":`, oldQty);
                if (newQtyStr === null) return;
                const newQty = parseInt(newQtyStr, 10);
                if (isNaN(newQty) || newQty < 0) {
                    showToast('Quantity cannot be negative.', 'error');
                    return;
                }

                const newPriceStr = prompt(`Update retail price (₹) for "${name}":`, oldPrice);
                if (newPriceStr === null) return;
                const newPrice = parseFloat(newPriceStr);
                if (isNaN(newPrice) || newPrice < 0) {
                    showToast('Price cannot be negative.', 'error');
                    return;
                }

                const res = await apiFetch(`/api/pharmacy/inventory/${id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ quantity: newQty, price: newPrice })
                });

                if (res.ok) {
                    showToast(`Updated stock and price for "${name}".`, 'success');
                    await loadInventory();
                } else {
                    showToast(res.message || 'Failed to update stock.', 'error');
                }
            };
        });
    }

    // 4. Load Master Catalog Options for Modal
    async function loadCatalogOptions() {
        medSelect.innerHTML = '<option value="">Loading master catalog...</option>';
        const res = await apiFetch('/api/medicines');
        if (res.ok && res.data && Array.isArray(res.data.medicines)) {
            const allMeds = res.data.medicines;
            // Filter out medicines already in inventory
            const stockedIds = new Set(inventoryData.map(i => i.medicine_id));
            const available = allMeds.filter(m => !stockedIds.has(m.id));

            if (available.length === 0) {
                medSelect.innerHTML = '<option value="">All catalog medicines are already stocked in your inventory.</option>';
                return;
            }

            medSelect.innerHTML = '<option value="">-- Choose a medicine from catalog --</option>' + available.map(m => `
                <option value="${m.id}">${escapeHtml(m.name)} (${escapeHtml(m.dosage_form || '')} ${escapeHtml(m.strength || '')}) ${m.requires_prescription ? '[Rx Required]' : '[OTC]'}</option>
            `).join('');
        } else {
            medSelect.innerHTML = '<option value="">Failed to load catalog.</option>';
        }
    }

    // Handle add stock form submit
    addStockForm.onsubmit = async (e) => {
        e.preventDefault();
        const medId = medSelect.value;
        const qty = parseInt(document.getElementById('modal-stock-qty').value, 10);
        const price = parseFloat(document.getElementById('modal-stock-price').value);

        if (!medId) {
            showToast('Please select a medicine.', 'warning');
            return;
        }

        const res = await apiFetch('/api/pharmacy/inventory', {
            method: 'POST',
            body: JSON.stringify({
                medicine_id: parseInt(medId, 10),
                quantity: qty,
                price: price
            })
        });

        if (res.ok) {
            showToast('Medicine added to your inventory!', 'success');
            addStockModal.style.display = 'none';
            addStockForm.reset();
            await loadInventory();
        } else {
            showToast(res.message || 'Failed to add medicine.', 'error');
        }
    };

    function getStatusStyle(status) {
        if (status === 'COMPLETED') return 'background:#dcfce7;color:#15803d;';
        if (status === 'REJECTED') return 'background:#fee2e2;color:#b91c1c;';
        if (status === 'READY_FOR_PICKUP') return 'background:#ede9fe;color:#6d28d9;';
        if (status === 'OUT_FOR_DELIVERY') return 'background:#fef3c7;color:#b45309;';
        if (status === 'PREPARING') return 'background:#fef3c7;color:#92400e;';
        if (status === 'ACCEPTED') return 'background:#dbeafe;color:#1d4ed8;';
        return 'background:#e0f2fe;color:#0369a1;';
    }
});
