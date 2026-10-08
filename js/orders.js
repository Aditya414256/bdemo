// ==========================================
// MediFind - Customer Orders & Live Polling
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireRole(['CUSTOMER'])) return;

    const listContainer = document.getElementById('orders-list-items');
    const countBadge = document.getElementById('orders-count-badge');
    const detailPanel = document.getElementById('order-detail-panel');

    const urlParams = new URLSearchParams(window.location.search);
    let selectedOrderId = urlParams.get('id') ? parseInt(urlParams.get('id'), 10) : null;
    let pollInterval = null;
    let ordersData = [];

    // Load Customer Orders
    await loadOrders();

    async function loadOrders() {
        const res = await apiFetch('/api/orders');
        if (res.ok && res.data && Array.isArray(res.data.orders)) {
            ordersData = res.data.orders;
            countBadge.textContent = `${ordersData.length} order(s)`;

            if (ordersData.length === 0) {
                listContainer.innerHTML = `
                    <div style="text-align:center;padding:30px 10px;color:#64748b;font-size:0.88rem;">
                        You have not placed any orders yet.
                        <div style="margin-top:12px;">
                            <a href="HomePage.html" style="color:#0284c7;font-weight:600;text-decoration:none;">Search Medicines →</a>
                        </div>
                    </div>
                `;
                detailPanel.innerHTML = `
                    <div style="text-align:center;padding:60px 20px;color:#64748b;">
                        <h3 style="color:#0f172a;margin-bottom:8px;">No Active Orders</h3>
                        <p style="margin:0 0 16px 0;">Start by finding your required medicines and choosing a nearby pharmacy.</p>
                        <a href="HomePage.html" style="background:#0284c7;color:#fff;padding:10px 20px;border-radius:10px;text-decoration:none;font-weight:600;display:inline-block;">Find Medicines</a>
                    </div>
                `;
                return;
            }

            renderOrdersList();

            // Select specified order or default to the most recent one
            const targetOrder = selectedOrderId 
                ? ordersData.find(o => o.id === selectedOrderId) || ordersData[0]
                : ordersData[0];

            selectOrder(targetOrder.id);
        } else {
            listContainer.innerHTML = `
                <div style="padding:20px;text-align:center;color:#ef4444;font-size:0.85rem;">
                    Failed to load orders.
                </div>
            `;
        }
    }

    function renderOrdersList() {
        listContainer.innerHTML = ordersData.map(o => `
            <div class="order-item-card ${o.id === selectedOrderId ? 'active' : ''}" data-id="${o.id}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-weight:700;color:#0f172a;font-size:0.95rem;">Order #${o.id}</span>
                    <span style="font-size:0.75rem;padding:3px 8px;border-radius:999px;font-weight:700;${getStatusBadgeStyle(o.status)}">
                        ${formatStatusLabel(o.status)}
                    </span>
                </div>
                <div style="font-size:0.85rem;color:#475569;margin-bottom:4px;">
                    🏥 ${escapeHtml(o.pharmacy?.name || 'Pharmacy')}
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.8rem;color:#64748b;">
                    <span>${o.fulfillment_type === 'DELIVERY' ? '🚚 Delivery' : '🏪 Pickup'}</span>
                    <strong style="color:#0f172a;font-family:'Space Grotesk',sans-serif;font-size:0.95rem;">₹${parseFloat(o.total_amount).toFixed(2)}</strong>
                </div>
            </div>
        `).join('');

        listContainer.querySelectorAll('.order-item-card').forEach(card => {
            card.onclick = () => {
                const id = parseInt(card.getAttribute('data-id'), 10);
                selectOrder(id);
            };
        });
    }

    async function selectOrder(orderId) {
        selectedOrderId = orderId;
        renderOrdersList();

        // Clear existing polling
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }

        // Fetch fresh order details
        await updateOrderDetail(orderId);

        // Start polling if status is still active
        const order = ordersData.find(o => o.id === orderId);
        if (order && !['COMPLETED', 'REJECTED'].includes(order.status)) {
            pollInterval = setInterval(async () => {
                await updateOrderDetail(orderId, true);
            }, 3500);
        }
    }

    async function updateOrderDetail(orderId, isPolling = false) {
        const res = await apiFetch(`/api/orders/${orderId}`);
        if (!res.ok || !res.data) return;

        const order = res.data;

        // Update local list state
        const idx = ordersData.findIndex(o => o.id === order.id);
        if (idx !== -1) {
            ordersData[idx] = order;
            if (isPolling) renderOrdersList();
        }

        renderTrackingView(order);

        // Stop polling if status reached final state
        if (['COMPLETED', 'REJECTED'].includes(order.status)) {
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
        }
    }

    function renderTrackingView(order) {
        const isDelivery = order.fulfillment_type === 'DELIVERY';
        const status = order.status;
        const msg = order.status_message || getStatusMessage(status);

        // Steps definitions
        const steps = isDelivery 
            ? [
                { key: 'PLACED', label: 'Order Placed' },
                { key: 'ACCEPTED', label: 'Confirmed' },
                { key: 'PREPARING', label: 'Preparing' },
                { key: 'OUT_FOR_DELIVERY', label: 'Out for Delivery' },
                { key: 'COMPLETED', label: 'Completed' }
            ]
            : [
                { key: 'PLACED', label: 'Order Placed' },
                { key: 'ACCEPTED', label: 'Confirmed' },
                { key: 'PREPARING', label: 'Preparing' },
                { key: 'READY_FOR_PICKUP', label: 'Ready for Pickup' },
                { key: 'COMPLETED', label: 'Completed' }
            ];

        const currentStepIndex = steps.findIndex(s => s.key === status);

        detailPanel.innerHTML = `
            <!-- Order Header -->
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #e2e8f0;">
                <div>
                    <span style="font-size:0.8rem;color:#64748b;font-weight:600;">ORDER TRACKING</span>
                    <h2 style="margin:2px 0 0 0;font-family:'Space Grotesk',sans-serif;font-size:1.6rem;color:#0f172a;">
                        Order #${order.id}
                    </h2>
                    <div style="font-size:0.82rem;color:#64748b;margin-top:4px;">
                        Placed on ${new Date(order.created_at).toLocaleString()}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.4rem;font-weight:800;color:#0284c7;font-family:'Space Grotesk',sans-serif;">
                        ₹${parseFloat(order.total_amount).toFixed(2)}
                    </div>
                    <span style="font-size:0.75rem;padding:3px 8px;border-radius:999px;font-weight:600;background:${order.payment_status === 'PAID' ? '#dcfce7;color:#166534;' : '#fef3c7;color:#92400e;'}">
                        Cash (${order.payment_status || 'PENDING'})
                    </span>
                </div>
            </div>

            <!-- Customer Status Banner (Exact wording requirement) -->
            <div class="status-banner ${status.toLowerCase()}">
                <div style="font-size:24px;">${getStatusIcon(status)}</div>
                <div>
                    <div style="font-size:1.1rem;font-weight:800;">
                        "${msg}"
                    </div>
                    <div style="font-size:0.82rem;opacity:0.9;margin-top:2px;">
                        ${getStatusSubtext(status, isDelivery)}
                    </div>
                </div>
            </div>

            <!-- Stepper Progress Bar (if not rejected) -->
            ${status !== 'REJECTED' ? `
                <div class="stepper-container">
                    ${steps.map((s, idx) => {
                        let stateClass = '';
                        if (idx < currentStepIndex) stateClass = 'completed';
                        else if (idx === currentStepIndex) stateClass = 'active';

                        return `
                            <div class="stepper-step ${stateClass}">
                                <div class="stepper-circle">
                                    ${idx < currentStepIndex ? '✓' : idx + 1}
                                </div>
                                <div class="stepper-label">${s.label}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            ` : `
                <div style="padding:16px;background:#fef2f2;border:1px dashed #fca5a5;border-radius:12px;color:#991b1b;margin-bottom:24px;font-size:0.9rem;">
                    <strong>Notice:</strong> This order was not taken by the pharmacy or the uploaded prescription was rejected. Any inventory reservation was released.
                </div>
            `}

            <!-- Order Details Grid -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
                    <h4 style="margin:0 0 8px 0;font-size:0.95rem;color:#0f172a;">🏥 Pharmacy Details</h4>
                    <div style="font-weight:700;color:#0f172a;font-size:0.92rem;">${escapeHtml(order.pharmacy?.name)}</div>
                    <div style="font-size:0.82rem;color:#64748b;margin-top:4px;">📍 ${escapeHtml(order.pharmacy?.address)}, ${escapeHtml(order.pharmacy?.city)}</div>
                    ${order.pharmacy?.phone ? `<div style="font-size:0.82rem;color:#64748b;margin-top:2px;">📞 ${escapeHtml(order.pharmacy?.phone)}</div>` : ''}
                </div>

                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
                    <h4 style="margin:0 0 8px 0;font-size:0.95rem;color:#0f172a;">📦 Delivery / Fulfillment</h4>
                    <div style="font-weight:700;color:#0f172a;font-size:0.92rem;">
                        ${isDelivery ? '🚚 Home Delivery' : '🏪 In-Store Pickup'}
                    </div>
                    ${isDelivery ? `
                        <div style="font-size:0.82rem;color:#64748b;margin-top:4px;">
                            <strong>Address:</strong> ${escapeHtml(order.delivery_address || 'Provided at checkout')}
                        </div>
                    ` : `
                        <div style="font-size:0.82rem;color:#64748b;margin-top:4px;">
                            Pick up in person during pharmacy open hours. Pay cash at counter.
                        </div>
                    `}
                    ${order.has_prescription ? `
                        <div style="margin-top:6px;font-size:0.8rem;color:#0369a1;font-weight:600;">
                            Prescription Review: <span style="text-transform:uppercase;">${order.prescription_status || 'PENDING'}</span>
                        </div>
                    ` : ''}
                </div>
            </div>

            <!-- Ordered Medicines Table -->
            <div>
                <h4 style="margin:0 0 10px 0;font-size:0.95rem;color:#0f172a;">Ordered Items</h4>
                <div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
                    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;text-align:left;">
                        <thead>
                            <tr style="background:#f8fafc;border-bottom:1px solid #e2e8f0;color:#475569;">
                                <th style="padding:10px 14px;">Medicine</th>
                                <th style="padding:10px 14px;text-align:center;">Qty</th>
                                <th style="padding:10px 14px;text-align:right;">Unit Price</th>
                                <th style="padding:10px 14px;text-align:right;">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${order.items.map(item => `
                                <tr style="border-bottom:1px solid #f1f5f9;">
                                    <td style="padding:12px 14px;">
                                        <strong>${escapeHtml(item.medicine_name)}</strong>
                                        <div style="font-size:0.75rem;color:#64748b;">${escapeHtml(item.dosage_form || '')} ${escapeHtml(item.strength || '')}</div>
                                    </td>
                                    <td style="padding:12px 14px;text-align:center;font-weight:600;">${item.quantity}</td>
                                    <td style="padding:12px 14px;text-align:right;">₹${parseFloat(item.unit_price).toFixed(2)}</td>
                                    <td style="padding:12px 14px;text-align:right;font-weight:700;">₹${parseFloat(item.subtotal).toFixed(2)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    function getStatusMessage(status) {
        const msgs = {
            'PLACED': 'Your order has been placed.',
            'ACCEPTED': 'Your order has been confirmed.',
            'PREPARING': 'Your order is being prepared.',
            'READY_FOR_PICKUP': 'Your order is ready for pickup.',
            'OUT_FOR_DELIVERY': 'Your order is out for delivery.',
            'COMPLETED': 'Your order has been completed.',
            'REJECTED': 'Your order was not taken.'
        };
        return msgs[status] || 'Order updated.';
    }

    function getStatusSubtext(status, isDelivery) {
        if (status === 'PLACED') return 'Waiting for pharmacy owner to confirm stock and review prescription.';
        if (status === 'ACCEPTED') return 'The pharmacy has confirmed stock and accepted your order.';
        if (status === 'PREPARING') return 'Pharmacist is packaging your medicines.';
        if (status === 'READY_FOR_PICKUP') return 'You can visit the pharmacy store counter to collect your order.';
        if (status === 'OUT_FOR_DELIVERY') return 'Delivery partner is bringing your medicine to your address.';
        if (status === 'COMPLETED') return 'Order completed and payment received in cash.';
        if (status === 'REJECTED') return 'Order was declined by the pharmacy.';
        return '';
    }

    function getStatusIcon(status) {
        if (status === 'COMPLETED') return '✅';
        if (status === 'REJECTED') return '❌';
        if (status === 'READY_FOR_PICKUP') return '🏪';
        if (status === 'OUT_FOR_DELIVERY') return '🚚';
        if (status === 'PREPARING') return '💊';
        if (status === 'ACCEPTED') return '👍';
        return '⏳';
    }

    function formatStatusLabel(status) {
        return status.replace(/_/g, ' ');
    }

    function getStatusBadgeStyle(status) {
        if (status === 'COMPLETED') return 'background:#dcfce7;color:#15803d;';
        if (status === 'REJECTED') return 'background:#fee2e2;color:#b91c1c;';
        if (status === 'READY_FOR_PICKUP') return 'background:#ede9fe;color:#6d28d9;';
        if (status === 'OUT_FOR_DELIVERY') return 'background:#fef3c7;color:#b45309;';
        if (status === 'PREPARING') return 'background:#fef3c7;color:#92400e;';
        if (status === 'ACCEPTED') return 'background:#dbeafe;color:#1d4ed8;';
        return 'background:#e0f2fe;color:#0369a1;';
    }

    // Cleanup polling when navigating away
    window.addEventListener('beforeunload', () => {
        if (pollInterval) clearInterval(pollInterval);
    });
});
