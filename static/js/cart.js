document.addEventListener('DOMContentLoaded', () => {
    
    renderCartPage();

    async function renderCartPage() {
        const cartItemsContainer = document.getElementById('cart-items-list');
        const emptyState = document.getElementById('cart-empty');
        const summaryCard = document.querySelector('.cart-summary-section');
        const headerItemCount = document.getElementById('header-item-count');
        const subtotalEl = document.getElementById('subtotal');
        const totalEl = document.getElementById('total');
        const shippingEl = document.getElementById('shipping');
        const discountEl = document.getElementById('discount');
        
        if (!cartItemsContainer) return;

        try {
            const response = await fetch('/api/cart/');
            if (!response.ok) throw new Error('Failed to fetch cart');
            const state = await response.json();
            
            const totalItems = state.items.reduce((acc, item) => acc + item.quantity, 0);
            headerItemCount.textContent = totalItems;
            
            // Update global nav cart count as well
            const navCounts = document.querySelectorAll('.cart-count');
            navCounts.forEach(el => el.textContent = totalItems);

            if (state.items.length === 0) {
                cartItemsContainer.innerHTML = '';
                emptyState.style.display = 'block';
                summaryCard.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            summaryCard.style.display = 'block';
            
            cartItemsContainer.innerHTML = state.items.map(item => {
                const disableMinus = item.quantity <= 1 ? 'disabled' : '';
                const disablePlus = item.quantity >= 9 ? 'disabled' : '';
                
                return `
                <div class="cart-item" id="cart-item-${item.id}">
                    <div class="item-image" style="background-image: url('${item.image || '/static/images/placeholder.png'}');"></div>
                    <div class="item-details">
                        <div class="item-title-row">
                            <div>
                                <h3 class="item-name">${item.name}</h3>
                                <span class="item-category">${item.category || 'Apparel'}</span>
                                <div class="item-meta">${[item.color, item.size, item.fit].filter(Boolean).join(' | ')}</div>
                                ${item.custom_text ? `<div class="item-custom">"${item.custom_text}" - ${item.placement}</div>` : ''}
                            </div>
                            <div class="item-price">₹${parseFloat(item.price).toLocaleString('en-IN')}</div>
                        </div>
                        <div class="item-actions">
                            <div class="quantity-controls">
                                <button class="qty-btn dec-qty" onclick="handleUpdateCartItem(${item.id}, ${item.quantity - 1})" ${disableMinus}>-</button>
                                <span class="qty-val">${item.quantity}</span>
                                <button class="qty-btn inc-qty" onclick="handleUpdateCartItem(${item.id}, ${item.quantity + 1})" ${disablePlus}>+</button>
                            </div>
                            <button class="remove-item" onclick="handleRemoveCartItem(${item.id})">REMOVE</button>
                        </div>
                    </div>
                </div>
            `}).join('');

            subtotalEl.textContent = `₹${parseFloat(state.subtotal).toLocaleString('en-IN')}`;
            const shipping = state.subtotal > 5000 ? 0 : 100; // Mock logic, ideally from backend but matching what exists
            shippingEl.textContent = shipping === 0 ? 'FREE' : `₹${shipping}`;
            totalEl.textContent = `₹${(parseFloat(state.subtotal) + shipping).toLocaleString('en-IN')}`;

        } catch (e) {
            console.error("Error rendering cart page:", e);
        }
    }
    
    // Attach these to window so inline onclick can use them
    window.handleUpdateCartItem = async function(id, quantity) {
        if (quantity < 1 || quantity > 9) return;
        
        if (typeof updateCartItem === 'function') {
            await updateCartItem(id, quantity); // global.js function
            renderCartPage(); // re-render without full reload
        }
    };
    
    window.handleRemoveCartItem = async function(id) {
        const itemEl = document.getElementById(`cart-item-${id}`);
        if (itemEl) {
            itemEl.classList.add('removing');
            setTimeout(async () => {
                if (typeof removeCartItem === 'function') {
                    await removeCartItem(id); // global.js function
                    renderCartPage(); 
                }
            }, 300); // Wait for CSS animation
        } else {
            if (typeof removeCartItem === 'function') {
                await removeCartItem(id);
                renderCartPage();
            }
        }
    };

    // ----------------------------------------------------
    // Razorpay Checkout Integration
    // ----------------------------------------------------
    const btnProceedCheckout = document.getElementById('btn-proceed-checkout');
    if (btnProceedCheckout) {
        btnProceedCheckout.addEventListener('click', async () => {
            
            // Check auth (assuming anonymous users can't reach this properly or will be rejected by backend)
            btnProceedCheckout.textContent = "PROCESSING...";
            btnProceedCheckout.disabled = true;

            try {
                // Read configuration
                const configDiv = document.getElementById('checkout-config');
                const createPaymentUrl = configDiv ? configDiv.getAttribute('data-create-payment-url') : '/checkout/create-payment/';
                const paymentSuccessUrl = configDiv ? configDiv.getAttribute('data-payment-success-url') : '/checkout/payment-success/';

                // 1-6. Create local order and Razorpay order
                const res = await fetch(createPaymentUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({}) // We send empty body to let backend use default address
                });
                
                if (!res.ok) {
                    // Try to parse json if backend sent error, otherwise throw generic text
                    let errMsg = 'Failed to create order. Please try again.';
                    try {
                        const errData = await res.json();
                        if (errData.error) errMsg = errData.error;
                    } catch (e) {
                        errMsg = `Server Error (${res.status})`;
                    }
                    throw new Error(errMsg);
                }

                const data = await res.json();

                // 7. Initialize Razorpay Checkout
                const options = {
                    "key": data.key_id, 
                    "amount": data.amount,
                    "currency": data.currency,
                    "name": "URBN",
                    "description": "Premium Streetwear Order",
                    "order_id": data.razorpay_order_id,
                    "prefill": {
                        "name": data.customer_name,
                        "email": data.customer_email,
                        "contact": data.customer_phone ? (data.customer_phone.startsWith('+91') ? data.customer_phone : '+91' + data.customer_phone) : ""
                    },
                    "theme": {
                        "color": "#121212"
                    },
                    "handler": async function (response) {
                        // 11. Payment success, verify on backend
                        try {
                            const verifyRes = await fetch(paymentSuccessUrl, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: JSON.stringify({
                                    razorpay_payment_id: response.razorpay_payment_id,
                                    razorpay_order_id: response.razorpay_order_id,
                                    razorpay_signature: response.razorpay_signature,
                                    local_order_id: data.order_id
                                })
                            });
                            
                            if (!verifyRes.ok) {
                                let vErrMsg = 'Payment verification failed.';
                                try {
                                    const vErrData = await verifyRes.json();
                                    if (vErrData.error) vErrMsg = vErrData.error;
                                } catch(e) {}
                                throw new Error(vErrMsg);
                            }

                            const verifyData = await verifyRes.json();
                            if (verifyData.success) {
                                // 12. Redirect to Confirmation
                                window.location.href = `/orders/${verifyData.order_number}/confirmed/`;
                            } else {
                                alert("Payment verification failed: " + verifyData.error);
                                resetCheckoutBtn();
                            }
                        } catch (err) {
                            console.error("Verification error", err);
                            alert("Something went wrong verifying the payment.");
                            resetCheckoutBtn();
                        }
                    },
                    "modal": {
                        "ondismiss": function() {
                            // 12. Payment Cancelled
                            showToast("Payment cancelled. Your items are still in your bag.", "info");
                            resetCheckoutBtn();
                        }
                    }
                };
                
                const rzp1 = new Razorpay(options);
                
                rzp1.on('payment.failed', function (response){
                    // 11. Payment Failed
                    showToast("Payment failed. Please try again.", "error");
                    resetCheckoutBtn();
                });
                
                // 8. Open Razorpay Checkout
                rzp1.open();
                
            } catch (err) {
                console.error("Checkout error:", err);
                if (err.message.includes('Authentication') || err.message.includes('login')) {
                    window.location.href = '/accounts/login/?next=/cart/';
                } else {
                    showToast(err.message, "error");
                    resetCheckoutBtn();
                }
            }
        });
    }

    function resetCheckoutBtn() {
        if (btnProceedCheckout) {
            btnProceedCheckout.textContent = "PROCEED TO CHECKOUT";
            btnProceedCheckout.disabled = false;
        }
    }

    // Utility for cookies (required for Django CSRF)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
